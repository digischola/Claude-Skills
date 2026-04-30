# Model Routing — Cost-Aware Per-Scene Selection

Every scene in the scene_plan gets a `model_choice`. The router picks based on scene type + cost budget. Override per scene with `--force-model <name>` on the CLI.

**Model IDs verified against Higgsfield `models_explore` 2026-04-30.** Update this file if Higgsfield changes IDs.

## Model matrix (Higgsfield 2026-04-30)

| Model ID                | Credits/clip* | Strengths                                    | Best for                          |
|-------------------------|---------------|----------------------------------------------|-----------------------------------|
| `kling3_0`              | 6             | Cheap, fast, decent realism, multi-shot      | Default B-roll, lifestyle, action |
| `kling2_6`              | 8             | Cinematic motion, advanced physics           | Premium-feel B-roll               |
| `minimax_hailuo`        | 10            | Natural physics, facial emotion              | Dialogue, character-driven        |
| `seedance_1_5`          | 18            | Reliable motion, versatile                   | General-purpose                   |
| `veo3_1_lite`           | 20            | Budget Veo, fast, batch                      | **Cheap establishing shots**      |
| `seedance_2_0`          | 25            | Reference-driven, consistent identity        | Product shots, multi-SKU          |
| `grok_video`            | 25            | T2V/I2V with audio                           | Versatile fallback                |
| `marketing_studio_video`| 30            | **UGC/Tutorial/Unboxing/TV Spot ad modes**   | **Client ads (TikTok/Reels)**     |
| `wan2_6`                | 30            | Stylized, experimental (needs start_image)   | Stylized brand work               |
| `veo3`                  | 35            | Cinematic, requires start_image              | Cinematic with reference          |
| `wan2_7`                | 35            | Audio-synced, character-consistent           | Audio-driven content              |
| `veo3_1`                | 50            | Ultra-realistic, top-tier cinema             | **Hero / money shots**            |
| `cinematic_studio_3_0`  | 60            | Most advanced cinema-grade                   | Premium hero (only when justified)|

*Approximate. Higgsfield adjusts. Run `balance` before/after to see actual deltas.

## Router decision tree

```
For each scene in storyboard:

  IF scene.tags contains "ad_ugc" / "ad_tutorial" / "ad_unboxing" / "ad_product_review" / "ad_tv_spot":
      → marketing_studio_video  (with corresponding mode)
  ELIF scene.tags contains "hero" OR "key_brand_moment" OR "money_shot":
      → veo3_1
  ELIF scene.tags contains "establishing":
      → veo3_1_lite           (cheap Veo for non-money establishing shots)
  ELIF scene.tags contains "stylized" OR "anime" OR "abstract":
      → wan2_6                (needs reference image — generate_image first)
  ELIF scene.tags contains "product" OR "text_on_screen" OR "ui_demo":
      → seedance_2_0
  ELIF scene.tags contains "dialogue" OR "character_action":
      → minimax_hailuo
  ELIF scene.tags contains "cinematic_premium":
      → cinematic_studio_3_0   (premium hero only — 60cr is steep)
  ELIF scene.tags contains "lifestyle" OR "broll" OR "transition":
      → kling3_0
  ELSE:
      → kling3_0  (default — cheapest)
```

## Tag inference from storyboard prompts

When the input doesn't pre-tag scenes, `parse_brief.py` infers from prompt language:

- "unboxing", "tutorial", "product review", "UGC", "user-generated" → `ad_ugc`
- "wide shot", "drone", "aerial", "sweeping" → `hero`
- "establishing", "opening shot", "landscape" → `establishing`
- "product close-up", "screen recording", "UI", "logo" → `product`
- "talking", "speaking", "conversation", "person says" → `dialogue`
- "yoga", "lifestyle", "morning routine", "outdoor", "smiling" → `lifestyle`
- "anime", "illustrated", "cartoon", "abstract" → `stylized`
- default → no tag → kling3_0

## Marketing Studio modes (UGC ad work)

When routing to `marketing_studio_video`, also pick a mode based on the scene:

