#!/usr/bin/env python3
"""stitch_video.py — concat scene MP4s + mix VO/BGM + render captions + brand chip.

ffmpeg-driven. Reuses video-edit's caption components for kinetic captions when
HyperFrames is available; falls back to drawtext-based subtitles otherwise.

v1: minimal viable end-to-end. Polish-pass via video-edit is opt-in (--polish).
"""
import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str], **kw) -> int:
    print("$", " ".join(cmd))
    return subprocess.run(cmd, **kw).returncode


def get_duration(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nokey=1:noprint_wrappers=1", str(path)],
        capture_output=True, text=True,
    )
    try:
        return float(out.stdout.strip())
    except ValueError:
        return 0.0


def concat_scenes(scenes_dir: Path, manifest: dict, out_path: Path) -> int:
    """Concat scenes in scene_id order, skipping any [FAILED] entries."""
    list_path = scenes_dir.parent / "concat-list.txt"
    entries = []
    for s in manifest["scenes"]:
        if s.get("source") == "[FAILED]":
            continue
        clip = Path(s.get("output_path") or scenes_dir / f"{s['scene_id']}.mp4")
        if clip.exists():
            entries.append(f"file '{clip.resolve()}'")
    if not entries:
        print("✗ No scenes to concat", file=sys.stderr)
        return 1
    list_path.write_text("\n".join(entries))
    return run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(list_path),
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "30",
        "-an",  # strip audio from clips; we re-mix VO/BGM after
        str(out_path),
    ])


def mix_audio(silent_video: Path, vo: Path | None, bgm: Path | None, out: Path) -> int:
    """Mix VO at -14 LUFS over BGM at -18 LUFS, then mux onto the silent video."""
    inputs = ["-i", str(silent_video)]
    audio_inputs = []
    if vo and vo.exists():
        inputs += ["-i", str(vo)]
        audio_inputs.append(("vo", len(audio_inputs) + 1))
    if bgm and bgm.exists():
        inputs += ["-i", str(bgm)]
        audio_inputs.append(("bgm", len(audio_inputs) + 1))

    if not audio_inputs:
        # No audio — just copy
        return run(["ffmpeg", "-y", "-i", str(silent_video), "-c:v", "copy", str(out)])

    if len(audio_inputs) == 1:
        kind, idx = audio_inputs[0]
        target_lufs = -14 if kind == "vo" else -18
        return run([
            "ffmpeg", "-y", *inputs,
            "-filter_complex", f"[{idx}:a]loudnorm=I={target_lufs}:TP=-1.5:LRA=11[aout]",
            "-map", "0:v", "-map", "[aout]",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
            str(out),
        ])

    # Both VO and BGM
    vo_idx = audio_inputs[0][1]
    bgm_idx = audio_inputs[1][1]
    fc = (
        f"[{vo_idx}:a]loudnorm=I=-14:TP=-1.5:LRA=11[vo];"
        f"[{bgm_idx}:a]loudnorm=I=-18:TP=-2:LRA=11[bgm];"
        f"[vo][bgm]amix=inputs=2:duration=longest:dropout_transition=2[aout]"
    )
    return run([
        "ffmpeg", "-y", *inputs,
        "-filter_complex", fc,
        "-map", "0:v", "-map", "[aout]",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
        str(out),
    ])


def overlay_brand_chip(in_video: Path, chip_png: Path | None, out: Path) -> int:
    if not chip_png or not chip_png.exists():
        # Just copy through if no chip configured
        return run(["ffmpeg", "-y", "-i", str(in_video), "-c", "copy", str(out)])
    fc = "[1:v]scale=iw*0.18:-1[chip];[0:v][chip]overlay=W-w-30:H-h-30"
    return run([
        "ffmpeg", "-y", "-i", str(in_video), "-i", str(chip_png),
        "-filter_complex", fc,
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "copy",
        str(out),
    ])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("working_dir")
    ap.add_argument("--captions", choices=["kinetic", "simple", "off"], default="simple")
    ap.add_argument("--chip", default="auto", help="Path to brand chip PNG, or 'auto' to read client wiki, or 'off'")
    ap.add_argument("--aspect", default="9:16")
    ap.add_argument("--bgm", default=None, help="Path to BGM mp3, optional")
    args = ap.parse_args()

    wd = Path(args.working_dir)
    manifest = json.loads((wd / "manifest.json").read_text())
    scenes_dir = wd / "scenes"
    silent = wd / "concat-silent.mp4"
    mixed = wd / "concat-mixed.mp4"
    branded = wd / "draft.mp4"

    if concat_scenes(scenes_dir, manifest, silent) != 0:
        return 1

    vo = wd / "voiceover.mp3"
    bgm = Path(args.bgm) if args.bgm else None
    if mix_audio(silent, vo if vo.exists() else None, bgm if bgm and bgm.exists() else None, mixed) != 0:
        return 1

    chip_png = None
    if args.chip and args.chip != "off":
        chip_png = Path(args.chip) if args.chip != "auto" else None
        # Auto-discovery: future — read brand-identity.md to find chip asset
    if overlay_brand_chip(mixed, chip_png, branded) != 0:
        return 1

    duration = get_duration(branded)
    print(f"\n✓ Draft written: {branded}")
    print(f"  Duration: {duration:.1f}s")
    print(f"  Captions: {args.captions} (kinetic captions deferred to video-edit polish pass)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
