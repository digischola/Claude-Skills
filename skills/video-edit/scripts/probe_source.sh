#!/usr/bin/env bash
# probe_source.sh — inspect a source video, emit source-probe.json
# Usage: probe_source.sh <source.mp4> <output-dir>
# Writes: <output-dir>/source-probe.json

set -euo pipefail

SRC="${1:?usage: probe_source.sh <source.mp4> <output-dir>}"
OUT_DIR="${2:?usage: probe_source.sh <source.mp4> <output-dir>}"

mkdir -p "$OUT_DIR"
OUT="$OUT_DIR/source-probe.json"

if [ ! -f "$SRC" ]; then
  echo "ERROR: source file not found: $SRC" >&2
  exit 1
fi

command -v ffprobe >/dev/null 2>&1 || { echo "ERROR: ffprobe not found"; exit 1; }

STREAMS=$(ffprobe -v quiet -print_format json -show_streams -show_format "$SRC")

# Extract primary video stream + format
W=$(echo "$STREAMS" | jq -r '[.streams[] | select(.codec_type=="video")][0].width // 0')
H=$(echo "$STREAMS" | jq -r '[.streams[] | select(.codec_type=="video")][0].height // 0')
FPS_FRAC=$(echo "$STREAMS" | jq -r '[.streams[] | select(.codec_type=="video")][0].r_frame_rate // "0/1"')
FPS=$(echo "$FPS_FRAC" | awk -F/ '{ if ($2>0) printf "%.3f", $1/$2; else print 0 }')
DUR=$(echo "$STREAMS" | jq -r '.format.duration // "0"')
BITRATE=$(echo "$STREAMS" | jq -r '.format.bit_rate // "0"')
ACHAN=$(echo "$STREAMS" | jq -r '[.streams[] | select(.codec_type=="audio")][0].channels // 0')
ACODEC=$(echo "$STREAMS" | jq -r '[.streams[] | select(.codec_type=="audio")][0].codec_name // "none"')

# Aspect label
ASPECT_LABEL="other"
if [ "$W" -gt 0 ] && [ "$H" -gt 0 ]; then
  RATIO=$(awk -v w="$W" -v h="$H" 'BEGIN { printf "%.4f", w/h }')
  # 9:16 = 0.5625, 16:9 = 1.7778, 1:1 = 1.0, 4:5 = 0.8
  ASPECT_LABEL=$(awk -v r="$RATIO" 'BEGIN {
    if (r >= 0.55 && r <= 0.58) print "9:16";
    else if (r >= 1.75 && r <= 1.80) print "16:9";
    else if (r >= 0.98 && r <= 1.02) print "1:1";
    else if (r >= 0.78 && r <= 0.82) print "4:5";
    else print "other";
  }')
fi

# Target render dims routing
case "$ASPECT_LABEL" in
  "9:16") TW=1080; TH=1920 ;;
  "16:9") TW=1920; TH=1080 ;;
  "1:1")  TW=1080; TH=1080 ;;
  "4:5")  TW=1080; TH=1350 ;;
  *)      TW="$W"; TH="$H" ;;
esac

# Audio loudness (LUFS) — only if audio track exists
LUFS="null"
if [ "$ACHAN" -gt 0 ]; then
  LUFS_RAW=$(ffmpeg -hide_banner -nostats -i "$SRC" -af "loudnorm=print_format=json" -f null - 2>&1 \
    | awk -F'"' '/"input_i"/ { print $4; exit }')
  # Validate: must parse as a number
  if [ -n "$LUFS_RAW" ] && [ "$LUFS_RAW" != "-inf" ]; then
    if printf '%f' "$LUFS_RAW" >/dev/null 2>&1; then
      LUFS="$LUFS_RAW"
    fi
  fi
fi

# Silent segment detection — segments >0.6s below -35 dB
SILENCE_RAW=$(ffmpeg -hide_banner -nostats -i "$SRC" -af "silencedetect=noise=-35dB:d=0.6" -f null - 2>&1 || true)
SILENCE_JSON=$(echo "$SILENCE_RAW" | awk '
  /silence_start:/ { s=$NF; next }
  /silence_end:/   { printf "{\"start\":%s,\"end\":%s},", s, $5 }
' | sed 's/,$//')
SILENCE_JSON="[${SILENCE_JSON:-}]"

# Assemble output JSON
cat > "$OUT" <<JSON
{
  "source_path": "$SRC",
  "duration_sec": $DUR,
  "width": $W,
  "height": $H,
  "fps": $FPS,
  "bitrate_bps": $BITRATE,
  "aspect_label": "$ASPECT_LABEL",
  "target_render_dims": { "width": $TW, "height": $TH },
  "audio": {
    "channels": $ACHAN,
    "codec": "$ACODEC",
    "lufs": $LUFS
  },
  "silent_segments": $SILENCE_JSON
}
JSON

echo "$OUT"
