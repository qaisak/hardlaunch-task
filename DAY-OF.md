# Saturday 12 Sept, 11:00 to 15:00 Oman time (14:00 to 18:00 Thai)

## Before 11:00 (30 min, in order)
- [ ] Eat. Water. Phone on silent except email / WhatsApp from Matt.
- [ ] PowerShell (use `;` between commands, never `&&`): `cd C:\Users\Qais\hardlaunch-task; .venv\Scripts\activate`
- [ ] Paste your API key into `.env` (copy `.env.example` to `.env` first) and run `python check_setup.py`
- [ ] `python generate.py inputs/sample_brief.md --n 3 --top 1` and read `out/sample_brief.md` once,
      so you know what the system produces before the brief arrives
- [ ] Open README.md, RATIONALE.md, prompts/taste.md in the editor. Claude Code open in this folder.
- [ ] When the brief lands, reply "Received, starting now" so the clock is unambiguous.

## 11:00 to 11:20  Read and decide
- Read the brief twice. Write at the top of RATIONALE.md: input, output, what "good" means, what is ambiguous.
- Send Matt 2 or 3 clarifying questions NOW. Timestamp them in RATIONALE.md.
- Pick the narrowest version that still demonstrates views-per-post. Write "in scope / out of scope".

## 11:20 to 12:00  Ship v0
- Adapt `load_input()` and the JSON schema in `prompts/generate.md` to the actual brief.
- Run end to end on their sample input. `git add -A; git commit -m "v0 end to end"`.

## 12:00 to 14:00  Make the output good
- First candidate improvement: a revise pass that applies each variant's 'Editor fix' and re-scores. Cheap, visible quality jump.
- Read the output like Matt would. Fix `prompts/taste.md` before touching code.
- Keep the loop: generate variants, critique, rank. Add whatever the brief needs on top.
- Commit after each working improvement.
- Stuck 15 min on anything? Message Matt. They said to.

## 14:00 to 14:30  Break it
- Run on 2 or 3 inputs of a different kind than their sample (other niche, messier, shorter).
- Fix the worst failure. Write the rest under "Where it breaks".

## 14:30 to 15:00  Rationale and hand-in. NO NEW CODE.
- Fill RATIONALE.md fully. One page.
- Do the README run instructions work from a clean clone? Check.
- Remove `out/` from .gitignore so sample output ships. `git commit -m "final"`, push or zip, send.

## Questions to have ready for the first 20 min (pick what applies)
- Platform and length? (TikTok, 20-40s assumed if unsaid)
- Any past performance data, or cold start?
- Output as scripts / hooks / captions only, or also a visual spec / storyboard?
- Is views the only objective, or is there a conversion constraint to respect?
- How will you test it, CLI on a file? (so it matches their harness)

## Hand-in checklist
- [ ] Runs from README in one command
- [ ] Sample output committed in out/
- [ ] RATIONALE.md complete, escalations with timestamps
- [ ] Known failures listed honestly
