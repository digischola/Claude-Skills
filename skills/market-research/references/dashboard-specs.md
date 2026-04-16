# HTML Dashboard Specifications

The dashboard is the client-facing presentation of research findings. It should look like a premium strategy presentation — not a report displayed as a webpage. The reference standard is the CrownTech dashboard (see `deliverables/CrownTech_Market_Research_Presentation.html` for the benchmark).

---

## Design Philosophy

- **Presentation, not report.** Every section should be visual-first with supporting text, not text-first with decorative elements.
- **Data visualization over data listing.** Charts, progress bars, radar diagrams instead of bullet lists.
- **Interactive exploration.** Collapsible sections, tooltips on every stat, hover states on cards.
- **Client branding.** Use brand-config.json colors and fonts throughout. The client should feel like this was built for them.
- **Responsive.** Works on desktop and tablet. Print-friendly (hide nav, expand collapsibles).

## Required Libraries

- **Chart.js 4.x** — MUST use the UMD build: `https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js`. The cdnjs `chart.min.js` is ESM-only and does NOT register a global `Chart` object, causing "Chart is not defined" errors. Always use `chart.umd.min.js` from jsdelivr.
- **No other external dependencies.** All CSS is inline. All JS is vanilla.

## Layout Structure

### Navigation
- Sticky top nav bar with `background: var(--dark)` (from brand config)
- Section links: Overview, Market Size, Porter's, PESTEL, SWOT, Competitors, Keywords, Buyers, Channels, Blue Ocean, Strategy, Glossary
- Brand name as first nav item with `font-weight: 700`
- Active section highlighting on scroll or click

### Hero Section
- Full-width gradient background using brand dark color
- Business name and research title (large heading)
- Subtitle with scope and date
- KPI row: 6-8 key statistics in card format with tooltips explaining each number
- "Prepared for {client} · Presented by {consultant} · {date}" footer line

### Section Template (repeats for each dimension)
Each section follows this pattern:
```
Section Title + Badge (section number)
Section description (one line)
├── Chart(s) or data visualization (primary content)
├── Key stat cards (3-4 across in grid)
├── Collapsible detail sections with expand/collapse
└── Supporting text with inline tooltips
```

## Section-Specific Components

### 1. Market Size & Demand
- Bar chart: adjacent market sizes (TAM context)
- Line chart: growth projections over time
- Cards: key market figures (TAM, growth rate, market size)
- Collapsible: CRE trends with vacancy chart
- Collapsible: growth drivers vs headwinds (side by side cards)

### 2. Porter's Five Forces
- Radar/spider chart (Chart.js radar) with 5 forces rated 1-5
- Legend with 1-2 sentence explanation per force
- Overall assessment card

### 3. PESTEL Analysis
- 6 cards in 2x3 grid, each with icon, title, and key points
- Color-coded by PESTEL category
- Collapsible detail for each factor

### 4. SWOT Analysis
- 2x2 grid with distinct background colors:
  - Strengths: green tint
  - Weaknesses: amber tint
  - Opportunities: blue tint
  - Threats: red tint
- Each cell has h4 title + bulleted findings

### 5. Competitive Landscape
- Full-width comparison table with columns: Company, Location, Positioning, Key Differentiators, Size, Google Ads Active, SEO Rank
- Hover highlight on rows
- Client row highlighted with accent background
- Collapsible: "invisible competitor" analysis

### 6. Keywords & Ads (Dark Section)
- Dark background section using brand dark color
- Keyword data table with columns: Keyword, Avg Monthly Searches, Competition, CPC Low, CPC High
- Cluster headers separating keyword groups
- Color-coded competition (green = low, amber = medium, red = high)
- Volume highlights for high-value terms
- If CSV keyword data was ingested, embed the actual data here

### 7. Platform Benchmarks & Unit Economics
- Funnel visualization: Impressions → Clicks → Leads → Opportunities → Deals
- Benchmark comparison cards: industry avg vs estimated for this client
- Charts: CPC by keyword cluster, budget allocation recommendation
- Unit economics calculation display

