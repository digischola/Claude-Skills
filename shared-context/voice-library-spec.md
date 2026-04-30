# Voice Library — Universal Spec

Cross-skill bedrock for client copy/voice consistency. Lives at `{client}/_engine/wiki/voice-library.json` (single-program) or `{client-root}/_engine/wiki/voice-library.json` (multi-program shared brand voice).

## Why this exists

Client copy across ads + landing pages + visuals + video VOs was being freshly-invented per skill-run, drifting from proven-winner voice patterns. The structural cause: skills had **visual reference manifests** (PNGs of past creatives) but no **voice reference manifests** (parsed copy patterns from past creatives). Voice-library.json closes that gap.

Read the file before generating any copy. Validators across skills enforce compliance.

## Schema

```json
{
  "schema_version": "1.0",
  "client": "<Client Name>",
  "scope": "shared | program-specific",
  "extracted_from": [
    {
      "source": "<campaign / page / post identifier>",
      "performance": "<topline metric: CPL / CPA / CTR / engagement>",
      "extraction_date": "YYYY-MM-DD",
      "method": "windsor_pull | meta_ads_library | manual_paste | screenshot_ocr"
    }
  ],
  "headline_patterns": [
    {
      "id": "<snake_case>",
      "name": "<human label>",
      "structure": "<formula with {placeholders}>",
      "examples": ["<verbatim example 1>", "<verbatim example 2>"],
      "max_words": 8,
      "tone_tags": ["calm", "devotional", "scroll-stop", "objection-handling", "..."],
      "best_for_audience_tier": ["cold", "lookalike", "warm", "retention"]
    }
  ],
  "trust_line_template": {
    "format": "<token order: e.g. {day} · {time} · {modifier?} · {location?}>",
    "examples": ["<verbatim>", "..."],
    "separator": "·",
    "separator_color_hex": "<from brand-config palette>",
    "rules": [
      "always_include_day_for_event_campaigns",
      "always_include_time_for_event_campaigns",
      "include_in_english_qualifier_for_cold_cultural_audiences",
      "no_brand_fluff_phrases"
    ],
    "forbidden_in_trust_line": ["<phrases like 'world-class', 'transformative', stat-fluff>"]
  },
  "cta_verb_noun_pairs": [
    {
      "verb": "Reserve",
      "nouns": ["a plate", "a seat", "a class spot", "your spot"],
      "context": "RSVP / event booking",
      "object_specificity_rule": "noun must match the visual subject of the card"
    }
  ],
  "voice_rules": {
    "max_headline_words": 8,
    "max_subhead_words": 12,
    "tone": ["conversational", "contracted", "english-direct"],
    "forbidden_phrases": ["world-class", "transformative", "premier", "renowned", "best-in-class"],
    "punctuation_style": "declarative period; no em-dash (universal kernel rule)",
    "language_handling": "<client-specific: e.g. Sanskrit transliterated only, no devanagari, no ॐ>"
  },
  "campaign_type_anchor_pattern": {
    "event": {
      "anchor_field": "event_facts.canonical_string",
      "must_appear_on_every_variant": true,
      "drift_tolerance": 0.8,
      "rationale": "Cold scrollers see ONE variant; event-fact bedrock has to land on every card."
    },
    "evergreen": {
      "anchor_field": "core_offer_facts.canonical_string",
      "must_appear_on_every_variant": false,
      "drift_tolerance": 0.6
    },
    "promotional": {
      "anchor_field": "promo_facts.canonical_string (deadline + discount)",
      "must_appear_on_every_variant": true,
      "drift_tolerance": 0.9
    }
  }
}
```

## Pattern vocabulary (extend per client)

Common headline patterns observed across proven winners. Voice-library extraction should tag matching patterns + invent new ones when they don't fit.

