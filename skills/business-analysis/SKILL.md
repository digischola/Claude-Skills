---
name: business-analysis
description: "Comprehensive business DNA extraction and client onboarding skill. Crawls the client website, extracts brand identity, documents all offerings/products/services with per-offering detail, audits digital presence, and initializes the client wiki that all downstream skills consume. Use when user mentions: new client, client onboarding, business analysis, understand the business, analyze this business, extract brand, document offerings, business DNA, client setup, website analysis, or provides a business URL for the first time. Also trigger for existing clients adding new offerings or products. Do NOT trigger for market research, competitor analysis, ad copy writing, campaign creation, or performance reporting."
---

# Business Analysis & Client Onboarding

Extract the complete DNA of any business before marketing work begins. Creates the client wiki that every downstream skill reads from.

## Context Loading

Read these shared context files before starting:
- `shared-context/analyst-profile.md` — workflow, client types, quality standards
- `shared-context/accuracy-protocol.md` — 3 accuracy rules for all data handling
- `shared-context/output-structure.md` — write final HTML/MP4/PDF and upload-ready CSV bundles to `outputs/`, intermediate MD/JSON/CSV to `working/`
- `shared-context/client-shareability.md` — client-facing files must read like first copies; no correction trails / audit history / internal-process commentary. Validator: `python3 ~/.claude/scripts/check_client_shareability.py {client}`

If a client wiki already exists (`{client-folder}/wiki/`), read it first. This may be an update, not a fresh onboard.

## Process Overview

### Step 1: Client Folder & Wiki Init

**Structure detection:** Check if `Desktop/{Client Name}/` exists. If yes, run `market-research/scripts/init_wiki.py {path} --detect` to determine structure type (NEW_CLIENT, SINGLE_PROGRAM, MULTI_PROGRAM).

**Create folder:** For new clients, create `Desktop/{Client Name}/{Business Name}/` with sources/, wiki/, deliverables/. For multi-program clients, business-analysis outputs to `_shared/` (brand DNA is shared across all programs).

**Init wiki:** Run `market-research/scripts/init_wiki.py` with appropriate mode:
- New single-program: `init_wiki.py {client_folder} {business_name} {project_name}`
- New multi-program: `init_wiki.py {client_folder} {business_name} --shared` then `--program "Name"`
- Existing client, new program: `init_wiki.py {client_folder} {business_name} --program "Name"` (if already multi-program) or `--migrate "Name"` (to convert single→multi)

Creates base pages (business.md, brand-identity.md, digital-presence.md, offerings.md) + index.md + log.md + wiki-config.json. If wiki exists, skip init. Read `market-research/references/multi-program-structure.md` for full multi-program folder layout.

### Step 2: Website Crawl & Extraction

Take the business URL. Run `scripts/crawl_site.py {url}` to get structured page inventory.

**If crawl fails** (network error, JS-only site): follow the fallback chain in `references/extraction-fallbacks.md` (WebFetch → Chrome MCP → computer-use → manual). Elementor/React sites need Chrome MCP for rendered DOM.

**Always WebFetch the homepage** after crawl — crawl_site.py only captures headings/meta/schema, not body content. WebFetch reveals CTAs, booking widgets, WhatsApp buttons, trust signals, and incentives invisible to the crawler.

**Booking subdomain verification (mandatory):** If any booking subdomain or external booking URL is detected (booking.example.com, reservations.example.com, or links to third-party engines like FareHarbor, Bokun, ResNexus, Checkfront), **WebFetch or screenshot that URL immediately**. Classify the booking model as one of: `DIRECT_BOOKING` (guests can select dates/packages and complete payment online), `ENQUIRY_ONLY` (form submission, staff follow up), or `HYBRID` (some items bookable, some enquiry-only). Tag as [EXTRACTED] with the booking URL as source. This directly impacts downstream funnel architecture — getting this wrong cascades into market-research, paid-media-strategy, and ad copy.

**Determine business type** from crawl data. Load the appropriate sector lens from `references/sector-lenses/`:
- `wellness-retreats.md` — retreat centers, yoga studios, spas
- `local-services.md` — local physical businesses (salons, gyms, retail)
- `restaurant-food-service.md` — restaurants, cafes, cloud kitchens, catering
- `saas-software.md` — SaaS products, mobile apps, software platforms
- `professional-services-b2b.md` — IT services, consulting, agencies, B2B
- `temple-cultural-org.md` — temples, religious orgs, cultural centers, community orgs

If no matching lens exists, use the universal extraction framework in `references/website-crawl-guide.md`.

**Extract from crawl data:** all pages inventory, service/product pages, about/team info, testimonials, pricing, contact details, social links, any structured data.

