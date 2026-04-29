---
name: video-edit
description: One-command video editor — takes a raw source video + plain-English brief, produces a top-tier edited MP4 with kinetic captions, B-roll cutaways (fake landing pages in Safari chrome, form-shrinking mockups, metric-counter takeovers), arrow callouts, zoom-punch moments on face, Apple-aesthetic motion design, and a unified branded chip that covers any HeyGen/Synthesia/AI-avatar watermark. Auto-detects aspect ratio, trims silence, re-encodes with dense keyframes, transcribes via Whisper, detects face placement via OpenCV, generates a content-plan.json via a director brain, assembles the HyperFrames composition, renders, normalizes audio, validates, delivers to the client folder. Works for ANY client, ANY brand — Digischola brand is just the default. Use when user says: edit this video, polish this video, make this video pop, Apple-aesthetic this, premium edit, motion graphics, turn this raw footage into a Reel, add kinetic captions, cinematic edit, client video, testimonial edit, case study video, one-click video, auto-edit. Do NOT trigger for: drafting post copy (use post-writer), creating a video from scratch with NO source footage and only images/script (use visual-generator for now), scheduling/publishing (use scheduler-publisher), ad video copy concepts (use ad-copywriter).
---

# video-edit

Turn a raw source video into a polished edit, end-to-end, from one command. The skill handles the technical translation — probing, silence trim, loudness normalization, transcription, face detection, composition authoring, rendering, post-processing, validation, delivery.

## Trigger Pattern

User says: *"Edit this testimonial. ~/Downloads/raw.mp4. Make it feel premium. Client is Thrive Retreats / Nrsimha 2026."*

Skill runs the pipeline and drops a finished MP4 at `Desktop/{Client}/{Project}/{YYYY-MM-DD}-{name}.mp4` (folder root — final MP4s are presentables under the post-2026-04-29 `_engine/` convention).

## Pipeline (11 steps — execute literally per Skill Protocol Supremacy)

### Step 1 — Load context

1. Read [analyst-profile.md](../../shared-context/analyst-profile.md) for Mayank's voice/quality standards.
2. Read [output-structure.md](../../shared-context/output-structure.md) — post-2026-04-29 `_engine/` convention: client-folder videos go at the program-folder root (drop the final MP4 directly in `Desktop/{Client}/{Project}/`, not in `outputs/`) and re-run `~/.claude/scripts/build_outputs_index.py {client}`; for Digischola, drop into `brand/videos/edits/` or `brand/queue/pending-approval/` (both stay at top under the new convention) then run `~/.claude/scripts/build_digischola_index.py`.
3. Identify **client**, **project folder**, **brief**, **source video path** from the user message. If missing, ask for the minimum: which client + what mood/feel?
3. Default brand config path: `Desktop/{Client}/{Project}/_engine/wiki/brand-identity.md` (single-program client) or `Desktop/{Client}/_engine/wiki/brand-identity.md` (multi-program). For Digischola, `Desktop/Digischola/brand/_engine/wiki/brand-identity.md`. If the file is absent, use Digischola's brand config as a neutral fallback and flag the missing client brand.

### Step 2 — Run the prepare phase

Single command:

```
python3 /Users/digischola/Desktop/.claude/skills/video-edit/scripts/edit_video.py prepare \
  "<source-video-path>" --brief "<user-brief>" --client "<ClientName>" \
  [--project "brand/videos/projects"] [--preset apple-premium]
```

This runs: scaffold HyperFrames project → probe → ffmpeg prepass (silence trim + normalize + dense keyframes) → copy prepped to assets → Whisper transcribe → validate transcript (flag metric words) → OpenCV face detection. Outputs:
- `project_dir/source-probe.json`
- `project_dir/cuts.json`
- `project_dir/prepped.mp4`
- `project_dir/assets/source.mp4`
- `project_dir/assets/transcript.json`
- `project_dir/face-bboxes.json`

**If the validate_transcript step flags any metric-like words** (percentages, dollar amounts, multipliers, large integers): read the flagged words aloud to the user and ask them to confirm before proceeding. A wrong number in a published Reel is unfixable.

### Step 3 — Generate content-plan.json

Read [references/content-plan-recipe.md](references/content-plan-recipe.md) — it's the director rulebook (hook picking, caption grouping, B-roll cue selection, emphasis classes, voice-guide rules, validation checklist).

Read the prepared inputs:
- `source-probe.json` — dims, duration, aspect
- `assets/transcript.json` — word-level timings
- `face-bboxes.json` — where NOT to put captions/overlays
- `brand-identity.md` for the client — colors, fonts, voice rules

Produce a complete content-plan.json at `project_dir/content-plan.json` matching [references/content-plan-schema.md](references/content-plan-schema.md). Self-check against the recipe's validation checklist before writing the file.

**For autonomous runs** (cron / scheduler), use `scripts/content_plan_brain.py` with ANTHROPIC_API_KEY set — it calls Claude API with the same recipe as the system prompt. (This script is optional; the in-session Claude-generated path is the default.)

### Step 4 — Run the ship phase

Single command:

