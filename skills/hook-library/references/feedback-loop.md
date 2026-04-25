# Feedback Loop — hook-library

## When to log a learning

Add a dated entry to SKILL.md "Learnings & Rules" when:

- A new tier transition rule is added (e.g., new auto-promotion threshold)
- A new category of patterns emerges (currently 8 — adding a 9th)
- A pattern caused unexpected behavior (e.g., consistently misclassified by performance-review)
- The sync-from-post-writer parser broke when post-writer changed its reference format
- A new downstream skill starts consuming hook-library
- Mayank manually overrides tier suggestions consistently → tune the auto-suggestion thresholds

## Format

```
- [YYYY-MM-DD] [CONTEXT TAG] Finding → Action.
```

Context tags:
- `[Initial build]`
- `[Tier]` — promotion / demotion logic
- `[Sync]` — sync-from-post-writer parser issues
- `[Cross-skill]` — interaction with post-writer / repurpose / case-study-generator / performance-review
- `[Catalog]` — adding / removing patterns
- `[Performance signal]` — auto-tier-suggest issues

## Cross-skill impact

When hook-library schema changes:
- `post-writer` — updates its query/fallback logic
- `repurpose` — updates its cross-channel queries
- `case-study-generator` — updates its category-specific queries
- `performance-review` — updates its tier-suggestion / mark-used calls

When tier definitions change (e.g., raising the auto-promotion threshold from 4 HITs to 6):
- Update `references/tier-system.md`
- Update `scripts/hook_lib.py` thresholds
- Surface the change in performance-review's next report so Mayank knows promotions will be rarer

## Quarterly review

Every 3 months:
1. Run `hook_lib.py stats` — counts per tier per pillar
2. Run `hook_lib.py promotion-log --limit 20` — see recent tier changes
3. Audit Tier 1: are all 8 (max per pillar) still earning their slot? Pull recent performance, force-demote any laggards
4. Audit Tier 3: how long have experiments been there? Move stalled ones to Tier 2 or archive
5. Sync from post-writer to catch any new manual additions
6. Export to post-writer's reference file (regenerate the human-friendly mirror)

## Eval candidates

Add a test case to `evals/evals.json` when:

- A new sync-from-post-writer parser case is encountered (new table format)
- A new tier transition rule is added
- A new CLI subcommand lands
- A new pattern field is added to the schema

Tests should run on fixture `data/hooks.json` files (not the live one) to keep the catalog stable.
