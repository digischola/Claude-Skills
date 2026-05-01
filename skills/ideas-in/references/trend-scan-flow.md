# trend-scan-flow

Detailed steps for `ideas-in trend-scan`. Loaded only when scanning trends.

## Pillar query templates

Each pillar has a 4-query battery. Run all four per pillar; merge + dedupe results.

### Pillar 1: Landing-Page Conversion Craft

1. `landing page conversion rate optimization 2026 case study`
2. `wellness retreat landing page benchmarks conversion`
3. `lead gen form length conversion impact 2026`
4. `LP hero headline test results conversion lift`

### Pillar 2: Solo Freelance Ops

1. `solo marketing freelancer ops stack 2026`
2. `AI workflow freelance digital marketer time saving`
3. `freelance marketing pricing client retention 2026`
4. `solo agency vs freelancer outcome comparison`

### Pillar 3: Small-Budget Paid Media

1. `small budget Meta ads ROAS 2026 benchmarks`
2. `Google Ads under $500 monthly performance`
3. `low budget paid media wellness brands case study`
4. `Meta Ads creative testing low budget framework`

## Relevance scoring rubric (0-10)

| Score | Meaning |
|---|---|
| 9-10 | Direct match for pillar definition + concrete data point we can quote |
| 7-8 | Direct match, no data — opinion / framework worth riffing on |
| 5-6 | Tangential match, keep only if pillar is gap-flagged this week |
| <5 | Drop |

Apply `accuracy-protocol`: if relevance is borderline, drop it. Better fewer good entries than noise.

## Dedup logic

Script handles dedup automatically against existing idea-bank entries:

- Exact URL match → skip
- Title >70% Levenshtein similarity to existing trend headline → skip
- Same `pillar` + same `tags` set captured within 14 days → skip

## Output entry shape

```json
{
  "id": "<uuid>",
  "type": "trend",
  "captured_at": "<iso8601>",
  "raw_note": "<headline + 1-line summary>",
  "source_url": "<url>",
  "pillar": "<pillar name>",
  "relevance_score": 8,
  "channel_fit": ["LinkedIn", "X"],
  "format_candidates": ["LI-post", "X-thread"],
  "tags": ["trend", "<pillar-slug>"],
  "status": "raw"
}
```

## Cron context

Triggered by `weekly-ritual` Wednesday 09:00 IST as part of the planning chain. The ritual fires a notification + clipboard prompt; user pastes into Claude Code; Claude runs WebSearch per pillar and pipes results to `scripts/scan_trends.py --append`.

## Anti-patterns

- Do NOT run trend-scan more than once per week per pillar — leads to noise.
- Do NOT keep trend entries with no source URL.
- Do NOT promote a trend to draft directly. Trends sit in the bank for `draft-week` to pick from.
