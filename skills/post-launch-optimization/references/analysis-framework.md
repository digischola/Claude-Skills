# Analysis Framework — 11 Layers

Load this file in Step 3. Contains decision thresholds, analysis logic, and output structure for each layer.

## Universal Rules

1. **Minimum data threshold.** Don't analyze segments with <$20 spend or <200 impressions — noise, not signal.
2. **Conversion lag.** Meta reports conversions on click date. A campaign that looks dead today may have conversions attributing tomorrow. Flag "insufficient data" for campaigns <7 days old.
3. **Learning phase.** Meta ad sets need ~50 conversions in 7 days to exit learning phase. Google campaigns need 15-30 conversions in 30 days. Don't kill campaigns still in learning unless spend is extreme.
4. **Baseline-first.** If no previous analysis exists, the first run establishes baselines — no kill/scale recommendations on first run. Observe, benchmark, then optimize.

---

## Layer 1: Health Check

**Purpose:** Is the account healthy? Red/amber/green per campaign.

**Inputs:** MQ1, GQ1 (current + comparison period)

**Status thresholds:**

| Metric | Green | Amber | Red |
|---|---|---|---|
| Budget pacing (% of expected spend) | 85-110% | 70-85% or 110-130% | <70% or >130% |
| CPA vs baseline | <1.2x baseline | 1.2-2x baseline | >2x baseline |
| ROAS vs baseline | >0.8x baseline | 0.5-0.8x baseline | <0.5x baseline |
| Frequency (Meta) | <2.0 | 2.0-3.5 | >3.5 |
| Impression share (Google) | >60% | 30-60% | <30% |
| Learning phase | Exited | In learning, <7 days | In learning, >14 days |

**Output:** One-line status per campaign with color code and primary concern.

**First-run behavior:** All campaigns get "BASELINE" status. Record current metrics as the benchmark.

---

## Layer 2: Diagnosis

**Purpose:** Where exactly are the problems?

**Inputs:** MQ2, MQ3, MQ5, MQ6, GQ2, GQ4, GQ5

**Analysis steps:**

1. **Rank all campaigns** by CPA (ascending). Top 25% = "carrying the account." Bottom 25% = "dragging the account."
2. **Within each campaign, rank ad sets/ad groups** by CPA. Flag any with CPA >2x campaign average.
3. **Within each ad set, rank ads** by CPA. Flag bottom performers with >$30 spend.
4. **Demographic analysis (Meta):** Cross-tab age × gender. Identify segments spending >15% of budget with <5% of conversions.
5. **Placement analysis (Meta):** Compare CPA across Feed, Stories, Reels, Audience Network. Flag any placement with CPA >3x best placement.
6. **Device analysis (Google):** Compare mobile vs desktop CPA. Flag if gap >2x.
7. **Day/time analysis (Google):** Flag worst-performing day if CPA >2x best day.
8. **Keyword analysis (Google):** Flag keywords with quality score <5. Flag keywords with spend >$50 and 0 conversions.

**Output:** Ranked tables with flags and specific problem identifiers.

---

## Layer 3: Prescription

**Purpose:** What to do about Layer 2 findings. Specific actions, not insights.

**Decision matrix:**

### Kill (pause/remove)
- Ad/ad set with CPA >3x baseline AND spend >$50 AND <2 conversions in 30 days
- Keywords with spend >$50 AND 0 conversions AND quality score <5
- Placements with CPA >3x best placement AND >$30 spend
- Age/gender segments with >$50 spend AND 0 conversions
- Search terms: irrelevant with spend >$20

### Scale (increase budget/bid)
- Campaigns/ad sets with CPA <0.5x baseline AND >10 conversions
- Keywords with CPA <0.5x target AND quality score >7
- Not in learning phase
- Has headroom (Meta frequency <2.5, Google IS loss >20% from budget)

### Test (needs more data)
- CPA between 0.5-2x baseline AND <20 conversions
- New campaigns <14 days old
- Campaigns in learning phase with reasonable early metrics

### Adjust (optimize without killing)
- Bid adjustments: device +/- 20% based on CPA differential
- Dayparting: reduce bids during worst-performing hours/days
- Negative keywords: add from search terms analysis
- Audience refinements: exclude worst demographics

