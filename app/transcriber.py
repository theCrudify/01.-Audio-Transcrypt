import json
import os
import subprocess
from pathlib import Path
from uuid import uuid4

from app.audio import convert_to_wav
from app.config import CLI_PATH, GPU_DEVICE, MODEL_PATH, TEMP_DIR
from app.diarization import diarization_error, load_diarization_pipeline, speaker_for_segment

backend_error = None


def backend_ready() -> bool:
    """Validates availability of whisper-cli executable and model file."""
    global backend_error
    if not CLI_PATH.is_file():
        backend_error = f"whisper-cli tidak ditemukan: {CLI_PATH}"
        return False
    if not MODEL_PATH.is_file():
        backend_error = f"Model ggml tidak ditemukan: {MODEL_PATH}"
        return False
    backend_error = None
    return True


def run_transcription(
    audio_path: Path,
    language_code: str | None,
    task: str,
    beam_size: int,
    vad_filter: bool,
    diarize: bool,
):
    """Executes whisper.cpp Vulkan backend on GPU and processes segments."""
    if not backend_ready():
        raise RuntimeError(backend_error or "Backend Vulkan belum tersedia.")

    temp_id = uuid4().hex
    wav_path = TEMP_DIR / f"whisper-input-{temp_id}.wav"
    output_prefix = TEMP_DIR / f"whisper-result-{temp_id}"
    json_path = output_prefix.with_suffix(".json")
    try:
        convert_to_wav(audio_path, wav_path)

        if not wav_path.is_file() or wav_path.stat().st_size < 100:
            raise RuntimeError("Gagal menghasilkan file audio WAV yang valid untuk diproses.")

        base_command = [
            str(CLI_PATH),
            "-m", str(MODEL_PATH),
            "-f", str(wav_path),
            "-oj",
            "-of", str(output_prefix),
            "-t", str(max(1, min(8, os.cpu_count() or 4))),
            "-bs", str(beam_size),
            "-l", language_code or "auto",
            "-np",
        ]
        if task == "translate":
            base_command.append("-tr")

        # Coba jalankan dengan GPU yang dikonfigurasi (GPU 1: RX 6550M)
        command = base_command + ["-dev", str(GPU_DEVICE)]
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=int(os.getenv("WHISPER_TIMEOUT_SECONDS", "3600")),
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )

        # Jika gagal pada GPU tertentu, coba fallback ke GPU 0 atau mode GPU otomatis
        if completed.returncode != 0 and GPU_DEVICE != 0:
            command_fallback = base_command + ["-dev", "0"]
            completed = subprocess.run(
                command_fallback,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=int(os.getenv("WHISPER_TIMEOUT_SECONDS", "3600")),
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )

        if completed.returncode != 0 or not json_path.is_file():
            details = (completed.stderr or completed.stdout or "").strip()[-1200:]
            raise RuntimeError(f"whisper.cpp gagal (exit {completed.returncode}): {details}")

        payload = json.loads(json_path.read_text(encoding="utf-8"))

        diarization = None
        if diarize:
            pipeline = load_diarization_pipeline()
            if pipeline is None:
                raise RuntimeError(diarization_error or "Diarization tidak tersedia.")
            diarization = pipeline(str(wav_path))
    finally:
        for temp_file in [wav_path, *TEMP_DIR.glob(f"whisper-result-{temp_id}.*")]:
            temp_file.unlink(missing_ok=True)

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
                item["speaker"] = speaker_for_segment(
                    diarization,
                    item["start"],
                    item["end"],
                    speaker_labels,
                )
            transcript_segments.append(item)

    language = payload.get("result", {}).get("language", language_code or "")
    duration = max((seg["end"] for seg in transcript_segments), default=0)
    return transcript_segments, language, duration
