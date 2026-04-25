# Feedback Loop (performance-review)

Per CLAUDE.md Mandatory Session Close Protocol. Entries go in the `## Learnings & Rules` section of SKILL.md.

## What to capture

**Always capture:**
- Schema gaps — metrics the user wanted to track but the schema didn't support (e.g., LinkedIn newsletter subscribers)
- Baseline noise — when baseline computation feels off (outlier posts distorting medians)
- Scoring formula miscalibrations — weighted scores that don't match intuition (a post felt like a hit but scored mid)
- Suggestion accuracy — when a P1 suggestion turned out wrong or right (track applied suggestions)
- Data-source workflow pain (the user hated the CSV paste step; need a shortcut)

**Skip:**
- Per-post commentary (that's per-record, not skill-level)
- Emotional reactions without actionable adjustments

## Context tags

- `[Schema]` — metrics-schema.md adjustment
- `[Scoring]` — scoring-rules.md formula/threshold adjustment
- `[Promotion]` — promotion-rules.md mapping or threshold
- `[Workflow]` — CLI flow, CSV import ergonomics, data entry friction
- `[Cross-skill]` — output affecting another skill negatively (e.g., too many false-positive Tier 1 promotions polluting post-writer)

## Performance-tracking meta-learnings

Once this skill has 12+ weeks of data, it should meta-analyze its own suggestions:

- Suggestions that the user APPLIED and subsequently kept performing well → the scoring formula is calibrated for that pattern
- Suggestions that the user APPLIED but then the pattern regressed → overfit signal, raise the threshold
- Suggestions that the user REJECTED → note why, adjust suggestion-priority logic

Log these in SKILL.md under a special `## Meta-learnings (self-review)` subsection. This is what makes performance-review smarter about its own judgments, not just about other skills' patterns.

## When a learning triggers a reference update

7+3 rule applies:
1. Update the reference file in performance-review/references/
2. Add dated learning to SKILL.md
3. If the change affects other skills' reference formats (e.g., new metric field that post-writer should surface in frontmatter), flag cross-skill update

## Relationship to other feedback loops

This skill's learnings feed forward to other skills' learnings:

- When a Tier 1 hook gets promoted, the applicable learning goes in **post-writer**/SKILL.md under `[Performance-promoted]`
- When a transformation recipe wins, the learning goes in **repurpose**/SKILL.md
- When a slot consistently wins, the learning goes in **content-calendar**/SKILL.md

Cross-reference: performance-review is the only skill that modifies OTHER skills' learnings directly (in v2 auto-apply mode; v1 just suggests).
