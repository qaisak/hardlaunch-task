# Brand URL in, on-brand short-form content out

```
python make.py https://www.somebrand.com
```

Produces, in `out/<brand>/`:

| File | What |
|---|---|
| `post.md` | The post: overlay text, base-video spec, audio, caption, why it is this brand, the format decision, runners-up, and the brand profile used |
| `post.png` | 9:16 preview with the text burned on TikTok-style, where the silent reacting creator would be |
| `profile.json` | Brand profile extracted from the site |
| `variants.json`, `scores.json` | All drafts and the editor's scores |

Around 90 seconds per brand, well under £1.

## Setup
```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env        (paste ANTHROPIC_API_KEY into .env)
python check_setup.py
python make.py https://www.calai.app
```

## How it works
1. **Ingest** (`ingest()`): GET the homepage plus up to two "about / how it works" pages, strip to text.
   If the site is a JS shell or bot-gated (under 400 chars), fall back to Claude's server-side web fetch.
2. **Brand profile** (`prompts/profile.md`): one call turns the site text into JSON: niche, audience,
   the core pain, the exact objects and rival tools people use instead (`old_way_objects`), real scenes
   where the pain shows, tone, proof points, do-not-say.
3. **Format decision** (`prompts/format_select.md`): long overlay vs slideshow vs hook+demo, with a reason.
   The system always renders long overlay (one content type was sufficient; it is the dominant format
   and needs no footage), but the decision is recorded so a human can see it.
4. **Drafts** (`prompts/overlay_generate.md` + `prompts/overlay_style.md`): N overlays in the house style,
   each a different scene and verdict, brand name exactly once, niche-specific nouns from the profile.
5. **Critique** (`prompts/overlay_critique.md`): a strict editor scores on-brand, voice, hook, not-an-ad,
   comment bait, honesty, length, and names one fix per draft.
6. **Revise** (`prompts/overlay_revise.md`): the editor's fix is applied to the winner.
7. **Assemble** (`render_png()`): text burned onto a 9:16 frame with a black stroke, plus the markdown pack.

The taste lives in `prompts/overlay_style.md` (what a long overlay is and the seven things every one must
have, derived from the reference piece) and `prompts/taste.md` (general short-form rules). Editing those
changes the output; the code is plumbing.

## Also in the repo
`generate.py` is the earlier, more general generator (any text input to N hook/format variants with a
critique pass). `make.py` imports its `call()` and JSON helpers. `inputs/` and `out/sample_*` are from that.

## Web page (for the walkthrough)
```
python app.py
```
Open http://localhost:8000, paste a URL, click make. About 90 seconds later you see the preview frame,
the post, base-video spec, caption, the format decision, the brand profile and the runners-up.
Stdlib only, one request at a time, no polish on purpose (UI was out of scope).
