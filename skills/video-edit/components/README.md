# Video-Edit Component Library

The shelf a pro editor pulls pieces from. Every composition is ASSEMBLED from these — never written from scratch.

## Philosophy

- **Self-contained** — each component is one HTML snippet + CSS + GSAP block. Drop into any HyperFrames composition.
- **Parameterized** — primary/accent colors, text, duration are inputs. No hardcoded values.
- **Deterministic** — no Math.random, no Date.now. Seekable, renderable frame-by-frame.
- **Brand-agnostic** — components don't know about Digischola blue. They take a color token.

## Categories

| Folder | What it contains | Count target v1 |
|---|---|---|
| `text/` | Hook cards, caption kinetic styles, pull quotes, lower thirds, end cards | 12 |
| `motion/` | Text reveals (slide, blur, letter-stagger, split), shape morphs, camera moves, particles | 10 |
| `charts/` | Metric counter, bar chart, line chart, donut, before/after split, progress bar | 8 |
| `mockups/` | Browser chrome (Safari/Chrome), phone, dashboard, form, LP hero, app UI | 8 |
| `overlays/` | Blur panel, color wash, vignette, noise, light leaks | 6 |
| `emphasis/` | Highlighter sweep, hand-drawn circle, underline scribble, arrow, badge, price tag | 8 |
| `broll/` | Full cutaway scenes — landing page scrolling, form shrinking, cursor trail, bar building, stopwatch ticking | 10 |

`_registry/` holds the machine-readable index of all components (name, category, inputs, duration range, use-case tags) so the composition assembler can query it.

## External libraries this stack uses — 100% FREE

All dependencies are free (MIT / free tier downloads only). No paid subscriptions.

| Library | License | Why | Where |
|---|---|---|---|
| **GSAP core** | Free MIT | Animation engine — timeline, stagger, eases, tweens | All components |
| **Lottie (lottie-web runtime)** | Free MIT | Plays AE-exported animations in-browser | `broll/`, `charts/`, `motion/` |
| **LottieFiles free downloads** | Free | Tens of thousands of free Lotties (paid tier only for collab — skipped) | Downloaded JSONs stored in `components/_assets/lottie/` |
| **Chart.js** | Free MIT | Data viz — bar, line, donut, comparison | `charts/` |
| **Tailwind CSS (via CDN)** | Free | Rapid utility styling for mockups | `mockups/` |
| **Lucide Icons SVG** | Free MIT | Icon set (3000+) | `emphasis/`, `mockups/` |
| **Paper Design mesh gradients** | Free | Hero backgrounds | `overlays/` |
| **Pexels API** | Free with API key | Real B-roll stock footage | pulled on demand |
| **flubber.js** | Free MIT | SVG path morphing (replaces paid MorphSVG) | `motion/`, `emphasis/` |

### Free replacements for GSAP Club plugins

We do NOT use paid GSAP Club plugins. Free alternatives:

| Club plugin (paid) | Free alternative | Implementation |
|---|---|---|
| SplitText | Manual split into spans + GSAP stagger | `components/_helpers/splitText.js` |
| ScrambleText | Custom loop with random-char tween | `components/_helpers/scramble.js` |
| DrawSVG | Pure CSS `stroke-dasharray` + `stroke-dashoffset` | `components/_helpers/draw-svg.css` |
| MorphSVG | flubber.js free MIT for path morphs | `components/_helpers/morph.js` |

## Registry format

Every component has a `*.json` sidecar in `_registry/` describing:

```json
{
  "id": "broll/landing-page-scrolling",
  "name": "Landing Page Scrolling Mockup",
  "category": "broll",
  "description": "Fake landing page that scrolls from top to bottom, cursor arrow visible, great for 'visitor scrolls to understand' or 'above the fold' moments.",
  "inputs": {
    "primary_color": "hex",
    "page_title": "text",
    "hero_copy": "text",
    "cta_text": "text (optional)"
  },
  "duration_range": [2.0, 6.0],
  "aspect_support": ["9:16", "16:9"],
  "use_cases": [
    "visitor_scrolls_moment",
    "above_fold_reference",
    "landing_page_audit_context"
  ],
  "snippet_file": "broll/landing-page-scrolling.html",
  "dependencies": ["tailwind", "gsap"]
}
```

A composition assembler reads the registry, picks components matching use-case tags from the content-plan, injects input values, and stitches together the final index.html.

## How a pro composition assembles

1. Content plan says: "at 13.5s, emphasize '+130% conversion' → HERO beat"
2. Registry query: `use_cases ∋ metric_hero, duration_range contains 2.0s` → returns `charts/metric-counter-odometer.json`
3. Assembler reads the snippet, injects `{metric: "+130%", label: "Conversion lift", color: "#4ADE80"}`, drops into composition at `data-start="13.5"`.
4. Repeat for every beat in the content plan.

This replaces the "write HTML from scratch" workflow. New edit = pick 8-12 components + inject values + render.

## Next build order (phase A of v2)

Starting components — the minimum set to actually edit a talking-head Reel like a pro:

1. `broll/landing-page-scrolling.html` — fake LP with cursor scroll (Tailwind + GSAP)
2. `broll/form-shrinking.html` — long form collapsing to short form
3. `charts/metric-counter-odometer.html` — big number counting up
4. `charts/bar-chart-build.html` — bar animating from 0 to target (Chart.js + GSAP)
5. `text/hook-card-split.html` — split-screen hook with big number
6. `text/kinetic-caption-wordpop.html` — word-by-word pop-in caption
7. `mockups/browser-chrome.html` — Safari-style frame wrapper (Tailwind)
8. `mockups/phone.html` — iPhone frame wrapper (Tailwind)
9. `emphasis/marker-sweep.html` — highlighter pen over text (GSAP DrawSVG)
10. `emphasis/arrow-callout.html` — curved arrow pointing at an element (Lucide SVG + DrawSVG)
11. `overlays/blur-panel.html` — frosted glass panel with backdrop-filter
12. `motion/zoom-punch.html` — brief 1.0→1.08 zoom with subtle shake (GSAP)

Each is small (50-200 lines HTML+CSS+JS). Build them all before wiring the assembler.
