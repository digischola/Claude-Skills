#!/usr/bin/env python3
"""
Generate voiceover audio in Mayank's voice using F5-TTS (local, free, no API).

REQUIRES Python 3.11+ (F5-TTS dependency chain doesn't resolve on 3.9).
If this file is launched under python3.9, it re-execs itself under
/opt/homebrew/bin/python3.11.

Reads reference samples from `brand/_engine/voice-samples/` (produced by enroll_voice.py),
takes a VO script, synthesizes via F5-TTS on Apple Silicon MPS backend, saves MP3.

First run installs F5-TTS dependencies + downloads model weights (~1.3GB, one-time).
Subsequent runs are fast (~10-30 sec per Reel VO).

Usage:
    # Quick text → MP3
    python3 clone_voice.py --text "Hello, world" --out /tmp/hello.mp3

    # From a draft file (reads VO script from frontmatter `vo_script` field or body)
    python3 clone_voice.py --draft path/to/draft.md

    # Pick a specific reference sample (default: sample-01.wav)
    python3 clone_voice.py --text "..." --ref-sample 3 --out voice.mp3

    # Check F5-TTS install status, install if missing
    python3 clone_voice.py --install-check
"""

from __future__ import annotations

import argparse
import importlib
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

# F5-TTS needs Python 3.10+. If we're on 3.9 (macOS /usr/bin/python3), re-exec
# under /opt/homebrew/bin/python3.11.
_PY311 = "/opt/homebrew/bin/python3.11"
if sys.version_info < (3, 10) and os.path.exists(_PY311) and not os.environ.get("CLONE_VOICE_REEXEC"):
    os.environ["CLONE_VOICE_REEXEC"] = "1"
    os.execv(_PY311, [_PY311, __file__, *sys.argv[1:]])

sys.path.insert(0, str(Path(__file__).resolve().parent))

DEFAULT_BRAND = Path("/Users/digischola/Desktop/Digischola")


# ── frontmatter reader (stdlib only) ───────────────────────────────────────

def read_frontmatter(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}, text
    _, fm_block, body = text.split("---\n", 2)
    fm = {}
    for line in fm_block.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip().strip("'\"")
    return fm, body.lstrip()


# ── Reference-sample discovery ─────────────────────────────────────────────

def find_reference(brand: Path, preferred_id: int = 1) -> tuple[Path, str]:
    """Return (sample_wav_path, transcript) for the chosen enrolled sample."""
    # Post-2026-04-29 _engine/ convention: voice-samples + voice-lock under brand/_engine/.
    samples_dir = brand / "brand" / "_engine" / "voice-samples"
    if not samples_dir.exists():
        sys.exit(
            "No voice samples found. Run enroll_voice.py first:\n"
            "  python3 visual-generator/scripts/enroll_voice.py\n"
        )
    wav = samples_dir / f"sample-{preferred_id:02d}.wav"
    if not wav.exists():
        # Fallback: use first available
        avail = sorted(samples_dir.glob("sample-*.wav"))
        if not avail:
            sys.exit(f"No sample-NN.wav files found in {samples_dir}. Re-run enroll_voice.py.")
        wav = avail[0]

    # Pull transcript from voice-lock.md (now under _engine/wiki/)
    voice_lock = brand / "brand" / "_engine" / "wiki" / "voice-lock.md"
    transcript = ""
    if voice_lock.exists():
        text = voice_lock.read_text(encoding="utf-8")
        # Find the "Transcript:" line under the section matching sample-NN
        sample_name = wav.stem  # e.g. "sample-01"
        try:
            idx = text.index(f"`brand/_engine/voice-samples/{sample_name}.wav`")
            # Walk back to the nearest "**Transcript:**" before that point
            prefix = text[:idx]
            last_t = prefix.rfind("**Transcript:**")
            if last_t != -1:
                line_end = prefix.find("\n", last_t)
                transcript = prefix[last_t + len("**Transcript:**"):line_end].strip()
        except ValueError:
            pass

    if not transcript:
        # Hard-coded fallback to what enroll_voice.py wrote for sample-01
        transcript = "Hello, I'm Mayank from Digischola. I help wellness retreats convert more leads at lower cost."

    return wav, transcript


# ── F5-TTS install + load ──────────────────────────────────────────────────

def check_f5_tts() -> bool:
    try:
        importlib.import_module("f5_tts")
        return True
    except ImportError:
        return False


