# Meta Ad Library Competitor Audit Procedure

Operational procedure for checking competitor Meta/Facebook ad activity using Chrome MCP browser automation. Runs during market-research Step 4 after the competitor list is populated in strategy.md.

## When to Run

- After Step 4 (Perplexity analysis) when strategy.md has a populated Competitive Landscape table
- The "Ads Active" column will typically be BLANK after Perplexity research — this procedure fills it
- Can also be run standalone as a follow-up if the column was left BLANK during initial research

## Prerequisites

- Chrome MCP connected (`mcp__Claude_in_Chrome__*` tools available)
- Chrome browser open
- No Meta login required — Ad Library is publicly accessible

## Procedure

### 1. Extract Competitor List

Read strategy.md competitor table from the "Competitive Landscape" section. Extract company names from the first column.

**Option A (automated):** Run `scripts/parse_competitor_list.py /path/to/_engine/wiki/strategy.md` to get a JSON array of competitor objects with URL-encoded names.

**Option B (manual):** Read the table directly from strategy.md and extract names.

**Limits:**
- Process top 10 competitors maximum (prioritize by relevance/price proximity to client)
- If more than 10 competitors exist, skip the least relevant ones

### 2. For Each Competitor

Navigate to Meta Ad Library with the competitor name as search query.

**URL pattern:**
```
https://www.facebook.com/ads/library/?active_status=all&ad_type=all&country=AU&q={competitor_name_url_encoded}
```

**Country code:** Match the client's target market. Default AU for Australian clients. Adjust per client:
- AU = Australia
- US = United States
- IN = India
- GB = United Kingdom

**Chrome MCP execution sequence:**

```
a. mcp__Claude_in_Chrome__navigate → Meta Ad Library URL with competitor name
b. Wait for page load (the library has dynamic content — may need 2-3 seconds)
c. mcp__Claude_in_Chrome__get_page_text → read the page content
d. If page text is ambiguous, use mcp__Claude_in_Chrome__read_page for structured DOM reading
e. Alternatively, mcp__Claude_in_Chrome__computer (screenshot) to visually confirm results
```

**Data to capture per competitor:**

| Field | What to look for |
|---|---|
| ads_active | true/false — does the page show active ads or "no ads" message? |
| ad_count | Number of active ads shown (exact count if visible, "multiple" if paginated) |
| ad_types | image, video, carousel — note which formats are visible |
| date_range | Earliest/latest ad start dates visible on the page |
| page_name | The exact Facebook page name running the ads (may differ from company name) |
| notes | Any notable observations — heavy video spend, seasonal patterns, specific offers |

**Interpreting results:**
- "This Page has no ads" or similar message → ads_active: false, ad_count: 0
- Results shown with ad cards → ads_active: true, count the visible cards
- Multiple Facebook pages with same name → pick the most likely match (check page details, location, followers)
- No results at all → competitor may not have a Facebook page, record as "No Facebook page / No ads"

### 3. Rate Limiting & Pacing

- Wait 3-5 seconds between each competitor check (Meta may throttle rapid requests)
- If the page shows a CAPTCHA or access block, pause for 30 seconds and retry once
- If blocked after retry, skip that competitor and mark as "UNABLE TO CHECK (rate limited)"
- Maximum 2 retries per competitor before skipping

### 4. Record Results

Build a summary table with all results:

```markdown
### Meta Ad Library Audit ({date})
| Competitor | Ads Active | Ad Count | Ad Types | Page Name | Notes |
|---|---|---|---|---|---|
| {name} | Yes/No | {count} | image, video, carousel | {page_name} | {notes} |
```

### 5. Update strategy.md

Update the "Ads Active" column in the Competitive Landscape table with concise results:

**Format for each cell:**
- Active ads: `Meta: X active ads (image, video)` — include ad types observed
- No ads: `Meta: No ads found`
- Error: `Meta: UNABLE TO CHECK (reason)`
- No page: `Meta: No Facebook page found`

**Also add** the full audit summary table (from step 4) below the Competitive Landscape section as a sub-section.

### 6. Error Handling

| Scenario | Action |
|---|---|
| Chrome MCP unavailable | Skip entire audit, leave Ads Active as BLANK with reason "Chrome MCP not available" |
| Meta Ad Library blocked/CAPTCHA | Pause 30sec, retry once, then skip with "UNABLE TO CHECK (blocked)" |
| Competitor name is ambiguous (common word) | Add industry qualifier to search (e.g., "Häuslein tiny homes"), note multiple results |
| Page loads but no content renders | Try screenshot to verify, retry once with page refresh |
| Country selector not matching | Verify country code in URL, try navigating again with explicit country parameter |

### 7. Quality Checks

Before finalizing:
- Verify at least 80% of competitors were successfully checked (if <80%, note in audit summary)
- Cross-reference: if a competitor has a strong online presence but "No ads found," this is still a valid finding (they rely on organic)
- Flag any competitor with >20 active ads as a "heavy advertiser" in notes
- Flag any competitor running video ads specifically (video creative is higher investment)

## Integration with Dashboard

The dashboard agent reads the "Ads Active" column from strategy.md to populate the competitor table. Color coding:

| Indicator | Meaning | Dashboard Display |
|---|---|---|
| Green dot | No ads found | Opportunity — competitor not defending this channel |
| Red dot | Active ads | Competition — competitor is spending on Meta |
| Orange dot | Heavy advertiser (>20 ads) | Strong competition — needs differentiated creative |
| Grey dot | BLANK/unchecked | Unknown — audit not yet run or failed |

## Output Artifacts

This procedure modifies one file only:
- `{client-folder}/_engine/wiki/strategy.md` — updates Ads Active column + adds audit summary sub-section

No separate deliverable file is created. The audit data lives in the wiki for downstream skill consumption.

## Downstream Connections

- **meta-ad-copywriter:** Knows which competitors are actively advertising and what formats they use
- **paid-media-strategy:** Competitive ad intensity informs budget recommendations and channel allocation
- **dashboard:** Competitor table shows visual ad activity indicators
