---
name: ai-video-generator
description: "End-to-end AI video generation pipeline for client work. Takes a creative brief or an ad-copywriter storyboard and produces a finished MP4 by routing scenes through Higgsfield MCP (Veo 3.1 / Veo 3.1 Lite / Kling 3.0 / Minimax Hailuo / Seedance 2.0 / Wan 2.6 / Marketing Studio Video for UGC ads / Cinema Studio 3.0 — 30+ models) with cost-aware per-scene model selection, then stitches clips with VO + BGM + captions + brand chip. Hands off to video-edit for premium polish when requested. Reads client wiki for brand voice/colors. Manifest tracks model, prompt, seed, credits per scene. Use when user says: generate AI video, AI video for client, Higgsfield video, ai-video-generator, make a Veo clip, make a Kling video, generate B-roll for ad, create video from storyboard, ad creative video, UGC ad, Reel from storyboard, AI cinematic video, generate video from script, ad-copywriter to video. Do NOT trigger for: Digischola personal-brand visuals (use visual-generator — Digischola bans AI gen), polishing existing footage (use video-edit), writing the script/storyboard itself (use ad-copywriter), HTML landing pages (use landing-page-builder), scheduling/publishing (use scheduler-publisher)."
---

# AI Video Generator (v1.0 — Higgsfield-driven)

End-to-end pipeline. Storyboard or brief in, polished MP4 out. Scenes routed per model based on cost + cinematic fit.

**Track:** client-skills only. Digischola visual-generator is photo-free by policy — never use this skill for personal-brand content.

## Prerequisites — read first

1. **Higgsfield MCP must be connected.** See `references/mcp-setup.md`. The skill runs `scripts/check_mcp.py` on launch and aborts loud if not connected.
2. **Higgsfield account with credits.** Ultra tier ($99/mo, 3,000 credits + unlimited Nano Banana 2 Flash + 3 unlimited video models: Kling 2.5 / Seedance 1.0 / Hailuo 2.3) is the working baseline as of 2026-05-01. Plus ($39/mo, 1,000 credits) acceptable for low volume; Starter too credit-starved. Routing default tier flipped: cheap clips no longer cost credits. See cost matrix in `references/model-routing.md`.
3. **Client wiki exists.** `Desktop/{Client}/{Project}/_engine/wiki/brand-identity.md`. If absent, fall back to a neutral spec and flag the missing brand.
4. **ffmpeg + ChatterBox installed.** Same stack as visual-generator + video-edit.

## Context Loading

Read in this order:

- `shared-context/analyst-profile.md` — Mayank's quality bar
- `shared-context/accuracy-protocol.md` — every clip's manifest entry must source-label `[GENERATED]` with model + seed + prompt
- `shared-context/output-structure.md` — final MP4 at client folder root, internals in `_engine/working/`
- `shared-context/client-shareability.md` — final deliverable cannot read like a draft
- `references/mcp-setup.md` — Higgsfield connector install + auth
- `references/storyboard-schema.md` — input contract (ad-copywriter JSON OR free-form markdown)
- `references/model-routing.md` — cost-aware model picker per scene type
- `references/pipeline-architecture.md` — full dataflow
- `references/feedback-loop.md`

## Inputs

Two accepted forms:

**Form A — ad-copywriter storyboard (preferred).** Path to `*-storyboard.json` produced by ad-copywriter. Already has per-frame visual prompts, motion direction, VO script, music mood. Skill consumes directly.

**Form B — free-form markdown brief.** User pastes 2-5 lines: client, format (15s ad / 30s reel / 60s explainer), aspect (9:16 / 16:9 / 1:1), mood, key shots wanted. Skill calls `parse_brief.py` to derive a scene_plan.json.

## Pipeline (7 steps — execute literally per Skill Protocol Supremacy)

### Step 1 — Verify MCP + load context

```
python3 scripts/check_mcp.py
```

