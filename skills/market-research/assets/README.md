# Assets Directory

## Dashboard Template Approach

This skill does NOT use a static HTML template. Each dashboard is built from scratch using the specifications in `references/dashboard-specs.md` because:

1. Every dashboard is heavily customized to the client's data, brand, and platform focus
2. Chart.js visualizations are data-driven (not placeholder-swappable)
3. The number and type of charts varies by what data is available

## Quality Reference

The benchmark for dashboard quality is the CrownTech dashboard:
`Gargi Modi/CrownTech/deliverables/CrownTech_Market_Research_Presentation.html`

Every new dashboard should match or exceed this quality level for:
- Chart.js visualizations (radar, bar, line, doughnut)
- Tooltips on every KPI
- Collapsible detail sections
- Client brand colors from brand-config.json
- Keyword data tables from platform CSVs
- Source indicators (EXTRACTED/INFERRED/BLANK)
