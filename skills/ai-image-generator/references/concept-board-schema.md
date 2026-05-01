# Concept Board Schema — Input + Output Contracts

The concept-board.json is the central planning document. It's produced by `parse_brief.py` from one of three input forms (A: ad-copywriter image-prompts.json, B: free-form markdown, C: standalone brief). It's then consumed by `plan_generations.py` to build the MCP call queue.

## Concept board JSON shape

```json
{
  "campaign_id": "WLF-2026-05",
  "client": "ISKM Singapore",
  "project": "Weekend Love Feast Meta Creatives",
  "goal": "registrations",
  "landing_url": "https://events.srikrishnamandir.org/weekend-love-feast",
  "voice_register": "religious-grounded",
  "brand_colors": {"primary": "#7B4F2C", "accent": "#FFB75A", "bg": "#0F0B07"},
  "concepts": [
    {
      "concept_id": "01-prasadam-invite",
      "concept_name": "Prasadam invite — atmospheric brass thali",
      "intent": "cover_slide",
      "creative_direction": "Top-down brass thali heaped with sattvic prasadam, warm candlelight, rose petals scattered, devotional ambiance. Title overlay reads 'Sunday Love Feast — Free for Everyone' in serif typography. Sub: 'Sunday 12 May | 6 PM | Sri Krishna Mandir Singapore'. Devotional warmth, not luxury food photography.",
      "intended_placement": ["meta_feed", "meta_explore", "instagram_feed"],
      "tags": ["prasadam", "atmospheric", "typography_medium"],
      "variations": [
        {
          "variation_id": "v1",
          "model_choice": "nano_banana_flash",
          "aspect_ratio": "1:1",
          "resolution": "2k",
          "prompt": "...",
          "negative_prompt": "no AI faces, no inappropriate religious imagery, no luxury restaurant aesthetic, no cluttered text",
          "reference_image_ids": ["prasadam-thali-real-01.jpg"],
          "reference_role": "style",
          "expected_credits": 0,
          "voice_check": "PASS"
        },
        {
          "variation_id": "v2",
          "model_choice": "nano_banana_flash",
          "aspect_ratio": "4:5",
          "resolution": "2k",
          "prompt": "(same prompt, 4:5 framing)",
          "reference_image_ids": ["prasadam-thali-real-01.jpg"],
          "reference_role": "style",
          "expected_credits": 0,
          "voice_check": "PASS"
        },
        {
          "variation_id": "v3-premium",
          "model_choice": "gpt_image_2",
          "aspect_ratio": "1:1",
          "resolution": "2k",
          "prompt": "(same prompt, premium typography focus)",
          "reference_image_ids": ["prasadam-thali-real-01.jpg"],
          "reference_role": "style",
          "expected_credits": 6,
          "voice_check": "PASS"
        }
      ]
    },
    {
      "concept_id": "02-deity-darshan-composite",
      "concept_name": "Deity darshan — composite frame",
      "intent": "cover_slide",
      "creative_direction": "Background atmospheric (temple interior, candles, marigold garlands), with space reserved for the deity reference photo to be composited in. Generated frame contains background + decorative elements + typography only — sacred subject is composited post-generation, not redrawn.",
      "intended_placement": ["meta_feed", "instagram_feed"],
      "tags": ["sacred_composite", "background_only"],
      "variations": [
        {
          "variation_id": "v1",
          "model_choice": "soul_location",
          "aspect_ratio": "1:1",
          "resolution": "2k",
          "prompt": "Temple interior background, soft warm candlelight, marigold garland frames the upper portion, central area reserved as a clean rectangular space for portrait composite. Bottom third holds the title 'Sunday Love Feast' and date strip. No human or deity figures generated. Devotional, sacred.",
          "negative_prompt": "no faces, no figures, no deity, no people",
          "reference_image_ids": [],
          "reference_role": "none",
          "expected_credits": 5,
          "voice_check": "PASS",
          "post_generation_composite": {
            "deity_image": "deity-radha-krishna-01.jpg",
            "placement": "centered, 60% of frame height"
          }
        }
      ]
    }
  ],
  "totals": {
    "total_generations": 4,
    "free_generations": 2,
    "paid_generations": 2,
    "total_credits_estimate": 11
  },
  "created_at": "2026-05-01T...",
  "form": "C"
}
```

## Field reference

### Top level

