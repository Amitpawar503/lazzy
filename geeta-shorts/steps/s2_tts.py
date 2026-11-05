"""
STEP 2 — Narration audio (OPTIONAL).

For every scene that does NOT already point to a pre-recorded `audio` file,
synthesize narration with Kokoro TTS (Apache-2.0, free, runs on CPU) and save
it as scene_XX/narration.wav.

If you recorded your own voice for every scene, set `tts.engine: none` in
config.yaml and skip this step — the pipeline will just use your files.
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _util import load_config, load_script, scene_dir, resolve, banner


def synth_kokoro(cfg, scenes):
    try:
        import soundfile as sf
        from kokoro import KPipeline
    except ImportError:
        sys.exit("Kokoro not installed. Run: pip install kokoro soundfile\n"
                 "Or set tts.engine: none and supply your own audio files.")

    lang = cfg["tts"]["lang"]
    voice = cfg["tts"]["voice"]
    speed = float(cfg["tts"].get("speed", 1.0))
    pipeline = KPipeline(lang_code=lang)

    for sc in scenes:
        if sc.get("audio"):
            continue  # user supplied their own audio
        text = (sc.get("narration") or "").strip()
        if not text:
            continue
        out = scene_dir(cfg, sc["id"]) / "narration.wav"
        print(f"  scene {sc['id']}: TTS → {out.name}")
        import numpy as np
        chunks = [audio for _, _, audio in pipeline(text, voice=voice, speed=speed)]
        if not chunks:
            continue
        audio = np.concatenate(chunks) if len(chunks) > 1 else chunks[0]
        sf.write(str(out), audio, 24000)
        sc["audio"] = str(out)  # in-memory only; s3/s5 resolve per scene anyway


def main():
    cfg = load_config()
    if cfg["tts"]["engine"] == "none":
        print("  tts.engine = none → skipping (using your recorded audio).")
        return
    script = load_script(cfg)
    scenes = script["scenes"]
    needing = [s for s in scenes if not s.get("audio") and s.get("narration")]
    if not needing:
        print("  Every scene already has audio — nothing to synthesize.")
        return
    synth_kokoro(cfg, scenes)
    print(f"✓ narration generated for {len(needing)} scene(s)")


if __name__ == "__main__":
    banner("STEP 2 — Text-to-speech (optional)")
    main()
