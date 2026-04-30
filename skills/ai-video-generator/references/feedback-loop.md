# Feedback Loop — ai-video-generator

Per the Mandatory Session Close Protocol in CLAUDE.md, every skill run ends with a feedback loop.

## Format

Append to SKILL.md → Learnings & Rules section. Format:

```
[YYYY-MM-DD] [CLIENT-TYPE] Finding → Action
```

## What to capture

Every run, ask:

1. **Routing accuracy.** Did the model picker choose well? Any scene where Kling underperformed and Veo was needed (or vice versa)? Note model + scene-type pair for future routing rule tuning.

2. **Prompt quality.** Did any Higgsfield generation come back unusable? Why? Prompt too vague, too long, conflicting motion verbs, missing camera angle? Update `references/storyboard-schema.md` with prompt-writing guidance.

3. **Credit accuracy.** Did actual credit burn match the estimate? If a model burned more than expected, update `references/model-routing.md` matrix.

4. **Watermark detection.** Did `validate_output.py` correctly catch (or miss) a watermark? If it false-negatived, tune ROI sampling regions.

5. **Caption + chip overlay.** Any face-overlap or brand-color clash? Note client + issue for that client's brand-identity.md to flag.

6. **VO quality.** Did ChatterBox produce delivery that matched voice-direction tags? If not, tune emotion tag mapping.

## Cross-skill patterns

If the same finding shows up across multiple runs, append a one-liner to `Desktop/.claude/skills/_skill-corrections-log.md`:

```
YYYY-MM-DD | ai-video-generator | <tag> | <one-line summary> | <files-touched>
```

Tags from the corrections log header: scope-creep, mode-confusion, validator-gap, validator-false-positive, prompt-drift, deliverable-gap, path-detection, output-format, voice-rule, other.

For this skill specifically, expect tags:

- `prompt-drift` — Higgsfield prompts that worked stop working after model updates
- `validator-false-positive` — watermark-detection ROI catches a brand-chip pixel
- `validator-gap` — a scene rendered with off-aspect dimensions and got delivered
- `routing-miss` — model picker chose Kling but scene needed Veo (or vice versa)

## When to patch the skill mid-run

Per the Skill Auto-Update Rule:

1. If a script breaks → fix script + update SKILL.md + write Learnings entry — same turn
2. If a reference rule is wrong → fix reference + update SKILL.md if step description changed + write entry
3. If output format changes → fix output schema + update downstream consumers (scheduler-publisher, video-edit, post-launch-optimization)

Never defer to "I'll update the skill later." That's how skills stop learning.
