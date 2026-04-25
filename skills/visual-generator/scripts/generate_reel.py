#!/usr/bin/env python3
"""
generate_reel.py — v7 Remotion-first reel orchestrator.

Takes a reel draft (markdown with YAML frontmatter + `## Scene breakdown`) and:
  1. Parses scene breakdown → list of {n, scene_type, vo, overlay, mood}
  2. Ensures voiceover.mp3 exists (invokes clone_voice.py if missing)
  3. Builds per-scene Remotion props JSON with word-timestamps
  4. Invokes `npx remotion render` per scene → scene-N-rmt.mp4
  5. Stitches scenes with ffmpeg (polish + flash + BGM ducking)

Smoke-test mode: if `--hard-coded-timestamps wellness-lp` is passed, uses
built-in word-timestamps from the Root.tsx smoke-test set. For real reels,
run extract_word_timestamps.py first to produce voiceover.words.json.

Stitch logic ports POLISH_FILTER + generate_flash_clip + _mux_audio from
.archive-v6/assemble_reel.py (preserved during 2026-04-21 v5→v7 cleanup).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

# Shared notify helper (click-through)
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "shared-scripts"))
try:
    from notify import notify as _notify, notify_reviewable_artifact  # type: ignore
except ImportError:
    _notify = None
    notify_reviewable_artifact = None

# ── Paths ──────────────────────────────────────────────────────────────────
DEFAULT_BRAND = Path("/Users/digischola/Desktop/Digischola")
REMOTION_STUDIO = DEFAULT_BRAND / "brand" / "remotion-studio"
HYPERFRAMES_SCENES = DEFAULT_BRAND / "brand" / "hyperframes-scenes"
SKILL_SCRIPTS = Path(__file__).resolve().parent
NPX = shutil.which("npx") or "/opt/homebrew/bin/npx"
BUNX = os.path.expanduser("~/.bun/bin/bunx")

# Dual-engine routing (v7.4). Maps scene_type → engine.
# Source of truth: scripts/scene_spec.py::SCENE_ROUTING.
# Duplicated here to avoid import-time side effects; keep in sync.
SCENE_ROUTING = {
    "hook":          "remotion",
    "problem_beat":  "remotion",
    "insight_beat":  "remotion",
    "data_reveal":   "remotion",
    "cta":           "remotion",
    "outro":         "remotion",
    # Social-platform overlay scenes → Hyperframes catalog blocks
    "x_post_overlay":        "hyperframes",
    "instagram_follow":      "hyperframes",
    "tiktok_follow":         "hyperframes",
    "reddit_overlay":        "hyperframes",
    "spotify_now_playing":   "hyperframes",
    "macos_notification":    "hyperframes",
    "yt_subscribe_cta":      "hyperframes",
}
HYPERFRAMES_CATALOG_MAP = {
    "x_post_overlay":       "x-post",
    "instagram_follow":     "instagram-follow",
    "tiktok_follow":        "tiktok-follow",
    "reddit_overlay":       "reddit-post",
    "spotify_now_playing":  "spotify-card",
    "macos_notification":   "macos-notification",
    "yt_subscribe_cta":     "yt-lower-third",
}

# ── Scene classifier (ported from .archive-v6/generate_tow_prompts.py; v7.4 extended for Hyperframes scenes) ─────
HEADING_LABEL_MAP = {
    # ── Remotion-routed (v7.3 UI-mockup primitives)
    "hook": "hook",
    "problem": "problem_beat",
    "tension": "problem_beat",
    "b-roll": "problem_beat",
    "cutaway": "problem_beat",
    "the rule": "insight_beat",
    "the shift": "insight_beat",
    "the truth": "insight_beat",
    "the lesson": "insight_beat",
    "insight": "insight_beat",
    "the data": "data_reveal",
    "data": "data_reveal",
    "stat": "data_reveal",
    "proof": "data_reveal",
    "cta": "cta",
    "close": "cta",
    "handoff": "cta",
    "outro": "outro",
    "brand mark": "outro",
    "sign-off": "outro",

    # ── Hyperframes-routed (v7.4 catalog block overlays)
    "x post": "x_post_overlay",
    "twitter post": "x_post_overlay",
    "tweet": "x_post_overlay",
    "instagram follow": "instagram_follow",
    "ig follow": "instagram_follow",
    "tiktok follow": "tiktok_follow",
    "tt follow": "tiktok_follow",
    "reddit post": "reddit_overlay",
    "reddit": "reddit_overlay",
    "spotify": "spotify_now_playing",
    "now playing": "spotify_now_playing",
    "macos notification": "macos_notification",
    "notification": "macos_notification",
    "youtube subscribe": "yt_subscribe_cta",
    "yt lower third": "yt_subscribe_cta",
    "subscribe": "yt_subscribe_cta",
}

# Map scene_type → Remotion composition ID
SCENE_COMPOSITION = {
    "hook": "KineticHook",
    "problem_beat": "ProblemBeat",
    "insight_beat": "InsightBeat",
    "data_reveal": "DataReveal",
    "cta": "OutroCard",     # CTA uses same composition as outro
    "outro": "OutroCard",
}

SCENE_DURATION = {
    # Remotion-routed (must match theme/brand.ts::sceneDuration)
    "hook": 2.9,
    "problem_beat": 3.3,
    "insight_beat": 5.0,
    "data_reveal": 3.8,
    "cta": 4.0,
    "outro": 3.8,
    # Hyperframes-routed (match catalog block default durations)
    "x_post_overlay": 5.0,
    "instagram_follow": 4.5,
    "tiktok_follow": 4.5,
    "reddit_overlay": 5.0,
    "spotify_now_playing": 5.0,
    "macos_notification": 5.0,
    "yt_subscribe_cta": 4.5,
}

HEADING_LABEL_RE = re.compile(r"—\s*([A-Za-z][A-Za-z\s]*?)\s*$")


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


def parse_scenes(draft_path: Path) -> list[dict]:
    """Parse ## Scene breakdown section into [{n, scene_type, vo, overlay, mood}]."""
    text = draft_path.read_text(encoding="utf-8")
    # Find scene breakdown section
    m = re.search(r"##\s+Scene breakdown.*?$", text, re.MULTILINE)
    if not m:
        sys.exit("No ## Scene breakdown section found in draft.")
    scenes_body = text[m.end():]
    # Split on ### Scene N headings
    scene_blocks = re.split(r"^###\s+Scene\s+", scenes_body, flags=re.MULTILINE)[1:]
    scenes = []
    for block in scene_blocks:
        header_line = block.split("\n", 1)[0]
        # Extract label after em-dash
        label_match = HEADING_LABEL_RE.search(header_line)
        heading_label = label_match.group(1).strip().lower() if label_match else ""
        scene_type = HEADING_LABEL_MAP.get(heading_label)
        if not scene_type:
            # Try content-cue fallback
            for key, mapped in HEADING_LABEL_MAP.items():
                if key in heading_label.lower():
                    scene_type = mapped
                    break
            if not scene_type:
                scene_type = "insight_beat"  # default

        # Extract scene number
        n_match = re.match(r"(\d+)", header_line)
        n = int(n_match.group(1)) if n_match else len(scenes) + 1

        # Extract fields from bullet points
        vo = _extract_bullet_field(block, "VO")
        visual = _extract_bullet_field(block, "Visual")
        mood = _extract_bullet_field(block, "Mood")
        overlay = _extract_bullet_field(block, "On-screen text overlay") or \
                  _extract_bullet_field(block, "Overlay")

        scenes.append({
            "n": n,
            "scene_type": scene_type,
            "vo": vo,
            "visual": visual,
            "mood": mood,
            "overlay": overlay,
            "duration_sec": SCENE_DURATION.get(scene_type, 4.0),
        })
    return scenes


