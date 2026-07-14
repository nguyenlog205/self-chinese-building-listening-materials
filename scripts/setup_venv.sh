#!/usr/bin/env bash
# Creates .venv, installs the project, and wires LD_LIBRARY_PATH so
# faster-whisper's CUDA execution provider (libcublas/libcudnn, installed
# via the nvidia-cublas-cu12 / nvidia-cudnn-cu12 pip wheels) is found at
# runtime without a system-wide CUDA toolkit install.
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

python3 -m venv .venv
.venv/bin/pip install -q --upgrade pip
.venv/bin/pip install -q -e .

SITE_PACKAGES="$(.venv/bin/python -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])')"
CUDA_LD_LINE="export LD_LIBRARY_PATH=\"$SITE_PACKAGES/nvidia/cublas/lib:$SITE_PACKAGES/nvidia/cudnn/lib:\${LD_LIBRARY_PATH:-}\""

if ! grep -qF "nvidia/cudnn/lib" .venv/bin/activate; then
    printf '\n# Added by scripts/setup_venv.sh — required for faster-whisper GPU inference\n%s\n' "$CUDA_LD_LINE" >> .venv/bin/activate
fi

echo "Done. Run 'source .venv/bin/activate' before using the CLI or API."