Aborts with setup link if Higgsfield MCP not connected. Then load client wiki, brand-identity, voice-guide.

### Step 2 — Parse brief → scene plan

```
python3 scripts/parse_brief.py <input> --client "<Client>" --project "<Project>" \
  --aspect 9:16 --duration 30 --output _engine/working/<entry>/scene-plan.json
```

Output schema in `references/storyboard-schema.md`. One entry per scene with: `scene_id`, `duration_sec`, `model_choice` (from router), `prompt`, `motion_preset`, `aspect`, `seed_strategy`, `vo_text`, `music_cue`. **Never invent metric numbers** — leave VO blank if uncertain (accuracy-protocol).

### Step 3 — Route models (cost-aware)

`scripts/parse_brief.py` invokes `references/model-routing.md` rules:

- **Hero/cinematic shot** → Veo 3.1 (40-70 credits)
- **Lifestyle B-roll, dialogue, action** → Kling 3.0 (6 credits) or Hailuo (10 credits)
- **Product/text-on-screen** → Seedance 2.0 (25 credits)
- **Stylized/anime/abstract** → Sora 2 (60 credits)
- **Default fallback** → Kling 3.0

User can override per scene with `--force-model`. Total credit budget logged before generation runs.

### Step 4 — Generate scenes

```
python3 scripts/generate_scenes.py _engine/working/<entry>/scene-plan.json
```

For each scene, call the appropriate Higgsfield MCP tool (text-to-video or image-to-video). Save MP4 to `_engine/working/<entry>/scenes/<scene_id>.mp4`. Append manifest entry to `manifest.json`:

```json
{
  "scene_id": "01",
  "model": "veo-3.1",
  "prompt": "...",
  "seed": 42,
  "credits_used": 50,
  "duration_sec": 8,
  "source": "[GENERATED]",
  "generated_at": "2026-04-30T..."
}
```

Retry on transient errors. Skip scenes that already exist (idempotent re-runs). On per-scene failure, mark scene `[FAILED]` in manifest and continue — don't abort the whole pipeline.

### Step 5 — Generate VO + pick BGM

VO via ChatterBox using the client's voice-lock if available (otherwise default neutral male/female):

```
python3 scripts/clone_voice.py --vo-text-from manifest.json \
  --output _engine/working/<entry>/voiceover.mp3
```

BGM auto-picked by mood from `_engine/music/` library — same source as visual-generator. Skip if storyboard says `music: silent`.

### Step 6 — Stitch + caption + brand chip

```
python3 scripts/stitch_video.py _engine/working/<entry>/ \
  --captions kinetic --chip auto --aspect 9:16
```

ffmpeg concat scenes → align VO timeline → mix BGM at -18 LUFS under VO at -14 LUFS → Whisper-transcribe VO for caption timing → render kinetic captions via existing video-edit caption components → overlay client brand chip from `_engine/wiki/brand-identity.md`. Output: `_engine/working/<entry>/draft.mp4`.

**Optional polish pass.** If user flags `--polish-with-video-edit`, hand `draft.mp4` to video-edit's ship phase for the Apple-aesthetic treatment. Skip otherwise — saves 60-90 seconds and compute.

### Step 7 — Validate + deliver + feedback

```
python3 scripts/validate_output.py _engine/working/<entry>/draft.mp4
```

Checks: resolution matches aspect, duration within ±10% of brief, audio levels, no Higgsfield watermark visible (free tier produces watermarks — check before delivery), captions don't overlap face bbox if face detected. CRITICAL failures abort.

On clean pass:
- Move `draft.mp4` to `Desktop/{Client}/{Project}/{YYYY-MM-DD}-{name}.mp4` (folder root — presentables)
- Run `~/.claude/scripts/build_outputs_index.py {Client}` to refresh index
- Append dated entry to Learnings & Rules below
- Flag downstream: scheduler-publisher can pick up from `pending-approval/` if requested

## Outputs

