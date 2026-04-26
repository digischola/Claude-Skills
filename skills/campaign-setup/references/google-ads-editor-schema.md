# Google Ads Editor — CSV Bulk Import Schema

Reference for exact column names Google Ads Editor expects in bulk-import CSV files. Source: Google Ads Editor Help + battle-tested agency templates.

**Universal rule:** The first row of every CSV is the header row. Do NOT modify column header names. Multi-value cells use semicolons `;` as delimiters.

**Universal status values:** `Enabled`, `Paused`, `Removed`. Default to `Paused` on import — user enables in Step 2 of launch runbook after review.

---

## 1. Campaigns CSV (`01-campaigns.csv`)

One row per campaign.

| Column | Type | Required | Example | Notes |
|---|---|---|---|---|
| Campaign | string | ✅ | `NSW_NonBrand_Search_Operators` | Unique within account |
| Campaign Type | enum | ✅ | `Search` | Values: Search, Display, Shopping, Video, App, Performance Max, Demand Gen |
| Campaign Status | enum | ✅ | `Paused` | Start paused — enable after review |
| Budget | decimal | ✅ | `40.00` | Daily budget in account currency |
| Budget Type | enum | ⚪ | `Daily` | Daily (default) or Total |
| Bid Strategy Type | enum | ✅ | `Maximize Conversions` | Manual CPC, Maximize Clicks, Maximize Conversions, Target CPA, Target ROAS, Target Impression Share |
| Target CPA | decimal | ⚪ | `120.00` | Required if Bid Strategy = Target CPA |
| Target ROAS | decimal | ⚪ | `4.00` | Required if Bid Strategy = Target ROAS (as multiplier, e.g., 4.0 = 400%) |
| Networks | multi | ⚪ | `Google search;Search partners` | Semicolon-delimited |
| Languages | multi | ⚪ | `English` | |
| Locations | multi | ⚪ | `New South Wales, Australia;Queensland, Australia` | Use Google location IDs if known |
| Location Exclusions | multi | ⚪ | | Same format as Locations |
| Location Bid Modifier | decimal | ⚪ | | |
| Ad Rotation | enum | ⚪ | `Optimize` | Optimize or Rotate evenly |
| Campaign Start Date | date | ⚪ | `2026-04-20` | YYYY-MM-DD |
| Campaign End Date | date | ⚪ | | |
| Tracking Template | string | ⚪ | `{lpurl}?utm_source=google&utm_medium=cpc&utm_campaign={_campaign}` | Campaign-level tracking template |
| Frequency Cap | string | ⚪ | | For Display/Video |
| Labels | multi | ⚪ | `Launch-2026Q2;Priority-High` | |

**Naming convention (recommended):** `{REGION}_{BRAND_FLAG}_{CAMPAIGN_TYPE}_{AUDIENCE}` — e.g., `NSW_NonBrand_Search_Operators`, `AU_Brand_Search_All`.

---

## 2. Ad Groups CSV (`02-ad-groups.csv`)

One row per ad group. Each ad group must reference an existing Campaign by name.

| Column | Type | Required | Example | Notes |
|---|---|---|---|---|
| Campaign | string | ✅ | `NSW_NonBrand_Search_Operators` | Must match Campaigns CSV |
| Ad Group | string | ✅ | `Oculus_InvestorIntent` | Unique within campaign |
| Ad Group Status | enum | ✅ | `Paused` | |
| Ad Group Type | enum | ⚪ | `Standard` | Standard (default), Dynamic |
| Max CPC | decimal | ⚪ | `4.50` | Only if campaign uses manual CPC |
| Max CPM | decimal | ⚪ | | Display only |
| Target CPA | decimal | ⚪ | | Overrides campaign Target CPA |
| Labels | multi | ⚪ | | |

---

## 3. Keywords CSV (`03-keywords.csv`)

One row per keyword. Each keyword references Campaign + Ad Group.

