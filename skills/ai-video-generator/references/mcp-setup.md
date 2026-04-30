# Higgsfield MCP Setup

The skill cannot run without the Higgsfield MCP connector. **Connector confirmed live on Mayank's Claude Code as of 2026-04-30.**

## Install (Claude Code)

```bash
claude mcp add --transport http higgsfield https://mcp.higgsfield.ai/mcp
```

Restart Claude Code; on first call, the MCP prompts for OAuth — log in with the Higgsfield account.

## Verified tool surface (server ID `b39cf66e-...`)

The MCP exposes 13 tools. The skill uses these:

| Tool                  | Purpose                                                        |
|-----------------------|----------------------------------------------------------------|
| `balance`             | Check credits + plan tier (no args)                            |
| `models_explore`      | Discover model IDs, durations, aspect ratios, required medias  |
| `generate_video`      | **Single tool for text-to-video AND image-to-video.** Mode determined by `medias[]` array (role: `start_image` / `end_image` / `image`) |
| `generate_image`      | Generate reference stills (Soul / Flux / Nano Banana Pro)      |
| `media_upload`        | Upload local image to use as `start_image` reference           |
| `show_generations`    | List past generations                                          |
| `transactions`        | Credit transaction history                                     |
| `select_workspace`    | Switch active workspace                                        |
| `job_display`         | Display a specific job                                         |

The full list also includes: `list_workspaces`, `media_confirm`, `show_medias`, `show_marketing_studio`.

## Plan + credits — known constraint

**Mayank's account verified 2026-04-30: Free plan, 0 credits.** Generation will not run until either:

1. **Upgrade to Plus tier ($39/mo, 1,000 credits)** — recommended baseline
2. **Buy credits a-la-carte** if Higgsfield exposes that on free tier

| Plan        | Monthly | Credits | Veo 3.1 clips | Kling 3.0 clips | Verdict for client work |
|-------------|---------|---------|---------------|-----------------|-------------------------|
| Free        | $0      | 150     | ~3            | ~25             | Test only — watermarked |
| Starter     | $15     | 200     | ~3-5          | ~33             | Too credit-starved      |
| **Plus**    | **$39** | **1,000** | **~17-25**  | **~166**        | **Recommended baseline**|
| Ultra       | $99     | 3,000   | ~50-75        | ~500            | Only if shipping weekly |

## Verified video model IDs (from `models_explore`)

These are the exact strings that go in `params.model`:

| Model ID                | Provider   | Best for                                 | Duration constraints  |
|-------------------------|------------|------------------------------------------|-----------------------|
| `veo3_1`                | Google     | Ultra-realistic hero, top cinematic      | 4, 6, or 8 sec        |
| `veo3_1_lite`           | Google     | Budget Veo for batch B-roll              | 4, 6, or 8 sec        |
| `veo3`                  | Google     | Cinematic, requires `start_image`        | (no enum)             |
| `kling3_0`              | Kling      | Default lifestyle B-roll, multi-shot     | 3-15 sec              |
| `kling2_6`              | Kling      | Cinematic motion + advanced physics      | 5 or 10 sec           |
| `minimax_hailuo`        | Hailuo     | Natural physics, facial emotion          | 6 or 10 sec           |
| `seedance_2_0`          | Bytedance  | Reference-driven product, multi-SKU      | 4-15 sec              |
| `seedance_1_5`          | Bytedance  | Reliable motion, versatile               | 4, 8, 12 sec          |
| `wan2_6`                | Wan        | Stylized, REQUIRES `start_image`         | 5, 10, 15 sec         |
| `wan2_7`                | Wan        | Audio-synced, character-consistent       | 2-15 sec              |
| `cinematic_studio_3_0`  | Higgsfield | Most advanced cinema-grade (premium)     | 4-15 sec              |
| `marketing_studio_video`| Higgsfield | **TikTok/Reels ads with UGC modes**      | (custom)              |
| `grok_video`            | xAI        | T2V + I2V with audio                     | 1-15 sec              |

**Marketing Studio modes** (`mode` param): `UGC`, `Tutorial`, `Unboxing`, `Hyper Motion`, `Product Review`, `TV Spot`, `Wild Card`, `UGC Virtual Try On`, `Pro Virtual Try On`. This is purpose-built for ad work — use it for any UGC-style client ad before reaching for Kling.

**No Sora 2** in Higgsfield's catalog. If a client wants Sora-style cinematic narrative, the closest substitutes are `cinematic_studio_3_0` or `veo3_1`.

## generate_video call shape

```json
{
  "params": {
    "model": "kling3_0",
    "prompt": "Wide aerial drone shot over Goa beach at sunrise...",
    "aspect_ratio": "9:16",
    "duration": 5,
    "medias": [
      {"role": "start_image", "value": "<UUID_or_URL>"}
    ]
  }
}
```

- `model` and `prompt` are required.
- `medias[]` only included for image-to-video flows or when the model requires it (`wan2_6`, `veo3`).
- Per-model params (e.g. `quality`, `resolution`, `mode`, `genre`, `sound`) go alongside `model`/`prompt` inside `params` — see `MODEL_PARAMS` in `scripts/generate_scenes.py`.
- The server returns `adjustments` if it had to fall back (e.g. unsupported aspect → closest match, unsupported duration → nearest allowed).

## Verify

```bash
python3 ~/Desktop/.claude/skills/ai-video-generator/scripts/check_mcp.py
```

Or directly call `balance` from Claude Code session — confirms email + credits + plan in one shot.

## Troubleshooting

- **0 credits** → upgrade to Plus or buy a-la-carte; Free tier credits insufficient for client work + watermarked
- **OAuth fails** → log into higgsfield.ai in browser first, then retry connector add
- **`insufficient_credits` mid-run** → top up plan; failed scenes stay marked `[FAILED]` and re-run skips successful ones (idempotent)
- **`unsupported aspect`** → check the model's `aspect_ratios` via `models_explore action=get model_id=<id>`
- **`unsupported duration`** → server clamps; check the model's `durations` or `duration_range`
- **Higgsfield renames a tool or model** → re-run `models_explore action=list type=video` and update `MODEL_PARAMS` in `generate_scenes.py`