| Mode             | Use when scene is...                                       |
|------------------|------------------------------------------------------------|
| `UGC`            | First-person creator-style ad, hand-held aesthetic         |
| `Tutorial`       | How-to, step-by-step instructional                         |
| `Unboxing`       | Product reveal, packaging, first-impression                |
| `Hyper Motion`   | High-energy, fast-cut, attention-grabbing opener           |
| `Product Review` | Demonstrative, comparison, feature walkthrough             |
| `TV Spot`        | Broadcast-quality ad with polished cinematography          |
| `Wild Card`      | Experimental / category-bending                            |
| `UGC Virtual Try On` | Try-on UGC for fashion/beauty/eyewear                  |
| `Pro Virtual Try On` | Polished try-on for premium fashion                    |

## Scene count budgeting

Default safe budget: **100 credits per video.** Triggers:

| Estimated burn | Action                                |
|----------------|---------------------------------------|
| ≤ 100 credits  | Run silently                          |
| 101-250        | Print warning, log, continue          |
| 251-500        | Require `--confirm-cost` flag         |
| > 500          | Abort — explain, ask for explicit OK  |

`parse_brief.py` prints the manifest preview before generation:

```
Scene plan summary
─────────────────
01  hero           veo3_1                50 cr   "wide aerial drone over Goa beach..."
02  ad_ugc         marketing_studio_video 30 cr   "creator unboxing the welcome kit..."
03  lifestyle      kling3_0                6 cr   "yoga teacher demonstrating pose..."
04  product        seedance_2_0           25 cr   "close-up of branded merchandise..."

Total: 4 scenes, 111 credits, ~$4.40 at Plus tier
Proceed? (y/n)
```

## Image-to-video flow (when reference frames matter)

For scenes that need character consistency or specific composition (or models that REQUIRE a start_image — `wan2_6`, `veo3`):

1. Generate reference image first via `generate_image` (Soul or Flux) — 4-5 credits
2. Use the resulting `job_id` (or upload-returned UUID) as `medias[].value` with `role: "start_image"`
3. Manifest logs both the image generation AND the video generation as separate entries

Use case: Thrive Retreats sequence where the same yoga teacher appears in 3 scenes — generate one Soul Cast reference, reuse across clips for character consistency.

## Aspect ratio handling per model

Not all models support all aspects. Verified:

| Aspects supported              | Models                                                          |
|--------------------------------|-----------------------------------------------------------------|
| 9:16, 16:9, 1:1                | kling3_0, kling2_6, wan2_6, grok_video                          |
| 9:16, 16:9 only                | veo3, veo3_1                                                    |
| 9:16, 16:9, 1:1, 4:3, 3:4      | wan2_7, cinematic_studio_video                                  |
| auto, 21:9, 16:9, 4:3, 1:1, 3:4, 9:16 | seedance_2_0, marketing_studio_video, seedance_1_5      |
| (no constraints declared)      | minimax_hailuo                                                  |

Skill defaults to **9:16** for ad work (highest-volume placement). If a routed model doesn't support the requested aspect, Higgsfield clamps to the nearest match and returns an `adjustments` field — log it.

## Duration handling per model

Some models accept any duration in a range, others enforce discrete values:

- `veo3_1`, `veo3_1_lite` — discrete: 4, 6, 8 sec only
- `seedance_1_5` — discrete: 4, 8, 12 sec
- `wan2_6` — discrete: 5, 10, 15 sec
- `kling2_6` — discrete: 5, 10 sec
- `minimax_hailuo` — discrete: 6, 10 sec
- `kling3_0`, `seedance_2_0`, `cinematic_studio_3_0`, `wan2_7`, `grok_video` — range (3-15 / 4-15 / 1-15 / 2-15)

`parse_brief.py` should snap requested durations to allowed values before generation. Server clamps, but explicit snapping logs cleaner.

## Learning hook (future)

`manifest.json` per scene + ad performance data (post-launch-optimization output) will eventually feed:

- Per-model ROAS by scene type
- Cost-per-effective-clip by client industry
- Promote/demote tier moves analogous to hook-library

After 20+ delivered videos with downstream perf data, write `scripts/analyze_model_performance.py` to surface insights.
