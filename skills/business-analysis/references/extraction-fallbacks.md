# Data Extraction Fallback Chain

When extracting text/data from external sources (websites, social profiles, review platforms), use this tiered fallback. Each tier is tried only if the previous one fails or returns insufficient data.

---

## Tier 1: WebFetch (Default)

**Tool:** `WebFetch(url, prompt)`
**Best for:** Static HTML sites, standard CMS (WordPress, Simplotel, Squarespace rendered pages), review platforms (TripAdvisor), documentation sites.
**Strengths:** Fast, no dependencies, works without browser.
**Fails on:** Social platforms (Instagram, Facebook, LinkedIn), JS-heavy SPAs (Elementor, React apps), login-gated pages, dynamic pricing tables rendered client-side.

**How to detect failure:**
- Response contains only CSS variables, JS bootstrap code, or `<noscript>` content
- Response says "cannot extract" or returns generic meta tags without page content
- Content length < 200 chars for a page that should have substantial content

**Action on failure:** Move to Tier 2.

---

## Tier 2: Chrome MCP (Rendered DOM)

**Tool:** `mcp__Claude_in_Chrome__get_page_text(tabId)` or `mcp__Claude_in_Chrome__read_page(tabId)`
**Prerequisite:** Chrome extension connected. User has the target page (or can open it) in Chrome.
**Best for:** JS-rendered sites, social profiles user is logged into, Elementor pages, SPAs, Facebook Ad Library.
**Strengths:** Reads the fully rendered DOM — everything the user sees, Chrome MCP can read. Handles login sessions (user's cookies).
**Fails on:** Chrome extension not connected, page not open in Chrome, content behind interactions (click-to-expand, infinite scroll).

**Steps:**
1. Check if Chrome MCP is available (look for `mcp__Claude_in_Chrome__*` tools)
2. Ask user to open the target URL in Chrome if not already open
3. Use `tabs_context_mcp` to find the right tab
4. Use `get_page_text` for full text extraction, or `read_page` for structured DOM reading
5. For below-fold content: use `mcp__Claude_in_Chrome__javascript_tool` to scroll, then re-read

**Social media specific:**
- **Instagram:** User must be logged in. Profile page shows follower count, bio, recent posts in rendered DOM.
- **Facebook:** User must be logged in. Page shows likes, followers, about text, recent posts.
- **Facebook Ad Library:** Open facebook.com/ads/library, search for the brand. Chrome MCP reads the results.
- **Google Business Profile:** Open the Maps listing. Chrome MCP reads rating, review count, hours.

**Action on failure:** Move to Tier 3.

---

## Tier 3: Computer-Use MCP (Visual Extraction)

**Tool:** `mcp__computer-use__screenshot` + multimodal reading
**Prerequisite:** Computer-use MCP connected. Target page visible on screen.
**Best for:** Verifying element existence, extracting data from visual-only contexts (infographics, images with text, complex layouts), capturing what Chrome MCP misses.
**Weakness:** Lossy — screenshots can't copy text perfectly, may miss below-fold content, requires multiple captures for long pages.

**Steps:**
1. Ensure the target page is visible on screen (use Chrome MCP or `open_application` to navigate)
2. Take screenshot with `mcp__computer-use__screenshot`
3. Read the screenshot visually — extract data points, counts, ratings visible in the image
4. For long pages: scroll using computer-use, take multiple screenshots at different scroll positions
5. For social profiles: capture the header area (followers/following/posts count) in one screenshot

**When to combine Tier 2 + 3:**
- Chrome MCP extracts the bulk text data (fast, accurate)
- Computer-use screenshot verifies specific visual elements (logos, layout, charts, follower counts displayed as images)
- This hybrid approach is the most reliable for complex pages

**Action on failure:** Move to Tier 4.

---

## Tier 4: Manual Checklist (Last Resort)

**When:** No MCP tools available, or page requires authentication the user hasn't provided, or content is simply not extractable programmatically.

**Action:** Generate a structured checklist in the wiki page with BLANK fields and instructions:

```markdown
### Manual Verification Needed

The following fields could not be extracted automatically. Please check manually and update:

- [ ] Instagram followers: _____ (check instagram.com/handle)
- [ ] Facebook page likes: _____ (check facebook.com/page)
- [ ] Google Business rating: _____ (search "[business name]" on Google Maps)
- [ ] Meta Pixel installed: _____ (check site source for fbq or Facebook Pixel Helper extension)
```

Tag all manual fields as `BLANK — requires manual verification, [tool] extraction failed`.

---

## Decision Matrix: Which Tier for Which Source?

| Source | Tier 1 (WebFetch) | Tier 2 (Chrome) | Tier 3 (Computer-Use) | Notes |
|--------|:-:|:-:|:-:|-------|
| Business website (standard CMS) | ✅ | fallback | rare | Most sites work at Tier 1 |
| Business website (Elementor/React) | ❌ | ✅ | verify | JS rendering needs Chrome |
| TripAdvisor | ✅ | fallback | rare | WebFetch works well |
| Google Maps / GBP | partial | ✅ | verify | WebFetch gets some data |
| Instagram | ❌ | ✅ (logged in) | verify | Requires user login |
| Facebook page | ❌ | ✅ (logged in) | verify | Requires user login |
| Facebook Ad Library | ❌ | ✅ | verify | No login needed, but JS-heavy |
| LinkedIn | ❌ | ✅ (logged in) | fallback | Heavy anti-scraping |
| Twitter/X | partial | ✅ | fallback | WebFetch gets some data |
| Google Ads Keyword Planner | ❌ | ✅ (logged in) | ❌ | Requires Google Ads account |

---

## Logging Extraction Attempts

When a tier fails, log it in the wiki page:

```markdown
- **Instagram followers:** BLANK — WebFetch returned CSS-only (Tier 1 failed), Chrome MCP not connected (Tier 2 unavailable)
```

This helps future sessions know which tiers were attempted and which to try next.
