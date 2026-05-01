#!/usr/bin/env python3
"""plan_generations.py — read concept-board.json, build mcp-call-queue.json.

Each entry in the queue is one MCP `generate_image` call. Idempotent: skips
variations whose output PNG already exists. Emits budget preview and (optionally)
requires --confirm-cost flag for high-burn runs.

Architecture: this script does NOT call MCP. It writes a queue Claude reads and
invokes in-session, then download_outputs.py pulls each result into creatives/.

Usage:
    python3 plan_generations.py <working_dir>
    python3 plan_generations.py <working_dir> --confirm-cost
"""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


MCP_TOOL_GENERATE_IMAGE = "mcp__b39cf66e-63d0-49fc-a861-0eb724d588df__generate_image"

# Per-model param defaults (verified against models_explore 2026-05-01)
MODEL_PARAMS: dict[str, dict] = {
    "nano_banana_flash":      {"resolution": "2k"},
    "nano_banana_2":          {"resolution": "2k"},
    "nano_banana":            {},
    "gpt_image_2":            {"quality": "high", "resolution": "2k"},
    "gpt_image":              {"quality": "high"},
    "marketing_studio_image": {"resolution": "2k"},
    "cinematic_studio_2_5":   {"resolution": "2k"},
    "soul_2":                 {},
    "soul_cast":              {},
    "soul_cinematic":         {},
    "soul_location":          {},
    "seedream_v4_5":          {"quality": "high"},
    "seedream_v5_lite":       {"quality": "high"},
    "flux_2":                 {"resolution": "2k", "model": "pro"},
    "flux_kontext":           {},
    "kling_omni_image":       {"resolution": "2k"},
    "grok_image":             {"mode": "pro"},
    "z_image":                {},
    "image_auto":             {},
}

# Models that REQUIRE a reference image
REQUIRES_REFERENCE = {"flux_kontext"}

BUDGET_TIERS = [
    (50, "silent"),
    (150, "warn"),
    (400, "require_confirm"),
    (10**9, "abort"),
]


def output_png_path(creatives_dir: Path, concept_id: str, variation_id: str, aspect: str) -> Path:
    aspect_slug = aspect.replace(":", "x").replace(".", "p")
    concept_dir = creatives_dir / concept_id
    return concept_dir / f"{variation_id}-{aspect_slug}.png"


def reference_uuid_lookup(reference_manifest_path: Path) -> dict[str, str]:
    if not reference_manifest_path.exists():
        return {}
    manifest = json.loads(reference_manifest_path.read_text())
    return {img["id"]: img["higgsfield_uuid"] for img in manifest["images"] if img.get("higgsfield_uuid")}


def build_queue(concept_board: dict, creatives_dir: Path, ref_uuids: dict[str, str]) -> tuple[list[dict], list[dict]]:
    queue: list[dict] = []
    blocked: list[dict] = []
    for concept in concept_board["concepts"]:
        for variation in concept["variations"]:
            out_path = output_png_path(creatives_dir, concept["concept_id"], variation["variation_id"], variation["aspect_ratio"])
            if out_path.exists():
                queue.append({
                    "concept_id": concept["concept_id"],
                    "variation_id": variation["variation_id"],
                    "status": "SKIP_EXISTING",
                    "output_path": str(out_path),
                })
                continue
            if variation.get("voice_check") == "FAIL":
                blocked.append({
                    "concept_id": concept["concept_id"],
                    "variation_id": variation["variation_id"],
                    "reason": "voice_check_failed",
                    "details": variation.get("voice_check_reason", "see concept-board.json"),
                })
                continue

            model = variation["model_choice"]
            ref_ids: list[str] = variation.get("reference_image_ids") or []
            ref_uuid_list = [ref_uuids[r] for r in ref_ids if r in ref_uuids]

            if model in REQUIRES_REFERENCE and not ref_uuid_list:
                blocked.append({
                    "concept_id": concept["concept_id"],
                    "variation_id": variation["variation_id"],
                    "reason": "missing_required_reference",
                    "details": f"Model '{model}' requires medias[]; no reference UUIDs resolved",
                })
                continue

            params: dict = {
                "model": model,
                "prompt": variation["prompt"],
                "aspect_ratio": variation["aspect_ratio"],
                **MODEL_PARAMS.get(model, {}),
            }
            # Override resolution if variation specifies
            if variation.get("resolution"):
                params["resolution"] = variation["resolution"]
            if ref_uuid_list:
                params["medias"] = [{"role": "image", "value": uuid} for uuid in ref_uuid_list]

            queue.append({
                "concept_id": concept["concept_id"],
                "variation_id": variation["variation_id"],
                "status": "PENDING",
                "mcp_tool": MCP_TOOL_GENERATE_IMAGE,
                "tool_args": {"params": params},
                "output_path": str(out_path),
                "expected_credits": variation.get("expected_credits", 0),
                "model": model,
                "reference_image_ids": ref_ids,
                "reference_uuids_resolved": ref_uuid_list,
            })

    return queue, blocked


