# Feedback Loop — case-study-generator

## When to log a learning

Add a dated entry to SKILL.md "Learnings & Rules" when:

- A new public-allowed client is added to digischola.in (extends the named-client list)
- A validator rule fired falsely + needed tuning (e.g., metric drift detection too strict)
- A platform's format constraints changed (X char limit, IG carousel max slides)
- A new structural convention emerges (e.g., 4-stage instead of 6-stage for shorter case studies)
- A bundle was published + performance-review showed which format won (LI carousel vs blog vs X thread vs IG)
- An anonymization template needs to be added for a new industry

## Format

```
- [YYYY-MM-DD] [CONTEXT TAG] Finding → Action.
```

Context tags:
- `[Initial build]`
- `[Naming]` — client-naming policy edits
- `[Validator]` — validate_case_study.py issues
- `[Structure]` — Setup→Problem→Diagnosis→Fix→Result→Lesson framework changes
- `[Platform adapt]` — per-channel format adjustments
- `[Cross-skill]` — interaction with post-writer / visual-generator / scheduler-publisher
- `[Performance]` — feedback from performance-review on which deliverable won

## Cross-skill impact

case-study-generator interacts with:
- **idea-bank.json** (work-capture's data store) — reads client-win entries
- **voice-guide.md** — enforces Conservative naming + universal voice rules
- **credentials.md** — public-allowed clients
- **post-writer/scripts/validate_post.py** — reused for per-deliverable validation
- **visual-generator/scripts/generate_brief.py** — invoked for LI + IG carousel briefs
- **scheduler-publisher** — bundle deliverables ship via apply_calendar.py + tick.py
- **performance-review** — measures engagement per deliverable; feedback informs next case study's format weighting

If any of these change their interface (esp. validate_post.py CLI signature or generate_brief.py arguments), update case_study.py's invocation accordingly.

## Quarterly review checklist

Every 3 months:
1. **Public client list** — has Mayank added new case studies to digischola.in? Update `client-naming-policy.md` to reflect.
2. **Bundle performance** — pull last 3-5 case-study bundles from queue/published/. Which deliverable performed best per bundle (LI vs X vs blog vs IG)? Note the pattern. After 3 bundles, the data may suggest dropping a low-performing format.
3. **Structure tweaks** — has any case study found that 4-stage works better than 6-stage for shorter wins? Codify.
4. **Validator false positives** — any case where Claude had to manually override the validator? If a check is too strict, tune the threshold.

## Eval candidates

Add a test case to `evals/evals.json` when:

- A new validation rule lands
- A new platform adaptation rule changes (e.g., X allows longer threads now)
- A new public client is added (test that naming logic picks up the client)
- A new anonymization industry template is added

Each test should run with mock idea-bank entries + dry-run mode (no actual file writes to pending-approval).
