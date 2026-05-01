#!/usr/bin/env python3
"""inventory_references.py — walk a reference image folder, dedup, and prepare upload queue.

Architecture: this script does the file walk + hashing + initial tag inference. It writes:

  reference-manifest.json — one entry per unique image with subject_type / sacred /
                            consent_status / usage_scope / auto_attach_to_concepts...
  upload-queue.json       — list of files to upload via Higgsfield media_upload
                            (Claude reads this, runs media_upload + media_confirm in-session,
                            then patches reference-manifest.json with returned UUIDs)

Tag inference is initial only — based on subfolder names, filename patterns, and EXIF.
Claude in-session refines tags by reading actual images for ambiguous cases.

Usage:
    python3 inventory_references.py <reference_folder> --output <working_dir>/reference-manifest.json
    python3 inventory_references.py --finalize <working_dir>  (after Claude uploads)
"""
import argparse
import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".tiff", ".tif"}

# Subfolder name → initial tag inference
SUBFOLDER_TAG_HINTS = {
    "deities": {"subject_type": "deity", "sacred": True, "usage_scope": "input_only_no_redraw", "ai_redraw_allowed": False, "auto_attach": ["sacred_composite"]},
    "deity": {"subject_type": "deity", "sacred": True, "usage_scope": "input_only_no_redraw", "ai_redraw_allowed": False, "auto_attach": ["sacred_composite"]},
    "scripture": {"subject_type": "scripture", "sacred": True, "usage_scope": "input_only_no_redraw", "ai_redraw_allowed": False, "auto_attach": ["sacred_composite"]},
    "devotees-consent-ok": {"subject_type": "devotee_human", "contains_face": True, "contains_human": True, "consent_status": "cleared", "usage_scope": "reference_or_subject", "ai_redraw_allowed": True, "auto_attach": ["ugc", "lifestyle", "atmospheric"]},
    "devotees": {"subject_type": "devotee_human", "contains_face": True, "contains_human": True, "consent_status": "unknown", "usage_scope": "unknown", "ai_redraw_allowed": False, "auto_attach": []},
    "consent-ok": {"contains_face": True, "consent_status": "cleared"},
    "prasadam": {"subject_type": "food_object", "auto_attach": ["cover_slide", "atmospheric", "lifestyle"]},
    "food": {"subject_type": "food_object", "auto_attach": ["cover_slide", "atmospheric", "lifestyle"]},
    "temple-interior": {"subject_type": "interior_atmospheric", "auto_attach": ["cover_slide", "atmospheric"]},
    "kirtan-events": {"subject_type": "interior_atmospheric", "auto_attach": ["atmospheric", "lifestyle"]},
    "festivals": {"subject_type": "interior_atmospheric", "auto_attach": ["atmospheric"]},
    "decorative": {"subject_type": "decorative_object", "auto_attach": ["cover_slide", "atmospheric"]},
    "product": {"subject_type": "product_object", "auto_attach": ["ad_product_hero", "cover_slide"]},
    "people-portraits": {"subject_type": "client_team", "contains_face": True, "consent_status": "unknown", "auto_attach": []},
    "founder": {"subject_type": "client_founder", "contains_face": True, "consent_status": "cleared", "auto_attach": ["character_consistent"]},
    "team": {"subject_type": "client_team", "contains_face": True, "consent_status": "unknown", "auto_attach": []},
    "talent": {"subject_type": "talent_model", "contains_face": True, "consent_status": "cleared", "auto_attach": ["ugc", "character_consistent"]},
    "locations": {"subject_type": "building_exterior", "auto_attach": ["hero_landing", "cover_slide"]},
    "landscape": {"subject_type": "landscape", "auto_attach": ["atmospheric"]},
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def get_dimensions(path: Path) -> tuple[int, int] | None:
    """Return (width, height) using stdlib only — PIL not assumed available."""
    try:
        with path.open("rb") as f:
            head = f.read(32)
        # PNG: 8 byte sig + 4 byte chunk len + 4 byte 'IHDR' + 4 byte width + 4 byte height
        if head.startswith(b"\x89PNG\r\n\x1a\n"):
            w = int.from_bytes(head[16:20], "big")
            h = int.from_bytes(head[20:24], "big")
            return (w, h)
        # JPEG: walk markers to find SOF
        if head.startswith(b"\xff\xd8"):
            with path.open("rb") as f:
                data = f.read()
            i = 2
            while i < len(data) - 9:
                if data[i] != 0xFF:
                    i += 1
                    continue
                marker = data[i+1]
                if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                    h = int.from_bytes(data[i+5:i+7], "big")
                    w = int.from_bytes(data[i+7:i+9], "big")
                    return (w, h)
                seg_len = int.from_bytes(data[i+2:i+4], "big")
                i += 2 + seg_len
        # WebP: RIFF .... WEBP VP8X
        if head[0:4] == b"RIFF" and head[8:12] == b"WEBP":
            with path.open("rb") as f:
                data = f.read(64)
            if data[12:16] == b"VP8X":
                w = int.from_bytes(data[24:27], "little") + 1
                h = int.from_bytes(data[27:30], "little") + 1
                return (w, h)
    except Exception:
        return None
    return None


def aspect_ratio_str(w: int, h: int) -> str:
    """Reduce w:h to a clean ratio string."""
    from math import gcd
    g = gcd(w, h)
    a, b = w // g, h // g
    # Snap common ratios
    common = {(16, 9): "16:9", (9, 16): "9:16", (4, 3): "4:3", (3, 4): "3:4",
              (1, 1): "1:1", (3, 2): "3:2", (2, 3): "2:3", (4, 5): "4:5",
              (5, 4): "5:4", (21, 9): "21:9", (191, 100): "1.91:1"}
    if (a, b) in common:
        return common[(a, b)]
    # Fallback: nearest common
    target = w / h
    best = min(common.items(), key=lambda kv: abs(target - kv[0][0] / kv[0][1]))
    return best[1]


def load_consent_csv(folder: Path) -> dict[str, str]:
    """Read consent.csv at folder root if present."""
    csv_path = folder / "consent.csv"
    if not csv_path.exists():
        return {}
    consent: dict[str, str] = {}
    with csv_path.open() as f:
        reader = csv.DictReader(f)
        for row in reader:
            fn = (row.get("filename") or "").strip()
            status = (row.get("consent_status") or "").strip().lower()
            if fn and status:
                consent[fn] = status
    return consent


def initial_tags(rel_path: Path, filename: str, consent_lookup: dict[str, str]) -> dict:
    """Build initial tag dict from subfolder + filename + consent.csv."""
    tags = {
        "subject_type": "mixed",
        "contains_face": False,
        "contains_human": False,
        "sacred": False,
        "consent_status": "n/a",
        "usage_scope": "reference_or_subject",
        "ai_redraw_allowed": True,
        "auto_attach_to_concepts_with_intent": [],
    }
    parts = [p.lower() for p in rel_path.parts[:-1]]  # subfolder chain
    for part in parts:
        for hint_key, hint_val in SUBFOLDER_TAG_HINTS.items():
            if hint_key in part:
                for k, v in hint_val.items():
                    if k == "auto_attach":
                        tags["auto_attach_to_concepts_with_intent"] = list(set(tags["auto_attach_to_concepts_with_intent"]) | set(v))
                    else:
                        tags[k] = v
    fname_lower = filename.lower()
    name_only = Path(filename).stem.lower()
    for keyword, hint_val in SUBFOLDER_TAG_HINTS.items():
        if keyword in name_only:
            for k, v in hint_val.items():
                if k == "auto_attach":
                    tags["auto_attach_to_concepts_with_intent"] = list(set(tags["auto_attach_to_concepts_with_intent"]) | set(v))
                else:
                    tags.setdefault(k, v)
    # consent.csv override
    csv_status = consent_lookup.get(filename) or consent_lookup.get(str(rel_path))
    if csv_status:
        tags["consent_status"] = csv_status
        if csv_status == "cleared" and tags.get("contains_face"):
            tags["usage_scope"] = "reference_or_subject"
            tags["ai_redraw_allowed"] = True
    return tags


def cmd_inventory(folder: Path, output: Path) -> int:
    if not folder.exists() or not folder.is_dir():
        print(f"x reference folder not found: {folder}", file=sys.stderr)
        return 1
    output.parent.mkdir(parents=True, exist_ok=True)

    consent_lookup = load_consent_csv(folder)
    images: list[dict] = []
    seen_hashes: set[str] = set()
    duplicates_skipped = 0

    for path in sorted(folder.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in IMAGE_EXTS:
            continue
        sha = sha256_file(path)
        if sha in seen_hashes:
            duplicates_skipped += 1
            continue
        seen_hashes.add(sha)

        rel = path.relative_to(folder)
        filename = path.name
        dims = get_dimensions(path) or (0, 0)
        ar = aspect_ratio_str(*dims) if dims[0] and dims[1] else "unknown"
        size = path.stat().st_size

        tags = initial_tags(rel, filename, consent_lookup)
        # Stable ID: subject-prefix + first 8 of sha
        prefix = tags["subject_type"].replace("_", "-")
        img_id = f"{prefix}-{sha[:8]}"

        images.append({
            "id": img_id,
            "filename": str(rel),
            "absolute_path": str(path),
            "sha256": sha,
            "dimensions": {"width": dims[0], "height": dims[1]},
            "aspect_ratio": ar,
            "file_size_bytes": size,
            "uploaded_at": None,
            "higgsfield_uuid": None,
            "tags": tags,
            "tag_confidence": "initial",
            "tag_notes": "",
        })

    manifest = {
        "folder_root": str(folder),
        "scanned_at": datetime.now(timezone.utc).isoformat(),
        "total_files": sum(1 for _ in folder.rglob("*") if _.is_file() and _.suffix.lower() in IMAGE_EXTS),
        "total_unique": len(images),
        "duplicates_skipped": duplicates_skipped,
        "uploaded_to_higgsfield": 0,
        "images": images,
    }

    output.write_text(json.dumps(manifest, indent=2))

    # Build the upload queue separately for Claude to consume
    upload_queue = {
        "manifest_path": str(output),
        "to_upload": [
            {"id": img["id"], "absolute_path": img["absolute_path"], "tags": img["tags"]}
            for img in images
        ],
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    queue_path = output.parent / "reference-upload-queue.json"
    queue_path.write_text(json.dumps(upload_queue, indent=2))

    # Print summary
    sacred_count = sum(1 for img in images if img["tags"]["sacred"])
    face_count = sum(1 for img in images if img["tags"]["contains_face"])
    consent_unknown = sum(
        1 for img in images
        if img["tags"]["contains_face"] and img["tags"]["consent_status"] in {"unknown", "pending"}
    )

    print(f"\nReference inventory: {output}")
    print(f"  Folder root:       {folder}")
    print(f"  Total scanned:     {manifest['total_files']}")
    print(f"  Unique images:     {len(images)}")
    print(f"  Duplicates skipped:{duplicates_skipped}")
    print(f"  Sacred refs:       {sacred_count}  (input_only_no_redraw — composite path)")
    print(f"  Face refs:         {face_count}    ({consent_unknown} need consent confirmation)")
    print(f"\n  Upload queue:      {queue_path}")
    print(f"  Next: Claude reads upload-queue.json, calls media_upload + media_confirm")
    print(f"        per entry, patches reference-manifest.json with higgsfield_uuid + uploaded_at")
    print(f"        Then: python3 inventory_references.py --finalize {output.parent}")

    if consent_unknown > 0:
        print(f"\n!  WARNING: {consent_unknown} face images have unknown consent status.")
        print(f"   Resolve before generation: move to consent-ok/ subfolder OR add to consent.csv")
        print(f"   OR write consent-override.md in the working dir.")

    return 0


def cmd_finalize(working_dir: Path) -> int:
    manifest_path = working_dir / "reference-manifest.json"
    if not manifest_path.exists():
        print(f"x reference-manifest.json not found at {manifest_path}", file=sys.stderr)
        return 1
    manifest = json.loads(manifest_path.read_text())
    uploaded = sum(1 for img in manifest["images"] if img.get("higgsfield_uuid"))
    failed = [img["id"] for img in manifest["images"] if not img.get("higgsfield_uuid")]
    manifest["uploaded_to_higgsfield"] = uploaded
    manifest["finalized_at"] = datetime.now(timezone.utc).isoformat()
    manifest_path.write_text(json.dumps(manifest, indent=2))
    print(f"  Reference inventory finalized: {manifest_path}")
    print(f"    Uploaded: {uploaded} / {len(manifest['images'])}")
    if failed:
        print(f"    Failed:   {len(failed)}  ({failed[:5]}{'...' if len(failed) > 5 else ''})")
        return 2
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("folder", nargs="?", help="Reference image folder to inventory")
    ap.add_argument("--output", help="Path to reference-manifest.json")
    ap.add_argument("--finalize", help="Working dir to finalize uploads in")
    args = ap.parse_args()

    if args.finalize:
        return cmd_finalize(Path(args.finalize))
    if args.folder and args.output:
        return cmd_inventory(Path(args.folder), Path(args.output))
    print("Usage: inventory_references.py <folder> --output <manifest.json>", file=sys.stderr)
    print("       inventory_references.py --finalize <working_dir>", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
