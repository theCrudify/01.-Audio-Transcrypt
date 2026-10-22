#!/usr/bin/env bash
# Builds ready-to-run bundles (Python + deps + whisper.cpp + models) into dist/:
#   dist/AudioTranscrypt-linux.tar.gz   (needs glibc >= 2.38, e.g. Ubuntu 24.04+)
#   dist/AudioTranscrypt-windows.zip
# Run on Linux after scripts/build_whisper.sh. Usage: bash scripts/package.sh [linux|windows|all]
set -e

cd "$(dirname "$0")/.."
TARGET="${1:-all}"
PBS="https://github.com/astral-sh/python-build-standalone/releases/download/20261001"
PY_VER="3.12.15%2B20261001"
CACHE=dist/.cache
mkdir -p "$CACHE"

for f in models/ggml-large-v3-turbo-q5_0.bin models/ggml-silero-v5.1.2.bin; do
    [ -f "$f" ] || { echo "Missing $f (see README)"; exit 1; }
done

fetch_python() {  # $1 = platform triple, $2 = destination dir
    local tgz="$CACHE/python-$1.tar.gz"
    [ -f "$tgz" ] || curl -fL -o "$tgz" "$PBS/cpython-$PY_VER-x86_64-$1-install_only.tar.gz"
    tar -xzf "$tgz" -C "$2"
}

copy_common() {  # $1 = bundle dir
    mkdir -p "$1/models"
    cp -r app static "$1/"
    find "$1/app" -name __pycache__ -prune -exec rm -rf {} +
    cp models/ggml-large-v3-turbo-q5_0.bin models/ggml-silero-v5.1.2.bin "$1/models/"
}

if [ "$TARGET" = linux ] || [ "$TARGET" = all ]; then
    [ -x build-linux/bin/whisper-cli ] || { echo "Run scripts/build_whisper.sh first"; exit 1; }
    OUT=dist/AudioTranscrypt-linux
    rm -rf "$OUT" && mkdir -p "$OUT/build-linux/bin"
    fetch_python unknown-linux-gnu "$OUT"
    "$OUT/python/bin/python3" -m pip install -q --no-warn-script-location -r requirements/base.txt
    copy_common "$OUT"
    cp build-linux/bin/whisper-cli "$OUT/build-linux/bin/"
    cat > "$OUT/start.sh" <<'EOF'
#!/usr/bin/env bash
cd "$(dirname "$0")"
export APP_RELOAD=0 KMP_DUPLICATE_LIB_OK=TRUE
exec python/bin/python3 -m app.main
EOF
    chmod +x "$OUT/start.sh"
    tar -czf dist/AudioTranscrypt-linux.tar.gz -C dist AudioTranscrypt-linux
    echo "Built dist/AudioTranscrypt-linux.tar.gz"
fi

if [ "$TARGET" = windows ] || [ "$TARGET" = all ]; then
    OUT=dist/AudioTranscrypt-windows
    rm -rf "$OUT" && mkdir -p "$OUT/build-vulkan/bin/Release"
    fetch_python pc-windows-msvc "$OUT"
    # Cross-install Windows wheels from Linux; uvloop has no Windows wheel and is skipped by uvicorn on Windows anyway.
    grep -v '^uvicorn' requirements/base.txt > "$CACHE/requirements-win.txt"
    echo 'uvicorn>=0.35,<1.0' >> "$CACHE/requirements-win.txt"
    echo 'colorama' >> "$CACHE/requirements-win.txt"
    python3 -m pip install -q --target "$OUT/python/Lib/site-packages" \
        --platform win_amd64 --python-version 3.12 --implementation cp --only-binary=:all: \
        -r "$CACHE/requirements-win.txt"
    copy_common "$OUT"
    cp build-vulkan/bin/Release/whisper-cli.exe build-vulkan/bin/Release/*.dll "$OUT/build-vulkan/bin/Release/"
    # whisper-cli.exe is an MSVC build; ship the VC++ runtime app-locally so no redistributable install is needed.
    python3 -m pip download -q msvc-runtime==14.44.35112 --platform win_amd64 --python-version 3.12 \
        --only-binary=:all: --no-deps -d "$CACHE"
    unzip -qjo "$CACHE"/msvc_runtime-14.44.35112-*.whl 'msvc_runtime-14.44.35112.data/data/Scripts/*.dll' \
        -d "$OUT/build-vulkan/bin/Release/"
    printf '@echo off\r\ncd /d "%%~dp0"\r\nset "APP_RELOAD=0"\r\nset "KMP_DUPLICATE_LIB_OK=TRUE"\r\npython\\python.exe -m app.main\r\npause\r\n' > "$OUT/start.bat"
    rm -f dist/AudioTranscrypt-windows.zip
    (cd dist && zip -qr AudioTranscrypt-windows.zip AudioTranscrypt-windows)
    echo "Built dist/AudioTranscrypt-windows.zip"
fi
