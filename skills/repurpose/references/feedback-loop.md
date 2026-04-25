# Feedback Loop (repurpose)

Per CLAUDE.md Mandatory Session Close Protocol. Entries go in the `## Learnings & Rules` section of SKILL.md.

## What to capture

**Always capture:**
- Source → target pairs the user rewrote heavily (signal that transformation-recipes.md recipe needs tightening)
- Hook adaptations that the user reverted (hook should have been preserved verbatim)
- Channel variants that consistently failed validation on the same rule
- Transformation recipes that produced drafts shorter than channel sweet-spot (too aggressive compression)

**Skip:**
- One-off per-post tweaks
- Personal preference drifts without a rule implication

## Context tags

- `[Recipe]` — transformation-recipes.md adjustment
- `[Hook]` — hook-preservation.md edge case
- `[Channel]` — a specific channel-format combination issue
- `[Validator]` — ran into a post-writer validator gate (cross-skill reference)
- `[Policy]` — Conservative naming or Restrained emoji edge case in a variant

## When a learning triggers a reference update

Apply the 7+3 rule:
1. Update the affected recipe in transformation-recipes.md OR rule in hook-preservation.md
2. Add learning to SKILL.md with concrete before/after
3. If the issue affects post-writer references too (e.g., a hook pattern that only works on LI, not X), flag for cross-skill update

## Integration with performance-review

When `performance-review` ships, it will identify which repurpose variants converted (clicks, saves, comments) vs. which flopped. That data feeds:
- Transformation recipes that consistently produce winners → promote to "Tier 1" status
- Recipes that consistently underperform their source → rewrite or deprecate
- Channel-specific adaptations that the audience liked → codify

Until performance-review ships, this loop runs on user feedback alone.
