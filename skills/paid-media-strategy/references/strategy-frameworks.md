# Strategy Frameworks & Decision Trees

Decision logic for every major strategy dimension. These are not suggestions — they're conditional rules based on platform mechanics, conversion volume, budget, and business maturity. Read the relevant platform reference file (meta-ads-system.md or google-ads-system.md) alongside this file.

---

## Table of Contents

1. [Campaign Type Selection](#1-campaign-type-selection)
2. [Bidding Strategy Selection](#2-bidding-strategy-selection)
3. [Audience & Targeting Architecture](#3-audience--targeting-architecture)
4. [Budget Allocation Frameworks](#4-budget-allocation-frameworks)
5. [Creative Format Recommendations](#5-creative-format-recommendations)
6. [Conversion & Measurement Setup](#6-conversion--measurement-setup)
7. [Phased Execution Logic](#7-phased-execution-logic)

---

## 1. Campaign Type Selection

### Google Ads Decision Tree

```
START → What is the primary conversion action?

├── Purchase (e-commerce)
│   ├── Has Merchant Center feed? → YES → PMax (primary) + Brand Search (protection)
│   │   └── Add Standard Shopping only if need product-level bid control
│   └── NO feed → Search (non-brand) + Brand Search + Demand Gen (if video assets exist)
│
├── Lead (form fill, call, booking)
│   ├── Budget > $3K/mo AND conversion volume > 30/mo expected?
│   │   ├── YES → Search (non-brand) + PMax (with lead form assets) + Brand Search
│   │   └── NO → Search (non-brand) + Brand Search only (consolidate for learning)
│   └── Local service? → Add Local Services Ads if eligible
│
├── App Install
│   ├── Has Play Store listing? → App Campaign (primary)
│   │   └── Add Search (app-related keywords) if budget allows
│   └── iOS only → App Campaign + consider Demand Gen for awareness
│
├── Awareness / Consideration
│   ├── Has video assets? → Video (YouTube) + Demand Gen
│   └── No video → Display (remarketing) + Demand Gen (image)
│
└── Store Visit / Local
    └── PMax (with location assets) + Local Services Ads (if eligible)
```

### Meta Ads Decision Tree

```
START → What is the primary conversion action?

├── Purchase (e-commerce / DTC)
│   ├── Has product catalog + 50+ weekly purchases?
│   │   ├── YES → Advantage+ Shopping Campaign (ASC) primary + manual Sales campaign for testing
│   │   └── NO (low volume) → Sales campaign, optimize for AddToCart or InitiateCheckout first
│   │       └── Move to Purchase optimization once hitting 50/week threshold
│   └── Subscription? → Sales campaign, optimize for Subscribe or Trial Start event
│
├── Lead Generation
│   ├── CRM integration available?
│   │   ├── YES → Leads objective (Instant Forms) + Sales objective (website Lead event) — run parallel
│   │   └── NO → Leads objective (Instant Forms) with lead quality filtering questions
│   └── High-consideration / B2B? → Leads with conditional logic forms + retargeting funnel
│
├── App Install / Engagement
│   ├── SDK/MMP properly configured + SKAN setup?
│   │   ├── YES → Advantage+ App Campaign (AAC) primary
│   │   └── NO → Fix tracking first. Do NOT launch without proper attribution.
│   └── Re-engagement? → App Promotion with in-app event optimization
│
├── Traffic / Content
│   └── Traffic objective → optimize for Landing Page Views (not Link Clicks)
│       └── Build retargeting pools for later conversion campaigns
│
└── Awareness / Reach
    └── Awareness objective → optimize for Reach with frequency cap
        └── Use as top-of-funnel feeder for conversion campaigns
```

### Cross-Platform Decision (When Both)

When running both Google and Meta, the split depends on:
- **Intent capture vs demand creation:** Google captures existing demand (search intent), Meta creates demand (interruption-based). Lead with Google if category has search volume. Lead with Meta if visual/emotional product with low search volume.
- **Budget allocation starting point:** 60/40 Google/Meta for search-heavy categories. 40/60 for visual/lifestyle/DTC. 50/50 when unclear — let performance data decide.
- **Attribution overlap:** Use platform-specific conversion tracking (not just GA4) for optimization. Accept that both platforms will claim some of the same conversions. Use incrementality/lift studies when budget allows.

---

## 2. Bidding Strategy Selection

### Google Ads Bidding Decision Tree

```
New campaign / < 30 conversions per month:
→ Maximize Conversions (no target) — let Google learn
→ Exception: if CPC matters more than conversions (awareness), use Maximize Clicks
→ Exception: Brand campaigns → Target Impression Share (90%+ top of page)

Stable campaign / 30-50+ conversions per month:
→ Know your target CPA? → Maximize Conversions with tCPA
→ Know your target ROAS? → Maximize Conversion Value with tROAS
→ Don't know targets? → Run Maximize Conversions for 2-4 weeks, then set tCPA at 10-20% above observed CPA

PMax:
→ Always Smart Bidding (Maximize Conversions or Maximize Conversion Value)
→ Set tCPA/tROAS only after 2-4 weeks of stable conversion data
→ Start without targets to avoid throttling spend

Scaling:
→ Increase budgets by max 20% per change (Google equivalent of Meta's 20% rule)
→ When changing bid strategy, expect 1-2 week learning period
→ Never change bid strategy AND budget simultaneously
```

### Meta Ads Bidding Decision Tree

```
New campaign / learning phase:
→ Highest Volume (default) — no cost cap, no ROAS goal
→ Let the system learn who converts at what cost
→ Budget must support 50 optimization events/week per ad set

Stable campaign / post-learning:
→ Profitable and want to protect margin? → Cost per Result Goal (set at observed CPA)
→ Want to maximize revenue with ROAS floor? → ROAS Goal (Minimum ROAS)
→ Scaling aggressively? → Stay on Highest Volume, increase budget 20% max per 3-4 days

Advantage+ Shopping (ASC):
→ Uses Highest Volume or ROAS Goal only
→ Set existing customer cap (typically 20-30%) to control remarketing spend

Budget type:
→ CBO (Campaign Budget Optimization) — preferred for most setups, lets Meta distribute
→ Ad Set Budget — only when you need hard spend control per audience segment
→ CBO rule: fewer ad sets (3-5) is better than many small ones for learning
```

---

## 3. Audience & Targeting Architecture

### Google Ads Targeting

```
Search campaigns:
├── Keyword match types:
│   ├── Broad match + Smart Bidding = Google's 2025 recommendation for most
│   ├── Phrase match = when you need more control, moderate volume
│   ├── Exact match = brand terms, very high-intent specific terms
│   └── Negative keywords = CRITICAL — build aggressively from search term reports
├── Audience layers (Observation mode first, then Targeting if data supports):
│   ├── In-market segments (people actively researching)
│   ├── Custom segments (keyword + URL based)
│   └── Remarketing lists (site visitors, converters)
└── Don't: use SKAGs (deprecated approach), over-segment with exact match only

PMax:
├── Audience signals (hints, NOT hard targeting):
│   ├── Custom segments (competitor URLs, search themes)
│   ├── Your data (remarketing lists, Customer Match)
│   └── In-market / affinity segments
├── Search themes (up to 25 per asset group) — guide PMax search behavior
└── Brand exclusions — prevent PMax from cannibalizing brand search

Display / Demand Gen:
├── Remarketing = primary use case for Display
├── In-market + custom segments for prospecting
└── Lookalike / similar audiences where available (Demand Gen supports)
```

### Meta Ads Targeting

```
2025-2026 reality: Andromeda system rewards BROAD targeting + strong creative diversity.

Prospecting:
├── Broad targeting (age + gender + location only) = Meta's recommended starting point
│   └── Let Advantage+ Audience expand from there
├── Interest stacking = use as audience signals, NOT narrow restrictions
│   └── Stack 5-10 related interests per ad set for signal diversity
├── Lookalike audiences:
│   ├── Source: purchasers/leads (highest quality seed)
│   ├── Size: 1-3% for precision, 5-10% for scale
│   └── Layer with Advantage+ Audience expansion ON
└── Custom audiences (prospecting exclusion):
    └── Exclude existing customers from prospecting to avoid waste

Retargeting:
├── Website visitors (Pixel + CAPI required)
│   ├── 7-day visitors (hot)
│   ├── 30-day visitors (warm)
│   └── 180-day visitors (cold retarget)
├── Engagement audiences:
│   ├── Video viewers (25%, 50%, 75%, 95% watched)
│   ├── Instagram/Facebook engagers
│   └── Lead form openers (didn't submit)
└── Customer lists (CRM upload for exclusion or upsell)

Key rule: Consolidate audiences. Fewer, larger ad sets > many small, overlapping ones.
Andromeda and Lattice optimize better with broad inputs and creative variation.
```

---

## 4. Budget Allocation Frameworks

### Framework 1: Funnel-Based Allocation

```
Conservative (lead gen, B2B, high-consideration):
├── 60-70% Bottom-of-funnel (conversion campaigns)
├── 20-30% Mid-funnel (retargeting, consideration)
└── 10% Top-of-funnel (awareness, audience building)

Aggressive (e-commerce, DTC, impulse purchase):
├── 40-50% Bottom-of-funnel (Sales/Purchase campaigns)
├── 30-40% Mid-funnel (retargeting, cart abandonment)
└── 20% Top-of-funnel (prospecting, video views)

New account / no data:
├── 80% Bottom-of-funnel (prove ROI first)
├── 20% Retargeting
└── 0% Top-of-funnel (add later once conversion flow proven)
```

### Framework 2: Campaign-Type Allocation (Google)

```
Lead gen business:
├── 50-60% Search (non-brand, high-intent keywords)
├── 15-20% PMax (with lead form extensions)
├── 10-15% Brand Search (protection)
├── 10-15% Display/Demand Gen (remarketing + awareness)

E-commerce:
├── 40-50% PMax (with Merchant Center feed)
├── 20-30% Search (non-brand, category terms)
├── 10-15% Brand Search
├── 10-15% Demand Gen / YouTube
```

### Framework 3: Campaign-Type Allocation (Meta)

```
Lead gen business:
├── 50-60% Leads / Sales campaigns (conversion-optimized)
├── 20-30% Retargeting (website visitors, engagers)
├── 10-20% Top-of-funnel (video views for audience building)

E-commerce / DTC:
├── 40-50% ASC (if qualified — 50+ weekly purchases)
├── 20-30% Manual Sales campaign (creative testing)
├── 10-20% Retargeting (DPA, cart abandonment)
├── 10% Awareness / video (prospecting pool)

App install:
├── 50-60% AAC (primary UA)
├── 20-30% App Promotion (re-engagement, in-app events)
├── 10-20% Traffic / Awareness (pre-launch or soft-launch)
```

### Monthly Budget Minimums (Directional)

These are starting points, not hard rules. Actual minimums depend on CPC/CPM in the market.

```
Google Ads:
├── Search-only (lead gen): $1,500-2,500/mo minimum for learning
├── Search + PMax: $3,000-5,000/mo minimum
├── Full stack (Search + PMax + Display + Video): $5,000+/mo

Meta Ads:
├── Single campaign: $1,000-1,500/mo minimum (to exit learning)
├── Prospecting + retargeting: $2,000-3,000/mo minimum
├── ASC-qualified: $3,000+/mo (need volume for Advantage+ to work)

Both platforms:
├── Minimum viable: $3,000-4,000/mo split across both
├── Recommended: $5,000-10,000/mo for meaningful cross-platform data
```

---

## 5. Creative Format Recommendations

### Google Ads Creative

```
Search (RSA):
├── 15 headlines (use all slots): brand, benefit, CTA, location, offer, social proof variants
├── 4 descriptions: value prop, features, urgency, trust signals
├── Pin sparingly — only pin brand name to H1 if needed, let Google test combinations
├── Ad strength: aim for "Good" or "Excellent"

PMax asset groups:
├── Images: 20 unique assets minimum (landscape, square, portrait)
├── Videos: at least 1 video per asset group (Google will auto-generate if not provided, but custom is better)
├── Headlines: 5 short (30 char) + 5 long (90 char)
├── Descriptions: 5 (90 char)
├── Call to action: match to conversion type
├── Sitelinks, callouts, structured snippets: fill all extension slots

Display (RDA):
├── Up to 15 images (multiple aspect ratios)
├── 5 headlines (30 char) + 1 long headline (90 char) + 5 descriptions (90 char)
└── Logo required
```

### Meta Ads Creative

```
Format priority (2025-2026):
├── 1. Short-form video (Reels-first): 9:16, under 30 seconds, hook in first 3 seconds
├── 2. Static image: 1:1 or 4:5, high contrast, clear CTA
├── 3. Carousel: 3-5 cards, story arc or product showcase
├── 4. UGC-style content: outperforming polished creative in most verticals

Creative testing framework:
├── Per ad set: 3-6 creatives minimum for Advantage+ to optimize
├── Test variables: hook (first 3 sec), offer, format, CTA, social proof
├── Kill rule: if CTR < 50% of ad set average after 2x the CPA in spend, pause
├── Refresh cycle: every 2-4 weeks rotate new creatives (fatigue is real)

Specs to enforce:
├── Image: 1080x1080 (1:1) or 1080x1350 (4:5), <30MB
├── Video: 1080x1920 (9:16) or 1080x1080, <4GB, H.264
├── Carousel: 1080x1080 per card, 2-10 cards
├── Text: Primary 125 chars, Headline 40 chars, Description 30 chars (recommended, not hard limits)
```

---

## 6. Conversion & Measurement Setup

### Google Ads

```
Must-haves:
├── Google tag (gtag.js) or GTM container on all pages
├── Primary conversion action = the real business outcome (purchase, lead, call)
├── Secondary conversion actions = micro-conversions (page view, button click) — for signals, not bidding
├── Enhanced conversions = ALWAYS enable (hashed first-party data matching)
├── Consent Mode v2 = MANDATORY for EU/EEA traffic (behavioral modeling for consented users)

Attribution:
├── Default: Data-driven attribution (Google's recommendation)
├── Conversion window: 30-day click, 1-day view for most
├── Offline conversions: import if sales cycle > 1 day (GCLID matching)

PMax-specific:
├── Conversion value rules: set different values by location, device, audience if applicable
├── New customer acquisition goal: enable to prioritize net-new customers over repeat
```

### Meta Ads

```
Must-haves:
├── Meta Pixel on all pages (base code + standard events)
├── Conversions API (CAPI) = MANDATORY alongside Pixel (server-side deduplication)
│   └── Match quality score: aim for 6+/10 (name, email, phone, external_id)
├── Domain verification + Aggregated Event Measurement (AEM) for iOS
├── Event priority ranking: set top 8 events (Purchase > Lead > AddToCart > ViewContent etc.)

Attribution:
├── Default: 7-day click, 1-day view (Meta's standard, post-iOS 14.5)
├── Compare with 1-day click for a "floor" view of performance
├── Accept modeled conversions (Meta uses statistical modeling for untracked events)

iOS considerations:
├── SKAdNetwork for app campaigns
├── AEM limits optimization events to 8 per domain
├── Expect 20-30% underreporting on Meta's dashboard vs actual (industry consensus)
```

---

## 7. Phased Execution Logic

### Phase 1: Foundation (Days 1-30)

```
Goal: Prove the conversion flow works. Get baseline data.

Google:
├── Launch Search (non-brand, highest intent keywords) + Brand Search
├── Maximize Conversions bidding (no targets yet)
├── Set up all conversion tracking + enhanced conversions
├── Build negative keyword list aggressively from search terms
├── If e-commerce: launch PMax with Merchant Center feed

Meta:
├── Launch 1-2 conversion campaigns (broadest viable targeting)
├── Highest Volume bidding (no cost caps)
├── Ensure Pixel + CAPI firing correctly, match quality score 6+
├── Test 3-6 creatives per ad set
├── Build retargeting audiences (visitors, engagers, video viewers)

Both:
├── Set up UTM parameters consistently across platforms
├── Establish baseline KPIs: CPC, CTR, conversion rate, CPA/ROAS
├── Weekly check-ins: are campaigns exiting learning?
```

### Phase 2: Optimize (Days 30-60)

```
Goal: Improve efficiency. Start scaling what works.

Google:
├── Set tCPA or tROAS based on Phase 1 data (10-20% above observed)
├── Add PMax if not already running (enough conversion data now)
├── Expand keyword coverage: add phrase/broad match with Smart Bidding
├── Add audience signals to PMax (custom segments, remarketing)
├── Launch Display remarketing if budget allows

Meta:
├── Switch to Cost per Result Goal on profitable ad sets
├── Scale winning ad sets: increase budget 20% every 3-4 days
├── Pause underperformers (creative kill rules)
├── Add retargeting campaigns (website visitors, video viewers)
├── Test new creative angles based on Phase 1 hook/hold rates
├── Consider ASC if hitting 50+ weekly purchases

Both:
├── Cross-platform deduplication analysis (which platform drives incremental?)
├── Adjust platform budget split based on CPA/ROAS comparison
├── Refresh ad copy/creative based on performance data
```

### Phase 3: Scale (Days 60-90)

```
Goal: Expand reach. Test new audiences, formats, campaigns.

Google:
├── Add Demand Gen campaigns (if video assets available)
├── Expand geographic targeting if local business showing ROI
├── Test new ad formats (callout extensions, promotion extensions)
├── PMax: add new asset groups for different product/service categories

Meta:
├── Scale ASC budget (if qualified)
├── Test lookalike audiences (1%, 3%, 5% from best converters)
├── Launch awareness/video view campaigns for top-of-funnel
├── Expand to new placements (Reels, Stories if not already)
├── UGC creative production pipeline

Both:
├── Incrementality testing (geo-lift, holdout groups) if budget > $10K/mo
├── Build automated reporting dashboard
├── Quarterly strategy review: what's working, what to cut, what to test next
```
