# Mayank Verma — Universal Session Rules

## Who I Am

AI-based digital marketing freelancer. Pre-marketing research and campaign development for Meta + Google Ads. Based in Gurugram, Haryana. Full background in `.claude/shared-context/analyst-profile.md`.

## Active Skills

Four client-track skills:

- `business-analysis` — extract business DNA, brand identity, offerings; initialize client wiki
- `market-research` — pre-marketing research, audience, competitors, keywords, benchmarks
- `landing-page-audit` — conversion audit of an existing landing page
- `landing-page-builder` — build a high-converting landing page from scratch

Anything else: do it inline in the session. Skills are minimal scaffolding, not procedural automation.

## Accuracy Protocol

Three rules apply to all research, analysis, and data extraction:

1. **Blank when uncertain.** If a data point is ambiguous, missing, or contradictory, leave it BLANK with a one-sentence reason. Never fill gaps with reasonable guesses.
2. **3x penalty.** A wrong answer is 3x more damaging than a blank. When in doubt, leave it blank.
3. **Source label everything.** Every finding gets tagged: `[EXTRACTED]` (directly from source) or `[INFERRED]` (your synthesis, with the evidence stated).

Full protocol: `.claude/shared-context/accuracy-protocol.md`.

## Voice Rules

See `.claude/shared-context/copywriting-rules.md` for the universal copywriting bedrock. Headline rules:

- No em dashes in any content Mayank publishes.
- Plain English in all chat replies. No jargon, no acronyms, no engineer-speak. File content can stay technical; chat replies cannot.
- Grounded simple ad copy by default. No poetic dyads, no constancy-claim cadence, no clever-clever, no marketing jargon. Religious and serious sectors especially grounded. Humor brands are the only exception.

## Formatting Preferences

- No salutations, no fluff
- Simple, direct language
- No tabular format in prose (tables OK for benchmark data and comparisons)
- Outputs feel like a senior strategist briefing
- Dashboards: dark mode, client branding, premium feel

## Client Work Structure

Client deliverables go in `Desktop/{Client Name}/{Project or Business}/`.

Folder layout:
- Top of the folder = presentables only (`.html`, `.pdf`, `.csv`, `.mp4`, `.mov`, `.png`, `.jpg`).
- `_engine/` = everything else (markdown, JSON, working scratch, configs, wiki, sources).

When Mayank opens a client folder he should see only files he can consume directly. Skill scaffolding hides in `_engine/`.

## Same-Client Re-Run

When re-running a skill on the same client, overwrite existing files in place. No v1/v2/v3, no `-{date}` parallel filenames. One file per role, current state only. The exception is `_engine/wiki/briefs.md`, which is append-only with `[ACTIVE]` / `[SUPERSEDED]` markers.
