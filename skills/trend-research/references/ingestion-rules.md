# Ingestion Rules — dedup, quality filter, idea-bank schema

Rules for adding trend candidates to `brand/idea-bank.json` without polluting it.

## Idea-bank schema (matches work-capture)

Each entry in `idea-bank.json` "entries" array:

```json
{
  "type": "trend",
  "pillar": "lp-craft" | "solo-ops" | "paid-media" | "cross-pillar",
  "seed": "1-2 sentence factual summary of the trend",
  "raw_note": "<copy of seed for backwards compat with content-calendar parser>",
  "hook_candidate": "1 line in Mayank's voice as a possible post hook",
  "suggested_pillar": "Landing-Page Conversion Craft" | "Solo Freelance Ops" | "Small-Budget Paid Media",
  "channel_fit": ["LinkedIn", "X", "Instagram", "Facebook"],
  "format_candidates": ["LI-post", "X-thread", "IG-carousel"],
  "source_urls": ["https://...", "https://..."],
  "tags": ["wellness", "case-study", "mobile-first"],
  "relevance_score": 4,
  "via": "trend-research",
  "captured_at": "2026-04-20T09:15:00+05:30",
  "status": "raw",
  "manual_review_needed": false,
  "notes": "Optional Claude commentary on quality, fit, or caveats"
}
```

`raw_note` mirrors `seed` so existing content-calendar code that reads `raw_note` keeps working. New consumers should prefer `seed`.

## Dedup logic

Before appending a candidate, check against ALL existing entries (any type, not just `trend`):

1. **Exact-text match** on `seed` / `raw_note` / `hook_candidate` → SKIP (this is a re-run of the same trend)
2. **Fuzzy match** ≥70% token overlap on the same fields → SKIP and log as "duplicate of <existing entry_id>"
3. **URL overlap** on `source_urls` → if all proposed URLs are already in some existing entry's source_urls → SKIP
4. **Same-pillar 30-day cap** → if there are already 8+ trend entries for this pillar in the last 30 days, SKIP unless relevance_score is 5

The 70% threshold is generous to avoid false positives (different angles on same broader topic should both be kept). Adjust to 80% if dedup is too aggressive.

## Quality filter (auto-reject)

Drop a candidate before ingestion if ANY of these are true:

1. `relevance_score` < 3
2. `seed` or `hook_candidate` contains an em dash (`—` or `--`)
3. `seed` or `hook_candidate` contains hype words from voice-guide: `unlock`, `revolutionize`, `game-changer`, `massive`, `explode`, `crush`, `10x`, `effortless`
4. `source_urls` is empty OR all paywalled (paywalled domains: nytimes.com, ft.com, hbr.org, wsj.com — extend list as needed)
5. `pillar` doesn't match one of the 3 valid slugs
6. `hook_candidate` is verbatim from a source (must be Mayank's voice rephrasing, not plagiarism)

## Manual-review flag

Set `manual_review_needed: true` (DON'T auto-skip) if:

- `relevance_score` is exactly 3 (borderline)
- `source_urls` includes a domain Claude doesn't recognize as authoritative
- `seed` includes a strong claim with weak source ("Study shows X" but the source URL doesn't actually state X)
- The trend appears to be a paid promotion / sponsored post

content-calendar / post-writer can filter on `manual_review_needed: true` and skip those entries until Mayank manually flips them to `false`.

## Pillar slug normalization

The script accepts both human-readable + slug forms:

| Slug | Human |
|---|---|
| `lp-craft` | "Landing-Page Conversion Craft" |
| `solo-ops` | "Solo Freelance Ops" |
| `paid-media` | "Small-Budget Paid Media" |
| `cross-pillar` | (used when 2+ pillars apply) |

Both `pillar` (slug) and `suggested_pillar` (human) get written for backwards compatibility.

## Append safety

Before writing to idea-bank.json:

1. Read the current file
2. Verify it parses (don't corrupt existing data on a malformed read)
3. Append to `entries` array
4. Write atomically (write to temp file, then rename — prevents partial-write corruption)
5. If write fails, restore from the original

## Logging

Per-week scan log at `brand/_research/trends/<week>/scan-log.md`:

```markdown
# Trend Scan — 2026-W17

Mode: autonomous (WebSearch)
Run at: 2026-04-20T09:00:00+05:30

## LP Craft
- Added 3 / Skipped 2
  - Added: "Phone above fold +41% wellness LPs" (score 5, 2 URLs)
  - Added: "Forms 2 fields beats 6 by 2.3x conversion" (score 4, 1 URL)
  - Added: "Page speed under 2.5s = +18% mobile conversion" (score 4, 3 URLs)
  - Skipped: "10 landing page tips" (relevance 2, generic listicle)
  - Skipped: "Hero copy testing 2026" (duplicate of entry from 2026-W14)

## Solo Ops
- ...

## Paid Media
- ...

## Total
- Scanned: 18 candidates
- Added: 9
- Skipped: 9 (4 duplicates, 3 quality, 2 wrong-pillar)
```