def _extract_bullet_field(block: str, name: str) -> str:
    """Extract `- Field: value` from scene block."""
    m = re.search(rf"^\s*-\s*{re.escape(name)}:\s*(.+)$", block, re.MULTILINE)
    return m.group(1).strip().strip('"').strip() if m else ""


# ── Word-timestamp loader ──────────────────────────────────────────────────
# Smoke-test mode: hand-tagged timestamps matching the wellness-LP draft.
# Real pipeline will load these from <assets>/voiceover.words.json (produced
# by extract_word_timestamps.py in Phase 9).

SMOKE_TIMESTAMPS = {
    # scene_n → words array (each scene's VO starts at t=0 for that scene)
    1: [  # hook
        {"word": "I", "start": 0.05, "end": 0.2},
        {"word": "audited", "start": 0.22, "end": 0.62, "emphasis": "insight"},
        {"word": "40", "start": 0.66, "end": 0.9, "emphasis": "hook"},
        {"word": "wellness", "start": 0.95, "end": 1.35},
        {"word": "retreat", "start": 1.4, "end": 1.78},
        {"word": "pages.", "start": 1.82, "end": 2.4},
    ],
    2: [  # problem_beat
        {"word": "Most", "start": 0.1, "end": 0.38},
        {"word": "spent", "start": 0.42, "end": 0.8, "emphasis": "insight"},
        {"word": "5", "start": 0.85, "end": 1.02, "emphasis": "hook"},
        {"word": "seconds", "start": 1.06, "end": 1.55},
        {"word": "saying", "start": 1.6, "end": 2.0},
        {"word": "nothing.", "start": 2.05, "end": 2.8, "emphasis": "insight"},
    ],
    3: [  # insight_beat
        {"word": "Here's", "start": 0.1, "end": 0.45},
        {"word": "the", "start": 0.48, "end": 0.62},
        {"word": "rule:", "start": 0.66, "end": 1.0, "emphasis": "insight"},
        {"word": "If", "start": 1.2, "end": 1.35},
        {"word": "visitors", "start": 1.4, "end": 1.9},
        {"word": "scroll", "start": 1.95, "end": 2.35, "emphasis": "insight"},
        {"word": "to", "start": 2.4, "end": 2.55},
        {"word": "understand,", "start": 2.6, "end": 3.3},
        {"word": "you've", "start": 3.4, "end": 3.75},
        {"word": "lost", "start": 3.8, "end": 4.15, "emphasis": "insight"},
        {"word": "them.", "start": 4.2, "end": 4.5},
    ],
    4: [  # data_reveal
        {"word": "Form", "start": 0.1, "end": 0.4},
        {"word": "cuts", "start": 0.44, "end": 0.8},
        {"word": "alone", "start": 0.85, "end": 1.25},
        {"word": "lift", "start": 1.3, "end": 1.65, "emphasis": "insight"},
        {"word": "conversion", "start": 1.7, "end": 2.35},
        {"word": "120%.", "start": 2.4, "end": 3.3, "emphasis": "insight"},
    ],
    5: [  # outro/cta (no caption needed — OutroCard renders its own CTA text)
    ],
}


