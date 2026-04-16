# Guided Strategy Questions Framework

Ask 3-5 questions before building strategy. Questions are NOT generic — they're selected based on platform choice, business type, and what's already known from the wiki. The goal is to fill strategy-critical gaps, not repeat what the research already answered.

---

## Question Selection Logic

```
1. Read wiki data → identify what's already known
2. Check platform selection → load platform-specific questions
3. Check business type → load business-type-specific questions
4. Select 3-5 questions from the pool that fill the BIGGEST gaps
5. Present as AskUserQuestion with clear options
```

**Rule:** Never ask a question the wiki already answers. If the wiki has competitor data, don't ask "who are your competitors?" If the wiki has buyer personas, don't ask "who is your target audience?"

---

## Universal Questions (Select 1-2)

### Q1: Conversion Maturity
**Ask when:** Wiki doesn't specify what conversion actions are currently tracked, or the business is new to ads.

"What conversion tracking is currently in place?"
- A) Full tracking (Pixel/tag, server-side, offline import) — we're optimizing
- B) Basic tracking (Pixel/tag only, no server-side) — needs improvement
- C) Minimal/none — needs full setup before launch
- D) Not sure — I need help assessing

**Why it matters:** Determines bidding strategy (can't run Smart Bidding without conversion data), platform recommendations (Meta requires CAPI for reliable tracking post-iOS 14.5), and whether a tracking setup phase is needed before strategy.

### Q2: Account History
**Ask when:** Unknown whether this is a new account or existing.

"Is this a new ad account or are there existing campaigns?"
- A) Brand new account, never run ads before
- B) Existing account with historical data but underperforming
- C) Existing account performing OK, want to scale/restructure
- D) Pausing current campaigns, starting fresh strategy

**Why it matters:** Existing account data changes everything — bidding targets, audience seeds, creative benchmarks, and what's already been tested. New accounts start in Phase 1; existing accounts might skip straight to Phase 2.

### Q3: Growth Priority
**Ask when:** Budget is specified but priorities aren't clear.

"What's the primary growth priority for the next 90 days?"
- A) Volume — get as many leads/sales as possible, efficiency secondary
- B) Efficiency — improve CPA/ROAS, willing to sacrifice some volume
- C) Scale — currently profitable, want to spend more while maintaining returns
- D) Testing — trying paid ads as a new channel, need proof of concept

**Why it matters:** Directly determines bidding strategy, budget allocation, and how aggressive the phased plan should be.

---

## Google Ads-Specific Questions (Select 1-2 when Google is in scope)

### Q4: Keyword Landscape Knowledge
**Ask when:** Wiki has keyword data from market research but no campaign history.

"For Google Search, do you have a sense of which keywords are most valuable?"
- A) Yes, I know the high-intent terms and have keyword research data
- B) Market research identified clusters but I haven't validated in Google Ads yet
- C) No idea — need keyword strategy from scratch
- D) Currently running Search campaigns — I can share search term reports

**Why it matters:** If keyword data exists from market-research wiki, we build on it. If search term reports exist, we can skip discovery and go straight to optimization.

### Q5: PMax Readiness
**Ask when:** E-commerce or lead gen with enough expected volume.

"For Performance Max, do you have these assets ready?"
- A) Product feed (Merchant Center) + images + videos + text — ready to go
- B) Product feed + images, no video — can launch partial
- C) No product feed, but have images and text — PMax without Shopping
- D) Not planning to use PMax

**Why it matters:** PMax with a feed is fundamentally different from PMax without. Asset availability determines campaign type selection and creative direction.

### Q6: Search Brand Protection
**Ask when:** Business has an established brand name or competitors might bid on it.

"Are competitors bidding on your brand name in search?"
- A) Yes, it's a problem — we need brand protection campaigns
- B) Not sure — haven't checked
- C) No, our brand is too niche/new for competitor conquesting
- D) We don't want to bid on our own brand name

**Why it matters:** Brand Search campaigns are cheap insurance. If competitors are bidding on the brand, it's mandatory. If not, it's still recommended but lower priority.

---

## Meta Ads-Specific Questions (Select 1-2 when Meta is in scope)

### Q7: Creative Asset Availability
**Ask when:** Wiki doesn't specify creative capabilities.

"What creative assets are available or can be produced for Meta Ads?"
- A) Video production capability (can produce short-form, UGC, product demos)
- B) Static images only (product photos, branded graphics)
- C) Mix of existing assets — some video, some static, need to audit
- D) Starting from zero — need creative direction before production

**Why it matters:** Meta's algorithm heavily rewards creative diversity and video (especially Reels). Creative availability determines campaign structure, placement strategy, and whether a creative production phase is needed.

### Q8: Audience Data Assets
**Ask when:** Wiki has persona data but doesn't specify existing audience lists.

"What first-party audience data do you have for Meta targeting?"
- A) Customer email list (1,000+ contacts) for Custom Audiences and Lookalikes
- B) Website has significant traffic (1,000+ monthly visitors) for Pixel audiences
- C) Both email list and website traffic
- D) Neither — starting from scratch with interest targeting and broad

**Why it matters:** First-party data quality determines whether we can use Lookalike audiences (which outperform interest targeting) and how strong our retargeting pool is. No data = broad targeting + creative-led strategy.

### Q9: Advantage+ Qualification
**Ask when:** E-commerce / DTC with purchase objective.

"How many purchases or conversions does the business get per week (from all sources, not just ads)?"
- A) 50+ per week — consistent volume
- B) 20-49 per week — moderate but growing
- C) Under 20 per week — still building
- D) Not sure / haven't tracked this

**Why it matters:** Advantage+ Shopping Campaigns (ASC) need ~50 weekly conversions to work well. Below that threshold, manual Sales campaigns with higher-funnel optimization events are more effective.

---

## Business-Type-Specific Questions

### Local Service Business (restaurant, wellness, salon, etc.)
**Ask:** Q1 (conversion maturity), Q3 (growth priority), plus:

"What's the primary action you want customers to take?"
- A) Call the business / book an appointment
- B) Visit the physical location
- C) Fill out a contact form
- D) Make an online purchase/booking

### B2B / High-Consideration
**Ask:** Q2 (account history), Q3 (growth priority), plus:

"How long is the typical sales cycle from first touch to closed deal?"
- A) Same day / under 1 week (transactional)
- B) 1-4 weeks (considered but not complex)
- C) 1-3 months (complex, multi-touch)
- D) 3+ months (enterprise, requires nurturing)

### E-commerce / DTC
**Ask:** Q1 (conversion maturity), Q9 (Advantage+ qualification), plus:

"What's the average order value (AOV) and customer lifetime value (LTV)?"
- A) AOV under $50, LTV 1-2x AOV (single purchase typical)
- B) AOV $50-200, moderate repeat purchase rate
- C) AOV $200+, high LTV with repeat purchases or subscriptions
- D) Subscription model — monthly recurring revenue

### App Install
**Ask:** Q1 (conversion maturity), Q3 (growth priority), plus:

"What's the monetization model for the app?"
- A) Freemium (free install, paid upgrade)
- B) Subscription (free trial → paid)
- C) In-app purchases
- D) Paid upfront download
- E) Ad-supported (free app with ads)

---

## How to Present Questions

Use AskUserQuestion tool with multiple-choice format. Present 3-5 questions maximum in a single batch. Frame the context briefly: "Based on the market research for {business}, I need a few strategy inputs before building the plan."

After receiving answers, map each answer to strategy implications and proceed to Step 3.
