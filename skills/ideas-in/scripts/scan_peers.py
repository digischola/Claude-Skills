#!/usr/bin/env python3
"""Peer-scan: log peer-pattern entries + advance creator-study week pointer.

Claude runs WebSearch for the week's 4 creators, parses results, calls this
script with the structured findings.

Usage:
  python3 scan_peers.py \
    --brand-folder /Users/digischola/Desktop/Digischola \
    --findings-file /tmp/peer.json

  findings.json shape:
    {
      "creators": [
        {"handle": "@justinwelsh", "pattern_formula": "...", "source_url": "...", "tags": ["..."]}
      ]
    }
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from idea_bank_io import append_entry, dedup_url


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--brand-folder", type=Path, required=True)
    ap.add_argument("--findings-file", type=Path, required=True)
    args = ap.parse_args()

    if not args.findings_file.exists():
        print(f"findings file missing: {args.findings_file}", file=sys.stderr)
        return 2

    data = json.loads(args.findings_file.read_text())
    added: list[str] = []
    skipped = 0

    for c in data.get("creators", []):
        url = c.get("source_url", "")
        if url and dedup_url(args.brand_folder, url):
            skipped += 1
            continue
        entry = {
            "type": "peer-pattern",
            "raw_note": f"{c.get('handle', '?')}: {c.get('pattern_formula', '')[:140]}",
            "creator_handle": c.get("handle", ""),
            "pattern_formula": c.get("pattern_formula", ""),
            "source_url": url,
            "tags": list({"peer-pattern", *(c.get("tags") or [])}),
            "channel_fit": ["LinkedIn", "X"],
        }
        new_id = append_entry(args.brand_folder, entry)
        added.append(new_id)

    print(f"peer-scan: {len(added)} added, {skipped} skipped")
    for a in added:
        print(f"  + {a}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
