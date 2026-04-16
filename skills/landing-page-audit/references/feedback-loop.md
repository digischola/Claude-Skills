# Feedback Loop & Self-Improvement Protocol

How the landing page audit skill learns from every use.

---

## After Every Audit Session

1. **Review the output** — Did every finding have a specific fix recommendation? Were scores consistent with the detailed criteria? Did the dashboard render correctly with all interactive elements?

2. **Capture learnings** — anything discovered during the session:
   - Audit criteria that needed more/less depth for this page type
   - Common patterns across client pages (recurring issues)
   - Dashboard sections the client found most/least useful
   - Fix recommendations that were too vague or too detailed
   - Page types that needed criteria the current checklists don't cover
   - Scoring calibration — did the scores feel right for the page quality?

3. **Update the Learnings & Rules section** in SKILL.md with concise, actionable entries.

4. **Prune quarterly** — remove obvious, redundant, or outdated entries.

## Learnings Format

```
- [DATE] [PAGE TYPE] Finding: {what was learned}. Action: {what to do differently}.
```

Example:
```
- [2026-04] [Restaurant Lead Gen] Finding: Restaurant pages almost always have stock food photography instead of real dishes — this is a top-3 conversion killer for food businesses. Action: Flag stock food images as CRITICAL, not MAJOR, for restaurant clients.
```

## What Gets Logged vs What Doesn't

**Log:**
- Patterns that repeat across 2+ audits
- Scoring calibration adjustments (criterion was weighted too high/low)
- Page-type-specific criteria that the generic checklist missed
- Client feedback on which recommendations they actually implemented
- Dashboard design feedback

**Don't log:**
- One-off page quirks
- Generic "be more thorough" observations
- Anything already covered in the reference checklists
- Redundant entries

## Max Size

Learnings section in SKILL.md stays under 30 lines. Promote repeated patterns into the reference checklist files.
