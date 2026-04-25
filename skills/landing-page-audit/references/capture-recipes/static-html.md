# Capture Recipe: Static HTML (default fallback)

**Profile ID:** `static-html`
**Detection signals:** None of the framework / CMS fingerprints matched. Treated as the safe default.

**Examples:** Hand-coded landing pages, simple HTML files, Webflow-exported static sites, static-site-generator output (Astro, Hugo, 11ty, etc.).

## Why this is the default

If no detection signals match, the page is assumed to be plain static HTML with predictable rendering behavior. Animations (if any) are CSS-only. Content is present in the initial HTML, not hydrated by JS. Screenshots work without special handling.

## Capture protocol

1. Navigate to URL
2. Inject animation-kill CSS as a precaution (no-op if there are no animations)
3. Resize Chrome window — mobile (Chrome MCP will land ~500px on macOS) and desktop
4. Capture immediately — no long wait needed; content is server-rendered and present at navigate-time

## Specific checks for this profile

- **Fewer false-positive risks.** Screenshots generally show what the page actually looks like in a real browser. DOM-First Rule still applies, but content-missing claims are rare.
- **If the page unexpectedly has dynamic behavior** (e.g., a "Load More" button that fetches content), treat those specific interactive sections as profile-mismatch cases and document them as audit limitations.
- **Accessibility-first:** static pages are more likely to ship with bad contrast, no alt text, missing form labels. Lean harder on Visual UX + CRO form-friction checklists.

## What NOT to do

- ❌ Over-engineer the capture (don't inject counter-freeze, don't wait 15s — nothing is animating)
- ❌ Assume static = simple; some hand-coded pages have custom JS that still lazy-loads images

## Verification

- Screenshot shows the same visual content as viewing the page in a regular browser
- DOM query of hero headings / body copy returns non-empty strings immediately after navigate
