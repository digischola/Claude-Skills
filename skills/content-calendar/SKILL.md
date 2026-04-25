---
name: content-calendar
description: "Weekly content planner for the Digischola personal brand. Reads the idea-bank and channel-playbook, applies pillar rotation (Mon LP Craft / Wed Solo Ops / Fri Small-Budget Paid Media), assigns entries to 10-12 weekly slots across LinkedIn + X + Instagram + Facebook, auto-repurposes one idea to multiple channels (Mon LI → Tue X thread → Sat IG Reel), detects gaps (pillar shortage, AI-theme cadence, total-volume) and surfaces them honestly, and flips matched idea-bank entries raw → shaped. Writes a per-week markdown file to Desktop/Digischola/brand/calendars/YYYY-WXX.md that post-writer consumes slot-by-slot. Use when user says: plan next week, content calendar, weekly plan, build the calendar, content plan, schedule my posts, week plan, content schedule, what should I post next week, plan my content, build-calendar. Do NOT trigger for: drafting an individual post (use post-writer), capturing a new idea (use work-capture), publishing (use scheduler-publisher — future skill), monthly or quarterly strategy (out of scope for v1)."
---

# Content Calendar

Plan next week's posts across all channels by pulling from the idea-bank. Outputs a per-week markdown file that lists every slot (day / channel / format / pillar / assigned entry) plus an ordered list of which slots to run `post-writer` on first. Detects and surfaces gaps honestly.

## Context Loading

Read before running:

**Brand wiki (required):**
- `Desktop/Digischola/brand/pillars.md` — Status MUST be LOCKED
- `Desktop/Digischola/brand/channel-playbook.md` — phase + weekly rhythm
- `Desktop/Digischola/brand/voice-guide.md` — register-per-channel for planned slots
- `Desktop/Digischola/brand/idea-bank.json` — source entries

**Skill references:**
- `references/cadence-templates.md` — Phase 1 slot grid (Mon LI / Wed LI / Fri LI / Thu carousel / Sat IG)
- `references/rotation-rules.md` — matching algorithm, pillar balance, format variety, AI-theme cadence
- `references/gap-detection.md` — gap thresholds + BLOCK conditions

**Shared context:**
- `.claude/shared-context/analyst-profile.md`
- `.claude/shared-context/accuracy-protocol.md`

## Inputs

1. **Brand folder path** (required) — e.g. `/Users/digischola/Desktop/Digischola`
2. **Target week start** (optional; default: next Monday) — must be a Monday
3. **Theme override** (optional) — one of the 3 pillar names. All Mon/Wed/Fri slots lock to this pillar for the week.
4. **Dry-run flag** (optional) — print the plan without writing files or flipping entry statuses.

## Process

### Step 1: Validate pillars LOCKED

Script runs `load_pillars_status()`. If `pillars.md` first 20 lines do not show `Status: LOCKED`, exit 2 with a prompt to run `personal-brand-dna` first.

### Step 2: Load idea-bank

Script loads `idea-bank.json` and filters to entries with `status: raw` AND no `scheduled_week` set (not already assigned to a previous week).

### Step 3: BLOCK checks

Refuse to generate (exit 2) when:
- Idea-bank has 0 raw entries → "Run work-capture first"
- Queue has >10 pending-approval drafts → "Clear the queue first"

### Step 4: Build the week slot grid

Default Phase 1 grid per `references/cadence-templates.md`:

| Slot ID | Day | Channel | Format | Pillar lock |
|---|---|---|---|---|
| `mon-li` | Mon | LinkedIn | text-post | Pillar 1 (LP Craft) |
| `tue-x-thread` | Tue | X | thread | (repurpose of mon-li) |
| `tue-x-fresh` | Tue | X | single | flex |
| `wed-li` | Wed | LinkedIn | text-post | Pillar 2 (Solo Ops) |
| `wed-x` | Wed | X | single | (repurpose of wed-li) |
| `thu-li-carousel` | Thu | LinkedIn | carousel | flex |
| `thu-x-fresh` | Thu | X | single | flex |
| `fri-li` | Fri | LinkedIn | text-post | Pillar 3 (Paid Media) |
| `fri-x-thread` | Fri | X | thread | (repurpose of fri-li) |
| `sat-ig` | Sat | Instagram | reel-or-carousel | (repurpose candidate) |
| `sat-x` | Sat | X | single | flex |
| `sun-rest` | Sun | none | engagement-outbound-day | (no original posts) |

Themed week override (`--theme "{pillar-name}"`) changes all Mon/Wed/Fri locks to the same pillar.

### Step 5: Match entries to slots

Four-pass algorithm per `references/rotation-rules.md`:

1. **Pillar-locked slots first.** Pick freshest raw entry per locked pillar.
2. **Repurpose inheritance.** Repurpose slots inherit the source slot's entry_id.
3. **Saturday IG repurpose.** Pick the strongest LI slot entry to reuse as Reel/carousel.
4. **Flex slots (Thu carousel, Tue/Thu/Sat fresh X).** Pick best-fit remaining entry, favoring under-represented pillars.

