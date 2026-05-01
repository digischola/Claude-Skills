#!/usr/bin/env python3
"""Capture mode: append a structured entry to idea-bank.json.

Usage:
  python3 capture.py \
    --brand-folder /Users/digischola/Desktop/Digischola \
    --type client-win \
    --raw-note "Thrive +188% sales after LP fix" \
    --suggested-pillar "Landing-Page Conversion Craft" \
    --channel-fit linkedin,x,instagram \
    --tags thrive,client-win,2026-04
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from idea_bank_io import append_entry, VALID_TYPES


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--brand-folder", type=Path, required=True)
    ap.add_argument("--type", required=True, choices=sorted(VALID_TYPES))
    ap.add_argument("--raw-note", required=True)
    ap.add_argument("--suggested-pillar", default="")
    ap.add_argument("--channel-fit", default="", help="comma-separated")
    ap.add_argument("--format-candidates", default="", help="comma-separated")
    ap.add_argument("--tags", default="", help="comma-separated")
    ap.add_argument("--client-handle", default="")
    ap.add_argument("--source-url", default="")
    args = ap.parse_args()

    entry: dict = {
        "type": args.type,
        "raw_note": args.raw_note,
    }
    if args.suggested_pillar:
        entry["suggested_pillar"] = args.suggested_pillar
    if args.channel_fit:
        entry["channel_fit"] = [c.strip() for c in args.channel_fit.split(",") if c.strip()]
    if args.format_candidates:
        entry["format_candidates"] = [c.strip() for c in args.format_candidates.split(",") if c.strip()]
    if args.tags:
        entry["tags"] = [t.strip() for t in args.tags.split(",") if t.strip()]
    if args.client_handle:
        entry["client_handle"] = args.client_handle
    if args.source_url:
        entry["source_url"] = args.source_url

    new_id = append_entry(args.brand_folder, entry)
    print(f"captured: {new_id} ({args.type})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
