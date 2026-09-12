"""Burn overlay text onto a base clip and write an MP4.

Mirrors the real pipeline: a real creator's silent reaction clip (base/*.mp4) + text burned on.
If base/ is empty, falls back to an animated version of the still frame (slow push-in), so there
is always a playable file.

    from video import render_mp4
    render_mp4("overlay text", Path("out/brand/post.mp4"), brand="brand")
"""

from __future__ import annotations

import random
import subprocess
import textwrap
from pathlib import Path

import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).parent
BASE_DIR = ROOT / "base"
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
W, H = 1080, 1920


def _font(size: int) -> ImageFont.FreeTypeFont:
    for p in (r"C:\Windows\Fonts\arialbd.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(p, size)
        except OSError:
            continue
    return ImageFont.load_default()


def text_layer(text: str, path: Path, brand: str = "") -> Path:
    """Transparent PNG of the overlay text, TikTok-style: white bold, black stroke, centred block."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    font = _font(58)
    lines = []
    for para in text.split("\n"):
        lines += textwrap.wrap(para, width=30) or [""]
    line_h = 76
    y = (H - line_h * len(lines)) // 2 - 80  # sit slightly above centre, where creators put it
    for ln in lines:
        d.text((W // 2, y), ln, font=font, fill="white", anchor="ma", stroke_width=6, stroke_fill="black")
        y += line_h
    if brand:
        d.text((W // 2, 120), f"@{brand}", fill=(230, 230, 230, 200), font=_font(34), anchor="mm",
               stroke_width=3, stroke_fill=(0, 0, 0, 160))
    img.save(path)
    return path


def read_time(text: str) -> float:
    """Seconds a viewer needs: ~2.6 words/s reading pace, plus a beat, clamped for the platform."""
    return max(8.0, min(20.0, len(text.split()) / 2.6 + 2.5))


def pick_base() -> Path | None:
    clips = sorted(p for p in BASE_DIR.glob("*") if p.suffix.lower() in (".mp4", ".mov", ".m4v", ".webm"))
    return random.choice(clips) if clips else None


def render_mp4(text: str, out: Path, brand: str = "", still: Path | None = None) -> tuple[Path, str]:
    """Returns (path, how): how is 'base clip <name>' or 'animated still'."""
    out.parent.mkdir(parents=True, exist_ok=True)
    layer = text_layer(text, out.with_suffix(".overlay.png"), brand)
    dur = read_time(text)
    base = pick_base()
    if base is not None:
        # scale/crop the phone clip to 9:16, loop it if shorter than the read time, burn the layer on
        vf = (f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1[bg];"
              f"[bg][1:v]overlay=0:0:format=auto,format=yuv420p[v]")
        cmd = [FFMPEG, "-y", "-stream_loop", "-1", "-i", str(base), "-i", str(layer),
               "-filter_complex", vf, "-map", "[v]", "-t", f"{dur:.1f}", "-r", "30",
               "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-an", str(out)]
        how = f"base clip {base.name}"
    else:
        # no base clip: slow push-in on the still so it is at least a video, not a poster
        if still is None or not still.exists():
            raise FileNotFoundError("no base clip and no still to animate")
        frames = int(dur * 30)
        vf = (f"scale=1296:2304,zoompan=z='1+0.0008*on':d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
              f":s={W}x{H}:fps=30,format=yuv420p")
        cmd = [FFMPEG, "-y", "-loop", "1", "-i", str(still), "-vf", vf, "-t", f"{dur:.1f}",
               "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-an", str(out)]
        how = "animated still (drop a clip in base/ to use a real creator)"
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError("ffmpeg failed:\n" + r.stderr[-1500:])
    return out, how


if __name__ == "__main__":
    import sys
    t = sys.argv[1] if len(sys.argv) > 1 else "just seen a guy testing the video renderer. no base clip. no footage. no excuses. just him and ffmpeg against the world. Respect"
    p, how = render_mp4(t, ROOT / "out" / "_test" / "post.mp4", "test", still=ROOT / "out" / "rihal" / "post.png")
    print(p, "|", how)
