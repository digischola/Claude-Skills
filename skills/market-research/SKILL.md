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

If a client wiki exists (`{client-folder}/wiki/`), check it first — carry forward what's valid, focus on what's changed. Read `references/wiki-operations.md` for INGEST/QUERY/LINT operations.

## Process Overview

### Step 1: Client Intake, Wiki Init & Brand Extraction

**Structure detection:** Run `scripts/init_wiki.py {client-folder} --detect` to check client structure. Three outcomes:
- `NEW_CLIENT` → ask: single program or multi-program? Init accordingly.
- `SINGLE_PROGRAM` → check if user wants research on a *different program*. If yes, migrate with `--migrate` then `--program`. If same program, proceed normally.
- `MULTI_PROGRAM` → ask which program. If new program, run `--program "Name"`. If existing, load its wiki.

Read `references/multi-program-structure.md` for full folder layout and migration logic. For multi-program clients, brand-config lives in `_shared/deliverables/`, program research in `{Program}/wiki/`.

**Gather client info.** Flag what's missing: business URL, name, type, location, product/service, geographic focus, platform need (Google Ads, Meta Ads, or both), known competitor names.

**Determine platform focus:** Ask which platform(s) the client needs — Google Ads only, Meta Ads only, or both. This shapes the Perplexity prompt (sections 6, 7, 11) and the platform data step.

**Brand extraction:** Run `scripts/extract_brand.py {url}` (thin wrapper that imports from `business-analysis/scripts/extract_brand.py`). If script returns warnings, use WebFetch and manually extract. Save brand-config.json to the correct location (root `deliverables/` for single-program, `_shared/deliverables/` for multi-program).

### Step 2: Generate Perplexity Deep Research Prompt

**Offering selection (conditional):** Read `{client-folder}/wiki/offerings.md`. If the business has multiple offerings that serve **fundamentally different markets** (different buyer segments, different industries, different competitor sets), ask which offering to focus on. If offerings are pricing tiers/plans of the same product, skip — use the primary offering from offering prioritization and proceed. Rule of thumb: "Would the competitor list change?" If yes, ask. If no, proceed.

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

1. Run `scripts/process_keyword_planner_csv.py --generate-seeds --output {client-folder}/sources/` to generate 3 batches of 10 seed keywords tailored to client context.
2. Present seed batches to user. User opens Google Ads → Tools → Keyword Planner → "Get search volumes and forecasts", pastes each batch (10 keywords per batch), sets location to client's target market, downloads CSV.
3. User drops CSVs into `{client-folder}/sources/` (or provides paths).
4. Run `scripts/process_keyword_planner_csv.py {csv1} {csv2} {csv3} --output {client-folder}/sources/` to merge, deduplicate, auto-cluster, and generate unified JSON+CSV.
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

**Wiki INGEST:** Save raw Perplexity output to `sources/perplexity-{date}.md`. Save keyword CSVs to `sources/`. Write tagged findings into wiki pages. Update wiki/log.md and wiki/index.md. See `references/wiki-operations.md`.

**Meta Ad Library Audit (conditional):** If Chrome MCP is available and the competitor table in strategy.md has BLANK "Ads Active" columns, run the automated audit. Read `references/meta-ad-library-audit.md` for the full procedure. Use `scripts/parse_competitor_list.py` to extract competitor names. Navigate Meta Ad Library for each competitor via Chrome MCP, record ad activity, and update strategy.md. Skip if Chrome MCP is unavailable — leave as BLANK with reason.

### Step 5: Gap Analysis & Follow-up

Identify critical gaps, contradictions, and low-confidence areas. If gaps are significant for marketing decisions, generate 1-2 targeted follow-up Perplexity queries. Otherwise, proceed.

### Step 6: Generate Research Report (Markdown)

Read `references/report-structure.md`. Report covers all 11 dimensions with: source tags on every data point, BLANK fields with explanations, confidence ratings (HIGH/MEDIUM/LOW), marketing implications per section, and "data-supported" vs "directional" labels on recommendations.

Save as `{client-folder}/deliverables/{business-name}-market-research.md`.

### Step 7: Generate HTML Dashboard

Read `references/dashboard-specs.md` for the full specification. The dashboard must be presentation-quality (reference: CrownTech dashboard in deliverables/). Key requirements:

