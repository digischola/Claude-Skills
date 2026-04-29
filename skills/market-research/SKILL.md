---
name: market-research
description: "Comprehensive pre-marketing business and market research skill. Generates a Perplexity deep research mega-prompt covering 11 dimensions (market size, Porter's, PESTEL, SWOT, competitors, keywords, benchmarks, buyer personas, referral ecosystem, blue ocean, strategy), collects platform keyword data (Google Ads Keyword Planner and/or Meta Ads via Chrome tools or CSV import), analyzes with strict accuracy protocol, and produces a markdown report plus a premium HTML dashboard with Chart.js visualizations, tooltips, collapsibles, and client branding. Use when user mentions: new client research, business analysis, market research, competitor analysis, audience research, client onboarding, pre-campaign research, market sizing, industry benchmarks, competitive landscape, or provides a business URL to understand before running ads. Also trigger for existing clients launching new products. Do NOT trigger for ad copy writing, campaign creation, content calendars, or performance reporting."
---

# Market Research & Business Analysis

Strategy-grade market research for any business before a single marketing dollar is spent. Covers 11 dimensions, applies strict accuracy protocol, and produces client-ready deliverables.

## Context Loading

Read these shared context files before starting:
- `shared-context/analyst-profile.md` — workflow, client types, quality standards
- `shared-context/accuracy-protocol.md` — 3 accuracy rules for all data handling
- `shared-context/output-structure.md` — write final HTML/MP4/PDF and upload-ready CSV bundles to the folder root, intermediate MD/JSON/CSV to `_engine/working/`
- `shared-context/client-shareability.md` — client-facing files must read like first copies; no correction trails / audit history / internal-process commentary. Validator: `python3 ~/.claude/scripts/check_client_shareability.py {client}`

If a client wiki exists (`{client-folder}/_engine/wiki/`), check it first — carry forward what's valid, focus on what's changed. Read `references/wiki-operations.md` for INGEST/QUERY/LINT operations.

## Process Overview

### Step 1: Client Intake, Wiki Init & Brand Extraction

**Structure detection:** Run `scripts/init_wiki.py {client-folder} --detect` to check client structure. Three outcomes:
- `NEW_CLIENT` → ask: single program or multi-program? Init accordingly.
- `SINGLE_PROGRAM` → check if user wants research on a *different program*. If yes, migrate with `--migrate` then `--program`. If same program, proceed normally.
- `MULTI_PROGRAM` → ask which program. If new program, run `--program "Name"`. If existing, load its wiki.

Read `references/multi-program-structure.md` for full folder layout and migration logic. For multi-program clients, brand-config lives in the client root's `_engine/` (`{client}/_engine/brand-config.json`), program research in `{Program}/_engine/wiki/`.

**Gather client info.** Flag what's missing: business URL, name, type, location, product/service, geographic focus, platform need (Google Ads, Meta Ads, or both), known competitor names.

**Determine platform focus:** Ask which platform(s) the client needs — Google Ads only, Meta Ads only, or both. This shapes the Perplexity prompt (sections 6, 7, 11) and the platform data step.

**Brand extraction:** Run `scripts/extract_brand.py {url}` (thin wrapper that imports from `business-analysis/scripts/extract_brand.py`). If script returns warnings, use WebFetch and manually extract. Save brand-config.json to the correct location: `{client}/{program}/_engine/brand-config.json` for single-program, `{client}/_engine/brand-config.json` (at the client root) for multi-program.

**GBP review-count gate (local-business primary-source verification — MANDATORY for local sectors):** When the client is a local business (single-location yoga / fitness / spa / salon / restaurant / retail / clinic / studio), Perplexity output MUST be cross-checked against an actual GBP screenshot before any review-count claim ≥ 200 is treated as load-bearing. Read `references/local-business-verification.md` for the full protocol. Specifically: GBP routinely surfaces a "Reviews from the web" panel listing third-party platform counts (MindBody, ClassPass, Booking.com, TripAdvisor) that text-only extraction conflates with actual Google reviews. Verification options: (a) ask user for GBP screenshot, (b) Chrome MCP visit, (c) tag as `[EXTRACTED — UNVERIFIED, requires GBP screenshot]` until verified. The `_engine/wiki/digital-presence.md` MUST include a "GBP Verification Log" section with date, method, separate Google vs third-party counts.

