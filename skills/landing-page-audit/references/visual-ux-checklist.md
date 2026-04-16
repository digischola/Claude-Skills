# Visual UI/UX Checklist

Audit criteria for visual design and user experience. Mobile-first — evaluate mobile before desktop for every criterion.

---

## 1. Visual Hierarchy (Weight: High)

**What to evaluate:** Does the page guide the eye through content in the right order? The hierarchy should lead: headline → supporting info → CTA → trust/proof → deeper content.

**Good:**
- Largest/boldest element is the headline (not the logo or a decorative image)
- CTA button is the most visually prominent interactive element
- Content sections have clear visual separation
- Important elements use size, color, and position to stand out
- Z-pattern (desktop) or single-column (mobile) flow works naturally

**Common failures:**
- Everything is the same size/weight — nothing stands out
- Logo dominates while headline is undersized
- CTA is smaller or less prominent than other buttons
- Decorative elements compete with functional content
- Inconsistent heading sizes that confuse the information hierarchy

**Scoring:** 9-10 = Eye moves naturally through content in conversion-optimized order. 7-8 = Mostly clear, one element misplaced. 5-6 = Hierarchy present but weak. 3-4 = Competing elements, unclear where to look. 1-2 = No discernible hierarchy.

---

## 2. Layout & Whitespace (Weight: High)

**What to evaluate:** Is content spaced for readability and scannability? Does the layout feel breathable or cramped?

**Good:**
- Consistent spacing system (padding between sections feels even)
- Content blocks have breathing room — not packed edge-to-edge
- Margins on mobile prevent text from touching screen edges (minimum 16px)
- Sections have clear visual boundaries (spacing, background color, or dividers)
- Grid alignment is consistent — elements line up across the page

**Common failures:**
- Content crammed together with no breathing room
- Inconsistent spacing (some sections packed, others floating)
- Text runs edge-to-edge on mobile (no horizontal padding)
- Floating elements that break the visual grid
- Too much whitespace making the page feel empty (rare but possible)

**Scoring:** 9-10 = Clean, consistent spacing, easy to scan. 7-8 = Generally good, minor inconsistencies. 5-6 = Some sections cramped or poorly spaced. 3-4 = Layout feels cluttered or disorganized. 1-2 = No spatial organization.

---

## 3. Color Contrast & Accessibility (Weight: High)

**What to evaluate:** Can visitors easily read text and identify interactive elements? Do colors support or hinder usability?

**Benchmarks:**
- WCAG AA minimum: 4.5:1 contrast for normal text, 3:1 for large text
- CTA button should have the highest contrast ratio on the page
- No information conveyed by color alone (important for color-blind users)

**Good:**
- Text is highly readable against its background
- CTA button color is distinct from the page palette — it pops
- Links look different from body text (color, underline, or both)
- Form field borders are visible against the background
- Error messages use color AND text/icon (not just red)

