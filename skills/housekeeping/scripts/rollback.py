#!/usr/bin/env python3
"""
rollback.py — Restore items from quarantine to their original paths.

Reads manifest.json for the given date-folder, moves items back to original paths.
Fails loudly if destination exists (never overwrites — user must resolve manually).

Usage:
    python3 rollback.py --date 2026-04-27
    python3 rollback.py --date 2026-04-27 --pattern "*.csv"
    python3 rollback.py --date 2026-04-27 --path "Desktop/Digischola/brand/_mining/voice-samples.txt"
    python3 rollback.py --date 2026-04-27 --dry-run
"""
from __future__ import annotations
import argparse
import fnmatch
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
    line = f"[{ts}] [rollback] {msg}\n"
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a") as f:
        f.write(line)
    print(line.rstrip(), file=sys.stderr)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True, help="YYYY-MM-DD quarantine date-folder")
    ap.add_argument("--pattern", help="Filename pattern filter (fnmatch, e.g., '*.csv')")
    ap.add_argument("--path", help="Exact original path to restore")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    date_dir = QUARANTINE_ROOT / args.date
    manifest_path = date_dir / "manifest.json"

    if not manifest_path.exists():
        print(f"ERROR: no manifest at {manifest_path}")
        return 2

    manifest = json.loads(manifest_path.read_text())
    if not manifest:
        print(f"Manifest is empty — nothing to restore.")
        return 0

    # Filter
    selected = []
    for entry in manifest:
        orig = entry["original_path"]
        if args.path and orig != args.path:
            continue
        if args.pattern and not fnmatch.fnmatch(Path(orig).name, args.pattern):
            continue
        selected.append(entry)

    if not selected:
        print("No manifest entries matched the filter.")
        return 0

    print(f"{'DRY RUN — would restore' if args.dry_run else 'Restoring'} {len(selected)} items from {date_dir}")

    restored = 0
    conflicts = 0
    missing = 0
    for entry in selected:
        orig = Path(entry["original_path"])
        qpath = Path(entry["quarantine_path"])

        if not qpath.exists():
            print(f"  [MISSING] {qpath} (already purged or moved)")
            missing += 1
            continue

        if orig.exists():
            print(f"  [CONFLICT] {orig} already exists — skipping (resolve manually)")
            conflicts += 1
            continue

        if args.dry_run:
            print(f"  [WOULD RESTORE] {qpath} -> {orig}")
            continue

        orig.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.move(str(qpath), str(orig))
            log(f"RESTORED: {qpath} -> {orig}")
            print(f"  [RESTORED] {orig}")
            restored += 1
        except Exception as e:
            log(f"ERROR restoring {qpath}: {e}")
            print(f"  [ERROR] {qpath}: {e}")

    # Update manifest to drop restored entries
    if not args.dry_run and restored > 0:
        remaining = [e for e in manifest if not Path(e["quarantine_path"]).parent.exists() or Path(e["quarantine_path"]).exists()]
        # Re-check after moves: keep entries still on disk
        remaining = [e for e in manifest if Path(e["quarantine_path"]).exists()]
        manifest_path.write_text(json.dumps(remaining, indent=2))

    print(f"\n{restored} restored, {conflicts} conflicts, {missing} missing.")
    return 0 if conflicts == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
