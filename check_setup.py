"""Run this first on the day. Confirms key, SDK and one real call in under 10 seconds."""
import os
import sys

from dotenv import load_dotenv

load_dotenv()
if not os.getenv("ANTHROPIC_API_KEY"):
    sys.exit("ANTHROPIC_API_KEY missing. Copy .env.example to .env and paste your key.")

import anthropic  # noqa: E402

r = anthropic.Anthropic().messages.create(
    model="claude-opus-5",
    max_tokens=50,
    output_config={"effort": "low"},
    messages=[{"role": "user", "content": "Reply with the single word OK."}],
)
print("API OK:", "".join(b.text for b in r.content if b.type == "text").strip())
