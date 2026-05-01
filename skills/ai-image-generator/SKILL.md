---
name: ai-image-generator
description: "End-to-end AI image creative pipeline for client work via Higgsfield MCP. Takes a creative brief, an ad-copywriter image-prompts.json, or a free-form concept board AND an optional reference-image folder, then routes each concept × variation to the right Higgsfield image model (Nano Banana 2 Flash unlimited on Ultra / Nano Banana Pro / GPT Image 2 / Marketing Studio Image / Soul Cast / Flux 2 / Seedream 4.5 / Cinema Studio 2.5), polls until done, downloads to client folder, builds dashboard.html for review, scores variants, validates aspect + brand fit + religious-sensitivity. Reusable for Meta image ads, Google Display, LinkedIn image creatives, ad creative variation engines, landing-page hero imagery, ICP carousel covers. Reads client wiki for brand voice/colors. Manifest tracks model + prompt + seed + reference-images + credits per gen. Use when user says: generate ad creatives, image creatives, Meta image ads, Google Display creatives, LinkedIn image ads, ad creative variations, image campaign, hero imagery, carousel covers, ai-image-generator, Higgsfield images, scale creatives, render image prompts, generate from ad-copywriter prompts. Do NOT trigger for: Digischola personal-brand visuals (use visual-generator with its ai-illustration mode), video generation (use ai-video-generator), polishing existing creative (manual or video-edit), writing the copy itself (use ad-copywriter), publishing (use scheduler-publisher), bulk Ads Editor CSV (use campaign-setup)."
---

# AI Image Generator (v1.0 — Higgsfield-driven, Ultra-aware)

End-to-end pipeline. Brief or ad-copywriter image-prompts in, finished image creatives out. Variants routed per model based on cost + visual fit. Optional reference-image folder anchors brand consistency and handles religious / sacred / portrait subjects safely.

**Track:** client-skills only. Personal-brand `visual-generator` has its own ai-illustration mode for Digischola — never use this skill for personal-brand work.

## Prerequisites

1. **Higgsfield MCP must be connected.** See `references/mcp-setup.md`. Skill runs `scripts/check_mcp.py` on launch and aborts loud if not connected.
2. **Higgsfield account with credits.** Ultra tier ($99/mo, 3,000 credits + unlimited Nano Banana 2 Flash + 3 unlimited video models) is the working baseline as of 2026-05-01. Plus tier works for low-volume; Free tier blocks production due to watermark.
3. **Client wiki exists.** `Desktop/{Client}/{Project}/_engine/wiki/brand-identity.md`. Falls back to neutral spec + flag if absent.
4. **Reference image folder (optional but unlocks figurative/sacred/portrait work).** See `references/reference-image-protocol.md` for tagging + religious guardrails.

## Context Loading

- `shared-context/analyst-profile.md` — Mayank's quality bar
- `shared-context/accuracy-protocol.md` — every gen's manifest entry source-labels `[GENERATED]` with model + seed + prompt + reference-image IDs
- `shared-context/output-structure.md` — final PNGs + dashboard.html at client folder root, internals in `_engine/working/`
- `shared-context/client-shareability.md` — final deliverable cannot read like a draft
- `shared-context/copywriting-rules.md` — text-on-image follows the same grounded/no-poetic/no-hype rules as ad copy
- `references/mcp-setup.md` — Higgsfield image-side tools + verified model IDs
- `references/model-routing.md` — Ultra-aware cost-routing per concept type
- `references/concept-board-schema.md` — input + output JSON contracts
- `references/reference-image-protocol.md` — folder inventory, tagging, religious-brand guardrails
- `references/pipeline-architecture.md` — full dataflow
- `references/feedback-loop.md`

## Inputs (three accepted forms)

**Form A — ad-copywriter image-prompts.json (preferred).** Path to `_engine/working/image-prompts.json` produced by ad-copywriter v2.1+. Already has per-concept structured prompts, aspect ratio, `requires_reference_image`, `reference_subject` tags, designer-brain 7-block depth. Skill consumes directly.

**Form B — concept board markdown.** User pastes 3-8 concepts: name + one-line creative direction + intended placement (feed/story/display) + optional reference subject tags. Skill calls `parse_brief.py --form B` to derive a `concept-board.json`.

**Form C — standalone brief.** User describes campaign goal + target audience + 4-6 angles. Skill asks 3 clarifying questions then builds the concept board internally.

## Pipeline (8 steps — execute literally per Skill Protocol Supremacy)

### Step 1 — Verify MCP + load context

```
python3 scripts/check_mcp.py
```

Aborts with setup link if MCP not connected. Then load client wiki, brand-identity, voice-guide.

### Step 2 — Inventory reference image folder (if provided)

