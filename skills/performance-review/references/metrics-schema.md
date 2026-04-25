# Metrics Schema (What to Collect per Channel)

Canonical per-channel metric fields. Each post records one metrics object matching its channel's schema. Extra fields are ignored by the scorer. Missing required fields trigger a validation error.

## LinkedIn

| Field | Required | Notes |
|---|---|---|
| impressions | yes | Primary reach signal |
| reactions | yes | All reaction types (like, celebrate, support, etc.) summed |
| comments | yes | Count of unique comments (not replies to comments) |
| comments_meaningful | no | Comments > 15 words, if user tracks this |
| reshares | yes | Reposts (with or without commentary) |
| saves | yes | Bookmark count |
| clicks | no | Click-throughs to profile, link, or media |

**Weighted score formula:**
```
weighted_score = comments*15 + saves*10 + reshares*8 + reactions*1
engagement_rate = weighted_score / impressions * 100  (if impressions > 0)
```

Rationale: 2026 LinkedIn "Depth Score" model weights comments 15x vs likes (per post-writer/references/platform-specs.md). Saves nearly as weighted as comments. Reshares slightly less (less dwell).

## X (Twitter)

| Field | Required | Notes |
|---|---|---|
| impressions | yes | Post-level view count |
| replies | yes | Direct replies to this tweet (or first tweet for threads) |
| retweets | yes | Reposts (native RT) |
| quote_tweets | no | Quote-retweets with added commentary |
| likes | yes | |
| bookmarks | yes | If visible |
| link_clicks | no | If a link was in the tweet |

**Weighted score formula (single tweet or thread as a whole):**
```
weighted_score = replies*10 + retweets*8 + bookmarks*6 + (quote_tweets or 0)*7 + likes*1
```

Rationale: X's 2026 Phoenix update weights engagement velocity. Replies drive the first 30-min window most; retweets second; bookmarks signal long-tail value.

**For threads:** record metrics on tweet 1 only (thread virality lives off the first tweet). The rest are consequences.

## Instagram (feed)

| Field | Required | Notes |
|---|---|---|
| reach | yes | Unique accounts that saw the post |
| impressions | no | Total views (reach + re-views) |
| likes | yes | |
| comments | yes | |
| saves | yes | Primary Instagram ranking signal |
| shares | yes | DMs/reshares |
| profile_visits | no | |

**Weighted score:**
```
weighted_score = saves*15 + shares*10 + comments*5 + likes*1
engagement_rate = weighted_score / reach * 100
```

Rationale: Saves dominate IG ranking in 2026. Shares second. Likes are vanity.

## Instagram (Reel)

| Field | Required | Notes |
|---|---|---|
| plays | yes | Video play count |
| reach | yes | |
| likes | yes | |
| comments | yes | |
| saves | yes | |
| shares | yes | |
| avg_watch_time_sec | no | Retention signal; critical for long-form Reels |
| completion_rate | no | |

**Weighted score:**
```
weighted_score = saves*15 + shares*10 + comments*5 + likes*1 + (completion_rate or 0)*20
```

Higher weight on saves + shares than feed posts; completion_rate is a Reel-specific amplifier.

## Instagram (Story)

| Field | Required | Notes |
|---|---|---|
| views | yes | |
| exits | no | Early skip signal |
| replies | no | DMs from the story |
| taps_forward | no | |
| taps_back | no | Re-read signal (interesting!) |

**Weighted score:**
```
weighted_score = replies*20 + taps_back*5 + views*1 - exits*2
```

Stories are BTS warm-audience content; DMs = real intent.

## Facebook

| Field | Required | Notes |
|---|---|---|
| reach | yes | |
| reactions | yes | |
| comments | yes | |
| shares | yes | |
| clicks | no | |

**Weighted score:**
```
weighted_score = shares*10 + comments*8 + reactions*1
```

FB is low-priority in Phase 1 for Digischola; simple scoring.

## WhatsApp Status

| Field | Required | Notes |
|---|---|---|
| views | yes | Seen-count |
| replies | no | Direct message replies to the status |

**Weighted score:**
```
weighted_score = replies*20 + views*1
```

WA Status is warm-audience; replies are very high-signal.

## WhatsApp Channel

| Field | Required | Notes |
|---|---|---|
| views | yes | |
| reactions | yes | Native reactions |
| forwards | yes | Primary amplification signal |

**Weighted score:**
```
weighted_score = forwards*15 + reactions*3 + views*1
```

## Universal required context (for every record)

In addition to channel-specific metrics, every record captures context needed for pattern analysis:

- `post_file` — path to the queue draft file
- `entry_id` — source idea-bank entry id (from frontmatter)
- `channel` — normalized channel name
- `format` — text-post | thread | carousel | reel | etc.
- `hook_category` — from post-writer frontmatter (Data, Counterintuitive, Story, etc.)
- `voice_framework` — from post-writer frontmatter
- `pillar` — from post-writer frontmatter
- `repurpose_source` — from frontmatter if this post was a repurpose variant; null otherwise
- `published_at` — when the post went live (user-provided; defaults to recording timestamp if unknown)
- `recorded_at` — when the performance record was added
- `weighted_score` — computed from channel's weighted formula

This combination enables pattern analysis: "Hook Category X on Channel Y with Voice Framework Z produced weighted scores above median N% of the time."
