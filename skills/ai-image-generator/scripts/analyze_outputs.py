#!/usr/bin/env python3
"""analyze_outputs.py — orchestrator for in-session Claude scoring of generated PNGs.

This script does NOT run an LLM itself. It writes a `scoring-queue.json` listing every
PNG the analyst Claude must read in-session via the Read tool. Claude reads each PNG,
scores on 5 dimensions (each 0-20, total /100), writes the result to scores.json.

Dimensions:
  brand_voice_fit            — 0-20
  visual_hierarchy           — 0-20  (eye flows correctly to CTA)
  cta_readability            — 0-20  (text legible, no overlap)
  sector_sensitivity         — 0-20  (no inappropriate descriptors / sacred drift)
  variation_differentiation  — 0-20  (this v differs meaningfully from sibling vs)

Usage:
    python3 analyze_outputs.py <working_dir>            # build scoring-queue.json
    python3 analyze_outputs.py <working_dir> --finalize # validate scores.json shape
"""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


SCORE_DIMENSIONS = ["brand_voice_fit", "visual_hierarchy", "cta_readability",
                    "sector_sensitivity", "variation_differentiation"]


def cmd_queue(wd: Path) -> int:
    manifest_path = wd / "manifest.json"
    if not manifest_path.exists():
        print(f"x manifest.json missing", file=sys.stderr)
        return 1
    manifest = json.loads(manifest_path.read_text())
    queue = []
    for g in manifest["generations"]:
        if g.get("status") != "OK":
            continue
        queue.append({
            "score_key": f"{g['concept_id']}/{g['variation_id']}/{g['aspect']}",
            "png_path": g["output_path"],
            "concept_id": g["concept_id"],
            "variation_id": g["variation_id"],
            "aspect": g["aspect"],
            "model": g["model"],
        })
    out = wd / "scoring-queue.json"
    out.write_text(json.dumps({
        "instructions": (
            "For each entry, read the PNG via the Read tool, then score on the 5 dimensions "
            "(each 0-20, total /100). Append to scores.json under .scores keyed by score_key. "
            "Format: {brand_voice_fit:int, visual_hierarchy:int, cta_readability:int, "
            "sector_sensitivity:int, variation_differentiation:int, total:int, notes:str}"
        ),
        "dimensions": SCORE_DIMENSIONS,
        "queue": queue,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }, indent=2))
    print(f"  Scoring queue: {out}  ({len(queue)} PNGs)")
    print(f"  Next: Claude reads each PNG via Read tool, scores, appends to scores.json")
    return 0


def cmd_finalize(wd: Path) -> int:
    scores_path = wd / "scores.json"
    if not scores_path.exists():
        print(f"x scores.json missing — Claude must populate it first", file=sys.stderr)
        return 1
    scores = json.loads(scores_path.read_text())
    if "scores" not in scores:
        scores = {"scores": scores}
    issues = []
    for k, v in scores["scores"].items():
        for dim in SCORE_DIMENSIONS:
            if dim not in v:
                issues.append(f"{k} missing dimension '{dim}'")
            elif not isinstance(v[dim], (int, float)) or not (0 <= v[dim] <= 20):
                issues.append(f"{k}.{dim} out of range (got {v[dim]!r})")
        # Compute total if missing
        if "total" not in v:
            v["total"] = sum(v.get(d, 0) for d in SCORE_DIMENSIONS)
    scores["finalized_at"] = datetime.now(timezone.utc).isoformat()
    scores_path.write_text(json.dumps(scores, indent=2))
    if issues:
        print(f"!  scoring issues:")
        for i in issues[:20]:
            print(f"   - {i}")
        return 2
    print(f"  Scores finalized: {scores_path}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("working_dir")
    ap.add_argument("--finalize", action="store_true")
    args = ap.parse_args()
    wd = Path(args.working_dir)
    return cmd_finalize(wd) if args.finalize else cmd_queue(wd)


if __name__ == "__main__":
    sys.exit(main())
