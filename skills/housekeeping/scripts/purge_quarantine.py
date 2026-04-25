#!/usr/bin/env python3
"""
purge_quarantine.py — Permanently delete quarantine entries older than N days.

The only script in housekeeping that actually removes data from disk.
Only operates inside Desktop/.housekeeping-quarantine/ — defense in depth.

Usage:
    python3 purge_quarantine.py               # default 7 days
    python3 purge_quarantine.py --keep-days 14
    python3 purge_quarantine.py --dry-run
"""
from __future__ import annotations
import argparse
import json
import os
import shutil
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

HOME = Path(os.path.expanduser("~"))
DESKTOP = HOME / "Desktop"
QUARANTINE_ROOT = DESKTOP / ".housekeeping-quarantine"
SKILL_DIR = Path(__file__).resolve().parent.parent
LOG_FILE = SKILL_DIR / "housekeeping.log"

IST = timezone(timedelta(hours=5, minutes=30))


def log(msg: str) -> None:
    ts = datetime.now(IST).isoformat(timespec="seconds")
    line = f"[{ts}] [purge] {msg}\n"
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a") as f:
        f.write(line)
    print(line.rstrip(), file=sys.stderr)


def dir_size(path: Path) -> int:
    total = 0
    for root, _, files in os.walk(path, onerror=lambda e: None):
        for f in files:
            try:
                total += (Path(root) / f).lstat().st_size
            except OSError:
                pass
    return total


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--keep-days", type=int, default=7)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not QUARANTINE_ROOT.exists():
        print(f"No quarantine root at {QUARANTINE_ROOT} — nothing to purge.")
        return 0

    now = datetime.now(IST)
    cutoff = now - timedelta(days=args.keep_days)

    to_purge = []
    for child in sorted(QUARANTINE_ROOT.iterdir()):
        if not child.is_dir():
            continue
        # Parse YYYY-MM-DD folder name
        try:
            folder_date = datetime.strptime(child.name, "%Y-%m-%d").replace(tzinfo=IST)
        except ValueError:
            print(f"  [SKIP] non-date folder: {child.name}")
            continue
        if folder_date < cutoff:
            to_purge.append((child, folder_date))

    if not to_purge:
        print(f"No quarantine folders older than {args.keep_days} days.")
        return 0

    total_bytes = 0
    for folder, _ in to_purge:
        total_bytes += dir_size(folder)

    print(f"{'DRY RUN — would purge' if args.dry_run else 'Purging'} {len(to_purge)} folder(s), "
          f"{total_bytes / (1024*1024):.1f} MB total:")
    for folder, fdate in to_purge:
        age = (now - fdate).days
        size = dir_size(folder)
        print(f"  {folder.name}  ({age}d old, {size / (1024*1024):.1f} MB)")
        if not args.dry_run:
            # Safety: require path is under QUARANTINE_ROOT
            try:
                folder.resolve().relative_to(QUARANTINE_ROOT.resolve())
            except ValueError:
                log(f"REFUSED purge of path outside quarantine root: {folder}")
                continue
            try:
                shutil.rmtree(folder)
                log(f"PURGED: {folder} ({size} bytes)")
            except Exception as e:
                log(f"ERROR purging {folder}: {e}")
                print(f"  ERROR: {e}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
