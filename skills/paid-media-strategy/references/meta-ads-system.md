\# Meta Ads Expert Reference Guide (2025–2026)

## Table of Contents

- [Executive Summary](#executive-summary)
- [1. Campaign Objectives & Optimization Events](#1-campaign-objectives--optimization-events)
- [2. Advantage+ & Automation Features](#2-advantage--automation-features)
- [3. Audience Architecture](#3-audience-architecture)
- [4. Bidding & Budget Strategies](#4-bidding--budget-strategies)
- [5. Campaign Structure Best Practices](#5-campaign-structure-best-practices)
- [6. Placements & Formats](#6-placements--formats)
- [7. Conversion Tracking & Attribution](#7-conversion-tracking--attribution)
- [8. Reporting & Optimization Signals](#8-reporting--optimization-signals)

\#\# Executive Summary

Meta Ads has fully migrated to the ODAX objective framework (Awareness, Traffic, Engagement, Leads, App Promotion, Sales) and layered it on top of a fundamentally new AI-driven delivery stack built around Meta Lattice, Andromeda, GEM and the Advantage+ suite. Performance in 2025–2026 is less about micromanaging knobs in Ads Manager and more about feeding the system strong conversion signals, broad audiences, and diverse creatives while selectively overriding automation where it clearly underperforms. This guide summarizes current-best practices and platform rules at a level suitable for senior media buyers and strategy tooling.\[1\]\[2\]\[3\]\[4\]\[5\]

\*\*\*

\#\# 1\. Campaign Objectives & Optimization Events

\#\#\# 1.1 Current ODAX Objective List

Meta’s Outcome-Driven Ad Experiences (ODAX) consolidates the legacy 11 objectives into six core objectives that now appear in Ads Manager globally: Awareness, Traffic, Engagement, Leads, App Promotion, and Sales. Store Traffic remains partially supported in some accounts but is no longer a primary front-end option and should be treated as a legacy/edge case.\[6\]\[1\]

| ODAX Objective | Typical Optimization Events (at ad set) | Primary Use Cases |  
| \--- | \--- | \--- |  
| Awareness | Reach, Impressions | Brand awareness, reach, frequency-building, top-of-funnel video or static bursts.\[1\]\[7\] |  
| Traffic | Link Clicks, Landing Page Views, Impressions, Daily Unique Reach | Driving site visits, blog traffic, pre-sell content, building website retargeting pools.\[8\]\[9\] |  
| Engagement | Post Engagement, Video Views, ThruPlays, Messages, Event Responses, Page Likes | Social proof, content distribution, video view funnels, Messenger/DM conversations.\[1\]\[10\] |  
| Leads | On‑platform Instant Forms, Calls, Messages, Conversions (lead events) | Lead gen via native forms, calls, or routed to site, often for high-consideration services/B2B.\[11\] |  
| App Promotion | App Installs, In‑app Events (registrations, purchases, custom events) | User acquisition and re‑engagement for mobile apps, subscriptions, and games.\[12\]\[11\] |  
| Sales | Conversions (web/app), Value, Catalog Sales events, Messaging, Calls | E‑commerce, DTC, subscriptions, bookings, broad ROAS-driven performance.\[13\]\[7\] |

Meta explicitly recommends mapping the objective to where the user is in the funnel (Awareness top, Traffic/Engagement mid, Leads/App Promotion/Sales bottom), and its optimization models are tuned accordingly.\[8\]\[14\]

\#\#\# 1.2 Optimization Event Selection by Objective

\*\*Awareness\*\* should generally optimize for Reach (or Impressions) to maximize unique exposure and frequency control; brand-lift optimization is only available via Brand Lift Studies for qualifying spend levels.\[15\]\[1\]

\*\*Traffic\*\* can optimize for Link Clicks or Landing Page Views; Meta’s own documentation notes that LPV optimization requires a pixel and is designed to show ads to users likely to click and fully load the destination URL, which typically yields higher-quality visits than simple clicks. For performance advertisers, LPV is preferable when conversion volume is still low but page engagement quality matters.\[16\]\[9\]

\*\*Engagement\*\* supports optimization for post engagements, video views/ThruPlays, event responses, and messages; this is best used when the immediate KPI is social proof (comments, saves, shares), video watch-through, or message volume rather than direct sales.\[10\]\[1\]

\*\*Leads\*\* can optimize for on‑platform form completions (Instant Forms), calls, messages, or conversion-based leads firing a \`Lead\` event on your site/app; Meta favors native forms from a completion-rate standpoint, but conversion-based leads are usually better when CRM quality is critical.\[17\]\[11\]

\*\*App Promotion\*\* uses install and in‑app event optimization based on App Events SDK/partner MMP data; Meta’s help center explicitly lists App Promotion, Traffic, Engagement, Sales and Leads as objectives that can run app ads, but App Promotion is tuned specifically for install and post-install actions with SKAdNetwork and app events support.\[12\]\[18\]

\*\*Sales\*\* campaigns optimize for conversions (standard or custom events), value, or catalog events, including Shop and website purchases; at ad set level you choose the specific optimization event (e.g., Purchase, InitiateCheckout, AddToCart) or Value optimization with optional ROAS goal.\[19\]\[13\]

\#\#\# 1.3 Choosing Optimization Events by Business Goal

For \*\*app installs and early-stage UA\*\*, use App Promotion with Install optimization if you lack post-install data; once the app has consistent in‑app events, switch to in‑app event or Value optimization to improve user quality and LTV.\[20\]\[11\]

For \*\*purchases and ROAS\*\*, optimize Sales campaigns to \`Purchase\` (or \`Subscribe\` for subscriptions) as soon as you can reliably hit \~50 purchase events per ad set per week; if purchase volume is too low, start with \`AddToCart\` or \`InitiateCheckout\` and move down-funnel once volume supports it.\[21\]\[14\]

For \*\*lead generation\*\*, Leads objective with Instant Forms is usually optimal for volume and cost-efficiency, while Sales or Traffic optimized to a site-based \`Lead\` event is often better for lead quality and CRM alignment; many practitioners run both in parallel and benchmark lead-to-opportunity rates.\[13\]\[17\]

For \*\*video views and brand storytelling\*\*, Engagement campaigns optimized to ThruPlay or 15-second video views are preferable; these build warm video-view audiences used later for conversion retargeting.\[22\]\[10\]

For \*\*traffic-only goals\*\* (content marketing, SEO support, low-intent nurture), Traffic optimized to Landing Page Views strikes a balance between volume and session quality; pure Link Click optimization is reserved for very soft objectives or extremely cheap experimentation.\[9\]\[16\]

\#\#\# 1.4 Bid Strategy Choice: Maximize Conversions vs Cost per Result Goal

Meta’s default bid strategy of \*\*Highest Volume\*\* (aka “Maximize conversions” when your performance goal is conversions) instructs the system to spend the budget and get as many optimization events as possible, without explicit concern for CPA or ROAS. This is almost always recommended for:\[23\]\[19\]

\- New campaigns and tests without historical benchmarks.  
\- Ad sets currently in learning phase that need volume.  
\- Prospecting at scale where stable spend and data are more important than tight cost control.

\*\*Cost per Result Goal\*\* (the renamed Cost Cap) layers a target CPA on top of Highest Volume; Meta attempts to maintain average cost near your goal, but may under-spend if the goal is unrealistic relative to auction dynamics, especially in small audiences or new campaigns. Use Cost per Result Goal when:\[24\]\[19\]

\- You already know a sustainable CPA from historical data.  
\- The ad set is out of learning and producing stable volume.  
\- You are scaling budget and want to guard margin.

\#\#\# 1.5 Learning Phase and the 50-Event Rule

Meta’s Help Center defines the \*\*learning phase\*\* as the period when the delivery system is still exploring who responds to your ads; frequent changes or low volume keep ad sets in learning or trigger “Learning Limited.” A wide range of agency and platform documentation converges on the guideline that ad sets need roughly \*\*50 optimization events per week\*\* for the selected event (e.g., purchases, leads) to exit learning and stabilize.\[25\]\[26\]\[27\]\[21\]

Practically, this means:

\- If you cannot hit 50 weekly purchases, optimize for a higher-funnel event (AddToCart, InitiateCheckout) that can hit the threshold and then step down-funnel later.\[21\]  
\- Large, consolidated ad sets are preferred over many small ones so each can accumulate enough events; consolidation is one of the most common recommendations in 2024–2026 learning-phase optimization guides.\[28\]\[29\]  
\- Even after exiting learning, Meta still prefers sustained volume; performance can degrade if event counts fall well below 50 per week, though it may not immediately re-flag learning.

\*\*\*

\#\# 2\. Advantage+ & Automation Features

\#\#\# 2.1 Advantage+ Shopping Campaigns (ASC)

Advantage+ Shopping Campaigns are the default recommended configuration when you create a Sales campaign and are designed to handle both prospecting and remarketing in a single, highly automated structure. ASC:\[30\]\[31\]

\- Locks the campaign objective to \*\*Sales\*\*, with Performance Goal set to either maximize conversions or maximize conversion value, optionally with a ROAS goal in some accounts.\[30\]  
\- Uses \*\*Advantage+ Placements\*\* by default and does not allow manual placement selection beyond minor configurations (e.g., sometimes toggling Audience Network).\[32\]\[30\]  
\- Heavily restricts manual targeting; you can set broad location/age and provide “existing customer” lists for control of remarketing proportions, but ASC primarily relies on broad \+ pixel signals.\[32\]\[30\]  
\- Does not support Dynamic Creative at the ad level, because ASC internally tests large numbers of ad combinations; Meta cites support for automatically testing up to \~150 creative combinations.\[33\]

Best use cases for ASC include e‑commerce stores with clean Product Catalogs, functioning pixel/CAPI, and sufficient conversion volume (50+ weekly conversions per campaign) that want scale with minimal manual segmentation. Practitioners often pair ASC with one or two manually built Sales campaigns for more granular testing of offers, creative angles or specific product categories, then roll proven winners back into ASC.\[31\]\[32\]

\#\#\# 2.2 Advantage+ App Campaigns (AAC)

Advantage+ App Campaigns (previously Automated App Ads) are the App Promotion analog of ASC, consolidating app install and in‑app optimization in a unified automated campaign. AAC:\[11\]\[20\]

\- Uses App Promotion or Sales objectives with app as conversion location and relies on the Meta SDK or MMP (via SKAdNetwork/CAPI) for install and in‑app event signals.\[18\]\[12\]  
\- Automates audience, placements, and much of creative rotation; creative is typically uploaded as a set of videos/images and text variations, which the system then tests and permutes.  
\- Requires proper SKAdNetwork configuration and app event mapping to optimize correctly for iOS; failing SKAN setup often results in under-reporting and weaker optimization for iOS traffic.\[20\]\[18\]

AAC should be the default for scaled app advertisers once tracking is correctly implemented; more manual, segmented app campaigns are primarily useful for targeted experiments (e.g., specific geos, creative bets) or as backups when AAC performance materially degrades.

\#\#\# 2.3 Advantage+ Audience

Advantage+ Audience is Meta’s default automated targeting option in new campaigns, combining advertiser inputs (age, location, custom audiences, interests) with AI that can expand beyond those inputs when it predicts better results. It behaves as follows:\[34\]

\- If you provide suggestions (e.g., interests, lookalikes, custom audiences), Meta prioritizes people who match those attributes but can expand to broader demographics and interests as the system learns.\[34\]  
\- You can still set hard constraints for minimum age, geo, language, and exclusions (e.g., purchasers), which Meta will not override.\[34\]  
\- It works best with conversion-focused objectives (Sales, Leads, App Promotion), where strong event data allows the system to identify high-propensity converters beyond your manual definitions.\[35\]\[36\]

Advertisers can \*\*switch back to “original audience options”\*\* at the ad set level if they want full manual control; Meta applies Advantage+ Audience by default in many new campaign creation flows, but it is not yet mandatory outside of Advantage+ Sales/App/Leads campaign types.\[37\]\[34\]

\#\#\# 2.4 Advantage+ Placements

Advantage+ Placements is simply the new name for Automatic Placements; it tells Meta to dynamically allocate delivery across all eligible placements (Feeds, Stories, Reels, in-stream, search, Audience Network, etc.) based on where the system expects the best performance for your objective. Meta explicitly recommends Advantage+ Placements for conversion-based objectives like Leads, App Promotion, and Sales and cites internal data showing lower CPM and broader reach versus manual placements.\[38\]\[39\]\[40\]\[37\]

You can still switch to \*\*Manual Placements\*\* to restrict where ads appear, which remains advisable when:

\- Brand safety demands excluding Audience Network or certain in-stream formats.  
\- Creative is not produced in vertical aspect ratios and performs poorly in Stories/Reels.  
\- You are intentionally testing placement performance (e.g., Reels-only creatives or feed vs. Reels ROAS splits).

\#\#\# 2.5 Advantage+ Creative (Standard & Expanded Enhancements)

Advantage+ Creative is a suite of ad-level enhancements that automatically modify images, videos, and text to improve performance. Documented behaviors include:\[41\]\[42\]

\- \*\*Standard enhancements\*\*: adjust brightness, contrast, and sharpness of images; minor color and clarity tweaks.\[42\]\[41\]  
\- \*\*Dynamic formatting and cropping\*\*: resize assets, change aspect ratios, and crop images/videos to fit different placements (Feeds, Stories, Reels).\[43\]\[42\]  
\- \*\*Text variations and overlays\*\*: change font size, positioning, and sometimes add templated overlays such as “20% off” banners when the system predicts lift.\[44\]\[42\]  
\- \*\*Asset personalization\*\*: generate multiple personalized variations from a single asset, combining different crops, text snippets, and backgrounds.\[44\]\[43\]

Meta claims that Standard Enhancements can reduce cost per result by around 4 percent on average for link-click and conversion-optimized campaigns. Enhancements are typically \*\*enabled by default\*\* at the ad level and must be manually toggled off if you want pixel-perfect control.\[45\]\[41\]\[44\]

\#\#\# 2.6 Andromeda Targeting System

Andromeda is Meta’s new ad \*\*retrieval\*\* system, replacing older infrastructure and dramatically expanding the number of ads considered in each auction. Meta’s engineering blog and third-party analyses highlight several properties relevant to media buyers:\[46\]\[47\]

\- Andromeda uses deep neural networks and hierarchical indexing to retrieve candidate ads from a pool of tens of millions in milliseconds, representing a 10,000× increase in model capacity and 6–8 percent gains in retrieval accuracy and ad quality.\[48\]\[47\]\[5\]  
\- Targeting is now far more \*\*individualized\*\*; Meta is matching ads to people based on granular behavioral embeddings rather than simple audience bucket membership.\[49\]\[46\]  
\- The system is explicitly designed for \*\*broad targeting, creative variety, and automation-first structures\*\*, and industry guidance notes that complex, over-segmented account structures now actively underperform.\[4\]\[50\]

In practice this means:

\- Broad targeting and Advantage+ Audience align with how Andromeda retrieves ads; tight interest stacking or narrow lookalikes reduce candidate pools and may undercut performance.\[51\]\[4\]  
\- Creative diversity (many distinct hooks, angles, and formats) is a more powerful lever than micromanaged interests; Andromeda needs options to match different people with different creatives.\[52\]\[4\]

\#\#\# 2.7 Meta Lattice and GEM

Meta Lattice is a large unified model architecture used for \*\*ad ranking\*\*, predicting performance across surfaces (Feed, Stories, Reels) and multiple objectives (clicks, conversions, video views) simultaneously. Meta reports that Lattice improved overall ad quality by about 8 percent and boosts performance by sharing learning across placements and objectives that used to be siloed.\[2\]\[3\]

GEM, introduced widely in late 2025, is another AI model focused on improving conversion rates, particularly on Instagram and Reels; Meta and independent analyses attribute roughly 3–5 percent incremental conversion lift when GEM is active. GEM works alongside Lattice and Andromeda and especially benefits advertisers using Advantage+ Creative and broad automated setups.\[5\]

\#\#\# 2.8 Which Advantage+ Features Are Mandatory vs Optional

As of early 2026:

\- \*\*Mandatory or quasi-mandatory\*\* in certain flows:  
  \- ASC and AAC \*\*require\*\* Advantage+ Placements and Advantage+ Audience-style automation; you cannot convert them to fully manual targeting, though you can add exclusions and some audience hints.\[37\]\[30\]  
  \- Several Advantage+ enhancements (e.g., some placement and formatting behaviors) are tightly coupled with the campaign type and effectively cannot be fully disabled.  
\- \*\*Optional/toggleable\*\*:  
  \- Advantage+ Audience can be turned off in standard (non-Advantage+) campaigns by switching to Original Audience options.\[34\]  
  \- Advantage+ Placements can be toggled off in favor of Manual Placements for most non-ASC campaign types.\[40\]  
  \- Advantage+ Creative enhancements are individually toggleable at the ad level; Standard enhancements, image expansion, music, and text improvements can be disabled.\[41\]\[43\]

Meta’s product direction is clearly toward increased automation, but for now the only fully locked-down experiences are the dedicated Advantage+ campaign types; senior buyers should deliberately decide when to embrace those vs maintain manual control.

\*\*\*

\#\# 3\. Audience Architecture

\#\#\# 3.1 Broad Targeting

Broad targeting (age/geo/gender only, with no interests or lookalikes) has become a mainstream best practice for conversion campaigns, especially in larger markets. Under Andromeda and Lattice, Meta is explicitly encouraging advertisers to go broad and keep structures simple, noting better CPMs, more stable delivery, and improved performance when the system has freedom to find high-intent users.\[53\]\[4\]\[51\]

Broad works best when:

\- You have robust pixel/CAPI data and at least dozens of conversions per week for the chosen event.  
\- Your product has wide applicability (e.g., general e‑commerce, mass-market apps) rather than ultra-niche B2B.  
\- You feed the system diverse creatives representing different personas and stages of awareness.

\#\#\# 3.2 Interest Targeting Post-Andromeda

Interest targeting still exists but is less deterministic; Advantage+ detailed targeting and Andromeda allow Meta to show ads to users outside your specified interests when the system predicts better results. Studies and practitioner reports in 2024–2026 show that interest-only prospecting now often underperforms broad, especially once accounts have meaningful conversion history.\[54\]\[46\]\[51\]\[34\]

Recommended use cases for interests:

\- Early-stage accounts with limited conversion data, using a handful of logical interests to give the system initial direction.  
\- Highly niche segments where broad would waste budget (e.g., specialized B2B tools, rare hobbies) and you combine interests with custom audiences.  
\- Layered as “audience suggestions” inside Advantage+ Audience rather than hard constraints, so Meta can expand when needed.\[36\]\[34\]

\#\#\# 3.3 Lookalike Audiences

Lookalikes remain valuable, but their relative edge over broad has narrowed as Meta’s retrieval systems improved. Key principles:\[55\]\[51\]

\- \*\*Source quality\*\* matters more than size: build lookalikes from high-intent events like Purchasers, High-LTV Purchasers, or Qualified Leads, not generic Page Engagers.\[56\]\[55\]  
\- \*\*Size recommendations\*\*:  
  \- 1 percent lookalikes (top 1 percent of users most similar to source) deliver highest precision and often the best CPA but limited scale, especially in smaller geos.\[57\]\[58\]  
  \- 2–3 percent deliver more scale with modestly higher CPA and are good for scaling once 1 percent is profitable.\[58\]\[57\]  
  \- 4–10 percent prioritize reach over precision and are best used for awareness or when you have already saturated lower bands.\[57\]\[58\]  
\- Many recent analyses suggest starting with a strong 1 percent LAL and only expanding once you have proven economics, as larger lookalikes do not fix weak offers or creatives.\[59\]\[51\]

\#\#\# 3.4 Custom Audiences

Meta supports four core custom audience types: website traffic, app activity, customer lists, and engagement (Facebook/Instagram properties).\[60\]\[56\]

\- \*\*Website custom audiences\*\* are built with the Meta Pixel, allowing you to retarget visitors by URL, time-on-site, or event behavior (e.g., all \`AddToCart\` in last 7 days).\[61\]  
\- \*\*App activity audiences\*\* rely on the Meta SDK or MMP to segment users by in‑app behavior (opens, levels, purchases) and are critical for app retargeting funnels.\[62\]\[63\]  
\- \*\*Customer list audiences\*\* are fed from CRM/POC data (emails, phones, etc.) and are the backbone for retention, upsell, and high-quality LAL seeds; Meta’s own docs emphasize proper hashing and field mapping for higher match rates.\[64\]\[60\]  
\- \*\*Engagement audiences\*\* capture people who interacted with your content (video viewers, IG profile visitors, lead form openers, page engagers, etc.) and are excellent for mid‑funnel nurturing.\[61\]

Customer list audiences are persistent (users remain until removed) and are less affected by cookie expiry, making them more durable than website-based audiences for long-term retention and suppression.\[64\]

\#\#\# 3.5 Exclusions and Suppression

Exclusion audiences are a non‑negotiable part of modern architecture; they prevent wasted spend and protect user experience.

Common exclusion patterns include:

\- Excluding purchasers from prospecting and mid‑funnel campaigns (except for explicit upsell/cross-sell flows).\[32\]\[64\]  
\- Excluding recent lead submitters from top-of-funnel lead gen to avoid duplicates and spam complaints.  
\- Excluding “serial clickers, non-buyers” segments when identifiable in larger accounts.

As automation increases, careful exclusions are one of the few remaining levers to enforce business logic against Meta’s desire to chase cheap results.

\#\#\# 3.6 Audience Overlap

Audience overlap still matters, but less than in earlier generations because Andromeda matches at an individual level and because Advantage+ Audience is often expanding beyond manual definitions. Heavy overlap between prospecting ad sets mostly leads to internal competition and unpredictable learning if you keep budgets small.\[46\]\[49\]

Best practices:

\- Use fewer, broader ad sets rather than many slightly different ones; this consolidates learning and reduces accidental bidding wars.\[29\]\[52\]  
\- When you need segmentation (e.g., by geo or language), ensure audiences are mutually exclusive (separate countries, non-overlapping exclusions) to reduce overlap.

\#\#\# 3.7 Advantage+ Audience vs Manual

Advantage+ Audience is generally favored for:

\- Mature accounts optimizing for Sales or Leads with strong pixel/CAPI data.\[36\]\[34\]  
\- Large geos where broad reach and algorithmic exploration outperform handcrafted segments.\[50\]\[37\]

Manual audiences are still appropriate when:

\- You need precise control for compliance reasons (e.g., certain special categories or regulated industries).  
\- You are running small geos or highly niche B2B targets where broad would be wasteful.  
\- You are testing specific hypotheses (e.g., a new interest cluster) and want cleaner readouts.

\*\*\*

\#\# 4\. Bidding & Budget Strategies

\#\#\# 4.1 Available Bid Strategies

Meta currently exposes five primary bid strategies in Ads Manager: Highest Volume, Highest Value, Cost per Result Goal, ROAS Goal, and Bid Cap.\[65\]\[19\]

\- \*\*Highest Volume\*\* (default in most conversion campaigns) aims to get the maximum number of optimization events within your budget, without explicit cost or ROAS constraints.\[19\]\[23\]  
\- \*\*Highest Value\*\* is the default when your performance goal is Value; it focuses on generating the greatest total conversion value, even at higher CPAs.\[24\]\[19\]  
\- \*\*Cost per Result Goal\*\* (formerly Cost Cap) tries to keep your average CPA near a specified target while still pursuing volume; overly aggressive targets can cause underdelivery.\[65\]\[24\]  
\- \*\*ROAS Goal\*\* (formerly Min ROAS) is a value-based strategy where you specify a minimum acceptable ROAS and Meta optimizes for high-value conversions subject to that constraint.\[24\]\[19\]  
\- \*\*Bid Cap\*\* sets a strict maximum bid in each auction; Meta’s Help Center stresses that this is for advanced advertisers who can calculate bids from predicted conversion rates and requires ongoing bid management.\[66\]\[67\]

\#\#\# 4.2 When to Use Each Bid Strategy

\- Use \*\*Highest Volume\*\* for: new campaigns, early testing, most evergreen prospecting, and when you prioritize learning and stability over tight cost control.\[19\]\[24\]  
\- Use \*\*Cost per Result Goal\*\* once you have stable historical CPA benchmarks and want to scale while protecting margin; start with a target near recent averages, not a wishful number.\[68\]\[24\]  
\- Use \*\*Highest Value\*\* when order values vary widely and you care more about revenue than sheer order count, especially in catalog-heavy accounts.\[69\]\[19\]  
\- Use \*\*ROAS Goal\*\* for mature e‑commerce setups with reliable purchase-value tracking where you can define a clear minimum viable ROAS.\[66\]\[24\]  
\- Use \*\*Bid Cap\*\* sparingly for very competitive auctions (e.g., Black Friday, high-ticket B2B) where you need strict maximum bids or to protect against runaway CPCs; recognize that mis-set caps can dramatically throttle delivery.\[67\]\[66\]

\#\#\# 4.3 CBO vs Ad Set Budgets

Meta still supports both \*\*Campaign Budget Optimization (CBO)\*\* and ad set–level budgets; however, platform guidance and automation trends increasingly favor CBO, especially in Advantage+ structures.\[54\]\[37\]

Advantages of CBO:

\- Budget is automatically allocated toward better-performing ad sets, which aligns well with Andromeda/Lattice’s cross-ad set comparisons.  
\- It simplifies management and reduces the need for constant manual rebalancing.

Advantages of ad set budgets:

\- Clear control when testing specific audiences or when you want guaranteed spend in small segments.  
\- Useful in early testing phases or when internal reporting requires fixed budget splits.

In practice, media buyers often test with ad set budgets for clarity, then migrate winners into CBO campaigns for scale.

\#\#\# 4.4 Daily vs Lifetime Budgets

Daily budgets pace spend per day, while lifetime budgets allow Meta to shift spend across days within the schedule to hit optimization goals.\[70\]\[71\]

\- \*\*Daily budgets\*\* are safer for always-on campaigns; they provide predictable daily outlay and straightforward performance comparisons over time.  
\- \*\*Lifetime budgets\*\* can be effective for short flights, promos, and event-based campaigns where you want Meta to front-load spend on higher-opportunity days but can complicate forecasting.

\#\#\# 4.5 Scaling Without Breaking Learning

Significant changes to budgets, bids, or targeting can re-enter or prolong the learning phase; Meta documentation and multiple practitioner guides converge on the heuristic of \*\*limiting budget increases to \~20 percent at a time\*\* to avoid hard resets.\[28\]\[29\]

Common scaling patterns:

\- Increase budget by 15–20 percent every 2–3 days on stable ad sets rather than doubling or tripling overnight.  
\- For aggressive scaling, duplicate the ad set with a higher budget rather than editing the original; this creates a new learning phase but preserves the original.  
\- Consider moving to CBO when scaling multiple ad sets so the system can reallocate dollars in real time.

\#\#\# 4.6 Understanding and Managing the Learning Phase

The learning phase begins whenever you create a new ad set or make significant changes to budget, bid strategy, optimization event, or major targeting; smaller tweaks to creative typically have less impact. “Learning Limited” appears when Meta estimates that the ad set is unlikely to reach the \~50 events per week threshold with current settings.\[27\]\[21\]

Mitigation steps for Learning Limited:

\- Consolidate similar ad sets to aggregate conversions and budget into fewer entities.\[28\]  
\- Increase budget (if unit economics support it) to achieve required event volume; some scaling guides explicitly back-calculate minimum daily budget from target CPA × 50 events/week.\[21\]\[28\]  
\- Move up the funnel to a more frequent optimization event, then later switch back down to purchases once volumes support it.\[21\]

\*\*\*

\#\# 5\. Campaign Structure Best Practices

\#\#\# 5.1 Consolidated vs Segmented Structures

Meta’s own messaging and industry analyses now explicitly favor \*\*simplified, consolidated account structures\*\* rather than the granular segmentation common in 2018–2020. Andromeda and Lattice reward:\[14\]\[4\]

\- Fewer campaigns.  
\- Broad audiences and Advantage+ Audience.  
\- Multi-creative ad sets where the algorithm selects the right ad for each person.

Segmented structures (many small campaigns by interest, placement, or micro-geo) can still be useful for measurement and business logic, but they generally underperform for scale and learning.

\#\#\# 5.2 When to Separate Campaigns or Ad Sets

Justifiable segmentation axes include:

\- \*\*Objective\*\*: separate campaigns for distinct goals (e.g., Awareness video views vs Sales purchase optimization).\[8\]  
\- \*\*Geography and language\*\*: different languages, currencies, or pricing sometimes need separate funnels; keep geos mutually exclusive per campaign when possible.  
\- \*\*Placement-specific creative\*\*: if you have Reels-native creative versus static feed creative, separate ad sets or campaigns for clean testing is sensible.\[40\]  
\- \*\*Spend control by business line\*\*: when internal budgeting mandates fixed allocations (e.g., brand vs performance budgets).

Avoid splitting purely by small interest differences or minor demographic tweaks unless you have very large budgets.

\#\#\# 5.3 Naming Conventions

Consistent naming conventions do not affect performance but are critical for scaling and analytics. A common pattern for senior buyers is:

\- \*\*Campaign\*\*: Objective | Funnel Stage | Geo | Offer or Product (e.g., “Sales – BOFU – US – Main Catalog”).  
\- \*\*Ad Set\*\*: Audience Type | Optimization Event | Key Constraints (e.g., “Broad+LAL – Purchase – 25–55 US – EN”).  
\- \*\*Ad\*\*: Hook | Format | Creative ID (e.g., “UGC – 15s Reels – Price Anchor”).

Include dates or sprint numbers when running structured tests so historic performance is traceable.

\#\#\# 5.4 Number of Ad Sets and Ads

Meta previously recommended no more than six ads per ad set, but Andromeda’s launch and subsequent documentation updates have quietly removed that hard guidance; one widely-cited 2025 change list notes that the six-ad limit recommendation disappeared as Andromeda now benefits from larger creative libraries.\[52\]

Current practice among high-spend accounts tends to be:

\- \*\*Per campaign\*\*: 1–3 ad sets for a given geo/funnel stage (e.g., 1 broad, 1 LAL, 1 retargeting), not dozens.\[4\]\[14\]  
\- \*\*Per ad set\*\*: 4–8 meaningfully different ads, each with distinct hooks/angles, rather than dozens of tiny variants; some Advantage+ creative setups effectively allow more when using permutations.\[44\]\[52\]

\#\#\# 5.5 Testing Structures

There are three main ways to test on Meta in 2025–2026:

\- \*\*A/B Tests (Experiments)\*\*: formal split tests where Meta isolates variables (e.g., audience, creative, bidding) and provides an experiment readout; best when you need statistical rigor.\[15\]  
\- \*\*Dynamic Creative / Advantage+ Creative\*\*: feed multiple assets and copies into one ad, letting Meta assemble combinations; this is efficient for exploratory testing but makes it harder to attribute performance to specific elements.  
\- \*\*Manual ad variations\*\*: separate ads or ad sets for each hypothesis (e.g., Hook A vs Hook B), analyzed via standard metrics; offers more control but requires stricter structure and volume.

A pragmatic framework is to use manual structures to identify winning \*\*concepts\*\* (angles, offers, formats) and then use Advantage+ Creative within scale campaigns to squeeze incremental gains from formatting and personalization.\[44\]

\#\#\# 5.6 Creative Testing Framework

Effective creative testing aligns with how Andromeda and Lattice learn from diversity:

\- Test \*\*hooks\*\* (first 3 seconds for video, first line for primary text) by holding offer and format constant while varying opening frames/lines.\[22\]  
\- Test \*\*angles\*\* (value propositions, objections handled, emotional vs rational) using consistent format and CTAs.  
\- Test \*\*formats\*\* (1:1 feed video, 9:16 Reels, carousels, static image) across the same offer.  
\- Test \*\*offers\*\* (discounts, bundles, bonuses, risk reversals) once you have a proven angle.

Run tests with sufficient budget to hit at least 50–100 conversions per variant where possible to avoid overfitting noise and ensure the learning system can reliably pick winners.\[29\]\[21\]

\*\*\*

\#\# 6\. Placements & Formats

\#\#\# 6.1 Available Placement Families

Meta’s current placement taxonomy groups individual placements into categories such as Feeds, Stories & Reels, In‑Stream, Search Results, and Apps & Sites (Audience Network).\[71\]\[40\]

Key placements relevant for most advertisers include:

\- \*\*Feeds\*\*: Facebook Feed, Instagram Feed, Instagram Profile Feed, Facebook Marketplace, Facebook Video Feeds, Facebook Right Column, Instagram Explore feed, Instagram Explore home, Messenger Inbox.\[40\]  
\- \*\*Stories & Reels\*\*: Facebook Stories, Instagram Stories, Messenger Stories, Facebook Reels, Instagram Reels.\[70\]\[40\]  
\- \*\*Search Results\*\*: Facebook Search results, Marketplace search.\[70\]  
\- \*\*Apps and Sites (Audience Network)\*\*: third-party mobile apps and websites.\[71\]

Not every objective supports every placement (e.g., some lead formats and certain Instant Experience/Collection configurations are feed-only), so Ads Manager dynamically filters valid placements by objective and ad format.\[72\]

\#\#\# 6.2 Placement Performance Patterns

General patterns observed across benchmarks and practitioner reports:

\- Feeds often have the highest intent and strongest purchase performance but also the most competition and highest CPMs.\[71\]\[40\]  
\- Stories and Reels typically offer cheaper impressions and strong engagement but require native vertical creative; performance varies heavily by creative quality.\[22\]\[40\]  
\- Audience Network drives incremental reach and low CPMs but can have weaker traffic quality for some verticals; many brands exclude it for strict brand-safety reasons.\[39\]\[71\]

Advantage+ Placements lets Meta arbitrage these differences in real time; testing has repeatedly shown lower overall CPM and higher reach when using Advantage+ Placements versus pre-filtered manual sets, though lead or purchase quality must still be validated by downstream data.\[73\]\[39\]

\#\#\# 6.3 When to Use Advantage+ vs Manual Placements

Use \*\*Advantage+ Placements\*\* when:

\- Running conversion-focused campaigns with strong creative adapted to multiple aspect ratios.  
\- You want maximum reach and efficiency and have no hard brand-safety constraints.  
\- You are still gathering data and don’t yet know which placements work best.\[39\]\[40\]

Use \*\*Manual Placements\*\* when:

\- You need to exclude certain surfaces (Audience Network, In‑Stream Video) for brand-safety or regulatory reasons.\[73\]  
\- You have placement-specific creative (e.g., Reels-only creative) and want to run it in isolation.  
\- You are measuring incremental performance of new surfaces and require clean testing.

\#\#\# 6.4 Creative Format Specifications

Meta’s format specs are updated frequently; current commonly cited ranges as of 2025–2026 include:

\- \*\*Single image\*\*: JPG or PNG, at least 1080×1080 resolution, aspect ratios 1:1, 4:5, or 9:16 depending on placement. File size typically up to 30 MB.\[74\]\[75\]  
\- \*\*Carousel\*\*: 2–10 cards, each 1080×1080 (1:1) or 4:5; images up to 30 MB, videos up to 4 GB, with video durations up to 240 minutes per card.\[75\]\[76\]\[74\]  
\- \*\*Video\*\*: MP4, MOV, or GIF; minimum dimensions \~120×120, with maximum video length around 240 minutes for most placements; recommended aspect ratios are 1:1 or 4:5 for feeds and 9:16 for Stories/Reels.\[76\]\[74\]

Text limits vary slightly by placement, but common guidelines include primary text of \~125 characters before truncation, headlines up to 40–45 characters, and descriptions around 18–30 characters for carousels.\[77\]\[74\]

\#\#\# 6.5 Collection Ads and Instant Experience

Collection ads combine a hero creative (image or video) with a product grid, opening into an Instant Experience (full-screen mobile landing) when tapped.\[77\]\[22\]

Best used when:

\- You have a catalog or at least a small set of products to showcase.  
\- You want to deliver a frictionless, on-platform storefront experience before sending users off-site.

Instant Experiences can also be used standalone for immersive storytelling, lookbooks, or lead gen; they load faster than many mobile sites, which can improve conversion rates on slower connections.\[9\]

\#\#\# 6.6 Dynamic Creative vs Manual Variations

Dynamic Creative (distinct from Advantage+ Creative) allows you to upload multiple images/videos, headlines, and body texts, and Meta will automatically assemble and test combinations.\[41\]\[22\]

\- Pros: efficient testing, less manual cloning, good for accounts with limited bandwidth.  
\- Cons: less transparency into which specific element drove performance, and less control over combinations for regulated brands.

Manual variations give more precise control and analysis at the cost of setup time; many advanced buyers use manual structures for high-level concept testing and rely on Advantage+ Creative/Dynamic for ongoing micro-optimization.\[44\]

\#\#\# 6.7 Creative Fatigue and Refresh Cadence

Key fatigue signals include rising frequency, falling CTR, increasing CPC/CPA, and declining quality rankings over time. Many Andromeda-oriented guides now recommend refreshing major creatives every 1–2 weeks in high-spend ad sets and every 3–4 weeks in lower-spend ones, particularly for Reels and Stories where novelty decays quickly.\[78\]\[79\]\[50\]\[14\]

\*\*\*

\#\# 7\. Conversion Tracking & Attribution

\#\#\# 7.1 Meta Pixel and Events

The Meta Pixel remains the primary browser-based tracking mechanism for web conversions, using standard events such as \`ViewContent\`, \`AddToCart\`, \`InitiateCheckout\`, \`Purchase\`, \`Lead\`, and custom events for tailored actions. Proper implementation includes:\[80\]\[14\]

\- Installing the base pixel on all pages.  
\- Firing standard and custom events with relevant parameters (value, currency, content IDs, etc.).\[80\]  
\- Testing via Events Manager and browser helpers to ensure deduplication with CAPI where used.\[81\]

\#\#\# 7.2 Conversions API (CAPI)

Meta’s Conversions API allows server-side transmission of the same events captured by the pixel, directly from server or backend systems to Meta’s servers. Its key benefits include:\[82\]\[83\]

\- Bypassing browser restrictions, ad blockers, and iOS tracking limitations, recovering an estimated 20–30 percent of otherwise lost conversions and improving attribution accuracy.\[83\]\[78\]  
\- Enabling richer event payloads (user identifiers, LTV, product details) and improved Event Match Quality, which directly affects optimization performance.\[84\]\[17\]

Meta and multiple integration partners recommend running Pixel and CAPI together with event deduplication; server events should include \`event\_id\` matching that of the corresponding pixel events to avoid double-counting.\[85\]\[83\]

\#\#\# 7.3 App Events SDK

For apps, Meta uses App Events through native SDKs or MMP integrations to track installs and in‑app events for optimization, retargeting, and analytics. App events support:\[63\]\[86\]

\- Automatically logged events such as App Install and App Launch.  
\- Custom in‑app events (e.g., level achieved, subscription upgrade, in‑app purchases).\[63\]

These events feed App Promotion and Sales campaigns and are a prerequisite for value optimization and advanced SKAdNetwork measurement on iOS.\[18\]\[20\]

\#\#\# 7.4 Aggregated Event Measurement (AEM) – Old vs New

Historically, AEM required advertisers to select and prioritize up to eight conversion events per domain to measure iOS 14.5+ users, with only the highest-priority event reported in certain cases. In \*\*June 2025\*\*, Meta removed the eight-event limit and the manual AEM configuration UI, moving to an automatic aggregation system that operates behind the scenes.\[87\]\[81\]\[80\]

Current state (2025–2026):

\- AEM still aggregates and privacy-protects web and app events but no longer requires manual event prioritization; advertisers instead must ensure consistent event naming and robust Pixel+CAPI setups.\[88\]\[81\]  
\- Domain verification and proper event mapping remain required for accurate reporting.

\#\#\# 7.5 Attribution Windows and Settings

As of 2025–2026, Meta’s \*\*default attribution setting\*\* for most campaigns is Standard: \*\*7-day click, 1-day view, and 1-day engaged view (for video)\*\*. Other available combinations include 1-day click, 7-day click only, and variations with 1-day view.\[89\]\[90\]\[91\]\[92\]

Key distinctions:

\- The \*\*attribution setting\*\* at ad set level influences both optimization and default reporting columns; the algorithm seeks conversions that fit within that window.\[92\]  
\- The \*\*reporting window\*\* can be compared using “Compare Attribution Settings” to see how performance would look under different windows without changing delivery.\[92\]

Best-practice mappings:

\- Use 7-day click \+ 1-day view for most products with moderate consideration cycles.\[91\]\[89\]  
\- Consider 1-day click for impulse purchases or very short decision windows.\[91\]  
\- Use longer click-only windows when selling high-ticket items or B2B offers with longer decision cycles.

\#\#\# 7.6 SKAdNetwork (SKAN) for iOS App Campaigns

Apple’s SKAdNetwork framework measures app-install and post-install events in a privacy-preserving, aggregated way; Meta integrates with SKAN via App Events SDKs and partners like AppsFlyer or Adjust. Key concepts:\[93\]\[20\]

\- Conversion value schemas encode a limited set of post-install behaviors (e.g., revenue tiers, registrations) into SKAN postbacks, which Meta and MMPs then decode.\[94\]\[18\]  
\- Advertisers must enable SKAN support in Events Manager and/or MMP dashboards; iOS 16.1+ supports SKAN 4.0 with more flexible postback windows.\[95\]\[20\]

AAC/App Promotion campaigns require correct SKAN configuration for accurate iOS performance measurement.

\#\#\# 7.7 Estimated vs Actual Conversions

Post-iOS privacy and AEM changes mean that Meta often reports \*\*modeled conversions\*\* using statistical methods, especially for view-through and iOS traffic; these can differ from raw backend numbers. Discrepancies arise due to:\[88\]\[80\]

\- Limited attribution windows vs longer purchase cycles.  
\- Cross-device behavior and mismatched identifiers.  
\- Data loss from ad blockers and consent choices even with CAPI.

Best practice is to treat Meta’s numbers as \*\*channel-attributed\*\* conversions and reconcile them with backend and analytics (e.g., GA4) using blended ROAS/CPA views rather than expecting one-to-one parity.\[84\]\[88\]

\*\*\*

\#\# 8\. Reporting & Optimization Signals

\#\#\# 8.1 Core Performance Metrics

Standard performance metrics include:

\- \*\*CPM\*\* (cost per thousand impressions): primary gauge of auction competitiveness and creative/targeting efficiency.\[96\]  
\- \*\*CPC\*\* (cost per link click) and \*\*CTR\*\* (link click-through rate): measures of traffic efficiency and creative resonance; 2026 benchmarks place typical CTR between \~0.9–1.5 percent overall, higher for e‑commerce.\[78\]\[96\]  
\- \*\*CPA/CPL\*\* (cost per acquisition/lead) and \*\*ROAS\*\* (return on ad spend): primary efficiency and profitability metrics.\[97\]\[78\]  
\- \*\*Frequency\*\*: average number of impressions per user; high frequency with stagnant results often signals fatigue.\[78\]

\#\#\# 8.2 Hook and Hold Rates for Video

Advanced media buyers increasingly track:

\- \*\*Hook rate\*\*: 3-second video views divided by impressions, indicating how many people stop scrolling; low hook rates generally signal weak opening shots or first-line copy.\[78\]  
\- \*\*Hold rate\*\*: ThruPlays or longer video views divided by 3-second views, showing mid-video retention and narrative strength.\[22\]\[78\]

Improving hooks (first 1–3 seconds) and narrative arcs has outsized impact on conversion funnel performance for Reels and Stories.

\#\#\# 8.3 Ad Relevance Diagnostics

Meta replaced the old relevance score with three diagnostics: Quality Ranking, Engagement Rate Ranking, and Conversion Rate Ranking, each benchmarking your ad against others competing for the same audience.\[79\]\[15\]

\- \*\*Quality Ranking\*\*: perceived quality of your ad vs competitors (creative clarity, landing page, feedback, etc.).\[79\]\[15\]  
\- \*\*Engagement Rate Ranking\*\*: expected engagement (clicks, likes, comments, shares) vs peers.\[79\]  
\- \*\*Conversion Rate Ranking\*\*: expected conversion rate vs other ads with same optimization goal.\[15\]\[79\]

Persistent “Below average” scores in these diagnostics often correlate with higher CPMs and weaker overall efficiency.\[79\]

\#\#\# 8.4 Kill vs Let-Run Frameworks

While Meta does not prescribe hard thresholds, experienced buyers use decision rules such as:

\- Kill or pause ads with CTR significantly below account averages (e.g., \< 0.7 percent when peers are 1.5–2 percent) after sufficient impressions.\[78\]\[79\]  
\- Pause ads with “Below average” Quality and Conversion Rate rankings that also show clearly worse CPA than peers, assuming enough spend to reach significance.\[79\]  
\- Allow ads to run through learning (50+ events) before making aggressive judgments, unless performance is catastrophically bad.

The exact thresholds should be calibrated by vertical and margin structure, but the key is consistent rules tied to both cost metrics and diagnostics.

\#\#\# 8.5 Optimization Levers When CPA Is Too High (continued)  
Once you’ve checked creative and offer/landing page, senior buyers typically work through these additional levers:

Audience & structure

If CTR and on-site conversion rate are both solid, widen targeting (broader geo/age, fewer interest constraints, Advantage+ Audience) so Andromeda can find cheaper conversions.

If quality is poor (high bounce, low session depth), tighten with better exclusions, higher-intent lookalike sources, or segment out problematic placements (e.g., Audience Network) into separate tests.

Bidding & budget

Move from Highest Volume to Cost per result goal once you have a proven CPA; set the goal close to recent 7–30 day averages, not an aspirational number, or you risk under-delivery.

For strong but volatile performance, consider ROAS goal or Highest Value so Lattice can prioritize high-value buyers rather than sheer volume.

Reduce budgets on underperforming ad sets and reallocate to proven ones; avoid frequent large swings that re-trigger learning.

Attribution & measurement sanity check

Confirm you’re using an attribution setting appropriate for your buying cycle (e.g., 7-day click \+ 1-day view for most e‑com, 1-day click for impulse, longer click-only for high-ticket).

Compare Meta-attributed results with backend/KPI tools (GA4, CRM, BI) using blended views; if Meta looks expensive but blended ROAS is strong, you may be under-valuing view-through and modeled conversions.

8.6 Account Spending Limits & Payment Thresholds  
Meta enforces two different financial controls at the account level: payment thresholds and account spending limits.

Payment threshold (billing threshold)

This is the amount of cumulative spend at which Meta charges your primary payment method (e.g., charges at 2 → 5 → 25 → 50 → 250 → 500+ as trust builds).

For new accounts, thresholds start very low to manage risk; successful payments automatically increase the threshold over time, up to larger increments (e.g., \~900 units of your currency) or until you manually set a cap.

In Ads Manager → Billing → Payment settings, you can request increases or decreases to the threshold; increases may require a history of successful charges.

Account spending limit (ASL)

This is an overall cap on your account’s lifetime spend; once reached, all campaigns stop delivering until you raise or remove the limit.

You control ASL in Billing → Payment settings; useful for new clients, small businesses, or agency safety when onboarding. Meta may also apply implicit daily caps to brand-new accounts until they build a payment history.

For your internal tool, treat thresholds/limits as non-performance constraints that can mimic “delivery issues” if they are hit silently; always check billing and ASL when a healthy campaign suddenly halts.

9\. Policy & Restrictions (2025–2026)  
9.1 Special Ad Categories (SAC)  
Meta’s Special Ad Categories require stricter rules and limited targeting for sensitive verticals: Housing, Employment, Financial products and services (credit/finance), and Social issues, elections or politics.

2025 updates expanded the Finance category beyond pure credit to include broader financial services (banking, investments, insurance) under SAC rules in many markets.

When you flag a campaign as SAC, Meta automatically restricts:

Targeting (e.g., no age \<18 and often forced 18–65+, limited geographic granularity, reduced detailed targeting options; lookalikes and some interest exclusions disabled).

Delivery and optimization options for some Advantage+ features (certain SAC campaigns cannot access all Advantage+ tools per Meta and agency writeups).

Your strategy tool should explicitly prompt: “Is this Housing / Employment / Finance / Social-Political?” and, if yes, lock out non-compliant audience/bid recommendations.

9.2 Prohibited & Restricted Content (High-Level)  
Meta’s 2025 policy updates emphasize three pillars: special ad categories, content guidelines, and user privacy/first-party data compliance.

Core prohibited content areas (non-exhaustive) include:

Illegal products/services; weapons, explosives, drugs and many supplements.

Discriminatory content or targeting (race, religion, disability, etc.).

Misleading or deceptive claims, especially around health, finance, and income opportunities (including exaggerated ROI, “get rich quick”, or unsubstantiated before/after results).

Adult content, sensational or graphic imagery, and “clickbait” tactics (fake UI, deceptive CTA).

Restricted content (allowed with tight rules and often age-gating) includes alcohol, gambling/lotteries, medical/healthcare, subscription services, and political/issue ads; many require local-law disclosures and platform authorization.

9.3 Account Health, Feedback Score, and Appeals  
Meta surfaces account-level health primarily via the Account Quality / Business Portfolio Feedback Score interfaces.

The Business Portfolio Feedback Score is based on post-purchase user feedback (primarily for commerce/Shop advertisers) and can reduce delivery or increase CPMs when low.

Repeated ad rejections, disapproved assets, and policy violations accumulate at the account level and can trigger review, throttling, or bans.

Appeals: advertisers can request manual review for disapproved ads or restricted accounts via Account Quality; 2025 guidance stresses providing clear documentation (e.g., licenses, disclaimers, proof of claims) to speed reinstatement.

For a strategy tool, it’s useful to surface risk flags: high violation rates, low feedback score, or SAC misconfiguration.

9.4 Business Verification  
Meta is gradually tying more features (Shops, advanced API access, political ads, some payment methods) to Business Verification through Business Manager.

Verification typically requires official business documents, domain verification, and sometimes identity checks for admins (especially for political/issue advertisers).

Unverified businesses can still run many standard campaigns but may be blocked from certain features or see additional review friction.

Your playbook should indicate: “If advertiser wants to run issue/political ads, or use higher-risk categories at scale, ensure Business Verification is completed.”

9.5 iOS 14.5+ Impact & Current State (2025–2026)  
Initial iOS 14.5 changes (ATT, limited device IDs, delayed SKAN postbacks) led to major reporting gaps; Meta responded with Aggregated Event Measurement and modeled conversions. By 2025–2026:

The explicit “8 events per domain” AEM limit and manual prioritization UI have been removed; AEM still aggregates/protects data, but configuration is now more automatic.

Meta relies more heavily on modeled conversions and statistical attribution, especially for iOS and view-through; this makes Meta’s numbers diverge from last-click analytics but often closer to true incremental lift.

Server-side Conversions API has become de facto mandatory for serious performance advertisers to recover signal loss and feed Andromeda/Lattice high-quality data.

Any tooling you build should treat CAPI \+ Pixel \+ SKAN (for apps) as a baseline requirement, not an “advanced” option.

10\. Recent Changes & Emerging Features (2024–2026)  
10.1 Campaign Types, Objectives, and Naming  
ODAX’s six outcomes (Awareness, Traffic, Engagement, Leads, App Promotion, Sales) remain the core structure in 2025–2026, but Meta has iterated the automation and naming around Sales/App/Leads.

Key changes:

Advantage+ Shopping Campaigns have been rebranded and generalized as Advantage+ Sales Campaigns, reflecting that they are not just for “shopping” but any online purchase/transaction objective.

The creation flow has been simplified so that Sales, Leads, and App Promotion campaigns all start in a “simplified Advantage+ format” by default, with advanced/manual controls available behind additional options.

This is the context for your truncated sentence:

Between 2024 and 2025, Meta expanded Advantage+ beyond Shopping into App and Leads campaigns, simplified setup flows, and made Advantage+ Audience and Placements the default configuration for most performance-oriented Sales, App Promotion, and Leads campaigns in the standard creation flow.

10.2 Advantage+ Expansions & Changes (Completed)  
Recent evolutions of Advantage+:

Coverage expansion

Advantage+ automation now covers Sales, App, and Leads campaigns, not just e‑commerce.

Advantage+ Leads Campaigns give lead-gen advertisers a Shopping-style experience: automated targeting, placements, and budget optimization, with Meta touting \~10 percent lower cost per qualified lead when Advantage+ is enabled.

More flexible Sales campaigns

Advantage+ Shopping was renamed Advantage+ Sales, with added flexibility: more custom audience include/exclude options, multiple ad sets per campaign (not just 1), and up to 50 ads per ad set instead of a single 150-ad monolith.

The old “manual vs automated” setup toggle has been removed; new Sales campaigns always start in the Advantage+ view, and you adjust toward manual controls as needed.

Defaults and nudges

Advantage+ Audience and Advantage+ Placements are now on by default in most performance creation flows; Ads Manager surfaces “performance score” prompts that give “points” for enabling more automation (Advantage+ placements, creative, etc.).

Meta’s marketing claims \~22 percent higher ROAS for Advantage+ Sales vs manual setups when tracking and creatives are strong, though practitioner reports stress variable results by vertical and data quality.

Your tool should clearly separate: “Meta-Recommended (Advantage+ default)” vs “Manual/override structures practitioners use when Advantage+ underperforms.”

10.3 Attribution & Measurement Updates  
In addition to AEM’s eight-event removal, attribution/measurement changes since 2024 include:

Standardization of 7-day click \+ 1-day view (and engaged-view for video) as the default attribution setting in most accounts, simplifying cross-account comparisons.

More transparent reporting around modeled vs observed conversions, with “Modeled” labels and comparison tools to see performance under different attribution windows.

Closer integration of SKAN 4.0 features (multiple postbacks, coarse/fine conversion values) for app advertisers, improving early and late-funnel measurement when configured with supported MMPs.

10.4 New Creative Features and AI  
Meta has introduced a range of AI/ML creative tools tightly integrated with Advantage+ Creative:

Auto-generated text variations, headline suggestions, and image enhancements (cropping, brightness/contrast, background tweaks) as part of “Standard Enhancements” and related options.

Template-driven overlays (sale callouts, price badges) and creative “scorecards” inside Ads Manager nudging advertisers to adopt more vertical video and mobile-first layouts.

Ongoing experiments with generative AI for image variants and multi-language copy, initially rolled into Advantage+ setups and then exposed via ad-level toggles in 2025 pilots.

Meta’s position: turn on enhancements and feed lots of raw creative; practitioner consensus: use enhancements when brand guidelines allow, but keep a set of “clean” manual creatives for regulated/brand-sensitive campaigns.

10.5 Targeting Capability Changes & Privacy  
Targeting has continued to shift away from granular controls toward automation and privacy compliance:

As of March 2025, Meta retired several detailed targeting exclusions and layered filters, especially around sensitive demographics and interests, pushing advertisers toward broader audiences and event-based optimization.

Special Ad Categories now rely on “Special Ad Audiences” replacement logic and compliance tools, reducing custom targeting knobs to avoid discrimination and requiring proper declaration at setup.

Policy updates require clearer consent and documentation for customer list and lookalike audiences, including how data was collected and how consent was obtained.

Your tool should assume that micro-targeting is dying: strategy should be built around data (events/CAPI) \+ creative \+ exclusions rather than long interest stacks.

10.6 AI/ML System Upgrades: Andromeda, Lattice, GEM  
Between 2023 and 2025, Meta has rolled out several major infrastructure upgrades:

Meta Lattice (2023) unified ad ranking across placements and objectives, improving ad quality and performance by learning jointly from multiple signals (clicks, conversions, watch time, etc.).

Andromeda (2024–2025) dramatically scaled up candidate ad retrieval using advanced embeddings and retrieval architectures, allowing tens of thousands of candidate ads per impression and improving match quality by 6–8 percent in Meta’s tests.

GEM (2025) added another layer focused on conversion performance, with external analyses citing \~3–5 percent incremental conversion lift, especially on Instagram and Reels.

These systems all favor broad, consolidated structures and creative diversity; narrow, overlapping ad sets starve the models of data and options.

10.7 Deprecations & Removed Features  
Important deprecations to bake into any 2025–2026 playbook:

Manual vs Advantage+ Sales toggle removed; Sales/App/Leads flows default to Advantage+ with optional manual overrides rather than separate campaign types.

The AEM 8-event limit and manual prioritization UI have been removed; events are still aggregated but no longer require manual ranking.

Earlier “Special Ad Audiences” (lookalike-like constructs for SAC) were deprecated and replaced by broader SAC-compliant targeting logic; SAC campaigns now rely more on Advantage+ Audience under strict fairness constraints.

Several detailed targeting options and exclusion controls have been sunset or merged, especially around sensitive user attributes, further shifting power to Andromeda and Advantage+ Audience.  
