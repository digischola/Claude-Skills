# Meta Ads Manager — Bulk Import Schema

Reference for Meta's bulk import Excel/CSV template. Meta's bulk import is less mature than Google Ads Editor and has sharp edges — this file documents what works, what breaks, and when to fall back to manual build.

**Critical rule:** Creative assets (images, videos) must be uploaded to the Asset Library BEFORE the bulk import runs. The CSV references them by Image Hash or Video ID — you cannot upload creative through the bulk import flow itself.

**Universal status values:** `ACTIVE`, `PAUSED`, `DELETED`, `ARCHIVED`. Default to `PAUSED` on import.

---

## 1. Bulk Import CSV (`meta-bulk-import.csv`)

Single CSV with three row types distinguished by the `Level` column: Campaign, Ad Set, Ad. Rows for a given entity must appear AFTER the parent entity row (campaign → ad set → ad).

### Campaign-level columns

| Column | Type | Required | Example | Notes |
|---|---|---|---|---|
| Campaign ID | string | ⚪ | | Leave blank for new campaigns; populated on re-import |
| Campaign Name | string | ✅ | `RetreatHouse_Leads_Investor_AU` | Unique within ad account |
| Campaign Status | enum | ✅ | `PAUSED` | ACTIVE, PAUSED, DELETED, ARCHIVED |
| Campaign Objective | enum | ✅ | `OUTCOME_LEADS` | Values: OUTCOME_AWARENESS, OUTCOME_TRAFFIC, OUTCOME_ENGAGEMENT, OUTCOME_LEADS, OUTCOME_APP_PROMOTION, OUTCOME_SALES |
| Buying Type | enum | ⚪ | `AUCTION` | AUCTION (default) or RESERVED |
| Campaign Budget Optimization | enum | ⚪ | `ADVANTAGE_CAMPAIGN_BUDGET` | Enables CBO. Blank = ad-set-level budget |
| Campaign Daily Budget | decimal | ⚪ | `50.00` | Required if CBO enabled |
| Campaign Lifetime Budget | decimal | ⚪ | | Alternative to daily budget |
| Campaign Bid Strategy | enum | ⚪ | `LOWEST_COST_WITHOUT_CAP` | LOWEST_COST_WITHOUT_CAP (default), LOWEST_COST_WITH_BID_CAP, COST_CAP, LOWEST_COST_WITH_MIN_ROAS |
| Special Ad Categories | multi | ⚪ | | Values: CREDIT, EMPLOYMENT, HOUSING, ISSUES_ELECTIONS_POLITICS, ONLINE_GAMBLING_AND_GAMING. Comma-separated |
| Campaign Start Time | datetime | ⚪ | `2026-04-20 09:00:00` | Account timezone |
| Campaign Stop Time | datetime | ⚪ | | |

### Ad Set-level columns

