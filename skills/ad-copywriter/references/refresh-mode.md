# Refresh Mode — Ad Copy Rotation After Fatigue

Refresh Mode is the third operating mode of ad-copywriter (alongside Standalone and Downstream modes). It's triggered when `post-launch-optimization` flags creative fatigue and produces a `rotation-brief.json`. The goal is drop-in replacement copy that keeps brand/framework/persona stable while changing the fatigued angle, hook, or proof element.

---

## When Refresh Mode fires

Input detected: a file matching `{client}/_engine/working/*-rotation-brief.json` in the client folder.

Typical trigger chain:
1. post-launch-optimization Layer 4 detects fatigue on an ad (frequency >3.5, CTR decline >30%, CPA increase >50%)
2. Layer 10 elevates "refresh fatigued creative" into the top-5 action list
3. Skill emits `{client}-rotation-brief.json` alongside the report
4. Analyst runs ad-copywriter → it reads the rotation brief → enters Refresh Mode

---

## `rotation-brief.json` schema

```json
{
  "client_name": "Thrive Retreats",
  "analysis_date": "2026-04-16",
  "source_report": "Thrive-optimization-2026-04-16.md",
  "source_creative_brief": "Thrive-creative-brief.json",
  "refresh_urgency": "URGENT",
  "fatigued_creatives": [
    {
      "ad_name": "Emily_Teacher_Training_Hero_v1",
      "platform": "meta",
      "campaign": "TT Prospecting",
      "ad_set": "Prospecting — Wellness Curious",
      "format": "SINGLE_IMAGE",
      "persona": "Wellness-curious F 35-50",
      "framework_used": "BAB",
      "fatigue_signals": {
        "frequency": 3.7,
        "ctr_decline_pct": 42,
        "cpa_increase_pct": 68,
        "impressions_lifetime": 128400,
        "days_live": 54
      },
      "original_copy": {
        "primary_text": "Turn your yoga practice into a career. Our 200-hour program trains you to lead transformational classes …",
        "headline": "Teach Yoga. Full Time.",
        "description": "Next cohort Jan 2027 — early-bird pricing closes soon.",
        "cta": "Apply Now"
      },
      "keep": ["framework: BAB", "persona", "cta_type: Apply", "brand_voice"],
      "change": ["hook_angle", "imagery_direction", "lead_proof_element"],
      "new_angles_to_try": [
        "specificity ladder — name the exact outcome",
        "authority / social proof stack — Yoga Alliance + alumni count",
        "objection-inversion — 'I'm not flexible enough' reframe"
      ],
      "rationale": "Emily face is saturated for this audience. Same offer, same persona, but new visual POV and hook angle."
    }
  ],
  "strategy_guardrails": {
    "respect_character_limits": true,
    "preserve_cta_target_url": true,
    "ab_test_against_original": true,
    "min_new_variants_per_fatigued": 2
  }
}
```

---

## Refresh Mode workflow (overrides to the standard Steps 1-8)

### Step 1 — Mode detection (overridden)
- Detect `*-rotation-brief.json` in `{client}/_engine/working/` → Refresh Mode
- Load the rotation brief AND the original `*-creative-brief.json` AND the wiki
- Skip the 6-question standalone intake entirely
- State clearly in the output: "Refresh Mode — 3 fatigued creatives being rotated"

### Step 2 — Skipped
Refresh Mode has all the context it needs from the rotation brief + creative brief + wiki.

### Step 3 — Load specs + rotation context
Load `copywriting-frameworks.md`, `creative-research.md`, `image-prompt-patterns.md` as usual, PLUS the rotation brief's `keep` / `change` arrays per fatigued creative.

### Step 4 — Generate replacement copy (modified)
For each fatigued creative in the brief:
- Hold everything in the `keep` list **constant** (framework, persona, CTA type, brand voice)
- Change everything in the `change` list (hook, imagery direction, proof element, etc.)
- Generate **at least** `min_new_variants_per_fatigued` variants (default 2)
- Each variant gets a clear `[REFRESH]` source label (distinct from `[BRIEF]` / `[GENERATED]` / `[ADAPTED]`)
- Name new ads with a version suffix: `Emily_Teacher_Training_Hero_v2`, `_v3`
- Include a brief "What changed and why" block for each new variant — the analyst needs to explain the rotation to the client

### Step 5 — Platform CSVs
Produce the same Google + Meta CSVs as standard flow, but **only for the replacement ads** (not a full campaign rewrite). Include both the new variants AND the original for A/B test pairing per `strategy_guardrails.ab_test_against_original`.

### Step 6 — Image prompts
Respect `image_gen_prompt_prefix` from the original creative brief (brand consistency is non-negotiable in refresh mode). Apply new `change` directions to the scene/subject/composition, not the style. Flag each new prompt with a `{rotation of: <original_ad_name>}` tag for traceability.

### Step 7 — Video storyboards
Only if the fatigued creative was video. Otherwise skip.

### Step 8 — Validate & update wiki
- Validator runs against refreshed outputs + checks `[REFRESH]` label present on every new variant
- Wiki log entry: `REFRESH 3 creatives rotated in Ad Set Prospecting-Wellness (triggered by optimization #4, 2026-04-16)`
- Flag downstream for campaign-setup: "Load the refreshed CSV segment and upsert the new ads via Meta bulk import / Google Ads Editor."

---

## Output differences from Standalone/Downstream modes

| Artifact | Standalone / Downstream | Refresh Mode |
|----------|------------------------|--------------|
| Ad copy report | full campaign architecture | only the refreshed ads + rationale section |
| CSVs | all campaigns, all ads | only replacement rows (incremental) |
| Image prompts | all personas × formats | only rotated placements |
| Video storyboards | all video ads in plan | only refreshed video ads |
| Wiki entry | full handoff block | `REFRESH` delta entry |
| Source labels | `[BRIEF] / [GENERATED] / [ADAPTED]` | `[REFRESH]` on all new variants |

---

## Why this exists

Creative fatigue is real (4 impressions per user is the industry-cited threshold for noticeable decline on Meta). Without an automated rotation loop, the analyst either (a) manually rewrites copy from scratch, losing framework/brand consistency, or (b) delays rotation and CPA creeps up silently. Refresh Mode closes the loop: fatigue signal → structured handoff → drop-in replacement copy — with the original preserved as the A/B control so the rotation's impact is measurable next cycle.
