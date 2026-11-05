"""
STEP 4 — Generate one image per scene.

Engines (set images.engine in config.yaml):
  • placeholder  — no download, draws a captioned gradient card. Use this to
                   test the full video pipeline instantly.
  • flux-schnell — FLUX.1-schnell (Apache-2.0, commercial use allowed). Best
                   quality, 1–4 steps, needs PyTorch (GPU recommended).
  • sdxl         — Stable Diffusion XL base (OpenRAIL++), a lighter fallback.

Output: scene_XX/image.png
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _util import load_config, load_script, scene_dir, banner

GEN_W, GEN_H = 1024, 1024  # base generation size; ffmpeg crops to each format


# ─────────────────────────── placeholder (no models) ─────────────────────────
def gen_placeholder(cfg, scenes):
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont
    palettes = [((18, 24, 64), (120, 72, 20)), ((40, 10, 50), (200, 140, 30)),
                ((10, 40, 40), (180, 120, 40)), ((30, 20, 60), (210, 90, 40))]
    try:
        font_big = ImageFont.truetype("DejaVuSans-Bold.ttf", 46)
        font_sm = ImageFont.truetype("DejaVuSans.ttf", 30)
    except Exception:
        font_big = ImageFont.load_default()
        font_sm = font_big
    for i, sc in enumerate(scenes):
        top, bot = palettes[i % len(palettes)]
        t = np.linspace(0.0, 1.0, GEN_H)[:, None]            # vertical gradient
        top_a = np.array(top, dtype=float)
        bot_a = np.array(bot, dtype=float)
        row = top_a[None, :] + (bot_a - top_a)[None, :] * t  # (H,3)
        arr = np.repeat(row[:, None, :], GEN_W, axis=1).astype("uint8")
        img = Image.fromarray(arr, "RGB")
        d = ImageDraw.Draw(img)
        ref = sc.get("verse_ref", f"Scene {sc['id']}")
        d.text((60, 80), f"॥ {ref} ॥", font=font_big, fill=(255, 230, 160))
        prompt = (sc.get("image_prompt") or sc.get("translation") or "")[:120]
        d.text((60, GEN_H - 160), prompt, font=font_sm, fill=(235, 235, 235))
        out = scene_dir(cfg, sc["id"]) / "image.png"
        img.save(out)
        print(f"  scene {sc['id']}: placeholder → {out.name}")


# ─────────────────────────── diffusers (FLUX / SDXL) ─────────────────────────
def pick_device(cfg):
    dev = cfg["images"].get("device", "auto")
    if dev != "auto":
        return dev
    try:
        import torch
        if torch.cuda.is_available():
            return "cuda"
        if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
            return "mps"
    except Exception:
        pass
    return "cpu"


def build_prompt(cfg, sc):
    base = sc.get("image_prompt") or sc.get("translation") or sc.get("verse_ref", "")
    suffix = " ".join((cfg["images"].get("style_suffix") or "").split())
    return f"{base}, {suffix}" if suffix else base


def gen_diffusers(cfg, scenes, engine):
    import torch
    device = pick_device(cfg)
    dtype = torch.float16 if device in ("cuda", "mps") else torch.float32
    low_vram = bool(cfg["images"].get("low_vram", True))
    steps = int(cfg["images"]["steps"])
    guidance = float(cfg["images"]["guidance"])
    seed = int(cfg["images"].get("seed", 42))
    neg = " ".join((cfg["images"].get("negative_prompt") or "").split())

    print(f"  engine={engine} device={device} dtype={dtype} low_vram={low_vram}")
    if engine == "flux-schnell":
        from diffusers import FluxPipeline
        pipe = FluxPipeline.from_pretrained(cfg["images"]["flux_model"],
                                            torch_dtype=dtype)
    else:  # sdxl
        from diffusers import StableDiffusionXLPipeline
        pipe = StableDiffusionXLPipeline.from_pretrained(
            cfg["images"]["sdxl_model"], torch_dtype=dtype,
            use_safetensors=True)
        if steps < 20:
            steps, guidance = 28, 6.0  # SDXL needs more steps than schnell

    if low_vram and device == "cuda":
        pipe.enable_model_cpu_offload()
    else:
        pipe = pipe.to(device)

    for sc in scenes:
        prompt = build_prompt(cfg, sc)
        gen = torch.Generator(device="cpu").manual_seed(seed + int(sc["id"]))
        print(f"  scene {sc['id']}: generating…  \"{prompt[:70]}…\"")
        kw = dict(prompt=prompt, width=GEN_W, height=GEN_H,
                  num_inference_steps=steps, generator=gen)
        if engine == "flux-schnell":
            kw["guidance_scale"] = guidance
        else:
            kw["guidance_scale"] = guidance
            kw["negative_prompt"] = neg
        image = pipe(**kw).images[0]
        out = scene_dir(cfg, sc["id"]) / "image.png"
        image.save(out)
        print(f"    → {out.name}")


def main():
    cfg = load_config()
    scenes = load_script(cfg)["scenes"]
    engine = cfg["images"]["engine"]
    if engine == "placeholder":
        gen_placeholder(cfg, scenes)
    elif engine in ("flux-schnell", "sdxl"):
        try:
            import torch  # noqa
        except ImportError:
            sys.exit("PyTorch not installed. Install it for your platform from "
                     "https://pytorch.org/get-started/locally/ then "
                     "`pip install -r requirements.txt`.\n"
                     "Tip: set images.engine: placeholder to test without models.")
        gen_diffusers(cfg, scenes, engine)
    else:
        sys.exit(f"Unknown images.engine: {engine}")
    print(f"✓ images ready for {len(scenes)} scene(s)")


if __name__ == "__main__":
    banner("STEP 4 — Generate images")
    main()
