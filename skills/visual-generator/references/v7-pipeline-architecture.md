# v7.3 Reel Pipeline Architecture — Path B End-to-End

The full data flow from source draft → published MP4. Read this when onboarding a new scene type, diagnosing a broken reel, or training someone on the pipeline.

---

## One-sentence version

Draft markdown → parse scenes → clone VO → extract word timestamps → per-scene Remotion render → ffmpeg polish + flash + BGM ducking → QA gate → final reel.mp4.

---

## Stage map

```
┌──────────────────────────────────────────────────────────────────────┐
│ 0. INPUT                                                             │
│    Source draft: brand/queue/pending-approval/<entry_id>.md          │
│    YAML frontmatter + `## Voiceover script` + `## Scene breakdown`   │
└──────────┬───────────────────────────────────────────────────────────┘
           │
┌──────────▼───────────────────────────────────────────────────────────┐
│ 1. CLONE VOICE                                                       │
│    scripts/clone_voice.py --draft <source>                           │
│    ChatterBox (MIT) reads voice-lock.md reference samples            │
│    Output: assets/<entry_id>/voiceover.mp3                           │
└──────────┬───────────────────────────────────────────────────────────┘
           │
┌──────────▼───────────────────────────────────────────────────────────┐
│ 2. WORD TIMESTAMPS                                                   │
│    (Smoke-test path) SMOKE_TIMESTAMPS hardcoded in generate_reel.py  │
│    (Real path — pending) MFA → WhisperX → whisper.cpp fallback       │
│    Output: assets/<entry_id>/voiceover.words.json                    │
│      [{word, start, end, emphasis?}, ...] — per-scene indexed        │
└──────────┬───────────────────────────────────────────────────────────┘
           │
┌──────────▼───────────────────────────────────────────────────────────┐
│ 3. PARSE SCENES + CLASSIFY                                           │
│    scripts/generate_reel.py::parse_scenes()                          │
│    Reads ### Scene N headings; label after em-dash → scene_type via  │
│    HEADING_LABEL_MAP (hook / problem_beat / insight_beat /           │
│    data_reveal / cta / outro).                                       │
│    Output: list[{n, scene_type, vo, visual, mood, overlay}]          │
└──────────┬───────────────────────────────────────────────────────────┘
           │
┌──────────▼───────────────────────────────────────────────────────────┐
│ 4. BUILD PER-SCENE PROPS                                             │
│    build_props_for_scene(scene, words)                               │
│    scene_type → composition-specific prop shape:                     │
│      hook        → {words, meshTone, showLogo}                       │
│      problem     → {words}                                           │
│      insight     → {words}                                           │
│      data_reveal → {number, suffix, sign, eyebrow, sublabel, words}  │
│      outro/cta   → {ctaText, ctaUrl, handle}                         │
│    CTA extraction: VO imperative-verb scan first, then overlay       │
│    ALL-CAPS minus URL, fallback "LINK IN BIO". URL match strips to   │
│    domain, uppercased.                                               │
└──────────┬───────────────────────────────────────────────────────────┘
           │
┌──────────▼───────────────────────────────────────────────────────────┐
│ 5. RENDER EACH SCENE (Remotion)                                      │
│    cd brand/remotion-studio && npx remotion render <CompId>          │
│      --props=<tempfile>.json <assets>/scene-N-rmt.mp4                │
│    30 fps · 1080×1920 · H.264 · CRF 18 · yuv420p                     │
│    Chromium OpenGL renderer: angle (required for Paper shaders)      │
│    Each scene ~15-40 sec render time on M-series                     │
│    Output: assets/<entry_id>/scene-{1..5}-rmt.mp4                    │
└──────────┬───────────────────────────────────────────────────────────┘
           │
┌──────────▼───────────────────────────────────────────────────────────┐
│ 6. STITCH (ffmpeg)                                                   │
│    stitch_reel() — single chained pass:                              │
│      a) flash.mp4 (2-frame white 1080×1920) via lavfi                │
│      b) concat.txt interleaving scene-N + flash between pairs        │
│      c) concat + polish: eq (sat 1.08, contrast 1.06) + vignette     │
│         (PI/5) + noise (alls=8:allf=t)                               │
│      d) mux VO + optional BGM:                                       │
│         [vo] asplit → [vo_out][vo_key]                               │
│         [bgm] volume 0.22 → [bgm_raw]                                │
│         [bgm_raw][vo_key] sidechaincompress                          │
│            (thresh 0.04, ratio 8, attack 10, release 400)            │
│         [bgm_ducked][vo_out] amix weights=1:2                        │
│      e) -t <vo_duration> trims trailing silence                      │
│    Output: assets/<entry_id>/reel.mp4                                │
└──────────┬───────────────────────────────────────────────────────────┘
           │
