---
name: hook-library
description: "Standalone hook-pattern catalog with tier system, queryable by post-writer / repurpose / case-study-generator / weekly-ritual. Wraps post-writer's existing 35-pattern hook-library.md as the seed; adds (1) Tier system: Tier 1 (promoted, performance-confirmed winners — top priority for first-choice draft, max 8 per pillar) / Tier 2 (standard, default tested patterns) / Tier 3 (experimental, recently-added trial patterns). (2) CLI for queries: list patterns by pillar/channel/tier/category, get full pattern details, search by keyword, show stats. (3) Promotion API: performance-review can auto-suggest tier moves (4 consecutive HITs → Tier 1 candidate); Mayank confirms manually. (4) Sync: re-parses post-writer's reference file when Mayank manually adds new patterns. Each pattern stored in data/hooks.json with: id, name, category, tier, formula structure, examples, best_for (pillars/channels/formats), originator, performance_signal, use_count, last_used_at. Use when user says: hook library, list hooks, find hooks for, promote hook, demote hook, hook stats, what hooks for X pillar, sync hooks, top hooks, tier 1 hooks. Do NOT trigger for: drafting a post (use post-writer), creating new hook patterns from scratch (manual edit + sync), measuring hook performance (use performance-review)."
---

# Hook Library

Standalone catalog + tier system for the 35+ hook patterns. Source of truth for hook discovery; downstream skills (post-writer, repurpose, case-study-generator) query via CLI.

## Why this exists (split from post-writer)

post-writer originally embedded the hook library as `references/hook-library.md` — fine for 1 skill consuming it. Now multiple skills need hooks (post-writer drafts, repurpose adapts hooks, case-study-generator picks bundle hooks, weekly-ritual chooses hooks during Sunday draft pass), AND performance-review needs to feed back winner data.

A standalone skill enables:
1. Queryable catalog (Tier 1 vs all, by pillar, by channel)
2. Tier system (winners get promoted, losers get demoted) without touching post-writer's file
3. Performance loop: HITs / FLOPs auto-suggest tier moves
4. Single source of truth — post-writer's reference file becomes a generated mirror

## Context Loading

**Read inputs:**
- `data/hooks.json` — master catalog (machine-readable; source of truth)
- `post-writer/references/hook-library.md` — the seed file (parsed initially via `sync-from-post-writer`; re-parsed when Mayank manually adds patterns)
- `Desktop/Digischola/brand/_engine/wiki/voice-guide.md` — for filter rules (no em dashes, no hype, etc.)
- `Desktop/Digischola/brand/_engine/wiki/pillars.md` — for pillar mapping
- (Optional) `brand/performance/YYYY-WXX.md` — performance-review output that triggers auto-promotion suggestions

**Write outputs:**
- `data/hooks.json` — tier changes, use_count increments, last_used_at, performance_signal
- `data/promotion-log.json` — history of all tier changes (auditable)
- (Optional) `post-writer/references/hook-library.md` — regenerated mirror via `export --target post-writer`

**Shared context:**
- `.claude/shared-context/analyst-profile.md` — workflow, voice standards (no em dashes, no hype, conservative client naming)
- `shared-context/output-structure.md` — Digischola uses queue-based structure (NOT outputs/working/ split); after content drops, run `python3 ~/.claude/scripts/build_digischola_index.py` to refresh the index

**Skill references:**
- `references/hook-pattern-anatomy.md` — what makes a pattern, how to add one
- `references/tier-system.md` — Tier 1/2/3 definitions, promotion + demotion rules
- `references/pattern-index.md` — overview of categories + counts
- `references/usage-by-skill.md` — how each downstream skill queries hook-library
- `references/feedback-loop.md`

## Tier System (summary, full in references/tier-system.md)

| Tier | Role | Cap | Source |
|---|---|---|---|
| **1 — Promoted** | Performance-confirmed winners. First-choice for draft. | Max 8 per pillar | performance-review auto-suggests (4 consecutive HITs); Mayank confirms |
| **2 — Standard** | Tested patterns from initial 35. Default tier. | No cap | Initial seed + manual additions |
| **3 — Experimental** | Recently added; on trial. Used cautiously by post-writer. | Max 5 per pillar | Manual additions OR Claude proposes from trend-research |

Tier moves are logged in `data/promotion-log.json` with reason + timestamp + source.

## Process

### Initial setup (one-time)

```bash
python3 scripts/hook_lib.py sync-from-post-writer
```

