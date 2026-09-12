Below is text scraped from a brand's website. Build a brand profile for a short-form content team.
Be concrete. Every field must be specific to THIS brand and niche. If the site does not say
something, infer carefully from the niche and mark it with "(inferred)". Never invent numbers.

Return ONLY a JSON object (no prose, no fences):
{
  "brand_name": "as the brand writes it, lowercase if that is their style",
  "one_liner": "what it is, in 12 words or fewer, plain language",
  "niche": "e.g. calorie tracking app, study tool, running shoes, skincare",
  "product_type": "app | saas | physical product | service | marketplace | other",
  "audience": "who actually uses it, specific (age, situation, identity)",
  "core_pain": "the painful thing people do manually or badly without it",
  "old_way_objects": ["5-8 exact tools, objects, habits or rival products people use instead, lowercase, e.g. 'scales', 'myfitnesspal', 'a notes app'"],
  "scenes": ["3 real-life moments where the pain shows: place + person + what they are doing"],
  "tone": "3-5 words on how the brand talks",
  "proof_points": ["only facts stated on the site: numbers, awards, claims. empty list if none"],
  "do_not_say": ["claims or words that would be off-brand or legally risky"],
  "cta": "what the brand wants people to do (download, buy, sign up)"
}

WEBSITE TEXT:
{text}
