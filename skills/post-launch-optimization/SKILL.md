---
name: post-launch-optimization
description: "Weekly post-launch campaign optimization for Meta and Google Ads. Pulls live data via Windsor.ai MCP, runs 11-layer analysis (health check, diagnosis, prescription, creative intelligence, testing framework, competitive context, benchmarking, cross-platform, trend analysis, action prioritization, session memory), produces actionable report + HTML dashboard. Works standalone (any client with Windsor.ai connected) or downstream (reads wiki/strategy from prior skills). Use when user mentions: optimize, optimization, campaign review, performance analysis, weekly review, what's working, kill/scale, ad performance, CPA too high, ROAS check, audit campaigns, analyze ads, check performance, fire check. Do NOT trigger for: campaign setup, ad copy writing, market research, landing page audit, media strategy, budget planning."
---

# Post-Launch Optimization

Pulls live campaign data via Windsor.ai MCP, analyzes across 11 layers, and produces a prioritized action report + HTML dashboard. Weekly cadence. Per-client output.

## Context Loading

Read these shared context files before starting:
- `shared-context/analyst-profile.md` — workflow, client types, quality standards
- `shared-context/accuracy-protocol.md` — 3 accuracy rules for all data handling

## Process Overview

### Step 1: Client Identification & Config

Check Windsor.ai MCP for connected accounts:
```
get_connectors(include_not_yet_connected=false)
```

If client has a wiki folder (`{client-folder}/wiki/`), read:
- `wiki/strategy.md` — campaign architecture, targets, personas
- `wiki/index.md` — what skills have been run
- `deliverables/*-optimization-report.md` — previous analysis (session memory, Layer 11)

If no wiki exists (standalone mode), ask:
1. Which account(s) to analyze? (show connected accounts)
2. What conversion event matters? (purchases, leads, landing page views)
3. Monthly budget?
4. Any specific concerns?

Build/read client config. See `references/client-config-spec.md` for format.

### Step 2: Data Pull via Windsor.ai MCP

Run all queries defined in `references/data-queries.md`. 12 queries total:
- Meta: 6 queries (campaign health, ad set, ad creative, video metrics, demographics, placements)
- Google: 6 queries (campaign health, ad group + keyword, search terms, ad performance, device + time, auction insights)

Skip platform queries if client doesn't use that platform. Date ranges:
- Primary: last 30 days
- Comparison: previous 30 days (for trend detection)
- Daily breakdown: last 14 days (for Layer 9 trend analysis)

### Step 3: Run 11-Layer Analysis

Load `references/analysis-framework.md` for thresholds and logic.

| Layer | Purpose | Key Output |
|---|---|---|
| 1. Health Check | Budget pacing, CPA/ROAS vs baseline, frequency, learning phase | Red/amber/green status per campaign |
| 2. Diagnosis | Campaign/ad set/ad/keyword ranking by efficiency | Bottom 20% flagged |
| 3. Prescription | Kill/scale/test decisions with spend amounts | Specific actions with thresholds |
| 4. Creative Intelligence | Fatigue detection, hook rate, hold rate | Refresh triggers |
| 5. Testing Framework | What to test next, sample size checks | Test recommendations |
| 6. Competitive Context | Auction insights, impression share shifts | Competitor alerts |
| 7. Benchmarking | Client metrics vs vertical benchmarks | Above/below benchmark flags |
| 8. Cross-Platform | Unified CPA comparison, budget allocation | Platform shift recommendations |
| 9. Trend Analysis | Daily/weekly trends, anomaly detection | Trend direction + anomalies |
| 10. Action Prioritization | Top 3-5 actions ranked by impact x confidence x effort | Prioritized action list |
| 11. Session Memory | Compare to last analysis, track recommendation outcomes | Progress tracking |

### Step 4: Generate Report

Save as `{client-folder}/deliverables/{business-name}-optimization-report.md`.

Report structure defined in `references/output-format-spec.md`. Key sections:
- Executive summary (5 lines max — what happened, what to do)
- Health dashboard (red/amber/green per campaign)
- Top 3-5 actions (from Layer 10) with specific implementation steps
- Platform-by-platform breakdown
- Creative performance with fatigue flags
- Trend charts (text-based for markdown, visual for dashboard)
- Appendix: full data tables

