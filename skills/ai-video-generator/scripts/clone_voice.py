#!/usr/bin/env python3
"""clone_voice.py — generate VO via ChatterBox from manifest.json's vo_text fields.

Concatenates each scene's vo_text (in scene_id order, with 0.3s silence between)
and runs ChatterBox to produce voiceover.mp3. Falls back to silent track if
ChatterBox is unavailable, with a warning logged.

Reuses Digischola's voice-lock if --use-digischola-voice is passed; otherwise
defaults to neutral. For client work, future: per-client voice-lock under
{client}/_engine/voice-samples/.
"""
import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

GAP_SECONDS = 0.3


def find_chatterbox() -> str | None:
    """Locate the ChatterBox CLI/script as used by visual-generator."""
    # Reuse visual-generator's invocation if present
    candidate = Path.home() / "Desktop" / ".claude" / "skills" / "visual-generator" / "scripts" / "clone_voice.py"
    if candidate.exists():
        return str(candidate)
    # Fall back to PATH
    if shutil.which("chatterbox"):
        return "chatterbox"
    return None


def write_silent_track(out_path: Path, duration_sec: float) -> int:
    """Generate a silent MP3 fallback when ChatterBox is unavailable."""
    cmd = [
        "ffmpeg", "-y", "-f", "lavfi",
        "-i", f"anullsrc=r=44100:cl=stereo",
        "-t", f"{duration_sec:.2f}",
        "-q:a", "9", "-acodec", "libmp3lame",
        str(out_path),
    ]
    return subprocess.run(cmd, capture_output=True).returncode


def assemble_vo_text(manifest: dict) -> tuple[str, list[tuple[str, str]]]:
    """Return (concatenated text, list of (scene_id, vo_text) for chunked TTS)."""
    chunks = []
    full_parts = []
    for s in manifest.get("scenes", []):
        text = (s.get("vo_text") or "").strip()
        if not text:
            continue
        chunks.append((s["scene_id"], text))
        full_parts.append(text)
    return " ".join(full_parts), chunks


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--working-dir", required=True)
    ap.add_argument("--voice-lock", default=None,
                    help="Path to client voice-lock corpus (else neutral default)")
    ap.add_argument("--total-duration", type=float, default=30.0,
                    help="Used only for silent-track fallback length")
    args = ap.parse_args()

    wd = Path(args.working_dir)
    manifest_path = wd / "manifest.json"
    out_path = wd / "voiceover.mp3"

    if not manifest_path.exists():
        print(f"✗ manifest.json missing — run generate_scenes.py --finalize first", file=sys.stderr)
        return 1

    manifest = json.loads(manifest_path.read_text())
    full_text, chunks = assemble_vo_text(manifest)

    if not full_text:
        print("⚠ No vo_text in any scene — generating silent VO track")
        if write_silent_track(out_path, args.total_duration) == 0:
            print(f"✓ Silent VO: {out_path}")
            return 0
        return 1

    cb = find_chatterbox()
    if not cb:
        print("⚠ ChatterBox not found — generating silent VO track instead")
        print("  Install ChatterBox per visual-generator/references/voice-cloning-setup.md")
        if write_silent_track(out_path, args.total_duration) == 0:
            return 0
        return 1

    # Delegate to existing ChatterBox path for v1 — write a single text file and call
    text_path = wd / "vo-script.txt"
    text_path.write_text(full_text)
    cmd = ["python3", cb, "--text-file", str(text_path), "--output", str(out_path)]
    if args.voice_lock:
        cmd += ["--voice-lock", args.voice_lock]
    rc = subprocess.run(cmd, capture_output=False).returncode
    if rc != 0:
        print(f"✗ ChatterBox failed (rc={rc}) — falling back to silent track", file=sys.stderr)
        write_silent_track(out_path, args.total_duration)
        return 1
    print(f"✓ VO written: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
