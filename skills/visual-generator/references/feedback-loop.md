# Feedback Loop (visual-generator)

Per CLAUDE.md Mandatory Session Close Protocol. Entries go in the `## Learnings & Rules` section of SKILL.md.

## What to capture

**Always capture:**
- Engine-selection misfits — a format was routed to Claude Design but actually needed Hyperframes (or vice versa). Update engine-selection.md.
- Brief template gaps — the brief didn't include a field Claude Design or Hyperframes needed, causing a bad first render. Update brief template in generate_brief.py.
- Brand memory drift — Claude Design's output violated brand rules (wrong color, em dash, etc.) despite the brand-memory setup. May need to re-seed or reinforce in the brief.
- Hyperframes version changes — if the HeyGen repo API shifts and the "make a video" skill invocation breaks, update hyperframes-setup.md.
- Render quality issues — MP4 encoding came out wrong (wrong codec, low bitrate, wrong aspect). Update render handoff instructions.
- Asset import naming collisions or ambiguous source linkage. Update import_assets.py logic.

**Skip:**
- Individual aesthetic preferences per visual (those are per-design feedback, not skill-level rules)

## Context tags

- `[Engine]` — engine-selection.md adjustment
- `[Brief]` — generate_brief.py output format adjustment
- `[Brand]` — brand memory / Claude Design drift
- `[Hyperframes]` — Hyperframes version or workflow issue
- `[Import]` — import_assets.py orchestration issue
- `[Render]` — rendering pipeline (Chrome headless, ffmpeg) issue

## When a learning triggers a reference update

7+3 rule: update the reference file + log the learning + update related wiki if it affects a generated deliverable.

## Cross-skill feedback

When a pattern is visual-only but affects content-level decisions (e.g., a hook is great on text but terrible as a carousel slide 1 because the data doesn't fit visually), propagate that finding to:
- `repurpose/references/transformation-recipes.md` — note which LI → IG-carousel transformations work vs don't
- `post-writer/references/hook-library.md` — tag hooks that struggle visually

This keeps upstream skills aware of downstream rendering constraints.

## Meta-learning (about tools themselves)

This skill's references assume current state of Claude Design + Hyperframes. Both tools are early / evolving (Claude Design launched research preview 2026-04-17). When either tool releases breaking changes or new capabilities, update:
- engine-selection.md (decision tree)
- The corresponding workflow file (claude-design-workflow.md OR hyperframes-setup.md)
- Relevant brief templates in generate_brief.py

Tag these as `[Tool-update]` for clarity.
