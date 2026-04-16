# Feedback Loop — Landing Page Builder

Run this at session close after every page generation.

## Checklist

### Design Quality
- [ ] Does the page follow the section architecture for its page type? (landing-page-research.md §1)
- [ ] Is the above-the-fold content correct? (headline, CTA, trust signal visible without scroll)
- [ ] Does spacing follow the 8px grid system?
- [ ] Are animations limited to GPU-accelerated properties (transform, opacity)?
- [ ] Is the page under 150KB (prototype) / 2MB (with images)?
- [ ] Does the page respect prefers-reduced-motion?
- [ ] Is the layout mobile-responsive (375px test)?

### Copy Quality
- [ ] Does the headline follow a formula from copy-frameworks.md §1?
- [ ] Is copy at grade 6-8 readability level?
- [ ] Are CTAs first-person, action + benefit, 2-5 words?
- [ ] Does the emotional arc follow: aspiration → logic → trust → urgency?
- [ ] Are benefits framed as outcomes, not features?
- [ ] Is microcopy present near every CTA (risk reducer, time reducer, or social proof)?

### CRO Compliance
- [ ] Single primary conversion goal per page?
- [ ] CTAs placed before 50% scroll mark?
- [ ] Sticky CTA for mobile?
- [ ] Form fields ≤ 5?
- [ ] Social proof distributed (near hero, benefits, pricing)?
- [ ] FAQ handles top objections for this page type?

### Brand Consistency
- [ ] Colors match brand-config.json?
- [ ] Typography uses client fonts or appropriate wellness pairings?
- [ ] Tone matches audience sophistication level?
- [ ] No stock imagery language — real/specific descriptions?

### Lovable Portability
- [ ] Semantic HTML structure (section, header, main, footer)?
- [ ] Clean class naming (BEM or utility)?
- [ ] No deeply nested animation wrappers?
- [ ] Flexbox/Grid layout (no float hacks)?
- [ ] No canvas/complex SVG that Lovable can't rebuild?

## Learning Entry Format

```
[DATE] [PAGE TYPE] Finding → Action
```

Example:
```
[2026-04-20] [RETREAT BOOKING] Hero image pushed CTA below fold on iPhone SE → Added max-height: 45vh constraint on hero images for all page types.
```

## Quality Benchmarks

(Fill after 5+ pages generated)

| Metric | Target | Actual |
|---|---|---|
| Sections match type blueprint | 100% | |
| CTA above fold (mobile) | 100% | |
| Grade 6-8 readability | 100% | |
| Under 150KB prototype | 100% | |
| Client approval rate | >80% | |
| Validator pass rate | >90% | |