- **Chart.js** visualizations (bar, line, radar, doughnut)
- **Tooltips** on every KPI and stat explaining context and source
- **Collapsible sections** for detailed sub-content
- **12 sections:** Overview hero, Market Size, Porter's, PESTEL, SWOT grid, Competitors table, Keywords (dark section with data from CSVs), Benchmarks & Funnel, Buyer Personas, Channels, Blue Ocean, Strategy timeline + Glossary
- **Brand colors and fonts** from brand-config.json (never defaults)
- **Keyword data tables** populated from platform CSV data when available
- **Source indicators** (tooltips for INFERRED, "Data not available" for BLANK)

Save as `{client-folder}/deliverables/{business-name}-research-dashboard.html`.

### Step 8: Update Wiki & Flag Downstream Connections

Write strategic implications into `wiki/strategy.md`. Flag cross-skill connections: "Positioning gap X → ready for meta-ad-copywriter" or "Content gap Y → content calendar skill."

Update wiki/log.md, wiki/index.md, and wiki-config.json.

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
- [ ] Raw sources saved to sources/ (immutable)

## Learnings & Rules

<!--
Format: [DATE] [CLIENT TYPE] Finding → Action
Keep under 30 lines. Prune quarterly. See references/feedback-loop.md for protocol.
-->

