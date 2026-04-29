---
name: landing-page-audit
description: "Landing page conversion audit from CRO, visual UI/UX, and persuasion/copy perspectives. Analyzes screenshots and URLs of lead gen and booking/event pages to produce a scored audit with priority-ranked issues and full mockup-level fix recommendations. Outputs a premium HTML dashboard (dark mode, annotated screenshots + section cards). Use when user mentions: landing page audit, page review, conversion audit, CRO review, LP analysis, why isn't my page converting, review my landing page, page UX feedback, form optimization, CTA review, above the fold check, landing page score, conversion rate optimization review, page redesign recommendations. Also trigger when user shares a landing page URL or screenshots asking for feedback. Do NOT trigger for ad copy writing, full website redesign, SEO audits, page speed/technical audits, or campaign performance reporting."
---

# Landing Page Conversion Audit

Systematic audit of landing pages from three perspectives — CRO fundamentals, visual UI/UX, and persuasion & copy — producing a scored, actionable report with mockup-level fix recommendations. Designed for lead gen and booking/event pages before ad traffic hits them.

## Context Loading

Read these shared context files before starting:
- `shared-context/analyst-profile.md` — workflow, client types, quality standards
- `shared-context/accuracy-protocol.md` — accuracy rules for all assessments
- `shared-context/output-structure.md` — write final HTML/MP4/PDF to the client/program folder root; intermediate MD/JSON to `_engine/working/`; raw screenshots/inputs to `_engine/sources/`
- `shared-context/client-shareability.md` — client-facing files must read like first copies; no correction trails / audit history / internal-process commentary. Validator: `python3 ~/.claude/scripts/check_client_shareability.py {client}`

If a client wiki or brand-config.json exists in the client folder, load it — brand colors inform dashboard output and previous research provides context about the business, audience, and positioning.

## Process Overview

### Step 0: Pre-flight (MANDATORY — run before any client work)

Before invoking this skill on a client URL, verify the skill is healthy and pick the right capture recipe for the target page type.

1. **Health check** — run `scripts/health_check.py`. It verifies fixtures still classify correctly, required references exist, templates are intact, and the validator loads. If the exit code is non-zero, the skill is broken — do NOT proceed on a client page. Per CLAUDE.md Skill Protocol Supremacy: stop, patch, re-run.

2. **Target profile detection** — run `scripts/detect_target_profile.py <client_url>`. It fingerprints the page and returns a recipe ID (`react-spa-countup` / `elementor-wordpress` / `static-html` / `webflow` / `squarespace` / `shopify` / `wordpress-generic`).

3. **Load the recipe** — read `references/capture-recipes/<profile>.md`. Each recipe has profile-specific pitfalls, the correct capture protocol, DOM-verify rules, and what NOT to do. Follow it literally in Step 1.

If the detected profile has no recipe yet (gap), stop and write the recipe before running — per Skill Protocol Supremacy.

### Step 1: Intake & Page Capture

**Collect from user:**
- Landing page URL (required)
- Business context: what the page sells, target audience, primary conversion action (form submit, booking, call, etc.)

**Find the client folder.** Scan Desktop for an existing folder matching the organization name (check full names, abbreviations, variations). NEVER create a new folder if one already exists. If found, check for `*/_engine/brand-config.json` — load it immediately for dashboard colors. Also check for prior research deliverables (`_engine/wiki/`, competitor positioning, buyer personas) that inform the persuasion audit.

**Auto-capture screenshots via Chrome tools (MANDATORY FIRST ACTION).** Read `references/screenshot-capture.md` for the full process. This runs BEFORE HTML analysis. Summary:
1. Navigate to the landing page URL using Chrome
2. Resize browser to mobile viewport (375×667px)
3. Take full-page screenshot (scroll and capture sections if needed)
4. Resize to desktop viewport (1440×900px)
5. Take desktop screenshot
6. Save both to `{client-folder}/_engine/sources/` as `{page-name}-mobile.png` and `{page-name}-desktop.png`
7. Screenshots MUST be embedded as `<img>` tags in the final dashboard — no placeholders

