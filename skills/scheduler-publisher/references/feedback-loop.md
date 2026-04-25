# Feedback Loop — scheduler-publisher

## When to log a learning

Add a dated entry to SKILL.md's "Learnings & Rules" section when:

- An API response shape changed and broke the publisher (LinkedIn or X versioned the endpoint, deprecated a field, etc.)
- A retry strategy needs tuning (wait too short / too long for a given error class)
- A frontmatter field name needs adding (e.g., `posting_image_alt_text` for LinkedIn accessibility)
- A LaunchAgent quirk discovered (Mac sleep, time zone bug, plist permission)
- macOS notification system changed (new permission prompt, sound API change)
- A draft type wasn't anticipated (LinkedIn poll, X Space, IG Reel cover frame, etc.)

## Format

```
- [YYYY-MM-DD] [CONTEXT TAG] Finding → Action.
```

Context tags:
- `[Initial build]` — design decisions baked in at v1
- `[LinkedIn]` `[X]` `[IG]` `[FB]` `[WhatsApp]` — channel-specific
- `[LaunchAgent]` — cron quirks
- `[Keychain]` — token storage
- `[Calendar parse]` — apply_calendar parser issues
- `[State machine]` — frontmatter status transitions
- `[Failure recovery]` — retry / fallback issues
- `[Cross-skill]` — interaction with post-writer / visual-generator / performance-review

## Cap

Keep "Learnings & Rules" under 30 lines. If it grows beyond, prune oldest entries that have been fully superseded by code changes.

## Cross-skill connection log

When this skill ships a post, it writes back to the source draft:
```yaml
posted_at: 2026-04-22T09:03:14+05:30
platform_url: https://linkedin.com/feed/update/urn:li:activity:7186...
posting_status: posted
published_via: api
```

These three fields are CRITICAL for `performance-review.py` to fetch live engagement metrics. If you change frontmatter field names here, also update `performance-review/scripts/record_performance.py`.

## Eval candidates

Add a test case to `evals/evals.json` when:

- A new channel is added
- A new failure mode is observed in production
- A new frontmatter field is consumed
- The state machine gains a new state

Each eval test should be runnable in dry-run mode (no actual API calls). Mock fixtures live in `evals/fixtures/` (drafts with various frontmatter combinations + expected state transitions).
