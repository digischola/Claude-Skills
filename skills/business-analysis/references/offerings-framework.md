# Offerings Documentation Framework

How to document each product/service/offering in the wiki. Every offering gets its own section in `_engine/wiki/offerings.md` with a standardized structure.

---

## Identifying Offerings

An "offering" is anything the business sells, provides, or promotes as a distinct service/product. Signs of a distinct offering:
- Has its own page or section on the website
- Has its own pricing
- Targets a different audience segment
- Could be marketed independently

**Examples by business type:**
- Retreat center: wellness retreat, yoga teacher training, corporate offsite, day spa
- Restaurant: dine-in, catering, private events, meal delivery
- Temple: regular services, special events, cultural programs, donation drives
- IT company: managed services, cloud migration, cybersecurity, consulting

---

## Per-Offering Documentation Structure

Each offering section in `_engine/wiki/offerings.md` follows this format:

```markdown
## {Offering Name}

> Status: {Active/Seasonal/Upcoming/Discontinued} | Page: {URL} | Last updated: {date}

### Overview
{2-3 sentence description of what this offering is}

### Target Audience
- **Who buys this:** {description}
- **Decision maker:** {title/role if B2B, or demographic if B2C}
- **Purchase triggers:** {what causes someone to seek this out}

### Pricing & Model
- **Price range:** {visible pricing or "not public"}
- **Pricing model:** {per session/package/subscription/one-time/donation}
- **Booking mechanism:** {online booking, phone, email, walk-in}

### Differentiation
- **USP:** {what makes this offering unique vs alternatives}
- **Key claims on website:** {specific claims made in copy}
- **Social proof:** {testimonials, reviews, case studies specific to this offering}

### Seasonality & Timing
- **Peak periods:** {when demand is highest}
- **Off-peak:** {when demand drops}
- **Lead time:** {how far in advance do people book/buy}

### Campaign Priority Context
- **Client preference:** {does client want to promote this? from intake}
- **Prioritization signals:** {margin, audience size, competition level — from Step 7}

### Gaps
{What we don't know about this offering — BLANK fields with reasons}
```

---

## Multiple Offerings Rules

1. **Document ALL visible offerings** during initial business analysis, not just the one the client wants to advertise. Context matters.
2. **Don't merge similar offerings.** A "90-minute massage" and a "full-day spa package" are separate offerings even if they're in the same category.
3. **Flag cross-sell relationships.** If Offering A naturally leads to Offering B (e.g., drop-in yoga → teacher training), note it.
4. **Thin offerings are OK.** If a page has minimal info, document what's there and mark the rest BLANK. Don't pad with assumptions.

## Downstream Usage

Market research reads `offerings.md` to scope its Perplexity prompt to a specific offering. Ad copywriter reads it for messaging angles. Campaign strategy reads it for budget allocation across offerings. Every downstream skill benefits from thorough offering documentation.