| Field             | Required | Notes                                                          |
|-------------------|----------|----------------------------------------------------------------|
| `campaign_id`     | yes      | Short slug, e.g. `WLF-2026-05`                                 |
| `client`          | yes      | Folder name on Desktop                                         |
| `project`         | yes      | Project folder under client                                    |
| `goal`            | yes      | `registrations` / `sales` / `leads` / `awareness`              |
| `landing_url`     | optional | Used in voice-check + dashboard                                |
| `voice_register`  | yes      | `grounded-default` / `religious-grounded` / `humor-domain` / `luxury` (drives copywriting-rules.md application) |
| `brand_colors`    | optional | Read from client wiki if not provided                          |
| `concepts[]`      | yes      | At least one concept                                           |
| `form`            | yes      | `A` (ad-copywriter), `B` (markdown brief), `C` (standalone)    |

### Per concept

| Field                | Required | Notes                                                                |
|----------------------|----------|----------------------------------------------------------------------|
| `concept_id`         | yes      | `NN-slug` format, sortable                                           |
| `concept_name`       | yes      | Human-readable                                                       |
| `intent`             | yes      | `cover_slide` / `body_slide` / `ad_product_hero` / `hero_landing` / `ugc` / `character_consistent` / `edit_reference` / `wide_banner` / `stylized` / `lifestyle` / `atmospheric` |
| `creative_direction` | yes      | One paragraph human description, prose                               |
| `intended_placement` | yes      | Array of placements — drives aspect ratio matrix                     |
| `tags`              | optional  | Free-form tags for routing + filtering                               |
| `variations[]`       | yes      | At least one variation                                               |

### Per variation

| Field                       | Required | Notes                                                                |
|-----------------------------|----------|----------------------------------------------------------------------|
| `variation_id`              | yes      | `v1` / `v2` / `v3-premium` etc.                                      |
| `model_choice`              | yes      | Verified Higgsfield model ID — see model-routing.md                  |
| `aspect_ratio`              | yes      | Must be supported by model — validator catches mismatches            |
| `resolution`                | yes      | `1k` / `2k` / `4k` per model spec                                    |
| `prompt`                    | yes      | Full structured prompt                                               |
| `negative_prompt`           | optional | What to exclude — useful for sector sensitivity                      |
| `reference_image_ids`       | optional | Array of reference image filenames (resolved to UUIDs at queue time) |
| `reference_role`            | optional | `none` / `style` / `composition` / `subject_lock` / `subject_lock_no_redraw` |
| `expected_credits`          | yes      | 0 for unlimited tier, integer for paid                               |
| `voice_check`               | yes      | `PASS` / `FAIL` — set by parse_brief voice scanner                   |
| `post_generation_composite` | optional | If sacred subject must be composited post-gen, this describes how    |

## Placement → aspect ratio matrix (defaults)

| Intended placement                      | Default aspect(s)         |
|-----------------------------------------|---------------------------|
| `meta_feed` / `instagram_feed`          | 4:5 + 1:1                 |
| `meta_explore`                          | 1:1                       |
| `meta_story` / `instagram_story` / `instagram_reel_cover` | 9:16 |
| `meta_marketplace`                      | 1:1                       |
| `linkedin_feed`                         | 1.91:1 → use 1.91:1 if model supports, else 16:9 |
| `linkedin_carousel`                     | 1:1 (carousel rule)       |
| `google_display_300x250`                | 1.2:1 → 4:3 closest       |
| `google_display_300x600`                | 1:2 → 9:16 closest        |
| `google_display_728x90`                 | 8:1 → no model supports → render at 16:9 + crop |
| `google_display_responsive`             | 1.91:1 + 1:1 + 4:5        |
| `landing_page_hero_desktop`             | 16:9 or 21:9              |
| `landing_page_hero_mobile`              | 4:5 or 9:16               |

`parse_brief.py` reads each concept's `intended_placement[]` and emits one variation per (placement, model_choice) pair. The variation id includes the aspect (e.g. `v1-1x1`, `v1-4x5`).

## Voice check

Before any concept enters the queue, `parse_brief.py` scans:

- `prompt` text for: em dashes, hype words (game-changer, revolutionary, ultimate, transform), engagement bait (DM me, like if, comment below)
- `creative_direction` text for the same
- Any text rendered into the image (extracted from prompt) for the same
- Religious-sector concepts: scan for inappropriate descriptors of sacred subjects

Failures get `voice_check: "FAIL"` with reason. `plan_generations.py` skips FAIL variations and prints the failure list — analyst rewrites and re-runs.

## Idempotency

Concept-board entries are stable. Re-running `plan_generations.py` against the same concept-board.json:
- Skips variations whose output PNG already exists
- Re-queues variations marked `[FAILED]` in manifest
- Adds new variations if the concept-board.json was edited to include them
