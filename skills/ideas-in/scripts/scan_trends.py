#!/usr/bin/env python3
"""Trend-scan: append trend candidates to idea-bank.json.

Claude (the agent) runs WebSearch for the pillar queries from
references/trend-scan-flow.md and pipes the parsed results to this script.

Usage:
  python3 scan_trends.py \
    --brand-folder /Users/digischola/Desktop/Digischola \
    --pillar "Landing-Page Conversion Craft" \
    --headline "..." --url "https://..." --score 8 --tags lp,trend

Or pipe a JSON list of candidates via --candidates-file:
  python3 scan_trends.py --brand-folder ... --candidates-file /tmp/cands.json
  candidates.json shape:
    [{"pillar": "...", "headline": "...", "url": "...", "score": 8, "tags": ["..."]}]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from idea_bank_io import append_entry, dedup_url

PILLAR_TO_CHANNEL_HINT = {
    "Landing-Page Conversion Craft": ["LinkedIn", "X"],
    "Solo Freelance Ops": ["LinkedIn", "X"],
    "Small-Budget Paid Media": ["LinkedIn", "X"],
}


def add_trend(
    brand_folder: Path,
    pillar: str,
    headline: str,
    url: str,
    score: int,
    tags: list[str],
) -> str | None:
    if not url:
        print(f"skip (no url): {headline[:60]}", file=sys.stderr)
        return None
    if score < 6:
        print(f"skip (score<6): {headline[:60]}", file=sys.stderr)
        return None
    if dedup_url(brand_folder, url):
        print(f"skip (dup url): {url}", file=sys.stderr)
        return None

    entry = {
        "type": "trend",
        "raw_note": headline.strip(),
        "source_url": url,
        "pillar": pillar,
        "relevance_score": score,
        "channel_fit": PILLAR_TO_CHANNEL_HINT.get(pillar, ["LinkedIn", "X"]),
        "format_candidates": ["LI-post", "X-tweet"],
        "tags": list({"trend", *(tags or [])}),
    }
    return append_entry(brand_folder, entry)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--brand-folder", type=Path, required=True)
    ap.add_argument("--pillar")
    ap.add_argument("--headline")
    ap.add_argument("--url")
    ap.add_argument("--score", type=int)
    ap.add_argument("--tags", default="")
    ap.add_argument("--candidates-file", type=Path)
    args = ap.parse_args()

    added: list[str] = []
    skipped = 0

    if args.candidates_file and args.candidates_file.exists():
        candidates = json.loads(args.candidates_file.read_text())
        for c in candidates:
            new_id = add_trend(
                args.brand_folder,
                c.get("pillar", ""),
                c.get("headline", ""),
                c.get("url", ""),
                int(c.get("score", 0)),
                c.get("tags", []),
            )
            if new_id:
                added.append(new_id)
            else:
                skipped += 1
    elif args.pillar and args.headline and args.url:
        tags = [t.strip() for t in (args.tags or "").split(",") if t.strip()]
        new_id = add_trend(args.brand_folder, args.pillar, args.headline, args.url, args.score or 0, tags)
        if new_id:
            added.append(new_id)
        else:
            skipped = 1
    else:
        print("error: pass --candidates-file OR --pillar+--headline+--url+--score", file=sys.stderr)
        return 2

    print(f"trend-scan: {len(added)} added, {skipped} skipped")
    for a in added:
        print(f"  + {a}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
