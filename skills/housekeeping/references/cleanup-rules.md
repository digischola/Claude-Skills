# Cleanup Rules — Classification Catalog

Source of truth for housekeeping classification. `scripts/scan.py` hardcodes these rules in Python for speed and testability; this file is the human-readable spec. When they disagree, update both.

Classification tiers (scan.py applies in order, first match wins):

1. **PROTECTED** — never flag, never deletable. Silently skipped.
2. **AUTO-BLOAT** — flag automatically. Batch confirmation default: "Quarantine all". Well-understood junk patterns.
3. **LIKELY-BLOAT** — flag automatically. Batch confirmation default: "Review one-by-one". Rebuildable but user may have reasons to keep.
4. **AMBIGUOUS** — flag automatically. Always ask per-item. Pattern matches but intent unclear.
5. **UNCLASSIFIED** — not flagged. Scanner ignores. (Most files fall here — we only touch known patterns.)

---

## §PROTECTED — Never flag, never delete

### Framework files
- `.claude/CLAUDE.md`
- `.claude/shared-context/analyst-profile.md`
- `.claude/shared-context/accuracy-protocol.md`
- `.claude/shared-context/skill-architecture-standards.md`
- `.claude/shared-context/strategic-context.md`
- `.claude/settings.local.json`, `.claude/launch.json`

### Skill architecture (every skill in `Claude Skills/skills/*/` and `.claude/skills/*/`)
- `**/SKILL.md`
- `**/references/**`
- `**/scripts/**`
- `**/assets/**`
- `**/evals/**`
- `shared-scripts/**`

### LOCKED brand wiki (`Desktop/Digischola/brand/_engine/wiki/`)
- `brand-wiki.md`, `pillars.md`, `voice-guide.md`, `brand-identity.md`, `credentials.md`, `channel-playbook.md`, `icp.md`, `voice-flavor.md`, `voice-lock.md`
- `_engine/wiki-config.json`, `_engine/idea-bank.json`, `_engine/credential-usage-log.json`, `_engine/weekly-ritual.state.json`, `housekeeping.state.json` (skill-dir state)

### Performance data (tiny, irreplaceable reference)
- `performance/log.json`
- `performance/*.md` (weekly review reports — keep all)

### Active queue drafts
- `queue/pending-approval/*.md` where frontmatter `posting_status` ∈ {absent, scheduled, posting, notified, failed, manual_publish_overdue}
- `queue/published/*.md` newer than 180 days
- `queue/briefs/**` newer than 30 days
- `queue/assets/{entry_id}/**` newer than 180 days OR where source draft still `scheduled`/`posting`

### Client wiki (under `_engine/`)
- `Desktop/{Client}/{Project}/_engine/wiki/**` (every page, every log, every config)
- `Desktop/{Client}/_engine/wiki/**` (multi-program shared DNA — formerly `_shared/wiki/`)

### Client primary deliverables (always keep)
Under the 2026-04-29 `_engine/` convention, presentables (HTML/MP4/PDF/upload-ready CSV bundles) live at the folder root and internals (md/json/intermediate csv) live in `_engine/working/`.
- `Desktop/{Client}/{Project}/*.html` — dashboards, audits, landing pages
- `Desktop/{Client}/{Project}/*.mp4`, `*.mov`, `*.webm`, `*.pdf` — finished video / docs
- `Desktop/{Client}/{Project}/campaign-setup/**` — bulk-import directory tree (folder-bundle presentable)
- `Desktop/{Client}/{Project}/_engine/working/*.md` — research, strategy, copy, audit, optimization, landing-page reports
- `Desktop/{Client}/{Project}/_engine/working/*.json` — creative-brief, page-spec, rotation-brief, client-config
- `Desktop/{Client}/{Project}/_engine/working/*.csv` — media plans, ad-copy CSVs (intermediate)
- `Desktop/{Client}/{Project}/_engine/brand-config.json` (single-program) or `Desktop/{Client}/_engine/brand-config.json` (multi-program, at client root)

### Scheduler state (active)
- `scheduler.log`, `scheduler-failures.log`, `housekeeping.log` (active, rotate not delete)
- `~/Library/LaunchAgents/com.mayank.*.plist`

### Source code versioning
- `.git/**` everywhere
- `.gitignore`, `.gitattributes`

### Claude Code session transcripts
- `.claude/projects/*/*.jsonl` — full session transcripts. personal-brand-dna's `mine_transcripts.py` reads these for voice extraction; deleting them loses voice samples forever. Individual `tool-results/*.json` inside session dirs ARE touchable (see AUTO-BLOAT).