# ── Remotion rendering ─────────────────────────────────────────────────────

def build_props_for_scene(scene: dict, smoke_test: bool = True) -> dict:
    """Build the props object passed to the Remotion composition."""
    scene_type = scene["scene_type"]
    n = scene["n"]
    words = SMOKE_TIMESTAMPS.get(n, []) if smoke_test else []

    if scene_type == "hook":
        return {"words": words, "meshTone": "neutral", "showLogo": True}
    if scene_type == "problem_beat":
        return {"words": words}
    if scene_type == "insight_beat":
        return {"words": words}
    if scene_type == "data_reveal":
        # Try to extract number + eyebrow from overlay/vo heuristically
        combined = f"{scene.get('overlay', '')} {scene.get('vo', '')}"
        num_match = re.search(r"(\+|-)?(\d+(?:\.\d+)?)\s*(%|x|K)?", combined)
        sign = (num_match.group(1) or "+") if num_match else "+"
        number = int(float(num_match.group(2))) if num_match else 120
        suffix = (num_match.group(3) or "%") if num_match else "%"
        return {
            "number": number,
            "suffix": suffix,
            "sign": sign,
            "eyebrow": "RESULT",
            "sublabel": "LIFT" if sign == "+" else "DROP",
            "words": words,
        }
    if scene_type in ("cta", "outro"):
        overlay = scene.get("overlay", "")
        url_match = re.search(
            r"([a-zA-Z0-9][a-zA-Z0-9\-.]*\.(?:com|in|io|co|app|me)(?:/[^\s]*)?)",
            overlay,
        )
        cta_url = url_match.group(1).upper() if url_match else "DIGISCHOLA.IN"
        vo_clauses = [c.strip() for c in re.split(r"[.!?]", scene.get("vo", "")) if c.strip()]
        imperatives = ("audit", "try", "save", "get", "grab", "book", "join",
                       "start", "build", "check", "watch", "follow", "dm", "visit")
        cta_text = "LINK IN BIO"
        for clause in vo_clauses:
            fw = clause.lower().split(" ")[0] if clause else ""
            if fw in imperatives:
                cta_text = " ".join(clause.split()[:4]).upper().rstrip(".,!?")
                break
        return {"ctaText": cta_text, "ctaUrl": cta_url, "handle": "DIGISCHOLA"}
    return {}


