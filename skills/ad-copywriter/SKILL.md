---
name: ad-copywriter
description: "Platform-specific ad copy, AI image generation prompts, and video storyboards. Generates Google RSA headlines/descriptions, Meta primary text/headlines, Gemini-ready image prompts, and frame-by-frame video storyboards with voiceover scripts. Works standalone or downstream from paid-media-strategy creative brief. Use when user mentions: ad copy, copywriter, write ads, headlines, creative copy, image prompts, video storyboard, Gemini prompts, ad creative, write headlines, RSA copy, meta ad text, video script, voiceover script. Do NOT trigger for: media strategy, campaign plan, budget allocation, market research, landing page audit, campaign setup in Ads Manager."
---

# Ad Copywriter

Generates production-ready ad copy, AI image prompts, and video storyboards from a creative brief or standalone input. Sits after paid-media-strategy, before campaign-setup. Outputs are directly pasteable into Ads Manager, Gemini, and AI Studio.

## Context Loading

Read these shared context files before starting:
- `shared-context/analyst-profile.md` — workflow, client types, quality standards
- `shared-context/accuracy-protocol.md` — 3 accuracy rules for all data handling
- `shared-context/output-structure.md` — write final HTML/MP4/PDF and upload-ready CSV bundles to the client/program folder root; intermediate MD/JSON/CSV to `_engine/working/`
- `shared-context/client-shareability.md` — client-facing files must read like first copies; no correction trails / audit history / internal-process commentary. Validator: `python3 ~/.claude/scripts/check_client_shareability.py {client}`

## Process Overview

### Step 1: Input Check & Mode Selection

Check in this order — Refresh Mode takes priority because it's the narrowest and most time-sensitive trigger:

**Refresh Mode** (fatigue rotation) — if `{client-folder}/_engine/working/*-rotation-brief.json` exists:
- Load `references/refresh-mode.md` for the full workflow — it overrides Steps 2, 4, 5, 8
- Load the rotation brief, the original `*-creative-brief.json`, and the wiki
- State explicitly in output: "Refresh Mode — N fatigued creatives being rotated"
- Skip Step 2 entirely

**Downstream mode** (creative brief exists, no rotation brief):
- Read the creative brief JSON — campaigns, personas, hooks, formats, visual_direction, landing_page, ab_testing, proof_elements, brand_voice
- Read `{client-folder}/_engine/wiki/strategy.md` for competitor context
- Read `{client-folder}/_engine/brand-config.json` for brand identity
- **Read offerings (Gate B source-of-truth):** `{client-folder}/_engine/wiki/offerings.md` (single-program) — or `{client-root}/_engine/wiki/offerings.md` for multi-program clients (where `_engine/` sits at the client root, formerly `_shared/`). This is the cross-check authority for every service-claim phrase generated in Step 4.
- **Detect Gate A trigger conditions** in the creative brief (any one fires gated-output mode):
  1. `do_not_launch_until_phase_0_complete: true`
  2. Any `phase_0_prerequisites[].status` ∈ {`GATED`, `BLOCKED`, `PENDING`}
  3. `verdict` ∈ {`DO-NOT-LAUNCH`, `BEST-CASE`, `GATED`}
  4. `framing` containing `best-case`
- Skip to Step 3

See `references/offerings-cross-check.md` for the full Gate A + Gate B protocol.

**Standalone mode** (no creative brief, no rotation brief):
- Proceed to Step 2

### Step 2: Guided Questions (Standalone Only)

Ask 6 questions to build a minimal creative brief internally:

1. What product/service and price point?
2. Which platform(s)? Google, Meta, or both?
3. Who are the 2-3 target personas? (name + one-line description)
4. What are the top 3 hooks/USPs?
5. What proof elements exist? (media mentions, certifications, stats, testimonials)
6. Brand voice: premium, casual, professional, playful? Any words to avoid?

Optional: Landing page URL, existing ad examples to reference.

Build an internal brief object from answers. Proceed to Step 3.

### Step 3: Load Platform Specs & Frameworks

