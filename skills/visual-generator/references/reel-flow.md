# reel-flow

Detailed steps for `visual-generator reel`. Loaded only when producing a 15-30 sec Reel.

## Source

A draft with `format: reel` or a draft adapted from a carousel via `draft-week repurpose`. The body has a hook + 3-5 insight beats + outro.

## Step 1: Storyboard

Build a 4-6 scene plan:

| Scene | Time | Purpose | Source |
|---|---|---|---|
| Hook | 0-3s | Grab attention. On-screen text + bold visual. | Higgsfield AI illustration OR UI-mockup |
| Beat 1 | 3-9s | First insight. Specific number or framework. | UI-mockup screenshot OR Higgsfield video |
| Beat 2 | 9-15s | Second insight. Contrast or proof. | UI-mockup OR Higgsfield video |
| Beat 3 | 15-21s | Third insight (optional, depends on length target). | UI-mockup OR Higgsfield video |
| Outro | 21-30s | CTA + still portrait + handle. | Static portrait + brand chip |

## Step 2: Per-scene routing

For each scene, decide UI-mockup vs Higgsfield video:

- **UI-mockup** (preferred for LP-craft pillar) — Claude writes simple HTML showing a landing page mockup, a form shrinking, a metric counter. Playwright captures + ffmpeg trims to scene duration.
- **Higgsfield video** (preferred for Solo Ops + Paid Media pillars when atmosphere matters) — Higgsfield Kling 2.5 / Hailuo 2.3 / Seedance 1.0.

| Higgsfield model | Best for | Notes |
|---|---|---|
| Kling 2.5 | Cinematic, motion-controlled hero scenes | Default. Unlimited on Ultra. |
| Hailuo 2.3 | Motion-heavy abstract | Unlimited on Ultra. Faster. |
| Seedance 1.0 | Stylized illustration in motion | Unlimited on Ultra. |
| Veo 3.1 | Premium cinematic | Paid (50cr). Use sparingly. |

## Step 3: Generate scenes

For UI-mockup scenes:
1. Claude writes HTML/CSS for the mockup (no JS required).
2. Playwright opens the HTML, captures frames at 30fps for `scene_duration` seconds.
3. ffmpeg encodes to MP4: `ffmpeg -framerate 30 -i frame-%04d.png -c:v libx264 -pix_fmt yuv420p -t <duration> scene-N.mp4`.

For Higgsfield video scenes:
1. Write the prompt respecting guardrails (no people, no deity, no logos).
2. Call `mcp__b39cf66e..__generate_video` with model + duration.
3. Poll until done. Download to `brand/videos/<entry_id>/scene-N.mp4`.

## Step 4: Voiceover

Default: kinetic on-screen text only. Silent.

If VO is desired:
- Generate via Higgsfield Voice (when available) using the locked voice corpus reference, OR
- Skip and rely on captions only.

The old ChatterBox voice-cloning stack is retired for the personal brand.

## Step 5: Outro

Static portrait at `brand/_engine/face-samples/portrait.png` overlaid with:
- Handle: `@digischola.in`
- Logo: locked Digischola wave (top-left or center)
- CTA text: "DM if [pillar]-related" or "Follow for more [pillar] tear-downs"

This is a real photo, not AI-generated. Hold on screen for 4-6 seconds.

## Step 6: Stitch

```bash
ffmpeg -i scene-1.mp4 -i scene-2.mp4 -i scene-3.mp4 -i scene-4.mp4 -i outro.mp4 \
  -filter_complex "[0:v][1:v][2:v][3:v][4:v]concat=n=5:v=1:a=0[v]" \
  -map "[v]" \
  -c:v libx264 -pix_fmt yuv420p \
  brand/videos/<entry_id>/reel.mp4
```

Add brand chip overlay:

```bash
ffmpeg -i reel.mp4 -i brand_chip.png \
  -filter_complex "overlay=W-w-20:H-h-20" \
  reel-final.mp4
```

## Step 7: Validate

```bash
python3 scripts/validate_output.py --reel brand/videos/<entry_id>/reel-final.mp4
```

Checks:
- Duration 15-30 seconds
- Aspect ratio 9:16 (1080x1920) for Reels/TikTok, OR 1:1 for IG feed
- Audio peak < -3 dBFS (if audio present)
- Brand chip visible on every frame
- No human face detected in any non-outro frame (OpenCV cascade)

## Anti-patterns

- Do NOT generate AI faces of Mayank or anyone else. Outro is the static photo only.
- Do NOT exceed 30 seconds. Algorithm penalizes Reels >30s.
- Do NOT skip the brand chip — that's the recall mechanism.
- Do NOT mix aspect ratios across scenes — final stitch needs uniform 9:16 or 1:1.
- Do NOT use Higgsfield to generate anything containing text — it garbles. Use ffmpeg overlay for kinetic captions.
