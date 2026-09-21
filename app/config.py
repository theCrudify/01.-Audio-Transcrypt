from pathlib import Path
import os

# Project root: 1 level above app/
BASE_DIR = Path(__file__).resolve().parent.parent

STATIC_DIR = BASE_DIR / "static"
TEMP_DIR = BASE_DIR / "uploads"
STATIC_DIR.mkdir(exist_ok=True)
TEMP_DIR.mkdir(exist_ok=True)

APP_NAME = "Local AI Transcription Studio"
MODEL_SIZE = os.getenv("WHISPER_MODEL", "small")
CLI_PATH = Path(os.getenv("WHISPER_CLI", str(BASE_DIR / "build-vulkan" / "bin" / "Release" / "whisper-cli.exe")))
MODEL_PATH = Path(os.getenv("WHISPER_MODEL_PATH", str(BASE_DIR / "models" / f"ggml-{MODEL_SIZE}.bin")))
GPU_DEVICE = int(os.getenv("WHISPER_GPU_DEVICE", "1"))
DEVICE = "vulkan"
COMPUTE_TYPE = "gpu"
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "512"))
MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024
ALLOWED_EXTENSIONS = {
    ".aac",
    ".flac",
    ".m4a",
    ".mkv",
    ".mov",
    ".mp3",
    ".mp4",
    ".ogg",
    ".opus",
    ".wav",
    ".webm",
}