**Output:** Action list with specific implementation steps:
```
[KILL] Campaign X > Ad Set Y > Ad Z — $87 spent, 0 conversions, CPA ∞. Pause immediately.
[SCALE] Campaign A > Ad Set B — CPA $12 vs $30 baseline, 24 conversions. Increase daily budget from $20 to $35.
[NEGATIVE] Add "free" as campaign-level negative in Campaign X — 23 clicks, $41 spent, 0 conversions.
```

---

## Layer 4: Creative Intelligence

**Purpose:** Is creative fatiguing? What patterns win?

**Inputs:** MQ3, MQ4

**Fatigue signals (any 2 of 3 = fatigued):**
1. Frequency >3.5 at ad level
2. CTR declined >30% from peak (compare first 7 days vs last 7 days)
3. CPA increased >50% from first week

**Video analysis:**
- Hook rate (3s views / impressions): <25% = weak hook
- Hold rate (ThruPlay / 3s views): <30% = weak content
- Drop-off curve: biggest drop between which quartiles?
  - p25→p50 drop >50% = lose interest after hook
  - p50→p75 drop >50% = video too long or loses momentum
  - p75→p100 drop >50% = weak ending/CTA

**Winner pattern analysis:**
- Among top 3 ads by CPA: what's common? (format, copy length, image style, CTA)
- Among bottom 3 ads by CPA: what's common?
- Output a "winning creative profile" paragraph

**Refresh recommendations:**
- URGENT: >2 fatigue signals + CPA >2x baseline → new creative needed this week
- PLAN: 1 fatigue signal → start producing replacement creative
- MONITOR: no fatigue signals → continue running

---

## Layer 5: Testing Framework

**Purpose:** What to test next and how to evaluate.

**Test priority logic:**
1. Biggest spend item with no A/B test running → test there first (most impact)
2. Areas where Layer 2 flagged a problem → test a fix
3. New creative concepts from Layer 4 winner pattern analysis

**Minimum sample sizes before declaring winner:**
- Impressions: >1,000 per variant
- Conversions: >20 per variant
- Run time: >7 days (covers day-of-week variation)
- Statistical method: if >2x difference in CPA with >20 conversions each, declare winner. Under that, need more data.

**Testing rules:**
- Max 2 tests per ad set simultaneously
- Only change one variable per test (copy, image, audience, placement — not multiple)
- Document what's being tested and hypothesis

**Output:**
```
[TEST] Campaign X > Ad Set Y: Test new headline variant against current winner.
Hypothesis: Question-based headline will improve CTR.
Minimum run: 7 days, need 20+ conversions per variant.
```

---

## Layer 6: Competitive Context

**Purpose:** Are performance changes driven by competitors or by us?

**Inputs:** GQ6

**Analysis:**
- List top 5 competitors by impression share
- Compare to previous analysis (Layer 11): who's new, who grew, who declined?
- If client's impression share dropped AND a competitor's grew by similar amount → competitive pressure, not ad quality
- If client's impression share dropped AND no competitor gained → likely a quality/bid issue

**Meta note:** Meta doesn't have auction insights. For Meta, competitive context is limited to qualitative observation (quality/engagement/conversion rankings from MQ3).

**Output:** Competitor landscape paragraph + specific alert if new/aggressive competitor detected.

---

## Layer 7: Benchmarking

**Purpose:** How does this client compare to industry norms?

**Inputs:** Client metrics from Layer 1 + `references/industry-benchmarks.md`

**Analysis:**
- Compare client's CTR, CPC, CPA, conversion rate, ROAS vs vertical benchmarks
- Flag metrics >2 standard deviations below benchmark → "significantly underperforming industry"
- Flag metrics >1.5x above benchmark → "outperforming — protect what's working"

**Context matters:**
- Benchmarks are ranges, not exact numbers
- Client's funnel, price point, and geography affect comparisons
- Use benchmarks as context, not as targets — a $210K architecture product will have different CPA than a $50 yoga class

**Output:** Benchmark comparison table with "above/at/below" industry indicators.

---

## Layer 8: Cross-Platform

**Purpose:** Unified view when client runs both Google and Meta.

**Inputs:** MQ1, GQ1

**Analysis:**
- Unified CPA: what's the blended CPA across both platforms?
- Which platform delivers cheaper conversions?
- If CPA gap >50% between platforms, recommend budget shift
- Calculate: "If we shifted $X from [expensive platform] to [cheap platform], projected impact = Y additional conversions"
- Attribution note: both platforms claim credit. True unified CPA ≈ total spend / total unique conversions (estimate overlap at 10-20%)

