# Client Folder Output Structure

Universal convention for organizing client deliverables. Every skill that produces client artifacts MUST write to this structure. Adopted 2026-04-26.

## The structure

```
{Client Name}/
├── index.html                  ← double-click entry point, lists outputs as cards
├── outputs/                    ← consumable, double-clickable (browse here daily)
│   ├── *.html                  ← dashboards, landing pages, audits
│   ├── *.mp4 / *.mov           ← videos
│   ├── *.pdf                   ← finished documents
│   └── campaign-setup/         ← upload-ready CSV bundles (Google Ads / Meta Ads)
├── working/                    ← intermediate / machine-readable / handoff files
│   ├── *.md                    ← markdown reports (research, audit, ad-copy, strategy)
│   ├── *.json                  ← creative briefs, page specs, rotation briefs, brand-config
│   ├── *.csv                   ← keyword data, media plans, intermediate ad CSVs
│   └── ...
├── wiki/                       ← unchanged — skill-managed knowledge graph
└── sources/                    ← unchanged — raw inputs (Perplexity, Keyword Planner exports, screenshots)
```

For multi-program clients (Yoga Ashfield, Sri Krishna Mandir, etc.):

```
{Client Name}/
├── index.html                  ← top-level: links to each program's index
├── _shared/                    ← unchanged — shared brand DNA, cross-program assets
│   ├── wiki/
│   └── deliverables/           ← keep `deliverables/` here; _shared/ is backend, not user-facing
├── {Program A}/
│   ├── index.html
│   ├── outputs/
│   ├── working/
│   ├── wiki/
│   └── sources/
└── {Program B}/
    ├── index.html
    ├── outputs/
    └── ...
```

## Classification rules

A file goes in **`outputs/`** if:
- Mayank double-clicks it to consume: `.html`, `.mp4`, `.mov`, `.webm`, `.pdf`
- It's a folder bundle of upload-ready CSVs: `campaign-setup/` (the entire bulk-import set)
- It's a folder containing a finished `index.html` + assets (e.g., a landing-page-builder bundle)

A file goes in **`working/`** if:
- It's a markdown report (`*.md`) — Mayank rarely reads these; they're for skill chaining + audit trail
- It's machine-readable (`*.json` — creative briefs, page specs, rotation briefs, brand-configs)
- It's an intermediate CSV that gets transformed downstream (e.g., ad-copywriter's `*-google-ads.csv` is intermediate; the campaign-setup `01-campaigns.csv` is the upload-ready output)
- It's keyword research data, media plans, segmentation tables, etc.

When in doubt: if Mayank wouldn't open it directly, it goes in `working/`.

## index.html — the front door

Every client folder root and every program folder root gets an auto-generated `index.html`. It:

- Lists every file in `outputs/` as a card, grouped by kind (Dashboard / Audit / Landing page / Video / Document / Campaign bulk-import)
- Links directly to each artifact (relative paths)
- Shows generation timestamp
- Mentions `working/` exists (for the rare case Mayank needs the markdown / spec)
- Renders dark-mode by default to match the dashboard aesthetic

Top-level (multi-program) `index.html` lists each program as a program-card linking to that program's `index.html`.

## Generation script

`/Users/digischola/Desktop/.claude/scripts/build_outputs_index.py` does both:
1. Migration (one-time): moves `deliverables/*` → `outputs/` or `working/` per the classification rules, then generates index files
2. Index refresh (recurring): regenerates `index.html` files for clients whose `outputs/` contents have changed

Usage:
```bash
# Migrate or refresh one client
python3 ~/.claude/scripts/build_outputs_index.py "/Users/digischola/Desktop/{Client Name}"

# Multiple clients
python3 ~/.claude/scripts/build_outputs_index.py "{Client A}" "{Client B}" "{Client C}"

# Dry-run to preview
python3 ~/.claude/scripts/build_outputs_index.py --dry-run "{Client}"
```

After every client-skill session that produces new output files, the skill (or session-close hook) should re-run the index builder for that client folder.

## Skill write paths — what to update

Every skill that produces client artifacts must write to the new paths. Migration table:

