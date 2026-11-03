#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/.."
export KMP_DUPLICATE_LIB_OK=TRUE

# Any Python 3.10+ works for setup; it creates .venv on the first run (Linux usually has no plain `python`).
if [ -x .venv/bin/python ]; then SYS_PY=.venv/bin/python
elif command -v python3 >/dev/null; then SYS_PY=python3
else SYS_PY=python
fi

# First run on Debian/Ubuntu: install missing system packages (asks for the sudo password once).
APT_PKGS="python3-venv git build-essential cmake libvulkan-dev glslc mesa-vulkan-drivers"
if [ ! -x build-linux/bin/whisper-cli ] && command -v apt-get >/dev/null && command -v dpkg >/dev/null; then
    MISSING=""
    for pkg in $APT_PKGS; do dpkg -s "$pkg" >/dev/null 2>&1 || MISSING="$MISSING $pkg"; done
    if [ -n "$MISSING" ]; then
        printf '\nInstalling system packages:%s\n' "$MISSING"
        sudo apt-get update && sudo apt-get install -y $MISSING
    fi
fi

printf '\nPreparing files (first run downloads ~650 MB and builds whisper.cpp)...\n'
"$SYS_PY" -m app.bootstrap

if [ -x .venv/bin/python ]; then PY=.venv/bin/python
else PY=.venv/Scripts/python.exe   # Git Bash on Windows
fi

printf '\nChecking environment...\n'
"$PY" -m app.verify

printf '\nStarting Local AI Transcription Studio...\n'
exec "$PY" -m app.main
