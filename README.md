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
5. Rank three reactions by mood and situation, with visible reasons. Older saved posts without a label use
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
| `audience.json` | Optional audience themes, source URLs, excerpts and collection method |
| `profile.json` | Extracted brand profile |
| `variants.json`, `scores.json` | Generated drafts and original editorial scores |

## Clip library

`base/clips.json` contains seven active familiar reactions. Legacy stock files are disabled and never selected or shown in the picker.
Each entry records the observed expression, name and framing; reaction references also record
source pages and personal-demo usage. This catalogue does not assert commercial clearance.
The renderer preserves wide reaction clips using a blurred backdrop. Exporting at 1080p does
not create extra detail in low-resolution source GIFs.

To add a clip, place a video in `base/`, add its entry to `clips.json` and a matching `.jpg`
thumbnail. Available reaction labels are `confused`, `disbelief`, `deadpan`, `skeptical`, and
`thoughtful`, and `approval`. Set `"collection": "reaction"`, `"enabled": true`, and `"fit": "contain"`. Add secondary moods under `tags` and situations under `situations`. Missing reactions stop the export with an actionable error; stock is never substituted.

## Validation and limitations

```powershell
python -m unittest discover -v
```

Tests cover clip matching and overrides, missing footage, reading time, long-text layout and
editor path validation. The local server supports video range requests, asynchronous jobs and
one rendering/generation job at a time. A failed render is reported as a failure, not a completed video.

This is a local trial prototype, not a hosted multi-user service. Website extraction can be thin;
brand profiles may include labelled inferences. The small clip collection cannot suit every brand.
Nothing is posted to social media. `generate.py` is the earlier text-only pipeline and supplies
shared model-call helpers. `RATIONALE.md` describes the final implementation and tradeoffs.

## Optional Reddit audience context

Automatic research now runs by default. To supply your own sources, expand **Override audience research** below the brand URL. Supply up to three discussion links and relevant excerpts. With multiple links, place each URL on its own line immediately above its excerpt. The reader attempts ordinary public HTML only when an excerpt is absent; Reddit often returns an unreadable shell. In that case the job asks for pasted text instead of inventing insights.

One additional AI call identifies original writing angles with exact supporting quotes. Quotes are checked against the supplied source text. The writer receives summaries and angles, not copied comments, and the result shows linked evidence labelled as pasted or publicly read. Pasted text is not independently authenticated. These anecdotes do not establish prevalence or brand claims.

## Trend inspiration and comparison

Automatic discovery supplies references when relevant indexed results are available. Expand **Override trend research** to use your own references. Add one to three TikTok, Creative Center or Instagram links, your observations, observation date, and target region/language. Links are retained as references; this version does not watch videos, download music, scrape a live trend feed or verify momentum. Observations older than 14 days at generation are labelled for review.

The usual six-draft workflow creates the evergreen winner. One extra AI call produces an original adaptation using the supplied reference structure, with an explanation of the fit. Both appear in the editor. **Use trend-inspired draft** loads its words and clears the old clip selection; **Rebuild video** exports the selected direction with a matching reaction. Either draft can be edited. Saved exports of each direction have separate download links; the current choice also appears as `post.mp4`. Exports remain silent.

`trends.json` records sources, date, market and observations. `directions.json` preserves both drafts; `final.json` identifies the currently exported direction. Editorial fit is not a prediction of views. Real performance comparison requires publishing and measuring results, outside this demo.

Jenni AI is the new rehearsal brand: HardLaunch's public agency page names it in the founders' experience and describes consumer AI and study-tool work. It is a relevant test, not a prediction of their live test URL.

## Automatic research — default URL-only workflow

After profiling a brand, the app creates audience-problem search queries and uses [DDGS](https://github.com/deedy5/ddgs), an MIT-licensed metasearch library, to search indexed Reddit, TikTok and Instagram material. Searches run concurrently, with a recent-content filter for social references. A relevance review selects at most three audience and three content references. Every accepted summary must include an exact excerpt matching the returned search snippet; unknown IDs and invented evidence are rejected.

Reddit evidence informs the main writing; relevant content references create the second direction automatically. Research failures or failed adaptations leave the evergreen export available. Manual inputs are overrides, and **Skip automatic research** disables discovery for that run. Successful research is cached locally for 24 hours per brand URL to avoid repeated collection. This adds two model calls, plus an adaptation call when references exist.

The **Automatic research** panel and `research.json` record queries, source URLs, excerpts, summaries, collection time, coverage and errors. Source publication dates may be unknown or older than the search window. TikTok discovery pages are labelled as topic signals. No direct social account credentials or Apify token are configured; search discovery works without them. It does not provide platform-wide rankings, watched-video analysis or measured growth. Full trend velocity would require time-series metrics from a separate collector. No recurring background job is created.

Verified URL-only example: `https://opalapp.com/`. It found Reddit and TikTok evidence and produced drafts and a playable MP4; no manual research inputs were supplied. Instagram searches can yield no relevant results, which the coverage panel reports.

## Brand research reliability

The current research version always searches the quoted brand name on Reddit, TikTok and Instagram, separately from audience/category queries. Each search tries Bing first and retries empty, failed or unusable results through DuckDuckGo with a simpler query and no recency restriction. Six searches have at most two attempts each. Sources are deduplicated and labelled as brand mentions, audience discussions or category references; topic pages are identified explicitly.

The results panel separates found and selected counts, shows search attempts and failures, and retains reasons for unselected candidates. Exact evidence checks still apply. Cache keys include the research version and profile to avoid reusing earlier broad-only searches. Dates extracted from snippets are labelled unverified.

Automatic alternate drafts are labelled **Research-inspired**, not trending. They must cite a supplied URL and matching evidence, then pass a separate editorial alignment check. A draft that sidesteps its reference, invents product claims or shares only a broad category is rejected; the evergreen video remains the output. This validation is AI-assisted editorial review, not proof of trend performance.
