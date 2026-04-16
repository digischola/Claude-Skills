# Output Format Spec

Load this file in Steps 4 and 5. Defines the report and dashboard structure.

## Report Structure (`{business-name}-optimization-report.md`)

```markdown
# {Client Name} — Weekly Optimization Report

**Date:** {date}
**Period:** {date_from} to {date_to}
**Platforms:** {Meta / Google / Both}
**Analysis #:** {sequential number}

---

## Executive Summary

{5 lines max. What happened. What to do. No fluff.}

---

## Account Health

| Campaign | Status | Spend | CPA | vs Baseline | Frequency/IS | Trend |
|---|---|---|---|---|---|---|

{Color-coded status: 🟢 Green, 🟡 Amber, 🔴 Red}

---

## Top Actions (Priority Ranked)

### #1: {Action title} [Score: XX]
**Type:** KILL / SCALE / TEST / ADJUST
**Where:** {Campaign > Ad Set > Ad/Keyword}
**Why:** {One sentence with data}
**How:** {Specific implementation steps}
**Expected Impact:** {Projected savings or improvement}

### #2: ...
### #3: ...

---

## Platform: Meta Ads

### Campaign Performance
{Table: campaigns ranked by efficiency}

### Ad Set Analysis
{Table: ad sets with flags}

### Creative Performance
{Table: ads with relevance diagnostics}
{Fatigue alerts if any}

### Video Performance
{Hook rate, hold rate, drop-off analysis — if video ads exist}

### Audience Insights
{Age × gender matrix with CPA}
{Placement breakdown with CPA}

---

## Platform: Google Ads

### Campaign Performance
{Table: campaigns ranked by efficiency}

### Keyword Performance
{Table: keywords with quality scores and flags}

### Search Terms Analysis
{Negative keyword recommendations}
{New keyword opportunities}

### Ad Performance
{RSA comparison within ad groups}

### Device & Time Patterns
{Device CPA comparison}
{Day-of-week patterns}

### Competitive Landscape
{Auction insights summary}
{Competitor movement alerts}

---

## Cross-Platform View

{Unified CPA comparison — only if both platforms active}
{Budget allocation recommendation}

---

## Trends (Last 14 Days)

{CPA trend direction per campaign: improving / stable / degrading}
{Anomaly flags with dates and probable cause}

---

## Benchmarks

| Metric | Client | Industry Range | Status |
|---|---|---|---|

---

## Since Last Analysis

{Comparison to previous report — only if Layer 11 has data}
{Recommendation follow-up: implemented? did it work?}
{Baseline shift tracking}

---

## Testing Recommendations

{What to test next, hypothesis, minimum sample size}

---

## Appendix: Full Data Tables

{Raw data tables for reference — campaign, ad set, ad, keyword level}
```

## Source Labels

Every finding must be tagged:
- `[DATA]` — directly from Windsor.ai query result
- `[CALCULATED]` — derived from raw data (CPA, ROAS, hook rate, etc.)
- `[BENCHMARK]` — from industry-benchmarks.md reference file
- `[INFERRED]` — analyst synthesis with stated evidence
- `[PREVIOUS]` — from prior optimization report (Layer 11)

## Dashboard Structure (`{business-name}-optimization-dashboard.html`)

Single-page HTML. Dark mode. Client branding from brand-config.json.

### Required Components

1. **Header bar** — Client name, date, analysis number, overall health indicator
2. **Health cards** (top row) — One card per campaign, color-coded (green/amber/red), showing spend, CPA, trend arrow
3. **Spend pacing gauge** — Circular or bar gauge showing % of monthly budget consumed vs expected
4. **Action priority cards** — Top 3-5 actions as prominent cards with impact scores
5. **Campaign ranking table** — Sortable by spend, CPA, conversions. Color-coded rows.
6. **Creative grid** — Top 3 winners vs bottom 3 losers with key metrics
7. **Trend sparklines** — Small line charts showing CPA, CTR, spend over last 14 days per campaign
8. **Benchmark comparison** — Horizontal bar chart showing client vs industry range
9. **Cross-platform comparison** — Side-by-side cards if both platforms active

### Design Rules

- Dark background (#0a0a0a or similar)
- Client accent color from brand-config.json (fallback: #3b82f6 blue)
- Aggressive animations: fade-in on scroll, counter animations for numbers, pulse on red alerts
- Mobile responsive (will be viewed on phone sometimes)
- All data rendered client-side from embedded JSON (no external dependencies)
- Total file size under 150KB
- Print-friendly mode (light background) via media query

### Animation Specs

```css
/* Counter animation for numbers */
@keyframes countUp { from { opacity: 0; transform: translateY(20px); } }

/* Fade in sections on scroll */
.section { animation: fadeIn 0.6s ease-out forwards; }

/* Pulse animation for red alerts */
.alert-red { animation: pulse 2s infinite; }

/* Sparkline draw animation */
.sparkline path { stroke-dasharray: 1000; stroke-dashoffset: 1000; animation: draw 2s forwards; }
```

### Interactivity

- Campaign table: click column headers to sort
- Health cards: hover for detailed metrics tooltip
- Action cards: expandable for full implementation steps
- Date range displayed prominently (no confusion about what period the data covers)