If Chrome tools are unavailable or the page requires authentication, fall back to asking the user for manual screenshots.

**If screenshot shows blank below hero** (Elementor/heavy JS rendering): switch to computer-use MCP hybrid capture — Chrome MCP navigates and scrolls, computer-use MCP screenshots the actual display. See `references/screenshot-capture.md` for full flow. Only fall back to manual screenshots if computer-use is also unavailable.

**Capture page HTML:** Use WebFetch on the URL to pull page source for structural analysis (form fields, heading hierarchy, link count, meta tags). Screenshots provide the visual/UX layer. Both inputs are needed — HTML for structure, screenshots for what users actually see.

### Step 2: Audit — Three Pillars

Run the audit across all three pillars. Read each reference file as you enter that pillar — they contain the detailed criteria, scoring rubrics, and best-practice benchmarks.

**Pillar 1: CRO Fundamentals**
Read `references/cro-checklist.md`. Evaluate: headline clarity, CTA placement & copy, form friction, trust signals, social proof, urgency/scarcity, above-the-fold content, distraction ratio, page goal clarity, **content rhythm & scannability** (text walls, visual breaks, section variety).

**Pillar 2: Visual UI/UX**
Read `references/visual-ux-checklist.md`. Evaluate: visual hierarchy, layout & whitespace, color contrast & accessibility, typography, image quality & relevance, mobile responsiveness, visual flow (eye tracking patterns), interactive element clarity, loading skeleton/perceived speed.

**Pillar 3: Persuasion & Copy**
Read `references/persuasion-copy-checklist.md`. Evaluate: message-market match, benefit vs feature framing, specificity of claims, objection handling, headline formulas, subhead support, microcopy quality, emotional triggers, reading level appropriateness, **copy density & sectional flow** (text walls, redundancy, structural hierarchy within sections).

**Mobile-first priority:** Evaluate mobile experience first for every pillar. Desktop is secondary. Most ad traffic (especially Meta) lands on mobile — if mobile fails, the page fails.

### Step 3: Score & Prioritize

Read `references/scoring-framework.md` for the rubric.

**Section scores:** Rate each pillar 1-10 with sub-scores per criterion. Calculate an overall Conversion Readiness Score (weighted: CRO 40%, Visual UX 30%, Persuasion 30%).

**Issue ranking:** Compile all findings into a single priority-ranked list:
- 🔴 CRITICAL — actively killing conversions, fix before running any ads
- 🟡 MAJOR — significant drag on conversion rate, fix within first sprint
- 🟢 MINOR — polish items, fix when time allows

Each issue gets: what's wrong, why it hurts conversions, and a specific fix recommendation with mockup-level detail (rewritten copy, layout change description, wireframe guidance).

### Step 4: Generate Fix Recommendations

This is the highest-value part of the audit. For each issue:
- **Copy issues:** Provide the exact rewritten headline, CTA, or body text — not "make it more compelling" but the actual words.
- **Layout issues:** Describe the specific rearrangement with element-by-element guidance (e.g., "Move testimonials block from below the fold to directly above the form. Place 2 testimonials side-by-side with star ratings visible.")
- **Visual issues:** Specify color values, spacing adjustments, font size changes. Reference the brand palette when available.
- **Form issues:** Specify which fields to remove, reorder, or rewrite labels for.

The output should be detailed enough that a developer or page builder user can implement changes without further interpretation.

### Step 5: Generate HTML Dashboard

Read `references/dashboard-specs.md` for the full specification, including template selection logic.

**Select the template** from `assets/` based on page type and audience:

| Page Type | Client-Facing | Internal |
|-----------|--------------|----------|
| Restaurant, wellness, salon, local service | `template-local-services.html` | `template-internal-quick.html` |
| Retreat, workshop, training, event booking | `template-booking-event.html` | `template-internal-quick.html` |
| B2B IT, consulting, professional services | `template-b2b-leadgen.html` | `template-internal-quick.html` |