def install_f5_tts() -> bool:
    print("F5-TTS not installed. Installing via pip (~5-10 min, downloads PyTorch + model)...")
    print(f"  Using interpreter: {sys.executable} (python {sys.version_info.major}.{sys.version_info.minor})")
    print("  Model weights (~1.3GB) download on first synthesis.")
    if sys.version_info < (3, 10):
        print("⚠️  Python 3.9 detected. F5-TTS requires 3.10+. Install Homebrew Python 3.11:", file=sys.stderr)
        print("    brew install python@3.11 && /opt/homebrew/bin/pip3.11 install --user f5-tts", file=sys.stderr)
        return False
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "--user", "f5-tts"],
            check=True, timeout=1200,
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"Install failed: {e}", file=sys.stderr)
        print("\nFallback: install manually:\n  /opt/homebrew/bin/pip3.11 install --user f5-tts", file=sys.stderr)
        return False
    except subprocess.TimeoutExpired:
        print("Install timed out (>20 min). Try manually:\n  /opt/homebrew/bin/pip3.11 install --user f5-tts", file=sys.stderr)
        return False


# ── Synthesis ──────────────────────────────────────────────────────────────

def synthesize(text: str, ref_wav: Path, ref_text: str, out_path: Path) -> bool:
    """Run F5-TTS inference. Saves WAV at out_path. Returns True on success."""
    if not check_f5_tts():
        if not install_f5_tts():
            return False

    try:
        from f5_tts.api import F5TTS  # type: ignore
    except Exception as e:
        print(f"Import still fails after install: {e}", file=sys.stderr)
        return False

    # On Apple Silicon, use MPS backend if available
    device = None
    try:
        import torch  # type: ignore
        if torch.backends.mps.is_available():
            device = "mps"
        elif torch.cuda.is_available():
            device = "cuda"
        else:
            device = "cpu"
    except Exception:
        device = "cpu"
    print(f"  F5-TTS device: {device}")

    print(f"  Reference: {ref_wav}")
    print(f"  Ref text: {ref_text[:80]}...")
    print(f"  Gen text: {text[:80]}...")
    print("  Synthesizing... (first run downloads model ~1.3GB)")

    tts = F5TTS(device=device) if device else F5TTS()
    # F5TTS.infer takes (ref_file, ref_text, gen_text, file_wave=, ...)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    wav_tmp = out_path.with_suffix(".wav")
    try:
        tts.infer(
            ref_file=str(ref_wav),
            ref_text=ref_text,
            gen_text=text,
            file_wave=str(wav_tmp),
            remove_silence=True,
        )
    except Exception as e:
        print(f"F5-TTS inference failed: {e}", file=sys.stderr)
        return False

    # Convert to MP3 (smaller, universal playback) if requested
    if out_path.suffix.lower() == ".mp3":
        try:
            subprocess.run([
                "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                "-i", str(wav_tmp),
                "-codec:a", "libmp3lame", "-qscale:a", "2",
                str(out_path),
            ], check=True, timeout=60)
            wav_tmp.unlink(missing_ok=True)
        except Exception as e:
            print(f"MP3 conversion failed (keeping WAV): {e}", file=sys.stderr)
            shutil.move(str(wav_tmp), str(out_path.with_suffix(".wav")))
    else:
        if wav_tmp != out_path:
            shutil.move(str(wav_tmp), str(out_path))

    return out_path.exists() or out_path.with_suffix(".wav").exists()


# ── Draft-file integration ─────────────────────────────────────────────────

def pick_output_for_draft(brand: Path, draft: Path, fm: dict) -> Path:
    entry_id = fm.get("entry_id", "unknown")
    assets_dir = brand / "brand" / "queue" / "assets" / str(entry_id)
    assets_dir.mkdir(parents=True, exist_ok=True)
    return assets_dir / "voiceover.mp3"


EMOTION_TAG_RE = re.compile(r"\[(neutral|direct|measured|firm|confident|warm|calm|excited|thoughtful|serious|playful|urgent|pause|breath|soft|assertive)\]", re.IGNORECASE)


def clean_for_tts(text: str, strip_emotion_tags: bool = True) -> str:
    """Normalize text for TTS. Optionally strip [emotion] tags (F5-TTS only)."""
    if strip_emotion_tags:
        text = EMOTION_TAG_RE.sub("", text)
    # Remove any markdown heading lines / comments / bullet markers
    lines = []
    for line in text.splitlines():
        s = line.strip()
        if not s:
            lines.append("")
            continue
        if s.startswith("#"):
            continue
        if s.startswith("<!--") or s.startswith("-->"):
            continue
        if s.startswith(("- ", "* ")):
            s = s[2:]
        lines.append(s)
    out = []
    prev_blank = False
    for l in lines:
        if not l:
            if not prev_blank and out:
                out.append("")
            prev_blank = True
        else:
            out.append(l)
            prev_blank = False
    return "\n".join(out).strip()


