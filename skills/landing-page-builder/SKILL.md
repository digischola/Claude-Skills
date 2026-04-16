---
name: landing-page-builder
description: "Generates high-converting HTML landing page prototypes for wellness retreats, yoga studios, workshops, events, and service businesses. Produces complete page copy, responsive design with animations, and structured spec for Lovable rebuild. Works standalone (any client) or downstream (reads creative brief, ad copy, audit findings from prior skills). Use when user mentions: build landing page, create landing page, landing page for, make a page for, new page, website page, sales page, booking page, registration page, lead gen page, conversion page, rebuild this page. Do NOT trigger for: landing page audit (evaluation only), ad copy writing, campaign setup, market research."
---

# Landing Page Builder

Generates complete HTML landing page prototypes with conversion-optimized copy, responsive design, animations, and client branding. Output is a self-contained HTML file ready for client review, then Lovable rebuild and Netlify deploy.

## Context Loading

Read these shared context files before starting:
- `shared-context/analyst-profile.md` — workflow, client types, quality standards
- `shared-context/accuracy-protocol.md` — 3 accuracy rules for all data handling

## Process Overview

### Step 1: Identify Mode & Load Context

**Check for downstream context:**
- `{client}/wiki/` exists? → Downstream mode
- No wiki? → Standalone mode

**Downstream mode — auto-load:**
- `deliverables/brand-config.json` — colors, fonts, logo
- `wiki/offerings.md` — offering details, pricing, inclusions
- `wiki/brand-identity.md` — tone, personality
- `deliverables/*-creative-brief.json` — visual direction, proof hierarchy (if exists)
- `deliverables/*-ad-copy-report.md` — headlines, CTAs, value props (if exists)
- `deliverables/*-landing-page-audit.md` — issues to fix (if exists)
- `deliverables/*-optimization-report.md` — CVR data, friction signals (if exists)

See `references/skill-coordination.md` for full upstream/downstream map.

**Standalone mode — ask guided questions:**
1. What's the page for? (retreat, workshop, consultation, training)
2. What's the offer? (name, price, dates, location, inclusions)
3. Who's the audience? (age, gender, pain points, sophistication level)
4. What's the conversion action? (book, register, enquire, apply)
5. Brand: colors, fonts, logo URL? (or use wellness defaults)
6. Any specific concerns or audit findings to address?

### Step 2: Determine Page Type & Architecture

Load `references/landing-page-research.md` §1.

Classify into one of 4 types:

| Type | Price Range | Sections | Words |
|---|---|---|---|
| retreat_booking | $300-2000+ | 10-14 | 1500-3000+ |
| workshop_event | $50-300 | 6-10 | 600-1500 |
| lead_gen | Free/$0 | 4-7 | <1000 |
| teacher_training | $2000+ | 8-12 | 1500-3000+ |

Select the mandatory section order from landing-page-research.md for the identified type.

### Step 3: Generate Page Copy

Load `references/copy-frameworks.md`.

Write copy for each section following:
- Headline formulas for the page type (§1)
- Section copy frameworks (§2)
- CTA patterns — first-person, action+benefit, 2-5 words (§3)
- Emotional arc: aspiration → logic → trust → urgency (§4)
- Wellness-specific language rules (§5)
- Readability: grade 6-8, 10-18 words/sentence, 1-3 sentence paragraphs (§6)
- Microcopy near every CTA and form (§7)

If downstream with ad copy available: align page headlines with ad headlines (message match = +20-35% conversion lift).

If audit exists: ensure every CRITICAL and HIGH issue is addressed in the new page.

### Step 4: Build HTML Prototype

Load `references/landing-page-research.md` §§8-16 for design rules.
**Mandatory: Load `references/mobile-readiness-checklist.md` and build to pass every CRITICAL check.** The validator enforces most of these; the manual review gate at the bottom of the checklist is the builder's responsibility.

