#!/usr/bin/env python3
"""
Geeta Shorts — one-command pipeline orchestrator.

Usage:
    python pipeline.py                 # run all steps
    python pipeline.py --from 4        # run from step 4 (images) to the end
    python pipeline.py --only 5        # run only step 5 (re-assemble video)
    python pipeline.py --steps 1 3 5   # run a specific set of steps

Steps:
    1  script      prepare / validate content/script.json
    2  tts         synthesize narration for scenes without audio (optional)
    3  transcribe  build caption timings from audio
    4  images      generate one image per scene
    5  assemble    render the final video(s)
"""
from __future__ import annotations
import argparse
import importlib
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "steps"))

STEPS = [
    (1, "script", "s1_script"),
    (2, "tts", "s2_tts"),
    (3, "transcribe", "s3_transcribe"),
    (4, "images", "s4_images"),
    (5, "assemble", "s5_assemble"),
]


def run_step(num, name, module):
    mod = importlib.import_module(module)
    print("\n" + "═" * 70)
    print(f"  STEP {num} — {name}")
    print("═" * 70)
    t0 = time.time()
    mod.main()
    print(f"  (step {num} took {time.time() - t0:.1f}s)")


def main():
    ap = argparse.ArgumentParser(description="Geeta Shorts pipeline")
    ap.add_argument("--from", dest="start", type=int, default=1,
                    help="run from this step number to the end")
    ap.add_argument("--only", type=int, help="run only this step")
    ap.add_argument("--steps", type=int, nargs="+",
                    help="run exactly these step numbers")
    args = ap.parse_args()

    if args.only:
        chosen = [s for s in STEPS if s[0] == args.only]
    elif args.steps:
        chosen = [s for s in STEPS if s[0] in set(args.steps)]
    else:
        chosen = [s for s in STEPS if s[0] >= args.start]

    if not chosen:
        sys.exit("No matching steps.")

    for num, name, module in chosen:
        run_step(num, name, module)

    print("\n✅ Pipeline finished. Check the 'output/' folder for your video(s).")


if __name__ == "__main__":
    main()
