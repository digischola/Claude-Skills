---
name: peer-tracker
description: "Monthly creator-study refresher. Keeps post-writer's references/creator-study.md current by scanning the 15 named creators (Peep Laja, Jon MacDonald, Harry Dry, Rishabh Dev, Julian Shapiro, Shreya Pattar, Varun Mayya, Dickie Bush, Justin Welsh, Jack Butcher, Barry Hott, Chase Dimond, Cody Plofker, Joly Tematio, Sam Piliero) for fresh top-performing posts, hook patterns, voice signature drift, and topic pivots. Rotation cadence: 4 creators per Sunday over 4 weeks, full cycle monthly. Two modes: (1) AUTONOMOUS — Claude uses WebSearch per creator, parses snippets, updates creator-study.md sections in place; (2) DEEP — Chrome MCP loads each creator's profile (LinkedIn / X) and scrapes last 30 days for richer data. Wired into weekly-ritual Sunday Step 2 (auto-skipped today; building this skill activates it). Use when user says: peer tracker, refresh creators, update creator study, who is posting what, peer refresh, sunday step 2, monthly creator scan. Do NOT trigger for: drafting from a creator's voice (use post-writer), trend research per pillar (use trend-research), capturing a creator's idea as your own content (use work-capture)."
---

# Peer Tracker

Keeps the 15-creator reference file fresh. Rotation: 4 creators per Sunday → full coverage every month. The output is a continuously-current `post-writer/references/creator-study.md` so post-writer's voice mimicry stays sharp.

## Why this exists

`post-writer/references/creator-study.md` was seeded from one Perplexity research run on 2026-04-18. Reach numbers, signature formats, and recent posts go stale within 90 days. Without refresh, post-writer ends up mimicking outdated voice signatures. peer-tracker prevents that decay.

## Context Loading

**Shared context:**
- `.claude/shared-context/analyst-profile.md` — workflow, voice standards (creators are mimicked for inspiration only, never voice-cloned)
- `shared-context/output-structure.md` — Digischola uses queue-based structure (NOT outputs/working/ split); after content drops, run `python3 ~/.claude/scripts/build_digischola_index.py` to refresh the index

**Read inputs:**
- `references/tracked-creators.md` — the 15 creators, their handles, channels, niches, current rotation index
- `references/refresh-strategy.md` — how Claude conducts the per-creator scan
- `references/pattern-extraction.md` — how to identify hooks, voice signatures, topic shifts from snippets
- `data/refresh-log.json` — per-creator last_refreshed_at timestamps + rotation state

**Write outputs:**
- `post-writer/references/creator-study.md` — updates per-creator sections in place (signature format, recent samples, audience size, status)
- `data/refresh-log.json` — bumps `last_refreshed_at` after each successful refresh

## Rotation logic

15 creators / 4 Sundays per month = 4 per Sunday (with one extra creator covered every other week to cycle through all 15 every 3.75 weeks).

Each Sunday:
1. Read `data/refresh-log.json`
2. Sort creators by `last_refreshed_at` ascending (oldest first)
3. Pick the top 4 (or 5 every other week — see schedule)
4. For each picked creator: Mode 1 (WebSearch) refresh
5. Update `creator-study.md` per-creator section
6. Bump `last_refreshed_at` in refresh-log.json

`scripts/peer_tracker.py rotation-due` returns the list of creators due this Sunday.

## Modes

### Mode 1 — Autonomous (default, used by weekly-ritual Sunday Step 2)

For each creator in this Sunday's rotation:
1. WebSearch query: `"<creator name>" LinkedIn OR X 2026 site:linkedin.com OR site:x.com` (or per-creator-specific from `tracked-creators.md`)
2. Get top 5-10 result snippets from last 30 days
3. Identify:
   - Top 3 most-engaging recent posts (from snippets indicating shares/comments)
   - Any new hook patterns vs the existing entry's "Signature format"
   - Topic shifts (creator pivoted off-pillar)
   - Audience metric updates (if visible in snippets)
4. Synthesize a per-creator update payload (see `references/pattern-extraction.md` for the exact schema)
5. Run `peer_tracker.py apply-refresh --creator "<name>" --findings '<json>'`