# ── Chunked-emotion parsing for ChatterBox ────────────────────────────────

# Map emotion-tag → (exaggeration, cfg_weight, reference_sample_id).
# exaggeration: 0.0=flat, 0.5=default, 0.7+=dramatic. cfg_weight: 0.3-0.5 (higher=more reference adherence, lower=more model freedom).
# reference_sample_id maps to voice-samples/sample-NN.wav that matches this emotion's tone.
EMOTION_PARAMS = {
    "neutral":    {"exaggeration": 0.40, "cfg_weight": 0.50, "ref_sample": 1},
    "direct":     {"exaggeration": 0.55, "cfg_weight": 0.40, "ref_sample": 2},  # sample-02 credential/authority
    "measured":   {"exaggeration": 0.40, "cfg_weight": 0.50, "ref_sample": 3},  # sample-03 brutal truth (deliberate)
    "firm":       {"exaggeration": 0.65, "cfg_weight": 0.40, "ref_sample": 8},  # sample-08 punchy
    "confident":  {"exaggeration": 0.60, "cfg_weight": 0.40, "ref_sample": 4},  # sample-04 data-anchored
    "warm":       {"exaggeration": 0.50, "cfg_weight": 0.45, "ref_sample": 7},  # sample-07 personal pivot
    "calm":       {"exaggeration": 0.35, "cfg_weight": 0.50, "ref_sample": 1},
    "excited":    {"exaggeration": 0.75, "cfg_weight": 0.35, "ref_sample": 8},
    "thoughtful": {"exaggeration": 0.40, "cfg_weight": 0.50, "ref_sample": 5},  # sample-05 rhetorical Q
    "serious":    {"exaggeration": 0.50, "cfg_weight": 0.45, "ref_sample": 3},
    "playful":    {"exaggeration": 0.70, "cfg_weight": 0.35, "ref_sample": 8},
    "urgent":     {"exaggeration": 0.70, "cfg_weight": 0.40, "ref_sample": 2},
    "soft":       {"exaggeration": 0.35, "cfg_weight": 0.50, "ref_sample": 1},
    "assertive":  {"exaggeration": 0.65, "cfg_weight": 0.40, "ref_sample": 2},
}
DEFAULT_EMOTION = "neutral"


def split_by_emotion(text: str) -> list[tuple[str, str]]:
    """Split VO script into (emotion, chunk_text) pairs.

    '[confident] Audit yours. 5 seconds.' → [('confident', 'Audit yours. 5 seconds.')]
    Untagged prefix text gets DEFAULT_EMOTION.
    """
    # First clean everything that isn't speakable text, but KEEP emotion tags
    cleaned = clean_for_tts(text, strip_emotion_tags=False)
    # Find all emotion tag positions
    matches = list(EMOTION_TAG_RE.finditer(cleaned))
    if not matches:
        return [(DEFAULT_EMOTION, cleaned)]
    chunks = []
    # Handle any prefix text before first tag
    if matches[0].start() > 0:
        prefix = cleaned[:matches[0].start()].strip()
        if prefix:
            chunks.append((DEFAULT_EMOTION, prefix))
    # Each tag owns the text until the next tag
    for i, m in enumerate(matches):
        emotion = m.group(1).lower()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(cleaned)
        chunk = cleaned[start:end].strip()
        if chunk:
            chunks.append((emotion, chunk))
    return chunks


# ── Reference-clip concatenation for ChatterBox (needs ≥10s) ──────────────

def ensure_long_reference(brand: Path, sample_ids: list[int], out_path: Path) -> Path:
    """Concatenate multiple enrolled samples into a single ≥10s WAV for ChatterBox.

    ChatterBox recommends 10s+ reference; our enrolled samples are 5s each.
    Concatenating 2-3 matching-tone samples gives us enough material.
    """
    if out_path.exists():
        return out_path
    samples_dir = brand / "brand" / "voice-samples"
    wavs = []
    for sid in sample_ids:
        p = samples_dir / f"sample-{sid:02d}.wav"
        if p.exists():
            wavs.append(p)
    if not wavs:
        # Fallback: all 10 samples concatenated
        wavs = sorted(samples_dir.glob("sample-*.wav"))[:5]
    # ffmpeg concat via concat demuxer
    concat_list = out_path.with_suffix(".txt")
    concat_list.write_text("\n".join(f"file '{w}'" for w in wavs))
    subprocess.run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-f", "concat", "-safe", "0", "-i", str(concat_list),
        "-ar", "24000", "-ac", "1",
        str(out_path),
    ], check=True, timeout=30)
    concat_list.unlink(missing_ok=True)
    return out_path


