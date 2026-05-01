# Feedback Loop

Every session ending in a delivered campaign-run must add a Learnings & Rules entry to SKILL.md. Format:

```
[YYYY-MM-DD] [CLIENT-TYPE | SECTOR | NOTABLE-CONTEXT] Finding → Action
```

## What to capture

**Things that surprised you (positive or negative):**
- A model produced unexpectedly good or bad results for a specific concept type
- Reference image attachment changed output quality dramatically
- A prompt pattern from one campaign worked / failed in another
- The voice-check caught (or missed) something important
- Ultra plan unlimited tier (Nano Banana Flash) hit a quality ceiling for X concept type
- Religious-brand guardrail triggered an interesting case (e.g., devotee photo without consent surfaced)

**Things that took longer than they should have:**
- Manual re-runs because aspect-ratio mismatch wasn't caught at planning
- Polling loop hit timeout because Higgsfield queue was slow
- Reference upload rate-limited
- Composite step needed manual intervention because composite_sacred.py couldn't auto-place

**Skill-improvement candidates (per Skill Protocol Supremacy):**
- Validator missed a real failure mode → patch validator + add eval
- Routing chose wrong model for a clear concept type → tighten model-routing.md decision tree
- Reference-tag inference was wrong → tighten inventory_references.py prompt
- Brand-voice fit scoring drifted from analyst preference → re-anchor scoring rubric

## How to update

1. Add a one-line entry to SKILL.md Learnings & Rules section (newest at top after the most recent entry)
2. If the finding requires a script/reference change → make the change in the same session per Skill Auto-Update Rule (CLAUDE.md):
   - Patch the script/reference
   - Update SKILL.md step description if behavior changed
   - Update wiki if a delivered artifact is affected
3. If the finding is a recurring failure pattern → add a corresponding eval to `evals/evals.json`
4. Append one line to `.claude/skills/_skill-corrections-log.md` per Skill Corrections Log (CLAUDE.md):
   ```
   YYYY-MM-DD | ai-image-generator | <type-tag> | one-line summary | files-touched
   ```

## Type tags for corrections log

- `validator-gap` — validator didn't catch a real failure
- `validator-false-positive` — validator flagged something that was fine
- `routing-mismatch` — model router picked the wrong tier for a clear case
- `ref-tagging-error` — inventory_references mistagged a reference image
- `voice-check-gap` — voice-check missed a hype/em-dash/bait
- `voice-check-false-positive` — voice-check rejected acceptable copy
- `religious-guardrail-gap` — sacred handling missed a case
- `composite-failure` — sacred composite step failed silently or misplaced
- `aspect-mismatch` — model didn't support requested aspect, fell back unexpectedly
- `cost-blowup` — actual credits exceeded estimate by >50%
- `download-failure` — download step failed transiently or permanently
- `dashboard-rendering` — dashboard.html didn't render correctly
- `mcp-version-drift` — Higgsfield renamed/deprecated a model or tool
- `prompt-drift` — prompt template generated bland or off-brand outputs

## Cross-skill flagging

When this skill discovers something actionable by another skill, note it in the output and update the other skill's learnings if it's a recurring pattern.

Examples:
- ad-copywriter image prompts consistently missing required `requires_reference_image` flag → flag for ad-copywriter learning + suggest checklist update
- Religious clients consistently need composite-into-design for deity → flag for ad-copywriter to mark `requires_composite: true` upstream
- campaign-setup expects creative folder structure that doesn't match what we ship → flag for output-structure update on either side
