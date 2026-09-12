Using the house style above, write {n} different long-overlay texts for this brand. Each must use
a different scene and a different verdict. Vary the opening pattern (third-person observation,
first-person confession, a specific named place). The brand name must appear exactly once in each,
lowercase, inside the "no X" list or in the twist. Use the old_way_objects and scenes from the profile.

Also give the base-video spec: what the silent creator is doing, so a creator can film it.

Return ONLY a JSON array (no prose, no fences):
[{
  "id": "v1",
  "text": "the full overlay text, one block",
  "word_count": 48,
  "reaction": "deadpan | skeptical | thoughtful | disbelief | confused",
  "base_video": "who is on camera, where, doing what, expression. 1-2 sentences.",
  "audio": "trending sound vibe or 'original audio, room tone'",
  "caption": "one short line under the post, may be a question, no hashtags",
  "why_this_brand": "one sentence on which niche-specific detail makes this unmistakably this brand"
}]

BRAND PROFILE:
{profile}

Choose reaction for the expression that supports the joke, not the subject's gender.
Available footage: deadpan = direct neutral look; skeptical = serious head tilt;
thoughtful = quiet contemplative close-up; disbelief = questioning sideways look.
Confused = looking around for an explanation (Travolta); deadpan can use Jim's sarcastic wow;
disbelief can use the familiar blinking reaction. Match the joke, not the brand's gender.