def render_scene_remotion(scene: dict, out_mp4: Path, smoke_test: bool = True) -> bool:
    """Invoke `npx remotion render` for a scene."""
    scene_type = scene["scene_type"]
    comp_id = SCENE_COMPOSITION.get(scene_type)
    if not comp_id:
        print(f"  ⚠ No composition mapped for scene_type={scene_type}", file=sys.stderr)
        return False

    props = build_props_for_scene(scene, smoke_test=smoke_test)
    # Write props to temp file (Remotion --props accepts inline JSON OR file path)
    props_file = Path(tempfile.mkstemp(suffix=".json")[1])
    props_file.write_text(json.dumps(props, indent=2))

    print(f"  ▶ [Remotion] Rendering scene {scene['n']} [{scene_type}] → {comp_id}")
    cmd = [
        NPX, "remotion", "render", comp_id,
        f"--props={props_file}",
        str(out_mp4),
    ]
    try:
        r = subprocess.run(cmd, cwd=REMOTION_STUDIO, check=False, timeout=300)
        return r.returncode == 0 and out_mp4.exists()
    except subprocess.TimeoutExpired:
        print(f"  ✗ Render timed out for scene {scene['n']}", file=sys.stderr)
        return False
    finally:
        props_file.unlink(missing_ok=True)


