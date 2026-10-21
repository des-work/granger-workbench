#!/usr/bin/env bash
# Explicitly installs the Python runtime only; no model or voice downloads.
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
"${PCSTUDIO_PYTHON:-python3}" -m venv "$root/.venv"
"$root/.venv/bin/python" -m pip install -r "$root/requirements.txt" -r "$root/requirements-pcstudio.txt"
if [[ "${1:-}" == "--voice" ]]; then
  "$root/.venv/bin/python" -m pip install -r "$root/requirements-voice.txt"
fi
echo "Runtime ready. Configure local models and optional tools; see docs/SETUP.md."
