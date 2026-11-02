#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/.."
export KMP_DUPLICATE_LIB_OK=TRUE

# Any Python 3.10+ works for setup; it creates .venv on the first run (Linux usually has no plain `python`).
if [ -x .venv/bin/python ]; then SYS_PY=.venv/bin/python
elif command -v python3 >/dev/null; then SYS_PY=python3
else SYS_PY=python
fi

printf '\nPreparing files (first run downloads ~600 MB and builds whisper.cpp)...\n'
"$SYS_PY" -m app.bootstrap

if [ -x .venv/bin/python ]; then PY=.venv/bin/python
else PY=.venv/Scripts/python.exe   # Git Bash on Windows
fi

printf '\nChecking environment...\n'
"$PY" -m app.verify

printf '\nStarting Local AI Transcription Studio...\n'
exec "$PY" -m app.main
