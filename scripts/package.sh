#!/usr/bin/env bash
# Maintainer only: builds dist/whisper-vulkan-windows-x64.zip, the asset app/bootstrap.py downloads on Windows
# (upload it to the GitHub Release, see README). It contains only whisper.cpp (MIT) and its license text;
# the Microsoft VC++ runtime is NOT bundled, users install it from Microsoft (bootstrap checks for it).
set -e

cd "$(dirname "$0")/.."
SRC=build-vulkan/bin/Release
[ -f "$SRC/whisper-cli.exe" ] || { echo "Missing $SRC/whisper-cli.exe"; exit 1; }
[ -f third_party/whisper.cpp-amd/LICENSE ] || { echo "Missing third_party/whisper.cpp-amd/LICENSE (run: python3 -m app.bootstrap)"; exit 1; }

STAGE=dist/.whisper-windows
rm -rf "$STAGE" dist/whisper-vulkan-windows-x64.zip && mkdir -p "$STAGE"
cp "$SRC"/whisper-cli.exe "$SRC"/whisper.dll "$SRC"/ggml.dll "$SRC"/ggml-base.dll "$SRC"/ggml-cpu.dll "$SRC"/ggml-vulkan.dll "$STAGE/"
cp third_party/whisper.cpp-amd/LICENSE "$STAGE/LICENSE-whisper.cpp.txt"
(cd "$STAGE" && zip -qX -9 ../whisper-vulkan-windows-x64.zip ./*)
rm -rf "$STAGE"
echo "Built dist/whisper-vulkan-windows-x64.zip sha256=$(sha256sum dist/whisper-vulkan-windows-x64.zip | cut -d' ' -f1)"
