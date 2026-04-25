#!/usr/bin/env python3
"""
Mark a manual-channel post (Instagram / Facebook / WhatsApp) as published.

After scheduler-publisher fires the macOS notification + clipboard-copies the
caption + reveals the asset folder, the user posts manually in the native app.
Then runs this script with the live URL to update the draft's frontmatter and
move the file to brand/queue/published/.

Usage:
  python3 confirm_published.py <path/to/draft.md>
  python3 confirm_published.py <path/to/draft.md> --url https://instagram.com/p/...
  python3 confirm_published.py <path/to/draft.md> --skip-url     # if you don't have the URL
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import frontmatter_io as fio
from tick import DEFAULT_BRAND


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("draft", type=Path)
    ap.add_argument("--brand-folder", type=Path, default=DEFAULT_BRAND)
    ap.add_argument("--url", help="The live URL of the published post")
    ap.add_argument("--skip-url", action="store_true",
                    help="Mark as published without a URL (performance-review will need one later)")
    args = ap.parse_args()

    if not args.draft.exists():
        sys.exit(f"Draft not found: {args.draft}")

    fm, _body = fio.read(args.draft)
    channel = fm.get("channel", "?")
    entry_id = fm.get("entry_id", args.draft.stem)

    if fm.get("posting_status") == "posted":
        sys.exit(f"Already marked posted: {fm.get('platform_url', '?')}")

    url = args.url
    if not url and not args.skip_url:
        print(f"\nMarking {entry_id} ({channel}) as published.")
        print("Paste the live URL from the post (or Enter to skip):")
        url = input("URL: ").strip()
        if not url:
            print("(no URL provided)")

    fio.mark_posted(args.draft, url or "", via="manual")

    # Move to published/
    published_dir = args.brand_folder / "brand" / "queue" / "published"
    published_dir.mkdir(parents=True, exist_ok=True)
    target = published_dir / args.draft.name
    shutil.move(str(args.draft), str(target))

    print(f"\n✓ Marked posted and moved to published/")
    print(f"  → {target}")
    if url:
        print(f"  → {url}")


if __name__ == "__main__":
    main()
