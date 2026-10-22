#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/.."
export KMP_DUPLICATE_LIB_OK=TRUE

# Prefer the project venv, then python3 (Linux usually has no plain `python`).
if [ -x .venv/bin/python ]; then PY=.venv/bin/python
elif [ -x .venv/Scripts/python.exe ]; then PY=.venv/Scripts/python.exe
elif command -v python3 >/dev/null; then PY=python3
else PY=python
fi

printf '\nChecking environment...\n'
"$PY" -m app.verify

printf '\nStarting Local AI Transcription Studio...\n'
exec "$PY" -m app.main
