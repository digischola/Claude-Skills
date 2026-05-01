---
name: ideas-in
description: "Single entry point for everything that fills the Digischola idea-bank. Three modes: (1) capture — Mayank pastes a raw note / chat / screenshot from today's work, skill structures it into an idea-bank entry. (2) trend-scan — autonomous WebSearch sweep across the 3 pillars (Landing-Page Conversion Craft, Solo Freelance Ops, Small-Budget Paid Media) appends fresh trend candidates. (3) peer-scan — rotate through the 15 named creators, surface fresh hook patterns + voice drift, log to creator-study.md. All three append to brand/_engine/idea-bank.json (schema v2.0). Use when user says: capture this, log work, today's note, idea bank, scan trends, weekly trend scan, refresh idea bank, peer refresh, scan creators, who is posting what, sunday step 1, sunday step 2, ideas-in, fill idea bank. Do NOT trigger for: drafting an actual post (use draft-week), publishing (use scheduler-publisher), client business research (use market-research)."
---

# ideas-in

One skill, three modes. Everything that becomes an entry in `idea-bank.json` flows through here. Downstream `draft-week` only reads the bank — it does not capture, scan, or scrape.

## Modes

| Mode | Trigger | Output |
|---|---|---|
| `capture` | "capture this", "today's note", "log work", "save for content", paste of work signal | New entry in idea-bank.json (`type: capture`) |
| `trend-scan` | "scan trends", "weekly trend scan", "refresh idea bank", "sunday step 1" | New entries in idea-bank.json (`type: trend`) — one per pillar per scan |
| `peer-scan` | "peer refresh", "scan creators", "who is posting what", "sunday step 2" | Updated `references/creator-study.md` + new entries in idea-bank.json (`type: peer-pattern`) |

If the trigger is ambiguous, ask which mode. Default `capture` only when the user pastes raw note content.

## Context loading (every mode)

Read once before doing anything:

- `Desktop/Digischola/brand/_engine/wiki/pillars.md` — must be `Status: LOCKED`. If not, abort with: "Pillars not approved. Run personal-brand-dna first."
- `Desktop/Digischola/brand/_engine/wiki/voice-guide.md` — voice rules
- `Desktop/Digischola/brand/_engine/idea-bank.json` — current bank (for dedup)
- `.claude/shared-context/analyst-profile.md`
- `.claude/shared-context/accuracy-protocol.md`

## Mode 1: capture

Triggered by: a paste of raw work signal (typed note / chat dump / voice transcript / screenshot description), or explicit "capture this".

Read `references/capture-flow.md` for the full step list. Summary:

1. Classify the entry `type` (one of: `client-win`, `insight`, `experiment`, `failure`, `build-log`, `client-comm`, `observation`).
2. Extract concrete numbers, named tools, named clients (use anonymized handles per credentials.md).
3. Suggest pillar fit + channel fit + format candidates per `references/channel-routing.md`.
4. Run `scripts/capture.py --note "<note>" --type <type>` — appends to idea-bank.json with UUID, `status: raw`, `captured_at` ISO timestamp.
5. Echo back the entry ID to the user.

Apply `accuracy-protocol.md`: if a metric is fuzzy, leave it BLANK with reason. Never invent numbers.

## Mode 2: trend-scan

Triggered by: scheduled weekly Sunday Step 1 OR explicit "scan trends".

Read `references/trend-scan-flow.md` for the full step list. Summary:

1. For each of the 3 pillars, run a WebSearch query (queries are templated in `scripts/scan_trends.py`).
2. Parse top 5 results per pillar. For each, score relevance 0-10 against pillar definition in `pillars.md`.
3. Drop anything scoring under 6. Dedupe against existing idea-bank entries by URL + headline similarity (script handles this).
4. Append surviving candidates as `type: trend` entries with `source_url`, `relevance_score`, `pillar`, `captured_at`, `status: raw`.
5. Report a one-line summary per pillar: "LP Craft: 2 fresh, 1 dup-skip. Solo Ops: 0 fresh."

Run via: `scripts/scan_trends.py --brand-folder /Users/digischola/Desktop/Digischola` — Claude executes the WebSearch queries; the script just dedupes + appends.

## Mode 3: peer-scan

Triggered by: scheduled weekly Sunday Step 2 OR explicit "scan creators".

Read `references/peer-scan-flow.md` for the full step list. Summary:

1. Pick 4 creators from the rotation (creator list + week pointer in `references/creator-study.md`).
2. For each, WebSearch their handle + recent 30 days. Parse 1-3 top-performing posts.
3. Identify: hook pattern used (cross-ref `brand/references/hooks.json`), voice signature drift, topic pivot.
4. If a hook pattern is borrow-worthy AND not already in our hook library, append as `type: peer-pattern` to idea-bank.json with the creator handle, source URL, the pattern formula.
5. Update `references/creator-study.md` with the per-creator findings (overwrite the section for that creator — never accumulate).
6. Advance the week pointer.

## Outputs (all modes)

- `idea-bank.json` is the single source of truth. Schema v2.0 fields per entry:
  - `id` (uuid), `type`, `raw_note`, `captured_at`, `status` (`raw` | `shaped` | `published`), `suggested_pillar`, `channel_fit`, `format_candidates`, `tags`, `source_url` (trend/peer only), `relevance_score` (trend only), `creator_handle` (peer only), `pattern_formula` (peer only).
- All entries start with `status: raw`. `draft-week` flips them to `shaped` when used in a calendar slot.

## Validation

After any mode, run `scripts/validate_idea_bank.py`. Fails on:
- Duplicate IDs
- Missing required fields per type
- Invalid status value
- Future `captured_at` timestamp

## Coordination

- Upstream: nothing (this is the entry point).
- Downstream: `draft-week` reads idea-bank.json by ID.
- The `weekly-ritual` cron prompts the user to run `ideas-in trend-scan` then `ideas-in peer-scan` Wednesday 09:00 IST.

## Learnings & Rules

Capture session insights here per the 7+3 rule. Format: `[YYYY-MM-DD] [mode] Finding → Action`.

- [2026-05-01] [overhaul] 13-skill suite consolidated to 7. work-capture + trend-research + peer-tracker merged into ideas-in. Old skills deleted. → All capture/scan/scrape flows enter via this skill; no parallel paths.

## Feedback loop

See `references/feedback-loop.md` for end-of-session protocol. Run it before closing the skill.
