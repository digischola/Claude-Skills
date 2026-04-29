# Client Folder Output Structure

Universal convention for organizing client and personal-brand deliverables. Every skill that produces client artifacts MUST write to this structure. Adopted 2026-04-29 (`_engine/` convention; supersedes the prior `outputs/` + `working/` + `_shared/` + `deliverables/` layout).

## The rule

Two kinds of files exist in any client or personal-brand folder:

- **Presentables** — what Mayank double-clicks: `.html`, `.pdf`, `.csv`, `.mp4`, `.mov`, `.webm`, `.png`, `.jpg`, plus any folder bundle whose entry point is a presentable (e.g. campaign-setup CSV bundles, landing-page-builder bundles with their own `index.html`).
- **Internals** — everything else: `.md`, `.json`, intermediate CSVs, raw notes, screenshots, wiki pages, sources, working scratch, configs, skill state.

**Top of the folder = presentables only. `_engine/` = everything else.** No `outputs/`, no `working/`, no `deliverables/`. The leading underscore on `_engine/` sorts it predictably in Finder and visually signals "skill-only state, do not open" — same convention as `.git`.

Why the rule exists: when Mayank opens any client folder he should see only files he can consume directly. Markdown reports, JSON briefs, raw research, working scratch — he doesn't read those, they're skill scaffolding. Hiding them in `_engine/` makes the folder presentable on first open.

## Single-program client

```
{Client Name}/
├── index.html                          ← optional, double-click entry point
├── {audit}.html                        ← presentables (audits, dashboards, landing pages)
├── {dashboard}.html
├── {video}.mp4
├── {document}.pdf
├── campaign-setup/                     ← upload-ready CSV bundle (folder-bundle counts as presentable)
└── _engine/
    ├── wiki/                           ← knowledge graph (md pages, log.md, etc.)
    ├── sources/                        ← raw inputs (Perplexity dumps, screenshots, exports)
    ├── working/                        ← intermediate skill output (md reports, json briefs, intermediate CSVs)
    ├── brand-config.json               ← skill-managed config files
    └── wiki-config.json
```

## Multi-program client

```
{Client Name}/
├── {client-wide-deliverable}.html      ← cross-program presentables (brand guide, business overview)
├── {client-wide-deliverable}.pdf
├── _engine/                            ← client-wide internals (formerly `_shared/`)
│   ├── wiki/                           ← cross-program brand DNA wiki
│   ├── sources/
│   ├── working/
│   ├── brand-config.json               ← formerly `_shared/deliverables/brand-config.json`
│   └── wiki-config.json
├── {Program A}/
│   ├── {program-deliverable}.html      ← program-specific presentables
│   ├── {program-deliverable}.mp4
│   └── _engine/
│       ├── wiki/
│       ├── sources/
│       ├── working/
│       └── wiki-config.json
└── {Program B}/
    └── ... (same shape)
```

## Personal-brand (Digischola)

The Digischola brand folder applies the same principle but its working surface is queue-based, not output-based. Mayank reviews `.md` drafts in `queue/pending-approval/` daily — those drafts are his consumption surface, so they stay at top.

```
~/Desktop/Digischola/
├── index.html                          ← double-click entry point (auto-generated)
├── strategic-context.md                ← strategy doc Mayank actually reads
├── *.log                               ← scheduler logs (top-level, ad-hoc inspection)
└── brand/
    ├── queue/                          ← daily review surface
    │   ├── pending-approval/           ← drafts to review (md + mp4 + bundles)
    │   ├── published/                  ← shipped archive
    │   ├── archive/
    │   ├── assets/
    │   └── briefs/
    ├── calendars/                      ← weekly content plans (md, Mayank reads)
    ├── performance/                    ← weekly performance reviews (md, Mayank reads)
    ├── videos/                         ← finished video projects
    ├── social-images/                  ← finished carousels & quote cards
    └── _engine/                        ← skill-only state
        ├── wiki/                       ← brand DNA wiki (brand-identity, voice-guide, pillars, icp, etc.)
        ├── _mining/                    ← skill scratch (raw mining)
        ├── _research/                  ← skill scratch (raw research)
        ├── idea-bank.json
        ├── weekly-ritual.state.json
        ├── wiki-config.json
        ├── face-samples/, voice-samples/, music/, hyperframes-scenes/, remotion-studio/   ← media assets and build projects
        └── log.md                      ← migration / audit trail
```

The `queue/`, `calendars/`, `performance/`, `videos/`, `social-images/` folders stay at the top of `brand/` because they ARE Mayank's working surface — he opens them to review, plan, or browse output.

The brand DNA `.md` files (`brand-identity.md`, `voice-guide.md`, `pillars.md`, `icp.md`, `channel-playbook.md`, `credentials.md`, `voice-flavor.md`, `voice-lock.md`, `brand-wiki.md`) move into `_engine/wiki/` — they're skill-managed knowledge graph, not daily review surface.

## Classification rules

A file goes at the **top of its folder** if:
- Mayank double-clicks it: `.html`, `.mp4`, `.mov`, `.webm`, `.pdf`, `.png`, `.jpg`, finished `.csv` bundles
- It's a folder bundle whose entry point is a presentable (`campaign-setup/`, landing-page-builder bundles with their own `index.html`)
- It's the auto-generated `index.html` front door
- For Digischola only: it's a workflow surface folder (`queue/`, `calendars/`, `performance/`, `videos/`, `social-images/`) or a strategy doc Mayank actually reads (`strategic-context.md`)