Apply accuracy protocol: tag every extracted data point as [EXTRACTED] with page URL as source.

### Step 3: Brand Extraction

Run `scripts/extract_brand.py {url}`. The script automatically:
- Fetches and parses **external CSS stylesheets** (theme CSS, Typekit, etc.) — not just inline styles
- Detects **@font-face custom fonts** and normalizes weight variants (Gilroy-Bold → Gilroy)
- Filters out **WordPress default preset colors** (43+ colors present on every WP site)
- Filters out **platform default colors** (Webflow blue #3898ec, Squarespace dark, Wix blue, Shopify green) — auto-detects platform from HTML/CSS
- Filters out **utility/status colors** (Material Design, Bootstrap error/success/warning) — BUT rescues them if used on prominent selectors (h1-h6, header, nav, .hero, .btn, body) via **prominence-based rescue** (threshold: 2+ prominent selector hits)
- **Prominence-weighted ranking** — colors scored by frequency + prominent selector hits + accent usage (background-color/border > text-only color). Secondary color must be from a different hue family (>30° apart)
- Filters out **icon fonts** (Font Awesome, icomoon, webflow-icons, bootstrap-icons, etc.)
- Validates **Google Fonts imports** against actual CSS usage (flags vestigial imports)
- Uses **HSL saturation** for grayscale detection (catches dark greens, navy blues that naive RGB misses)
- Captures CSS variables named as colors (`--navy`, `--gold`, `--cream`) not just `--primary-color`

**If confidence is LOW or NONE:** use WebFetch to pull page HTML manually and re-extract. If MEDIUM: proceed but flag in brand-identity.md as needing client confirmation. If FETCH_FAILED: ask client for brand guidelines PDF.

**VISUAL_EDITOR_SITE anomaly = mandatory visual verification (never skip).** When this anomaly fires (Squarespace, Webflow, Wix, Shopify), the script's chromatic colors may be CSS theme defaults or code block syntax highlighting — NOT actual visible brand colors. You MUST:
1. WebFetch the homepage and ask specifically: "What accent colors are actually visible on this page? Are there any colored buttons, section backgrounds, links, or CTAs that aren't black/white/gray?"
2. If WebFetch says monochromatic/no accent colors → set primaryAccent to #000000, secondaryAccent to #ffffff, confidence to MEDIUM, and add MONOCHROMATIC_SITE anomaly. The brand relies on typography + photography, not color.
3. If WebFetch confirms specific accent colors → use those instead of the script's auto-ranked colors.
4. Cross-check allChromaticColors against known syntax highlighting palettes (Monokai: #ae81ff, #f92672, #a6e22e; Dracula: #ff79c6, #bd93f9; Solarized) — filter these out before trusting any extracted color.

This check overrides the confidence level — even HIGH confidence with VISUAL_EDITOR_SITE requires visual verification. The script can't distinguish "color defined in CSS" from "color visible on the page."

Review the output's `allChromaticColors` array — it contains the full palette. **Check the `anomalies` array** — it flags situations that need human review: no external CSS found, all colors grayscale, utility colors rescued via prominence, no fonts detected, vestigial Google Fonts, very similar primary/secondary colors, missing logo, VISUAL_EDITOR_SITE, MONOCHROMATIC_SITE. Each anomaly has a severity (high/medium/low) and a suggested action.

Save to `{client-folder}/deliverables/brand-config.json`.

Populate wiki `brand-identity.md`: colors (primary, secondary, supporting palette), fonts (primary + secondary), tone of voice (inferred from site copy — tag as [INFERRED]), logo URL, visual identity notes.

### Step 4: Offerings Inventory

Read `references/offerings-framework.md` for the documentation structure.

**Pricing-page enumeration (MANDATORY when a `/pricing/`, `/membership/`, `/passes/`, or `/plans/` URL exists):** Read `references/pricing-enumeration.md`. Run **per-card structured extraction** (Chrome MCP or WebFetch) — NOT narrative summarization. For every distinct price card, capture name / price / billing_cycle / audience / channel / time_window / class_restriction / concession_price / purchase_url. Save machine-readable to `wiki/offerings.json` AND human-readable to `wiki/offerings.md`. Validator cross-checks distinct `$N` count on page vs offerings count — mismatch ≥ 2 = CRITICAL fail.

For non-pricing-page offerings (services without a price card grid), document in `wiki/offerings.md` as separate sections:
- Name, description, target audience, pricing (if visible), page URL
- USP / differentiator, seasonality, booking/purchase mechanism
- Sector-specific data points from the loaded sector lens

If a single offering is being added to an existing business, add only that section.

**Marketing Implications guard rail:** Marketing Implications sections in offerings.md must not contradict BLANK fields above them. If a data point is BLANK (e.g., booking model unknown), the implication must present both paths. Never resolve ambiguity in implications that was left unresolved in the data fields.

### Step 5: Client Intake

Read `references/client-intake-template.md`. Use **AskUserQuestion** tool to ask questions **one at a time** with 2-4 multiple-choice options each. Sequence:
1. Primary business goal (bookings / awareness / fill off-peak / promote specific package)
2. Ad platform (Meta / Google / both)
3. Which offering(s) to focus on
4. Target geography
5. Budget range
6. Ad history (never / paused / active)
7. Known competitors
8. Capacity/seasonal constraints

Populate `wiki/business.md` with intake data. Tag all intake responses as [INTAKE].

### Step 6: Digital Presence Audit

Assess and document in `wiki/digital-presence.md`:
- **Website:** quality, speed perception, mobile-friendliness, CTA clarity, booking widgets, chat widgets
- **Social media:** platforms active, follower counts, post frequency, engagement level
- **Google Business Profile:** rating, review count, response rate (if local business)
- **Existing ad accounts:** active campaigns, historical performance summary
- **SEO baseline:** basic organic visibility signals

**Extraction approach:** Follow `references/extraction-fallbacks.md` per source. TripAdvisor works via WebFetch. Instagram/Facebook/LinkedIn require Chrome MCP (Tier 2) or computer-use screenshot (Tier 3). If neither MCP is available, output a manual verification checklist with BLANK fields. Log which tiers were attempted per source.

**Three mandatory checks** (always attempt, never leave as BLANK without trying):
1. **Meta Pixel check:** WebFetch homepage source, search for `fbq(`, `facebook.com/tr`, `connect.facebook.net/en_US/fbevents.js`. Also note any GTM/GA4 tags found.
2. **Google Business Profile:** Chrome MCP → Google Maps search for business name + location. Extract rating, review count, claim status, category, amenities, OTA prices if visible.
3. **Meta Ad Library:** Chrome MCP → `facebook.com/ads/library/?active_status=all&ad_type=all&country=ALL&q={business_name}`. Confirm whether the client's page has ever run ads. Note any competitor ads that appear.

Tag each data point: [EXTRACTED] if directly observed, [INFERRED] if interpreted.

### Step 7: Offering Prioritization

Based on all collected data — margins, audience size potential, competitive signals, seasonality, client goals — write a "Prioritization Analysis" section in `wiki/business.md`.

This is **observational, not prescriptive**. Present what the data suggests with evidence. Tag all insights as [INFERRED]. Example: "Yoga teacher training has higher price point ($3,500 vs $250/retreat drop-in) and lower seasonal dependency — data suggests stronger ROI potential for paid campaigns."

Do not make campaign decisions. Flag which offering(s) the data points toward and why. The campaign strategy skill makes the actual plan.

### Step 8: Validate & Flag Downstream

**Run `scripts/validate_all.py {client_folder}`** — single command that runs all three validators in sequence:
1. **Unit tests** (run_evals.py) — verifies extract_brand.py filtering logic is intact (64 tests)
2. **Output validation** (validate_output.py) — structural checks on client deliverables
3. **Wiki lint** (lint_wiki.py) — content quality: source labels, BLANK explanations, Change History, page registry

Fix all CRITICAL/ERROR failures before delivery. WARNINGs are advisory — review but don't block.

**Flag connections:** Note in wiki/log.md: "Business analysis complete — ready for market-research skill on [offering name(s)]."

Update wiki index.md and wiki-config.json.

### Step 9: Feedback Loop (Mandatory — Never Skip)

Read `references/feedback-loop.md`. Capture what worked/didn't. Add learnings below (30 lines max).

## Output Checklist

- [ ] Client folder created with sources/, wiki/, deliverables/
- [ ] Wiki initialized with base pages (business, brand-identity, digital-presence, offerings)
- [ ] brand-config.json saved to deliverables/
- [ ] Every data point tagged [EXTRACTED] or [INFERRED]
- [ ] Missing data shows BLANK with explanation
- [ ] All offerings documented with per-offering sections
- [ ] Sector lens applied (if available for business type)
- [ ] Digital presence audited
- [ ] Offering prioritization analysis present (observational, not prescriptive)
- [ ] Wiki index.md and log.md updated
- [ ] Downstream skill connections flagged
- [ ] lint_wiki.py passes with 0 ERRORs
- [ ] run_evals.py passes with 0 failures

## Learnings & Rules
<!-- Format: [DATE] [CLIENT TYPE] Finding → Action. Keep under 30 lines. Prune quarterly. See references/feedback-loop.md for protocol.
Pre-2026-04-12 entries pruned 2026-04-26 — encoded into extract_brand.py / lint_wiki.py / validate_all.py / sector-lenses / Steps 2/5/6. -->
- [2026-04-12] [Wellness] Crawl misses CTAs/widgets/incentives. Homepage WebFetch in Step 2 is mandatory. Booking subdomains must be classified as DIRECT_BOOKING/ENQUIRY_ONLY/HYBRID — getting this wrong cascades into every downstream skill.
- [2026-04-12] [General] Step 6 has 3 mandatory checks: Meta Pixel (WebFetch homepage source), GBP (Chrome MCP Maps search), Meta Ad Library (Chrome MCP query by business name). Check Ad Library early — existing ads change campaign strategy.
- [2026-04-12] [General] VISUAL_EDITOR_SITE anomaly (Webflow/Shopify/Squarespace): ALWAYS visually verify chromatic colors. Blog code blocks inject syntax highlighting palettes. Add MONOCHROMATIC_SITE anomaly when no accent colors visible despite script findings.
- [2026-04-17] [Multi-program] lint_wiki.py now reads wiki-config.json `type` and lints only program-registered pages. Accepts dict OR list `pages`, paragraph-level label counting, `BLANK |` table cells.
- [2026-04-17] [Temple/WordPress-theme] extract_brand.py HIGH confidence surfaced Bootstrap defaults; live DOM getComputedStyle on buttons + h1-h3 revealed true palette. RULE: When HIGH-confidence output looks wrong for sector (temple no saffron, wellness no earth tones), DOM getComputedStyle check before trusting palette. Independent of VISUAL_EDITOR_SITE.
- [2026-04-17] [SPA landing pages] React SPA returns only `<div id="root"></div>` to WebFetch. Identifiable via `gpt-engineer-file-uploads` in og:image. RULE: skip WebFetch, go direct to Chrome MCP navigate + read_page + javascript_tool.
- [2026-04-25] [Wellness/WordPress-Divi] extract_brand.py surfaced `ETmodules` as primary fontFamily — that's Divi's icon font. Risk: `hustle-icons-font` + Divi default theme colors leak into allChromaticColors. Patch candidate: treat ETmodules + hustle-icons-font as icon fonts. Until patched: when `is_wordpress=true` and ETmodules appears, manually swap primary to fontSecondary.
- [2026-04-25] [Wellness/MindBody] MindBody embedded purchase widget (studioid in URL) = DIRECT_BOOKING signal even when `/pricing/` renders static pass table.
- [2026-04-26] [CRITICAL — Living Flow Yoga / wellness] **business-analysis missed 5 of 9 distinct products on the public pricing page** — including the $39 Midday Recharge Pass (the standalone monthly digital-eligible SKU we explicitly told the client did NOT exist), Single Month Unlimited ($199), Annual ($1,790), 6-Month ($950), Casual Class Pass ($27). Cascaded through every downstream skill: market-research's DO-NOT-LAUNCH verdict for Live-stream AU-wide rested on "no $39-49/mo digital SKU exists" — provably wrong. Root cause: Step 4 used narrative summarization, LLM grouped products into "intro passes" + "memberships" buckets and dropped standalone outliers. → **Patched 2026-04-26:** Step 4 now mandates per-card structured enumeration (NOT summarization) when any `/pricing/` `/membership/` `/passes/` `/plans/` URL is detected. Required fields per product captured to `wiki/offerings.json` AND `wiki/offerings.md`. Validator cross-checks distinct `$N` count on page vs offerings count — mismatch ≥ 2 = CRITICAL. Full protocol in `references/pricing-enumeration.md`. **RULE:** Every distinct price card on a public pricing page must produce one offerings entry. Narrative summarization is forbidden — LLM tendency is to group + drop outliers.
- [2026-04-27] [Multi-program] [lint_wiki.py false-positives on briefs.md / strategy.md] Re-running business-analysis on Living Flow Yoga (multi-program), the linter flagged briefs.md for "Missing standard section: ## Key Findings" and "Only 2/21 substantive lines in labeled paragraphs (10%)", and program strategy.md (owned by market-research) for "Only 7/140 substantive lines in labeled paragraphs (5%)". Both are false positives: briefs.md is append-only verbatim client text with one implicit [INTAKE] source per dated entry (per-paragraph labelling would be noise) and strategy.md is market-research output that uses its own finding-level labels and is linted by that skill. → **Patched 2026-04-27:** Added page-name exemptions to `lint_source_labels`, `lint_change_history`, and `lint_standard_sections` for both `briefs.md` and `strategy.md`. After patch: Local Studio + Live-stream + _shared all pass with 0 errors / 0 warnings. **RULE:** When a wiki page type has its own structural pattern (append-only entries, downstream-skill ownership) that deviates from the business.md / brand-identity.md / digital-presence.md / offerings.md template, exempt it explicitly in lint_wiki.py rather than letting analysts ship "lint passes with N warnings — they're false positives, ignore" — that erodes the validator's signal value over time.
- [2026-04-27] [Universal — applies to all skills] Same-Client Re-Run Rule landed in CLAUDE.md as a universal Always-Active section. Same-client/same-case re-runs overwrite outputs in place — no v1/v2/v3, no -DATE parallel filenames, no dated section headers preserving prior content. One file per role, current state only. Only `wiki/log.md` (by-design change log) and `wiki/briefs.md` (brief history with `[ACTIVE]`/`[SUPERSEDED]` markers) are append-only. **For this skill specifically:** wiki/business.md, wiki/brand-identity.md, wiki/digital-presence.md, wiki/offerings.md, deliverables/brand-config.json — all overwritten in place on re-run. **RULE:** if you find yourself about to create a new file for an output that has the same logical role as an existing one, stop and overwrite the existing file instead.
- [2026-04-27] [Self-brand / marketing-services freelance — DigiSchola] Running business-analysis on Mayank's own DigiSchola brand, with explicit instruction to use a folder separate from the existing personal-brand wiki, worked cleanly with `Desktop/{Brand} Self-Audit/{Brand}/`. Two findings worth carrying forward: (1) When the audit subject is itself a marketing-services brand, Step 6 tracking findings double as immediate sales material (DigiSchola sells "tracking from day one" but its own site has zero pixels — a credibility paradox to surface in business.md Marketing Implications). (2) Solo-freelance brands in this segment make GBP optional — LinkedIn + Upwork + WhatsApp carry the local-trust signal. Not blocking, but Step 6 should explicitly accept `[BLANK] — because freelance services brand` as a valid outcome rather than treating the gap as a failure. Possible future: `freelance-services` sector lens. **RULE:** when the brand IS a marketing-services freelance practice, surface Step 6 self-audit gaps as creative material, not just gaps.
- [2026-04-27] [General — lint_wiki.py BLANK regex strictness] Linter regex `\bBLANK\s*[—\-–:(\|]\s*\S` requires a separator IMMEDIATELY after BLANK. Three formats analysts naturally type but the regex rejects: `[BLANK] because ...` (brackets are not separators), `**BLANK** — because ...` (bold markers between BLANK and separator break the regex), `BLANK because ...` (the most common natural form). Required forms: `BLANK — reason`, `BLANK: reason`, `BLANK (reason)`, `BLANK | reason` (table cells). **RULE:** when writing wiki pages, use only the four accepted BLANK forms. Patch candidate (low priority): widen the regex to accept `[BLANK]` and `**BLANK**` so the tag-style is valid too — then analysts can use the same `[EXTRACTED] / [INFERRED] / [BLANK]` visual rhythm without breaking validation.
- [2026-04-29] [Multi-program ISKM / Weekend Love Feast new-program add] Three findings adding a new program ("Weekend Love Feast") to a mature multi-program client (ISKM, already had `_shared/` + Nrsimha Caturdasi 2026): (1) `validate_all.py` run against the client root yields 8 CRITICALs — validators expect single-program shape (`<root>/wiki/`, `<root>/deliverables/`). For multi-program, point validators at `<root>/_shared/`. **RULE:** for multi-program clients, run `validate_all.py "<client>/_shared"` not `<client>`. Patch candidate: have `validate_all.py` auto-detect via `wiki-config.json#type` and route. (2) `lint_wiki.py` takes the program PARENT folder, not `<program>/wiki/` — it appends `/wiki` itself; the wiki path yields `wiki/wiki not-a-directory`. Document path semantics in `--help`. (3) When a React-SPA WebFetch returns nothing (standard SPA outcome), the Lovable repo mirror at `<program>/site/src/pages/<Program>.tsx` is the fastest source — TSX files contain FAQS, SCHEDULE arrays, hero JSX, useEffect meta-tag setters as plain literals. **RULE:** when a Lovable / GPT-Engineer mirror exists, prefer reading the TSX directly over Chrome MCP for static copy / schedule / FAQ extraction. Use Chrome MCP only when verifying live DOM state (real-time Supabase counters, computed CSS, runtime-only behaviour).