| Artifact type | Old path | New path |
|---|---|---|
| Markdown reports (`*-report.md`, `*-research.md`, `*-strategy.md`) | `deliverables/` | `working/` |
| HTML dashboards (`*-dashboard.html`, `*-research-dashboard.html`) | `deliverables/` | `outputs/` |
| HTML landing pages (`*-landing-page.html`, `*-page-audit.html`) | `deliverables/` | `outputs/` |
| MP4 videos | `deliverables/` | `outputs/` |
| Creative briefs (`*-creative-brief.json`) | `deliverables/` | `working/` |
| Page specs (`*-page-spec.json`) | `deliverables/` | `working/` |
| Rotation briefs (`*-rotation-brief.json`) | `deliverables/` | `working/` |
| Brand configs (`brand-config.json`) — single-program | `deliverables/` | `working/` |
| Brand configs — multi-program | `_shared/deliverables/` | `_shared/deliverables/` (UNCHANGED — backend store) |
| Intermediate CSVs (`*-google-ads.csv`, `*-meta-ads.csv`, `*-media-plan.csv`) | `deliverables/` | `working/` |
| Campaign-setup bulk import bundle | `deliverables/campaign-setup/` | `outputs/campaign-setup/` |
| Pre-launch checklist + launch runbook | `deliverables/campaign-setup/` | `outputs/campaign-setup/` (stays inside the bundle) |

## Skill read paths — backward-compatibility

Existing client folders have the new structure (post-migration). New clients also get the new structure. So skill read paths can update directly to `working/` and `outputs/`.

For any client folder where migration hasn't happened yet, run the migration script first.

## Don't touch

- `wiki/` — managed by `init_wiki.py` and skill-specific writers
- `sources/` — raw inputs, immutable
- `_shared/` — multi-program backend store; structure stays as-is so cross-program skill reads keep working
- `.git/`, `.DS_Store`, etc.

## Why this exists

Mayank consumes outputs (HTML / MP4 / PDF / upload-ready CSVs). He rarely reads the markdown reports or JSON briefs that skills generate as scaffolding. The old `deliverables/` folder mixed both, forcing manual sifting. The split into `outputs/` (consumable) + `working/` (scaffolding) + `index.html` (front door) eliminates that sifting.

Future skills must respect this split. Do not regress to a flat `deliverables/` folder.

---

## Digischola personal-brand suite — different convention

The Digischola folder (`~/Desktop/Digischola/`) does **NOT** follow the `outputs/` + `working/` split. It already has good queue-based separation from before this convention existed:

```
Digischola/
├── index.html                  ← double-click entry point (auto-generated)
├── strategic-context.md        ← brand strategy doc
└── brand/
    ├── queue/
    │   ├── pending-approval/   ← drafts to review (ALL formats: .md posts, .mp4 videos, case-study/ bundles)
    │   ├── published/          ← shipped archive
    │   ├── archive/            ← old drafts
    │   ├── assets/             ← per-post asset bundles (images, video clips)
    │   └── briefs/             ← machine-readable post briefs
    ├── calendars/              ← weekly content plans (YYYY-WXX.md)
    ├── performance/            ← weekly performance reviews (YYYY-WXX.md)
    ├── idea-bank.json          ← captured raw + shaped ideas
    ├── videos/                 ← video edits + Remotion projects
    ├── social-images/          ← finished carousels & quote cards
    ├── _mining/, _research/    ← skill-internal scratch (do not consume directly)
    └── ...
```

### Index builder for Digischola

Run after any content-producing personal-brand skill (post-writer / repurpose / case-study-generator / visual-generator / scheduler-publisher / weekly-ritual / performance-review):

```bash
python3 ~/.claude/scripts/build_digischola_index.py
```

The Digischola `index.html` aggregates:
- Pending approval items grouped by channel/format (LinkedIn / X / Instagram / Reel)
- This week's calendar (latest `calendars/YYYY-WXX.md`)
- Last performance review (latest `performance/YYYY-WXX.md`)
- Recent videos (latest 5 MP4s across queue + videos/)
- Quick-link tiles (published archive, idea bank, social images, video projects, strategic-context)

### Why different

Client folders mix consumable HTML/MP4 with skill-scaffolding MD/JSON in one `deliverables/`. Personal-brand skills already separate by purpose: `pending-approval/` is BOTH a draft inbox AND a consumable destination (Mayank reads each MD draft to approve before publish). MD drafts in this context aren't scaffolding — they're the work product.

Don't try to migrate Digischola to `outputs/` + `working/`. The queue-based structure is already correct. Just keep the `index.html` updated.
