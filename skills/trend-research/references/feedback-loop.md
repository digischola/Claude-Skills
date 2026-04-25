# Feedback Loop — trend-research

## When to log a learning

Add a dated entry to SKILL.md "Learnings & Rules" when:

- A pillar's seed query list needs updating (a query is producing too much noise OR not finding signal)
- A new tracked source is added (new top-of-mind creator) or removed (one went silent)
- A topic blacklist needs expanding (a noise source keeps slipping through)
- The dedup threshold (70%) needs tuning (false positives or false negatives)
- A new auto-reject rule is added (e.g., new hype word emerges)
- Perplexity prompt template needs improvement (responses too shallow / too long / wrong format)
- The relevance scoring rubric needs adjusting (Mayank's content-calendar keeps rejecting score-4 entries)

## Format

```
- [YYYY-MM-DD] [CONTEXT TAG] Finding → Action.
```

Context tags:
- `[Initial build]`
- `[LP Craft]` `[Solo Ops]` `[Paid Media]` — pillar-specific
- `[WebSearch]` — Mode 1 quirks
- `[Perplexity]` — Mode 2 quirks
- `[Dedup]` — duplicate detection issues
- `[Quality filter]` — auto-reject rules
- `[Schema]` — idea-bank entry structure

## Cross-skill impact

When trend-research adds entries to idea-bank, downstream skills consume:
- `content-calendar` — picks entries by pillar, applies pillar rotation
- `post-writer` — drafts from selected entry
- `repurpose` — adapts source draft to additional channels
- `weekly-ritual` — fires this skill on Sunday Step 1

If trend-research changes the idea-bank entry schema, update:
- `work-capture/scripts/validate_entry.py` (if it validates schema)
- `content-calendar/scripts/build_calendar.py` (if it parses fields like `relevance_score`)
- `post-writer/SKILL.md` (if drafting flow expects new fields)

## Quarterly review checklist

Every 3 months, review:

1. **Seed queries** in `pillar-niches.md` — are they still surfacing fresh signal? Add 2-3 new queries per pillar, retire any that have produced 0 hits in 6+ runs.
2. **Tracked sources** — are the 15 named creators still active? Drop silent ones, add 2-3 new ones from peer-tracker's data.
3. **Topic blacklists** — are they still relevant? E.g., "AMP" was 2024-relevant; in 2026 maybe deprecated topic.
4. **Dedup threshold** — has Mayank complained about duplicates slipping through (raise threshold) or about good entries being rejected (lower threshold)?
5. **Auto-reject hype words** — has Mayank rejected entries containing words not in the current list? Add them.

## Eval candidates

Add a test case to `evals/evals.json` when:

- A new auto-reject rule lands
- The dedup threshold changes
- A new pillar is added (unlikely but possible if Mayank's positioning shifts)
- A new mode is added (e.g., daily mini-scan vs weekly deep-scan)

Each test should run in dry-run mode without actually appending to idea-bank.
