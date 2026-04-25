#!/usr/bin/env bash
# ffmpeg_postpass.sh — fade in/out + final encode + thumbnail extract.
# Usage: ffmpeg_postpass.sh <final-raw.mp4> <output-path.mp4> [preset]
# Writes: <output-path.mp4> and a sibling <name>-thumb.jpg at 1.5s.

set -euo pipefail

SRC="${1:?usage: ffmpeg_postpass.sh <final-raw.mp4> <output-path.mp4> [preset]}"
OUT="${2:?usage: ffmpeg_postpass.sh <final-raw.mp4> <output-path.mp4> [preset]}"
PRESET="${3:-corporate-clean}"

command -v ffmpeg >/dev/null 2>&1  || { echo "ERROR: ffmpeg not found"; exit 1; }
command -v ffprobe >/dev/null 2>&1 || { echo "ERROR: ffprobe not found"; exit 1; }
[ -f "$SRC" ] || { echo "ERROR: input not found: $SRC"; exit 1; }

mkdir -p "$(dirname "$OUT")"

DUR=$(ffprobe -v quiet -print_format json -show_format "$SRC" | jq -r '.format.duration')
# Fade out starts 0.4s before end (12 frames at 30fps)
FADE_OUT_START=$(awk -v d="$DUR" 'BEGIN { printf "%.3f", (d > 0.6) ? d-0.4 : 0 }')

# Fade durations per preset: gen-z / course-sell / event-recap use snappier fades
case "$PRESET" in
  "gen-z-punchy"|"course-sell"|"event-recap")
    FADE_IN_DUR="0.1"; FADE_OUT_DUR="0.2" ;;
  "apple-premium"|"documentary-warm")
    FADE_IN_DUR="0.35"; FADE_OUT_DUR="0.5" ;;
  *)
    FADE_IN_DUR="0.2"; FADE_OUT_DUR="0.4" ;;
esac

# Loudness target per preset — re-apply in post-pass because render can shift levels
case "$PRESET" in
  "apple-premium"|"documentary-warm"|"corporate-clean"|"testimonial-trust")
    LUFS_TARGET="-16" ;;
  "gen-z-punchy"|"course-sell"|"event-recap"|"tech-demo")
    LUFS_TARGET="-14" ;;
  *)
    LUFS_TARGET="-16" ;;
esac

VFIL="fade=t=in:st=0:d=${FADE_IN_DUR},fade=t=out:st=${FADE_OUT_START}:d=${FADE_OUT_DUR}"
AFIL="afade=t=in:st=0:d=${FADE_IN_DUR},afade=t=out:st=${FADE_OUT_START}:d=${FADE_OUT_DUR},loudnorm=I=${LUFS_TARGET}:LRA=11:TP=-1.5"

ffmpeg -y -hide_banner -loglevel error -i "$SRC" \
  -vf "$VFIL" -af "$AFIL" \
  -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p -movflags +faststart \
  -c:a aac -b:a 192k \
  "$OUT"

# Thumbnail at 1.5s (or 10% into the video if shorter than 2s)
THUMB_TS=$(awk -v d="$DUR" 'BEGIN { printf "%.3f", (d < 2) ? d*0.1 : 1.5 }')
THUMB_PATH="${OUT%.mp4}-thumb.jpg"
ffmpeg -y -hide_banner -loglevel error -ss "$THUMB_TS" -i "$OUT" -frames:v 1 -q:v 2 "$THUMB_PATH"

echo "final:     $OUT"
echo "thumb:     $THUMB_PATH"
echo "duration:  $DUR"
