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

If a client wiki or brand-config.json exists in the client folder, load it — brand colors inform dashboard output and previous research provides context about the business, audience, and positioning.

## Process Overview

### Step 1: Intake & Page Capture

**Collect from user:**
- Landing page URL (required)
- Business context: what the page sells, target audience, primary conversion action (form submit, booking, call, etc.)

**Find the client folder.** Scan Desktop for an existing folder matching the organization name (check full names, abbreviations, variations). NEVER create a new folder if one already exists. If found, check for `*/deliverables/brand-config.json` — load it immediately for dashboard colors. Also check for prior research deliverables (wiki/, competitor positioning, buyer personas) that inform the persuasion audit.

**Auto-capture screenshots via Chrome tools (MANDATORY FIRST ACTION).** Read `references/screenshot-capture.md` for the full process. This runs BEFORE HTML analysis. Summary:
1. Navigate to the landing page URL using Chrome
2. Resize browser to mobile viewport (375×667px)
3. Take full-page screenshot (scroll and capture sections if needed)
4. Resize to desktop viewport (1440×900px)
5. Take desktop screenshot
6. Save both to `{client-folder}/sources/` as `{page-name}-mobile.png` and `{page-name}-desktop.png`
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

Save as `{client-folder}/deliverables/{page-name}-landing-page-audit.html`.

### Step 5b: Generate Markdown Findings Report

