---
name: campaign-setup
description: "Generates bulk-import CSVs for Google Ads Editor and Meta Ads Manager from upstream strategy + ad copy + landing page deliverables. Produces campaign/ad-group/keyword/RSA CSVs for Google, campaign/ad-set/ad CSV for Meta, creative upload manifest, pre-launch verification checklist, and launch runbook. No third-party MCP or write-API dependency — outputs are bulk-import files the user uploads via Ads Editor / Ads Manager UI. Works downstream from paid-media-strategy + ad-copywriter + landing-page-builder (reads media-plan.csv, google-ads.csv, meta-ads.csv, page-spec.json). Use when user mentions: launch campaigns, build campaigns, campaign setup, set up Google Ads, set up Meta Ads, create campaigns, build Ads Editor CSV, Meta bulk import, ready to launch. Do NOT trigger for: strategy planning (paid-media-strategy), ad copy writing (ad-copywriter), post-launch optimization (post-launch-optimization), landing page building (landing-page-builder)."
---

# Campaign Setup

Produces bulk-import files for Google Ads Editor and Meta Ads Manager plus a verification checklist and launch runbook. No third-party tools, no write APIs — everything is a file the user imports manually via the official UIs.

## Context Loading

Read these shared context files before starting:
- `shared-context/analyst-profile.md` — workflow, client types, quality standards
- `shared-context/accuracy-protocol.md` — 3 accuracy rules for all data handling
- `shared-context/output-structure.md` — write final HTML/MP4/PDF and upload-ready CSV bundles to `outputs/`, intermediate MD/JSON/CSV to `working/`
- `shared-context/client-shareability.md` — client-facing files must read like first copies; no correction trails / audit history / internal-process commentary. Validator: `python3 ~/.claude/scripts/check_client_shareability.py {client}`

## Process Overview

### Step 1: Upstream Input Check

Verify the client has the required prior deliverables. This skill is designed to consume structured output from prior skills, not to run standalone. Standalone mode is supported but will require manual input for everything.

Required inputs:
- `{client}/wiki/strategy.md` — market research context
- `{client}/deliverables/{client}-paid-media-strategy.md` — platform strategy, campaign architecture
- `{client}/deliverables/{client}-media-plan.csv` — campaigns, budgets, targeting
- `{client}/deliverables/{client}-google-ads.csv` — RSAs, headlines, descriptions (if Google in scope)
- `{client}/deliverables/{client}-meta-ads.csv` — ad variants, primary text, headlines (if Meta in scope)
- `{client}/deliverables/{client}-*-page-spec.json` — landing page URLs (or direct URL from user)

Missing inputs → fall back to standalone mode with guided questions.

### Step 2: Load Context & Determine Scope

- Read all required deliverables above
- Parse media-plan.csv to determine: Google-only, Meta-only, or both
- Determine phase of strategy (Phase 1 launch, expansion, refresh)
- Extract: campaign objectives, budgets, targeting, conversion actions, landing page URLs

### Step 3: Client Intake via AskUserQuestion

