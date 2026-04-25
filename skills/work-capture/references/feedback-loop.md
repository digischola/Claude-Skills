# Feedback Loop — Learnings & Rules Protocol

Format matches `personal-brand-dna/references/feedback-loop.md`. This skill's learnings focus on:

## What to capture

- **Tagging drift** — if user keeps correcting a specific type assignment (e.g., "that's not client-comm, it's client-win"), refine the definition in `entry-schema.md`
- **Rejected inputs** — generic observations rejected; catalog common patterns to help users self-filter before asking
- **Channel fit surprises** — if a `build-log` unexpectedly performed well on WA-Status (per `performance-review`), update `entry-schema.md` channel heuristics
- **Schema gaps** — if new entry types emerge that don't fit the 7 allowed types, add them + bump schema version in `idea-bank.json`

## Format

```
- [YYYY-MM-DD] [CONTEXT] Finding: {observation}. → Action: {concrete change}.
```

Where CONTEXT is one of:
- `[Tagging]` — type / pillar / channel assignment issue
- `[Rejection]` — generic or duplicate input pattern
- `[Schema]` — structural change to entry format
- `[Integration]` — downstream skill consumption issue (e.g., `post-writer` expects a field `work-capture` isn't producing)

Keep the section in SKILL.md under 30 lines. Prune quarterly — consolidate related entries when they share a theme.
