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
Apply the 10 performance rules from image-prompt-patterns.md before writing any prompt.

**Mandatory rules (per `image-prompt-patterns.md`, A/B-validated 2026-04-27):**

1. **Standalone-prompt format** — every prompt is a complete copy-pasteable block. NO `[universal prefix]` placeholders, NO per-cell metadata above the prompt body. Brand prefix substituted in, aspect ratio embedded as natural language, ready to paste into Gemini / ChatGPT / Imagen.
2. **Dual-format** — every prompt MUST exist in BOTH spec-prose AND JSON form. JSON is wrapped with one instruction line ("Generate one image based on this design specification. Treat every field as a constraint. Use the exact_copy strings verbatim — render them as visible typography, not as concepts."). Modern models (Gemini 2+, Imagen 2) handle both reliably; analyst preference and per-tool performance dictate which to ship.
3. **Embedded text rendering allowed** — modern models render exact copy strings, headlines, ₹ glyphs, → arrows, chip text, and bracketed labels correctly. The previous "leave clean space for post-production overlay" rule is REVERTED. Use post-production overlay only when the analyst explicitly prefers Figma control.
4. **Reference-image flagging** — every prompt carries `requires_reference_image: bool` + `reference_subject: string` metadata. The HTML dashboard (Step 7.5) renders flagged prompts with an animated badge so the analyst sees the attachment requirement at scan-time. Flag `true` for: founder/team-member portraits, specific product shots, specific venue/location shots, custom logos. Flag `false` for: generic UI/dashboard mockups, conceptual illustrations, abstract data viz.

Use `image_gen_prompt_prefix` from creative brief as base prompt. Append per-ad specifics:
- Scene/subject changes per persona angle
- Aspect ratio instruction (4:5 feed, 9:16 stories, 1:1 square, 1.91:1 display)
- Text overlay zone instruction ("leave clean space at top 20% for text")
- P1/P2 priority from creative brief formats
- `requires_reference_image` + `reference_subject` per prompt

5. **Designer-brain mandate (added 2026-04-29 — see `image-prompt-patterns.md` §Designer-brain mandate).** Every prompt is a top-tier brand-spec hand-off, not a scene description. The skill thinks like an art director. Read four signals (conversion goal, emotional register, audience tier, sector context) and author the seven required blocks per prompt:
   - **BRAND DESIGN SYSTEM** — palette + typography + photography style + motif vocabulary
   - **COMPOSITION GRID** — aspect ratio + grid + zones in % or px
   - **SUBJECT** — frame coordinates, materials, colour grading direction
   - **LIGHT + SURFACE** — direction in degrees, hardness 0-1, falloff, surface materials
   - **TEXT ELEMENTS** — every embedded text piece: exact_copy + font + weight + size + colour + position + special-character emphasis
   - **DECORATIVE / VECTOR ELEMENTS** — gradients, motifs, dividers, callouts (drawn from brand motif library + sector vocabulary library); or `none — minimalist register intentional` declared
   - **NEGATIVE CONSTRAINTS** + **RENDER QUALITY** clause

   Authoring sequence: read four signals → derive design system floor from `_engine/brand-config.json` `design_system` block (scaffold a sector-default floor + write back to brand-config.json if absent) → layer `creative-brief.json` `visual_direction.design_system_overrides` → author the seven blocks (designer authority to embellish where brand vocabulary supports) → emit spec-prose + JSON for each.

   **Quality bar:** Digischola Self-Audit prompt library is the reference floor. If a prompt reads like "split-screen composition: left half shows a child" without pixel-anchored text-element specs / motif placements / light direction in degrees / negative constraints — it has not hit the bar. Validator hard-floor enforces this on every run.

Save as `{client-folder}/_engine/working/image-prompts.md`. The Step 7.5 dashboard renders both formats per prompt with tab toggles + reference-attachment badges.

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

### Step 7.5: Generate Ad Copy Dashboard HTML (MANDATORY)

Run `scripts/render_ad_copy_dashboard.py "<program-folder>"` to produce a presentation-grade HTML dashboard at the program folder root.

The script parses the four upstream outputs:
- `_engine/working/ad-copy-report.md` (5 ads × 3 primary text + headlines + descriptions, frameworks, Gate audit)
- `_engine/working/image-prompts.md` (image prompts with brand visual_direction prefix substituted)
- `_engine/working/video-storyboards.md` (frame-by-frame layers + combined VO scripts)
- `_engine/working/creative-brief.json` (campaigns + personas + visual_direction)

And reads `_engine/brand-config.json` (single-program) OR `{client-root}/_engine/brand-config.json` (multi-program — `_engine/` at the client root). Brand colors and fonts theme the dashboard automatically.

