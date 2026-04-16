# Feedback Loop & Self-Improvement Protocol

Defines how the paid-media-strategy skill learns from every use.

---

## After Every Strategy Session

1. **Review output against the checklist** in SKILL.md — did decision logic get explained? Were source labels applied? Were BLANK fields honest?

2. **Capture learnings:**
   - Decision trees that needed adjustment for this business type
   - Platform-specific logic that produced better/worse recommendations
   - Dashboard sections the client found most/least useful
   - Guided questions that were most/least informative
   - Strategy frameworks that needed updating based on platform changes

3. **Update Learnings & Rules** in SKILL.md — concise, actionable entries.

4. **Prune quarterly** — remove obvious rules, contradictions, outdated platform info.

## Learnings Format

```
- [DATE] [CLIENT TYPE] Finding: {what was learned}. Action: {what to do differently}.
```

## What Gets Logged vs What Doesn't

**Log:**
- Decision tree paths that needed a new branch for an edge case
- Platform updates that change strategy logic (new campaign types, bidding changes)
- Budget allocation patterns that consistently over/underperform
- Guided question answers that didn't map cleanly to strategy implications
- Cross-platform allocation ratios that worked better than defaults

**Don't log:**
- One-off client quirks
- Generic "strategy was good" observations
- Anything already in the reference files
- Redundant entries

## Platform Update Protocol

When Meta or Google makes significant platform changes (new campaign types, bidding strategy changes, targeting updates):
1. Update the relevant reference file (meta-ads-system.md or google-ads-system.md)
2. Update strategy-frameworks.md if decision trees are affected
3. Add a learning entry with the date and change summary
4. Flag any active client strategies that might be impacted

## Max Size Rule

Learnings & Rules section in SKILL.md: under 30 lines. Promote repeated patterns into reference files.
