"""Brand URL in, on-brand short-form content out.

    python make.py https://www.somebrand.com
    python make.py https://www.somebrand.com --n 6 --out out/

Pipeline: fetch site -> brand profile -> format decision -> N long-overlay drafts ->
critique -> pick the winner -> render a 9:16 preview PNG + a markdown pack.

Outputs land in out/<brand>/: post.png, post.md, profile.json, variants.json, scores.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import textwrap
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont

from generate import PROMPTS, ROOT, call, extract_json, read

load_dotenv()

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/128 Safari/537.36"}
MAX_CHARS = 14000


# ---------------------------------------------------------------- ingest ----

def fetch_page(url: str) -> str:
    r = requests.get(url, headers=UA, timeout=20)
    r.raise_for_status()
    return r.text


def html_to_text(html: str) -> tuple[str, list[str]]:
    """Visible text plus candidate internal links worth a second fetch (about, how it works)."""
    soup = BeautifulSoup(html, "html.parser")
    for t in soup(["script", "style", "noscript", "svg", "iframe"]):
        t.decompose()
    bits = []
    title = soup.title.string.strip() if soup.title and soup.title.string else ""
    if title:
        bits.append(f"TITLE: {title}")
    for m in soup.find_all("meta"):
        k = (m.get("name") or m.get("property") or "").lower()
        if k in ("description", "og:description", "og:title", "twitter:description"):
            bits.append(f"{k.upper()}: {m.get('content', '')}")
    text = soup.get_text("\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n", text)
    bits.append(text.strip())
    links = []
    for a in soup.find_all("a", href=True):
        h = a["href"].lower()
        if any(k in h for k in ("about", "how-it-works", "features", "why", "story", "faq")):
            links.append(a["href"])
    return "\n".join(bits), links


def ingest(url: str) -> str:
    """Homepage plus up to two informative internal pages, trimmed to MAX_CHARS."""
    if not url.startswith("http"):
        url = "https://" + url
    text, links = html_to_text(fetch_page(url))
    base = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
    seen, extra = set(), []
    for h in links:
        full = urljoin(url, h)
        if urlparse(full).netloc != urlparse(url).netloc or full in seen:
            continue
        seen.add(full)
        try:
            t, _ = html_to_text(fetch_page(full))
            extra.append(f"\n\n=== {full} ===\n{t[:4000]}")
        except Exception:
            continue
        if len(extra) >= 2:
            break
    out = f"URL: {url}\n{text}" + "".join(extra)
    if len(out) < 400:
        raise RuntimeError("Too little text scraped (JS-rendered site or blocked). Try a different page of the site.")
    return out[:MAX_CHARS]


# ---------------------------------------------------------------- render ----

def render_png(text: str, out: Path, brand: str) -> None:
    """9:16 preview: dark placeholder background (where the reacting creator would be) + white overlay text."""
    W, H = 1080, 1920
    img = Image.new("RGB", (W, H), (28, 28, 30))
    d = ImageDraw.Draw(img)
    # subtle vignette so the text reads as burned-on, not a poster
    for i in range(0, H, 8):
        shade = 28 + int(18 * (1 - abs(i - H / 2) / (H / 2)))
        d.rectangle([0, i, W, i + 8], fill=(shade, shade, shade + 2))
    d.text((W // 2, H - 140), "[ silent reacting creator here ]", fill=(110, 110, 115),
           font=_font(34), anchor="mm")
    d.text((W // 2, 120), f"@{brand}", fill=(150, 150, 155), font=_font(36), anchor="mm")
    font = _font(58)
    lines = []
    for para in text.split("\n"):
        lines += textwrap.wrap(para, width=30) or [""]
    line_h = 76
    y = (H - line_h * len(lines)) // 2
    for ln in lines:
        x = W // 2
        # black stroke = TikTok's classic burned-in look
        d.text((x, y), ln, font=font, fill="white", anchor="ma", stroke_width=5, stroke_fill="black")
        y += line_h
    img.save(out)


def _font(size: int) -> ImageFont.FreeTypeFont:
    for p in (r"C:\Windows\Fonts\arialbd.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(p, size)
        except OSError:
            continue
    return ImageFont.load_default()


# ---------------------------------------------------------------- main ------

def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-") or "brand"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("url")
    ap.add_argument("--n", type=int, default=6, help="overlay drafts to generate")
    ap.add_argument("--out", type=Path, default=ROOT / "out")
    args = ap.parse_args()

    import anthropic
    client = anthropic.Anthropic()
    t0 = time.time()
    log = lambda m: print(f"[{time.time()-t0:5.0f}s] {m}", flush=True)

    log(f"fetching {args.url}")
    site_text = ingest(args.url)
    log(f"scraped {len(site_text)} chars")

    taste = read(PROMPTS / "taste.md")
    style = read(PROMPTS / "overlay_style.md")

    log("building brand profile")
    profile = extract_json(call(client, taste, read(PROMPTS / "profile.md").replace("{text}", site_text), effort="medium"))
    brand = profile.get("brand_name", urlparse(args.url).netloc)
    outdir = args.out / slug(brand)
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "profile.json").write_text(json.dumps(profile, indent=2, ensure_ascii=False), encoding="utf-8")
    profile_s = json.dumps(profile, indent=1, ensure_ascii=False)

    log("choosing format")
    fmt = extract_json(call(client, taste, read(PROMPTS / "format_select.md").replace("{profile}", profile_s), effort="low"))

    log(f"writing {args.n} overlay drafts")
    variants = extract_json(call(client, taste + "\n\n" + style,
                                 read(PROMPTS / "overlay_generate.md").replace("{n}", str(args.n)).replace("{profile}", profile_s)))
    (outdir / "variants.json").write_text(json.dumps(variants, indent=2, ensure_ascii=False), encoding="utf-8")

    log("critiquing")
    scores = extract_json(call(client, taste + "\n\n" + style,
                               read(PROMPTS / "overlay_critique.md").replace("{variants}", json.dumps(variants, indent=1, ensure_ascii=False)).replace("{profile}", profile_s),
                               effort="medium"))
    (outdir / "scores.json").write_text(json.dumps(scores, indent=2, ensure_ascii=False), encoding="utf-8")

    by_id = {s["id"]: s for s in scores}
    ranked = sorted(variants, key=lambda v: by_id.get(v["id"], {}).get("overall", 0), reverse=True)
    win = ranked[0]
    ws = by_id.get(win["id"], {})

    log("rendering preview")
    render_png(win["text"], outdir / "post.png", brand)

    md = [f"# {brand}: long overlay\n",
          f"**Format decision:** {fmt.get('format')}. {fmt.get('reason')} Runner-up {fmt.get('runner_up')}: {fmt.get('why_not_runner_up')}\n",
          "## The post\n", f"> {win['text']}\n",
          f"**Base video:** {win.get('base_video')}  \n**Audio:** {win.get('audio')}  \n**Caption:** {win.get('caption')}  \n**Why it is this brand:** {win.get('why_this_brand')}\n",
          f"Score {ws.get('overall','?')}/10. Editor: {ws.get('fix','')}\n",
          f"Preview: `post.png`\n", "## Runners-up\n"]
    for v in ranked[1:]:
        s = by_id.get(v["id"], {})
        md.append(f"- ({s.get('overall','?')}/10) {v['text']}")
    md += ["\n## Brand profile used\n", "```json", profile_s, "```"]
    (outdir / "post.md").write_text("\n".join(md), encoding="utf-8")

    log(f"done -> {outdir / 'post.md'}")
    print("\n" + win["text"] + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
