# Website Render Fallback Chain

Extracting content from brand websites requires a tiered approach. Modern SPAs (Lovable, GPT-Engineer, Vercel React) return near-empty HTML to static fetchers.

## Tier 1 — WebFetch (try first)

```
WebFetch(url, prompt="Extract positioning, services, testimonials, credentials, contact info, social links, and visible tone.")
```

**Works for:** WordPress, static sites, server-rendered React (Next.js with SSR), Squarespace, Shopify, Wix.

**Fails for:** Lovable, GPT-Engineer, Vite React SPAs, anything with `<div id="root"></div>` as the entire body.

**Detection:** if WebFetch response is <500 chars of meaningful content OR says "appears to be a minimal landing page" OR the tool reports seeing only domain name + tagline, escalate to Tier 2.

## Tier 2 — Claude in Chrome MCP (SPA fallback)

```
1. mcp__Claude_in_Chrome__tabs_context_mcp (createIfEmpty: true)
   → returns tabId
2. mcp__Claude_in_Chrome__navigate (url, tabId)
3. mcp__Claude_in_Chrome__read_page (tabId, depth: 20)
   → accessibility tree: headings, services, testimonials, case studies, form options, links
4. mcp__Claude_in_Chrome__get_page_text (tabId)
   → body copy for tone/positioning extraction
```

**Why depth 20:** default depth 15 can miss deeply-nested service card content on sites with animated reveals.

**Navigation interactions:** if the site has a "click to continue" intro gate, use `mcp__Claude_in_Chrome__left_click` on the hero region before reading.

**Multiple pages:** navigate to `/work`, `/about`, `/contact` in sequence and read each. Case study detail pages (e.g. `/work#cs-<uuid>`) contain the richest metric content.

## Tier 3 — Computer-use screenshot (last resort)

If Chrome MCP extension is not connected:
- Ask user to connect the extension, OR
- Fall back to `mcp__computer-use__screenshot` + visual inspection

## Tier 4 — Manual checklist

If all tiers fail, output a manual extraction checklist with BLANK fields and ask the user to paste:
- Homepage copy
- Services list
- Testimonials
- Partner/client list
- Any credentials/awards
- Brand guide (colors/fonts) if they have one

## Anti-patterns

- Never guess a missing service from sector assumption. If Tier 1-3 don't reveal services, leave BLANK with reason.
- Never fabricate testimonial quotes even paraphrased. Only use exactly what's on the site.
- Never assume credentials (Ex-Google, $XB managed) that aren't explicitly displayed.
