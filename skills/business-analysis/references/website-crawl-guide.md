# Website Crawl & Extraction Guide

How to systematically extract business DNA from a website. This is the universal framework — sector lenses in `sector-lenses/` add business-type-specific data points.

---

## Crawl Strategy

### Step 1: Sitemap Check
- Fetch `{url}/sitemap.xml` first. If it exists, parse it for all page URLs.
- If no sitemap, fall back to internal link crawling from the homepage (max 2 levels deep).
- Use `scripts/crawl_site.py` for automated extraction.

### Step 2: Priority Pages
Not all pages matter equally. Prioritize in this order:

1. **Homepage** — overall positioning, hero messaging, primary CTA, value proposition
2. **Services/Products pages** — each offering, pricing, features, audience signals
3. **About page** — business story, team, credentials, years in operation
4. **Testimonials/Reviews** — social proof, customer language, transformation stories
5. **Pricing page** — pricing model (fixed/hourly/packages), tiers, what's included
6. **Contact page** — locations, phone, email, booking system type
7. **Blog/Resources** — content themes, publishing frequency, expertise signals
8. **FAQ page** — common objections, customer concerns

### Step 3: Per-Page Extraction
For each priority page, extract:

| Data Point | Where to Find | Tag |
|---|---|---|
| Page title & meta description | `<title>`, `<meta name="description">` | [EXTRACTED] |
| H1 and H2 headings | Heading tags | [EXTRACTED] |
| Primary CTA | Buttons, forms, booking links | [EXTRACTED] |
| Pricing (if visible) | Pricing section, packages | [EXTRACTED] |
| Social proof | Testimonials, review counts, logos | [EXTRACTED] |
| Key claims/USP | Hero section, about section | [EXTRACTED] |
| Images/visual style | Overall aesthetic assessment | [INFERRED] |
| Tone of voice | Copy analysis | [INFERRED] |

---

## Universal Extraction Framework

Every business, regardless of type, needs these documented:

### Business Identity
- Legal/brand name
- Tagline or positioning statement
- Year founded (if visible)
- Team size / key personnel
- Certifications, awards, affiliations

### Business Model
- How they make money (products, services, subscriptions, donations)
- Revenue streams (visible from site)
- Pricing model and range
- Geographic scope (local, national, international)

### Online Presence Signals
- Website technology (WordPress, Shopify, custom, Wix, Squarespace)
- SSL certificate present
- Mobile responsiveness
- Page load perception (fast/moderate/slow)
- Social media links and which platforms

### Customer-Facing Language
- How they describe their audience
- Pain points they address in copy
- Objections they preemptively handle
- Emotional vs rational messaging balance
- Industry jargon level

---

## Handling Incomplete Data

Apply accuracy protocol strictly during crawl:
- If a page exists but has thin content → note as [EXTRACTED] with "limited content on page"
- If a data point isn't visible anywhere on site → mark BLANK with reason ("not listed on website — needs client intake")
- If pricing is "contact us" → mark as [EXTRACTED] "pricing not public, requires inquiry"
- Never infer pricing, revenue, or team size from general industry knowledge

## Output Format

Crawl results go to `sources/website-crawl-{date}.json` as raw data. The structured findings get written into wiki pages (business.md, offerings.md, digital-presence.md) during Steps 2-6 of the skill flow.
