# Ad Copywriter — Feedback Loop Protocol

Run this at session close (mandatory) and after every battle test.

## Session Review Checklist

### Output Quality
1. Did all Google headlines pass ≤ 30 char validation?
2. Did all Google descriptions pass ≤ 90 char validation?
3. Did all Meta primary text stay under 125 chars (or flag if over)?
4. Were source labels ([BRIEF], [GENERATED], [ADAPTED]) applied to every copy block?
5. Did frameworks match the selection logic (PAS for problem-solving, BAB for transformation, etc.)?
6. Were proof elements from creative brief integrated naturally (not forced)?
7. Did image prompts use the `image_gen_prompt_prefix` from creative brief?
8. Were video VO scripts clean (no stage directions, no parentheticals)?
9. Did the combined VO script read as one natural, continuous spoken text?
10. Did campaign names match across report, Google CSV, and Meta CSV?

### Process Quality
1. Did the mode detection (downstream vs standalone) work correctly?
2. Were reference files loaded only as needed (not all upfront)?
3. Did validate_output.py catch any issues before delivery?
4. Were A/B variants from creative brief reflected in the copy?
5. Did persona-specific hooks drive different copy angles?

### What Broke / What Was Unexpected
- Document anything that didn't go as expected
- Note any creative brief fields that were missing or ambiguous
- Note any character limit violations that required rewriting
- Note any framework that didn't fit the campaign type

## Learning Entry Format

Add to SKILL.md Learnings & Rules section:

```
- [DATE] [CLIENT TYPE] Finding: {what happened} → Action: {what was changed/learned}
```

Rules:
- Keep under 30 lines total (prune quarterly)
- Be specific — "character limits violated" is useless, "H7 was 32 chars because 'certification' is 13 chars alone" is useful
- Action must be concrete — what changes in the skill, script, or reference file
- If no action needed, write "Action: No change — edge case, not a pattern"

## Quality Benchmarks

After 3+ battle tests, track these metrics:
- % of headlines that pass char limits on first generation (target: 95%+)
- % of copy blocks with source labels (target: 100%)
- Average image prompt word count (target: 40+ words)
- VO scripts clean rate (target: 100% — zero stage directions)
- Cross-file campaign name match rate (target: 100%)