### macOS system
- Keychain (inherently filesystem-untouchable; listed for clarity)

### User opt-out
- Any folder containing a `.housekeeping-keep` marker file is fully exempt (recursive).

---

## §AUTO-BLOAT — Batch-confirm, default Quarantine-all

Well-understood junk. Safe to quarantine without per-item review in most cases.

### Python caches
- `**/__pycache__/`
- `**/*.pyc`
- `**/.mypy_cache/`
- `**/.pytest_cache/`
- `**/.ruff_cache/`
- `**/.coverage`, `**/htmlcov/`

### macOS junk
- `**/.DS_Store`
- `**/._*` (AppleDouble resource forks)

### Node caches (only in eval/fixture trees, never in a skill's runtime deps)
- `**/evals/**/node_modules/`
- `**/fixtures/**/node_modules/`
- `**/out/.cache/`

### Tool-result overflow (my own persisted oversize outputs)
- `.claude/projects/*/tool-results/*.json` older than 14 days
- `.claude/projects/*/tool-results/*.txt` older than 14 days

### Editor + OS swap
- `**/*.swp`, `**/*.swo`, `**/*~`
- `**/.~lock.*` (LibreOffice)

### Build intermediates
- `**/node_modules/.cache/`
- `**/.next/cache/`
- `**/.turbo/`

---

## §LIKELY-BLOAT — Batch-confirm with summary, default Review-one-by-one

