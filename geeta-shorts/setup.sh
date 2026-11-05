#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# Geeta Shorts — one-time setup (Linux / macOS).
# Creates a virtualenv and installs the free/open-source dependencies.
# ─────────────────────────────────────────────────────────────────────────────
set -e
cd "$(dirname "$0")"

echo "▶ 1/5  Checking ffmpeg …"
if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "  ✗ ffmpeg not found. Install it, then re-run:"
  echo "      macOS:  brew install ffmpeg"
  echo "      Ubuntu: sudo apt update && sudo apt install -y ffmpeg fonts-noto"
  exit 1
fi
echo "  ✓ ffmpeg found: $(command -v ffmpeg)"

echo "▶ 2/5  Creating virtualenv (.venv) …"
python3 -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install --upgrade pip wheel >/dev/null

echo "▶ 3/5  Installing core + caption + video deps …"
pip install pyyaml pillow numpy faster-whisper requests

echo "▶ 4/5  Image generation (PyTorch + diffusers) — OPTIONAL but recommended."
echo "        Install PyTorch for YOUR hardware from https://pytorch.org first."
read -r -p "        Install diffusers/transformers now? [y/N] " ans
if [[ "$ans" =~ ^[Yy]$ ]]; then
  pip install diffusers transformers accelerate sentencepiece protobuf
fi

echo "▶ 5/5  Text-to-speech (Kokoro) — OPTIONAL (only if you want generated narration)."
read -r -p "        Install Kokoro TTS now? [y/N] " ans
if [[ "$ans" =~ ^[Yy]$ ]]; then
  pip install kokoro soundfile
fi

echo
echo "✅ Setup done. Next:"
echo "   source .venv/bin/activate"
echo "   # test the video pipeline instantly (no model downloads):"
echo "   #   images.engine is 'placeholder' by default in config.yaml"
echo "   python pipeline.py --steps 4 5"
echo "   # then switch config.yaml images.engine -> flux-schnell and run all:"
echo "   python pipeline.py"
