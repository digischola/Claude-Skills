# Feedback Loop — peer-tracker

## When to log a learning

Add a dated entry to SKILL.md "Learnings & Rules" when:

- A creator goes silent or pivoted (and Mayank decided to drop / replace)
- A new creator is added to `tracked-creators.md`
- The rotation cadence needs adjusting (e.g., 4/week is too aggressive or too slow)
- A new hook pattern is observed and added to `pattern-extraction.md`
- WebSearch returns insufficient signal for a creator → consider Chrome MCP fallback
- The `apply-refresh` script's update logic broke when post-writer's creator-study.md format changed
- Mayank manually edited a creator's entry and peer-tracker overwrote it (preserve-edits bug)

## Format

```
- [YYYY-MM-DD] [CONTEXT TAG] Finding → Action.
```

Context tags:
- `[Initial build]`
- `[Rotation]` — cadence / scheduling issues
- `[WebSearch]` — Mode 1 quirks
- `[Chrome MCP]` — Mode 2 quirks
- `[Pattern extraction]` — new hooks discovered, parser misses
- `[Topic drift]` — pivot detection issues
- `[Schema]` — refresh-log.json or creator-study.md format
- `[Cross-skill]` — interaction with post-writer

## Cross-skill impact

peer-tracker reads + writes `post-writer/references/creator-study.md`. If post-writer changes the file's structure (new subsections, new heading levels), peer-tracker's parser needs an update.

Quarterly compatibility check:
```bash
python3 scripts/peer_tracker.py validate-creator-study
```

This script reads creator-study.md, attempts to parse all 15 creator sections per the expected schema, and reports any parse failures.

If `apply-refresh` ever overwrites a Mayank-edited "Mimicry approach" line → that's a bug. The script must ONLY touch:
- "Reach" (if reach_update provided)
- "Signature format" (if hook_pattern_delta non-null, append the new pattern; never remove existing)
- "Last refreshed" subsection (always update)
- "Recent samples" subsection (always replace with the new top 3)

## Quarterly review checklist

Every 3 months:
1. Run `peer_tracker.py stats` — see refresh coverage + silent/pivoted counts
2. For each `silent` creator, decide: drop, pause, or wait
3. For each `pivoted` creator, decide: drop, move to different pillar, or note the new niche
4. Audit `pattern-extraction.md` — any new hook patterns observed in the wild that aren't in the catalog?
5. Audit `tracked-creators.md` — are there 5+ high-signal creators per pillar to balance?

## Eval candidates

Add a test case to `evals/evals.json` when:

- A new status type is added (beyond active/silent/pivoted)
- Rotation logic changes
- A new field is added to the findings payload
- A new creator section format is supported

Each test should run in dry-run mode (mock WebSearch, no actual file writes).
