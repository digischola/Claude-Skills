#!/usr/bin/env python3
"""
Show what's scheduled this week + status of recent shipments.

Usage:
  python3 ship_week.py
  python3 ship_week.py --week 2026-W17
  python3 ship_week.py --json    # for piping into other tools
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import frontmatter_io as fio
from tick import DEFAULT_BRAND


CHANNEL_ICON = {
    "linkedin": "in",
    "x": "x",
    "instagram": "ig",
    "facebook": "fb",
    "whatsapp": "wa",
}

STATUS_GLYPH = {
    "scheduled": "○",
    "posting": "…",
    "posted": "✓",
    "notified": "◐",
    "failed": "✗",
    "manual_publish_overdue": "⊘",
    None: "·",
}


def load_drafts(brand_folder: Path) -> list[tuple[Path, dict]]:
    items = []
    for sub in ("pending-approval", "published"):
        d = brand_folder / "brand" / "queue" / sub
        if not d.exists():
            continue
        for path in d.glob("*.md"):
            try:
                fm, _ = fio.read(path)
                items.append((path, fm))
            except Exception as e:
                print(f"  ! parse failed {path.name}: {e}", file=sys.stderr)
    return items


def in_week(dt_str: str | None, start: datetime, end: datetime) -> bool:
    dt = fio.parse_iso(dt_str) if dt_str else None
    if not dt:
        return False
    if dt.tzinfo is None:
        from datetime import timezone as tz_mod
        dt = dt.replace(tzinfo=tz_mod(timedelta(hours=5, minutes=30)))
    return start <= dt < end


def parse_week(week_str: str | None) -> tuple[datetime, datetime, str]:
    """Return (week_start_IST, week_end_IST, label) for a YYYY-Www string or current week."""
    from datetime import timezone as tz_mod
    ist = tz_mod(timedelta(hours=5, minutes=30))
    if not week_str:
        now = datetime.now(ist)
        year, week, _ = now.isocalendar()
    else:
        parts = week_str.replace("W", "").split("-")
        year = int(parts[0])
        week = int(parts[1])
    # Monday of this ISO week
    monday = datetime.fromisocalendar(year, week, 1).replace(tzinfo=ist)
    sunday_end = monday + timedelta(days=7)
    return monday, sunday_end, f"{year}-W{week:02d}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--brand-folder", type=Path, default=DEFAULT_BRAND)
    ap.add_argument("--week", help="ISO week, e.g. 2026-W17 (default: current week)")
    ap.add_argument("--json", action="store_true", help="Machine-readable output")
    args = ap.parse_args()

    start, end, label = parse_week(args.week)
    items = load_drafts(args.brand_folder)

    rows = []
    for path, fm in items:
        sched = fm.get("scheduled_at")
        posted = fm.get("posted_at")
        in_window = in_week(sched, start, end) or in_week(posted, start, end)
        if not in_window:
            continue
        rows.append({
            "file": path.name,
            "entry_id": fm.get("entry_id", ""),
            "channel": fm.get("channel", "?"),
            "format": fm.get("format", "?"),
            "scheduled_at": sched,
            "posting_status": fm.get("posting_status"),
            "posted_at": posted,
            "platform_url": fm.get("platform_url"),
            "attempts": fm.get("posting_attempts", 0),
            "failure_reason": fm.get("posting_failure_reason"),
        })
    rows.sort(key=lambda r: r["scheduled_at"] or "")

    if args.json:
        print(json.dumps({"week": label, "rows": rows}, indent=2, default=str))
        return

    print(f"\n=== Week {label}  ({start.strftime('%a %b %d')} → {(end - timedelta(days=1)).strftime('%a %b %d')}) ===\n")
    if not rows:
        print("  (nothing scheduled or shipped this week)")
        return

    print(f"  {'when':18s}  {'st':2s}  {'ch':3s}  {'entry':10s}  {'fmt':14s}  url/reason")
    for r in rows:
        when = (r["scheduled_at"] or r["posted_at"] or "")[:16].replace("T", " ")
        st = STATUS_GLYPH.get(r["posting_status"], "·")
        ch = CHANNEL_ICON.get(r["channel"], r["channel"][:3])
        entry = r["entry_id"][:10]
        fmt = (r["format"] or "")[:14]
        url_or_reason = r["platform_url"] or r["failure_reason"] or ""
        url_or_reason = url_or_reason[:60]
        print(f"  {when:18s}  {st}   {ch:3s}  {entry:10s}  {fmt:14s}  {url_or_reason}")

    print()
    counts = {}
    for r in rows:
        s = r["posting_status"] or "scheduled"
        counts[s] = counts.get(s, 0) + 1
    print(f"  totals: {counts}")


if __name__ == "__main__":
    main()
