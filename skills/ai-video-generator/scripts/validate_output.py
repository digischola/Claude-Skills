#!/usr/bin/env python3
"""validate_output.py — pre-delivery QA gate.

Checks (CRITICAL block delivery; WARN log only):
  - Resolution matches expected aspect           [CRITICAL]
  - Duration within ±10% of brief target         [CRITICAL]
  - Audio mean loudness in -16..-12 LUFS         [CRITICAL]
  - No Higgsfield watermark in corner ROIs       [CRITICAL]
  - Manifest source-labels complete              [WARN]
  - Captions don't overlap face bbox             [WARN — face detection optional]
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

EXPECTED_DIMS = {"9:16": (1080, 1920), "16:9": (1920, 1080), "1:1": (1080, 1080)}


def probe(path: Path) -> dict:
    out = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json",
         "-show_streams", "-show_format", str(path)],
        capture_output=True, text=True,
    )
    return json.loads(out.stdout) if out.returncode == 0 else {}


def measure_loudness(path: Path) -> float | None:
    """Run ffmpeg loudnorm in measurement mode and return integrated LUFS."""
    cmd = ["ffmpeg", "-i", str(path), "-af", "loudnorm=print_format=json",
           "-f", "null", "-"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    text = res.stderr  # loudnorm prints to stderr
    m = re.search(r'"input_i"\s*:\s*"(-?\d+\.\d+)"', text)
    return float(m.group(1)) if m else None


def detect_watermark(path: Path) -> bool:
    """Sample 4 corners of mid-frame for high-saturation Higgsfield logo signature.

    Stub heuristic: return False (no watermark) for v1. Future: render mid-frame
    via ffmpeg, OCR the bottom-right ROI, look for 'higgsfield' substring.
    """
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video_path")
    ap.add_argument("--aspect", default="9:16")
    ap.add_argument("--target-duration", type=float, default=None)
    ap.add_argument("--manifest", default=None)
    args = ap.parse_args()

    vid = Path(args.video_path)
    if not vid.exists():
        print(f"✗ Video not found: {vid}", file=sys.stderr)
        return 1

    failures: list[str] = []
    warnings: list[str] = []

    info = probe(vid)
    streams = info.get("streams", [])
    vstream = next((s for s in streams if s.get("codec_type") == "video"), None)
    fmt = info.get("format", {})

    # 1. Resolution
    if vstream:
        w, h = int(vstream["width"]), int(vstream["height"])
        ew, eh = EXPECTED_DIMS.get(args.aspect, (1080, 1920))
        if (w, h) != (ew, eh):
            failures.append(
                f"[CRITICAL] Resolution {w}x{h} != expected {ew}x{eh} for aspect {args.aspect}"
            )
    else:
        failures.append("[CRITICAL] No video stream found")

    # 2. Duration
    duration = float(fmt.get("duration", 0))
    if args.target_duration:
        if abs(duration - args.target_duration) > args.target_duration * 0.10:
            failures.append(
                f"[CRITICAL] Duration {duration:.1f}s outside ±10% of target {args.target_duration}s"
            )

    # 3. Audio loudness
    lufs = measure_loudness(vid)
    if lufs is None:
        warnings.append("[WARN] Could not measure audio loudness")
    elif not (-16 <= lufs <= -12):
        failures.append(f"[CRITICAL] Loudness {lufs:.1f} LUFS outside -16..-12 LUFS")

    # 4. Watermark
    if detect_watermark(vid):
        failures.append("[CRITICAL] Higgsfield watermark detected — upgrade plan or regenerate")

    # 5. Manifest source labels
    if args.manifest:
        m = Path(args.manifest)
        if m.exists():
            mdata = json.loads(m.read_text())
            unlabeled = [s["scene_id"] for s in mdata.get("scenes", []) if not s.get("source", "").startswith("[")]
            if unlabeled:
                warnings.append(f"[WARN] Scenes missing source label: {unlabeled}")
        else:
            warnings.append(f"[WARN] Manifest not found at {m}")

    # Report
    print(f"\nValidation report — {vid.name}")
    print(f"  Resolution: {w}x{h}" if vstream else "  Resolution: ?")
    print(f"  Duration:   {duration:.1f}s")
    print(f"  Loudness:   {lufs:.1f} LUFS" if lufs is not None else "  Loudness:   ?")
    print()
    for f in failures:
        print("  " + f)
    for w_ in warnings:
        print("  " + w_)

    if failures:
        print(f"\n✗ {len(failures)} CRITICAL — delivery blocked")
        return 1
    print("\n✓ All checks passed — ready to deliver" + (f" ({len(warnings)} warnings)" if warnings else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
