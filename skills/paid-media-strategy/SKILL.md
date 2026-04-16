---
name: paid-media-strategy
description: "Per-platform paid media strategy for Google Ads, Meta Ads, or both. Generates campaign architecture, budget allocation, bidding strategy, audience targeting, creative direction, and phased execution plan. Reads market-research wiki for business context. Outputs HTML strategy dashboard + CSV media plan. Use when user mentions: media strategy, campaign strategy, ad strategy, paid strategy, Google Ads strategy, Meta Ads strategy, campaign plan, media plan, budget allocation, campaign architecture, targeting strategy, bidding strategy. Also trigger when market-research is complete and user wants to move to campaign planning. Do NOT trigger for: ad copy writing, creative production, campaign build/setup in Ads Manager, performance reporting, market research (use market-research skill instead)."
---

# Paid Media Strategy

Senior media buyer-level campaign strategy for Google Ads, Meta Ads, or both platforms. Sits between market-research and ad-copywriter/campaign-setup in the pipeline. Consumes wiki data from market research, applies platform-specific decision logic, and produces actionable strategy deliverables.

## Context Loading

Read these shared context files before starting:
- `shared-context/analyst-profile.md` — workflow, client types, quality standards
- `shared-context/accuracy-protocol.md` — 3 accuracy rules for all data handling

If a client wiki exists (`{client-folder}/wiki/`), read it first — strategy.md, offerings.md, competitors.md, audiences.md. The wiki is the primary input.

## Process Overview

### Step 1: Client Intake & Wiki Check

**Check for existing research.** Look for `{client-folder}/wiki/` from a prior market-research session. If it exists, read all wiki pages — this is the foundation. If no wiki exists, flag that market research should run first (this skill depends on it). **If no wiki exists and user wants to skip market-research:** proceed with intake questions only. Mark all wiki-dependent insights as BLANK. Flag in report: "Strategy based on limited data — market-research skill recommended before launch."

**Gather any missing info:** business name, URL, platform focus (Google, Meta, or Both), monthly budget range, primary conversion action (purchase, lead, app install, booking), geographic targeting scope, any existing campaigns or account history.

**Platform selection:** Ask which platform(s) this strategy covers. This determines which reference files to load and which decision trees to apply.

### Step 2: Guided Strategy Questions

Read `references/guided-questions.md` for the full question framework.

Ask 3-5 targeted questions based on platform + business type + wiki data. Questions are NOT generic — they're informed by the wiki findings and designed to fill strategy-critical gaps.

**Question categories** (select most relevant, not all):
- Conversion maturity: What conversion actions are tracked? Volume per week?
- Account history: New account or existing? Current performance benchmarks?
- Creative assets: What creative formats are available? Video capability?
- Competitive pressure: Willing to compete on branded terms? Competitor conquesting?
- Growth priority: Volume vs efficiency? Scale vs profitability?
- Sales cycle: How long from click to close? Offline conversion component?

**If user can't answer critical questions** (conversion tracking, account history): document as BLANK and use conservative assumptions. Flag: "Strategy uses conservative defaults — refine after 2 weeks of data."

Wait for answers before proceeding. These answers shape every downstream decision.

### Step 3: Platform Strategy Generation

Read the relevant reference file(s) based on platform selection:
- **Google Ads:** Read `references/google-ads-system.md` — campaign types, bidding, keywords, Quality Score, PMax, conversion tracking
- **Meta Ads:** Read `references/meta-ads-system.md` — ODAX objectives, Advantage+, Andromeda, audience architecture, placements, CAPI/Pixel
- **Both:** Read both files

Read `references/strategy-frameworks.md` for decision trees covering:
- Campaign type selection logic
- Bidding strategy selection logic
- Audience/targeting architecture
- Budget allocation frameworks
- Creative format recommendations
- Measurement & attribution setup

**Generate strategy across these dimensions:**

1. **Campaign Architecture** — which campaign types, how many, naming convention, structure rationale
2. **Bidding Strategy** — which strategy per campaign, why, when to change, learning phase management
3. **Audience & Targeting** — targeting layers, audience segments, exclusions, observation vs targeting
4. **Budget Allocation** — spend split by campaign, platform (if both), phase, and rationale
5. **Creative Direction** — format recommendations, messaging angles (from wiki personas), testing framework
6. **Conversion Setup** — what to track, primary vs secondary conversions, attribution window
7. **Measurement Plan** — KPIs per campaign, reporting cadence, optimization triggers
8. **Phased Execution** — Phase 1 (0-30 days: foundation), Phase 2 (30-60: optimize), Phase 3 (60-90: scale)