Source label every finding: `[DATA]` (from Windsor.ai), `[CALCULATED]` (derived metric), `[BENCHMARK]` (from reference data), `[INFERRED]` (analyst synthesis).

### Step 5: Generate Dashboard

Save as `{client-folder}/deliverables/{business-name}-optimization-dashboard.html`.

Read `references/output-format-spec.md` (Dashboard Structure section) for layout and components. Read client's `brand-config.json` for styling if available.

Dark mode, client branding, aggressive animations. Key components:
- Health status cards (red/amber/green)
- Spend pacing gauge
- CPA/ROAS trend sparklines
- Campaign ranking table (sortable)
- Creative winner/loser grid
- Action priority list with impact scores

### Step 6: Update Wiki & Session Memory

Update `{client-folder}/wiki/log.md` — add OPTIMIZATION entry with date and key findings.
Save analysis snapshot for Layer 11 next-session comparison.

If first analysis: establish baseline metrics and save to client config.

### Step 7: Validate & Close

Run `scripts/validate_output.py` against report and dashboard. Validator checks all 9 required dashboard components (header bar, health cards, spend pacing gauge, action priority cards, campaign ranking table, creative grid, trend sparklines, benchmark comparison, cross-platform comparison) — missing components are CRITICAL failures.
Run feedback loop per `references/feedback-loop.md`.
Flag if any campaigns need urgent action before next weekly review.

## Fire Check Mode (Lightweight)

When user says "quick check" or "fire check" — run Layer 1 only:
- Pull campaign health query (1 query per platform)
- Flag: overspend, paused campaigns, CPA >3x baseline, frequency >4.0
- Output: 5-line summary in chat, no report/dashboard generated

## Failure Handling

- Windsor.ai MCP not connected → instruct user to connect, provide setup link
- Account not found → show available accounts via get_connectors
- No data for date range → try shorter range, warn if account is new
- No previous analysis (Layer 11) → establish baseline, skip comparison
- Brand-config.json missing → use default dark theme for dashboard

## Learnings & Rules

- [2026-04-16] [WELLNESS/RETREAT] First battle test on Thrive Retreats (Meta + Google). Windsor.ai MCP data pull worked flawlessly — all Meta queries (MQ1-MQ6, MQ-Daily) and Google GQ1 returned structured data. Google detailed queries (GQ2-GQ6) were deferred to Analysis #2 to manage query volume on first run. → For dual-platform clients, run Meta full + Google GQ1 on first analysis, then GQ2-GQ6 on second.
- [2026-04-16] [WELLNESS/RETREAT] Google `get_options` returns 95K+ characters — too large to process raw. Use python script to extract field names only. → Always filter get_options output to just field names before analysis.
- [2026-04-16] [WELLNESS/RETREAT] Baseline-first approach validated — all campaigns marked BASELINE on first run. Kill/scale recommendations are observational only until Analysis #2 provides comparison data. This prevents overreacting to single-period data.
- [2026-04-16] [GENERAL] Dashboard validator checked only 4 components (health cards, action list, campaign table, animation). → Updated validator to check all 9 required components from output-format-spec.md: header bar, health cards, spend pacing gauge, action priority cards, campaign ranking table, creative grid, trend sparklines, benchmark comparison, cross-platform comparison. Animation check kept as separate design-rule warning. Missing components now raise CRITICAL (was WARNING).
- [2026-04-16] [GENERAL] The `references/dashboard-spec.md` file referenced in SKILL.md Step 5 does not exist — dashboard spec is embedded in `output-format-spec.md`. → Update Step 5 reference path or create separate file.
- [2026-04-16] [Validator hardening] Finding: validator checked `targets.mode` enum but never sanity-checked the baseline timeline. A stale `baseline_set_date` (e.g. from 3 months ago, with 6 subsequent analyses) would silently anchor kill/scale decisions against old baselines instead of recalibrated ones. analysis-framework.md mandates recalibration every 4 analyses but nothing enforced it. → Action: added baseline-date sanity check to `validate_config()` — parses `targets.baseline_set_date`, flags CRITICAL if in the future (config broken), WARNING if >100 days old with ≥4 prior analyses (overdue recalibration), and WARNING if mode='baseline' but baseline_set_date missing while history has entries (config out of sync). First-run behavior (empty history) produces INFO only.
