# Feedback Loop — Learnings & Rules Protocol

Every skill session ends with a feedback entry. This is non-negotiable per CLAUDE.md Mandatory Session Close Protocol.

## Format

Add entries to the `## Learnings & Rules` section at the bottom of `SKILL.md`:

```
- [DATE] [CONTEXT] Finding: {what happened}. → Action: {what changes in the skill or rule}.
```

Where:
- **DATE** = ISO date (YYYY-MM-DD)
- **CONTEXT** = one of: `[Initial build]`, `[Client type]`, `[Process]`, `[Script fix]`, `[Architecture]`, or a brand/client name
- **Finding** = specific observation from this session (what broke, what worked unexpectedly, what the user corrected)
- **Action** = concrete change (updated Step N, added reference file X, codified rule Y, or "none — noted")

## What to capture

**Always capture:**
- Explicit user corrections ("don't do X", "stop doing Y")
- Data sources that failed (WebFetch returning empty, memory files missing)
- Assumptions that turned out wrong (e.g., Insta had 1600 followers; actually LinkedIn does)
- Surprising signals in the data (e.g., "skill" mentions dominating over "client")
- Positioning / framing moments that resonated

**Skip:**
- Trivial task steps that worked as expected
- Generic observations without an action implication
- Duplicates of existing learnings (update the existing entry instead)

## Maintenance rules

- Keep the section under 30 lines. Prune quarterly.
- Consolidate related entries into single lines with "CONSOLIDATED <date>" comment when they share a theme.
- If a learning results in a script or reference change, link to the updated file in the Action field.
- Remove entries that are no longer relevant (e.g., if a rule became obsolete because the underlying skill logic changed).

## When the learning is the SKILL itself

Sometimes a session reveals a missing Step. In that case:
1. Add the Step to SKILL.md (respecting <200 line budget)
2. Write the reference file(s) it depends on
3. Add a learning: `[DATE] [Skill gap] Missing X step caused Y. → Action: Added Step N to SKILL.md + references/X.md`

This is the 7+3 rule in action per CLAUDE.md — fix + SKILL.md update + learning are a single atomic action.
