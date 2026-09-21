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
)
from app.diarization import diarization_available
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
):
    audio_path = await _save_upload(file)
    try:
        if not audio_path.is_file():
            raise HTTPException(status_code=500, detail="File upload tidak berhasil disimpan di server.")

        if beam_size < 1 or beam_size > 10:
            raise HTTPException(status_code=400, detail="Beam size harus berada di antara 1 dan 10.")

        language_code = None if language == "auto" else language.strip().lower()
        transcript_segments, detected_language, duration = await run_in_threadpool(
            run_transcription,
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
