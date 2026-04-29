# Voice Cloning — F5-TTS Setup + Usage

Free, local, unlimited voice clone of Mayank's voice for Reel voiceovers.
No APIs, no monthly caps, no ban risk. Runs on M-series Mac via MPS backend.

## One-time setup (3 min recording + ~5 min install)

### 1. Record your voice samples

```bash
python3 visual-generator/scripts/enroll_voice.py
```

Opens a dark-mode browser page at `http://127.0.0.1:8766`. Read 10 varied
sentences, Mac mic captures via MediaRecorder API, each sample auto-converted
to 24kHz mono WAV and saved to `brand/_engine/voice-samples/`. ~3 min total.

Sentences cover varied tone — greeting, credentials, data, rhetorical question,
punchy insight, measured reframe — so F5-TTS learns Mayank's full range, not
just a neutral baseline.

After all 10 recorded, `brand/_engine/wiki/voice-lock.md` auto-writes with transcripts +
metadata. The wizard self-shuts-down.

Status check / re-enrollment:

```bash
python3 visual-generator/scripts/enroll_voice.py --status
python3 visual-generator/scripts/enroll_voice.py --reset    # wipe + start over
```

### 2. Install F5-TTS (first use only)

```bash
python3 visual-generator/scripts/clone_voice.py --install-check
```

Installs F5-TTS via pip. First synthesis downloads model weights (~1.3GB) from
HuggingFace. After that, offline + unlimited.

## Per-Reel usage (automated during Sunday ritual)

### Direct text → MP3

```bash
python3 clone_voice.py --text "Your VO script" --out /tmp/vo.mp3
```

### From a draft file (integrates with scheduler-publisher queue)

```bash
python3 clone_voice.py --draft /path/to/draft.md
```

Auto-extracts VO script from frontmatter `vo_script:` field OR body section
labeled `## Voiceover`. Saves MP3 to `brand/queue/assets/<entry_id>/voiceover.mp3`
(standard asset path — review_queue.py auto-detects and displays it inline).

### Reference sample selection

Default: uses `sample-01.wav` (greeting, neutral-warm tone) as the reference.
Override per-VO with `--ref-sample N` (1-10) to match the mood of the script:

| Sample | Best for |
|---|---|
| 01 Greeting | neutral intro / bio reels |
| 02 Credentials | authority-led hooks |
| 03 Brutal truth | contrarian hooks |
| 04 Data audit | stat-heavy insights |
| 05 Rhetorical Q | question-format reels |
| 06 Numbers contrast | comparison data |
| 07 Personal pivot | story-arc reels |
| 08 Punchy | energetic/fast reels |
| 09 Value reframe | educational reels |
| 10 CTA | direct call-to-action endings |

Claude can pick automatically based on the draft's `hook_category`.

## How it integrates with the flow

```
post-writer (draft with vo_script in frontmatter, for Reel slots)
   ↓
visual-generator/generate_tow_prompts.py (Phase 3 — not built yet)
   generates: Nano Banana image prompts + Veo video prompts + VO script
   ↓
clone_voice.py --draft <draft>
   auto-generates voiceover.mp3 from voice samples (no user step)
   ↓
brand/queue/assets/<entry_id>/voiceover.mp3
   ↓
review_queue.py (existing, already displays MP3 with <audio controls>)
   ↓  user approves voice quality
apply_calendar + scheduler-publisher (unchanged)
```

## Quality notes

- F5-TTS output is ~90% of ElevenLabs Premium quality at zero cost.
- Expected timing: 10-30 seconds to synthesize a 30-second VO on M-series.
- First synthesis is slower (~60 sec) because the model loads into memory.
- Emotion tags in the script (e.g., `[excited]`, `[thoughtful]`) are partially
  respected — F5-TTS inherits tone from the reference sample, so the right
  reference-sample selection matters more than emotion tags.

## Troubleshooting

**"No module named f5_tts"**
```bash
python3 clone_voice.py --install-check
# OR
pip3 install --user f5-tts
```

**Model download fails / timeout**
First synthesis downloads from HuggingFace. If on a slow connection, run:
```bash
python3 -c "from f5_tts.api import F5TTS; F5TTS()"
```
Which loads the model once so subsequent runs are cached.

**Voice clone sounds off**
- Re-enroll with higher-quality samples (quieter room, better mic).
- Pick a different `--ref-sample` that matches the script's mood.
- Shorten the VO — F5-TTS quality drops on very long (>45 sec) outputs.

## Cross-skill impact

- No impact on LI text posts, carousels, or any non-Reel content.
- When a Reel is scheduled, visual-generator invokes clone_voice.py as part
  of brief generation. The MP3 lands in the assets folder where review_queue
  already picks it up for human approval.
- scheduler-publisher (manual.py) reveals the MP3 alongside images/videos at
  post time — Mayank drags it into IG/LI composer along with the video.
