# Frame — content studio

A brand website becomes an editable short-form post and a playable vertical video.
The local studio includes a reaction picker, live generation progress, caption editing,
MP4 downloads and saved examples.

## Run locally

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
Copy-Item .env.example .env
# Set ANTHROPIC_API_KEY in .env, then:
python app.py
```

Open http://localhost:8000. Leave the server running. Generation needs an Anthropic API key;
viewing existing examples and rebuilding their videos does not make an AI call.

The CLI is also available:

```powershell
python make.py https://www.forestapp.cc/ --n 6
python revideo.py
```

`revideo.py` rebuilds saved posts using their final text and any saved manual clip choice.
Generation and rendering can take a few minutes depending on the site and machine.

## Walkthrough

1. Open an example from the gallery and play its video.
2. Select a different reaction, optionally edit the text/caption, and click **Rebuild video**.
3. Download the MP4. Suggested music is not embedded: exports are silent.
4. Paste another brand URL and follow the stages until the new video opens.

## Pipeline

1. Read the homepage and up to two useful supporting pages. A homepage yielding fewer than
   1,500 characters triggers a model web-fetch fallback. Site access can still fail.
2. Build a structured brand profile: audience, niche, problems, tone and supporting facts.
3. Recommend a format. This is advisory; the implemented renderer exports reaction + text only.
4. Generate six drafts, critique them and revise the winner. Scores are AI editorial opinions;
   they are not audience performance data, and the revised version is not scored again.
5. Match the final reaction label to `base/clips.json`. Older saved posts without a label use
   deterministic text rules. A manual clip choice takes precedence.
6. Assemble a 1080 x 1920 H.264 MP4. Text uses measured wrapping in a separate lower panel.
   Reading time is 2.6 words/second plus 2.5 seconds, minimum eight seconds, without a 20-second cap.
7. Extract the poster from the actual video and save the final post and provenance.

## Outputs in `out/<brand>/`

| File | Purpose |
|---|---|
| `post.mp4` | Finished silent vertical video |
| `post.png` | Poster extracted from the MP4 |
| `post.md` | Readable post, caption, editorial notes and other drafts |
| `final.json` | Final text, caption, reaction and manual selection when present |
| `post.video.json` | Actual clip, reaction, selection method, duration and source |
| `profile.json` | Extracted brand profile |
| `variants.json`, `scores.json` | Generated drafts and original editorial scores |

## Clip library

`base/clips.json` contains three familiar reaction references and four stock clips.
Each entry records the observed expression, name and framing; reaction references also record
source pages and personal-demo usage. This catalogue does not assert commercial clearance.
The renderer preserves wide reaction clips using a blurred backdrop. Exporting at 1080p does
not create extra detail in low-resolution source GIFs.

To add a clip, place a video in `base/`, add its entry to `clips.json` and a matching `.jpg`
thumbnail. Available reaction labels are `confused`, `disbelief`, `deadpan`, `skeptical`, and
`thoughtful`. For non-cropped sources use `"fit": "contain"`; stock crop offsets are measured
against a 1080 x 1920 scaled frame. No footage produces an explicitly labelled placeholder.

## Validation and limitations

```powershell
python -m unittest test_video test_app -v
```

Tests cover clip matching and overrides, missing footage, reading time, long-text layout and
editor path validation. The local server supports video range requests, asynchronous jobs and
one rendering/generation job at a time. A failed render is reported as a failure, not a completed video.

This is a local trial prototype, not a hosted multi-user service. Website extraction can be thin;
brand profiles may include labelled inferences. The small clip collection cannot suit every brand.
Nothing is posted to social media. `generate.py` is the earlier text-only pipeline and supplies
shared model-call helpers. `RATIONALE.md` describes the final implementation and tradeoffs.
