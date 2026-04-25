#!/usr/bin/env python3
"""
Repurpose a published/drafted post for additional channels.

Three modes:
  inspect  - parse source file, output structured JSON (channel, format, body, hook, tags)
  save     - given a drafted variant body + target, write file to queue/pending-approval
  link     - after all variants are written, update source frontmatter with repurposed_into
             and run post-writer's validate_post.py on each variant

Usage:
  python3 repurpose_post.py inspect <source_file>
  python3 repurpose_post.py save <source_file> --target <channel> --format <format> --body-file <draft.md>
  python3 repurpose_post.py link <source_file> --variants <var1.md> <var2.md> ...

The skill orchestrator (Claude running SKILL.md) invokes these in order:
  1. inspect to get structural hints
  2. draft each variant inline (Claude judgment)
  3. save each variant (writes file + stamps frontmatter)
  4. link when all variants saved (updates source, validates each)
"""

import argparse
import json
import re
import subprocess
import sys
from datetime import date, datetime, timezone
from pathlib import Path


# Channel character budgets — mirror post-writer/references/platform-specs.md
CHANNEL_BUDGETS = {
    "linkedin-text": {"max_chars": 3000, "sweet_spot": (1200, 1800)},
    "linkedin-carousel": {"max_slides": 12, "slide_chars": (100, 200), "caption_chars": (300, 800)},
    "x-single": {"max_chars": 280, "sweet_spot": (240, 280)},
    "x-thread": {"tweets": (5, 7), "per_tweet_chars": (200, 270)},
    "instagram-caption": {"max_chars": 2200, "sweet_spot": (150, 400)},
    "instagram-carousel": {"slides": (7, 10), "slide_chars": (20, 40), "caption_chars": (150, 300)},
    "instagram-reel": {"seconds": (30, 90)},
    "whatsapp-status": {"chars": (40, 400)},
    "whatsapp-channel": {"chars": (100, 600)},
    "facebook-post": {"sweet_spot": (400, 1000)},
}


POST_WRITER_VALIDATOR = Path(
    "/Users/digischola/Desktop/Claude Skills/skills/post-writer/scripts/validate_post.py"
)


def parse_frontmatter(text: str):
    meta, body = {}, text
    if text.startswith("---\n"):
        parts = text.split("---\n", 2)
        if len(parts) >= 3:
            for line in parts[1].splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    meta[k.strip()] = v.strip()
            body = parts[2]
    return meta, body.strip()


def extract_hook(body: str, channel: str):
    """Pick the first 1-2 non-empty lines. Channel-aware length."""
    lines = [l for l in body.splitlines() if l.strip()]
    if not lines:
        return ""
    if channel in ("linkedin", "facebook"):
        # LinkedIn hook is the first 2 lines pre-truncation
        return "\n".join(lines[:2])
    if channel == "x":
        return lines[0]
    if channel == "instagram":
        return lines[0]
    return lines[0]


def infer_channel_key(meta: dict):
    channel = meta.get("channel", "").lower()
    fmt = meta.get("format", "").lower()
    if channel == "linkedin" and "text" in fmt:
        return "linkedin-text"
    if channel == "linkedin" and "carousel" in fmt:
        return "linkedin-carousel"
    if channel == "x" and "thread" in fmt:
        return "x-thread"
    if channel == "x":
        return "x-single"
    if channel == "instagram" and "carousel" in fmt:
        return "instagram-carousel"
    if channel == "instagram" and "reel" in fmt:
        return "instagram-reel"
    if channel == "instagram":
        return "instagram-caption"
    if channel == "whatsapp" and "channel" in fmt:
        return "whatsapp-channel"
    if channel == "whatsapp":
        return "whatsapp-status"
    if channel == "facebook":
        return "facebook-post"
    return f"{channel}-{fmt}" if channel and fmt else (channel or "unknown")


def default_targets(source_channel_key: str):
    """Default target channels based on source channel. Excludes source."""
    if "linkedin-text" in source_channel_key:
        return ["x-thread", "instagram-carousel", "instagram-reel",
                "whatsapp-status", "facebook-post"]
    if "linkedin-carousel" in source_channel_key:
        return ["x-thread", "instagram-carousel"]
    if "x-thread" in source_channel_key:
        return ["linkedin-text", "instagram-carousel"]
    if "x-single" in source_channel_key:
        return ["linkedin-text", "instagram-caption"]
    if "instagram-carousel" in source_channel_key:
        return ["linkedin-carousel", "x-thread"]
    return []


def inspect_cmd(args):
    src = Path(args.source_file)
    if not src.exists():
        sys.exit(f"Source file not found: {src}")

    text = src.read_text(errors="replace")
    meta, body = parse_frontmatter(text)
    ch_key = infer_channel_key(meta)

    result = {
        "source_file": str(src),
        "source_meta": meta,
        "source_channel_key": ch_key,
        "source_body_chars": len(body),
        "source_hook": extract_hook(body, meta.get("channel", "")),
        "source_pillar": meta.get("pillar"),
        "source_entry_id": meta.get("entry_id"),
        "default_targets": default_targets(ch_key),
        "budgets": CHANNEL_BUDGETS,
    }
    print(json.dumps(result, indent=2))
    return 0


