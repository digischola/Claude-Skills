# Wednesday Planning Flow

Detailed step-by-step Claude follows when Mayank pastes "run wednesday planning" (primary), "wednesday planning", or legacy "run sunday ritual" into Claude Code. Cron fires the notification + clipboard at 09:00 IST every Wednesday; this file is the playbook. Internal state key is still `last_fired_sunday` (kept as a neutral legacy label — see SKILL.md Learnings 2026-04-24).

## Pre-checks (BLOCK if any fails)

1. `Desktop/Digischola/brand/_engine/wiki/pillars.md` exists AND status is LOCKED
2. `Desktop/Digischola/brand/_engine/idea-bank.json` exists (the FILE — entry count check moved to after Step 1, since Step 1's whole job is to populate the bank via trend-research)
3. `Desktop/Digischola/brand/queue/pending-approval/` exists (create if not — queue/ stays at top)
4. `last_fired_sunday` in `brand/_engine/weekly-ritual.state.json` is >12h ago (idempotency)

If any pre-check fails, refuse and explain. Do not proceed.

## Post-populate gate (BLOCK before Step 3)

After Steps 1 + 2 have run, before Step 3 (content-calendar), verify:

- `idea-bank.json` has ≥7 total entries with `status: raw` across any `type` (work-capture entries OR type:trend entries from trend-research). If <7, surface:
  - "After trend-research + peer-tracker, bank has only N raw entries. Two options: (a) fall back to Mode 2 Perplexity deep-research for pillars with thin coverage; (b) ask Mayank to run a quick work-capture round for missing pillars before we build the calendar." Pause for input.

## Step 1 — Trend scan (active as of 2026-04-20)

Invoke the `trend-research` skill in Mode 1 (autonomous WebSearch).

- For each of the 3 pillars (lp-craft, solo-ops, paid-media):
  1. Read `trend-research/references/web-search-strategy.md` for the per-pillar search loop.
  2. Run 2 WebSearches per pillar (industry trends + creator activity), pulling 3-6 candidates per pillar.
  3. For each candidate, build the JSON dict with seed / hook_candidate / source_urls / tags / relevance_score.
  4. Run `python3 trend-research/scripts/trend_research.py dedupe-check --json '<candidate>'` — skip if DUP or QUALITY-REJECT.
  5. For survivors, run `python3 trend-research/scripts/trend_research.py ingest --pillar <slug> --json '<candidate>'`.
- After all 3 pillars: run `python3 trend-research/scripts/trend_research.py stats` to confirm count.
- Append per-pillar count + skipped reasons to `brand/_engine/_research/trends/<week>/scan-log.md`.

Target: 3-6 candidates added per pillar (9-18 total per week). If <3 added for any pillar, surface a WARNING — Mayank may want to manually run Mode 2 (Perplexity-prompt deep research) for that pillar.

## Step 2 — Peer refresh (active as of 2026-04-20)

Invoke the `peer-tracker` skill in Mode 1 (autonomous WebSearch).

- Run `python3 peer-tracker/scripts/peer_tracker.py rotation-due --week 2026-W17 --json` → get the 4 (or 5 every 4th week) creators due this Sunday
- For each due creator:
  1. Read existing entry from `post-writer/references/creator-study.md`
  2. Run 1-2 WebSearches per `peer-tracker/references/refresh-strategy.md` (per-creator query templates in `tracked-creators.md`)
  3. Extract per `peer-tracker/references/pattern-extraction.md`: top 3 recent posts (last 30d), hook pattern delta, status (active/silent/pivoted), reach update
  4. Submit findings: `python3 peer-tracker/scripts/peer_tracker.py apply-refresh --creator "<name>" --findings '<json>'`
- After all 4 (or 5): run `python3 peer-tracker/scripts/peer_tracker.py stats` to confirm coverage
- Surface to Mayank any creator marked `silent` (60+ days no posts) or `pivoted` (off-pillar) — he decides whether to drop / pause / move pillar

Total ~10-15 min. Full 15-creator cycle completes every ~4 weeks.

## Step 3 — Build the calendar

Invoke `content-calendar` for the **upcoming** ISO week (not the current one). Compute upcoming week as next Monday's ISO week. E.g., if today is Sun 2026-04-19, upcoming week = 2026-W17 (Mon 2026-04-20 onwards).

Run via skill invocation or directly via:
```bash
python3 "Desktop/Claude Skills/skills/content-calendar/scripts/build_calendar.py" --week 2026-WXX
```

Verify the calendar file at `brand/calendars/2026-WXX.md` was written and has ≥7 slots.

If content-calendar emits BLOCKING gaps (CRITICAL severity), surface them to Mayank and pause for input.

## Step 4 — Draft each slot

For each calendar slot in the new week file:
1. Read the assigned `entry_id` and `channel`
2. Look up the idea-bank entry by `entry_id`
3. Invoke post-writer for that entry + channel:
   - This is Claude generating prose. Use the post-writer skill in this session.
4. Save to `brand/queue/pending-approval/<date>-<entry_id>-<channel>-<format>.md`
5. Validate via post-writer's `validate_post.py`. Fix any HARD-RULE violations before moving on.

If a slot has no matching idea-bank entry, surface a WARNING and skip that slot.

## Step 5 — Repurpose to other channels

For each Mon/Wed/Fri "anchor" post (the LinkedIn primary), check if content-calendar marked it for repurposing. If yes:
- Invoke repurpose for each target channel (X thread, IG carousel, FB, WA Status as marked)
- Each variant lands in `pending-approval/` with `repurpose_source` frontmatter
- Source draft frontmatter gets updated with `repurposed_into: [...]`

## Step 6 — Generate visual briefs

For each draft whose channel/format requires media (carousels, quote cards, animated, reels):
- Invoke visual-generator with target format
- Brief lands at `brand/queue/briefs/<date>-<entry_id>-<target>-brief.md` (queue/ stays at top — briefs/ is inside queue/)
- Surface to Mayank: "These N briefs need rendering in Claude Design / Hyperframes"
- Do NOT auto-render — that's a manual creative step

## Step 6.5 — Review UI (human gate)

Before writing scheduled_at, hand off to the human for approve / edit / reject:

```bash
python3 "Desktop/Claude Skills/skills/scheduler-publisher/scripts/review_queue.py"
```

This:
1. Fires a macOS notification: "N drafts ready for review"
2. Opens `http://127.0.0.1:8765` in the default browser
3. Renders a dark-mode card for each draft (channel badge, scheduled time, hook preview, full body expandable, 3 buttons: Approve / Edit / Reject)
4. On click, writes `posting_status: approved|rejected|edit_requested` to frontmatter over AJAX
5. "Done" button → server shuts down + fires summary notification ("X approved, Y edits, Z rejected")

Claude should wait for the server to exit (script blocks on the user's "Done") before proceeding to Step 7. Drafts with `posting_status: rejected` are skipped by apply_calendar + tick.py. Drafts with `posting_status: edit_requested` are opened in VS Code for manual edits; user re-runs review after editing, or marks them approved manually.

## Step 7 — Apply calendar (write scheduled_at to each draft)

Run scheduler-publisher's apply_calendar:
```bash
python3 "Desktop/Claude Skills/skills/scheduler-publisher/scripts/apply_calendar.py" --week 2026-WXX
```

This writes `scheduled_at` (ISO 8601 with TZ Asia/Kolkata) and `posting_status: scheduled` into each draft's frontmatter. From here, scheduler-publisher's tick.py will ship them at their scheduled times.

## Step 8 — Summary report to Mayank

Produce a markdown summary:
- Calendar week: 2026-WXX
- Slots filled: X / Y
- Drafts pending visual rendering: N (list with brief paths)
- Repurposed variants: M
- Idea-bank entries flipped raw → shaped: K
- Drafts scheduled: P
- Warnings: pillar shortage, missing entries, etc.

Write the summary to `brand/_engine/weekly-ritual/sunday-2026-WXX.md` for traceability.

## Step 9 — Update state

Write to `brand/_engine/weekly-ritual.state.json`:
```json
{
  "last_fired_sunday": "2026-04-19T09:00:00+05:30",
  "last_completed_sunday": "2026-04-19T09:42:13+05:30",
  "last_calendar_week": "2026-W17"
}
```

## Manual user steps remaining after Sunday ritual

1. Review drafts in `pending-approval/` (Mayank reads + edits if needed)
2. Render any visual briefs in Claude Design / Hyperframes (manual creative, ~10-30 min per asset)
3. Drop the rendered media into `brand/queue/assets/<source-id>/` (visual-generator's `import_assets.py` handles)

After that, scheduler-publisher takes over autonomously.
