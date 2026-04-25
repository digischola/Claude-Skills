# Promotion Rules (How to Update Other Skills' References)

When a pattern crosses the threshold in `scoring-rules.md`, the weekly report generates a suggestion. This file specifies exactly what each suggestion translates into in terms of file edits.

**v1 is ADVISORY only.** The weekly report lists suggestions. The user opens the referenced file and applies the edit manually. v2 adds auto-apply after 12+ weeks of consistent signal.

## Promotion format

Each suggestion in the weekly report has this shape:

```
SUGGESTION [{type}]:
  Target file: {path}
  Edit: {specific before/after}
  Evidence: {data backing the suggestion — X posts, Y bucket points, N days}
  Review reason: {why this pattern matters}
```

## Target-file mapping

| Pattern Type | Target file | Edit action |
|---|---|---|
| Hook category promotion | `post-writer/references/hook-library.md` | Add "Tier 1" label next to the hook row (or move row under a "## Tier 1 (proven winners)" section) |
| Hook category deprecation | `post-writer/references/hook-library.md` | Strike-through the row with a note (e.g., `~~[row]~~ (deprecated 2026-WXX: 3 flops in 30d)`) or remove |
| Voice framework win | `post-writer/references/voice-frameworks.md` | Add performance note under the framework section (e.g., "Performance note 2026-WXX: net +6 over 4 uses") |
| Voice framework underperformer | same | Add review note (e.g., "Performance note 2026-WXX: net -3 — review content-framework fit") |
| Transformation recipe win | `repurpose/references/transformation-recipes.md` | Add "Tier 1 (verified by performance-review)" to the recipe header |
| Calendar slot win | `content-calendar/references/rotation-rules.md` | Add performance note under the relevant slot |
| Pillar imbalance | `brand/channel-playbook.md` | Suggest cadence adjustment (more / less / redistribute) |

## Cross-skill updates always use the 7+3 rule

When the user applies a promotion, they must:
1. Update the target reference file (edit above)
2. Write a learning in the target skill's SKILL.md Learnings & Rules (date + context)
3. Update any affected wiki file if applicable (e.g., channel-playbook.md if cadence changed)

The weekly report reminds the user of this protocol next to each suggestion.

## Suggestion priority

Suggestions are ranked in the weekly report by confidence:

| Priority | Criteria |
|---|---|
| P1 — Strong | ≥4 posts, net score magnitude ≥+6 or ≤-4, ≥30 days of data |
| P2 — Medium | ≥3 posts, net score ≥+4 or ≤-3, ≥21 days |
| P3 — Weak | ≥2 posts, at threshold |

User should apply P1 suggestions immediately. P2 after a cross-check. P3 only if the pattern is already obvious.

## Deprecation handling

Deprecating a hook or framework is a bigger move than promoting. Rules:

- Never deprecate based on <3 posts. Small samples lie.
- Never deprecate a hook that has zero other coverage for its use case (don't leave Pillar 3 with no hook options).
- Always note the deprecation date + reason in the target file's Learnings & Rules.
- Keep the deprecated row for historical reference (struck-through, not deleted) so performance-review can detect if the pattern comes back later.

## What promotion does NOT do

- Does not guarantee the pattern will keep winning (regression to the mean is real).
- Does not apply retroactively to past drafts in the queue.
- Does not override brand-policy rules (Conservative client naming + Restrained emoji stay universal regardless of performance signals).
- Does not modify validator hard rules (em dash ban, hype word ban stay even if somehow data suggested otherwise).

## Cross-skill dependency map (who reads this skill's output)

When performance-review writes its weekly report, these skills should re-consume it next run:

- `post-writer` — checks for Tier 1 hooks before generating; prefers them
- `content-calendar` — checks for winning slot patterns; reinforces in next week's plan
- `repurpose` — checks for Tier 1 recipes; uses them first
- `hook-library` (if split later) — absorbs hook-category promotions directly

In practice, these skills just re-read their own reference files at run time. This skill's job is to make sure those reference files reflect the latest performance signals.