**Common failures:**
- Light gray text on white background (low contrast, hard to read)
- CTA button same color as other elements (doesn't stand out)
- Text over images without overlay/scrim (unreadable in sections)
- Form fields with no visible border (user can't tell where to click)
- Color-dependent interactions (red = error with no other indicator)

**Scoring:** 9-10 = Excellent contrast everywhere, accessible. 7-8 = Good, minor contrast issues in non-critical areas. 5-6 = Some readability issues. 3-4 = Multiple contrast failures affecting usability. 1-2 = Significant portions of the page unreadable.

---

## 4. Typography (Weight: Medium)

**What to evaluate:** Is the text easy to read, properly sized, and visually consistent?

**Benchmarks:**
- Body text: minimum 16px on mobile, 16-18px on desktop
- Line height: 1.4-1.6 for body text
- Line length: 50-75 characters per line (desktop)
- Heading hierarchy: H1 > H2 > H3 with consistent sizing steps
- Maximum 2 font families on the page

**Good:**
- Body text easily readable without zooming on mobile
- Heading sizes create clear hierarchy
- Consistent font usage (not a font per section)
- Adequate line spacing for comfortable reading
- Bold/italic used sparingly for emphasis, not decoration

**Common failures:**
- Body text too small on mobile (under 16px)
- Tight line spacing makes text blocks feel dense
- Too many fonts (3+ families) creating visual noise
- All caps for long text (hard to read)
- Centered body text (harder to read than left-aligned)
- Extra-long lines on desktop (wider than 75 characters)

**Scoring:** 9-10 = Excellent readability, consistent hierarchy. 7-8 = Good, minor sizing or spacing issues. 5-6 = Readable but has consistent typography issues. 3-4 = Hard to read in multiple sections. 1-2 = Typography actively hinders readability.

---

## 5. Image Quality & Relevance (Weight: Medium)

**What to evaluate:** Do images support the page goal, or are they decorative filler?

**Good:**
- Hero image shows the product, service, or outcome (not abstract stock)
- Images are sharp, properly sized, not pixelated or stretched
- Photos show real people, real locations (for service businesses)
- Images reinforce the value proposition (e.g., happy customers using the service)
- Proper alt text for accessibility

**Common failures:**
- Generic stock photos that could be any business in any industry
- Low-resolution or pixelated images
- Huge uncompressed images that slow loading
- Images that don't connect to the page content
- Decorative graphics that take up space without conveying information
- Different photography styles across sections (inconsistent brand feel)

**Scoring:** 9-10 = Every image is purposeful, high-quality, and brand-consistent. 7-8 = Good images, minor quality or relevance issues. 5-6 = Mix of relevant and stock. 3-4 = Mostly stock or low quality. 1-2 = No images or all irrelevant/broken.

---

## 6. Mobile Responsiveness (Weight: Critical)

**What to evaluate:** Does the page work well on a phone screen? This is the most important UX criterion because most ad traffic lands on mobile.

**Good:**
- Content stacks cleanly in single column on mobile
- Tap targets are at least 44×44px with adequate spacing between them
- Text is readable without zooming or horizontal scrolling
- Form fields are easy to tap and fill (proper input types, large enough)
- No horizontal overflow or sideways scrolling
- CTA button is full-width or nearly full-width on mobile
- Images scale down properly, not clipped or overflowing

**Common failures:**
- Desktop layout squeezed onto mobile (horizontal scrolling)
- Tiny buttons/links that are hard to tap (too close together)
- Text overflows its container
- Fixed elements (headers, chat widgets) covering content
- Pop-ups that are impossible to close on mobile
- Form fields too small to comfortably type in
- Images wider than viewport causing layout break

**Scoring:** 9-10 = Native mobile-quality experience. 7-8 = Works well, minor issues. 5-6 = Functional but clearly a desktop page adapted. 3-4 = Significant mobile usability issues. 1-2 = Barely usable on mobile.

---

## 7. Visual Flow (Eye Tracking Patterns) (Weight: Medium)

**What to evaluate:** Does the layout follow natural scanning patterns?

**Patterns:**
- **F-pattern:** Users scan left-to-right at top, then sweep down the left edge. Applicable to text-heavy pages.
- **Z-pattern:** Eyes move in a Z across sections with large visual elements. Applicable to landing pages with alternating content blocks.
- **Gutenberg Diagram:** Terminal area (bottom-right) is where the eye naturally ends — ideal CTA placement.

**Good:**
- Key content sits along the natural eye path
- CTA appears in terminal area or after a natural content flow point
- Visual anchors (images, icons, color blocks) break up text and guide scanning
- Section transitions feel natural — eyes flow downward without jarring jumps

**Common failures:**
- CTA placed in a dead zone (top-left corner, mid-page sidebar)
- Important content in areas the eye naturally skips
- No visual anchors — wall of text that the eye bounces off
- Disjointed section transitions (different visual styles per section)

**Scoring:** 9-10 = Layout leverages scanning patterns perfectly. 7-8 = Mostly follows natural flow. 5-6 = Some elements misplaced. 3-4 = Layout fights natural eye movement. 1-2 = Chaotic layout, no discernible flow.

---

## 8. Interactive Element Clarity (Weight: Medium)

**What to evaluate:** Can users instantly tell what's clickable, tappable, or interactive?

**Good:**
- Buttons look like buttons (shaped, colored, elevated or outlined)
- Links are visually distinct from body text
- Hover/focus states provide feedback
- Form fields have clear borders and labels
- Toggle/accordion elements have clear expand/collapse indicators

**Common failures:**
- Flat design taken too far — buttons look like text blocks
- Ghost buttons (outline only) used for primary CTA
- No hover states on desktop
- Interactive text looks identical to static text
- Form placeholders used as labels (disappear on focus)

**Scoring:** 9-10 = Every interactive element is immediately obvious. 7-8 = Mostly clear, minor ambiguity. 5-6 = Some elements unclear. 3-4 = Multiple elements hard to identify as interactive. 1-2 = Can't tell what's clickable.
