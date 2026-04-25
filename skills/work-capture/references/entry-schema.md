# Idea-Bank Entry Schema

Every entry in `idea-bank.json` conforms to this schema. `scripts/append_to_idea_bank.py` enforces it.

## Schema

```json
{
  "id": "uuid (auto-assigned)",
  "captured_at": "ISO timestamp (auto-assigned)",
  "type": "one of: client-win | insight | experiment | failure | build-log | client-comm | observation",
  "raw_note": "user's raw input — preserve specifics (numbers, tools, client names, timestamps)",
  "suggested_pillar": "pillar ID from brand/pillars.md",
  "channel_fit": ["LinkedIn", "Instagram", "X", "Facebook", "WA-Status", "WA-Channel"],
  "format_candidates": ["LI-post", "LI-carousel", "IG-carousel", "IG-reel", "X-tweet", "X-thread", "WA-status", "WA-channel-post", "FB-post"],
  "tags": ["freeform strings — client name, tool, vertical, topic"],
  "status": "one of: raw | shaped | drafted | scheduled | posted | killed"
}
```

## Type definitions

| Type | Meaning | Example raw_note |
|------|---------|------------------|
| client-win | Concrete delivered result with a metric | "Thrive Aug: +28% Meta ROAS after switching to ASC + simplified LP. Attribution window: 7d click." |
| insight | Pattern that generalizes beyond one client | "Every LP I've audited this month that had a phone number above the fold converted 2x the form-only version. Small sample, strong directional signal." |
| experiment | Something tested, result ambiguous | "Tested tight geo (5km) vs. metro-wide for Samir's. Tight won on CTR; metro won on volume. Still unclear on CVR." |
| failure | Honest loss or mistake | "Ran a Ratha Yatra campaign with wrong date in the LP hero. Athil caught it before me. 2 days of spend wasted." |
| build-log | Skill / tool / system progress | "Added Chrome MCP fallback to personal-brand-dna Step 3. Lovable sites now render fully." |
| client-comm | Communication craft moment | "Athil asked why Ashfield is lagging. I framed it as LP friction, not ad failure, proposed a $10/day test. He agreed in 3 msgs." |
| observation | Industry / work pattern worth riffing | "Noticed 4 of 5 wellness retreats I've audited this year use a hero video that autoplays muted. None convert as well as a static image + 'book call' CTA." |

## Pillar assignment rules

`suggested_pillar` must match an approved pillar ID from `brand/pillars.md`. If uncertain:
- Use `uncertain` as the value and set `status: raw`
- The skill will flag for user review on next surface

## Channel fit heuristics

| Type | Natural channels |
|------|------------------|
| client-win | LinkedIn, IG-carousel, X-thread, WA-Status |
| insight | LinkedIn, X-tweet |
| experiment | LinkedIn, X-thread |
| failure | LinkedIn (high engagement on vulnerability), X |
| build-log | LinkedIn, X, IG-reel, WA-Status |
| client-comm | LinkedIn, X-thread |
| observation | X-tweet, LinkedIn (if expanded) |

Skill can override these based on voice-guide register and current brand phase.

## Format heuristics

| Entry context | Best format |
|---------------|-------------|
| Has 1 strong stat | X-tweet + LI-post |
| Has 3-5 parallel items | LI-carousel or IG-carousel |
| Visual before/after | IG-carousel (with Remotion-rendered slides) |
| 60-second story | IG-reel or X-thread |
| Quick real-time observation | WA-status or X-tweet |
| Longer teaching arc | LI-post |

## Status lifecycle

- `raw` — just captured, not yet shaped for a specific post
- `shaped` — refined; pillar/channel/format confirmed by user
- `drafted` — `post-writer` has produced a draft
- `scheduled` — in `scheduler-publisher` queue
- `posted` — live on channel
- `killed` — deliberately shelved (not deleted — kept for pattern analysis)

## What NOT to capture

- Purely personal moments unrelated to work
- Client information that isn't already public on digischola.in
- Generic statements ("AI is changing marketing") without specifics
- Duplicate entries (check idea-bank.json for similar raw_notes from last 7 days)
