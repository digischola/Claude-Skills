# Evidence Packaging — metrics, visuals, quotes

How to surface evidence consistently across all 4 deliverables.

## Metric surfacing rules

Every case study has 1 hero metric + 1-3 supporting metrics. The hero metric is the headline.

### Hero metric

The single number that pays off the hook. Format conventions:

| Metric type | Format example |
|---|---|
| Percentage change | `+188%` (always with sign), `-37%` for decreases |
| Multipler | `2.3x` (lowercase x), not `230%` (use percent for change) |
| Absolute count | `+12,000 leads`, not `12K leads` (precise > rounded) |
| Currency | `$1.4M revenue` (US dollar default; INR if India-specific) |
| Time | `48 hours`, `90 days` (always units) |

**Position:** Slide 1 of LI carousel + Tweet 1 + Blog H1 + Slide 1 of IG carousel — verbatim same.

### Supporting metrics

1-3 additional numbers that contextualize the hero. Mention all of them in:
- LI carousel: Slide 7 (Result)
- X thread: Tweet 9 (Result) — pack into 1-2 tweets if many
- Blog: H2 — The Result section
- IG carousel: Slide 7 (Result) — keep visual-light, max 2 supporting numbers

## Visual evidence

### Charts (recommended where applicable)

If the metric trend is showable as a chart, include 1 chart per deliverable:

- **LI carousel**: Slide 7 — line chart showing the curve from baseline → result
- **X thread**: Image attached to Tweet 9
- **Blog**: Inline chart in "The Result" section
- **IG carousel**: Slide 7 — large bar chart (before vs after) — IG audience prefers simple bars over line charts

Chart style (Digischola brand):
- Background: #000 (or transparent for blog inline)
- Bar/line color: #3B9EFF (positive) or #4ADE80 (success green)
- Axis labels: Manrope, #9BA8B9
- Title: Space Grotesk, #F8FAFC

### Screenshots

If showing before/after of a landing page or ad creative:
- Anonymize identifying details (logo blurred, copy generic-ized)
- Side-by-side preferred (before on left, after on right)
- Add Digischola corner brackets to maintain brand frame
- Aspect: 1080×1080 (square) for easy carousel insertion

### Photos

Avoid stock photos. If a real client photo is available + permission given:
- Single hero image at top of blog
- Small thumbnail in LI carousel Slide 2 (Setup)
- Skip on X thread (image budget tight)
- Optional Slide 2 of IG carousel

If no photo: use a Digischola dark-mode title card with the client name + period.

## Quotes (if available)

If the client gave a testimonial quote, surface in:
- **LI carousel**: Slide 8 (after Lesson) — pull-quote style with attribution
- **X thread**: Quote in Tweet 10, attribute in 11
- **Blog**: Block-quote in "What This Means For You" section
- **IG carousel**: Slide 8 — single quote with founder name + photo if avail

Format: `"<exact quote>" — <Founder Name>, <Title>, <Client>` (per public-allowed naming).

If no quote: don't fabricate. Skip the quote element.

## Number precision rules

| Number | Precise | Rounded (acceptable) |
|---|---|---|
| Percentages | `41%` (not 40%) | OK to round to nearest whole number |
| Currency | `$50/day` (not "low budget") | Round to clean number |
| Multipliers | `2.3x` (not 2x) | Keep one decimal for accuracy |
| Counts | `1,247 leads` | Round to nearest 50 if reading flow benefits |
| Percentages from a study | Quote the source's exact figure |

**Never invent or round in a misleading direction.** If conversion went from 1.2% to 2.3% (a 92% lift), don't round to "100% lift" because it's punchier. Mayank's credibility depends on accurate numbers.

## Cross-deliverable metric drift check

`validate_case_study.py` extracts all numeric mentions from each of the 4 deliverables and confirms they match. Drift triggers a hard error.

Example:
- LI Slide 1: "188%" ✓
- X Tweet 1: "188%" ✓
- Blog H1: "188% More Meta Sales in 90 Days" ✓
- IG Slide 1: "188%" ✓
- LI Slide 7: "188% sales / 37% CPS reduction" ✓
- X Tweet 9: "188% sales / 37% CPS reduction" ✓
- Blog Result section: "188% / 37%" ✓
- IG Slide 7: "188% / 37%" ✓

If LI Slide 7 said "190%" instead, the validator would fail with: `metric drift: hero metric Slide 1 says 188% but Slide 7 says 190%`.

## Source attribution

If the case study cites external research (e.g., "Wellness LP study by GoodUI"):
- Always include the URL in the blog post (linked footnote)
- Mention the source in LI carousel last slide
- Skip in X thread + IG carousel (visual budget tight)

If the metrics are entirely from Mayank's client work + on digischola.in: cite as "Source: digischola.in/case-studies" in the blog footer.
