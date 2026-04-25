# Capture Recipe: React SPA with CountUp + scroll-reveal

**Profile ID:** `react-spa-countup`
**Detection signals:** Vite/React build artifacts (`/assets/index-XXXX.js`), `gpt-engineer-file-uploads` (Lovable origin), `.stat-number` + `data-count` attributes, IntersectionObserver-driven reveals.

**Examples:** Lovable, GPT-Engineer, Bolt-generated event pages. ISKM Nṛsiṁha Caturdaśī 2026 was the discovery case.

## Pitfalls on this profile

1. **Scroll-reveal fade-in animations** (opacity 0 → 1 on IntersectionObserver). Screenshots taken mid-animation show content at ~10% opacity and look blank. Past false-positive: "broken images" that were actually sections faded in.
2. **CountUp-style number counters** — JS libraries that increment stats over ~2s on IntersectionObserver entry. Mid-frame numbers look like real data. Past false-positive: "500+/171+ contradiction" that was a mid-count capture.
3. **Lazy-loaded images** tied to the same observers — don't appear until their section is scrolled into view.

## Capture protocol (strict order)

1. Navigate to URL
2. **Inject animation-kill CSS** (see `references/screenshot-capture.md` "Kill Page Animations") — disables fade-in. DO NOT apply JS counter-freeze monkey-patches; they break CountUp.
3. Resize Chrome window (Chrome MCP will land at ~500px on macOS minimum — that's fine for mobile test)
4. **Trigger all observers** — scroll to `document.body.scrollHeight`, wait 1s, scroll back to 0
5. **Wait 10–15 seconds** for CountUp timers to finish naturally
6. **DOM-verify** counter values before trusting screenshot text:
   ```javascript
   [...document.querySelectorAll('.stat-number, [class*="count"]')]
     .map(el => el.textContent.trim())
   ```
7. Only THEN capture screenshots — treat screenshot text as presentation, DOM-queried values as canonical.

## Specific checks for this profile

- **Image asset pipeline:** React SPAs from Lovable/GPT-Engineer sometimes ship with dev-only asset URLs (`gpt-engineer-file-uploads.appspot.com`). DOM-query `img.src` on every hero/gallery image and grep for dev hostnames. If found → CRITICAL finding (production pipeline broken).
- **IntersectionObserver thresholds:** Some React reveal components have `threshold: 0.5` — if the user's browser window is small, content below may never reveal. Audit the bottom of the page by scrolling manually, not just JS `scrollTo`.
- **CountUp target values:** Read the `data-count` / `data-target` attribute directly if present. Only if absent, fall back to waiting for the animation to settle.

## What NOT to do

- ❌ Monkey-patch `requestAnimationFrame` to flush counters (breaks CountUp math)
- ❌ Monkey-patch `Date.now` to advance time (breaks CountUp + any time-based UI)
- ❌ Override `textContent` of stat elements before the counter initializes (the library will then reset them to 0 on scroll)
- ❌ Take screenshots before the 10–15s settle wait

## Verification

After capture, assert DOM-verified:
- At least 1 `.stat-number` element has text matching `^\d+\+?$` with the number > 0
- At least 1 heading contains the expected Sanskrit / brand-specific content
- At least N images have `naturalWidth > 0` where N is roughly the visible hero count
