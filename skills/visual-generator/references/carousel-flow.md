# carousel-flow

Detailed steps for `visual-generator carousel`. Loaded only when rendering a carousel.

## Source

A draft with `format: carousel` (LinkedIn or Instagram) saved by `draft-week`. The body is the slide content — typically 8-10 sections separated by `## Slide N` headers.

## Step 1: Parse slides

Split the draft body on `## Slide N` headers. For each slide, extract:
- `headline` — first line of the section (≤120 chars for cover, ≤80 for inner slides)
- `body` — remaining text (≤160 chars per slide for IG, ≤200 for LI)
- `icon_hint` — optional, if a `[icon: name]` token is present

## Step 2: Build `slides.json`

```json
[
  {
    "slide_number": 1,
    "type": "cover",
    "headline": "...",
    "body": "...",
    "icon_hint": null,
    "background_style": "accent"
  },
  ...
]
```

`background_style` options: `accent` (cover, CTA), `neutral` (insight slides), `data` (metric slides).

## Step 3: Render

Two render paths:

### Path 1: Direct HTML render (default for personal-brand)

`scripts/render_html_carousel.py` reads `slides.json` and a Jinja template, applies brand tokens, and renders each slide via Playwright at 1080x1080 (IG square) or 1200x1500 (LI vertical).

```bash
python3 scripts/render_html_carousel.py \
  --brief <path>/slides.json \
  --out <path>/social-images/<entry_id>/ \
  --aspect 1080x1080 \
  --brand-folder /Users/digischola/Desktop/Digischola
```

### Path 2: Claude Design handoff (when bespoke design needed)

For posts that need stronger visual treatment (case studies, hero LP teardowns), use Claude Design:

```bash
python3 scripts/generate_brief.py \
  --draft <draft.md> \
  --out <path>/social-images/<entry_id>/brief.md
```

Then hand the brief to Claude Design separately. Claude Design renders a polished version and saves PNGs back to `social-images/<entry_id>/`.

## Step 4: Validate

```bash
python3 scripts/validate_output.py --carousel <output_dir>
```

Checks:
- 8-10 slides present
- All PNGs match target dimensions (no crop/aspect drift)
- Cover slide hook ≤120 chars
- Brand colors within 5% Lab delta of locked palette
- Font is Orbitron (display) / Space Grotesk (body) / Manrope (UI) — locked in brand-identity.md

## Anti-patterns

- Do NOT use AI illustration on a carousel cover unless the draft has `allow_ai_illustration: true` AND a clear non-photographic aesthetic.
- Do NOT exceed 10 slides — engagement drops off cliff after 10.
- Do NOT mix aspect ratios across slides.
- Do NOT use emojis beyond Restrained policy (max 1 per slide, never on the cover).
