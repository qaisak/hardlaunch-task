"""Tiny local web page: paste a brand URL, see the post.

    python app.py            then open http://localhost:8000

No framework, stdlib only. Runs make.run() synchronously (about 90s), then shows the result.
Not production: one request at a time, no auth. It exists so the walkthrough is one paste away.
"""

from __future__ import annotations

import html
import json
import traceback
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

from make import ROOT, run

OUT = ROOT / "out"

PAGE = """<!doctype html><meta charset="utf-8"><title>brand url in, post out</title>
<style>
 body{{font:16px/1.5 system-ui,sans-serif;max-width:1000px;margin:40px auto;padding:0 20px;color:#111}}
 form{{display:flex;gap:10px;margin-bottom:30px}} input{{flex:1;font-size:18px;padding:10px}}
 button{{font-size:18px;padding:10px 20px;background:#111;color:#fff;border:0;cursor:pointer}}
 .row{{display:flex;gap:30px;align-items:flex-start}} img{{width:360px;border-radius:14px;box-shadow:0 6px 30px #0003}}
 blockquote{{font-size:20px;background:#f4f4f5;padding:16px 20px;border-radius:10px}}
 .meta{{color:#555;font-size:14px}} h2{{margin-top:32px}} li{{margin:8px 0}}
 .prev a{{margin-right:12px}}
</style>
<h1>brand url in, post out</h1>
<form method="post" action="/make">
 <input name="url" placeholder="https://www.somebrand.com" value="{url}" required>
 <button>make</button>
</form>
<p class="meta">Takes about 90 seconds. Long overlay format. The frame is a preview of where the silent reacting creator goes.</p>
{body}
<h2>previous</h2><p class="prev">{prev}</p>
"""


def result_html(slug: str) -> str:
    d = OUT / slug
    if not (d / "post.md").exists():
        return f"<p>no result for {html.escape(slug)}</p>"
    variants = json.loads((d / "variants.json").read_text(encoding="utf-8"))
    scores = {s["id"]: s for s in json.loads((d / "scores.json").read_text(encoding="utf-8"))}
    profile = json.loads((d / "profile.json").read_text(encoding="utf-8"))
    md = (d / "post.md").read_text(encoding="utf-8")
    # the final text is the blockquote line in post.md
    final = next((ln[2:] for ln in md.splitlines() if ln.startswith("> ")), "")
    fmt = next((ln for ln in md.splitlines() if ln.startswith("**Format decision:**")), "")
    ranked = sorted(variants, key=lambda v: scores.get(v["id"], {}).get("overall", 0), reverse=True)
    win = ranked[0]
    if (d / "final.json").exists():  # revised post, written by make.run()
        win = json.loads((d / "final.json").read_text(encoding="utf-8"))
        final = win["text"]
    e = html.escape
    runners = "".join(f"<li>({scores.get(v['id'], {}).get('overall', '?')}/10) {e(v['text'])}</li>" for v in ranked[1:])
    return f"""
<div class="row">
 <img src="/out/{slug}/post.png" alt="preview">
 <div>
  <h2 style="margin-top:0">{e(profile.get('brand_name', slug))}</h2>
  <blockquote>{e(final)}</blockquote>
  <p><b>Base video:</b> {e(str(win.get('base_video','')))}<br>
     <b>Audio:</b> {e(str(win.get('audio','')))}<br>
     <b>Caption:</b> {e(str(win.get('caption','')))}<br>
     <b>Why this brand:</b> {e(str(win.get('why_this_brand','')))}</p>
  <p class="meta">{e(fmt.replace('**',''))}</p>
  <p class="meta">Profile: {e(profile.get('one_liner',''))} | niche: {e(profile.get('niche',''))}<br>
     old way: {e(', '.join(profile.get('old_way_objects', [])))}</p>
 </div>
</div>
<h2>runners-up</h2><ul>{runners}</ul>
<p class="meta"><a href="/out/{slug}/post.md">post.md</a> · <a href="/out/{slug}/profile.json">profile.json</a></p>
"""


def prev_links() -> str:
    dirs = sorted((p for p in OUT.iterdir() if (p / "post.md").exists()), key=lambda p: p.stat().st_mtime, reverse=True)
    return " ".join(f'<a href="/r/{p.name}">{html.escape(p.name)}</a>' for p in dirs) or "none yet"


class H(SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=str(ROOT), **k)

    def do_GET(self):
        u = urlparse(self.path)
        if u.path == "/":
            return self._page("", "")
        if u.path.startswith("/r/"):
            return self._page("", result_html(u.path[3:]))
        if u.path.startswith("/out/"):
            return super().do_GET()
        self.send_error(404)

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        url = parse_qs(self.rfile.read(n).decode())["url"][0].strip()
        try:
            res = run(url, n=6, out=OUT)
            self.send_response(303)
            self.send_header("Location", f"/r/{res['slug']}")
            self.end_headers()
        except Exception as ex:
            traceback.print_exc()
            self._page(url, f"<p style='color:#b00'><b>failed:</b> {html.escape(str(ex))}</p>")

    def _page(self, url: str, body: str):
        out = PAGE.format(url=html.escape(url), body=body, prev=prev_links()).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(out)))
        self.end_headers()
        self.wfile.write(out)

    def log_message(self, *a):  # keep the console for pipeline logs
        pass


if __name__ == "__main__":
    print("open http://localhost:8000")
    HTTPServer(("127.0.0.1", 8000), H).serve_forever()