def render_scene_hyperframes(scene: dict, out_mp4: Path) -> bool:
    """Render a scene via `bunx hyperframes render`.

    Uses a per-scene project under brand/hyperframes-scenes/runs/<entry>-<n>/.
    Expected workflow:
      1. A catalog block (e.g. x-post.html) was pre-installed via `hyperframes add`
      2. A template index.html in hyperframes-scenes/templates/<scene_type>/ exists
         OR the catalog block is rendered standalone with data from `scene`
      3. This function copies the template to a temp project dir, substitutes
         placeholders, runs `bunx hyperframes render`, returns the MP4
    """
    scene_type = scene["scene_type"]
    catalog = HYPERFRAMES_CATALOG_MAP.get(scene_type)
    if not catalog:
        print(f"  ⚠ No catalog block mapped for scene_type={scene_type}", file=sys.stderr)
        return False

    block_file = HYPERFRAMES_SCENES / "compositions" / f"{catalog}.html"
    if not block_file.exists():
        print(f"  ✗ Catalog block not installed: {block_file}", file=sys.stderr)
        print(f"    Run: cd {HYPERFRAMES_SCENES} && bunx hyperframes add {catalog}", file=sys.stderr)
        return False

    # Per-scene working project
    run_dir = HYPERFRAMES_SCENES / "runs" / f"scene-{scene['n']}-{scene_type}"
    run_dir.mkdir(parents=True, exist_ok=True)

    # Minimal host index.html that wraps the catalog block in a 1080x1920 canvas
    # with tokens.css applied for brand consistency
    duration_sec = SCENE_DURATION.get(scene_type, 4.0)
    comp_id = f"scene-{scene['n']}-{scene_type}"
    host_html = f"""<!doctype html>
<html lang="en"><head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=1080, height=1920" />
<title>{comp_id}</title>
<link rel="stylesheet" href="../../shared/tokens.css">
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  html, body {{
    width: 1080px; height: 1920px; overflow: hidden;
    background: var(--color-bg-dark);
    font-family: var(--font-grotesk);
  }}
  .stage {{
    position: absolute; inset: 0;
    display: flex; align-items: center; justify-content: center;
  }}
  .block-host {{
    width: 840px; height: 520px;
    position: relative;
  }}
</style></head>
<body>
<div id="root"
     data-composition-id="{comp_id}"
     data-width="1080"
     data-height="1920"
     data-start="0"
     data-duration="{duration_sec}"
     style="position:relative; width:1080px; height:1920px;">
  <div class="atmo-mesh-neutral"></div>
  <div class="stage">
    <div class="block-host">
      <div data-composition-src="{block_file.relative_to(run_dir.parent.parent)}"
           data-start="0"
           data-duration="{duration_sec}"
           data-width="1920"
           data-height="1080"
           data-track-index="1"></div>
    </div>
  </div>
</div>
</body></html>
"""
    (run_dir / "index.html").write_text(host_html, encoding="utf-8")
    (run_dir / "hyperframes.json").write_text(json.dumps({
        "$schema": "https://hyperframes.heygen.com/schema/hyperframes.json",
        "registry": "https://raw.githubusercontent.com/heygen-com/hyperframes/main/registry",
        "paths": {"blocks": "compositions", "components": "compositions/components", "assets": "assets"},
    }, indent=2), encoding="utf-8")

    print(f"  ▶ [Hyperframes] Rendering scene {scene['n']} [{scene_type}] → {catalog} block")
    cmd = [BUNX, "hyperframes", "render", "-q", "standard", "-o", str(out_mp4)]
    try:
        r = subprocess.run(cmd, cwd=run_dir, check=False, timeout=300,
                           env={**os.environ, "PATH": f"{os.path.expanduser('~/.bun/bin')}:{os.environ.get('PATH','')}"})
        return r.returncode == 0 and out_mp4.exists()
    except subprocess.TimeoutExpired:
        print(f"  ✗ Hyperframes render timed out for scene {scene['n']}", file=sys.stderr)
        return False


def render_scene(scene: dict, out_mp4: Path, smoke_test: bool = True,
                 render_log: list | None = None) -> bool:
    """Route scene to the right engine + optionally append to render log."""
    scene_type = scene["scene_type"]
    engine = SCENE_ROUTING.get(scene_type, "remotion")
    start_t = time.time()
    ok = (render_scene_hyperframes(scene, out_mp4)
          if engine == "hyperframes"
          else render_scene_remotion(scene, out_mp4, smoke_test=smoke_test))
    elapsed = time.time() - start_t
    if render_log is not None:
        render_log.append({
            "scene_n": scene["n"],
            "scene_type": scene_type,
            "engine": engine,
            "render_time_sec": round(elapsed, 2),
            "out_file": out_mp4.name,
            "success": ok,
        })
    return ok


# ── Stitch: polish + flash + BGM ducking (ported from .archive-v6/) ────────

POLISH_FILTER = (
    "eq=saturation=1.08:contrast=1.06:brightness=-0.01,"
    "vignette=PI/5,"
    "noise=alls=8:allf=t"
)


def generate_flash_clip(out_path: Path, fps: int = 30, num_frames: int = 2) -> bool:
    duration = num_frames / fps
    try:
        subprocess.run([
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-f", "lavfi",
            "-i", f"color=c=white:s=1080x1920:r={fps}:d={duration:.4f}",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-t", f"{duration:.4f}",
            "-an",
            str(out_path),
        ], check=True, timeout=30)
        return out_path.exists()
    except subprocess.CalledProcessError:
        return False


def get_audio_duration_sec(audio_path: Path) -> float:
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