| Pattern ID | Structure | Example | Best for |
|---|---|---|---|
| `parallel_verb_action` | `{Verb}ed with {emotion}. {Verb}ed with {emotion}.` | "Prepared with care. Served with love." | Sensory/devotional cards |
| `objection_reassurance` | `{Negation}? {Reassurance}.` | "Never been to a temple? That's exactly who this is for." | Cold prospecting / newcomer |
| `constancy_claim` | `{Same/Every} {noun}. {Same/Every} {noun}.` | "Same warm room. Every weekend." | Retention / recurring program |
| `direct_specifier` | `{Day} {time}.` + `{Action}.` | "Saturday 5pm. Bring the kids." | Lookalike / mid-funnel |
| `before_after_bridge` | `{Status quo}. {Shift}. {Outcome}.` | "Stressed Monday. Settled by Sunday. That's the retreat." | Wellness / transformation |
| `unit_economics_proof` | `{Before-stat} → {After-stat}. {Period}.` | "$3.20 CPL → $0.71. Eight days." | B2B / SaaS / Digischola self-brand |

**Authoring discipline (validator-enforced):** the skill picks ONE pattern per creative based on `voice_anchor.pattern_id` in creative-brief.json. Invented headlines that don't match any pattern → CRITICAL.

## Cross-skill consumer contract

| Skill | Consumes | Produces |
|---|---|---|
| business-analysis | (sources: ad account history, screenshots, manual paste) | `voice-library.json` (extraction) |
| paid-media-strategy | `voice-library.json` | `creative-brief.json` with `event_facts.canonical_string` + per-creative `voice_anchor.pattern_id` + `cta_verb_noun_pair` |
| ad-copywriter | `voice-library.json` + `creative-brief.json` | ad copy + image-prompt `exact_copy` blocks compliant with anchor pattern; validator enforces |
| landing-page-builder | `voice-library.json` + `creative-brief.json` | LP headlines + subheads + CTA buttons matching same patterns |
| visual-generator / ai-video-generator | `voice-library.json` | on-screen text + VO scripts matching same voice |

## Validator rules (required across skills)

Every skill that generates copy MUST validate against voice-library.json:

1. **Event-fact anchor consistency** (event-type campaigns): every output variant's trust-line / equivalent must contain `event_facts.canonical_string` with ≥80% string similarity. CRITICAL on miss.
2. **Headline cadence**: heading word-count ≤ `voice_rules.max_headline_words`; doesn't contain any `voice_rules.forbidden_phrases`. CRITICAL on violation.
3. **CTA semantic-specificity**: cta_pill must match a verb+noun pair from `cta_verb_noun_pairs`. WARNING if generic CTA appears on >40% of variants in a single campaign; CRITICAL if generic CTA on a designated CTA-card.
4. **Pattern-anchor compliance** (where `voice_anchor.pattern_id` is set in brief): generated headline must match the pattern's structure (regex-tested). WARNING on mismatch (some creative latitude allowed).
5. **Forbidden language**: `voice_rules.forbidden_phrases` + `voice_rules.language_handling` prohibitions checked across all generated copy. CRITICAL on hit.

## Extraction protocol (business-analysis Step 7)

The protocol has TWO modes depending on whether the client has historic creative data.

### MODE A — Established client (has paid history OR proven organic content)

Sources, in priority order:
1. **Windsor.ai pull** — top 3 by lowest CPL (paid) or highest CTR (organic) over last 90 days. Extract ad creative copy via Meta Ad Library URL or attached screenshots.
2. **Meta Ad Library scrape** — Chrome MCP → ad library → page handle → top performing ads → screenshot + OCR or copy-paste copy.
3. **Manual paste from analyst** — analyst pastes 3-5 reference creatives' copy into the extraction script.
4. **Reference image manifest** — when creatives exist as PNGs in `_engine/references/images/`, OCR the visible text and parse pattern.

Output: `voice-library.json` with `bootstrapping: false`, `extracted_from` array populated with sources + performance metadata.

### MODE B — New client / no historic data (BOOTSTRAP)

Three-tier bootstrap. All three tiers run; results stack with founder voice winning conflicts.