**Design system:**
- Brand colors from brand-config.json (fallback: light theme, #e71c24 accent for wellness)
- 8px grid spacing system
- Fluid typography (16px min body, 24px+ headlines)
- Flexbox/Grid layout — semantic HTML (section, header, main, footer)
- Mobile-first responsive (375px base)

**Required elements:**
- Viewport meta tag
- Responsive media queries (375px, 768px, 1024px breakpoints)
- Sticky CTA bar on mobile
- Scroll-triggered reveal animations (IntersectionObserver + CSS transform/opacity)
- Number counter animations for social proof
- Button hover micro-interactions
- `prefers-reduced-motion` media query
- Print-friendly mode via media query

**Performance budget:**
- Prototype under 150KB (HTML + embedded CSS/JS)
- Only animate transform and opacity (GPU-accelerated)
- No external dependencies except fonts
- Lazy-load placeholder for below-fold images

**Lovable portability rules:**
- Semantic section wrappers with clean class names
- No deeply nested animation wrappers
- No canvas/complex SVG effects
- Flexbox/Grid layout, no float hacks

### Step 5: Generate Page Spec JSON

Save as `{client}/deliverables/{page-name}-page-spec.json`.

Structure:
```json
{
  "page_type": "retreat_booking|workshop_event|lead_gen|teacher_training",
  "client_name": "",
  "page_title": "",
  "conversion_action": "",
  "sections": [
    { "id": "hero", "type": "hero", "headline": "", "subheadline": "", "cta_text": "", "cta_microcopy": "" },
    ...
  ],
  "cta_primary": { "text": "", "url": "", "microcopy": "" },
  "brand": { "accent_color": "", "font_heading": "", "font_body": "", "logo_url": "" },
  "seo": { "title": "", "description": "", "og_title": "", "og_description": "" },
  "notes_for_lovable": "Any rebuild-specific instructions"
}
```

This spec helps the Lovable rebuild stay faithful to the prototype's structure and copy.

### Step 6: Update Wiki & Close

Update `{client}/wiki/log.md` — add LANDING-PAGE entry with date and page details.

If audit existed: note which issues were addressed.

### Step 7: Validate & Close

Run `scripts/validate_output.py` against HTML and spec JSON.
Fix any CRITICAL failures before delivery.
Run feedback loop per `references/feedback-loop.md`.
Flag downstream connections (post-launch-optimization will track CVR on new page).

## Failure Handling

- No brand-config.json → use wellness defaults (light theme, warm palette)
- No creative brief → use copy-frameworks.md formulas standalone
- No audit findings → build from research best practices only
- Client has no offerings data → ask in standalone mode
- Generated page exceeds 150KB → strip redundant CSS, compress

## Learnings & Rules

[2026-04-16] [Retreat House — first battle test, MONOCHROMATIC_SITE + high-ticket $210K] Finding: Page type classification was ambiguous — the conversion action (brochure download via Pipedrive form) is classic lead_gen, but the ticket size ($210K) and buyer sophistication (venue operators) demanded teacher_training-level depth (detailed FAQ, pricing anchoring, compliance proof section). Action: classified as lead_gen but deliberately borrowed architecture elements from teacher_training. Documented in spec JSON `notes` field. **RULE:** For high-ticket lead_gen pages ($5K+ AOV), use hybrid architecture: lead_gen CTA/form + teacher_training section depth. Don't force a binary classification.

[2026-04-16] [Retreat House — MONOCHROMATIC brand] Finding: brand-config.json has no accent_color because site is monochromatic (black/white + photography only). Using pure monochrome on a conversion landing page loses the visual hierarchy that premium CTAs need. Action: derived #2d4a3e (forest green) from the creative brief's visual direction (Byron Bay hinterland setting), labeled as [INFERRED] in spec JSON, flagged in `notes_for_lovable` to stay disciplined with single accent. **RULE:** For MONOCHROMATIC_SITE brands, derive a single accent color from the creative brief's visual direction or industry proxy — never auto-apply a generic wellness accent. Document the derivation in spec JSON so Lovable rebuild preserves discipline.

[2026-04-16] [Retreat House — Lovable portability] Finding: Client uses IvyPresto Display + FH Oscar fonts, neither available via Google Fonts. Prototype needed to work for preview without font licensing. Action: used Cormorant Garamond (Google Fonts substitute for IvyPresto) + Inter (substitute for FH Oscar), flagged both in `notes_for_lovable` with rebuild instructions (Adobe Fonts for IvyPresto, self-host for FH Oscar). **RULE:** When brand fonts aren't Google Fonts-available, pick the closest Google Fonts substitute for the prototype and explicitly document the swap in `notes_for_lovable`. Never block the prototype on font licensing.

[2026-04-16] [validator H1 detection] Finding: validate_output.py flagged H1 at 44% of document on a perfectly valid page — inline `<style>` block (10KB of CSS) inflated document length before `<body>`. Action: fixed validator to strip `<head>`, `<style>`, and `<script>` blocks before measuring H1 position, now measures position within body content only. After fix: H1 at 3% of body content. **RULE:** Validator HTML heuristics (H1 position, component scanning) must measure against body content only, not raw document. Inline CSS and JS are normal in self-contained prototypes.

[2026-04-16] [accessibility on interactive elements] Finding: validator warned "No ARIA attributes found" because FAQ items used `<div class="faq-question">` with click handlers. Not a CRITICAL fail but an accessibility regression. Action: converted FAQ questions to `<button>` elements with `aria-expanded` and `aria-controls`, paired with `role="region"` on answer panes. Mobile sticky CTA got `role="complementary"` and `aria-label`. JS updated to toggle aria-expanded alongside .open class. **RULE:** Interactive elements (FAQ toggles, sticky CTAs, custom dropdowns) must be semantic `<button>` tags with aria-expanded/aria-controls from the first build. Don't treat ARIA as a polish pass — it changes the element choice.

[2026-04-16] [external dependencies warning] Finding: validator flagged "2 external dependencies" for legitimate outbound links to the client's compliance tool on their domain. Warning is noisy for legitimate navigation links. Action: left as-is, documented as expected warning. **RULE:** External `href` links to client domain for navigation are expected. The warning is worth keeping for detecting accidental CDN/script leaks, but note in feedback loop when warning is a legitimate navigation link.

[2026-04-16] [mobile readiness — first-build gaps caught post-delivery] Finding: Retreat House landing page passed initial validator but reviewer found 5 mobile gaps that functional tests didn't catch: (1) no hamburger/mobile nav menu when desktop nav hidden below 900px, (2) state select missing `autocomplete="address-level1"`, (3) no optional phone field for a $210K product, (4) hero lede used fixed 1.25rem instead of `clamp()`, (5) hero used `<div class="hero-visual-ph">` placeholder instead of a real `<img>` or background-image. Root cause: mobile rules lived as prose in landing-page-research.md §13 but were never enforced by the validator — so compliance depended on memory. Action: (a) created `references/mobile-readiness-checklist.md` — pass/fail gate with severity mapping, (b) expanded `validate_output.py` with mobile-readiness section: form autocomplete, input type-for-name matching, fluid-typography check on h1, mobile-first vs max-width detection, body font-size ≥16px, img width/height/loading attributes, hero placeholder detection, mobile nav alternative detection, tap-target padding check, (c) updated SKILL.md Step 4 to mandate loading the checklist. **RULE:** Mobile optimization is a validator gate, not a memory task. Every rule in the checklist must either be validator-enforced or appear in the manual review gate section with a checkbox. When a reviewer catches something the validator missed, the fix has three parts: (1) fix the page, (2) add the check to the validator, (3) add the rule to the checklist. All three in the same session, no exceptions.
- [2026-04-16] [Validator hardening] Finding: three real gaps that let broken deliverables ship. (a) CTA regex missed "claim / qualify / enroll / donate / purchase / invest / request / submit / contact / speak" — B2B, non-profit and high-ticket CTAs were flagged as "no CTA found" even when the page had them. (b) No page-type awareness — a 9-field lead_gen page passed validation silently because the form-field budget from landing-page-research.md §7 was documented in prose only. (c) No Lovable portability lint — `<canvas>`, `float:` CSS, and `<path transform="matrix(...)">` would survive validation but cost hours to refactor during Lovable rebuild. → Action: expanded CTA verb list to 22 verbs (wellness/B2B/non-profit/high-ticket/lead-gen); added `SPEC_PAGE_TYPE` module global populated from page-spec.json before HTML validation so `validate_html` can enforce per-type form-field budgets (lead_gen/workshop=5, retreat=7, teacher_training=8); added three Lovable portability checks (canvas, float declarations, SVG matrix transforms). All three fire on real cases — smoke-tested with a lead_gen page using "Donate Now": CTA detected, budget within limits, Lovable-clean.
- [2026-04-16] [WCAG contrast — closes Phase 3 blind spot] Finding: validator lint covered mobile, forms, page-type budgets, and Lovable portability but had no check for the most fundamental accessibility failure — low color contrast on CTAs and body text. The monochromatic-brand derived-accent flow could land a CTA that looked on-brand but was illegible (e.g. forest green on dark background). WCAG math was flagged as "too complex, deferred" but is actually ~50 lines of stdlib code. → Action: implemented `_parse_color()` (hex/rgb/rgba with alpha-compositing-over-white/named), `_relative_luminance()` (WCAG 2.1 formula), `_contrast_ratio()`, and `_extract_css_rule()` that resolves `var(--primary)` against `:root` declarations. Check runs on `body` (4.5:1 min), `.btn` and `.cta` (3.0:1 min — button-as-large-text rule). Falls back to body bg for selectors without their own. Smoke-tested: #111 on #fff → 18.88:1 ✓, #aaa on #fff → 2.32:1 flagged, #fff on brand-primary #2d4a3e → 9.72:1 ✓, #999 on #ccc → 1.77:1 flagged. **RULE:** Once we adopt a derived-accent for a monochromatic brand, the validator is now the safety net catching any accent that renders illegible — not reviewer memory.
