#!/usr/bin/env python3
"""
Assisted-publish catchup for scheduler-publisher.

When Mayank is in a Claude Code session and realizes he missed scheduled
notifications (or just wants to batch-post without waiting for each
scheduled_at), this script:

  1. Lists all drafts in queue/pending-approval/ that are:
       - status: approved
       - scheduled_at: past OR posting_status in {notified, manual_publish_overdue}
  2. For each, outputs the minimum info Claude needs to drive Chrome
     (via the Claude-in-Chrome MCP) to assist the user:
       - channel + composer URL
       - asset file paths (for file upload)
       - full caption (for paste)
       - draft file path (for confirm_published.py after)

Claude (in the session) reads this JSON and uses MCP tools (navigate,
file_upload, form_input) to drive Chrome step-by-step. The user watches and
clicks the final "Post" / "Share" button themselves — Claude never submits.

This is SAFE because:
  - Runs only during an interactive Claude session (not cron)
  - User's logged-in Chrome profile (not headless / not new cookies)
  - User clicks submit (not Claude)
  - Platforms see a human session with a visible extension

Do NOT use this from cron. Autonomous browser automation gets accounts
flagged — same reason Meta API is off-limits for this scheduler.

Usage:
  python3 assist_publish.py list [--json]             # show overdue
  python3 assist_publish.py get <filename> [--json]   # full detail for one draft
  python3 assist_publish.py mark-notified <filename>  # mark as notified (for reminders)
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import frontmatter_io as fio  # type: ignore
from tick import DEFAULT_BRAND  # type: ignore
from publishers.manual import COMPOSER_URLS  # type: ignore


IST = timezone(timedelta(hours=5, minutes=30))


# ── Draft scanning ─────────────────────────────────────────────────────────

def _parse_scheduled_at(s: str) -> datetime | None:
    if not s:
        return None
    try:
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=IST)
        return dt
    except Exception:
        return None


def scan_overdue(brand_folder: Path, include_future: bool = False) -> list[dict]:
    """Find approved drafts with scheduled_at in the past (or all, if include_future)."""
    pending = brand_folder / "brand" / "queue" / "pending-approval"
    if not pending.exists():
        return []
    now = datetime.now(IST)
    results = []
    for p in sorted(pending.glob("*.md")):
        try:
            fm, body = fio.read(p)
        except Exception:
            continue
        status = fm.get("posting_status", "draft")
        if status in {"approved", "notified", "manual_publish_overdue", "failed_retry_due"}:
            sched_str = fm.get("scheduled_at", "")
            sched_dt = _parse_scheduled_at(sched_str)
            channel = (fm.get("channel") or "").lower()
            # Skip LinkedIn — UGC API handles it, human assist not needed
            if channel == "linkedin":
                continue
            is_overdue = (sched_dt is not None and sched_dt <= now)
            if include_future or is_overdue or status in {"notified", "manual_publish_overdue"}:
                results.append({
                    "filename": p.name,
                    "path": str(p),
                    "channel": channel,
                    "format": fm.get("format") or "",
                    "entry_id": fm.get("entry_id") or "",
                    "pillar": fm.get("pillar") or "",
                    "scheduled_at": sched_str,
                    "scheduled_at_overdue": is_overdue,
                    "posting_status": status,
                    "composer_url": COMPOSER_URLS.get(channel, ""),
                    "asset_paths": list_assets(brand_folder, fm),
                    "caption": body.strip(),
                })
    # Sort oldest overdue first so Claude handles the most-overdue posts first
    results.sort(key=lambda d: d["scheduled_at"])
    return results


def list_assets(brand_folder: Path, fm: dict) -> list[str]:
    """Return absolute paths of all image/video assets for this draft."""
    entry_id = fm.get("entry_id") or ""
    if not entry_id:
        return []
    assets_root = brand_folder / "brand" / "queue" / "assets"
    if not assets_root.exists():
        return []
    IMAGE = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
    VIDEO = {".mp4", ".mov", ".webm", ".m4v"}
    paths = []
    for d in sorted(assets_root.iterdir()):
        if not d.is_dir():
            continue
        if d.name != entry_id and not d.name.startswith(f"{entry_id}-"):
            continue
        for f in sorted(d.iterdir()):
            if f.is_file() and f.suffix.lower() in (IMAGE | VIDEO):
                paths.append(str(f.resolve()))
    return paths


# ── Operations ─────────────────────────────────────────────────────────────

def cmd_list(args):
    drafts = scan_overdue(args.brand_folder, include_future=args.all)
    if args.json:
        print(json.dumps(drafts, indent=2, ensure_ascii=False))
        return
    if not drafts:
        print("No overdue drafts. All clear.")
        return
    print(f"\nOverdue / awaiting manual post: {len(drafts)}\n")
    for d in drafts:
        mark = "⚠" if d["scheduled_at_overdue"] else "·"
        asset_count = len(d["asset_paths"])
        asset_str = f" + {asset_count} asset(s)" if asset_count else ""
        hook_preview = d["caption"].split("\n", 1)[0][:60]
        print(f"  {mark} {d['scheduled_at'][:16] or 'no schedule':16}  {d['channel']:10} "
              f"{d['filename']}{asset_str}")
        print(f"     hook: {hook_preview}")
        print(f"     composer: {d['composer_url']}")
        print()


def cmd_get(args):
    drafts = scan_overdue(args.brand_folder, include_future=True)
    match = next((d for d in drafts if d["filename"] == args.filename), None)
    if not match:
        sys.exit(f"Not found in overdue list: {args.filename}")
    if args.json:
        print(json.dumps(match, indent=2, ensure_ascii=False))
    else:
        for k, v in match.items():
            if isinstance(v, list):
                print(f"  {k}:")
                for item in v:
                    print(f"    - {item}")
            else:
                print(f"  {k}: {v}")


def cmd_mark_notified(args):
    path = args.brand_folder / "brand" / "queue" / "pending-approval" / args.filename
    if not path.exists():
        sys.exit(f"File not found: {path}")
    fm, body = fio.read(path)
    fm["posting_status"] = "notified"
    fm["notified_at"] = datetime.now(IST).isoformat()
    fio.write(path, fm, body)
    print(f"Marked notified: {args.filename}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--brand-folder", type=Path, default=DEFAULT_BRAND)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_list = sub.add_parser("list", help="Show overdue / awaiting-manual drafts")
    p_list.add_argument("--json", action="store_true")
    p_list.add_argument("--all", action="store_true",
                        help="Include future scheduled drafts too")
    p_list.set_defaults(func=cmd_list)

    p_get = sub.add_parser("get", help="Full detail for one draft (for Claude to drive Chrome)")
    p_get.add_argument("filename")
    p_get.add_argument("--json", action="store_true")
    p_get.set_defaults(func=cmd_get)

    p_mark = sub.add_parser("mark-notified", help="Mark draft as notified (manually)")
    p_mark.add_argument("filename")
    p_mark.set_defaults(func=cmd_mark_notified)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
