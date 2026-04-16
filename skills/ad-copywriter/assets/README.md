# Ad Copywriter — Assets

This folder holds templates and reusable assets for the ad-copywriter skill.

## Current Assets

None yet. Unlike paid-media-strategy (which has HTML dashboard templates), ad-copywriter outputs are markdown and CSV — generated from reference specs, not templates.

## When Templates Might Be Added

- If a CSV import template format changes for Google Ads Editor or Meta Business Suite bulk upload
- If a standardized storyboard visual template (HTML/PDF) is needed for client presentation
- If carousel ad card templates become repetitive enough to templatize

## Output Files (Generated, Not Templated)

All outputs are generated fresh per client using specs from `references/output-format-spec.md`:
- `{business-name}-ad-copy-report.md` — main deliverable
- `{business-name}-google-ads.csv` — Google Ads Editor import
- `{business-name}-meta-ads.csv` — Meta bulk upload
- `{business-name}-image-prompts.md` — Gemini image generation prompts
- `{business-name}-video-storyboards.md` — frame-by-frame video storyboards with VO