def budget_action(total_credits: int) -> str:
    for cap, action in BUDGET_TIERS:
        if total_credits <= cap:
            return action
    return "abort"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("working_dir", help="Path to _engine/working/<entry>/ folder")
    ap.add_argument("--confirm-cost", action="store_true", help="Acknowledge high credit burn")
    args = ap.parse_args()

    wd = Path(args.working_dir)
    cb_path = wd / "concept-board.json"
    if not cb_path.exists():
        print(f"x concept-board.json not found at {cb_path}", file=sys.stderr)
        return 1
    concept_board = json.loads(cb_path.read_text())

    creatives_dir = wd / "creatives"
    creatives_dir.mkdir(exist_ok=True)

    ref_uuids = reference_uuid_lookup(wd / "reference-manifest.json")

    queue, blocked = build_queue(concept_board, creatives_dir, ref_uuids)

    pending = [q for q in queue if q["status"] == "PENDING"]
    skipped = [q for q in queue if q["status"] == "SKIP_EXISTING"]
    total_credits = sum(q.get("expected_credits", 0) for q in pending)

    queue_path = wd / "mcp-call-queue.json"
    queue_path.write_text(json.dumps({
        "campaign_id": concept_board["campaign_id"],
        "client": concept_board["client"],
        "creatives_dir": str(creatives_dir),
        "queue": queue,
        "blocked": blocked,
        "totals": {
            "pending": len(pending),
            "skipped_existing": len(skipped),
            "blocked": len(blocked),
            "total_credits_estimate": total_credits,
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }, indent=2))

    print(f"\nMCP call queue written: {queue_path}\n")
    print(f"  Pending:  {len(pending)} generations,  ~{total_credits} credits")
    print(f"  Skipped:  {len(skipped)} (already generated)")
    if blocked:
        print(f"  BLOCKED:  {len(blocked)} (see queue file for reasons)")
    print()

    # Per-variation summary
    if pending:
        print("  Plan:")
        for q in pending[:30]:
            ref_note = f" [refs: {','.join(q['reference_image_ids'])}]" if q.get("reference_image_ids") else ""
            cred_note = f"{q['expected_credits']:>3} cr"
            print(f"    {q['concept_id']}/{q['variation_id']:<14} {q['model']:<24} {cred_note}{ref_note}")
        if len(pending) > 30:
            print(f"    ... and {len(pending) - 30} more")
        print()

    action = budget_action(total_credits)
    if action == "warn":
        print(f"!  Credit burn estimate {total_credits} > 50 — proceeding (warn tier).")
    elif action == "require_confirm" and not args.confirm_cost:
        print(f"x Credit burn estimate {total_credits} > 150 — pass --confirm-cost to proceed.")
        return 2
    elif action == "abort":
        print(f"x Credit burn estimate {total_credits} > 400 — abort. Reduce variations or split into runs.")
        return 3

    print("  Next: Claude reads mcp-call-queue.json, invokes generate_image per PENDING entry,")
    print("        polls show_generations until completed, runs download_outputs.py per result,")
    print("        appends manifest.json entries.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