Apply accuracy protocol: [EXTRACTED] for wiki data, [INFERRED] for strategy synthesis, BLANK for unknowns.

### Step 4: Generate Strategy Report (Markdown)

Read `references/report-structure.md` for the full template.

Write the strategy report covering all 8 dimensions. Each section includes: rationale, specific settings/values, decision logic explanation, and "what to watch" monitoring notes.

Save as `{client-folder}/deliverables/{business-name}-paid-media-strategy.md`.

### Step 5: Generate HTML Strategy Dashboard

**Brand-config gate (mandatory, do first):**
1. Read `{client-folder}/deliverables/brand-config.json` — extract colors, fonts, anomalies, manual_override notes.
2. Check for existing client dashboards (e.g., `*-research-dashboard.html`) — if one exists, match its design language (light/dark mode, section pattern, color palette, font stack). Consistency across deliverables is non-negotiable.
3. For monochromatic brands (primary = black/white): derive accent tones from product photography or manual_override guidance — never use generic tech colors.
4. Map brand fonts to web-safe fallbacks (e.g., IvyPresto Display → Georgia serif, FH Oscar → Helvetica Neue).

**Template selection** (see `assets/README.md` for decision tree):
- ONE platform → `template-single-platform.html`
- TWO platforms, both launch together → `template-dual-simultaneous.html`
- TWO platforms, one launches first → `template-dual-phased.html`

Adapt template to match brand-config — override default dark mode if brand/existing dashboards use light mode.

Read `references/dashboard-specs.md` for the full specification. Populate all `{{PLACEHOLDER}}` variables with strategy data and brand-derived colors/fonts.

Save as `{client-folder}/deliverables/{business-name}-strategy-dashboard.html`.

### Step 5.5: Generate Creative Brief JSON

Generate a structured creative brief for the ad-copywriter skill. Read `references/creative-brief-spec.md` for schema and field source labels. Populate from strategy report (campaigns, formats, hooks) + wiki (personas, pain points, brand voice). Save as `{client-folder}/deliverables/{business-name}-creative-brief.json`.

### Step 6: Generate CSV Media Plan

Read `references/csv-output-specs.md` for format.

Create a structured CSV/spreadsheet with:
- Campaign-level view: campaign name, type, objective, daily budget, bidding strategy, target metric
- Ad set/ad group view: targeting details, audience size estimates, placements
- Monthly budget projection: spend by month across phases
- KPI targets: expected CPC, CTR, conversion rate, CPA/ROAS by campaign

Save as `{client-folder}/deliverables/{business-name}-media-plan.csv`.

### Step 7: Update Wiki & Flag Downstream

Write strategy decisions into `{client-folder}/wiki/strategy.md` (update if exists from market-research).

Flag downstream connections:
- Campaign names + ad group structure → ready for campaign-setup skill
- Creative direction + messaging angles → ready for ad-copywriter skill
- Keyword clusters + match types → ready for campaign-setup skill (Google)
- Audience definitions → ready for campaign-setup skill (Meta)

Update wiki/log.md and wiki/index.md.

### Step 8: Validate & Evolve (Mandatory — Never Skip)

