# Data Queries Reference — Windsor.ai MCP

## Table of Contents

- [Query Execution Rules](#query-execution-rules)
- [Meta Ads Queries](#meta-ads-queries)
- [Google Ads Queries](#google-ads-queries)
- [Query Execution Order](#query-execution-order)
- [Conversion Event Mapping](#conversion-event-mapping)

Load this file in Step 2. Contains exact field names and query configurations for both platforms.

## Query Execution Rules

1. Always call `get_connectors()` first to confirm account IDs
2. Skip platform queries if client doesn't use that platform
3. Run queries in parallel where possible (independent queries)
4. Date ranges: `last_30d` for primary, custom dates for comparison period
5. If a query returns empty, log it and move on — don't fail the analysis

## Meta Ads Queries

### MQ1: Campaign Health

```
connector: "facebook"
fields: ["campaign", "campaign_id", "campaign_status", "campaign_objective",
         "spend", "impressions", "reach", "frequency", "cpm",
         "clicks", "link_clicks", "ctr", "cpc",
         "actions_lead", "actions_landing_page_view", "actions_purchase",
         "cost_per_action_type_lead", "cost_per_action_type_link_click",
         "action_values_purchase", "actions_link_click",
         "cost_per_action_type_landing_page_view"]
date_preset: "last_30d"
```

**Comparison query:** Same fields, `date_from` / `date_to` for previous 30-day window.

**Purpose:** Layer 1 (health check), Layer 8 (cross-platform), Layer 9 (trending with daily breakdown).

**Derived metrics to calculate:**
- ROAS = action_values_purchase / spend
- CPA = spend / conversions (use the relevant action field per client config)
- Budget pacing = spend / (monthly_budget × days_elapsed / days_in_month)

---

### MQ2: Ad Set Performance

```
connector: "facebook"
fields: ["campaign", "adset_name", "adset_id", "adset_status",
         "adset_daily_budget", "adset_bid_strategy",
         "spend", "impressions", "reach", "frequency",
         "clicks", "link_clicks", "ctr", "cpc",
         "actions_lead", "actions_purchase",
         "cost_per_action_type_lead", "action_values_purchase"]
date_preset: "last_30d"
```

**Purpose:** Layer 2 (which audiences/ad sets carry weight).

**Analysis rules:**
- Rank ad sets by CPA (ascending = best first)
- Flag ad sets with spend >$50 and 0 conversions
- Flag frequency >3.0 at ad set level
- Flag ad sets in learning phase (<50 conversions in 7 days)

---

### MQ3: Ad Creative Performance

```
connector: "facebook"
fields: ["campaign", "adset_name", "ad_name", "ad_id",
         "spend", "impressions", "clicks", "link_clicks", "ctr", "cpc",
         "actions_lead", "actions_purchase",
         "cost_per_action_type_lead", "action_values_purchase",
         "quality_ranking", "engagement_rate_ranking", "conversion_rate_ranking"]
date_preset: "last_30d"
```

**Purpose:** Layer 2 (creative winners/losers), Layer 4 (creative intelligence), Layer 3 (kill/scale).

**Analysis rules:**
- Rank ads by CPA within each ad set
- Flag quality_ranking = "BELOW_AVERAGE_35" or worse
- Flag engagement_rate_ranking = "BELOW_AVERAGE_35" or worse
- Flag ads with spend >$30 and 0 conversions as kill candidates
- Identify top 3 ads by efficiency — what do they have in common?

---

### MQ4: Video Creative Metrics

```
connector: "facebook"
fields: ["campaign", "ad_name", "ad_id",
         "spend", "impressions",
         "video_thruplay_watched_actions_video_view",
         "video_p25_watched_actions_video_view",
         "video_p50_watched_actions_video_view",
         "video_p75_watched_actions_video_view",
         "video_p100_watched_actions_video_view",
         "video_play_actions_video_view",
         "link_clicks", "actions_lead", "actions_purchase",
         "cost_per_action_type_lead"]
date_preset: "last_30d"
```

**Purpose:** Layer 4 (creative intelligence — video specific).

**Derived metrics to calculate:**
- Hook rate = video_play_actions_video_view / impressions (or 3s views if available)
- Hold rate = video_thruplay_watched_actions_video_view / video_play_actions_video_view
- Drop-off curve = p25 → p50 → p75 → p100 (where do viewers leave?)

**Analysis rules:**
- Hook rate <25% = weak hook, recommend new opening
- Hold rate <30% = weak creative, content doesn't sustain interest
- If p25 is high but p50 drops >50%, the middle of the video loses people
- If ThruPlay rate is good but CPA is bad, the CTA or landing page is the problem

---

### MQ5: Demographic Breakdown

```
connector: "facebook"
fields: ["campaign", "age", "gender",
         "spend", "impressions", "clicks", "link_clicks",
         "actions_lead", "actions_purchase",
         "cost_per_action_type_lead", "action_values_purchase"]
date_preset: "last_30d"
```

**Purpose:** Layer 2 (who converts vs who clicks).

**Analysis rules:**
- Identify age/gender segments with CPA >2x account average → exclusion candidates
- Identify segments with CPA <0.5x average → expansion candidates
- Flag segments with >15% of spend but <5% of conversions = wasted spend
- Minimum threshold: only analyze segments with >$20 spend (avoid noise)

---

### MQ6: Placement Breakdown

```
connector: "facebook"
fields: ["campaign", "publisher_platform", "platform_position",
         "spend", "impressions", "clicks", "link_clicks", "ctr",
         "actions_lead", "actions_purchase",
         "cost_per_action_type_lead", "action_values_purchase"]
date_preset: "last_30d"
```

**Purpose:** Layer 2 (is Stories/Reels/Audience Network burning budget?).

**Analysis rules:**
- Compare CPA across placements within each campaign
- Flag Audience Network if CPA >3x feed CPA → recommend exclusion
- Flag placements with >10% spend and 0 conversions
- Note: Advantage+ placements can't be individually excluded — flag for restructuring instead

---

### MQ-Daily: Daily Trend Data

```
connector: "facebook"
fields: ["campaign", "date", "spend", "impressions", "clicks",
         "link_clicks", "actions_lead", "actions_purchase",
         "ctr", "cpc", "cpm", "reach", "frequency"]
date_preset: "last_14d"
```

**Purpose:** Layer 9 (trend analysis, anomaly detection).

**Analysis rules:**
- Calculate 7-day rolling average for CPA, CTR, CPC
- Flag any day with CPA >3x the 7-day average → anomaly
- Detect trend direction: improving (CPA declining), stable, or degrading (CPA rising)
- Account for conversion lag: Meta reports conversions on click date, not conversion date

---

## Google Ads Queries

### GQ1: Campaign Health

```
connector: "google_ads"
fields: ["campaign_name", "campaign_status", "cost", "impressions", "clicks",
         "ctr", "average_cpc", "conversions", "conversion_rate",
         "cost_per_conversion", "conversion_value", "conversions_value_per_cost",
         "search_impression_share", "search_budget_lost_impression_share",
         "search_rank_lost_impression_share",
         "search_absolute_top_impression_share"]
date_preset: "last_30d"
```

**Comparison query:** Same fields, previous 30-day window.

**Purpose:** Layer 1, Layer 8, Layer 9.

**Derived metrics:**
- ROAS = conversion_value / cost
- Budget pacing = cost / (monthly_budget × days_elapsed / days_in_month)
- Total impression share lost = budget_lost + rank_lost

**Analysis rules:**
- Impression share <50% = significant opportunity gap
- Budget lost IS >20% = budget-constrained, consider increasing budget or narrowing targeting
- Rank lost IS >20% = quality/bid issue, check quality scores

---

### GQ2: Ad Group + Keyword

```
connector: "google_ads"
fields: ["campaign_name", "ad_group_name", "keyword_text", "keyword_match_type",
         "cost", "impressions", "clicks", "ctr", "average_cpc",
         "conversions", "conversion_rate", "cost_per_conversion",
         "quality_score"]
date_preset: "last_30d"
```

**Purpose:** Layer 2, Layer 3.

**Analysis rules:**
- Quality score <5 = needs attention (ad relevance, landing page, expected CTR)
- Keywords with spend >$50 and 0 conversions = pause candidates
- Keywords with CPA <0.5x target and >5 conversions = scale candidates
- Broad match keywords: check search terms report for relevance

---

### GQ3: Search Terms

```
connector: "google_ads"
fields: ["search_term", "campaign_name", "ad_group_name",
         "keyword_text", "keyword_match_type",
         "impressions", "clicks", "cost", "conversions",
         "cost_per_conversion"]
date_preset: "last_30d"
```

**Purpose:** Layer 3 (negative keyword mining).

**Analysis rules:**
- Search terms with spend >$20 and 0 conversions = negative keyword candidates
- Search terms with conversions and low CPA = potential new keyword additions
- Flag irrelevant search terms from broad/phrase match
- Group negatives by theme (e.g., "free", "DIY", competitor names if not targeting)

---

### GQ4: Ad Performance

```
connector: "google_ads"
fields: ["campaign_name", "ad_group_name", "ad_name", "ad_id",
         "cost", "impressions", "clicks", "ctr",
         "conversions", "conversion_rate", "cost_per_conversion"]
date_preset: "last_30d"
```

**Purpose:** Layer 2, Layer 3, Layer 4 (RSA performance).

**Analysis rules:**
- Compare ad CTR and CPA within each ad group
- Flag ads with >500 impressions and CTR <1% (search) → weak ad copy
- Identify winning RSA patterns (which headlines/descriptions appear most)

---

### GQ5: Device + Time Breakdown

```
connector: "google_ads"
fields: ["campaign_name", "device", "day_of_week",
         "cost", "clicks", "conversions", "cost_per_conversion"]
date_preset: "last_30d"
```

**Purpose:** Layer 2.

**Analysis rules:**
- Compare CPA across devices — if mobile CPA >2x desktop, recommend bid adjustment
- Identify worst-performing day of week — consider dayparting
- Flag device/day combinations with spend >$20 and 0 conversions

---

### GQ6: Auction Insights

```
connector: "google_ads"
fields: ["campaign_name", "auction_insight_domain",
         "search_impression_share",
         "search_absolute_top_impression_share"]
date_preset: "last_30d"
```

**Purpose:** Layer 6 (competitive context).

**Note:** Windsor.ai may not support all auction insight fields. If query fails, skip Layer 6 for Google and note in report. Auction insights is a special report type — test availability.

**Analysis rules:**
- Identify top 3 competitors by impression share
- Flag new competitors not seen in previous analysis
- Flag competitors whose impression share grew >10 points (aggressive entry)

---

### GQ-Daily: Daily Trend Data

```
connector: "google_ads"
fields: ["campaign_name", "date", "cost", "impressions", "clicks",
         "ctr", "average_cpc", "conversions", "cost_per_conversion"]
date_preset: "last_14d"
```

**Purpose:** Layer 9.

**Analysis rules:** Same as MQ-Daily — rolling averages, anomaly detection, trend direction.

---

## Query Execution Order

Recommended execution order for efficiency:

1. **Parallel batch 1:** MQ1 + GQ1 (campaign health — both platforms)
2. **Parallel batch 2:** MQ2 + MQ3 + GQ2 + GQ4 (mid-level detail)
3. **Parallel batch 3:** MQ4 + MQ5 + MQ6 + GQ3 + GQ5 (breakdowns)
4. **Parallel batch 4:** MQ-Daily + GQ-Daily (trend data)
5. **Sequential:** GQ6 (auction insights — may fail, run last)

Total: 14 queries. Expected execution: 30-60 seconds via MCP.

## Conversion Event Mapping

The skill must use the correct conversion field per client. Read from client config:

| Conversion Type | Meta Field | Google Field |
|---|---|---|
| Leads (form fills) | actions_lead | conversions |
| Purchases | actions_purchase | conversions |
| Landing page views | actions_landing_page_view | conversions |
| Bookings | actions_purchase (usually) | conversions |

Google Ads uses a single `conversions` field (pre-filtered by account-level conversion settings). Meta requires selecting the correct action field.
