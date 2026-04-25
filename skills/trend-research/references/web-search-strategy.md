# Web Search Strategy (Mode 1 — Autonomous)

How Claude conducts the weekly trend scan when invoked autonomously (default flow used by weekly-ritual Sunday Step 1).

## Per-pillar search loop

For each of the 3 pillars, do **2 WebSearches**: one for industry trends, one for creator activity.

### Search 1 — industry trends (per pillar)

Pick 1-2 seed queries from `references/pillar-niches.md` (rotate weekly so we don't search the same query every week).

Example for LP Craft (week N):
```
WebSearch query: "landing page conversion rate 2026 case study"
Date filter: last 14 days (or "this week")
```

Look for:
- Recent case studies with metrics (e.g., "+47% conversion after X change")
- Contrarian takes vs. conventional CRO wisdom
- New tools / tactics that the community is discussing
- Benchmarks updates from industry reports

### Search 2 — creator activity (per pillar)

Search for the tracked authors' recent posts:
```
WebSearch query: "Peep Laja LinkedIn post 2026" OR "site:linkedin.com Peep Laja"
```

Or for a topic-creator combo:
```
WebSearch query: "Harry Dry marketing examples landing page 2026"
```

Look for:
- Top-performing posts (high engagement signals in the snippet)
- Threads / carousels with strong frameworks
- Quote-worthy lines

## Synthesis rules

After running both searches per pillar (6 searches total across 3 pillars):

1. Group findings by pillar
2. Per pillar, surface 3-6 candidates (not more — quality over quantity)
3. Each candidate has:
   - `seed`: 1-2 sentence factual summary
   - `hook_candidate`: a Mayank-voice hook line draft (NOT the source author's words)
   - `source_urls`: 1-3 URLs from search results
   - `tags`: 2-4 relevant tags
   - `relevance_score`: 1-5 (see below)
   - `pillar`: the matching pillar slug (lp-craft, solo-ops, paid-media)
   - `type: trend`
   - `via: trend-research`
   - `status: raw`

## Relevance scoring rubric

| Score | Meaning |
|---|---|
| 5 | Strong fit — exact pillar topic, has metrics, contrarian or fresh angle, Mayank's voice fits naturally |
| 4 | Good fit — solid pillar match, has either metrics OR fresh angle, easily adapted |
| 3 | OK fit — pillar-relevant but generic OR niche-specific in a way Mayank's ICPs may not care about |
| 2 | Weak fit — adjacent to pillar but stretchy; would require manual editorial work |
| 1 | Wrong pillar — skip entirely |

Quality filter drops anything <3. Borderline 3s get flagged `manual-review: true` so Mayank can decide.

## Anti-patterns

- Do NOT use WebSearch for queries that aren't tied to a specific seed in pillar-niches.md (results get noisy)
- Do NOT include trends that are >30 days old (content-calendar wants fresh)
- Do NOT include URLs from the topic blacklist sources in pillar-niches.md
- Do NOT generate >6 candidates per pillar per week (idea-bank gets cluttered)

## Example output (one candidate)

```json
{
  "type": "trend",
  "pillar": "lp-craft",
  "seed": "A 2026 GoodUI study on 200 wellness landing pages found pages with phone-number-above-fold convert 41% higher than pages with phone tucked in the footer. Effect strongest for retreats and yoga studios.",
  "hook_candidate": "41% conversion lift from one decision: phone number above the fold. We tested it on a wellness retreat client. Numbers matched.",
  "source_urls": [
    "https://goodui.org/wellness-lp-study-2026",
    "https://www.linkedin.com/posts/peep-laja_phone-above-fold-wellness"
  ],
  "tags": ["wellness", "form-design", "case-study", "mobile-first"],
  "relevance_score": 5,
  "via": "trend-research",
  "captured_at": "2026-04-20T09:15:00+05:30",
  "status": "raw"
}
```

## After synthesis

Pass each candidate through `scripts/trend_research.py dedupe-check` then `ingest`. Both calls are idempotent — safe to re-run.

Final report: log per-pillar count + skipped (with reason) to `brand/_research/trends/<week>/scan-log.md`.
