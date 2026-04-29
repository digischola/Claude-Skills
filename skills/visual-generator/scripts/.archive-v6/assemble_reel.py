#!/usr/bin/env python3
"""
Assemble final Reel MP4 from per-scene assets + voiceover (v2 — hybrid engine).

Per-scene engine routing driven by scene_type from generate_tow_prompts.parse_scenes():
  - founder_face  → Nano Banana PNG + Ken Burns (gentle 1.0→1.08)
  - hook          → Nano Banana PNG + punch-in (1.0→1.20, aggressive)
  - problem_beat  → Nano Banana PNG + slow pan (no face, cinematic B-roll feel)
  - insight_beat  → Nano Banana PNG + punch-in (lean in on thesis)
  - data_reveal   → Hyperframes MP4 if present (scene-N-hf.mp4), else PNG + punch-in
  - cta           → Nano Banana PNG + pull-back (1.15→1.0 handoff)

Reads:
  - Reel draft .md (entry_id + ## Scene breakdown → scene_types + durations)
  - brand/queue/assets/<entry_id>/scene-N.png | scene-N.mp4 | scene-N-hf.mp4
  - brand/queue/assets/<entry_id>/voiceover.mp3

Outputs:
  - brand/queue/assets/<entry_id>/reel.mp4 (1080x1920, H.264, AAC)

Quick-cut pacing (2026 Reel best practice): 3-5s average scene duration, hard cuts
between scenes. Text overlays are burned into Nano Banana images so no ffmpeg
drawtext needed for image-mode scenes.

Usage:
    python3 assemble_reel.py --draft path/to/reel-draft.md
    python3 assemble_reel.py --draft ... --no-trim     # don't trim to VO length
    python3 assemble_reel.py --draft ... --out /tmp/test-reel.mp4
    python3 assemble_reel.py --draft ... --legacy      # old behavior: uniform Ken Burns
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path


DEFAULT_BRAND = Path("/Users/digischola/Desktop/Digischola")


def read_frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}
    _, fm_block, _ = text.split("---\n", 2)
    fm = {}
    for line in fm_block.splitlines():
        if ":" in line and not line.startswith(" "):
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip().strip("'\"")
    return fm


IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".webp")


MOTION_GRAPHIC_TYPES = {"data_reveal", "insight_beat", "hook", "cta", "outro"}
# Scene types where Mayank's face speaks — lip-sync candidates (v5 only, deprecated in v6)
LIPSYNC_TYPES = {"founder_face"}


def collect_scene_assets(assets_dir: Path, num_scenes: int, scene_meta: list[dict] | None = None,
                          enable_lipsync: bool = True, voiceover_path: Path | None = None) -> list[dict]:
    """For each scene 1..N, discover the best asset + its mode.

    Precedence per scene (v6 / v7-pending):
      1. scene-N-lipsync.mp4 — Final lip-sync clip (e.g. manually-aligned Kling output)
      2. scene-N-hf.mp4      — Hyperframes pre-rendered (motion graphics + outro-card)
      3. If scene_type ∈ MOTION_GRAPHIC_TYPES and no hf.mp4, AUTO-GENERATE via build_motion_scene.py
      4. scene-N.mp4         — Generic video source (including scene-N-kling.mp4 / scene-N-broll.mp4
                                once v7 precedence is wired; for now, manually rename to scene-N.mp4)
      5. scene-N.{png,jpg,jpeg,webp} — Nano Banana still → Ken Burns

    scene_meta provides scene_type + fields used by the auto-generators.
    voiceover_path is kept on the signature for v7 Kling / Meta AI alignment hooks
    (currently unused after v5 Veo + SadTalker paths were pruned 2026-04-21).

    DEPRECATED PATHS (removed 2026-04-21):
      - scene-N-veo.mp4 auto-alignment to ChatterBox (v5 Veo path — dropped due to drift)
      - SadTalker fallback via brand/_engine/_lipsync/sadtalker-venv/ (too slow on Apple Silicon)
    """
    meta_by_n = {m["n"]: m for m in (scene_meta or [])}
    assets = []

    # VO chunks stay plumbed (unused today, v7 face_body alignment will wire in here).
    _ = enable_lipsync  # silence unused warning
    _ = voiceover_path  # silence unused warning

    for i in range(1, num_scenes + 1):
        lipsync_mp4 = assets_dir / f"scene-{i}-lipsync.mp4"
        hf_mp4 = assets_dir / f"scene-{i}-hf.mp4"
        plain_mp4 = assets_dir / f"scene-{i}.mp4"
        meta = meta_by_n.get(i, {})
        scene_type = meta.get("scene_type", "")

        # 1. Already-rendered lipsync MP4 wins (e.g. manually-muxed Kling + ChatterBox)
        if lipsync_mp4.exists():
            assets.append({"n": i, "path": lipsync_mp4, "mode": "lipsync"})
            continue

        # 2. Already-rendered Hyperframes MP4
        if hf_mp4.exists():
            assets.append({"n": i, "path": hf_mp4, "mode": "hyperframes"})
            continue

        # 3. Auto-generate Hyperframes for motion-graphic scene types
        if scene_type in MOTION_GRAPHIC_TYPES and meta:
            ok = auto_render_motion_scene(meta, hf_mp4)
            if ok:
                assets.append({"n": i, "path": hf_mp4, "mode": "hyperframes"})
                continue
            else:
                print(f"  ⚠ Scene {i} auto-motion-graphic failed — falling back to image", file=sys.stderr)

        # 4. Generic video (covers manually-renamed Kling / Meta AI / Veo outputs for now)
        if plain_mp4.exists():
            assets.append({"n": i, "path": plain_mp4, "mode": "video"})
            continue

        # 5. Image + Ken Burns (Nano Banana still)
        for ext in IMAGE_EXTS:
            img = assets_dir / f"scene-{i}{ext}"
            if img.exists():
                assets.append({"n": i, "path": img, "mode": "image"})
                break
    return assets


def _ensure_vo_chunks(voiceover_path: Path, expected_count: int) -> list[Path]:
    """Invoke extract_vo_chunk.py to split voiceover.mp3 into per-scene WAVs.
    Caches in /tmp keyed on voiceover path + mtime."""
    vo_tag = f"{voiceover_path.stem}-{int(voiceover_path.stat().st_mtime)}-{expected_count}"
    out_dir = Path(f"/tmp/vo-chunks-{vo_tag}")
    expected_files = [out_dir / f"chunk-{i}.wav" for i in range(1, expected_count + 1)]
    if all(f.exists() for f in expected_files):
        return expected_files
    extractor = Path(__file__).resolve().parent / "extract_vo_chunk.py"
    try:
        subprocess.run([
            "/opt/homebrew/bin/python3.11", str(extractor),
            "--voiceover", str(voiceover_path),
            "--out-dir", str(out_dir),
            "--expected-count", str(expected_count),
        ], check=True, timeout=60)
    except Exception as e:
        print(f"  ⚠ VO chunk extraction failed: {e}", file=sys.stderr)
        return []
    return [f for f in expected_files if f.exists()]


# ── Auto-invoke build_motion_scene.py for motion-graphic scenes ─────────────

import re as _re


def parse_hyperframes_vars(scene: dict) -> tuple[str, dict]:
    """Infer (template_name, vars_dict) from a scene's fields.

    scene_type → template:
      data_reveal  → data-reveal
      insight_beat → kinetic-insight

    Extraction heuristics:
      data-reveal: find first number in VO or overlay, detect suffix, infer color
                   (green for positive-delta phrasing, blue neutral), split overlay
                   on "·" / "|" / ":" for eyebrow/label.
      kinetic-insight: split VO into 3 lines (first 2 on sentence splits, 3rd is
                       the payoff — last sentence gets accent color).
    """
    scene_type = scene.get("scene_type", "")
    # Normalize: strip smart/straight quotes + whitespace at boundaries
    def _clean(s: str) -> str:
        return s.strip().strip('"').strip('"').strip('"').strip("'").strip()
    vo = _clean(scene.get("vo", ""))
    overlay = _clean(scene.get("overlay", ""))
    mood = _clean(scene.get("mood", ""))

    if scene_type == "data_reveal":
        # Find the first number (optional +/-, optional %/x/K suffix)
        num_match = _re.search(r"(\+|-)?(\d+(?:\.\d+)?)\s*(%|x|K|k)?", overlay + " " + vo)
        if num_match:
            sign = num_match.group(1) or ""
            number = int(float(num_match.group(2)))
            suffix = num_match.group(3) or ""
        else:
            sign, number, suffix = "", 0, ""

        # Color: green for positive-delta signals, blue for neutral
        positive_cues = ["+", "lift", "boost", "growth", "up", "more", "increase"]
        combined = (overlay + " " + vo + " " + mood).lower()
        hero_color = "#4ADE80" if any(c in combined for c in positive_cues) or sign == "+" else "#3B9EFF"

        # Split overlay on separator for eyebrow + label
        separators = [" · ", " | ", " : ", " — "]
        parts = [overlay]
        for sep in separators:
            if sep in overlay:
                parts = [p.strip().strip('"') for p in overlay.split(sep) if p.strip()]
                break

        # Heuristic: part with digits is the headline; other is eyebrow context
        digit_parts = [p for p in parts if _re.search(r"\d", p)]
        non_digit_parts = [p for p in parts if not _re.search(r"\d", p)]
        eyebrow = (non_digit_parts[0] if non_digit_parts else "").upper()
        label = "LIFT" if hero_color == "#4ADE80" else "RESULT"
        # Pull last clause of VO as sublabel for context
        vo_sentences = [s.strip() for s in _re.split(r"[.!?]", vo) if s.strip()]
        sublabel = vo_sentences[-1] if vo_sentences else ""

        vars_ = {
            "TARGET_NUMBER": number,
            "SUFFIX": suffix,
            "HERO_COLOR": hero_color,
            "EYEBROW": eyebrow,
            "LABEL": label.upper(),
            "SUBLABEL": sublabel,
        }
        return "data-reveal", vars_

    if scene_type == "hook":
        # kinetic-hook template: punch-in text
        # Heuristic: pick the most punchy short phrase from VO or overlay.
        # Prefer overlay if present (author-curated short text). Else shrink VO to first clause.
        hook_source = overlay if overlay else vo
        # Split on sentence delimiter, take first clause
        first_clause = _re.split(r"[.!?,]", hook_source)[0].strip()
        # Cap at ~5 words for impact
        words = first_clause.split()
        hook_text = " ".join(words[:5]).strip().upper() if words else "HOOK"

        # Eyebrow = short context label (use mood or a generic default)
        eyebrow = ""
        if overlay and overlay != hook_text:
            eyebrow = overlay.upper()
        else:
            eyebrow = "THE FINDING" if "audited" in vo.lower() or "reviewed" in vo.lower() else "READ THIS"

        # Sub = rest of VO as muted supporting line (truncate to ~10 words)
        sub_source = vo if vo else ""
        sub_words = sub_source.split()
        sub_text = " ".join(sub_words[:10]).strip()
        if len(sub_words) > 10:
            sub_text += "..."

        return "kinetic-hook", {
            "EYEBROW": eyebrow[:40],
            "HOOK": hook_text[:40],
            "SUB": sub_text[:100],
        }

    if scene_type in ("cta", "outro"):
        # outro-card template: static face + dynamic CTA text + URL + handle
        # Priority order for CTA_TEXT extraction:
        #   1. VO first imperative clause ("Audit yours" → "AUDIT YOURS") — most reliable
        #   2. ALL-CAPS phrase in overlay EXCLUDING the URL substring
        #   3. Generic fallback "LINK IN BIO"
        # URL extracted separately from overlay+VO.
        cta_text = ""
        cta_url = ""

        # 1. URL detection — scan for domain pattern
        url_match = _re.search(r"([a-zA-Z0-9][a-zA-Z0-9\-.]*\.(?:com|in|io|co|app|me)(?:/[^\s]*)?)", overlay + " " + vo)
        if url_match:
            cta_url = url_match.group(1).upper()

        # 2. CTA_TEXT — VO-first strategy (imperative verb clause is the actual call-to-action)
        vo_clauses = [c.strip() for c in _re.split(r"[.!?]", vo) if c.strip()]
        # Common imperative verbs that signal a CTA ("audit yours", "save this", "try it")
        imperative_verbs = ("audit", "try", "save", "get", "grab", "steal", "book", "join",
                             "start", "stop", "build", "check", "watch", "follow", "share",
                             "dm", "comment", "link", "visit", "learn", "take", "do")
        for clause in vo_clauses:
            first_word = clause.lower().split(" ")[0] if clause else ""
            if first_word in imperative_verbs:
                words = clause.split()[:4]
                cta_text = " ".join(words).upper().rstrip(".,!?")
                break

        # 3. If VO didn't yield one, scan overlay for ALL-CAPS phrase, but STRIP the URL first
        if not cta_text:
            overlay_minus_url = overlay
            if url_match:
                overlay_minus_url = overlay.replace(url_match.group(1), "").replace(
                    url_match.group(1).upper(), "")
            caps_match = _re.search(r"\b([A-Z][A-Z\s·]{3,25}[A-Z])\b", overlay_minus_url)
            if caps_match:
                cta_text = caps_match.group(1).strip().replace("·", "").strip()

        # 4. Last-resort fallback
        if not cta_text:
            if vo_clauses:
                words = vo_clauses[0].split()[:4]
                cta_text = " ".join(words).upper().rstrip(".,!?")
            else:
                cta_text = "LINK IN BIO"

        if not cta_url:
            cta_url = "DIGISCHOLA.IN"

        # Face URL — use an absolute path to the outro portrait (fall back to face-01)
        face_path = DEFAULT_BRAND / "brand" / "face-samples" / "face-outro.jpg"
        if not face_path.exists():
            face_path = DEFAULT_BRAND / "brand" / "face-samples" / "face-01.jpg"

        return "outro-card", {
            "FACE_URL": f"file://{face_path}",
            "CTA_TEXT": cta_text[:40],
            "CTA_URL": cta_url[:40],
            "HANDLE": "DIGISCHOLA",
        }

    if scene_type == "insight_beat":
        # Split VO into 3 lines at sentence boundaries, then strip quote-only fragments
        sentences = [_clean(s) for s in _re.split(r"[.!?]", vo) if _clean(s)]
        # If fewer than 3 sentences, split the longest on commas to get a 3-line structure
        while len(sentences) < 3 and any("," in s for s in sentences):
            longest = max(sentences, key=len)
            idx = sentences.index(longest)
            parts = [_clean(p) for p in longest.split(",", 1) if _clean(p)]
            if len(parts) < 2:
                break
            sentences = sentences[:idx] + parts + sentences[idx + 1:]
        # Pad if still <3
        while len(sentences) < 3:
            sentences.append("")

        vars_ = {
            "EYEBROW": overlay.upper() if overlay else "THE INSIGHT",
            "LINE1": sentences[0],
            "LINE2": sentences[1] if len(sentences) > 1 else "",
            "LINE3": sentences[2] if len(sentences) > 2 else "",
        }
        return "kinetic-insight", vars_

    return "", {}


def auto_render_motion_scene(scene: dict, out_mp4: Path) -> bool:
    """Invoke build_motion_scene.py to render a Hyperframes motion graphic for
    a data_reveal or insight_beat scene."""
    template, vars_ = parse_hyperframes_vars(scene)
    if not template:
        return False

    duration = scene.get("duration_sec", 4.0)
    builder = Path(__file__).resolve().parent / "build_motion_scene.py"
    if not builder.exists():
        print(f"  build_motion_scene.py not found at {builder}", file=sys.stderr)
        return False

    import json as _json
    print(f"  ▶ Auto-rendering scene {scene['n']} [{scene['scene_type']}] via template '{template}' ({duration}s)")
    print(f"    Vars: {vars_}")
    try:
        subprocess.run([
            "/opt/homebrew/bin/python3.11", str(builder),
            "--template", template,
            "--out", str(out_mp4),
            "--duration", str(duration),
            "--vars", _json.dumps(vars_),
        ], check=True, timeout=180)
        return out_mp4.exists()
    except subprocess.CalledProcessError as e:
        print(f"  build_motion_scene failed: {e}", file=sys.stderr)
        return False
    except subprocess.TimeoutExpired:
        print(f"  build_motion_scene timed out", file=sys.stderr)
        return False


def collect_scenes_legacy(assets_dir: Path) -> tuple[list[Path], str]:
    """Legacy: no-scene-type uniform collection. Kept for --legacy flag."""
    videos = sorted(assets_dir.glob("scene-*.mp4"))
    if videos:
        return videos, "video"
    images = []
    for i in range(1, 20):
        for ext in IMAGE_EXTS:
            p = assets_dir / f"scene-{i}{ext}"
            if p.exists():
                images.append(p)
                break
    return images, "image"


SCENE_DURATIONS_DEFAULT = [6.0, 7.0, 7.0, 6.0, 4.0]  # legacy — sums to 30 for 5 scenes

# Per-scene-type motion profile: (zoom_style, start_zoom, end_zoom, pan_amplitude_px)
# More aggressive zoom for hook/insight/cta; gentle for founder_face; slow pan for problem_beat.
MOTION_BY_TYPE = {
    "hook":         {"style": "punch_in",  "z0": 1.00, "z1": 1.20, "pan_amp": 0},
    "problem_beat": {"style": "pan",       "z0": 1.08, "z1": 1.08, "pan_amp": 80},
    "founder_face": {"style": "punch_in",  "z0": 1.00, "z1": 1.08, "pan_amp": 0},
    "insight_beat": {"style": "punch_in",  "z0": 1.02, "z1": 1.18, "pan_amp": 0},
    "data_reveal":  {"style": "punch_in",  "z0": 1.00, "z1": 1.15, "pan_amp": 0},
    "cta":          {"style": "pull_back", "z0": 1.15, "z1": 1.00, "pan_amp": 0},
}
DEFAULT_MOTION = {"style": "punch_in", "z0": 1.00, "z1": 1.12, "pan_amp": 0}


def motion_image_to_video(image_path: Path, out_path: Path, duration_sec: float,
                          motion: dict,
                          fps: int = 30, width: int = 1080, height: int = 1920) -> bool:
    """Convert a still image into a motion-video with per-scene-type motion profile.

    motion dict: {"style": "punch_in"|"pull_back"|"pan", "z0": float, "z1": float, "pan_amp": int}
    - punch_in: linear zoom from z0 → z1 (z1 > z0)
    - pull_back: linear zoom from z0 → z1 (z0 > z1)
    - pan: constant zoom z0, horizontal sine pan amplitude pan_amp px

    Outputs H.264 silent MP4 at 1080x1920.
    """
    total_frames = int(duration_sec * fps)
    style = motion.get("style", "punch_in")
    z0 = motion.get("z0", 1.0)
    z1 = motion.get("z1", 1.12)
    pan_amp = motion.get("pan_amp", 0)

    # Linear-interp zoom: z(t) = z0 + (z1-z0) * on/(total_frames-1)
    # Use 'on' (frame counter) instead of time for smoother motion
    if style == "punch_in":
        z_expr = f"'{z0}+({z1}-{z0})*on/{max(total_frames-1,1)}'"
        x_expr = "'iw/2-(iw/zoom/2)'"
        y_expr = "'ih/2-(ih/zoom/2)'"
    elif style == "pull_back":
        z_expr = f"'{z0}+({z1}-{z0})*on/{max(total_frames-1,1)}'"
        x_expr = "'iw/2-(iw/zoom/2)'"
        y_expr = "'ih/2-(ih/zoom/2)'"
    elif style == "pan":
        z_expr = f"{z0}"
        x_expr = f"'iw/2-(iw/zoom/2)+sin(on/{total_frames}*3.14159)*{pan_amp}'"
        y_expr = "'ih/2-(ih/zoom/2)'"
    else:  # fallback
        z_expr = f"'{z0}+({z1}-{z0})*on/{max(total_frames-1,1)}'"
        x_expr = "'iw/2-(iw/zoom/2)'"
        y_expr = "'ih/2-(ih/zoom/2)'"

    zoompan = (
        f"scale={width*2}:{height*2}:force_original_aspect_ratio=increase,crop={width*2}:{height*2},"
        f"zoompan=z={z_expr}:x={x_expr}:y={y_expr}:"
        f"d={total_frames}:s={width}x{height}:fps={fps}"
    )

    try:
        subprocess.run([
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-loop", "1", "-i", str(image_path),
            "-t", f"{duration_sec:.2f}",
            "-vf", zoompan,
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-an",
            str(out_path),
        ], check=True, timeout=90)
        return out_path.exists()
    except subprocess.CalledProcessError as e:
        print(f"Motion render failed for {image_path.name}: {e}", file=sys.stderr)
        return False


# Backward-compat wrapper
def ken_burns_image_to_video(image_path: Path, out_path: Path, duration_sec: float,
                              fps: int = 30, width: int = 1080, height: int = 1920,
                              zoom_style: str = "in") -> bool:
    """Legacy wrapper — maps old zoom_style strings to new motion dict."""
    if zoom_style == "in":
        motion = {"style": "punch_in", "z0": 1.0, "z1": 1.12, "pan_amp": 0}
    elif zoom_style == "out":
        motion = {"style": "pull_back", "z0": 1.15, "z1": 1.0, "pan_amp": 0}
    else:  # pan
        motion = {"style": "pan", "z0": 1.1, "z1": 1.1, "pan_amp": 50}
    return motion_image_to_video(image_path, out_path, duration_sec, motion, fps, width, height)


def render_scene_videos(scene_assets: list[dict], scene_meta: list[dict], tmp_dir: Path) -> list[Path]:
    """Convert per-scene assets (images/videos/hyperframes) to uniform scene MP4s
    using per-scene-type motion profiles from MOTION_BY_TYPE.

    scene_assets: from collect_scene_assets() — [{n, path, mode}]
    scene_meta: from generate_tow_prompts.parse_scenes() — [{n, scene_type, duration_sec, ...}]

    If scene_meta is empty or doesn't cover a scene, falls back to legacy zoom cycling.
    """
    # Index scene_meta by scene number
    meta_by_n = {m["n"]: m for m in scene_meta}
    out_paths = []
    for asset in scene_assets:
        n = asset["n"]
        meta = meta_by_n.get(n, {})
        scene_type = meta.get("scene_type", "founder_face")
        duration = meta.get("duration_sec", 4.0)
        motion = MOTION_BY_TYPE.get(scene_type, DEFAULT_MOTION)

        out = tmp_dir / f"scene-{n}.mp4"

        if asset["mode"] in ("hyperframes", "video", "lipsync"):
            # Pre-rendered video — just re-encode to target spec
            print(f"  Scene {n} [{scene_type}, {duration}s] {asset['mode']}: {asset['path'].name} → pass-through")
            ok = reencode_video_to_spec(asset["path"], out, duration_sec=duration)
        else:
            # Image → motion video
            print(f"  Scene {n} [{scene_type}, {duration}s] image + {motion['style']} (z={motion['z0']}→{motion['z1']}): {asset['path'].name}")
            ok = motion_image_to_video(asset["path"], out, duration, motion)

        if ok:
            out_paths.append(out)
        else:
            print(f"  ⚠ Scene {n} render failed, skipping")
    return out_paths


def reencode_video_to_spec(in_path: Path, out_path: Path, duration_sec: float | None = None,
                           fps: int = 30, width: int = 1080, height: int = 1920) -> bool:
    """Re-encode video to 1080x1920 H.264 yuv420p silent at target fps, optionally trim."""
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(in_path)]
    if duration_sec:
        cmd.extend(["-t", f"{duration_sec:.2f}"])
    cmd.extend([
        "-vf", f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},fps={fps}",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-an",
        str(out_path),
    ])
    try:
        subprocess.run(cmd, check=True, timeout=120)
        return out_path.exists()
    except subprocess.CalledProcessError as e:
        print(f"Re-encode failed for {in_path.name}: {e}", file=sys.stderr)
        return False


# Backward-compat — old callers using Path list + durations list
def images_to_scene_videos(images: list[Path], tmp_dir: Path,
                           durations: list[float] | None = None) -> list[Path]:
    """Legacy: uniform Ken Burns cycling. Kept for --legacy mode."""
    out_paths = []
    styles = ["in", "out", "in", "pan", "in", "out", "in", "pan"]
    for i, img in enumerate(images):
        dur = durations[i] if durations and i < len(durations) else (
            SCENE_DURATIONS_DEFAULT[i] if i < len(SCENE_DURATIONS_DEFAULT) else 6.0
        )
        style = styles[i % len(styles)]
        out = tmp_dir / f"scene-{i+1}.mp4"
        print(f"  [legacy] Ken Burns: {img.name} → scene-{i+1}.mp4 ({dur}s, zoom-{style})")
        if ken_burns_image_to_video(img, out, dur, zoom_style=style):
            out_paths.append(out)
        else:
            print(f"  ⚠ Failed scene {i+1}, skipping")
    return out_paths


def get_audio_duration_sec(audio_path: Path) -> float:
    """Use ffprobe to get audio duration. Returns 0.0 on failure."""
    try:
        r = subprocess.run([
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(audio_path),
        ], capture_output=True, text=True, timeout=10)
        return float(r.stdout.strip()) if r.stdout.strip() else 0.0
    except Exception:
        return 0.0


# ── v6 cinematic polish chain ───────────────────────────────────────────────
# Applied to the full concat during re-encode for a unified "graded" look.
# - eq: small sat + contrast bump + tiny brightness lift-down (cinema feel)
# - vignette: subtle darkening at edges → focal point compression
# - noise: light film grain (temporal-only to avoid fixed-pattern ugliness)
# Tuned gentle so brand text stays crisp and faces don't look crushed.
POLISH_FILTER = (
    "eq=saturation=1.08:contrast=1.06:brightness=-0.01,"
    "vignette=PI/5,"
    "noise=alls=8:allf=t"
)


def generate_flash_clip(out_path: Path, width: int = 1080, height: int = 1920,
                        fps: int = 30, num_frames: int = 2) -> bool:
    """Generate a short white-flash clip for inserting between hard cuts.
    2 frames @ 30fps ≈ 67ms — enough to feel like a camera shutter, too fast
    to register as a full frame. Used between scenes in v6 to punch transitions."""
    duration = max(num_frames / fps, 0.034)
    try:
        subprocess.run([
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-f", "lavfi",
            "-i", f"color=c=white:s={width}x{height}:r={fps}:d={duration:.4f}",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-t", f"{duration:.4f}",
            "-an",
            str(out_path),
        ], check=True, timeout=30)
        return out_path.exists()
    except subprocess.CalledProcessError:
        return False


# Pillar → BGM filename heuristic. Keep lowercase-hyphen keys that match
# pillar slugs used elsewhere in post-writer / content-calendar.
BGM_PILLAR_MAP = {
    "lp_craft": "lp-craft.mp3",
    "landing_page": "lp-craft.mp3",
    "solo_ops": "solo-ops.mp3",
    "solo_freelance": "solo-ops.mp3",
    "paid_media": "paid-media.mp3",
    "small_budget": "paid-media.mp3",
}


def resolve_bgm(brand_folder: Path, pillar_hint: str | None = None) -> Path | None:
    """Pick a BGM track from brand/_engine/music/ for audio ducking.

    Priority:
      1. brand/_engine/music/<pillar_hint>.mp3 (if pillar_hint maps to a file)
      2. brand/_engine/music/default.mp3
      3. First *.mp3 found in brand/_engine/music/
      4. None → no BGM (caller will skip ducking)

    Tracks must be license-free (Pixabay / Mixkit / Uppbeat free tier).
    Post-2026-04-29 _engine/ convention: media build dirs live under brand/_engine/.
    """
    music_dir = brand_folder / "brand" / "_engine" / "music"
    if not music_dir.exists():
        return None
    if pillar_hint:
        candidate_names = []
        slug = pillar_hint.strip().lower().replace(" ", "-").replace("_", "-")
        candidate_names.append(f"{slug}.mp3")
        mapped = BGM_PILLAR_MAP.get(pillar_hint.strip().lower().replace("-", "_"))
        if mapped:
            candidate_names.append(mapped)
        for name in candidate_names:
            p = music_dir / name
            if p.exists():
                return p
    default = music_dir / "default.mp3"
    if default.exists():
        return default
    mp3s = sorted(music_dir.glob("*.mp3"))
    return mp3s[0] if mp3s else None


def assemble(scenes: list[Path], voiceover: Path | None, out_path: Path,
             trim_to_vo: bool = True, apply_polish: bool = True,
             apply_flash: bool = True, bgm_path: Path | None = None,
             bgm_volume: float = 0.22) -> bool:
    """Stitch scene MP4s + optional voiceover (+ optional BGM) into a final Reel MP4.

    v6 features (all on by default, opt-out via flags):
      - apply_polish: cinematic color grade + vignette + film grain (POLISH_FILTER)
      - apply_flash: 2-frame white flash inserted between every pair of scenes
      - bgm_path: background music track, ducked under VO via sidechaincompress
    """
    if not scenes:
        print("No scenes to assemble.", file=sys.stderr)
        return False

    out_path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as td:
        td = Path(td)

        # 1. Optional flash clip (reused between every scene pair)
        flash_clip = None
        if apply_flash and len(scenes) > 1:
            flash_clip = td / "flash.mp4"
            if generate_flash_clip(flash_clip):
                print(f"  ⚡ Flash transitions enabled (2-frame white between {len(scenes)-1} scene pairs)")
            else:
                print("  ⚠ Flash clip generation failed — falling back to hard cuts")
                flash_clip = None

        # 2. Build ffmpeg concat list file — interleave flash between scenes
        concat_list = td / "concat.txt"
        with open(concat_list, "w") as f:
            for idx, s in enumerate(scenes):
                escaped = str(s).replace("'", r"'\''")
                f.write(f"file '{escaped}'\n")
                # Insert flash between pairs — not after final scene
                if flash_clip and idx < len(scenes) - 1:
                    f_escaped = str(flash_clip).replace("'", r"'\''")
                    f.write(f"file '{f_escaped}'\n")

        # 3. Concat all clips into one silent video + apply polish filter
        base_vf = (
            "scale=1080:1920:force_original_aspect_ratio=decrease,"
            "pad=1080:1920:(ow-iw)/2:(oh-ih)/2"
        )
        full_vf = f"{base_vf},{POLISH_FILTER}" if apply_polish else base_vf
        if apply_polish:
            print(f"  🎨 Polish filter applied: grade + vignette + grain")

        concat_video = td / "concat.mp4"
        try:
            subprocess.run([
                "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                "-f", "concat", "-safe", "0",
                "-i", str(concat_list),
                "-c:v", "libx264", "-pix_fmt", "yuv420p",
                "-vf", full_vf,
                "-r", "30",
                "-an",  # no audio for now
                str(concat_video),
            ], check=True, timeout=240)
        except subprocess.CalledProcessError as e:
            print(f"Concat failed: {e}", file=sys.stderr)
            return False

        # 4. Mux audio (VO + optional BGM with ducking) and output final
        return _mux_audio(concat_video, voiceover, bgm_path, out_path,
                          trim_to_vo=trim_to_vo, bgm_volume=bgm_volume)


def _mux_audio(video_in: Path, voiceover: Path | None, bgm_path: Path | None,
               out_path: Path, trim_to_vo: bool = True,
               bgm_volume: float = 0.22) -> bool:
    """Mux video + VO + optional BGM. When both VO and BGM present, BGM gets
    ducked under VO via sidechaincompress (broadcast-style ducking)."""
    has_vo = voiceover is not None and voiceover.exists()
    has_bgm = bgm_path is not None and bgm_path.exists()

    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"]
    cmd.extend(["-i", str(video_in)])

    vo_dur = get_audio_duration_sec(voiceover) if has_vo else 0.0

    if has_vo and has_bgm:
        # VO + BGM with ducking
        cmd.extend(["-i", str(voiceover)])
        cmd.extend(["-stream_loop", "-1", "-i", str(bgm_path)])  # loop BGM to cover video
        # Filter graph:
        #   BGM: volume down → sidechaincompress (keyed off VO) → "bgm_ducked"
        #   VO:  split into "vo_out" (mix) + "vo_key" (sidechain key)
        #   Mix: [bgm_ducked][vo_out]amix
        filter_complex = (
            f"[1:a]asplit=2[vo_out][vo_key];"
            f"[2:a]volume={bgm_volume}[bgm_raw];"
            f"[bgm_raw][vo_key]sidechaincompress=threshold=0.04:ratio=8:attack=10:release=400[bgm_ducked];"
            f"[bgm_ducked][vo_out]amix=inputs=2:duration=first:dropout_transition=0:weights=1 2[aout]"
        )
        cmd.extend([
            "-filter_complex", filter_complex,
            "-c:v", "copy",
            "-c:a", "aac", "-b:a", "192k",
            "-map", "0:v:0", "-map", "[aout]",
            "-shortest",
        ])
        if trim_to_vo and vo_dur > 0:
            cmd.extend(["-t", f"{vo_dur:.2f}"])
            print(f"  Trimming output to VO duration: {vo_dur:.2f}s")
        print(f"  🎵 BGM ducked under VO: {bgm_path.name} @ vol={bgm_volume}")
    elif has_vo:
        cmd.extend(["-i", str(voiceover)])
        cmd.extend([
            "-c:v", "copy",
            "-c:a", "aac", "-b:a", "192k",
            "-map", "0:v:0", "-map", "1:a:0",
        ])
        if trim_to_vo and vo_dur > 0:
            cmd.extend(["-t", f"{vo_dur:.2f}"])
            print(f"  Trimming output to VO duration: {vo_dur:.2f}s")
    elif has_bgm:
        cmd.extend(["-stream_loop", "-1", "-i", str(bgm_path)])
        cmd.extend([
            "-filter_complex", f"[1:a]volume={bgm_volume * 2.5:.2f}[aout]",
            "-c:v", "copy",
            "-c:a", "aac", "-b:a", "192k",
            "-map", "0:v:0", "-map", "[aout]",
            "-shortest",
        ])
        print(f"  🎵 BGM-only (no VO): {bgm_path.name}")
    else:
        # Silent
        cmd.extend(["-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100"])
        cmd.extend([
            "-c:v", "copy",
            "-c:a", "aac", "-b:a", "128k", "-shortest",
            "-map", "0:v:0", "-map", "1:a:0",
        ])
        print("  No voiceover found — outputting silent reel.")

    cmd.append(str(out_path))

    try:
        subprocess.run(cmd, check=True, timeout=240)
    except subprocess.CalledProcessError as e:
        print(f"Final mux failed: {e}", file=sys.stderr)
        return False

    return out_path.exists()


def qc_checks(scenes_meta: list[dict], voiceover: Path | None, assets: list[dict]) -> None:
    """Lightweight QC — warn on common problems. Advisory only, doesn't block."""
    print("\n▶ QC checks")
    # 1. Scene count vs asset count
    if len(scenes_meta) != len(assets):
        print(f"  ⚠ Scene count mismatch: draft has {len(scenes_meta)} scenes but only {len(assets)} assets found")
    # 2. Scene type distribution
    types = [s.get("scene_type", "?") for s in scenes_meta]
    print(f"  Scene types: {', '.join(types)}")
    # 3. Total video duration vs VO duration
    total_video = sum(s.get("duration_sec", 4.0) for s in scenes_meta)
    vo_dur = get_audio_duration_sec(voiceover) if voiceover and voiceover.exists() else 0.0
    print(f"  Total video: {total_video:.1f}s · Voiceover: {vo_dur:.1f}s")
    if voiceover and voiceover.exists():
        diff = abs(total_video - vo_dur)
        if diff > 3.0:
            print(f"  ⚠ Video/VO duration mismatch {diff:.1f}s (>3s) — video will be trimmed/padded")
        else:
            print(f"  ✓ Video/VO within 3s ({diff:.1f}s diff)")
    # 4. Warn if any scene > 6s (too slow for modern reel pacing)
    slow_scenes = [s["n"] for s in scenes_meta if s.get("duration_sec", 4.0) > 6.0]
    if slow_scenes:
        print(f"  ⚠ Scenes {slow_scenes} > 6s each (consider shortening for Reel pacing)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--draft", type=Path, help="Reel draft .md (reads entry_id from frontmatter)")
    ap.add_argument("--entry-id", help="Override entry_id explicitly")
    ap.add_argument("--brand-folder", type=Path, default=DEFAULT_BRAND)
    ap.add_argument("--out", type=Path, help="Output MP4 path (default: brand/queue/assets/<entry_id>/reel.mp4)")
    ap.add_argument("--no-trim", action="store_true",
                    help="Don't trim final to voiceover length (keep full video duration).")
    ap.add_argument("--legacy", action="store_true",
                    help="Legacy mode: uniform Ken Burns, no per-scene-type motion.")
    # v6 polish flags
    ap.add_argument("--no-polish", action="store_true",
                    help="Disable cinematic color-grade + vignette + film grain.")
    ap.add_argument("--no-flash", action="store_true",
                    help="Disable 2-frame white flash between scenes (hard cuts only).")
    ap.add_argument("--bgm", type=Path, default=None,
                    help="Explicit BGM track (mp3). Overrides pillar auto-resolve.")
    ap.add_argument("--pillar", default=None,
                    help="Pillar hint for BGM auto-resolve (lp-craft, solo-ops, paid-media).")
    ap.add_argument("--bgm-volume", type=float, default=0.22,
                    help="BGM volume multiplier (0.0-1.0). Default 0.22. Gets ducked under VO.")
    ap.add_argument("--no-bgm", action="store_true",
                    help="Disable BGM even if a track is resolved.")
    args = ap.parse_args()

    if args.draft:
        if not args.draft.exists():
            sys.exit(f"Draft not found: {args.draft}")
        fm = read_frontmatter(args.draft)
        entry_id = fm.get("entry_id") or args.entry_id
    else:
        entry_id = args.entry_id

    if not entry_id:
        sys.exit("Must provide --draft (with entry_id in frontmatter) or --entry-id.")

    assets_dir = args.brand_folder / "brand" / "queue" / "assets" / entry_id
    if not assets_dir.exists():
        sys.exit(f"Assets folder not found: {assets_dir}\n"
                 f"Expected: brand/queue/assets/{entry_id}/scene-N.{{mp4,png,jpg}} …")

    # ── v2: per-scene routing using scene_type from the draft ──
    scenes_meta = []
    if args.draft and not args.legacy:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        try:
            from generate_tow_prompts import read_md, parse_scenes  # type: ignore
            _fm, body = read_md(args.draft)
            scenes_meta = parse_scenes(body)
        except Exception as e:
            print(f"  ⚠ Couldn't parse scene breakdown ({e}). Falling back to legacy mode.")
            args.legacy = True

    if args.legacy or not scenes_meta:
        # LEGACY PATH: old uniform Ken Burns
        scenes, mode = collect_scenes_legacy(assets_dir)
        if not scenes:
            sys.exit(f"No assets found in {assets_dir}.")
        if mode == "image":
            print(f"\n▶ [legacy] Image mode ({len(scenes)} scenes). Uniform Ken Burns...")
            import tempfile as _tempfile
            td = Path(_tempfile.mkdtemp(prefix="reel-ken-"))
            scenes = images_to_scene_videos(scenes, td)
            if not scenes:
                sys.exit("All Ken Burns renders failed.")
    else:
        # V2/V4/V5 PATH: per-scene-type routing + auto-invoke Hyperframes + Veo alignment
        voiceover_for_chunks = assets_dir / "voiceover.mp3"
        assets = collect_scene_assets(assets_dir, len(scenes_meta), scenes_meta,
                                       voiceover_path=voiceover_for_chunks if voiceover_for_chunks.exists() else None)
        if not assets:
            sys.exit(f"No scene assets found in {assets_dir}.\n"
                     f"Expected: scene-1.{{png,jpg,mp4}} … scene-{len(scenes_meta)}.{{png,jpg,mp4}}\n"
                     f"Or pre-rendered Hyperframes clips: scene-N-hf.mp4")

        voiceover_check = assets_dir / "voiceover.mp3"
        voiceover_check = voiceover_check if voiceover_check.exists() else None
        qc_checks(scenes_meta, voiceover_check, assets)

        print(f"\n▶ v2 hybrid-engine mode ({len(assets)} scenes, per-type motion)...")
        import tempfile as _tempfile
        td = Path(_tempfile.mkdtemp(prefix="reel-v2-"))
        scenes = render_scene_videos(assets, scenes_meta, td)
        if not scenes:
            sys.exit("All scene renders failed.")

    voiceover = assets_dir / "voiceover.mp3"
    if not voiceover.exists():
        print(f"⚠ No voiceover.mp3 in {assets_dir}. Output will be silent.")
        voiceover = None

    out = args.out or (assets_dir / "reel.mp4")

    print(f"\n▶ Reel assembly")
    print(f"  Entry: {entry_id}")
    print(f"  Scenes: {len(scenes)} ({', '.join(s.name for s in scenes)})")
    print(f"  Voiceover: {voiceover.name if voiceover else '(none, silent)'}")
    print(f"  Output: {out}")

    # Resolve BGM path: explicit --bgm > pillar hint > nothing
    bgm_path = None
    if not args.no_bgm:
        if args.bgm and args.bgm.exists():
            bgm_path = args.bgm
        else:
            pillar_hint = args.pillar
            if not pillar_hint and args.draft:
                pillar_hint = (fm.get("pillar") if isinstance(fm, dict) else None)
            bgm_path = resolve_bgm(args.brand_folder, pillar_hint=pillar_hint)
            if bgm_path:
                print(f"  🎵 Auto-resolved BGM: {bgm_path.name} (pillar={pillar_hint or 'n/a'})")
            elif (args.brand_folder / "brand" / "music").exists():
                print(f"  ℹ No BGM track matched — drop MP3s in brand/_engine/music/ to enable")

    ok = assemble(scenes, voiceover, out,
                  trim_to_vo=not args.no_trim,
                  apply_polish=not args.no_polish,
                  apply_flash=not args.no_flash,
                  bgm_path=bgm_path,
                  bgm_volume=args.bgm_volume)
    if ok:
        size = out.stat().st_size
        print(f"\n✓ Reel assembled: {out} ({size:,} bytes)")
        print(f"  Open: open '{out}'")
        subprocess.run(["osascript", "-e",
                        f'display notification "Reel ready · {size//1024} KB" '
                        f'with title "Reel assembled" sound name "Glass"'],
                       capture_output=True, timeout=5)
    else:
        sys.exit("✗ Assembly failed.")


if __name__ == "__main__":
    main()
