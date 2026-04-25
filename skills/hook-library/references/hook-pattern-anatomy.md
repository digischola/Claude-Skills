# Hook Pattern Anatomy

What makes a hook pattern, and how to add a new one to the library.

## Required fields per pattern

Each entry in `data/hooks.json` has:

| Field | Type | Required | Purpose |
|---|---|---|---|
| `id` | string (kebab-case) | yes | Unique stable id (e.g., `brutal-truth-text-post`) |
| `name` | string | yes | Human-readable title (e.g., "Brutal Truth Text Post") |
| `category` | string | yes | One of 8 categories (see pattern-index.md) |
| `tier` | int (1, 2, 3) | yes | Current tier per tier-system.md |
| `description` | string | yes | 1-2 sentence what-it-is |
| `formula` | string | yes | Template-style structure (e.g., "Most X are Y. The few who Z...") |
| `examples` | list of strings | yes | 1-3 Mayank-voice adaptations using real Digischola data where possible |
| `best_for` | object | yes | `{pillars: [...], channels: [...], formats: [...]}` |
| `originator` | string | no | Creator who pioneered this format (e.g., "Peep Laja") |
| `credential_anchor_required` | bool | no | Does this hook need a credential drop to land? Default false |
| `voice_framework` | string | no | Which voice framework this pairs with (Hormozi / Naval / etc.) |
| `notes` | string | no | Free-form caveats or pairing tips |
| `tier_history` | list | auto | Tier changes tracked here |
| `last_used_at` | ISO timestamp | auto | Updated when post-writer uses this pattern |
| `use_count` | int | auto | Total times used across all channels |
| `performance_signal` | object | auto | `{hits_28d, flops_28d, hits_total, flops_total, last_perf_check}` |
| `archived` | bool | auto | True if pattern is dropped from default `list` queries |

## How to add a new pattern

### Option A — Manual via JSON

```bash
python3 scripts/hook_lib.py add --json '{
  "id": "founder-vulnerability-confession",
  "name": "Founder Vulnerability Confession",
  "category": "personal-stake",
  "tier": 3,
  "description": "Vulnerable admission of past mistake → reframed as lesson",
  "formula": "I lost [outcome] because I [decision]. Here is the lesson.",
  "examples": [
    "I lost a $4,000/month wellness retainer because I overpromised on a 14-day timeline. Here is the lesson on scope-setting."
  ],
  "best_for": {
    "pillars": ["solo-ops"],
    "channels": ["linkedin"],
    "formats": ["text-post"]
  },
  "originator": "Shreya Pattar",
  "credential_anchor_required": false,
  "voice_framework": "Naval"
}'
```

Adds to `data/hooks.json` as Tier 3 (experimental) with all auto fields initialized to defaults.

### Option B — Append to post-writer reference, then sync

1. Edit `post-writer/references/hook-library.md` and add a new row in the appropriate category table:

```markdown
| 36 | New formula here | Mayank-adapted example | LI | Best-for context |
```

2. Run `python3 scripts/hook_lib.py sync-from-post-writer`

The sync will detect the new row, add it as Tier 3 with auto-generated id, and report what was added.

### Option C — Claude proposes from trend-research / peer-tracker

If trend-research or peer-tracker output flags a new hook pattern observed in the wild (e.g., "Peep Laja started using a Question-Stack Carousel"), Claude can propose it:

```bash
python3 scripts/hook_lib.py add --json '<payload>' --tier 3 --source claude-proposed
```

The promotion log records `source: claude-proposed` so Mayank knows it wasn't a manual addition.

## Quality bar for new patterns

A "real" hook pattern (worthy of adding):
- ≥3 distinct examples can be drafted using it (not just 1 specific situation)
- Fits at least 1 pillar
- Doesn't duplicate an existing pattern (use `search` to check)
- Has a clear opening structure that can be templated

A "fake" pattern (don't add):
- One-off creative line that worked once
- Too specific to a particular client / situation
- Substantially overlaps with an existing pattern (just add another example to that pattern instead)

## Pattern naming conventions

- `id`: kebab-case, descriptive, ≤4 words. Examples: `numbers-hero`, `before-after-visual`, `solo-ops-receipts`
- `name`: Title Case, ≤6 words. Examples: "Numbers Hero", "Before/After Visual", "Solo Ops Receipts Drop"
- Avoid creator names in id/name (e.g., NOT `peep-laja-style`) — patterns transcend their originator

## Update lifecycle

When `post-writer` uses a pattern:
1. Increments `use_count`
2. Updates `last_used_at`
3. Logs to internal post-writer history (per existing reference)

When `performance-review` runs after a post:
1. Computes the post's bucket (HIT / ABOVE / BELOW / FLOP)
2. Calls `hook_lib.py record-performance --pattern-id <id> --bucket HIT --channel linkedin --pillar lp-craft`
3. Updates the pattern's `performance_signal` field
4. May trigger auto-promotion or auto-demotion suggestion

When tier changes:
1. `tier_history` gets an appended entry with from/to/reason/timestamp/source
2. `data/promotion-log.json` also logs (single source of truth for promotion-history queries)