┌──────────▼───────────────────────────────────────────────────────────┐
│ 7. QA GATE                                                           │
│    scripts/qa_reel.py --reel <reel.mp4>                              │
│    Extracts frames @ 2fps, runs 3 checks via ffmpeg signalstats +    │
│    SSIM:                                                             │
│      • visual_density   ≥ 0.08   (frame is not empty)                │
│      • pure_black_ratio ≤ 0.92   (frame is not black hole)           │
│      • frame_delta      ≥ 0.01   (motion present, not stuck)         │
│    Non-zero exit → orchestrator warns, prints frame numbers.         │
└──────────┬───────────────────────────────────────────────────────────┘
           │
┌──────────▼───────────────────────────────────────────────────────────┐
│ 8. MANIFEST + CROSS-LINK                                             │
│    scripts/import_assets.py writes manifest.json                     │
│    Source draft frontmatter gets visual_assets_dir: <path>           │
│    Ready for scheduler-publisher to consume.                         │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Scene → Composition → Props table

| scene_type | Composition (Root.tsx id) | Duration (s) | Required props | Primitives used |
|---|---|---|---|---|
| `hook` | `KineticHook` | 2.9 | `words` | BrowserCycler, Counter, MeshGradient, DigischolaLogo, KaraokeCaption(A) |
| `problem_beat` | `ProblemBeat` | 3.3 | `words` | BrowserFrame, LandingPageMockup(wellness-bad), GazeTrail(drops), Stopwatch(inline), CalloutArrow(warning), KaraokeCaption(B) |
| `insight_beat` | `InsightBeat` | 5.0 | `words` | BrowserFrame, LandingPageMockup(wellness-good), FoldLine, GazeTrail(holds), KaraokeCaption(B) |
| `data_reveal` | `DataReveal` | 3.8 | `number, suffix, sign, words` | FormReducer(9→3), Counter(+N%), LiftChart, CalloutArrow(accent), KaraokeCaption(B) |
| `cta` / `outro` | `OutroCard` | 3.8–4.0 | `ctaText, ctaUrl, handle` | face-01.jpg (iOS-icon square), @handle, centered CTA, URL, DigischolaLogo |

Durations are in `theme/brand.ts::sceneDuration` and mirrored in `generate_reel.py::SCENE_DURATION`. Changing one without the other breaks the pipeline.

---

## Word-timestamp shape

Each scene's caption is driven by a `Word[]` prop. Shape:

```ts
type Word = {
  word: string;     // single token with trailing punctuation kept ("nothing.")
  start: number;    // seconds from scene start (NOT reel start)
  end: number;
  emphasis?: "hook" | "insight";  // drives color + scale
};
```

**Timing rule:** `start` / `end` are per-scene (re-zeroed at each scene boundary). The KaraokeCaption component reads `useCurrentFrame()` which is scene-local.

**Emphasis rule:** `hook` tokens get the accent palette; `insight` tokens get the success/warning pairing from theme. Untagged tokens use the School's base style.

**Punctuation stays attached** to the word it follows. `"nothing."` is one token, not two.

---

## Sticky-active word rule

Inside `KaraokeCaption::RenderedPage`:

```ts
const stickyActiveIdx = page.tokens.reduce(
  (best, t, idx) => currentTimeMs >= t.fromMs ? idx : best,
  -1,
);
```

The last-started word stays highlighted until the next word starts — no dead-state where every word is dim. This is why the caption never looks broken even if a word's `end` is short.

---

## Page grouping rule

`createTikTokStyleCaptions` from `@remotion/captions` groups by speech gap. That broke for us: 6 words with tight inter-word gaps all landed on one page, overflowing the 900px max-width.

**Fix:** bypassed it. We use `groupIntoPages(words, maxWordsPerPage)` — a hard cap:

- School A (hook): `maxWordsPerPage=1` — single-word tiny punch
- School B (default): `maxWordsPerPage=2` — 2-word chunks, 56px

---

## Composition → palette token map

Every composition pulls from `theme/brand.ts`:

