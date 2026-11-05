"""
STEP 3 — Caption timing from audio.

Runs faster-whisper (MIT) on each scene's audio to get time-aligned text, then
writes scene_XX/captions.json as a list of {start, end, text} segments (times
are relative to the start of that scene's audio).

These captions are burned onto the video in step 5. Skipped entirely if
captions.enabled is false.
"""
from __future__ import annotations
import json
import sys
import textwrap
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _util import load_config, load_script, scene_dir, scene_audio, banner


def pick_device(cfg):
    dev = cfg["transcribe"].get("device", "auto")
    comp = cfg["transcribe"].get("compute_type", "auto")
    if dev == "auto" or comp == "auto":
        try:
            import torch
            if torch.cuda.is_available():
                return ("cuda" if dev == "auto" else dev,
                        "float16" if comp == "auto" else comp)
        except Exception:
            pass
        return ("cpu" if dev == "auto" else dev,
                "int8" if comp == "auto" else comp)
    return dev, comp


def split_segment(text, start, end, max_chars):
    """Break one long whisper segment into readable caption lines, spreading
    the time range proportionally so subtitles don't sit too long on screen."""
    text = text.strip()
    if not text:
        return []
    lines = textwrap.wrap(text, width=max_chars) or [text]
    total = max(len(text), 1)
    out, cursor = [], start
    span = max(end - start, 0.01)
    for ln in lines:
        frac = len(ln) / total
        seg_end = min(cursor + span * frac, end)
        out.append({"start": round(cursor, 3), "end": round(seg_end, 3),
                    "text": ln})
        cursor = seg_end
    out[-1]["end"] = round(end, 3)
    return out


def main():
    cfg = load_config()
    if not cfg["captions"]["enabled"]:
        print("  captions.enabled = false → skipping transcription.")
        return
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        sys.exit("faster-whisper not installed. Run: pip install faster-whisper")

    script = load_script(cfg)
    device, compute = pick_device(cfg)
    print(f"  loading whisper '{cfg['transcribe']['model']}' on {device}/{compute} …")
    model = WhisperModel(cfg["transcribe"]["model"], device=device,
                         compute_type=compute)
    lang = cfg["transcribe"].get("language") or None
    max_chars = int(cfg["captions"]["max_chars"])

    for sc in script["scenes"]:
        apath = scene_audio(cfg, sc)
        out = scene_dir(cfg, sc["id"]) / "captions.json"
        if not apath:
            out.write_text("[]", encoding="utf-8")
            print(f"  scene {sc['id']}: no audio → empty captions")
            continue
        print(f"  scene {sc['id']}: transcribing {apath.name} …")
        segments, _ = model.transcribe(str(apath), language=lang,
                                       vad_filter=True, word_timestamps=False)
        caps = []
        for s in segments:
            caps.extend(split_segment(s.text, s.start, s.end, max_chars))
        out.write_text(json.dumps(caps, ensure_ascii=False, indent=2),
                       encoding="utf-8")
        print(f"    → {len(caps)} caption line(s)")

    print("✓ captions written")


if __name__ == "__main__":
    banner("STEP 3 — Transcribe for captions")
    main()
