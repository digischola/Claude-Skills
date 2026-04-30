#!/usr/bin/env python3
"""generate_scenes.py — orchestrate Higgsfield MCP calls per scene.

Architecture note: Python scripts cannot directly invoke Claude Code MCP tools.
This script runs in two modes:

  1. --plan      Read scene-plan.json, write mcp-call-queue.json — one entry per
                 scene with the MCP tool name + args. Idempotent: skips scenes
                 whose scenes/<scene_id>.mp4 already exists.

  2. --finalize  Read manifest.json (Claude wrote it after making the MCP calls)
                 and validate every queued scene now has a corresponding MP4.

Between the two phases, Claude (in-session) reads mcp-call-queue.json and invokes
the Higgsfield MCP tools, downloads each result to scenes/<scene_id>.mp4, and
appends manifest entries.

Usage:
    python3 generate_scenes.py --plan <working_dir>
    python3 generate_scenes.py --finalize <working_dir>
"""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Higgsfield MCP exposes a SINGLE `generate_video` tool. Text-to-video vs image-to-video
# is determined by the presence of `medias[]` with a `start_image` (or `image`) role.
# Verified via models_explore + tool schema 2026-04-30 — note Higgsfield does NOT host Sora 2.
MCP_TOOL_NAME = "mcp__b39cf66e-63d0-49fc-a861-0eb724d588df__generate_video"

# model_id values verified against models_explore. Each entry includes any model-specific
# top-level parameters Higgsfield expects (passed alongside model/prompt/aspect_ratio).
MODEL_PARAMS = {
    "veo3_1":               {},  # supports quality (basic/high/ultra), durations [4,6,8]
    "veo3_1_lite":          {},  # durations [4,6,8]
    "veo3":                 {},  # requires start_image
    "kling3_0":             {},  # mode pro/std, duration_range 3-15
    "kling2_6":             {"sound": True},
    "minimax_hailuo":       {},  # durations [6,10]
    "seedance_2_0":         {"resolution": "720p"},  # duration 4-15
    "seedance_1_5":         {"resolution": "720p"},  # durations [4,8,12]
    "wan2_6":               {"quality": "720p"},  # REQUIRES start_image
    "wan2_7":               {"resolution": "720p"},
    "marketing_studio_video": {"resolution": "720p"},  # has UGC/Tutorial/Unboxing/etc modes
    "cinematic_studio_3_0": {},  # duration 4-15
    "grok_video":           {},
}

# Models that REQUIRE a reference image (image-to-video only)
REQUIRES_IMAGE = {"wan2_6", "veo3"}


def aspect_to_dims(aspect: str) -> tuple[int, int]:
    return {
        "9:16": (1080, 1920),
        "16:9": (1920, 1080),
        "1:1": (1080, 1080),
    }.get(aspect, (1080, 1920))


def build_call_queue(plan: dict, scenes_dir: Path) -> list[dict]:
    queue: list[dict] = []
    aspect = plan["format"]["aspect"]
    for scene in plan["scenes"]:
        out_path = scenes_dir / f"{scene['scene_id']}.mp4"
        if out_path.exists():
            queue.append({
                "scene_id": scene["scene_id"],
                "status": "SKIP_EXISTING",
                "output_path": str(out_path),
            })
            continue

        model_key = scene["model_choice"]
        if model_key in REQUIRES_IMAGE and not scene.get("reference_image"):
            # Skip — caller must generate or supply a reference image first
            queue.append({
                "scene_id": scene["scene_id"],
                "status": "BLOCKED_NEEDS_IMAGE",
                "model": model_key,
                "output_path": str(out_path),
                "note": f"{model_key} requires a start_image — call generate_image first or add reference_image to scene",
            })
            continue

        # Build params payload per Higgsfield generate_video tool schema
        params: dict = {
            "model": model_key,
            "prompt": scene["prompt"],
            "aspect_ratio": aspect,
            "duration": scene["duration_sec"],
            **MODEL_PARAMS.get(model_key, {}),
        }
        if scene.get("reference_image"):
            params["medias"] = [{
                "role": "start_image",
                "value": scene["reference_image"],
            }]

        queue.append({
            "scene_id": scene["scene_id"],
            "status": "PENDING",
            "mcp_tool": MCP_TOOL_NAME,
            "tool_args": {"params": params},
            "output_path": str(out_path),
            "expected_credits": scene["model_credits"],
            "model": model_key,
        })
    return queue


