# Strategy Report Structure (Markdown)

The markdown report is the comprehensive strategy document covering all 8 dimensions. Every section includes rationale, specific settings, and monitoring notes.

---

## Template

```markdown
# Paid Media Strategy: {Business Name}

> **Prepared for:** {Client/Consultant Name}
> **Date:** {Date}
> **Platform Focus:** {Google Ads / Meta Ads / Both}
> **Monthly Budget:** {Budget Range}
> **Primary Objective:** {Purchase / Lead / App Install / Booking}
> **Geographic Scope:** {Target Markets}
> **Sources:** Market research wiki, {platform} reference data, client intake answers

---

## Executive Summary

{3-5 paragraphs synthesizing the strategy. Cover: what we're building, why this architecture, what we expect to achieve, and the phased approach. Every claim traces to a section below.}

---

## 1. Campaign Architecture
**Platform:** {Google / Meta / Both}

### 1.1 Campaign Structure Overview
{Visual representation of account → campaign → ad group/ad set hierarchy. Include naming convention.}

### 1.2 Campaign Details
{For each campaign: type, objective, optimization event, daily budget, bidding strategy, rationale.}

### 1.3 Structure Rationale
{Why this structure vs alternatives. Reference platform best practices from reference files.}

### What to Watch
{Signs the structure needs adjustment — cannibalizing, learning limited, budget misallocation.}

---

## 2. Bidding Strategy
**Platform:** {Google / Meta / Both}

### 2.1 Strategy by Campaign
{Each campaign: bidding strategy, target (if applicable), rationale, when to adjust.}

### 2.2 Learning Phase Management
{How to handle learning phase, what NOT to change, when to expect stability.}

### 2.3 Scaling Rules
{Budget increase limits, bid strategy transition triggers, timeline.}

### What to Watch
{CPA spikes, underspend, learning limited flags, conversion volume drops.}

---

## 3. Audience & Targeting

### 3.1 Google Targeting (if applicable)
{Keyword strategy: match types, clusters, negatives. Audience layers: observation vs targeting.}

### 3.2 Meta Targeting (if applicable)
{Audience architecture: broad, interests, lookalikes, custom, retargeting. Advantage+ settings.}

### 3.3 Exclusions
{Who to exclude and why — existing customers, irrelevant geos, competitor employees.}

### What to Watch
{Audience overlap, fatigue indicators, search term report red flags.}

---

## 4. Budget Allocation

### 4.1 Platform Split (if both)
{Google vs Meta allocation with rationale.}

### 4.2 Campaign-Level Allocation
{Budget per campaign with percentage and dollar amount.}

### 4.3 Monthly Projection
{Month 1, 2, 3 spend plan with scaling assumptions.}

### 4.4 Unit Economics
{Full funnel math: budget → impressions → clicks → leads/purchases → revenue → ROI.}

### What to Watch
{Overspend alerts, underspend patterns, platform rebalancing triggers.}

---

## 5. Creative Direction

### 5.1 Format Recommendations
{Prioritized format list per platform with specs.}

### 5.2 Messaging Angles
{Derived from wiki buyer personas: each persona → hook, pain point, CTA.}

### 5.3 Testing Framework
{What to test, how many variants, kill rules, refresh cadence.}

### What to Watch
{CTR decline = fatigue, hook rate drops, frequency > 3 on Meta.}

---

## 6. Conversion & Measurement Setup

### 6.1 Tracking Requirements
{What needs to be implemented before launch: pixels, CAPI, enhanced conversions, GTM.}

### 6.2 Primary vs Secondary Conversions
{Which events to optimize toward, which to track for signals only.}

### 6.3 Attribution
{Attribution model, conversion windows, cross-platform considerations.}

### What to Watch
{Tracking discrepancies, modeled vs observed gaps, consent mode impact.}

---

## 7. KPI Targets & Measurement Plan

### 7.1 KPI Dashboard
{Target metrics: CPC, CTR, conversion rate, CPA/ROAS, volume, spend efficiency.}

### 7.2 Reporting Cadence
{Daily checks, weekly reports, monthly reviews — what to look at when.}

### 7.3 Optimization Triggers
{Specific thresholds that trigger action: "If CPA exceeds $X for 7 days, do Y."}

---

## 8. Phased Execution Plan

### Phase 1: Foundation (Days 1-30)
{Launch actions, expected outcomes, success criteria for moving to Phase 2.}

### Phase 2: Optimize (Days 30-60)
{Optimization actions, scaling triggers, testing plan.}

### Phase 3: Scale (Days 60-90)
{Expansion plan, new campaign types, budget increase plan.}

---

## Data Gaps & Assumptions

{What we don't know, what assumptions underpin the strategy, what additional data would improve it. BLANK fields with reasons.}

## Sources

{All sources: wiki pages, reference data, platform benchmarks, client intake answers.}
```

---

## Writing Guidelines

1. **Source label every data point.** [EXTRACTED] from wiki, [INFERRED] from strategy logic.
2. **BLANK when uncertain.** Include the blank with reason — especially for budget projections and KPI targets that depend on unknown conversion rates.
3. **Explain decisions, not just list them.** "Use Maximize Conversions because..." not just "Use Maximize Conversions."
4. **Label recommendations.** "data-supported" (backed by wiki data) or "directional" (strategy logic without hard numbers).
5. **"What to Watch" per section.** Every strategy decision can go wrong — tell the user what signals to monitor.
6. **Tables for comparisons.** Campaign details, budget allocation, KPI targets — tables are expected.
7. **Executive summary last.** Write it after all sections are complete.
