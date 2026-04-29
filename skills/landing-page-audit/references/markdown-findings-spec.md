# Markdown Findings Report — Specification

Structured markdown file produced alongside the HTML dashboard. Portable, shareable version for client calls, email summaries, and downstream skill consumption.

**File path:** `{client-folder}/_engine/working/{page-name}-audit-findings.md`

---

## Template

```
# [Page Name] — Landing Page Audit Findings
Date | Consultant | URL

## Scores
Overall (X/10) | CRO (X/10) | Visual UX (X/10) | Persuasion (X/10)

## Critical Issues (fix before ads)
### 1. [Issue title]
**Pillar:** CRO/Visual/Persuasion | **Criterion:** [name] | **Score:** X/10
**Problem:** What's wrong and why it kills conversions
**Fix:** Specific, actionable recommendation with exact copy/layout changes

## Major Issues (fix in first sprint)
(same format)

## Minor Issues (fix when time allows)
(same format)

## Pillar Breakdown
### CRO Fundamentals (X/10)
- Criterion: score — one-line finding
(for each criterion)

### Visual UI/UX (X/10)
(same format)

### Persuasion & Copy (X/10)
(same format)

## Recommendations Summary
### Immediate (before ad launch)
1. ...
### Sprint 1
1. ...
### Polish
1. ...
```

---

## Rules

- Every finding carries `[EXTRACTED]` or `[INFERRED]` tags per accuracy protocol
- Issue numbering matches the HTML dashboard (same issue #1 in both files)
- Fix recommendations are identical between MD and HTML — no summarizing or trimming
- Include sub-scores per criterion in the pillar breakdown
- No CSS, no charts — pure readable markdown
- Downstream skills (ad-copywriter, paid-media-strategy) read this MD directly

---

## Why separate from the HTML dashboard

The HTML dashboard is great for client presentation but impractical for:
- Quick reference during client calls
- Email sharing
- Downstream skill consumption (skills can't parse HTML reliably)

The markdown findings report closes that gap without duplicating effort — same data, different format.
