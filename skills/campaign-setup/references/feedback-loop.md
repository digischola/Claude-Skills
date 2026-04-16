# Feedback Loop — campaign-setup

Runs after every skill execution to capture learnings and improve quality.

---

## Quality Self-Check

After generating all outputs, answer honestly:

1. **Did every CSV pass the validator with 0 CRITICAL?**
   - If no → the fix must be added to `scripts/validate_output.py` AND to the checklist AND to the relevant schema reference. Three-layer defense (rule: same meta-rule as landing-page-builder).

2. **Did character limits cause any truncations?**
   - If yes → ad-copywriter upstream produced copy that exceeded the limit. Update the ad-copywriter skill's learnings with the client type and the limit that was missed.

3. **Did any `<REPLACE_ME>` tokens slip through without being listed in the checklist?**
   - If yes → validator missed them. Add a token-scan step.

4. **Were there any campaign types in the media plan that we couldn't fully support (PMax, Discovery, catalog)?**
   - If yes → document what was missing and what manual steps the user must take.

5. **Did upstream deliverables have any gaps that forced standalone-mode fallback?**
   - If yes → note which fields were missing so upstream skills can strengthen their output.

6. **Did the naming convention hold across all generated entities?**
   - If yes → campaign → ad group → ad names all traceable to media plan.

7. **Is the launch runbook actually followable by a human who didn't build the campaigns?**
   - Reread with fresh eyes. Any "obvious" step missing = runbook defect.

---

## Learning Entry Format

Append to SKILL.md's Learnings & Rules section:

```
[YYYY-MM-DD] [CLIENT_TYPE] {Finding} → {Action taken}
```

### Examples (format reference only)

```
[2026-04-20] [B2C Hospitality] Google RSA import failed on 3 ads — 2 headlines over 30 chars despite ad-copywriter validator pass → Ad-copywriter validator was counting grapheme clusters not UTF-8 length. Fixed in ad-copywriter/scripts/validate_output.py and added cross-check in campaign-setup validator.

[2026-04-21] [SaaS B2B] Meta bulk import CSV rejected Instant Form ID — form existed but wasn't yet connected to the Page → Added Instant Form ↔ Page linkage check to pre-launch checklist Section 1 (Tracking Infrastructure).

[2026-04-22] [Luxury Retail] Shared negative keyword list only attached to 2 of 4 campaigns after import → 08-negative-keywords.csv needs explicit Shared Set attachment rows, not just the keyword list itself. Updated google-ads-editor-schema.md Section 8.
```

---

## Meta-Rule: Three-Layer Defense

When a reviewer (human or downstream step) catches something the validator missed, the fix has THREE parts:

1. **Fix the instance** — correct the current client's output
2. **Add the check to the validator** — `scripts/validate_output.py` gets a new rule
3. **Add the rule to the reference** — schema file or checklist gets the explicit constraint

Skipping any of these means the next session will repeat the failure.

---

## Downstream Validation Signal

After post-launch-optimization runs its first report (Day 7), it should report back:
- Any campaigns that had config issues only visible in live data (e.g., wrong conversion event, wrong audience)
- Any naming mismatches between CSV and what appears in the platform

Those signals feed back into this skill's learnings.
