---
name: visual-generator
description: "Digischola visual production — Higgsfield-first. Three modes: (A) carousel — Claude Design handoff + render_html_carousel.py produces a 10-slide PNG set. (B) illustration — Higgsfield Nano Banana 2 Flash (unlimited on Ultra plan) for non-photographic AI illustrations: backgrounds, iconography, decorative atmosphere. (C) reel — Higgsfield Kling 2.5 / Hailuo 2.3 / Seedance 1.0 (unlimited on Ultra) for 15-30 sec Reels via UI-mockup B-roll, abstract motion, or stylized illustration scenes. Hard guardrails: no AI photos of people, no AI deity imagery, no AI logos. Reads draft frontmatter for the visual brief; saves outputs to brand/social-images/<entry_id>/ and brand/videos/<entry_id>/. Use when user says: generate visual, make a carousel, create a Reel, render quote card, design brief, visual for this post, make a video, IG carousel, Reel for X, visual-generator. Do NOT trigger for: drafting post copy (use draft-week), planning the week (use weekly-ritual), capturing an idea (use ideas-in), client visual work (use ai-image-generator / ai-video-generator)."
---

# visual-generator (lean Higgsfield edition)

One skill, three paths. Higgsfield Ultra plan supplies unlimited AI image + video for non-photographic personal-brand work. The old Remotion + ChatterBox + Hyperframes stack was retired (2026-05-01 overhaul) — that complexity belonged in client-track skills.

## Modes

| Mode | Trigger | Output |
|---|---|---|
| `carousel` | "make a carousel", "render quote card", LI-carousel / IG-carousel slot in calendar | `brand/social-images/<entry_id>/slide-1.png ... slide-N.png` |
| `illustration` | "AI illustration for this post", `visual_request: illustration` in draft frontmatter | `brand/social-images/<entry_id>/illustration.png` |
| `reel` | "make a Reel", IG-Reel slot in calendar, `format: reel` in draft | `brand/videos/<entry_id>/reel.mp4` |

## Hard rules (Path C guardrails — non-negotiable)

1. **No AI photographs of people.** Mayank's face, any client's face, any human face — banned. Use the static portrait at `brand/_engine/face-samples/portrait.png` only on a Reel outro, and only as a real photo, not a generated one.
2. **No AI deity imagery, no AI religious symbols.** ISKM client work and Digischola personal-brand are subject to this. If a post about ISKM needs a visual, use the client's photography or hand-picked stock.
3. **No AI logos.** Generated logos misrepresent brand identity. Use Mayank's locked Digischola logo from `brand/_engine/wiki/brand-identity.md`.
4. **AI illustrations OK** — abstract backgrounds, iconography, typographic compositions, UI-mockup B-roll, decorative atmosphere. Per-scene opt-in via `allow_ai_illustration: true`.

Full Path C guardrails: `references/ai-illustration-mode.md`.

## Context loading

- `Desktop/Digischola/brand/_engine/wiki/brand-identity.md` — colors, fonts, logo, UI rules.
- `Desktop/Digischola/brand/_engine/wiki/voice-guide.md` — emoji + tone discipline.
- `Desktop/Digischola/brand/_engine/wiki/pillars.md` — must be `Status: LOCKED`.
- The source draft in `brand/queue/pending-approval/<draft>.md`.
- Skill references in `references/` — load only the active mode's flow.

## Mode A: carousel

Read `references/carousel-flow.md`. Summary:

1. Source draft has `format: carousel` (LI or IG). Pull hook from frontmatter or first body line.
2. Build `slides.json` — array of slide objects: `{ "headline": "...", "body": "...", "icon_hint": "..." }`. 8-10 slides.
3. Hand to Claude Design via `scripts/generate_brief.py` for design pass, OR write HTML directly using locked design tokens in `brand/_engine/wiki/brand-identity.md`.
4. Run `scripts/render_html_carousel.py --brief <slides.json> --out <output_dir>` — Playwright renders each slide to PNG at 1080x1080 (IG) or 1200x1500 (LI vertical).
5. Run `scripts/validate_output.py --carousel <output_dir>` — slide count, dimensions, font fidelity, color contrast.
6. Save final PNGs to `brand/social-images/<entry_id>/`.