| Token | Value | Usage |
|---|---|---|
| `palette.bgDark` | `#0A0E1A` | AbsoluteFill background |
| `palette.accent` | `#3B9EFF` | Neutral highlights, data callouts |
| `palette.success` | `#4ADE80` | Wins, fold line, after-state, +counter |
| `palette.warning` | `#EF4444` | Problems, warning mesh, gaze drops, stopwatch |
| `palette.muted` | — | BEFORE bar, eyebrow labels |
| `palette.strokeDark` | `#0A0E1A` | Cursor stroke |
| `palette.glowSuccess` | — | Counter drop-shadow glow |

**No inline colors. Ever.** If a new color is needed, it goes in `brand.ts` first.

---

## Files in the pipeline

### Skill side (`skills/visual-generator/`)

- `scripts/generate_reel.py` — orchestrator (parse → build props → render → stitch → QA)
- `scripts/clone_voice.py` — ChatterBox VO
- `scripts/qa_reel.py` — post-render frame QA
- `scripts/import_assets.py` — manifest + frontmatter cross-link
- `scripts/render_html_carousel.py` / `render_html_mp4.py` — Path A (carousels/animated)
- `scripts/generate_brief.py` — Path A brief generator

### Studio side (`brand/remotion-studio/src/`)

- `Root.tsx` — composition registry (id → component + duration + defaultProps)
- `theme/brand.ts` — palette, fonts, subtitle tokens, easing, per-scene durations
- `components/BrandBackgrounds.tsx` — MeshGradient, AnimatedNoise, SubtitleSafeZone, GeometricGrid
- `components/UIMockups.tsx` — 10 mockup primitives (see `references/ui-mockup-vocabulary.md`)
- `components/KaraokeCaption.tsx` — word-sync subtitle system
- `components/DigischolaLogo.tsx` — brand logo with staggered letter reveal
- `components/DataPrimitives.tsx` — CountUpNumber, UnderlineDrawOn, Sparkline, KenBurnsImage
- `compositions/*.tsx` — one file per scene type (5 total)
- `public/face-01.jpg` — outro portrait

---

## Determinism contract

Every render must be pixel-identical across runs of the same input. Protections:

1. **No `Math.random()` anywhere.** Use `random("seed-string")` from `remotion`. See `BrowserCycler::scrollY`.
2. **No wall-clock time.** Every animation is frame-indexed via `useCurrentFrame()`.
3. **No network calls in compositions.** `staticFile("face-01.jpg")` only; no `fetch`.
4. **Fonts pre-declared.** Google Fonts loaded at studio init; heavy font use needs `delayRender()`/`continueRender()`.

If a render is NOT pixel-identical across two runs with the same props, it's a bug.

---

## Regeneration strategy

A reel can be regenerated at any cached stage:

- **Tweak a composition** → re-run scene render only: `npx remotion render <CompId> --props=<saved-props>.json <new-out>.mp4`, then re-run stitch.
- **Re-stitch only** (polish/BGM tweak) → `generate_reel.py --draft <source> --skip-render` re-uses cached `scene-N-rmt.mp4`.
- **Fresh VO** → delete `voiceover.mp3`, re-run `clone_voice.py`, re-extract timestamps, re-render all scenes.

---

## Known limitations (v7.3)

1. **Word-timestamp extraction is smoke-test only.** Real extraction via MFA/WhisperX pending. Until then, hand-tagged timestamps in `SMOKE_TIMESTAMPS`.
2. **No multi-reel batch mode.** Each reel is run independently.
3. **No on-the-fly scene reordering.** Order follows `### Scene N` numbering in the draft.
4. **QA gate is shape-level only.** It catches empty/black/stuck frames but does not verify the scene matches creative intent. Human review still needed.
5. **No variant output.** One reel per run. No A/B at render time.

---

## Change log

- **2026-04-21** — v7.3 shipped. This doc locks the architecture. Five compositions, 10 mockup primitives, QA gate wired, sticky-active captions, UI-mockup discipline.
- **2026-04-21** — v7.2 pivot: geometric abstractions → UI mockups (Cody Plofker aesthetic). Subtitles 96→56px. Anchor 1760→1560.
- **2026-04-21** — v7.1: Paper Design mesh shaders + KaraokeCaption page-grouping bypass.
- **2026-04-21** — v7.0: Remotion-primary rebuild. Hyperframes deprecated. Kling / Meta AI / Veo all removed.