# ── ChatterBox synthesis ──────────────────────────────────────────────────

_CHATTERBOX_MODEL = None


def _get_chatterbox():
    """Lazy-load ChatterBox model (singleton)."""
    global _CHATTERBOX_MODEL
    if _CHATTERBOX_MODEL is not None:
        return _CHATTERBOX_MODEL
    try:
        from chatterbox.tts import ChatterboxTTS  # type: ignore
        import torch  # type: ignore
    except ImportError as e:
        print(f"ChatterBox not installed: {e}", file=sys.stderr)
        return None
    device = "mps" if torch.backends.mps.is_available() else ("cuda" if torch.cuda.is_available() else "cpu")
    print(f"  Loading ChatterBox on {device}...")
    _CHATTERBOX_MODEL = ChatterboxTTS.from_pretrained(device=device)
    return _CHATTERBOX_MODEL


def synthesize_chatterbox(text: str, brand: Path, out_path: Path) -> bool:
    """Chunked-emotion synthesis via ChatterBox. Each [emotion] chunk uses matched
    reference sample + its own exaggeration/cfg_weight params, then all chunks are
    concatenated into a single MP3 with natural silence spacing between beats."""
    model = _get_chatterbox()
    if model is None:
        return False

    try:
        import torch  # type: ignore
        import torchaudio as ta  # type: ignore
    except ImportError:
        print("torchaudio missing", file=sys.stderr)
        return False

    chunks = split_by_emotion(text)
    print(f"  Split into {len(chunks)} emotion-tagged chunks:")
    for i, (emotion, chunk_text) in enumerate(chunks):
        preview = chunk_text[:60].replace("\n", " ")
        print(f"    [{i+1}] [{emotion}] {preview}...")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    wav_parts = []
    sample_rate = model.sr

    for i, (emotion, chunk_text) in enumerate(chunks):
        if not chunk_text.strip():
            continue
        params = EMOTION_PARAMS.get(emotion, EMOTION_PARAMS[DEFAULT_EMOTION])
        # Build a ≥10s reference clip matching this emotion's tone (cached per emotion)
        ref_ids = [params["ref_sample"]]
        # Pad with sample-01 (neutral anchor) + an alternate to hit 10s+
        if params["ref_sample"] != 1:
            ref_ids.append(1)
        ref_ids.append((params["ref_sample"] % 10) + 1)
        ref_path = brand / "brand" / "voice-samples" / f"ref-concat-{emotion}.wav"
        ensure_long_reference(brand, ref_ids, ref_path)

        print(f"  [{i+1}/{len(chunks)}] Synthesizing [{emotion}] (exag={params['exaggeration']}, cfg={params['cfg_weight']})...")
        try:
            wav = model.generate(
                chunk_text,
                audio_prompt_path=str(ref_path),
                exaggeration=params["exaggeration"],
                cfg_weight=params["cfg_weight"],
            )
        except Exception as e:
            print(f"  chunk {i+1} failed: {e}", file=sys.stderr)
            return False
        wav_parts.append(wav)
        # Insert 250ms silence between beats for natural pacing
        if i < len(chunks) - 1:
            silence = torch.zeros(1, int(sample_rate * 0.25))
            wav_parts.append(silence)

    if not wav_parts:
        print("  No audio generated", file=sys.stderr)
        return False

    # Concatenate all chunks along the time dimension
    # ChatterBox output shape is (1, N) tensor, int16 or float
    full_wav = torch.cat(wav_parts, dim=-1)
    wav_tmp = out_path.with_suffix(".wav")
    ta.save(str(wav_tmp), full_wav, sample_rate)

    # Transcode to MP3 if requested
    if out_path.suffix.lower() == ".mp3":
        subprocess.run([
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-i", str(wav_tmp), "-codec:a", "libmp3lame", "-qscale:a", "2",
            str(out_path),
        ], check=True, timeout=60)
        wav_tmp.unlink(missing_ok=True)

    return out_path.exists() or out_path.with_suffix(".wav").exists()