### Step 2: Generate Perplexity Deep Research Prompt

**Run-mode branch (decide first, never skip Step 2 silently):**

- **FRESH mode** — no prior `_engine/sources/perplexity-*.md` exists, OR the existing research is older than 6 months, OR confidence is MEDIUM/LOW on >3 dimensions. Generate the full 11-dimension mega-prompt per the rest of this step.
- **UPDATE mode** — prior HIGH-confidence Perplexity research exists AND an upstream skill (typically business-analysis) corrected a load-bearing fact (offerings catalogue, booking model, GBP review count, pricing tier) that invalidates a subset of the prior dimensions. Generate a **targeted follow-up prompt** covering ONLY the dimensions touched by the correction. **Overwrite `_engine/sources/perplexity-prompt.md` in place** with the current iteration's prompt — do NOT keep the previous prompt content, do NOT create a new dated file, do NOT append a dated section. One file per role, current state only. The previous prompt is gone; the wiki is the persistent state. Same rule for the response file: save to `_engine/sources/perplexity-response.md`, overwriting any prior response. Mark inside the new prompt which dimensions are out of scope (already HIGH confidence, do not re-research). Re-ingest the response into only the affected `_engine/wiki/strategy.md` sections.
- **NO-NEW-RESEARCH mode** — only valid when the upstream correction touches no Perplexity-sourced fact (e.g., a typo fix, a brand-config color swap, a non-research metadata change). Document explicitly in `_engine/wiki/log.md` as "no Perplexity follow-up generated because [reason]". This is the only branch where Step 2 produces no prompt artefact, and it must be logged.

Never skip Step 2 by judgment. The mode decision is the step.

**Offering selection (conditional):** Read `{client-folder}/_engine/wiki/offerings.md`. If the business has multiple offerings that serve **fundamentally different markets** (different buyer segments, different industries, different competitor sets), ask which offering to focus on. If offerings are pricing tiers/plans of the same product, skip — use the primary offering from offering prioritization and proceed. Rule of thumb: "Would the competitor list change?" If yes, ask. If no, proceed.

**Mandatory wiki context injection:** Before generating the prompt, extract these data points from the business-analysis wiki and inject them into the prompt's business description:
- **Booking model:** DIRECT_BOOKING / ENQUIRY_ONLY / HYBRID / UNKNOWN (from offerings.md or business.md). If BLANK, state this explicitly so Perplexity researches both funnel types.
- **Booking infrastructure:** booking URL, payment capability, booking platform identity
- **Conversion paths:** all known paths (booking system, phone, email, chat, gift cards)
- **Pricing transparency:** whether prices are publicly visible or inquiry-only
- **Existing ad activity:** current ads running, pixel status, audience sizes

These shape Sections 7 (funnel benchmarks), 8 (buyer journey), and 11 (strategic recommendations). Omitting them produces a generic funnel model that may be wrong for this specific business.

Read `references/perplexity-prompt-template.md` for the mega-prompt framework. Read `references/research-dimensions.md` for all 11 dimensions:

1. Market Size & Demand — TAM/SAM/SOM, growth, headwinds
2. Porter's Five Forces — competitive structure
3. PESTEL Analysis — external macro forces
4. SWOT Analysis — strategic positioning
5. Competitive Landscape — top 10-15 competitors, ad presence, positioning
6. Search Demand & Keywords — keyword clusters, volumes, CPCs
7. Platform Benchmarks & Unit Economics — CPC, CTR, CPL, CPA, ROAS, full funnel
8. Buyer Personas & Purchase Journey — decision makers, triggers, objections
9. Channel Partners & Referral Ecosystem — who refers work
10. Blue Ocean Opportunities — underserved markets, service gaps
11. Strategic Recommendations — campaign structure, budget, phased plan

Generate ONE comprehensive Perplexity prompt customized to this business and platform focus. Use the correct Section 6 & 7 variant from `perplexity-prompt-template.md` based on platform:
- **Google only** → standard sections (search keywords, CPC benchmarks)
- **Meta only** → Meta variant (audience targeting, CPM/creative benchmarks)
- **Both platforms** → Both variant (combined search + audience, Google + Meta benchmarks side by side, budget split rationale)

