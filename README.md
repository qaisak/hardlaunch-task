# Short-form content generator

Input (brief / transcript / past-post data) -> N hook-and-format variants -> strict critique
pass -> ranked output with a suggested test plan.

## Run
```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env        (paste ANTHROPIC_API_KEY into .env)
python check_setup.py
python generate.py inputs/sample_brief.md --n 8 --top 3
```
Output lands in `out/<input>.md` (readable) plus `.variants.json` and `.scores.json`.

`--dry-run` runs the whole pipeline with placeholder content and no API calls.

## How it works
1. `prompts/taste.md` is the content rulebook (hook, retention, share trigger, native-ness, format).
   It is the system prompt for every call. Edit this to change taste, not the code.
2. `prompts/generate.md` asks for N variants that differ in hook and format, as JSON.
3. `prompts/critique.md` scores each variant as a harsh editor (including an honesty check
   against the input) and names one fix per variant.
4. `generate.py` ranks by score, marks the top K as SHIP, and appends a test plan.

## Extending
- New input shape: edit `load_input()` in `generate.py`.
- New output shape: edit the JSON schema in `prompts/generate.md` and `render()`.

## Fallback backend
`python generate.py inputs/x.md --backend cli` runs the same pipeline through `claude -p`
(Claude Code subscription) instead of the API. Requires `claude` to be logged in. Set
`CLAUDE_CLI` if the binary is somewhere else.
