# Feedback Loop — weekly-ritual

## When to log a learning

Add a dated entry to SKILL.md "Learnings & Rules" when:

- A skill in the chain changes its CLI / output structure (Sunday flow needs to update its subprocess call)
- A new skill is added that should join the Sunday or Friday chain
- A pre-check turns out to be insufficient (Mayank reports the ritual ran but with bad data)
- The cron fire time needs adjustment (e.g., 09:00 IST is too early)
- The notification + clipboard prompt needs different wording
- Idempotency window changes (currently 12h)
- A new ritual day is added (e.g., Wednesday mid-week check-in)

## Format

```
- [YYYY-MM-DD] [CONTEXT TAG] Finding → Action.
```

Context tags:
- `[Initial build]`
- `[Sunday]` `[Friday]` — ritual-specific
- `[Cron]` — LaunchAgent / scheduling quirks
- `[Notification]` — macOS notification UX
- `[State file]` — idempotency / state tracking
- `[Skill chain]` — interaction with other skills
- `[TCC]` — permission issues

## Cross-skill impact

When weekly-ritual's flow changes, check:
- `content-calendar` — sunday-flow Step 3 calls this skill. If its CLI changes, update sunday-flow.md.
- `post-writer` — sunday-flow Step 4. Same.
- `repurpose` — sunday-flow Step 5. Same.
- `visual-generator` — sunday-flow Step 6. Same.
- `scheduler-publisher` — sunday-flow Step 7 calls `apply_calendar.py`. If that script's interface changes, update sunday-flow.md.
- `performance-review` — friday-flow Steps 2-3. Same.

## Eval candidates

Add a test case to `evals/evals.json` when:

- A new pre-check is added
- A new ritual day is added
- The cron interval changes
- The state file schema changes

Each test case should be runnable in dry-run mode (no actual notifications, no actual subprocess calls).
