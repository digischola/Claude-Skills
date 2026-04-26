#!/usr/bin/env python3
"""
Scheduler tick — main loop.

Runs every 5 minutes via macOS LaunchAgent. Per tick:
  1. Acquire /tmp/digischola-scheduler.lock (fcntl flock) — prevent concurrent ticks
  2. Refresh proactive: warn if any token expires in <7d
  3. Scan brand/queue/pending-approval/ for due drafts
  4. Dispatch to channel publisher
  5. Update frontmatter, move file to published/ on success
  6. Log everything to brand/scheduler.log
  7. Re-notify manual-channel posts that are >24h since notification
  8. Mark manual-channel posts as `manual_publish_overdue` if >48h since notification

Usage:
  python3 tick.py                # one tick (LaunchAgent invokes this)
  python3 tick.py --dry-run      # show what would happen, no API calls / no file moves
  python3 tick.py --once --verbose

Exit codes:
  0 = ok (even if no work or some failures)
  1 = lock contention (another tick in flight) — LaunchAgent retries next interval
  2 = catastrophic error (couldn't load drafts / write log)
"""

from __future__ import annotations

import argparse
import fcntl
import logging
import shutil
import sys
import traceback
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

# Add parent dir to path so we can import sibling modules
sys.path.insert(0, str(Path(__file__).resolve().parent))

import frontmatter_io as fio
import token_store
from publishers import linkedin as li_pub
from publishers import x as x_pub
from publishers import manual as manual_pub


DEFAULT_BRAND = Path("/Users/digischola/Desktop/Digischola")
LOCK_PATH = Path("/tmp/digischola-scheduler.lock")
MAX_ATTEMPTS = 4
RETRY_BACKOFFS = [5, 30, 120, 0]  # seconds: attempt 1→5s, 2→30s, 3→120s, 4→stop


def setup_logging(brand_folder: Path, verbose: bool):
    log_path = brand_folder / "scheduler.log"
    handlers = [
        logging.FileHandler(log_path, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ]
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)-7s %(message)s",
        handlers=handlers,
    )
    return log_path


def log_failure(brand_folder: Path, draft: Path, error: str, traceback_str: str = ""):
    fail_path = brand_folder / "scheduler-failures.log"
    with open(fail_path, "a", encoding="utf-8") as f:
        f.write(f"\n[{datetime.now(timezone.utc).isoformat()}] {draft.name}\n")
        f.write(f"  error: {error}\n")
        if traceback_str:
            f.write(f"  traceback:\n{traceback_str}\n")


def acquire_lock():
    """Returns the open lock file. Caller must keep the reference for the lock to hold."""
    f = open(LOCK_PATH, "w")
    try:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        return f
    except BlockingIOError:
        f.close()
        return None


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def scan_due(brand_folder: Path) -> list[Path]:
    """Return draft paths whose scheduled_at is past AND status is scheduled or failed-retry-due."""
    pending = brand_folder / "brand" / "queue" / "pending-approval"
    if not pending.exists():
        return []
    due = []
    nu = now_utc()
    for path in sorted(pending.glob("*.md")):
        try:
            fm, _ = fio.read(path)
        except Exception as e:
            logging.warning(f"failed to parse {path.name}: {e}")
            continue
        if fio.is_due(fm, nu):
            due.append(path)
    return due


def scan_overdue_manual(brand_folder: Path) -> list[Path]:
    """Return notified manual-channel drafts that are 24h+ since notification."""
    pending = brand_folder / "brand" / "queue" / "pending-approval"
    if not pending.exists():
        return []
    overdue = []
    nu = now_utc()
    for path in sorted(pending.glob("*.md")):
        try:
            fm, _ = fio.read(path)
        except Exception:
            continue
        if fm.get("posting_status") != "notified":
            continue
        notified_at = fio.parse_iso(fm.get("notified_at"))
        if not notified_at:
            continue
        if notified_at.tzinfo is None:
            notified_at = notified_at.replace(tzinfo=timezone.utc)
        hours = (nu - notified_at).total_seconds() / 3600
        if hours >= 24:
            overdue.append((path, fm, hours))
    return overdue


