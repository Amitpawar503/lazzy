"""Shared helpers used by every step."""
from __future__ import annotations
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("Missing dependency 'pyyaml'. Run: pip install -r requirements.txt")

ROOT = Path(__file__).resolve().parent.parent


def load_config(path: str = "config.yaml") -> dict:
    p = (ROOT / path) if not os.path.isabs(path) else Path(path)
    with open(p, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_script(cfg: dict) -> dict:
    sp = ROOT / cfg["project"]["script"]
    if not sp.exists():
        sample = ROOT / "content" / "script.sample.json"
        sys.exit(
            f"Script not found: {sp}\n"
            f"Copy the sample to get started:\n"
            f"    cp {sample} {sp}"
        )
    with open(sp, "r", encoding="utf-8") as f:
        return json.load(f)


def work_dir(cfg: dict) -> Path:
    d = ROOT / cfg["project"]["work_dir"]
    d.mkdir(parents=True, exist_ok=True)
    return d


def scene_dir(cfg: dict, scene_id) -> Path:
    d = work_dir(cfg) / f"scene_{int(scene_id):02d}"
    d.mkdir(parents=True, exist_ok=True)
    return d


def resolve(path: str) -> Path:
    """Resolve a path from the config against the project root."""
    if not path:
        return None
    p = Path(path)
    return p if p.is_absolute() else (ROOT / p)


def have(binary: str) -> bool:
    return shutil.which(binary) is not None


def require_ffmpeg():
    if not have("ffmpeg") or not have("ffprobe"):
        sys.exit(
            "ffmpeg / ffprobe not found on PATH.\n"
            "  macOS:   brew install ffmpeg\n"
            "  Ubuntu:  sudo apt install ffmpeg\n"
            "  Windows: winget install Gyan.FFmpeg"
        )


def run(cmd: list[str], **kw):
    """Run a subprocess, echoing the command, raising on failure."""
    printable = " ".join(str(c) for c in cmd)
    print(f"  $ {printable[:400]}{'…' if len(printable) > 400 else ''}")
    return subprocess.run([str(c) for c in cmd], check=True, **kw)


def media_duration(path) -> float:
    """Return duration (seconds) of an audio/video file via ffprobe."""
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True,
    )
    try:
        return float(out.stdout.strip())
    except ValueError:
        return 0.0


def scene_audio(cfg: dict, sc: dict):
    """Return the Path to a scene's audio: the user-supplied file if given,
    otherwise the TTS narration.wav produced by step 2, else None."""
    if sc.get("audio"):
        p = resolve(sc["audio"])
        if p and p.exists():
            return p
    nar = scene_dir(cfg, sc["id"]) / "narration.wav"
    return nar if nar.exists() else None


def banner(title: str):
    print("\n" + "─" * 70)
    print(f"▶  {title}")
    print("─" * 70)
