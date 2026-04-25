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

From the crawl data, identify every distinct product/service/offering. For each offering, document in `wiki/offerings.md` as a separate section:
- Name, description, target audience, pricing (if visible), page URL
- USP / differentiator, seasonality, booking/purchase mechanism
- Sector-specific data points from the loaded sector lens

If a single offering is being added to an existing business, add only that section.

**Marketing Implications guard rail:** Marketing Implications sections in offerings.md must not contradict BLANK fields above them. If a data point is BLANK (e.g., booking model unknown), the implication must present both paths: "IF enquiry-only → lead gen funnel. IF direct booking → conversion-optimized funnel." Never resolve ambiguity in implications that was left unresolved in the data fields.

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

<!--
Format: [DATE] [CLIENT TYPE] Finding → Action
Keep under 30 lines. Prune quarterly. See references/feedback-loop.md for protocol.
-->

<!-- CONSOLIDATED 2026-04-09 script fixes (all baked into extract_brand.py): external CSS fetching, vestigial Google Font detection, WP preset filtering, HSL grayscale, utility color filtering + prominence rescue, icon font filtering (incl carousel/Webflow), platform default filtering, prominence-weighted scoring with hue-diff secondary, VISUAL_EDITOR_SITE anomaly, anomalies array (8 detectors), validate_all.py master runner, lint_wiki.py content linter -->
- [2026-04-09] [General] Finding: Brand style guide PDF may not match website CSS — always ask for guidelines during intake. → Action: Added to Step 5.
- [2026-04-09] [Process] Finding: Script fixes without SKILL.md updates violate feedback loop. → Action: CLAUDE.md Skill Auto-Update Rule created — learnings are part of the fix.
- [2026-04-12] [Architecture] Finding: Clients with multiple programs/products need separate research per program but share brand DNA. Old structure forced everything into one folder — running a second program meant either overwriting or awkward subfolder hacks. → Action: Added multi-program support to init_wiki.py (--shared, --program, --migrate, --detect). Brand DNA (business.md, brand-identity.md, digital-presence.md, offerings.md, brand-config.json) goes to `_shared/`. Per-program research gets its own folder. Reference doc at `market-research/references/multi-program-structure.md`. Step 1 updated with structure detection.
- [2026-04-10] [SaaS/Mobile App] SaaS/app businesses use Free/Pro/Enterprise tier structure vs services. offerings.md handles this with per-tier sections.
- [2026-04-11] [General] No failure/fallback protocols existed. → Action: Added inline failure handling + 4 new sector lenses + 2 new eval edge cases.
- [2026-04-11] [General] lint_wiki.py rejected PENDING confidence from init_wiki.py. → Action: Updated regex to accept PENDING with WARNING.
- [2026-04-12] [Wellness/Simplotel] Simplotel uses standard CSS — HIGH confidence extraction. Hospitality CMS platforms work well for CSS-based brand extraction.
- [2026-04-12] [Wellness/Simplotel] Crawl data misses CTAs/widgets. Homepage WebFetch caught Simplotel booking widget + WhatsApp + 5% off incentive. → Action: Always WebFetch homepage in Step 2.
- [2026-04-12] [Process] Sequential AskUserQuestion intake (1 question, 2-4 options) works much better than wall-of-text. → Action: Updated Step 5.
- [2026-04-12] [Process] Use "BLANK — reason" format (em-dash). Reserve "BLANK" for data fields only — "empty" in narrative prose.
- [2026-04-12] [Wellness] Currency mismatch (USD pricing for INR audience) creates cognitive friction. → Flag in business.md marketing implications.
- [2026-04-12] [General] WebFetch fails on IG/FB/LinkedIn. Chrome MCP succeeds for FB (if logged in). Computer-use works for IG screenshots. 4-tier fallback validated.
<!-- CONSOLIDATED 2026-04-12 script + quality fixes: lint_wiki.py Details skip for 3+ sections, darkBackground→darkText rename, lightBackground added, primary+secondary seeded into allChromaticColors, source label format must be exact `[EXTRACTED]` token (not `[EXTRACTED — detail]`), use `[EXTRACTED] (detail)` format, `[INTAKE]` not recognized — use `[EXTRACTED] (client intake)` -->
- [2026-04-12] [General] 3 mandatory checks in Step 6: Meta Pixel (WebFetch), GBP (Chrome MCP), Meta Ad Library (Chrome MCP). Check Ad Library early — existing ads fundamentally change campaign strategy. Google Maps: use search URL not short URLs.
- [2026-04-12] [Wellness] GBP claim status + OTA pricing critical for hospitality. Booking subdomains must be WebFetched in Step 2 — classify as DIRECT_BOOKING/ENQUIRY_ONLY/HYBRID. Marketing implications must not contradict BLANK fields.
<!-- CONSOLIDATED 2026-04-12 Shopify/Squarespace visual editor fixes: Shopify triggers VISUAL_EDITOR_SITE (same as Webflow), TripAdvisor WebFetch unreliable (use Google Maps widget), Squarespace misdetected as Webflow, Monokai syntax highlighting colors polluted allChromaticColors, MONOCHROMATIC_SITE anomaly type needed -->
- [2026-04-12] [General] VISUAL_EDITOR_SITE anomaly (Webflow/Shopify/Squarespace): ALWAYS visually verify chromatic colors. Blog code blocks can inject syntax highlighting palettes (Monokai, Dracula). Add MONOCHROMATIC_SITE anomaly when no accent colors are visible despite script findings.
- [2026-04-12] [Process] v1→v2 cycle validated (Shreyas + Gwinganna). Skill maturity increasing — Gwinganna passed validate_all.py first run.
- [2026-04-12] [Product/Manufacturing] Product companies need no sector lens — universal framework covers single-product businesses with B2C/B2B segmentation.
- [2026-04-17] [Multi-program] lint_wiki.py crashed on list-type `pages` field from multi-program init_wiki, and demanded all 4 shared-DNA pages in program folders. → Action: lint_wiki now (a) accepts dict OR list `pages`; (b) reads wiki-config.json `type` — when `type: program`, lints only registered pages; (c) paragraph-level label counting (was bullet/bold-only — missed prose); (d) accepts `BLANK |` inside table cells.
- [2026-04-17] [Temple — ISKM Singapore] extract_brand.py HIGH confidence but surfaced Bootstrap defaults (#cc3366/#5cb85c/Inter). Live DOM getComputedStyle on buttons + h1-h3 revealed true palette (gold #f1c66e / navy #1f3671 / Noto Sans — classic ISKCON). → Action: When HIGH-confidence output looks wrong for the sector (temple showing no saffron/gold, wellness showing no earth tones), DOM getComputedStyle check is mandatory before trusting the palette. Independent of VISUAL_EDITOR_SITE check — this is a WordPress theme where script read theme CSS but not computed styles.
- [2026-04-17] [SPA landing pages] React SPA event subdomain returned only `<div id="root"></div>` to WebFetch. Identifiable by `gpt-engineer-file-uploads` in og:image (Lovable/GPT-Engineer origin). → Action: skip WebFetch, go direct to Chrome MCP navigate + read_page + javascript_tool.
- [2026-04-25] [Wellness/WordPress-Divi] extract_brand.py surfaced `ETmodules` as primary fontFamily on a Divi-themed WP site (Yoga Ashfield). ETmodules is Divi's icon font, not a body font. Same risk: `hustle-icons-font` and Divi's default theme blues/purples (#2ea3f2, #008bdb, #974df3, #7e3bd0) leaked into allChromaticColors. → Action: Divi-specific filter candidate for extract_brand.py — treat ETmodules + hustle-icons-font like Font Awesome / webflow-icons (always icon fonts). Until patched: when `is_wordpress=true` and ETmodules appears as fontFamily, manually swap primary to fontSecondary (Poppins / Roboto / Montserrat are Divi body-font defaults).
- [2026-04-25] [Wellness/MindBody] MindBody embedded purchase widget (studioid in URL) = DIRECT_BOOKING signal even when `pricing` page renders static pass table — students pick class, pay, book in one flow. Logged for sector-lens reuse on other MindBody studios.