Produce a structured markdown file alongside the HTML dashboard — portable, shareable, and readable by downstream skills (HTML isn't parseable).

Read `references/markdown-findings-spec.md` for the full template, rules, and rationale.

**File:** `{client-folder}/deliverables/{page-name}-audit-findings.md`

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

<!--
Format: [DATE] [CLIENT TYPE] Finding → Action
Keep under 30 lines. Prune quarterly. See references/feedback-loop.md for protocol.
-->

- [2026-04] [General] Finding: Dashboard specs describing what to build (sections, layout, interactions) without a working HTML scaffold produces broken, unstyled output. Every run reinvents the HTML/CSS/JS from scratch and fails differently. Action: Bundle a complete HTML dashboard template in `assets/dashboard-template.html` with all CSS, Chart.js config, collapsible JS, and dark mode styling pre-built. Skill should populate the template with audit data, not generate HTML from scratch.
- [2026-04] [General] Finding: All 3 test runs independently wrote similar dashboard code — classic signal for bundling a script. Action: Create `scripts/generate_dashboard.py` that takes structured audit JSON and produces the final HTML from the template.
- [2026-04] [General] Finding: Chart.js UMD build requirement is documented in dashboard-specs.md but gets ignored when the model writes HTML from scratch. Having it in the template eliminates this failure mode entirely.
- [2026-04] [General] Finding: Asking users for manual screenshots adds friction and inconsistency. Chrome tools can auto-capture mobile (375×667) and desktop (1440×900) views. Action: Added `references/screenshot-capture.md` with full auto-capture process. Fallback to manual only if Chrome tools unavailable or page requires auth.
- [2026-04-10] [General] Finding: Screenshot placeholder div had `min-height: 600px` with near-invisible hatching pattern, creating ~1400px dark void when no real screenshot is embedded. Looks like a broken page on first scroll past hero. Action: Removed fixed min-height from `.screenshot-container`, added `:has(img)` variant (600px only when screenshot present), reduced placeholder to 180px with dashed border instead of hatching. Applied across all 4 templates.
- [2026-04-10] [General] Finding: Sub-score values (/10) in pillar score tables lacked visual weight — blended into surrounding text on dark background. Action: Added `font-size: 16px` to `.sub-score-val` across all templates.
- [2026-04-10] [General] Finding: Issue card description text was dense and hard to scan. Action: Added `line-height: 1.7` to `.issue-card` across all templates.
- [2026-04-11] [Event/Cultural] Finding: Chrome MCP screenshot fails on Elementor pages below the hero — blank cream background due to headless capture limitations with nested Elementor containers. Action: Discovered computer-use MCP captures actual display pixels and renders Elementor perfectly. Updated screenshot-capture.md with hybrid flow: Chrome MCP navigates/scrolls, computer-use MCP captures. Fallback hierarchy: Chrome capture → computer-use capture (Elementor/JS-heavy) → manual screenshots (last resort).
- [2026-04-11] [Event/Cultural] Finding: Event/festival pages often serve as both content hubs AND landing pages, creating an inherent distraction ratio problem. The page had 5+ competing conversion goals. Action: Audit recommendation should always include "build a focused ad landing page" as a CRITICAL fix when the page is a multi-purpose content page being used for ad traffic.
- [2026-04-11] [General] Finding: Created a new client folder (`ISKM/`) instead of using the existing `Sri Krishna Mandir/` folder on Desktop. Wasted time, had to move files and delete the rogue folder. Action: Step 1 must explicitly scan Desktop for an existing client folder matching the organization name before creating anything. Check for variations (abbreviations, full names).
- [2026-04-11] [General] Finding: brand-config.json existed in the client folder from a prior business-analysis run but was not loaded at intake. Dashboard was generated with manually guessed brand colors and had to be patched afterward. Action: Step 1 intake must always glob for `*/deliverables/brand-config.json` in the client folder. If found, load it and apply colors to the template. Never guess brand colors when a config exists.
- [2026-04-11] [General] Finding: No failure/fallback protocols existed — skills assumed every step succeeds. → Action: Added inline failure handling for blank screenshot captures (Elementor/JS-heavy pages).
- [2026-04-11] [General] Finding: validate_output.py didn't check for unreplaced {{PLACEHOLDER}} text — dashboards could ship with literal placeholder syntax. → Action: Added CRITICAL check for unreplaced {{PLACEHOLDER}} placeholders in HTML output.
- [2026-04-11] [General] Finding: Eval coverage had gaps — no high-scoring page test, no Elementor fallback case, no SaaS page audit. → Action: Added 3 new eval cases (IDs 4-6) covering high-scoring page, Elementor screenshot limitation, and SaaS pricing page edge cases.
- [2026-04-11] [Event/Cultural] Finding: Sri Krishna Mandir Ratha Yatra page had 15+ sections of dense text with minimal visual breaks — the audit caught "Content Hub" as a CRITICAL but didn't systematically score text density or visual rhythm. Pages with text walls score well on individual copy criteria but fail at the macro level. → Action: Added "Content Rhythm & Scannability" (13% weight) to CRO checklist — evaluates consecutive text blocks, visual anchors per scroll height, section layout variety. Not about page length — about sectional breaks with images and whitespace.
- [2026-04-11] [General] Finding: Copy can be well-written but still dense — 500-word unbroken blocks, redundant messaging across sections, educational content where persuasive should be. Reading Level criterion doesn't catch this. → Action: Added "Copy Density & Sectional Flow" (14% weight) to Persuasion checklist — evaluates paragraph length, redundancy, hierarchy within sections, whether copy earns its scroll.
- [2026-04-11] [General] Finding: Screenshot capture was documented as mandatory but agents skipped it, going straight to HTML analysis and leaving placeholder divs in the final dashboard. → Action: Tightened screenshot-capture.md — marked as "MANDATORY FIRST ACTION," added rule that final dashboard must have `<img>` tags not placeholders, updated SKILL.md Step 1 to emphasize capture runs BEFORE analysis.
- [2026-04-11] [General] Finding: HTML dashboard is great for presentation but impractical for quick reference during client calls, email sharing, or downstream skill consumption. Findings locked inside HTML with no portable text format. → Action: Added Step 5b — generate a structured markdown findings report alongside the HTML dashboard. Same issue numbering, same fix recommendations, source labels on all findings. Downstream skills (meta-ad-copywriter, paid-media-strategy) can read the MD directly.
- [2026-04-16] [General] Finding: SKILL.md had grown to 210 lines — breached the <200 line progressive-disclosure rule from skill-architecture-standards.md. The fattest section was Step 5b (Markdown Findings Report) with a 40-line inline template. → Action: Moved the full template, rules, and rationale into `references/markdown-findings-spec.md`. Trimmed Step 5b to a pointer with the file path and key constraints only. SKILL.md now 167 lines.
- [2026-04-16] [Validator hardening] Finding: two real gaps that let incomplete audits ship. (a) Placeholder regex only caught `{{PLACEHOLDER}}` — `[PLACEHOLDER]`, `{PLACEHOLDER}` (single-brace), and `${PLACEHOLDER}` variants would pass silently, even though Step 5's templates and analyst notes sometimes use them. (b) Step 5b (Markdown Findings Report, added today) was never validated — the markdown file could be missing entirely and validation would still pass, defeating the point of the new portable format. → Action: (a) expanded placeholder check to four pattern families with length guards (≥3-char keys) so CSS `{color:red}` / markdown `[link]` don't false-positive; (b) added CRITICAL check that derives the expected markdown filename (`…-landing-page-audit.html` → `…-audit-findings.md`, with a looser `-findings.md` fallback) and blocks delivery if it's missing. Both fire on deliberate negative cases in the smoke test.
