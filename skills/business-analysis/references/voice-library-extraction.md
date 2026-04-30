# Voice Library Extraction Protocol

Step 7 of business-analysis. Produces `{client}/_engine/wiki/voice-library.json` (single-program) or `{client-root}/_engine/wiki/voice-library.json` (multi-program shared brand voice).

Read `~/.claude/shared-context/voice-library-spec.md` first for schema + cross-skill consumer contract. This file is the **how-to-extract** protocol.

## Mode detection

Run `scripts/extract_voice_library.py --detect <client_folder>` first. The script returns one of:

- **`MODE_A_ESTABLISHED`** — client has at least one of: Windsor.ai connected with paid history; Meta Ads Library shows >3 active or recent ads; analyst has reference creatives stored in `_engine/references/images/`. Run extraction from those sources.
- **`MODE_B_BOOTSTRAP`** — none of the above. Run three-tier bootstrap.

## MODE A — Established client

Sources, in priority order:

### 1. Windsor.ai pull (preferred when connected)
Use `scripts/extract_voice_library.py --windsor --client <id> --top-n 3 --metric cpl_lowest --window 90d`.
The script:
- Pulls top-3 ads by performance (lowest CPL for paid lead gen, highest CTR for awareness, highest ROAS for ecommerce)
- For each ad, attempts to fetch creative copy via Meta Ad Library URL when available
- If copy unavailable, prompts analyst for screenshot + OCR or manual paste

### 2. Meta Ads Library scrape (when Windsor.ai unavailable but page-handle exists)
Use Chrome MCP: `facebook.com/ads/library/?active_status=all&q={page_handle}&country=ALL`.
Capture top 5 active or recent ads → screenshot → OCR or copy-paste copy → feed into extraction script.

### 3. Manual paste (analyst supplies)
`scripts/extract_voice_library.py --paste` opens a multiline prompt. Analyst pastes 3-5 reference creatives' copy in the format:

```
=== CREATIVE 1 ===
performance: $0.71 CPL, 222 leads, 5.56% CTR
headline: Prepared with care. Served with love.
subhead:
trust_line: Free Prasadam · Sat or Sun, 7:15 PM
cta: Reserve a plate
=== CREATIVE 2 ===
...
```

### 4. Reference image OCR
When `_engine/references/images/manifest.json` lists past-creative PNGs, the script can OCR visible text via local OCR (tesseract) or via Chrome MCP screenshot upload. Lower fidelity than analyst paste — use as fallback.

### Pattern induction
Once 3-5 creatives are captured, the script analyses copy across all samples and inducts patterns:
- Group headlines by syntactic structure (parallel-clause / question-answer / specifier-action / etc.)
- Extract the trust-line template by tokenising day / time / qualifier / location
- Catalogue verb+noun pairs in CTAs
- Flag any forbidden_phrases that appeared (mark for explicit ban) AND any phrases that recurred (mark for canonical preference)

Output written to `voice-library.json` with `bootstrapping: false`.

## MODE B — Bootstrap (new client)

Three tiers. All run; results stack with founder voice winning conflicts.

### Tier 1 — Sector-default seed
Read `business-analysis/references/voice-library-sector-seeds/{sector}.json` matching the client's primary sector (per `business.md` + sector-lens). If no exact match, load `_default.json`.

The seed populates `headline_patterns`, `trust_line_template`, `cta_verb_noun_pairs`, `voice_rules.forbidden_phrases`, and `campaign_type_anchor_pattern` as starting values.

### Tier 2 — Founder/owner voice intake
**Mandatory** when in MODE_B. Use AskUserQuestion to ask three questions ONE AT A TIME (per business-analysis Step 5 conventions):

1. **Service description in two sentences** — *"Describe your service to a friend in two short sentences. Use your normal voice — exactly how you'd say it out loud."*
2. **Top objection + reassurance** — *"What's the most common hesitation or objection a new customer raises? And how do you typically answer it?"*
3. **Conversion-moment feeling** — *"When someone signs up, books, or buys, what's the feeling you want them to have in that moment?"*

Save answers verbatim under `founder_voice_samples` in voice-library.json. Then the script:
- Parses Q1's two sentences as a template for the headline cadence (length, contractions, conversational rhythm). Adds as a custom pattern `id: founder_voice_natural`.
- Parses Q2 as the canonical objection_reassurance pair. Adds the literal Q2 answer as an example under that pattern.
- Parses Q3 to derive emotional register tags + CTA tone direction.

**Founder voice overrides sector seed on conflict** — if founder uses "premier" but sector seed forbids it, founder wins (it's their voice, our job is to capture not correct). Flag the conflict in the voice-library.json `lineage` block for analyst review.

### Tier 3 — Competitor anti-pattern reference
Pull top 3 competitor names from `_engine/wiki/competitors.md` or `strategy.md`. For each:
- If Meta Ads Library accessible → grab top 1-2 ad headlines per competitor
- Else → WebFetch competitor homepage → extract hero headline + tagline

Save under `competitor_voice_reference` with `usage: differentiate_from`. Include a `differentiation_rule` line: *"Voice patterns above are deliberately different from the competitor voice samples. If a generated headline could plausibly appear on a competitor's site without changes, it has failed differentiation."*

### Output
`voice-library.json` written with:
- `bootstrapping: true`
- `extracted_from`: array showing which tiers contributed (sector_seed + founder_intake + competitor_scan)
- `refresh_trigger`: auto-review after 50+ leads OR ≥500 link clicks OR 30 days live spend

## Mode B → Mode A transition

`post-launch-optimization` checks `bootstrapping: true` weekly. When a refresh trigger fires:
- Pull live performance data (Windsor.ai or manual)
- Suggest pattern updates: `pattern X drove $Y CPL — promote to verified`; `pattern Z was unused — demote to archive`
- Analyst confirms via AskUserQuestion → script updates voice-library.json → flips `bootstrapping: false`

## Quality bar

A voice-library.json passes the bar when it has ALL of:
- ≥3 headline_patterns with examples populated
- trust_line_template with `format` + ≥2 examples
- ≥2 cta_verb_noun_pairs
- voice_rules.forbidden_phrases populated (universal floor + sector-specific)
- campaign_type_anchor_pattern set for at least the campaign types the client runs

If any are missing, business-analysis Step 7 fails and asks analyst to provide more reference data OR to use BOOTSTRAP mode tier 2 to fill the gaps.

## Cross-skill handoff

Once written, voice-library.json is consumed by:
- **paid-media-strategy** — populates `event_facts.canonical_string` + per-creative `voice_anchor.pattern_id` + `cta_verb_noun_pair` in creative-brief.json
- **ad-copywriter** — uses anchor patterns to author headlines/subheads/CTAs; validator enforces compliance
- **landing-page-builder** — uses same patterns for LP hero copy, section headers, button text
- **visual-generator / ai-video-generator** — uses same patterns for on-screen text + VO scripts

Update `_engine/wiki/log.md` with the extraction entry. Flag downstream skills.

## Re-extraction triggers

Re-run Step 7 (overwriting voice-library.json in place per Same-Client Re-Run Rule) when:
- Client provides new brand voice guide
- Performance review shows the bootstrapping flag should be flipped
- A new product line / sector launches under the same brand
- An audit reveals voice drift in shipped creatives

Never create voice-library-v2.json. The wiki log records the change history.
