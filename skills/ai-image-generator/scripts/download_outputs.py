#!/usr/bin/env python3
"""download_outputs.py — download a Higgsfield generation result PNG to disk + append manifest entry.

Called by Claude in-session after a generate_image MCP call completes. Claude provides:
  --url        the result URL (or --local-source if Claude already saved bytes)
  --output     full target path
  --concept-id, --variation-id, --aspect, --model, --prompt, --credits

Usage:
    python3 download_outputs.py <working_dir> --url <url> --output <png_path> \
        --concept-id 01 --variation-id v1 --aspect 1:1 --model nano_banana_flash \
        --prompt "..." --credits 0 [--reference-ids id1,id2] [--seed 42]
"""
import argparse
import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


def append_manifest(working_dir: Path, entry: dict) -> None:
    manifest_path = working_dir / "manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
    else:
        manifest = {"generations": [], "started_at": datetime.now(timezone.utc).isoformat()}
    # Replace existing entry with same concept+variation+aspect, else append
    key = (entry["concept_id"], entry["variation_id"], entry["aspect"])
    manifest["generations"] = [g for g in manifest["generations"]
                               if (g.get("concept_id"), g.get("variation_id"), g.get("aspect")) != key]
    manifest["generations"].append(entry)
    manifest["updated_at"] = datetime.now(timezone.utc).isoformat()
    manifest_path.write_text(json.dumps(manifest, indent=2))


def download_url(url: str, dest: Path) -> int:
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "ai-image-generator/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp, dest.open("wb") as f:
            while True:
                chunk = resp.read(65536)
                if not chunk:
                    break
                f.write(chunk)
    except Exception as e:
        print(f"x download failed: {e}", file=sys.stderr)
        return 1
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("working_dir")
    ap.add_argument("--url", help="Higgsfield result URL")
    ap.add_argument("--local-source", help="Local file Claude saved bytes to (alt to --url)")
    ap.add_argument("--output", required=True, help="Target PNG path")
    ap.add_argument("--concept-id", required=True)
    ap.add_argument("--variation-id", required=True)
    ap.add_argument("--aspect", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--credits", type=int, default=0)
    ap.add_argument("--reference-ids", help="Comma-separated reference IDs used")
    ap.add_argument("--seed", type=int, help="Generation seed if returned")
    ap.add_argument("--generation-id", help="Higgsfield generation_id for manifest")
    args = ap.parse_args()

    wd = Path(args.working_dir)
    out = Path(args.output)

    if args.url:
        rc = download_url(args.url, out)
        if rc != 0:
            return rc
    elif args.local_source:
        src = Path(args.local_source)
        if not src.exists():
            print(f"x local source not found: {src}", file=sys.stderr)
            return 1
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(src.read_bytes())
    else:
        print("x must provide --url or --local-source", file=sys.stderr)
        return 1

    if not out.exists() or out.stat().st_size == 0:
        print(f"x download produced empty file: {out}", file=sys.stderr)
        return 1

    entry = {
        "concept_id": args.concept_id,
        "variation_id": args.variation_id,
        "aspect": args.aspect,
        "model": args.model,
        "prompt": args.prompt,
        "credits_used": args.credits,
        "reference_image_ids": args.reference_ids.split(",") if args.reference_ids else [],
        "seed": args.seed,
        "generation_id": args.generation_id,
        "source": "[GENERATED]",
        "status": "OK",
        "output_path": str(out),
        "file_size_bytes": out.stat().st_size,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    append_manifest(wd, entry)
    print(f"  saved {out.name} ({out.stat().st_size:,} bytes), manifest updated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
