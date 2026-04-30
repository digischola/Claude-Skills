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

**Voice-library bedrock (mandatory before drafting):** Read `{client}/_engine/wiki/voice-library.json` (or `{client-root}/_engine/wiki/voice-library.json` for multi-program). The brief's per-creative `voice_anchor.pattern_id` points to a `headline_patterns[]` entry — match its structure, max_words, tone_tags. Per-creative `cta_verb_noun_pair` defines the CTA. Root-level `event_facts.canonical_string` (event campaigns) MUST appear verbatim or near-verbatim (≥80% similarity) in every variant's trust-line / headline / body. `voice_rules.forbidden_phrases` is a hard ban list. Spec: `~/.claude/shared-context/voice-library-spec.md`. `validate_voice_library_compliance()` enforces.

**Frameworks (secondary, voice-library wins on conflict):** Google RSA = Feature-Benefit-Proof; Meta Prospecting = PAS or BAB; Meta Retargeting = Social Proof Stack; Video = AIDA; long Meta primary = AIDA or PAS.

**Google RSA per ad group:** 15 H ≤30 chars + 4 D ≤90 chars + 2 paths ≤15 chars; pin brand→H1, CTA→D1; headlines must work with any description.

**Meta per ad:** 3-5 primary (≤125 for feed) + 3-5 headlines ≤40 + desc ≤30 + CTA + A/B variants from `ab_testing.test_pairs`.

**Quality:** every char counts; proof woven in per `references/copywriting-frameworks.md`; brand voice do/don't from creative brief respected; label each block `[BRIEF]` / `[GENERATED]` / `[ADAPTED]`.

**Gate B (always-on):** verify every service/modality/class-style phrase in `_engine/wiki/offerings.md` (single OR multi-program client-root). Unmatched → drop, reframe, or wrap `<<UNVERIFIED-CLAIM:phrase>>`. Full protocol + false-claim categories: `references/offerings-cross-check.md` §Gate B.

**Output filename:** Default `_engine/working/ad-copy-report.md`. **Gate A fired** → two files (`ad-copy-best-case.md` + `ad-copy-current-state.md`); Step 5 CSV from current-state only. Both files MUST include `## Gate Audit (auto-generated)` section per `references/offerings-cross-check.md` template.

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

Use `image_gen_prompt_prefix` from creative brief as base prompt. Append per-ad: scene/subject changes per persona, aspect ratio per format → aspect map (full table in `references/image-prompt-patterns.md`; validator-enforced — key rule: **carousel = 1:1 ONLY**, single_image = 4:5/1:1, reel/story = 9:16, GDN = 1.91:1), text overlay zone, P1/P2 priority, `requires_reference_image` + `reference_subject`.

**Carousel card-count rule (validator-enforced):** If a creative's `format_priority` contains `carousel_N_card` (e.g. `carousel_5_card`, `carousel_5_card_static`), author **exactly N cards** with **contiguous CARD-1, CARD-2, ..., CARD-N IDs** under that creative. Missing or extra cards CRITICAL-fail at validation. Do not analyst-judge "4 cards tells the story enough" — the spec is the contract. If 4 is genuinely correct, change the brief upstream to `carousel_4_card`.

5. **Designer-brain mandate** — every prompt = 7 blocks (BRAND DESIGN SYSTEM / COMPOSITION GRID / SUBJECT / LIGHT + SURFACE / TEXT ELEMENTS / DECORATIVE / NEGATIVE CONSTRAINTS + RENDER QUALITY). Authoring sequence: 4 signals (goal/register/tier/sector) → brand-config `design_system` floor → creative-brief `design_system_overrides` overlay → emit spec-prose + JSON. Validator hard-floor enforces 7 blocks present + ≥8/30 per prompt + avg ≥18/30. Full spec: `references/image-prompt-patterns.md` §Designer-brain mandate.

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

Saves as `{client-folder}/ad-copy-dashboard.html` (folder root). Dashboard sections + failure modes documented in script docstring. Brand-config-themed, mobile-readable, multi-program path-aware.

### Step 8: Validate & Update Wiki

Run `scripts/validate_output.py` against all deliverables. Fix any CRITICAL failures (character limits, missing fields).

Update `{client-folder}/_engine/wiki/log.md` — add AD-COPYWRITER COMPLETE entry.
Update `{client-folder}/_engine/wiki/index.md` — update downstream status.

Flag downstream: campaign-setup skill can consume the CSV sheets + image prompts.

## Output Checklist

- [ ] Mode + platform specs loaded; char limits enforced (RSA 30/90/15; Meta 125/40/30)
- [ ] Framework labeled per campaign + source labels (`[BRIEF]` / `[GENERATED]` / `[ADAPTED]`) on every block
- [ ] Google CSV (15 H + 4 D / ad group) and/or Meta CSV (primary + headline + desc + CTA) per platform scope
- [ ] Image prompts: standalone-pasteable + dual-format (spec-prose + JSON) + `requires_reference_image` + `reference_subject` + format→aspect rule respected
- [ ] Designer-brain depth: 7 blocks per prompt, validator hard-floor passes
- [ ] Video storyboards: frame layers + clean VO (no parentheticals, ~35-40 words / 15s, ~70-80 / 30s)
- [ ] Message match honored when `landing_page.message_match_notes` present
- [ ] Step 7.5 dashboard at folder root, brand-config-themed, copy buttons functional
- [ ] `scripts/validate_output.py` 0 CRITICAL; wiki log + downstream flag updated

## Failure Handling