## Mode B: illustration

Read `references/illustration-flow.md`. Summary:

1. Confirm `allow_ai_illustration: true` in the source draft frontmatter. If false → abort, suggest carousel instead.
2. Write a Higgsfield image prompt that respects guardrails (no people, no deity, no logos).
3. Route to Higgsfield Nano Banana 2 Flash (default — unlimited on Ultra). Escalate to Nano Banana Pro for typographic precision (paid).
4. Generate 3 variations. Score for brand fit (color match, voice fit, no banned elements).
5. Save winner to `brand/social-images/<entry_id>/illustration.png`. Log model + prompt + seed in `manifest.json`.

The Higgsfield invocation happens via the Higgsfield MCP tools (`mcp__b39cf66e..__generate_image`). This skill doesn't shell out to a Python wrapper — Claude calls the MCP directly during the session.

## Mode C: reel

Read `references/reel-flow.md`. Summary:

1. Source draft has `format: reel` or carousel adapted to Reel. Pull hook + body beats.
2. Build a 4-6 scene storyboard: hook (0-3s), 3-4 insight beats, outro (24-30s). Each beat is 4-6s.
3. For each scene, decide: live UI-mockup screenshot (preferred for LP-craft pillar) OR Higgsfield video gen (preferred for atmosphere / abstract).
4. UI-mockup scenes — Claude writes simple HTML mockups; Playwright/ffmpeg captures them as a clip.
5. AI video scenes — route to Higgsfield via `mcp__b39cf66e..__generate_video`:
   - **Kling 2.5** — cinematic, motion-controlled (default for hero scenes)
   - **Hailuo 2.3** — motion-heavy, quick output
   - **Seedance 1.0** — stylized, illustrative
   - All three are unlimited on Mayank's Ultra plan.
   - Each clip 6-8 seconds.
6. Voiceover — kinetic on-screen text by default; spoken VO optional via Higgsfield voice (when stable) or skip silent.
7. Stitch with ffmpeg. Add brand chip overlay (logo bottom-right). Output `brand/videos/<entry_id>/reel.mp4`.
8. Run `scripts/validate_output.py --reel <reel.mp4>` — duration, aspect ratio, audio loudness, watermark presence, banned-element scan.

## Manifest

Every output gets a `manifest.json` next to it:

```json
{
  "entry_id": "<id>",
  "draft_file": "<draft.md>",
  "mode": "carousel | illustration | reel",
  "outputs": ["slide-1.png", "..."],
  "higgsfield_calls": [
    {"model": "nano_banana_flash", "prompt": "...", "seed": 12345, "credits": 0}
  ],
  "validator_status": "clean",
  "rendered_at": "<iso8601>"
}
```

## Validation

`scripts/validate_output.py` runs per output. Checks:
- File exists, non-empty, correct format
- Dimensions match channel spec
- For Reels: duration 15-30s, audio peak < -3 dBFS, brand chip present
- Banned element scan: no human face detection (OpenCV cascade), no flagged keywords in prompt

## Coordination

- Upstream: `draft-week` produces drafts with visual hints. This skill reads them.
- Downstream: `scheduler-publisher` reads draft frontmatter — if `visual_assets:` references a path that exists, it attaches to the post.
- For client-track visuals (not personal-brand), use `ai-image-generator` and `ai-video-generator` directly — those have full client wiki context and broader model access.

## Learnings & Rules

Capture insights here per the 7+3 rule. Format: `[YYYY-MM-DD] [mode] Finding → Action`.

- [2026-05-01] [overhaul] Stripped Remotion + ChatterBox + Hyperframes stack. Replaced with Higgsfield-first paths (Nano Banana Flash for images, Kling/Hailuo/Seedance for video — all unlimited on Ultra). → Old complexity moved to quarantine. Visual production now matches the personal-brand cadence (1-2 visuals/week) instead of the client-grade pipeline.

## Feedback loop

See `references/feedback-loop.md`.
