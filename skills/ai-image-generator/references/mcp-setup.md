# Higgsfield MCP Setup — Image Side

The skill cannot run without the Higgsfield MCP connector. Connector confirmed live on Mayank's Claude Code as of 2026-05-01 on Ultra plan.

## Install (Claude Code)

```bash
claude mcp add --transport http higgsfield https://mcp.higgsfield.ai/mcp
```

Restart Claude Code; on first call, the MCP prompts for OAuth — log in with the Higgsfield account.

## Verified tool surface (server ID `b39cf66e-...`)

The skill uses these image-relevant tools:

| Tool                  | Purpose                                                        |
|-----------------------|----------------------------------------------------------------|
| `balance`             | Check credits + plan tier (no args)                            |
| `models_explore`      | Discover model IDs, aspect ratios, parameters, required medias |
| `generate_image`      | **Single tool for text-to-image AND image-to-image.** Mode determined by `medias[]` array (role: `image`) |
| `media_upload`        | Upload local image to use as reference (returns UUID)          |
| `media_confirm`       | Confirm uploaded media is processed                            |
| `show_generations`    | List past generations + status (poll for completion)           |
| `show_medias`         | List uploaded reference media                                  |
| `transactions`        | Credit transaction history                                     |
| `select_workspace`    | Switch active workspace                                        |
| `job_display`         | Display a specific job                                         |

## Plan + credits — Ultra baseline (2026-05-01)

Mayank's account: Ultra plan, 3,000 credits + unlimited Nano Banana 2 Flash + 3 unlimited video models (Kling 2.5, Seedance 1.0, Hailuo 2.3) + 30-day Nano Banana 2 unlimited window.

| Plan        | Monthly | Credits | Unlimited models                                | Verdict for client image work     |
|-------------|---------|---------|-------------------------------------------------|-----------------------------------|
| Free        | $0      | 150     | None                                            | Test only — watermarked           |
| Starter     | $15     | 200     | None                                            | Too credit-starved                |
| Plus        | $39     | 1,000   | Nano Banana 2 (30-day)                          | Acceptable, low-volume baseline   |
| **Ultra**   | **$99** | **3,000** | **Nano Banana 2 Flash + Kling 2.5 + Seedance 1.0 + Hailuo 2.3** | **Working baseline as of 2026-05-01** |

## Verified image model IDs (from `models_explore` 2026-05-01)

These are the exact strings that go in `params.model`:

| Model ID                  | Provider          | Best for                                       | Constraints / notes               |
|---------------------------|-------------------|------------------------------------------------|-----------------------------------|
| `nano_banana_flash`       | Google            | **Default tier — unlimited on Ultra.** Fast, photorealistic, decent text rendering | resolution: 1k/2k/4k, all common aspects |
| `nano_banana_2`           | Google            | Premium quality, text rendering, diagrams      | resolution: 1k/2k/4k, all aspects |
| `nano_banana`             | Google            | Budget realistic                               | basic                             |
| `gpt_image_2`             | OpenAI            | **Best text rendering, premium typography, 4k** | quality: low/med/high, resolution: 1k/2k/4k |
| `gpt_image`               | OpenAI            | GPT Image 1.5 — typography, diagrams           | quality: low/med/high             |
| `marketing_studio_image`  | Higgsfield        | **One-click product / social ad images**       | resolution: 1k/2k/4k, all aspects |
| `cinematic_studio_2_5`    | Higgsfield        | Cinematic stills, dramatic lighting, 4k        | resolution: 1k/2k/4k              |
| `soul_2`                  | Higgsfield        | UGC, fashion editorial, character generation   | optional `soul_id` for identity-lock |
| `soul_cast`               | Higgsfield        | **Consistent character identity across creatives** | budget param (default 50)         |
| `soul_cinematic`          | Higgsfield        | Cinema-grade stills + concept art              | -                                 |
| `soul_location`           | Higgsfield        | Environment + background generation            | -                                 |
| `seedream_v4_5`           | Bytedance         | 4k, precise control, transformations           | quality: basic/high               |
| `seedream_v5_lite`        | Bytedance         | Visual reasoning, instruction-based editing    | quality: basic/high               |
| `flux_2`                  | Black Forest Labs | Precise prompt adherence, creative versatility | resolution: 1k/2k, model: pro/flex/max |
| `flux_kontext`            | Black Forest Labs | Context-aware editing + style transfer         | reference-image required          |
| `kling_omni_image`        | Kling             | Versatile photorealistic, wide aspects         | resolution: 1k/2k                 |
| `grok_image`              | xAI               | Expressive, high-contrast, bold                | mode: std/pro                     |
| `z_image`                 | Tongyi-MAI        | Super fast stylized                            | budget                            |
| `image_auto`              | Higgsfield        | Auto-routes to best model per prompt           | (smart fallback)                  |

**Naming gotcha:** Higgsfield's pricing page calls `nano_banana_flash` "Nano Banana 2" and `nano_banana_2` "Nano Banana Pro" — confusing but the API IDs are stable. The Ultra-plan unlimited model is `nano_banana_flash`.

## generate_image call shape

```json
{
  "params": {
    "model": "nano_banana_flash",
    "prompt": "Soft warm candlelight illuminates a polished brass thali heaped with golden khichdi, halwa, and pakoras. Rose petals scattered. Shallow depth of field, top-down 45 degree angle. Title text: 'Sunday Love Feast — Free for Everyone'. Sub: 'Sunday 12 May | 6 PM | Sri Krishna Mandir'.",
    "aspect_ratio": "1:1",
    "resolution": "2k",
    "medias": [
      {"role": "image", "value": "<UUID_from_media_upload>"}
    ]
  }
}
```

- `model` and `prompt` are required.
- `medias[]` only included for image-to-image / reference-anchored flows. Some models (`flux_kontext`) require it.
- Per-model params (`quality`, `resolution`, `mode`, `soul_id`, `budget`) go alongside `model`/`prompt`.
- The server returns generation_id; poll `show_generations` until status is `completed`, then download from the returned URL.

## Reference-image upload flow

```
1. media_upload(file_path | url) → returns media UUID
2. media_confirm(uuid) → confirms processing complete
3. generate_image with medias: [{role: "image", value: uuid}]
```

For batch reference workflows, upload once + reuse the UUID across multiple generations.

## Verify

```bash
python3 ~/Desktop/.claude/skills/ai-image-generator/scripts/check_mcp.py
```

Or directly call `balance` from Claude Code session — confirms email + credits + plan.

## Troubleshooting

- **Watermark visible** → Free tier — upgrade to Plus or Ultra; validate_output catches this
- **OAuth fails** → log into higgsfield.ai in browser first, then retry connector add
- **`insufficient_credits` mid-run** → top up plan; failed gens stay marked `[FAILED]` and re-run skips successful ones
- **`unsupported aspect`** → check the model's `aspect_ratios` via `models_explore action=get model_id=<id>`
- **Upload UUID not found mid-gen** → ensure `media_confirm` ran after `media_upload`
- **Higgsfield renames a tool or model** → re-run `models_explore action=list type=image` and update `MODEL_PARAMS` in `plan_generations.py`
