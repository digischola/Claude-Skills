# Ad Copywriter — Assets

This folder holds templates and reusable assets for the ad-copywriter skill.

## Current Assets

None yet. Unlike paid-media-strategy (which has HTML dashboard templates), ad-copywriter outputs are markdown and CSV — generated from reference specs, not templates.

## When Templates Might Be Added

- If a CSV import template format changes for Google Ads Editor or Meta Business Suite bulk upload
- If a standardized storyboard visual template (HTML/PDF) is needed for client presentation
- If carousel ad card templates become repetitive enough to templatize

## Output Files (Generated, Not Templated)

All outputs are generated fresh per client using specs from `references/output-format-spec.md`. Files are written to `_engine/working/` (folder location encodes client + program — no client/business name prefix in the filename):
- `ad-copy-report.md` — main deliverable
- `google-ads.csv` — Google Ads Editor import
- `meta-ads.csv` — Meta bulk upload
- `image-prompts.md` — Gemini image generation prompts
- `video-storyboards.md` — frame-by-frame video storyboards with VO
- `prompt-library.html` — at the client/program folder root (presentable)