def cmd_plan(working_dir: Path) -> int:
    plan_path = working_dir / "scene-plan.json"
    if not plan_path.exists():
        print(f"✗ scene-plan.json not found at {plan_path}", file=sys.stderr)
        return 1
    plan = json.loads(plan_path.read_text())
    scenes_dir = working_dir / "scenes"
    scenes_dir.mkdir(exist_ok=True)

    queue = build_call_queue(plan, scenes_dir)
    queue_path = working_dir / "mcp-call-queue.json"
    queue_path.write_text(json.dumps({
        "creative_id": plan["creative_id"],
        "client": plan["client"],
        "scenes_dir": str(scenes_dir),
        "queue": queue,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }, indent=2))

    pending = [q for q in queue if q["status"] == "PENDING"]
    skipped = [q for q in queue if q["status"] == "SKIP_EXISTING"]
    total_cost = sum(q.get("expected_credits", 0) for q in pending)

    print(f"\nMCP call queue: {queue_path}\n")
    print(f"  Pending:  {len(pending)} scenes, {total_cost} credits")
    print(f"  Skipped:  {len(skipped)} scenes (already generated)")
    print()
    if pending:
        print("  Next: Claude must read mcp-call-queue.json and invoke the listed")
        print("        Higgsfield MCP tools, saving each output to its output_path.")
        print("        Manifest is appended in-session after each successful call.")
    return 0


def cmd_finalize(working_dir: Path) -> int:
    manifest_path = working_dir / "manifest.json"
    queue_path = working_dir / "mcp-call-queue.json"
    if not queue_path.exists():
        print(f"✗ mcp-call-queue.json missing — run --plan first", file=sys.stderr)
        return 1

    queue_data = json.loads(queue_path.read_text())
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {"scenes": []}
    manifest_by_id = {m["scene_id"]: m for m in manifest.get("scenes", [])}

    missing: list[str] = []
    failed: list[str] = []
    for q in queue_data["queue"]:
        sid = q["scene_id"]
        out = Path(q["output_path"])
        if not out.exists():
            missing.append(sid)
            continue
        if sid not in manifest_by_id:
            # Backfill a minimal manifest entry from queue info
            manifest_by_id[sid] = {
                "scene_id": sid,
                "model": q.get("model", "unknown"),
                "prompt": q.get("args", {}).get("prompt", ""),
                "seed": q.get("args", {}).get("seed"),
                "credits_used": q.get("expected_credits", 0),
                "duration_sec": q.get("args", {}).get("duration_seconds", 0),
                "source": "[GENERATED]",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "output_path": str(out),
            }
        elif manifest_by_id[sid].get("status") == "[FAILED]":
            failed.append(sid)

    manifest_out = {
        "creative_id": queue_data["creative_id"],
        "client": queue_data["client"],
        "scenes": [manifest_by_id[k] for k in sorted(manifest_by_id)],
        "finalized_at": datetime.now(timezone.utc).isoformat(),
        "missing_scene_ids": missing,
        "failed_scene_ids": failed,
    }
    manifest_path.write_text(json.dumps(manifest_out, indent=2))

    total_credits = sum(s.get("credits_used", 0) for s in manifest_out["scenes"])
    print(f"\nManifest finalized: {manifest_path}")
    print(f"  Generated: {len(manifest_out['scenes']) - len(missing) - len(failed)}")
    print(f"  Missing:   {len(missing)}  {missing if missing else ''}")
    print(f"  Failed:    {len(failed)}   {failed if failed else ''}")
    print(f"  Total credits used: {total_credits}")
    return 0 if not missing else 2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("working_dir", help="Path to _engine/working/<entry>/ folder")
    ap.add_argument("--plan", action="store_true", help="Build mcp-call-queue.json")
    ap.add_argument("--finalize", action="store_true", help="Validate manifest after MCP calls")
    args = ap.parse_args()

    wd = Path(args.working_dir)
    if not wd.exists():
        print(f"✗ Working dir not found: {wd}", file=sys.stderr)
        return 1

    if args.plan:
        return cmd_plan(wd)
    if args.finalize:
        return cmd_finalize(wd)
    print("Specify --plan or --finalize", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