Read these reference files (load only sections relevant to the client's platforms):
- `paid-media-strategy/references/google-ads-system.md` — Section 7 (Ad Formats) for RSA specs, character limits, pinning
- `paid-media-strategy/references/meta-ads-system.md` — Section 6.4 (Creative Format Specs) for text limits, placements
- `references/copywriting-frameworks.md` — framework selection logic + proof integration patterns
- `references/output-format-spec.md` — deliverable file structures

### Step 4: Generate Ad Copy

**Framework selection per campaign:**
- Google RSA → Feature-Benefit-Proof
- Meta Prospecting → PAS (problem-solving products) or BAB (transformation/lifestyle)
- Meta Retargeting → Social Proof Stack
- Video scripts → AIDA
- Longer Meta primary text → AIDA or PAS

**Google RSA output per ad group:**
- 15 headlines (each ≤ 30 characters — VALIDATE before output)
- 4 descriptions (each ≤ 90 characters — VALIDATE)
- 2 path fields (each ≤ 15 characters)
- Pinning recommendations (pin brand to H1, main CTA to D1)
- Headlines must work independently — any headline with any description

**Meta output per ad:**
- 3-5 primary text variants (keep under 125 chars for feed visibility, flag if over)
- 3-5 headline variants (each ≤ 40 characters)
- Description (≤ 30 characters)
- CTA button selection
- A/B test variants from creative brief's `ab_testing.test_pairs`

**Quality rules:**
- Every character counts — no filler words in headlines
- Proof elements woven in per `references/copywriting-frameworks.md` proof integration patterns
- Brand voice do/don't from creative brief respected throughout
- Label each copy block: [BRIEF] = from creative brief hooks, [GENERATED] = new, [ADAPTED] = modified from brief

**Gate B — Service-offering cross-check (always-on):**
For every persona / ad-group label / headline / description / callout / snippet value that names a specific service, modality, or class style, verify it appears in `_engine/wiki/offerings.md`. If unmatched: drop, reframe to a verified offering, or wrap as `<<UNVERIFIED-CLAIM:phrase>>`. See `references/offerings-cross-check.md` §Gate B for the full protocol and common false-claim categories (prenatal yoga, chair yoga, EMDR, hydrafacial, etc.).

**Output filename:**
- **Default:** `{client-folder}/_engine/working/ad-copy-report.md`
- **Gate A fired** (Step 1 detected gated launch state): write **two** files in `_engine/working/`:
  - `ad-copy-best-case.md` — banner: "BEST CASE — DO NOT IMPORT until Phase 0 complete". Includes gated claims for forward planning.
  - `ad-copy-current-state.md` — banner: "Current-state copy — safe for production import". Gated claims stripped per `phase_0_prerequisites[].claim_phrases`. The Step 5 CSV is generated **only from this file**.

Both files MUST include a `## Gate Audit (auto-generated)` section listing triggers, stripped phrases, and Gate B verified/failed claims. See `references/offerings-cross-check.md` §"Logging requirements" for the audit-section template.

### Step 5: Generate Platform CSV Sheets

Read `references/output-format-spec.md` for column formats.

**Google Ads CSV** (`{client-folder}/_engine/working/google-ads.csv` — intermediate, consumed by campaign-setup):
- One row per RSA: Campaign, Ad Group, H1-H15, D1-D4, Path1, Path2, Pin notes, Final URL
- Character limit validation on every cell — CRITICAL, do not ship over-limit copy

**Meta Ads CSV** (`{client-folder}/_engine/working/meta-ads.csv` — intermediate, consumed by campaign-setup):
- One row per ad variant: Campaign, Ad Set, Ad Name, Primary Text, Headline, Description, CTA, Format, Landing URL
- A/B variant labels in Ad Name (e.g., "Prospecting-DesignBuyer-HookA")

### Step 6: Generate Image Prompts

Read `references/image-prompt-patterns.md` AND `references/creative-research.md` (performance intelligence).
Apply the 10 performance rules from image-prompt-patterns.md before writing any prompt. Key rules: light backgrounds (+70% purchase rate), high contrast (+32% CTR), 40-80 word prompts after prefix, "ultra-realistic photograph" + specific lens, no text overlay for Google placements.

Use `image_gen_prompt_prefix` from creative brief as base prompt. Append per-ad specifics:
- Scene/subject changes per persona angle
- Aspect ratio instruction (4:5 feed, 9:16 stories, 1:1 square, 1.91:1 display)
- Text overlay zone instruction ("leave clean space at top 20% for text")
- P1/P2 priority from creative brief formats

Save as `{client-folder}/_engine/working/image-prompts.md`.

### Step 7: Generate Video Storyboards

Read `references/video-storyboard-spec.md` AND `references/creative-research.md` (Section 6: Video Creative Science).
Key rules: text in first 3 seconds (+46% purchase rate), design for sound-off (85% muted), 10-15s optimal for lead gen, treat first frame as standalone static ad, CTA early AND repeated at end.

One storyboard per video ad from creative brief formats. Per frame:
- **Visual:** Gemini image prompt for this frame
- **Motion:** camera/animation direction (slow zoom, pan, static parallax)
- **Text overlay:** copy that appears on screen
- **Voiceover:** clean script for AI voice tool (no stage directions, natural contractions, short sentences)
- **Voice direction:** tone/pace for model selection (separate from VO text)
- **Music:** mood/energy level

Include combined VO script at bottom — one continuous text block for pasting into AI Studio.

Save as `{client-folder}/_engine/working/video-storyboards.md`.

### Step 8: Validate & Update Wiki

Run `scripts/validate_output.py` against all deliverables. Fix any CRITICAL failures (character limits, missing fields).

Update `{client-folder}/_engine/wiki/log.md` — add AD-COPYWRITER COMPLETE entry.
Update `{client-folder}/_engine/wiki/index.md` — update downstream status.

Flag downstream: campaign-setup skill can consume the CSV sheets + image prompts.

## Output Checklist

- [ ] Mode correctly identified (downstream from creative brief vs standalone with guided intake)
- [ ] Platform specs loaded; character limits enforced (RSA 30 / 90 / 15; Meta 125 / 40 / 30)
- [ ] Framework labeled per campaign (PAS / BAB / Feature-Benefit-Proof / AIDA / Social Proof Stack)
- [ ] Source labels applied to every copy block: `[BRIEF]` / `[GENERATED]` / `[ADAPTED]`
- [ ] Google Ads CSV produced with 15 headlines + 4 descriptions per ad group (if Google in scope)
- [ ] Meta Ads CSV produced with primary text + headline + description + CTA (if Meta in scope)
- [ ] Image prompts use `image_gen_prompt_prefix` from creative brief (downstream mode)
- [ ] Image prompts follow creative-research.md rules: light background bias, high contrast, no Google Display text overlay, 1-3 sentences after prefix
- [ ] Video storyboards use frame layers (Visual / Motion / Text Overlay / Voiceover / Voice Direction / Music)
- [ ] Voiceover scripts are clean text only (no parentheticals, stage directions, or ALL CAPS); word count within duration target (~35-40 words per 15s, ~70-80 per 30s)
- [ ] Message match honored when creative brief specifies `landing_page.message_match_notes`
- [ ] `scripts/validate_output.py` passes with 0 CRITICAL failures
- [ ] Wiki log updated; downstream flagged for campaign-setup

## Failure Handling

- Character limit violation → CRITICAL, rewrite the offending copy before output
- Missing creative brief in downstream mode → fall back to standalone mode, warn user
- Platform specs file not found → warn, use hardcoded limits (RSA: 30/90, Meta: 125/40/30)

## Learnings & Rules

<!-- Pre-2026-04-26 entries pruned: encoded into scripts/validate_output.py (char-limit enforcement, VO regex, image-prompt prefix, message-match, VO duration budget) and references/ (creative-research.md, refresh-mode.md, image-prompt-patterns.md). See git log for history. -->

- [2026-04-16] [Refresh Mode] Creative fatigue → ad-copywriter handoff was manual. Added Refresh Mode (3rd operating mode alongside Standalone/Downstream); trigger = `*-rotation-brief.json`; new files preserve framework/persona/CTA, change hook angle/imagery/proof; `[REFRESH]` source label + `_v2`/`_v3` ad naming. See `references/refresh-mode.md`. Eval #6 covers the full path. **RULE:** Creative refresh = closed loop: fatigue signal → machine-readable handoff → drop-in replacement copy with original preserved as A/B control.

- [2026-04-26] [CRITICAL — Living Flow Yoga / wellness / Phase-0-gated brief] **ad-copywriter generated production copy claiming services that don't exist** (free trial, prenatal yoga, trimester-safe modifications, chair yoga). Caught at pre-launch — would have shipped to Google Ads if not audited. Two failure modes:
  1. **Gated mechanism leakage:** brief carried `do_not_launch_until_phase_0_complete: true` + GATED phase_0_prerequisites; skill produced 60+ production headlines/CSV rows around "7-Day Free Trial" anyway.
  2. **Search-demand-without-service-offering:** "Pregnancy / Pre-Postnatal" persona seeded from keyword volume (670/mo AU); offerings.md documents only Vinyasa / Yin / Beginners / Yang to Yin. Every downstream skill treated search demand as equivalent to service offering.
  → **Action — Gate A + Gate B coded into validator (2026-04-26):**
  - **Gate A:** brief flags Phase-0 → MUST emit `*-ad-copy-best-case.md` + `*-ad-copy-current-state.md`; CSV generated only from current-state. Validator CRITICAL-fails if single report or CSV contains gated-claim phrases.
  - **Gate B:** scan copy for service-claim phrases (22 yoga/wellness/therapy/fitness/beauty patterns); cross-check against `_engine/wiki/offerings.md` (single-program) or `{client-root}/_engine/wiki/offerings.md` (multi-program); CRITICAL-fail any unverified claim.
  - Full protocol in `references/offerings-cross-check.md`. Eval #7 covers gated-brief + offerings-mismatch scenario. Risk avoided: ACL §18/§29 false-advertising exposure + Google Ads policy disapprovals + near-100% bounce on /pricing/.
  **RULE:** Search demand ≠ service offering. Every persona, ad group, headline, callout, snippet must trace to a verified offerings.md entry — or drop, reframe, or wrap as `<<UNVERIFIED-CLAIM>>`.
- [2026-04-27] [Universal — applies to all skills] Same-Client Re-Run Rule landed in CLAUDE.md as a universal Always-Active section. Same-client/same-case re-runs overwrite outputs in place — no v1/v2/v3, no -DATE parallel filenames, no dated section headers preserving prior content. One file per role, current state only. Only `_engine/wiki/log.md` (by-design change log) and `_engine/wiki/briefs.md` (brief history with `[ACTIVE]`/`[SUPERSEDED]` markers) are append-only. **For this skill specifically:** _engine/working/CLIENT-ad-copy-report.md, _engine/working/CLIENT-google-ads.csv, _engine/working/CLIENT-meta-ads.csv, _engine/working/CLIENT-image-prompts.md, _engine/working/CLIENT-video-storyboards.md — all overwritten in place on re-run. Refresh Mode _v2/_v3 ad-NAMING (in Meta Ads Manager) is preservation-of-A/B-control, NOT a re-run pattern — those are distinct ad-copy rotations, not the same case being re-run. **RULE:** if you find yourself about to create a new file for an output that has the same logical role as an existing one, stop and overwrite the existing file instead.
- [2026-04-29] [STRUCTURAL REFACTOR] Folder convention changed: all skill internals (wiki, sources, working, configs) now live in `_engine/` subfolder; presentables (HTML/PDF/CSV/MP4) at folder root. Ad-copywriter intermediate CSVs (`*-google-ads.csv`, `*-meta-ads.csv`) are pre-bundle, so they go in `_engine/working/` (campaign-setup consumes them and produces the upload-ready bundle at folder root). → Updated all path references in SKILL.md, references/, scripts/, evals/.
- [2026-04-29] [STRUCTURAL REFACTOR — filename simplification] Output filename templates dropped redundant client/business-name prefix. Filename = deliverable type only: `ad-copy-report.md`, `ad-copy-best-case.md`, `ad-copy-current-state.md`, `google-ads.csv`, `meta-ads.csv`, `image-prompts.md`, `video-storyboards.md`, `prompt-library.html`, `rotation-brief.json` — folder location already encodes client + program. Validator detects both new short-name forms and legacy `{client}-`prefixed forms via substring match (`'in name'`), so backwards-compat is automatic. → Updated SKILL.md, references/refresh-mode.md, references/output-format-spec.md, references/image-prompt-patterns.md, references/offerings-cross-check.md, assets/README.md, scripts/validate_output.py docstring, evals/evals.json.
