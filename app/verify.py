import importlib
import os
import sys
from pathlib import Path

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
        print("python -m pip install -r requirements.txt")
        return False

    checks = {
        "whisper-cli Vulkan": root / "build-vulkan" / "bin" / "Release" / "whisper-cli.exe",
        "ggml-small model": root / "models" / "ggml-small.bin",
    }
    for label, path in checks.items():
        if path.is_file():
            print(f"OK: {label} -> {path}")
        else:
            print(f"MISSING: {label} -> {path}")
            return False

    print("Ready to run with AMD Vulkan GPU.")
    return True


if __name__ == "__main__":
    if not run_verification():
        sys.exit(1)
