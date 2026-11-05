"""
STEP 1 — Prepare the scene script.

Validates content/script.json. If `llm.enabled` is true, it will use a LOCAL
Ollama model to fill in any MISSING `narration` or `image_prompt` fields from
the verse/translation you provide.

IMPORTANT: The sacred verses (sanskrit / transliteration / translation) are
NEVER auto-generated — always type them from an authentic source. The LLM is
only used to suggest a narration line or an image description.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _util import load_config, load_script, banner, ROOT


def ollama_complete(cfg, prompt: str) -> str:
    import requests
    r = requests.post(
        f"{cfg['llm']['host']}/api/generate",
        json={"model": cfg["llm"]["model"], "prompt": prompt, "stream": False},
        timeout=120,
    )
    r.raise_for_status()
    return r.json().get("response", "").strip()


def main():
    cfg = load_config()
    script = load_script(cfg)
    scenes = script.get("scenes", [])
    if not scenes:
        sys.exit("script.json has no 'scenes'.")

    use_llm = cfg.get("llm", {}).get("enabled", False)
    changed = False

    for sc in scenes:
        sid = sc.get("id")
        # Validate essentials
        if "id" not in sc:
            sys.exit("Every scene needs an 'id'.")
        sc.setdefault("narration", "")
        sc.setdefault("image_prompt", "")
        sc.setdefault("audio", "")

        if use_llm and (not sc["narration"] or not sc["image_prompt"]):
            context = (sc.get("translation") or sc.get("transliteration")
                       or sc.get("sanskrit") or "").strip()
            if not sc["narration"] and context:
                sc["narration"] = ollama_complete(
                    cfg,
                    "Write ONE short, devotional narration line (<=20 words) in "
                    f"the language of this text, for a Bhagavad Gita video. "
                    f"Return only the line.\nText: {context}")
                changed = True
                print(f"  scene {sid}: narration ← LLM")
            if not sc["image_prompt"] and context:
                sc["image_prompt"] = ollama_complete(
                    cfg,
                    "Write ONE vivid English image-generation prompt (<=30 words, "
                    "no camera brand, no text in image) depicting this Bhagavad "
                    f"Gita idea. Return only the prompt.\nText: {context}")
                changed = True
                print(f"  scene {sid}: image_prompt ← LLM")

        # Final sanity: a scene needs either narration text or an audio file.
        if not sc["narration"] and not sc["audio"]:
            print(f"  ⚠ scene {sid}: no narration and no audio — it will be silent.")
        if not sc["image_prompt"]:
            print(f"  ⚠ scene {sid}: no image_prompt — a plain card will be used.")

    if changed:
        out = ROOT / cfg["project"]["script"]
        with open(out, "w", encoding="utf-8") as f:
            json.dump(script, f, ensure_ascii=False, indent=2)
        print(f"  saved enriched script → {out}")

    print(f"✓ {len(scenes)} scene(s) ready: \"{script.get('title','(untitled)')}\"")


if __name__ == "__main__":
    banner("STEP 1 — Prepare script")
    main()
