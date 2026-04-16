# Feedback Loop & Self-Improvement Protocol (Level 6)

This file defines how the market research skill learns from every use and gets better over time.

---

## How It Works

After every research session, before closing:

1. **Review the output** against the accuracy checklist — did any data points slip through without source labels? Were blanks properly explained? Were there inferred conclusions that should have been flagged?

2. **Capture learnings** — anything discovered during the session that should improve future runs. This includes:
   - Perplexity prompt adjustments that produced better/worse results
   - Research dimensions that needed more/less depth for this client type
   - Dashboard sections that the client found most/least useful
   - Data sources that were reliable vs unreliable
   - Time/effort distribution that could be optimized

3. **Update the Learnings & Rules section** in SKILL.md with concise, actionable rules — not vague observations but specific "do this / don't do this" entries.

4. **Prune quarterly** — every 3 months, review the learnings section and remove:
   - Obvious rules that are now embedded in the process
   - Contradictory or outdated entries
   - Rules that haven't influenced output quality

## Learnings Format

Each entry in the Learnings & Rules section of SKILL.md follows this format:

```
- [DATE] [CLIENT TYPE] Finding: {what was learned}. Action: {what to do differently}.
```

Example:
```
- [2026-04] [B2B Services] Finding: Perplexity returns better competitor data when you name 2-3 known competitors in the prompt. Action: During intake, always ask user if they know any competitor names to seed the Perplexity prompt.
```

## What Gets Logged vs What Doesn't

**Log:**
- Patterns that repeat across 2+ client research sessions
- Perplexity prompt modifications that measurably improved output quality
- Client/analyst feedback on report sections (what was useful, what was ignored)
- Industry-specific research approaches that worked better than the generic framework
- Dashboard design feedback (sections that needed rework)

**Don't log:**
- One-off client quirks that won't repeat
- Generic "be more thorough" observations
- Anything already covered in the reference files
- Redundant entries that restate existing rules

## Max Size Rule

The Learnings & Rules section in SKILL.md must stay under 30 lines. If it approaches this limit, consolidate related entries and promote the most important patterns into the reference files where they belong (e.g., a repeated Perplexity prompt improvement goes into perplexity-prompt-template.md, not the learnings section).