```
Desktop/{Client}/{Project}/
├── 2026-04-30-thrive-retreat-promo.mp4              ← final deliverable
└── _engine/working/<entry_id>/
    ├── scene-plan.json
    ├── manifest.json                                 ← model/prompt/seed/credits per scene
    ├── scenes/01.mp4 ... NN.mp4                      ← raw Higgsfield clips
    ├── voiceover.mp3
    └── draft.mp4
```

Downstream consumers:
- **video-edit** — can polish `draft.mp4` further (optional)
- **scheduler-publisher** — ships final MP4 to client's social channels
- **post-launch-optimization** — reads ad performance to feed model-picker learning

## Hard rules

- ❌ Never use this skill for Digischola personal brand
- ❌ Never invent metric numbers in VO text — leave blank, ask user, label uncertain
- ❌ Never deliver a Higgsfield-watermarked clip — validate_output catches this
- ❌ Never burn credits on duplicate generations — manifest is idempotent, re-runs skip existing scenes
- ❌ Never bypass the brand chip step — client deliverables are unbranded only on explicit request
- ✅ Always log credits-used per scene to manifest — fuels future cost analysis
- ✅ Always source-label every scene `[GENERATED]` with model + seed
- ✅ Always run validate_output before delivery — CRITICAL failures abort

## Cost guardrails

`parse_brief.py` prints estimated credit burn before Step 4 runs. If estimate exceeds:
- 100 credits → log warning
- 250 credits → require explicit `--confirm-cost` flag
- 500 credits → abort with explanation

Default safe budget: 100 credits per video (≈ $4 at Plus tier).

## Coordination with other skills

| Upstream                     | Output we read                                | Use                                    |
|------------------------------|-----------------------------------------------|----------------------------------------|
| ad-copywriter                | `*-storyboard.json`                           | Direct input — Form A                  |
| business-analysis            | `_engine/wiki/brand-identity.md`              | Brand chip, colors, voice              |
| paid-media-strategy          | `creative-brief.json` visual_direction        | Mood, aspect, format hints             |

| Downstream                   | Output they read                              | Use                                    |
|------------------------------|-----------------------------------------------|----------------------------------------|
| video-edit                   | `draft.mp4`                                   | Optional premium polish pass           |
| scheduler-publisher          | Final MP4 at folder root                      | Ship to client social channels         |
| post-launch-optimization     | manifest.json + ad performance                | Future: learn which models drive ROAS  |

## Learnings & Rules

Format: `[YYYY-MM-DD] [CLIENT-TYPE] Finding → Action`

- [2026-05-01] [Ultra plan migration] Mayank moved to Higgsfield Ultra ($99/mo) — 3,000 credits + 30-day unlimited Nano Banana 2 Flash + 3 unlimited video models (Kling 2.5, Seedance 1.0, Hailuo 2.3). Updated `references/model-routing.md`: Kling 3.0 / kling2_6 cousins + Hailuo + Seedance variants now routed as default tier with 0-credit cost on Ultra; Veo 3.1 / Cinematic Studio 3.0 / Marketing Studio Video kept as paid escalation tier. Updated SKILL.md prerequisites to reflect Ultra as working baseline. Default budget comment in SKILL.md left at 100 credits per video, but practical: a typical 30-sec UGC ad now costs $0 on Ultra (all Kling/Hailuo) — credits reserved for hero Veo shots only. Sibling skill ai-image-generator built same day.

- [2026-04-30] [SKILL CREATION] Skill v1.0 scaffolded. Pipeline architecture: Higgsfield MCP for clip generation → ChatterBox VO → ffmpeg stitch + captions + chip → optional video-edit polish. Cost-aware model routing prefers Kling 3.0 (6cr) over Veo 3.1 (50cr) by default; hero shots flag Veo. Default budget: 100 credits per video. Hard rule: never run on Digischola — that brand is photo-free by visual-generator policy.
