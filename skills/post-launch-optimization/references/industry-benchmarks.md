# Industry Benchmarks Reference

Load this file in Layer 7. Contains benchmark ranges by vertical for Meta and Google Ads.

**Source:** Compiled from WordStream, LOCALiQ, Databox annual reports, and industry publications. Ranges, not exact numbers — use as directional context, not absolute targets.

**Last updated:** 2026-04-16 (initial build — needs Perplexity research to fill gaps)

**Important:** These are global/US-centric benchmarks. Australian market may differ. Label all benchmark comparisons as `[BENCHMARK — directional only]`.

---

## Meta Ads Benchmarks by Vertical

| Vertical | CTR (Link) | CPC (AUD) | CPM (AUD) | CPA Lead (AUD) | CPA Purchase (AUD) | CVR |
|---|---|---|---|---|---|---|
| Wellness / Retreats | 0.8-2.0% | $0.80-2.50 | $8-20 | $15-45 | $30-80 | 2-5% |
| Fitness / Yoga | 1.0-2.5% | $0.60-2.00 | $7-18 | $10-35 | $25-60 | 3-6% |
| Education / Training | 0.7-1.8% | $1.00-3.00 | $10-25 | $20-60 | $40-120 | 2-4% |
| Real Estate / Architecture | 0.5-1.5% | $1.50-4.00 | $12-30 | $25-75 | N/A | 1-3% |
| Hospitality / Events | 1.0-2.5% | $0.50-2.00 | $6-18 | $15-40 | $20-60 | 3-7% |
| E-commerce (general) | 1.0-2.0% | $0.50-1.50 | $8-15 | N/A | $15-50 | 2-5% |
| Professional Services / B2B | 0.5-1.2% | $2.00-5.00 | $15-35 | $30-100 | N/A | 1-3% |
| Restaurants / Food | 1.5-3.0% | $0.30-1.00 | $5-12 | $8-25 | $10-30 | 4-8% |

---

## Google Ads Benchmarks by Vertical (Search)

| Vertical | CTR | CPC (AUD) | CVR | CPA Lead (AUD) | Quality Score Avg |
|---|---|---|---|---|---|
| Wellness / Retreats | 3.5-6.0% | $1.50-4.00 | 3-7% | $25-70 | 5-7 |
| Fitness / Yoga | 3.0-5.5% | $1.00-3.00 | 4-8% | $15-50 | 5-7 |
| Education / Training | 3.0-5.0% | $2.00-5.00 | 3-6% | $30-80 | 5-6 |
| Real Estate / Architecture | 2.5-5.0% | $2.00-6.00 | 2-5% | $40-120 | 5-7 |
| Hospitality / Events | 4.0-7.0% | $1.00-3.00 | 4-8% | $20-50 | 6-7 |
| E-commerce (general) | 2.5-4.5% | $1.00-3.00 | 3-6% | N/A | 5-7 |
| Professional Services / B2B | 2.0-4.0% | $3.00-8.00 | 2-5% | $50-150 | 5-6 |
| Restaurants / Food | 4.0-8.0% | $0.50-2.00 | 5-10% | $10-30 | 6-8 |

---

## Benchmark Application Rules

1. **Match vertical first.** Use the closest vertical to the client's industry. If no match, use "Professional Services / B2B" as fallback.
2. **Ranges, not points.** Always compare against the range. "Below range" = concerning. "Within range" = normal. "Above range" = outperforming.
3. **Context matters.** A $210K architecture product naturally has higher CPA than a $50 yoga class. Price point adjusts expectations within the range.
4. **Currency.** All benchmarks in AUD. For SGD clients, multiply AUD by ~0.9 for rough conversion. For USD clients, divide AUD by ~1.5.
5. **Seasonal variation.** Benchmarks represent annual averages. Q4 (Nov-Dec) typically sees +20-40% CPM. Q1 (Jan-Feb) typically sees -10-20% CPM.

## Status Assignment

| Client Metric vs Benchmark Range | Status | Label |
|---|---|---|
| Better than top of range | 🟢 | Outperforming industry |
| Within range | 🟢 | At industry standard |
| Within 20% below bottom of range | 🟡 | Slightly below industry |
| >20% below bottom of range | 🔴 | Significantly below industry |
| No benchmark available | ⚪ | No benchmark data |

## Gaps to Fill (Perplexity Research)

- [ ] Australian-specific benchmarks (current data is global/US-heavy)
- [ ] Meta Ads ROAS benchmarks by vertical
- [ ] Google Display/Demand Gen benchmarks (current is Search only)
- [ ] Seasonal multipliers by vertical and country
- [ ] Video ad benchmarks (hook rate, hold rate by vertical)
- [ ] Frequency tolerance by vertical (wellness may tolerate higher frequency than B2B)
