# Client Shareability — First-Copy Quality Rule

**Rule:** Every file in `{Client}/outputs/` (or any folder a client may receive) must read like a first copy. No correction trails. No audit history. No internal-process commentary. Even if the analysis was iterated 5 times during the session, the final deliverable presents only the final analysis — not the journey to it.

This rule applies to every skill that writes to `outputs/` or a path that may end up in a client's hands. Adopted 2026-04-26 after Living Flow Yoga deliverables shipped with visible "[Correction 2026-04-25]" banners + "Pre-Launch Audit (2026-04-26) — Reality Check Applied" sections + "Updated 2026-04-25 with real $2.97 CPC (was $41.67 at $2.50 assumed CPC)" parentheticals.

## What's prohibited in client-facing files

### Process commentary

- "Earlier drafts cited X — that figure was misattributed..."
- "[Correction 2026-04-DD] / Reality Check / Pre-Launch Audit"
- "(Was X at Y assumed CPC — real data tightens margin but verdict holds.)"
- "Updated 2026-04-DD with real..."
- "Updated 2026-04-DD · Real CPC unit economics"
- "(refreshed 2026-04-DD)"
- "Course Correction · Disproven / Strengthened" (when reframed as a process correction)
- "DISPROVEN by keyword data" (process framing) — present the data finding directly without the "earlier we thought X" framing

### Audit trails / decision history

- "False claims removed from this set after pre-launch audit"
- "All 7 RSA mentions stripped, callout replaced with..."
- "AG3 reframed from 'X' → 'Y'; N keywords dropped"
- "Mayank audited / Natalie has accepted / inflated 18×"
- "ACL §18/§29 risk eliminated. Do not re-introduce..."

### Internal architecture leakage

- Skill names exposed: "Run landing-page-builder skill" / "Mayank → landing-page-builder skill"
- File paths from the working folder: "intro-pass-landing-page.html which is sitting unused"
- Internal flag references: `do_not_launch_until_phase_0_complete: true`
- Validator framings: "Gate A FIRED", "BEST CASE — DO NOT LAUNCH banner"
- Internal workflow names: "post-launch-optimization Layer 4"

### Hallucination / data-correction admissions

- "Perplexity conflated the two..."
- "Inflated 18× from MindBody-vote data..."
- "Misattributed as Google reviews..."
- Fix the underlying data and present it cleanly. Don't admit the hallucination in the client document.

## What's allowed in client-facing files

- **Source citations**: "Source: Roy Morgan 2023 [6]" — fine, normal in research
- **Methodology notes**: "Real CPC $2.97 from AU Keyword Planner" — fine, attributes the data
- **Confidence labels**: "Confidence: HIGH" — fine, signals certainty
- **Date ranges**: "Q4 2025 data" — fine, scopes the data
- **Owner labels**: "Owner: Digischola" / "Owner: Natalie" — fine for accountability (but use entity names, not personal "Mayank → skill" patterns)
- **Footer credit**: "Prepared by [Analyst Name] · Digischola · [Date]" — single-line byline is fine; this isn't process commentary

## What to do with the audit history that needs to be preserved

It's still important to preserve the audit trail for the analyst's own memory + future skill-chain runs. Move it OUT of `outputs/` and INTO:

- `working/audit-trail-{date}.md` — per-deliverable change log
- `wiki/log.md` — append a log entry per session
- Skill-level Learnings & Rules section (as we already do)

The audit trail lives in the working folder. The deliverable lives in outputs. Never mix.

## Skill-level rule

Every skill that writes to `outputs/` MUST:

1. Generate the deliverable in first-copy voice — present the analysis as if it were the first attempt
2. If the skill discovers/corrects a finding mid-session, the correction goes to `working/audit-trail.md` or `wiki/log.md` — NOT into the deliverable
3. Validator runs `scripts/validate_output.py` against patterns in `references/client-shareability-patterns.md` (or this doc) and CRITICAL-fails any match

## Validator pattern set

Patterns that auto-fail validation when found in `outputs/*.html`, `outputs/*.md`, or any client-facing file:

```
\[Correction\s*\d{4}-\d{2}-\d{2}\]
Pre-Launch Audit \(\d{4}-\d{2}-\d{2}\)
Reality Check Applied
Earlier drafts (cited|said|claimed)
\(Was [^)]*at \$[\d.]+\s*assumed
Updated \d{4}-\d{2}-\d{2} with (real|new|corrected)
Course Correction\s*·\s*(Disproven|Strengthened)
DISPROVEN by keyword data
False claims removed
N RSA mentions stripped
AG\d reframed from
keywords dropped during
ACL §\d+
inflated \d+×
Perplexity (conflated|hallucinat)
misattributed
fabricated (claim|figure|count)
Mayank → \S+\s*skill
Run \S+-\S+\s*skill
do_not_launch_until_phase_0
Gate [AB] (FIRED|fired)
BEST CASE\s*—\s*DO NOT LAUNCH
phase_0_prerequisites
```

## Why the rule exists

Two reasons:

1. **Client trust**: A correction banner reads as "we made mistakes and admitted them mid-document". A first-copy presentation reads as "this is the considered finding". Same data, different perceived rigor. Clients buy strategy on perceived rigor.
2. **Liability surface**: Documents that admit "earlier draft said X but reality is Y" can be cited back as proof the analyst hallucinated. Documents that present only Y don't have that surface area.

Internal preserves audit trail. External presents conclusions. Don't blur the line.
