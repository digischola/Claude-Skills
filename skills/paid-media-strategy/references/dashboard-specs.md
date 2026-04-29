# Strategy Dashboard HTML Specification

The strategy dashboard is the client-facing presentation of the paid media plan. It should look like a premium strategy deck — visual, interactive, and immediately actionable. The reference standard is the CrownTech market research dashboard, adapted for strategy output.

---

## Brand-Config Priority (Read First)

Before any design decisions, read `{client-folder}/_engine/brand-config.json` (single-program) or `{client-root}/_engine/brand-config.json` (multi-program). This overrides ALL defaults below.

1. **Existing dashboard match.** If the client already has a dashboard (e.g., `*-research-dashboard.html`), match its design language — mode (light/dark), section pattern, color palette, font stack. Cross-deliverable consistency is mandatory.
2. **Monochromatic brands** (primary = #000000 or #ffffff): Do NOT use generic tech colors. Derive accent tones from product photography or `manual_override` notes in brand-config. Use muted, natural palette.
3. **Font mapping.** Map brand fonts to web-safe fallbacks (e.g., IvyPresto Display → Georgia serif, FH Oscar → Helvetica Neue). Never use system defaults when brand-config specifies fonts.
4. **Mode override.** Default is dark mode, but if brand-config or existing dashboards use light mode, switch to light mode with alternating dark sections.

## Design Philosophy

- **Strategy deck, not a report.** Visual campaign architecture, budget charts, timeline — not walls of text.
- **Actionable.** Copy buttons on campaign names, audience definitions, KPI targets, budget numbers.
- **Decision logic visible.** Every recommendation has a tooltip explaining WHY, not just WHAT.
- **Brand-first, premium feel.** Client branding from brand-config.json, animations, aggressive visual polish. Dark mode is default but yields to brand-config.
- **Per-platform sections** when strategy covers both Google and Meta.

## Required Libraries

- **Chart.js 4.x** — MUST use the UMD build: `https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js`
- The cdnjs `chart.min.js` is ESM-only and does NOT register a global `Chart` object. **Never use cdnjs for Chart.js.**
- **No other external dependencies.** All CSS is inline. All JS is vanilla.

## Layout Structure

### Navigation
- Sticky top nav bar with `background: var(--dark)`
- Section links: Overview, Campaigns, Budget, Audiences, Creative, Funnel, Timeline, Platform Details
- Brand name as first nav item
- Active section highlighting

### Hero Section
- Full-width gradient background using brand dark color
- Strategy title: "{Business Name} — Paid Media Strategy"
- Subtitle: platform scope, date, consultant
- KPI target row: 4-6 target metrics in card format (target CPA, target ROAS, monthly budget, estimated leads/sales)
- Each KPI card has a tooltip explaining the target rationale

### Section Template
```
Section Title + Platform Badge (Google / Meta / Both)
Section description (one line)
├── Chart or visual (primary content)
├── Key decision cards (3-4 across)
├── Collapsible detail with full rationale
└── Copy buttons on actionable elements
```

## Section-Specific Components

### 1. Strategy Overview
- Summary cards: platform(s), total monthly budget, primary objective, expected CPA/ROAS range
- Phase timeline visual (3 horizontal bars: Foundation → Optimize → Scale)
- Key strategic insight (1-2 sentences from wiki analysis)

### 2. Campaign Architecture
- **Visual campaign tree:** hierarchical display showing:
  ```
  Account
  ├── Campaign 1 (type, objective, budget)
  │   ├── Ad Group/Ad Set 1 (targeting, bid strategy)
  │   └── Ad Group/Ad Set 2
  ├── Campaign 2
  └── Campaign 3
  ```
- Separate tree per platform if both
- Color-coded by campaign type (Search = blue, PMax = purple, Meta Sales = green, etc.)
- Copy button on each campaign name
- Collapsible: full rationale for structure decisions

### 3. Budget Allocation
- **Doughnut chart:** budget split by campaign (Chart.js)
- If both platforms: **stacked bar chart** showing Google vs Meta split
- Monthly projection table: Month 1, 2, 3 spend with scaling plan
- Budget rule cards: "Increase max 20% per change", "Minimum 50 events/week per ad set"
- Collapsible: budget rationale with unit economics math

### 4. Audience & Targeting Map
- **For Google:** keyword cluster cards with match type, estimated volume, priority
- **For Meta:** audience segment cards (broad, interest, lookalike, retargeting) with estimated sizes
- Targeting architecture diagram: visual showing how audiences layer
- Exclusion list section
- Copy buttons on audience definitions and keyword lists

### 5. Creative Direction
- Format recommendation cards with specs (dimensions, duration, character limits)
- Testing framework: what to test first, kill rules, refresh cadence
- Messaging angle cards (derived from wiki buyer personas): each persona → recommended hook/angle
- Collapsible: full creative brief per campaign type

### 6. Funnel & KPI Targets
- **Funnel visualization:** Impressions → Clicks → Leads/ATC → Conversions → Revenue
  - Show estimated numbers at each stage based on benchmarks
  - Show target metrics (CTR, conversion rate, CPA) at each transition
- **Benchmark comparison:** bar chart showing industry avg vs target
- KPI dashboard: cards for each metric with target, benchmark, and monitoring threshold
- Copy buttons on KPI target values

### 7. Phased Execution Timeline
- **3-phase visual timeline:**
  - Phase 1 (Days 1-30): Foundation — cards with specific launch actions
  - Phase 2 (Days 30-60): Optimize — cards with optimization triggers
  - Phase 3 (Days 60-90): Scale — cards with expansion plan
- Each phase card has: actions, expected outcomes, decision criteria for moving to next phase
- Collapsible: detailed week-by-week actions

### 8. Platform-Specific Details (conditional)
- **Google section (if applicable):**
  - Bidding strategy per campaign with decision logic tooltip
  - Keyword strategy summary with match type rationale
  - Quality Score optimization notes
  - PMax signal and theme recommendations
- **Meta section (if applicable):**
  - Advantage+ configuration decisions with rationale
  - Audience architecture (broad vs stacked vs lookalike per campaign)
  - Creative rotation plan
  - iOS/tracking considerations

### Glossary
- 3-column grid of term definitions
- Platform-specific terms used in the dashboard

## Interactive Elements

### Copy Buttons
```html
<button class="copy-btn" onclick="copyText(this)" data-copy="Campaign Name: Brand Search | Type: Search | Budget: $500/mo">
  📋
</button>
```
- Small clipboard icon next to every actionable element
- On click: copies the text to clipboard, shows "Copied!" tooltip for 1.5s
- Use on: campaign names, audience definitions, keyword lists, KPI targets, budget figures

### Tooltips
```html
<span class="tip">Target CPA: $45
  <span class="tiptext">Based on market-research benchmark of $52 industry avg CPA, adjusted down 15% for strong creative and broad targeting strategy. [INFERRED from wiki benchmarks + strategy logic]</span>
</span>
```
- Every KPI, budget figure, and strategic decision gets a tooltip
- Tooltip explains the "why" — not just restates the number

### Collapsible Sections
```html
<button class="collapse-btn" onclick="toggle(this)">
  Full Rationale <span class="arrow">▼</span>
</button>
<div class="collapse-body">Detailed decision logic here</div>
```
- Used for deep-dive content that would clutter the main view

### Card Hover States
- All cards lift on hover: `transform: translateY(-2px)`
- Shadow deepens on hover
- Transition: 0.2s ease

## CSS Custom Properties (from brand-config.json)

```css
:root {
  --blue: {primaryAccent};
  --blue-hover: {buttonHover};
  --dark: {darkBackground};
  --text: {darkText};
  --light: {lightText};
  --white: #FFFFFF;
  --green: #10B981;
  --red: #EF4444;
  --amber: #F59E0B;
  --purple: #8B5CF6;
  --cyan: #06B6D4;
  --font: {fontFamily};
}
```

## Source Indicators

- **[EXTRACTED]** data (from `_engine/wiki/`): displayed normally
- **[INFERRED]** data (strategy logic): tooltip with inference explanation
- **BLANK** data: displayed as "To be determined" with dashed border
- **data-supported** recommendations: solid border accent
- **directional** recommendations: dashed border accent with "directional" badge

## Chart Configuration

All Chart.js charts:
- Use brand colors for data series
- `responsive: true, maintainAspectRatio: false`
- Tooltips for context
- Clean axis labels
- Wrap in: `<div class="chart-wrap"><canvas id="chartName"></canvas></div>`
- Container height: 280px

## Quality Checklist

- [ ] Brand colors from brand-config.json (no defaults)
- [ ] Every KPI has a tooltip with rationale
- [ ] Charts render with real data (not placeholder)
- [ ] Copy buttons work on all actionable elements
- [ ] Collapsibles toggle correctly
- [ ] Campaign tree is platform-accurate (correct terminology per platform)
- [ ] Budget numbers add up
- [ ] Phase timeline matches strategy report
- [ ] Responsive on 1024px+ screens
- [ ] Chart.js UMD build used (not ESM)
- [ ] No placeholder text remaining
