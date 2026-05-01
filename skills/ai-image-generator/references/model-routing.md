# Model Routing — Cost-Aware Per-Concept Selection (Ultra Plan)

Every concept × variation × aspect ratio in the concept-board gets a `model_choice`. The router picks based on intent + cost budget. Override per concept with `--force-model <name>` on the CLI.

**Model IDs verified against Higgsfield `models_explore` 2026-05-01.** Update this file if Higgsfield changes IDs.

## Tier system (Ultra plan)

### Default tier — UNLIMITED on Ultra (0 credits)
| Model ID                 | Tier      | Strengths                                     | Best for                                |
|--------------------------|-----------|-----------------------------------------------|-----------------------------------------|
| `nano_banana_flash`      | Default   | Fast, photorealistic, decent text, all aspects, 4k | **Default for everything — variations, body slides, B-roll stills, lifestyle, product, atmospheric** |

### Premium tier — costs credits
| Model ID                 | Approx credits | Strengths                                     | Best for                                |
|--------------------------|----------------|-----------------------------------------------|-----------------------------------------|
| `nano_banana_2`          | ~5             | Top quality, text + diagrams, 4k              | Hero / cover slides / typography-heavy  |
| `gpt_image_2`            | ~5-8           | **Best text rendering, premium typography**   | Cover slide w/ event details, headline-heavy creative |
| `marketing_studio_image` | ~5             | Purpose-built for one-click product/social ads| Product hero shots, social-ad templates |
| `cinematic_studio_2_5`   | ~6             | Cinematic stills, dramatic lighting, 4k       | Luxury / wellness / film-aesthetic hero |
| `seedream_v4_5`          | ~6             | 4k, precise control, transformations          | Reference editing / style transfer      |
| `flux_2`                 | ~4             | Precise prompt adherence                      | Tricky prompts, creative latitude       |
| `flux_kontext`           | ~5             | Context-aware editing + style transfer        | Edit a reference image, style transfer  |
| `soul_2`                 | ~5             | UGC, fashion, character generation            | Real-feel UGC ads, fashion              |
| `soul_cast`              | budget param   | **Consistent character identity reuse**       | Same person across multiple creatives   |
| `soul_cinematic`         | ~5             | Cinema-grade stills + concept art             | Concept-art style premium hero          |
| `soul_location`          | ~5             | Environment / background generation           | Location plate for composite work       |
| `kling_omni_image`       | ~4             | Photorealistic, wide aspects (21:9)           | Banner + GDN responsive                 |
| `grok_image`             | ~4             | Expressive, high-contrast, bold               | Bold/loud creative angles               |
| `gpt_image`              | ~4             | GPT Image 1.5 — typography                    | Typography fallback                     |
| `image_auto`             | varies         | Higgsfield auto-routes                        | When unsure                             |
| `z_image`                | ~2             | Super fast stylized                           | Quick stylized variants                 |

*Credit values are observed approximations. Run `balance` before/after to confirm actual deltas. Higgsfield can change pricing.*

## Router decision tree

```
For each concept × variation:

  IF concept.intent == "ad_product_hero" OR tags contain "product_shot":
      → marketing_studio_image
  ELIF concept.intent == "cover_slide" AND text_density == "heavy":
      → gpt_image_2 (best text rendering)
  ELIF concept.intent == "cover_slide" AND text_density == "medium":
      → nano_banana_2 (Pro — strong typography + photorealistic)
  ELIF concept.intent == "hero_landing" OR tags contain "luxury":
      → cinematic_studio_2_5
  ELIF concept.intent == "character_consistent" (same person across N creatives):
      → soul_cast (define soul_id once, reuse across all variations)
  ELIF concept.intent == "ugc" OR tags contain "creator_style":
      → soul_2
  ELIF concept.intent == "edit_reference" OR concept.has_reference AND reference_role == "style":
      → flux_kontext OR seedream_v4_5
  ELIF concept.intent == "stylized" OR tags contain "abstract":
      → grok_image OR z_image (cheap)
  ELIF concept.intent == "wide_banner" (21:9 GDN):
      → kling_omni_image (wide aspect support)
  ELSE:
      → nano_banana_flash (DEFAULT — unlimited, photorealistic)
```

## Variation strategy

For each concept, generate **3 variations × N aspect ratios** by default:

