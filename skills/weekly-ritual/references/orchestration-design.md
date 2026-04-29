# Orchestration Design — why hybrid

## The problem

Eight skills produce a content production line:
```
work-capture → content-calendar → post-writer → repurpose → visual-generator → apply_calendar → scheduler-publisher → performance-review
```

Each skill works fine standalone. But there's no autonomous trigger that fires the upstream chain on a regular cadence. Mayank has to manually invoke each one.

The questions: WHO triggers the chain? HOW often?

## Three rejected designs

### Design 1: Pure-cron orchestrator (rejected)

A Python script runs everything as subprocesses:
```python
# weekly_ritual.py
subprocess.run(["python3", "content-calendar/build.py"])
subprocess.run(["python3", "post-writer/draft.py"])  # ← doesn't exist
subprocess.run(["python3", "repurpose/adapt.py"])    # ← also doesn't exist
```

**Why it fails:** post-writer, repurpose, and visual-generator have NO standalone "do everything" script. The actual writing/adaptation/briefing is **Claude reasoning**. There's no `draft.py "write a LinkedIn post about X" → output.md` because the writing IS Claude's reasoning. So pure-cron can only execute ~3 of the 8 chain steps.

### Design 2: Pure-Claude orchestrator (rejected)

Mayank manually invokes each skill on a Sunday cadence:
```
Sun 09:00 — Mayank: "build calendar for next week"
Sun 09:30 — Mayank: "draft each slot"
Sun 10:00 — Mayank: "repurpose Mon LI to X + IG"
...
```

**Why it fails:** depends on Mayank remembering the cadence + the order. Will not survive the first vacation, busy week, or "I'll do it tomorrow" decision.

### Design 3: Anthropic remote agent (rejected)

Use Claude Code's `schedule` skill to wake a Claude instance on Anthropic's infrastructure every Sunday + Friday. The remote agent runs the chain.

**Why it fails:** Remote agents can't write to Mayank's local Mac filesystem. Drafts, calendars, brand wiki, idea-bank all live on his Mac. A remote agent has no way to read/write them. Rejected.

## The chosen design: hybrid

**Cron handles WHEN. Claude handles WHAT.**

1. **macOS LaunchAgent** at `~/Library/LaunchAgents/com.digischola.weekly-ritual.plist` fires `weekly_ritual.py` at:
   - Sunday 09:00 IST (`--day sunday`)
   - Friday 18:00 IST (`--day friday`)

2. **`weekly_ritual.py`** does ONLY two things:
   a. Fire a macOS notification ("Sunday planning ready" / "Friday review ready")
   b. Copy a ritual prompt to clipboard ("run sunday ritual" / "run friday review")
   c. Update state file `brand/_engine/weekly-ritual.state.json` with `last_fired_sunday/friday`

3. **Mayank** sees the notification, opens Claude Code (likely already open), pastes from clipboard.

4. **Claude (this skill being triggered)** reads `references/sunday-flow.md` or `friday-flow.md` and executes the entire chain by invoking the existing skills (content-calendar, post-writer, repurpose, visual-generator, scheduler-publisher, performance-review) in sequence.

This bridges the cron→Claude gap with a 2-second human action (paste the prompt). Mayank doesn't have to remember anything; the Mac taps him on the shoulder.

## Why this is better than the alternatives

| Design | Cadence reliability | Creative quality | Filesystem access | Setup complexity |
|---|---|---|---|---|
| Pure-cron | ★★★ | ★ (no Claude reasoning) | ★★★ | ★★ |
| Pure-Claude | ★ (depends on memory) | ★★★ | ★★★ | ★ |
| Remote agent | ★★★ | ★★★ | ✗ (no local FS) | ★★★ |
| **Hybrid (this)** | **★★★** | **★★★** | **★★★** | **★★** |

The 2-second human paste is acceptable friction. It also gives Mayank a chance to skip the ritual on weeks he doesn't want it (just dismiss the notification).

## Edge cases handled

### Mac asleep at 09:00 Sunday
LaunchAgent's `StartCalendarInterval` fires at the next wake. So if Mac wakes at 11am, ritual fires at 11am. Acceptable.

### Mayank ignores the notification
State file records `last_fired_sunday` but not `last_completed_sunday`. Next Sunday's notification mentions the un-completed prior ritual.

### Mayank pastes the prompt twice in same week
Idempotency check in the SKILL.md flow: if `last_completed_sunday` is within current ISO week, refuse and tell Mayank "Already done this week, want to override? (Y/N)".

### Friday review runs with no posts
Pre-check in friday-flow.md detects empty published/ folder, BLOCKs gracefully.

### A skill in the chain is missing
Sunday flow's trend-research and peer-tracker steps gracefully skip if the skills don't exist (test via filesystem check). Required skills (content-calendar, post-writer, etc.) BLOCK with a clear "build skill X first" message.

### TCC permission
The python3 binary already has Full Disk Access (granted for scheduler-publisher). Same binary, same permission, no new grant needed.
