---
name: trend-research
description: "Weekly trend scanner for the 3 Digischola pillars (Landing-Page Conversion Craft, Solo Freelance Ops, Small-Budget Paid Media). Drops fresh trend candidates into idea-bank.json so content-calendar always has fuel even when work-capture has been quiet. Two modes: (1) AUTONOMOUS — Claude uses WebSearch to scan each pillar's niche per week, dedupes against existing idea-bank entries, appends new candidates with type:trend + source URLs + relevance scores. (2) DEEP — generates a Perplexity mega-prompt per pillar for offline deep-research with citations; user runs Perplexity, pastes response back, ingest_response.py parses + dedupes + appends. Wired into weekly-ritual Sunday Step 1 (auto-skipped today; building this skill activates it). Use when user says: trend research, scan trends, what's hot in marketing, weekly trend scan, find trending topics, refresh idea bank, perplexity research, sunday step 1. Do NOT trigger for: capturing a specific idea (use work-capture), client market research (use market-research), drafting from a known idea (use post-writer), creator-style refresh (use peer-tracker)."
---

# Trend Research

Weekly trend scanner. Keeps idea-bank fresh by surfacing what's getting traction in the 3 pillar niches. Runs autonomously inside Claude (WebSearch) or as a Perplexity-paste flow when deep research with citations is wanted.

## Why this exists

content-calendar pulls from idea-bank. If work-capture has been quiet for a week (busy client work, vacation), the bank runs thin and the calendar pulls from stale entries. This skill is the "always-on" feed source — every Sunday, 3-6 fresh candidates per pillar land in the bank with proper sourcing.

## Context Loading

**Brand wiki:**
- `Desktop/Digischola/brand/_engine/wiki/pillars.md` — must be LOCKED
- `Desktop/Digischola/brand/_engine/idea-bank.json` — appends here (matches work-capture schema; type: `trend`)
- `Desktop/Digischola/brand/_engine/wiki/voice-guide.md` — relevance filter (skip trends that need em dashes / hype words)
- `Desktop/Digischola/brand/_engine/wiki/icp.md` — relevance filter (skip trends irrelevant to wellness / spiritual / hospitality / B2B / freelancer / SMB ICPs)

**Shared context:**
- `.claude/shared-context/analyst-profile.md` — workflow, voice/quality standards used as relevance filter
- `shared-context/output-structure.md` — Digischola uses queue-based structure (NOT outputs/working/ split); after content drops, run `python3 ~/.claude/scripts/build_digischola_index.py` to refresh the index

**Skill references:**
- `references/pillar-niches.md` — keyword seeds + tracked sources per pillar
- `references/web-search-strategy.md` — how Claude conducts the autonomous scan
- `references/perplexity-prompt-templates.md` — the deep-research prompt per pillar
- `references/ingestion-rules.md` — dedup logic, quality filter, idea-bank schema
- `references/feedback-loop.md`

## Modes

### Mode 1 — Autonomous (default, used by weekly-ritual Sunday)

Claude reads `references/web-search-strategy.md` and runs:
- 3 WebSearches (one per pillar) for last-7-days trending topics
- Synthesizes 3-6 trend candidates per pillar
- Dedupes against existing idea-bank entries (`scripts/trend_research.py dedupe-check`)
- Appends new candidates via `scripts/trend_research.py ingest --pillar X --json '{...}'`

Total time: ~3-5 min when invoked.

### Mode 2 — Deep (Perplexity offline)

User runs `scripts/trend_research.py prompt --week 2026-W17` →
- Writes 3 mega-prompts to `brand/_engine/_research/trends/2026-W17/<pillar>-prompt.md`
- Copies first prompt to clipboard

User opens Perplexity, pastes prompt, copies the response into `brand/_engine/_research/trends/2026-W17/<pillar>-response.md`. Then runs:
```bash
python3 scripts/trend_research.py ingest-perplexity --pillar lp-craft --week 2026-W17
```

Script parses, dedupes, appends to idea-bank.

Use Mode 2 when planning a content theme or before launching a new pillar focus — when you want depth + citations, not just a quick scan.

## Process — Mode 1 (the Sunday default)

When invoked autonomously (or by user saying "scan trends"):

1. **Pre-checks**: `_engine/wiki/pillars.md` LOCKED, `_engine/idea-bank.json` exists. Block if not.
2. **For each of 3 pillars**, do a WebSearch using the keyword strategy in `references/web-search-strategy.md`:
   - LP Craft: queries around "landing page conversion 2026", "CTA optimization tactics", "form length conversion"
   - Solo Ops: queries around "solo freelance marketing 2026", "AI marketing operator", "indie agency stack"
   - Paid Media: queries around "low budget meta ads", "$10/day campaign optimization", "PPC small business 2026"
