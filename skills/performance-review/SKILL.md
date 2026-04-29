---
name: performance-review
description: "Weekly (review-day) performance analysis for posted Digischola content. Primary path: pulls post-level metrics directly from Windsor.ai (linkedin_organic, x_organic, facebook_organic, instagram connectors) via pull_performance_windsor.py. Manual fallback: record_performance.py for JSON/CSV paste. Computes rolling 30-day baselines per channel, buckets posts (HIT / ABOVE / BELOW / FLOP), and generates a weekly markdown report in brand/performance/YYYY-WXX.md. After 56+ days of data, emits promotion / deprecation suggestions for hook categories, voice frameworks, transformation recipes, and calendar slots in other skills' reference files. v1 is ADVISORY only — user applies suggestions manually. All Windsor pulls are READ-ONLY per the Jon Loomer 2026-03-19 Meta-ad-shutdown warning. Use when user says: performance review, weekly review, how did posts perform, check performance, analyze last week, what worked, what flopped, fire check, record metrics, log post performance, performance analysis, engagement data, pull metrics, windsor pull. Do NOT trigger for: client campaign performance (use post-launch-optimization), content planning (use content-calendar), drafting (use post-writer), repurposing (use repurpose)."
---

# Performance Review

Weekly engagement-data analysis for Digischola posts. Records metrics, computes baselines, buckets posts, surfaces winners and losers, and (after enough data) suggests reference-file updates to other skills. v1 is advisory — no auto-apply.

## Context Loading

Read before running:

**Brand wiki (post-2026-04-29 `_engine/wiki/` convention):**
- `Desktop/Digischola/brand/_engine/wiki/pillars.md` — pillar reference for aggregation
- `Desktop/Digischola/brand/_engine/wiki/channel-playbook.md` — channel priority per phase

**Skill references (this skill):**
- `references/metrics-schema.md` — per-channel required fields + weighted-score formulas
- `references/scoring-rules.md` — baseline modes, bucketing thresholds, promotion/deprecation thresholds
- `references/promotion-rules.md` — how suggestions map to edits in other skills' reference files
- `references/windsor-field-map.md` — Windsor connector + field mapping per channel, safety rule

**Data source priority (locked 2026-04-22):**
1. **Windsor.ai pulls** (primary) — `pull_performance_windsor.py` plan → Claude executes MCP `get_data` per job → merge back to log. READ-ONLY only; never issue write operations to any Meta surface via Claude.
2. **Draft frontmatter `performance: {...}`** (cached) — once merged, compact summary stays on the draft for quick per-post inspection.
3. **Manual `record_performance.py`** (fallback) — only when Windsor is down, a post isn't indexed yet, or a channel isn't covered (WhatsApp, TikTok, Threads).

**Shared context:**
- `.claude/shared-context/analyst-profile.md`
- `shared-context/output-structure.md` — Digischola uses queue-based structure (top-level `queue/`, `calendars/`, `performance/`, `videos/`, `social-images/`; skill internals + brand DNA wiki in `brand/_engine/`); after content drops, run `python3 ~/.claude/scripts/build_digischola_index.py` to refresh the index

## Inputs

Two modes:

**Mode 1: Record single post.** User provides:
1. Post file path (from queue/pending-approval/ — preferably with the post already marked as posted externally)
2. Metrics (inline JSON, `--metrics-file`, or pasted then converted by Claude)
3. Optional `--published-at` timestamp
4. Optional `--exclude` to skip this record from baseline (e.g., test post or viral outlier)

**Mode 2: Weekly review.** User invokes with no per-post data. Skill reads `brand/performance/log.json` and generates the week's report.

## Process

### Step 1: Validate context

Read pillars.md to confirm LOCKED status. Confirm `brand/performance/` folder exists (create if not).

### Step 2: For each post to record (Mode 1)