**Tier 1 — Sector-default voice seed.**
Load `business-analysis/references/voice-library-sector-seeds/{sector}.json` matching the client's business type (sectors mirror existing sector-lenses: wellness-retreats, temple-cultural-org, local-services, restaurant-food-service, saas-b2b, professional-services). Each seed carries 4-6 headline patterns proven across the sector + a sector-tuned trust-line template + CTA verb-noun starter set + sector-specific forbidden phrases. If no matching sector seed exists, use `_default.json` (universal floor).

**Tier 2 — Founder/owner voice capture.**
During business-analysis Step 5 (Client Intake), ask three additional voice-capture questions via AskUserQuestion. Log answers verbatim in voice-library.json under `founder_voice_samples`:

1. *"Describe your service to a friend in two short sentences."* → captures natural headline cadence + conversational rhythm
2. *"What's the most common objection or hesitation new customers raise, and how do you answer it?"* → captures `objection_reassurance` pattern + reassurance phrasing
3. *"When someone signs up / books / buys, what do you want them to feel in that moment?"* → captures emotional register + CTA tone

The skill parses these samples, extracts 1-2 patterns per answer, tags them `source: founder_voice`, and merges with sector seed. **Founder voice overrides sector seed on conflict.**

**Tier 3 — Competitor voice reference (anti-pattern).**
Pull top 3 competitor names from `_engine/wiki/competitors.md` (or strategy.md). For each, attempt to extract headline samples (Meta Ad Library if accessible; landing page hero copy via WebFetch otherwise). Save under `competitor_voice_reference` with explicit `usage: differentiate_from` tag. **This is NOT for imitation** — it's a "don't sound like these" reference so the skill can actively avoid sounding generic-sector or copying competitor positioning.

**Output:** `voice-library.json` with `bootstrapping: true`, `extracted_from` array showing which tiers contributed, and a `refresh_trigger` block defining when to flip `bootstrapping` to false.

### Bootstrap → Mature transition

`voice-library.json` carries `bootstrapping: true` until ANY of these triggers fire (post-launch-optimization checks weekly):

- 50+ leads OR conversions logged on a campaign that uses voice-library patterns
- ≥500 link clicks OR ≥1000 LPVs across any campaign
- 30 days continuous live spend
- Manual flip by analyst

When triggered: post-launch-optimization auto-suggests pattern updates from live performance (e.g. "Pattern X drove $0.71 CPL across 222 leads — promote to verified-winner"). Analyst confirms; sector-seed patterns that didn't get used get demoted; new patterns from live data get added. Flag flips to `bootstrapping: false`. Library matures with the client.

## When voice-library.json updates

- **Initial extraction** at business-analysis client onboarding (Step 7).
- **Refresh** after every `paid-media-strategy` re-run when post-launch-optimization shows new winners (auto-suggested pattern promotions).
- **Manual edit** when client provides new brand voice guide / hires new designer / relaunches.
- **Same-Client Re-Run Rule** applies: overwrite in place, no v1/v2 files. `_engine/wiki/log.md` records the change.

## Failure modes the bedrock prevents

1. **Voice drift across carousel cards** (5 cards, 5 different trust-line strings) — caught by event-fact anchor consistency check.
2. **Audience-segmented copy that loses event facts** — caught by mandatory anchor presence on every variant.
3. **Generic CTAs reused across cards regardless of card visual** — caught by CTA semantic-specificity rule.
4. **Fresh-invented headlines per run that drift from proven winners** — caught by pattern-anchor compliance.
5. **Brand-fluff phrases creeping into trust-lines** ("250+ devotees gather every weekend" instead of "Sat or Sun · 5 to 7:30 PM") — caught by `forbidden_in_trust_line` list.

## Boundary against `copywriting-rules.md` (kernel)

- `copywriting-rules.md` (kernel-locked) = universal rules across ALL writing (no em-dashes, etc).
- `voice-library.json` = client-specific patterns extracted from proven winners.
- Both apply. Kernel rules win on conflict (kernel rules are universal floor).