| Column | Type | Required | Example | Notes |
|---|---|---|---|---|
| Ad Set ID | string | ⚪ | | Blank for new |
| Ad Set Name | string | ✅ | `Operators_NSW_QLD_InterestBroad` | Unique within campaign |
| Ad Set Status | enum | ✅ | `PAUSED` | |
| Ad Set Daily Budget | decimal | ⚪ | `20.00` | Blank if campaign uses CBO |
| Ad Set Lifetime Budget | decimal | ⚪ | | |
| Ad Set Start Time | datetime | ⚪ | | |
| Ad Set End Time | datetime | ⚪ | | Required if lifetime budget |
| Optimization Goal | enum | ✅ | `LEAD_GENERATION` | Values depend on objective. Common: LINK_CLICKS, LANDING_PAGE_VIEWS, CONVERSIONS, LEAD_GENERATION, OFFSITE_CONVERSIONS, THRUPLAY, REACH, IMPRESSIONS |
| Billing Event | enum | ⚪ | `IMPRESSIONS` | IMPRESSIONS (default) or LINK_CLICKS or THRUPLAY |
| Bid Amount | decimal | ⚪ | | Required if bid cap / cost cap strategy |
| Destination Type | enum | ⚪ | `WEBSITE` | WEBSITE, APP, MESSENGER, INSTAGRAM_DIRECT, PHONE_CALL, ON_AD (for lead gen instant forms), ON_PAGE |
| Conversion Location | enum | ⚪ | `WEBSITE` | |
| Conversion Event | string | ⚪ | `Lead` | Standard event name or custom event (e.g., `Lead`, `Purchase`, `CompleteRegistration`, or custom conversion ID) |
| Pixel ID | string | ⚪ | `123456789012345` | Required for website conversions |
| Custom Audiences | multi | ⚪ | `Website_Visitors_30d;Customer_List_Investors` | Semicolon-delimited audience names (must exist in ad account) |
| Excluded Custom Audiences | multi | ⚪ | `Existing_Customers` | |
| Lookalike Audiences | multi | ⚪ | `LAL_1pct_Purchasers_AU` | |
| Age Min | int | ⚪ | `30` | Default 18 |
| Age Max | int | ⚪ | `65` | Default 65 |
| Genders | multi | ⚪ | `All` | `All`, `Male`, `Female` |
| Countries | multi | ⚪ | `AU` | ISO country codes, semicolon-delimited |
| Regions | multi | ⚪ | `New South Wales;Queensland` | Meta region names or IDs |
| Cities | multi | ⚪ | | |
| Location Types | multi | ⚪ | `home;recent` | `home`, `recent`, `travel_in` |
| Interests | multi | ⚪ | `Short-term rentals;Accommodation;Real estate investing` | Meta's interest taxonomy. Interest IDs more reliable than names |
| Behaviors | multi | ⚪ | `Small business owners` | |
| Demographics | multi | ⚪ | | Education, job title, relationship status, etc. |
| Detailed Targeting Expansion | enum | ⚪ | `EXPANSION_ALL` | EXPANSION_ALL (default), EXPANSION_NONE |
| Advantage+ Audience | enum | ⚪ | `OPT_OUT` | OPT_IN or OPT_OUT. Default depends on objective |
| Placements | multi | ⚪ | `Advantage+ Placements` | `Advantage+ Placements` (default recommended) OR manual list like `Facebook Feed;Instagram Feed;Instagram Reels;Facebook Reels;Facebook Stories;Instagram Stories;Facebook Right Column;Audience Network` |
| Devices | multi | ⚪ | `mobile;desktop` | |
| Languages | multi | ⚪ | `English` | |
| Frequency Cap | string | ⚪ | | `{impressions}_in_{days}` format — e.g., `2_in_7` for awareness campaigns |

### Ad-level columns

| Column | Type | Required | Example | Notes |
|---|---|---|---|---|
| Ad ID | string | ⚪ | | Blank for new |
| Ad Name | string | ✅ | `Ad_01_Oculus_74K_Hero` | Unique within ad set |
| Ad Status | enum | ✅ | `PAUSED` | |
| Creative Type | enum | ✅ | `SINGLE_IMAGE` | Values: SINGLE_IMAGE, SINGLE_VIDEO, CAROUSEL, COLLECTION, DYNAMIC_CREATIVE |
| Page ID | string | ✅ | `1234567890` | Facebook Page ID the ad runs from |
| Instagram Account ID | string | ⚪ | `17841400000000000` | Required for Instagram placements — get from Meta Business Suite |
| Body | string | ✅ | `The most architecturally awarded mobile home in Australia — and it earns $74K/yr.` | Primary text. Limit: 125 chars recommended (mobile truncation beyond 125) |
| Title | string | ⚪ | `$74K/yr Per Oculus Unit` | Headline. Limit: 27 chars mobile / 40 chars max |
| Link Description | string | ⚪ | `Free investor brochure` | Displayed under headline. Limit: 27 chars |
| Link | string | ✅ | `https://retreathouse.com.au/investors?utm_source=facebook&utm_medium=paid&utm_campaign=leads_investor` | Landing page URL with UTMs |
| Display Link | string | ⚪ | `retreathouse.com.au` | Brand-friendly URL display |
| Call to Action | enum | ✅ | `LEARN_MORE` | Values: LEARN_MORE, SIGN_UP, GET_OFFER, DOWNLOAD, APPLY_NOW, CONTACT_US, GET_QUOTE, SUBSCRIBE, BOOK_TRAVEL, SHOP_NOW, SEND_MESSAGE, WHATSAPP_MESSAGE, GET_DIRECTIONS, CALL_NOW |
| Image Hash | string | conditional | `abc123def456abc123def456abc123de` | Required if SINGLE_IMAGE. 32-char hash returned by Asset Library upload |
| Video ID | string | conditional | `987654321098765` | Required if SINGLE_VIDEO |
| Video Thumbnail URL | string | ⚪ | | Custom video thumbnail |
| Carousel Cards | multi-JSON | conditional | | For CAROUSEL — see below |
| URL Tags | string | ⚪ | `utm_source=facebook&utm_medium=paid&utm_campaign={{campaign.name}}&utm_content={{ad.name}}` | Meta's dynamic URL parameter macros |
| Instant Form ID | string | conditional | `1234567890` | Required if Destination Type = ON_AD (lead gen) |
| Preview Link | string | output | | Generated by Meta after import for review |

