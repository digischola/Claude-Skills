# Feedback Loop Protocol (post-writer)

Every skill session ends with a feedback entry per CLAUDE.md Mandatory Session Close Protocol.

## Format

Add entries to the `## Learnings & Rules` section at the bottom of SKILL.md:

```
- [YYYY-MM-DD] [CONTEXT] Finding: {observation}. → Action: {concrete change}.
```

## What to capture (post-writer specific)

**Always capture:**
- Hook patterns the user flagged as "not my voice" (update hook-library.md to deprecate or rewrite that row)
- Credential anchoring attempts the user rejected (update credential-anchoring.md with specifics)
- Channel format choices the user overrode (update platform-specs.md if the research was wrong)
- AI-integration phrasing the user rewrote (update ai-integration.md example list)
- Validator misses (the script passed a post the user still rejected — add a new check)

**Skip:**
- Individual post tweaks (those are per-draft edits, not skill-level learnings)
- Opinions without a specific rule change

## Context tags specific to this skill

- `[Hook]` — hook-library adjustment
- `[Voice]` — voice-frameworks or voice-guide mismatch
- `[Platform]` — platform-specs algorithm or format rule refinement
- `[Credential]` — credential-anchoring cadence issue
- `[AI-theme]` — AI integration phrasing adjustment
- `[Regional]` — regional-nuances audience mismatch
- `[Validator]` — validate_post.py gap

## When a learning triggers a reference update

The 7+3 rule applies: if a reference file needs updating, update it AND log the learning in SKILL.md AND update any downstream consumers.

Example: user rejects a hook pattern because it sounds too salesy for their voice.
1. Update hook-library.md to deprecate or rewrite that row
2. Add learning to SKILL.md: "[DATE] [Hook] Pattern X rejected as too salesy. → Action: rewrote row X in hook-library.md, removed the 'CTA angle' sub-variant."
3. If a downstream skill (repurpose) uses the same pattern, flag it there too.

## Tier-1 promotion (future)

When `performance-review` is built, it will identify hook patterns that consistently beat benchmarks. These get promoted to "Tier 1" in hook-library.md. The skill should weight Tier 1 hooks higher when generating candidates.

Similarly, voice-framework techniques that land well get flagged in voice-frameworks.md with a usage note.

This creates a learning loop: post-writer generates → user ships → performance-review measures → results feed back into post-writer references. Every 4 weeks the skill gets sharper.
