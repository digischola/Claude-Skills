# Failure Handling

## Retry policy

When an autonomous publish (LinkedIn / X) fails:

| Attempt | Wait before retry | Notes |
|---|---|---|
| 1 (initial) | — | Immediate publish on tick |
| 2 | 5 seconds | Same tick if still in lock window; else next tick |
| 3 | 30 seconds | Next tick |
| 4 | 2 minutes | Next tick |
| 5 (permanent) | _(stop)_ | Mark `posting_status: failed`, fire failure notification |

`posting_attempts` int in frontmatter increments on each failed attempt. `posting_next_retry_at` gets set after each failure to gate the next tick.

## State machine

```
                    +-----------+
                    |  scheduled |  <-- written by apply_calendar.py
                    +-----+-----+
                          |
                  tick.py acquires lock
                          v
                    +----+-----+
                    | posting   |  <-- in flight; lock prevents concurrent ticks
                    +-----+-----+
                          |
        +-----------------+----------------+
        |                                  |
   API success                       API failure
        |                                  |
        v                                  v
    +-------+                   +----------------+
    | posted |                  | failed (or)    |
    | (move  |                  | retry (waits)  |
    |  to    |                  +-------+--------+
    |published)                         |
    +-------+              attempts < 4 |   attempts >= 4
                                        |          |
                                  back to scheduled  |
                                                     v
                                              +-----------+
                                              |  failed   |
                                              | (notify   |
                                              |  user)    |
                                              +-----------+
```

For manual channels (IG/FB/WhatsApp), the state machine has an extra branch:

```
scheduled -> notified (notification fired) -> posted (user runs confirm_published.py)
                                           -> manual_publish_overdue (after 48h)
```

## Failure causes (from real APIs)

### LinkedIn
| Error | Cause | Auto-retry? |
|---|---|---|
| `401 Unauthorized` | Access token expired | Yes — refresh token first, then retry |
| `403 Forbidden` | Scope missing or app suspended | No — notify user to fix |
| `429 Too Many Requests` | Rate limit (~150/day for personal) | Yes — wait 1h |
| `422 Unprocessable Entity` | Asset upload incomplete or malformed payload | No — notify user to inspect draft |
| Timeout | Network flake | Yes — full retry policy |

### X
| Error | Cause | Auto-retry? |
|---|---|---|
| `401` | Token expired | Yes — refresh first |
| `403 duplicate content` | Same tweet text within 24h | No — mark failed, no retry (user must edit and retry) |
| `429` | Daily / monthly limit hit | Yes — wait until next IST midnight |
| `400 Tweet length` | Over 280 chars (post-writer should catch this earlier) | No — notify |
| Timeout | Network flake | Yes |

### Manual channels
- Notification-fire failures (osascript exit non-zero) → log + retry next tick
- User never confirms within 48h → mark `manual_publish_overdue`, no further auto-action

## Logs

```
brand/scheduler.log              — every tick (start, scanned N drafts, attempted M, succeeded P)
brand/scheduler-failures.log     — only failures with full traceback
brand/scheduler-notifications.log — every macOS notification fired
```

Log rotation: each log file capped at 10MB, then renamed to `.1` and a new one started. Keep 5 generations. Older deleted.

## Notifications on failure

A failed autonomous post fires a Banso-sound macOS notification with the entry_id, channel, and last error. User can investigate, fix, then either:
- `python3 scripts/ship_now.py <draft.md>` to retry from scratch
- Or edit the draft frontmatter to set `posting_status: scheduled` and let the next tick pick it up

## Catastrophic failures (scheduler itself crashes)

The LaunchAgent has `KeepAlive: true` — if `tick.py` exits non-zero, macOS auto-restarts on the next 5-min interval. If it crashes 3+ times in a row, LaunchAgent's `ThrottleInterval` kicks in to slow restart attempts. Check with:

```bash
launchctl list | grep digischola
log show --last 1h --predicate 'subsystem contains "com.digischola.scheduler"' --style compact
```
