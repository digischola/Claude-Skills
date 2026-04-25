# Scoring Rules (Baselines, Buckets, Suggestions)

Turns raw metrics into buckets (Hit / Above / Below / Flop) and generates promotion / deprecation suggestions after enough data accumulates.

## Baseline computation

Baseline is the **rolling 30-day median weighted_score per channel**.

```
baseline[channel] = median(weighted_score for entries where
    channel == channel
    AND recorded_at within last 30 days)
```

Separate baseline per channel (LinkedIn's 450 median ≠ X's 120 median). Never cross-compare.

## Baseline readiness modes

| Days of data per channel | Mode | Behavior |
|---|---|---|
| 0-20 days | **Collecting** | No bucketing. Report shows raw numbers only. "Collecting baseline (week N of 3)" banner. |
| 21-55 days | **Active, early** | Buckets applied. Suggestions NOT generated yet (too few pattern repeats). |
| 56+ days | **Active, mature** | Buckets + promotion/deprecation suggestions enabled. |

Rationale: with ~4 posts/week on LinkedIn, 56 days = ~32 posts. Enough to detect pattern-level signal.

## Bucketing algorithm

Within each channel, rank the last 30 days' weighted_scores. Assign buckets by percentile:

| Percentile (within channel) | Bucket | Weight in promotion analysis |
|---|---|---|
| Top 20% | HIT | +2 promotion points |
| 20-50% | ABOVE | +1 promotion point |
| 50-80% | BELOW | -1 promotion point |
| Bottom 20% | FLOP | -2 promotion points |

Edge cases:
- If a channel has <5 posts in the window, fall back to "raw numbers only" for that channel.
- If all posts have identical scores, bucket all as ABOVE (no ties in top).

## Pattern-level scoring

For each pattern dimension tracked (hook_category, voice_framework, transformation recipe, calendar slot), aggregate bucket points across posts:

```
pattern_score[Hook Category: Data] = sum of bucket points over all posts using Data hook
```

Example:
- Data hook used in 5 posts: 2 HIT (+4), 2 ABOVE (+2), 1 BELOW (-1) = net +5. Strong.
- Story hook used in 3 posts: 3 FLOP (-6). Weak.

## Promotion suggestion thresholds (Active, mature mode only)

Generate a promotion suggestion when:

| Pattern | Condition | Suggestion |
|---|---|---|
| Hook category | net score ≥ +6 AND ≥3 posts in 30d | "Promote Hook Category X to Tier 1 in hook-library.md" |
| Voice framework | net score ≥ +4 AND ≥3 posts in 30d | "Flag framework Y as consistently winning in voice-frameworks.md" |
| Transformation recipe | net score ≥ +3 AND ≥2 variant posts | "Mark recipe X→Y as Tier 1 in transformation-recipes.md" |
| Calendar slot | net score ≥ +4 AND ≥3 posts in the slot | "Reinforce slot in rotation-rules.md (winning slot)" |
| Pillar | net score ≥ +6 AND ≥4 posts | "This pillar is overperforming. Consider increasing its cadence share." |

Suggestions are NEVER auto-applied in v1. User reviews the weekly report and decides what to update. v2 candidate: auto-apply for signals >12 weeks of consistency.

## Deprecation suggestion thresholds

Generate a deprecation suggestion when:

| Pattern | Condition | Suggestion |
|---|---|---|
| Hook category | net score ≤ -4 AND ≥2 posts | "Consider deprecating Hook Category X in hook-library.md" |
| Voice framework | net score ≤ -3 AND ≥2 posts | "Framework Y is underperforming. Review." |
| Transformation recipe | net score ≤ -3 AND ≥2 variants | "Review recipe X→Y." |
| Pillar | net score ≤ -4 AND ≥3 posts | "Pillar Z is flat. Review content quality or pillar fit." |

## Computed flags in weekly report

Each post in the weekly report also gets flags based on context:

- `hook_overexposed` — same hook category used in ≥40% of last month's posts (user audience sees the same formula too often)
- `credential_saturation` — same credential anchored ≥2 times in last 30 days (violates cadence rule in post-writer credential-anchoring.md)
- `pillar_imbalance` — one pillar >60% of this week's posts
- `ai_theme_drift` — AI-themed posts dropped to 0 this week (brand positioning at risk)

## What the scorer does NOT do

- Does not normalize across platforms. LinkedIn's 200 comments ≠ X's 200 replies. Each channel is scored within itself.
- Does not weight by follower count (audience grows; baselines reset implicitly via rolling window).
- Does not penalize a low-impression post if engagement_rate is strong (small audience, high resonance = winning).
- Does not apply suggestions automatically. v1 is advisory.

## Manual overrides

User can flag a post `--exclude` to remove from scoring (e.g., a test post, a post that got an anomalous viral spike). The log keeps the record but excludes it from baseline computation.