Default to client-facing unless user explicitly says "internal" or "quick audit." If page type is ambiguous, ask.

**Populate the template:** Read the selected template from `assets/`. Replace all `{{PLACEHOLDER}}` variables with actual audit data — scores, findings, fix recommendations, brand colors. Do NOT generate HTML from scratch. The templates have all CSS, Chart.js config, collapsible JS, animations, and dark mode pre-built.

**Template-specific sections to populate:**
- **Local services:** Trust & Social Proof panel (Google reviews, testimonials, real photos status)
- **Booking/event:** Urgency checklist + Transformation narrative (before → after)
- **B2B:** Credibility panel (certs, case studies, SLAs, insurance) + Form field analysis (keep/remove/optional per field)
- **Internal quick:** Compact scores, flat issue list with inline fixes, internal notes, downstream flags

**Screenshot annotations:** Place numbered marker divs inside the screenshot container using CSS `position: absolute` with `top` and `left` percentages. Replace the placeholder div with an actual `<img>` tag if screenshot files are available.

Save as `{client-folder}/{page-name}-landing-page-audit.html` (folder root — it's a presentable).

### Step 5b: Generate Markdown Findings Report

Produce a structured markdown file alongside the HTML dashboard — portable, shareable, and readable by downstream skills (HTML isn't parseable).

Read `references/markdown-findings-spec.md` for the full template, rules, and rationale.

**File:** `{client-folder}/_engine/working/{page-name}-audit-findings.md`

Key constraints: same issue numbering as the HTML dashboard, identical fix recommendations (no summarizing), `[EXTRACTED]`/`[INFERRED]` tags on every finding.

### Step 6: Validate & Evolve (Mandatory — Never Skip)

**Validate:** Run `scripts/validate_output.py {dashboard_path}`. Fix CRITICAL failures before delivery.

**Evolve:** Read `references/feedback-loop.md`. Capture what worked/didn't. Add learnings below.

**Flag downstream:** Note connections — "CTA copy rewrite ready for meta-ad-copywriter to align ad → page messaging" or "form friction findings relevant for paid-media-strategy audience targeting."

## Output Checklist

- [ ] All three pillars audited with specific findings (not generic advice)
- [ ] Every finding tied to a conversion impact explanation
- [ ] Mobile experience audited first, desktop second
- [ ] Section scores (1-10) for each pillar + overall Conversion Readiness Score
- [ ] Priority-ranked issue list (CRITICAL / MAJOR / MINOR)
- [ ] Fix recommendations include exact copy rewrites, not vague suggestions
- [ ] Layout fixes include element-level specificity
- [ ] Dashboard uses annotated screenshots at top
- [ ] Dashboard uses client brand colors (not defaults)
- [ ] Chart.js visualizations for scores (not just numbers)
- [ ] All assessment criteria have tooltips explaining the rating
- [ ] No generic "improve your CTA" advice — everything specific to THIS page
- [ ] Markdown findings report generated alongside HTML dashboard
- [ ] Issue numbering consistent between MD and HTML files
- [ ] MD file has source labels ([EXTRACTED]/[INFERRED]) on all findings

## Learnings & Rules
<!-- Format: [DATE] [CLIENT TYPE] Finding → Action. Keep under 30 lines. Prune quarterly. See references/feedback-loop.md for protocol. -->
- [2026-04] [General] Finding: Dashboard specs describing what to build (sections, layout, interactions) without a working HTML scaffold produces broken, unstyled output. Every run reinvents the HTML/CSS/JS from scratch and fails differently. Action: Bundle a complete HTML dashboard template in `assets/dashboard-template.html` with all CSS, Chart.js config, collapsible JS, and dark mode styling pre-built. Skill should populate the template with audit data, not generate HTML from scratch.
- [2026-04] [General] Finding: All 3 test runs independently wrote similar dashboard code — classic signal for bundling a script. Action: Create `scripts/generate_dashboard.py` that takes structured audit JSON and produces the final HTML from the template.
- [2026-04] [General] Finding: Chart.js UMD build requirement is documented in dashboard-specs.md but gets ignored when the model writes HTML from scratch. Having it in the template eliminates this failure mode entirely.
- [2026-04] [General] Finding: Asking users for manual screenshots adds friction and inconsistency. Chrome tools can auto-capture mobile (375×667) and desktop (1440×900) views. Action: Added `references/screenshot-capture.md` with full auto-capture process. Fallback to manual only if Chrome tools unavailable or page requires auth.
- [2026-04-10] [General] Finding: Screenshot placeholder div had `min-height: 600px` with near-invisible hatching pattern, creating ~1400px dark void when no real screenshot is embedded. Looks like a broken page on first scroll past hero. Action: Removed fixed min-height from `.screenshot-container`, added `:has(img)` variant (600px only when screenshot present), reduced placeholder to 180px with dashed border instead of hatching. Applied across all 4 templates.
- [2026-04-10/11] [General — CONSOLIDATED] Template + validator + intake fixes: (a) sub-score values sized 16px, issue-card line-height 1.7 across all templates for scanability; (b) Chrome MCP fails on Elementor pages below hero → fall back to computer-use MCP for screenshot; (c) event/festival hybrid pages have inherent distraction — always recommend "build a focused ad LP" as CRITICAL in those audits; (d) ALWAYS scan Desktop for existing client folder (name variants) before creating new; (e) ALWAYS glob `*/_engine/brand-config.json` at intake — never guess brand colors; (f) validator checks for unreplaced `{{PLACEHOLDER}}` as CRITICAL; (g) eval cases 4-6 cover high-scoring, Elementor-fallback, SaaS-pricing edge cases.
- [2026-04-11] [General — CONSOLIDATED] Rubric + process tightening: (a) added "Content Rhythm & Scannability" (13% weight) to CRO checklist — evaluates sectional breaks with images/whitespace, not raw page length; (b) added "Copy Density & Sectional Flow" (14% weight) to Persuasion checklist — catches dense well-written copy (500-word blocks, redundancy, educational-over-persuasive); (c) screenshot-capture.md marked "MANDATORY FIRST ACTION" — final dashboard MUST have `<img>` tags, never placeholder divs; (d) added Step 5b — markdown findings report alongside HTML dashboard for client-call + downstream-skill consumption.
- [2026-04-16] [General] Finding: SKILL.md had grown to 210 lines — breached the <200 line progressive-disclosure rule from skill-architecture-standards.md. The fattest section was Step 5b (Markdown Findings Report) with a 40-line inline template. → Action: Moved the full template, rules, and rationale into `references/markdown-findings-spec.md`. Trimmed Step 5b to a pointer with the file path and key constraints only. SKILL.md now 167 lines.
- [2026-04-16] [Validator hardening] Finding: two real gaps that let incomplete audits ship. (a) Placeholder regex only caught `{{PLACEHOLDER}}` — `[PLACEHOLDER]`, `{PLACEHOLDER}` (single-brace), and `${PLACEHOLDER}` variants would pass silently, even though Step 5's templates and analyst notes sometimes use them. (b) Step 5b (Markdown Findings Report, added today) was never validated — the markdown file could be missing entirely and validation would still pass, defeating the point of the new portable format. → Action: (a) expanded placeholder check to four pattern families with length guards (≥3-char keys) so CSS `{color:red}` / markdown `[link]` don't false-positive; (b) added CRITICAL check that derives the expected markdown filename (`…-landing-page-audit.html` → `…-audit-findings.md`, with a looser `-findings.md` fallback) and blocks delivery if it's missing. Both fire on deliberate negative cases in the smoke test.
- [2026-04-16] [Chart.js + markers — closes Phase 3 blind spots] Finding: two correctness gaps that would let the client see contradictory numbers and orphan markers. (a) Chart.js datasets vs textual scores weren't cross-checked — a dashboard could display "CRO 7/10" in text while the radar chart rendered the dataset as `[5, 6, 7, 8]` with the 7 in a different position, or an Overall gauge showing 8.0 while individual pillars weighted to 5.3. (b) Screenshot markers weren't mapped to the issue list — marker #99 could float alone, CRITICAL issue #5 could exist without a marker, marker severity color could mismatch issue severity. → Action: (a) parse `createGauge(id, score, 10)` and `createRadar(id, labels, [scores])` call-site arguments, compare against textual `X/10` values in the HTML body; verify `overall = CRO×0.4 + Visual×0.3 + Persuasion×0.3` within ±0.5 tolerance using the authoritative `gaugeOverall/CRO/Visual/Persuasion` calls. (b) parse `<div class="marker critical|major|minor">N</div>` and issue headings with severity context from surrounding text; flag orphan markers, missing markers for CRITICAL/MAJOR issues, and severity-class mismatches. Smoke-tested on positive case (3 consistent markers, weighted avg 6.30 matches 6.4) and negative case (marker #99 orphan, issue #5 missing marker, #1 marker=minor but issue=critical, weighted 5.3 vs declared 8.0). **RULE:** Chart numbers + marker numbers + text scores form a three-way contract with the client. The dashboard is one artifact with three views; all three must agree.
- [2026-04-17] [React SPA — ISKM Singapore] Finding: First landing-page audit on a Lovable/GPT-Engineer React SPA revealed two systemic issues that single-page audits on WordPress/Webflow don't surface: (a) Image asset pipeline can silently break in production — Lovable asset URLs point to dev-only `gpt-engineer-file-uploads` hostnames; 19+ images (hero, 6 cards, 12 gallery) all rendered as blank placeholders while the page itself scored well on copy and structure; (b) A single broken subsystem (images) can destroy Visual UX score on a page that's otherwise solid — Visual UX 6.4/10 with image-quality at 1/10; remove that one issue and it jumps to 8+. → Learning: When auditing Lovable/Bolt/GPT-Engineer React SPAs, always check image <img src> URLs in devtools for dev-only hostnames as a first pass, and call out asset-pipeline brittleness as a CRITICAL finding tied to production readiness, not just design quality. The asset pipeline becomes the page's silent conversion killer.
- [2026-04-17] [Multi-program naming] Finding: Validator expected markdown findings filename `iskm-nrsimha-caturdasi-2026-audit-findings.md` (derived from HTML as `-landing-page-audit.html` → `-audit-findings.md`). Initially saved as `iskm-nrsimha-caturdasi-2026-landing-page-audit-findings.md` (appended `-landing-page-audit-findings` verbatim). → Learning: The derived-filename rule strips `landing-page-audit` and adds `audit-findings`. Follow the validator's naming contract exactly on first write — or the file lives in two places briefly. Also: any "X/10" pattern in flavor text (e.g., "jumps to ~8.5/10") triggers the chart-text consistency check even if it's aspirational narrative, not an actual score. Use phrasing like "upper-8 range" instead when referencing hypothetical post-fix scores.

- [2026-04-17] [React SPA — false-positive prevention] Scroll-triggered fade-in + CountUp animations on React SPAs captured mid-animation produced 3 phantom CRITICAL findings (imagined broken images, stat contradiction, missing diacritics) on ISKM Nrsimha Caturdasi audit where actual page was fine. → Action: (a) inject animation-kill CSS as first pre-step before any screenshot — see references/screenshot-capture.md 'Kill Page Animations'; (b) any content-missing CRITICAL must carry DOM-verification ack — see references/screenshot-capture.md 'DOM-First Rule'; (c) scripts/validate_output.py now WARNs when CRITICAL claims match broken-image-class patterns without a DOM-verified note; (d) eval #7 covers the scenario.

- [2026-04-17] [Tooling gap — Chrome MCP mobile] `resize_window` tool succeeds but does not constrain `window.innerWidth` — media queries don't trigger mobile breakpoints, so screenshots taken after a 375×812 resize are still effectively desktop. → Action: patched `references/screenshot-capture.md` with mobile-capture fallback order (user-supplied mobile screenshot → computer-use iPhone mirror → desktop-only with explicit mobile-not-verified flag). NEVER hack viewport via CSS — React SPAs read innerWidth and won't respond. Visual UX mobile-responsiveness criterion must be marked 'not verified' when Chrome MCP is the only capture path.

- [2026-04-17] [Tooling gap — JS counters] `animation-kill` CSS stops CSS transitions but NOT JavaScript-driven number counters (CountUp.js, react-countup). Screenshots can show `1+`, `9+`, `34+`, `306+` mid-animation for stat bars whose target is `50+`, `500+`, `10+`, `30+`. → Action: patched `references/screenshot-capture.md` with 3-strategy counter freeze (data-* attribute text override, rAF monkey-patch to flush loops, Date.now advance by 60s). Plus mandated: DOM-verify any number read from a screenshot before treating as audit data. Verified live on ISKM page — DOM settled to 50+/500+/10+/30+ after 10s wait and queryselector on .stat-number.

- [2026-04-17] [Protocol self-correction] Counter-freeze strategies from previous same-day learning (rAF monkey-patch + Date.now advance) BROKE the CountUp library — stats that would naturally settle to 50+/500+ got stuck at 0+ after the patches were applied, because counter libraries read performance.now() diffs and fake-future timestamps corrupt their math. → Action: reverted `references/screenshot-capture.md` to the correct minimal protocol: CSS kill + scroll-through + wait 10-15s + DOM-verify. No rAF/Date.now monkey-patching. Demonstrated skill-correction: not every 'fix' is an improvement — live testing revealed the 'fix' made things worse.

- [2026-04-17] [Structural — pre-flight gate] Skill got patched 3 times in one session chasing page-category gaps on live client work. → Action: added Step 0 (pre-flight) with `scripts/health_check.py` (gate), `scripts/detect_target_profile.py` (target fingerprint), `scripts/test_fixtures.py` (classification smoke), 3 saved fixtures under `evals/fixtures/`, and 3 recipe playbooks under `references/capture-recipes/` (react-spa-countup, elementor-wordpress, static-html). RULE: health_check must pass before running on any client URL. Detection gaps become skill improvements, not silent audit errors.

- [2026-04-17] [Pre-flight gap closed — wordpress-generic recipe] First client run on a custom-theme WP page (thriveretreats.com.au) hit detector output `wordpress-generic` with no matching recipe. Per Skill Protocol Supremacy, paused client work, wrote `references/capture-recipes/wordpress-generic.md` (covers Lenis/Slick smooth-scroll quirks, lazy-img defer, Yoast schema vs body drift, CF7 honeypot exclusion from friction score, cache-plugin staleness), added `evals/fixtures/wordpress-generic.html`, registered in `test_fixtures.py` EXPECTATIONS. Health check now reports 4/4. Rule holds: detection gaps become skill improvements, not silent audit errors.

- [2026-04-17] [Contrast claim — always DOM-verify computed colors] ISKM Nṛsiṁha re-run #5 caught a persistent error that survived 4 prior validations: audit said "pink CTA #fb9ebb on cream = 2.8:1 fails WCAG AA" — actual DOM `getComputedStyle` returned `background: rgb(248,164,192)` + `color: rgb(30,58,110)` = deep-navy text on salmon pink, ~6:1 passes AA. The wrong white-text assumption persisted because nobody ran `getComputedStyle` on the live button. → RULE for every Color Contrast finding: before flagging an AA/AAA failure, run `getComputedStyle(btn).backgroundColor` AND `.color` on the actual DOM node, compute the ratio, and tag the finding `[EXTRACTED — DOM getComputedStyle]`. Never infer contrast from a hex pulled out of the CSS file or a screenshot — React/framework wrappers and cascade overrides shift the rendered result. Applies to buttons, links, form labels, badges, any text-on-color element.

- [2026-04-18] [Higher-ed admission — dead-CTA detection via DOM click simulation] NIMS University Marik Admission 2026 audit caught two production-blocker CRITICAL issues that would not have been visible from screenshot inspection alone: (a) the page's primary in-content CTA "Talk to Admission Counsellor" was an `<a href="#">` with no bound listener — looks clickable, does literally nothing, verified via `cta.click()` + before/after URL+scroll+modal-count diff; (b) three "View Course List →" spans on the program cards carried `cursor:pointer` and an arrow glyph but were wrapped in `<span>`, not `<a>`, and the parent `.program-card` had no listener — verified by `card.click()` + null-change diff. Both would have slipped past a purely visual audit. → RULE for every landing page: run a DOM click simulation on every visible button/link-looking element. If `location.href`, `document.body.innerHTML.length`, scroll position, and visible-modal-count are all unchanged 200ms after `el.click()`, the element is a dead CTA — log CRITICAL. Cheap to run, catches high-impact production bugs that only manifest for users, not reviewers.

- [2026-04-18] [Chrome MCP output filter — URL/JSON blocking workaround] Multiple `javascript_tool` calls returning `JSON.stringify({...})` came back `[BLOCKED: Cookie/query string data]` even though the data contained nothing sensitive — the output filter treats URL-like strings inside JSON as cookie/query material. Plain string concatenation (`'k1:' + v1 + ' // k2:' + v2`) passed through immediately. → RULE: for Chrome MCP `javascript_tool` when extracting DOM data, prefer flat string concatenation over `JSON.stringify()`. If you need structured output, use pipe/double-pipe separators (`'a=1 || b=2'`) and parse on the way back. Saves 3-4 retried tool calls per audit.

- [2026-04-18] [CMS admin-UI leakage — new finding pattern on higher-ed pages] NIMS Marik page shipped with 147 "modal" elements, a `<form>` containing `script_editor` / `custom_script_autoload` / `custom_script_fields` textareas, and hidden controls for Yes/Cancel/Save Anyway/Resubscribe User/Re-assign User/purgeDeleteModalInput. This is the CMS landing-page-builder's admin UI leaking into the published HTML. Not visible to users but bloats DOM, signals rushed QA, and is one CSS bug away from exposing admin controls to end users. → RULE for every audit: grep the DOM for common admin-UI tokens (`script_editor`, `purgeDelete`, `Resubscribe`, `Re-assign User`). If found, log as CRITICAL technical-hygiene finding — it's cheap to detect and meaningful when present. NopaperForms builder + similar Indian ed-tech CMSes show this pattern frequently.

- [2026-04-19] [WordPress custom theme — Thrive Midweek Reset] Hero-banner file size check caught a 1.0 MB uncompressed PNG (1,082,890 bytes, 2560×960, rendered at ~1455×718) served as the LCP element — 3.6× over the wordpress-generic recipe's 300 KB threshold and not in WebP. Detected by downloading via `curl` + `du` after reading `currentSrc` from DOM. → RULE: add hero-image weight check as a standard step whenever capturing a WordPress page. One-liner: `curl -s -o /tmp/hero.png "$URL" && du -h /tmp/hero.png`. Flag CRITICAL if >300 KB or not WebP — directly hurts LCP and paid-traffic quality scores.

- [2026-04-19] [Sticky-bar layout bug — DOM-verify + screenshot-verify both] Thrive Midweek Reset page had a fixed-position `section.cta.sticky-bottom` (z-index 99999) containing an H2 at x=88 with a "CLAIM 5% OFF" pill overlapping the first ~100px, cropping "Hit" on desktop viewport. Detected by reading `getBoundingClientRect()` on the H2 AND screenshot inspection — DOM rect alone would not have surfaced this (DOM is correct; rendering collides). → RULE: whenever a `position:fixed`/`sticky` container holds both a headline AND adjacent pills/badges/buttons, take a desktop screenshot AND check whether the headline's left edge collides with siblings' right edge. Visible-only bug — no DOM query will catch it alone.

- [2026-04-19] [OG:image audit — always check] Missing `<meta property="og:image">` on Thrive Midweek Reset broke social-share previews for a retreat business that leans on WhatsApp/FB community shares. Zero preview image cuts expected share CTR by 50–65%. → RULE: add OG-image/OG-description to the standard intake check for every client page. `document.querySelector('meta[property="og:image"]')?.content` — if empty, log CRITICAL for shareable/event/retreat pages; MAJOR for B2B/lead-gen.

- [2026-04-19] [Validator false-positive — marker severity matching across action-plan] Validator flagged markers #8, #10, #11 as "marker=major, issue=critical" when all three ARE correctly major in the issue list. Root cause: validator scans the entire HTML for proximity of "critical" to "Issue #N" and matches the action-plan section, where critical and major issues are referenced together by number. → Known false positive when an "Action Plan" section exists and references multiple severities by issue number. Safe to ship with this warning. Future validator fix: scope the severity-match lookup to issue-card blocks only, not action-plan blocks.

- [2026-04-19] [Screenshot marker numbering contract] First write used abstract marker numbers (1–5) keyed to visual regions, not to issue numbers — validator correctly flagged them as orphans. Re-numbered markers to match issue IDs (#1, #4, #8, #10, #11) and updated the legend. → RULE: screenshot markers MUST use the same numbering as the issue list. If issue #10 is marked on the hero, the marker renders "10", not "4". This preserves the three-way contract (chart numbers + marker numbers + text scores) even when only a subset of issues is visualised.

- [2026-04-20] [Intake gap — must read wiki/business.md BEFORE scoring] Thrive Midweek Reset audit shipped with "Issue #2: no lead-capture form" as a CRITICAL — but `_engine/wiki/business.md` at line 31 had an existing rule from 2026-04-17 saying all Book Now CTAs redirect to Booking Layer by design and LP audits should not flag this as a CRO gap. The audit didn't respect that rule because Step 1 intake only globs for `brand-config.json`, not for `_engine/wiki/business.md`. User caught it and asked to update, then asked for the rule to be persisted to the wiki — which it already was. → RULE: Step 1 (Intake & Page Capture) MUST glob for `{client-folder}/_engine/wiki/business.md` AND `{client-folder}/_engine/wiki/index.md` when they exist. Read both. Respect the conversion-model, booking-system, and campaign-objective notes BEFORE scoring form friction, lead-gen criteria, or recommending capture forms. If `_engine/wiki/index.md` has a "⚠ MUST-READ" section, load it into the audit's opening context. Strengthened this client's wiki: `business.md` → explicit "DIRECT PURCHASE ONLY, NO LEAD CAPTURE" paragraph; `index.md` → top-of-file warning. Future Thrive Retreats LP audits, ad briefs, and media strategies will read the warning and avoid re-committing the same scope error.
- [2026-04-27] [Universal — applies to all skills] Same-Client Re-Run Rule landed in CLAUDE.md as a universal Always-Active section. Same-client/same-case re-runs overwrite outputs in place — no v1/v2/v3, no -DATE parallel filenames, no dated section headers preserving prior content. One file per role, current state only. Only `_engine/wiki/log.md` (by-design change log) and `_engine/wiki/briefs.md` (brief history with `[ACTIVE]`/`[SUPERSEDED]` markers) are append-only. **For this skill specifically:** {client}/PAGE-NAME-landing-page-audit.html (folder root), {client}/_engine/working/PAGE-NAME-audit-findings.md, {client}/_engine/sources/PAGE-NAME-mobile.png, {client}/_engine/sources/PAGE-NAME-desktop.png — all overwritten in place on re-run. **RULE:** if you find yourself about to create a new file for an output that has the same logical role as an existing one, stop and overwrite the existing file instead.
- [2026-04-29] [STRUCTURAL REFACTOR] Folder convention changed: all skill internals (wiki, sources, working, configs) now live in `_engine/` subfolder; presentables (HTML/PDF/CSV/MP4) at folder root. Audit dashboard HTML stays at folder root (presentable); markdown findings go to `_engine/working/`; screenshot inputs go to `_engine/sources/`. → Updated all path references in SKILL.md, references/, scripts/, evals/.
