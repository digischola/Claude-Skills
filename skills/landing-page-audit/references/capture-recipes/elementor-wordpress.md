# Capture Recipe: Elementor on WordPress

**Profile ID:** `elementor-wordpress`
**Detection signals:** `elementor-widget-container` class, `wp-content/plugins/elementor` asset paths, `elementor-kit-N` body class, `class="elementor ..."` containers.

**Examples:** Most WordPress sites built with the Elementor page builder. srikrishnamandir.org main site.

## Pitfalls on this profile

1. **Chrome MCP internal screenshot fails below the hero** — Elementor's deeply-nested widget JS doesn't fully render in headless capture mode. Sections below the hero come out as blank cream / white background even though content is rendered in a real browser.
2. **Heavy external CSS** — theme + Elementor + plugin stylesheets stacked. `extract_brand.py` can read theme defaults instead of visually applied styles (ISKM case: Bootstrap success green #5cb85c surfaced instead of the actual saffron gold #f1c66e).
3. **WordPress block editor remnants** — unrelated classes / preset color vars (`--wp--preset--color-*`) pollute CSS extraction.

## Capture protocol

1. Navigate to URL
2. Inject animation-kill CSS (safe on WP; Elementor rarely uses IntersectionObserver fades)
3. Resize Chrome window to mobile dimensions
4. **Use computer-use MCP hybrid capture** for anything below the hero:
   - Chrome MCP: `navigate`, `javascript_tool` for scroll positioning
   - computer-use MCP: `screenshot` for actual display pixels
5. Capture at desktop viewport too — Elementor pages often have different desktop/mobile layouts that need visual check

## Specific checks for this profile

- **DOM-override brand extraction:** After running `extract_brand.py`, inspect computed styles on visible buttons/headings via `getComputedStyle`:
  ```javascript
  document.querySelectorAll('a.elementor-button, .elementor-button, button').forEach(b => {
    console.log(getComputedStyle(b).backgroundColor);
  });
  ```
  If the script's primary color doesn't appear in the top 3 button backgrounds, override it.
- **Sanskrit/custom font rendering:** WP sites often rely on external Google Fonts that may not preload — verify `Cardo`, `Noto Sans`, or whatever the theme declares is actually loaded in production (not falling back to Times/Arial).
- **Plugin vs theme CSS conflicts:** If `extract_brand.py` returns `WP_PRESET_FILTERED` warnings, the real brand palette likely lives in the child theme's `style.css`, not the theme defaults.

## What NOT to do

- ❌ Trust Chrome MCP's screenshot of below-hero sections without a computer-use verification pass
- ❌ Accept `extract_brand.py` output without DOM-override check when the business is a specific brand category (temple → expect saffron/gold; wellness → expect earth tones)

## Verification

- Capture top-of-page screenshot shows branded hero with real typography
- Computer-use capture of mid/bottom sections shows actual widget content (not blank)
- DOM-verified brand colors match visible button/heading computed styles