Total time per Sunday: ~10-15 min (4 creators × 2-3 min each).

### Mode 2 — Deep (Chrome MCP scrape)

When richer data is wanted (e.g., monthly review or onboarding a new tracked creator):

1. Claude in Chrome MCP loads the creator's profile (LinkedIn or X)
2. Scrolls 30 days back, captures top posts by engagement
3. Parses post text + reactions/comments/reshares counts
4. Generates the same update payload as Mode 1
5. Applies via `peer_tracker.py apply-refresh`

Mode 2 takes ~5-8 min per creator and requires Mayank to be logged into LinkedIn / X in Chrome.

## Process — Sunday Step 2 (autonomous)

When invoked by weekly-ritual or directly by Mayank ("peer refresh"):

1. **Pre-check**: `creator-study.md` exists at `post-writer/references/`. Block if not.
2. **Get rotation**: `peer_tracker.py rotation-due --week 2026-W17` → returns 4-5 creator names
3. **For each creator**:
   - Read existing entry from creator-study.md
   - Run WebSearch per `references/refresh-strategy.md`
   - Synthesize update payload
   - Run `peer_tracker.py apply-refresh`
4. **Post-process**:
   - Mark `silent` any creator with 0 recent posts (likely stopped or paused)
   - Flag for Mayank any creator who pivoted off-pillar (drop from list?)
5. **Report**: log to `data/refresh-log.json` + write per-Sunday summary to `data/sunday-2026-W17.md`

## Output Checklist

- [ ] 4-5 creators refreshed this Sunday
- [ ] `creator-study.md` updated in place (each creator's "Recent samples" + "Last refreshed" subsections)
- [ ] `refresh-log.json` updated with new timestamps
- [ ] Sunday summary written
- [ ] Any silent / pivoted creators surfaced for Mayank's decision

## Anti-patterns

- Do NOT rewrite creator-study.md from scratch — update sections in place to preserve Mayank's manual edits.
- Do NOT add new creators in this skill — that's a manual decision (edit `tracked-creators.md`).
- Do NOT scrape paid platforms (LinkedIn Premium analytics, X Premium signals).
- Do NOT mimic the actual creator content into post-writer's drafts — peer-tracker only refreshes the REFERENCE; post-writer still creates original content in Mayank's voice.
- Do NOT auto-drop a creator who pivots off-pillar — flag and let Mayank decide.
- Do NOT exceed 5 creators per Sunday (rate-limit + WebSearch quality concern).

## Learnings & Rules

<!--
Format: [DATE] [CONTEXT] Finding → Action. Keep under 30 lines.
-->
- [2026-04-20] [Initial build] Built as the monthly creator-study refresher. Rotation: 4-5 creators per Sunday over 4 weeks → full coverage of all 15 monthly. Default mode WebSearch (Claude in the loop, no manual setup). Mode 2 Chrome MCP for deeper scrape when needed. State in `data/refresh-log.json` tracks per-creator last_refreshed_at + rotation index. Updates `post-writer/references/creator-study.md` IN PLACE — never rewrites from scratch (preserves Mayank's manual edits). Activates weekly-ritual Sunday Step 2 (was auto-skipped).
- [2026-04-20] [Cross-skill] Reads from + writes to `post-writer/references/creator-study.md`. If post-writer changes that file's structure, peer-tracker's parser may break — keep parser tolerant of minor heading changes. Schedule a quarterly compatibility check: run `peer_tracker.py validate-creator-study` after any post-writer reference edit.
- [2026-04-20] [Silent + pivot detection] If WebSearch returns 0 recent posts for a creator → mark `status: silent`. If creator's recent posts are off-pillar (e.g., Jon MacDonald pivots to general business advice instead of CRO) → mark `status: pivoted` + add note for Mayank. Do not auto-drop — Mayank decides each quarterly review.
- [2026-04-29] [STRUCTURAL REFACTOR] Folder convention changed: skill internals (idea-bank.json, brand DNA wiki, _mining, _research, media assets, configs) now live in `Digischola/brand/_engine/` subfolder; daily-workflow folders (queue/, calendars/, performance/, videos/, social-images/) stay at top of `Digischola/brand/`. → Updated all path references in SKILL.md, references/, scripts/, evals/.