def stitch_reel(scene_mp4s: list[Path], voiceover: Path | None, bgm: Path | None,
                 out_path: Path, apply_polish: bool = True, apply_flash: bool = True,
                 bgm_volume: float = 0.22) -> bool:
    """Concat scenes → polish → mux VO + optional BGM (ducking) → final MP4."""
    if not scene_mp4s:
        print("No scenes to stitch.", file=sys.stderr)
        return False

    out_path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as td:
        td = Path(td)

        # 1. Optional flash clip between scenes
        flash_clip = None
        if apply_flash and len(scene_mp4s) > 1:
            flash_clip = td / "flash.mp4"
            if not generate_flash_clip(flash_clip):
                flash_clip = None

        # 2. Concat list
        concat_list = td / "concat.txt"
        with open(concat_list, "w") as f:
            for idx, s in enumerate(scene_mp4s):
                f.write(f"file '{str(s).replace(chr(39), chr(39)+chr(92)+chr(39)+chr(39))}'\n")
                if flash_clip and idx < len(scene_mp4s) - 1:
                    f.write(f"file '{flash_clip}'\n")

        # 3. Concat + polish pass (single ffmpeg pass)
        base_vf = "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2"
        full_vf = f"{base_vf},{POLISH_FILTER}" if apply_polish else base_vf
        concat_video = td / "concat.mp4"
        try:
            subprocess.run([
                "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                "-f", "concat", "-safe", "0",
                "-i", str(concat_list),
                "-c:v", "libx264", "-pix_fmt", "yuv420p",
                "-vf", full_vf,
                "-r", "30",
                "-an",
                str(concat_video),
            ], check=True, timeout=240)
        except subprocess.CalledProcessError as e:
            print(f"Concat + polish failed: {e}", file=sys.stderr)
            return False

        # 4. Mux audio
        has_vo = voiceover and voiceover.exists()
        has_bgm = bgm and bgm.exists()
        cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(concat_video)]

        if has_vo and has_bgm:
            cmd.extend(["-i", str(voiceover), "-stream_loop", "-1", "-i", str(bgm)])
            filter_complex = (
                f"[1:a]asplit=2[vo_out][vo_key];"
                f"[2:a]volume={bgm_volume}[bgm_raw];"
                f"[bgm_raw][vo_key]sidechaincompress=threshold=0.04:ratio=8:attack=10:release=400[bgm_ducked];"
                f"[bgm_ducked][vo_out]amix=inputs=2:duration=first:dropout_transition=0:weights=1 2[aout]"
            )
            cmd.extend(["-filter_complex", filter_complex,
                         "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                         "-map", "0:v:0", "-map", "[aout]", "-shortest"])
            vo_dur = get_audio_duration_sec(voiceover)
            if vo_dur > 0:
                cmd.extend(["-t", f"{vo_dur:.2f}"])
            print(f"  🎵 BGM ducked under VO: {bgm.name}")
        elif has_vo:
            cmd.extend(["-i", str(voiceover), "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                         "-map", "0:v:0", "-map", "1:a:0"])
            vo_dur = get_audio_duration_sec(voiceover)
            if vo_dur > 0:
                cmd.extend(["-t", f"{vo_dur:.2f}"])
        else:
            cmd.extend(["-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
                         "-c:v", "copy", "-c:a", "aac", "-b:a", "128k", "-shortest",
                         "-map", "0:v:0", "-map", "1:a:0"])
            print("  No voiceover — silent output")

        cmd.append(str(out_path))
        try:
            subprocess.run(cmd, check=True, timeout=240)
        except subprocess.CalledProcessError as e:
            print(f"Final mux failed: {e}", file=sys.stderr)
            return False

    return out_path.exists()


# ── Main ────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--draft", type=Path, required=True)
    ap.add_argument("--brand-folder", type=Path, default=DEFAULT_BRAND)
    ap.add_argument("--out", type=Path, help="Output MP4 path")
    ap.add_argument("--smoke-test", action="store_true",
                    help="Use hard-coded word-timestamps (skip extraction)")
    ap.add_argument("--skip-render", action="store_true",
                    help="Skip per-scene render if scene-N-rmt.mp4 already exists")
    ap.add_argument("--bgm", type=Path, help="Optional BGM track")
    args = ap.parse_args()

    if not args.draft.exists():
        sys.exit(f"Draft not found: {args.draft}")

    fm = read_frontmatter(args.draft)
    entry_id = fm.get("entry_id") or args.draft.stem
    assets_dir = args.brand_folder / "brand" / "queue" / "assets" / entry_id
    assets_dir.mkdir(parents=True, exist_ok=True)

    scenes = parse_scenes(args.draft)
    print(f"\n▶ Parsed {len(scenes)} scenes: {', '.join(s['scene_type'] for s in scenes)}")

    voiceover = assets_dir / "voiceover.mp3"
    if not voiceover.exists():
        print(f"⚠ No voiceover.mp3 — run clone_voice.py first for {entry_id}")
        voiceover = None

    # Render each scene — dual-engine router (v7.4) picks Remotion or Hyperframes
    # per SCENE_ROUTING, logs metadata to render_log.jsonl for future learning.
    scene_mp4s = []
    render_log: list[dict] = []
    for scene in scenes:
        engine = SCENE_ROUTING.get(scene["scene_type"], "remotion")
        # Filename suffix encodes engine: -rmt for Remotion, -hf for Hyperframes
        suffix = "-hf" if engine == "hyperframes" else "-rmt"
        out_mp4 = assets_dir / f"scene-{scene['n']}{suffix}.mp4"
        if args.skip_render and out_mp4.exists():
            print(f"  ↩ Scene {scene['n']} cached [{engine}]: {out_mp4.name}")
            scene_mp4s.append(out_mp4)
            continue
        if render_scene(scene, out_mp4, smoke_test=args.smoke_test, render_log=render_log):
            scene_mp4s.append(out_mp4)
        else:
            print(f"  ✗ Scene {scene['n']} failed [{engine}] — aborting")
            sys.exit(1)

    # Append to persistent render log — future performance-review can analyze
    # which engine renders which scene_type faster / cleaner / with higher QA pass rate.
    if render_log:
        log_path = assets_dir / "render_log.jsonl"
        with open(log_path, "a") as f:
            for row in render_log:
                row["entry_id"] = entry_id
                f.write(json.dumps(row) + "\n")
        print(f"  ◆ Logged {len(render_log)} render events → {log_path.name}")

    # Stitch
    out_path = args.out or (assets_dir / "reel.mp4")
    print(f"\n▶ Stitching {len(scene_mp4s)} scenes → {out_path}")
    ok = stitch_reel(scene_mp4s, voiceover, args.bgm, out_path)
    if not ok:
        sys.exit("✗ Stitch failed.")

    size = out_path.stat().st_size
    print(f"\n✓ Reel assembled: {out_path} ({size:,} bytes)")

    # ── Automated QA gate ───────────────────────────────────────────────────
    # Ported per playbook v2: validate_reel_output runs 3 checks. Fails loudly
    # with non-zero exit so orchestrator can regenerate without user-in-loop.
    qa_script = SKILL_SCRIPTS / "qa_reel.py"
    if qa_script.exists():
        print(f"\n▶ Running QA gate...")
        qa_result = subprocess.run([
            "/opt/homebrew/bin/python3.11", str(qa_script),
            "--reel", str(out_path),
        ], capture_output=False, timeout=180)
        if qa_result.returncode != 0:
            print("⚠ QA gate flagged issues — review frames before shipping.")

    # Click-to-open notification (2026-04-22 UX batch). Land on the draft's
    # card in review_queue so user can Approve/Edit/Reject inline.
    try:
        if notify_reviewable_artifact is not None:
            notify_reviewable_artifact(
                title=f"Reel v7 ready: {entry_id}",
                body=f"{size // 1024} KB · Click to review.",
                entry_id=entry_id,
                brand_folder=args.brand_folder,
                subtitle="Digischola",
                sound="Glass",
                visual_only=True,
            )
        elif _notify is not None:
            _notify(
                f"Reel v7 ready: {entry_id}",
                f"{size // 1024} KB. Click to open review UI.",
                subtitle="Digischola", sound="Glass",
                open_url="http://127.0.0.1:8765/",
                group="digischola-render",
            )
    except Exception as e:
        print(f"  (notification failed: {e})", file=sys.stderr)


if __name__ == "__main__":
    main()
