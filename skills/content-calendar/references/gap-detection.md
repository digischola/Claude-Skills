# Gap Detection (When the Idea-Bank Is Too Thin)

The calendar generator must detect and surface gaps honestly, not pad them with synthetic content.

## Gap types and thresholds

### Gap type 1: Pillar-specific shortage

For each pillar, count raw entries. Thresholds:

| Raw entries in pillar | Severity | Message |
|---|---|---|
| 0 | CRITICAL | "Pillar {name} has zero raw entries. The {day} slot cannot be filled. Capture at least 1 entry this week via work-capture." |
| 1 | WARNING | "Pillar {name} has only 1 raw entry. Next week's {day} slot will be empty unless you capture another." |
| 2+ | OK | (no flag) |

Reported in the calendar file under a "Gap alerts" section.

### Gap type 2: Total volume shortage

Count total raw entries across all pillars.

| Total raw entries | Severity | Message |
|---|---|---|
| 0 | BLOCK | Refuse to generate. Respond: "Idea-bank is empty. Run work-capture on recent client moments, insights, or experiments before planning a week." |
| 1-3 | CRITICAL | "Only {N} raw entries. Week will be mostly gaps. Capture 5+ more via work-capture before Sunday for a full Phase 1 week." |
| 4-6 | WARNING | "{N} entries available; Phase 1 weeks ideally need 6-10 raw entries for balanced slots. Consider capturing more." |
| 7+ | OK | (no flag) |

### Gap type 3: Format shortage

If all 7+ raw entries are the same type (e.g., all client-wins), format variety suffers.

| Distribution | Severity | Message |
|---|---|---|
| All one type | WARNING | "All entries are {type}. Week will read monotone. Aim for a mix: client-win + insight + experiment + build-log." |
| Missing type for scheduled slot | INFO | Context-specific: "Thursday carousel slot works best with a structured entry (experiment or framework-type insight); current pool has none." |

### Gap type 4: AI-theme shortage

Count raw entries with AI tags or AI workflow mentions.

| AI-themed entries | Severity | Message |
|---|---|---|
| 0 of 7+ | WARNING | "No AI-themed entries this cycle. The brand's AI-native-operator positioning is at risk. Capture a recent AI workflow moment." |
| 1+ of 7+ | OK | (no flag) |

### Gap type 5: Channel backlog

Check queue/pending-approval/ for unapproved drafts.

| Unapproved drafts in queue | Severity | Message |
|---|---|---|
| 0-5 | OK | (no flag) |
| 6-10 | WARNING | "{N} drafts pending approval. Clear the queue before adding more via calendar." |
| 11+ | BLOCK | Refuse to generate. "{N} drafts in queue. Approve, ship, or kill pending drafts before planning a new week." |

## Gap output format

In the calendar markdown file, include a clearly flagged section:

```markdown
## Gap alerts

- **CRITICAL:** Pillar 3 (Small-Budget Paid Media) has 0 raw entries. Friday LI slot cannot be filled.
  - Fix: capture 1+ Small-Budget Paid Media moment via work-capture.
- **WARNING:** No AI-themed entries this week. Brand AI-native positioning at risk.
  - Fix: log your next client audit that involved Claude or Perplexity.
- **INFO:** Thursday carousel slot has no structured entries. Consider capturing an experiment or framework moment.
```

If no gaps: "## Gap alerts\n\nNone. Idea-bank is healthy for this week's plan."

## Behavior when gaps BLOCK calendar generation

When a gap severity is BLOCK (empty idea-bank OR queue backlog):

1. Do NOT write the calendar file.
2. Do NOT flip any entry statuses.
3. Return a clear prompt explaining what needs to happen first.
4. Suggest exact next actions.

Example:

```
BLOCKED: idea-bank has 0 raw entries.

Capture 3-5 entries before planning the week. Easy sources:
- Today's client work (a win, a failure, an insight)
- This week's most memorable moment
- A client message that worked well (client-comm type)
- A tool workflow that saved time (build-log + AI-theme)

Run work-capture and come back.
```

## Recap rules

- **Gaps are a feature, not a bug.** Flag them honestly. Never pad.
- **Partial calendars are OK.** A 5-slot week beats a 12-slot week of filler.
- **BLOCK only on truly unusable state** (empty bank, critical queue backlog).
- **Every gap message includes a concrete fix action.** No vague "capture more content" without specifics.