```
python3 scripts/inventory_references.py "<reference_folder>" --output _engine/working/<entry>/reference-manifest.json
```

Walks the folder, hashes each image (dedup), captures dimensions + aspect, runs Claude in-session over each image to write a structured tag (subject_type / contains_face / sacred / consent_status / usage_scope). Output is consumed by Step 4 to attach references to gens. **Religious-brand rule:** if any image tagged `subject_type=deity`, lock it as input-only (model never redraws — composite-into-design pattern only). Full protocol: `references/reference-image-protocol.md`.

### Step 3 — Parse brief / image-prompts → concept board

```
python3 scripts/parse_brief.py <input> --client "<Client>" --project "<Project>" \
  --goal registrations --output _engine/working/<entry>/concept-board.json
```

Output schema in `references/concept-board-schema.md`. One entry per concept × variation × aspect ratio with: `concept_id`, `variation_id`, `aspect_ratio`, `model_choice` (from router), `prompt`, `negative_prompt`, `reference_image_ids`, `reference_role` (style / composition / subject-lock), `intended_placement`, `expected_credits`, `voice_check`. Voice-check pass via shared-context/copywriting-rules.md before generation queue is built.

### Step 4 — Route models (Ultra-aware, cost-aware)

`parse_brief.py` invokes `references/model-routing.md` rules. Default tier on Ultra plan = `nano_banana_flash` (unlimited credits). Escalation tiers cost credits.

- **Default / unlimited tier** → `nano_banana_flash` (Nano Banana 2, 4k, photorealistic + text rendering decent)
- **Premium typography / cover slide / 4k hero** → `nano_banana_2` (Pro) or `gpt_image_2` (best text rendering)
- **One-click product ads** → `marketing_studio_image` (purpose-built for social)
- **Cinematic stills / luxury / film aesthetic** → `cinematic_studio_2_5`
- **Character identity reuse across creatives** → `soul_cast` (define identity once, reuse)
- **UGC / portrait / fashion editorial** → `soul_2`
- **Reference-image editing / style transfer** → `flux_kontext` or `seedream_v4_5`
- **Precise prompt adherence with creative latitude** → `flux_2`

User can override per concept with `--force-model`. Total credit budget logged before generation runs (see Cost guardrails below).

### Step 5 — Plan generations + queue MCP calls

```
python3 scripts/plan_generations.py _engine/working/<entry>/concept-board.json
```

Builds `mcp-call-queue.json` — one entry per pending generation with the MCP tool name (`generate_image`) + args (model, prompt, aspect_ratio, resolution, medias[]). Idempotent: skips concepts whose output PNG already exists. Prints budget preview, asks for confirm if budget exceeds threshold.

### Step 6 — Generate (Claude in-session)

Claude reads `mcp-call-queue.json` and invokes the Higgsfield MCP `generate_image` tool per entry. Polls `show_generations` every 60-90s until each completes, then downloads each result PNG to `creatives/<concept_id>/<variation_id>-<aspect>.png` via `download_outputs.py`. Manifest entries appended after each successful download.

```
python3 scripts/download_outputs.py _engine/working/<entry>/ \
  --generation-id <id> --concept-id <concept> --variation <var> --aspect <aspect>
```

Retry on transient errors. On per-gen failure, mark gen `[FAILED]` in manifest and continue — don't abort the queue.

### Step 7 — Validate + score + dashboard

```
python3 scripts/validate_output.py _engine/working/<entry>/
```

Checks per PNG: aspect matches request, dimensions within 2% tolerance, no Higgsfield watermark visible, color profile sRGB, file size sane. CRITICAL failures flagged for re-gen.

```
python3 scripts/analyze_outputs.py _engine/working/<entry>/
```

Claude in-session reads each PNG via the Read tool (multimodal), scores on 5 dimensions (brand-voice fit / visual hierarchy / CTA readability / sector sensitivity / variation differentiation), writes `scores.json`.

```
python3 scripts/render_dashboard.py _engine/working/<entry>/
```

Assembles `Desktop/{Client}/{Project}/{YYYY-MM-DD}-image-creatives-dashboard.html` — all variants on one page, side-by-side, scored, brand-themed, with "use this one" buttons. Mayank reviews and picks winners.

### Step 8 — Deliver + feedback

- Move winning PNGs to `Desktop/{Client}/{Project}/creatives/{YYYY-MM-DD}-{concept-name}/<aspect>.png` (folder root — presentables)
- Run `~/.claude/scripts/build_outputs_index.py {Client}` to refresh index
- Append dated entry to Learnings & Rules below
- Flag downstream: `campaign-setup` can pick up creatives from `creatives/` for Meta/Google bulk-import CSV

## Outputs