Adjust scope by business type. Seed known competitor names. Include research quality rules at the end (source citing, geographic specificity, data-supported vs directional labels).

Present the prompt to the user. They run it in Perplexity and paste the output back.

**If Perplexity output is weak** (fewer than 8 of 11 dimensions have substantive data): generate 1-2 targeted follow-up queries for the weakest dimensions. Maximum 2 follow-up rounds, then proceed with gaps marked BLANK.

### Step 3: Collect Platform Keyword Data

**Google keyword data — Keyword Planner CSV export (primary method):**

1. Run `scripts/process_keyword_planner_csv.py --generate-seeds --output {client-folder}/_engine/sources/` to generate 3 batches of 10 seed keywords tailored to client context.
2. Present seed batches to user. User opens Google Ads → Tools → Keyword Planner → "Get search volumes and forecasts", pastes each batch (10 keywords per batch), sets location to client's target market, downloads CSV.
3. User drops CSVs into `{client-folder}/_engine/sources/` (or provides paths).
4. Run `scripts/process_keyword_planner_csv.py {csv1} {csv2} {csv3} --output {client-folder}/_engine/sources/` to merge, deduplicate, auto-cluster, and generate unified JSON+CSV.
5. Script outputs: cluster breakdown, top 20 by volume, markdown table for strategy.md, JSON for dashboard.

**Google Ads API (optional, if credentials exist):** Run `scripts/google_keyword_volume.py` if user has completed `references/google-ads-api-setup.md` setup with Basic access token. Faster for repeat runs but requires MCC + developer token + Basic access approval (multi-day OAuth setup) — hence CSV export is primary.

**Meta Ads data:** Audience size estimates, interest targeting data, CPM benchmarks. Reference `references/meta-interest-database.csv` for 329 pre-pulled interests with global audience sizes across 27 categories. Use as starting point, then refine in Ads Manager with location targeting.

**If user has no Google Ads access at all:** Proceed without. Mark dimensions 6 and 7 as BLANK. Use Perplexity benchmarks as directional only.
**If keyword CSV arrives after Step 7 dashboard was already generated:** re-run Step 7 to refresh the keywords section (real volumes/CPCs, horizontal bar chart by cluster) — don't leave placeholder "data not available" cells next to real data.

This step can happen in parallel with Step 2 (while waiting for Perplexity output).

### Step 4: Analyze Perplexity Output + Platform Data (Accuracy Protocol)

Apply accuracy protocol from `shared-context/accuracy-protocol.md`:
- **Rule 1:** Blank when uncertain — leave field BLANK with one-sentence reason
- **Rule 2:** 3x penalty — wrong data is 3x worse than a blank
- **Rule 3:** Source label everything — [EXTRACTED] (cited source) or [INFERRED] (synthesis with evidence)

Parse Perplexity output against all 11 dimensions. Three passes: absorb → tag every data point → identify gaps and mark BLANK. Integrate platform keyword data into dimensions 6 and 7.

**Wiki INGEST:** Save raw Perplexity output to `_engine/sources/perplexity-response.md` (overwrites prior response — one file per role per the universal Same-Client Re-Run Rule in CLAUDE.md). Save keyword CSVs to `_engine/sources/`. Write tagged findings into wiki pages. Update `_engine/wiki/log.md` and `_engine/wiki/index.md`. See `references/wiki-operations.md`.

**Meta Ad Library Audit (conditional):** If Chrome MCP is available and the competitor table in strategy.md has BLANK "Ads Active" columns, run the automated audit. Read `references/meta-ad-library-audit.md` for the full procedure. Use `scripts/parse_competitor_list.py` to extract competitor names. Navigate Meta Ad Library for each competitor via Chrome MCP, record ad activity, and update strategy.md. Skip if Chrome MCP is unavailable — leave as BLANK with reason.

### Step 5: Gap Analysis & Follow-up

Identify critical gaps, contradictions, and low-confidence areas. If gaps are significant for marketing decisions, generate 1-2 targeted follow-up Perplexity queries. Otherwise, proceed.

### Step 6: Generate Research Report (Markdown)

