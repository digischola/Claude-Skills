# Feedback Loop — video-edit

Append a dated entry to SKILL.md's `## Learnings & Rules` section after every session.

## Format

`[YYYY-MM-DD] [CLIENT TYPE] Finding → Action`

- **YYYY-MM-DD** — date the session ran
- **CLIENT TYPE** — bracketed descriptor: `[TESTIMONIAL]`, `[AD]`, `[DEMO]`, `[EVENT]`, `[PERSONAL]`
- **Finding** — what surprised / broke / worked (one sentence)
- **Action** — what changed in the skill as a result (one sentence)

## Examples

```
[2026-04-25] [TESTIMONIAL] Client brand has mint-green primary that clashed with apple-premium's blue accent — overrode per brand-config.json → Action: brief-translator already handles this, confirmed working
[2026-04-27] [DEMO] Source was 4k 60fps screen-record; hyperframes lint flagged fps mismatch → Action: added fps normalization to ffmpeg_prepass.sh so hyperframes always sees 30fps
[2026-05-02] [AD] gen-z-punchy + 12s vertical source: caption animation felt chaotic (too many color pops) → Action: capped color-pop keywords at 1 per 3 seconds in brief-translator output
```

## Rules

1. Capture entries **as part of the same fix** — never defer to "next session."
2. Keep Learnings & Rules to under 30 lines in SKILL.md. Prune quarterly — promote durable patterns into references/ where they belong.
3. If a pattern appears 3+ times, stop logging it as a learning and codify it:
   - If it's a content rule → update aesthetic-presets.md
   - If it's a pipeline rule → update the relevant script
   - If it's a translator rule → update brief-translator.md

## What Not to Log

- Client names or confidential metrics — use generic descriptors
- One-off "it worked" — only log if something was non-obvious or counter to defaults
- Bugs that are actually skill-wide issues (those go in the session's general notes, not a specific skill's learnings)
