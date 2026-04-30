#!/usr/bin/env python3
"""parse_brief.py — normalize storyboard JSON or free-form markdown brief into scene-plan.json.

Forms accepted:
  A) ad-copywriter `*-storyboard.json` (preferred) — has frames with visual_prompt, motion, vo
  B) free-form markdown brief (5+ lines: client, format, mood, key shots)

Output: scene-plan.json conforming to references/storyboard-schema.md.

Usage:
    python3 parse_brief.py <input> --client "<C>" --project "<P>" \\
        --aspect 9:16 --duration 30 --output scene-plan.json [--force-model M]
"""
import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# Model cost matrix (credits per clip) — verified against Higgsfield models_explore 2026-04-30
# Keep in sync with references/model-routing.md
MODEL_COSTS = {
    "veo3_1": 50,
    "veo3_1_lite": 20,
    "veo3": 35,
    "kling3_0": 6,
    "kling2_6": 8,
    "minimax_hailuo": 10,
    "seedance_2_0": 25,
    "seedance_1_5": 18,
    "wan2_6": 30,
    "wan2_7": 35,
    "marketing_studio_video": 30,
    "cinematic_studio_3_0": 60,
    "grok_video": 25,
}

# Tag -> model decision tree (mirror of model-routing.md). Verified IDs.
TAG_TO_MODEL = [
    (("ad_ugc", "ad_tutorial", "ad_unboxing", "ad_product_review", "ad_tv_spot"), "marketing_studio_video"),
    (("hero", "key_brand_moment", "money_shot"), "veo3_1"),
    (("establishing",), "veo3_1_lite"),  # cheaper Veo for non-money establishing shots
    (("stylized", "anime", "abstract"), "wan2_6"),
    (("product", "text_on_screen", "ui_demo"), "seedance_2_0"),
    (("dialogue", "character_action"), "minimax_hailuo"),
    (("cinematic_premium",), "cinematic_studio_3_0"),
    (("lifestyle", "broll", "transition"), "kling3_0"),
]

# Prompt-language inference rules (when scenes are untagged)
INFERENCE = [
    (re.compile(r"\b(unboxing|product review|tutorial|UGC|user[- ]generated)\b", re.I), "ad_ugc"),
    (re.compile(r"\b(wide shot|drone|aerial|sweeping)\b", re.I), "hero"),
    (re.compile(r"\b(establishing|opening shot|landscape)\b", re.I), "establishing"),
    (re.compile(r"\b(product|close[- ]?up|screen recording|UI|logo|interface)\b", re.I), "product"),
    (re.compile(r"\b(talking|speaking|conversation|dialogue|says|tells)\b", re.I), "dialogue"),
    (re.compile(r"\b(yoga|lifestyle|morning routine|outdoor|walking|smiling|laughing)\b", re.I), "lifestyle"),
    (re.compile(r"\b(anime|illustrated|cartoon|abstract|stylized)\b", re.I), "stylized"),
]


def infer_tags(prompt: str) -> list[str]:
    tags = []
    for rx, tag in INFERENCE:
        if rx.search(prompt):
            tags.append(tag)
    return tags or ["broll"]


def route_model(tags: list[str], force: str | None) -> tuple[str, int]:
    if force:
        return force, MODEL_COSTS.get(force, 50)
    for keys, model in TAG_TO_MODEL:
        if any(t in keys for t in tags):
            return model, MODEL_COSTS[model]
    return "kling-3.0", MODEL_COSTS["kling-3.0"]


def parse_storyboard_json(p: Path) -> dict:
    data = json.loads(p.read_text())
    frames = data.get("frames", [])
    if not frames:
        raise ValueError(f"{p}: no 'frames' key found — not an ad-copywriter storyboard")
    return data


def parse_markdown_brief(p: Path) -> dict:
    """Extract client, project, format, aspect, duration, mood, key_shots from a markdown brief.

    Expected loose format (case-insensitive labels):
        client: ...
        project: ...
        format: ... (e.g. "9:16 reel, 30 seconds")
        mood: ...
        key shots:
          - shot 1
          - shot 2
    """
    raw = p.read_text()
    fields: dict[str, str] = {}
    shots: list[str] = []
    current_list_key = None
    for line in raw.splitlines():
        line = line.rstrip()
        if not line:
            continue
        if line.lstrip().startswith(("-", "*")) and current_list_key:
            shots.append(line.lstrip("-* ").strip())
            continue
        m = re.match(r"^([a-zA-Z _]+):\s*(.*)$", line)
        if m:
            key = m.group(1).strip().lower().replace(" ", "_")
            val = m.group(2).strip()
            if key in {"key_shots", "shots", "scenes"} and not val:
                current_list_key = key
            else:
                fields[key] = val
                current_list_key = None
    if not shots:
        raise ValueError(f"{p}: no 'key shots:' bullet list found")
    return {
        "client": fields.get("client", "Unknown"),
        "project": fields.get("project", "Unknown"),
        "format_str": fields.get("format", "9:16 reel, 30 seconds"),
        "music_mood": fields.get("mood", "neutral"),
        "key_shots": shots,
        "voiceover_full": fields.get("voiceover", ""),
    }


