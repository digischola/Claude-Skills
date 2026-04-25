# Usage by Downstream Skill

How each skill that consumes hook-library should call it.

## post-writer

post-writer drafts a single platform-specific post from one idea-bank entry. It needs 3 candidate hooks per draft.

**Recommended call pattern:**

```bash
# Step 1: get tier 1 candidates first (top priority)
python3 hook-library/scripts/hook_lib.py list --tier 1 --pillar <PILLAR> --channel <CHANNEL> --json

# Step 2: if <3 results, fall back to tier 2
python3 hook-library/scripts/hook_lib.py list --tier 2 --pillar <PILLAR> --channel <CHANNEL> --json

# Step 3: optionally include 1 tier 3 experimental
python3 hook-library/scripts/hook_lib.py list --tier 3 --pillar <PILLAR> --channel <CHANNEL> --json --limit 1
```

post-writer then picks 3 candidates per voice-framework rules + presents to Claude (or Mayank) for selection.

After draft is finalized:
```bash
# Mark this pattern as used (increments use_count + sets last_used_at)
python3 hook-library/scripts/hook_lib.py mark-used --id <pattern-id>
```

**Backwards compatibility:** post-writer's existing `references/hook-library.md` stays as a fallback. If `hook_lib.py` errors / file missing, post-writer falls back to grepping its local file. The local file should be regenerated periodically via `hook_lib.py export --target post-writer`.

## repurpose

repurpose adapts a source draft for additional channels. The hook is preserved verbatim across variants by repurpose's existing logic. So repurpose doesn't query hook-library directly for hook selection.

BUT repurpose CAN query for guidance on which patterns work cross-channel:

```bash
# What patterns are best for both LI and X?
python3 hook-library/scripts/hook_lib.py list --channels-all linkedin x
```

This helps repurpose know whether the source's hook is single-channel-only or cross-fits gracefully.

## case-study-generator

case-study-generator picks one hook for the entire 4-deliverable bundle (the hero metric stays verbatim across all 4). It needs a Tier 1 candidate that fits "Numbers Hero" or "Single-Lever Result" or "Small-Budget Hero" (data category).

**Recommended call:**

```bash
python3 hook-library/scripts/hook_lib.py list --tier 1 --category data --pillar <PILLAR> --json
```

If no Tier 1 data hooks for the pillar, fall back to `--tier 2 --category data`.

case-study-generator marks the chosen hook as used:
```bash
python3 hook-library/scripts/hook_lib.py mark-used --id <pattern-id>
```

## weekly-ritual (Sunday Step 4 — drafting)

Sunday's ritual produces 5-7 drafts in one batch. weekly-ritual calls hook-library indirectly through post-writer (Step 4 of sunday-flow.md). No direct call needed.

## performance-review (Friday — feeds tier promotions)

After weekly_review.py buckets posts (HIT / ABOVE / BELOW / FLOP), it scans for hooks that hit the promotion threshold:

```bash
# Suggest tier moves based on last 28d of performance
python3 hook-library/scripts/hook_lib.py suggest-tier-moves --window 28d --json
```

Returns:
```json
{
  "to_promote_to_tier_1": [
    {"id": "brutal-truth-text-post", "reason": "4 HITs / 0 FLOPs in 28d on LI"}
  ],
  "to_demote_from_tier_1": [
    {"id": "question-stack-li", "reason": "3 FLOPs in 21d"}
  ]
}
```

performance-review surfaces these as P1 suggestions in its weekly report. Mayank approves manually:
```bash
python3 hook-library/scripts/hook_lib.py promote brutal-truth-text-post --reason "4 HITs / 0 FLOPs"
python3 hook-library/scripts/hook_lib.py demote question-stack-li --reason "3 FLOPs"
```

## trend-research / peer-tracker

These skills can OBSERVE new hook patterns in the wild. When they see a pattern that doesn't match any existing entry, they can propose addition:

```bash
python3 hook-library/scripts/hook_lib.py add --json '<pattern_payload>' --tier 3 --source claude-proposed
```

The pattern lands as Tier 3 (experimental). Mayank decides whether to keep on next quarterly review.

## Backwards compatibility contract

**Important:** All downstream skills MUST handle hook-library being unavailable:

```python
try:
    candidates = subprocess.run(["python3", "hook_lib.py", "list", ...], ...)
except (FileNotFoundError, subprocess.CalledProcessError):
    # Fall back to local cached reference
    candidates = parse_local_hook_library_md(...)
```

This ensures post-writer / repurpose / case-study-generator never break if hook-library has a bug or is mid-migration. The local cached reference (`post-writer/references/hook-library.md`) is the safety net.

## CLI reference (full)

```
hook_lib.py list [--tier N] [--pillar X] [--channel Y] [--category Z] [--limit N] [--json]
hook_lib.py get <pattern-id>
hook_lib.py search <query> [--limit N]
hook_lib.py promote <pattern-id> --reason "..."
hook_lib.py demote <pattern-id> --reason "..."
hook_lib.py mark-used --id <pattern-id>
hook_lib.py add --json <payload> [--tier N] [--source SRC]
hook_lib.py sync-from-post-writer
hook_lib.py export --target post-writer [--out PATH]
hook_lib.py suggest-tier-moves [--window 28d] [--json]
hook_lib.py stats
hook_lib.py promotion-log [--limit N]
```