Parses `post-writer/references/hook-library.md`'s 35 patterns, populates `data/hooks.json`, all start as Tier 2. Reports parsed count.

### Daily use (queries from other skills)

```bash
# What are the Tier 1 hooks for LP Craft on LinkedIn?
python3 scripts/hook_lib.py list --tier 1 --pillar lp-craft --channel linkedin

# Get full details on one pattern
python3 scripts/hook_lib.py get brutal-truth-text-post

# Search by keyword
python3 scripts/hook_lib.py search "contrarian"

# Show counts per tier per pillar
python3 scripts/hook_lib.py stats
```

post-writer's flow becomes:
1. Identify pillar + channel from idea-bank entry
2. Query hook-library: `list --tier 1 --pillar X --channel Y` (top priority)
3. If <3 Tier 1 matches → fall back to Tier 2
4. Pick 3 candidates per voice-frameworks logic, draft post, run validate_post.py

### Promotion / demotion (from performance-review feedback)

```bash
python3 scripts/hook_lib.py promote brutal-truth-text-post --reason "4 HITs in last 28d (LI, +220% vs baseline)"
python3 scripts/hook_lib.py demote question-stack-li --reason "3 FLOPs in last 21d"
```

Both write to `data/promotion-log.json` + update tier in `hooks.json`.

### Sync after manual edits

If Mayank adds a new pattern to `post-writer/references/hook-library.md`, run:

```bash
python3 scripts/hook_lib.py sync-from-post-writer
```

This re-parses + adds new patterns as Tier 3 (experimental until proven).

### Export (regenerate post-writer's mirror)

```bash
python3 scripts/hook_lib.py export --target post-writer
```

Regenerates `post-writer/references/hook-library.md` from `data/hooks.json`. Optional — only if Mayank wants the post-writer file to reflect tier changes / new patterns visually.

## Output Checklist

- [ ] `data/hooks.json` populated with 35+ patterns from post-writer (after initial sync)
- [ ] Each pattern has tier (1/2/3), category, channel/pillar fit, originator
- [ ] CLI queries return correct filters
- [ ] Promotion / demotion writes to log
- [ ] post-writer can fall back to its local file if CLI unavailable

## Anti-patterns

- Do NOT auto-promote without performance-review evidence — Tier 1 is reserved for confirmed winners.
- Do NOT exceed 8 patterns in Tier 1 per pillar — promotes mediocre patterns + clutters first-choice list.
- Do NOT exceed 5 in Tier 3 per pillar — too many experiments simultaneously dilutes signal.
- Do NOT delete patterns from `data/hooks.json` directly — demote to Tier 3 + flag with `archived: true`.
- Do NOT rewrite post-writer's hook-library.md by hand once `export --target post-writer` is the source-of-truth path; the export will overwrite manual edits.
- Do NOT use a hook >2 weeks apart per pillar — `last_used_at` filter prevents repetition.

## Learnings & Rules

<!--
Format: [DATE] [CONTEXT] Finding → Action. Keep under 30 lines.
-->
- [2026-04-20] [Initial build] Built as a wrapper around post-writer's existing 35-pattern reference. `sync-from-post-writer` parses the markdown table format (8 categories with 3-5 patterns each) into `data/hooks.json` with all patterns starting at Tier 2. CLI exposes list/get/search/promote/demote/sync/export/stats. Promotion log at `data/promotion-log.json` tracks all tier changes with reason + timestamp + source (performance-review / manual / claude-suggested).
- [2026-04-20] [Tier caps] Tier 1 capped at 8 per pillar (else first-choice list bloats). Tier 3 capped at 5 per pillar (else too many experiments dilute signal). Tier 2 uncapped — default home for tested patterns. Caps enforced by `promote` command refusing to add a 9th Tier 1 pattern; user must demote one first.
- [2026-04-20] [Cross-skill] Downstream consumers (post-writer, repurpose, case-study-generator) call `hook_lib.py list/get` for queries. They MUST handle the case where hook-library is offline (script error / missing file) by falling back to their local cached reference. post-writer's `references/hook-library.md` becomes a generated mirror (via `export --target post-writer`) so the fallback path stays current.
- [2026-04-29] [STRUCTURAL REFACTOR] Folder convention changed: skill internals (idea-bank.json, brand DNA wiki, _mining, _research, media assets, configs) now live in `Digischola/brand/_engine/` subfolder; daily-workflow folders (queue/, calendars/, performance/, videos/, social-images/) stay at top of `Digischola/brand/`. → Updated all path references in SKILL.md, references/, scripts/, evals/.