Read `references/report-structure.md`. Report covers all 11 dimensions with: source tags on every data point, BLANK fields with explanations, confidence ratings (HIGH/MEDIUM/LOW), marketing implications per section, and "data-supported" vs "directional" labels on recommendations.

Save as `{client-folder}/_engine/working/market-research.md`.

### Step 7: Generate HTML Dashboard

Read `references/dashboard-specs.md` for the full specification. The dashboard must be presentation-quality (reference: CrownTech dashboard in the client folder root). Key requirements:

- **Chart.js** visualizations (bar, line, radar, doughnut)
- **Tooltips** on every KPI and stat explaining context and source
- **Collapsible sections** for detailed sub-content
- **12 sections:** Overview hero, Market Size, Porter's, PESTEL, SWOT grid, Competitors table, Keywords (dark section with data from CSVs), Benchmarks & Funnel, Buyer Personas, Channels, Blue Ocean, Strategy timeline + Glossary
- **Brand colors and fonts** from brand-config.json (never defaults)
- **Keyword data tables** populated from platform CSV data when available
- **Source indicators** (tooltips for INFERRED, "Data not available" for BLANK)

Save as `{client-folder}/research-dashboard.html` (folder root — HTML is a presentable).

### Step 8: Update Wiki & Flag Downstream Connections

Write strategic implications into `_engine/wiki/strategy.md`. Flag cross-skill connections: "Positioning gap X → ready for meta-ad-copywriter" or "Content gap Y → content calendar skill."

Update `_engine/wiki/log.md`, `_engine/wiki/index.md`, and `_engine/wiki-config.json`.

### Step 9: Validate & Evolve (Mandatory — Never Skip)

**Validate:** Run `scripts/validate_output.py {report} {dashboard}`. Fix CRITICAL failures before delivery. Run `scripts/run_evals.py output-check {eval_id} {report} {dashboard}` if applicable. Run `scripts/lint_wiki.py {client_folder}` to check wiki health (orphan sources, stale pages, persistent gaps).

**Evolve:** Read `references/feedback-loop.md`. Capture what worked/didn't. Add learnings below (30 lines max). If a prompt modification improved results, update `references/perplexity-prompt-template.md`.

## Output Checklist

- [ ] Every data point has [EXTRACTED] or [INFERRED] label
- [ ] Missing data shows BLANK with explanation, not guesses
- [ ] All 11 research dimensions covered
- [ ] Markdown report has confidence ratings and marketing implications per section
- [ ] Recommendations labeled "data-supported" or "directional"
- [ ] HTML dashboard uses Chart.js charts, tooltips, collapsibles (not just cards)
- [ ] Dashboard uses client's actual brand colors/fonts (not defaults)
- [ ] Platform keyword data integrated into dashboard (sections 6 & 7)
- [ ] Competitive analysis covers ad strategies, not just existence
- [ ] Buyer personas include purchase journey and objection handling
- [ ] Porter's, PESTEL, SWOT frameworks present with visualizations
- [ ] Brand config JSON saved for downstream skill reuse
- [ ] Strategic implications flag connections to other skills
- [ ] Client wiki initialized or updated (all pages + index + log)
- [ ] Raw sources saved to `_engine/sources/` (immutable)

## Learnings & Rules
<!-- Format: [DATE] [CLIENT TYPE] Finding → Action. Keep under 30 lines. Prune quarterly. See references/feedback-loop.md for protocol.
Pre-2026-04-12 entries pruned 2026-04-26: encoded into perplexity-prompt-template.md, research-dimensions.md, dashboard-specs.md, extract_brand.py, lint_wiki.py, process_keyword_planner_csv.py, multi-program-structure.md, meta-ad-library-audit.md, validate_output.py {{PLACEHOLDER}} + Chart.js UMD checks, Step 2 wiki-context-injection, evals 5-6. -->

