import json
import os
import socket
import subprocess
import tempfile
import uuid
import wave
from array import array
from pathlib import Path
from typing import Literal
from importlib.util import find_spec

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.background import BackgroundTask
from starlette.concurrency import run_in_threadpool

try:
    from app.config import (
        ALLOWED_EXTENSIONS,
        APP_NAME,
        CLI_PATH,
        COMPUTE_TYPE,
        DEVICE,
        GPU_DEVICE,
        MAX_UPLOAD_BYTES,
        MAX_UPLOAD_MB,
        MODEL_PATH,
        MODEL_SIZE,
        STATIC_DIR,
        TEMP_DIR,
    )
except ImportError:
    from config import (
        ALLOWED_EXTENSIONS,
        APP_NAME,
        CLI_PATH,
        COMPUTE_TYPE,
        DEVICE,
        GPU_DEVICE,
        MAX_UPLOAD_BYTES,
        MAX_UPLOAD_MB,
        MODEL_PATH,
        MODEL_SIZE,
        STATIC_DIR,
        TEMP_DIR,
    )

# Faster-Whisper plus the Windows scientific stack can load duplicate OpenMP runtimes.
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

app = FastAPI(
    title=APP_NAME,
    description="Local audio/video transcription powered by whisper.cpp Vulkan.",
    version="1.0.0",
)

backend_error = None
diarization_pipeline = None
diarization_error = None


def backend_ready() -> bool:
    global backend_error
    if not CLI_PATH.is_file():
        backend_error = f"whisper-cli tidak ditemukan: {CLI_PATH}"
        return False
    if not MODEL_PATH.is_file():
        backend_error = f"Model ggml tidak ditemukan: {MODEL_PATH}"
        return False
    backend_error = None
    return True


def _extension_for(filename: str) -> str:
    return Path(filename).suffix.lower()


async def _save_upload(file: UploadFile) -> Path:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Nama file wajib ada.")

    extension = _extension_for(file.filename)
    if extension not in ALLOWED_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_EXTENSIONS))
        raise HTTPException(status_code=400, detail=f"Format file tidak didukung. Gunakan: {allowed}.")

    temp_name = f"{uuid.uuid4().hex}{extension}"
    target_path = TEMP_DIR / temp_name
    bytes_written = 0

    try:
        with target_path.open("wb") as buffer:
            while chunk := await file.read(1024 * 1024):
                bytes_written += len(chunk)
                if bytes_written > MAX_UPLOAD_BYTES:
                    raise HTTPException(
                        status_code=413,
                        detail=f"Ukuran file melebihi batas {MAX_UPLOAD_MB} MB.",
                    )
                buffer.write(chunk)
    except Exception:
        if target_path.exists():
            target_path.unlink()
        raise
    finally:
        await file.close()

    return target_path


@app.exception_handler(HTTPException)
async def http_exception_handler(_, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": "error", "message": exc.detail},
    )


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "app": APP_NAME,
        "model_loaded": backend_ready(),
        "model": MODEL_SIZE,
        "device": DEVICE,
        "compute_type": COMPUTE_TYPE,
        "max_upload_mb": MAX_UPLOAD_MB,
        "model_error": backend_error,
        "backend": "whisper.cpp Vulkan",
        "gpu_device": GPU_DEVICE,
        "diarization_available": diarization_available(),
    }


@app.post("/api/warmup")
async def warmup_model():
    if not backend_ready():
        raise HTTPException(status_code=503, detail=backend_error or "Backend Vulkan belum tersedia.")
    return {"status": "ready", "model": MODEL_SIZE, "device": DEVICE, "gpu_device": GPU_DEVICE}