def expand_markdown_to_scenes(parsed: dict, duration: int) -> list[dict]:
    """Expand each key shot into a scene with sane defaults.

    For Form B without explicit per-frame prompts, distribute duration evenly.
    Mayank can refine per scene before generation.
    """
    n = len(parsed["key_shots"])
    per_scene = max(3, min(10, duration // n))  # 3-10s per Higgsfield clip cap
    scenes_raw = []
    for i, shot in enumerate(parsed["key_shots"], start=1):
        scenes_raw.append({
            "frame_id": f"{i:02d}",
            "duration_sec": per_scene,
            "visual_prompt": shot,
            "motion": "static" if i == 1 else "slow_pan",
            "voiceover": "",
            "voice_direction": "neutral",
            "music": parsed["music_mood"],
        })
    return scenes_raw


def normalize_scenes(frames: list[dict], force_model: str | None) -> list[dict]:
    out = []
    for f in frames:
        prompt = f.get("visual_prompt", "").strip()
        tags = infer_tags(prompt)
        model, credits = route_model(tags, force_model)
        out.append({
            "scene_id": str(f.get("frame_id", "")).zfill(2),
            "duration_sec": int(f.get("duration_sec", 5)),
            "tags": tags,
            "model_choice": model,
            "model_credits": credits,
            "prompt": prompt,
            "motion_preset": f.get("motion", "static"),
            "reference_image": f.get("reference_image"),
            "seed": f.get("seed"),
            "vo_text": f.get("voiceover", ""),
            "vo_emotion_tags": [f.get("voice_direction", "neutral").split(",")[0].strip()],
            "music_cue": f.get("music", ""),
            "source": "[INFERRED-from-brief]" if not prompt else "[EXTRACTED-from-storyboard]",
        })
    return out


def parse_format_str(s: str) -> tuple[str, int]:
    """Parse '9:16 reel, 30 seconds' → ('9:16', 30)."""
    aspect_m = re.search(r"(\d+:\d+)", s)
    dur_m = re.search(r"(\d+)\s*(?:s|sec|seconds)", s)
    return (
        aspect_m.group(1) if aspect_m else "9:16",
        int(dur_m.group(1)) if dur_m else 30,
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input", help="Path to storyboard JSON or markdown brief")
    ap.add_argument("--client", required=True)
    ap.add_argument("--project", required=True)
    ap.add_argument("--aspect", default=None, help="e.g. 9:16, 16:9, 1:1")
    ap.add_argument("--duration", type=int, default=None, help="Total seconds")
    ap.add_argument("--output", required=True, help="Output scene-plan.json path")
    ap.add_argument("--force-model", default=None, help="Override router for all scenes")
    args = ap.parse_args()

    inp = Path(args.input)
    if not inp.exists():
        print(f"✗ Input not found: {inp}", file=sys.stderr)
        return 1

    if inp.suffix.lower() == ".json":
        data = parse_storyboard_json(inp)
        aspect, duration = (
            args.aspect or data.get("format", {}).get("aspect", "9:16"),
            args.duration or data.get("format", {}).get("total_duration_sec", 30),
        )
        if isinstance(aspect, str) and "," in aspect:
            aspect = aspect.split(",")[0].strip()
        scenes = normalize_scenes(data["frames"], args.force_model)
        vo_full = data.get("voiceover_full", "")
        music_mood = data.get("music_mood", "neutral")
    else:
        parsed = parse_markdown_brief(inp)
        aspect_p, duration_p = parse_format_str(parsed["format_str"])
        aspect = args.aspect or aspect_p
        duration = args.duration or duration_p
        frames = expand_markdown_to_scenes(parsed, duration)
        scenes = normalize_scenes(frames, args.force_model)
        vo_full = parsed["voiceover_full"]
        music_mood = parsed["music_mood"]

    # Reconcile total duration vs sum-of-scenes
    total_sec = sum(s["duration_sec"] for s in scenes)
    if abs(total_sec - duration) > 1:
        # Pad or trim last scene
        delta = duration - total_sec
        scenes[-1]["duration_sec"] = max(3, scenes[-1]["duration_sec"] + delta)

    estimated_credits = sum(s["model_credits"] for s in scenes)

    plan = {
        "creative_id": Path(inp).stem,
        "client": args.client,
        "project": args.project,
        "format": {"aspect": aspect, "total_duration_sec": duration, "fps": 30},
        "voiceover_full": vo_full,
        "music_mood": music_mood,
        "estimated_credits": estimated_credits,
        "scenes": scenes,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(plan, indent=2))

    # Print summary
    print(f"\nScene plan: {out_path}\n")
    print(f"  Client: {args.client}  Project: {args.project}")
    print(f"  Format: {aspect} @ {duration}s, {len(scenes)} scenes")
    print(f"  Estimated cost: {estimated_credits} credits  (~${estimated_credits * 0.04:.2f} at Plus tier)")
    print()
    for s in scenes:
        print(f"  {s['scene_id']}  {','.join(s['tags']):20s}  {s['model_choice']:14s}  {s['model_credits']:3d} cr   {s['prompt'][:60]}")
    print()

    # Cost guardrails
    if estimated_credits > 500:
        print(f"⚠ Cost {estimated_credits} cr exceeds 500 — abort. Reduce scene count or force cheaper models.", file=sys.stderr)
        return 2
    if estimated_credits > 250:
        print(f"⚠ Cost {estimated_credits} cr > 250 — re-run generation with --confirm-cost", file=sys.stderr)
    elif estimated_credits > 100:
        print(f"⚠ Cost {estimated_credits} cr > 100 — proceed with caution", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
