# Windsor.ai Field Map

How each Digischola channel's post-level metrics map to Windsor connector fields. Reference for `pull_performance_windsor.py`.

**Built 2026-04-22** after surfacing that manual CSV paste is unsustainable. All 4 channels are already connected on the user's Windsor account (`digischola@gmail.com`):

| Channel | Windsor connector | Account ID | Account name |
|---|---|---|---|
| LinkedIn | `linkedin_organic` | `108990232` | DigiSchola |
| X | `x_organic` | `Digischola Scheduler` | Digischola Scheduler |
| Facebook Page | `facebook_organic` | `1029294316942000` | Digischola |
| Instagram | `instagram` | `17841404814439751` | DigiSchola (digischola) |

The connector ID + account ID mapping lives in `scripts/pull_performance_windsor.py` as `CONNECTOR_REGISTRY`. If any account re-authenticates and gets a new ID, update the registry there (not here — keep code-authoritative).

## Safety rule (from Loomer article)

The Meta connectors (`facebook_organic`, `instagram`, and the client-side `facebook` ads connector) inherit the risk described in Jon Loomer's 2026-03-19 article ["AI-Related Ad Account Shutdowns"](https://www.jonloomer.com/ai-related-ad-account-shutdowns/). Meta flags third-party-tool API traffic as automated abuse and has been shutting down accounts. Rule:

- **All Windsor use from Claude is READ-ONLY.** Never call a write-endpoint on any Meta surface via Claude or any MCP.
- **Ad account writes** (pause campaign, change budget, edit targeting) are handled by the user in Ads Manager, not by Claude. The post-launch-optimization skill generates instructions; Mayank executes.
- **Organic reads** (what this file covers) are lower-risk but still go through Windsor's cert with Meta — if Windsor's relationship sours, we lose data temporarily. Acceptable.

## Channel → metric mapping

Each channel has:
- A **scorer** in `record_performance.SCORERS` that defines required metrics + weighted-score formula
- A **field_map** in `pull_performance_windsor.CONNECTOR_REGISTRY` that translates Windsor field names → scorer metric keys

The two must stay in sync. If a scorer adds a new required metric, check the Windsor field list below for a match; if none exists, scorer must tolerate a `0` default.

### LinkedIn (`linkedin_organic`)

Scorer: `linkedin`. Required metrics: `impressions, reactions, comments, reshares, saves`.

| Scorer metric | Windsor field | Notes |
|---|---|---|
| `impressions` | `share_impression_count` | |
| `reactions` | `share_like_count` | "Like" count on LinkedIn = all reactions (like/celebrate/support/love/insightful/funny) |
| `comments` | `share_comment_count` | |
| `reshares` | `share_count` | Confusingly named — this is the reshare count |
| `saves` | ⚠️ *not exposed* | LinkedIn Organization Analytics API doesn't expose post-level saves. Passes as 0. Scorer's formula doesn't weight saves for LinkedIn (it weights comments, saves, reshares, reactions in that order), so a missing saves = small score underestimate. Acceptable. |

Bonus fields pulled (not used by scorer but stored in raw row for future use):
- `share_unique_impressions_count` — dedup'd reach
- `share_clicks_count` — profile/link clicks
- `share_engagement_rate` — Windsor's precomputed ratio
- `ctr` — impressions / clicks
- `organization_follower_count` — account-level snapshot (useful for baseline drift tracking)

### X (`x_organic`)

Scorer: `x`. Required metrics: `impressions, replies, retweets, likes, bookmarks`.

| Scorer metric | Windsor field | Notes |
|---|---|---|
| `impressions` | `impression_count` | |
| `replies` | `reply_count` | |
| `retweets` | `retweet_count` | |
| `likes` | `like_count` | |
| `bookmarks` | ⚠️ *not reliably exposed* | X's API v2 gates bookmarks behind Pro tier. Passes as 0. Scorer tolerates. |
| `quote_tweets` | ⚠️ *not reliably exposed* | Same gating as bookmarks. |