**Validate:** Run `scripts/validate_output.py {report} {dashboard} {csv}`. Fix CRITICAL failures before delivery. Validator checks: required sections, source labels, rationale density (16 patterns, min 10), copy button element count (DOM-only, excludes CSS), brand-config compliance (reads brand-config.json, flags generic defaults on non-monochromatic brands), light-section contrast (flags text lighter than #6b7280), Chart.js UMD build, placeholders, tooltips, collapsibles, **cross-file consistency** (campaign name/count match, budget total match within 15%, platform consistency between report and CSV). Run `scripts/run_evals.py output-check` to validate deliverables against eval assertions.

**Evolve:** Read `references/feedback-loop.md`. Capture learnings in the section below.

## Output Checklist

- [ ] Platform selection confirmed (Google, Meta, or Both)
- [ ] Wiki data consumed and referenced throughout
- [ ] All 8 strategy dimensions covered with rationale
- [ ] Decision logic explained (not just "use this" but "use this because...")
- [ ] Accuracy protocol applied ([EXTRACTED], [INFERRED], BLANK)
- [ ] Bidding strategy matched to conversion volume and business maturity
- [ ] Budget allocation adds up and is defensible
- [ ] Phased execution plan with clear milestones
- [ ] HTML dashboard uses Chart.js UMD build, brand colors, tooltips, collapsibles
- [ ] CSV media plan has campaign-level and monthly projections
- [ ] Copy buttons on actionable strategy elements in dashboard
- [ ] Wiki updated with strategy decisions
- [ ] Downstream skill connections flagged

## Learnings & Rules

<!--
Format: [DATE] [CLIENT TYPE] Finding → Action
Keep under 30 lines. Prune quarterly. See references/feedback-loop.md for protocol.
-->
- [2026-04-10] [SaaS App] Finding: App install strategy has a critical creative dependency — "starting from zero" means a 1-2 week pre-launch production sprint before any ads can run. The skill should flag creative readiness as a launch blocker, not just a recommendation. Action: Add a creative readiness gate in Step 2 — if creative = zero, mandate production timeline before campaign launch dates.
- [2026-04-10] [SaaS App] Finding: For subscription apps, Phase 1 unit economics will almost always be unprofitable. CAC per subscriber at scale CPI is too high without down-funnel optimization. The strategy needs to explicitly set expectations: Phase 1 = data collection, NOT ROI. Action: Add a "profitability reality check" subsection to budget allocation that calculates break-even scenarios upfront.
- [2026-04-10] [SaaS App] Finding: The 50-event learning phase rule creates a cascade problem for app subscription funnels. Install events easily hit 50/week, but trial_start and subscription_started may never hit that threshold at moderate budgets. Strategy needs to be explicit about which optimization events are realistically achievable at each budget level. Action: Add a "learning phase viability calculator" to Step 3 — budget ÷ estimated CPA = weekly events, then flag which events can realistically exit learning.
- [2026-04-10] [SaaS App] Finding: Validation script flagged insufficient "data-supported" / "directional" labels in the report. These get lost in long strategy documents. Action: Add data-supported/directional labels to all Phase success criteria and key recommendations, not just the strategic recommendations section.
- [2026-04-10] [SaaS App] Finding: Guided questions worked well for this client type (4 questions, all actionable). The "creative assets" question was the most strategy-impacting — it changed the entire launch timeline. The "growth priority" answer (volume) shaped bidding strategy across all campaigns. Action: For app install clients, always ask creative readiness and growth priority — these are the two highest-leverage questions.
- [2026-04-11] [General] Finding: No failure/fallback protocols existed — skills assumed every step succeeds. → Action: Added inline failure handling to steps with known failure modes (missing wiki, unanswerable intake questions).
- [2026-04-11] [General] Finding: evals.json existed with 3 test cases but no run_evals.py to execute them — evals were documentation-only. → Action: Created run_evals.py with output-check and structure-check modes for automated deliverable validation.
- [2026-04-11] [General] Finding: validate_output.py didn't check for unreplaced {{PLACEHOLDER}} text — dashboards could ship with literal placeholder syntax. Also lacked a broad Chart.js UMD build catch-all beyond the CDN-specific checks. → Action: Added CRITICAL check for unreplaced {{PLACEHOLDER}} placeholders and Chart.js UMD build verification in dashboard HTML validator.
- [2026-04-11] [General] Finding: paid-media-strategy was the only skill without HTML templates in assets/ — every dashboard was generated from scratch each session. → Action: Created template-single-platform.html and template-dual-platform.html with Chart.js, dark mode, collapsibles, tooltips, copy buttons, and placeholder syntax matching landing-page-audit quality.
- [2026-04-11] [General] Finding: Eval coverage had gaps — no wellness/retreat clients, no temple/cultural org, no dual-platform with limited budget. → Action: Added 2 new eval cases (IDs 4-5) covering seasonal wellness retreat (Meta-only) and temple dual-objective (Google + Meta) edge cases.
- [2026-04-12] [Product/Manufacturing] Finding: Zero Meta creative + sub-$3K budget = must phase platform launches, not run both simultaneously. Google-first is correct for search-heavy categories with proven keyword volume. Creative readiness gate (from SaaS learning) applied correctly — Meta delayed to Phase 2. → Action: When creative = zero AND budget < $3K, always default to single-platform Phase 1 with the intent-capture platform.
- [2026-04-12] [Product/Manufacturing] Finding: Monochromatic brand (black/white only) makes dashboard branding challenging. Validator flagged "no CSS custom properties for brand colors" — but using dark theme defaults IS correct for a monochromatic brand. → Action: For monochromatic brands, use dark theme defaults and derive accent tones from product photography or use cyan/green functional colors. Validator warning is acceptable.
- [2026-04-12] [Product/Manufacturing] Finding: Template dual-platform.html was NOT used as-is — the placeholder syntax didn't map cleanly to the strategy's phased structure (Phase 1 = Google only, Phase 2 = add Meta). Dashboard was generated from template structure but with significant modifications. → Action: Consider adding a "phased dual-platform" template variant for cases where platforms launch at different times.
- [2026-04-12] [General] Finding: Validator had no cross-file consistency checks — report and CSV could have mismatched campaign names, budgets, or platforms without any warning. For phased strategies, CSV lists all campaigns across phases so daily budget sums exceed any single phase's monthly total (expected behavior, correctly flagged as WARNING). → Action: Added validate_cross_file_consistency() checking 4 dimensions: campaign count match, campaign name match (fuzzy, handles substring containment), budget total match (15% tolerance, extracts from markdown tables), platform consistency. Runs automatically when both report and CSV are provided.
- [2026-04-12] [General] Finding: $210K unit price makes CPA math extremely forgiving — even $200 CPA is acceptable when 1 sale = $210K. High-ticket products should lead with "break-even threshold" framing rather than CPA optimization. Strategy's unit economics section is the most impactful part of the report for client confidence. → Action: For high-ticket products (>$50K), always include break-even math prominently in executive summary and budget section.
- [2026-04-12] [Product/Manufacturing] Finding: Dashboard was generated with generic dark-mode tech colors (blue/purple/cyan) instead of reading brand-config.json and matching the client's established design language from research dashboard. Client rejected it. Root cause: Step 5 didn't mandate brand-config reading or cross-dashboard consistency. → Action: Added mandatory brand-config gate to Step 5 — read brand-config.json first, check for existing dashboards, match design language. For monochromatic brands, derive accents from product photography. Updated dashboard-specs.md with brand-config priority rules.
- [2026-04-12] [General] Finding: validate_output.py had 4 issues: (1) copy button count inflated by CSS declarations — regex matched class names in style blocks, reported 17 when dashboard had 4 actual buttons. (2) Rationale detection only matched "because/rationale/reason" — missed "since", "given", "based on", "at this budget", "this means", causing false-positive low-rationale warnings. (3) No brand-config compliance check. (4) No light-section contrast check. → Action: Fixed copy-btn regex to match only element tags. Broadened rationale patterns to 16 phrases with min threshold 10. Added brand-config.json reader with monochromatic exemption (WARNING). Added light-contrast checker flagging text lighter than #6b7280.
- [2026-04-12] [General] Finding: Strategy report creative direction (Section 5) and wiki personas contain all data needed for a structured creative brief, but ad-copywriter skill had no machine-readable input — only prose. Manual translation from report to ad copy is error-prone and loses persona-specific hooks. → Action: Added Step 5.5 to generate a creative-brief.json with per-campaign persona mappings, hooks, formats, brand voice, and competitor angles. Schema defined in references/creative-brief-spec.md with [EXTRACTED]/[INFERRED] source labels per field.
- [2026-04-12] [General] Finding: Retreat House dashboard required heavy manual modifications to template-dual-platform.html because the simultaneous template has no concept of phased platform launches. → Action: Created template-dual-phased.html with phased split bars, phase-tagged campaigns, monthly budget progression, and platform-agnostic placeholders. Supports light/dark mode via body class.
- [2026-04-12] [General] Finding: Creative brief JSON lacked visual direction, landing page mapping, A/B testing plan, and proof element hierarchy. Brief was ~75% complete for ad-copywriter and ~50% for creative production. → Action: Added 4 new field groups to creative-brief-spec.md: visual_direction (with image_gen_prompt_prefix for AI image tools), landing_page (url + page_type + message match), ab_testing (priority variable + test pairs), proof_elements (media mentions, certifications, stats with campaign mapping). 5 new validation rules.
- [2026-04-16] [Validator hardening] Finding: two validator blind spots. (a) Step 5.5 produces `creative-brief.json` — the pipeline's spine contract — but the validator never checked that it existed or parsed. A paid-media-strategy session could "pass" with no brief at all, then silently break ad-copywriter, landing-page-builder, and campaign-setup 30 minutes later. (b) Cross-file campaign-name match used pure substring containment (`cn in rn or rn in cn`), so "Summer" wrongly matched "Summer Sale Campaign" — real drift could pass. → Action: (a) added `validate_creative_brief_presence()` step that globs for `*-creative-brief.json` in the deliverables folder, parses it, requires `business_name` + `campaigns[]`, and warns if no campaign has `visual_direction.image_gen_prompt_prefix`; (b) replaced substring match with `_is_structured_variant()` — accepts exact equality OR structured separator variants (`" — "`, `" – "`, `": "`, `" | "`, `" / "`) with a 60% minimum length-overlap guard. Eliminates false matches on short names inside longer ones.