```
python3 /Users/digischola/Desktop/.claude/skills/video-edit/scripts/edit_video.py ship "<project_dir>"
```

This runs: assemble_composition → hyperframes lint → hyperframes render → ffmpeg postpass (fade + loudnorm + final encode) → validate_output → deliver. Exit 0 on clean delivery.

### Step 5 — Validate + feedback loop (MANDATORY — per session-close protocol)

1. `validate_output.py` runs automatically inside ship phase. Any CRITICAL failure aborts before delivery.
2. Append a dated entry to Learnings & Rules below: `[YYYY-MM-DD] [CLIENT-TYPE] Finding → Action`.
3. Flag downstream: if the delivered MP4 will be posted on LinkedIn/X/IG, note that `scheduler-publisher` can pick it up from `pending-approval/`.

## Components in the library

[components/README.md](components/README.md) lists all — broll (landing-page, form-shrinking), charts (metric-counter), emphasis (arrow-callout), mockups (browser-chrome), motion (zoom-punch), text (hook card, kinetic-caption-wordpop). Add new components when a client need recurs — never write one-off composition HTML.

## Presets

8 aesthetic presets live in [references/aesthetic-presets.md](references/aesthetic-presets.md). Translator maps plain-English brief → preset in [references/brief-translator.md](references/brief-translator.md). Default: apple-premium.

## Free-only stack

GSAP core (free MIT) + Lottie (free downloads) + Chart.js + Tailwind CDN + Lucide icons + OpenCV Haar cascade + Whisper small.en via hyperframes CLI. No paid plugins. No API key required for in-session operation.

## Skill coordination

- **Upstream:** `ad-copywriter` (for ad-video briefs), `case-study-generator` (testimonial edits of client-win footage), user directly.
- **Downstream:** `scheduler-publisher` picks up delivered MP4s. `post-writer` drafts captions referencing the final edit. `performance-review` tracks engagement after publish.
- **Sibling:** `visual-generator` handles from-scratch Reels (images + voiceover, no source footage). `video-edit` handles anything WITH source video. Don't overlap.

## Environment requirements

- macOS Darwin
- Node 22+, `npx hyperframes` (installs on demand)
- ffmpeg + ffprobe + jq
- Python 3.9+ with `opencv-python`, `numpy` (face detection), `anthropic` (autonomous API path only)
- Optional: ANTHROPIC_API_KEY env var (autonomous content-plan generation for cron runs)

Verify prerequisites on first run with `ffmpeg -version`, `which jq`, `python3 -c "import cv2"`.

## Learnings & Rules

(Add dated entries after every use. Format: `[YYYY-MM-DD] [CLIENT TYPE] Finding → Action`. Keep under 30 lines, prune quarterly.)

- [2026-04-24] [SKILL-BUILD] Smoke test confirmed validator correctly flags dim-mismatch when post-pass runs without HyperFrames render upscaling. Rule: post-pass runs ONLY after HyperFrames render, never on prepped.mp4.
- [2026-04-24] [PERSONAL] Sparse keyframes on source (10s interval) caused HyperFrames seek/freeze warnings. Fixed `ffmpeg_prepass.sh` both branches with `-g 30 -keyint_min 30 -movflags +faststart` to force dense keyframes (1 keyframe/frame at 30fps).
- [2026-04-24] [PERSONAL] Loudness drifted to -10.8 LUFS after HyperFrames re-encode. Fixed `ffmpeg_postpass.sh` to re-apply `loudnorm` per preset during final encode. Rule: loudnorm runs at least once between render and delivery.
- [2026-04-24] [PERSONAL] `+120%` overflowed bottom/top in metric-hero beat. Reduced default font-size 380→260px, added `white-space: nowrap`, `max-width: 100%`, `padding: 0 40px` safety in assembler CSS.
- [2026-04-24] [PERSONAL] HeyGen watermark + lower-third stacked on top of each other. Unified: removed separate `watermark-mask`, enlarged `#lower-third` to 460×200px at `right:0 bottom:0`, extended to full source-video window (clip_start → clip_end).
- [2026-04-25] [SKILL-BUILD] One-command orchestrator `edit_video.py` (prepare + ship phases) + director recipe + transcript accuracy gate + face detection. Skill now runs end-to-end without hand-written JSON: user drops video + brief, agent reads recipe + inputs, writes content-plan.json, orchestrator delivers MP4.
- [2026-04-29] [STRUCTURAL REFACTOR] Folder convention changed: skill internals (idea-bank.json, brand DNA wiki, _mining, _research, media assets, configs) now live in `Digischola/brand/_engine/` subfolder; client wikis and intermediate working files now live under `_engine/`; presentables (HTML/MP4/PDF) sit at the program-folder root. Daily-workflow folders (queue/, calendars/, performance/, videos/, social-images/) stay at top for Digischola. → Updated SKILL.md Step 1 (output destination + brand config path), trigger-pattern delivery path (final MP4 at folder root, no longer `edits/` subdir for client work), and `references/content-plan-recipe.md` (brand config input path under `_engine/wiki/`). Source video paths and HyperFrames project paths are user/runtime inputs (no migration needed).