@app.post("/api/extract-audio")
async def extract_audio(file: UploadFile = File(...)):
    source_path = await _save_upload(file)
    output_path = None
    try:
        if not source_path.is_file():
            raise HTTPException(status_code=500, detail="File upload tidak berhasil disimpan di server.")

        output_name = f"{Path(file.filename).stem}-audio.wav"
        output_path = TEMP_DIR / f"{uuid.uuid4().hex}.wav"

        try:
            await run_in_threadpool(_extract_audio_track, source_path, output_path)
        except Exception as exc:
            raise RuntimeError(f"Gagal mengekstrak audio: {exc}") from exc

        return FileResponse(
            path=output_path,
            media_type="audio/wav",
            filename=output_name,
            background=BackgroundTask(output_path.unlink, missing_ok=True),
        )
    except HTTPException:
        raise
    except Exception as exc:
        print(f"Audio extraction error for {source_path}: {exc}")
        if output_path is not None and output_path.exists():
            output_path.unlink()
        raise HTTPException(status_code=500, detail=f"Ekstraksi audio gagal ({type(exc).__name__}): {exc}") from exc
    finally:
        if source_path.exists():
            source_path.unlink()


def _load_diarization_pipeline():
    global diarization_pipeline, diarization_error

    if diarization_pipeline is not None:
        return diarization_pipeline

    token = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_TOKEN")
    if not token:
        diarization_error = "HF_TOKEN belum diatur. PyAnnote membutuhkan token Hugging Face."
        return None

    try:
        from pyannote.audio import Pipeline

        try:
            diarization_pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                token=token,
            )
        except TypeError:
            diarization_pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                use_auth_token=token,
            )
        diarization_error = None
        return diarization_pipeline
    except Exception as exc:  # pragma: no cover - depends on optional local package/model
        diarization_error = str(exc)
        return None


def diarization_available() -> bool:
    token = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_TOKEN")
    return bool(token and find_spec("pyannote.audio"))


def _speaker_for_segment(diarization, start: float, end: float, labels: dict[str, str]) -> str:
    best_speaker = "Unknown"
    best_overlap = 0.0
    for turn, _, speaker in diarization.itertracks(yield_label=True):
        overlap = max(0.0, min(end, turn.end) - max(start, turn.start))
        if overlap > best_overlap:
            best_overlap = overlap
            if speaker not in labels:
                labels[speaker] = f"Pembicara {len(labels) + 1}"
            best_speaker = labels[speaker]
    return best_speaker


