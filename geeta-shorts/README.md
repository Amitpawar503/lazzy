# 🕉️ Geeta Shorts — zero-cost Bhagavad Gita video generator

Generate **YouTube Shorts & long videos** about the Bhagavad Gita entirely on
your **local machine**, using only **free, open-source models**. No paid APIs,
no credits, no sign-ups. You bring the **text** (story + shlokas) and optionally
the **audio**; the scripts generate **images**, (optionally) **narration**, and
assemble the final **video** with motion + burned-in captions.

> **Note on the Claude "Bhagwat Geeta" project:** this coding session can only
> see this git repo, not your Claude.ai *Project*, so this is a clean,
> self-contained pipeline built from your description. Copy this `geeta-shorts/`
> folder to your local machine and run it there (image/TTS models need to
> download multi-GB weights and run best on your own GPU/CPU).

---

## What it does (the pipeline)

```
content/script.json  ──▶  [1] prepare script
  (your verses,            [2] TTS narration   (Kokoro — only for scenes with no audio)
   narration,              [3] transcribe       (faster-whisper → caption timings)
   image prompts)          [4] generate images  (FLUX.1-schnell / SDXL)
                           [5] assemble video    (FFmpeg: Ken Burns + captions + music)
                                   │
                                   ▼
                     output/geeta-shorts_shorts.mp4   (1080×1920, YouTube Shorts)
                     output/geeta-shorts_long.mp4     (1920×1080, normal video)
```

## The tools — all open-source, all free

| Need | Tool | License | Runs on |
|------|------|---------|---------|
| **Images** from text | **FLUX.1-schnell** (primary) | Apache-2.0 — **commercial OK** | GPU (best), CPU (slow) |
| Images (fallback) | **SDXL base** | OpenRAIL++ | GPU / CPU |
| Images (instant test) | **placeholder** (built-in) | — | anything |
| **Narration** (optional) | **Kokoro TTS** | Apache-2.0 — commercial OK | CPU |
| **Caption timing** from your audio | **faster-whisper** | MIT | CPU / GPU |
| **Video** (motion, captions, music) | **FFmpeg** | LGPL/GPL | anything |
| Story expansion (optional) | **Ollama** (Qwen/Llama/Gemma) | permissive | local |

> ⚠️ Do **not** use FLUX.1-**dev** or SD3.x for monetized videos — those have
> non-commercial licenses. This pipeline defaults to the **commercial-safe**
> FLUX.1-schnell and SDXL.

---

## Install (one time)

**Requirements:** Python 3.9+, `ffmpeg`, and (for AI images) PyTorch.

```bash
cd geeta-shorts
bash setup.sh          # creates .venv and installs deps (asks before big ones)
```

Or manually:

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# PyTorch is installed SEPARATELY for your hardware — pick the right command at
# https://pytorch.org/get-started/locally/   e.g. CPU-only:
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

**ffmpeg** (system package):
- macOS: `brew install ffmpeg`
- Ubuntu/Debian: `sudo apt install ffmpeg fonts-noto`
- Windows: `winget install Gyan.FFmpeg`

---

## Quick start — see a video in 30 seconds (no model download)

`config.yaml` ships with `images.engine: placeholder`, so you can test the whole
video assembly immediately:

```bash
source .venv/bin/activate
python pipeline.py --steps 4 5
# ▶ output/geeta-shorts_shorts.mp4  and  output/geeta-shorts_long.mp4
```

Then switch to real AI images and run everything:

```bash
# edit config.yaml →  images.engine: flux-schnell
python pipeline.py
```

---

## Running individual steps

```bash
python pipeline.py              # all steps
python pipeline.py --from 4     # from images to the end
python pipeline.py --only 5     # just re-assemble (after tweaking captions/music)
python pipeline.py --steps 1 4 5

# or run a step directly:
python steps/s4_images.py
```

---

## How YOU provide content → `content/script.json`

Each **scene** = one image + its narration/audio + its caption. Edit
`content/script.json` (a ready example is in `content/script.sample.json`):

