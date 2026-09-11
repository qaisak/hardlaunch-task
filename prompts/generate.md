Using the taste rules above, produce {n} distinct short-form video post variants from the
INPUT below. Vary the HOOK and FORMAT aggressively across variants; the underlying message
can stay the same. Do not produce near-duplicates.

Return ONLY a JSON array (no prose, no markdown fences). Each element:
{
  "id": "v1",
  "format": "name of the reusable format",
  "hook": {
    "visual": "what is on screen in the first 1.5s",
    "audio": "first spoken line (or 'silent / trending audio')",
    "text_overlay": "on-screen text in the first 1.5s, max 8 words"
  },
  "script": ["line 1", "line 2", "..."],   // 5-10 short spoken lines, each one a beat
  "on_screen_text": ["text beat 1", "..."], // optional text overlays for later beats
  "caption": "one line, optionally a question",
  "duration_s": 25,
  "share_reason": "who sends this to whom and why",
  "comment_trigger": "what makes people reply",
  "why_views": "one sentence on why this hook and format should raise hold rate"
}

INPUT:
{input}