def dispatch(draft: Path, brand_folder: Path, dry_run: bool) -> str:
    """Publish a single draft. Returns the resulting status string."""
    fm, body = fio.read(draft)
    channel = fm.get("channel", "").lower()
    entry_id = fm.get("entry_id", draft.stem)

    if dry_run:
        logging.info(f"  [DRY-RUN] would publish {entry_id} → {channel}")
        return "dry_run"

    fio.mark_posting(draft)
    # X is routed to manual_pub as of 2026-04-20: console.x.com migrated to pay-per-use,
    # the free 1500/mo tier is gone. The X autonomous publisher code is kept in publishers/x.py
    # for the day X re-introduces free posting OR if the user funds credits — flip back here.
    publisher_map = {
        "linkedin": li_pub.publish_draft,
        "x": manual_pub.publish_draft,
        "twitter": manual_pub.publish_draft,
        "instagram": manual_pub.publish_draft,
        "facebook": manual_pub.publish_draft,
        "whatsapp": manual_pub.publish_draft,
    }
    if channel not in publisher_map:
        fio.mark_failed(draft, f"unknown_channel: {channel}", attempts=MAX_ATTEMPTS)
        return "failed"

    try:
        result = publisher_map[channel](fm, body, brand_folder)
    except Exception as e:
        tb = traceback.format_exc()
        log_failure(brand_folder, draft, str(e), tb)
        attempts = int(fm.get("posting_attempts", 0)) + 1
        if attempts >= MAX_ATTEMPTS:
            fio.mark_failed(draft, f"exception: {e}", attempts)
            # Click-to-reveal the draft (2026-04-22 UX batch).
            manual_pub.fire_failure_notification(channel, entry_id, str(e),
                                                 draft_path=draft)
        else:
            fio.mark_retry_due(draft, str(e), attempts, RETRY_BACKOFFS[min(attempts - 1, 2)])
        return "exception"

    if result.status == "posted":
        fio.mark_posted(draft, result.url or "", via="api")
        # Move to published/
        published_dir = brand_folder / "brand" / "queue" / "published"
        published_dir.mkdir(parents=True, exist_ok=True)
        target = published_dir / draft.name
        shutil.move(str(draft), str(target))
        logging.info(f"  ✓ {entry_id} → {channel} → {result.url}")
        # Click-to-open ship-success banner (added 2026-04-22 notification-UX
        # batch per backlog #5). Previously autonomous ships were silent; now
        # user gets a banner they can click to verify the live post.
        try:
            manual_pub.fire_ship_success_notification(
                channel, entry_id, result.url,
            )
        except Exception as e:
            logging.warning(f"  (ship-success notify failed: {e})")
        return "posted"
    if result.status == "notified":
        fio.mark_notified(draft)
        logging.info(f"  ◯ {entry_id} → {channel} (notification fired)")
        return "notified"
    if result.status == "retry_due":
        attempts = int(fm.get("posting_attempts", 0)) + 1
        if attempts >= MAX_ATTEMPTS:
            fio.mark_failed(draft, result.reason or "retry_exhausted", attempts)
            manual_pub.fire_failure_notification(channel, entry_id,
                                                 result.reason or "",
                                                 draft_path=draft)
            logging.warning(f"  ✗ {entry_id} → {channel} permanent fail: {result.reason}")
            return "failed"
        backoff = result.retry_after_sec or RETRY_BACKOFFS[min(attempts - 1, 2)]
        fio.mark_retry_due(draft, result.reason or "transient", attempts, backoff)
        logging.warning(f"  … {entry_id} → {channel} retry {attempts}/{MAX_ATTEMPTS} after {backoff}s")
        return "retry"
    # status == "failed"
    attempts = int(fm.get("posting_attempts", 0)) + 1
    fio.mark_failed(draft, result.reason or "unknown", attempts)
    manual_pub.fire_failure_notification(channel, entry_id,
                                         result.reason or "",
                                         draft_path=draft)
    logging.warning(f"  ✗ {entry_id} → {channel} fail: {result.reason}")
    return "failed"


def check_token_expiry():
    """Fire proactive notifications if any platform token is expiring soon."""
    for platform in ("linkedin", "x"):
        if token_store.get(f"{platform}_access_token") is None:
            continue  # not set up yet
        if token_store.is_token_expiring_soon(platform, days=7):
            exp = token_store.get_expires_at(platform)
            if not exp:
                days_left = 0
            else:
                days_left = max(0, (exp - now_utc()).days)
            manual_pub.fire_token_expiring_notification(platform, days_left)
            logging.info(f"  ⚠ {platform} token expires in {days_left} days")


