# Pricing-Page Product Enumeration

When a business has a public pricing/membership/passes page, every distinct purchase option on that page MUST be captured as a separate row in offerings.md AND offerings.json. Narrative summarization is forbidden — the LLM tendency is to group products into "intro passes" + "memberships" buckets and drop standalone offers, which is how Living Flow's $39 Midday Recharge Pass + Single Month Unlimited + Annual + 6-Month memberships were missed during their 2026-04-25 onboarding despite all being on the public pricing page.

## Trigger

This step fires whenever the website crawl finds any of:
- A `/pricing/` URL
- A `/membership/` or `/memberships/` URL
- A `/passes/` URL
- A `/plans/` or `/subscriptions/` URL
- Any page where structured price data appears (multiple `$N` patterns in card-shaped DOM)

## Required fields per product

For every distinct purchase option visible on the page, capture:

| Field | Description | Example | If missing |
|---|---|---|---|
| `name` | Product/pass/plan name as labeled | "Midday Recharge" | BLANK |
| `price` | Numeric amount | 39 | BLANK |
| `currency` | ISO code | AUD | BLANK |
| `billing_cycle` | one-off / per-class / per-week / per-fortnight / per-month / per-6-months / per-year / lifetime | "30 days" | BLANK |
| `audience` | new / existing / both / unspecified | "both" | BLANK |
| `channel` | in-studio / live-stream / online-only / both / hybrid / unspecified | "both" | BLANK |
| `unlimited_within_window` | true if all-you-can-eat for the duration | true | BLANK |
| `time_window` | day-of-week / time-of-day restriction | "12:15pm Mon-Fri" | null |
| `class_type_restriction` | specific class types only | null | null |
| `concession_price` | discounted variant if offered | 75 | null |
| `purchase_url` | direct link to checkout | "...?prodId=10271" | BLANK |
| `mindbody_product_id` | extracted from URL if MindBody/Healcode | "10271" | null |
| `description` | full marketing copy verbatim | "Take a pause..." | BLANK |
| `position_on_page` | order on the pricing page (1, 2, 3...) | 1 | required |

## Process — how to actually extract

1. **Open pricing page in Chrome MCP** (or WebFetch if static). NOT crawl_site.py — that captures structure, not content.
2. **Take a full-page screenshot** to preserve the visual order and grouping.
3. **Run an explicit per-card extraction prompt:**

   > For every distinct price card / pass card / membership card visible on this page, return one JSON object per card. Do not group, summarize, or skip. If the page has 9 cards, return 9 objects. Do not consolidate "intro passes" into one entry — list each separately.

4. **Cross-check the count.** Use a separate query: "How many distinct $N price points appear on this page?" The product count must match (allowing for free trials and gift vouchers).

5. **Save to `_engine/wiki/offerings.json`** as the machine-readable source of truth. Render `_engine/wiki/offerings.md` from it.

## Validator cross-check

`scripts/validate_output.py` runs this check on every business-analysis session where the crawl found a pricing URL:

1. Fetch the live pricing page
2. Count distinct `\$\d+` patterns (with deduplication for repeated mentions of the same price)
3. Compare against `len(offerings.json)`
4. If page distinct-prices > offerings count by ≥ 2, **CRITICAL fail** with the page URL + the extra prices found

Distinct-price floor allows for gift vouchers and free options that may not have a `$` (e.g., "Any Value" cards).

## Common patterns missed without enumeration

These are the offer types that get systematically dropped when a skill summarizes instead of enumerates:

- **Standalone monthly passes** (e.g., $39 Midday Recharge) — sit between intro passes and memberships, easy to miss
- **Time-window-limited unlimited passes** (e.g., "12:15pm only") — looks like a feature flag rather than a product
- **Annual / 6-month upfront packages** — visually deprioritized below monthly options but represent the highest LTV
- **Concession variants** — listed as a sub-line ("Concession: $75/fortnight") and gets folded into the main price instead of becoming its own audience-segmented row
- **Gift vouchers / one-off variable-amount cards** — non-standard pricing, often dropped
- **First-class trial offers** — sometimes hidden in popups, sometimes inline on pricing page

## Why narrative summarization fails

LLMs tasked with "summarize the pricing page" optimize for compactness. The dominant visual pattern (3 intro pass cards under "Start here if you're new") becomes the model of the offerings, and outliers (standalone $39 pass at the top, $1,790 annual at the bottom) get described as "additional options exist" or omitted.

Structured enumeration with explicit per-row constraints + a validator count-check is the only reliable fix. This is identical to the discipline already used in `paid-media-strategy/references/csv-output-specs.md` for media plans — every campaign gets its own row with required fields. Apply the same pattern here.