Rebuildable artifacts. User may have reasons to keep (e.g., won't re-run Perplexity to save $). Surface summary, let user decide per batch.

### Raw research sources (rebuildable by re-running upstream skill)
- `Desktop/{Client}/{Project}/_engine/sources/perplexity-*.md` older than 90 days
- `Desktop/{Client}/{Project}/_engine/sources/*.png` (screenshots) older than 90 days
- `Desktop/{Client}/{Project}/_engine/sources/*keyword-plan*.csv` older than 90 days
- `Desktop/{Client}/{Project}/_engine/sources/*keyword*.csv` older than 90 days

### Brand mining artifacts (rebuildable via `personal-brand-dna/scripts/mine_transcripts.py`)
- `Desktop/Digischola/brand/_engine/_mining/**` older than 60 days

### Trend research weekly folders (rebuildable from trend-research skill)
- `Desktop/Digischola/brand/_engine/_research/trends/{YYYY-WNN}/**` older than 56 days (8 weeks)
- Exception: keep the most recent 8 weeks always

### Old published drafts (past attribution window)
- `Desktop/Digischola/brand/queue/published/*.md` older than 180 days
  - performance-review has already baselined these
  - Windsor attribution doesn't query files this old

### Visual assets tied to old drafts
- `Desktop/Digischola/brand/queue/assets/{entry_id}/**` where source draft status=`posted` AND older than 180 days

### Render intermediates
- `Desktop/Digischola/brand/_engine/remotion-studio/out/**/*.mp4` older than 30 days (intermediate scene renders — final goes to `queue/assets/`)
- `Desktop/Digischola/brand/_engine/remotion-studio/out/**/*.png` older than 30 days
- `Desktop/Digischola/brand/_engine/_renders/**` older than 30 days

### Rotated log archives
- `Desktop/Digischola/brand/scheduler.log.*` archives older than 90 days
- `housekeeping.log.*` archives older than 90 days

### Old tool-result persistence
- `.claude/projects/*/tool-results/*` 7-14 days old (extends AUTO tier's >14d rule). Rule id: `tool-results-stale`

### Explicitly-cleared archive folders
- `**/queue/archive/*cleared*/` or `*retired*/` or `*-done/` folders older than 3 days. User explicitly named them — intent is retired. Rule id: `cleared-archive`

### Test-iteration renders in queue/assets/
- `**/queue/assets/**/*-v{N}.{mp4|mov|webm|png|jsx}` older than 7 days. Common case: `reel-v7.1.mp4`, `reel-v7.2.mp4`, `scenes-v2.jsx`. Rule id: `test-iteration-render`

### Test-named drafts in queue/
- `**/queue/**/{*-test-*|test-*|*-mvp*|*-wip*}` files older than 3 days. Rule id: `test-draft`

### Housekeeping's own stale runtime files
- `skills/housekeeping/scan-report.json` and `approved-plan.json` older than 7 days. Most-recent run kept for debugging/diff. Rule id: `stale-scan-runtime`

### Superseded deliverables (post-walk detector)
- For each program folder root (presentables sit at the top — HTML/MP4/PDF) and `_engine/working/` directory (intermediate md/json/csv): group files by `(dir, suffix)` where suffix ∈ the DELIVERABLE_SUFFIX_RE list.
- Within each group, flag older files **only** if the newer file's stem starts with `{older-stem}-` (or vice versa — newer is a prefix of older).
  - Catches: `thrive-market-research.md` superseded by `thrive-retreat-market-research.md`
  - Catches: `kingscliff-landing-page-audit.html` superseded by `kingscliff-lovable-landing-page-audit.html`
  - Does NOT catch: unrelated distinct deliverables in same dir (`midweek-reset` vs `ashfield` vs `kingscliff`)
- Tier: AMBIGUOUS — user decides per item (could be intentional before/after keeping). Rule id: `superseded-deliverable`

### Weekly files past 52-week retention
- `Desktop/Digischola/brand/performance/YYYY-WNN.md` older than 364 days
- `Desktop/Digischola/brand/calendars/YYYY-WNN.md` older than 364 days
- Per user policy "keep 52 weeks, archive older". These should be **archived** (moved to `{parent}/_archive/`) not quarantined.
- **TODO before first fire (~2027-04):** write `scripts/archive_old.py` that moves approved items to `{parent}/_archive/` instead of quarantine. Until then, flagging is informational only.
- Rule id: `weekly-over-52w`

---

## §AMBIGUOUS — Always ask per-item

Pattern matches suggest deletion but intent is unclear. Always AskUserQuestion per item.

### Orphaned client folders
- `Desktop/{FolderName}/` where ALL of the following:
  - Not in strategic-context `Current Clients & Revenue` list
  - No `_engine/wiki/` subfolder modified in last 120 days
  - No top-level presentables (`*.html`, `*.mp4`, `*.pdf`, `campaign-setup/**`) or `_engine/working/` files modified in last 120 days
  - Top-level folder itself not modified in last 120 days
- Examples to watch: test clients, one-off projects, old exploratory work

### Versioned tools/ folders under Digischola
- `Desktop/Digischola/tools/{name}-v{N}/` where folder name matches `[-_]v\d+` pattern AND folder is >14 days old
- Example: `tools/lp-audit-v1/` — test iteration folder from a prior build
- Rule id: `tools-version-folder`

### Unknown top-level directories in `Desktop/Digischola/brand/`
- `{folder}/` where {folder} NOT in known set: {queue, calendars, performance, videos, social-images, _engine, _archive}
- Note (2026-04-29 `_engine/` convention): media build dirs (remotion-studio, hyperframes-scenes, music, face-samples, voice-samples) and skill scratch (_mining, _research) live INSIDE `_engine/` now. Do not flag `_engine/` itself as unknown.

### Unknown top-level directories on `Desktop/`
- `{folder}/` where {folder} NOT in known set: {Digischola, Claude Skills, .claude, Thrive Retreat, Happy Buddha, ISKM, Salt Air Cinema, Gargi Modi, remotion-promo} AND not modified in last 90 days
- Update the known set when a new real client is onboarded.

### Large single files (>50MB) outside known patterns
- Anything >50MB NOT in: Remotion renders, `_engine/music/`, `_engine/face-samples/`, `_engine/voice-samples/`, top-level presentables (HTML/MP4/PDF), brand-identity assets

### Loose Desktop clutter
- `Desktop/Screenshot *.png` older than 30 days
- `Desktop/*.pdf`, `Desktop/*.zip`, `Desktop/*.dmg` older than 30 days (loose files, not in a project folder)

### Duplicates by content (SHA256)
- Identical-content files across multiple paths — keep newest, flag others AMBIGUOUS (user may intentionally have copies)

---

## §Exemptions

- Any folder containing a file named `.housekeeping-keep` is fully PROTECTED, recursive.
- Any file with a leading `KEEP-` prefix is individually PROTECTED (e.g., `KEEP-baseline-data.csv`).

---

## Rule Hygiene

- Every rule has a rationale. When adding a rule, write WHY it's safe to propose (what skill can rebuild it, or why it has no value past N days).
- Promotion: a LIKELY-BLOAT rule that has fired >8 times across 3 months with 100% "quarantine" approval → promote to AUTO-BLOAT.
- Demotion: an AUTO-BLOAT rule that gets "Keep" responses twice in a row → demote to LIKELY-BLOAT and investigate.
- Log all misfires in the skill's Learnings & Rules section.