1. Read the post file's frontmatter — must have `entry_id`, `channel`, `format`, `pillar`.
2. Determine the scorer key from channel + format (e.g., `instagram` + `reel` = `instagram-reel`).
3. Validate metrics against the scorer's required fields per `metrics-schema.md`. Missing field → exit 1 with clear error.
4. Run `scripts/record_performance.py <post_file> --metrics '<json>' --published-at <iso>`. Script:
   - Computes weighted_score from channel's formula
   - Appends a full record to `brand/performance/log.json`
   - Stamps a compact `performance: {...}` summary into the post file frontmatter

For CSV imports from LinkedIn analytics page: Claude reads the CSV row-by-row, maps columns to the metrics schema, and calls `record_performance.py` once per row.

### Step 3: Weekly review (Mode 2)

Run `scripts/weekly_review.py`. Script:

1. Loads `log.json`
2. Groups entries by channel, computes days-of-data per channel
3. Determines mode per channel:
   - **Collecting** (0-20d): no bucketing, raw numbers only
   - **Active early** (21-55d): buckets, no suggestions
   - **Active mature** (56+d): buckets + suggestions
4. For each channel, computes 30-day rolling median baseline
5. For this week's posts, buckets each as HIT / ABOVE / BELOW / FLOP based on percentile rank within the 30-day window
6. Aggregates bucket points per pattern dimension (hook_category, voice_framework, pillar, repurpose_source)
7. Generates suggestions ONLY if overall mode reaches `active_mature`:
   - Promotion per thresholds in `scoring-rules.md`
   - Deprecation per thresholds
   - Each suggestion tagged P1 / P2 / P3 by confidence
8. Writes `brand/performance/{ISO-week}.md` with week summary, per-channel breakdown, flags (hook overexposure, pillar imbalance), and suggestions
9. Surfaces key findings to user in chat

### Step 4: Present suggestions (if any)

If suggestions are present:
1. Summarize P1 and P2 suggestions in chat
2. For each, state the target file + the specific edit + evidence
3. Wait for user approval before applying (v1 is advisory — user applies via Edit tool manually)

### Step 5: Apply approved suggestions (manual in v1)

User applies each approved suggestion by opening the target file and making the edit. They also:
1. Add a learning entry to the target skill's SKILL.md under `[Performance-promoted]` tag
2. If the change affects a wiki file (e.g., channel-playbook cadence), update the wiki too

v2 will auto-apply P1 suggestions. v1 requires manual application for safety.

### Step 6: Feedback loop

Read `references/feedback-loop.md`. Capture:
- Metrics the user tried to track that weren't in schema
- Suggestions the user rejected and why
- Baseline noise or scoring miscalibrations

## Output Checklist

- [ ] `brand/performance/log.json` exists and has at least 1 valid entry before running weekly review
- [ ] Each recorded post has: scorer-key-matched required metrics, weighted_score computed, log entry appended, post frontmatter stamped
- [ ] Weekly report written to `brand/performance/YYYY-WXX.md` with sections: Week summary / By channel / Flags / Suggestions
- [ ] Suggestions (if any) tagged with P1/P2/P3 and include target file + specific edit + evidence
- [ ] User surfaces and (in v1) manually applies approved suggestions

## Anti-patterns

- Do NOT invent metrics. Missing fields = exit 1. Never fill in zeros silently.
- Do NOT cross-compare channels (LinkedIn 200 comments ≠ X 200 replies). Each channel baselines separately.
- Do NOT auto-apply suggestions in v1. Even P1. User reviews.
- Do NOT promote a pattern based on <3 posts. Small samples lie.
- Do NOT override brand-policy rules (em dash ban, Conservative naming, Restrained emoji) regardless of performance signals.
- Do NOT delete entries from the log. Use `--exclude` to remove from baseline while keeping historical record.
- Do NOT run weekly review before at least 1 post has been recorded. Script will exit 1 with guidance.

## Learnings & Rules

