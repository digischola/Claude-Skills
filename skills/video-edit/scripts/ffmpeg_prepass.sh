#!/usr/bin/env bash
# ffmpeg_prepass.sh — trim silent segments + normalize audio on a source video.
# Usage: ffmpeg_prepass.sh <source.mp4> <probe.json> <output-dir> [preset]
# Writes: <output-dir>/prepped.mp4 + <output-dir>/cuts.json
# Preset (optional): apple-premium | gen-z-punchy | corporate-clean | documentary-warm |
#                    tech-demo | testimonial-trust | course-sell | event-recap
# Preset affects loudness target and LUT choice. Default = corporate-clean.

set -euo pipefail

SRC="${1:?usage: ffmpeg_prepass.sh <source.mp4> <probe.json> <output-dir> [preset]}"
PROBE="${2:?usage: ffmpeg_prepass.sh <source.mp4> <probe.json> <output-dir> [preset]}"
OUT_DIR="${3:?usage: ffmpeg_prepass.sh <source.mp4> <probe.json> <output-dir> [preset]}"
PRESET="${4:-corporate-clean}"

mkdir -p "$OUT_DIR"
OUT="$OUT_DIR/prepped.mp4"
CUTS_JSON="$OUT_DIR/cuts.json"

command -v ffmpeg >/dev/null 2>&1 || { echo "ERROR: ffmpeg not found"; exit 1; }
command -v jq >/dev/null 2>&1 || { echo "ERROR: jq not found"; exit 1; }
[ -f "$SRC" ]   || { echo "ERROR: source not found: $SRC"; exit 1; }
[ -f "$PROBE" ] || { echo "ERROR: probe not found: $PROBE"; exit 1; }

# Loudness target per preset
case "$PRESET" in
  "apple-premium"|"documentary-warm"|"corporate-clean"|"testimonial-trust")
    LUFS_TARGET="-16" ;;
  "gen-z-punchy"|"course-sell"|"event-recap"|"tech-demo")
    LUFS_TARGET="-14" ;;
  *)
    LUFS_TARGET="-16" ;;
esac

DUR=$(jq -r '.duration_sec' "$PROBE")
SILENCE_COUNT=$(jq -r '.silent_segments | length' "$PROBE")

# Build keep-segments list (inverse of silent segments).
# Rule: only trim silence >0.6s AND preserve a 0.15s head/tail buffer so speech doesn't clip.
python3 - "$PROBE" "$DUR" > "$CUTS_JSON" <<'PY'
import json, sys
probe_path, total_dur = sys.argv[1], float(sys.argv[2])
with open(probe_path) as f:
    probe = json.load(f)
silences = probe.get("silent_segments", [])
# sort + clamp with head/tail buffer
BUFFER = 0.15
clean_silences = []
for s in silences:
    start = max(float(s["start"]) + BUFFER, 0.0)
    end   = max(float(s["end"])   - BUFFER, start)
    if end - start >= 0.6:
        clean_silences.append({"start": round(start,3), "end": round(end,3)})
# invert to keeps
keeps, cursor = [], 0.0
for s in clean_silences:
    if s["start"] > cursor:
        keeps.append({"start": round(cursor,3), "end": round(s["start"],3)})
    cursor = s["end"]
if cursor < total_dur:
    keeps.append({"start": round(cursor,3), "end": round(total_dur,3)})
# sanity: if no silences or keeps empty, keep the whole thing
if not keeps:
    keeps = [{"start": 0.0, "end": round(total_dur,3)}]
json.dump({
    "removed_silence_segments": clean_silences,
    "keep_segments": keeps,
    "original_duration": round(total_dur,3),
    "kept_duration": round(sum(k["end"]-k["start"] for k in keeps),3),
}, sys.stdout, indent=2)
PY

KEPT_DUR=$(jq -r '.kept_duration' "$CUTS_JSON")

# Build ffmpeg concat filter from keep segments
KEEPS=$(jq -c '.keep_segments' "$CUTS_JSON")

if [ "$SILENCE_COUNT" = "0" ] || [ "$KEEPS" = "[]" ]; then
  # No silence to trim — re-encode video with DENSE keyframes (every frame)
  # so the hyperframes renderer can seek without freezes, plus normalize audio.
  ffmpeg -y -hide_banner -loglevel error -i "$SRC" \
    -af "loudnorm=I=${LUFS_TARGET}:LRA=11:TP=-1.5" \
    -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p \
    -r 30 -g 30 -keyint_min 30 -movflags +faststart \
    -c:a aac -b:a 192k "$OUT"
else
  # Build select and aselect expressions + concat with loudness normalization
  VEXPR=$(jq -r '.keep_segments | map("between(t,\(.start),\(.end))") | join("+")' "$CUTS_JSON")
  FILTER="[0:v]select='${VEXPR}',setpts=N/FRAME_RATE/TB[v];[0:a]aselect='${VEXPR}',asetpts=N/SR/TB,loudnorm=I=${LUFS_TARGET}:LRA=11:TP=-1.5[a]"

  ffmpeg -y -hide_banner -loglevel error -i "$SRC" \
    -filter_complex "$FILTER" \
    -map "[v]" -map "[a]" \
    -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p \
    -r 30 -g 30 -keyint_min 30 -movflags +faststart \
    -c:a aac -b:a 192k "$OUT"
fi

echo "prepped: $OUT"
echo "cuts:    $CUTS_JSON"
echo "kept_duration: $KEPT_DUR"