Ask these one-pass guided questions (non-negotiable — these can't be inferred from prior deliverables):

1. **Google Ads account ID** (if Google in scope) — format: XXX-XXX-XXXX. Leave blank if account not yet created.
2. **Meta Ad Account ID + Pixel ID** (if Meta in scope). Leave blank if not yet created.
3. **Conversion action names** — exact names as set up in Google Ads (e.g., "Enquiry", "Brochure Download"). Blank if conversions not yet configured.
4. **Existing audiences to include** — list saved audience names or IDs. Blank if no existing audiences.
5. **Tracking URL parameters** — default UTM structure or custom tracking template.
6. **Location exclusions** — specific zones to exclude beyond the strategy's targeting.
7. **Day-parting or schedule** — campaign schedule if not in strategy (most strategies default to 24/7).
8. **Call/location extensions content** — phone number, business address, if Google Ads Search scope.

If any field is blank, the skill outputs CSVs with placeholder `<REPLACE_ME>` tokens and flags them in the pre-launch checklist. NEVER fabricate account IDs or conversion names.

### Step 4: Generate Google Ads Editor Bulk Import CSVs

Load `references/google-ads-editor-schema.md` for exact column specs.

**Pre-filter step (MANDATORY for wellness / yoga / fitness / therapy / healthcare / financial / employment / housing clients):** Before emitting `03-keywords.csv`, run every positive keyword through the restricted-category pattern list in `references/restricted-keyword-categories.md`. Google's Personalized Advertising Restrictions auto-reject keywords matching health-condition / mental-health / weight-loss / financial-status / employment-status patterns at import. Reframe per the recipe table or drop. Negatives are exempt (they SHOULD reference these terms). Validator hard-fails any restricted match in positive keywords.

**Structured Snippets format (CRITICAL — do not regress):** Emit `07-structured-snippets.csv` with the single `Snippet Values` column, semicolon-delimited (e.g. `Vinyasa;Yin;Beginners`). DO NOT use per-column `Value 1`/`Value 2`/... format — Editor's parser rejects that with "There are too few values for a structured snippet" even when 3+ values are populated. See `references/google-ads-editor-schema.md §7`.

Produce separate CSV files (one entity type per file — matches Ads Editor's "Make multiple changes" paste workflow):

```
deliverables/campaign-setup/google-ads/
  01-campaigns.csv              Campaigns + budgets + bidding + targeting
  02-ad-groups.csv              Ad groups per campaign
  03-keywords.csv               Keywords with match types + final URLs
  04-responsive-search-ads.csv  RSAs (up to 15 headlines + 4 descriptions)
  05-sitelink-extensions.csv    4-8 sitelinks per campaign
  06-callout-extensions.csv     Callouts (4 per campaign minimum)
  07-structured-snippets.csv    Structured snippets (optional)
  08-negative-keywords.csv      Campaign/ad group level negatives
  README.md                     Import order, paste instructions, troubleshooting
```

Character limit enforcement (CRITICAL — will cause import errors otherwise):
- RSA headlines: 30 chars
- RSA descriptions: 90 chars
- RSA path 1/2: 15 chars each
- Sitelink text: 25 chars
- Sitelink description 1/2: 35 chars each
- Callouts: 25 chars
- Structured snippets: 25 chars per value

### Step 5: Generate Meta Ads Manager Bulk Import

Load `references/meta-bulk-import-schema.md` for exact column specs.

Meta's bulk import is less mature than Google's — produce both machine-readable and human-guided outputs:

```
deliverables/campaign-setup/meta-ads/
  meta-bulk-import.csv          Single CSV with campaigns, ad sets, ads rows
  creative-upload-manifest.md   List of all image/video assets to upload to Asset Library BEFORE bulk import
  campaign-blueprint.md         Step-by-step manual build guide (fallback if bulk import fails)
  README.md                     Import order, creative prep steps, troubleshooting
```

Character limit enforcement:
- Meta Primary Text (Body): 125 chars recommended (truncation warning 125+)
- Meta Headline (Title): 27 chars mobile / 40 chars recommended
- Meta Description (Link Description): 27 chars
- URL display (Display Link): brand domain

Creative upload manifest format:
```
| asset_id | filename | type | aspect_ratio | campaign | ad_set | ad_name |
```

### Step 6: Generate Pre-Launch Verification Checklist

Load `references/pre-launch-checklist-template.md`.

Produces `deliverables/campaign-setup/pre-launch-checklist.md` with sections:
1. Tracking infrastructure (conversion actions, pixel, CAPI, GA4, UTM)
2. Account settings (billing, time zone, currency, attribution)
3. Campaign-level verification (budgets, bid strategy, locations, languages, schedules)
4. Ad group verification (keywords, bids, negatives)
5. Creative verification (URLs live, UTM appended, character limits)
6. Extensions (sitelinks live, callouts match landing page)
7. Placeholder tokens — every `<REPLACE_ME>` from Step 3 listed
8. Final sign-off — client approval checkbox before posting changes

### Step 7: Generate Launch Runbook

Load `references/launch-runbook-template.md`.

Produces `deliverables/campaign-setup/launch-runbook.md` with:
1. Pre-upload prep (download Ads Editor, export current account, back up)
2. Google Ads Editor upload sequence (import each CSV in order, review, post changes)
3. Meta Ads Manager upload sequence (upload creative first, then bulk import, then review)
4. Post-launch first-24-hour checks (ads approved, conversions firing, impressions > 0)
5. 7-day and 14-day checkpoints

### Step 8: Validate Outputs

Run `scripts/validate_output.py` against generated CSVs. Fixes any CRITICAL failures before delivery:
- Character limit violations (will cause Ads Editor / Meta import rejection)
- Placeholder `<REPLACE_ME>` tokens (must be listed in checklist, not silently passed)
- Schema column name mismatches
- Orphan references (ad group referencing non-existent campaign)
- URL format errors
- Duplicate entity names within same parent

### Step 9: Update Wiki & Close

- Add `CAMPAIGN-SETUP COMPLETE` entry to `{client}/wiki/log.md` with platform(s), campaign count, total ad count, placeholder token count
- Flag downstream: `post-launch-optimization` will track this campaign family once live
- Run feedback loop per `references/feedback-loop.md`
- If battle-test mode: add learnings to SKILL.md

## Failure Handling

- No paid-media-strategy upstream → run standalone mode, ask 12-question intake covering strategy basics
- No ad-copywriter upstream → cannot produce RSAs/ads CSVs; block and request ad copy first
- No landing page URL → use `<REPLACE_ME_LANDING_URL>` token; flag in checklist
- Character limit violations → truncate to limit + append `[TRUNCATED]` marker in generated CSV + WARNING in validator output
- Media plan has unsupported campaign type (e.g., Discovery, DemandGen) → flag as WARNING, generate best-effort CSV, document manual setup steps in runbook
- Meta bulk import known to fail for complex campaigns → always produce campaign-blueprint.md as manual fallback, even if bulk CSV succeeds

## Learnings & Rules

- **[2026-04-16] [B2C high-ticket, both platforms] Meta bulk CSV column alignment is critical → Rule: when hand-writing CSV rows where only columns 1-5 and columns 27+ have values, count commas exactly. Between Ad Set Name (col 6) and Ad Name (col 27) there must be 21 commas (20 empty fields + separators). Off-by-one on this produced 28 CRITICAL validator errors — "SINGLE_IMAGE" got read as a status value, "retreathouse.com.au" as a URL without https. Fix landed in meta-bulk-import.csv second pass. Validator already catches schema drift via column count and enum checks — trust it, don't override.**
- **[2026-04-16] [B2C high-ticket, both platforms] Meta Body limit is SOFT not HARD → Rule: Meta truncates primary text with "… See more" at roughly 125 chars but copy longer than 125 is not rejected by bulk import. Ad copy is often written to survive truncation (hook in first 125, supporting detail after). Validator was originally CRITICAL on Body > 125 which produced false positives against correctly-written ad-copywriter output. Fixed: added `soft=True` param to `check_char_limit()`, `META_SOFT_LIMITS = {"Body"}`. Body overflow now logs WARNING with note "(soft — will truncate on delivery)" instead of CRITICAL. All other Meta limits (Title 40, Link Description 27) remain HARD/CRITICAL because they truncate destructively without ellipsis.**
- **[2026-04-16] [B2C high-ticket, both platforms] Meta Link Description 27-char discipline → Rule: Link Description is the SHORTEST Meta field after Card Headline/Description. Even copy that reads short ("Floor plans & pricing inside." = 29) can overflow. Generator/writer must verify BEFORE paste, not after — fixing post-validator costs a full regenerate of the CSV row. Preferred format: two short clauses separated by "+" or ".", max 4 words per clause, avoid & and filler words like "inside", "today", "now".**
- **[2026-04-16] [B2C high-ticket, both platforms] Phased launch requires phase-aware placeholder strategy → Rule: when client strategy is multi-phase (e.g., Phase 1 Google → Phase 2 Meta Prospecting → Phase 3 Meta Retargeting) and upstream hasn't produced all assets yet, generate ALL phases' CSVs with `<REPLACE_ME_*>` tokens for Phase 2/3 assets that don't exist. Group placeholder list in checklist Section 0 by phase, so each phase has a clean launch-authorization section. Do NOT skip future phases — pre-generating the CSV saves the analyst from context-switching 30-60 days later. Retreat House checklist has three separate "Launch authorized" gates (Phase 1 / Phase 2 / Phase 3).**
- **[2026-04-16] [B2C high-ticket, both platforms] STR/Investor subset routes to dedicated landing page → Rule: when upstream has produced a secondary landing page (investor LP, B2B LP, industry LP) distinct from homepage, route ONLY the matching ad group/ad set's traffic there. In Retreat House case: `STR_Investment` Google ad group + Meta `Prospecting-STRInvestor-*` + `Retargeting-STRInvestor-*` ads → `retreathouse.com.au/investors`; every other entity → `retreathouse.com.au`. Validator must accept the mixed URL pattern (both URLs resolve HTTPS) without flagging inconsistency.**
- **[2026-04-16] [B2C high-ticket, both platforms] Carousel ads belong in manual-build fallback, NOT bulk CSV → Rule: Meta's bulk import for carousel (5 cards, each with own image/headline/description/link) is known-fragile. Moving carousel to `campaign-blueprint.md` as a manual-build instruction (5 card specs with copy + image asset reference) keeps the bulk CSV clean (only SINGLE_IMAGE ads) and gives the analyst a checklist to build the carousel in Ads Manager UI. Applies universally — do not attempt carousel in bulk CSV.**
- **[2026-04-16] [B2C high-ticket, both platforms] Advantage+ Audience OPT_IN for prospecting, OPT_OUT for retargeting → Rule: prospecting ad sets rely on Advantage+ Audience (Meta's ML audience expansion) since there's no intent signal to respect — set `EXPANSION_ALL` / `OPT_IN`. Retargeting ad sets target a specific warm pool and expansion dilutes that — set `EXPANSION_NONE` / `OPT_OUT`. The validator doesn't enforce this distinction but the schema and blueprint must.**
- **[2026-04-16] [SKILL DESIGN] Manual bulk-import flow confirmed as v1 scope → Decision: skill stays manual-only (Google Ads Editor paste + Meta bulk import UI) per analyst instruction on 2026-04-16. Automation via Google Ads API push script was considered and deferred. Revisit trigger: if campaign launches exceed 3/month across client book OR if a single client runs multi-phase rollouts that compound friction. When revisited, Google Ads API automation is higher-ROI than Meta Marketing API (Meta API requires App Review + Business verification + has worse error surface). Option A path: add `scripts/push_to_google_ads.py` that consumes the same 8 CSVs via `google-ads-python` SDK with `--dry-run` flag. Do NOT build until the scale trigger fires — building now would violate the "60%+ time building tools vs earning" pain point.**
- **[2026-04-16] [SKILL DESIGN] Evals schema drift corrected → Finding: `evals/evals.json` used `{skill, version, test_cases}` while every other skill uses `{skill_name, evals}` per the Level-5 standard in skill-architecture-standards.md. Zero blast radius today (no unified eval runner exists) but would break one the moment it's built. Action: renamed top-level keys (`skill` → `skill_name`, `test_cases` → `evals`), dropped `version` (not in the standard, no other skill carries it). All 5 test cases preserved byte-identical. Rule: every new skill's evals.json must match `{skill_name, evals}` before commit — treat schema drift as a CRITICAL validator finding the day a cross-skill validator exists.**
- **[2026-04-16] [Validator hardening] Meta Optimization Goal × Objective enum validation** → Finding: Meta silently rejects ad-set imports when Optimization Goal doesn't match the parent campaign's Objective (e.g. `OUTCOME_LEADS` + `LINK_CLICKS` → bulk import fails with vague error). Validator only checked char limits, required fields, status/creative-type enums — never this pairing. Rule: at AD_SET level, Optimization Goal must be in the valid set for the parent campaign's Objective. Action: added a 6-objective → valid-goals map (`OUTCOME_AWARENESS` / `_TRAFFIC` / `_ENGAGEMENT` / `_LEADS` / `_APP_PROMOTION` / `_SALES`) covering Marketing API 2024+ ODAX values. Two-pass implementation: first pass builds Campaign Name → Objective map from CAMPAIGN-level rows; second pass looks up the parent campaign for each AD_SET row and validates. Flags CRITICAL on mismatch with the valid-goal list in the error message, WARNING on unrecognized Objective (future-proofs the check against Meta adding new objectives).
- **[2026-04-26] [Google Ads Editor — Living Flow Yoga] Structured Snippet CSV format mismatch** → Finding: per-column format (`Value 1`, `Value 2`, ...) from `references/google-ads-editor-schema.md` failed import with "There are too few values for a structured snippet. Create at least 3" — Editor's current parser couldn't read the per-column values. Switched to single `Snippet Values` column with semicolon-delimited values (`Vinyasa Flow;Yin Yoga;Beginners Yoga;Yang to Yin`) — imported clean. → **Rule:** structured snippet CSVs should use `Snippet Values` (single column, `;`-delimited) NOT `Value 1`/`Value 2`/... per-column. Schema reference doc in this skill currently lists the per-column format — needs updating. Action: patch `references/google-ads-editor-schema.md` Section 7 + the campaign-setup skill's snippet-writer to emit the semicolon-delimited format by default.
- **[2026-04-26] [Google Ads policy — Wellness/Yoga clients] Health-condition keywords auto-rejected by Personalized Advertising Restrictions** → Finding: keyword `yoga for back pain sydney` rejected at Editor import with "health category not accepted." Google's restricted-categories policy auto-rejects keywords implying medical conditions, pain, mental-health diagnoses, fertility, weight loss, addiction. Affects every wellness/yoga/fitness/therapy/healthcare client. Other terms in this trap to pre-filter: `yoga for back pain`, `yoga for anxiety`, `yoga for depression`, `yoga for arthritis`, `yoga for fibromyalgia`, `yoga for weight loss`, `yoga for fertility`, `yoga for migraines`, `yoga for sciatica`, `yoga for insomnia`, `yoga for adhd`, `yoga for ptsd`. → **Rule:** when generating keyword sets for wellness / yoga / fitness / therapy / healthcare clients, pre-filter against Google's restricted-health-condition list. Reframe symptom-keywords into structural alternatives: "yoga for back pain" → "yoga for desk workers" / "mobility yoga"; "yoga for anxiety" → "yoga for stress" / "calming yoga"; "yoga for weight loss" → "yoga for fitness" / "body composition yoga". Generation-time fix is cheaper than post-import fix because rejected keyword propagates through ad-copy report + media plan + dashboard + creative brief CSV. Action candidate: add `references/restricted-keyword-categories.md` listing Google's sensitive categories with sector-specific reframing recipes; integrate as a Step 4 pre-filter in keyword CSV generation; could share the reference file with ad-copywriter + market-research skills since they generate keyword universes too.
- [2026-04-27] [Universal — applies to all skills] Same-Client Re-Run Rule landed in CLAUDE.md as a universal Always-Active section. Same-client/same-case re-runs overwrite outputs in place — no v1/v2/v3, no -DATE parallel filenames, no dated section headers preserving prior content. One file per role, current state only. Only `wiki/log.md` (by-design change log) and `wiki/briefs.md` (brief history with `[ACTIVE]`/`[SUPERSEDED]` markers) are append-only. **For this skill specifically:** outputs/campaign-setup/google-ads/*.csv, outputs/campaign-setup/meta-ads/*.csv, outputs/campaign-setup/pre-launch-checklist.md, outputs/campaign-setup/launch-runbook.md — all overwritten in place on re-run. **RULE:** if you find yourself about to create a new file for an output that has the same logical role as an existing one, stop and overwrite the existing file instead.
