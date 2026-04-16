# Landing Page Audit Dashboard Specifications

The dashboard is produced by populating a pre-built HTML template from `assets/`. NEVER generate HTML from scratch — the templates have all CSS, Chart.js config, animations, and dark mode pre-built. Your job is to select the right template and replace the `{{PLACEHOLDER}}` variables with audit data.

---

## Template Selection

Four templates are available in `assets/`:

| Template | File | When to Use |
|----------|------|-------------|
| Local Services | `template-local-services.html` | Restaurants, wellness, salons, local service businesses. Highlights trust signals, social proof, real photos. |
| Booking / Event | `template-booking-event.html` | Retreats, workshops, trainings, event registrations. Highlights urgency/scarcity, transformation narrative, pricing presentation. |
| B2B Lead Gen | `template-b2b-leadgen.html` | IT services, consulting, professional services. Highlights credibility (certs, case studies, SLAs), form field analysis (keep/remove/optional). |
| Internal Quick | `template-internal-quick.html` | Your own pre-campaign checks. Stripped down — compact scores, flat issue list, internal notes, downstream flags. No animations. Print-friendly. |

**Selection rules:**
- Default to client-facing (one of the first three) unless user says "internal" or "quick audit"
- Choose based on the business type identified during intake
- If the page type doesn't cleanly fit one category, pick the closest match and note why

## How to Populate Templates

1. Read the selected template file from `assets/`
2. Replace every `{{PLACEHOLDER}}` with the actual audit data
3. For score colors, use: `score-green` (7+), `score-amber` (5-6.9), `score-red` (<5)
4. For Chart.js gauge/radar initialization at the bottom of the template, replace the score values directly
5. For section content (sub-scores, issues, findings), generate the HTML fragments and insert at the marked comment locations
6. Save the populated HTML to the client deliverables folder

### Placeholder Reference

**Global:** `{{PAGE_NAME}}`, `{{PAGE_URL}}`, `{{BRAND_NAME}}`, `{{CONSULTANT}}`, `{{AUDIT_DATE}}`, `{{PRIMARY_COLOR}}`, `{{DARK_BG}}`

**Scores:** `{{OVERALL_SCORE}}`, `{{CRO_SCORE}}`, `{{VISUAL_SCORE}}`, `{{PERSUASION_SCORE}}` (numeric), plus `{{*_SCORE_CLASS}}` (score-green/score-amber/score-red), `{{OVERALL_INTERPRETATION}}` (text explanation)

**Radar charts:** `{{CRO_RADAR_LABELS}}` (comma-separated quoted strings), `{{CRO_RADAR_SCORES}}` (comma-separated numbers). Same pattern for VISUAL and PERSUASION.

**Content sections:** `{{CRO_SUB_SCORES}}`, `{{CRO_DETAILED_FINDINGS}}`, `{{CRO_KEY_INSIGHT}}`, etc. — generate HTML fragments matching the template's CSS classes.

**Issues:** `{{CRITICAL_ISSUES}}`, `{{MAJOR_ISSUES}}`, `{{MINOR_ISSUES}}` — generate issue-card divs with collapse-btn/collapse-body for fix details.

**Template-specific:** Local services has `{{GOOGLE_REVIEWS_STATUS}}`, booking/event has `{{URGENCY_CHECKLIST_ITEMS}}` and `{{TRANSFORM_BEFORE/AFTER}}`, B2B has `{{CREDIBILITY_ITEMS}}` and `{{FORM_FIELDS_ANALYSIS}}`.

---

## Design Philosophy

- **Hybrid presentation.** Screenshots first (show problems visually), then structured analysis cards (detail each finding).
- **Dark mode default.** Use brand-config.json if available, otherwise use a professional dark theme.
- **Severity-coded.** Red/yellow/green color coding throughout for instant priority reading.
- **Actionable over analytical.** Every finding connects directly to a specific fix recommendation.
- **Mobile-responsive.** The dashboard itself must work on tablet/desktop for client presentation.

## Required Libraries

- **Chart.js 4.x** — MUST use the UMD build: `https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js`. The cdnjs `chart.min.js` is ESM-only and does NOT register a global `Chart` object.
- **No other external dependencies.** All CSS inline. All JS vanilla.

---

## Layout Structure

### 1. Navigation
- Sticky top nav: `background: var(--dark)`
- Section links: Overview, Screenshots, CRO, Visual UX, Persuasion, Issues, Recommendations
- Brand name or "Landing Page Audit" as first nav item
- Active section highlighting on scroll

### 2. Hero Section
- Full-width gradient using brand dark color
- Page name/URL and audit title
- Date and consultant info
- **Score summary row:** 4 gauge/donut charts side by side:
  - Overall Conversion Readiness Score (largest)
  - CRO Fundamentals score
  - Visual UI/UX score
  - Persuasion & Copy score
- Score label with color: green (7+), amber (5-6), red (<5)
- Tooltip on each score explaining the weight breakdown

### 3. Annotated Screenshot Section
- **This is the highest-impact section** — clients immediately see their page with problems marked.
- Display uploaded screenshot(s) at full width
- Overlay numbered markers on the screenshot pointing to specific issues
- Markers color-coded: 🔴 red circle = CRITICAL, 🟡 yellow = MAJOR, 🟢 green = MINOR
- Below the screenshot, a legend mapping each marker number to the issue summary
- If both mobile and desktop screenshots: show mobile screenshot first (larger), desktop second