- [2026-04] [B2B Services] Finding: Perplexity returns stronger competitor data when 2-3 known competitor names are seeded into the prompt. Action: During intake, always ask if user knows any competitor names.
- [2026-04] [B2B Services] Finding: Google Business Profile data often missing from Perplexity output — critical for local businesses. Action: Always flag GBP status as a gap if not in Perplexity data, recommend direct verification.
- [2026-04] [General] Finding: Brand color extraction from websites needs systematic approach, not manual eyeballing. Action: Use extract_brand.py script first, fall back to manual only if script fails.
- [2026-04] [B2B Services] Finding: Perplexity prompt with Porter's/PESTEL/SWOT frameworks produces significantly deeper analysis than just raw data dimensions. Action: Always include strategic frameworks in the prompt.
- [2026-04] [General] Finding: Dashboard quality gap between Chart.js + tooltips + collapsibles vs plain CSS cards is massive. Action: Always use Chart.js and interactive elements, never fall back to static cards.
- [2026-04] [General] Finding: Platform keyword data (Google Ads Keyword Planner CSVs) embedded in dashboard makes research immediately actionable for campaign setup. Action: Always collect and integrate keyword data.
- [2026-04] [SaaS App] Finding: Multi-offering businesses don't always need offering selection. Pricing tiers of the same product (Free/Pro/Enterprise) share the same market, competitors, and buyer personas. Offering selection only needed when offerings serve fundamentally different markets (different competitor sets). Rule: "Would the competitor list change?" If yes, ask. If no, proceed with primary offering. Action: Added conditional offering check to Step 2.
- [2026-04] [SaaS App] Finding: For Meta Ads-only research, section 6 (Search Demand) should be reframed as "Meta Ads Audience & Targeting" — interest categories, audience sizes, lookalike strategy, custom audiences, CPM benchmarks. Search keywords are irrelevant for Meta-only. Action: Perplexity prompt template should have Meta-specific section 6 variant.
- [2026-04] [SaaS App] Finding: Perplexity cannot access Meta Ads Library for live competitor creative data. This is always a gap for Meta-focused research. Action: Flag as known gap, recommend manual Ads Library search as a parallel step during research.
- [2026-04] [SaaS App] Finding: Unit economics math (CPI × conversion rate = CAC, LTV from retention × price) is the most actionable output for subscription app clients. Without it, budget recommendations are guesswork. Action: Always include detailed unit economics funnel calculations in sections 7 and 11.
- [2026-04] [General] Finding: Chart.js 4.x `chart.min.js` on cdnjs is ESM-only — does NOT register global `Chart` object. Causes "Chart is not defined" error. Action: Always use UMD build: `https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js`. Updated dashboard-specs.md.
- [2026-04-11] [General] Finding: No failure/fallback protocols existed — skills assumed every step succeeds. → Action: Added inline failure handling to steps with known failure modes (weak Perplexity output, missing keyword data).
- [2026-04-11] [General] Finding: extract_brand.py was duplicated across business-analysis (1225 lines) and market-research (478 lines) — bug fixes couldn't propagate. → Action: Replaced market-research version with thin wrapper importing from business-analysis canonical implementation.
- [2026-04-11] [General] Finding: lint_wiki.py rejected PENDING confidence from init_wiki.py — freshly initialized wikis always failed lint. → Action: Updated confidence regex to accept PENDING as valid (with WARNING). Added check_metadata_headers() to market-research linter (was missing entirely).
- [2026-04-11] [General] Finding: Meta-only Perplexity prompt used search keyword questions (Section 6/7) — irrelevant for Meta. → Action: Added complete Meta-only variant text for Section 6 (Audience & Targeting) and Section 7 (Benchmarks & Creative) to perplexity-prompt-template.md.
- [2026-04-11] [General] Finding: validate_output.py didn't check for unreplaced {{PLACEHOLDER}} text — dashboards could ship with literal placeholder syntax visible to clients. Also missing Chart.js UMD build verification in HTML validator. → Action: Added CRITICAL check for unreplaced {{PLACEHOLDER}} placeholders and Chart.js UMD build validation in HTML output.
- [2026-04-11] [General] Finding: Eval coverage had gaps — Channel Partners (dim 9) never tested, no weak-output scenario with missing dimensions. → Action: Added 2 new eval cases (IDs 5-6) covering weak Perplexity output with gaps and explicit Channel Partners dimension testing.
- [2026-04-11] [General] Finding: "Both platforms" Perplexity prompt had no actual replacement text — only a conceptual note. Google+Meta clients got Google-only questions for Section 6/7. → Action: Added Both Platforms variant with combined search + audience targeting (Section 6) and Google + Meta benchmarks with budget split rationale (Section 7).
- [2026-04-12] [Wellness/Shopify] Finding: validate_output.py flags "Search Demand & Keywords" as missing for Meta-only runs because Section 6 becomes "Meta Ads Audience & Targeting". Not an error — correct behavior for Meta-only. → Action: Validator should accept Meta section title as a valid Section 6 variant. Advisory only for now.
- [2026-04-12] [General] Finding: Perplexity cannot access Meta Ad Library — competitor "Ads Active" column always BLANK after research. Manual checking is tedious and error-prone. → Action: Created automated Meta Ad Library audit procedure using Chrome MCP (references/meta-ad-library-audit.md) and competitor name parser (scripts/parse_competitor_list.py). Integrated as conditional sub-step in Step 4.
- [2026-04-12] [Wellness/Shopify] Finding: lint_wiki.py expects per-dimension wiki pages (market.md, competitors.md, audience.md, benchmarks.md) but for single-source Perplexity ingest, consolidating all research into strategy.md is cleaner and avoids thin wiki pages with redundant content. → Learning: Consolidated strategy.md approach is valid when all data comes from one Perplexity session. Split into per-dimension pages only when multiple sources need independent tracking.
- [2026-04-12] [Wellness/Shopify] Finding: Perplexity output for AU wellness retreats was exceptionally strong — 117 sources, all 11 dimensions covered, no follow-up needed. Seeding 7 competitor names + specific GBP data from business-analysis wiki produced deep competitive section. → Learning: The more business-analysis data is seeded into the Perplexity prompt (competitors from GBP, offerings from wiki, pricing from Ad Library), the stronger the output. Pre-research pays compound returns.
- [2026-04-12] [Process] Finding: Launching report + dashboard agents in parallel while handling wiki updates in the main thread is optimal — total wall-clock time ~8 min vs ~16 min sequential. Both agents completed without conflicts. → Learning: Always parallelize report + dashboard generation. Wiki work goes in main thread.
- [2026-04-12] [Wellness/Shopify] Finding: Business-analysis wiki said "lead gen, not direct purchase" but booking.gwinganna.com supports direct online booking (DIRECT_BOOKING). Perplexity prompt lacked booking infrastructure context → entire funnel model assumed enquiry-first. → Action: Mandatory wiki context injection in Step 2 (booking model, conversion paths, pricing transparency, ad activity). Added {booking_model} to Perplexity prompt template.
- [2026-04-12] [Product/Manufacturing] Finding: Retreat House (tiny home builder, $210K) — "Both Platforms" Perplexity prompt variant produced excellent output (100+ sources, all 11 dimensions, no follow-up needed). Wiki context injection (ENQUIRY_ONLY + Pipedrive + pixel status) ensured correct funnel model. Product companies with single SKU don't need offering selection. → Learning: Wiki context injection is validated across both booking models (DIRECT_BOOKING and ENQUIRY_ONLY). Both-platforms variant works well for dual-channel clients.
- [2026-04-12] [Tooling] Finding: Step 3 relied entirely on Chrome tools or manual CSV export for Google keyword data — fragile and slow. → Action: Added `scripts/google_keyword_volume.py` (Google Ads API integration via KeywordPlanIdeaService) and `references/google-ads-api-setup.md` (one-time setup guide). Script supports batched queries, --exact-only filtering, --dry-run, JSON+CSV output. Step 3 updated with API as preferred Option A.
- [2026-04-12] [Product/Manufacturing] Finding: First live Meta Ad Library audit on Retreat House competitors — 9/10 checked successfully. Only Aussie Tiny Houses running active Meta ads (4+ active, image+text). 8 competitors have zero Meta presence. Confirms Meta is blue ocean for AU tiny homes. → Learning: Chrome MCP + JS extraction is faster than read_page for Ad Library (dynamic content, large DOM). Use `javascript_tool` with setTimeout for page load wait. Generic brand names (Tall Tiny, Base Cabin) return noisy keyword results — add industry qualifier or skip. Audit takes ~5 min for 10 competitors.
- [2026-04-12] [Tooling] Finding: Google Ads API developer token starts at "Test account" access level — only works with test accounts. Basic access requires separate application through MCC API Center (few business days). → Action: Updated google-ads-api-setup.md with access level documentation. Script works correctly but is blocked until Basic access approved. Keyword volume automation is not instant — account for multi-day setup lead time in client timelines.
- [2026-04-12] [Tooling] Finding: Google Ads API setup is too complex for standard workflow (MCC + developer token + OAuth + Basic access approval = multi-day). Chrome MCP blocks ads.google.com and all SEO tool domains. Computer-use gives read-only for browsers. No keyword MCP connectors exist. → Action: Created `scripts/process_keyword_planner_csv.py` — user exports CSVs from Keyword Planner UI (2 min per batch of 10 seeds), script merges/deduplicates/auto-clusters/generates JSON+CSV+markdown. Made CSV export the PRIMARY method in Step 3, API demoted to optional. Script also generates seed keyword batches (3×10) via `--generate-seeds` flag. Zero setup required — works with any Google Ads account.
- [2026-04-12] [Tooling] Finding: Google Keyword Planner exports as UTF-16 LE, tab-delimited, with 2 metadata rows before column headers (title row + date range row). Standard csv.DictReader chokes on NUL bytes. → Action: Added UTF-16 to encoding detection chain, tab delimiter auto-detection, and header row scanning (looks for row starting with "keyword" + containing "search" or "currency"). Script now handles actual Keyword Planner format. Tested on 3 real CSVs: 6,513 raw → 6,503 unique keywords.
- [2026-04-12] [Product/Manufacturing] Finding: When keyword data becomes available after dashboard was already built, dashboard must be updated — old placeholder table with "AU data not available" cells looks wrong next to real data. → Action: Always update dashboard keyword section when CSV data is processed. Add horizontal bar chart (Chart.js) showing volume by cluster. Update table with real volumes, CPCs, and opportunity badges. This is part of the CSV processing workflow, not a separate step.
- [2026-04-12] [Architecture] Finding: Multi-program clients need separate research per program but shared brand DNA. Single-folder structure breaks when running research for a different program — forces overwrite or ad-hoc subfolder hacks. → Action: Added multi-program support to init_wiki.py (4 modes: single-program, --shared, --program, --migrate + --detect). Created `references/multi-program-structure.md` (full folder layout, detection logic, migration path, wiki-config schemas, cross-program intelligence rules). Step 1 updated with structure detection. Decision test: "Would the competitor list change?" — if yes, multi-program; if no, single-program with segment filters.
- [2026-04-16] [Meta-only / Validator] Finding: `scripts/validate_output.py` dimension-6 regex only accepted "Search Demand & Keywords" style headings (`[Kk]eyword|[Ss]earch\s+[Dd]emand`). Meta-only reports correctly use the variant heading "Meta Ads Audience & Targeting" and "Both platforms" reports use "Search Demand & Audience Targeting (Google + Meta)" — both would have been falsely flagged as missing dimension 6. Risk affects all Meta-only active clients (Thrive, Happy Buddha, ISKM). → Action: Expanded regex to `[Kk]eyword|[Ss]earch\s+[Dd]emand|[Aa]udience\s*(?:&|and)\s*[Tt]argeting|[Aa]udience\s+[Tt]argeting` and renamed dimension label in validator to "Search Demand / Audience & Targeting" to cover all three platform variants. Smoke-tested against all 3 variants + negative case.
- [2026-04-16] [Knowledge promotion] Finding: The "keyword CSV arrives after dashboard was already generated" workflow was documented in Learnings (2026-04-12, Retreat House case) but never surfaced in Step 3 — so any future session following SKILL.md alone would leave stale "data not available" cells next to real data. Also merged the "Why this over API" explanation into the API-option bullet to reclaim a line. → Action: Added explicit "If keyword CSV arrives after Step 7" guidance to Step 3; tightened the API-complexity rationale inline. Skill Auto-Update Rule catch-up — promote workflow rules out of Learnings and into the step that owns them.
