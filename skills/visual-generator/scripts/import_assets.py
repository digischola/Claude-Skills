#!/usr/bin/env python3
"""
Import rendered visual assets into the brand queue.

Moves files (PNG, MP4, PDF) from a handoff/render folder OR a single file path
into brand/queue/assets/<source-id>/ with normalized naming and a manifest.

Usage:
  # Import a single file
  python3 import_assets.py /path/to/reel.mp4 --source-id 4e4eed15 --kind reel

  # Import a folder (e.g., Claude Design handoff output)
  python3 import_assets.py /path/to/handoff-folder/ --source-id 4e4eed15 --kind carousel

  # With manifest from the brief linkage
  python3 import_assets.py /path/to/out/ --source-id 4e4eed15 --brief-file /path/to/brief.md

Exit codes:
  0 = imported successfully
  1 = source path missing
  2 = kind unrecognized / manifest write failed
"""

import argparse
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path


SUPPORTED_KINDS = {
    "carousel": {"ext_prefers": [".png"], "pattern": "slide-{n}.png"},
    "quote-card": {"ext_prefers": [".png"], "pattern": "quote.png"},
    "reel": {"ext_prefers": [".mp4"], "pattern": "reel.mp4"},
    "animated-graphic": {"ext_prefers": [".mp4"], "pattern": "animated.mp4"},
    "story": {"ext_prefers": [".png"], "pattern": "story-{n}.png"},
    "pdf": {"ext_prefers": [".pdf"], "pattern": "carousel.pdf"},
    "mixed": {"ext_prefers": [".png", ".mp4", ".pdf"], "pattern": "asset-{n}{ext}"},
}

# Brief-target names → import kind. Kept narrow: only the targets generate_brief.py emits.
KIND_ALIASES = {
    "reel-script": "reel",
    "carousel-slides": "carousel",
}


def collect_files(source: Path):
    """Return list of (file_path, extension) for all files in source (or single file)."""
    if source.is_file():
        return [(source, source.suffix.lower())]
    if source.is_dir():
        files = []
        for f in sorted(source.iterdir()):
            if f.is_file() and not f.name.startswith("."):
                files.append((f, f.suffix.lower()))
        return files
    return []


def hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def normalize_filename(kind: str, index: int, ext: str) -> str:
    spec = SUPPORTED_KINDS.get(kind, {})
    pattern = spec.get("pattern", "asset-{n}{ext}")
    name = pattern.replace("{n}", str(index)).replace("{ext}", ext)
    return name


def import_assets(source: Path, brand_folder: Path, source_id: str,
                  kind: str, brief_file: Path = None):
    assets_dir = brand_folder / "brand" / "queue" / "assets" / source_id
    assets_dir.mkdir(parents=True, exist_ok=True)

    files = collect_files(source)
    if not files:
        print(f"  ERROR: no files found at {source}", file=sys.stderr)
        return 1

    allowed_exts = SUPPORTED_KINDS.get(kind, {}).get("ext_prefers", [])
    # Filter to just matching extensions if kind specifies
    if kind != "mixed" and allowed_exts:
        files = [(f, e) for f, e in files if e in allowed_exts]
        if not files:
            print(f"  ERROR: no files matching {allowed_exts} in {source}", file=sys.stderr)
            return 1

    imported = []
    idx = 1
    for f_path, ext in files:
        new_name = normalize_filename(kind, idx, ext)
        dest = assets_dir / new_name
        shutil.copy2(f_path, dest)
        imported.append({
            "original_name": f_path.name,
            "stored_as": new_name,
            "size_bytes": dest.stat().st_size,
            "sha256_16": hash_file(dest),
            "ext": ext,
        })
        idx += 1

    # Write manifest
    manifest = {
        "source_id": source_id,
        "kind": kind,
        "imported_at": datetime.now(timezone.utc).isoformat(),
        "origin_path": str(source),
        "brief_file": str(brief_file) if brief_file else None,
        "assets": imported,
        "count": len(imported),
    }
    manifest_path = assets_dir / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"Imported {len(imported)} asset(s) to {assets_dir}")
    for a in imported:
        print(f"  {a['original_name']}  →  {a['stored_as']}  ({a['size_bytes']} bytes)")
    print(f"Manifest: {manifest_path}")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source", type=Path,
                    help="Single file path OR folder of rendered assets")
    ap.add_argument("--source-id", required=True,
                    help="Entry ID or logical source identifier (e.g., first 8 chars of idea-bank entry_id)")
    ap.add_argument("--kind",
                    choices=sorted(set(list(SUPPORTED_KINDS.keys()) + list(KIND_ALIASES.keys()))),
                    default="mixed",
                    help="Asset kind for naming convention. Accepts brief-target aliases like 'reel-script' (maps to 'reel') and 'carousel-slides' (maps to 'carousel').")
    ap.add_argument("--brief-file", type=Path, default=None,
                    help="Path to the brief that produced these assets (for manifest traceability)")
    ap.add_argument("--brand-folder", type=Path,
                    default=Path("/Users/digischola/Desktop/Digischola"))
    args = ap.parse_args()

    if not args.source.exists():
        print(f"  ERROR: source path not found: {args.source}", file=sys.stderr)
        sys.exit(1)

    # Resolve brief-target aliases (reel-script → reel, etc.)
    resolved_kind = KIND_ALIASES.get(args.kind, args.kind)

    exit_code = import_assets(
        args.source, args.brand_folder, args.source_id,
        resolved_kind, args.brief_file
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
