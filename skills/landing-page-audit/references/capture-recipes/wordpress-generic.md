# Capture Recipe: WordPress (generic / custom theme)

**Profile ID:** `wordpress-generic`
**Detection signals:** `/wp-content/`, `/wp-includes/`, `wp-json` — but NO Elementor (`/plugins/elementor`) or React-SPA markers. Typically a custom theme + Gutenberg core blocks + Yoast + a cache plugin.

**Examples:** Custom-theme WordPress sites from Australian/SG/US agencies. `thriveretreats.com.au` was the discovery case (custom theme + Slick carousel + Lenis smooth-scroll + Contact Form 7 + Breeze cache).

## Pitfalls on this profile

1. **Smooth-scroll libraries** (Lenis, Locomotive, SmoothScroll.js) intercept `window.scrollTo` and animate over 600–1200ms. Programmatic scroll snapshots mid-animation look blank or half-rendered. Always wait 1.5s after any `scrollTo` before reading DOM or capturing screenshot.
2. **`<img loading="lazy">` on WP core blocks** — Gutenberg core image block and most custom themes set `loading="lazy"` by default. Images below the fold report `.complete = false` and `naturalWidth = 0` until scrolled into view.
3. **Cache plugin staleness** (Breeze, WP Rocket, W3 Total Cache, LiteSpeed) — HTML may be served from a stale cache. The live DOM reflects true state; WebFetch on a cached page may show outdated copy. Prefer DOM queries over fetched HTML when they disagree.
4. **Slick/Swiper carousel init delay** — Sliders usually init on `DOMContentLoaded` or later. Screenshots before init runs show raw stacked slides. Wait 2s after page load before first capture.
5. **Contact Form 7 / WPForms / Gravity Forms** — expect a hidden honeypot field and sometimes reCAPTCHA (v2 or v3 badge). Count form friction on VISIBLE fields only; the honeypot is invisible to users and doesn't count.
6. **Yoast schema vs page content drift** — JSON-LD in `<head>` may contain date/price/stock data that contradicts the visible page. When auditing, always compare schema against rendered body text.

## Capture protocol (strict order)

1. Navigate to URL
2. **Wait 2s** for Slick/Swiper carousel init, custom JS handlers, Lenis scroll init. Do NOT inject animation-kill CSS blanket as it can break Slick and Lenis.
3. **Dismiss overlays** — WordPress commonly has GDPR cookie banners (e.g., Cookie Notice, CookieYes) on first load. Click accept/dismiss.
4. **Identify smooth-scroll library** — run:
   ```javascript
   !!window.lenis || !!window.Lenis || !!document.querySelector('[data-locomotive-scroll]') || !!window.locomotiveScroll
   ```
   If true, use `window.lenis?.scrollTo(y, {immediate: true})` (Lenis) or the library's native API instead of `window.scrollTo`. If the library can't be controlled, accept 1–1.5s wait after each scrollTo for the animation to land.
5. **Incremental scroll** to trigger `loading="lazy"` images: scroll in 500px steps with 400ms pauses, then scroll back to top.
6. **Wait 3–5s** for lazy images to decode.
7. **DOM-verify** before trusting screenshots:
   ```javascript
   const imgs = [...document.querySelectorAll('img')];
   ({
     total: imgs.length,
     loaded: imgs.filter(i => i.naturalWidth > 0).length,
     pending: imgs.filter(i => !i.complete).length,
     broken: imgs.filter(i => i.complete && i.naturalWidth === 0).length
   })
   ```
8. Capture screenshot.

## Specific checks for this profile

- **Contact Form 7 / WPForms / Gravity Forms detection:** look for `.wpcf7`, `.wpforms-form`, `.gform_wrapper`. Note form plugin because CF7's built-in spam defense (honeypot + invisible reCAPTCHA) affects friction scoring.
- **Honeypot detection:** check for hidden inputs via `.getBoundingClientRect().width === 0` or CSS `display:none`/`visibility:hidden`. Don't count them in form-friction score.
- **reCAPTCHA presence:** look for `.g-recaptcha`, iframe with `recaptcha/api2`, or `window.grecaptcha`. Invisible v3 is friction-free; v2 "I'm not a robot" checkbox is +1 friction.
- **Yoast schema audit:** parse `<script class="yoast-schema-graph">` JSON and cross-check key fields (name, datePublished, description, breadcrumb, offers.price if present) against rendered page content. Inconsistency is a CRITICAL because social shares, Google rich results, and aggregators use schema.
- **Cache plugin detection:** look for `<!-- Breeze -->`, `<!-- WP Rocket -->`, `<!-- W3TC -->` HTML comments. Note the plugin for later — cache freshness affects whether WebFetch and DOM agree.
- **Theme identification:** read `/wp-content/themes/<slug>/` path from CSS/JS refs. Custom themes (like `thriveretreats`) have full layout control; premium themes (Divi, Astra, Kadence, GeneratePress) each have known quirks.
- **Block library vs custom builder:** presence of `wp-block-library` + custom theme CSS = Gutenberg + custom theme. No page-builder interference.

## What NOT to do

- ❌ Blanket animation-kill CSS (breaks Slick, Lenis, Swiper — audit the animations, don't kill them)
- ❌ Trust WebFetch HTML over live DOM when a cache plugin is present
- ❌ Count honeypot or off-screen CF7 fields toward form-friction score
- ❌ Use `window.scrollTo` without the smooth-scroll library API if one is detected — your scroll may be ignored or animated over multiple seconds
- ❌ Assume every WordPress page is Elementor — check theme/plugin markers first

## Verification

After capture, assert DOM-verified:
- At least 1 visible form element (`form:not([style*="display:none"])`) with more than 1 visible field
- Hero image has `naturalWidth > 0` (not lazy-deferred)
- Yoast schema (if present) `name` matches visible H1 within 80% string similarity
- No WordPress admin bar visible (unless user is logged in — then flag it)
- No "coming soon" / "maintenance" plugin interstitial

## Audit-specific notes

- **Form friction:** score VISIBLE fields only. Honeypot and nonces are invisible; don't penalize.
- **Above-the-fold:** with Breeze/cache + custom theme, first paint can feel fast but LCP may still be slow if hero is a large un-optimized `<img>`. Flag if hero image > 300KB or not in WebP.
- **Mobile:** WordPress custom themes often have distinct mobile breakpoints (<= 768px, <= 480px). If Chrome MCP mobile viewport hack doesn't work, verify responsive classes exist (`.mobile-menu`, `.hamburger`) as a structural fallback.
