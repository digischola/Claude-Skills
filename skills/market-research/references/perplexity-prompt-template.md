# Perplexity Deep Research Mega-Prompt Template

Generates ONE comprehensive Perplexity prompt customized to each client. The goal is a strategy-grade research output that covers market analysis, strategic frameworks, competitive intelligence, and platform-specific ad benchmarks — all in a single deep research session.

## Template Structure

Replace all `{variables}` with client-specific data from Step 1. Adjust, remove, or add sections based on client needs (Google only, Meta only, or both). Add known competitor names, specific client concerns, and industry-specific sub-questions.

---

### The Mega-Prompt

```
I need a strategy-grade market research report for {business_name} ({business_url}), a {country} company specializing in {business_description}. They operate in {geographic_scope} with a focus on {primary_market}.

Their booking/purchase model is {booking_model}: {booking_model_details}. Conversion paths: {conversion_paths}. Pricing is {pricing_transparency}. {existing_ad_activity}.

This research will inform a {platform_strategy} acquisition strategy but must be grounded in deep market understanding. Provide real data, cite sources, include numbers wherever possible. {country}-specific data preferred; {fallback_region} as fallback.

1. MARKET SIZE & DEMAND

Total addressable market (TAM), serviceable addressable market (SAM), and serviceable obtainable market (SOM) for {industry} in {country}
{fallback_region} market size, revenue, CAGR, and projections (2024–2030)
Number of {relevant_transaction_type} per year in {country}, especially {primary_market}
What % of {relevant_transaction_type} involve professional {service_type} vs handled in-house?
Growth drivers: {list_3-5_industry_specific_growth_drivers}
Headwinds: {list_3-5_industry_specific_headwinds}
Commercial real estate trends (if B2B/local service): {primary_market} vacancy rates, net absorption, new lease activity — how do these correlate with demand?
Any data from {relevant_data_sources} on {industry} activity

2. PORTER'S FIVE FORCES ANALYSIS

Competitive rivalry: How many {service_type} firms operate in {country}/{primary_market}? Fragmented or consolidated? Do adjacent service providers also compete?
Threat of new entrants: Barriers to entry? (certifications, insurance, specialized equipment, enterprise trust/track record)
Threat of substitutes: How often do {buyer_type} use in-house alternatives instead of a specialist? Are there technology substitutes that eliminate the need for this service?
Buyer power: How do {buyer_type} evaluate vendors? RFP processes, vendor panels, preferred supplier lists? Strong negotiating leverage?
Supplier power: Dependence on specialized labor, equipment, logistics. Ease of scaling for large projects?

3. PESTEL ANALYSIS ({country}-specific)

Political/Legal: Relevant regulations during service delivery, government procurement requirements
Economic: Interest rates, commercial activity trends, budgets in recessionary vs growth periods
Social: Workforce trends impacting demand (hybrid work, demographics, consumer behavior shifts)
Technological: Technology shifts that increase or decrease demand for this service
Environmental: Relevant environmental regulations, sustainability requirements, ESG reporting
Legal/Compliance: Insurance, liability, industry-specific compliance requirements

4. SWOT ANALYSIS FOR A {industry} SPECIALIST IN {country}

Strengths of niche positioning (specialist vs generalist)
Weaknesses (market awareness, sales cycles, revenue model challenges)
Opportunities (underserved verticals, geographic expansion, adjacent services)
Threats (technology disruption, DIY alternatives, economic conditions)

5. COMPETITIVE LANDSCAPE

Top 10-15 {service_type} companies in {primary_market} and across {country} — with location, positioning, key differentiators, approximate size
How do they position: price-focused, enterprise-only, full-service, niche specialist, bundled with adjacent services?
Which competitors are running {platform_type} Ads? What keywords, landing pages, and offers?
What lead magnets and CTAs are used? (free assessments, consultations, instant quotes)
Competitive saturation on {platform_type} for {industry} terms — crowded or underserved?
SEO presence: who ranks organically for {industry} terms in {primary_market}?
The "invisible competitor": how often is the real alternative just {diy_alternative}? What's the failure rate?

6. SEARCH DEMAND & KEYWORD LANDSCAPE

What terms do {buyer_type} search when looking for {service_type}? List all keyword clusters with approximate search volumes.
CPC estimates in {country}/{primary_market}
Long-tail opportunities (e.g., "{service_type} {primary_market}", "{industry} company {city}")
Seasonal trends — when do {buyer_type} search most? (fiscal cycles, lease cycles, seasonal patterns)
Adjacent/intent-signal keywords
Negative keyword insights: what searches look relevant but aren't?

7. {PLATFORM} ADS BENCHMARKS & UNIT ECONOMICS

CPC benchmarks for {industry} and related keywords in {country}
{industry} {platform_type} ads benchmarks: CTR, conversion rate, CPL, CPA
Estimated monthly budget to capture meaningful impression share in {primary_market}
Average deal size in {currency} by {customer_segmentation}
Customer lifetime value: repeat purchase rate, referral rate?
Unit economics: cost per click → cost per lead → cost per qualified opportunity → cost per closed deal → ROI per deal
{platform_specific_questions}

8. BUYER PERSONAS & PURCHASE JOURNEY

Who makes the buying decision? (list relevant titles/roles)
Decision-making unit: who researches, who shortlists, who signs off?
Industries/segments that need this service most?
Company size segments and their typical procurement process
Key triggers: {list_4-6_purchase_triggers}
Top buyer concerns: {list_5-7_buyer_concerns}
How do buyers evaluate vendors? Typical shortlisting process?
Average sales cycle: first search → signed contract/purchase

9. CHANNEL PARTNER & REFERRAL ECOSYSTEM

Who refers {service_type} work? (list relevant referral partners)
Are there industry associations or certifications that drive trust?
Do enterprise clients use procurement platforms or vendor marketplaces?

10. UNDERSERVED MARKETS & BLUE OCEAN OPPORTUNITIES

Geographic gaps in {country} with high demand but few {service_type} specialists
Vertical gaps: segments needing this service frequently but underserved
Service gaps: adjacent services that could be bundled
Digital marketing gaps: are competitors weak on {platform_type} Ads, SEO, content, Google Business Profile?
Adjacent service opportunities for bundling

11. STRATEGIC RECOMMENDATIONS FOR {PLATFORM} ADS

Campaign structure recommendation
Priority keyword/audience groups and why
Landing page strategy
Budget allocation across campaigns
Top 3 verticals/segments to target first
Ad copy angles for {buyer_type}
Recommended conversion actions
Quick wins (0-3 months) vs medium-term (3-6) vs long-term (6-12)

Format: Clear headers, data tables where appropriate, cite all sources with URLs. Include a summary matrix or scorecard where possible.

Research quality rules:
- For every statistic or number, include exact source name, date, and URL. If no verifiable source, say "No reliable data found" rather than estimating.
- Clearly distinguish between {primary_market}-specific data, {country}-wide data, and global data. Do not present {fallback_region} benchmarks as if they apply to {country} without caveat.
- If a question cannot be answered with available data, say so directly and explain what the closest available data point is.
- For the strategic recommendation section, label each recommendation as either "data-supported" (backed by specific numbers above) or "directional" (informed opinion based on patterns but no hard number).
```

