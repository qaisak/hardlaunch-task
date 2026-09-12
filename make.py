"""Brand URL in, on-brand short-form content out.

    python make.py https://www.somebrand.com
    python make.py https://www.somebrand.com --n 6 --out out/

Pipeline: fetch site -> brand profile -> format decision -> N long-overlay drafts ->
critique -> pick the winner -> render a 9:16 preview PNG + a markdown pack.

Outputs land in out/<brand>/: post.png, post.md, profile.json, variants.json, scores.json
"""

from __future__ import annotations

import argparse
import shutil
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

from generate import PROMPTS, ROOT, call, call_json, extract_json, read
from video import render_mp4
from trends import trend_input, adapt
from discovery import discover, audience_context as research_context, trend_reference
from audience import build_insights, writing_context

load_dotenv()

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/128 Safari/537.36"}
MAX_CHARS = 14000
MIN_CHARS = 1500  # below this a bare GET is a JS shell or a thin page: use the model's web fetch


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


def ingest_via_model(client, url: str) -> str:
    """Fallback for JS-rendered or bot-gated sites: Claude's server-side web fetch reads the page
    (it renders more than a bare GET) and returns the visible copy verbatim-ish."""
    r = client.messages.create(
        model="claude-opus-5",
        max_tokens=8000,
        output_config={"effort": "low"},
        tools=[{"type": "web_fetch_20260209", "name": "web_fetch", "max_uses": 3}],
        messages=[{"role": "user", "content":
                   f"Fetch {url} (and one 'about' or 'how it works' page if linked). Return the visible marketing "
                   f"copy of the site as plain text, as close to verbatim as you can: headline, subheads, product "
                   f"descriptions, claims, prices, reviews, FAQs. No commentary, no summary, just the text."}],
    )
    text = "".join(b.text for b in r.content if b.type == "text")
    if len(text) < 400:
        raise RuntimeError(f"Could not read {url} by scraping or by web fetch.")
    return f"URL: {url}\n{text}"


def ingest(url: str, client=None) -> str:
    """Homepage plus up to two informative internal pages, trimmed to MAX_CHARS.
    Falls back to model web fetch when a bare GET returns a JS shell."""
    if not url.startswith("http"):
        url = "https://" + url
    try:
        text, links = html_to_text(fetch_page(url))
    except Exception as e:
        text, links = "", []
        print(f"  scrape failed ({e}); trying web fetch fallback", flush=True)
    if len(text) < MIN_CHARS and client is not None:
        return ingest_via_model(client, url)[:MAX_CHARS]
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