**Output:** Cross-platform comparison table + budget reallocation recommendation if applicable.

**Single-platform clients:** Skip this layer entirely.

---

## Layer 9: Trend Analysis

**Purpose:** Is performance improving, stable, or degrading?

**Inputs:** MQ-Daily, GQ-Daily

**Analysis:**
1. **7-day rolling average** for CPA, CTR, CPC across last 14 days
2. **Trend direction:** Fit a simple direction:
   - Last 7d average CPA < previous 7d average CPA → improving
   - Within 10% → stable
   - Last 7d > previous 7d → degrading
3. **Anomaly detection:** Any single day with CPA >3x the 7-day rolling average → flag as anomaly
   - Check: did spend spike that day? (budget change)
   - Check: did impressions drop? (competition or audience exhaustion)
   - Check: is it a known low-conversion day? (weekends for B2B)
4. **Conversion lag check:** For Meta, compare conversions reported today for clicks from 3-7 days ago vs clicks from 0-2 days ago. If recent days have significantly fewer conversions, it's likely lag, not a real decline.

**Output:** Trend direction per campaign (improving/stable/degrading) + any anomaly flags with probable cause.

---

## Layer 10: Action Prioritization

**Purpose:** Reduce all findings to top 3-5 actions ranked by impact.

**Scoring formula:**

```
Priority Score = Impact × Confidence × Ease
```

- **Impact** (1-5): How much spend/performance is affected?
  - 5 = affects >50% of account spend
  - 4 = affects 20-50% of spend
  - 3 = affects 10-20% of spend
  - 2 = affects 5-10% of spend
  - 1 = affects <5% of spend

- **Confidence** (1-5): How much data supports this recommendation?
  - 5 = >50 conversions, >$200 spend, clear pattern
  - 4 = 20-50 conversions, strong signal
  - 3 = 10-20 conversions, moderate signal
  - 2 = 5-10 conversions, directional
  - 1 = <5 conversions, speculative

- **Ease** (1-5): How easy to implement?
  - 5 = one click (pause ad, add negative keyword)
  - 4 = 5-minute change (bid adjustment, budget shift)
  - 3 = 30-minute task (new ad creative, audience restructure)
  - 2 = half-day project (new campaign build, landing page change)
  - 1 = multi-day project (full creative refresh, campaign restructure)

**Output:** Ranked list of top 3-5 actions:
```
#1 [Score: 60] KILL 3 underperforming ads in Website Sales (Impact 5, Confidence 4, Ease 3)
    → Saves ~$120/week, redirects spend to winners
#2 [Score: 48] ADD 12 negative keywords in Brand Search (Impact 4, Confidence 4, Ease 5)
    → Eliminates $85/month wasted spend on irrelevant queries
#3 [Score: 36] SCALE Ad Set B daily budget from $20→$35 (Impact 3, Confidence 4, Ease 5)
    → CPA 60% below baseline, room to grow
```

---

## Layer 11: Session Memory

**Purpose:** Track what was recommended last time and whether it worked.

**Inputs:** Previous `{business-name}-optimization-report.md`

**Analysis:**
1. Read previous report's action list
2. Check current data: did the recommended actions get implemented?
   - If a "KILL" recommendation was made → is that ad/keyword still active?
   - If a "SCALE" recommendation was made → did budget increase?
   - If metrics improved after recommendations → note what worked
3. Compare current baselines to previous baselines:
   - CPA trend over multiple analyses
   - ROAS trend
   - Spend efficiency trend

**First-run behavior:** No previous report → skip Layer 11, establish baselines.

**Output:** "Since last analysis" comparison section + recommendation follow-up tracker.

---

## Layer Execution Order

1. **Layer 1** (Health Check) — establishes the big picture
2. **Layer 9** (Trend Analysis) — is it getting better or worse?
3. **Layer 2** (Diagnosis) — where exactly are the problems?
4. **Layer 4** (Creative Intelligence) — is creative the issue?
5. **Layer 6** (Competitive Context) — is it us or the market?
6. **Layer 7** (Benchmarking) — how do we compare to industry?
7. **Layer 8** (Cross-Platform) — unified view
8. **Layer 3** (Prescription) — what to do about it all
9. **Layer 5** (Testing Framework) — what to test next
10. **Layer 10** (Action Prioritization) — top 3-5 actions
11. **Layer 11** (Session Memory) — compare to last time