Windsor's `x_organic` doesn't expose a clean URL field per tweet. The puller constructs the canonical URL from `tweet_id` + a handle default (`digischola`) for attribution matching. If the X account handle changes, update `_construct_x_url` in `pull_performance_windsor.py`.

### Facebook Page (`facebook_organic`)

Scorer: `facebook`. Required metrics: `reach, reactions, comments, shares`.

| Scorer metric | Windsor field | Notes |
|---|---|---|
| `reach` | `post_impressions_organic_unique` | Unique people who saw it, organic-only |
| `reactions` | `post_reactions_total` | All reaction types summed |
| `comments` | `post_comments_total` | |
| `shares` | `post_activity_by_action_type_share` | Shares as a type-of-action |

Attribution via `permalink_url`. Bonus available fields include breakdown-per-reaction-type (`post_reactions_like_total`, `post_reactions_love_total`, etc.) if we ever want sentiment analysis.

### Instagram (`instagram`)

Scorer: `instagram` (feed posts + carousels) or `instagram-reel` (reels) — `resolve_channel_key()` routes based on draft's `format` field.

| Scorer metric | Windsor field | Notes |
|---|---|---|
| `reach` | `media_reach` | |
| `likes` | `media_like_count` | |
| `comments` | `media_comments_count` | |
| `saves` | `media_saved` | **IG's most important engagement signal** — saves indicate high-intent. Weighted 15× in scorer. |
| `shares` | `media_shares` | |
| `plays` (reels only) | `media_plays` | |
| `completion_rate` (reels only) | ⚠️ derive from `media_reel_avg_watch_time` | Not directly exposed. Would need Reel duration from creative brief to compute. For v1, leave unset. |

Attribution via `media_permalink`. For carousels, `carousel_album_*` fields also populate (carousel-specific metrics).

### Facebook & Instagram (Meta) — Loomer caveat

Both are Meta Graph API pulls. Monitor Business Manager for any warnings about "unusual API activity". If one ever lands, run:
```bash
python3 pull_performance_windsor.py summary   # see last-pulled date
```
Disconnect the relevant Windsor connector in Windsor's dashboard if the warning escalates. Fall back to `record_performance.py` manual paste for the gap period.

## Fields we considered but didn't pull

- **LinkedIn `share_engagement_rate`**: Windsor pre-computes this. We compute our own weighted score instead for cross-channel comparability — Windsor's rate is just `(impressions - clicks + likes + comments + shares) / impressions` or similar, which is not what we want. Stored in raw row for curiosity.
- **Facebook `page_*` fields** (page_fans, page_follows, etc.): page-level, not post-level. Useful for baseline drift but not per-post scoring. Future enhancement.
- **Instagram `story_*` fields**: Stories aren't in our Phase 1 channel mix. Add to registry if/when we start doing Stories.
- **X `video_views`, `playback_XX_count`**: only matter for video tweets. Not in current mix.
- **Demographics fields** (`country_follower_counts`, `audience_age_name`, etc.): account-level audience breakdown, not post-level. Out of scope for per-post scoring. Would be interesting for a quarterly audience-composition report.

## Updating the registry

If you add a new channel (e.g., YouTube, Pinterest, Threads):
1. Run `get_connectors(include_not_yet_connected=True)` via Windsor MCP to find the connector ID
2. If not connected yet, run `get_connector_authorization_url(connector=...)` and paste the URL into a browser to OAuth
3. Run `get_options(connector=..., accounts=[...])` to enumerate available fields
4. Add a scorer to `record_performance.SCORERS` (copy an existing one and adjust weights per the channel's highest-intent engagement signal)
5. Add a registry entry to `pull_performance_windsor.CONNECTOR_REGISTRY` pointing to the right fields
6. Update this file's channel-map table
