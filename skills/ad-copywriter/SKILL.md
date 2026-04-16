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

## Process Overview

### Step 1: Input Check & Mode Selection

Check in this order — Refresh Mode takes priority because it's the narrowest and most time-sensitive trigger:

**Refresh Mode** (fatigue rotation) — if `{client-folder}/deliverables/*-rotation-brief.json` exists:
- Load `references/refresh-mode.md` for the full workflow — it overrides Steps 2, 4, 5, 8
- Load the rotation brief, the original `*-creative-brief.json`, and the wiki
- State explicitly in output: "Refresh Mode — N fatigued creatives being rotated"
- Skip Step 2 entirely

**Downstream mode** (creative brief exists, no rotation brief):
- Read the creative brief JSON — campaigns, personas, hooks, formats, visual_direction, landing_page, ab_testing, proof_elements, brand_voice
- Read `{client-folder}/wiki/strategy.md` for competitor context
- Read `{client-folder}/deliverables/brand-config.json` for brand identity
- Skip to Step 3

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

Save as `{client-folder}/deliverables/{business-name}-ad-copy-report.md`.

### Step 5: Generate Platform CSV Sheets

Read `references/output-format-spec.md` for column formats.

**Google Ads CSV** (`{business-name}-google-ads.csv`):
- One row per RSA: Campaign, Ad Group, H1-H15, D1-D4, Path1, Path2, Pin notes, Final URL
- Character limit validation on every cell — CRITICAL, do not ship over-limit copy

**Meta Ads CSV** (`{business-name}-meta-ads.csv`):
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

Save as `{client-folder}/deliverables/{business-name}-image-prompts.md`.

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

Save as `{client-folder}/deliverables/{business-name}-video-storyboards.md`.

### Step 8: Validate & Update Wiki

Run `scripts/validate_output.py` against all deliverables. Fix any CRITICAL failures (character limits, missing fields).

Update `{client-folder}/wiki/log.md` — add AD-COPYWRITER COMPLETE entry.
Update `{client-folder}/wiki/index.md` — update downstream status.

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

