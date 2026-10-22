#!/usr/bin/env bash
# Builds whisper.cpp with Vulkan for Linux into build-linux/ (Windows uses the prebuilt build-vulkan/).
# Needs: cmake, a C++ compiler, Vulkan headers + glslc (Debian/Ubuntu: sudo apt install libvulkan-dev glslc).
set -e

cd "$(dirname "$0")/.."
cmake -S third_party/whisper.cpp-amd -B build-linux -DGGML_VULKAN=1 -DCMAKE_BUILD_TYPE=Release
cmake --build build-linux -j --config Release --target whisper-cli
