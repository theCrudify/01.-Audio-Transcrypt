import importlib
import os
import sys
from pathlib import Path

from app.config import CLI_PATH, MODEL_PATH

def run_verification() -> bool:
    root = Path(__file__).resolve().parent.parent
    print("Project directory:", root)
    print("Python executable:", sys.executable)

    required = ["fastapi", "uvicorn", "av"]
    missing = []
    for name in required:
        try:
            importlib.import_module(name)
            print(f"OK: {name}")
        except Exception as exc:  # pragma: no cover - diagnostic script only
            missing.append(f"{name}: {exc}")
            print(f"MISSING: {name} -> {exc}")

    if missing:
        print("\nDependency check failed. Install dependencies with:")
        print(f"{sys.executable} -m pip install -r requirements/base.txt")
        return False

    checks = {
        "whisper-cli Vulkan": CLI_PATH,
        "whisper model": MODEL_PATH,
    }
    for label, path in checks.items():
        if path.is_file():
            print(f"OK: {label} -> {path}")
        else:
            print(f"MISSING: {label} -> {path}")
            if path == CLI_PATH and os.name != "nt":
                print("Build it with: bash scripts/build_whisper.sh")
            return False

    from app.diarization import diarization_available

    print("OK: speaker diarization (sherpa-onnx)" if diarization_available()
          else "INFO: speaker diarization belum siap (opsional) -> python -m app.bootstrap")
    print("Ready to run (Vulkan GPU, CPU fallback).")
    return True


if __name__ == "__main__":
    if not run_verification():
        sys.exit(1)
