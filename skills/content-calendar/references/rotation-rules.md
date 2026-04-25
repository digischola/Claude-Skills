# Rotation Rules (Pillar Balance + Format Variety + AI-Theme Cadence)

Logic the generator applies when matching idea-bank entries to weekly slots.

## Input state

- **Slots:** the week's slot grid from `cadence-templates.md` (usually 10-12 slots per week in Phase 1)
- **Entries:** all idea-bank entries with `status: raw` (no `scheduled_week` set)
- **Brand wiki:** pillars, channel-playbook, voice-guide
- **Phase:** read from channel-playbook.md (currently Phase 1)

## Matching algorithm (in priority order)

### Priority 1 — Pillar-locked day slots

Monday, Wednesday, Friday have pillar-locked defaults:
- Mon → Pillar 1 (Landing-Page Conversion Craft)
- Wed → Pillar 2 (Solo Freelance Ops)
- Fri → Pillar 3 (Small-Budget Paid Media)

For each pillar-locked slot, look up raw entries with `suggested_pillar == {slot pillar}`. Pick the freshest (most recent `captured_at`).

If no matching entry exists → gap flag, slot left unfilled.

### Priority 2 — Repurpose mapping

After a Mon/Wed/Fri slot is filled, auto-fill the auto-repurpose targets per `cadence-templates.md` repurpose table:
- Mon LI → Tue X thread + Sat IG (same entry_id, different `format`)
- Wed LI → Wed X single tweet
- Fri LI → Fri X thread + Sat carousel

Mark these slots with `repurpose_of: {source entry_id}` so post-writer knows to adapt format, not re-draft from scratch.

### Priority 3 — Flex slots (Thursday LI carousel, additional X fresh tweets)

Flex slots take whatever raw entry best fits the format (carousel favors structured/numerical entries; fresh single tweet favors observational or contrarian entries).

If multiple candidates, priority:
1. Pillar that has NOT been covered this week yet (rebalance)
2. Entry type matching format (client-win + carousel; observation + single tweet)
3. Freshness (most recent captured_at)

### Priority 4 — Remaining flex slots

If slots still unfilled after matching all raw entries, gap-flag them. Never pad with low-quality or synthetic content.

## Format-fit heuristic

| Entry type | Best LI formats | Best IG formats | Best X formats |
|---|---|---|---|
| client-win | carousel, text-post | carousel, Reel | thread |
| insight | text-post | caption + image | single tweet |
| experiment | text-post | carousel | thread |
| failure | text-post (vulnerability works long-form) | story/Reel | thread (rare) |
| build-log | text-post, video | Reel | thread |
| client-comm | text-post | — | thread |
| observation | text-post (short) | — | single tweet |

The calendar suggests a format per slot; post-writer applies the actual hook category + voice framework.

## Pillar balance check

After assigning slots, count slots filled per pillar. A balanced week has:
- Pillar 1: 1-2 slots (LinkedIn Mon + repurposes)
- Pillar 2: 1-2 slots (LinkedIn Wed + repurposes)
- Pillar 3: 1-2 slots (LinkedIn Fri + repurposes)

Imbalance >2:1 ratio (e.g., Pillar 1 has 4 slots, Pillar 3 has 0) triggers a warning in the calendar file: "Pillar 3 under-represented; capture more Small-Budget Paid Media moments next week."

## AI-theme cadence check

Count slots where the source entry has AI-related tags (Claude, Perplexity, AI, Lovable, Remotion, Wabo, Canva) OR whose raw_note mentions an AI workflow.

Target: **1 in 3 LinkedIn posts** should be AI-themed (~33%).

- 0 AI-themed in 4 LinkedIn posts → warning: "This week has no AI-theme content; the brand loses the AI-native operator edge. Consider flexing one slot to an AI-workflow entry."
- 3+ AI-themed in 4 LinkedIn posts → warning: "This week is AI-heavy (75%+). Rebalance next week toward pure case-study or operator content to preserve credibility."

## Format variety check

Scan the week's LI slots for format repetition.

- 3 consecutive text-posts → warning: "Week leans text-heavy. Swap Thursday to carousel if not already."
- 4 consecutive text-posts → critical: must rebalance. Flag the 4th slot for carousel override.

## Channel distribution check

Target Phase 1:
- LinkedIn: 4 slots/week (critical)
- Instagram: 1-3 slots/week
- X: 5-7 slots/week
- Facebook: 1 slot/week
- WhatsApp: 0 (Phase 1 dark)

Under-delivery on LinkedIn = critical warning. LinkedIn is the whole Phase 1 strategy.

## Themed-week override

When the user passes `--theme {pillar-name}`, the entire week's pillar-locked defaults shift to that pillar:
- All Mon/Wed/Fri LI slots → themed pillar
- Thu/Sat flex slots still pick best-fit from any pillar

This is for launch weeks (e.g., case-study drop, tool unveil). Default: OFF (balanced).

## Entry status transitions (after calendar is written)

For every entry that was matched to a slot:
- `status: raw` → `status: shaped`
- Add field: `scheduled_week: "YYYY-WXX"` (ISO week)

If the calendar is regenerated for the same week, existing entries with `scheduled_week == current_week` are kept in their slots. The script should never re-randomize a week that's already been planned.

If the user deletes the calendar file and regenerates, the script resets matched entries back to `raw` first (unless `--keep-status` flag passed).

## What the generator does NOT do

- Does NOT draft posts (that is post-writer's job)
- Does NOT publish (that is scheduler-publisher's job, future)
- Does NOT edit hook categories (content-calendar only notes the planned hook; post-writer picks 3 candidates on run)
- Does NOT auto-schedule — the calendar is a plan, the user still triggers post-writer per slot