- **Variation 1:** primary prompt as-written, `nano_banana_flash` (unlimited)
- **Variation 2:** prompt with composition rotated (close-up vs wide, top-down vs side angle), `nano_banana_flash`
- **Variation 3:** premium tier with same primary prompt — `nano_banana_2` Pro for typography concepts, `gpt_image_2` for headline-heavy, `marketing_studio_image` for product

Result: 2 free + 1 paid per concept × N aspects. For 6 concepts × 2 aspects (1:1 + 4:5) = 12 free + 12 paid = 24 images, ~60-90 credits.

## Aspect ratio handling per model

Verified against `models_explore` 2026-05-01:

| Aspects supported (besides 1:1)                    | Models                                                |
|----------------------------------------------------|-------------------------------------------------------|
| 4:5, 5:4, 9:16, 16:9, 21:9, 4:3, 3:4, 3:2, 2:3     | nano_banana_flash, nano_banana_2, marketing_studio_image, seedream_v4_5 |
| 4:3, 3:4, 16:9, 9:16, 3:2, 2:3 (no 21:9)           | gpt_image_2                                           |
| 4:3, 3:4, 16:9, 9:16, 21:9 (no 4:5)                | kling_omni_image, seedream_v4_5                       |
| 4:3, 3:4, 16:9, 9:16 only                          | soul_2, soul_cast, soul_cinematic, soul_location, flux_2, flux_kontext, grok_image, z_image, cinematic_studio_2_5 |
| 1:1, 3:2, 2:3, auto only (NO 4:5 — gotcha for Meta) | gpt_image (1.5)                                       |

**Meta-ad gotcha:** Meta's primary feed placement is **4:5**. If routing to `gpt_image` (1.5) or any model without 4:5 support, fall back to 1:1 for feed and warn — or escalate to `nano_banana_flash` / `nano_banana_2` / `gpt_image_2` which support 4:5 natively.

## Resolution defaults

- **Variations / dashboard review:** 1k (faster, cheaper, good enough to evaluate)
- **Final winners:** 2k (delivery quality)
- **Hero / landing-page:** 4k (where supported — `nano_banana_*`, `gpt_image_2`, `marketing_studio_image`, `cinematic_studio_2_5`)

`plan_generations.py` defaults to 2k for everything except known cheap-mode variants which stay at 1k.

## Cost budgeting

Default safe budget: **150 credits per campaign run.** Triggers:

| Estimated burn (paid models only) | Action                                |
|-----------------------------------|---------------------------------------|
| ≤ 50 credits                      | Run silently                          |
| 51-150                            | Print warning, log, continue          |
| 151-400                           | Require `--confirm-cost` flag         |
| > 400                             | Abort — explain, ask for explicit OK  |

`plan_generations.py` prints the manifest preview before generation:

```
Concept-board generation summary
─────────────────────────────────
01-prasadam-invite  v1  1:1  nano_banana_flash      0 cr   "warm candlelight + brass thali..."
01-prasadam-invite  v1  4:5  nano_banana_flash      0 cr   "..."
01-prasadam-invite  v3  1:1  gpt_image_2            6 cr   "...with title overlay rendered..."
02-deity-darshan    v1  1:1  nano_banana_flash      0 cr   "[ref: deity-01.jpg, role: composite]..."
...
Total: 24 generations, 12 unlimited + 12 paid = ~72 credits, ~$2.40 at Ultra rate
Proceed? (y/n)
```

## Reference-image flow (when references attached)

For concepts with `reference_image_ids`:

1. Inventory step pre-uploaded each reference via `media_upload` → UUIDs in `reference-manifest.json`
2. `plan_generations.py` attaches matching UUIDs to the gen call as `medias: [{role: "image", value: uuid}]`
3. The model uses references for layout, lighting, style, or subject-lock per `reference_role`
4. Manifest logs both the reference UUIDs AND the generation as separate-but-linked entries

**Sacred-reference rule:** if `reference_role == "subject_lock_no_redraw"` (set by religious-brand guardrail in inventory step), the model is asked to generate background, typography, and atmospheric elements only — the sacred subject is composited in post-generation, not regenerated. Best models for this pattern: `flux_kontext` (preserves reference subject + edits surround), `soul_location` (background-only generation).

## Learning hook (future)

`manifest.json` per gen + ad performance data (post-launch-optimization output) will eventually feed:

- Per-model CTR / CPM by ad format and concept type
- Cost-per-effective-creative by client industry
- Promote/demote tier moves

After 50+ delivered creatives with downstream perf data, write `scripts/analyze_model_performance.py` to surface insights.
