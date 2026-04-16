# Screenshot Capture Process

**MANDATORY FIRST ACTION in Step 1.** Screenshot capture is not optional — it runs before any HTML analysis. The captured screenshots get embedded directly into the dashboard as `<img>` tags. No placeholders in the final deliverable.

---

## Priority: This Runs First

Screenshot capture is the **first thing that happens** after intake. Don't skip it. Don't defer it. Don't say "I'll get screenshots later." Capture → then analyze HTML → then audit.

## Prerequisites

- Claude in Chrome browser tools must be available (check for `navigate`, `resize_window`, `upload_image` tools)
- The landing page URL must be publicly accessible (no login required)
- If the page requires authentication or is behind a paywall, fall back to manual screenshots from the user

## Capture Sequence

### 1. Navigate to the Page

```
Tool: navigate
URL: {landing_page_url}
```

Wait for the page to fully load. If the page has cookie consent banners or popups, dismiss them first using `javascript_tool` to click the accept/close button — these block the real content.

### 2. Dismiss Overlays (if present)

Common overlays to handle before screenshots:
```javascript
// Cookie consent
document.querySelector('[class*="cookie"] button, [id*="cookie"] button, .cc-btn')?.click();

// Generic popups/modals
document.querySelector('.modal-close, [class*="popup"] .close, [aria-label="Close"]')?.click();

// Chat widgets — minimize, don't remove (they're part of the UX audit)
document.querySelector('[class*="chat-widget"] .minimize')?.click();
```

Wait 1-2 seconds after dismissing for animations to complete.

### 3. Mobile Screenshot (375×667px)

```
Tool: resize_window
width: 375
height: 667
```

Wait 2 seconds for responsive reflow.

```
Tool: read_page (screenshot mode)
```

This captures the above-the-fold mobile view — the most critical viewport for the audit.

**Full-page mobile capture (if needed):** For pages longer than one viewport, scroll down in sections and capture multiple screenshots. The key sections to capture:
- Above the fold (first viewport)
- Main content area (form, features, testimonials)
- Footer area (CTA repetition, trust signals)

Save screenshots to: `{client-folder}/sources/{page-name}-mobile.png`
If multiple scroll captures: `{page-name}-mobile-1.png`, `{page-name}-mobile-2.png`, etc.

### 4. Desktop Screenshot (1440×900px)

```
Tool: resize_window
width: 1440
height: 900
```

Wait 2 seconds for responsive reflow.

```
Tool: read_page (screenshot mode)
```

Save to: `{client-folder}/sources/{page-name}-desktop.png`

### 5. Restore Browser

Resize back to a standard window so the user's browser isn't left in a weird state:
```
Tool: resize_window
width: 1280
height: 800
```

## Using Screenshots in the Dashboard

**Screenshots MUST be embedded as actual `<img>` tags — never leave placeholder divs in the final deliverable.**

The captured screenshots get embedded in the dashboard template's annotated screenshot section:

1. Copy the screenshot files to the deliverables folder alongside the HTML dashboard
2. In the template, replace the `<div class="screenshot-placeholder">` with actual `<img>` tags:
   ```html
   <!-- Mobile view -->
   <img src="{page-name}-mobile.png" alt="Mobile view of {page-name}" style="width:100%;">
   
   <!-- Desktop view (if desktop section exists in template) -->
   <img src="{page-name}-desktop.png" alt="Desktop view of {page-name}" style="width:100%;">
   ```
3. Position marker overlays on top using CSS absolute positioning (top/left percentages)
4. If using base64 encoding (for self-contained HTML), convert images inline:
   ```html
   <img src="data:image/png;base64,{base64_data}" alt="Mobile view" style="width:100%;">
   ```

**Rule:** If screenshots were successfully captured, the final dashboard HTML must contain `<img` tags with actual image sources — not placeholder text. If screenshots failed (Elementor/auth), use a clean "Screenshots unavailable" message styled as a subtle note, not a broken-looking placeholder.

## Elementor Fix: Computer-Use Screenshots

Chrome MCP's internal screenshot method fails on Elementor pages — it captures blank backgrounds below the hero because Elementor's deeply-nested container/widget JS doesn't render in headless capture. The computer-use MCP bypasses this entirely by photographing actual display pixels.

**Hybrid capture flow for Elementor pages:**

1. **Navigate** with Chrome MCP (`navigate` tool) — loads the page in the real browser
2. **Scroll** with Chrome MCP (`javascript_tool` → `window.scrollTo()`) — positions the viewport
3. **Capture** with computer-use MCP (`screenshot` tool) — photographs what's actually on screen

This works because computer-use captures the rendered display, not the DOM. Elementor's JS runs normally in the real browser, so every section renders correctly.

**When to use this flow:**
- Elementor detected (look for `wp-content/plugins/elementor` in page source, or `.elementor-widget-container` classes)
- Chrome MCP screenshots show blank/cream/white below the hero
- Any page builder that relies on heavy JS rendering (Elementor, Divi, Beaver Builder)

**Capture sequence (3 positions minimum):**
```
Position 1: Top of page (hero + above fold) → computer-use screenshot
Position 2: Mid-page (scrollTo ~40% of page height) → computer-use screenshot  
Position 3: Bottom (scrollTo ~75% of page height) → computer-use screenshot
```

For mobile view: use Chrome MCP `resize_window` to set mobile viewport (390×844) before the scroll+capture sequence.

**Requirements:**
- macOS Screen Recording permission must be granted for Claude (System Settings → Privacy & Security → Screen Recording)
- Chrome browser must be the frontmost window during capture
- `request_access` must be called for the browser application before first screenshot

## Known Limitations

**Elementor pages:** Chrome MCP's internal screenshot fails below the hero. **Use the computer-use hybrid flow above** — this is the primary fix, not a workaround.

**Auth-gated pages:** Pages behind login walls require the user to be logged in before capture. Navigate to the page, confirm it's loaded, then capture.

**Very long pages:** Computer-use captures only the visible viewport. For pages longer than 3 scroll positions, add more capture points. Maximum useful screenshots per page: 5-6 (beyond that, diminishing returns for audit purposes).

## Fallback: Manual Screenshots

Last resort — only if both Chrome MCP AND computer-use MCP are unavailable (e.g., Screen Recording permission denied, no display access).

1. **Mobile screenshot** (required): "Can you take a full-page screenshot of the landing page on your phone? Or open Chrome DevTools → Toggle Device Toolbar → iPhone 12 Pro (390px) and screenshot."

2. **Desktop screenshot** (optional but helpful): "If you can also screenshot the desktop view, that helps with the layout analysis."

The user can upload screenshots directly into the conversation or drop them into the client folder.

## What to Look for While Capturing

While the page is loading and you're resizing viewports, note these things for the audit — they're visible during capture but might not be obvious from a static screenshot later:

- **Load time feel:** Did the page feel slow? Did elements jump around (layout shift)?
- **Cookie/popup behavior:** How intrusive was the overlay? Did it block the main content?
- **Responsive breakpoint:** Did the layout cleanly adapt from desktop to mobile, or did elements break?
- **Horizontal overflow:** Did anything cause horizontal scroll on mobile?
- **Font rendering:** Did text stay readable at mobile sizes?

Capture these observations as notes for the audit — they inform the Visual UX pillar.
