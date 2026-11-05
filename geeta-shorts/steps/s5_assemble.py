"""
STEP 5 — Assemble the final video(s) with FFmpeg.

For each output format (shorts 1080x1920 and/or long 1920x1080):
  1. turn each scene's still image into a moving clip (Ken Burns zoom/pan),
  2. burn that scene's captions (ASS subtitles) onto it,
  3. attach the scene's audio (your recording or the TTS narration),
  4. concatenate all scenes,
  5. mix background music softly underneath.

Only dependency is ffmpeg/ffprobe — no Python media libraries, so this step is
very robust across machines.

Output: output/<project>_shorts.mp4 and/or output/<project>_long.mp4
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _util import (load_config, load_script, work_dir, scene_dir, scene_audio,
                   resolve, require_ffmpeg, run, media_duration, banner)

DEFAULT_SCENE_SECONDS = 5.0


# ──────────────────────────────── captions (ASS) ─────────────────────────────
def ass_time(t: float) -> str:
    t = max(t, 0.0)
    h = int(t // 3600); t -= h * 3600
    m = int(t // 60); t -= m * 60
    s = int(t); cs = int(round((t - s) * 100))
    if cs == 100:
        s += 1; cs = 0
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def write_ass(caps, path: Path, cfg, W, H, fmt):
    c = cfg["captions"]
    size = c["shorts_size"] if fmt == "shorts" else c["long_size"]
    margin_v = c["margin_v_shorts"] if fmt == "shorts" else c["margin_v_long"]
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour, Bold, Italic, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{c['font']},{size},{c['primary_color']},{c['outline_color']},&H64000000,1,0,1,{c['outline']},1,2,60,60,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = []
    for seg in caps:
        txt = str(seg.get("text", "")).replace("\n", " ").strip()
        if not txt:
            continue
        lines.append(f"Dialogue: 0,{ass_time(seg['start'])},{ass_time(seg['end'])},"
                     f"Default,,0,0,0,,{txt}")
    path.write_text(header + "\n".join(lines) + "\n", encoding="utf-8")


# ─────────────────────────────── scene clip ──────────────────────────────────
def build_scene_clip(cfg, sc, fmt, W, H, fps, motion, out_path):
    sdir = scene_dir(cfg, sc["id"])
    image = sdir / "image.png"
    if not image.exists():
        sys.exit(f"Missing image for scene {sc['id']}: run step 4 first ({image})")

    apath = scene_audio(cfg, sc)
    if apath:
        dur = media_duration(apath)
    else:
        dur = float(sc.get("duration", DEFAULT_SCENE_SECONDS))
    dur = max(dur, 0.8)
    frames = int(round(dur * fps))

    # captions
    caps = []
    cj = sdir / "captions.json"
    if cfg["captions"]["enabled"] and cj.exists():
        caps = json.loads(cj.read_text(encoding="utf-8"))
    ass_name = f"captions_{fmt}.ass"
    if caps:
        write_ass(caps, sdir / ass_name, cfg, W, H, fmt)

    # Ken Burns chain (built inline so we control fps/frames exactly)
    iw, ih = W * 2, H * 2
    cx, cy = "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
    if motion == "zoom_in":
        z, x, y = f"min(1+0.25*on/{frames},1.25)", cx, cy
    elif motion == "zoom_out":
        z = f"if(eq(on,0),1.25,max(1.25-0.25*on/{frames},1.0))"; x, y = cx, cy
    elif motion == "pan_left":
        z, x, y = "1.2", f"(iw-iw/zoom)*(1-on/{frames})", cy
    else:
        z, x, y = "1.2", f"(iw-iw/zoom)*on/{frames}", cy

    vf = (f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,"
          f"crop={W}:{H},scale={iw}:{ih},"
          f"zoompan=z='{z}':x='{x}':y='{y}':d={frames}:s={W}x{H}:fps={fps},"
          f"trim=duration={dur:.3f},setsar=1")
    if caps:
        vf += f",ass={ass_name}"   # relative → we run ffmpeg with cwd=sdir
    vf += "[v]"

    cmd = ["ffmpeg", "-y", "-loop", "1", "-i", str(image.resolve())]
    if apath:
        cmd += ["-i", str(apath.resolve())]
    else:
        cmd += ["-f", "lavfi", "-t", f"{dur:.3f}",
                "-i", "anullsrc=channel_layout=stereo:sample_rate=44100"]
    cmd += [
        "-filter_complex", vf,
        "-map", "[v]", "-map", "1:a",
        "-t", f"{dur:.3f}",
        "-r", str(fps), "-pix_fmt", "yuv420p",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-c:a", "aac", "-ar", "44100", "-ac", "2",
        str(out_path.resolve()),
    ]
    run(cmd, cwd=str(sdir))
    return dur


# ──────────────────────────── format assembly ────────────────────────────────
def assemble_format(cfg, script, fmt):
    dims = cfg["video"][fmt]
    W, H = int(dims["width"]), int(dims["height"])
    fps = int(cfg["video"]["fps"])
    motions = cfg["video"]["motion"]
    wd = work_dir(cfg)
    tmp = wd / f"_clips_{fmt}"
    tmp.mkdir(parents=True, exist_ok=True)

    print(f"\n  building {fmt} ({W}x{H}) …")
    clips = []
    for i, sc in enumerate(script["scenes"]):
        motion = motions[i % len(motions)]
        clip = tmp / f"scene_{int(sc['id']):02d}.mp4"
        build_scene_clip(cfg, sc, fmt, W, H, fps, motion, clip)
        clips.append(clip)

    # concat
    listfile = tmp / "concat.txt"
    listfile.write_text("".join(f"file '{c.resolve()}'\n" for c in clips),
                        encoding="utf-8")
    body = tmp / "body.mp4"
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(listfile),
         "-c", "copy", str(body)])

    # background music (optional)
    music = resolve(cfg["audio"].get("music"))
    final = wd / f"{cfg['project']['name']}_{fmt}.mp4"
    if music and music.exists():
        mv = float(cfg["audio"]["music_volume"])
        nv = float(cfg["audio"]["narration_volume"])
        fc = (f"[1:a]volume={mv},aresample=44100[m];"
              f"[0:a]volume={nv}[n];"
              f"[n][m]amix=inputs=2:duration=first:dropout_transition=0[a]")
        run(["ffmpeg", "-y", "-i", str(body),
             "-stream_loop", "-1", "-i", str(music),
             "-filter_complex", fc, "-map", "0:v", "-map", "[a]",
             "-c:v", "copy", "-c:a", "aac", "-ar", "44100", "-shortest",
             str(final)])
    else:
        if music:
            print(f"  (music file not found at {music} — skipping music)")
        run(["ffmpeg", "-y", "-i", str(body), "-c", "copy", str(final)])

    print(f"  ✓ {final}")
    return final


def main():
    require_ffmpeg()
    cfg = load_config()
    script = load_script(cfg)
    if not script.get("scenes"):
        sys.exit("No scenes in script.json")
    outputs = []
    for fmt in cfg["video"]["formats"]:
        if fmt not in ("shorts", "long"):
            print(f"  (unknown format '{fmt}' — skipping)")
            continue
        outputs.append(assemble_format(cfg, script, fmt))
    print("\n✓ DONE. Final video(s):")
    for o in outputs:
        print(f"   • {o}")


if __name__ == "__main__":
    banner("STEP 5 — Assemble video")
    main()