### Carousel Cards (if Creative Type = CAROUSEL)

Multiple cards per ad. Format as JSON-like or use separate "Carousel Card" rows depending on template version. Columns per card:
- `Card Name`
- `Image Hash` OR `Video ID`
- `Headline` (27 chars)
- `Description` (27 chars)
- `Link`
- `Call to Action`

**Minimum 2 cards, max 10 cards per carousel.**

---

## 2. Creative Upload Manifest (`creative-upload-manifest.md`)

Meta bulk import references assets by Image Hash / Video ID, but the CSV cannot upload the asset itself. Hashes are generated only AFTER upload via:
- Meta Business Suite → Ads Manager → Asset Library (manual)
- Marketing API `POST /{ad_account_id}/adimages` (developer)
- Meta Ads Editor desktop app (drag-drop)

Manifest format — one row per asset to upload:

```
| asset_id | filename | type | aspect_ratio | dimensions | file_size | campaign | ad_set | ad_name | image_hash_or_video_id | status |
|---|---|---|---|---|---|---|---|---|---|---|
| A01 | oculus_hero_1080sq.jpg | image | 1:1 | 1080×1080 | 420KB | RH_Leads_Investor | Operators_NSW_QLD | Ad_01_Hero_74K | <PENDING_UPLOAD> | TO_UPLOAD |
| A02 | oculus_story_1080x1920.jpg | image | 9:16 | 1080×1920 | 380KB | RH_Leads_Investor | Operators_NSW_QLD | Ad_01_Hero_74K | <PENDING_UPLOAD> | TO_UPLOAD |
| V01 | oculus_tour_15sec_1080sq.mp4 | video | 1:1 | 1080×1080 | 9.2MB | RH_Leads_Investor | Operators_NSW_QLD | Ad_02_Video_Tour | <PENDING_UPLOAD> | TO_UPLOAD |
```

Upload workflow:
1. User uploads each asset to Asset Library manually
2. Copy Image Hash or Video ID from Asset Library details panel
3. Paste hash/ID into manifest's `image_hash_or_video_id` column
4. Run validator to confirm all `<PENDING_UPLOAD>` tokens resolved
5. Only then run bulk CSV import

**Asset spec cheat-sheet:**
- Image max: 30MB. Recommended 1080×1080 (1:1) and 1080×1920 (9:16 for Stories/Reels)
- Video max: 4GB, 241 min. Recommended 1080×1080 MP4, H.264, 30fps, 128kbps audio
- Carousel images: all same aspect ratio (1:1 recommended)
- Always provide 1:1 AND 9:16 variants — Advantage+ Placements uses both

---

## 3. Campaign Blueprint (`campaign-blueprint.md`) — manual fallback

Meta's bulk import is known to fail silently or partially for:
- Complex targeting combinations (Detailed Targeting + Custom Audiences + Lookalikes + Exclusions)
- Special Ad Categories (Housing for real-estate = restricted targeting)
- Dynamic Creative (DCO) with many asset variants
- Instant Forms (lead gen) — Form ID must exist and match ad account
- Catalog-based campaigns (Sales objective with product sets)

Always produce a human-readable blueprint as fallback. Structure:

```
## Campaign 1: {Campaign Name}

**Objective:** {value}
**Budget:** ${amount}/day, CBO {on/off}
**Dates:** {start} → {end or "ongoing"}

### Ad Set 1.1: {Ad Set Name}
- Optimization goal: {value}
- Conversion event: {event name} (Pixel {id})
- Audience:
  - Location: {countries/regions/cities}
  - Age: {min}-{max}
  - Gender: {all/m/f}
  - Custom Audiences (include): {list}
  - Custom Audiences (exclude): {list}
  - Interests: {list}
  - Advantage+ Audience: {opt-in/opt-out}
- Placements: {Advantage+ / manual list}
- Budget: ${amount}/day

#### Ads (2-4 per ad set)
- **Ad 1.1.1** — {Ad Name}
  - Format: {Single Image/Video/Carousel}
  - Creative: {asset filename(s)}
  - Primary text: {body copy}
  - Headline: {headline}
  - Description: {description}
  - Link: {URL with UTMs}
  - CTA: {button value}
```