A file goes in **`_engine/`** if:
- It's `.md` (reports, audit findings, research, briefs, wiki pages) — Mayank's words: "MD I hardly read and they are not presentable"
- It's `.json` (creative briefs, page specs, rotation briefs, brand-configs, skill state)
- It's an intermediate CSV that gets transformed downstream (e.g. ad-copywriter's pre-bundle CSVs)
- It's raw input (Perplexity exports, Keyword Planner CSVs, screenshots) → `_engine/sources/`
- It's wiki-managed knowledge → `_engine/wiki/`
- It's skill scratch / config → `_engine/working/` or `_engine/`

When in doubt: if Mayank wouldn't open it directly to consume the contents, it goes in `_engine/`.

## Skill write paths — migration table

| Artifact type | Old path | New path |
|---|---|---|
| Markdown reports (`*-report.md`, `*-research.md`, `*-strategy.md`, `*-audit-findings.md`) | `working/` or `deliverables/` | `_engine/working/` |
| HTML dashboards (`*-dashboard.html`, `*-research-dashboard.html`) | `outputs/` or `deliverables/` | folder root |
| HTML landing pages (`*-landing-page.html`, `*-page-audit.html`) | `outputs/` or `deliverables/` | folder root |
| MP4 videos | `outputs/` or `deliverables/` | folder root |
| PDF documents | `outputs/` or `deliverables/` | folder root |
| Creative briefs (`*-creative-brief.json`) | `working/` or `deliverables/` | `_engine/working/` |
| Page specs (`*-page-spec.json`) | `working/` or `deliverables/` | `_engine/working/` |
| Rotation briefs (`*-rotation-brief.json`) | `working/` or `deliverables/` | `_engine/working/` |
| Brand configs (`brand-config.json`) — single-program | `working/` or `deliverables/` | `_engine/brand-config.json` |
| Brand configs — multi-program | `_shared/deliverables/brand-config.json` | `_engine/brand-config.json` (at client root) |
| Intermediate CSVs (pre-bundle) | `working/` or `deliverables/` | `_engine/working/` |
| Campaign-setup bulk import bundle | `outputs/campaign-setup/` or `deliverables/campaign-setup/` | `campaign-setup/` (folder root) |
| Pre-launch checklist + launch runbook | `outputs/campaign-setup/` | `campaign-setup/` (stays inside the bundle) |
| Wiki pages | `wiki/` | `_engine/wiki/` |
| Wiki config | `wiki-config.json` (folder root) | `_engine/wiki-config.json` |
| Sources / raw inputs | `sources/` | `_engine/sources/` |
| Multi-program shared wiki | `_shared/wiki/` | `_engine/wiki/` (at client root, since `_shared/` is renamed to `_engine/`) |

## What `_engine/` looks like internally

```
_engine/
├── wiki/                       ← managed by init_wiki.py and skill-specific wiki writers
│   ├── index.md
│   ├── log.md                  ← append-only audit log for this folder
│   ├── strategy.md
│   ├── business.md
│   ├── brand-identity.md
│   ├── offerings.md
│   ├── digital-presence.md
│   └── briefs.md               ← append-only client-brief history
├── sources/                    ← raw, immutable inputs
├── working/                    ← intermediate / machine-readable / handoff files
│   ├── *.md
│   ├── *.json
│   └── *.csv
├── wiki-config.json            ← schema config
└── {other skill state}         ← brand-config.json, weekly-ritual.state.json, etc.
```

## Don't touch

- `_engine/wiki/` — managed by `init_wiki.py` and skill-specific writers
- `_engine/sources/` — raw inputs, immutable
- `.git/`, `.DS_Store`, etc.
- `Sri Krishna Mandir/Nrsimha Caturdasi 2026/site/` — read-only Lovable repo mirror, special-cased; stays at program root despite not being a "deliverable"

## Why this exists

Mayank consumes presentables (HTML / MP4 / PDF / upload-ready CSVs). He rarely reads the markdown reports or JSON briefs that skills generate as scaffolding. The pre-2026-04-29 layout had four sibling folders at every client root (`outputs/`, `working/`, `wiki/`, `sources/`) plus sometimes `deliverables/` and `_shared/`, all visually equal but semantically very different. Multi-program clients added a sixth (`_shared/`).

Collapsing all internals into one `_engine/` folder leaves the top of every client folder showing only what Mayank opens. Same principle, simpler shape.

Future skills must respect this rule. Do not regress to flat `outputs/` + `working/` + `deliverables/` siblings.

---

## Index builder

`/Users/digischola/Desktop/.claude/scripts/build_outputs_index.py` regenerates the auto-generated `index.html` front door for client folders. Under the new convention it scans the folder root (and program subfolders) for presentables instead of the old `outputs/` subfolder.

Run after any client-skill session that produces new presentables:

```bash
python3 ~/.claude/scripts/build_outputs_index.py "/Users/digischola/Desktop/{Client Name}"
```

For Digischola, `build_digischola_index.py` aggregates the queue + calendars + performance review surface. Same script, same purpose, just adapted to the queue-based shape.
