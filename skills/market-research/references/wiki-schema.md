# Client Wiki Schema

Every client gets a persistent wiki — a living knowledge base that compounds across sessions. Based on Andrej Karpathy's LLM Wiki pattern adapted for marketing research.

---

## Per-Client Folder Structure

```
{Client Name}/
├── {Project or Business}/
│   ├── sources/                    ← Raw, immutable inputs
│   │   ├── perplexity-YYYY-MM-DD.md
│   │   ├── client-brief.md
│   │   ├── performance-YYYY-MM.csv
│   │   └── ...
│   ├── wiki/                       ← LLM-maintained, compounds over time
│   │   ├── index.md                ← Content catalog, updated on every ingest
│   │   ├── log.md                  ← Append-only chronological record
│   │   ├── business.md             ← Business fundamentals
│   │   ├── market.md               ← Local market dynamics
│   │   ├── competitors.md          ← Competitive landscape
│   │   ├── audience.md             ← Audience & customer psychology
│   │   ├── benchmarks.md           ← Industry benchmarks (Meta + Google)
│   │   ├── digital-presence.md     ← Digital presence & ad landscape
│   │   └── strategy.md             ← Strategic implications & recommendations
│   ├── deliverables/               ← Final outputs for client/team
│   │   ├── research-dashboard.html
│   │   ├── brand-config.json
│   │   └── ...
│   └── wiki-config.json            ← Wiki metadata (created date, last update, source count)
```

---

## Core Wiki Pages

### index.md
Content catalog. Updated on every ingest. Format:

```markdown
# {Business Name} — Knowledge Index

Last updated: {date}
Sources ingested: {count}

## Pages
- [Business Fundamentals](business.md) — {one-line summary} — Last updated: {date}
- [Market Dynamics](market.md) — {one-line summary} — Last updated: {date}
- [Competitors](competitors.md) — {one-line summary} — Last updated: {date}
- [Audience](audience.md) — {one-line summary} — Last updated: {date}
- [Benchmarks](benchmarks.md) — {one-line summary} — Last updated: {date}
- [Digital Presence](digital-presence.md) — {one-line summary} — Last updated: {date}
- [Strategy](strategy.md) — {one-line summary} — Last updated: {date}

## Sources
1. {source filename} — ingested {date} — {type: perplexity/csv/brief/manual}
2. ...
```

### log.md
Append-only timeline. Every ingest, query, or update gets an entry:

```markdown
# Change Log

## {YYYY-MM-DD}
- **INGEST** perplexity-2026-04-07.md — Created all 7 wiki pages from initial research
- **UPDATE** competitors.md — Added new competitor "Cablify" from client call notes
- **UPDATE** benchmarks.md — Updated CPC with actual campaign data (was $5-15 estimate, actual $8.40)
- **QUERY** "What messaging angles haven't we tested?" — Generated new strategy section
```

### Wiki Page Format (business.md, market.md, etc.)

Each wiki page follows this structure:

```markdown
# {Dimension Name}

> Last updated: {date} | Sources: {count} | Confidence: {HIGH/MEDIUM/LOW}

## Key Findings
{Bulleted findings, each with [EXTRACTED] or [INFERRED] label and source reference}

## Details
{Deeper analysis organized by sub-topic}

## Gaps & Unknowns
{What we don't know yet — BLANK fields with reasons, carried forward until filled}

## Marketing Implications
{So-what for campaigns — what this means for ad strategy, targeting, creative}

## Change History
- {date}: Initial creation from {source}
- {date}: Updated {section} from {source}
```

---

## Wiki Config (wiki-config.json)

```json
{
  "business_name": "CrownTECH",
  "project": "IT Relocation Services",
  "created": "2026-04-07",
  "last_updated": "2026-04-07",
  "sources_ingested": 1,
  "brand_config": "deliverables/brand-config.json",
  "pages": ["business", "market", "competitors", "audience", "benchmarks", "digital-presence", "strategy"]
}
```

---

## Key Principles

1. **Sources are immutable.** Raw inputs never get modified. The wiki synthesizes them.
2. **Wiki pages compound.** New data updates existing pages — doesn't replace them. Change history tracks what changed and why.
3. **Gaps carry forward.** BLANK fields from the first research pass stay visible until filled by new data. They're a to-do list, not a failure.
4. **Cross-references.** Wiki pages link to each other. A finding in competitors.md that affects strategy gets linked in both places.
5. **Source traceability.** Every claim traces back to a specific source file in sources/. The accuracy protocol (EXTRACTED/INFERRED/BLANK) applies to wiki content exactly like standalone reports.
6. **One wiki per project.** Different projects for the same client get separate wikis. CrownTech IT Relocation ≠ CrownTech Cloud Services.
