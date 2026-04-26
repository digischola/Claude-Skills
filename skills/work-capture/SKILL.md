---
name: work-capture
description: "Daily content-capture skill. Turns raw work signal (typed notes, voice transcript pastes, conversation dumps, screenshots) into structured entries in the personal-brand idea-bank.json that content-calendar + post-writer downstream skills consume. Use when user says: capture this, add to idea bank, log work, note this for content, today I built X, client win, here's an insight, save this for a post, today's note, end of day capture, or pastes a client chat / screenshot they want converted to content. Do NOT trigger for: client business analysis, market research, writing a post directly (use post-writer), or generic note-taking unrelated to the personal brand."
---

# Work Capture

Turn raw work signal into structured content candidates in the personal-brand idea-bank. Run daily (ideally end-of-day) or whenever a share-worthy moment happens. The idea-bank is what `content-calendar` and `post-writer` pull from — without capture, they hallucinate generic takes.

## Context Loading

Read before starting:
- `shared-context/analyst-profile.md`
- `shared-context/accuracy-protocol.md`
- `shared-context/output-structure.md` — Digischola uses queue-based structure (NOT outputs/working/ split); after content drops, run `python3 ~/.claude/scripts/build_digischola_index.py` to refresh the index
- `Desktop/{Brand}/brand/pillars.md` — approved pillars (required for tagging)
- `Desktop/{Brand}/brand/voice-guide.md` — tone per channel (required for format candidates)
- `Desktop/{Brand}/brand/idea-bank.json` — append target

The pillar-approval gate is enforced in `scripts/append_to_idea_bank.py` (reads `pillars.md` first 20 lines for a `Status: LOCKED` marker). If the gate blocks, tell the user to run `personal-brand-dna` and change pillars.md status to LOCKED. Bypass via `--force-unlocked` is reserved for test-fixture seeding only.

## Process

### Step 1: Intake

Accept one of these input modes (user chooses or skill infers):

1. **Direct typed note** — user pastes text describing the moment
2. **Voice transcript paste** — user pastes transcribed voice memo
3. **Conversation dump** — user pastes a client chat (WhatsApp / email / Slack)
4. **Session transcript mine** — user points to a specific CLI session JSONL or says "mine today's conversation"
5. **Screenshot path** — user gives a screenshot; skill runs OCR via `Read` tool (images work natively)

For mode 4, run `scripts/mine_session.py {session_id}` to extract shareable moments from that specific session.

### Step 2: Parse into candidate entries

From the raw input, identify 1 or more discrete moments. Each becomes an entry. Moment types:

- **client-win** — a concrete result delivered (metric, before/after, finished project)
- **insight** — a realization that generalizes beyond one client
- **experiment** — something you tested (could be success, failure, or mixed)
- **failure** — honest loss, mistake, or dead-end lesson
- **build-log** — progress on a skill, tool, system (MarketingOS-style content)
- **client-comm** — communication craft (how you explained something, how you proposed a test)
- **observation** — noticed something in the industry or your work worth riffing on

One raw input can yield multiple entries. Split them.

### Step 3: Tag each entry

For each entry, produce:
- `suggested_pillar` — one of the approved pillar IDs from `pillars.md`
- `channel_fit` — array of channels the entry naturally works for (LinkedIn / Instagram / X / WA-Status / WA-Channel / Facebook)
- `format_candidates` — array of concrete formats (LI-post / LI-carousel / IG-carousel / IG-reel / X-tweet / X-thread / WA-status / WA-channel-post)
- `tags` — free-form strings (client name, tool, vertical, topic)
- `status` — always `raw` on first capture

Tagging follows `references/entry-schema.md`.

### Step 4: Append to idea-bank.json

Run `scripts/append_to_idea_bank.py {brand_folder} {entry_json}`. Script:
- Validates the entry schema
- Assigns a UUID
- Timestamps the capture
- Appends atomically to `idea-bank.json`
- Updates `last_updated` in the file

### Step 5: Surface top candidates (optional, on request)

If user asks "what should I post today?", read idea-bank.json, filter by `status: raw` and recency, apply `references/candidate-ranking.md` heuristic (freshness × pillar-balance × format-variety), and surface top 3 entries with a one-line reason for each.

### Step 6: Feedback Loop

Read `references/feedback-loop.md`. Add dated learning if a pattern surfaced (e.g., user keeps tagging things `insight` that should be `build-log` — refine the definitions).

## Output Checklist

- [ ] pillars.md status confirmed as LOCKED before capture (abort otherwise)
- [ ] Each raw input produces ≥1 structured entry
- [ ] Every entry has: type, suggested_pillar, channel_fit, format_candidates, tags, status
- [ ] Entry appended to idea-bank.json atomically
- [ ] No entries with blank required fields

## Anti-patterns

- Do NOT capture generic observations without a specific hook. "AI is changing marketing" → reject. "I replaced 6 hours of research with a 20-minute skill run today" → capture.
- Do NOT guess tags. If uncertain which pillar fits, tag as `uncertain` and surface for user review.
- Do NOT auto-post. This skill only captures; `post-writer` drafts; user approves; scheduler publishes.
- Do NOT strip context. Raw notes should preserve specific numbers, client names (only if already approved in credentials.md), timestamps.

## Learnings & Rules

<!--
Format: [DATE] [CONTEXT] Finding → Action. Keep under 30 lines. Prune quarterly.
-->
- [2026-04-18] [Initial] Skill built alongside personal-brand-dna. Schema seeded in idea-bank.json with 7 entry types and status lifecycle (raw, shaped, drafted, scheduled, posted, killed).
- [2026-04-18] [Gate enforcement] Moved pillars-LOCKED check from prose-only Step 1 language into `scripts/append_to_idea_bank.py` as a hard gate (exit code 2). Previously the gate was advisory; now the script physically blocks until pillars.md has `Status: LOCKED`. Bypass flag `--force-unlocked` added for test fixture seeding. Tested both paths: blocked on DRAFT, passed on force.
- [2026-04-18] [Location — verified empirically] Tested nesting under `.claude/skills/personal-brand/work-capture/` for visual grouping: discovery broke (skill vanished from the harness list). Flattened back to `.claude/skills/work-capture/` (resolves to Claude Skills Git repo via symlink). → Rule: Claude Code skill discovery is strictly one-level-deep; use naming prefixes for grouping (rename option: `personal-brand-work-capture`) instead of subfolders.
