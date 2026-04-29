# Skill Coordination — Landing Page Builder

## Upstream Skills (reads from)

### business-analysis
- `_engine/wiki/brand-identity.md` — tone of voice, brand personality
- `_engine/brand-config.json` — colors, fonts, logo URL
- `_engine/wiki/offerings.md` — offering details, pricing, inclusions

### market-research
- `_engine/wiki/research.md` — buyer personas, competitor positioning
- `research-dashboard.html` at folder root (default short name; legacy fallback `*-research-dashboard.html`) — keyword themes, audience insights presentable; raw report at `_engine/working/market-research.md` (legacy fallback `_engine/working/*-market-research.md`)

### paid-media-strategy
- `_engine/working/creative-brief.json` (default short name; legacy fallback `_engine/working/*-creative-brief.json`) — campaign architecture, visual direction, image_gen_prompt_prefix, landing page mapping, A/B testing plan, proof element hierarchy
- `_engine/working/paid-media-strategy.md` (default short name; legacy fallback `_engine/working/*-paid-media-strategy.md` or `*-strategy-report.md`) — campaign goals, target audiences, budget context

### ad-copywriter
- `_engine/working/ad-copy-report.md` (default short name; legacy fallback `_engine/working/*-ad-copy-report.md`) — headlines, CTAs, value propositions, primary text
- `_engine/working/meta-ads.csv` (default short name; legacy fallback `_engine/working/*-meta-ads.csv`) — Meta ad copy (primary text, headlines, descriptions; intermediate CSV)
- `_engine/working/google-ads.csv` (default short name; legacy fallback `_engine/working/*-google-ads.csv`) — Google RSA copy (headlines, descriptions; intermediate CSV)

### landing-page-audit
- `landing-page-audit.html` at the client/program folder root (default short name; multi-page collision or legacy fallback `*-landing-page-audit.html`) + `_engine/working/audit-findings.md` (default short name; multi-page collision or legacy fallback `_engine/working/*-audit-findings.md`) — scored issues, fix recommendations, mockup-level suggestions
- Provides specific CRO/UX/copy problems to solve in the new page

### post-launch-optimization
- `_engine/working/optimization-report.md` (default short name; legacy fallback `_engine/working/*-optimization-report.md`) — conversion rate data, landing page friction signals (e.g., high CTR + low CVR = page issue)

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
| Landing page bundle | `{client}/landing-page/index.html` (folder root, presentable bundle — default short name; multi-page collision fallback: `{client}/{page-name}/index.html`) | Full HTML prototype + assets |
| Page spec JSON | `{client}/_engine/working/page-spec.json` (default short name; multi-page collision fallback: `{client}/_engine/working/{page-name}-page-spec.json`) | Structured spec for Lovable rebuild |
| Wiki log entry | `{client}/_engine/wiki/log.md` | LANDING-PAGE entry |

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
