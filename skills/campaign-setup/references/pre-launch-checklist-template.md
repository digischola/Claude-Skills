# Pre-Launch Verification Checklist Template

Fill-in template for `{client}/campaign-setup/pre-launch-checklist.md` (lives inside the bundle at the client/program folder root). Every item must be checked before campaigns move from Paused → Enabled. A single unchecked item = do not launch.

Rule: the client or account owner signs the final section. The checklist is the audit trail.

---

# {{CLIENT_NAME}} — Pre-Launch Checklist

**Prepared:** {{DATE}}
**Reviewer:** {{ANALYST_NAME}}
**Account:** {{GOOGLE_CID}} / {{META_AD_ACCOUNT_ID}}
**Campaigns covered:** {{CAMPAIGN_LIST}}

---

## 0. Placeholder Tokens (must be resolved before launch)

Every `<REPLACE_ME_*>` token in the generated CSVs is listed here. Campaigns cannot launch with any of these unresolved.

- [ ] `<REPLACE_ME_GOOGLE_CID>` — Google Ads Customer ID (format XXX-XXX-XXXX)
- [ ] `<REPLACE_ME_META_AD_ACCOUNT_ID>` — Meta Ad Account ID
- [ ] `<REPLACE_ME_META_PIXEL_ID>` — Meta Pixel ID
- [ ] `<REPLACE_ME_META_PAGE_ID>` — Facebook Page ID
- [ ] `<REPLACE_ME_META_INSTAGRAM_ID>` — Instagram Account ID (if IG placements)
- [ ] `<REPLACE_ME_CONVERSION_ACTION_{EVENT}>` — exact Google conversion action name(s)
- [ ] `<REPLACE_ME_INSTANT_FORM_ID>` — Meta Instant Form ID (if lead gen)
- [ ] `<REPLACE_ME_LANDING_URL>` — final landing page URL(s)
- [ ] `<REPLACE_ME_CUSTOM_AUDIENCE_{NAME}>` — each custom audience referenced
- [ ] `<REPLACE_ME_ASSET_HASH_{ID}>` — each Meta image hash / video ID (see creative manifest)
- [ ] `<REPLACE_ME_PHONE>` — call extension phone number
- [ ] `<REPLACE_ME_ADDRESS>` — location extension business address

