# Feedback Loop — Post-Launch Optimization

Run this at the end of every optimization session.

## Output Quality Checklist

### Data Integrity
- [ ] All Windsor.ai queries returned data (no silent failures)
- [ ] Conversion event matches client config (not using wrong action field)
- [ ] Date ranges are correct (30d primary, 14d daily trend)
- [ ] Currency is consistent throughout (AUD, USD, SGD — not mixed)
- [ ] Derived metrics calculated correctly (CPA = spend/conversions, ROAS = value/spend)

### Analysis Quality
- [ ] All 11 layers executed (or intentionally skipped with reason)
- [ ] Health status applied consistently (green/amber/red thresholds respected)
- [ ] Kill/scale/test recommendations have data backing (not opinions)
- [ ] Minimum data thresholds respected (no analyzing segments with <$20 spend)
- [ ] First-run behavior followed if applicable (baseline, no prescriptions)

### Output Quality
- [ ] Executive summary is ≤5 lines
- [ ] Top actions are prioritized with impact × confidence × ease scores
- [ ] Every finding has a source label ([DATA], [CALCULATED], [BENCHMARK], [INFERRED])
- [ ] Report saved to correct client folder
- [ ] Dashboard renders correctly (if generated)
- [ ] Wiki log updated
- [ ] Client config updated (baselines, analysis history)

### Session Memory
- [ ] Previous report read and compared (if exists)
- [ ] Recommendation follow-up tracked
- [ ] Baseline shift noted if significant

## Process Quality Checklist

- [ ] Windsor.ai MCP connected and responding
- [ ] Queries ran without timeout issues
- [ ] No data discrepancies flagged (Windsor vs expected)
- [ ] Client was asked about any ambiguous findings before making recommendations
- [ ] Report generated before dashboard (report drives dashboard content)

## Learning Entry Format

```
[DATE] [CLIENT NAME] Finding: {what was observed}. → Action: {what was done or should be done next time}.
```

## Quality Benchmarks (update after 5+ analyses)

| Metric | Target | Current |
|---|---|---|
| Queries successful | 100% | TBD |
| Layers completed | 11/11 | TBD |
| False positive rate (bad recommendations) | <10% | TBD |
| Client action rate (did they implement?) | >60% | TBD |
| Time to generate report | <10 min | TBD |