def tick(brand_folder: Path, dry_run: bool, verbose: bool, skip_lock: bool = False):
    log_path = setup_logging(brand_folder, verbose)
    logging.info(f"tick start (dry_run={dry_run}) brand={brand_folder}")

    if not skip_lock:
        lock = acquire_lock()
        if lock is None:
            logging.warning("another tick is in flight; skipping")
            sys.exit(1)
    else:
        lock = None

    try:
        # Token-expiry proactive check
        try:
            check_token_expiry()
        except Exception as e:
            logging.warning(f"token expiry check failed: {e}")

        # Due drafts
        due = scan_due(brand_folder)
        logging.info(f"  scanned: {len(due)} due drafts")
        results = {"posted": 0, "notified": 0, "retry": 0, "failed": 0, "exception": 0, "dry_run": 0}
        for draft in due:
            try:
                r = dispatch(draft, brand_folder, dry_run)
                results[r] = results.get(r, 0) + 1
            except Exception as e:
                tb = traceback.format_exc()
                log_failure(brand_folder, draft, f"dispatcher: {e}", tb)
                logging.error(f"  ✗ {draft.name} dispatcher exception: {e}")
                results["exception"] += 1

        # Manual-channel overdue re-notifications.
        #
        # Throttle: only re-fire if it's been ≥RENOTIFY_COOLDOWN_HOURS since the
        # last re-notification (or no re-notification yet). Without this throttle
        # the StartInterval=900 cron would fire a banner every 15 min for every
        # overdue manual post — user reported "3-4 prompts every 15 min, can't
        # manage notifications." Cooldown is 4h per scheduler-publisher
        # Learnings 2026-04-26b.
        RENOTIFY_COOLDOWN_HOURS = 4
        overdue = scan_overdue_manual(brand_folder)
        skipped_in_cooldown = 0
        for draft, fm, hours in overdue:
            channel = fm.get("channel", "?")
            entry_id = fm.get("entry_id", draft.stem)
            if hours >= 48 and not dry_run:
                fio.update_fields(draft, posting_status="manual_publish_overdue",
                                  manual_overdue_at=fio.now_ist_iso())
                logging.warning(f"  ⊘ {entry_id} {channel} marked manual_publish_overdue ({hours:.0f}h)")
                continue

            # 24-48h window: re-notify with 4h cooldown.
            last_renotified = fio.parse_iso(fm.get("last_renotified_at"))
            should_renotify = True
            if last_renotified is not None:
                if last_renotified.tzinfo is None:
                    last_renotified = last_renotified.replace(tzinfo=timezone.utc)
                hours_since_last = (now_utc() - last_renotified).total_seconds() / 3600
                if hours_since_last < RENOTIFY_COOLDOWN_HOURS:
                    should_renotify = False
                    skipped_in_cooldown += 1
                    logging.debug(f"  ⏸ {entry_id} {channel} re-notify skipped "
                                  f"({hours_since_last:.1f}h since last, "
                                  f"<{RENOTIFY_COOLDOWN_HOURS}h cooldown)")

            if should_renotify:
                if not dry_run:
                    # Pass draft path so banner click reveals the file in Finder
                    # (2026-04-22 UX batch: banners previously had no click action).
                    manual_pub.fire_overdue_reminder(channel, entry_id, int(hours),
                                                    draft_path=draft)
                    fio.update_fields(draft, last_renotified_at=fio.now_ist_iso())
                logging.info(f"  ↻ {entry_id} {channel} re-notified ({hours:.0f}h since)")

        if skipped_in_cooldown:
            logging.info(f"  re-notify cooldown: {skipped_in_cooldown} skipped")

        logging.info(f"tick end: {results} (overdue manual: {len(overdue)})")
    finally:
        if lock is not None:
            lock.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--brand-folder", type=Path, default=DEFAULT_BRAND)
    ap.add_argument("--dry-run", action="store_true",
                    help="Don't actually publish or move files; just log what would happen")
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--once", action="store_true",
                    help="Run one tick and exit (default behavior; flag is for clarity)")
    ap.add_argument("--skip-lock", action="store_true",
                    help="Skip the flock — only for debugging from a different shell")
    args = ap.parse_args()
    tick(args.brand_folder, args.dry_run, args.verbose, args.skip_lock)


if __name__ == "__main__":
    main()