def _convert_to_wav(source_path: Path, target_path: Path) -> None:
    import av

    resampler = av.audio.resampler.AudioResampler(format="s16", layout="mono", rate=16000)
    pcm = array("h")
    with av.open(str(source_path), mode="r", metadata_errors="ignore") as container:
        for frame in container.decode(audio=0):
            for resampled in resampler.resample(frame):
                pcm.extend(resampled.to_ndarray().reshape(-1).tolist())
    with wave.open(str(target_path), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(16000)
        output.writeframes(pcm.tobytes())


def _extract_audio_track(source_path: Path, target_path: Path, sample_rate: int = 44100) -> None:
    import av

    with av.open(str(source_path), mode="r", metadata_errors="ignore") as container:
        if not container.streams.audio:
            raise RuntimeError("File tidak memiliki jalur audio.")
        channels = container.streams.audio[0].codec_context.channels or 1
        layout = "stereo" if channels >= 2 else "mono"
        resampler = av.audio.resampler.AudioResampler(format="s16", layout=layout, rate=sample_rate)
        pcm = array("h")
        for frame in container.decode(audio=0):
            for resampled in resampler.resample(frame):
                pcm.extend(resampled.to_ndarray().reshape(-1).tolist())

    if not pcm:
        raise RuntimeError("Tidak ada audio yang berhasil diekstrak dari file ini.")

    with wave.open(str(target_path), "wb") as output:
        output.setnchannels(2 if layout == "stereo" else 1)
        output.setsampwidth(2)
        output.setframerate(sample_rate)
        output.writeframes(pcm.tobytes())


def _run_transcription(
    audio_path: Path,
    language_code: str | None,
    task: str,
    beam_size: int,
    vad_filter: bool,
    diarize: bool,
):
    if not backend_ready():
        raise RuntimeError(backend_error or "Backend Vulkan belum tersedia.")

    with tempfile.TemporaryDirectory(prefix="whisper-") as work_dir:
        work_path = Path(work_dir)
        wav_path = work_path / "input.wav"
        output_prefix = work_path / "result"
        _convert_to_wav(audio_path, wav_path)
        command = [
            str(CLI_PATH), "-m", str(MODEL_PATH), "-f", str(wav_path),
            "-oj", "-of", str(output_prefix), "-dev", str(GPU_DEVICE),
            "-t", str(max(1, os.cpu_count() or 4)), "-bs", str(beam_size),
            "-l", language_code or "auto", "-np",
        ]
        if task == "translate":
            command.append("-tr")
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=int(os.getenv("WHISPER_TIMEOUT_SECONDS", "3600")),
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        json_path = output_prefix.with_suffix(".json")
        if completed.returncode != 0 or not json_path.is_file():
            details = (completed.stderr or completed.stdout).strip()[-1200:]
            raise RuntimeError(f"whisper.cpp gagal (exit {completed.returncode}): {details}")
        payload = json.loads(json_path.read_text(encoding="utf-8"))

        diarization = None
        if diarize:
            pipeline = _load_diarization_pipeline()
            if pipeline is None:
                raise RuntimeError(diarization_error or "Diarization tidak tersedia.")
            diarization = pipeline(str(wav_path))

    transcript_segments = []
    speaker_labels = {}
    for segment in payload.get("transcription", []):
        text = segment.get("text", "").strip()
        offsets = segment.get("offsets", {})
        if text:
            item = {
                "start": round(offsets.get("from", 0) / 100, 2),
                "end": round(offsets.get("to", 0) / 100, 2),
                "text": text,
            }
            if diarization is not None:
                item["speaker"] = _speaker_for_segment(
                    diarization,
                    item["start"],
                    item["end"],
                    speaker_labels,
                )
            transcript_segments.append(item)
    language = payload.get("result", {}).get("language", language_code or "")
    duration = max((segment["end"] for segment in transcript_segments), default=0)
    return transcript_segments, language, duration


@app.post("/api/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    language: str = Form("id"),
    task: Literal["transcribe", "translate"] = Form("transcribe"),
    beam_size: int = Form(5),
    vad_filter: bool = Form(True),
    diarize: bool = Form(False),
):
    audio_path = await _save_upload(file)
    try:
        if not audio_path.is_file():
            raise HTTPException(status_code=500, detail="File upload tidak berhasil disimpan di server.")

        if beam_size < 1 or beam_size > 10:
            raise HTTPException(status_code=400, detail="Beam size harus berada di antara 1 dan 10.")

        language_code = None if language == "auto" else language.strip().lower()
        transcript_segments, detected_language, duration = await run_in_threadpool(
            _run_transcription,
            audio_path,
            language_code,
            task,
            beam_size,
            vad_filter,
            diarize,
        )
        text = " ".join(segment["text"] for segment in transcript_segments).strip()

        return {
            "status": "success",
            "language": detected_language,
            "language_probability": 1.0,
            "duration": duration,
            "segments": transcript_segments,
            "text": text,
            "settings": {
                "model": MODEL_SIZE,
                "device": DEVICE,
                "gpu_device": GPU_DEVICE,
                "task": task,
                "beam_size": beam_size,
                "vad_filter": vad_filter,
                "diarize": diarize,
            },
        }
    except HTTPException:
        raise
    except Exception as exc:
        print(f"Transcription error for {audio_path}: {exc}")
        raise HTTPException(status_code=500, detail=f"Transkripsi gagal ({type(exc).__name__}): {exc}") from exc
    finally:
        if audio_path.exists():
            audio_path.unlink()


app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")


def pick_free_port(start_port: int = 8000, max_attempts: int = 20) -> int:
    requested_port = int(os.getenv("PORT", str(start_port)))
    ports_to_try = [requested_port] + list(range(start_port, start_port + max_attempts))
    seen = set()

    for port in ports_to_try:
        if port in seen:
            continue
        seen.add(port)

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue

    raise RuntimeError(
        f"Tidak ada port yang tersedia mulai dari {requested_port}. Tutup layanan lain atau ubah PORT."
    )


if __name__ == "__main__":
    import uvicorn

    try:
        port = pick_free_port()
    except RuntimeError as exc:
        print(exc)
        raise SystemExit(1) from exc

    print(f"Starting app on http://127.0.0.1:{port}")
    uvicorn.run(app, host="127.0.0.1", port=port)