```
Desktop/{Client}/{Project}/
├── 2026-05-01-image-creatives-dashboard.html        ← review surface
├── creatives/                                       ← presentables (final picks)
│   └── 2026-05-01-prasadam-invite/
│       ├── 1x1.png
│       ├── 4x5.png
│       └── 9x16.png
└── _engine/working/<entry_id>/
    ├── concept-board.json                           ← what we asked for
    ├── reference-manifest.json                      ← inventoried reference folder + tags
    ├── mcp-call-queue.json                          ← per-gen MCP args
    ├── manifest.json                                ← model/prompt/seed/refs/credits per gen
    ├── scores.json                                  ← Claude-in-session scoring
    └── creatives/                                   ← all variants (winners + losers)
```

Downstream consumers:
- **campaign-setup** — reads `creatives/` for Meta + Google bulk-import CSVs
- **landing-page-builder** — can request hero imagery via this skill (flag `--mode landing-hero`)
- **post-launch-optimization** — reads manifest.json + ad performance to feed model-picker learning

## Hard rules

- ❌ Never use this skill for Digischola personal brand — use `visual-generator` ai-illustration mode
- ❌ Never AI-redraw a sacred subject (deity, scripture). Reference photos go in as input-only; model generates the surround, not the subject. See religious guardrails in `references/reference-image-protocol.md`
- ❌ Never generate AI portraits of real people without a reference image of that person flagged `consent_status=cleared`
- ❌ Never deliver a Higgsfield-watermarked image — validate_output catches this; reject + re-queue on Ultra plan
- ❌ Never burn credits on duplicate generations — manifest is idempotent, re-runs skip existing PNGs
- ❌ Never bypass voice-check — text-on-image follows shared-context/copywriting-rules.md (no em dashes, no hype, no engagement bait)
- ✅ Always log credits-used per gen to manifest — fuels future cost analysis
- ✅ Always source-label every gen `[GENERATED]` with model + seed + reference-image IDs
- ✅ Always run validate_output before delivery — CRITICAL failures abort

## Cost guardrails (Ultra plan baseline)

`plan_generations.py` prints estimated credit burn before Step 6 runs. Ultra unlimited tier (`nano_banana_flash`) burns 0 credits per gen. Escalation tiers:

| Estimated burn (paid models only) | Action                                   |
|-----------------------------------|------------------------------------------|
| ≤ 50 credits                      | Run silently                             |
| 51-150                            | Print warning, log, continue             |
| 151-400                           | Require `--confirm-cost` flag            |
| > 400                             | Abort — explain, ask for explicit OK     |

Default safe budget: 150 credits per campaign run (≈ 30 GPT Image 2 hero gens or 10 Nano Banana Pro 4k gens, on top of unlimited Nano Banana Flash variants).

## Coordination with other skills

| Upstream                     | Output we read                                | Use                                    |
|------------------------------|-----------------------------------------------|----------------------------------------|
| ad-copywriter                | `_engine/working/image-prompts.json`          | Direct input — Form A                  |
| business-analysis            | `_engine/wiki/brand-identity.md`              | Brand chip, colors, voice              |
| paid-media-strategy          | `creative-brief.json` visual_direction        | Mood, aspect, format hints             |
| landing-page-builder         | `_engine/working/page-spec.json` hero_intent  | Hero image generation request          |

| Downstream                   | Output they read                              | Use                                    |
|------------------------------|-----------------------------------------------|----------------------------------------|
| campaign-setup               | `creatives/` PNGs + manifest.json             | Meta + Google bulk-import CSVs         |
| landing-page-builder         | `creatives/landing-hero/` PNGs                | Embed hero in HTML build               |
| post-launch-optimization     | manifest.json + ad performance                | Future: learn which models drive ROAS  |

## Learnings & Rules

Format: `[YYYY-MM-DD] [CLIENT-TYPE] Finding → Action`

- [2026-05-01] [SKILL CREATION] Skill v1.0 scaffolded after Mayank moved to Higgsfield Ultra plan (3,000 credits + unlimited Nano Banana 2 Flash + 3 unlimited video models). Pipeline architecture: Higgsfield MCP `generate_image` for image generation → reference-folder inventory + tagging → concept-board JSON → cost-aware model routing (default tier = `nano_banana_flash` unlimited; escalation to `nano_banana_2` Pro / `gpt_image_2` / `marketing_studio_image` etc.) → in-session MCP polling + download → per-PNG validation + Claude-in-session scoring → branded dashboard.html for analyst review → final picks moved to client folder root for `campaign-setup` consumption. Default budget: 150 credits per campaign (unlimited Flash + ~30 paid hero gens). Hard rule: never run on Digischola — that brand uses `visual-generator` ai-illustration mode by policy. Religious-brand rule: deity / scripture references are input-only — composite-into-design, never AI-redraw.
