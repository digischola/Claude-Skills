# Storyboard / Scene Plan Schema

Two input formats accepted. Both normalize to the same `scene-plan.json` for downstream stages.

## Form A — ad-copywriter storyboard JSON (preferred)

ad-copywriter outputs `*-storyboard.json` per video creative. Expected shape:

```json
{
  "creative_id": "thrive-meta-reel-001",
  "client": "Thrive Retreats",
  "format": "9:16 reel, 30s",
  "voiceover_full": "Burned out from another quarter of grinding? ...",
  "music_mood": "calm uplifting",
  "frames": [
    {
      "frame_id": "01",
      "duration_sec": 3,
      "visual_prompt": "Wide aerial drone shot over Goa beach at sunrise, palm trees, ocean waves",
      "motion": "slow forward dolly",
      "text_overlay": "",
      "voiceover": "Burned out from another quarter of grinding?",
      "voice_direction": "warm, measured, slightly low",
      "music": "soft pad enters"
    },
    ...
  ]
}
```

`parse_brief.py` maps each `frame` to a scene:

| ad-copywriter field | scene-plan field    | Transform                              |
|--------------------|---------------------|----------------------------------------|
| frame_id           | scene_id            | Direct copy                            |
| duration_sec       | duration_sec        | Direct copy                            |
| visual_prompt      | prompt              | Direct copy + brand tokens injected    |
| motion             | motion_preset       | Mapped to Higgsfield preset names      |
| voiceover          | vo_text             | Direct copy                            |
| voice_direction    | vo_emotion_tags     | Mapped to ChatterBox `[firm]` etc      |
| music              | music_cue           | Direct copy                            |
| (inferred)         | model_choice        | Router picks per scene                 |
| (inferred)         | tags                | Inferred from prompt language          |

## Form B — free-form markdown brief

For one-off requests without a storyboard. Minimal viable brief (5 lines):

```markdown
client: Thrive Retreats
project: Nrsimha Caturdasi 2026 retreat ad
format: 9:16 reel, 30 seconds
mood: aspirational, calm, transformation
key shots:
  - wide drone over retreat venue at sunrise
  - yoga teacher demonstrating pose
  - guests laughing at communal meal
  - text reveal: "Book your reset" with URL
```

`parse_brief.py` calls Claude API (or in-session reasoning) to expand into a scene_plan.json: 4-6 scenes typically, prompts written in Higgsfield-friendly language (concrete nouns, camera motion verbs, lighting descriptors), VO derived from mood + key shots, default music_cue from mood.

## Output — scene-plan.json (canonical)

```json
{
  "creative_id": "thrive-meta-reel-001",
  "client": "Thrive Retreats",
  "project": "Nrsimha Caturdasi 2026",
  "format": {
    "aspect": "9:16",
    "total_duration_sec": 30,
    "fps": 30
  },
  "voiceover_full": "...",
  "music_mood": "calm uplifting",
  "estimated_credits": 72,
  "scenes": [
    {
      "scene_id": "01",
      "duration_sec": 3,
      "tags": ["hero", "establishing"],
      "model_choice": "veo-3.1",
      "model_credits": 50,
      "prompt": "Wide aerial drone shot over Goa beach at sunrise, palm trees swaying, golden hour, cinematic, 9:16",
      "motion_preset": "slow_forward_dolly",
      "reference_image": null,
      "seed": 42,
      "vo_text": "Burned out from another quarter of grinding?",
      "vo_emotion_tags": ["measured", "warm"],
      "music_cue": "soft pad enters",
      "source": "[INFERRED-from-brief]"
    },
    {
      "scene_id": "02",
      "duration_sec": 4,
      "tags": ["lifestyle"],
      "model_choice": "kling-3.0",
      "model_credits": 6,
      "prompt": "...",
      ...
    }
  ]
}
```

## Required fields

Per scene:
- `scene_id` — `01`, `02`, ... zero-padded
- `duration_sec` — integer, 3-10 range (Higgsfield clip max ≈ 8-10s)
- `prompt` — text-to-video prompt, ≤ 500 chars
- `model_choice` — one of: `veo-3.1`, `sora-2`, `kling-3.0`, `hailuo-02`, `seedance-2.0`, `wan-2.6`
- `aspect` — inherited from format unless scene overrides

Optional:
- `reference_image` — path to image for image-to-video
- `seed` — for reproducibility (random if omitted)
- `vo_text` — voiceover for this scene window
- `motion_preset` — Higgsfield motion library preset name
- `negative_prompt` — things to exclude

## Validation rules

- Total `sum(scenes.duration_sec)` must equal `format.total_duration_sec` ± 1s
- `voiceover_full` must concat to ≤ `total_duration_sec × 2.7` words (roughly 160wpm cap)
- Every scene's `prompt` must be present and non-empty
- `estimated_credits` must match sum of scene credits

`parse_brief.py` runs validation and refuses to write the plan if any rule fails.
