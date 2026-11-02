import os
import socket
import uuid
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.background import BackgroundTask
from starlette.concurrency import run_in_threadpool

from app.audio import extract_audio_track
from app.config import (
    HOST,
    ALLOWED_EXTENSIONS,
    APP_NAME,
    COMPUTE_TYPE,
    DEVICE,
    GPU_DEVICE,
    MAX_UPLOAD_BYTES,
    MAX_UPLOAD_MB,
    MODEL_SIZE,
    STATIC_DIR,
    TEMP_DIR,
    WHISPER_LANGUAGES,
)
from app.diarization import MAX_SPEAKERS, diarization_available
from app.transcriber import backend_error, backend_ready, run_transcription

# Avoid duplicate OpenMP runtimes on Windows
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

app = FastAPI(
    title=APP_NAME,
    description="Local audio/video transcription powered by whisper.cpp Vulkan.",
    version="1.0.0",
)


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

    try:
        written = 0
        with target_path.open("wb") as buffer:
            while chunk := await file.read(1024 * 1024):
                written += len(chunk)
                if MAX_UPLOAD_BYTES and written > MAX_UPLOAD_BYTES:
                    raise HTTPException(status_code=413, detail=f"File terlalu besar. Maksimal {MAX_UPLOAD_MB} MB.")
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


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse(STATIC_DIR / "favicon.svg", media_type="image/svg+xml")


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
async def extract_audio_endpoint(file: UploadFile = File(...)):
    source_path = await _save_upload(file)
    output_path = None
    try:
        if not source_path.is_file():
            raise HTTPException(status_code=500, detail="File upload tidak berhasil disimpan di server.")

        output_name = f"{Path(file.filename).stem}-audio.wav"
        output_path = TEMP_DIR / f"{uuid.uuid4().hex}.wav"

        try:
            await run_in_threadpool(extract_audio_track, source_path, output_path)
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


@app.post("/api/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    language: str = Form("id"),
    task: Literal["transcribe", "translate"] = Form("transcribe"),
    beam_size: int = Form(5),
    vad_filter: bool = Form(True),
    diarize: bool = Form(False),
    num_speakers: int = Form(0),
):
    # Validasi sebelum upload disimpan: kode tak dikenal membuat whisper-cli gagal setelah konversi audio.
    language = language.strip().lower()
    if language != "auto" and language not in WHISPER_LANGUAGES:
        await file.close()
        raise HTTPException(status_code=400, detail=f"Kode bahasa tidak dikenal: {language!r}. Gunakan 'auto' atau kode Whisper seperti 'id', 'en'.")
    # whisper.cpp menolak lebih dari 8 decoder (WHISPER_MAX_DECODERS).
    if beam_size < 1 or beam_size > 8:
        await file.close()
        raise HTTPException(status_code=400, detail="Beam size harus berada di antara 1 dan 8.")

    if not 0 <= num_speakers <= MAX_SPEAKERS:
        await file.close()
        raise HTTPException(status_code=400, detail=f"Jumlah pembicara harus 0 (otomatis) sampai {MAX_SPEAKERS}.")

    audio_path = await _save_upload(file)
    try:
        if not audio_path.is_file():
            raise HTTPException(status_code=500, detail="File upload tidak berhasil disimpan di server.")

        language_code = None if language == "auto" else language
        transcript_segments, detected_language, duration, language_checks = await run_in_threadpool(
            run_transcription,
            audio_path,
            language_code,
            task,
            beam_size,
            vad_filter,
            diarize,
            num_speakers,
        )
        text = " ".join(segment["text"] for segment in transcript_segments).strip()

        return {
            "status": "success",
            "language": detected_language,
            "language_probability": 1.0,
            "duration": duration,
            # Saat bahasa dipilih manual: bahasa yang terdeteksi di awal/tengah/akhir ucapan ([] jika auto).
            "language_checks": language_checks,
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
                "num_speakers": num_speakers,
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
                sock.bind((HOST, port))
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

    print(f"Starting app on http://{HOST}:{port}")
    # HOST=0.0.0.0 agar bisa diakses dari jaringan; APP_RELOAD=0 untuk server/paket portable.
    uvicorn.run("app.main:app", host=HOST, port=port, reload=os.getenv("APP_RELOAD", "1") == "1")
