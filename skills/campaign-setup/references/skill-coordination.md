# Skill Coordination — campaign-setup

Describes how `campaign-setup` consumes upstream skill outputs and prepares data for downstream skills.

---

## Upstream Inputs

### 1. `market-research` → `{client}/_engine/wiki/strategy.md`
What this skill reads:
- Buyer personas (used for audience naming, messaging tone)
- Keywords (baseline for Google keyword expansion)
- Benchmarks (CPC, CPL, CTR) for sanity-checking bid strategies
- Positioning angle (used in negative-keyword planning)

Required fields in strategy.md: buyer_personas, keyword_seeds, cpl_benchmark, positioning.

### 2. `paid-media-strategy` → `{client}/_engine/working/paid-media-strategy.md` and `{client}/_engine/working/media-plan.csv` (legacy fallback: `*-paid-media-strategy.md`, `*-media-plan.csv`)
What this skill reads:
- Campaign architecture (how many campaigns, how split)
- Budget allocation (per campaign / per platform / per phase)
- Bid strategy choice
- Location targeting
- Conversion events
- Phase of rollout (Phase 1 / 2 / 3)

Required columns in media-plan.csv:
`Platform, Campaign Name, Campaign Type, Objective, Daily Budget, Bid Strategy, Target CPA, Locations, Languages, Audience, Phase, Start Date, End Date`

### 3. `ad-copywriter` → `google-ads.csv`, `meta-ads.csv`, image prompts, video storyboards (legacy fallback: `*-google-ads.csv`, `*-meta-ads.csv`)
What this skill reads:
- Google: RSAs with 15 headlines + 4 descriptions per ad group
- Meta: primary text + headline + description per ad variant
- Asset list: image prompts and video storyboards → maps to creative upload manifest

Required columns in google-ads.csv:
`Campaign, Ad Group, Headline 1..15, Description 1..4, Path 1, Path 2, Final URL`

Required columns in meta-ads.csv:
`Campaign, Ad Set, Ad Name, Creative Type, Body, Title, Link Description, Link, CTA, Asset Filename`

### 4. `landing-page-builder` → `page-spec.json` + HTML prototype (legacy fallback: `*-page-spec.json`)
What this skill reads:
- `page_url_slug` → populates Final URL
- `analytics.conversion_events[].event` → maps to Google conversion actions and Meta custom events
- `brand.accent_color` → only for reference, not used in CSVs
- `performance_targets` → reference for launch-runbook landing-page check

---

## Input Validation Before Building

Before generating CSVs, validate upstream deliverables:
1. `paid-media-strategy` exists for every platform in scope (Google, Meta)
2. `ad-copywriter` has produced RSAs/ads for every campaign in media plan
3. Ad group names in `google-ads.csv` match ad group names derivable from `media-plan.csv`
4. All Final URLs in ads resolve to landing pages built by `landing-page-builder` OR are explicitly flagged `<REPLACE_ME_LANDING_URL>`

If any validation fails, fall back to standalone mode with guided questions and flag the missing upstream in the output README.

---

## Downstream Outputs

### 1. `post-launch-optimization` consumes:
- Campaign names, ad group names, ad names from the generated CSVs (for filtering live data in Windsor.ai MCP)
- Media plan targets (for benchmarking actuals vs plan)
- Pre-launch-checklist.md (for reference — what was expected at launch)
- Conversion action names (for attribution matching)

What to flag downstream:
- Campaign family (e.g., `{REGION}_{BRAND}_*`) so post-launch-optimization can scope reports
- Total campaign count and creative count (for baseline ratio: spend per ad, spend per keyword)
- Any `<REPLACE_ME>` tokens still unresolved at launch

### 2. Wiki log entry format
After completing the skill, write to `{client}/_engine/wiki/log.md`:

```
## {{DATE}}
- **CAMPAIGN-SETUP COMPLETE** Generated bulk-import CSVs for {{PLATFORMS}}. 
  {{N_CAMPAIGNS}} campaigns, {{N_AD_GROUPS}} ad groups/ad sets, 
  {{N_ADS}} ads total. {{N_EXTENSIONS}} extensions. 
  Pre-launch checklist + launch runbook delivered. 
  Validator: {{N_CRITICAL}} critical, {{N_WARNINGS}} warnings. 
  {{N_PLACEHOLDERS}} placeholder tokens flagged for client input before launch.
```

### 3. Handoff to client
The bundle folder structure (at `{client}/campaign-setup/`, sitting at the client/program folder root as a presentable) is the client handoff. It should be:
- Self-contained (no external references required)
- Versioned (include `generated_at` timestamp in README)
- Auditable (each CSV traceable to an upstream source field)

---

## Failure Handling Matrix

| Upstream missing | Action |
|---|---|
| No market-research | Ask user for business type / personas inline |
| No paid-media-strategy | Run standalone — ask 12-question intake covering campaign architecture |
| No ad-copywriter (required for ads) | BLOCK — cannot produce RSAs/ads CSVs. Direct user to run ad-copywriter first |
| No landing-page-builder | Accept URL from user, flag if no page-spec.json for analytics events |
| Ad-copywriter has wrong ad group names | Warn, auto-suggest mapping based on closest string match, require user confirmation |
| Media plan has unsupported campaign type (PMax, Discovery) | Generate best-effort CSV with WARNING header in file, document manual steps in runbook |

---

## Standalone Mode Inputs (fallback when no upstream)

If run without upstream deliverables, ask the user the following before generating anything:

1. Business name and website URL
2. Target location(s)
3. Primary offer / product / service
4. Price point or deal size
5. Platforms (Google, Meta, both)
6. Monthly budget (total)
7. Campaign objective(s)
8. Landing page URL(s)
9. Conversion events (already set up in Google Ads / Meta?)
10. Existing audiences (names)
11. Known negative keywords
12. Launch deadline

Outputs are generated with heavy `<REPLACE_ME>` annotation and a prominent STANDALONE MODE header warning the analyst to validate strategy assumptions manually.
