---
name: housekeeping
description: Universal weekly storage cleanup. Scans client deliverable folders, Digischola brand wiki, and .claude caches for deprecated/leftover/test-output files and folders. Classifies findings in 4 tiers (PROTECTED never-touched, AUTO-BLOAT batch-confirm, LIKELY-BLOAT batch-confirm with summary, AMBIGUOUS ask-per-item). Presents batched deletion candidates via AskUserQuestion; user approves per category. All deletes go to a 7-day quarantine before permanent removal (rollback-safe via scripts/rollback.py). Runs Saturday 10:00 IST via macOS LaunchAgent (nudge pattern — notification + clipboard prompt, Claude drives via AskUserQuestion, mirrors weekly-ritual design). Use when user says: housekeeping, cleanup, clean up storage, delete old files, purge test folders, weekly cleanup, storage bloat, disk space, purge caches, archive old drafts, too much on desktop. Do NOT trigger for: active queue drafts (use post-writer/repurpose), client deliverables still in use (confirm against strategic-context), skill architecture files (PROTECTED in references/cleanup-rules.md), manual one-file deletion (just use rm), content archival policy decisions (that's a skill-improvement discussion, not a cleanup run).
---

# Housekeeping — Weekly Storage Cleanup

Universal cross-track skill. Runs every Saturday 10:00 IST. Scans three zones — client deliverable folders (`Desktop/{Client}/`), Digischola brand wiki (`Desktop/Digischola/brand/`), and `.claude/projects/` caches — classifies findings against `references/cleanup-rules.md`, presents batched confirmations via AskUserQuestion, moves approved items to 7-day quarantine at `Desktop/.housekeeping-quarantine/`, auto-purges quarantine entries older than 7 days (rollback window has passed).

Safety posture: **never rm -rf, always move-to-quarantine, always log, always validate**. The rollback window is the real safety net — you can undo any delete within 7 days via `scripts/rollback.py`.

## Process Steps

1. **Pre-check.** Ensure quarantine root `Desktop/.housekeeping-quarantine/` exists. Read `housekeeping.state.json` from the skill dir. Skip if last run < 24 hours ago (idempotency — prevents double-fires). Print "last run: {timestamp}".

2. **Scan.** Run `python3 scripts/scan.py --report scan-report.json`. Walks target paths, classifies every file/folder against rules (PROTECTED / AUTO-BLOAT / LIKELY-BLOAT / AMBIGUOUS / UNCLASSIFIED). Writes `scan-report.json` with grouped items + size totals per category.

3. **Summary.** Read the report. Present totals to the user in chat: "Found N items across 4 tiers, X MB reclaimable."

4. **Batch confirmation per category.** For each of AUTO-BLOAT, LIKELY-BLOAT, AMBIGUOUS (PROTECTED never surfaced — it's never deletable): use `AskUserQuestion` with 4 options — "Quarantine all in batch", "Review one-by-one", "Skip this category", "Show details first". If "Show details first" → print paths + sizes, then re-ask.

5. **Per-item review (if requested).** Iterate items in category. For each, `AskUserQuestion` with path + reason + size + modified date. Options: "Quarantine", "Keep", "Skip remaining in this category".

6. **Execute.** Write user's approvals to `approved-plan.json`. Run `python3 scripts/cleanup.py --plan approved-plan.json --execute`. This **moves** (never deletes) approved items to `Desktop/.housekeeping-quarantine/{YYYY-MM-DD}/{flattened-path}/`. Every action logged to `housekeeping.log` with timestamp, original path, quarantine path, size.

7. **Purge expired quarantine.** Run `python3 scripts/purge_quarantine.py`. Permanently deletes quarantine date-folders older than 7 days. Logs each permanent deletion. This is the only step that actually erases data from disk.

8. **Validate.** Run `python3 scripts/validate_output.py`. Confirms: no PROTECTED path was touched, quarantine contains what the log says it should, log file intact, state file updated.

9. **Summary + update state.** Report to user: total MB recovered, items quarantined this run, items permanently purged from old quarantine, next auto-purge date. Update `housekeeping.state.json` with `last_run_at` (ISO, IST).

10. **Feedback loop.** Per `references/feedback-loop.md`: capture new bloat patterns discovered, rules that fired incorrectly, categories to promote (LIKELY → AUTO) or demote.

## Setup (one-time)

```
python3 scripts/install_launchagent.py
```

Writes `~/Library/LaunchAgents/com.mayank.housekeeping.plist` with `StartCalendarInterval` Saturday 10:00 IST. LaunchAgent fires `scripts/weekly_nudge.py` which displays a macOS notification and copies `run housekeeping` to the clipboard. User pastes into Claude Code when ready.

## Rollback

Within 7 days of quarantine:

```
python3 scripts/rollback.py --date YYYY-MM-DD
python3 scripts/rollback.py --date YYYY-MM-DD --pattern "*.csv"
python3 scripts/rollback.py --date YYYY-MM-DD --path "Desktop/Digischola/brand/_engine/_mining/voice-samples.txt"
```

Restores items to their original paths. Fails loudly on destination-conflict (file was recreated at original path in the meantime — requires manual resolution).

## Protected — NEVER DELETE

Read `references/cleanup-rules.md` §PROTECTED for full list. Highlights that should never appear in any cleanup batch:

- `.claude/CLAUDE.md`, `.claude/shared-context/*.md`
- Any skill's `SKILL.md`, `references/`, `scripts/`, `assets/`, `evals/` (the architecture itself)
- LOCKED brand wiki (under `_engine/wiki/`): `pillars.md`, `voice-guide.md`, `brand-identity.md`, `credentials.md`, `channel-playbook.md`, `icp.md`, `brand-wiki.md`, `voice-flavor.md`, `voice-lock.md`
- `_engine/idea-bank.json`, `_engine/credential-usage-log.json`, `_engine/weekly-ritual.state.json`, `_engine/wiki-config.json`, `performance/log.json`, active `scheduler.log`
- Active client wiki pages (`Desktop/{Client}/{Project}/_engine/wiki/**`)
- Drafts in `queue/pending-approval/` where `posting_status ≠ posted` (queue stays at top — unchanged)
- Drafts in `queue/published/` newer than 180 days (performance-review attribution window)
- Primary client presentables at folder root (HTML/MP4/PDF/campaign-setup bundles) + intermediate working files in `_engine/working/` (md/json/csv reports, briefs, page-specs)
- `.git/**` anywhere, macOS Keychain (filesystem-untouchable anyway)

## References

- `references/cleanup-rules.md` — Full classification catalog. The source of truth. When scan.py's Python rules and this file disagree, update both.
- `references/quarantine-protocol.md` — Quarantine structure, 7-day auto-purge math, rollback flow, conflict handling.
- `references/skill-coordination.md` — How housekeeping relates to weekly-ritual, scheduler-publisher, performance-review. Contracts for never-delete-if-still-needed files.
- `references/feedback-loop.md` — Session-close protocol for capturing new rules, misfires, and promotion candidates.

## Learnings & Rules

- [2026-04-23] [AMBIGUOUS:unknown-brand-subfolder] Pre-first-run audit flagged `brand/voice-samples/` (ChatterBox voice-clone corpus) and `brand/social-images/` as unknown → Added `voice-samples`, `social-images`, and `tools` to `KNOWN_BRAND_FOLDERS` in scan.py. They are legitimate brand subfolders consumed by visual-generator / scheduler-publisher.
- [2026-04-23] [PROTECTED:session-transcript] Pre-first-run audit flagged an active 52.9 MB `.claude/projects/<session>/*.jsonl` as large-file AMBIGUOUS. These are Claude Code session transcripts that `personal-brand-dna/scripts/mine_transcripts.py` reads for voice extraction — rule documented in references/skill-coordination.md but not coded in scan.py → Added `session-transcript` PROTECTED rule in scan.py matching `.claude/projects/*/*.jsonl`. Individual `tool-results/*.json` inside session dirs remain AUTO-BLOAT-able (>14d old).
- [2026-04-23] [NEW-RULES] User flagged gap: test-version/archive/stale-tool-result bloat not covered. Added LIKELY-BLOAT rules: `cleared-archive` (queue/archive/*cleared* folders >3d), `test-iteration-render` (versioned MP4/JSX in queue/assets/ >7d), `test-draft` (test/mvp/wip-named drafts in queue/ >3d), `stale-scan-runtime` (housekeeping's own scan-report.json/approved-plan.json >7d), `tool-results-stale` (7-14d tool-results, extending AUTO tier's >14d). Added AMBIGUOUS rule: `tools-version-folder` (tools/{name}-v{N}/ >14d).
- [2026-04-23] [NEW-RULE:superseded-deliverable] User flagged: multi-run deliverables pile up and confuse. Added post-walk detector: groups files by `(deliverables-dir, suffix)` where suffix ∈ {market-research, paid-media-strategy, creative-brief, optimization-report, landing-page-audit, audit-findings, page-spec, brand-config, client-config, etc.}. Flag: Initial version grouped ALL same-suffix files → false-positives (midweek-reset vs ashfield vs kingscliff as 'dupes'). Fixed: only flag when newer-stem starts-with older-stem+'-' (or vice versa). Catches genuine `kingscliff-lovable` superseding `kingscliff` without flagging unrelated siblings.
- [2026-04-23] [NEW-RULE:weekly-over-52w] User chose 'keep 52 weeks, archive older' for brand/performance/ and brand/calendars/ weekly files. Added detector matching `YYYY-WNN.md` pattern, flags >364d as LIKELY-BLOAT. Does not fire today (cleanup-rules.md documents that when it fires, an archive_old.py script must exist to move to `_archive/` instead of quarantine — TODO before first fire in ~12 months).
- [2026-04-23] [TIER-CONFLICT] cleanup.py's defense-in-depth PROTECTED rule blocked moving 2 kingscliff `.html`/`.md` files even after user approved them via AskUserQuestion on the `superseded-deliverable` scan finding. Scan tier said "user should decide", cleanup tier said "never deliverables". Fixed: approved-plan.json entries are now `{path, rule_id}` dicts (or plain strings for backwards compat); `DELIVERABLE_OVERRIDE_RULE_IDS = {"superseded-deliverable"}` in cleanup.py lets explicit-user-approved exceptions through while keeping the safety net for everything else. Rule: when adding a new AMBIGUOUS rule that can match client deliverables, add its rule_id to DELIVERABLE_OVERRIDE_RULE_IDS in cleanup.py as part of the same fix.
- [2026-04-23] [THRESHOLD-FIX] Lowered `cleared-archive` rule from age >3d to no threshold (user-renamed `*cleared*` folder IS the intent signal). Added pruning of cleared-archive children from walk so they aren't double-flagged. Caught the 132.7 MB `queue/archive/2026-04-22-cleared/` archive that was invisible due to being only 1 day old.
- [2026-04-23] [FOLDER-MTIME-UNRELIABLE] `tools-version-folder` rule needed age >3d, but folder mtime gets bumped every time any child is created/deleted (including cleanup.py's own moves). So `lp-audit-v1/` showed 0d old despite having v1/v2/v3 files that were clearly a test-iteration sandbox. But ALSO — mtime-based alone is wrong because lp-audit-v1 was ACTIVELY being iterated (landing-page-v4.html written 3 min before scan). Fix: introduced `newest_child_mtime(path)` helper that walks the tree and returns the most recent file mtime anywhere inside. Rule now skips if newest-child-age <24h (folder currently in use). Applies to tools-version-folder; extensible to other folder-level rules.
- [2026-04-23] [PRE-QUARANTINE-INSPECT] User requested "check internal files before doing that — some might be recent" before quarantining the 132.7 MB cleared-archive. Inspection revealed 6 unique entry_ids in the archive that DON'T exist in active queue — would be permanently lost if quarantined + not rolled back within 7 days. Rule: for any LIKELY-BLOAT or AMBIGUOUS folder >50 MB OR containing `pending-approval/`-shaped drafts, always surface a contents-preview (top 10 files by mtime + any unique-to-archive identifiers) before AskUserQuestion. Don't rely on the name-signals-intent alone for large folders — intent is a hypothesis; content is the evidence. Pending: add `scripts/inspect_folder.py` helper for this pattern so future runs don't require Claude to hand-craft the inspection command.

- [2026-04-24] [NAME-SIGNALS-INTENT-PROVEN-UNRELIABLE] Second housekeeping run on the same `2026-04-22-cleared` folder. After detailed inspection (per pre-quarantine-inspect rule above), surfaced 5 future-dated drafts (Apr 28 a5592011, Apr 29 77235986, Apr 30 39d288c2, Apr 30 6960361a, May 02 bb6662fc) with entry-IDs absent from the active queue. User chose "Skip everything — keep the archive as-is" despite the folder being explicitly named `*cleared*`. Confirms the prior rule: name-signals-intent is unreliable when the folder contains future-scheduled work the user may have re-shuffled hastily. → New rule: when a `*cleared*` folder contains pending-approval-shaped drafts dated AFTER today, downgrade the recommendation tier from "Quarantine all" to "Quarantine only obviously-stale media files; preserve all .md drafts." The cleared-archive name is a soft signal, not a quarantine warrant. The `scripts/inspect_folder.py` helper is still pending and again required hand-crafted bash this run — promote to higher priority.

- [2026-04-24] [SKIP-RUN-IS-VALID-OUTCOME] Run completed with 0 items quarantined and 0 bytes reclaimed. Validate step warned "no manifest" because nothing was moved — that's correct behavior, not an error. State file updated normally to record the no-op run so the 24h idempotency check still works. Rule: a "skip everything" outcome is a successful run, not a failed one. Treat zero-quarantine as data — it tells you the user wants to keep what they have and bloat tolerance is currently high. After 3+ consecutive skip-everything runs, surface a question: "you've kept everything 3 weeks running — should I lower the AUTO threshold or expand PROTECTED rules?" Don't keep asking the same questions if the answer is consistently no.

- [2026-04-29] [STRUCTURAL REFACTOR] Folder convention changed: skill internals (idea-bank.json, brand DNA wiki, _mining, _research, media assets, configs) now live in `Digischola/brand/_engine/` subfolder; daily-workflow folders (queue/, calendars/, performance/, videos/, social-images/) stay at top. Client folders mirror: `_engine/wiki/`, `_engine/sources/`, `_engine/working/`, with presentables (HTML/MP4/PDF/campaign-setup bundles) at the program-folder root. → Updated `references/cleanup-rules.md` (PROTECTED brand wiki paths under `_engine/wiki/`, client wiki + deliverables redefined for new layout, raw-research + mining + render-intermediates paths under `_engine/`, KNOWN_BRAND_FOLDERS reduced to top-level set, large-file allowlist), `references/skill-coordination.md` (every never-delete and rebuildable path), `references/quarantine-protocol.md` (flatten examples), SKILL.md (Protected list + rollback example), `scripts/scan.py` (KNOWN_BRAND_FOLDERS + LOCKED_BRAND_FILES sets, is_protected for `_engine/wiki/` brand DNA + client wiki + presentables/working files, classify_likely_bloat paths under `_engine/`, large-file allowlist, analyze_deliverables_groups now scans both folder roots and `_engine/working/`), `scripts/cleanup.py` (PROTECTED_NAMES added voice-flavor/lock, defense-in-depth check for `_engine/wiki/` and presentables + `_engine/working/`), `scripts/rollback.py` (docstring example). Recognized that `_engine/` is the new internals folder — its contents are NOT flagged as bloat just for being below the top level; legitimate top-level entries are now exactly `{queue, calendars, performance, videos, social-images, _engine, _archive, tools}`.
