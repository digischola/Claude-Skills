#!/usr/bin/env python3
"""
Ship one draft RIGHT NOW (ignore scheduled_at).

Usage:
  python3 ship_now.py <path/to/draft.md>
  python3 ship_now.py <path/to/draft.md> --dry-run
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import frontmatter_io as fio
from tick import dispatch, DEFAULT_BRAND, setup_logging


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("draft", type=Path)
    ap.add_argument("--brand-folder", type=Path, default=DEFAULT_BRAND)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    if not args.draft.exists():
        sys.exit(f"Draft not found: {args.draft}")

    setup_logging(args.brand_folder, args.verbose)

    # Force-set scheduled_at to now if absent so dispatch's eligibility check passes.
    fm, _ = fio.read(args.draft)
    if not fm.get("scheduled_at"):
        fio.update_fields(args.draft, scheduled_at=fio.now_ist_iso(),
                          posting_status="scheduled")
    elif fm.get("posting_status") in ("posted", "posting"):
        sys.exit(f"Draft is already {fm['posting_status']}; refusing to ship.")
    else:
        # Reset retry/failure state and force re-attempt
        fio.update_fields(args.draft,
                          posting_status="scheduled",
                          posting_attempts=0,
                          posting_next_retry_at=None)

    result = dispatch(args.draft, args.brand_folder, args.dry_run)
    print(f"\nResult: {result}")
    sys.exit(0 if result in ("posted", "notified", "dry_run") else 1)


if __name__ == "__main__":
    main()
