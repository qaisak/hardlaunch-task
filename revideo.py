"""Re-render post.mp4 for every brand in out/ from the saved final text. No model calls.
Run after dropping a new base clip in base/ so every example uses the real creator footage."""
import json, sys
from pathlib import Path
from video import ROOT, render_mp4

for d in sorted((ROOT / "out").iterdir()):
    md = d / "post.md"
    if not md.exists() or d.name.startswith("_"):
        continue
    fj = d / "final.json"
    text = (json.loads(fj.read_text(encoding="utf-8"))["text"] if fj.exists()
            else next(ln[2:] for ln in md.read_text(encoding="utf-8").splitlines() if ln.startswith("> ")))
    brand = json.loads((d / "profile.json").read_text(encoding="utf-8")).get("brand_name", d.name)
    final = json.loads(fj.read_text(encoding="utf-8")) if fj.exists() else {}
    _, how = render_mp4(text, d / "post.mp4", brand, still=d / "post.png", reaction=final.get("reaction"), clip_name=final.get("selected_clip"))
    if final:
        final["video"] = how
        fj.write_text(json.dumps(final, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"{d.name:12s} {how}")