---

## 4. Placements Reference

| Placement | Value in CSV | Aspect Ratios Required |
|---|---|---|
| Advantage+ Placements (recommended) | `Advantage+ Placements` | 1:1, 9:16 (both) |
| Facebook Feed | `Facebook Feed` | 1:1 or 4:5 |
| Facebook Reels | `Facebook Reels` | 9:16 |
| Facebook Stories | `Facebook Stories` | 9:16 |
| Facebook Right Column | `Facebook Right Column` | 1.91:1 |
| Facebook Marketplace | `Facebook Marketplace` | 1:1 |
| Facebook In-Stream Video | `Facebook In-Stream Video` | 16:9 or 1:1 |
| Instagram Feed | `Instagram Feed` | 1:1 or 4:5 |
| Instagram Reels | `Instagram Reels` | 9:16 |
| Instagram Stories | `Instagram Stories` | 9:16 |
| Instagram Explore | `Instagram Explore` | 1:1 |
| Messenger Stories | `Messenger Stories` | 9:16 |
| Audience Network | `Audience Network` | 1:1 or 16:9 |

---

## 5. Import Workflow

1. **Pre-import:** Upload all creative assets to Asset Library, record hashes in manifest
2. **Prepare CSV:** Replace `<PENDING_UPLOAD>` tokens with actual hashes/IDs
3. **Validate:** Run `scripts/validate_output.py` — check char limits, audience existence, pixel ID, page ID
4. **Import:** Ads Manager → ⋮ menu → Export & Import → Import Ads → Upload CSV
5. **Review:** Meta shows per-row preview. Red rows = errors. Fix CSV and re-import.
6. **Keep as Draft:** Status = PAUSED on import. Review each ad preview before publishing.
7. **Publish:** Select campaigns → Publish Draft

---

## 6. Known Gotchas

- **Ad Account timezone:** All datetime fields use the ad account's timezone. Verify before scheduling.
- **Pixel ID vs Conversion Event:** Pixel must have the event firing BEFORE campaign goes live, or Meta rejects optimization goal at spend time.
- **Special Ad Categories:** If ad promotes Housing, Employment, Credit — MUST set Special Ad Categories. Disables most targeting (no age/gender/interest, only country/region).
- **Instant Forms (Lead Gen):** Form must exist and be connected to the same Page ID as the ad. Form ID format is numeric.
- **Custom Audience size:** Audience <1000 users may fail to deliver. Validator should warn.
- **UTM macros:** `{{campaign.name}}`, `{{ad.name}}`, `{{placement}}`, `{{site_source_name}}` are valid Meta macros in URL Tags field.
- **Dynamic Creative:** Advantage+ Creative overrides manual Title/Body if enabled. Turn off at ad set level if you want exact copy control.
- **Character limits enforced softly:** Meta will ACCEPT longer text but truncate on delivery. Validator MUST fail beyond limits or copy is silently cut.
- **Image Hash is case-sensitive:** 32-char lowercase hex. Copy from Asset Library exactly.
- **Duplicated ad in multiple ad sets:** Use same Creative Hash/Video ID across ad sets — Meta counts these as separate ads (creative reused, not shared).

---

## 7. Comparison: Bulk Import vs Manual Build

| Criterion | Bulk CSV | Manual Build |
|---|---|---|
| Speed for 1 campaign / 2 ad sets / 4 ads | Slower (asset upload + CSV + validation) | Faster (15 min) |
| Speed for 3+ campaigns / 6+ ad sets / 12+ ads | Much faster | Painful, error-prone |
| Repeatability / auditability | ✅ CSV is the source of truth | ❌ State only in Ads Manager |
| Complex targeting (lookalikes + interests + custom audience exclusions) | ⚠️ Often fails silently | ✅ UI shows errors immediately |
| Instant Forms (Lead Gen) | ⚠️ Form ID must pre-exist | ✅ Can create form in flow |
| Dynamic Creative | ❌ Not supported via CSV | ✅ UI supported |
| Catalog / Shopping | ❌ Not supported via CSV | ✅ UI required |

**Rule of thumb:** Use CSV for 2+ campaigns OR 6+ ads. Use manual for single-campaign lead gen launches.