```json
{
  "title": "Bhagavad Gita — Nishkam Karma",
  "language": "hi",
  "scenes": [
    {
      "id": 1,
      "verse_ref": "2.47",
      "sanskrit": "कर्मण्येवाधिकारस्ते ...",
      "transliteration": "karmaṇy-evādhikāras te ...",
      "translation": "You have a right to perform your duty ...",
      "narration": "तेरा अधिकार केवल कर्म पर है, फल पर कभी नहीं।",
      "image_prompt": "a farmer sowing seeds at sunrise, selfless action",
      "audio": ""
    }
  ]
}
```

- **`narration`** — text to speak. Leave `audio` empty → step 2 (Kokoro) voices it.
- **`audio`** — path to YOUR recording for this scene (`"my_voice/scene1.wav"`).
  If set, it's used as-is and the scene's length = that clip's length.
- **`image_prompt`** — what to draw. A global `style_suffix` in config keeps a
  consistent look across scenes.
- **`duration`** (optional) — seconds, only used when a scene has no audio.

### Using the audio you already have
Two easy options:
1. **One file per scene** — put the path in each scene's `audio`. Cleanest; scene
   timing comes straight from your clips. Set `tts.engine: none`.
2. **Generate narration** — leave `audio` empty, set your text in `narration`,
   and let Kokoro voice it (Hindi voice `hf_alpha` by default).

> 🔱 **About the shlokas:** always type the Sanskrit/translation from an
> **authentic source**. The optional local LLM (`llm.enabled`) only drafts a
> *narration line* or an *image prompt* — never the sacred verse text.

---

## Fonts (important for Hindi/Devanagari captions)

libass renders captions using a font **family name** (`captions.font` in config).
For Devanagari you need a font that contains those glyphs:

- **Ubuntu/Debian:** `sudo apt install fonts-noto` → use `"Noto Sans Devanagari"`
- **macOS:** Devanagari MN is built in, or install Noto from Google Fonts
- **Windows:** "Nirmala UI" is built in → set `font: "Nirmala UI"`

If captions show as ▯ boxes, the chosen font lacks those glyphs — install Noto
and set `captions.font: "Noto Sans Devanagari"`. (Romanized/English captions work
with the universal `"DejaVu Sans"`.)

---

## Hardware notes

- **No GPU?** Set `images.engine: sdxl` is still heavy on CPU. For CPU-only,
  FLUX-schnell at 4 steps is slow (minutes/image) but works; or keep
  `placeholder` and drop in your own images (`scene_XX/image.png`).
- **GPU < 16 GB VRAM:** keep `images.low_vram: true` (enables CPU offload).
- **Apple Silicon:** `images.device: mps`.
- faster-whisper auto-uses `int8` on CPU, `float16` on CUDA.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `ffmpeg not found` | install ffmpeg (see above) |
| Captions are ▯ boxes | install a Devanagari font, set `captions.font` |
| `PyTorch not installed` | install torch from pytorch.org, or use `placeholder` |
| FLUX download huge / slow | first run downloads ~20 GB once; then cached |
| Out of VRAM | `low_vram: true`, lower resolution, or use `placeholder`/SDXL |
| Kokoro error | `pip install kokoro soundfile`, or `tts.engine: none` + own audio |
| Video too long/short | scene length follows the audio; or set `duration` |

---

## File map

```
geeta-shorts/
├── config.yaml                 ← edit everything here
├── pipeline.py                 ← orchestrator (run this)
├── requirements.txt
├── setup.sh
├── content/
│   ├── script.json             ← YOUR scenes (verses, narration, prompts)
│   └── script.sample.json      ← reference example
├── assets/music/               ← drop bg.mp3 here (optional)
├── output/                     ← generated images + final videos
└── steps/
    ├── s1_script.py            ← validate / LLM-enrich script
    ├── s2_tts.py               ← Kokoro narration (optional)
    ├── s3_transcribe.py        ← faster-whisper caption timing
    ├── s4_images.py            ← FLUX / SDXL / placeholder images
    └── s5_assemble.py          ← FFmpeg Ken Burns + captions + music
```

Everything here is free and runs locally. 🙏