def run(url: str, n: int = 6, out: Path = ROOT / "out", progress=None, audience_links='', audience_excerpts='', trend_links='', trend_notes='', trend_observed='', trend_market='', auto_research=True) -> dict:
    """The whole pipeline for one URL. Returns the result dict; also used by app.py."""
    reference = trend_input(trend_links, trend_notes, trend_observed, trend_market)
    import anthropic
    client = anthropic.Anthropic()
    t0 = time.time()
    def log(message):
        print(f"[{time.time()-t0:5.0f}s] {message}", flush=True)
        if progress:
            progress(message)

    log(f"fetching {url}")
    site_text = ingest(url, client)
    log(f"scraped {len(site_text)} chars")

    taste = read(PROMPTS / "taste.md")
    style = read(PROMPTS / "overlay_style.md")

    log("building brand profile")
    profile = call_json(client, taste, read(PROMPTS / "profile.md").replace("{text}", site_text), effort="medium")
    profile["source_url"] = url
    insights = build_insights(client, profile, audience_links, audience_excerpts, log) if audience_links or audience_excerpts else None
    research = discover(client, profile, log) if auto_research else {"status":"Automatic research disabled", "audience":[], "trends":[]}
    audience_context = writing_context(insights) if insights else research_context(research)
    reference = reference or trend_reference(research)
    brand = profile.get("brand_name", urlparse(url).netloc)
    outdir = out / slug(brand)
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "profile.json").write_text(json.dumps(profile, indent=2, ensure_ascii=False), encoding="utf-8")
    (outdir / "audience.json").write_text(json.dumps(insights or {"themes": [], "sources": []}, indent=2, ensure_ascii=False), encoding="utf-8")
    (outdir / "research.json").write_text(json.dumps(research, indent=2, ensure_ascii=False), encoding="utf-8")
    profile_s = json.dumps(profile, indent=1, ensure_ascii=False)

    log("choosing format")
    fmt = call_json(client, taste, read(PROMPTS / "format_select.md").replace("{profile}", profile_s), effort="low")

    log(f"writing {n} overlay drafts")
    variants = call_json(client, taste + "\n\n" + style + audience_context,
                                 read(PROMPTS / "overlay_generate.md").replace("{n}", str(n)).replace("{profile}", profile_s))
    (outdir / "variants.json").write_text(json.dumps(variants, indent=2, ensure_ascii=False), encoding="utf-8")

    log("critiquing")
    scores = call_json(client, taste + "\n\n" + style + audience_context,
                               read(PROMPTS / "overlay_critique.md").replace("{variants}", json.dumps(variants, indent=1, ensure_ascii=False)).replace("{profile}", profile_s),
                               effort="medium")
    (outdir / "scores.json").write_text(json.dumps(scores, indent=2, ensure_ascii=False), encoding="utf-8")

    by_id = {s["id"]: s for s in scores}
    ranked = sorted(variants, key=lambda v: by_id.get(v["id"], {}).get("overall", 0), reverse=True)
    win = ranked[0]
    ws = by_id.get(win["id"], {})

    log("applying editor fix")
    final = win
    if ws.get("fix"):
        try:
            rev = call_json(client, taste + "\n\n" + style + audience_context,
                                    read(PROMPTS / "overlay_revise.md").replace("{text}", win["text"]).replace("{fix}", ws["fix"]).replace("{profile}", profile_s),
                                    effort="medium")
            final = {**win, "text": rev["text"], "caption": rev.get("caption", win.get("caption")), "what_changed": rev.get("what_changed", ""), "reaction": rev.get("reaction", win.get("reaction"))}
        except Exception as e:  # revise is a bonus, never let it sink the run
            log(f"revise skipped: {e}")

    directions = {}
    if reference:
        log("Adapting a second direction from trend references")
        try:
            adapted = adapt(client, profile, final, reference, taste + "\n" + style)
            directions = {"evergreen": dict(final), "trend": adapted}
        except Exception as error:
            log("Trend adaptation unavailable; exporting evergreen: " + type(error).__name__)
            research["adaptation_status"] = "Adaptation unavailable; evergreen exported"
            (outdir / "research.json").write_text(json.dumps(research, indent=2), encoding="utf-8")
    (outdir / "trends.json").write_text(json.dumps(reference or {}, indent=2, ensure_ascii=False), encoding="utf-8")
    (outdir / "directions.json").write_text(json.dumps(directions, indent=2, ensure_ascii=False), encoding="utf-8")
    final["direction"] = "evergreen"
    final["audience_used"] = bool(insights or research.get("audience"))
    log("rendering preview")
    render_png(final["text"], outdir / "post.png", brand)
    log("rendering video")
    try:
        _, how = render_mp4(final["text"], outdir / "post.mp4", brand, still=outdir / "post.png", reaction=final.get("reaction"))
        if reference:
            shutil.copy2(outdir / "post.mp4", outdir / "evergreen.mp4")
            (outdir / "trend.mp4").unlink(missing_ok=True)
        final["video"] = how
        log(f"video: {how}")
    except Exception as e:
        log(f"Video could not be completed: {e}")
        raise RuntimeError("Video export failed; the written drafts were saved. " + str(e)) from e

    md = [f"# {brand}: long overlay\n",
          f"**Format decision:** {fmt.get('format')}. {fmt.get('reason')} Runner-up {fmt.get('runner_up')}: {fmt.get('why_not_runner_up')}\n",
          "## The post\n", f"> {final['text']}\n",
          f"**Base video:** {final.get('base_video')}  \n**Audio:** {final.get('audio')}  \n**Caption:** {final.get('caption')}  \n**Why it is this brand:** {final.get('why_this_brand')}\n",
          f"Draft scored {ws.get('overall','?')}/10. Editor fix applied: {ws.get('fix','')}  \nWhat changed: {final.get('what_changed','nothing')}  \nOriginal draft: {win['text']}\n",
          f"Preview: `post.png`\n", "## Runners-up\n"]
    for v in ranked[1:]:
        s = by_id.get(v["id"], {})
        md.append(f"- ({s.get('overall','?')}/10) {v['text']}")
    md += ["\n## Brand profile used\n", "```json", profile_s, "```"]
    (outdir / "post.md").write_text("\n".join(md), encoding="utf-8")
    (outdir / "final.json").write_text(json.dumps({**final, "format": fmt, "draft_score": ws.get("overall"),
                                                   "editor_fix": ws.get("fix")}, indent=2, ensure_ascii=False), encoding="utf-8")

    log(f"done -> {outdir / 'post.md'}")
    return {"brand": brand, "slug": slug(brand), "outdir": outdir, "final": final, "format": fmt,
            "ranked": ranked, "scores": by_id, "profile": profile}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("url")
    ap.add_argument("--n", type=int, default=6, help="overlay drafts to generate")
    ap.add_argument("--out", type=Path, default=ROOT / "out")
    ap.add_argument("--audience-links", type=Path, help="Text file with up to three Reddit discussion URLs")
    ap.add_argument("--audience-excerpts", type=Path, help="Text file containing selected source excerpts")
    args = ap.parse_args()
    res = run(args.url, args.n, args.out,
              audience_links=args.audience_links.read_text(encoding='utf-8-sig') if args.audience_links else '',
              audience_excerpts=args.audience_excerpts.read_text(encoding='utf-8-sig') if args.audience_excerpts else '')
    print("\n" + res["final"]["text"] + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
