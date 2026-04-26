---
name: weekly-ritual
description: "Cron-triggered orchestrator for the Digischola personal-brand suite. Two recurring rituals: (1) WEDNESDAY 09:00 IST — Planning → trend scan + peer refresh + content-calendar + post-writer drafts + repurpose variants + visual-generator briefs + apply_calendar to schedule the week. (2) MONDAY 18:00 IST — Review → record_performance for last week's posts + weekly_review for HIT/ABOVE/BELOW/FLOP analysis + suggested promotions. The macOS LaunchAgent fires a notification at the scheduled time + copies the ritual prompt to clipboard. User pastes the prompt into Claude Code and Claude drives the full chain via the existing skills (content-calendar, post-writer, repurpose, visual-generator, performance-review). Use when user says: run wednesday planning, wednesday planning, wednesday ritual, run monday review, monday review, monday ritual, weekly ritual, weekly orchestrator, plan and ship the week, performance-review and apply, install weekly cron, run sunday ritual, run friday review (legacy aliases still accepted). Do NOT trigger for: drafting one post (use post-writer), planning week without ritual context (use content-calendar), creating one visual (use visual-generator), capturing one idea (use work-capture), publishing (handled by scheduler-publisher autonomously)."
---

# Weekly Ritual

The orchestration playbook for Mayank's weekly cadence. macOS LaunchAgent fires twice a week to nudge; Claude drives the chain through existing skills when invoked.

Naming convention: rituals are named by the day they run. The **Wednesday Planning** ritual builds next week's content. The **Monday Review** ritual scores last week's posts. Internal code paths still use the legacy labels `sunday`/`friday` as neutral keys (state.json, CLI flags, prompt constants) — only the user-facing names and docs are day-based.

## Why hybrid (cron + Claude)

Half the chain is script-driven (idempotent, automatable): trend-research, peer-tracker, content-calendar, apply_calendar, weekly_review.
Half the chain needs Claude (creative, judgment-driven): post-writer drafts, repurpose hook adaptation, visual-generator briefs, performance-review interpretation.

A pure-cron version would skip the creative half. A pure-Claude version would require Mayank to remember the cadence. The hybrid: **cron nudges, Claude executes**.

## Context Loading

**Brand wiki:**
- `Desktop/Digischola/brand/pillars.md` — must be LOCKED for both rituals
- `Desktop/Digischola/brand/idea-bank.json` — Wednesday-Planning reads, week's drafts get scheduled_week stamped
- `Desktop/Digischola/brand/calendars/YYYY-WXX.md` — Wednesday-Planning writes
- `Desktop/Digischola/brand/queue/pending-approval/` — Wednesday-Planning writes drafts here, Monday-Review reads from `published/`
- `Desktop/Digischola/brand/performance/YYYY-WXX.md` — Monday-Review writes

**Shared context:**
- `.claude/shared-context/analyst-profile.md` — workflow, voice/quality standards used to gate ritual outputs
- `shared-context/output-structure.md` — Digischola uses queue-based structure (NOT outputs/working/ split); after content drops, run `python3 ~/.claude/scripts/build_digischola_index.py` to refresh the index

**Skill references:**
- `references/wednesday-planning-flow.md` — full Wednesday step-by-step
- `references/monday-review-flow.md` — full Monday step-by-step
- `references/orchestration-design.md` — why hybrid, what's automated vs Claude-driven
- `references/feedback-loop.md`

**Other skills consumed (Claude orchestrates these):**
- `content-calendar` (Wednesday-Planning step 3)
- `post-writer` (Wednesday-Planning step 4)
- `repurpose` (Wednesday-Planning step 5)
- `visual-generator` (Wednesday-Planning step 6, optional per slot)
- `scheduler-publisher` apply_calendar.py (Wednesday-Planning step 7)
- `performance-review` (Monday-Review)

## Process — Wednesday Planning

When Mayank pastes "run wednesday planning" / "wednesday planning" / legacy "run sunday ritual" (or similar trigger) into Claude Code, Claude follows this chain literally per `references/wednesday-planning-flow.md`. High level:

