# Hyperframes Setup — ARCHIVED v6 install notes

> ⚠ **ARCHIVED 2026-04-22.** This file documents the v6 Hyperframes install procedure (pre-v7 rebuild). It is kept for historical reference only.
>
> **Current (v7.4) Hyperframes wiring:** see `SKILL.md` + `references/v7-pipeline-architecture.md` + `references/engine-selection.md`. The live Hyperframes project now lives at `brand/hyperframes-scenes/` (not the old `brand/hyperframes-studio/`), is driven by `bunx hyperframes` (not a custom install), and renders social-platform overlay scenes only. UI-mockup teardown scenes render via Remotion.
>
> Do NOT follow the setup instructions below. They are outdated.

---

# [HISTORICAL] Hyperframes Setup (v6)

Hyperframes is HeyGen's open-source video engine built for Claude Code. Purpose-built for the HTML → browser → ffmpeg → MP4 pipeline. Has a catalog of animation elements, its own "make a video" skill, and a studio preview on localhost.

## One-time setup

### 1. Clone the repo

```bash
cd /Users/digischola/Desktop/Digischola/brand
git clone https://github.com/HeyGen-Official/hyperframes hyperframes-studio
cd hyperframes-studio
```

If the repo path above has shifted, find the current official repo at HeyGen's GitHub org. The Hyperframes project is actively maintained.

### 2. Install dependencies

```bash
npm install
```

This pulls in Node packages for the React components, renderer, and ffmpeg wrapper. Takes 2-5 minutes depending on network.

### 3. Verify ffmpeg is installed

```bash
ffmpeg -version
```

If not found:

```bash
brew install ffmpeg
```

### 4. Start the studio (verify install)

```bash
npm run dev
```

Opens a localhost preview on a port (usually 3000 or 3001). You should see the Hyperframes studio UI. Ctrl+C to stop once you've verified.

### 5. Bring brand context into the project

Add a `BRAND.md` or `CLAUDE.md` at the root of `hyperframes-studio/` that points at the Digischola brand identity:

```markdown
# Brand context for this Hyperframes project

Read brand specs from:
/Users/digischola/Desktop/Digischola/brand/brand-identity.md

Core rules:
- Background: #000000
- Primary accent: #3B9EFF
- Fonts: Orbitron (display), Space Grotesk (headings), Manrope (body) via @remotion/google-fonts
- Dark mode only
- No em dashes in any rendered text
- No hype words
```

This way any Claude Code session inside the hyperframes-studio project picks up brand context automatically.

## Running a Hyperframes video session

1. **Generate the brief.** `scripts/generate_brief.py <source-file> --target reel` — writes a paste-ready brief with video-specific sections (hook, beats, close, animation tempo).
2. **Drop source assets into hyperframes-studio.** If there's a source video or image asset, put it at `hyperframes-studio/public/<source-id>/`. Scripts + briefs are passed directly in the Claude Code prompt.
3. **cd into hyperframes-studio and start Claude Code there.** Hyperframes has its own "make a video" skill that activates when you're working inside the project folder.
4. **Invoke the built-in skill.** Prompt Claude Code:
   ```
   Use the make-a-video skill. Brief is at: /Users/digischola/Desktop/Digischola/brand/queue/briefs/<source-id>-reel-brief.md
   Follow the brief's format specs, animation direction, and close. Use the Digischola brand (BRAND.md).
   ```
5. **Iterate.** Hyperframes starts a localhost preview. Review, give feedback ("the hero title is cut off at 6 seconds"), let Claude Code re-render.
6. **Final render.** When approved, Claude Code runs the render command → outputs MP4 to `hyperframes-studio/out/<project>.mp4`.
7. **Import into queue.** Run `scripts/import_assets.py hyperframes-studio/out/<project>.mp4 --source-id <id>` → moves to `brand/queue/assets/<source-id>/` with proper naming + manifest.

## Hyperframes features worth knowing

- **Catalog of animation elements** — Mac OS notifications, Reddit cards, app showcases, terminal effects, 3D UI reveals, transitions. Use these as building blocks.
- **Built-in skill** — "make a video" walks through planning → script → scenes → render. Mirrors a human video editor's flow.
- **Localhost preview** — live-reloads on changes; faster iteration than blind re-renders.
- **ffmpeg integration** — renders use system ffmpeg. Matches IG Reel spec (H.264 + AAC, 1080x1920, 30fps).
- **Free and open source** — no license fee.

## When NOT to use Hyperframes

- Static graphics (carousel, quote card) → Claude Design is simpler.
- One-off exploratory design → Claude Design's UI iteration is faster.
- You don't want Node dependencies → stick with Claude Design + handoff rendering.

## Common issues + fixes

- **Localhost preview shows 0 seconds / blank** — sometimes happens with new compositions. Ask Claude Code to "render full" instead of relying on preview.
- **Font loading lags** — `@remotion/google-fonts` takes a moment on first render. Cache warms after first pass.
- **Render taking forever** — use `--concurrency 4` (or lower) if CPU is overheating. Default uses all cores.
- **whisper.cpp crashing RAM** — v1 skips transcription entirely. If v2 adds it, use `faster-whisper` (pip install, base.en model, ~140MB) instead of whisper.cpp.

## Version pinning

This skill was built against Hyperframes as of 2026-04. If the repo API changes significantly (e.g., the "make a video" skill is renamed), update this file and note the working Hyperframes version. Check the repo README for migration notes.
