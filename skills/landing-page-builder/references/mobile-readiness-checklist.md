# Mobile Readiness Checklist

Every landing page must pass this checklist before delivery. The validator enforces what can be automated; the rest is a manual review gate.

Run through every build at Step 4 (HTML Prototype). No exceptions. A page that fails any CRITICAL item here is not shippable.

---

## 1. Viewport & Foundation (Validator-Enforced)

- [ ] `<meta name="viewport" content="width=device-width, initial-scale=1.0">` present
- [ ] `<meta charset="UTF-8">` present
- [ ] Base body font-size ≥ 16px (prevents iOS auto-zoom on input focus)

## 2. Layout (Validator-Enforced + Visual Review)

- [ ] Mobile-first CSS: media queries use `@media (min-width: X)`, not `max-width` (mobile is default)
- [ ] Every grid collapses to single column below 700px
- [ ] Container horizontal padding ≥ 16px on smallest viewport (never edge-to-edge)
- [ ] No horizontal overflow at 375px width (visual check: scroll bar should only appear vertically)

## 3. Typography (Validator-Enforced)

- [ ] All display headlines (h1, h2, lede) use `clamp()` for fluid sizing — NOT fixed rem/px
- [ ] Body copy is 16-18px mobile, scales up for desktop via clamp if desired
- [ ] Line-length constrained (max-width on text blocks, typically 680-820px)

## 4. Tap Targets (Validator-Enforced)

- [ ] Every CTA button has padding that produces ≥ 44×44 CSS pixels total hit area
- [ ] Primary CTAs are full-width on mobile (`width:100%` in mobile layout or inherited from grid)
- [ ] At least 8px spacing between adjacent tappable elements (no mis-taps)
- [ ] Sticky mobile CTA exists, shows after ~400px scroll, hidden on desktop (min-width:900px)
- [ ] Body bottom padding compensates for sticky CTA height so nothing is occluded

## 5. Mobile Navigation (Validator-Enforced)

- [ ] If desktop nav exists, mobile has either:
  - a hamburger menu toggle with accessible `<button aria-expanded>`, OR
  - anchor links accessible via the sticky CTA / hero CTAs (no lost routes)
- [ ] Never leave users stranded: if desktop has 4+ nav links and mobile hides them all with no alternative, that's a CRITICAL fail

## 6. Forms (Validator-Enforced)

Every input field must have the correct type + autocomplete. No exceptions.

| Field | type | autocomplete |
|---|---|---|
| Name | text | name (or given-name/family-name if split) |
| Email | email | email |
| Phone | tel | tel |
| Date | date | — |
| State/Region | text or select | address-level1 |
| City | text | address-level2 |
| Postcode | text | postal-code |
| Country | text or select | country-name |
| Address | text | street-address |

- [ ] 3-5 fields max for lead_gen; 5-8 for higher-ticket pages
- [ ] Submit CTA is full-width on mobile
- [ ] Microcopy below CTA (risk-reducer or trust signal)
- [ ] For high-ticket ($5K+) pages: include optional phone field with `type="tel"`

## 7. Images (Validator-Enforced)

- [ ] Every `<img>` has `loading="lazy"` except the hero image
- [ ] Every `<img>` has explicit `width` and `height` attributes (prevents CLS)
- [ ] Every `<img>` has `alt` attribute (accessibility + SEO)
- [ ] Hero image constrained to 40-50% viewport height on mobile (never pushes CTA below fold)
- [ ] No placeholder `<div>` elements standing in for real images in the final deliverable — if the real asset isn't available, flag it in `notes_for_lovable` as a TODO, don't ship the placeholder silently

## 8. Motion & Performance (Validator-Enforced)

- [ ] `prefers-reduced-motion: reduce` media query disables all reveal/count animations
- [ ] Animated properties are ONLY `transform` and `opacity` (GPU-accelerated, no reflow)
- [ ] No `animation: ... width/height/margin/padding/top/left` rules
- [ ] Prototype under 150KB total (HTML + embedded CSS/JS)

## 9. Accessibility (Validator-Enforced)

- [ ] FAQ items use `<button aria-expanded aria-controls>` — not clickable `<div>`
- [ ] Sticky mobile CTA has `role="complementary"` and `aria-label`
- [ ] Every interactive element is keyboard-focusable
- [ ] Every section heading follows a logical h1 → h2 → h3 hierarchy (no skipped levels)

## 10. Cross-Device Manual Check (Reviewer Gate)

Before delivery, the builder must manually verify:

- [ ] Preview at 375px (iPhone SE baseline)
- [ ] Preview at 360px (Galaxy S8 / smallest common Android)
- [ ] Preview at 768px (iPad portrait)
- [ ] Preview at 1440px (standard desktop)
- [ ] Form submission test: tab order makes sense, mobile keyboard doesn't occlude CTA
- [ ] Sticky CTA behavior when a form field is focused

---

## Severity Mapping for Validator

| Severity | Rule |
|---|---|
| CRITICAL | Missing viewport, missing body font-size rule, form missing autocomplete, placeholder `<div>` instead of `<img>` in hero, fixed font-size on display headlines |
| WARNING | No hamburger menu when desktop nav is present, missing `loading="lazy"` on below-fold images, missing `width`/`height` on `<img>`, no `prefers-reduced-motion` query |
| INFO | Mobile breakpoint count, form field count, tap target sample |

---

## Learnings Applied

- 2026-04-16 — Retreat House: first build passed all functional checks but missed hamburger nav, phone field, state autocomplete, fluid lede, and used `<div>` placeholder for hero visual. All caught AFTER delivery because the prose in landing-page-research.md wasn't gated by the validator. This checklist + validator expansion closes that gap.
