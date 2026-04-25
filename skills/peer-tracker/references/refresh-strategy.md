# Refresh Strategy (Mode 1 — Autonomous WebSearch)

How Claude refreshes one creator per Sunday Step 2 invocation.

## Per-creator scan loop

For each creator in this Sunday's rotation (from `peer_tracker.py rotation-due`):

### Step 1 — Existing entry context

Read the creator's section in `post-writer/references/creator-study.md`:
- Current "Reach"
- Current "Signature format"
- Current "Mimicry approach"
- Last refreshed timestamp (if any)

This gives Claude the baseline to compare new findings against.

### Step 2 — WebSearch (1-2 queries per creator)

Use the templates in `references/tracked-creators.md`. Examples:

```
WebSearch query 1: "Peep Laja" LinkedIn 2026 best post
WebSearch query 2: site:linkedin.com peeplaja 2026
```

For X-primary creators, query both x.com and twitter.com:
```
WebSearch query 1: "Julian Shapiro" thread 2026
WebSearch query 2: site:x.com julian 2026 growth
```

For newsletter creators (Harry Dry):
```
WebSearch query 1: site:marketingexamples.com 2026
WebSearch query 2: "Harry Dry" 2026 example
```

### Step 3 — Extract signal from snippets

For each top result:
- Date check: is it within last 30 days? (Skip if older.)
- Engagement signal: does the snippet mention "1.2K reactions", "viral", "trending"? (Soft heuristic — snippets sometimes show this.)
- Hook pattern: read the post text in the snippet — does it match the existing "Signature format" or is it a new pattern?
- Topic check: is the post on-pillar?

Synthesize 3 things per creator:
1. **Top recent posts** (3 strongest from last 30 days, by engagement signal or content quality)
2. **Hook pattern delta** — new pattern observed, or "consistent with existing"
3. **Status flag** — `active` (default), `silent` (no posts last 30d), `pivoted` (posts off-pillar)

### Step 4 — Build update payload

```json
{
  "creator": "Peep Laja",
  "refreshed_at": "2026-04-20T09:30:00+05:30",
  "status": "active",
  "reach_update": null,
  "recent_posts": [
    {
      "date": "2026-04-12",
      "url": "https://linkedin.com/posts/peeplaja-...",
      "summary": "Brutal-truth post on enterprise CRO budget allocation. ~1.5K reactions.",
      "hook_pattern": "Brutal Truth Text Post"
    },
    {
      "date": "2026-04-08",
      "url": "https://linkedin.com/posts/...",
      "summary": "Contrast statement on SaaS landing page hero copy. ~800 reactions.",
      "hook_pattern": "Brutal Truth Text Post"
    },
    {
      "date": "2026-04-02",
      "url": "https://linkedin.com/posts/...",
      "summary": "Carousel: 5 questions to ask before redesigning a landing page.",
      "hook_pattern": "NEW: Question-Stack Carousel"
    }
  ],
  "hook_pattern_delta": "Adding Question-Stack Carousel as a secondary pattern alongside Brutal Truth Text Post. Carousel format new for him.",
  "topic_drift": null,
  "notes": "Reach appears stable around 100-150K range. No pivot."
}
```

Submit via:
```bash
python3 scripts/peer_tracker.py apply-refresh --creator "Peep Laja" --findings '<json>'
```

### Step 5 — Edge cases

**Silent creator** (no posts in last 30 days):
```json
{
  "creator": "...",
  "refreshed_at": "...",
  "status": "silent",
  "recent_posts": [],
  "hook_pattern_delta": null,
  "topic_drift": null,
  "notes": "0 posts found in last 30 days. May be on break or paused."
}
```

If a creator stays silent for 60+ days → flag for Mayank to consider dropping.

**Pivoted creator** (posts are off-pillar):
```json
{
  "creator": "...",
  "refreshed_at": "...",
  "status": "pivoted",
  "recent_posts": [...],  // still log what they ARE posting
  "hook_pattern_delta": null,
  "topic_drift": "Shifted from CRO to general business advice + AI commentary",
  "notes": "Off-pillar pivot. Recommend Mayank consider dropping or moving to a different pillar."
}
```

Do NOT auto-drop. Mayank decides.

## What Claude updates in creator-study.md

After `apply-refresh`, the script updates these subsections in the creator's entry:

```markdown
### Peep Laja
- **Handles:** LinkedIn @peeplaja, X @peeplaja
- **Reach:** 100-150K  ← updated if reach_update provided
- **Niche:** B2B messaging strategy, harsh truths about CRO
- **Signature format:** The Brutal Truth Text Post + Question-Stack Carousel  ← merges hook_pattern_delta
- **Mimicry approach for Mayank:** Use contrast statements to dismantle SMB-level ad advice...
- **Last refreshed:** 2026-04-20 (active, 3 posts last 30d)  ← NEW SUBSECTION peer-tracker maintains
- **Recent samples:**  ← NEW SUBSECTION peer-tracker maintains
  - 2026-04-12: Brutal-truth on enterprise CRO budget. [link]
  - 2026-04-08: Contrast on SaaS hero copy. [link]
  - 2026-04-02: Carousel: 5 questions before LP redesign. [link]
```

The script preserves all other content (Mayank's manual edits to "Mimicry approach", etc.) — only the "Last refreshed" + "Recent samples" subsections (and "Signature format" if hook_pattern_delta is non-null) get touched.

## Throughput

Mode 1 with 4 creators per Sunday: ~10-15 min total. Each creator:
- 2 WebSearches: 5-10 sec each (10-20 sec total per creator)
- Snippet parsing + synthesis: 1-2 min
- apply-refresh script: instant

Mode 2 (Chrome MCP scrape) per creator: 5-8 min — only use when Mayank specifically asks for deep refresh.
