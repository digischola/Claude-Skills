# Skill Coordination — Paid Media Strategy

How this skill connects to the pipeline.

---

## Upstream (Input Sources)

### market-research skill → this skill
**Consumes:**
- `{client-folder}/wiki/` — all wiki pages (strategy.md, offerings.md, competitors.md, audiences.md)
- `{client-folder}/deliverables/brand-config.json` — for dashboard branding
- `{client-folder}/deliverables/{name}-market-research.md` — full research report
- `{client-folder}/sources/` — keyword CSVs, Perplexity raw output

**Key data points used:**
- Market size and growth rate → informs budget ambition
- Competitor ad activity → informs competitive positioning and budget
- Keyword clusters + CPC ranges → informs Google campaign structure
- Buyer personas → informs audience targeting and creative direction
- Industry benchmarks (CPC, CTR, CPA, ROAS) → informs KPI targets
- Blue ocean opportunities → informs targeting priorities
- Unit economics → informs bidding targets and ROI projections

**If market-research hasn't run:** Flag it. This skill depends on wiki data. Can run without it in degraded mode (more BLANKs, more directional recommendations) but output quality drops significantly.

## Downstream (Output Consumers)

### this skill → ad-copywriter skill
**Produces:**
- Creative direction (format recommendations, messaging angles per persona)
- Campaign names and types (so copy is written for the right context)
- Platform-specific creative specs
- Testing framework (what angles to test first)

**Handoff format:** Wiki strategy.md update + strategy report section 5 (Creative Direction)

### this skill → campaign-setup skill
**Produces:**
- Campaign architecture (exact campaign names, types, objectives)
- Bidding strategies per campaign
- Budget allocation per campaign
- Targeting details (keywords, audiences, match types, exclusions)
- Conversion setup requirements
- CSV media plan for direct implementation

**Handoff format:** CSV media plan + wiki strategy.md + strategy report

### this skill → performance-reporting skill (future)
**Produces:**
- KPI targets (CPC, CTR, conversion rate, CPA/ROAS targets)
- Optimization triggers (thresholds for action)
- Reporting cadence recommendations
- Phase milestones for progress tracking

**Handoff format:** CSV KPI targets section + strategy report section 7

## Cross-Skill Data Flow

```
market-research
    ├── wiki/ (all pages)
    ├── brand-config.json
    ├── keyword CSVs
    └── research report
         │
         ▼
paid-media-strategy (this skill)
    ├── strategy report (.md)
    ├── strategy dashboard (.html)
    ├── media plan (.csv)
    └── wiki/strategy.md (updated)
         │
         ├──▶ ad-copywriter (creative direction, messaging angles)
         ├──▶ campaign-setup (campaign architecture, CSV media plan)
         └──▶ performance-reporting (KPI targets, optimization triggers)
```

## Wiki Updates

This skill updates these wiki pages:
- `wiki/strategy.md` — full strategy summary (create or update)
- `wiki/log.md` — add STRATEGY entry with date and scope
- `wiki/index.md` — add strategy page if new

Does NOT modify:
- `wiki/offerings.md` — market-research owns this
- `wiki/competitors.md` — market-research owns this
- `wiki/audiences.md` — market-research owns this (but strategy may reference and enrich)
