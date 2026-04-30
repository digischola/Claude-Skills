# Pipeline Architecture — End to End

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  INPUT                                                                       │
│  ──────                                                                      │
│  Form A: ad-copywriter `*-storyboard.json`                                   │
│  Form B: free-form markdown brief (client + format + mood + key shots)       │
└──────────────┬──────────────────────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 1 — Verify MCP + Load Context                                          │
│  ───────────────────────────────────                                         │
│  scripts/check_mcp.py        → verify Higgsfield connector connected         │
│  Read client wiki            → brand-identity.md, voice-guide.md             │
│  Read shared context         → analyst-profile, accuracy-protocol            │
│                                                                              │
│  ABORT if MCP not connected — point to references/mcp-setup.md               │
└──────────────┬──────────────────────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 2 — Parse Brief                                                        │
│  ────────────────────                                                        │
│  scripts/parse_brief.py                                                      │
│      ├─ Form A: load JSON, map ad-copywriter frames → scenes                 │
│      └─ Form B: expand markdown via reasoning → 4-6 scenes                   │
│  Inject brand tokens from client wiki (no invented metrics, blank-when-      │
│      uncertain per accuracy-protocol).                                       │
│                                                                              │
│  Output: _engine/working/<entry>/scene-plan.json                             │
└──────────────┬──────────────────────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 3 — Route Models                                                       │
│  ─────────────────────                                                       │
│  references/model-routing.md decision tree:                                  │
│      hero → Veo 3.1 (50cr)                                                   │
│      product → Seedance (25cr)                                               │
│      lifestyle → Kling 3.0 (6cr)  [default]                                  │
│      stylized → WAN 2.6 (30cr)                                               │
│      dialogue → Hailuo 02 (10cr)                                             │
│  Apply --force-model overrides if present.                                   │
│                                                                              │
│  Print credit estimate. ABORT > 500cr without --confirm-cost.                │
└──────────────┬──────────────────────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 4 — Generate Scenes (Higgsfield MCP)                                   │
│  ─────────────────────────────────────────                                   │
│  scripts/generate_scenes.py                                                  │
│      For each scene in scene-plan:                                           │
│          - Skip if scenes/<scene_id>.mp4 exists (idempotent)                 │
│          - If reference_image required → generate_image first                │
│          - Call text_to_video or image_to_video with model + prompt          │
│          - Save MP4 to scenes/<scene_id>.mp4                                 │
│          - Append manifest.json entry: model, prompt, seed, credits, ts      │
│          - On per-scene failure → mark [FAILED], continue                    │
│                                                                              │
│  Output: _engine/working/<entry>/scenes/01.mp4 ... NN.mp4                    │
│          _engine/working/<entry>/manifest.json                               │
└──────────────┬──────────────────────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 5 — Voiceover + BGM                                                    │
│  ────────────────────────                                                    │
│  scripts/clone_voice.py     → ChatterBox VO from manifest VO concat          │
│      (uses client voice-lock.md if available, else neutral default)          │
│  Auto-pick BGM from _engine/music/<mood-slug>.mp3                            │
│                                                                              │
│  Output: _engine/working/<entry>/voiceover.mp3                               │
│          _engine/working/<entry>/bgm.mp3                                     │
└──────────────┬──────────────────────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 6 — Stitch + Caption + Brand Chip                                      │
│  ─────────────────────────────────────                                       │
│  scripts/stitch_video.py                                                     │
│      - ffmpeg concat scenes in scene_id order (skip [FAILED])                │
│      - Mix VO at -14 LUFS over BGM at -18 LUFS                               │
│      - Whisper-transcribe VO → caption timing JSON                           │
│      - Render kinetic captions (reuse video-edit caption components)         │
│      - Overlay brand chip from client wiki brand-identity.md                 │
│      - Final encode at platform-native resolution                            │
│                                                                              │
│  Output: _engine/working/<entry>/draft.mp4                                   │
│                                                                              │
│  OPTIONAL polish flag --polish-with-video-edit:                              │
│    Hand draft.mp4 to video-edit ship phase for Apple-aesthetic treatment     │
└──────────────┬──────────────────────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 7 — Validate + Deliver + Feedback                                      │
│  ──────────────────────────────────────                                      │
│  scripts/validate_output.py                                                  │
│      Resolution match aspect    [CRITICAL]                                   │
│      Duration ±10% of brief     [CRITICAL]                                   │
│      Audio levels (-14 ± 1 LUFS) [CRITICAL]                                  │
│      No Higgsfield watermark    [CRITICAL — checks corner ROIs]              │
│      Captions don't overlap face bbox [WARN]                                 │
│      Manifest source labels complete  [WARN]                                 │
│                                                                              │
│  On clean pass:                                                              │
│      - Move draft.mp4 → Desktop/{Client}/{Project}/{date}-{name}.mp4         │
│      - python3 ~/.claude/scripts/build_outputs_index.py {Client}             │
│      - Append Learnings & Rules entry to SKILL.md                            │
│      - Append skill-corrections-log entry if any patches made                │
│                                                                              │
│  Output: Desktop/{Client}/{Project}/{YYYY-MM-DD}-{name}.mp4                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Idempotency rules

Re-running the skill on the same `<entry>` folder:

- Step 2 — overwrites scene-plan.json
- Step 4 — skips scenes whose MP4 exists, re-generates only missing/[FAILED] ones (saves credits)
- Step 5 — overwrites VO + BGM
- Step 6 — overwrites draft.mp4
- Step 7 — overwrites final delivery

Rationale: failed scene re-generation is the common case (Higgsfield occasionally returns errors). Wholesale re-run would burn credits unnecessarily.

## Failure modes

| Failure                          | Behavior                                            |
|----------------------------------|-----------------------------------------------------|
| MCP not connected                | Abort Step 1 with mcp-setup.md link                 |
| Brief validation fails           | Abort Step 2 with specific rule violation           |
| Credit budget exceeded           | Abort Step 3 with --confirm-cost prompt             |
| Single scene generation fails    | Mark [FAILED] in manifest, continue                 |
| All scenes fail                  | Abort Step 4 — no clips to stitch                   |
| ChatterBox VO fails              | Continue with silent track + warning                |
| validate_output CRITICAL         | Abort delivery, leave draft.mp4 in working/         |
| validate_output WARN             | Deliver with warning logged                         |

## Performance targets (v1)

- Step 4 (generation) ≈ 30-90s per scene depending on model
- Step 6 (stitch) ≈ 30-60s for 30s output
- Total wallclock for typical 4-scene 30s ad: 3-6 minutes
- Credits: 70-130 per video (default routing, Plus tier comfortable)
