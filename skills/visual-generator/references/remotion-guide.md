# Remotion Studio Guide — v7 Reel Pipeline

What it is, where it lives, how to extend it. Read this before authoring new compositions or debugging a render.

---

## What Remotion is (non-technical)

Remotion is a React-based video engine. You write scenes as React components; Remotion renders them frame-by-frame to MP4 through headless Chromium. Every animation is deterministic — same code → identical pixels. No AI, no generation, no randomness unless we seed it.

**Why we chose it**: free, programmatic (data-driven), deterministic, zero marginal cost per reel.

**Licensing**: Remotion is free for individuals + companies up to 3 employees. Digischola is well under that.

---

## Where it lives

```
Desktop/Digischola/brand/_engine/remotion-studio/
├── package.json                    ← deps (Remotion, Paper shaders, etc.)
├── tsconfig.json
├── remotion.config.ts              ← render config (WebGL, codec, etc.)
├── public/
│   └── face-01.jpg                 ← outro icon portrait
├── src/
│   ├── index.ts                    ← entry point
│   ├── Root.tsx                    ← composition registry
│   ├── theme/
│   │   └── brand.ts                ← palette, fonts, subtitle tokens, easing, timings
│   ├── components/                 ← reusable primitives
│   │   ├── BrandBackgrounds.tsx    ← MeshGradient, AnimatedNoise, SubtitleSafeZone, GeometricGrid
│   │   ├── DigischolaLogo.tsx
│   │   ├── KaraokeCaption.tsx      ← word-sync subtitle system (School A + B)
│   │   ├── DataPrimitives.tsx      ← CountUpNumber, UnderlineDrawOn, Sparkline, KenBurnsImage
│   │   └── UIMockups.tsx           ← BrowserFrame, LandingPageMockup, Counter, Cursor, GazeTrail,
│   │                                  FoldLine, CalloutArrow, BrowserCycler, FormReducer, LiftChart
│   └── compositions/               ← one file per scene type
│       ├── KineticHook.tsx
│       ├── ProblemBeat.tsx
│       ├── InsightBeat.tsx
│       ├── DataReveal.tsx
│       └── OutroCard.tsx
└── node_modules/
```

See `references/ui-mockup-vocabulary.md` for the primitive catalog and `references/v7-pipeline-architecture.md` for the full Path B data flow.

---

## How to render a single scene

From `remotion-studio/`:

```bash
npx remotion render <CompositionId> <output-path> --props='{"words":[...]}'
```

- `CompositionId` matches the `id` prop in `Root.tsx` (e.g. `KineticHook`, `DataReveal`)
- `<output-path>` is any `.mp4` path
- `--props=` accepts inline JSON or a file path (`--props=path/to/props.json`)

**Live studio** (for iteration, not rendering):

```bash
npx remotion studio
```

Opens a browser UI at `localhost:3000` where you can scrub through frames, tweak props, preview animations.

---

## How to add a new composition

1. Create `src/compositions/<Name>.tsx` — default-export a React component that takes props.
2. Import primitives from `components/` — don't roll your own mesh or browser frame.
3. Use brand tokens from `theme/brand.ts` — NEVER inline colors, fonts, or cubic-beziers.
4. Register it in `src/Root.tsx`:

```tsx
<Composition
  id="MyScene"
  component={MyScene as unknown as React.ComponentType<Record<string, unknown>>}
  durationInFrames={Math.round(sceneDuration.my_scene_type * canvas.fps)}
  fps={canvas.fps}
  width={canvas.width}
  height={canvas.height}
  defaultProps={{...} as unknown as Record<string, unknown>}
/>
```

5. If it's a new scene_type, add it to `sceneDuration` in `theme/brand.ts` AND the `SCENE_DURATION` + `SCENE_COMPOSITION` maps in `scripts/generate_reel.py`.

---

## Render config (`remotion.config.ts`)

- `setVideoImageFormat("jpeg")` — faster than PNG, fine for MP4
- `setConcurrency(4)` — 4 parallel frame renders
- `setPixelFormat("yuv420p")` — social-safe H.264
- `setCodec("h264")` — IG / LinkedIn reel spec
- `setCrf(18)` — visually lossless
- `setChromiumOpenGlRenderer("angle")` — **required** for Paper Design shaders (WebGL). Without this, Paper shader compositions crash with "WebGL not supported."

---

## Common gotchas

1. **TypeScript cast for Composition `component` prop**: Remotion's types require `as unknown as React.ComponentType<Record<string, unknown>>` when your component has typed props. This is a known friction — the cast is safe.

2. **WebGL crash**: if a render fails with `Paper Shaders: WebGL is not supported`, check that `remotion.config.ts` has `setChromiumOpenGlRenderer("angle")`. This is already configured.

3. **Determinism**: never use `Math.random()` — use `random(seedString)` from `remotion`, or deterministic seeded functions (see `BrowserCycler` for reference).

4. **Scene duration vs VO**: each scene's `durationInFrames` is registered in `Root.tsx` and must include ~300-500ms buffer past the VO's last word end, or the subtitle gets cut off mid-word. See `sceneDuration` in `theme/brand.ts` — already tuned.

5. **Subtitle overflow**: if a word is too wide for the 900px caption max-width, it wraps weirdly. Captions are sized 56px (School B) / 72px (School A) — fit ~12-16 chars per line at this size. If a word breaks poorly, shorten the line in the draft.

6. **Static assets**: anything in `public/` is accessed via `staticFile("filename.ext")`. Don't hardcode absolute paths.

---

## Render performance

On M-series Macs, typical scene render:
- 2.5s hook (75 frames @ 1080x1920): ~15-20 seconds
- 5s insight (150 frames): ~30-40 seconds
- Full 5-scene reel end-to-end (render + stitch + QA): ~3-4 minutes

If slow, check `setConcurrency` hasn't been lowered. `npx remotion render` auto-uses all cores.

---

## Debugging a broken render

1. **Render fails with no output**: run with `--log=verbose` to see the Chromium console.
2. **Composition looks wrong in studio but renders differently**: fonts may not be loaded at render start. Paper Design shaders + Google Fonts usually work, but for heavy font use, add `delayRender()` / `continueRender()` handshakes in the composition.
3. **TypeScript errors**: run `./node_modules/.bin/tsc --noEmit` to catch issues before render.

---

## Change log

- **2026-04-21** — v7.3 Remotion-first reel pipeline shipped. Five compositions, 10 UIMockup primitives, Paper Design shaders, QA gate wired. This doc written to lock the knowledge.
