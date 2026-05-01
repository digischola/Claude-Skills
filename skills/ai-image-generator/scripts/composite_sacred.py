#!/usr/bin/env python3
"""composite_sacred.py — composite a sacred reference image into a generated frame.

Used when a concept has reference_role == 'subject_lock_no_redraw' (deity / scripture).
The model generates background + decorative + typography only. This script overlays the
sacred subject from the reference photo into the reserved space.

Requires Pillow. If unavailable, prints fallback instructions.

Usage:
    python3 composite_sacred.py <generated.png> <sacred_reference.jpg> \
        --placement centered_60pct --output final.png
"""
import argparse
import sys
from pathlib import Path


PLACEMENT_PRESETS = {
    "centered_60pct": {"anchor": "center", "scale": 0.6},
    "centered_50pct": {"anchor": "center", "scale": 0.5},
    "centered_70pct": {"anchor": "center", "scale": 0.7},
    "upper_third_centered": {"anchor": "upper_third", "scale": 0.5},
    "right_third_centered": {"anchor": "right_third", "scale": 0.45},
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("background", help="Generated background PNG")
    ap.add_argument("subject", help="Sacred reference image (JPG/PNG)")
    ap.add_argument("--placement", default="centered_60pct", choices=list(PLACEMENT_PRESETS.keys()))
    ap.add_argument("--output", required=True)
    ap.add_argument("--soft-edge", action="store_true", help="Apply soft alpha edge to subject")
    args = ap.parse_args()

    try:
        from PIL import Image, ImageFilter
    except ImportError:
        print("x Pillow not installed. Install with: pip install Pillow")
        print("  OR composite manually in Photoshop / Affinity using these specs:")
        print(f"  - Background: {args.background}")
        print(f"  - Subject:    {args.subject}")
        print(f"  - Placement:  {args.placement}  ({PLACEMENT_PRESETS[args.placement]})")
        return 1

    bg = Image.open(args.background).convert("RGBA")
    subject = Image.open(args.subject).convert("RGBA")
    bw, bh = bg.size
    preset = PLACEMENT_PRESETS[args.placement]
    target_h = int(bh * preset["scale"])
    target_w = int(subject.width * (target_h / subject.height))
    subject_resized = subject.resize((target_w, target_h), Image.LANCZOS)

    if args.soft_edge:
        # Build a soft alpha mask
        mask = Image.new("L", subject_resized.size, 255)
        mask = mask.filter(ImageFilter.GaussianBlur(radius=8))
        subject_resized.putalpha(mask)

    # Compute paste position
    if preset["anchor"] == "center":
        x = (bw - target_w) // 2
        y = (bh - target_h) // 2
    elif preset["anchor"] == "upper_third":
        x = (bw - target_w) // 2
        y = bh // 6
    elif preset["anchor"] == "right_third":
        x = bw - target_w - (bw // 12)
        y = (bh - target_h) // 2
    else:
        x = (bw - target_w) // 2
        y = (bh - target_h) // 2

    bg.alpha_composite(subject_resized, dest=(x, y))
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    bg.convert("RGB").save(args.output, "PNG", optimize=True)
    print(f"  Composited: {args.output}  ({bw}x{bh}, subject {target_w}x{target_h} at ({x},{y}))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