### Step 6: Gap detection

Per `references/gap-detection.md`, produce alerts at three severities:

- **CRITICAL** — pillar-locked slot has 0 matching entry; pillar has 0 raw entries in bank; total raw entries 1-3
- **WARNING** — pillar has 1 raw entry only; 4-6 total entries; 0 AI-themed entries in bank; uniform format across week
- **INFO** — flex slot empty; monotone entry types

### Step 7: Write calendar file

Unless `--dry-run`, write markdown to `Desktop/Digischola/brand/calendars/{ISO-week}.md`. Includes:
- Weekly overview table (day / channel / format / pillar / entry / repurpose flag)
- Run-order list for post-writer
- Gap alerts (bucketed CRITICAL / WARNING / INFO)
- Distribution summary (slots filled, channel counts, pillar coverage, AI-theme density)

### Step 8: Flip entry statuses

For every entry matched to a slot: change `status: raw` → `status: shaped`, add `scheduled_week: {ISO-week}`. Atomic write via temp file + rename.

If re-running for the same week, matched entries are kept in slots. If the calendar file is deleted first, a fresh regeneration picks fresh entries.

### Step 9: Exit code summary

- Exit 0: clean week, no gaps
- Exit 1: warnings or critical gaps (calendar still written; user notified)
- Exit 2: BLOCKED (empty bank OR queue backlog OR pillars not LOCKED)

### Step 10: Feedback Loop

Read `references/feedback-loop.md`. Add dated learning if user overrode slot assignments or gap patterns recur.

## Output Checklist

- [ ] pillars.md status confirmed as LOCKED (script gate)
- [ ] Week start resolved (Monday)
- [ ] All CRITICAL block conditions passed (non-empty bank, queue under cap)
- [ ] Slot grid built (12 slots for Phase 1 balanced week)
- [ ] All 3 pillar-locked slots (Mon/Wed/Fri) either filled or CRITICAL-flagged
- [ ] Repurpose chain applied (Mon LI → Tue X thread; Fri LI → Fri X thread; Sat IG from strongest LI)
- [ ] Gap alerts generated at correct severity
- [ ] Calendar markdown written to `brand/calendars/{ISO-week}.md`
- [ ] Entries flipped raw → shaped with `scheduled_week` set

## Anti-patterns

- Do NOT pad empty slots with synthetic or duplicate-with-no-purpose content. A partial calendar beats a padded one.
- Do NOT silently drop the CRITICAL / WARNING / INFO distinction. Severity matters.
- Do NOT modify entries already at status `shaped`, `drafted`, `scheduled`, or `posted`.
- Do NOT run this skill to write posts. It plans; `post-writer` writes.
- Do NOT mix client-skills track and personal-brand track. This skill is personal-brand only.

## Learnings & Rules

<!--
Format: [DATE] [CONTEXT] Finding → Action. Keep under 30 lines. Prune quarterly.
See references/feedback-loop.md for protocol.
-->
- [2026-04-18] [Initial build] Built v1 Phase 1 balanced-week generator. 12 slots (4 LI + 6 X + 1 IG + 1 rest). Pillar-lock rotation Mon/Wed/Fri. Auto-repurpose Mon LI → Tue X + Sat IG; Fri LI → Fri X. Gap detection at 3 severities with BLOCK on empty bank or queue backlog >10. Flips `raw` → `shaped` with `scheduled_week` field.
- [2026-04-18] [Design decision] v1 does not track historical performance. When `performance-review` ships, it should feed: hooks promoted to Tier 1, pillar weightings for rotation, winning formats per day. Rotation-rules.md has a placeholder section for this.
- [2026-04-18] [Design decision] Themed-week (`--theme`) is an opt-in override, not a default. Balanced mode is the operational default.
- [2026-04-22] [Ambiguous-format resolver — user caught the gap] W18 shipped with ZERO video content because the Sat IG slot's `format` was literally `reel-or-carousel` — a decision-punt string that forced Step 6 (visual-generator) to pick. Downstream had no rule, so it always defaulted to carousel. User asked "we did not create any video why so?". Root cause: Skill Protocol Supremacy violation — calendar should commit to one format at build time. Fix: added `resolve_ambiguous_format()` (Pass 5 in `match_slots_to_entries`) with rule: **default reel (IG algorithmic growth bias); override to carousel only when entry is data-heavy** (benchmark/median/threshold/tier/floor keywords, 3+ numeric signals, or CAROUSEL_TAGS). Honors REEL_TAGS (case-study, transformation, win, behind-the-scenes) as explicit reel overrides. Resolutions appear inline in calendar markdown with ‡ marker + reason line. Follow-up finding: W18's Sat IG entry (LP benchmark data) STILL resolves to carousel under the new rule because it's legitimately data-heavy. Real unlock is UPSTREAM: idea-bank is currently 15-of-17 trend entries (data-heavy by design), so Reels stay rare until work-capture adds story/win/transformation entries. Target mix: 60% data-heavy / 40% story-heavy entries for healthy Reel cadence.
