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
# "auto" = GPU diskrit (NVIDIA/AMD/Intel Arc), lalu iGPU, lalu CPU; atau nomor GPU Vulkan.
GPU_DEVICE = os.getenv("WHISPER_GPU_DEVICE", "auto")
DEVICE = "vulkan"
COMPUTE_TYPE = "gpu"

HOST = os.getenv("HOST", "127.0.0.1")

# Speaker diarization (sherpa-onnx, tanpa login): diunduh otomatis oleh app/bootstrap.py.
DIARIZATION_SEGMENTATION_MODEL = BASE_DIR / "models" / "pyannote-segmentation-3.0.onnx"
DIARIZATION_EMBEDDING_MODEL = BASE_DIR / "models" / "3dspeaker_speech_eres2net_sv_en_voxceleb_16k.onnx"

# Kode bahasa yang diterima whisper.cpp untuk -l (daftar large-v3). Sinkron dengan WHISPER_LANGS di static/index.html.
WHISPER_LANGUAGES = frozenset(
    "en zh de es ru ko fr ja pt tr pl ca nl ar sv it id hi fi vi he uk el ms cs ro da hu ta no th ur hr bg lt la mi "
    "ml cy sk te fa lv bn sr az sl kn et mk br eu is hy ne mn bs kk sq sw gl mr pa si km sn yo so af oc ka be tg sd "
    "gu am yi lo uz fo ht ps tk nn mt sa lb my bo tl mg as tt haw ln ha ba jw su yue".split()
)

# File Upload Limits
# 0 = tanpa batas (default). Isi angka MB untuk membatasi, misalnya di mode server.
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "0"))
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
