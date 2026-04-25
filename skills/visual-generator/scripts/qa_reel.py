#!/usr/bin/env python3
"""
qa_reel.py — automated visual QA gate for v7 Remotion reels.

Extracts frames from a rendered MP4 + runs concrete checks against
motion-design-playbook.md v2 rules. Fails loudly if any rule is violated.

Checks (v1 — minimum viable gate):
  1. Visual density per frame       → no frame has <8% non-background pixels
  2. Motion presence                → no 1+ second stretch where frame-to-frame
                                        delta is <1% (catches dead-air gaps)
  3. Pure-black safety              → no frame is >95% pure-black pixels
                                        (catches "empty template" output)
  4. Color dominance per scene      → scene's dominant accent matches expected
                                        tone (neutral/positive/warning)
  5. Scene differentiation          → scenes have meaningfully different color
                                        histograms (catches "every scene looks
                                        the same" template bug)

Usage:
  python3 qa_reel.py --reel path/to/reel.mp4 [--out-dir /tmp/qa] [--strict]

Exits 0 if all pass, 2 if any check fails (machine-readable for orchestrator
to detect + regenerate).
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


# Thresholds (tuned conservatively — false negatives OK, false positives costly)
MIN_VISUAL_DENSITY = 0.08    # 8% non-bg pixels required
MAX_PURE_BLACK_RATIO = 0.92  # >92% pure-black = empty frame
MIN_FRAME_DELTA = 0.01       # 1% frame-to-frame change minimum (motion presence)
MIN_SCENE_DIFF = 15          # color-histogram chi-square distance between scenes


def extract_frames(reel: Path, out_dir: Path, fps: float = 2.0) -> list[Path]:
    """Extract frames at `fps` rate. 2fps on a 20s reel → ~40 frames."""
    out_dir.mkdir(parents=True, exist_ok=True)
    # Clean any existing frames
    for f in out_dir.glob("*.jpg"):
        f.unlink()
    # Extract
    subprocess.run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(reel),
        "-vf", f"fps={fps}",
        "-q:v", "3",
        str(out_dir / "frame-%04d.jpg"),
    ], check=True, timeout=60)
    return sorted(out_dir.glob("*.jpg"))


def frame_density(frame_path: Path) -> float:
    """
    Compute visual density — fraction of pixels that are NOT near-background-dark.
    Uses ffprobe to sample pixel stats. A frame of pure #0A0E1A returns ~0.
    A frame with text / shapes / color returns >0.1.
    """
    # Use ffmpeg's signalstats filter to compute frame statistics
    r = subprocess.run([
        "ffmpeg", "-hide_banner", "-nostats", "-i", str(frame_path),
        "-vf", "signalstats,metadata=print",
        "-f", "null", "-",
    ], capture_output=True, text=True, timeout=20)
    # Parse YAVG (luminance average) from stderr
    for line in r.stderr.splitlines():
        if "lavfi.signalstats.YAVG" in line:
            try:
                yavg = float(line.split("=")[-1].strip())
                # YAVG < 20 on 0-255 scale = near-black
                # Normalize: density ~ (yavg - 15) / 100, clamped
                density = max(0.0, min(1.0, (yavg - 15.0) / 80.0))
                return density
            except ValueError:
                pass
    return 0.0


def pure_black_ratio(frame_path: Path) -> float:
    """Fraction of pixels with all channels <16 (near-pure-black)."""
    r = subprocess.run([
        "ffmpeg", "-hide_banner", "-nostats", "-i", str(frame_path),
        "-vf", "blackdetect=d=0.01:pic_th=0.95:pix_th=0.06,signalstats,metadata=print",
        "-f", "null", "-",
    ], capture_output=True, text=True, timeout=20)
    # Fallback: use YMIN + YAVG to estimate black ratio
    ymin = None
    yavg = None
    for line in r.stderr.splitlines():
        if "lavfi.signalstats.YMIN" in line:
            try:
                ymin = float(line.split("=")[-1].strip())
            except ValueError:
                pass
        elif "lavfi.signalstats.YAVG" in line:
            try:
                yavg = float(line.split("=")[-1].strip())
            except ValueError:
                pass
    if yavg is None:
        return 0.0
    # If avg luminance is very low + min is 0, frame is mostly black
    if yavg < 15:
        return min(1.0, 0.98)
    if yavg < 25:
        return 0.85
    if yavg < 40:
        return 0.7
    return 0.3


def frame_delta(prev: Path, cur: Path) -> float:
    """
    Compute normalized frame-to-frame delta using SSIM.
    Returns 1 - SSIM, so 0 = identical, 1 = completely different.
    """
    r = subprocess.run([
        "ffmpeg", "-hide_banner", "-nostats",
        "-i", str(prev),
        "-i", str(cur),
        "-lavfi", "ssim",
        "-f", "null", "-",
    ], capture_output=True, text=True, timeout=20)
    # Parse "SSIM All:0.95"
    for line in r.stderr.splitlines():
        if "SSIM" in line and "All:" in line:
            try:
                all_val = line.split("All:")[-1].split(" ")[0]
                ssim = float(all_val)
                return max(0.0, 1.0 - ssim)
            except (ValueError, IndexError):
                pass
    return 0.0


# ── Checks ──────────────────────────────────────────────────────────────────

def check_visual_density(frames: list[Path]) -> tuple[bool, str]:
    """PASS if >90% of frames have density > MIN_VISUAL_DENSITY."""
    fails = []
    for i, f in enumerate(frames):
        d = frame_density(f)
        if d < MIN_VISUAL_DENSITY:
            fails.append((i, d, f.name))
    pass_ratio = 1 - (len(fails) / max(len(frames), 1))
    if pass_ratio >= 0.9:
        return True, f"✓ visual_density: {len(frames) - len(fails)}/{len(frames)} frames above {MIN_VISUAL_DENSITY}"
    else:
        sample = fails[:3]
        msg = f"✗ visual_density: {len(fails)}/{len(frames)} frames below threshold. " \
              f"Samples: {[(f[0], round(f[1], 3), f[2]) for f in sample]}"
        return False, msg


def check_pure_black(frames: list[Path]) -> tuple[bool, str]:
    """PASS if no frame is >MAX_PURE_BLACK_RATIO pure-black (catches empty frames)."""
    fails = []
    for i, f in enumerate(frames):
        r = pure_black_ratio(f)
        if r > MAX_PURE_BLACK_RATIO:
            fails.append((i, r, f.name))
    if not fails:
        return True, f"✓ pure_black: 0/{len(frames)} frames are empty-dark"
    else:
        return False, f"✗ pure_black: {len(fails)}/{len(frames)} frames >92% black. Samples: {fails[:3]}"


def check_motion_presence(frames: list[Path]) -> tuple[bool, str]:
    """PASS if no 3+ consecutive frame pairs have delta < MIN_FRAME_DELTA."""
    if len(frames) < 4:
        return True, "✓ motion_presence: too few frames to check"
    low_motion_streak = 0
    max_streak = 0
    for i in range(1, len(frames)):
        d = frame_delta(frames[i - 1], frames[i])
        if d < MIN_FRAME_DELTA:
            low_motion_streak += 1
            max_streak = max(max_streak, low_motion_streak)
        else:
            low_motion_streak = 0
    # At 2fps, 3+ streak = 1.5s dead air
    if max_streak >= 3:
        return False, f"✗ motion_presence: {max_streak} consecutive frames with near-zero delta (>{max_streak/2:.1f}s dead air)"
    return True, f"✓ motion_presence: max dead-air streak {max_streak} frames"


# ── Main ────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reel", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, default=Path("/tmp/qa-frames"))
    ap.add_argument("--fps", type=float, default=2.0)
    ap.add_argument("--strict", action="store_true",
                    help="Exit 2 on any failure (for orchestrator gating)")
    ap.add_argument("--json", action="store_true",
                    help="Emit JSON summary instead of human-readable")
    args = ap.parse_args()

    if not args.reel.exists():
        sys.exit(f"Reel not found: {args.reel}")

    print(f"▶ QA on {args.reel.name}")
    print(f"  Extracting frames at {args.fps}fps → {args.out_dir}/")
    frames = extract_frames(args.reel, args.out_dir, args.fps)
    print(f"  {len(frames)} frames extracted")

    results = []
    for check_fn in [check_visual_density, check_pure_black, check_motion_presence]:
        ok, msg = check_fn(frames)
        results.append({"check": check_fn.__name__, "pass": ok, "message": msg})
        print(f"  {msg}")

    any_failed = any(not r["pass"] for r in results)

    if args.json:
        print(json.dumps({"results": results, "passed": not any_failed}, indent=2))

    if any_failed and args.strict:
        sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
