# illustration-flow

Detailed steps for `visual-generator illustration`. Loaded only when generating AI illustration.

## Pre-flight check

The source draft frontmatter MUST contain:

```yaml
allow_ai_illustration: true
visual_request: illustration
```

If `allow_ai_illustration` is false or missing → abort. Suggest the carousel mode instead, or attach a hand-picked stock image.

## Step 1: Write the Higgsfield prompt

Prompt template:

```
[Subject — abstract concept, NEVER human/face/deity]
[Style — minimalist editorial illustration / flat geometric / typographic / UI mockup]
[Color — palette anchored to Digischola: #3B9EFF accent, #FFFFFF base, dark charcoal #0F172A]
[Negative — no people, no faces, no deity imagery, no logos, no children, no celebrities]
```

Example prompts:

- LP-craft pillar: `flat geometric illustration of a website wireframe with a single bold CTA button, ascending bar chart visible behind, deep blue accent, white background, editorial style, no humans, no logos`
- Solo Ops pillar: `minimalist desktop scene with three floating UI mockups, soft typography, warm neutral palette, editorial illustration, no people, no faces`
- Paid Media pillar: `abstract data dashboard illustration, charts spilling outward, accent blue #3B9EFF, clean negative space, flat editorial style, no humans`

## Step 2: Route to Higgsfield model

| Use case | Model | Why |
|---|---|---|
| Default | Nano Banana 2 Flash | Unlimited on Ultra. Fast. Good for editorial illustration. |
| Typographic precision needed | Nano Banana Pro | Better text rendering. Paid (50cr per gen). |
| Photorealistic but abstract | Flux 2 / Seedream 4.5 | Higher fidelity. Paid. |
| Cinematic UI mockup | Cinematic Studio 2.5 | Premium. Paid. |

Default → Nano Banana 2 Flash.

## Step 3: Generate 3 variations

Call `mcp__b39cf66e..__generate_image` 3 times with seeds 1/2/3 (or random) to get variety. Same prompt, different seeds.

## Step 4: Score variations

For each output, check:

- **Color match** — extract dominant colors, compare to brand palette. Within 5% Lab delta = pass.
- **Voice fit** — does it match Restrained / Confident / Pragmatic tone? (Subjective — Claude judges.)
- **Banned elements** — run OpenCV face cascade (in `validate_output.py`). If a face is detected → reject.
- **Logo overlap** — if a generated shape resembles the Digischola wave logo → reject.

Pick the winner. If all three fail → regenerate with refined prompt.

## Step 5: Save winner

```
brand/social-images/<entry_id>/illustration.png
brand/social-images/<entry_id>/manifest.json
```

manifest.json shape:

```json
{
  "mode": "illustration",
  "draft_file": "<draft.md>",
  "higgsfield_calls": [
    {"model": "nano_banana_flash", "prompt": "...", "seed": 1, "result": "var-1.png", "selected": false},
    {"model": "nano_banana_flash", "prompt": "...", "seed": 2, "result": "var-2.png", "selected": true},
    {"model": "nano_banana_flash", "prompt": "...", "seed": 3, "result": "var-3.png", "selected": false}
  ],
  "selected_output": "illustration.png",
  "rendered_at": "<iso8601>"
}
```

## Anti-patterns

- Do NOT include any human or face in the prompt — even "abstract person silhouette". The OpenCV cascade will catch it.
- Do NOT include religious symbols, deity names, or sacred imagery in the prompt.
- Do NOT generate logos. Use the locked Digischola logo from brand-identity.md.
- Do NOT use this for client work. Client work goes through `ai-image-generator`.
