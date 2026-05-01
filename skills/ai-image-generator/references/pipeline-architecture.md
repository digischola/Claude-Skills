# Pipeline Architecture — End-to-End Dataflow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ INPUTS                                                                      │
│  • ad-copywriter image-prompts.json   (Form A — preferred)                  │
│  • free-form concept board markdown   (Form B)                              │
│  • standalone brief (3 questions)     (Form C)                              │
│  • OPTIONAL reference image folder    ({client}/Reference Library/)         │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 1 — check_mcp.py                                                       │
│  Verify Higgsfield MCP connected, plan tier, credits available.             │
│  Abort loud if not connected or insufficient credits.                       │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 2 — inventory_references.py  (only if folder provided)                 │
│  Walk folder → hash + dedup → upload each via media_upload → media_confirm  │
│  → Claude in-session tags each (subject_type, sacred, consent_status, etc.) │
│  → reference-manifest.json                                                  │
│  Religious-brand guardrails fire automatically on deity/scripture/face.     │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 3 — parse_brief.py                                                     │
│  Read input form (A/B/C) + reference-manifest.json + client wiki +          │
│  shared-context/copywriting-rules.md.                                       │
│  Build concept-board.json: concepts × variations × aspects × model_choice.  │
│  Auto-attach references per auto_attach_to_concepts_with_intent.            │
│  Voice-check every prompt + creative_direction + on-image text.             │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 4 — model routing (inside parse_brief.py)                              │
│  Apply references/model-routing.md decision tree to each variation.         │
│  Default tier = nano_banana_flash (unlimited on Ultra).                     │
│  Premium tier escalation per intent (cover_slide / hero / product / sacred).│
│  Compute expected_credits.                                                  │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 5 — plan_generations.py                                                │
│  Read concept-board.json. For each variation, build MCP call entry:         │
│  { mcp_tool: "generate_image", params: { model, prompt, aspect_ratio,       │
│    resolution, medias: [{role: "image", value: <ref_uuid>}] } }             │
│  Skip variations whose output PNG already exists (idempotent).              │
│  Print budget preview + ask --confirm-cost if needed.                       │
│  Output: mcp-call-queue.json                                                │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 6 — Claude in-session: Higgsfield MCP calls                            │
│  Read mcp-call-queue.json. For each PENDING entry:                          │
│   1. Call generate_image with the queued args                               │
│   2. Capture generation_id                                                  │
│   3. Poll show_generations every 60-90s until status == "completed"         │
│   4. Run download_outputs.py to fetch the PNG to creatives/                 │
│   5. Append manifest.json entry (model, prompt, seed, refs, credits)        │
│   6. On per-gen failure → mark [FAILED] in manifest, continue queue         │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 7 — validate_output.py + analyze_outputs.py + render_dashboard.py      │
│  • validate_output.py: aspect, dimensions, watermark, color profile, size   │
│  • Sacred composite step (if any sacred references): composite_sacred.py    │
│  • analyze_outputs.py: Claude in-session reads each PNG, scores 5 dims      │
│    (brand-voice fit / visual hierarchy / CTA readability / sector           │
│     sensitivity / variation differentiation), writes scores.json            │
│  • render_dashboard.py: assemble dashboard.html (brand-themed, side-by-side │
│    variants with scores, "use this one" buttons), save to client folder root│
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 8 — Mayank reviews dashboard, picks winners                            │
│  Click "use this one" buttons → write picks.json                            │
│  Run finalize.py (or manual mv) → winners moved to:                         │
│    Desktop/{Client}/{Project}/creatives/{YYYY-MM-DD}-{concept-name}/        │
│  Update wiki log + outputs index                                            │
│  Flag downstream: campaign-setup ready to consume                           │
└─────────────────────────────────────────────────────────────────────────────┘
```

## File flow per step

| Step | Reads                                                        | Writes                                                                    |
|------|--------------------------------------------------------------|---------------------------------------------------------------------------|
| 1    | (Higgsfield MCP balance call)                                | (stdout only)                                                             |
| 2    | reference folder, consent.csv (if exists)                    | _engine/working/<entry>/reference-manifest.json                           |
| 3    | input form, reference-manifest.json, wiki, shared-context    | _engine/working/<entry>/concept-board.json                                |
| 4    | (inside parse_brief.py — no separate file IO)                | (concept-board.json populated with model_choice + expected_credits)       |
| 5    | concept-board.json                                           | _engine/working/<entry>/mcp-call-queue.json                               |
| 6    | mcp-call-queue.json                                          | _engine/working/<entry>/creatives/*.png + manifest.json                   |
| 7    | creatives/*.png + manifest.json                              | _engine/working/<entry>/scores.json + dashboard.html (folder root)        |
| 8    | dashboard.html picks                                         | Desktop/{Client}/{Project}/creatives/<date-name>/*.png                    |

## Idempotency contract

The whole pipeline is idempotent on re-run with the same concept-board.json:

- Step 2 skips reference images already uploaded (sha256 match)
- Step 5 skips variations whose output PNG already exists
- Step 6 only generates PENDING entries
- Step 7 re-scores all extant PNGs (may flag new issues if validator updated)
- Step 8 is manual

Forced re-gen: delete the target PNG OR delete its manifest entry, re-run from Step 5.

## Failure handling

| Failure                                | Behavior                                                  |
|----------------------------------------|-----------------------------------------------------------|
| MCP not connected                      | Step 1 aborts with setup link                             |
| Insufficient credits                   | Step 1 warns; Step 6 aborts on first credit error         |
| Reference upload fails                 | Step 2 retries 2x, then marks `upload_failed: true`       |
| Voice-check fails                      | Step 3 marks variation `voice_check: FAIL`; Step 5 skips  |
| Model returns generation error         | Step 6 marks `[FAILED]` in manifest, continues            |
| Aspect mismatch (model doesn't support)| Step 5 either falls back per matrix or fails              |
| Watermark detected on output           | Step 7 CRITICAL — re-queue OR escalate plan tier issue    |
| Sacred reference + AI redraw attempt   | Step 5 hard-blocks, requires composite-into-design path   |

## Coordination boundaries

This skill **stops at delivery to client folder root**. It does NOT:

- Write Meta / Google Ads bulk-import CSVs (that's `campaign-setup`)
- Schedule or publish creatives (that's `scheduler-publisher`)
- Edit photographs (use Photoshop / external tools — this skill generates, doesn't retouch)
- Generate video (that's `ai-video-generator`)
- Write the ad copy itself (that's `ad-copywriter`)

It DOES expose its outputs in a structure that downstream skills can consume directly:

```
Desktop/{Client}/{Project}/creatives/{YYYY-MM-DD}-{concept-name}/
├── 1x1.png            ← campaign-setup picks this for Meta feed 1:1 placement
├── 4x5.png            ← campaign-setup picks this for Meta feed 4:5 placement
├── 9x16.png           ← campaign-setup picks this for stories
└── manifest.json      ← model + prompt + credits provenance
```