def save_cmd(args):
    src = Path(args.source_file)
    if not src.exists():
        sys.exit(f"Source file not found: {src}")

    body_file = Path(args.body_file)
    if not body_file.exists():
        sys.exit(f"Variant body file not found: {body_file}")

    # Read source frontmatter to inherit pillar, entry_id
    src_text = src.read_text(errors="replace")
    src_meta, _ = parse_frontmatter(src_text)

    variant_body = body_file.read_text(errors="replace").strip()

    # Build variant frontmatter
    today = date.today().isoformat()
    entry_short = (src_meta.get("entry_id", "nil")[:8]) if src_meta.get("entry_id") else "nil"
    target_clean = args.target.replace("-", "")
    variant_fname = f"{today}-{entry_short}-{args.target}-{args.format}-repurpose.md"
    queue_dir = src.parent
    variant_path = queue_dir / variant_fname

    fm_lines = [
        "---",
        f"channel: {args.target.split('-')[0]}",
        f"format: {args.target.split('-', 1)[1] if '-' in args.target else args.format}",
        f"entry_id: {src_meta.get('entry_id', 'unknown')}",
        f"pillar: {src_meta.get('pillar', 'unknown')}",
        f"repurpose_source: {src.name}",
        f"hook_preservation: {args.hook_preservation}",
        f"validator_status: pending",
        "---",
    ]
    out = "\n".join(fm_lines) + "\n" + variant_body + "\n"
    variant_path.write_text(out)

    print(f"Saved variant: {variant_path}")
    return 0


def link_cmd(args):
    src = Path(args.source_file)
    if not src.exists():
        sys.exit(f"Source file not found: {src}")

    # Update source frontmatter with repurposed_into list
    text = src.read_text(errors="replace")
    meta, body = parse_frontmatter(text)

    variant_names = [Path(v).name for v in args.variants]
    meta["repurposed_into"] = variant_names
    meta["repurposed_at"] = datetime.now(timezone.utc).isoformat()

    # Rebuild frontmatter (preserve order reasonably)
    fm_lines = ["---"]
    for k, v in meta.items():
        if isinstance(v, list):
            fm_lines.append(f"{k}: [{', '.join(v)}]")
        else:
            fm_lines.append(f"{k}: {v}")
    fm_lines.append("---")
    new_text = "\n".join(fm_lines) + "\n" + body + "\n"
    src.write_text(new_text)
    print(f"Source frontmatter updated with {len(variant_names)} variants.")

    # Run post-writer's validate_post.py on each variant
    print("\n--- Validating variants ---")
    failures = []
    for v_path in args.variants:
        v = Path(v_path)
        if not v.exists():
            print(f"  MISSING: {v}")
            failures.append(v_path)
            continue
        # infer channel from frontmatter for validator
        v_text = v.read_text(errors="replace")
        v_meta, _ = parse_frontmatter(v_text)
        ch_key = infer_channel_key(v_meta)
        r = subprocess.run(
            ["python3", str(POST_WRITER_VALIDATOR), str(v),
             "--channel", ch_key],
            capture_output=True, text=True
        )
        status = "CLEAN" if r.returncode == 0 else (
            "WARN" if r.returncode == 1 else "CRITICAL")
        print(f"  [{status}] {v.name}")
        if r.returncode == 2:
            failures.append(v_path)
            print(r.stdout[-400:])

    if failures:
        print(f"\n{len(failures)} variants blocked. Review and fix before shipping.")
        return 2
    print(f"\nAll {len(args.variants)} variants pass hard rules.")
    return 0


def main():
    ap = argparse.ArgumentParser(description="Repurpose a source post for additional channels.")
    sub = ap.add_subparsers(dest="mode", required=True)

    p1 = sub.add_parser("inspect", help="Parse source and emit structured hints as JSON.")
    p1.add_argument("source_file", type=str)

    p2 = sub.add_parser("save", help="Save a drafted variant with proper frontmatter.")
    p2.add_argument("source_file", type=str)
    p2.add_argument("--target", required=True,
                    help="Target channel-format key, e.g. x-thread, instagram-carousel")
    p2.add_argument("--format", default="",
                    help="Override format (optional; derived from --target if omitted)")
    p2.add_argument("--body-file", required=True,
                    help="File containing the drafted variant body (no frontmatter)")
    p2.add_argument("--hook-preservation", default="preserved",
                    help="preserved | adapted (<reason>) | new")

    p3 = sub.add_parser("link", help="Link source to variants + validate each.")
    p3.add_argument("source_file", type=str)
    p3.add_argument("--variants", nargs="+", required=True,
                    help="List of variant file paths created this run")

    args = ap.parse_args()

    if args.mode == "inspect":
        sys.exit(inspect_cmd(args))
    if args.mode == "save":
        sys.exit(save_cmd(args))
    if args.mode == "link":
        sys.exit(link_cmd(args))


if __name__ == "__main__":
    main()
