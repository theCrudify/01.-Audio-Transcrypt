import json
import os
import subprocess
import tempfile
from pathlib import Path

from app.audio import convert_to_wav
from app.config import CLI_PATH, GPU_DEVICE, MODEL_PATH
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

    with tempfile.TemporaryDirectory(prefix="whisper-") as work_dir:
        work_path = Path(work_dir)
        wav_path = work_path / "input.wav"
        output_prefix = work_path / "result"

        convert_to_wav(audio_path, wav_path)

        command = [
            str(CLI_PATH),
            "-m", str(MODEL_PATH),
            "-f", str(wav_path),
            "-oj",
            "-of", str(output_prefix),
            "-dev", str(GPU_DEVICE),
            "-t", str(max(1, os.cpu_count() or 4)),
            "-bs", str(beam_size),
            "-l", language_code or "auto",
            "-np",
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
            pipeline = load_diarization_pipeline()
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
