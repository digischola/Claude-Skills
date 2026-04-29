# Monday Review Flow

Step-by-step for "run monday review" (primary), "monday review", or legacy "run friday review" trigger. Cron fires Monday 18:00 IST. Internal state key is still `last_fired_friday` (kept as a neutral legacy label — see SKILL.md Learnings 2026-04-24).

## Pre-checks

1. `performance-review` skill exists (it does)
2. At least 1 post in `brand/queue/published/` with `posted_at` in the last 7 days
   - If 0 posts, BLOCK with: "No posts published in the last 7 days. Either no scheduling happened or scheduler-publisher hasn't fired yet. Skipping Friday review."
3. `last_fired_friday` in state >12h ago (idempotency)

## Step 1 — Identify posts to record

List all `.md` files in `brand/queue/published/` whose `posted_at` is within the last 7 days. For each, extract:
- `entry_id`
- `channel`
- `format`
- `pillar`
- `platform_url`
- `posted_at`

Group by channel for efficient metric collection.

## Step 2 — Pull metrics from Windsor.ai (automatic, replaces manual entry)

Changed 2026-04-22: user flagged manual CSV paste as unsustainable. Windsor.ai has the relevant 4 connectors already authenticated for Digischola (`linkedin_organic`, `x_organic`, `facebook_organic`, `instagram`). Performance-review now pulls post-level metrics directly — zero manual prompting of Mayank.

**2a. Build the pull plan** (Python-side, deterministic):

```bash
python3 "Desktop/Claude Skills/skills/performance-review/scripts/pull_performance_windsor.py" \
  plan --days 7 \
  --output /tmp/windsor-plan.json
```

Output: a JSON file describing one "job" per channel that has published posts in the last 7 days, with connector ID, account IDs, fields to pull, date range, and the list of drafts each job should attribute.

**2b. Execute each job via Windsor MCP** (Claude-side):

Read `/tmp/windsor-plan.json`. For each `job`:
1. Call the Windsor MCP `get_data` tool:
   ```
   connector: job.connector
   accounts: job.accounts
   fields: job.fields
   date_from: job.date_from
   date_to: job.date_to
   ```
2. Capture the `result` array. Store all results keyed by `job.channel` into a single dict:
   ```json
   {
     "linkedin": {"result": [...]},
     "x": {"result": [...]},
     "facebook": {"result": [...]},
     "instagram": {"result": [...]}
   }
   ```
3. Write the combined dict to `/tmp/windsor-results.json`.

**2c. Merge results into log.json** (Python-side, deterministic):

```bash
python3 "Desktop/Claude Skills/skills/performance-review/scripts/pull_performance_windsor.py" \
  merge \
  --plan /tmp/windsor-plan.json \
  --results /tmp/windsor-results.json
```

This matches each Windsor row → one of the drafts (by `posted_url` primarily, by timestamp nearest-neighbor fallback), computes the weighted score via the canonical scorer, and appends to `brand/performance/log.json`. Also stamps a compact `performance: {weighted_score, impressions, recorded_at}` summary on each draft's frontmatter.

Per `shared-context` and the Jon Loomer 2026-03-19 warning about Meta ad-account shutdowns on AI-agent API traffic: **this pull is READ-ONLY**. Never issue write operations to Meta via Claude or any MCP. If Meta's Graph API tightens and Digischola's page/IG gets a warning, disconnect the relevant Windsor connector and fall back to Step 2-FALLBACK below.

**2-FALLBACK. Manual record_performance.py** (only if Windsor is down):

For each post, prompt Mayank:

> Post: 4e4eed15 · LinkedIn · text-post · "188% more Meta sales..." · posted 2026-04-22T09:00 IST
> URL: https://www.linkedin.com/feed/update/urn:li:activity:xxxxx
>
> Open the post in native analytics, paste metrics as JSON:

```bash
python3 "Desktop/Claude Skills/skills/performance-review/scripts/record_performance.py" \
  <post.md> --metrics '{"impressions": 1200, "reactions": 45, "comments": 12, "reshares": 6, "saves": 18}'
```

This path stays supported forever as a backstop. Use if `pull_performance_windsor.py merge` reports unmatched rows or Windsor returns empty results unexpectedly.

## Step 3 — Run the weekly review

```bash
python3 "Desktop/Claude Skills/skills/performance-review/scripts/weekly_review.py" --week 2026-WXX
```

This:
1. Computes per-post weighted scores per channel
2. Compares against rolling 30-day baselines
3. Buckets each post: HIT (top 10%) / ABOVE (top 25%) / BELOW (bottom 25%) / FLOP (bottom 10%)
4. Aggregates pattern-level scores: hook category, voice framework, pillar, transformation recipe, calendar slot
5. Writes report to `brand/performance/2026-WXX.md`

## Step 4 — Surface promotion suggestions

If we're past the active-mature threshold (56+ days of data), the report will contain P1/P2/P3 suggestions:
- **P1**: Promote winning hook patterns to "Tier 1" in `post-writer/references/hook-library.md`
- **P2**: Update voice-framework rotation rules
- **P3**: Adjust calendar slot timing

Surface these to Mayank. He decides which to apply. v1 is ADVISORY — do NOT auto-apply.

If we're still in collecting (0-20 days) or active-early (21-55 days), report shows raw numbers + buckets but no suggestions. That's expected; just show Mayank the numbers.

## Step 5 — Update state

Write to `brand/_engine/weekly-ritual.state.json`:
```json
{
  "last_fired_friday": "2026-04-24T18:00:00+05:30",
  "last_completed_friday": "2026-04-24T18:18:42+05:30",
  "last_review_week": "2026-W17",
  "posts_reviewed": 6,
  "buckets": {"HIT": 1, "ABOVE": 2, "BELOW": 2, "FLOP": 1}
}
```

## Step 6 — Suggest next-Sunday planning constraints

Based on this week's results, surface 1-3 constraints to remember for next Sunday's calendar:
- "Hook category 'Data' had 2 HITs — bias next week's calendar toward Data hooks"
- "Friday slot underperformed both weeks — consider moving to Saturday"
- "X-thread-from-LI repurpose got 3x baseline — increase repurpose cadence"

These get noted in the Friday review report. content-calendar's gap-detection will pick them up next Sunday.

## Manual user steps after Friday review

1. Open `brand/performance/2026-WXX.md` and read the report
2. Decide which P1/P2/P3 suggestions to apply (if any)
3. Manually edit `post-writer/references/hook-library.md` etc. if applying suggestions
4. Optionally: capture insights to idea-bank as new content ideas

If no posts had metrics recorded, the Friday flow still runs but with sparse data. The report will note this and recommend recording metrics earlier in the week.