def extract_vo_script(fm: dict, body: str) -> str:
    """
    Find the VO script in a draft. Priority:
      1. frontmatter `vo_script` field (multiline not supported yet)
      2. body markdown section labeled 'Voiceover' or 'VO script'
      3. fall back to full body (strip markdown headings)

    Always runs clean_for_tts() on the result before returning.
    """
    if fm.get("vo_script"):
        return clean_for_tts(fm["vo_script"])
    # Look for a VO heading — match the WHOLE line (heading may have extra text after "Voiceover")
    heading_re = re.compile(r"^(##+)\s*(voiceover|vo\s*script)\b[^\n]*$", re.IGNORECASE | re.MULTILINE)
    m = heading_re.search(body)
    if m:
        # Content starts right after the matched heading line
        content_start = m.end()
        # Capture until next heading at same-or-shallower level
        rest = body[content_start:]
        next_hash = re.search(r"\n##\s", rest)
        chunk = rest[:next_hash.start()] if next_hash else rest
        return clean_for_tts(chunk)
    # Fall back: strip markdown headings from body, return plain text
    return clean_for_tts(body)


# ── CLI ────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--brand-folder", type=Path, default=DEFAULT_BRAND)
    ap.add_argument("--text", help="VO text to synthesize (direct)")
    ap.add_argument("--draft", type=Path, help="Draft markdown file (extracts VO script)")
    ap.add_argument("--out", type=Path, help="Output path (.mp3 or .wav). Default: auto-pick from draft.")
    ap.add_argument("--engine", choices=("chatterbox", "f5"), default="chatterbox",
                    help="TTS engine. chatterbox = emotion-aware chunked synthesis (default). f5 = flat fallback.")
    ap.add_argument("--ref-sample", type=int, default=1,
                    help="[F5-only] Which enrolled sample to use (1-10). Ignored by chatterbox.")
    ap.add_argument("--ref-text", help="[F5-only] Override reference transcript")
    ap.add_argument("--install-check", action="store_true",
                    help="Check + install F5-TTS and exit")
    args = ap.parse_args()

    if args.install_check:
        if check_f5_tts():
            print("✓ f5_tts installed.")
            return
        ok = install_f5_tts()
        sys.exit(0 if ok else 1)

    # Figure out what text to synthesize
    if args.draft:
        if not args.draft.exists():
            sys.exit(f"Draft not found: {args.draft}")
        fm, body = read_frontmatter(args.draft)
        # For chatterbox, preserve emotion tags (it splits on them)
        raw_body = body
        if args.engine == "chatterbox":
            fm2, body2 = read_frontmatter(args.draft)
            # Use the raw VO heading match but DON'T strip emotion tags
            if fm2.get("vo_script"):
                text = fm2["vo_script"]
            else:
                heading_re = re.compile(r"^(##+)\s*(voiceover|vo\s*script)\b[^\n]*$", re.IGNORECASE | re.MULTILINE)
                m = heading_re.search(body2)
                if m:
                    rest = body2[m.end():]
                    next_hash = re.search(r"\n##\s", rest)
                    text = rest[:next_hash.start()] if next_hash else rest
                else:
                    text = body2
        else:
            text = extract_vo_script(fm, body)
        if not text.strip():
            sys.exit(f"No VO script found in {args.draft}")
        out_path = args.out or pick_output_for_draft(args.brand_folder, args.draft, fm)
    elif args.text:
        text = args.text
        out_path = args.out or Path("/tmp/voice-clone-output.mp3")
    else:
        sys.exit("Provide --text or --draft.")

    print(f"\n▶ VO generation [{args.engine}]")
    print(f"  Text chars: {len(text)}")
    print(f"  Output: {out_path}")

    if args.engine == "chatterbox":
        ok = synthesize_chatterbox(text, args.brand_folder, out_path)
    else:
        # F5-TTS path (legacy / fallback)
        ref_wav, ref_text = find_reference(args.brand_folder, args.ref_sample)
        if args.ref_text:
            ref_text = args.ref_text
        # F5 can't handle emotion tags — strip them
        clean_text = clean_for_tts(text, strip_emotion_tags=True)
        ok = synthesize(clean_text, ref_wav, ref_text, out_path)

    if ok:
        print(f"\n✓ Done: {out_path}")
        print(f"  Play: open '{out_path}'")
    else:
        sys.exit("✗ Synthesis failed.")


if __name__ == "__main__":
    main()
