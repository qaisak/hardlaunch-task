# Rationale

I chose a reaction-led text format because the brief identifies long overlays as the team's dominant format. One relatable scene, a specific problem and a dry payoff are easier to judge than a large number of generic scripts. The prototype exports a finished vertical MP4, with the reaction above a separate reading panel so the face and copy stay clear.

A brand URL starts the workflow. Python reads the homepage and supporting pages, with a web-fetch fallback for thin responses. Claude organises that text into a profile covering audience, product, problems, tone and supporting facts. It recommends a format, writes six candidate posts, critiques them and revises the strongest. The format recommendation is advisory: this implementation exports one format only.

The final post also supplies a reaction label. A local catalogue maps labels to stock footage and familiar reaction references; older examples use deterministic text rules. The editor can replace the selected clip, edit the text and caption, and rebuild without another writing call. Clips loop for a duration based on reading time. Exports are silent, and suggested audio is not represented as an included asset.

The system uses Python, Claude through the Anthropic SDK, requests, BeautifulSoup, Pillow and FFmpeg. A small local web interface shows generation progress, previews results and downloads MP4s. Claude Code and Codex assisted development.

The main tradeoffs are a small curated clip library, variable source resolution, and a formula that suits some brands better than others. Reaction references are included for this personal demonstration, not presented as a cleared commercial asset library. Thin websites can produce weak profiles, and AI editorial scores are not evidence of real performance. With more time I would strengthen fact checks, add a slideshow renderer, expand the labelled footage library and calibrate selection against actual creator feedback and audience results.