3. **Synthesize** 3-6 candidates per pillar from search results. Each candidate is:
   - `type: trend`
   - `pillar: <pillar name>`
   - `seed`: 1-2 sentence summary of the topic
   - `hook_candidate`: a possible hook line drawn from the topic
   - `source_urls`: 1-3 URLs Claude found
   - `tags`: relevant tags (e.g., "wellness", "ai-tooling", "case-study")
   - `relevance_score`: 1-5 (Claude's judgment of fit)
   - `via: trend-research`
   - `captured_at`: ISO 8601 IST
   - `status: raw`
4. **Dedupe** each candidate via `dedupe-check`: skip if seed text overlaps >70% with an existing idea-bank entry's `seed` / `raw_note` / `hook_candidate`.
5. **Apply quality filter**: drop candidates with relevance_score <3, or that contain anti-patterns (em dashes, hype words from voice-guide).
6. **Append** survivors to `_engine/idea-bank.json` via `ingest`.
7. **Report**: list what was added and what was skipped (with reason).

## Process — Mode 2 (Perplexity deep)

```bash
python3 scripts/trend_research.py prompt --week 2026-W17
# → writes prompts to brand/_engine/_research/trends/2026-W17/{lp-craft,solo-ops,paid-media}-prompt.md
# → first prompt copied to clipboard
```

User does Perplexity round-trip per pillar, saves response file. Then:

```bash
python3 scripts/trend_research.py ingest-perplexity \
  --pillar lp-craft \
  --response brand/_engine/_research/trends/2026-W17/lp-craft-response.md
```

## Output Checklist

- [ ] At least 1 candidate added per pillar per week (else WARN)
- [ ] No duplicates against existing idea-bank entries
- [ ] Each entry has source_urls (Claude WebSearch citations OR Perplexity citations)
- [ ] Each entry passes voice-guide quality filter
- [ ] Report logged to `brand/_engine/_research/trends/<week>/scan-log.md`

## Anti-patterns

- Do NOT auto-add candidates without dedupe — content-calendar will pick duplicates and post-writer will draft the same idea twice.
- Do NOT trust trends that lack source URLs (Perplexity occasionally hallucinates URLs; verify or skip).
- Do NOT include paywalled URLs as the sole source.
- Do NOT post-process the trend candidate into a draft — that's post-writer's job. trend-research only feeds the bank.
- Do NOT scan more than once per week per pillar (rate-limit ish + signal-to-noise concern).
- Do NOT include trends from outside the 3 pillars. If a topic is interesting but doesn't fit, skip it.

## Learnings & Rules

<!--
Format: [DATE] [CONTEXT] Finding → Action. Keep under 30 lines.
-->
- [2026-04-20] [Initial build] Built as the autonomous feed source for idea-bank. Two modes: WebSearch (Claude in the loop, runs in ~3-5 min) and Perplexity-paste (deeper research with citations, requires user round-trip). Mode 1 is default for weekly-ritual Sunday Step 1; Mode 2 for ad-hoc deep dives. Idea-bank schema extended with new entry type `trend` + fields: `seed`, `hook_candidate`, `source_urls`, `relevance_score`, `via`. Dedup by 70% text-overlap on seed + raw_note + hook_candidate. Quality filter rejects relevance_score <3 and entries containing em dashes / hype words.
- [2026-04-20] [Cross-skill] Activates weekly-ritual's Sunday Step 1 (was auto-skipped). The flow now: Sunday 09:00 → trend-research scans 3 pillars → 9-18 candidates added → content-calendar pulls fresher entries when assigning slots → post-writer drafts from cleaner pool. Closes the "what if work-capture has been quiet?" gap.
- [2026-04-20] [Sources] WebSearch returns top results from major 2026 outlets (industry blogs, LinkedIn posts, X threads, Reddit r/marketing). For each pillar, pre-defined seed query lists in `references/web-search-strategy.md` to ensure consistent niche scanning. Re-evaluate seed queries quarterly as Mayank's pillars sharpen.
- [2026-04-20] [Schema] Protocol gap caught during first live Sunday ritual test: `build_entry()` wrote trend entries WITHOUT an `id` field. content-calendar's `find_entry_for_pillar()` does `e["id"] not in used_ids` and KeyErrors. Fixed: added `import uuid` + `"id": candidate.get("id") or str(uuid.uuid4())` at top of entry dict in `build_entry()`. Backfilled existing 10 entries with UUIDs. Going forward all ingests will include an id. Takeaway: cross-skill schema contracts need tests — add a content-calendar compatibility check to evals next iteration.
- [2026-04-29] [STRUCTURAL REFACTOR] Folder convention changed: skill internals (idea-bank.json, brand DNA wiki, _mining, _research, media assets, configs) now live in `Digischola/brand/_engine/` subfolder; daily-workflow folders (queue/, calendars/, performance/, videos/, social-images/) stay at top of `Digischola/brand/`. → Updated all path references in SKILL.md, references/, scripts/, evals/.
