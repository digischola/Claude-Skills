# How a Good Video Editor Thinks — Plain English

This file explains the 5-layer thinking process that separates a real video editor from a template engine. Every step in SKILL.md flows from this.

---

## Layer 1 — Look at the source

Before any design choices, the skill WATCHES the source video and builds a map of:

- **Where the face is** — a rectangle around the speaker's face, updated every half-second. So text never covers the face.
- **Where the empty space is** — the parts of the frame with nothing interesting. Best spots for overlays.
- **When there are natural cut points** — shot boundaries if any, or silence gaps where a transition can land without breaking a sentence.
- **When the speaker emphasizes** — loud words, pauses before key phrases.
- **What color and brightness dominate each moment** — so we don't put blue text on a blue wall.
- **Beat grid if music is present** — so cuts and text-pops sync to the music.

Output: `source-intel.json` — every downstream decision reads this.

## Layer 2 — Understand the story

The skill reads the transcript (and source-intel) and figures out:

- What is the HOOK (the first 2-3 seconds)?
- What is the ONE hero number or claim?
- What are the 2-3 words worth emphasizing?
- What is the call-to-action at the end?
- Where is the natural "aha" moment vs the setup?

Output: `content-plan.json` — this is what turns raw footage into an edit script.

## Layer 3 — Decide the look

Brand colors, fonts, motion style. Comes from:
- Client's brand-config if it exists (highest priority)
- One of the 8 aesthetic presets (apple-premium, gen-z-punchy, etc.)
- The user's one-line mood description

Output: `DESIGN.md` — the visual identity lock.

## Layer 4 — Pull pieces from the shelf

Rather than writing HTML from zero, compositions are assembled from a shelf of pre-built components. The shelf is organized in 6 categories:

**Text pieces** — hook cards, kinetic caption styles (word-pop / karaoke / slam / highlighter sweep / scatter / elastic / blur-in / scramble), pull quotes, lower thirds, end cards.

**Motion pieces** — text reveals (slide, blur, letter-by-letter), shape morphs, camera moves (push-in, pull-out, parallax), particle effects (dust, sparkle), glitch.

**Chart pieces** — metric counter (odometer / scramble / count-up), bar chart with animated build, line chart that draws in with milestone markers, donut / pie chart, before-and-after comparison split, progress bar, pictograph (repeating icons).

**Mockup pieces** — fake browser window (Safari or Chrome frame), fake phone screen (iPhone or Android), fake dashboard panel, fake form with input fields, fake landing page hero section, fake app UI (Slack / Linear / Notion style).

**Overlay pieces** — blur panel (frosted glass look), brand-color wash, vignette (darkens edges), noise / film grain, light leaks, shader transitions.

**Emphasis pieces** — highlighter sweep over words, hand-drawn circle around a word, underline scribble, arrow callouts, price tag, pill badge.

Each piece is a self-contained HTML + CSS + GSAP snippet with inputs like color and text. The editor picks which pieces fit the message and assembles them.

## Layer 5 — Quality check during build (not after)

Before render completes, check:

- **Face-safe placement** — no text or overlay covers the detected face rectangle
- **Readable contrast** — white text against a dark-enough background (WCAG AA standard)
- **Pacing** — no silent stretches >1.5 seconds with nothing happening on screen
- **Brand adherence** — all colors trace to the DESIGN.md palette, no rogue hex codes
- **No overlap bugs** — two overlays don't land in the same pixel area at the same time

Any quality failure triggers a fix, then re-render. Not "render and hope."

---

## Why source intelligence is the biggest unlock

Template engines can't know that YOUR video has a face at pixel 540-720 between seconds 2 and 18. A real editor knows and auto-places captions in the empty space below.

Same for cut points: template engines land transitions on fixed timestamps. A real editor lands transitions on natural pauses so sentences never get chopped in half.

Same for emphasis: template engines emphasize predictable words. A real editor emphasizes the one claim word that actually carries the insight.

Everything else is common — most tools have SOME component library. The source-intelligence layer is the moat.

---

## How this changes SKILL.md

The old 9-step pipeline becomes:

1. Load context (unchanged)
2. **NEW: Look at the source** → `source-intel.json`
3. Probe technical specs (unchanged — merged with step 2 in future)
4. **NEW: Understand the story** → `content-plan.json`
5. Translate brief + plan → preset + DESIGN.md (existing, expanded)
6. ffmpeg pre-pass (unchanged)
7. **CHANGED: Assemble composition from component shelf** (not write from scratch)
8. Render via HyperFrames CLI (unchanged)
9. **NEW: Quality checks during build** → face-safe, contrast, pacing, brand
10. ffmpeg post-pass (unchanged)
11. Deliver (unchanged)
12. Validate + feedback loop (unchanged)
