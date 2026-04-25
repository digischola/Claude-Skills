# content-plan.json schema

What the content-plan brain produces and the assembler consumes. One JSON file = one video edit.

## Top-level fields

```json
{
  "project_name": "2026-04-24-lp-audit-reel",
  "duration_sec": 21.0,
  "target_dims": { "width": 1080, "height": 1920 },
  "narrative_arc": "hook-framer",
  "preset": "apple-premium",
  "brand": {
    "bg": "#000000",
    "fg": "#F8FAFC",
    "muted": "#9BA8B9",
    "primary": "#3B9EFF",
    "primary_glow": "#6BB8FF",
    "success": "#4ADE80",
    "accent_danger": "#FF2D55",
    "card_bg": "#080808",
    "border": "#262626",
    "fonts_import": "https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600&family=Orbitron:wght@700&family=Space+Grotesk:wght@500;600;700&display=swap",
    "font_display": "Orbitron",
    "font_heading": "Space Grotesk",
    "font_body": "Manrope"
  },
  "source": {
    "video_path": "assets/source.mp4",
    "audio_path": "assets/source.mp4",
    "clip_start": 1.2,
    "clip_duration": 18.71
  },
  "transcript_path": "assets/transcript.json",
  "beats": [ ... ]
}
```

## Beat types

Every beat has `type`, `start`, `duration`. Additional fields depend on type.

### `hook`
```json
{ "type": "hook", "start": 0.0, "duration": 1.2,
  "main": "THE 5-SECOND RULE",
  "sub": "Why 40 wellness landing pages fail",
  "glow_tint": "primary" }
```

### `payoff`
```json
{ "type": "payoff", "start": 19.6, "duration": 1.4,
  "cta": "AUDIT YOUR LANDING PAGE",
  "wordmark": "DIGI|SCHOLA",
  "url": "DIGISCHOLA.IN" }
```
`wordmark` uses `|` to mark where the brand-primary highlight span begins.

### `lower-third`
```json
{ "type": "lower-third", "start": 3.2, "duration": 16.3,
  "primary": "MAYANK VERMA",
  "secondary": "FOUNDER · DIGI|SCHOLA" }
```

### `caption-phrase`
```json
{ "type": "caption-phrase", "start": 1.27, "duration": 1.47,
  "words": [
    { "text": "I", "class": "word" },
    { "text": "audited", "class": "word" },
    { "text": "40", "class": "metric" },
    { "text": "wellness", "class": "word" }
  ] }
```
`class` = `word | accent | metric` — controls per-word style.

### `caption-wordpop`
Same as `caption-phrase` but includes word-level `start`/`end` for per-word scale-pop animation:
```json
{ "type": "caption-wordpop", "start": 1.27, "duration": 1.47,
  "words": [
    { "text": "I", "class": "word", "start": 1.27, "end": 1.38 },
    { "text": "audited", "class": "word", "start": 1.38, "end": 1.76 },
    ...
  ] }
```

### `broll-landing-page`
```json
{ "type": "broll-landing-page", "start": 4.9, "duration": 3.0,
  "chrome_style": "safari-light",
  "url": "acme.co",
  "page_title": "The solution your team needs to scale growth",
  "page_copy": "We help businesses at every stage...",
  "cta_text": "GET STARTED",
  "scroll_from": 0, "scroll_to": -1400,
  "cursor_from": "18%", "cursor_to": "70%" }
```

### `broll-form-shrinking`
```json
{ "type": "broll-form-shrinking", "start": 12.1, "duration": 1.3,
  "form_title": "Request a demo",
  "fields_long": ["First name", "Last name", "Company", "Phone", "Website", "Annual revenue"],
  "fields_keep": ["Email", "Company"],
  "callout_text": "-66%",
  "callout_color": "success" }
```

### `metric-hero`
```json
{ "type": "metric-hero", "start": 13.4, "duration": 2.05,
  "prefix": "+",
  "target_value": 120,
  "suffix": "%",
  "label": "CONVERSION LIFT",
  "color": "success" }
```

### `arrow-callout`
```json
{ "type": "arrow-callout", "start": 5.2, "duration": 2.4,
  "from": [820, 900],
  "to": [640, 520],
  "control": [920, 700],
  "label": "VAGUE HOOK",
  "label_pos": { "right": 60, "top": 880 },
  "color": "accent_danger" }
```

### `zoom-punch`
```json
{ "type": "zoom-punch", "start": 7.0,
  "target": "#video-stage",
  "intensity": "subtle",
  "hold": 0.2, "recovery": 0.6 }
```

### `takeover-text`
```json
{ "type": "takeover-text", "start": 11.0, "duration": 1.0,
  "text": "YOU'VE\nLOST THEM.",
  "color": "accent_danger",
  "font": "Orbitron",
  "size_px": 160 }
```

### `video-dim`
```json
{ "type": "video-dim", "start": 13.4, "duration": 1.9,
  "target_opacity": 0.55 }
```

Brand tokens like `"color": "success"` are resolved against `brand` at assembly time (e.g. `success` → `#4ADE80`).
