#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/.."
export KMP_DUPLICATE_LIB_OK=TRUE

printf '\nChecking environment...\n'
python -m app.verify

printf '\nStarting Local AI Transcription Studio...\n'
exec python -m app.main
