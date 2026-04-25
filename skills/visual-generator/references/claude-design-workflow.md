# Claude Design Workflow

How to work with claude.ai/design for Digischola-branded visuals. This is the primary engine for static graphics + simple animations.

## One-time setup: seed brand memory

Open claude.ai/design once and set up a "Digischola design system" so every future design inherits brand identity automatically.

**Paste this into a new Claude Design project:**

```
Create a design system called "Digischola" with these brand specifications:

COLORS
- Primary Blue: #3B9EFF (CTAs, links, highlights, metric callouts)
- Primary Glow: #6BB8FF (hover states, accents)
- Background: #000000 (dark mode primary)
- Card Background: #080808
- Foreground text: #F8FAFC
- Muted text: #9BA8B9 (supporting text only)
- Success green: #4ADE80 (positive metric callouts only; use sparingly)
- Border: #262626

TYPOGRAPHY
- Display / hero: Orbitron Bold 700 (40-80px)
- Section headings: Space Grotesk SemiBold 600 (24-40px)
- Subheadings: Space Grotesk SemiBold 600 (20-24px)
- Body: Manrope Regular 400 (15-18px)
- CTAs: Space Grotesk SemiBold 600 UPPERCASE

LOGO
- Wordmark: DIGISCHOLA with SCHOLA in Primary Blue (#3B9EFF)
- Lives on dark backgrounds (primary); light version for print only

AESTHETIC
- Tech-forward, performance-credibility, dark-mode modern
- Orbitron lends a slight futurist / operator-mode feel
- Blue gradient (#3B9EFF → #6BB8FF) for visual hook moments
- Success green reserved for positive metric callouts (188%, +65%)
- Never use em dashes in any copy (universal rule)
- Never use hype words (unlock, revolutionize, game-changer)

Save this as the Digischola brand memory so every future design in this account uses it.
```

Claude Design should confirm the brand system is saved. From then on, prompts like "make a carousel for the Thrive LP audit" will inherit these specs automatically.

**Verify setup:** ask Claude Design "what's our brand?" — it should recite the colors, fonts, and aesthetic correctly.

## Running a design session

1. **Generate the brief.** Run `scripts/generate_brief.py <source-file> --target <format>` — produces a paste-ready markdown brief at `brand/queue/briefs/<source-id>-<target>-brief.md`.
2. **Open claude.ai/design** and create a new project.
3. **Paste the brief.** The brief is structured (format specs + per-slide content + brand reminders).
4. **Iterate in the web UI.** Tell Claude Design what to adjust: "slide 3 feels cluttered", "the blue accent on slide 1 should be bigger", etc.
5. **Hand off to Claude Code.** When the design is final, click "Hand off to Claude Code" in Claude Design. It gives a command like:
   ```
   Render https://claude.ai/design/<design-id> as MP4 / PNG / PDF to <output-folder>
   ```
6. **Paste that command into this Claude Code session.** Claude Code will render the HTML via browser + ffmpeg and save to `brand/queue/assets/<source-id>/`.
7. **Import + catalog.** Run `scripts/import_assets.py <output-folder> --source-id <id>` to move files into the skill's standard queue location with proper naming and a manifest.

## Brief template structure (what generate_brief.py produces)

```markdown
# Visual Brief: <source-id> → <target-format>

## Engine
Claude Design at claude.ai/design. Paste this entire brief, iterate, then hand off to Claude Code for render.

## Brand
Use Digischola brand memory (dark mode, #3B9EFF primary, Orbitron/Space Grotesk/Manrope, no em dashes).

## Target format
<format-specific specs: aspect ratio, dimensions, duration, slide count>

## Source content
<extracted content from source draft: hook, body, per-slide breakdown, CTA>

## Animation direction (if animated)
<tempo, transitions, visual energy>

## End card / CTA
<soft close matching source>

## Render format when handing off
<PNG sequence for carousel / MP4 for Reel / PDF for LinkedIn document>
```

## Handoff render gotchas

- Claude Design generates HTML. The render command uses a headless Chrome to screenshot (for PNG) or record (for MP4 via ffmpeg).
- If the render fails (browser can't load the page, fonts missing), re-run from scratch. The design itself doesn't need to be recreated — just re-hand off.
- For MP4 animations, ensure duration matches the brief (Claude Design sometimes defaults to shorter). Verify in preview before handoff.

## When to skip Claude Design

- Needs precise reproducibility (same data → same pixels every time) → use Hyperframes
- Volume > 5 visuals per week → Hyperframes' programmatic approach is faster at scale
- Talking-head Reel (video with speech) → Hyperframes (v2, after transcription added)
