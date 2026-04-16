# Scoring Framework

How to score the landing page audit across all three pillars and produce the overall Conversion Readiness Score.

---

## Pillar Scores

Each pillar gets a score from 1-10 based on the weighted average of its criteria.

### Pillar 1: CRO Fundamentals (Overall weight: 40%)

| Criterion | Weight |
|-----------|--------|
| Headline Clarity | 12% |
| CTA Placement & Copy | 14% |
| Form Friction | 12% |
| Trust Signals | 12% |
| Social Proof | 8% |
| Urgency & Scarcity | 5% |
| Above-the-Fold Content | 14% |
| Distraction Ratio | 5% |
| Page Goal Clarity | 5% |
| Content Rhythm & Scannability | 13% |

### Pillar 2: Visual UI/UX (Overall weight: 30%)

| Criterion | Weight |
|-----------|--------|
| Visual Hierarchy | 20% |
| Layout & Whitespace | 15% |
| Color Contrast & Accessibility | 15% |
| Typography | 10% |
| Image Quality & Relevance | 10% |
| Mobile Responsiveness | 20% |
| Visual Flow | 5% |
| Interactive Element Clarity | 5% |

### Pillar 3: Persuasion & Copy (Overall weight: 30%)

| Criterion | Weight |
|-----------|--------|
| Message-Market Match | 17% |
| Benefit vs Feature Framing | 17% |
| Specificity of Claims | 13% |
| Objection Handling | 13% |
| Headline Formulas | 8% |
| Subhead & Supporting Copy | 8% |
| Microcopy | 5% |
| Emotional Triggers | 3% |
| Reading Level | 2% |
| Copy Density & Sectional Flow | 14% |

---

## Overall Conversion Readiness Score

```
Overall = (CRO Score × 0.40) + (Visual UX Score × 0.30) + (Persuasion Score × 0.30)
```

### Score Interpretation

| Score | Label | Meaning |
|-------|-------|---------|
| 9-10 | Conversion Ready | Page is optimized, run traffic confidently |
| 7-8 | Good with Fixes | Solid foundation, address MAJOR issues before scaling spend |
| 5-6 | Needs Work | Several conversion barriers, fix CRITICAL + MAJOR before ads |
| 3-4 | Significant Issues | Fundamental problems, major rework needed before any ad spend |
| 1-2 | Not Ready | Page is actively repelling conversions, rebuild recommended |

---

## Issue Severity Classification

After scoring, every finding gets classified into a severity tier. The classification depends on two factors: how many visitors it affects and how directly it blocks conversion.

### 🔴 CRITICAL — Fix before running any ads

Issues that directly prevent or actively deter conversion. If you run traffic to this page, these will burn budget.

Indicators:
- CTA not visible above the fold on mobile
- Form is broken or has major usability failures
- Page goal is unclear — visitors don't know what to do
- Mobile experience is broken (horizontal scroll, unreadable text)
- Headline communicates the wrong thing or is missing
- Page loads with overlay/popup blocking the content

### 🟡 MAJOR — Fix within the first sprint

Issues that significantly drag conversion rate but don't completely block it. Some visitors will convert despite these, but you're leaving money on the table.

Indicators:
- CTA copy is generic ("Submit", "Learn More")
- Trust signals missing or buried below the fold
- Form has unnecessary fields adding friction
- Visual hierarchy doesn't guide eye toward CTA
- Copy is generic — doesn't match the specific audience
- Key objections not addressed
- Distraction ratio is high (full nav, social links)

### 🟢 MINOR — Fix when time allows

Polish items that improve conversion incrementally. Worth doing but not blockers.

Indicators:
- Microcopy could be more specific
- Image quality could improve
- Typography spacing slightly off
- Some copy sections could be tighter
- Color contrast acceptable but not ideal
- Hover states missing on desktop

---

## Fix Recommendation Depth

Every issue — regardless of severity — gets a fix recommendation with this level of detail:

### Copy Fixes
Provide the EXACT rewritten text. Don't say "make the headline more compelling." Write the headline.

**Format:**
```
Current: "Welcome to Samir's Kitchen"
Recommended: "Authentic South Indian Cuisine — 15 Regional Dishes You Won't Find Anywhere Else in Sydney"
Why: The current headline wastes the most valuable real estate. The rewrite leads with the cuisine type (what they're looking for), adds specificity (15 dishes, regional), and anchors to location (Sydney).
```

### Layout Fixes
Describe the specific rearrangement with element names and positions.

**Format:**
```
Current: Hero image (full viewport) → Headline → About section → Testimonials → Form → CTA
Recommended: Headline + Subhead + CTA button (above fold) → Trust bar (review scores) → 3 benefit cards → Testimonials (2 side-by-side) → Form with CTA
Why: Current layout buries the CTA below 3 scroll-lengths of content. Recommended layout puts the value prop and CTA above the fold, then builds the case for scrollers.
```

### Visual Fixes
Specify measurable changes — color values, pixel sizes, spacing.

**Format:**
```
Current: CTA button uses #6B7280 (gray) on #F3F4F6 (light gray background)
Recommended: CTA button uses #2563EB (brand blue) on #FFFFFF, 48px height, 18px font, full-width on mobile
Why: Current CTA has a contrast ratio of 2.1:1 — below WCAG AA. It also looks like a disabled button. The brand blue against white gives 4.6:1 contrast and makes the CTA the most prominent element.
```

### Form Fixes
Specify which fields to keep, remove, reorder, or relabel.

**Format:**
```
Current fields: First Name, Last Name, Email, Phone, Company, Job Title, Message, How Did You Hear About Us
Recommended: Full Name, Email, Phone (optional), Message (optional)
Why: 8 fields → 4 fields (2 optional). First/Last name split adds friction with no value at lead gen stage. Company and Job Title can be collected after initial contact. "How did you hear" is analytics, not lead qualification.
```
