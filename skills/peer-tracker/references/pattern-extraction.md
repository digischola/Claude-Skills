# Pattern Extraction — what to look for in WebSearch snippets

How Claude turns search snippets into structured findings about each creator.

## Hook pattern types (catalog)

When parsing a recent post, classify its hook pattern. This vocabulary aligns with `post-writer/references/hook-library.md` so peer-tracker findings feed cleanly back.

### Recognized hook patterns

| Pattern | Snippet signature |
|---|---|
| **Brutal Truth Text Post** | "Most X are Y. The few who Z..." or "Stop doing X. Start doing Y." |
| **Contrast Statement** | "Amateurs X. Professionals Y." pattern |
| **Tear-Down Carousel** | Visual deconstruction; snippet mentions "carousel" or "swipe" + "before / after" |
| **Before/After Visual** | Side-by-side comparison; snippet typically image-led |
| **Framework Breakdown** | "The N-step framework for X" or named acronyms (PAS, AIDA) |
| **Deep-Dive Thread** | Multi-tweet textbook-style; snippet mentions "thread" or "1/N" |
| **Client Story** | Personal anecdote about a client; "I worked with X" or "A client of mine" |
| **AI Workflow Demo** | Shows AI doing a task; mentions "Claude", "Cursor", "automation" |
| **Numbers Hero** | Big number opener; "+188%", "$10K", "47%" as the first chars |
| **Question Stack** | Opens with 3-5 questions; "Are you X? Did you Y?" |
| **Receipts Drop** | Screenshot of result + 1-2 line context |
| **Contrarian Take** | "Everyone says X. Here's what they're missing." |
| **Confession** | "I used to X, here's what I learned" — vulnerability |

When you spot a pattern that doesn't fit any of these → mark as `NEW: <descriptive name>`. peer-tracker logs this so Mayank can decide whether to add it to `post-writer/references/hook-library.md` (manual decision; not auto-added).

## Topic drift detection

A creator is "on-pillar" if their recent posts match the pillar they were tracked for. Use these heuristics:

### Pillar 1 — LP Craft on-pillar signal words

`landing page`, `conversion`, `CRO`, `hero`, `CTA`, `form`, `above the fold`, `funnel`, `optimization`, `A/B test`, `messaging`, `headline`

### Pillar 2 — Solo Ops on-pillar signal words

`freelance`, `solo`, `agency`, `1-person`, `productized`, `client`, `pricing`, `retainer`, `ops`, `stack`, `tool`, `Claude`, `AI workflow`, `Upwork`

### Pillar 3 — Paid Media on-pillar signal words

`Meta ads`, `Facebook ads`, `Google ads`, `PPC`, `creative`, `budget`, `CPA`, `ROAS`, `audience`, `targeting`, `campaign`, `attribution`, `retargeting`

If <50% of recent posts contain ANY pillar signal words → mark `status: pivoted` and add a note describing what they ARE posting about.

## Engagement signal extraction

WebSearch snippets sometimes show engagement metrics like "1.2K reactions", "127 comments", "shared 89 times". Extract these conservatively:

- Look for: `\d+(K|M)?\s*(reactions|likes|comments|shares|reposts|reshares|bookmarks)`
- Treat as approximate (snippets may show stale metrics from when search-engine cached the page)
- Use to RANK posts (higher engagement → more likely to be a "top recent post"), NOT as absolute truth

If snippet has no metrics: rank by recency + content quality (prefer specific case-study-ish posts over generic advice).

## Reach update detection

Snippets occasionally show updated follower / connection counts:
- `123K followers`
- `4500 connections`
- `views: 50K`

If the new count differs from existing creator-study.md "Reach" by >25%, propose an update via `reach_update: "100-150K → 130-180K"`.

If no signal: leave `reach_update: null` (script keeps existing value).

## Recent post quality filter

Skip posts that:
- Are sponsored / paid (snippet contains "Sponsored" or "Promoted")
- Are reposts of someone else's content
- Are off-pillar (per topic-drift signal words)
- Are >30 days old (recency cap)
- Are job postings
- Are pure event announcements ("Join my webinar...") with no insight

A "good" recent post:
- On-pillar
- Within last 30 days
- Has identifiable hook pattern
- Has shareable insight, framework, or contrarian take

## Output validation

Before returning the findings JSON for `apply-refresh`:

1. `recent_posts` array has 0-3 entries (NOT more — preserve scannability of creator-study.md)
2. Each post has at minimum: `date`, `url`, `summary`. (`hook_pattern` is recommended.)
3. `summary` is ≤120 chars (snappy)
4. `status` is one of `active` | `silent` | `pivoted`
5. `hook_pattern_delta` is null OR a string describing the change
6. `notes` is ≤200 chars

If `apply-refresh` rejects the payload (validation fail), re-synthesize with corrected fields.