(Only the tokens actually present in this client's CSVs should appear above. Delete the rest.)

---

## 1. Tracking Infrastructure

### Google Ads
- [ ] GA4 property exists, measurement ID confirmed
- [ ] GA4 ↔ Google Ads linked (Admin → Product Links)
- [ ] Google Ads conversion action(s) created and status = Recording Conversions
- [ ] Test conversion fired from a staging form or URL tagger in last 48h
- [ ] Enhanced Conversions enabled for web (if applicable)
- [ ] Auto-tagging ON at account level (gclid passed)

### Meta Ads
- [ ] Meta Pixel installed on landing page (verified via Meta Pixel Helper Chrome extension)
- [ ] Conversions API (CAPI) active — server-side events flowing
- [ ] Event Match Quality ≥ 6.0 for Lead / Purchase events
- [ ] Custom Conversions set up for each funnel step (if used)
- [ ] Pixel ID matches CSV Pixel ID column
- [ ] Aggregated Event Measurement (AEM) — all web events configured, priority order set
- [ ] Domain verified in Business Manager (required for AEM)

### Offline / CRM
- [ ] Pipedrive / HubSpot / CRM webhook tested with sample lead
- [ ] UTM parameters flow into CRM contact record
- [ ] Lead attribution field populated on test record
- [ ] Offline conversion upload schedule agreed (daily / weekly)

---

## 2. Account Settings

### Google Ads
- [ ] Billing set up, payment method verified
- [ ] Account currency = {{CURRENCY}}
- [ ] Account time zone = {{TIMEZONE}}
- [ ] Default attribution model set (recommended: Data-driven, fallback Position-based)
- [ ] Auto-apply recommendations DISABLED (prevents Google changing bids/copy)
- [ ] My Client Center (MCC) link approved if agency-managed

### Meta Ads
- [ ] Billing method verified (credit card or direct debit)
- [ ] Account spend limit set (safety cap)
- [ ] Account currency = {{CURRENCY}}
- [ ] Account time zone = {{TIMEZONE}}
- [ ] Attribution setting chosen (1-day click default; 7-day click for consideration campaigns)
- [ ] Ad account roles: analyst has Advertiser or Admin access
- [ ] Business Manager ownership confirmed

---

## 3. Campaign-Level Verification

For each campaign, confirm (copy block per campaign):

### Campaign: {{CAMPAIGN_NAME}}
- [ ] Name matches naming convention `{REGION}_{BRAND_FLAG}_{TYPE}_{AUDIENCE}`
- [ ] Daily budget matches media-plan.csv: ${{BUDGET}}
- [ ] Bid strategy matches strategy: {{BID_STRATEGY}}
- [ ] Target CPA / ROAS values match media plan (if used)
- [ ] Locations correct — includes {{INCLUSIONS}}, excludes {{EXCLUSIONS}}
- [ ] Languages set
- [ ] Networks (Google): Search only or Search + Partners per strategy
- [ ] Placements (Meta): Advantage+ or manual list per strategy
- [ ] Schedule: 24/7 or day-parted per strategy
- [ ] Start date, end date set
- [ ] Tracking template / URL Tags populated with UTMs
- [ ] Status = Paused on import (enable after review)

---

## 4. Ad Group / Ad Set Verification

For each ad group (Google) or ad set (Meta):

### Ad Group / Ad Set: {{NAME}}
- [ ] Under correct parent campaign
- [ ] Keywords (Google) / Targeting (Meta) matches strategy
- [ ] Bid overrides set where needed
- [ ] Negative keywords applied (Google) — see shared list section below
- [ ] Audience exclusions applied (Meta)
- [ ] Optimization goal matches objective (Meta): LEAD_GENERATION, CONVERSIONS, etc.
- [ ] Conversion event selected on ad set (Meta)
- [ ] Custom Audiences exist in ad account (Meta) — names match CSV exactly

### Shared Negative Keywords (Google)
- [ ] Shared negative list created at account level
- [ ] Attached to all Non-Brand campaigns
- [ ] Brand terms excluded from Non-Brand campaigns
- [ ] Competitor names added if ad policy allows bidding

---

## 5. Creative Verification

### Google RSAs
- [ ] Each ad group has at least 1 RSA
- [ ] RSAs have 10+ headlines, 3+ descriptions
- [ ] Character limits respected: 30 (headlines) / 90 (descriptions) / 15 (paths)
- [ ] At most 2 pinned headlines per position
- [ ] Final URL resolves (HTTP 200) and is HTTPS
- [ ] Landing page matches ad promise (headline → hero match)
- [ ] UTM parameters append correctly (test by clicking live preview)
- [ ] Sitelinks, callouts, structured snippets attached
- [ ] Ad Strength ≥ "Good" (aim for Excellent)

### Meta Ads
- [ ] All image hashes / video IDs resolved (no `<PENDING_UPLOAD>` in CSV)
- [ ] Both 1:1 and 9:16 creative variants uploaded (for Advantage+ Placements)
- [ ] Primary Text ≤ 125 chars for above-the-fold rendering
- [ ] Headline ≤ 27 chars for mobile rendering
- [ ] Description ≤ 27 chars
- [ ] Link URL resolves (HTTP 200) and loads in under 3 seconds on 4G
- [ ] CTA button matches landing page intent (LEARN_MORE for brochure, SIGN_UP for waitlist)
- [ ] Page ID correct, Instagram Account ID correct
- [ ] Preview Link reviewed for each ad — no truncation, no broken formatting

---

## 6. Extensions / Assets

### Google
- [ ] Minimum 4 sitelinks per campaign, each with 1-2 descriptions and a valid URL
- [ ] Minimum 4 callouts per campaign
- [ ] Minimum 1 structured snippet set (3+ values)
- [ ] Call extension: phone number verified via Google Ads UI (requires pin code for some countries)
- [ ] Location extension linked to verified Google Business Profile
- [ ] Image extensions (if used): ≥3 images, 1200×1200 square and 1200×628 landscape

### Meta
- [ ] Advantage+ Creative enhancements decision made (ON only if exact copy control not required)
- [ ] Dynamic Creative OFF unless specifically testing

---

## 7. Landing Page

- [ ] URL resolves over HTTPS
- [ ] Mobile Lighthouse score ≥ 70 on Performance, ≥ 90 Accessibility
- [ ] Core Web Vitals: LCP < 2.5s, INP < 200ms, CLS < 0.1
- [ ] Form submission tested end-to-end (lead appears in CRM)
- [ ] Thank-you page (or in-page confirmation) fires conversion event
- [ ] UTM parameters captured in form hidden fields and saved to CRM
- [ ] Privacy policy link visible and valid
- [ ] Terms & conditions / compliance disclaimers present (finance, health, real estate)

---

## 8. Budget & Pacing Controls

- [ ] Daily budgets sum to monthly cap agreed with client: ${{MONTHLY_CAP}}
- [ ] Budget alerts configured at 80% and 100% monthly spend
- [ ] Delivery schedule matches campaign start/end dates
- [ ] Ad account spend limit set as hard ceiling
- [ ] Shared budget considered if multiple campaigns share pacing

---

## 9. Final Sign-Off

Block launch until both checkboxes confirmed in writing:

- [ ] **Client approval:** Campaigns reviewed by {{CLIENT_CONTACT}} on {{DATE}}, approved to launch.
- [ ] **Analyst approval:** All items above verified by {{ANALYST_NAME}} on {{DATE}}, zero unresolved placeholders.

**Launch authorized:** ☐ Yes, enable campaigns per launch-runbook.md
**Launch authorized:** ☐ Not yet — open items: {{LIST}}

---

## Appendix: Rollback Plan

If anything looks wrong in the first 24h:
1. Pause all campaigns at account level (Google: account status; Meta: pause all)
2. Export current account state as backup
3. Review flagged issue against this checklist
4. Re-import corrected CSV from `{client}/campaign-setup/`
5. Re-run this checklist for corrected entities only