1. **Pre-check**: pillars LOCKED, idea-bank.json EXISTS (file-only check; entry-count check moved to a post-Step-1 gate since trend-research's whole job is to populate the bank).
2. **Trend scan** (active as of 2026-04-20): invoke `trend-research` Mode 1 — Claude does 6 WebSearches (2 per pillar), synthesizes 3-6 candidates per pillar, dedupes against existing idea-bank, ingests survivors via `trend_research.py ingest`. Adds 9-18 fresh candidates per week. Optional Mode 2 (Perplexity deep) available via `trend_research.py prompt --week WXX`.
3. **Peer refresh** (active as of 2026-04-20): invoke `peer-tracker` Mode 1 — get rotation (4 creators / week, full 15-creator cycle every ~4 weeks) via `peer_tracker.py rotation-due`, run 1-2 WebSearches per due creator, synthesize findings (recent posts + hook delta + status), apply via `peer_tracker.py apply-refresh`. Updates `post-writer/references/creator-study.md` in place.
4. **Build calendar**: invoke content-calendar for the upcoming week (e.g., 2026-W18).
5. **Draft each slot**: for each of the 10-12 slots, invoke post-writer with the assigned idea-bank entry. Drafts land in `pending-approval/`.
6. **Repurpose first-channel posts** to additional channels per content-calendar's repurpose hints (Mon LI → Tue X thread → Sat IG Reel).
7. **Generate visual briefs** for any slot that needs media (carousels, quote-cards, animated, reels).
8. **Apply calendar** to write `scheduled_at` to each draft via `scheduler-publisher/scripts/apply_calendar.py`.
9. **Summary**: list what was scheduled, where the user must intervene (manual visual rendering in Claude Design / Hyperframes), and any warnings (missing idea-bank entries, pillar shortage).

## Process — Monday Review

When Mayank pastes "run monday review" / "monday review" / legacy "run friday review" Claude follows `references/monday-review-flow.md`:

1. **Pre-check**: at least 1 post in `queue/published/` from the last 7 days.
2. **Collect metrics**: for each published post, ask Mayank for the per-channel engagement numbers (reactions, comments, reshares, saves, etc.). Run `performance-review/scripts/record_performance.py` per post.
3. **Run weekly review**: `performance-review/scripts/weekly_review.py` — buckets posts HIT/ABOVE/BELOW/FLOP per channel, computes pattern-level scores, writes report to `brand/performance/YYYY-WXX.md`.
4. **Surface suggestions**: list P1/P2/P3 promotion + deprecation suggestions targeting hook-library / voice-frameworks / transformation-recipes / rotation-rules. Mayank decides which to apply.
5. **Loop back**: any insight that survives the review → fold into next Wednesday's planning constraints.

## Cron — install + state

```bash
python3 scripts/install_launchagents.py                # writes ~/Library/LaunchAgents/com.digischola.weekly-ritual.plist + loads
python3 scripts/install_launchagents.py --status
python3 scripts/install_launchagents.py --uninstall
python3 scripts/weekly_ritual.py --once --day planning  # manual fire (for testing) — alias: --day wednesday or --day sunday
python3 scripts/weekly_ritual.py --once --day review    # manual fire (for testing) — alias: --day monday or --day friday
```

The LaunchAgent fires `weekly_ritual.py` at:
- **Wednesday 09:00 IST** → planning ritual → notification + clipboard `"run wednesday planning"`
- **Monday 18:00 IST** → review ritual → notification + clipboard `"run monday review"`

Notification is the trigger. User opens Claude Code, paste from clipboard, Claude executes the chain.

State file `brand/weekly-ritual.state.json` tracks last-fired timestamps per ritual. Keys kept as legacy neutral labels (`last_fired_sunday` → Wednesday-planning fires, `last_fired_friday` → Monday-review fires) so rename doesn't break the 12-hour idempotency guard — see Learnings 2026-04-24.

## Output Checklist

- [ ] LaunchAgent installed: `launchctl list | grep com.digischola.weekly-ritual`
- [ ] After Wednesday Planning: calendar written, ≥7 drafts in pending-approval, scheduled_at set on each
- [ ] After Monday Review: performance/YYYY-WXX.md written, suggestions surfaced

## Anti-patterns

- Do NOT auto-publish from inside this skill. Publishing is scheduler-publisher's job; we only schedule.
- Do NOT skip the LOCKED pillars check on Wednesday Planning. If pillars aren't locked the calendar will be garbage.
- Do NOT auto-apply performance-review's promotion suggestions. v1 is advisory; user decides.
- Do NOT fire the notification more than once per cycle (idempotency: store last_fired_at in `brand/weekly-ritual.state.json`).
- Do NOT depend on trend-research / peer-tracker existing. Wednesday-planning flow gracefully skips them if scripts are absent.
- Do NOT post-process the calendar in this skill. content-calendar owns calendar logic; weekly-ritual just calls it.

## Learnings & Rules

<!--
Format: [DATE] [CONTEXT] Finding → Action. Keep under 30 lines.
-->
- [2026-04-20] [Initial build] Built as the orchestrator skill. Cron fires twice weekly via macOS LaunchAgent at `~/Library/LaunchAgents/com.digischola.weekly-ritual.plist`. Single plist, two `StartCalendarInterval` entries. Notification + clipboard-copy of ritual prompt. Claude reads SKILL.md to execute the chain when Mayank pastes the prompt. Idempotency: `brand/weekly-ritual.state.json` records last-fired ISO timestamps; weekly_ritual.py refuses to re-fire within 12h of last fire (prevents repeated nudges if Mac wakes up multiple times).
- [2026-04-20] [Hybrid design] Pure-cron version was rejected because creative steps (post-writer drafts, repurpose hook adaptation, visual-generator briefs) need Claude reasoning. Pure-Claude version was rejected because Mayank can't be relied on to remember the cadence. The macOS notification + clipboard-prompt is the bridge: cron handles "when", Claude handles "what". TCC permission for python3 (already granted for scheduler-publisher) covers this skill too.
- [2026-04-20] [Skill chain] Planning ritual depends on: pillars LOCKED, idea-bank populated (≥7 raw entries), content-calendar built (✓), post-writer built (✓), repurpose built (✓), visual-generator built (✓), scheduler-publisher's apply_calendar.py (✓). Trend-research + peer-tracker are gracefully optional. Review ritual depends on: performance-review built (✓), at least one post in queue/published/ from last 7 days. If any precondition fails, Claude refuses to start the ritual and tells Mayank what's missing.
- [2026-04-20] [Pre-check] Test run of planning ritual hit a protocol bug: pre-check #2 required ≥7 raw idea-bank entries BEFORE Step 1. But Step 1 (trend-research) was added later specifically to populate the bank. The pre-check ran too early — bank is legitimately empty on a cold start and the ritual would refuse to run, even though Step 1 would solve the problem in 2 minutes. Fix → pre-check #2 downgraded to file-existence-only; entry-count check moved to a new "post-populate gate" that runs between Step 2 and Step 3. See `references/wednesday-planning-flow.md` for the new gate text. If after Step 1+2 the bank still has <7 raw, we surface options instead of hard-block (Mode 2 Perplexity fallback OR quick work-capture round).
- [2026-04-22] [Notification UX dead-end — user caught it] Every notification this session was "banner-only" (`osascript display notification`). No click-to-action. User pointed out: when cron fires, banner appears + clipboard is silently copied, but if user forgets what the clipboard holds, the whole cycle is lost. Logged to `references/notification-ux-backlog.md` for end-of-session batch fix. Recommended approach: central `shared/notify.py` helper using `terminal-notifier` (`-open <url>`) with osascript fallback; inline action buttons for review gate via PyObjC if needed. Rule: every notification must have a click action that does the next step — no dead-end banners.
- [2026-04-22] [Step 6 gap — briefs are IOUs, not rendered assets] During first end-to-end W18 planning run, Step 6 generated visual BRIEFS (markdown TODO documents for Claude Design handoff) but did NOT render actual PNG/MP4 assets. Source drafts had no `visual_assets_dir` set → review_queue.py's UI served whatever was in `queue/assets/<entry_id>/` from prior sessions. Fix: Step 6 should RENDER fresh assets (Path A Claude Design handoff OR Path B Remotion/Hyperframes), not just write briefs. Write `visual_assets_dir` into source draft frontmatter pointing to the fresh render. Rule locked: IOUs in a pipeline that ships autonomously to public channels = silent bugs. Every visual slot must have a rendered asset before the draft is marked posting_status=scheduled.
- [2026-04-22] [Step 6.5 protocol gap — user caught it] During first end-to-end run Claude completed Steps 1-6 + 8 + 9 but SKIPPED Step 6.5 (review_queue.py) by offering the user "two ways to review" instead of executing the step literally. No macOS notification fired because the script wasn't run. Fix: Step 6.5 is MANDATORY — `python3 scheduler-publisher/scripts/review_queue.py` MUST be invoked by Claude. Offering alternatives is judgment substitution (per CLAUDE.md Skill Protocol Supremacy), not judgment within framework. Rule locked: the literal command line in wednesday-planning-flow.md is the contract; paraphrasing it for the user breaks the hand-off.
- [2026-04-22] [Notification-UX batch SHIPPED] End-of-session batch implemented all 7 items from `references/notification-ux-backlog.md`. New central helper `skills/shared-scripts/notify.py` exposes `notify()` (click-through via terminal-notifier, osascript fallback) + `notify_reviewable_artifact()` (auto-spawns review_queue.py on port 8765 if not running, builds URL with `#draft-<filename>` anchor). `weekly_ritual.py` now generates `brand/weekly-ritual/launcher-<day>.html` on each cron fire — full-page Chrome landing with ritual prompt + copy button + what-happens-next + current queue state + last-run timestamps. Banner click opens this page via `file://`. 8 scripts across 4 skills refactored. Autonomous LinkedIn ship now fires click-to-posted-URL banner. Failures reveal draft file in Finder.
- [2026-04-22] [Cadence shift — user moved cycle from Mon→Sun to Thu→Wed] Late-session user instruction: "so every future run works in this way from now as we are starting today i.e. 22nd instead of next monday i.e. 27th". Shifted W18's 11 drafts back by 4 days + renamed filenames, then patched the LaunchAgent cron: **Sun 09:00 → Wed 09:00** (plan) and **Fri 18:00 → Mon 18:00** (review). The ritual labels `sunday` (plan) and `friday` (review) were intentionally kept internally as neutral keys — state.json, SKILL.md chain references, launcher HTML filenames, and weekly_ritual.py's `SUNDAY_PROMPT`/`FRIDAY_PROMPT` constants still use those labels. Only the weekday-to-label mapping in `auto_detect_day()` changed: Wed→"sunday", Mon→"friday" (with Sun/Fri kept as fallbacks for one-shot `--day auto` runs during cycle-change weekends). `install_launchagents.py` updated, plist reinstalled + loaded. **Rule:** anyone wanting to shift the cycle again must (a) shift posting scheduled_at values + rename files, (b) edit Weekday integers in install_launchagents.py PLIST_TEMPLATE, (c) edit auto_detect_day() mapping, (d) reinstall plist. All four must happen in one sitting.
- [2026-04-24] [User-facing rename — "sunday ritual" / "friday review" confused the cadence] User: "maybe we should rename the rituals based on the days on which they run in cycle naming looks confusing". Renamed ritual labels throughout user-facing docs to match actual cron days: Wednesday Planning + Monday Review. Files: SKILL.md rewritten (frontmatter description + trigger phrases + Process sections + Output Checklist + Anti-patterns), `references/sunday-flow.md` → `wednesday-planning-flow.md`, `references/friday-flow.md` → `monday-review-flow.md`, `weekly_ritual.py` clipboard prompts updated ("run wednesday planning" / "run monday review" with legacy aliases still accepted in `auto_detect_day` + CLI `--day` resolver), `install_launchagents.py` plist comments updated. **Internal code paths (state.json keys, prompt-constant names, day-string CLI arg) intentionally kept as legacy `sunday`/`friday` neutral labels** to avoid breaking the 12-hour idempotency guard and to avoid a state migration today when there's no functional win. New CLI accepts `--day planning|wednesday|sunday` (all alias to the plan ritual) and `--day review|monday|friday` (all alias to the review ritual). Legacy trigger phrases "run sunday ritual" / "run friday review" still listed in frontmatter so muscle memory keeps working for a few weeks. Cron times unchanged (Wed 09:00 + Mon 18:00 IST). Next fires: Mon Apr 28 18:00 IST review → Wed Apr 30 09:00 IST plan.