---

## Customization Guidelines

When generating this prompt for a specific client:

1. **Replace all {variables}** with actual client data from Step 1
2. **Set platform strategy** based on client needs:
   - Google Ads only → sections 6, 7, 11 focus on search/keywords
   - Meta Ads only → sections 6, 7, 11 focus on audience/creative/CPM
   - Both platforms → include benchmarks for both in sections 7 and 11
3. **Adjust catchment/scope** based on business type:
   - Restaurant/cafe: 5-10km local
   - Retail store: 10-20km local
   - Service business: 15-30km or city-wide
   - B2B services: city/province/national
   - Online/e-commerce: country or international
   - Wellness/retreat: 50-100km+ or national/international
4. **Add industry-specific sub-questions** under relevant sections:
   - Restaurants: dietary trends, delivery platforms, peak dining times
   - Wellness/yoga: certification requirements, retreat vs studio, enrollment cycles
   - B2B services: RFP processes, procurement cycles, compliance requirements
   - Healthcare: regulatory compliance, patient data handling
5. **Seed known competitors** — if user knows competitor names, add them to section 5
6. **Remove irrelevant sections** — if purely online, trim local market. If no referral ecosystem, drop section 9.
7. **Add client's specific concerns** — weave any questions or worries from the client brief into the relevant sections
8. **Set booking model context** — inject the booking model from business-analysis wiki:
   - `DIRECT_BOOKING` → "Guests book and pay online via {booking_url}. Funnel benchmarks should reflect direct conversion, not lead gen."
   - `ENQUIRY_ONLY` → "No online booking. Guests submit enquiry forms; staff follow up. Funnel benchmarks should reflect lead gen / enquiry conversion."
   - `HYBRID` → "Some offerings are directly bookable; others are enquiry-only. Specify which. Benchmarks should cover both funnels."
   - `UNKNOWN` → "Booking model is unverified. Research should consider both direct booking and enquiry-only funnel models."
   Also inject conversion paths, pricing visibility, and existing ad activity. These shape Sections 7 (funnel), 8 (buyer journey), and 11 (strategy).

---

## Platform-Specific Variants

### Meta Ads Only — Section 6 & 7 Replacements

