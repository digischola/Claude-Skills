# Skill Coordination — Housekeeping

Housekeeping is cross-track (it spans both client-skills and personal-brand tracks) and has no upstream producers and no downstream consumers. It reads the filesystem and protects what other skills need. This file catalogs the contracts.

## Never-delete contracts

Each contract = a file or folder that some other skill actively reads/writes and therefore must remain PROTECTED in `references/cleanup-rules.md`.

| Protected path | Skill that needs it | Notes |
| --- | --- | --- |
| `Desktop/Digischola/brand/_engine/idea-bank.json` | work-capture, trend-research, content-calendar, post-writer, case-study-generator, performance-review | Source of truth for every piece of planned/written content. |
| `Desktop/Digischola/brand/_engine/wiki/pillars.md` | personal-brand-dna (writes), every downstream skill (reads, gates pre-check) | LOCKED after approval. Hard gate in `append_to_idea_bank.py`. |
| `Desktop/Digischola/brand/_engine/wiki/voice-guide.md` | post-writer, repurpose, case-study-generator | Read during draft generation. |
| `Desktop/Digischola/brand/_engine/wiki/brand-identity.md` | visual-generator, scheduler-publisher, content-calendar | Palette, fonts, easing — LOCKED. |
| `Desktop/Digischola/brand/_engine/wiki/credentials.md`, `_engine/credential-usage-log.json` | post-writer | 30-day rotation lookup. |
| `Desktop/Digischola/brand/_engine/wiki/channel-playbook.md`, `_engine/wiki/icp.md`, `_engine/wiki/brand-wiki.md`, `_engine/wiki-config.json` | All downstream personal-brand skills | LOCKED brand wiki. |
| `Desktop/Digischola/brand/queue/pending-approval/*.md` where `posting_status ≠ posted` | scheduler-publisher, repurpose | Active drafts. Never touch. (queue stays at top — unchanged) |
| `Desktop/Digischola/brand/queue/published/*.md` (<180 days) | performance-review, scheduler-publisher | Attribution window. |
| `Desktop/Digischola/brand/performance/log.json` | performance-review | Append-only scoring history. (performance/ stays at top — unchanged) |
| `Desktop/Digischola/brand/performance/*.md` | performance-review, weekly-ritual | Weekly review reports. |
| `Desktop/Digischola/brand/_engine/weekly-ritual.state.json` | weekly-ritual | Idempotency state. |
| `Desktop/Digischola/brand/calendars/*.md` | content-calendar, scheduler-publisher, post-writer | Active planning. Never touch. (calendars/ stays at top — unchanged) |
| `Desktop/{Client}/{Project}/_engine/wiki/**` | business-analysis + every downstream client skill | Client wiki is the memory layer. |
| `Desktop/{Client}/{Project}/*.html`, `*.mp4`, `*.pdf`, `campaign-setup/**` (presentables at folder root) + `_engine/working/**` (intermediate md/json/csv) | Every client skill | Primary deliverables — real work product. |
| `Claude Skills/skills/**` / `.claude/skills/**` | All skills | The architecture itself. |
| `shared-scripts/**` | market-research, landing-page-audit, performance-review, scheduler-publisher, housekeeping | Common utilities. |

## Safe-to-rebuild contracts

Each contract = a file or folder that some skill *can regenerate* from upstream inputs. Housekeeping may quarantine these with confirmation.

| Rebuildable path | Regenerator skill | How to regenerate |
| --- | --- | --- |
| `Desktop/Digischola/brand/_engine/_mining/**` | personal-brand-dna | Re-run `scripts/mine_transcripts.py` |
| `Desktop/Digischola/brand/_engine/_research/trends/{week}/` | trend-research | Re-run `scripts/trend_research.py prompt --week YYYY-WXX` |
| `Desktop/Digischola/brand/_engine/remotion-studio/out/**` (intermediates) | visual-generator | Re-run `scripts/generate_reel.py` for the draft |
| `Desktop/{Client}/{Project}/_engine/sources/perplexity-*.md` | market-research | Re-generate prompt + Perplexity round-trip |
| `Desktop/{Client}/{Project}/_engine/sources/*keyword*.csv` | market-research | Re-export Google Keyword Planner |
| `Desktop/{Client}/{Project}/_engine/sources/*.png` (audit screenshots) | landing-page-audit | Re-capture via Chrome MCP |

## Integration with weekly-ritual

Housekeeping is intentionally a SEPARATE LaunchAgent from weekly-ritual. Reasons:

- **Independent cadence.** Weekly-ritual fires Wed 09:00 (planning) + Mon 18:00 (review). Housekeeping fires Sat 10:00. Gives Mayank three distinct attention moments per week, non-overlapping.
- **Blast-radius isolation.** If housekeeping breaks or misclassifies, it doesn't delay content creation.
- **Different safety posture.** Weekly-ritual produces content. Housekeeping destroys files (via quarantine). Different review mindsets.
- **No shared state.** Weekly-ritual's `weekly-ritual.state.json` lives in `brand/_engine/`. Housekeeping's `housekeeping.state.json` lives in the skill dir. Both are PROTECTED.

If Mayank wants housekeeping integrated into weekly-ritual later, add Step 0 to `sunday-flow.md` that invokes housekeeping as a subroutine — but keep the SATURDAY LaunchAgent as a backup nudge.

## Contract with `.claude/projects/`

Claude Code writes per-session transcript data to `.claude/projects/-Users-digischola-Desktop/<session-uuid>/`. Within each session folder:

- `**/*.jsonl` — the transcript itself. **Not** touched by housekeeping (Claude Code owns this).
- `**/tool-results/*.json` and `*.txt` — persisted oversize tool outputs (like this session's 54KB Agent brief). Safe to quarantine once session is 14+ days old.

Personal-brand-dna's `mine_transcripts.py` reads the `.jsonl` files to build voice samples. If a session's `.jsonl` is deleted, future voice-guide refreshes lose that sample. Housekeeping does NOT touch `.jsonl`. Only `tool-results/` inside them.
