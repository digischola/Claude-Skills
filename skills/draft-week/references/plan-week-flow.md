# plan-week-flow

Detailed steps for `draft-week plan-week`. Loaded only when planning a week.

## Inputs

- Target ISO week (default: next week, Mon-Sun in Asia/Kolkata).
- Optional: pillar override, channel-mix override.

## Step 1: Score idea-bank

Filter `idea-bank.json` to entries with `status: raw` or `shaped`. Score each:

```
score = 0.4 * recency + 0.4 * pillar_fit + 0.2 * format_fit
```

- **recency**: 1.0 if captured ≤7 days ago, decay linearly to 0.0 at 60 days.
- **pillar_fit**: 1.0 if entry's `suggested_pillar` matches a pillar in this week's rotation; 0.5 if matches any pillar; 0 otherwise.
- **format_fit**: 1.0 if the entry's `format_candidates` has good fit for the target slot's channel/format; 0.5 if partial; 0 if mismatch.

Entries with score < 0.4 are not eligible for this week.

## Step 2: Pillar rotation

Default rotation per ISO week:

| Day | Pillar |
|---|---|
| Mon | Landing-Page Conversion Craft |
| Tue | mixed (depends on idea bank) |
| Wed | Solo Freelance Ops |
| Thu | mixed |
| Fri | Small-Budget Paid Media |
| Sat | mixed (lighter) |
| Sun | mixed (lighter) |

Override if `pillar.md` flags a pillar as "needs more volume".

## Step 3: Slot assignment (10-12 slots target)

| Channel | Target slots/week | Hard cap |
|---|---|---|
| LinkedIn-text | 3 | 4 |
| LinkedIn-carousel | 1 | 2 |
| X-single + X-thread | 4 | 6 |
| Instagram-carousel | 1 | 2 |
| Instagram-Reel | 1 | 2 |
| Facebook-post | 1 | 2 |
| WhatsApp-status | 1 | 2 |

Auto-repurpose: if a high-score entry fits multiple channels, mark it for write-post on primary channel + repurpose to 1-2 secondaries. Tag `repurpose_target` in the slot.

## Step 4: Time slotting (Asia/Kolkata)

Default times by channel:

| Channel | Time (IST) |
|---|---|
| LinkedIn | Tue/Thu 09:00, Wed 11:00 |
| X (LI-overlap) | 09:30, 14:00, 19:00 |
| Instagram | 12:00 |
| Facebook | 18:00 |
| WhatsApp-status | 21:00 |

These are starts; spread to avoid bunching.

## Step 5: Gap detection

Print a gap report — do NOT silently fill. Surface for user review:

- **Pillar shortage**: pillar X has 0 raw entries for this week.
- **AI-theme cadence**: 0 of N slots will name an AI tool. Brand voice expects ≥1/week.
- **Volume gap**: only N slots possible, target 10-12.
- **Credential cadence**: 0 of N slots will anchor a credential. Brand voice expects 1-2/week.

If gaps are critical, prompt user before writing the calendar file.

## Step 6: Write calendar file

`brand/calendars/YYYY-WXX.md` shape:

```markdown
# Week 2026-W19 (May 4 - May 10)

## Slot 1
- entry_id: 3a3c9bac
- channel: linkedin
- format: text-post
- pillar: Landing-Page Conversion Craft
- scheduled_at: 2026-05-04T09:00:00+05:30
- scheduled_day: Monday
- voice_framework: Graham
- credential_anchor_candidate: thrive_188
- repurpose_target: x-thread

## Slot 2
...
```

## Step 7: Flip status

For every entry assigned to a slot, flip `idea-bank.json` entry status from `raw` → `shaped` via:

```bash
python3 scripts/draft_io.py --brand-folder ... --flip-shaped <entry_id>
```

## Anti-patterns

- Do NOT auto-write the drafts in plan-week. That's `write-post`'s job. Plan-week only assigns slots.
- Do NOT push a slot to a date in the past.
- Do NOT use the same entry twice in one week unless `repurpose_target` is set.