- [2026-04-13] [PREMIUM ARCHITECTURE] Finding: All 16 Google descriptions failed validation on first pass. Report showed "88 chars" but actual count was 91-100. Cause: manual char counting is unreliable, especially with punctuation-heavy copy. → Action: Always run validate_output.py BEFORE writing the report char count column. Never trust hand-counted chars.
- [2026-04-13] [PREMIUM ARCHITECTURE] Finding: Em-dashes (—) in descriptions waste 1 char each vs using a period or comma, and introduce counting ambiguity. → Action: Avoid em-dashes in Google descriptions. Use periods or commas instead. Save chars for actual copy.
- [2026-04-13] [PREMIUM ARCHITECTURE] Finding: validate_output.py had broken final summary logic using sys.stdout.getvalue() which only works with StringIO. → Action: Replaced with counter-based tracking (total_criticals, total_warnings) and flush_logs() helper function.
- [2026-04-13] [PREMIUM ARCHITECTURE] Finding: Meta primary text over 125 chars is expected and normal (truncation in feed view). Validator correctly flags as WARNING not CRITICAL. → Action: No change — warnings are informational, not blocking.
- [2026-04-13] [PREMIUM ARCHITECTURE] Finding: 5 RSAs x 4 descriptions = 20 descriptions to validate. At 90-char limit, even 1-2 extra chars per description compounds to 16 CRITICALs. → Action: Target 75 chars for descriptions, giving 15-char safety margin. Only push to 85+ when absolutely needed for copy quality.
- [2026-04-13] [GENERAL] Finding: Background agents cannot write files (permission issues in this environment). → Action: Always write files in main thread. Use agents only for research/read tasks.
- [2026-04-16] [GENERAL] Finding: v1 image prompts were 85-140 words (too bloated) and based on aesthetic assumptions, not performance data. Research shows: shorter prompts (1-3 sentences after prefix) produce more consistent AI output, dark images underperform by 70%, high contrast = +32% CTR, Google Display must have NO text overlay. → Action: Added creative-research.md reference file, updated image-prompt-patterns.md with 10 performance rules, prompt templates now include "ultra-realistic photograph" + specific lens + light background bias. Step 6 and Step 7 now load creative-research.md.
- [2026-04-16] [GENERAL] Finding: validate_output.py video storyboard regex only catches `Voiceover:` but deliverable uses `**Voiceover:**` (markdown bold). Reports 7 "missing" VO when all 10 frames have VO. Image prompt regex also undercounts blockquoted prompts. → Action: Low priority fix — warnings are false positives, not false negatives. Validator still catches real structural issues (missing fields, char limits).
- [2026-04-16] [Validator] Finding: Deep-read audit upgraded the `**Voiceover:**` issue from "low priority" to a real bug. The regex does technically match mid-string, but the capture group `(.+)` swallowed the trailing `**`, so VO text came back as `** Hello world` instead of `Hello world`. Polluted word counts, combined-VO-script generation, and stage-direction checks. Same issue on `text overlay:`. → Action: Updated both patterns in `scripts/validate_output.py` to `\*{0,2}voiceover:\*{0,2}\s*(.+)` (and equivalent for text overlay) so leading/trailing `**` around the label is absorbed, not captured. Smoke-tested against plain, bold, bullet+bold, heading, and blockquote+bold forms — all capture clean text.
- [2026-04-16] [Knowledge promotion] Finding: ad-copywriter was the only skill of 8 without an Output Checklist in SKILL.md — paid-media-strategy, business-analysis, market-research, campaign-setup, landing-page-audit, landing-page-builder, post-launch-optimization all had one. Missing checklist meant completion criteria were implicit and varied session-to-session. → Action: Added 13-item Output Checklist between Step 8 close and Failure Handling. Covers mode detection, character limits, framework labels, source labels, per-platform CSV outputs, image-prompt prefix usage, creative-research rule compliance, VO script cleanliness + duration word budget, message-match honoring, validator pass, wiki update.
- [2026-04-16] [Validator hardening] Finding: three validator blind spots meant brand + message-match rules existed in SKILL.md but weren't enforced. (a) `image_gen_prompt_prefix` from creative-brief never verified in image-prompts output — skills could silently drop brand-consistent prompts. (b) `landing_page.message_match_notes` never verified in generated copy — losing the ad→LP echo that drives +20-35% conversion lift. (c) VO word-count vs video duration budget never checked — AI-voice delivery would sound rushed when frames went >25 words. → Action: extended `scripts/validate_output.py` to accept an optional `*-creative-brief.json` arg. On load, it (1) runs a 5-word significant-window match to verify the image prompt prefix flows through, (2) does a word-overlap check to confirm message_match_notes language is echoed in the ad copy report at ≥50% coverage, and (3) flags frames with >25 VO words and storyboards whose total VO exceeds `~2.5 wps × declared-seconds × 1.2` budget. Smoke-tested against a mock Bali Retreats brief — all three checks fire correctly on passing and failing inputs.
- [2026-04-16] [Refresh Mode — learning loop closes] Finding: creative fatigue was detected by post-launch-optimization Layer 4 (URGENT/PLAN/MONITOR status) but had no automated handoff to ad-copywriter — the analyst had to manually translate fatigue flags into a new copy brief each week, losing framework/brand consistency and creating multi-hour iteration loops. → Action: added Refresh Mode as a third operating mode alongside Standalone and Downstream. Trigger: `*-rotation-brief.json` in the client's deliverables folder. Created `references/refresh-mode.md` documenting the rotation-brief schema (fatigued creatives with fatigue signals, original copy, `keep[]` / `change[]` constraints, new_angles_to_try, strategy_guardrails), the workflow overrides for Steps 2/4/5/8, the `[REFRESH]` source label, and versioned ad naming (`_v2`, `_v3`). SKILL.md Step 1 now detects rotation-brief first (highest-priority mode). post-launch-optimization Layer 4 now emits the rotation-brief JSON. New eval #6 covers the full path. **RULE:** Creative refresh is a closed loop: fatigue signal → machine-readable handoff → drop-in replacement copy with original preserved as A/B control. No more manual translation.
