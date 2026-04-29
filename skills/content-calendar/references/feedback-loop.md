# Feedback Loop (content-calendar)

Per CLAUDE.md Mandatory Session Close Protocol. Entries go in the `## Learnings & Rules` section of SKILL.md.

## What to capture

**Always capture:**
- Slot assignments the user overrode or rejected (e.g., "Monday LP slot was assigned Thrive entry but user moved it to Thursday" → learn from that re-routing)
- Gap flags that repeatedly fire week after week (e.g., Pillar 3 is always under-represented → update capture prompts to nudge for that pillar)
- Rotation rule misfits (e.g., Monday = Pillar 1 but user prefers Pillar 1 on Thursday for structural reasons)
- Sparse-bank patterns: if idea-bank is routinely <5 entries, the work-capture frequency is too low — flag for cadence adjustment

**Skip:**
- One-off slot tweaks (individual edits are per-week, not skill-level rules)
- Subjective opinions without a concrete rule change

## Context tags

- `[Rotation]` — pillar-to-day mapping issue
- `[Cadence]` — channel frequency or timing issue
- `[Gap]` — idea-bank shortage pattern
- `[Format]` — variety or fit mismatch
- `[Theme]` — themed-week override learning
- `[Repurpose]` — repurpose-chain issue (e.g., X thread repurpose doesn't fit original LI)

## When a learning triggers a reference update

7+3 rule: reference edit + learning + any wiki/downstream updates together.

Example: user consistently moves Pillar 3 from Friday to Monday.
1. Update `cadence-templates.md` rotation table to reflect new preference
2. Add learning to SKILL.md: "[DATE] [Rotation] User prefers Pillar 3 on Monday, Pillar 1 on Friday. → Action: swapped Mon/Fri pillar locks in cadence-templates.md"
3. If this changes weekly cadence substantively, update `_engine/wiki/channel-playbook.md` in brand wiki too

## Future feedback source: performance-review

When `performance-review` ships, it will feed this loop:
- Slots that produced top-performing posts → the rotation/format choice gets promoted
- Slots that flopped → the pattern gets flagged for change

For now (pre-performance-review), the only signal is user edits and gap patterns.
