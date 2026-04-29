# Skill Coordination — Paid Media Strategy

How this skill connects to the pipeline.

---

## Upstream (Input Sources)

### market-research skill → this skill
**Consumes:**
- `{client-folder}/_engine/wiki/` — all wiki pages (strategy.md, offerings.md, competitors.md, audiences.md)
- `{client-folder}/_engine/brand-config.json` (single-program) or `{client-root}/_engine/brand-config.json` (multi-program) — for dashboard branding
- `{client-folder}/_engine/working/market-research.md` (default short name; legacy fallback `{client-folder}/_engine/working/*-market-research.md`) — full research report (intermediate)
- `{client-folder}/_engine/sources/` — keyword CSVs, Perplexity raw output

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
    ├── _engine/wiki/ (all pages)
    ├── _engine/brand-config.json
    ├── _engine/sources/ (keyword CSVs, Perplexity raw)
    └── research-dashboard.html (folder root, presentable; legacy `*-research-dashboard.html`) + _engine/working/market-research.md (legacy `*-market-research.md`)
         │
         ▼
paid-media-strategy (this skill)
    ├── _engine/working/paid-media-strategy.md (report)
    ├── strategy-dashboard.html (folder root, presentable)
    ├── _engine/working/media-plan.csv (intermediate)
    ├── _engine/working/creative-brief.json (handoff)
    └── _engine/wiki/strategy.md (updated)
         │
         ├──▶ ad-copywriter (creative direction, messaging angles)
         ├──▶ campaign-setup (campaign architecture, CSV media plan)
         └──▶ performance-reporting (KPI targets, optimization triggers)
```

## Wiki Updates

This skill updates these wiki pages (under `{client-folder}/_engine/wiki/`):
- `strategy.md` — full strategy summary (create or update)
- `log.md` — add STRATEGY entry with date and scope
- `index.md` — add strategy page if new

Does NOT modify:
- `offerings.md` — market-research owns this
- `competitors.md` — market-research owns this
- `audiences.md` — market-research owns this (but strategy may reference and enrich)
