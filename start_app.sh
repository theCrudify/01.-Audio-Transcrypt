#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
exec bash scripts/start_app.sh "$@"
