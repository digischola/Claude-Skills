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
- `shared-context/output-structure.md` — write final HTML/MP4/PDF and upload-ready CSV bundles to the folder root, intermediate MD/JSON/CSV to `_engine/working/`
- `shared-context/client-shareability.md` — client-facing files must read like first copies; no correction trails / audit history / internal-process commentary. Validator: `python3 ~/.claude/scripts/check_client_shareability.py {client}`

If a client wiki already exists (`{client-folder}/_engine/wiki/`), read it first. This may be an update, not a fresh onboard.

## Process Overview

### Step 1: Client Folder & Wiki Init

**Structure detection:** Check if `Desktop/{Client Name}/` exists. If yes, run `market-research/scripts/init_wiki.py {path} --detect` to determine structure type (NEW_CLIENT, SINGLE_PROGRAM, MULTI_PROGRAM).

**Create folder:** For new clients, create `Desktop/{Client Name}/{Business Name}/` with `_engine/` (containing sources/, wiki/, working/). For multi-program clients, business-analysis outputs to the client root's `_engine/` (brand DNA is shared across all programs).

**Init wiki:** Run `market-research/scripts/init_wiki.py` with appropriate mode:
- New single-program: `init_wiki.py {client_folder} {business_name} {project_name}`
- New multi-program: `init_wiki.py {client_folder} {business_name} --shared` then `--program "Name"`
- Existing client, new program: `init_wiki.py {client_folder} {business_name} --program "Name"` (if already multi-program) or `--migrate "Name"` (to convert single→multi)

Creates base pages (business.md, brand-identity.md, digital-presence.md, offerings.md) + index.md + log.md + `_engine/wiki-config.json`. If wiki exists, skip init. Read `market-research/references/multi-program-structure.md` for full multi-program folder layout.

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

Save to `{client-folder}/_engine/brand-config.json`.

Populate wiki `brand-identity.md`: colors (primary, secondary, supporting palette), fonts (primary + secondary), tone of voice (inferred from site copy — tag as [INFERRED]), logo URL, visual identity notes.

### Step 4: Offerings Inventory

Read `references/offerings-framework.md` for the documentation structure.

**Pricing-page enumeration (MANDATORY when a `/pricing/`, `/membership/`, `/passes/`, or `/plans/` URL exists):** Read `references/pricing-enumeration.md`. Run **per-card structured extraction** (Chrome MCP or WebFetch) — NOT narrative summarization. For every distinct price card, capture name / price / billing_cycle / audience / channel / time_window / class_restriction / concession_price / purchase_url. Save machine-readable to `_engine/wiki/offerings.json` AND human-readable to `_engine/wiki/offerings.md`. Validator cross-checks distinct `$N` count on page vs offerings count — mismatch ≥ 2 = CRITICAL fail.

For non-pricing-page offerings (services without a price card grid), document in `_engine/wiki/offerings.md` as separate sections:
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

