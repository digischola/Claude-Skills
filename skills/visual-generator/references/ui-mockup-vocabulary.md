# UI Mockup Vocabulary — v7.2 Primitive Catalog

Canonical spec for the 10 primitives in `brand/remotion-studio/src/components/UIMockups.tsx`. Every Remotion composition composes these — never roll a one-off mockup. If a scene needs something new, add a primitive here first.

Design lineage: **Cody Plofker teardown aesthetic** — realistic browser chrome, before/after, eye-gaze, callout arrows, data highlights. NO geometric abstractions. NO generic icons. Every scene must feel like the viewer is watching a real LP being diagnosed.

---

## Table of Contents

1. [Import](#import) — how to pull these into a composition
2. [BrowserFrame](#1-browserframe) — macOS window chrome
3. [LandingPageMockup](#2-landingpagemockup) — 5 LP variants (wellness-bad, wellness-good, generic, saas, minimal)
4. [Counter](#3-counter) — count-up number with linear/expo pacing
5. [Cursor](#4-cursor) — macOS-style SVG arrow cursor
6. [GazeTrail](#5-gazetrail) — dotted eye-tracking path
7. [FoldLine](#6-foldline) — above-the-fold dashed marker
8. [CalloutArrow](#7-calloutarrow) — curved bezier annotation
9. [BrowserCycler](#8-browsercycler) — rapid LP variant rotation (hook scene)
10. [FormReducer](#9-formreducer) — animated form field collapse (9 → 3)
11. [LiftChart](#10-liftchart) — before/after spring-animated bars
12. [Composition patterns](#composition-patterns) — how primitives compose into 5 scene types
13. [Adding a new primitive](#adding-a-new-primitive) — conventions + do-not rules

---

## Import

```tsx
import {
  BrowserFrame,
  LandingPageMockup,
  Counter,
  Cursor,
  GazeTrail,
  FoldLine,
  CalloutArrow,
  BrowserCycler,
  FormReducer,
  LiftChart,
  type GazePoint,
  type LPVariant,
} from "../components/UIMockups";
```

---

## 1. BrowserFrame

macOS window chrome: traffic lights (red/yellow/green), URL pill, rounded 16px radius, 24px 64px shadow. Children render inside a white content area.

```tsx
<BrowserFrame url="thrive-retreats.com" width={840} height={720}>
  <LandingPageMockup variant="wellness-good" scrollY={0} />
</BrowserFrame>
```

| Prop | Default | Notes |
|---|---|---|
| `url` | `"example.com"` | Shown in URL pill. Use realistic-sounding domains (`retreat-1.com`, `thrive-retreats.com`). |
| `width` | `840` | 1080 wide canvas leaves 120px margin each side at 840w. |
| `height` | `520` | Bump to 720 when showing more than hero. |
| `children` | — | The LP content. |
| `style` | — | Override position if needed. |

**Use when:** Any time a scene shows a landing page. Always pair with `LandingPageMockup` or custom content.

---

## 2. LandingPageMockup

Fake LP content: nav strip → hero block with variant-keyed headline/subtitle/CTA → below-fold sections (story / team / testimonials / contact). `scrollY` lets the parent animate vertical scroll.

```tsx
<LandingPageMockup variant="wellness-bad" scrollY={scrollAnimation} />
```

| Variant | Hero feel | Use for |
|---|---|---|
| `"wellness-bad"` | Vague "Our Philosophy" purple hero | Problem beats — demonstrating a confused LP |
| `"wellness-good"` | "7-Day Bali Retreat — $1,499" rose hero | Insight beats — demonstrating a clear LP |
| `"generic"` | "Welcome / We help you grow" yellow hero | Cycler filler, "most LPs look like this" |
| `"saas"` | "Ship faster / The platform for modern teams" blue hero | Pivoting into non-wellness proof |
| `"minimal"` | "Make things / That matter" stone hero | Cycler variety |

**Use when:** Any time you need page content inside a `BrowserFrame`. Don't build custom HTML — extend the variant list here instead.

---

## 3. Counter

Count-up from 0 → target. Orbitron Black by default. Two pacings: `"expo"` (fast-then-slow, default) or `"linear"` (uniform tick). Optional prefix / suffix.

```tsx
<Counter
  target={40}
  durationMs={2500}
  pace="linear"
  fontSize={140}
  color={palette.success}
  suffix=""
  style={{filter: `drop-shadow(0 0 24px ${palette.glowSuccess})`}}
/>
```

| Prop | Default | Notes |
|---|---|---|
| `target` | required | Final integer the counter lands on. |
| `startFrame` | `0` | Frame when 0→target animation begins. |
| `durationMs` | `1000` | Total animation time. |
| `prefix` | `""` | `"+"` for lift stats. |
| `suffix` | `""` | `"%"`, `"s"`, `"x"`. |
| `fontSize` | `96` | Suffix auto-scales to 65% of this. |
| `color` | `palette.text` | Use `success` for wins, `warning` for losses. |
| `pace` | `"expo"` | Use `"linear"` when the count must match VO timing (hook "I audited 40"). |

**Use when:** Headline numbers need to animate in. Never hand-roll `interpolate(frame, [0, N], …)` for a number.

---

## 4. Cursor

macOS-style SVG arrow cursor. Parent controls `x, y` via interpolated props. Has a drop shadow.

```tsx
const x = interpolate(frame, [30, 60], [400, 520]);
const y = interpolate(frame, [30, 60], [300, 380]);
<Cursor x={x} y={y} />
```

| Prop | Default |
|---|---|
| `x`, `y` | required (absolute px) |
| `size` | `36` |
| `color` | `"#FFFFFF"` |

**Use when:** Simulating a click flow or pointing at a specific CTA. For attention patterns without a click, use `GazeTrail` instead.

---

## 5. GazeTrail

Dotted path with a connecting dashed polyline — simulates an eye-tracking trail. Points appear in sequence based on `t` (0..1 fraction of the trail window).

```tsx
const GAZE: GazePoint[] = [
  {x: 320, y: 480, t: 0.0},
  {x: 500, y: 520, t: 0.25},
  {x: 600, y: 720, t: 0.5},
  {x: 300, y: 960, t: 0.85},
  {x: 80,  y: 1100, t: 1.0}, // off-screen bottom
];
<GazeTrail points={GAZE} startFrame={9} durationMs={2200} color={palette.warning} />
```

| Prop | Default |
|---|---|
| `points` | required `GazePoint[]` |
| `startFrame` | `0` |
| `durationMs` | `1500` |
| `color` | `palette.warning` |
| `dotSize` | `14` |

**Use when:** Showing attention — either dropping off (ProblemBeat) or staying above fold (InsightBeat). End the last point OFF-screen when the viewer bounced; keep them clustered above fold when the page worked.

---

## 6. FoldLine

Horizontal dashed line marking the "above-the-fold" boundary. Draws on left→right with expo ease. Label slides in after the line completes.

```tsx
<FoldLine
  y={BY + 420}
  width={840}
  xStart={BX}
  startFrame={msToFrames(600, fps)}
  color={palette.success}
  label="THE FOLD"
/>
```

| Prop | Default |
|---|---|
| `y` | required (absolute px) |
| `width` | `840` |
| `xStart` | `0` |
| `startFrame` | `0` |
| `color` | `palette.success` |
| `label` | `"THE FOLD"` |

**Use when:** Making the fold visible so the audience understands the scarcity problem (limited real estate) or confirms a good LP packed hero + CTA above the line.

---

## 7. CalloutArrow

Curved annotation arrow from `(fromX, fromY)` to `(toX, toY)` with optional text label near the origin. Path is a quadratic bezier with a perpendicular-offset control point. Draws on progressively; arrowhead appears when >85% drawn.

```tsx
<CalloutArrow
  fromX={860}
  fromY={420}
  toX={BX + 150}
  toY={BY + 880}
  label="attention: gone"
  startFrame={msToFrames(1800, fps)}
  color={palette.warning}
/>
```

| Prop | Default |
|---|---|
| `fromX`, `fromY` | required |
| `toX`, `toY` | required |
| `label` | optional |
| `startFrame` | `0` |
| `color` | `palette.warning` |

**Notes:**
- Label is positioned at `(fromX - 80, fromY - 48)` — account for text width ~200px when placing origin so it doesn't clip the edge.
- Don't place `fromY` inside another UI element (stopwatch block, counter). Offset below/above by 20-30px.
- Arrow color = semantic: `warning` for problems, `success` for wins, `accent` for neutral callouts.

---

## 8. BrowserCycler

Hero visual for the hook scene. Cycles through `totalCount` LP variants over the given frame window. Variants rotate through the 5 `LPVariant` values; each LP gets a seeded scroll jitter so it feels live.

```tsx
<BrowserCycler
  totalCount={40}
  startFrame={0}
  endFrame={durationInFrames}
/>
```

| Prop | Default |
|---|---|
| `totalCount` | required (e.g. 40 for "40 LPs audited") |
| `startFrame` | `0` |
| `endFrame` | required (usually `durationInFrames`) |

**Use when:** Establishing volume — "I audited 40 LPs", "scanned 200 ads", etc. Pair with a `Counter` ticking 0→totalCount on `pace="linear"` so the number matches the browser flicker cadence.

---

## 9. FormReducer

Before/after form shrink animation. Starts with `fromCount` fields (Name, Email, Phone, DOB, Address, Gender, Occupation, Referral, Comments — in order), animates fields beyond `toCount` sliding right + fading + collapsing height to 0 over `reduceDurationMs`.

```tsx
<FormReducer
  fromCount={9}
  toCount={3}
  startFrame={msToFrames(400, fps)}
  reduceDurationMs={1200}
  width={440}
/>
```

| Prop | Default |
|---|---|
| `fromCount` | `9` |
| `toCount` | `3` |
| `startFrame` | `0` |
| `reduceDurationMs` | `1200` |
| `width` | `560` |

**Use when:** DataReveal scenes about form simplification, friction removal, field count impact on conversion. Pair with a `Counter` showing the resulting lift.

---

## 10. LiftChart

Two-bar chart — gray "BEFORE" bar (short), green "AFTER" bar (tall with glow). Both animate with spring physics, staggered 300ms. Bar heights scale to `beforeValue / afterValue` ratio.

```tsx
<LiftChart
  beforeValue={1.8}
  afterValue={4.0}
  beforeLabel="BEFORE"
  afterLabel="AFTER"
  startFrame={msToFrames(1700, fps)}
  width={400}
  height={280}
/>
```

| Prop | Default |
|---|---|
| `beforeValue` | `1.8` |
| `afterValue` | `4.0` |
| `beforeLabel` | `"BEFORE"` |
| `afterLabel` | `"AFTER"` |
| `startFrame` | `0` |
| `width` | `400` |
| `height` | `300` |

**Use when:** DataReveal or InsightBeat scenes that need a visual of growth. Values don't have to be percentages — CVR (1.8%→4.0%), revenue ($X→$Y), time-on-page, anything with a before/after.

---

## Composition patterns

### Hook — volume + velocity
`BrowserCycler` + `Counter (linear)` + `KaraokeCaption (School A, 1 word/page)` + `DigischolaLogo` + mesh bg + grain.

### ProblemBeat — attention drop
`BrowserFrame` + `LandingPageMockup (wellness-bad)` + `GazeTrail (drops off bottom)` + `Stopwatch` (inline component) + `CalloutArrow (warning)` + mesh bg.

### InsightBeat — fold discipline
`BrowserFrame` + `LandingPageMockup (wellness-good)` + `FoldLine` + `GazeTrail (stays above)` + `KaraokeCaption (School B)`.

### DataReveal — friction removal
`FormReducer (9→3)` + `Counter (+120%)` + `LiftChart` + `CalloutArrow (accent)` on positive mesh bg.

### OutroCard — face + handle + CTA
Face in iOS-icon rounded square + @handle + centered CTA + URL + DigischolaLogo. No mockup primitives here — it's the brand moment.

---

## Adding a new primitive

1. Build in `UIMockups.tsx` alongside the existing 10. Use `useCurrentFrame` + `interpolate` / `spring` from remotion.
2. Follow the prop conventions: `startFrame`, `durationMs` (not frames — use `msToFrames` from theme), `color` defaulting to a palette token, optional `style` passthrough.
3. Document here — add a section matching the format above.
4. Add a learnings entry in `SKILL.md` noting what it's for and which scene introduced it.

**Do NOT:**
- Inline colors / fonts / cubic-beziers — import from `theme/brand.ts`.
- Use `Math.random()` — use `random("seed-string")` from remotion for determinism.
- Copy an entire LP mockup out to a one-off scene — extend `LPVariant` instead.
