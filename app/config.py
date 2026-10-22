from pathlib import Path
import os

# Root directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Storage and assets directories
STATIC_DIR = BASE_DIR / "static"
TEMP_DIR = BASE_DIR / "uploads"
STATIC_DIR.mkdir(exist_ok=True)
TEMP_DIR.mkdir(exist_ok=True)

# Application metadata
APP_NAME = "Local AI Transcription Studio"

# Whisper & Hardware Settings
# large-v3-turbo jauh lebih akurat untuk bahasa Indonesia; fallback ke small jika belum diunduh.
MODEL_SIZE = os.getenv(
    "WHISPER_MODEL",
    "large-v3-turbo-q5_0" if (BASE_DIR / "models" / "ggml-large-v3-turbo-q5_0.bin").is_file() else "small",
)
# Windows uses the MSVC build (multi-config: bin/Release); Linux/macOS use scripts/build_whisper.sh output.
DEFAULT_CLI_PATH = (
    BASE_DIR / "build-vulkan" / "bin" / "Release" / "whisper-cli.exe"
    if os.name == "nt"
    else BASE_DIR / "build-linux" / "bin" / "whisper-cli"
)
CLI_PATH = Path(os.getenv("WHISPER_CLI", str(DEFAULT_CLI_PATH)))
MODEL_PATH = Path(os.getenv("WHISPER_MODEL_PATH", str(BASE_DIR / "models" / f"ggml-{MODEL_SIZE}.bin")))
VAD_MODEL_PATH = Path(os.getenv("WHISPER_VAD_MODEL_PATH", str(BASE_DIR / "models" / "ggml-silero-v5.1.2.bin")))
GPU_DEVICE = int(os.getenv("WHISPER_GPU_DEVICE", "1"))
DEVICE = "vulkan"
COMPUTE_TYPE = "gpu"

# File Upload Limits
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
