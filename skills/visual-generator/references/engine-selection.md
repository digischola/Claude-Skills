# Engine Selection — Path A (Claude Design) vs Path B (Remotion)

The visual-generator skill has two paths. Pick the right one per target format.

## Decision table

| Target format | Path | Engine | Why |
|---|---|---|---|
| IG feed carousel (7-10 static slides) | A | Claude Design | Fast, brand memory handles consistency, HTML output renders cleanly |
| IG Story (single frame + simple anim) | A | Claude Design | Same; Story is 9:16 single slide |
| Quote card (1080×1080 static) | A | Claude Design | One static slide, no animation needed |
| LinkedIn document carousel (PDF) | A | Claude Design | Supports multi-page PDF via handoff |
| LinkedIn image post (single image) | A | Claude Design | Same as quote card |
| Animated graphic (no face, 10-20 sec) | A | Claude Design | Claude Design handles CSS-animated HTML well; hand off to Claude Code for MP4 render |
| **Reel (30-sec, script-driven, no face)** | **B** | **Remotion** | v7.3 default. Deterministic React-based video. Hard 5-composition scene library. |
| **Reel (30-sec, talking head + overlays)** | **B** | **Remotion** | Use OutroCard iOS-icon face on outro only. No talking-head anywhere else. |
| Metric/stat Reel (short, bold numbers) | A or B | either | Path A (Claude Design animated HTML) is simpler; Path B (DataReveal composition) is on-brand and data-primitive-rich |
| Templated / fast exploration | A | Claude Design | When speed > bespoke motion |

## Rule of thumb

- **Static or simple animation (up to ~20 sec HTML-driven)** → Path A / Claude Design
- **30-sec script-driven Reel with voiceover** → Path B / Remotion
- When in doubt, start with Path A. Move to Path B only when the format demands VO sync + scene-graph animation.

## Path A — Claude Design handoff (unchanged since v6)

1. `generate_brief.py <source> --target <target>` produces a structured brief
2. User pastes brief into claude.ai/design, iterates, clicks Hand off
3. Command pasted into Claude Code → `render_html_carousel.py` (PNG slides) or `render_html_mp4.py` (animated MP4)
4. `import_assets.py` normalizes filenames + writes manifest

Works. Don't over-engineer it.

## Path B — Remotion-first Reels (v7.3)

Architecture reference: `references/v7-pipeline-architecture.md`. Primitive catalog: `references/ui-mockup-vocabulary.md`. Creative gate: `references/motion-design-playbook.md`.

**What Path B is:**
- 5 locked compositions: `KineticHook`, `ProblemBeat`, `InsightBeat`, `DataReveal`, `OutroCard`
- 10 UI-mockup primitives: browser frames, landing-page mockups, form reducers, lift charts, gaze trails, callout arrows
- ChatterBox voiceover, free BGM, ffmpeg polish (eq + vignette + grain + sidechain ducking)
- Automated QA gate (visual density / pure-black / motion presence)
- Deterministic: same draft + same VO → pixel-identical reel every run

**What Path B is NOT:**
- Not Hyperframes — deprecated in v7 rebuild (2026-04-21)
- Not Veo / Kling / Meta AI — all AI video generators removed in v7
- Not a talking-head pipeline — face only appears in OutroCard as iOS-icon portrait
- Not a free-form video editor — scene types are limited to the 5 compositions; new scene types require a new composition + registration in `Root.tsx` + `generate_reel.py::SCENE_COMPOSITION`

## Two-path hand-off

For a launch asset that needs both a Reel AND a carousel:

1. Run Path B to ship the 30-sec Reel (primary social asset)
2. Run Path A to produce a static carousel recap (LinkedIn/IG feed slot)
3. Link both in the source draft's frontmatter under `visual_assets_dir:`

## Engine non-goals

**Path A (Claude Design) does NOT:**
- Natively export MP4 in-browser (requires Claude Code render hand-off)
- Handle script-with-VO synchronization (that's Path B's job)
- Do 30-sec multi-scene reels (use Path B)

**Path B (Remotion) does NOT:**
- Handle static single-frame graphics (use Path A)
- Use any AI image generation (policy: NO AI images anywhere in reel body)
- Use real-time transcription (VO word timestamps come from MFA / WhisperX / whisper.cpp — see pipeline doc)
- Render photographic imagery in the reel body (only face-01.jpg on OutroCard)

## Deprecated (do NOT use)

- **Hyperframes** — active v5–v6. Deprecated in v7 rebuild 2026-04-21. All reel generation goes through Remotion. If you see hyperframes mentioned in old learnings, it's historical.
- **Veo / Kling / Meta AI / Midjourney / DALL-E** — evaluated in v7 audit, rejected. No AI image generators in Path B.
- **SadTalker / MuseTalk / Wav2Lip** — evaluated in v6, deleted (3.7 GB) in v7 rebuild. No lip-sync.
