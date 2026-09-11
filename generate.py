"""Short-form content generator: input -> N variants -> critique -> ranked output.

Usage:
    python generate.py inputs/sample_brief.md            # real run
    python generate.py inputs/sample_brief.md --dry-run  # no API, proves the pipeline
    python generate.py inputs/*.md --n 8 --top 3 --out out/

Outputs per input file, in --out:
    <name>.variants.json   raw generated variants
    <name>.scores.json     critique scores
    <name>.md              ranked, readable result + suggested test plan
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).parent
PROMPTS = ROOT / "prompts"
MODEL = "claude-opus-5"


# ---------------------------------------------------------------- helpers ---

def read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def load_input(path: Path) -> str:
    """Anything text-like becomes the input string. Extend here if the brief hands you
    a different shape (CSV of past posts, URL dump, transcript)."""
    text = read(path)
    if path.suffix.lower() == ".csv":
        return "CSV data (columns then rows):\n" + text
    return text


def extract_json(text: str):
    """Model was told to return bare JSON, but be tolerant of fences or prose."""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.S)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("["), text.rfind("]")
        if start != -1 and end != -1:
            return json.loads(text[start : end + 1])
        raise


CLAUDE_CLI = os.getenv(
    "CLAUDE_CLI",
    r"C:\Users\Qais\AppData\Roaming\Claude\claude-code\2.1.266\claude.exe",
)


def call_cli(system: str, user: str) -> str:
    """Fallback backend: `claude -p` on the Claude Code subscription (needs `claude` logged in)."""
    proc = subprocess.run(
        [CLAUDE_CLI, "-p", "--output-format", "text", "--model", "opus",
         "--system-prompt", system],
        input=user, capture_output=True, text=True, encoding="utf-8", timeout=900,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"claude CLI failed: {proc.stderr.strip()}")
    return proc.stdout


def call(client, system: str, user: str, effort: str = "high") -> str:
    """One streamed call, returns the text. Streaming avoids timeouts on long outputs."""
    if client == "cli":
        return call_cli(system, user)
    with client.messages.stream(
        model=MODEL,
        max_tokens=32000,
        system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": user}],
        output_config={"effort": effort},
    ) as stream:
        msg = stream.get_final_message()
    if msg.stop_reason == "refusal":
        raise RuntimeError(f"Model refused: {msg.stop_details}")
    return "".join(b.text for b in msg.content if b.type == "text")


# ------------------------------------------------------------ pipeline ------

def generate_variants(client, taste: str, input_text: str, n: int, dry: bool) -> list[dict]:
    if dry:
        return [
            {
                "id": f"v{i+1}",
                "format": f"dry-run format {i+1}",
                "hook": {"visual": "placeholder", "audio": "placeholder", "text_overlay": "placeholder"},
                "script": ["line 1", "line 2", "line 3"],
                "on_screen_text": [],
                "caption": "placeholder caption",
                "duration_s": 20,
                "share_reason": "placeholder",
                "comment_trigger": "placeholder",
                "why_views": "placeholder",
            }
            for i in range(n)
        ]
    prompt = read(PROMPTS / "generate.md").replace("{n}", str(n)).replace("{input}", input_text)
    return extract_json(call(client, taste, prompt))


def critique(client, taste: str, input_text: str, variants: list[dict], dry: bool) -> list[dict]:
    if dry:
        return [
            {"id": v["id"], "scores": {}, "overall": 10 - i, "fix": "placeholder fix"}
            for i, v in enumerate(variants)
        ]
    prompt = (
        read(PROMPTS / "critique.md")
        .replace("{variants}", json.dumps(variants, indent=1, ensure_ascii=False))
        .replace("{input}", input_text)
    )
    return extract_json(call(client, taste, prompt, effort="medium"))


def render(name: str, variants: list[dict], scores: list[dict], top: int) -> str:
    by_id = {s["id"]: s for s in scores}
    ranked = sorted(variants, key=lambda v: by_id.get(v["id"], {}).get("overall", 0), reverse=True)
    out = [f"# {name}: ranked variants\n"]
    for rank, v in enumerate(ranked, 1):
        s = by_id.get(v["id"], {})
        tag = "SHIP" if rank <= top else "bench"
        out.append(f"## {rank}. [{tag}] {v['id']} - {v.get('format','')}  (score {s.get('overall','?')}/10)\n")
        h = v.get("hook", {})
        out.append(f"**Hook** visual: {h.get('visual','')} | audio: {h.get('audio','')} | text: **{h.get('text_overlay','')}**\n")
        out.append("**Script**")
        for line in v.get("script", []):
            out.append(f"- {line}")
        if v.get("on_screen_text"):
            out.append(f"\n**On-screen text:** {' / '.join(v['on_screen_text'])}")
        out.append(f"\n**Caption:** {v.get('caption','')}  \n**~{v.get('duration_s','?')}s**")
        out.append(f"\n**Share reason:** {v.get('share_reason','')}  \n**Comment trigger:** {v.get('comment_trigger','')}")
        out.append(f"\n**Why views:** {v.get('why_views','')}")
        if s.get("scores"):
            out.append("\nScores: " + ", ".join(f"{k} {val}" for k, val in s["scores"].items()))
        if s.get("fix"):
            out.append(f"\nEditor fix: {s['fix']}")
        out.append("\n---\n")
    top_ids = ", ".join(v["id"] for v in ranked[:top])
    out.append(
        "## Suggested test plan\n"
        f"- Post the top {top} ({top_ids}) across accounts in the same 48h window, same posting slot.\n"
        "- Hold the body constant where possible; the hook is the variable under test.\n"
        "- Measure 3s hold rate and completion before raw views; views lag, hold rate does not.\n"
        "- Promote the winning FORMAT (not just the video) into the template library and refill it.\n"
    )
    return "\n".join(out)


# ---------------------------------------------------------------- main ------

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("inputs", nargs="+", type=Path)
    ap.add_argument("--n", type=int, default=8, help="variants to generate per input")
    ap.add_argument("--top", type=int, default=3, help="how many to mark SHIP")
    ap.add_argument("--out", type=Path, default=ROOT / "out")
    ap.add_argument("--dry-run", action="store_true", help="no API calls, placeholder output")
    ap.add_argument("--backend", choices=["api", "cli"], default="api",
                    help="api = Anthropic SDK with ANTHROPIC_API_KEY; cli = claude -p on the Claude Code subscription")
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    client = None
    if not args.dry_run:
        if args.backend == "cli":
            client = "cli"
        else:
            import anthropic
            client = anthropic.Anthropic()

    taste = read(PROMPTS / "taste.md")

    for path in args.inputs:
        t0 = time.time()
        name = path.stem
        input_text = load_input(path)
        print(f"[{name}] generating {args.n} variants...", flush=True)
        variants = generate_variants(client, taste, input_text, args.n, args.dry_run)
        (args.out / f"{name}.variants.json").write_text(json.dumps(variants, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"[{name}] critiquing...", flush=True)
        scores = critique(client, taste, input_text, variants, args.dry_run)
        (args.out / f"{name}.scores.json").write_text(json.dumps(scores, indent=2, ensure_ascii=False), encoding="utf-8")
        md = render(name, variants, scores, args.top)
        (args.out / f"{name}.md").write_text(md, encoding="utf-8")
        print(f"[{name}] done in {time.time()-t0:.0f}s -> {args.out / (name + '.md')}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
