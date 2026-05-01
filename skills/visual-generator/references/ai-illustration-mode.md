# Path C — AI Illustration Mode (Digischola, conditional)

Added 2026-05-01 after Mayank moved to Higgsfield Ultra plan ($99/mo, 3,000 credits + unlimited Nano Banana 2 Flash). Lifts the v7 ban on AI image generation **only for non-photographic illustrations**. Photographs of people stay banned.

## What this mode unlocks

Generated frames that augment Path A (Claude Design carousels) and Path B (Remotion reels), specifically for these uses:

- **Iconographic illustrations** — abstract shapes, glyphs, infographic icons (e.g., upward arrow with chart, gear-and-cogwheel diagrams, simplified hand-drawn metaphors)
- **Typographic backgrounds** — texture / abstract / mesh-shader-style backgrounds for quote cards
- **UI mockups** — fake landing pages, dashboards, browser chrome variants that the Remotion `LandingPageMockup` primitive can't easily produce (e.g., a specific competitor's checkout flow, a fake SaaS dashboard)
- **Decorative atmosphere** — soft gradients, abstract geometric scenes, conceptual flat-illustration backdrops

## What this mode still BANS (hard)

- ❌ **AI photographs of any person** — Mayank, devotees, clients, anyone. Outro `face-01.jpg` stays the only real-photo human asset.
- ❌ **AI-generated faces** — even illustrated faces of recognizable people. Generic illustrated faces (no specific person) are gray-area; default ban, lift only with explicit per-asset analyst approval logged in render_log.jsonl.
- ❌ **Photorealistic AI** of any kind in body content. Outro photo stays real.
- ❌ **AI deity / sacred imagery** — never. Same kernel rule as `ai-image-generator` for client-track.
- ❌ **Photoreal AI portraits** — never. The whole reason for the ban: Mayank's authenticity hinges on real face presence.

## Routing

Path C invocation conditions inside `generate_reel.py` and `render_html_carousel.py`:

```
IF scene type / slide type ∈ {iconographic, typographic_bg, ui_mockup_bespoke, decorative_atmosphere}
   AND scene_spec.allow_ai_illustration == true (set by analyst in source draft frontmatter):
       → route to ai-image-generator's nano_banana_flash (unlimited on Ultra)
       → save to brand/queue/assets/<entry_id>/ai-illustrations/<slug>.png
       → composite into Remotion / carousel as a UIIllustration component
ELSE:
       → continue with native Path A / Path B (Claude Design / Remotion primitives)
```

The route is OFF BY DEFAULT for every reel and carousel. The analyst opts in per-asset by adding `allow_ai_illustration: true` to the source draft's `## Scene breakdown` block or `## Slide N` metadata.

## Source draft schema additions

Optional new fields on each scene / slide block:

```yaml
scene: insight_beat
allow_ai_illustration: true
illustration_brief: "Flat illustrated landing page mockup, browser chrome, hero section showing a single bold CTA button. Soft pastel palette matching brand. No people, no faces."
illustration_aspect: 16:9
```

Or in YAML frontmatter at draft top:

```yaml
---
visual_concept_brief:
  type: ai_illustration
  intent: typographic_bg
  prompt: "Soft mesh gradient backdrop, brand colors, suitable as quote card background"
  aspect: 1:1
---
```

`generate_reel.py` and `render_html_carousel.py` parse these and call `ai-image-generator` directly via the in-session MCP path. Manifest tracks the gen alongside Remotion / Claude Design components.

## Validation rules added

`scripts/qa_reel.py` and the carousel validator gain two new checks when AI-illustration assets are present:

1. **No-face check** — run a face detector (OpenCV haar cascades, already installed for video-edit) over each AI-illustration PNG. Any face detected → CRITICAL fail. Reject + re-prompt with stronger negative.
2. **No-deity check** — Claude in-session reads each AI-illustration PNG and checks for accidental sacred subject leak (Krishna iconography, Om symbol misuse, etc.). Flag for analyst review.

## When to NOT use Path C

Even with the lift, prefer Path A (Claude Design) and Path B (Remotion primitives) for everything they can do well. AI illustration is the escalation tier when the native primitives can't produce the needed asset. Reasons:

- Native primitives are deterministic — re-renderable identically forever
- Brand consistency is automatic via design-tokens.json
- Zero generation cost
- No risk of off-brand drift

AI illustration introduces stochasticity. Use it when the alternative is "give up on this scene" or "ship something visibly worse."

## Memory

Mayank's feedback memory `digischola-ai-illustration-allowed.md` (added 2026-05-01) codifies what's allowed and what's still banned. Cross-reference if the rule needs revisiting.
