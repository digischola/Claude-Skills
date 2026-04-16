# Skill Coordination & Shared Context (Level 7)

How the market research skill connects with other skills via the client wiki.

---

## The Wiki as Shared Knowledge Layer

The client wiki (`{client-folder}/wiki/`) is the single source of truth for everything known about a client. All skills read from the wiki — no skill re-derives knowledge that already exists.

```
{Client Name}/
├── sources/          ← Raw inputs (immutable)
├── wiki/             ← Living knowledge base (shared across all skills)
│   ├── index.md      ← Content catalog
│   ├── log.md        ← Change timeline
│   ├── business.md   ← Business fundamentals
│   ├── market.md     ← Local market dynamics
│   ├── competitors.md ← Competitive landscape
│   ├── audience.md   ← Audience & psychology
│   ├── benchmarks.md ← Industry benchmarks
│   ├── digital-presence.md ← Digital audit
│   └── strategy.md   ← Strategic implications
├── deliverables/     ← Final outputs (reports, dashboards, ad copy)
│   ├── brand-config.json
│   ├── research-dashboard.html
│   └── ...
└── wiki-config.json  ← Wiki metadata
```

## How Other Skills Consume the Wiki

### meta-ad-copywriter
- **Reads:** `wiki/audience.md` — pain points, decision triggers, objections, customer language
- **Reads:** `wiki/competitors.md` — competitor messaging to differentiate against
- **Reads:** `wiki/strategy.md` — positioning gaps that become ad angles
- **Reads:** `deliverables/brand-config.json` — brand identity for creative consistency

### Campaign Dashboard Builder
- **Reads:** `wiki/benchmarks.md` — KPI targets (CPC, CPM, ROAS estimates)
- **Reads:** `wiki/competitors.md` — competitive context for campaign architecture
- **Reads:** `deliverables/brand-config.json` — brand colors/fonts

### Content Calendar / Video Idea Generator
- **Reads:** `wiki/audience.md` — pain points and decision triggers (content themes)
- **Reads:** `wiki/competitors.md` — content gaps (opportunities)
- **Reads:** `wiki/strategy.md` — messaging themes and hooks

### Performance Reporting (future)
- **Reads:** `wiki/benchmarks.md` — compare actual vs estimated
- **Writes:** `wiki/benchmarks.md` — update with actual performance data (INGEST operation)
- **Writes:** `wiki/audience.md` — update with real audience insights from ad data

## Cross-Skill Flagging

During research, if findings are directly actionable by another skill, note it in `wiki/strategy.md`:

- "Positioning gap X maps to a Meta ad angle — ready for meta-ad-copywriter"
- "Content gap Y could drive TOFU traffic — consider content calendar skill"
- "Competitor Z's ad messaging weakness is exploitable — flag for campaign strategy"

Don't do the other skill's job. Flag the connection and move on.

## Wiki Compounding Across Skills

The wiki grows from multiple skills, not just market-research:

1. **market-research** creates the wiki and populates all pages from Perplexity data
2. **meta-ad-copywriter** reads audience/strategy, may update strategy.md with creative insights
3. **performance reporting** updates benchmarks.md with actual campaign data
4. **client calls/briefs** trigger manual INGEST into business.md or strategy.md

Each skill that writes to the wiki follows the same accuracy protocol (EXTRACTED/INFERRED/BLANK) and updates log.md with what changed.
