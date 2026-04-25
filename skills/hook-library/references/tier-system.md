# Tier System

Hook patterns live in 3 tiers. Tier determines priority when post-writer / repurpose / case-study-generator picks a hook.

## Tier 1 — Promoted (winners)

**Definition:** Patterns that performance-review has confirmed consistently outperform baseline.

**Promotion criteria** (any one):
- 4+ consecutive HITs (top 10% of channel) in last 28 days
- 6+ HITs total in any 56-day window with 0 FLOPs
- Mayank manual promotion (with reason logged)

**Cap:** 8 per pillar. If you'd be the 9th, demote one Tier 1 first (`hook_lib.py demote <id>`).

**Use priority:** Top of post-writer's candidate list. First 2-3 candidates always Tier 1 if available.

**Demotion triggers:**
- 3+ FLOPs (bottom 10%) in last 21 days
- 4+ BELOWs in last 28 days
- Mayank manual demotion (e.g., "feels stale", "trend-research showed creator pivoted away from it")

## Tier 2 — Standard (tested baseline)

**Definition:** Default tier. The 35 initial Perplexity-research patterns + any additions over time. Reliable but not yet proven exceptional.

**Promotion to Tier 1:** Per criteria above.
**Demotion to Tier 3:** Rare. Only if pattern produces 5+ FLOPs in any 90-day window (signal that the pattern is no longer working in 2026).

**Use priority:** Default fallback when no Tier 1 candidates match the pillar+channel filter.

**Cap:** No cap — this is the broad library.

## Tier 3 — Experimental

**Definition:** Recently added patterns that haven't accumulated performance data yet.

**Sources:**
- Mayank manually added a new pattern (via post-writer reference edit + `sync-from-post-writer`)
- Claude observed a new hook in trend-research / peer-tracker output and proposed it
- A demoted Tier 1 pattern (after performance dropped — sometimes patterns return to Tier 2 / 3 for re-trial)

**Cap:** 5 per pillar. Too many simultaneous experiments dilutes signal in performance-review.

**Use priority:** Used sparingly by post-writer (max 1 of 3 candidate hooks should be Tier 3). Allows trial without dominating the candidate list.

**Promotion to Tier 2:** After 3 uses with no FLOPs (any bucket OK).
**Promotion to Tier 1:** Skip Tier 2 if pattern hits 4 consecutive HITs immediately.
**Demotion to "archived":** If pattern produces 2+ FLOPs in first 4 uses, mark `archived: true` (still in catalog but excluded from `list` filters by default).

## Tier transitions diagram

```
       (manual / claude propose)
              |
              v
       +--- Tier 3 ---+
       |  experimental |
       +-------+------+
               |
       3 uses, 0 FLOPs   2+ FLOPs in 4 uses
               |              |
               v              v
       +--- Tier 2 ---+    archived
       |   standard    |
       +-------+------+
               |
       4 consec HITs  5+ FLOPs in 90d
               |              |
               v              v
       +--- Tier 1 ---+    Tier 3 (re-trial)
       |   promoted    |
       +-------+------+
               |
       3+ FLOPs in 21d  4+ BELOWs in 28d
               |              |
               v              v
            Tier 2          Tier 2
```

## Data captured per tier change

Every promote / demote writes to `data/promotion-log.json`:

```json
{
  "pattern_id": "brutal-truth-text-post",
  "from_tier": 2,
  "to_tier": 1,
  "reason": "4 HITs in last 28d on LI: +220% vs baseline",
  "source": "performance-review",
  "timestamp": "2026-04-20T09:15:00+05:30",
  "performance_signal": {
    "hits_28d": 4,
    "flops_28d": 0,
    "channel": "linkedin",
    "pillar": "lp-craft"
  }
}
```

## Manual override always allowed

Mayank can promote / demote any pattern at any time with a reason. Override doesn't require performance evidence. Useful for:
- Promoting a pattern that "feels right" before it has data
- Demoting a pattern that's gone stale culturally (e.g., format started feeling cliché on LinkedIn)
- Experimenting with rotation by manually shuffling Tier 1 to keep variety

## Quarterly tier audit

Every 3 months, review:
1. Are Tier 1 patterns still actually winning? Pull last 90 days of performance-review data.
2. Are any Tier 2 patterns ready for promotion that performance-review missed?
3. Are Tier 3 experiments stalled (no performance signal after 90+ days)? Move back to Tier 2 or archive.
4. Are tier caps being respected? If Tier 1 has 9+ for a pillar, force-demote the lowest-recent-engagement one.
