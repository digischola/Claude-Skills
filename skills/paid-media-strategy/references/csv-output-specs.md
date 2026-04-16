# CSV Media Plan Output Specification

The CSV media plan is the spreadsheet-ready output that allows the user (or downstream campaign-setup skill) to directly implement the strategy. It should be structured so it can be opened in Excel/Google Sheets and immediately used for campaign building.

---

## File Structure

Generate a single CSV with multiple logical sections separated by blank rows and section headers. Alternatively, if the skill has xlsx capability, produce an Excel file with separate tabs.

### Section 1: Campaign Overview

```csv
Section: Campaign Overview
Campaign Name,Platform,Campaign Type,Objective,Optimization Event,Daily Budget,Monthly Budget,Bidding Strategy,Bid Target,Status
Brand Search,Google,Search,Conversions,Lead,15,450,Target Impression Share,90% Top of Page,Phase 1
Non-Brand Search,Google,Search,Conversions,Lead,50,1500,Maximize Conversions,-,Phase 1
PMax - Lead Gen,Google,Performance Max,Conversions,Lead,35,1050,Maximize Conversions,-,Phase 2
Prospecting - Broad,Meta,Sales,Conversions,Lead,40,1200,Highest Volume,-,Phase 1
Retargeting - Web Visitors,Meta,Sales,Conversions,Lead,15,450,Highest Volume,-,Phase 1
```

**Columns:**
- Campaign Name: naming convention = {audience/intent} - {descriptor}
- Platform: Google / Meta
- Campaign Type: Search, PMax, Display, Video, Demand Gen, Sales, Leads, Awareness, App Promotion
- Objective: platform-specific objective name
- Optimization Event: the specific conversion action
- Daily Budget: in client currency
- Monthly Budget: daily × 30
- Bidding Strategy: exact strategy name as it appears in the platform
- Bid Target: tCPA/tROAS value, or "-" if no target
- Status: Phase 1 (launch), Phase 2 (add), Phase 3 (add)

### Section 2: Ad Group / Ad Set Details

```csv
Section: Ad Groups / Ad Sets
Campaign Name,Ad Group/Ad Set Name,Targeting Type,Targeting Detail,Match Type/Audience Size,Placements,Estimated CPC/CPM,Notes
Non-Brand Search,High Intent Keywords,Keywords,"commercial cleaning services toronto, office cleaning company",Phrase Match,-,$3.50-5.00 CPC,Highest priority cluster
Non-Brand Search,Long Tail Keywords,Keywords,"commercial cleaning quote toronto, janitorial services near me",Broad Match,-,$2.00-3.50 CPC,Volume play with Smart Bidding
Prospecting - Broad,Broad 25-65,Broad Targeting,"Age 25-65, Location: Toronto GTA",~2M audience,Advantage+ Placements,$15-25 CPM,Let Advantage+ find converters
Retargeting - Web Visitors,7-Day Visitors,Custom Audience,"Website visitors last 7 days",~5K audience,Advantage+ Placements,$10-18 CPM,Hottest retargeting pool
```

**Columns:**
- Campaign Name: matches Section 1
- Ad Group/Ad Set Name: descriptive name
- Targeting Type: Keywords / Broad Targeting / Interest / Lookalike / Custom Audience / Remarketing / In-Market
- Targeting Detail: specific keywords, interests, audience definitions
- Match Type/Audience Size: keyword match type or estimated audience size
- Placements: specific placements or "Advantage+" / "All" / "Search Only"
- Estimated CPC/CPM: range from wiki benchmarks
- Notes: strategy rationale in brief

### Section 3: Monthly Budget Projection

```csv
Section: Monthly Budget Projection
Month,Google Budget,Meta Budget,Total Budget,Phase,Key Actions
Month 1,$2000,$1650,$3650,Foundation,"Launch core campaigns, establish baselines"
Month 2,$2500,$2000,$4500,Optimize,"Add PMax, scale winners, add retargeting"
Month 3,$3000,$2500,$5500,Scale,"Expand keywords/audiences, add Demand Gen/video"
```

### Section 4: KPI Targets

```csv
Section: KPI Targets
Metric,Google Target,Meta Target,Combined Target,Industry Benchmark,Source
CPC,$3.50,$1.20,-,$4.20 (Google) / $1.50 (Meta),[EXTRACTED] wiki benchmarks
CTR,4.5%,1.2%,-,3.8% (Search) / 0.9% (Meta),[EXTRACTED] wiki benchmarks
Conversion Rate,5.0%,3.0%,-,4.2% (Search) / 2.5% (Meta),[INFERRED] from wiki + strategy
CPA,$70,$40,$55,$85 industry avg,[INFERRED] from funnel math
Monthly Leads,30,40,70,-,[INFERRED] from budget ÷ CPA
ROAS,-,-,-,-,BLANK - insufficient data for ROAS projection
```

---

## Formatting Rules

1. **Use actual data from wiki and strategy analysis** — no placeholder values
2. **Source label the KPI targets** — [EXTRACTED], [INFERRED], or BLANK with reason
3. **Campaign names must match exactly** between Section 1 and Section 2
4. **Budget numbers must add up** — daily × 30 = monthly, campaign budgets sum to total
5. **Include all campaigns across all phases** — mark Phase 2/3 campaigns clearly
6. **Currency should match client's market** (USD, AUD, CAD, INR as appropriate)

## Downstream Consumption

This CSV is designed to be consumed by:
- **campaign-setup skill** — reads campaign names, types, budgets, targeting for direct implementation
- **Client review** — opens in Excel/Sheets for approval before building
- **Reporting baseline** — KPI targets become the benchmark for performance reporting