- Character limit violation → CRITICAL, rewrite the offending copy before output
- Missing creative brief in downstream mode → fall back to standalone mode, warn user
- Platform specs file not found → warn, use hardcoded limits (RSA: 30/90, Meta: 125/40/30)

## Learnings & Rules

<!-- Pruned 2026-04-30: 9 entries collapsed to one-liners (encoded into validators / references / kernel). Full text in git history. Keep ≤30 lines per kernel. -->

- [2026-04-30] [carousel aspect-ratio bug] Authored WLF carousel cards at 4:5 instead of mandatory 1:1. Patched: format→aspect mapping table in Step 6 + `validate_format_aspect_consistency()` in validator + elevated rule in `references/image-prompt-patterns.md` line 329 + eval #8. **RULE:** Carousel = 1:1 ONLY. All cards in one carousel must share aspect. Validator enforces every run.

- [2026-04-30] [BEDROCK — voice-library compliance (cross-skill bedrock)] User flag on WLF carousel: 5 cards / 5 different trust-line strings / 3× "Reserve a seat" CTA reuse / fresh-invented headlines drifting from proven $0.71 CPL Nrsimha voice. Root cause: skill enforced visual rigor (7 designer-brain blocks) but had no copy-rigor anchor — TEXT_ELEMENTS specified font/size/color but not headline cadence / event-fact anchor / CTA verb-noun specificity. Patched: Step 4 reads `voice-library.json` before drafting; brief carries `event_facts.canonical_string` (must appear verbatim every variant) + per-creative `voice_anchor.pattern_id` + `cta_verb_noun_pair`; new `validate_voice_library_compliance()` enforces 5 checks (event-fact anchor consistency / max headline words / forbidden phrases / pattern-anchor compliance / CTA semantic specificity). Spec: `~/.claude/shared-context/voice-library-spec.md`. Cross-skill bedrock — business-analysis Step 8 extracts voice-library.json (MODE_A from past creatives OR MODE_B 3-tier bootstrap), paid-media-strategy 5.5 inherits into creative-brief.json, ad-copywriter validates the chain. Eval #11. **RULE:** No ad copy ships without voice-library compliance pass. Copy-rigor is a contract, not a vibe.

- [2026-04-30] [carousel CARD-COUNT bug — same failure class as aspect bug] Authored WLF-AD-01 with 4 cards (CARD-1, 2, 4, 5 — skipped CARD-3) when brief specified `format_priority: ["carousel_5_card", ...]`. Analyst-brain decided 4 cards "told the story enough" — but the `_5_card` suffix is a contract, not a suggestion. Patched: Step 6 `Carousel card-count rule` + `validate_carousel_card_count()` in validator (parses `carousel_N_card` pattern, counts CARD-X prompts per creative_id, CRITICAL on count mismatch OR non-contiguous indices) + eval #9. **RULE:** `carousel_N_card` in brief = exactly N contiguous CARD-1..CARD-N prompts. No card-skip storytelling. If 4 is genuinely correct, change brief to `carousel_4_card` upstream — don't silently under-deliver. Same authoring-discipline failure as the aspect bug — brief format-spec is the contract.

- [2026-04-26] [Gate A + Gate B — false-claims prevention] Prevented production-ready ad copy claiming services that don't exist (free trial, prenatal yoga, chair yoga). **Gate A:** Phase-0 brief flag → emit best-case + current-state files; CSV from current-state only. **Gate B:** scan service-claim phrases → cross-check `_engine/wiki/offerings.md` (single OR multi-program client-root); CRITICAL on unverified. Full protocol: `references/offerings-cross-check.md`. Eval #7. **RULE:** Search demand ≠ service offering. Every service phrase traces to offerings.md or is dropped/reframed/wrapped as `<<UNVERIFIED-CLAIM>>`.

- [2026-04-29] [dashboard wiring contract] When a deliverable is declared MANDATORY in references/, it MUST have all 4 wiring components: (a) Step in SKILL.md, (b) render script or template, (c) validator presence check, (d) checklist item. Otherwise it silently never produces. Verified by the `prompt-library.html` → `ad-copy-dashboard.html` rebuild (Step 7.5 + `render_ad_copy_dashboard.py` + `check_dashboard_presence()` + checklist).

- [2026-04-29] [designer-brain depth = production floor] Image prompts at designer-brain depth (7 blocks, ≥18/30 avg quality) verified as production floor on WLF temple/event sector. Brand-DNA inheritance: brand-config.json `design_system` → creative-brief.json `design_system_overrides` → image-prompts.md verbatim. Photographic temple/wellness/events prompts default `requires_reference_image: true`. Validator hard-floor enforces.

<!-- Older entries — see git for full text:
- [2026-04-16] Refresh Mode (3rd op mode) → references/refresh-mode.md + eval #6
- [2026-04-27] Same-Client Re-Run Rule → kernel CLAUDE.md (universal)
- [2026-04-29] Folder convention `_engine/` for internals; presentables at folder root → kernel + paths updated
- [2026-04-29] Filename simplification (no client prefix) → all references + validator substring match
- [2026-04-29] Temple/religious Meta compliance (no deity in cold/LAL) → references/refresh-mode.md + creative-brief voice rules
- [2026-04-29] Multi-program offerings.md path-probing → manual inline Gate Audit table workaround
- [2026-04-29] Dashboard `copyFrom(id)` pattern (avoid attribute-embedded JSON) → render_ad_copy_dashboard.py
- [2026-04-29] Re-run trigger via mtime comparison → patch candidate, check_freshness()
- [2026-04-27→28] Standalone + dual-format + reference-flag mandate → references/image-prompt-patterns.md
-->

