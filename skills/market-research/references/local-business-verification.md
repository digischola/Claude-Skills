# Local-Business Verification Protocol

This reference governs the **GBP review-count gate** and adjacent local-business primary-source verifications. It exists because the 2026-04-25 Living Flow Yoga session shipped a market-research report, dashboard, two strategy.md files, and a draft landing page all citing "1,235 Google Business Profile reviews" as a load-bearing strategic claim. The real GBP review count was **67**. The 1,235 figure was MindBody class-vote count surfaced in GBP's "Reviews from the web" panel, which Perplexity conflated with actual Google reviews.

## Why this gate exists

Perplexity confidently cited the wrong number with citation-backed sources. The accuracy protocol's 3x penalty rule was insufficient because the figure looked plausible AND came from a "primary source." The error inflated the strategic framing 18× and propagated through every downstream deliverable until the user caught it during landing-page review by sending a screenshot.

The mistake is fixable only by verifying review counts against an actual GBP screenshot or DOM extraction — not by trusting Perplexity, web-citations, or competitor-comparison data alone.

## When the gate fires

The gate runs at **Step 3 (Perplexity output processing)** and again at **Step 5 (validator)**. Both of these conditions trigger a mandatory verification step:

1. **Local business sector** — any of: yoga, fitness, gym, spa, salon, restaurant, cafe, retail, wellness, therapy, clinic, studio, single-location professional services
2. **Single-location operator** — fewer than 3 physical locations
3. **Review-count claim** — Perplexity output contains a number ≥ 200 followed by "Google review", "GBP review", "Business Profile review", or similar

When all three conditions match, the review count must be **GBP-verified** before it leaves market-research as load-bearing data.

## Verification methods (any one suffices)

In order of preference:

1. **GBP screenshot from user.** Ask the user to send a screenshot of the GBP "Reviews" tab on Google Maps. The number next to the star rating is the actual Google review count.
2. **Chrome MCP visit.** Navigate to the GBP listing or `https://www.google.com/maps/place/<business>`. Read the review count from the DOM. The element class containing the count varies, but the integer adjacent to the star rating is always the actual Google count.
3. **Direct GBP URL.** If the business has an explicit `/maps/place/` URL, fetch it and parse the `<meta>` tag with `aggregateRating` or the visible `4.9 (67)` pattern in the page header.
4. **Disclosure framing.** If none of the above is possible in this session, the field MUST be tagged `[EXTRACTED — UNVERIFIED, requires GBP screenshot]` everywhere it appears. Strategy MUST NOT make load-bearing claims based on the unverified figure.

## The "Reviews from the web" trap

Google Business Profile surfaces ratings from **third-party platforms** in a "Reviews from the web" panel, alongside the actual Google review count. These third-party numbers look identical in plain-text extraction:

| Source | Living Flow example | Common platforms |
|---|---|---|
| Actual Google reviews | `4.9 (67)` | Google Business Profile only |
| Reviews from the web | `MindBody · 4.9 (1,235 votes)` | MindBody, ClassPass, Booking.com, TripAdvisor, Yelp, Facebook, Trustpilot, Healthgrades, Avvo |

Perplexity's text-only extraction strips the source label and surfaces both as "Google reviews" — that's the exact failure mode. Always preserve the source attribution in the wiki:

```markdown
## Reviews & Trust Signals
- Google: 4.9 / 67 reviews [EXTRACTED — GBP screenshot 2026-04-25]
- MindBody: 4.9 / 1,235 votes [EXTRACTED — surfaced in GBP "Reviews from the web"]
- ClassPass: [BLANK — not surfaced in any source]
```

Two separate metrics, two separate strategic implications. Conflating them inflates the trust moat.

## Strategic implications when correctly disambiguated

The 67-vs-1235 distinction matters strategically:

- **67 Google reviews** = excellent rating but moderate review count. Local-pack visibility good but not dominant. Branded-search organic wins, but competitors with 200+ reviews can outrank in proximity-tied "near me" queries.
- **1,235 MindBody votes** = strong booking-system loyalty but invisible to non-MindBody-users searching Google. Indicates retention-class strength but doesn't help paid-search funnel math.

The "do-not-bid-on-brand" recommendation holds either way — but the "GBP organic dominates everything" framing only holds with 200+ Google reviews. Below that, paid search complements rather than gets crowded out.

## Other primary-source claims to verify

Same protocol applies to any local-business claim where a single number drives a major strategic recommendation:

| Claim | Trap | Verify via |
|---|---|---|
| Star rating | OK if ≥4.0; flag below | GBP screenshot |
| Review count | Conflation with third-party | GBP screenshot |
| Hours of operation | Outdated GBP info | GBP screenshot or business website |
| Service area | GBP not configured | GBP screenshot |
| Photos count | Includes user-submitted | Visual count |
| Q&A count | Often unanswered | GBP screenshot |

## Validator behaviour

The validator (`scripts/validate_output.py`) runs a regex scan over the report + strategy.md for patterns matching review counts. When a number ≥ 200 appears within 5 words of "Google review", "GBP review", or "Business Profile review", it WARNs unless the same passage carries `[EXTRACTED — GBP` or `[VERIFIED` source labels.

WARN, not CRITICAL — because high-volume legitimate review counts exist (hotels, restaurants, retail). The point is to force visible human review of any large number before it ships.

## Logging requirement

Every market-research session for a local-business client MUST include this section in `_engine/wiki/digital-presence.md`:

```markdown
## GBP Verification Log

- Verified: YYYY-MM-DD
- Method: [screenshot from user / Chrome MCP / direct URL / NOT VERIFIED]
- Google review count: XX [VERIFIED] or [UNVERIFIED]
- Star rating: X.X [VERIFIED] or [UNVERIFIED]
- Third-party ratings: list each source separately (MindBody, ClassPass, Booking.com)
- Discrepancies noted: [list any conflicts between Perplexity and actual GBP]
```

The presence of this log is itself the proof that verification happened.