**Use these sections INSTEAD OF the standard Section 6 and Section 7 when the client is Meta Ads only.** The standard sections focus on search keywords and CPC benchmarks, which are irrelevant for Meta-only campaigns. Swap them out completely — do not blend.

#### Section 6 Meta Variant — "Meta Ads Audience & Targeting"

Replace Section 6 ("Search Demand & Keyword Landscape") with:

```
6. META ADS AUDIENCE & TARGETING

What are the primary audience demographics for {business_type} in {geography}? (age, gender, income, education)
What interest categories and behaviors would reach {buyer_type} on Meta platforms?
What custom audience strategies work for {business_type}? (website visitors, email lists, app users, engagement audiences)
What lookalike audience seeds perform best for {business_type}?
What audience size ranges are typical for {geography} + {business_type} targeting?
What audience exclusions are critical? (existing customers, irrelevant demographics)
```

#### Section 7 Meta Variant — "Meta Ads Benchmarks & Creative Performance"

Replace Section 7 ("{PLATFORM} Ads Benchmarks & Unit Economics") with:

```
7. META ADS BENCHMARKS & CREATIVE PERFORMANCE

What are current CPM ranges for {business_type} in {geography} on Meta?
What CTR benchmarks exist for {ad_format} in {industry}?
What creative formats drive lowest CPA for {business_type}? (Reels, Stories, Carousel, Static)
What is the typical funnel: impression → click → landing page → {conversion_action}? What are conversion rate benchmarks at each stage?
What is the average CAC/CPA for {business_type} acquiring {customer_type} via Meta Ads?
What creative fatigue patterns exist? (frequency caps, refresh cadence)
```

### Google Ads Only — No Changes Needed

The standard Section 6 (Search Demand & Keywords) and Section 7 ({PLATFORM} Ads Benchmarks) are already Google-focused. Use them as-is.

---

### Both Platforms (Google + Meta) — Section 6 & 7 Replacements

**Use these sections INSTEAD OF the standard Section 6 and Section 7 when the client needs BOTH Google Ads and Meta Ads.** These combine search keyword research with audience targeting, and Google benchmarks with Meta benchmarks, in a single prompt.

#### Section 6 Both Variant — "Search Demand & Audience Targeting"

Replace Section 6 with:

```
6. SEARCH DEMAND & AUDIENCE TARGETING (GOOGLE + META)

GOOGLE ADS — Search Demand:
What terms do {buyer_type} search when looking for {service_type}? List all keyword clusters with approximate search volumes.
CPC estimates in {country}/{primary_market}
Long-tail opportunities (e.g., "{service_type} {primary_market}", "{industry} company {city}")
Seasonal search trends — when do {buyer_type} search most?
Negative keyword insights: what searches look relevant but aren't?

META ADS — Audience Targeting:
What are the primary audience demographics for {business_type} in {geography}? (age, gender, income, education)
What interest categories and behaviors would reach {buyer_type} on Meta platforms?
What custom audience strategies work for {business_type}? (website visitors, email lists, engagement audiences)
What lookalike audience seeds perform best for {business_type}?
What audience size ranges are typical for {geography} + {business_type} targeting?
What audience exclusions are critical?
```

#### Section 7 Both Variant — "Platform Benchmarks & Unit Economics (Google + Meta)"

Replace Section 7 with:

```
7. PLATFORM BENCHMARKS & UNIT ECONOMICS (GOOGLE + META)

GOOGLE ADS Benchmarks:
CPC benchmarks for {industry} keywords in {country}
{industry} Google Ads benchmarks: CTR, conversion rate, CPL, CPA
Estimated monthly budget to capture meaningful impression share in {primary_market}
Quality Score expectations for {industry} keywords

META ADS Benchmarks:
Current CPM ranges for {business_type} in {geography}
CTR benchmarks by ad format (Reels, Stories, Carousel, Static)
What creative formats drive lowest CPA for {business_type}?
Creative fatigue patterns — frequency caps, refresh cadence

SHARED Unit Economics:
Average deal size / order value in {currency} by {customer_segmentation}
Customer lifetime value: repeat rate, referral rate
Full funnel: cost per click → cost per lead → cost per qualified opportunity → cost per closed deal → ROI
How do Google Ads and Meta Ads compare on CPA and ROAS for {industry}? Which channel typically drives higher intent vs higher volume?
Recommended budget split between Google and Meta for {industry} (with rationale)
```

---

## Quality Check Before Sending

The generated prompt should:
- Be specific enough to return actionable data (not generic industry overviews)
- Include the business URL for site analysis
- Name specific data sources to check (CBRE, JLL, Stats Canada, IBISWorld, etc.)
- Request numbers and benchmarks, not just qualitative descriptions
- Include format instructions to keep output structured
- Have the research quality rules at the end (source citing, geographic specificity, data-supported vs directional labels)
- Cover the correct platform(s) based on client needs