**Voice-capture questions** (mandatory — feeds Step 8 voice-library bootstrap when client has no creative history):
9. Service description in two sentences (founder's natural voice)
10. Top objection + reassurance (how the founder answers the most common hesitation)
11. Conversion-moment feeling (what feeling the founder wants users to have at sign-up/booking)

Populate `_engine/wiki/business.md` with intake data. Tag all intake responses as [INTAKE].

### Step 6: Digital Presence Audit

Assess and document in `_engine/wiki/digital-presence.md`:
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

Based on all collected data — margins, audience size potential, competitive signals, seasonality, client goals — write a "Prioritization Analysis" section in `_engine/wiki/business.md`.

This is **observational, not prescriptive**. Present what the data suggests with evidence. Tag all insights as [INFERRED]. Example: "Yoga teacher training has higher price point ($3,500 vs $250/retreat drop-in) and lower seasonal dependency — data suggests stronger ROI potential for paid campaigns."

Do not make campaign decisions. Flag which offering(s) the data points toward and why. The campaign strategy skill makes the actual plan.

### Step 8: Voice Library Extraction (MANDATORY — bedrock for downstream copy/voice)

Read `references/voice-library-extraction.md` for the full protocol. Spec: `~/.claude/shared-context/voice-library-spec.md`.

Run `scripts/extract_voice_library.py --detect <client_folder>` to determine which mode applies:

**MODE_A_ESTABLISHED** (client has Windsor.ai paid history OR Meta Ads Library activity OR reference creatives in `_engine/references/images/`): pull top-3 by performance, extract patterns from real creative copy → write `voice-library.json` with `bootstrapping: false`.

**MODE_B_BOOTSTRAP** (new client, no historic data): three-tier stack:
1. **Sector seed** — `references/voice-library-sector-seeds/{sector}.json` (or `_default.json`)
2. **Founder voice** — three intake questions captured in Step 5, parsed into custom patterns (founder voice overrides sector seed on conflict)
3. **Competitor anti-pattern** — top 3 competitors from `competitors.md` saved as `differentiate_from` reference

Run `scripts/extract_voice_library.py --bootstrap <client> --sector <s> --founder-q1 ... --founder-q2 ... --founder-q3 ... --competitors "<a,b,c>"`. Output written to `{client}/_engine/wiki/voice-library.json` (single-program) OR `{client-root}/_engine/wiki/voice-library.json` (multi-program, brand voice is shared).

`bootstrapping: true` until refresh trigger fires (50+ leads OR 30 days live OR ≥500 link clicks) — at which point post-launch-optimization auto-suggests pattern updates from real performance, flag flips to false, library matures.

**Quality bar (script-enforced):** ≥3 headline_patterns w/ examples, trust_line_template w/ ≥2 examples, ≥2 cta_verb_noun_pairs, voice_rules.forbidden_phrases populated, campaign_type_anchor_pattern set. Fails → block downstream skills.

**Cross-skill handoff:** voice-library.json is consumed by paid-media-strategy (populates creative-brief event_facts + voice_anchor + cta_verb_noun_pair), ad-copywriter (validates compliance), landing-page-builder, visual-generator, ai-video-generator. The bedrock prevents voice drift across audience segments and proves the value of past-winner voice anchoring.

### Step 9: Validate & Flag Downstream

**Run `scripts/validate_all.py {client_folder}`** — single command that runs all three validators in sequence:
1. **Unit tests** (run_evals.py) — verifies extract_brand.py filtering logic is intact (64 tests)
2. **Output validation** (validate_output.py) — structural checks on client deliverables
3. **Wiki lint** (lint_wiki.py) — content quality: source labels, BLANK explanations, Change History, page registry

Fix all CRITICAL/ERROR failures before delivery. WARNINGs are advisory — review but don't block.

**Flag connections:** Note in `_engine/wiki/log.md`: "Business analysis complete — ready for market-research skill on [offering name(s)]. Voice library extracted: <MODE_A | MODE_B bootstrap>."

Update `_engine/wiki/index.md` and `_engine/wiki-config.json`.

### Step 10: Feedback Loop (Mandatory — Never Skip)

Read `references/feedback-loop.md`. Capture what worked/didn't. Add learnings below (30 lines max).

## Output Checklist

- [ ] Client folder created with `_engine/` (containing sources/, wiki/, working/)
- [ ] Wiki initialized with base pages (business, brand-identity, digital-presence, offerings)
- [ ] brand-config.json saved to `_engine/`
- [ ] Every data point tagged [EXTRACTED] or [INFERRED]
- [ ] Missing data shows BLANK with explanation
- [ ] All offerings documented with per-offering sections
- [ ] Sector lens applied (if available for business type)
- [ ] Digital presence audited
- [ ] Offering prioritization analysis present (observational, not prescriptive)
- [ ] Wiki index.md and log.md updated
- [ ] Downstream skill connections flagged
- [ ] **voice-library.json written to wiki** (Step 8) — MODE_A from past creatives OR MODE_B 3-tier bootstrap; quality bar passes
- [ ] lint_wiki.py passes with 0 ERRORs
- [ ] run_evals.py passes with 0 failures

## Learnings & Rules
<!-- Format: [DATE] [CLIENT TYPE] Finding → Action. Keep under 30 lines. Prune quarterly. See references/feedback-loop.md for protocol.
Pre-2026-04-12 entries pruned 2026-04-26 — encoded into extract_brand.py / lint_wiki.py / validate_all.py / sector-lenses / Steps 2/5/6. -->
- [2026-04-30] [BEDROCK — voice-library architecture across all clients] New Step 8 + scripts/extract_voice_library.py + references/voice-library-extraction.md + references/voice-library-sector-seeds/ added. Every client now gets `_engine/wiki/voice-library.json` extracted from past creatives (MODE_A) OR from sector seed + 3 founder intake Qs + competitor anti-pattern (MODE_B bootstrap). Spec: `~/.claude/shared-context/voice-library-spec.md`. Step 5 client intake gained 3 voice-capture Qs (service description / objection-reassurance / conversion-moment feeling). Cross-skill consumer chain: voice-library.json → paid-media-strategy creative-brief.json (event_facts + voice_anchor + cta_verb_noun_pair) → ad-copywriter validators (validate_voice_library_compliance) → landing-page-builder + visual-generator + ai-video-generator. Solves voice-drift across audience-segmented carousels (WLF Apr-30 finding: 5 cards / 5 different trust-line strings / generic CTAs). **RULE:** No client ships ad copy without a voice-library.json. New clients MUST run BOOTSTRAP; sector seed + founder voice must populate the file before any downstream skill writes copy.
- [2026-04-12→25] [Crawl + extraction + sector quirks — consolidated] Crawl misses CTAs/widgets/incentives → homepage WebFetch in Step 2 is mandatory. Booking subdomains classified DIRECT/ENQUIRY/HYBRID (downstream cascade risk). Step 6 has 3 mandatory checks (Meta Pixel / GBP / Meta Ad Library — check Ad Library early). VISUAL_EDITOR_SITE anomaly: visually verify chromatic colors; MONOCHROMATIC_SITE anomaly when no accent colors visible. extract_brand.py HIGH confidence can mask Bootstrap/Divi defaults — DOM getComputedStyle check on buttons + h1-h3 if sector palette looks wrong. ETmodules + hustle-icons-font are icon fonts (Divi). React SPA returns `<div id="root"></div>` to WebFetch (id via og:image gpt-engineer); skip to Chrome MCP. MindBody studioid in URL = DIRECT_BOOKING signal even with static `/pricing/` table. lint_wiki.py reads wiki-config.json type, accepts dict OR list pages, paragraph-level label counting.
- [2026-04-26] [CRITICAL — Living Flow Yoga / pricing enumeration] Step 4 used narrative summarization and missed 5 of 9 products on a public pricing page; cascaded downstream. **Patched:** Step 4 mandates per-card structured enumeration when `/pricing/` `/membership/` `/passes/` `/plans/` URL detected; offerings.json + offerings.md required; validator cross-checks distinct `$N` count vs offerings count — mismatch ≥ 2 = CRITICAL. See `references/pricing-enumeration.md`. **RULE:** every distinct price card → one offerings entry. Narrative summarization forbidden.
- [2026-04-27→29] [Multi-program + Same-Client Re-Run + lint exemptions + Lovable TSX] (1) Same-Client Re-Run Rule (kernel CLAUDE.md): re-runs overwrite in place — no v1/v2/v3 files. Append-only only for log.md + briefs.md. (2) lint_wiki.py exempts briefs.md + strategy.md from source-label / change-history / standard-sections rules. (3) When Lovable/GPT-Engineer SPA mirror exists, read `<program>/site/src/pages/<Program>.tsx` (FAQS / SCHEDULE arrays as plain literals) instead of WebFetch on the empty `<div id="root"></div>`. (4) Solo-freelance services brands: Step 6 GBP can validly be BLANK; surface tracking gaps as sales material when client IS a marketing-services brand.
- [2026-04-29] [STRUCTURAL REFACTOR] `_engine/` for skill internals, presentables at folder root. Multi-program `_shared/` → client-root `_engine/`.
- [2026-04-30] [Multi-program re-run + validator drift] WLF re-run findings. (1) `validate_all.py` takes the CLIENT FOLDER, NOT `<client>/_engine` (corrects 2026-04-27→29 note); lint_wiki.py takes the program PARENT, not `<program>/_engine/wiki/`. (2) `validate_output.py:130` BLANK-separator regex expanded to `— - – : | (` (was missing `|` and `(` — the kernel-rule set is now actually enforced). (3) Metadata header lint requires `Sources:` PLURAL form (singular `Source:` fails). **RULE:** when a multi-program `wiki-config.json` lists a program but the `{Client}/{Program}/_engine/wiki/` folder doesn't exist, a prior run shipped the registry without scaffolding — run `init_wiki.py --program "Name"` and populate `briefs.md` from any references in the parent log.
