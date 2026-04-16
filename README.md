# Claude Skills — MarketingOS

Personal skill library for Mayank Verma's AI-driven digital marketing practice. Powers pre-marketing research, campaign build, and post-launch optimization for Meta + Google Ads clients across India, Australia, Singapore, and North America.

## What's here

```
Claude Skills/
├── CLAUDE.md              Universal session rules (non-negotiable)
├── shared-context/        Analyst profile, accuracy protocol, skill architecture standards, strategic context
└── skills/
    ├── business-analysis          Step 1 — client DNA + wiki init
    ├── market-research            Step 2 — 11-dimension research + keyword data + dashboard
    ├── paid-media-strategy        Step 3 — campaign architecture + creative brief JSON
    ├── ad-copywriter              Step 4 — Google RSAs, Meta ads, image prompts, video storyboards
    ├── landing-page-builder       Step 4b — HTML prototype + page-spec JSON for Lovable
    ├── landing-page-audit         Evaluation — CRO / UX / copy scoring + fix recommendations
    ├── campaign-setup             Step 5 — Google Ads Editor + Meta bulk import CSVs + launch runbook
    ├── post-launch-optimization   Step 6 — Windsor.ai-driven 11-layer analysis + dashboard
    └── shared-scripts             Cross-skill utilities (dashboard generator)
```

Each skill is standalone-capable (works without upstream) and integrated-when-possible (reads upstream outputs via the client wiki + deliverables when present).

## Core principles

1. **Accuracy over appearance** — every finding carries `[EXTRACTED]` or `[INFERRED]`, every gap stays `BLANK` with a reason. A wrong answer is 3x more damaging than a blank.
2. **Progressive disclosure** — each SKILL.md stays under 200 lines; detailed knowledge lives in `references/` loaded on demand.
3. **Self-improving** — every session ends with a dated Learnings entry capturing what worked / didn't. The skill compounds across client runs.
4. **Loose coupling by design** — skills don't enforce a pipeline; they publish structured outputs that other skills can choose to consume.

See `CLAUDE.md` for the full universal rules and `shared-context/skill-architecture-standards.md` for the 7-level skill anatomy.

## Client work layout

Client deliverables live outside this repo, under `~/Desktop/{Client Name}/{Business Name}/` with `sources/`, `wiki/`, `deliverables/`. Skills read and write there; this repo holds only the skills themselves.