Saves as `{client-folder}/ad-copy-dashboard.html` (folder root — it's a presentable). The dashboard contains:
- Hero with KPI cards (Ads, Variants, Image prompts, Storyboards) + Gate A/B status pills
- Per-ad cards with framework, persona, audience, format, ID, primary-text variants (each with a 📋 Copy button), headlines + descriptions in collapsibles, CTA pill
- Image prompt grid with one card per prompt, full prompt visible, 📋 Copy full prompt button per card
- Video storyboard cards with frame-by-frame layer tables (Visual / Motion / Text overlay / Voiceover / Voice direction / Music) + Combined VO script with 📋 Copy VO button
- Voice / character / sensitivity audit list at the bottom

The script generalizes across all clients — single-program and multi-program. Brand-config-themed. Mobile-readable. Replaces the legacy `prompt-library.html` declared in `references/image-prompt-patterns.md` with broader scope (covers ad copy + prompts + storyboards + Gate audit, not just image prompts).

**Failure modes:**
- Missing `ad-copy-report.md` / `image-prompts.md` / `video-storyboards.md` → script exits with clear message naming missing files
- Missing brand-config.json → script falls back to neutral default palette + warns
- Markdown structure deviates from template → parser yields fewer cards but does not crash; check stdout for warnings

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
- [ ] Image prompts follow creative-research.md rules: light background bias (or brand-locked dark mode), high contrast, no Google Display text overlay
- [ ] **Each image prompt is standalone** — full prompt as one block, NO `[universal prefix]` placeholders, ready to paste
- [ ] **Each image prompt has BOTH spec-prose AND JSON formats** (per 2026-04-28 mandate) for analyst tool-fit testing
- [ ] **Each image prompt carries `requires_reference_image` + `reference_subject` metadata** so the dashboard can flag attachment-needed cards
- [ ] Video storyboards use frame layers (Visual / Motion / Text Overlay / Voiceover / Voice Direction / Music)
- [ ] Voiceover scripts are clean text only (no parentheticals, stage directions, or ALL CAPS); word count within duration target (~35-40 words per 15s, ~70-80 per 30s)
- [ ] Message match honored when creative brief specifies `landing_page.message_match_notes`
- [ ] **Step 7.5 dashboard generated** — `ad-copy-dashboard.html` exists at folder root, all sections rendered, copy buttons functional, brand-config-themed (not generic defaults)
- [ ] `scripts/validate_output.py` passes with 0 CRITICAL failures (including the new dashboard-presence check)
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
- [2026-04-29] [ISKM Weekend Love Feast — multi-program religious-content compliance pattern] Successfully ran ad-copywriter for a temple recurring-retention campaign with three brand-voice rules that uniquely shape Meta copy: (1) no em dashes (universal Mayank rule), (2) no "ISKCON" heritage references (banned in Singapore 1970s — brand confusion + legal risk), (3) no overt deity close-ups in cold/LAL ads (Meta sensitive-content auto-rejection risk). The 5-angle creative library deliberately reserves deity-adjacent imagery for the Festival Follow-On strict-retarget creative ONLY (Nṛsiṁha pixel audience = already warm, lower rejection risk, contained blast radius if rejected). All other 4 angles lead with community / family / food / education framing. **RULE:** For temple / religious-org ad copy at Meta, default to community/family/food/education leading visuals + copy. Reserve deity imagery for strict-retarget audiences only (warm pixel users who self-selected). Document this split explicitly in the ad-copy-report compliance audit so visual-generator inherits the rule.
- [2026-04-29] [Validator path-detection — multi-program offerings.md auto-discovery] Gate B validator's offerings.md auto-discovery checks `{client}/_engine/wiki/offerings.md` (single-program) but doesn't always reach `{client-root}/_engine/wiki/offerings.md` (multi-program — `_engine/` at the client root, formerly `_shared/`). For ISKM (multi-program), the file lives at `Sri Krishna Mandir/_engine/wiki/offerings.md` (one level up from the program folder). Validator emitted "Gate B unverified — no offerings.md found" warning even though the manual Gate B audit was performed and documented inline in ad-copy-report.md. Patch candidate (low-medium priority): widen Gate B path-detection to also probe `{program}/../_engine/wiki/offerings.md` for multi-program clients. Until patched, document the manual audit table inline in `ad-copy-report.md` under a `## Gate Audit (auto-generated)` section per the SKILL.md template. **RULE:** Multi-program ad-copywriter runs MUST include the inline Gate Audit table in ad-copy-report.md — the validator warning becomes advisory because the audit is human-verifiable in the report.
- [2026-04-29] [DASHBOARD GAP CLOSED — `prompt-library.html` was declared MANDATORY but never wired up] Three places in the skill mentioned `prompt-library.html` as a required deliverable: `references/image-prompt-patterns.md` line 84 (full spec, "MANDATORY"), `assets/README.md` line 23 (folder-root presentable), and the 2026-04-29 filename-simplification learning. But the actual workflow path was missing — no Step in SKILL.md invoked it, no template existed in `assets/`, no render script existed in `scripts/`, validator didn't enforce presence. Mayank caught this on the WLF run when the dashboard didn't get produced despite being on the file roster. → **Patched 2026-04-29:** (1) Built `scripts/render_ad_copy_dashboard.py` (parses ad-copy-report.md + image-prompts.md + video-storyboards.md + creative-brief.json + brand-config.json with multi-program path probing → emits unified HTML dashboard with 5 ad cards + image prompt grid + storyboard frame tables + Gate audit summary, all with copy buttons and brand-config-themed styling). (2) Added Step 7.5 in SKILL.md (MANDATORY, between Step 7 video storyboards and Step 8 validate). (3) Renamed deliverable from narrow `prompt-library.html` to broader `ad-copy-dashboard.html` to reflect that it now covers ad copy + prompts + storyboards + Gate audit, not just image prompts. Validator accepts both names for backwards-compat. (4) Added `validate_dashboard()` + `check_dashboard_presence()` to validate_output.py — CRITICAL-fails if dashboard missing at folder root when other ad-copy outputs exist. (5) Updated `references/image-prompt-patterns.md` to reflect the broader scope. Verified on WLF: 5 ads + 9 image prompts + 2 storyboards rendered, 65 copy buttons, 80813 chars, validator presence-check passes. **RULE:** When a deliverable is declared MANDATORY in references/, it MUST have all four wiring components: (a) Step in SKILL.md that invokes it, (b) template/asset OR render script that produces it, (c) validator check that enforces presence + structure, (d) updated checklist item. Without all four, the deliverable will silently be skipped on real runs even though the documentation declares it required. Skill-architecture audit: `scripts/audit_skill.py` (planned) should walk references/ for "MANDATORY" markers and confirm all four components exist.

- [2026-04-29] [Dashboard copy-button bug — JSON form with embedded `"` broke onclick attribute] After re-running ad-copywriter on ISKM WLF with the new dual-format image-prompts.md, the dashboard's "Copy JSON" buttons silently failed. Cause: `render_ad_copy_dashboard.py` embedded the full JSON content inside `onclick="copyText('...', this)"` HTML attributes. The JSON content has many double quotes (`"brand_system": {`), so the first `"` closed the HTML attribute prematurely → broken button, no console error, just nothing happens on click. Spec-prose buttons worked because prose has fewer raw quotes. → **Patched 2026-04-29:** switched all image-prompt copy buttons (and legacy single-format fallback) to `copyFrom('elementId', this)` pattern: each prompt panel gets a unique DOM id (`prompt-N-prose` / `prompt-N-json`), buttons reference the id, JS function reads `document.getElementById(id).textContent`. No content embedded in attributes → no escape gymnastics → guaranteed match between displayed and copied content. **RULE:** Any time a render script needs to put long text content inside an HTML attribute, use the `copyFrom(id)` pattern instead of `copyText(content)`. The simple-text pattern is only safe for short headline-/description-length strings that have been js_escape'd. JSON, markdown bodies, multi-line prose — always go through `textContent` of a rendered element. Patch candidate: extend `validate_dashboard()` to flag any `onclick="copyText\([^)]*"\b` (literal double-quote inside copyText argument) as a CRITICAL — would catch the bug class automatically next time.

- [2026-04-29] [ISKM Weekend Love Feast — designer-brain depth verified end-to-end on temple/cultural-event sector] Re-ran ad-copywriter on WLF after brand-DNA reset to v1.0 events-sub-brand tokens (pinkCTA #f8a4c0 reserved-for-CTA-pill-only, gold accent #f4c96b, navy #1e3a6e, cream #fdf5ed, Playfair Display + Source Sans Pro). Tested four end-to-end design-system inheritance contracts: (1) brand-config.json `design_system` block as the floor for the skill, (2) creative-brief.json `_design_system_inheritance` + `_reference_manifest` + per-creative `design_system_overrides` as the campaign-specific layer, (3) reference manifest at `_engine/references/images/manifest.json` with sector-aware `requires_reference_image: true` defaults for temple/cultural-event sector, (4) validator hard-floor 7-block check + quality scoring. **Result:** 9 prompts × 7 required blocks all present, avg quality score 24.3/30, min 21/30 — exceeded Digischola Self-Audit reference floor target (22+/30). 8 of 9 prompts use real reference manifest IDs (no generic stock placeholders). Brand-DNA bleed prevented (validator + manual sweep flagged zero parent-org-token leakage into events-sub-brand creatives). Copy is brand-token-agnostic so it survived the re-run untouched per Same-Client Re-Run Rule. **RULE:** Designer-brain depth is now the production floor for image prompts, not the aspiration. Every photographic prompt for temple/wellness/events/cultural-org sectors flags `requires_reference_image: true` by default with manifest-resolved file_path; abstract/UI/data-viz prompts can flag false. Design-system inheritance flows brand-config.json → creative-brief.json → image-prompts.md verbatim — no hand-translation, no token drift. The validator hard-floor is the contract: 7 blocks present + min 8/30 quality score per prompt + avg ≥18/30 across the set.

- [2026-04-29] [Same-Client Re-Run Rule end-to-end test — paid-media-strategy → ad-copywriter chain with brand-DNA reset trigger] Re-ran the full strategy → copywriter chain on ISKM WLF without creating any v2/v3 files. Trigger was a brand-DNA reset upstream (parent-org → events-sub-brand v1.0). Strategy report + media plan were brand-agnostic so survived untouched; creative-brief.json received schema_version 1.1 inheritance blocks; ad-copy-report.md + meta-ads.csv were brand-token-agnostic so survived; image-prompts.md was fully rewritten in place at designer-brain depth; video-storyboards.md got 2 stale typography references updated in place. Dashboard re-rendered. All 4 deliverables overwrite-in-place per Same-Client Re-Run Rule. **RULE:** Re-run trigger detection — if upstream brand-config.json or creative-brief.json has changed AFTER the last ad-copy run, ad-copywriter MUST re-run from Step 6 onwards (image-prompts + video-storyboards + dashboard). Steps 4-5 (copy + CSV) skip if voice rules unchanged. The skill should detect this via mtime comparison (creative-brief.json.mtime vs image-prompts.md.mtime) and warn if older outputs are stale. Patch candidate: add `check_freshness()` to validate_output.py that flags downstream outputs older than upstream inputs.

- [2026-04-27 → 2026-04-28] [DigiSchola — image-prompt UX rebuild + JSON/prose A/B + reference-flag system] Founder feedback during DigiSchola Self-Audit run surfaced three real problems in image prompt deliverables that hit every client, not just one. (1) Prompts were split into top-of-file `[universal prefix]` + per-cell body + above-block metadata — analyst had to mentally substitute the prefix and concatenate manually for every Gemini paste, ~30 manual operations for a 6-prompt set. (2) The "no embedded text rendering" rule (text overlay must be Figma-after-the-fact because AI models hallucinate text) was provably wrong on modern models — Gemini 2+ and ChatGPT-Imagen 2 rendered exact chip text + ₹ glyph + → arrow + headline correctly first-try in a 4-permutation A/B test (G-JSON, G-Prose, C-JSON, C-Prose). (3) When a prompt depicts a real-world subject (founder face, product, venue), the analyst routinely forgot to attach the reference image because the requirement was buried in prose metadata. → **Three patches landed in `references/image-prompt-patterns.md` (2026-04-27 → 2026-04-28):** (a) **Standalone-prompt mandate** — every prompt is one complete copy-pasteable block, prefix substituted in, aspect ratio embedded as natural language, no `[universal prefix]` placeholders. (b) **Dual-format mandate** — every prompt MUST exist in both spec-prose AND JSON form (JSON wrapped with one instruction line so the model treats it as design-spec not data). Analyst preference and per-tool performance dictate which to ship; both formats live in the dashboard with tab toggles. (c) **Reference-image flagging** — every prompt carries `requires_reference_image: bool` + `reference_subject: string` metadata; HTML dashboard renders flagged cards with a pulsing/animated amber paperclip badge so attachment requirement is impossible to miss at scan-time. Generalizes across clients: founder portraits (personal-brand), product packaging (D2C), venue exteriors (events/wellness), team headshots (B2B). **RULE:** Image prompt deliverables are paste-once production tools, not analyst-readable archives. Every prompt is standalone-complete, available in both formats, and self-flags its attachment requirement. The AI-models-hallucinate-text rule is dead — write the embedded text into the prompt and let the model render it. The HTML dashboard (Step 7.5) is where this all comes together; the markdown file is the audit trail. Pending wiring (separate session): `scripts/render_ad_copy_dashboard.py` should be extended to render the JSON/prose tabs + animated reference badges per the new mandate — current script renders single-format flat prompt blocks. Until that wires up, ad-hoc HTML output for clients should follow the DigiSchola `prompt-library.html` pattern as a manual reference.
