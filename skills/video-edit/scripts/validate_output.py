#!/usr/bin/env python3
"""validate_output.py — enforce CRITICAL checks on a delivered video-edit file.

Usage: python3 validate_output.py <final.mp4> <source-probe.json> <expected-preset>

Exits 0 if all CRITICAL checks pass. Exits 1 on any CRITICAL failure.
Prints a human-readable report either way. Per Mayank's session-close protocol,
this MUST be run on every delivery.

CRITICAL checks:
  - File exists and has non-zero size
  - Duration > 1.0s
  - Output dims match source target-render-dims (or letterbox note logged)
  - Audio stream present + non-silent (loudness > -50 LUFS)
  - Thumbnail sidecar exists

WARN checks (do not fail):
  - Loudness within +/- 3 LUFS of preset target
  - Duration kept > 40% of original (catches over-aggressive silence trim)
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Optional


CRITICAL_FAILS = []
WARNINGS = []


def probe(path: Path) -> dict:
    r = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json",
         "-show_format", "-show_streams", str(path)],
        capture_output=True, text=True, check=True,
    )
    return json.loads(r.stdout)


def measure_lufs(path: Path) -> Optional[float]:
    r = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", str(path),
         "-af", "loudnorm=print_format=json", "-f", "null", "-"],
        capture_output=True, text=True,
    )
    for line in r.stderr.splitlines():
        line = line.strip()
        if line.startswith('"input_i"'):
            val = line.split(":")[1].strip().strip(',').strip('"')
            try:
                return float(val)
            except ValueError:
                return None
    return None


def main() -> int:
    if len(sys.argv) < 4:
        print("usage: validate_output.py <final.mp4> <source-probe.json> <preset>")
        return 1
    final = Path(sys.argv[1])
    probe_path = Path(sys.argv[2])
    preset = sys.argv[3]

    # 1. File exists + non-zero
    if not final.is_file() or final.stat().st_size == 0:
        CRITICAL_FAILS.append(f"Output file missing or empty: {final}")
        _report()
        return 1

    # 2. Probe the output
    try:
        out_probe = probe(final)
    except subprocess.CalledProcessError as e:
        CRITICAL_FAILS.append(f"ffprobe failed on output: {e}")
        _report()
        return 1

    dur = float(out_probe["format"]["duration"])
    if dur < 1.0:
        CRITICAL_FAILS.append(f"Duration {dur:.2f}s < 1.0s — edit is too short to be real")

    vstreams = [s for s in out_probe["streams"] if s["codec_type"] == "video"]
    astreams = [s for s in out_probe["streams"] if s["codec_type"] == "audio"]
    if not vstreams:
        CRITICAL_FAILS.append("No video stream in output")
        _report()
        return 1
    if not astreams:
        CRITICAL_FAILS.append("No audio stream in output (all video-edit deliveries must have audio)")

    # 3. Dims match source target
    src_probe = json.loads(probe_path.read_text())
    tgt = src_probe.get("target_render_dims", {})
    tgt_w, tgt_h = tgt.get("width"), tgt.get("height")
    out_w, out_h = vstreams[0].get("width"), vstreams[0].get("height")
    if tgt_w and tgt_h and (out_w, out_h) != (tgt_w, tgt_h):
        CRITICAL_FAILS.append(
            f"Dims mismatch: output {out_w}x{out_h} != target {tgt_w}x{tgt_h}"
        )

    # 4. Thumbnail exists
    thumb = final.with_name(final.stem + "-thumb.jpg")
    if not thumb.is_file():
        CRITICAL_FAILS.append(f"Thumbnail missing: {thumb}")

    # 5. Audio not silent (loudness > -50 LUFS)
    if astreams:
        lufs = measure_lufs(final)
        if lufs is None:
            WARNINGS.append("Could not measure LUFS (ffmpeg returned no loudnorm JSON)")
        elif lufs < -50:
            CRITICAL_FAILS.append(f"Audio effectively silent: {lufs:.1f} LUFS")
        else:
            target_lufs = -14 if preset in {"gen-z-punchy", "course-sell", "event-recap", "tech-demo"} else -16
            if abs(lufs - target_lufs) > 3.0:
                WARNINGS.append(
                    f"Loudness {lufs:.1f} LUFS is {abs(lufs-target_lufs):.1f} off preset target {target_lufs}"
                )

    # 6. Duration kept reasonable vs source
    src_dur = float(src_probe.get("duration_sec", 0))
    if src_dur > 0 and dur / src_dur < 0.4:
        WARNINGS.append(
            f"Final duration {dur:.1f}s is only {100*dur/src_dur:.0f}% of source "
            f"({src_dur:.1f}s) — silence trim may have been too aggressive"
        )

    _report()
    return 1 if CRITICAL_FAILS else 0


def _report() -> None:
    if CRITICAL_FAILS:
        print("CRITICAL FAILURES:")
        for c in CRITICAL_FAILS:
            print(f"  - {c}")
    else:
        print("CRITICAL: all passed")
    if WARNINGS:
        print("WARNINGS:")
        for w in WARNINGS:
            print(f"  - {w}")


if __name__ == "__main__":
    sys.exit(main())
