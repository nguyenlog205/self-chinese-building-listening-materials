#!/usr/bin/env bash
# Creates the backend venv on first run, then launches the API server.
# Prints "READY <port>" to stdout once listening — Electron's main process
# watches for this line.
set -euo pipefail

BACKEND_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$BACKEND_DIR/.venv"

if [ ! -d "$VENV_DIR" ]; then
  echo "Setting up backend virtual environment (first run only)..." >&2
  python3 -m venv "$VENV_DIR"
  "$VENV_DIR/bin/pip" install --upgrade pip >&2
  "$VENV_DIR/bin/pip" install -e "$BACKEND_DIR" >&2
fi

exec "$VENV_DIR/bin/python" -m listening_backend.main