<!--
Format: [DATE] [CONTEXT] Finding → Action. Keep under 30 lines. Prune quarterly.
See references/feedback-loop.md for protocol + context tags.
-->
- [2026-04-19] [Initial build] v1 records metrics via manual JSON or CSV paste. No direct API pulls (LinkedIn/X/IG APIs are gated, paid, or painful). record_performance.py + weekly_review.py with schema + scoring + 3-tier baseline-readiness mode (collecting / active-early / active-mature). Suggestions advisory-only; auto-apply deferred to v2 after 12+ weeks.
- [2026-04-19] [Design decision] Performance record lives in log.json (append-only) + compact summary in post frontmatter. Enables both fast aggregation (log) and at-a-glance per-post inspection (frontmatter).
- [2026-04-19] [Cross-skill dependency] performance-review is the only skill that MODIFIES other skills' references in v2 (auto-apply) mode. v1 advisory-only keeps this contained. When v2 activates, update CLAUDE.md Skill Tracks section to note the cross-modification pattern.
- [2026-04-22] [Notification-UX batch] `weekly_review.py` now imports `shared-scripts/notify.py` and fires a click-to-open banner after writing the report. Click opens the freshly-written `brand/performance/YYYY-WXX.md` in the user's editor. Banner text shows total posts analyzed + suggestion count + overall baseline-readiness mode. Fridays at 18:00 IST no longer write the report silently — Mayank gets a banner he can click to jump straight to the week's analysis.
- [2026-04-22] [Windsor.ai integration — user caught "I can't do it manually man, we have Windsor"] v1 shipped with manual-CSV-paste as the only metric-entry path. User pointed out Windsor.ai already has 4 Digischola connectors authenticated (linkedin_organic, x_organic, facebook_organic, instagram — verified via get_connectors MCP). Built `scripts/pull_performance_windsor.py` (plan+merge CLI) + `references/windsor-field-map.md`. Flow: Claude runs `plan` command → reads plan.json → calls Windsor MCP `get_data` per job → writes results.json → Claude runs `merge` command → matches rows to drafts by URL (primary) or timestamp nearest-neighbor (±2h fallback) → computes weighted_score via canonical `record_performance.SCORERS` → appends to log.json + stamps draft frontmatter. `record_performance.py` kept as the manual fallback. friday-flow.md Step 2 rewritten from "ask Mayank for metrics" to "Windsor pull". Weekly-ritual Friday cron fires at Mon 18:00 IST (not Fri 18:00 — cadence shifted same day per the Thu→Wed cycle shift), user pastes "run friday review", Claude drives the Windsor pull + scoring + report rendering with zero manual entry.
- [2026-04-22] [Loomer read-only rule — locked] Jon Loomer 2026-03-19 article reports Meta shutting down AD accounts connected to AI agents via third-party connectors (Naman Bansal lost 17 accounts). Article is about ADS, not organic Graph API, but Meta is tightening across the board. Rule locked: Windsor pulls from Claude are READ-ONLY — no write endpoints on any Meta surface (facebook_organic, instagram, or client-side facebook ads). The puller + SKILL chain never call create/update/delete endpoints. If Meta's Graph API tightens further and Digischola's FB/IG page gets a warning, user disconnects the relevant Windsor connector in Windsor's dashboard and falls back to record_performance.py. See references/windsor-field-map.md §Safety rule.
- [2026-04-22] [Skill description expanded] SKILL.md frontmatter description updated to surface Windsor trigger keywords ("pull metrics", "windsor pull") + note the READ-ONLY safety rule. Primary path is Windsor; manual is fallback.
- [2026-04-29] [STRUCTURAL REFACTOR] Folder convention changed: skill internals (idea-bank.json, brand DNA wiki, _mining, _research, media assets, configs) now live in `Digischola/brand/_engine/` subfolder; daily-workflow folders (queue/, calendars/, performance/, videos/, social-images/) stay at top. → Updated brand wiki paths in SKILL.md context loading (`pillars.md` and `channel-playbook.md` now under `_engine/wiki/`), `references/promotion-rules.md` (channel-playbook target), and `scripts/weekly_review.py` (suggestion target field). queue/published/ + brand/performance/ paths used by record_performance.py + weekly_review.py + pull_performance_windsor.py are unchanged (queue/performance stay top-level).
