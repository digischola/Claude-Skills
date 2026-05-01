# peer-scan-flow

Detailed steps for `ideas-in peer-scan`. Loaded only when scanning peer creators.

## Creator roster (15 named, monthly cycle, 4 per week)

| Group | Creators |
|---|---|
| Week 1 | Peep Laja, Jon MacDonald, Harry Dry, Rishabh Dev |
| Week 2 | Julian Shapiro, Shreya Pattar, Varun Mayya, Dickie Bush |
| Week 3 | Justin Welsh, Jack Butcher, Barry Hott, Chase Dimond |
| Week 4 | Cody Plofker, Joly Tematio, Sam Piliero |

The current week pointer lives at top of `creator-study.md`. Increment after each scan. Wraps after week 4.

## Per-creator scan steps

For each creator in this week's group:

1. WebSearch `<handle> linkedin posts last 30 days` and `<handle> twitter recent tweets`.
2. Identify the top 1-3 posts by engagement signal (reactions, comments, reposts visible in snippets).
3. For each post:
   - Identify hook pattern → cross-ref `brand/references/hooks.json`. If pattern not in our library, log it as a peer-pattern entry.
   - Identify voice signature drift (this creator's typical tone vs this post).
   - Identify topic pivot (is creator suddenly posting outside their normal lanes?).
4. Update `creator-study.md` section for that creator. Overwrite — never accumulate (per Same-Client Re-Run Rule in CLAUDE.md).

## Borrow vs steal threshold

- **Borrow** (allowed) — pattern formula adapted to Mayank's pillars. Append as `type: peer-pattern`.
- **Steal** (banned) — copy-paste of the post's actual content. Never do this.

If the pattern is a structural template (e.g., "Setup → Twist → Lesson → CTA"), borrowing is fine. If the pattern is a specific narrative (e.g., "Day 1 of building X in public"), only borrow if Mayank has a parallel real journey.

## Output entry shape (peer-pattern)

```json
{
  "id": "<uuid>",
  "type": "peer-pattern",
  "captured_at": "<iso8601>",
  "raw_note": "<creator name>: <pattern formula in 1 sentence>",
  "source_url": "<url to source post>",
  "creator_handle": "<handle>",
  "pattern_formula": "<formula in plain English>",
  "tags": ["peer-pattern", "<creator-slug>"],
  "channel_fit": ["LinkedIn", "X"],
  "status": "raw"
}
```

## Cron context

Triggered by `weekly-ritual` Wednesday 09:00 IST after trend-scan, OR explicitly. Same nudge-pattern: cron fires notification + clipboard prompt.

## Anti-patterns

- Do NOT scan the same creator twice in a 28-day window.
- Do NOT flag a hook pattern as "borrow" if the originator was Mayank — that's just our own pattern.
- Do NOT update creator-study.md by APPENDING — overwrite the per-creator section.