- [2026-04-12] [Booking-model context] Wiki-context injection mandatory in Step 2 — booking_model (DIRECT_BOOKING / ENQUIRY_ONLY / HYBRID), conversion paths, pricing transparency, ad activity. Without it Perplexity assumes generic enquiry-first funnel. Encoded in Step 2.
- [2026-04-16] [Validator] Dimension-6 regex now accepts all three platform variants: "Search Demand & Keywords" (Google), "Meta Ads Audience & Targeting" (Meta), "Search Demand & Audience Targeting (Google + Meta)" (Both). Risk affected all Meta-only clients.
- [2026-04-17] [Religious / regulated sectors] Country-specific regulatory history is a blind spot. For religious/NGO/legally-regulated, explicitly ask "historical regulatory events relevant to this sector in this country" in the Perplexity prompt. (ISKM Singapore: ISKCON was banned in 1970s — load-bearing strategic risk Perplexity surfaced unprompted.)
- [2026-04-17] [Budget-constrained Tier-1 Meta] Section 7 must include "is goal mathematically achievable from paid alone?" check. If no, Section 11 must name the non-paid lever (organic / WhatsApp / partner) that closes the gap. (ISKM SGD 350 / 13 days reframed as paid-retargeting + organic-mobilization.)
- [2026-04-25] [Multi-program extension] Pattern works for "same product, different geographies/competitor sets" (Living Flow: local studio + AU-wide live-stream) — not just "different events" (ISKM). The "Would the competitor list change?" test correctly flags this.
- [2026-04-25] [DO-NOT-LAUNCH verdict pattern] When research produces campaign-halt math, structure deliverable to LEAD with verdict (executive summary + hero banner + strategy callout). Don't bury. Side-by-side current-vs-fixed unit-economics tables make the structural blocker concrete. (Live-stream AU-wide: $250 vs $41.67 CPA.)
- [2026-04-25] [Hypothesis-disproof workflow] Keyword data can DISPROVE Perplexity blue-ocean hypotheses. (Men's Broga: Perplexity flagged 300% participation growth → keyword check showed 20/mo search volume → DISPROVEN.) Always pressure-test persona-level blue-ocean claims against Keyword Planner before recommending paid spend. Update reports with "DISPROVEN by keyword data" callouts.
- [2026-04-25] [Strategic-pivot finding] When adjacent product line has 5×+ keyword volume of the campaign's nominal target, surface as Phase 3+ pivot candidate. (Living Flow retreat queries 15,250/mo vs online-yoga 2,410/mo = 6.3× gap.)
- [2026-04-25] [Tooling — process_keyword_planner_csv.py] Auto-cluster patterns are sector-specific (current set tuned to tiny-house). Action candidate: `--sector wellness|local|saas|product` flag loading from `references/keyword-clusters/`. Until patched: manually re-cluster on non-tiny-house runs.
- [2026-04-25] [Tooling — lint_wiki.py] Orphan-source check doesn't decode URL-encoded `%20` in markdown links → false-positive WARNINGs on filenames with spaces. Action candidate: `urllib.unquote()` markdown-link targets before substring match. Until patched: rename source files with hyphens.
- [2026-04-26] [CRITICAL — Perplexity GBP hallucination] **Perplexity reported "1,235 Google reviews" for Living Flow; actual Google review count was 67.** The 1,235 was MindBody votes surfaced in GBP "Reviews from the web" panel — Perplexity conflated the two. Error propagated through 2 reports + 2 dashboards + 2 strategy.md + LP draft until user caught via GBP screenshot. → **Patched 2026-04-26:** Added `gbp_review_count_verification` check to validate_output.py (flags any "N Google reviews" claim ≥200 without `[VERIFIED]/[GBP]/[EXTRACTED — GBP]` tag within 100 chars). Added `references/local-business-verification.md` with full protocol + third-party-conflation traps (MindBody / ClassPass / Booking.com / TripAdvisor / Yelp / Facebook). Step 1 mandates GBP screenshot or Chrome MCP visit for local-business sectors before treating review counts as load-bearing. Eval #7 covers full flow. **RULE:** For local-business research, GBP review count = mandatory primary-source verification, never accepted from Perplexity alone.
- [2026-04-27] [Validator regex] [Living Flow re-run] `validate_output.py` source_labels_present check used strict `re.findall(r'\[EXTRACTED\]', content)` and `r'\[INFERRED\]'` — only counted bare-bracket labels, missed citation-suffixed variants (`[EXTRACTED — Source [42]]`, `[EXTRACTED from business.md]`, `[INFERRED — reasoning]`) which are MORE rigorous than bare brackets. Live-stream report had 44 actual labels but validator counted 4 → CRITICAL false-positive. → **Patched 2026-04-27:** Pattern now `r'\[EXTRACTED(?:[\s—:\-][^\]]*)?\]'` and `r'\[INFERRED(?:[\s—:\-][^\]]*)?\]'`. Accepts bare brackets AND any citation/source suffix between space/dash/colon and closing bracket. Re-validate after patch: Live-stream 25/26 passed (0 CRITICAL). **RULE:** Validator regexes for source labels must accept the citation-suffix form, not just the bare bracket — the citation form is the gold standard.
- [2026-04-27] [Update-mode] [Living Flow Live-stream verdict flip] Re-running market-research on a client where business-analysis later corrected an offerings catalogue → the prior verdict can flip without any new Perplexity output. The Live-stream DO-NOT-LAUNCH verdict (2026-04-25) rested on "no $39-49/mo digital SKU exists" — provably wrong once business-analysis enumerated the public pricing page (the $39 Midday Recharge Pass is a standalone monthly digital-eligible SKU). Step 1 says "carry forward what's valid, focus on what's changed" — this run did exactly that: reframed §4 SWOT (weaknesses → Phase 2 lift candidates), §7 unit economics (current/fixed → Phase 1/Phase 2 stages), §11 strategic recommendations (4 prerequisites → 1 enabler + 3 lifts), §Marketing Implications, §Downstream Connections. Both report and strategy.md updated in place — no v1/v2 bloat. lint_wiki.py + check_client_shareability.py both clean post-update. **RULE:** When upstream business-analysis changes a load-bearing fact (offerings, booking model, GBP counts), market-research re-runs as a targeted reconcile of dependent sections, not a full re-research. The skill's existing "carry forward what's valid" guidance handles this — but the dependent sections must be enumerated explicitly so nothing is missed (executive summary, SWOT, unit economics, strategic recommendations, marketing implications, downstream connections).
- [2026-04-27] [CRITICAL — Skill Protocol Supremacy violation] **Same Living Flow re-run, Step 2 was silently skipped by judgment.** Reasoning at the time: "prior Perplexity research is HIGH confidence, the only change is offerings reconcile, no new Perplexity prompt is needed." That's exactly the failure mode CLAUDE.md's Skill Protocol Supremacy section bans — "Skipping a mandatory step because it felt harder than expected" / "Inventing missing protocols ad-hoc instead of adding them to the skill". User caught it: "noticed we did not generate perplexity research prompt why is that?" → "patch the skill rerun the skill and do not ever do that when i say run the skill i mean let the skill run don't add your assumptions". → **Patched 2026-04-27:** Step 2 now opens with an explicit run-mode branch (FRESH / UPDATE / NO-NEW-RESEARCH). UPDATE mode generates a targeted follow-up prompt covering only dimensions touched by the upstream correction. NO-NEW-RESEARCH mode is the only branch where Step 2 produces no prompt artefact and it must be logged in `_engine/wiki/log.md` with the reason. Local Studio re-run logged NO-NEW-RESEARCH explicitly. **RULE:** Step 2's run-mode decision IS the step. The right question is never "should I skip Step 2?" — it is "which of the three branches applies?" If the answer is NO-NEW-RESEARCH, log the reason. Never silently skip.
- [2026-04-27] [Same-client re-run rule — overwrite, don't accumulate] [Living Flow Live-stream] Two-step user correction landed today. First iteration of the patch instructed saving follow-up prompt to a NEW file `_engine/sources/perplexity-followup-{date}.md`. User caught it: "i noticed you created new files when i specifically asked to not bloat up". I then patched to "append in place under a dated section header" — also wrong. User clarified: "when we are doing re run for same client same case why do you need to create separate date wise thing just update existing files remove the previous entries". Final patched rule: for same-client/same-case re-runs, **overwrite the existing `_engine/sources/` file in place — no dated sections, no -{date} filenames, no parallel files**. One file per role, current state only. The previous prompt content is gone; the wiki is the persistent state. → **Patched 2026-04-27:** Step 2 UPDATE-mode now reads "Overwrite `_engine/sources/perplexity-prompt.md` in place with the current iteration's prompt — do NOT keep the previous prompt content, do NOT create a new dated file, do NOT append a dated section." Same rule for response file: `_engine/sources/perplexity-response.md` (no date suffix), overwrites prior response. Live-stream + Local Studio response files renamed from `perplexity-2026-04-25.md` → `perplexity-response.md`; all 8 wiki/working/source references updated via batch script. **RULE:** Same-client re-run = overwrite in place, no version artefacts. Dated audit history lives in `_engine/wiki/log.md` (which is by-design append-only as a change log) — not in `_engine/sources/` filenames or content sections. The wiki absorbs the analysis; `_engine/sources/` is just the latest input scratch.
- [2026-04-27] [Universal — applies to all skills] Same-Client Re-Run Rule landed in CLAUDE.md as a universal Always-Active section. Same-client/same-case re-runs overwrite outputs in place — no v1/v2/v3, no -DATE parallel filenames, no dated section headers preserving prior content. One file per role, current state only. Only `_engine/wiki/log.md` (by-design change log) and `_engine/wiki/briefs.md` (brief history with `[ACTIVE]`/`[SUPERSEDED]` markers) are append-only. **For this skill specifically:** `_engine/sources/perplexity-prompt.md`, `_engine/sources/perplexity-response.md`, `_engine/working/CLIENT-market-research.md`, `CLIENT-research-dashboard.html` (folder root), `_engine/wiki/strategy.md` — all overwritten in place on re-run (Step 2 already encodes this; Wiki INGEST step also patched today). **RULE:** if you find yourself about to create a new file for an output that has the same logical role as an existing one, stop and overwrite the existing file instead.
- [2026-04-27] [Self-brand · DigiSchola productized-audit India] Two patterns to carry forward. (1) When the audit subject is itself a marketing-services brand selling the audited capability, research surfaces a credibility paradox that doubles as creative material — DigiSchola sells "tracking from day one" but its own site has zero pixels. The Phase 0 fix is also the strongest LinkedIn-content moment ("I just installed the pixel after auditing my own site"). (2) For productized SKUs at micro-budget (₹500/day = ₹3,500/week), Meta Purchase-event learning-phase exit requires ~₹75K/week — about 21× available spend. Phase 1 must therefore optimize for upper-funnel proxy events (Initiate Checkout / LP View) until 30-40 audits log via combined paid+organic+referral, then transition to Purchase. **RULE:** for productized digital SKUs at <₹1K/day, hard-code a Phase 1 upper-funnel-proxy event recommendation and a Phase 2 Purchase-transition trigger condition into Section 11 of the Perplexity prompt. The default "optimize for Purchase from day 1" is provably wrong at this budget tier — call it out explicitly in the prompt so Perplexity doesn't drift into the generic recommendation.
- [2026-04-27] [Validator regex] [DigiSchola self-brand] Markdown validator's `executive_summary_present` check requires literal "Executive Summary" header — variants like "Executive Verdict" / "Executive Decision" do NOT match. Also `blank_fields_documented` warns on 0 BLANK occurrences — analyst can have a "Gaps & Unknowns" section but if it doesn't use the literal token "BLANK", validator counts it as zero gaps. Both warnings are advisory, but if treated as binding they push analysts to specific keywords. **RULE:** Use literal "Executive Summary" as section header (verdict-style framing belongs in the section body, not the header). When listing gaps, mark each with literal "BLANK — reason" so the validator can count them. Don't fight the validator on token shape — it's cheaper to conform than to widen the regex.
- [2026-04-29] [STRUCTURAL REFACTOR] Folder convention changed: all skill internals (wiki, sources, working, configs) now live in `_engine/` subfolder; presentables (HTML/PDF/CSV/MP4) at folder root. → Updated all path references in SKILL.md, references/, scripts/, evals/.
- [2026-04-29] [STRUCTURAL REFACTOR — filename simplification] Output filename templates dropped redundant client/business-name prefix. Filename = deliverable type only (`research-dashboard.html`, `market-research.md`) since folder location already encodes client + program. Validators accept legacy `{client}-`prefixed names as backwards-compat fallback. → Updated SKILL.md, references/wiki-schema.md, references/multi-program-structure.md.
