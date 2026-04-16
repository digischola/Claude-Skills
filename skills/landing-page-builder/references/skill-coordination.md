# Skill Coordination — Landing Page Builder

## Upstream Skills (reads from)

### business-analysis
- `wiki/brand-identity.md` — tone of voice, brand personality
- `deliverables/brand-config.json` — colors, fonts, logo URL
- `wiki/offerings.md` — offering details, pricing, inclusions

### market-research
- `wiki/research.md` — buyer personas, competitor positioning
- `deliverables/*-research-report.md` — keyword themes, audience insights

### paid-media-strategy
- `deliverables/*-creative-brief.json` — campaign architecture, visual direction, image_gen_prompt_prefix, landing page mapping, A/B testing plan, proof element hierarchy
- `deliverables/*-strategy-report.md` — campaign goals, target audiences, budget context

### ad-copywriter
- `deliverables/*-ad-copy-report.md` — headlines, CTAs, value propositions, primary text
- `deliverables/*-meta-ads.csv` — Meta ad copy (primary text, headlines, descriptions)
- `deliverables/*-google-ads.csv` — Google RSA copy (headlines, descriptions)

### landing-page-audit
- `deliverables/*-landing-page-audit.md` — scored issues, fix recommendations, mockup-level suggestions
- Provides specific CRO/UX/copy problems to solve in the new page

### post-launch-optimization
- `deliverables/*-optimization-report.md` — conversion rate data, landing page friction signals (e.g., high CTR + low CVR = page issue)

## Downstream Skills (outputs for)

### post-launch-optimization
- Generated landing page URL becomes the destination for ad campaigns
- Optimization skill tracks conversion rate changes after new page deploys

### ad-copywriter
- Landing page copy informs message match between ad and page
- Headlines on page should align with ad headlines for consistency

## Output Files

| File | Location | Description |
|---|---|---|
| Landing page HTML | `{client}/deliverables/{page-name}-landing-page.html` | Full HTML prototype |
| Page spec JSON | `{client}/deliverables/{page-name}-page-spec.json` | Structured spec for Lovable rebuild |
| Wiki log entry | `{client}/wiki/log.md` | LANDING-PAGE entry |

## Standalone Mode

When no upstream wiki exists:
1. Ask for: page purpose, offer details, target audience, conversion action, brand colors/fonts
2. Use defaults from landing-page-research.md for section architecture
3. Use copy-frameworks.md for all copy generation
4. Skip creative brief and ad copy alignment steps

## Downstream Mode

When wiki + creative brief exist:
1. Auto-load brand-config.json, creative brief, ad copy report
2. Align page headlines with ad headlines (message match = +20-35% conversion)
3. Use creative brief's visual direction for imagery descriptions
4. Use proof element hierarchy from strategy for social proof ordering
5. If audit exists, address every CRITICAL and HIGH issue from audit