**Implementation approach:**
- Place screenshot as background of a positioned container
- Use absolutely positioned marker elements (numbered circles) at the approximate locations of issues
- Markers should be interactive — click/hover reveals the issue detail

### 4. Pillar Cards (CRO, Visual UX, Persuasion)

Each pillar gets a full-width card:

```
Pillar Title + Score Badge (e.g., "CRO Fundamentals · 6.8/10")
├── Radar chart showing sub-scores across all criteria
├── Sub-score breakdown (criterion name + score + one-line finding)
│   Each sub-score row is color-coded by score (green/amber/red)
├── Collapsible: Detailed findings per criterion
│   └── What's wrong, why it hurts, specific fix recommendation
└── Key insight callout (most impactful finding from this pillar)
```

### 5. Priority Issue List

Full-width section listing ALL issues across all pillars, sorted by severity:

```
🔴 CRITICAL Issues (fix before ads)
├── Issue title + pillar badge + criterion
├── Impact explanation (1 sentence)
├── Collapsible: Full fix recommendation with mockup detail
│
🟡 MAJOR Issues (fix in first sprint)
├── Same format
│
🟢 MINOR Issues (fix when time allows)
├── Same format
```

Each issue links back to its pillar card for context.

### 6. Recommendations Summary

Concise action plan section:

```
Immediate Actions (before ad launch)
├── Numbered list of CRITICAL fixes in recommended order
│
Sprint 1 Improvements
├── Numbered list of MAJOR fixes
│
Polish Items
├── Numbered list of MINOR fixes
│
Estimated Impact
├── "Addressing all CRITICAL issues typically improves conversion rate by X-Y%"
└── (Use ranges based on common CRO benchmarks, labeled [INFERRED])
```

---

## Interactive Elements

### Score Gauges
Use Chart.js doughnut charts for score visualization:
- Arc fills proportional to score (e.g., 7/10 = 70% filled)
- Center text shows the numeric score
- Arc color matches severity (green/amber/red)
- Tooltip shows the weight breakdown

### Tooltips
```html
<span class="tip">Score or term
  <span class="tiptext">Explanation of how this was assessed</span>
</span>
```
- Every score and technical term gets a tooltip
- Dark background, white text, 280px max width

### Collapsible Sections
```html
<button class="collapse-btn" onclick="toggle(this)">
  Section Title <span class="arrow">▼</span>
</button>
<div class="collapse-body">Detailed content</div>
```
- Used for detailed findings and fix recommendations
- Smooth CSS transition

### Card Hover States
- Cards lift on hover: `transform: translateY(-2px)`
- Shadow deepens, 0.2s ease transition

---

## CSS Custom Properties

```css
:root {
  /* From brand-config.json if available, otherwise defaults: */
  --primary: #3B82F6;      /* Accent, score highlights */
  --dark: #0F172A;          /* Page background, nav, cards */
  --dark-card: #1E293B;     /* Card backgrounds */
  --dark-surface: #334155;  /* Elevated surfaces */
  --text: #F8FAFC;          /* Primary text on dark */
  --text-muted: #94A3B8;    /* Secondary text */
  --white: #FFFFFF;
  --critical: #EF4444;      /* Red — critical issues */
  --major: #F59E0B;         /* Amber — major issues */
  --minor: #10B981;         /* Green — minor issues / good scores */
  --font: 'Inter', -apple-system, system-ui, sans-serif;
}
```

When brand-config.json is available, map brand colors:
- `--primary` → brand's primary accent
- `--dark` → brand's dark background (or keep default if brand is light-themed)
- Other variables adapt to maintain contrast

---

## Chart Configuration

All Chart.js charts:
- `responsive: true`, `maintainAspectRatio: false`
- Brand/severity colors for data series
- Clean axis labels
- Tooltips for context
- Container: `<div class="chart-wrap"><canvas></canvas></div>` at 250px height
- Radar charts for pillar sub-score breakdowns
- Doughnut charts for score gauges

---

## Source Indicators

Apply accuracy protocol:
- Objective findings (e.g., "CTA is below fold on mobile"): no tag needed — it's verifiable
- Subjective assessments (e.g., "headline tone doesn't match audience"): tooltip with `[INFERRED]` and reasoning
- Benchmark comparisons: cite the benchmark source in tooltip

---

## Quality Checklist

Before delivering:
- [ ] Screenshot annotations match the findings (marker numbers correspond)
- [ ] All three pillar scores calculated correctly with weights
- [ ] Overall score matches weighted formula
- [ ] Every finding has a specific fix recommendation (no vague advice)
- [ ] Fix recommendations include exact copy rewrites where applicable
- [ ] All charts render with real data (not placeholder)
- [ ] Collapsible sections work
- [ ] Tooltips appear on all scores
- [ ] Color coding consistent (red/amber/green = critical/major/minor)
- [ ] Brand colors applied if brand-config.json available
- [ ] Responsive on 1024px+ screens
- [ ] No placeholder text remaining
