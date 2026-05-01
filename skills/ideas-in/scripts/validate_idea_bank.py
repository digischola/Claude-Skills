#!/usr/bin/env python3
"""Validate idea-bank.json against schema v2.0 + sanity rules.

Exit codes:
  0 = clean
  1 = warnings
  2 = CRITICAL (schema break)
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from idea_bank_io import load, VALID_TYPES, VALID_STATUS


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--brand-folder", type=Path, required=True)
    args = ap.parse_args()

    data = load(args.brand_folder)
    critical: list[str] = []
    warnings: list[str] = []

    if data.get("schema_version") != "2.0":
        critical.append(f"schema_version != 2.0 (got {data.get('schema_version')!r})")

    seen_ids: set[str] = set()
    now = datetime.now(timezone.utc)

    for i, e in enumerate(data.get("entries", [])):
        loc = f"entry[{i}]"
        eid = e.get("id")
        if not eid:
            critical.append(f"{loc}: missing id")
        elif eid in seen_ids:
            critical.append(f"{loc}: duplicate id {eid}")
        else:
            seen_ids.add(eid)

        t = e.get("type")
        if t not in VALID_TYPES:
            critical.append(f"{loc}: invalid type {t!r}")

        s = e.get("status", "raw")
        if s not in VALID_STATUS:
            critical.append(f"{loc}: invalid status {s!r}")

        if not e.get("raw_note"):
            critical.append(f"{loc}: missing raw_note")

        ts = e.get("captured_at")
        if not ts:
            warnings.append(f"{loc}: missing captured_at")
        else:
            try:
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                if dt > now:
                    critical.append(f"{loc}: captured_at in the future ({ts})")
            except (ValueError, AttributeError):
                warnings.append(f"{loc}: captured_at not ISO8601 ({ts})")

        if t == "trend" and not e.get("source_url"):
            critical.append(f"{loc}: trend entry missing source_url")
        if t == "peer-pattern" and not e.get("creator_handle"):
            critical.append(f"{loc}: peer-pattern entry missing creator_handle")

    print(f"\n=== validate_idea_bank.py ===")
    print(f"entries: {len(data.get('entries', []))}")
    print(f"unique ids: {len(seen_ids)}")
    if critical:
        print(f"\n  CRITICAL ({len(critical)}):")
        for c in critical:
            print(f"    - {c}")
    if warnings:
        print(f"\n  WARNING ({len(warnings)}):")
        for w in warnings:
            print(f"    - {w}")
    if not critical and not warnings:
        print("\n  All checks passed.")
        return 0
    if critical:
        return 2
    return 1


if __name__ == "__main__":
    sys.exit(main())