| Column | Type | Required | Example | Notes |
|---|---|---|---|---|
| Campaign | string | ✅ | `NSW_NonBrand_Search_Operators` | |
| Ad Group | string | ✅ | `Oculus_InvestorIntent` | |
| Keyword | string | ✅ | `tiny home for airbnb` | |
| Criterion Type | enum | ✅ | `Phrase` | Values: `Exact`, `Phrase`, `Broad`, `Negative Exact`, `Negative Phrase`, `Negative Broad` |
| Status | enum | ✅ | `Enabled` | |
| Max CPC | decimal | ⚪ | `4.50` | Overrides ad group bid |
| Final URL | string | ⚪ | `https://retreathouse.com.au/investors` | Overrides RSA final URL if set |
| Labels | multi | ⚪ | | |

---

## 4. Responsive Search Ads CSV (`04-responsive-search-ads.csv`)

One row per RSA. Each RSA belongs to one ad group.

| Column | Type | Required | Example | Notes |
|---|---|---|---|---|
| Campaign | string | ✅ | `NSW_NonBrand_Search_Operators` | |
| Ad Group | string | ✅ | `Oculus_InvestorIntent` | |
| Ad Type | enum | ✅ | `Responsive search ad` | Literal string |
| Ad Status | enum | ✅ | `Enabled` | |
| Final URL | string | ✅ | `https://retreathouse.com.au/investors` | Must be HTTPS |
| Final Mobile URL | string | ⚪ | | If different from Final URL |
| Path 1 | string | ⚪ | `Investor` | Max 15 chars |
| Path 2 | string | ⚪ | `Brochure` | Max 15 chars |
| Tracking Template | string | ⚪ | | Overrides campaign tracking template |
| Headline 1 | string | ✅ | `$74K/yr from One Oculus Unit` | Max 30 chars |
| Headline 1 position | int | ⚪ | `1` | Pin position (1, 2, or 3). Blank = unpinned |
| Headline 2 | string | ⚪ | ... | Max 30 chars. Up to 15 headlines (Headline 1 through Headline 15) |
| Headline 2 position | int | ⚪ | | |
| ... (up to Headline 15) | | | | |
| Description 1 | string | ✅ | `2.8-year payback. Free brochure with full ROI model.` | Max 90 chars |
| Description 1 position | int | ⚪ | `1` | Pin position (1 or 2). Blank = unpinned |
| Description 2 | string | ✅ | | Max 90 chars. Up to 4 descriptions |
| Description 2 position | int | ⚪ | | |
| Description 3 | string | ⚪ | | |
| Description 4 | string | ⚪ | | |
| Labels | multi | ⚪ | | |

**Pinning rules:**
- Pin at most 2 headlines to position 1 (prevents Google from choosing among them for that slot)
- Pin descriptions sparingly — Google's AI performs better with flexibility
- Common pattern: pin top 2 headlines with primary value prop to position 1

**Character limit validator:** Must enforce 30 chars (headlines) / 90 chars (descriptions) / 15 chars (paths). Violations cause silent truncation or import rejection depending on Ads Editor version.

---

## 5. Sitelink Extensions CSV (`05-sitelink-extensions.csv`)

Sitelinks can be attached at Account, Campaign, or Ad Group level.

| Column | Type | Required | Example | Notes |
|---|---|---|---|---|
| Campaign | string | ⚪ | `NSW_NonBrand_Search_Operators` | Blank = account-level |
| Ad Group | string | ⚪ | | Blank = campaign or account level |
| Asset Type | enum | ✅ | `Sitelink` | Literal |
| Status | enum | ✅ | `Enabled` | |
| Sitelink Text | string | ✅ | `See the Numbers` | Max 25 chars |
| Description 1 | string | ⚪ | `$74K/yr per Oculus unit` | Max 35 chars |
| Description 2 | string | ⚪ | `2.8-year payback model` | Max 35 chars |
| Final URL | string | ✅ | `https://retreathouse.com.au/investors#returns` | |
| Mobile URL | string | ⚪ | | |
| Start Date | date | ⚪ | | |
| End Date | date | ⚪ | | |

**Minimum:** 4 sitelinks per campaign. **Recommended:** 6-8 for full slot fill.

---

## 6. Callout Extensions CSV (`06-callout-extensions.csv`)

