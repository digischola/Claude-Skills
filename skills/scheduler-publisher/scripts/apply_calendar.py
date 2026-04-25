#!/usr/bin/env python3
"""
Apply a content-calendar markdown to the matching pending-approval drafts.

content-calendar produces brand/calendars/YYYY-WXX.md with slot assignments per
entry_id, each line containing a day, time, channel, and entry_id. This script
reads that file, finds matching drafts, and writes scheduled_at + posting_status
into each draft's frontmatter.

Calendar format expected (flexible parser):

  ## Mon 2026-04-22
  - 09:00  linkedin  4e4eed15  text-post   (LP Craft)
  - 11:00  x         4e4eed15  thread

  ## Tue 2026-04-23
  - 14:00  instagram 4e4eed15  carousel

The parser tolerates extra columns / different separators / pipes / dashes.

Usage:
  python3 apply_calendar.py --week 2026-W17
  python3 apply_calendar.py --calendar /path/to/2026-W17.md
  python3 apply_calendar.py --week 2026-W17 --dry-run
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
# Shared notify helper (click-through via terminal-notifier)
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "shared-scripts"))

import frontmatter_io as fio
from tick import DEFAULT_BRAND

try:
    from notify import notify as _notify  # type: ignore
except ImportError:
    _notify = None


# Match a date like "2026-04-22" anywhere in a heading
DATE_IN_HEADING_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")
# Match a slot line. Tolerates `- 09:00 linkedin 4e4eed15 ...` or `| 09:00 | linkedin | 4e4eed15 |...`
SLOT_RE = re.compile(
    r"""
    ^[\s\-|*•]*                       # bullet / pipe prefix
    (?P<time>\d{1,2}:\d{2})           # HH:MM
    \s*[\s|]\s*                       # separator
    (?P<channel>linkedin|x|twitter|instagram|facebook|whatsapp)
    \s*[\s|]\s*                       # separator
    (?P<entry_id>[a-z0-9][a-z0-9-_]+) # entry id (alphanumeric + dashes)
    """,
    re.IGNORECASE | re.VERBOSE,
)


def parse_calendar(path: Path) -> list[dict]:
    """Return list of {date, time, channel, entry_id} dicts."""
    if not path.exists():
        sys.exit(f"Calendar not found: {path}")
    text = path.read_text(encoding="utf-8")

    slots = []
    current_date = None
    for line in text.splitlines():
        # Date heading
        if line.lstrip().startswith("#"):
            m = DATE_IN_HEADING_RE.search(line)
            if m:
                current_date = m.group(1)
            continue
        # Slot row (legacy `- 09:00 linkedin entry_id` format)
        m = SLOT_RE.match(line.strip())
        if m and current_date:
            slots.append({
                "date": current_date,
                "time": m.group("time"),
                "channel": m.group("channel").lower().replace("twitter", "x"),
                "entry_id": m.group("entry_id"),
            })
            continue
        # content-calendar table format: | Mon | 2026-04-27 | linkedin | text-post | Pillar | f80273f7 | trend | no |
        if line.strip().startswith("|") and line.count("|") >= 6:
            parts = [p.strip() for p in line.strip().strip("|").split("|")]
            if len(parts) >= 6:
                date = parts[1]
                channel = parts[2].lower().replace("twitter", "x")
                entry_id = parts[5]
                if (re.match(r"^\d{4}-\d{2}-\d{2}$", date)
                        and channel in {"linkedin","x","instagram","facebook","whatsapp"}
                        and re.match(r"^[a-z0-9][a-z0-9-_]+$", entry_id, re.IGNORECASE)
                        and entry_id.upper() != "GAP"):
                    slots.append({
                        "date": date,
                        "time": default_time_for_channel(channel),
                        "channel": channel,
                        "entry_id": entry_id,
                    })
    return slots


# Default posting times per channel (IST). Used when calendar doesn't specify.
DEFAULT_POSTING_TIMES = {
    "linkedin":  "09:00",   # Mon–Fri India morning
    "x":         "11:00",   # late-morning IST
    "instagram": "18:00",   # evening engagement
    "facebook":  "18:30",
    "whatsapp":  "20:00",   # Status peak
}


def default_time_for_channel(channel: str) -> str:
    return DEFAULT_POSTING_TIMES.get(channel.lower(), "09:00")


def find_draft(brand_folder: Path, entry_id: str, channel: str) -> Path | None:
    """Find the draft file in pending-approval matching this entry_id + channel."""
    pending = brand_folder / "brand" / "queue" / "pending-approval"
    if not pending.exists():
        return None
    candidates = []
    for path in pending.glob("*.md"):
        try:
            fm, _ = fio.read(path)
        except Exception:
            continue
        if fm.get("entry_id") == entry_id and fm.get("channel", "").lower() == channel:
            candidates.append(path)
    if not candidates:
        # Fallback: filename contains entry_id AND channel as a dash-bounded segment
        # (prevents matching "x" inside "text-post" etc.)
        for path in pending.glob("*.md"):
            name_lower = path.name.lower()
            segments = re.split(r"[-_.]", name_lower)
            if entry_id.lower() in name_lower and channel in segments:
                candidates.append(path)
    return candidates[0] if candidates else None


def to_ist_iso(date_str: str, time_str: str) -> str:
    from datetime import timezone as tz_mod
    ist = tz_mod(timedelta(hours=5, minutes=30))
    dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M").replace(tzinfo=ist)
    return dt.isoformat()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--brand-folder", type=Path, default=DEFAULT_BRAND)
    ap.add_argument("--week", help="ISO week e.g. 2026-W17 → reads calendars/2026-W17.md")
    ap.add_argument("--calendar", type=Path, help="Explicit path to calendar .md")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not args.calendar and not args.week:
        sys.exit("Provide --week or --calendar.")

    cal_path = args.calendar or (args.brand_folder / "brand" / "calendars" / f"{args.week}.md")
    print(f"\n=== apply_calendar  →  {cal_path.name} ===\n")
    slots = parse_calendar(cal_path)
    if not slots:
        sys.exit("No slots parsed from calendar. Check format.")

    matched = 0
    missing = 0
    for slot in slots:
        scheduled_iso = to_ist_iso(slot["date"], slot["time"])
        draft = find_draft(args.brand_folder, slot["entry_id"], slot["channel"])
        if not draft:
            print(f"  ✗ {slot['date']} {slot['time']}  {slot['channel']:9s}  {slot['entry_id']:10s}  (no draft found)")
            missing += 1
            continue
        if args.dry_run:
            print(f"  [DRY] {slot['date']} {slot['time']}  {slot['channel']:9s}  {slot['entry_id']:10s}  → {draft.name}")
        else:
            fio.update_fields(draft, scheduled_at=scheduled_iso, posting_status="scheduled")
            print(f"  ✓ {slot['date']} {slot['time']}  {slot['channel']:9s}  {slot['entry_id']:10s}  → {draft.name}")
        matched += 1

    print(f"\nMatched {matched}/{len(slots)} slots. Missing drafts: {missing}.")

    # macOS notification — refactored 2026-04-22 batch to use the central
    # notify helper. Click-to-open lands on the calendar markdown file in the
    # user's default editor (VS Code or TextEdit), so they can confirm what
    # was scheduled without hunting for the file.
    if not args.dry_run and matched > 0 and _notify is not None:
        week_label = args.week or "current week"
        _notify(
            f"Calendar applied: {week_label}",
            f"{matched} posts scheduled. Click to open calendar in editor.",
            subtitle="Digischola",
            sound="Glass",
            open_url=str(cal_path.resolve()),  # editor opens .md via file://
            group="digischola-calendar",
        )


if __name__ == "__main__":
    main()