### 8. Buyer Personas
- Persona cards with icon, title, role description, and behavioral details
- 3-4 personas in horizontal layout
- Purchase journey timeline (3-phase: Awareness → Evaluation → Decision)

### 9. Channel Partners & Referral
- Cards listing referral sources with descriptions
- Trust signals / certification badges

### 10. Blue Ocean Opportunities
- Opportunity cards with impact assessment
- Geographic gap visualization if applicable
- Service gap matrix

### 11. Strategy & Recommendations (Dark Section)
- Phased timeline: Quick wins (0-3mo), Medium-term (3-6mo), Long-term (6-12mo)
- Each phase as a card with bulleted action items
- Label: "data-supported" vs "directional" on each recommendation
- Budget allocation chart (doughnut or bar)
- Priority verticals cards

### Glossary
- 3-column grid of term definitions
- Industry-specific terms that appear in the dashboard

## Interactive Elements

### Tooltips
```html
<span class="tip">Stat or term
  <span class="tiptext">Detailed explanation with source context</span>
</span>
```
- Appear on hover, positioned above the element
- Dark background, white text, 280px max width
- Used on every KPI, benchmark, and technical term

### Collapsible Sections
```html
<button class="collapse-btn" onclick="toggle(this)">
  Section Title <span class="arrow">▼</span>
</button>
<div class="collapse-body">Content here</div>
```
- Used for detailed sub-sections that would clutter the primary view
- Smooth CSS transition on expand/collapse

### Card Hover States
- All cards lift slightly on hover (`transform: translateY(-2px)`)
- Shadow deepens on hover
- Transition: 0.2s ease

## CSS Custom Properties (from brand-config.json)

```css
:root {
  --blue: {primaryAccent};        /* CTAs, accent elements */
  --blue-hover: {buttonHover};    /* Hover states */
  --dark: {darkBackground};       /* Dark sections, nav, footer */
  --text: {darkText};             /* Body text */
  --light: {lightText};           /* Text on dark backgrounds */
  --white: #FFFFFF;               /* Page backgrounds */
  --green: #10B981;               /* Positive indicators, low competition */
  --red: #EF4444;                 /* Negative indicators, high competition */
  --amber: #F59E0B;               /* Warning, medium competition */
  --purple: #8B5CF6;              /* Accent for special elements */
  --cyan: #06B6D4;                /* Secondary accent */
  --font: {fontFamily};
}
```

## Source Indicators

Every data point in the dashboard should indicate its source confidence:
- **[EXTRACTED]** data: displayed normally (strongest confidence)
- **[INFERRED]** data: tooltip with `class="tip"` showing the inference logic
- **BLANK** data: displayed as "Data not available" with dashed border and tooltip explaining why

## Chart Configuration

All Chart.js charts should:
- Use brand colors for data series
- Have responsive: true, maintainAspectRatio: false
- Use tooltips for additional context
- Have clean axis labels (no clutter)
- Wrap in a container: `<div class="chart-wrap"><canvas id="chartName"></canvas></div>`
- Be 280px height in the container

## JavaScript

Minimal JS required:
1. **Collapsible toggle function**
2. **Chart.js initialization** — all charts initialized in a single `<script>` block at bottom of body
3. **Scroll-based nav highlighting** (optional)
4. **No frameworks, no build tools** — everything inline in the single HTML file

## Quality Checklist

Before delivering the dashboard:
- [ ] All brand colors from brand-config.json applied (no defaults)
- [ ] Every KPI has a tooltip with context
- [ ] Charts render correctly with real data (not placeholder)
- [ ] Collapsible sections work
- [ ] Responsive on 1024px+ screens
- [ ] No duplicate JS variable declarations
- [ ] Keyword data from CSV integrated (if available)
- [ ] Print-friendly (nav hidden, collapsibles expanded)
- [ ] No placeholder text remaining