| Column | Type | Required | Example | Notes |
|---|---|---|---|---|
| Campaign | string | ⚪ | | Blank = account-level |
| Ad Group | string | ⚪ | | |
| Asset Type | enum | ✅ | `Callout` | Literal |
| Status | enum | ✅ | `Enabled` | |
| Callout Text | string | ✅ | `Architect-Designed` | Max 25 chars |
| Start Date | date | ⚪ | | |
| End Date | date | ⚪ | | |

**Minimum:** 4 callouts per campaign.

---

## 7. Structured Snippets CSV (`07-structured-snippets.csv`)

> **2026-04-26 fix:** Per-column `Value 1`/`Value 2`/... format is REJECTED by Google Ads Editor's current parser with the error "There are too few values for a structured snippet. Create at least 3" — even when 3+ values are populated. Use the **single `Snippet Values` column with semicolon-delimited values** instead. The validator enforces this format.

| Column | Type | Required | Example | Notes |
|---|---|---|---|---|
| Campaign | string | ⚪ | | |
| Ad Group | string | ⚪ | | |
| Asset Type | enum | ✅ | `Structured Snippet` | Literal |
| Status | enum | ✅ | `Enabled` | |
| Header | enum | ✅ | `Services` | Values from Google's fixed header list: Amenities, Brands, Courses, Degree Programs, Destinations, Featured Hotels, Insurance Coverage, Models, Neighborhoods, Service Catalog, Services, Shows, Styles, Types |
| Snippet Values | string | ✅ | `Vinyasa Flow;Yin Yoga;Beginners Yoga;Yang to Yin` | Semicolon-delimited. **Minimum 3 values** per snippet. Max 25 chars per value. Up to 10 values. |

**Example row:**
```csv
Campaign,Ad Group,Asset Type,Status,Header,Snippet Values
LF-Livestream-AU-Search,,Structured Snippet,Enabled,Types,Vinyasa;Yin;Beginners;Gentle;Yang to Yin
```

**DO NOT** emit `Value 1`,`Value 2`,...,`Value 10` columns — that schema is documented in older Google references but no longer matches Editor's import parser. The validator will CRITICAL-fail if it sees the per-column format.

---

## 8. Negative Keywords CSV (`08-negative-keywords.csv`)

| Column | Type | Required | Example | Notes |
|---|---|---|---|---|
| Campaign | string | ⚪ | | Blank = requires Shared Negative List name |
| Ad Group | string | ⚪ | | Blank = campaign-level |
| Shared Set | string | ⚪ | `Universal Negatives` | For account-level negative lists |
| Keyword | string | ✅ | `free` | |
| Criterion Type | enum | ✅ | `Negative Broad` | Values: `Negative Exact`, `Negative Phrase`, `Negative Broad` |

---

## Import Order (Critical)

Ads Editor builds entities hierarchically. Import in this order — later imports reference earlier entities:

1. **Campaigns** — creates campaign shells
2. **Ad Groups** — under campaigns
3. **Keywords** — under ad groups
4. **Responsive Search Ads** — under ad groups
5. **Sitelinks / Callouts / Snippets** — can be account/campaign/ad-group level
6. **Negative Keywords** — campaign or shared set level

If order is wrong, Ads Editor shows `Campaign "X" not found` errors.

## Paste Workflow

1. Open Google Ads Editor → select account
2. Menu: `Account → Import → From file` OR Tools: `Make multiple changes → Paste from clipboard`
3. Paste CSV contents. Editor shows a preview.
4. Review changes — flagged errors shown in red
5. Keep changes as Drafts (Campaign Status = Paused in CSV)
6. Menu: `Post` → selective post by campaign if needed

## Known Gotchas

- **Tracking template `{lpurl}`** — this is Google's macro. Don't replace with actual URL.
- **Location IDs vs names** — Editor accepts both but names can be ambiguous. Prefer IDs from Google's location list when possible.
- **Currency symbols** — never include `$`, `AUD`, etc. in Budget / Max CPC / Target CPA columns.
- **Decimal format** — use `.` as decimal separator regardless of locale.
- **Empty cells vs blank strings** — both are treated as "no change" / "default". To clear a field, use `--` (two dashes).
- **Ad Group reference case-sensitive** — `Oculus_InvestorIntent` ≠ `oculus_investorintent`. Validator must flag mismatches.
