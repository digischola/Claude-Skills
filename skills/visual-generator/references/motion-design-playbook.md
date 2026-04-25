# Motion Design Playbook — Digischola Reels (v2)

**Locked 2026-04-21. Replaces v1 (vibes-based).** Every value here is research-grounded.
Built from three parallel briefs: word-sync subtitles (School A vs B vs C framework),
dynamic geometric backgrounds (one dominant mechanic, Paper Design shader era), and
motion design fundamentals (10 easings + roles + timing hierarchy).

**Design principle that dominates everything below: make template-looking impossible by
construction.** Every element declares a role — hero / secondary / label / bg-plate /
fg-flourish — and its role determines its curve, duration, scale, color treatment,
and motion vocabulary. Authors pick roles. The system produces the motion. No one
hand-picks a cubic-bezier in a composition file.

---

## 0. Index

1. Philosophy (the 3 hard rules)
2. The Three-School Subtitle Framework
3. Motion System — Roles, Curves, Timings
4. Typography System
5. Color System
6. Subtitle System — Word-Sync Pipeline
7. Background System — One Mechanic, Not Five
8. Composition System — Vertical Grid + Safe Zones
9. Transition System — 15 Options Mapped to Narrative
10. Audio-Visual Sync Rules
11. The Never-Do List
12. Per-Scene Recipes
13. Benchmark Exemplars
14. Tool Stack

---

## 1. Philosophy — the 3 hard rules

