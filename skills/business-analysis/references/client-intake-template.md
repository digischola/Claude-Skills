# Client Intake Template

Structured questions to gather data that doesn't live on the website. Use during Step 5 of the business analysis flow.

---

## How to Use

Present these questions to the user (not the client directly). The user (Mayank) provides answers based on client conversations, emails, briefs, or direct knowledge. Not every question will have an answer — mark unknowns as BLANK.

Questions are grouped by priority. **Essential** questions block downstream work. **Important** questions improve quality. **Nice-to-have** enrich context.

---

## Essential (Must Have Before Proceeding)

### Business Basics
- Business name (as they want it displayed in marketing)
- Primary website URL
- Business type/industry
- Geographic location(s)
- Target geographic scope for ads (local radius, city, state, national, international)

### Campaign Scope
- Platform preference: Meta Ads, Google Ads, or both?
- Which offering(s) to focus campaigns on?
- Monthly ad budget range (or "TBD")
- Campaign timeline: launching when?

### Goals
- Primary objective: leads, sales, awareness, foot traffic, event registrations, donations?
- What does success look like? (specific KPIs if they have them)
- Any hard constraints? (industries to avoid targeting, messaging restrictions, compliance requirements)

---

## Important (Significantly Improves Output Quality)

### Competitive Context
- Known competitors (names, URLs if possible)
- How does the client see themselves vs competitors? (cheaper, premium, more specialized, etc.)
- Any competitors they explicitly don't want to be compared to?

### Past Marketing History
- Have they run Meta/Google Ads before? Results?
- Current or past agency? Why switching?
- What's worked well in the past? What hasn't?
- Existing creative assets (videos, photos, design files)?

### Audience Knowledge
- Who is their current customer? (demographics, psychographics they know from experience)
- Common objections they hear from prospects
- How do customers typically find them now? (word of mouth, search, social, referrals)

---

## Nice-to-Have (Enriches Context)

### Business Stage & Trajectory
- Years in operation
- Revenue range or growth trajectory (if shared)
- Seasonal patterns in their business
- Upcoming launches, events, or changes

### Brand Preferences
- Tone they want in ads (professional, casual, spiritual, luxury, etc.)
- Messaging they like or dislike (examples from other brands)
- Any brand guidelines or assets beyond the website?

### Technical Setup
- Pixel/conversion tracking already installed?
- Google Analytics or other tracking in place?
- CRM or booking system used?
- Landing pages: existing or need to be built?

---

## Recording Answers

All intake data goes into `_engine/wiki/business.md` under appropriate sections. Tag each answer:
- [EXTRACTED] if directly stated by client (quote or paraphrase from brief/call)
- [INFERRED] if interpreted from context (e.g., "client mentioned high-end clientele, inferring premium positioning")
- BLANK with reason if not discussed yet

Update `_engine/wiki/offerings.md` with any offering-specific intake data (campaign priority, budget allocation per offering, etc.).
