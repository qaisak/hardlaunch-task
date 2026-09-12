# Rationale

_Draft. Qais to edit into his own voice and cut to 200-400 words before hand-in._

## What format I chose and why

Long overlay. Three reasons. It is your dominant format, so taste is easiest to judge and most
useful to get right. It is text-first, so a system can produce a finished, postable piece for any
URL without generating or sourcing video, which is what lets it generalise in four hours. And the
reference piece gives the voice precisely: observational opening, the "no X. no Y." list, one absurd
escalation, a deadpan verdict, brand named once and never sold. That is a learnable structure, so I
wrote it down as seven rules and made every draft and every critique answer to them.

The system still makes the format decision (overlay vs slideshow vs hook+demo, with a reason) and
records it, so the choice is visible even though only one renderer exists.

## How it works end to end

URL in. Scrape the homepage plus an about page; if the site is a JS shell, Claude's web fetch reads it
instead. One call turns the text into a brand profile whose most important field is `old_way_objects`,
the exact tools and habits people use instead of the product, because that list is what makes an
overlay unmistakably this brand rather than any brand. Six drafts are written in the house style, each a
different scene. A strict editor scores them on on-brand, voice, hook, not-an-ad, comment bait, honesty
and length, and names one fix. The fix is applied to the winner. The text is burned onto a 9:16 frame
and the pack is written out with base-video spec, audio, caption and runners-up.

## Tools

Python, Claude Opus 5 through the Anthropic SDK (including its web fetch tool as the scrape fallback),
requests and BeautifulSoup for ingestion, Pillow for the render. Built with Claude Code. Prompts are
files, not code, so a content person can change taste without touching Python.

## Where it breaks, and what I would do with more time

- Thin sites. When the fallback only recovers a few hundred characters, the profile leans on inferred
  niche knowledge and the overlay can drift generic. Fix: fetch two or three more pages and the app store
  listing, and refuse to draft when the profile has fewer than N grounded facts.
- Brands with no relatable "old way" (B2B infrastructure, luxury). Overlay is the wrong format there and
  the selector says so, but there is no slideshow renderer yet. Next: build it, it is the same loop with a
  per-slide schema.
- The critic is calibrated on rules, not results. With a week I would feed real post performance back
  into the scorer and, since you run 100+ accounts, treat hooks as an experiment: post the top three
  variants across accounts in the same window, promote on 3s hold rate, retire the rest after 48 hours.
- No learned voice per brand yet. Tested on calorie app, study tool, natural deodorant, and it held;
  a fashion or finance brand with a strict tone of voice would need the profile to carry more of it.