1. **Restraint in motion, maximalism in craft.** Linear / Vercel / Framer / Pentagram / Wild all pick ONE dominant visual mechanic per scene (mesh gradient OR particle drift OR kinetic type OR shape array — never stacked). Amateur motion stacks 5 mechanics. Premium does 1 well. If a scene has a mesh background AND particles AND shape arrays AND kinetic type, cut three.
2. **One motion, not three.** Entry animations should apply ONE physical change (scale OR translate-Y OR opacity — pick) with accompanying micro-support (e.g. scale + opacity is fine, but don't also rotate + bounce + glow). Multi-motion is School A; our default is School B's restraint.
3. **Exits are 60% of entry duration.** A 900ms entry exits in 540ms. Always. Computed not authored. This is the single rule most template motion gets wrong.

---

## 2. The Three-School Subtitle Framework

Every caption system in 2026 short-form falls into one of three schools. Pick per scene, not per reel.

| School | Vibe | Words/page | Color | Font | Motion | Use for |
|---|---|---|---|---|---|---|
| **A — Hormozi Pop** | max energy, shouty | 1 | white → yellow/accent swap | Impact / Montserrat Bold | scale 1.0→1.15→1.0 bounce + color pop | Hook 0-2.5s ONLY |
| **B — Dynamic Minimalism** | designed, editorial | 2 (default), 3 (connectors), 1 (punchline) | white @ 85% → accent blue (instant swap) | Space Grotesk 700 + Orbitron for emphasis | scale 0.85→1.0 spring + opacity + 8px Y-slide, synchronous | **Digischola default for 90% of reel** |
| **C — Podcast Kinetic** | broadcast, slow | 3-5 | white on semi-opaque card | Inter / Manrope | whole-line fade cross-transition | Not used for Digischola (wrong format) |

**Decision architecture**: default School B. Flag the first hook page (0-2.5s) as School A for thumb-stop. Never School C.

---

## 3. Motion System — Roles, Curves, Timings

Every animated element declares a role. Role determines curve + duration + motion amount.

### Roles

| Role | Examples | Entry curve | Entry duration | Y-travel | Scale delta |
|---|---|---|---|---|---|
| **hero** | reel title, data number, outro CTA | Expo Out or Hero Spring | 700-900ms | 40-80px | 0.85 → 1.0 |
| **secondary** | subtitle line, context text | Quart Out | 500-650ms | 20-30px | 0.95 → 1.0 |
| **label** | eyebrow, URL, handle, timecode | Studio Curve | 300-450ms | 8-12px | 1.0 (no scale) |
| **bg-plate** | mesh gradient, noise, shape array | Quint In Out | 1000-1400ms | 0 (ambient drift only) | 1.0 |
| **fg-flourish** | accent bar, check-mark, sparkline | Back Out subtle or UI Spring | 250-400ms | — | 0.0 → 1.0 |
| **data-ticker** | counter, chart bar | Circ Out | 600-1200ms | — | — |

### Curve library (the 10 + 4 springs)

```ts
// cubic-bezier() strings — locked values, never inline
export const curves = {
  expoOut:         "cubic-bezier(0.16, 1, 0.3, 1)",       // hero entrance
  expoInOut:       "cubic-bezier(0.87, 0, 0.13, 1)",      // full-screen transitions
  quartOut:        "cubic-bezier(0.25, 1, 0.5, 1)",       // secondary text
  circOut:         "cubic-bezier(0, 0.55, 0.45, 1)",      // data counters, charts
  backOutSubtle:   "cubic-bezier(0.34, 1.56, 0.64, 1)",   // fg-flourishes, icons
  backOutStrong:   "cubic-bezier(0.68, -0.6, 0.32, 1.6)", // logo stamp only (1/reel)
  quintInOut:      "cubic-bezier(0.83, 0, 0.17, 1)",      // bg-plate camera moves
  sineInOut:       "cubic-bezier(0.37, 0, 0.63, 1)",      // ambient loops
  studio:          "cubic-bezier(0.65, 0, 0.35, 1)",      // system default UI flourish
  anticipation:    "cubic-bezier(0.5, -0.4, 0.5, 1)",     // CTA reveal, 1/reel
  // Exit helpers — 60% of entry duration, use this curve:
  expoIn:          "cubic-bezier(0.7, 0, 0.84, 0)",       // all exits
};

// Spring configs — use Remotion's spring() or framer-motion
export const springs = {
  hero:     { mass: 1,   damping: 20, stiffness: 180 },   // hero text, card arrivals
  ui:       { mass: 0.8, damping: 26, stiffness: 280 },   // buttons, icons, critically damped
  playful:  { mass: 1.2, damping: 14, stiffness: 200 },   // 1 element per reel max
  heavy:    { mass: 2.5, damping: 30, stiffness: 150 },   // full-screen cards
};
```

### Timing hierarchy per scene

- Hero enters at frame 0 of scene.
- Secondary enters at hero + 120ms.
- Label enters at hero + 240ms.
- Hold period after last element settles: **350-600ms of stillness, non-negotiable**. Where premium motion breathes.
- Exit stagger reversed: label first, secondary next, hero last. 80ms between each exit.

### Scene duration sweet spot

**1.2s to 2.8s per scene.** Under 1s viewer can't parse. Over 3s feels like slideshow. For 30s reel = 11-25 scenes, premium target is 14-18. Vary scene lengths (1.2, 1.8, 2.4, 1.6) — consistent 1s lengths kill rhythm.

---

## 4. Typography System

### Font pairing (one rule)

- **Body** (subtitle words, labels, captions): **Space Grotesk 700** — neutral geometric, reads "designed"
- **Emphasis** (hook words, data numbers, CTA): **Orbitron 700** — geometric display, impact moments
- **Support** (handle, URL, timestamps): **Manrope 500** — humanist neutral
- **Never mix all three in one scene.** Max 2 typefaces per scene, always body + one other.

### Sizes on 1080×1920 canvas

| Element | Size (px) | Weight | Tracking | Line-height |
|---|---|---|---|---|
| Hero (Orbitron) | 128 | 700 | +0.02em | 1.05 |
| Hero-heavy (data number, outro CTA) | 180-220 | 700-900 | +0.02em | 1 |
| Subtitle body (Space Grotesk) | 96 | 700 | -0.02em | 1.1 |
| Subtitle punchline (Orbitron) | 128 | 700 | +0.02em | 1.05 |
| Secondary/sub-label | 52-64 | 500 | 0 | 1.35 |
| Eyebrow/label (Space Grotesk uppercase) | 32 | 600 | +4% (tracking 2px) | 1.2 |
| Handle/URL (Manrope) | 36-44 | 500 | 0 | 1.3 |

**Max chars per line** (headlines): 18-22. **Max characters body**: 28-32. **Max words on screen at once**: 9-11 across the whole frame.

### Character stagger vs word reveal

- **Character stagger** (SplitText-style) = dated unless paired with distinctive curve + Y-offset. Don't use as default.
- **Word reveal via clip-path mask** (`inset(100% 0 0 0)` → `inset(0 0 0 0)` + 40px Y + Expo Out 750ms, parent-mask 1px blur fading off at 80%): **the single most premium text move in 2026.** This is our subtitle entry.

### Never

- Inter for display (too utility — use Space Grotesk instead)
- Poppins anywhere (reads 2019)
- Default system fonts for hero
- Bounce-per-letter typewriter
- 3D rotation text entries
- Rubber-band text bounces
- Mid-word line breaks (hard-break the copy before render if needed)

---

## 5. Color System

### Palette (LOCKED from brand-identity.md + playbook additions)

```ts
export const palette = {
  // Backgrounds — NEVER pure #000 or #FFF
  bgDark:      "#0A0E1A",  // primary dark canvas (tinted, not pure black)
  bgDarker:    "#08090A",  // deeper variants (Linear's base)
  surface1:    "#0F172A",
  surface2:    "#1E293B",

  // Brand accents
  accent:      "#3B9EFF",  // primary accent blue — active subtitle word, URLs, neutral emphasis
  success:     "#4ADE80",  // insight/punchline word, positive-delta numbers (max 1x per sentence)
  warning:     "#EF4444",  // problem-beat callouts, broken-state highlights (rare)

  // Text
  text:        "#F8FAFC",  // primary text (at 85% opacity for inactive subtitle words)
  textDim:     "rgba(248, 250, 252, 0.85)",  // inactive subtitle word
  muted:       "#9BA8B9",  // labels, secondary text, dim handle

  // Stroke / shadow — brand-dark NOT pure black (the designed tell)
  strokeDark:  "#0A0E1A",  // 4px text stroke — REPLACES pure black
  shadowDark:  "rgba(10, 14, 26, 0.6)",  // 0 6px 24px for subtitle depth
  glowAccent:  "rgba(59, 158, 255, 0.4)",  // 0 0 16px on active word
};
```

### Color treatment across motion beats

- **Entry**: ~70% saturation, ~90% target luminance (warming up)
- **Hold**: 100% target saturation + luminance (the pop moment)
- **Exit**: 60% saturation OR fades through neutral before leaving
- **On active subtitle word**: INSTANT color swap (no cross-fade — muddies on fast speech)

### Dark-mode specifics

- **Glow bleeds**: `filter: drop-shadow(0 0 16px ${glowAccent})` on active subtitle word. NOT box-shadow (too crisp).
- **Chromatic aberration**: 1-2px R/B offset on hero text for 200ms on entry, snap back. Longer = looks broken.
- **Colored shadows**: shadow color = 40% of accent hue, desaturated 20%. NEVER pure black on dark bg.
- **Avoid pure saturated primaries** (#FF0000 on #000 vibrates = chromostereopsis). Desaturate to 85% or shift hue 5-10°.
- **Subtitle safe zone background**: bottom 25-35% of frame dimmed 40-50% via soft 200-300px gradient mask — NOT blur (blur reads "out of focus") and NOT a hard card (that's School C).

### Per-scene color discipline

- **ONE accent per scene** on the most important element only
- **MAX two accents on screen** and only if they represent a binary (before/after)
- **Insight word rule**: reserve `#4ADE80` for exactly ONE word per sentence — the word that carries the meaning ("converts", "wastes", "fixes"). Every other active word stays `#3B9EFF`. Manually tagged in caption JSON. Worth it.

---

## 6. Subtitle System — Word-Sync Pipeline

This is the PRIMARY reel mechanic. Text tracks VO word-by-word. Not a "hook card".

### Pipeline

1. ChatterBox renders `voiceover.mp3` from script (existing, unchanged).
2. **NEW step** `scripts/extract_word_timestamps.py`:
   - Primary: **MFA (Montreal Forced Aligner)** — aligns known script text to known audio, sub-30ms precision.
   - Fallback: **WhisperX** (m-bain/whisperX) — wav2vec2 forced-alignment, 4-8s on M-series.
   - Draft tier: **@remotion/install-whisper-cpp** — whisper.cpp via npm, softer boundaries (±80-150ms) but zero friction.
3. Output: `voiceover.words.json` alongside MP3:
   ```json
   {
     "words": [
       {"word": "I", "start": 0.12, "end": 0.21},
       {"word": "audited", "start": 0.24, "end": 0.68, "emphasis": "insight"},
       {"word": "40", "start": 0.71, "end": 0.88}
     ]
   }
   ```
   `emphasis: "insight" | "hook"` is MANUALLY TAGGED per word during script review — this is what unlocks the #4ADE80 surgical color. One `insight` tag per sentence max.
4. Remotion compositions receive `words[]` as props.
5. `@remotion/captions` `createTikTokStyleCaptions({captions, combineTokensWithinMilliseconds})` groups words into pages.

### Page-grouping rules (words-per-page tied to meaning)

| Scene role | `combineTokensWithinMs` | Typical words/page |
|---|---|---|
| Hook line (0-2.5s) | 400 | 1 |
| Problem beat | 1200 | 2-3 |
| Insight | 1200 | 2 |
| Data reveal | 800 | 1-2 (include the number) |
| CTA | 600 | 1-2 |
| Connector/transition prose | 2000 | 3 |

### Visual spec (School B default)

| Attribute | Value |
|---|---|
| Position | y = 1190px (62% from top, NOT "bottom third") |
| Max width | 900px (~83% of 1080) |
| Font (body) | Space Grotesk 700, 96px, tracking -0.02em, line-height 1.1 |
| Font (emphasis page) | Orbitron 700, 128px, tracking +0.02em, line-height 1.05 |
| Inactive color | #F8FAFC @ 85% opacity |
| Active color | #3B9EFF (default) / #4ADE80 (emphasis word) |
| Stroke | 4px #0A0E1A (NOT #000) |
| Shadow | 0 6px 24px rgba(10, 14, 26, 0.6) |
| Glow on active | filter: drop-shadow(0 0 16px rgba(59, 158, 255, 0.4)) |
| Background card | NONE (that's School C) |
| Emojis | NEVER (reads 2023) |

### Animation mechanics (one synchronous spring)

```ts
// Per word, when it first enters the page:
// Spring from frame (wordStart - 180ms)
const progress = spring({
  frame: frame - wordStartFrame,
  fps,
  config: springs.ui, // { mass: 0.8, damping: 26, stiffness: 280 }
});

// All three properties driven by the same progress value:
const opacity = interpolate(progress, [0, 1], [0, 1]);      // 80ms apparent
const scale   = interpolate(progress, [0, 1], [0.85, 1]);   // 180ms spring
const y       = interpolate(progress, [0, 1], [8, 0]);       // 140ms feel

// Active state: INSTANT color swap at word.start (no cross-fade)
const isActive = timeMs >= wordStartMs && timeMs < wordEndMs;
const color = isActive
  ? (word.emphasis === "insight" ? palette.success : palette.accent)
  : palette.textDim;

// Page persistence: all words in current page stay from page.start to page.end
// Active-word STYLING moves through — words don't disappear until page flip
```

### School A hook exception (first 0-2.5s only)

- Scale 1.08 instead of 1.0 on active (popped)
- Color: `#4ADE80` on active (not `#3B9EFF`)
- Full glow on active word
- 1 word per page
- Orbitron 700 at 128px (not Space Grotesk body)

### Page flip transition

- Outgoing page: fade + 12px Y-translate, 140ms
- Incoming page: fade + 12px Y-translate upward, 140ms
- **60ms gap between pages** (prevents overlap strobing)

---

## 7. Background System — One Mechanic, Not Five

Pick ONE per scene. Never stack. Every amateur reel's tell is 5 stacked mechanics.

### Allowed mechanics + exact parameters

| Mechanic | Library | When | Parameters |
|---|---|---|---|
| **Paper Design mesh shader** | `@paper-design/shaders-react` | Hook, insight, CTA (default) | 3-5 color stops on grid, drift 0.05-0.15 units/s, octave-noise amplitude 0.08-0.15, accent stops 15-25% opacity MAX |
| **Simplex noise texture overlay** | `simplex-noise` + 3D Z-axis drift | ALWAYS on top of any bg, 3-6% opacity | noise Z-speed 0.1-0.3 units/s, `mixBlendMode: screen` on dark |
| **Sparse particle system** | Canvas/SVG + seeded random | Insight, data-reveal for texture | 40-120 particles max, size 2-6px (50% with 8-16px blur), drift 10-30 px/s, opacity 0.15-0.4, `screen` blend |
| **Geometric grid (visible lines)** | SVG, 6-col or 8-col | Problem beat, data context | 1px stroke at rgba(255,255,255,0.04-0.08), drift ±20px over 8-12s with sineInOut, never rotate >1°/s |
| **SVG shape array** | `@remotion/shapes` + seeded positions | Insight scenes with abstract concept | 8-20 shapes, 20-80px size, grid positioning with ±30% jitter, rotation ±15° slow, stagger entrance 40-80ms, 1-2 shape types MAX |
| **Scanning sweep line** | CSS animated gradient | Data reveal transitions | diagonal 15-30°, speed 20-60 px/s, opacity 0.03-0.08 |
| **Concentric circles / ripples** | SVG | Problem → insight transitions | 3-6 rings from anchor off-center, expand 40-80 px/s, opacity 0.3→0 over 2-3s, 0.6-1.0s stagger |

### The subtitle safe zone overlay

Every scene has this layer ABOVE bg but BELOW subtitles:

```tsx
<div style={{
  position: "absolute",
  bottom: 0,
  left: 0, right: 0,
  height: "38%", // covers the subtitle zone
  background: "linear-gradient(to bottom, transparent 0%, rgba(10, 14, 26, 0.45) 60%, rgba(10, 14, 26, 0.55) 100%)",
  pointerEvents: "none",
}} />
```

This dims the bg under subtitles without blur. Non-negotiable on every scene.

### Determinism rule

All "randomness" must be seeded per-frame function. Remotion renders frame-by-frame with no state.

```ts
// Seeded random via index (deterministic)
const seeded = (i: number) => Math.abs(Math.sin(i * 12.9898) * 43758.5453) % 1;
// OR Remotion's built-in:
import { random } from "remotion";
const r = random(`particle-${i}`);
```

### Background motion clamp

Clamp to 30fps feel even on 60fps renders:
```ts
const bgFrame = Math.floor(frame / 2); // use this for bg math, keep foreground on `frame`
```

---

## 8. Composition System — Vertical Grid + Safe Zones

### 1080×1920 composition zones

```
┌─────────────────────────────┐  0
│                             │
│      UPPER THIRD            │  ← hero content (hook text, data number)
│      y = 380 to 740         │     focal at y=640 (rule of 3) or y=733 (golden)
│                             │
├─────────────────────────────┤  740
│                             │
│      MIDDLE (breathing)     │  ← low-opacity bg motion only
│      y = 740 to 1220        │     no readable text here during bg drift
│                             │
├─────────────────────────────┤  1220
│                             │
│      SUBTITLE SAFE ZONE     │  ← word-sync subtitles live here
│      y = 1220 to 1620       │     subtitle anchor at y=1190 top of line
│                             │     dimmed bg via gradient mask
├─────────────────────────────┤  1620
│                             │
│      BRAND BAR              │  ← logo top-left, handle bottom-right
│      y = 1620 to 1920       │     always present, never animates mid-scene
│                             │
└─────────────────────────────┘  1920
```

### Horizontal safe zones

- 80px gutters each side → **920px usable width** for any text element
- Text-wrap enforcement: if copy would break mid-word, use CSS `hyphens: none; word-break: keep-all; overflow-wrap: normal;` and manually hard-break the copy before render

### Rules

- Minimum **40% of frame should be near-empty** at any moment (just bg base tone). "Random shapes floating" fills 70-80% — the amateur tell.
- Focal element on golden-ratio line (y=733 or y=1187). Never center.
- Visual weight: one element is the heaviest per scene (size × contrast × saturation). Background NEVER outweighs subject. Squint test.

---

## 9. Transition System — 15 Options, 70/30 Rule

**70% of scene transitions should be hard cuts.** Over-transitioning is the #1 amateur tell. Only use the fancy transitions at narrative turns.

| # | Transition | When | Duration | Curve |
|---|---|---|---|---|
| 1 | **Hard cut** | Subject change, speaker change, downbeat | 0 | — |
| 2 | **Black dip** | Narrative chapter breaks | 180+60+180ms | Expo In Out |
| 3 | **White flash** | Insight/revelation moments | 80ms | cut through |
| 4 | **Cross-dissolve** | Editorial montage, slow contemplative | 300ms | Sine In Out |
| 5 | **Diagonal wipe** | Chapter break, editorial feel | 600ms | Expo In Out (15-25°) |
| 6 | **Iris / circle reveal** | Problem → insight transitions | 700ms | Expo Out |
| 7 | **Scale crush** | Default "safe" premium scene change | 500ms | Expo Out (out: 0.85+fade, in: 1.15→1.0) |
| 8 | **Scale explode** | Hook → main content | 500ms | Expo Out (out: 1.4+fade, in: under) |
| 9 | **Directional slide + 3-layer parallax** | Inside a narrative section | 800ms | Expo In Out (0.3x/0.7x/1.0x) |
| 10 | **Liquid morph** | Brand moment (1/reel max) | 900ms | Quart In Out |
| 11 | **Shape-transition circle expand** | Problem → solution | 650ms | Expo Out |
| 12 | **RGB split glitch** | CTA energy shift only | 3-6 frames | — |
| 13 | **Light leak sweep** | Data → CTA reveal | 500ms | Quint In Out |
| 14 | **Motion blur carry-over** | Cinematic chapter end | 80ms blur | cut during |
| 15 | **Match cut** | Rare, high payoff | 0 | precise alignment |

### Narrative mapping for a standard reel

| From → To | Transition |
|---|---|
| Hook → Problem | Black dip OR scale crush (tonal shift) |
| Problem → Insight | White flash OR iris reveal (revelation) |
| Insight → Data | Directional slide (continuity) |
| Data → CTA | Light leak sweep OR scale explode (energy up) |
| CTA → Outro logo stamp | Hard cut + Back Out Strong on logo |

---

## 10. Audio-Visual Sync Rules

### Sync ON:
- **VO sentence boundaries** — cut at the breath, not frame counts
- **VO word emphasis peaks** — scale active word 108-112% for 200ms on peak amplitude
- **Music downbeats** — every 4 beats for cuts, every beat for accents (120 BPM → cuts at 1s or 2s intervals)
- **Punctuation moments** — period = hold 350ms, comma = micro-pause 150ms, exclamation = pulse

### Sync OFF:
- **Ambient bg motion** — let it drift independently (organic feel)
- **Foreground particle systems** — tie to time, not audio
- **Logo/brand elements** — their own rhythm
- **Hold periods** — these are musical rests, not sync points

### Amplitude-driven motion

2-4% scale pulse on VO amplitude peaks, clamped so small amplitude = 0 scale change. NEVER let amplitude drive visibility or position. Only scale + glow intensity.

---

## 11. The Never-Do List (hard rules)

1. ❌ Default CSS `ease` / `ease-in-out` — use named curves from the library
2. ❌ Linear fades over 500ms (lifeless)
3. ❌ Pure `#FFFFFF` on pure `#000000` with no technique (add glow / tint / grain / stroke)
4. ❌ 5+ simultaneous animations (eye can't track)
5. ❌ Mid-word line breaks ("AU / DITED" disaster)
6. ❌ Font below 44px on 9:16
7. ❌ Pure saturated colors on dark (#FF0000 on #000 vibrates)
8. ❌ Text denser than the hold duration allows for reading (0.3s per word minimum)
9. ❌ Rotating text in 3D on entry (dated)
10. ❌ Bounce-per-letter typewriter (template tier)
11. ❌ Cross-dissolves >400ms between different scenes
12. ❌ All parallax layers moving same speed (pointless)
13. ❌ Drop shadows with 0 blur + pure black (Microsoft Word energy)
14. ❌ Emojis same size as body text, unanimated (pasted feel)
15. ❌ Logo stamp at end with no entry motion (default-tier)
16. ❌ Ken Burns on stills with no narrative reason
17. ❌ Text arriving AND exiting same frame as scene cut (no breathing room)
18. ❌ Consistent 1s scene lengths (rhythm needs variation — 1.2, 1.8, 2.4, 1.6)
19. ❌ Photographic imagery in reel body (geometric only)
20. ❌ Em dashes anywhere in rendered text (universal brand rule)
21. ❌ Pure `#000` as bg (use `#0A0E1A` or `#08090A` — tinted)
22. ❌ Pure `#000` as text stroke (use `#0A0E1A` — the designed tell)
23. ❌ Cross-fade color on active subtitle word (INSTANT swap only)
24. ❌ Background card under subtitles (that's School C)
25. ❌ Emojis in caption text (reads 2023)
26. ❌ One typeface for the whole reel (need body + emphasis distinction)
27. ❌ More than 2 accent colors on screen (unless binary like before/after)
28. ❌ Stacking 3+ bg mechanics (pick ONE)
29. ❌ Particles denser than 120 per frame
30. ❌ Blur >20px on animated bg elements (GPU-expensive + cheap-looking)

---

## 12. Per-Scene Recipes

Every composition wires these exact specs. Role + timing + color determined by scene type.

### Hook (0-2.5s / 75 frames @ 30fps)

- Background: Paper Design mesh shader (neutral tone) + simplex noise 4%
- Safe-zone overlay: ON
- Subtitle: School A exception — 1 word per page, Orbitron 700 at 128px, scale 1.08 active, #4ADE80 on emphasis, full glow
- Brand bar: DIGISCHOLA logo fades in at frame 3 top-left; handle at frame 6 bottom-right
- Transition in: hard cut from black (opening scene)
- Transition out: black dip (180+60+180ms) OR scale crush

### Problem beat (3-6s / 4.0s)

- Background: Geometric grid 6-col (1px lines at 0.05 opacity) + simplex noise 4% + warning-red mesh at 8% opacity off-center
- Safe-zone overlay: ON
- Subtitle: School B — 2-3 words per page, Space Grotesk 700 96px, inactive #F8FAFC @85%, active #3B9EFF, manually tagged insight word gets #4ADE80
- 1 fg-flourish: small red slash SVG (rough-notation style, 1/scene)
- Transition in: black dip from hook
- Transition out: white flash OR iris reveal to insight

### Insight beat (6-10s / 4.5s)

- Background: Paper Design mesh (positive tone — green-tinted) + sparse particles (60-80) + simplex noise 4%
- Safe-zone overlay: ON
- Subtitle: School B, 2 words per page default; if draft tags a punchline word, bump to Orbitron 128px for that page only
- 1 fg-flourish: SVG underline draw-on under the insight line (stroke-dashoffset, 600ms Expo Out)
- Transition in: white flash from problem
- Transition out: directional slide to data

### Data reveal (10-13s / 3.5s)

- Background: Paper Design mesh neutral + simplex noise 4%
- Hero: Orbitron 700 at 220px, big number, odometer-flip digits using Circ Out, 600-1200ms
- Secondary: label below in Space Grotesk 700 at 64px
- Subtitle: School B, 1-2 words with the number called out with #4ADE80
- fg-flourish: SVG sparkline draws on beneath number (stroke-dashoffset, 900ms)
- Transition in: directional slide + 3-layer parallax
- Transition out: light leak sweep to CTA

### CTA (13-17s / 4.0s)

- Background: Paper Design mesh (accent blue-heavy, 25% stops) + simplex noise 5%
- Hero: Orbitron 700 128px CTA phrase, scale 0.85→1.0 with Hero Spring
- Secondary: URL in Space Grotesk 700 accent blue 48px, fg-flourish
- fg-flourish: accent bar grows under hero (Back Out Subtle, 400ms), 120px wide
- Transition in: light leak sweep from data
- Transition out: hard cut to outro

### Outro (17-21s / 3.5-4.0s)

- Background: face-01.jpg top 55% with Ken Burns 1.0→1.08 (Decel curve, over full scene) + gradient fade to black at y=1056 (55% mark)
- Above face: animated geometric elements (3 faint accent-blue squares drifting, 0.15 opacity, 20 px/s)
- Hero: DIGISCHOLA logo SVG morph-intro top-left at frame 3 (Back Out Strong, 1/reel exception)
- CTA text: Orbitron 104px uppercase slides up from frame 15 (Hero Spring, y=1280)
- URL: Space Grotesk 48px accent blue at frame 30 (Quart Out)
- Handle: @DIGISCHOLA Manrope 500 muted at frame 45 (Studio Curve)
- Held state: Ken Burns continues + simplex noise 4% on top
- Transition in: hard cut from CTA

---

## 13. Benchmark Exemplars

Study these frame-by-frame. Download, open in DaVinci, scrub 33ms per frame (at 30fps). Catalog 5 moves per reel.

| Source | What to study |
|---|---|
| **Linear** (@linear on X, linear.app/method) | "Cycles," "Insights," "Customer Requests" launch reels — mesh bg + kinetic type house style |
| **Vercel** (@vercel, Ship events) | Next.js version launches — mesh + triangle-sphere motif + type |
| **Framer** (@framer reels) | Shape-array drift, r3f 3D embedded, motion blur |
| **Paper Design** (paper.design homepage) | Their shader demos ARE the 2026 mesh gradient reference |
| **MetaLab** (@metalab IG) | Product case studies — pristine kinetic type |
| **Wild** (wild.as, @wild.as IG) | Scandinavian minimalism — closest tone to Digischola aspiration |
| **Pentagram** (own brand reels) | Kinetic typography as composition |
| **Rauno Freiberg** (rauno.me) | Vercel DX work + motion principles writeups |
| **Emil Kowalski** (emilkowal.ski) | Blog posts on motion principles |
| **Hormozi reels** (@hormozi) | School A subtitle reference (yellow-swap energy) |
| **Justin Welsh reels** (@justin.welsh) | School B subtitle reference — Digischola default match |
| **Dickie Bush reels** (@dickiebush) | School B with writing-focus content, closest to our pillar |

---

## 14. Tool Stack

### Render engine
- **Remotion 4.0+** — programmatic React video, deterministic frame math
- `@remotion/captions` — `createTikTokStyleCaptions({captions, combineTokensWithinMilliseconds})`
- `@remotion/shapes` — SVG primitives
- `@remotion/paths` — SVG path interpolation
- `@remotion/transitions` — built-in scene transitions
- `@remotion/noise` — official deterministic noise
- `@remotion/install-whisper-cpp` — draft-tier word-timestamp extraction

### Motion + shaders
- `@paper-design/shaders-react` — the 2026 mesh gradient library (drop-in)
- `simplex-noise` — 2D/3D noise
- `framer-motion` — avoid inside Remotion (use Remotion's `spring()` instead)
- `d3-delaunay` / `d3-geo-voronoi` — tessellation, optional
- `@react-three/fiber` + `@react-three/drei` — 3D if needed (most reels don't)

### Word-timestamp extraction
- **Primary**: MFA (Montreal Forced Aligner) — sub-30ms when script is known
- **Fallback**: WhisperX (m-bain/whisperX) — wav2vec2 alignment, 4-8s on M-series
- **Draft**: whisper.cpp via `@remotion/install-whisper-cpp`

### Voice + audio
- **ChatterBox** (existing) — voice cloning
- **ffmpeg** — stitching, BGM mix via sidechaincompress ducking
- **Pixabay / Mixkit / Uppbeat** — free commercial-use BGM

### Deprecated (removed 2026-04-21)
- Veo, Kling, Meta AI, Nano Banana, SadTalker, MuseTalk, Wav2Lip
- F5-TTS fallback (ChatterBox primary)
- Hyperframes (Remotion replaces)

---

## Change Log

- **2026-04-21 v2** — Full rewrite based on 3-agent design research. Replaces v1's vibes-based spec with concrete values: 10-curve easing library, 4 spring configs, role-based motion hierarchy, three-school subtitle framework (Digischola defaults to School B Dynamic Minimalism), word-sync architecture with MFA pipeline, Paper Design shader for backgrounds, subtitle safe zone protocol, vertical composition zones, 15-transition system with 70/30 rule, 30-item never-do list, per-scene recipes.
- **2026-04-21 v1** — Initial (vibes-based), superseded.
