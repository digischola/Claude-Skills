#!/usr/bin/env python3
"""
install_launchagent.py — Install macOS LaunchAgent for weekly housekeeping nudge.

Writes ~/Library/LaunchAgents/com.mayank.housekeeping.plist firing every Saturday
at 10:00 IST. LaunchAgent runs weekly_nudge.py which shows a macOS notification
and copies "run housekeeping" to the clipboard.

Usage:
    python3 install_launchagent.py              # install + load
    python3 install_launchagent.py --uninstall  # stop + remove
    python3 install_launchagent.py --dry-run    # print plist without writing
"""
from __future__ import annotations
import argparse
import os
import subprocess
import sys
from pathlib import Path

HOME = Path(os.path.expanduser("~"))
LAUNCH_AGENTS = HOME / "Library" / "LaunchAgents"
PLIST_NAME = "com.mayank.housekeeping.plist"
PLIST_PATH = LAUNCH_AGENTS / PLIST_NAME
SKILL_DIR = Path(__file__).resolve().parent.parent
NUDGE_SCRIPT = SKILL_DIR / "scripts" / "weekly_nudge.py"

LABEL = "com.mayank.housekeeping"

# Saturday = Weekday 6 in macOS launchd (Sun=0 ... Sat=6).
# Fire at 10:00 IST. macOS launchd interprets times in system local time zone;
# Mayank is in IST, so this is straightforward. If system TZ ever diverges,
# adjust Hour accordingly.

PLIST_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{label}</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/env</string>
        <string>python3</string>
        <string>{nudge_script}</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Weekday</key>
        <integer>6</integer>
        <key>Hour</key>
        <integer>10</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>{log_out}</string>
    <key>StandardErrorPath</key>
    <string>{log_err}</string>
    <key>RunAtLoad</key>
    <false/>
</dict>
</plist>
"""


def render_plist() -> str:
    return PLIST_TEMPLATE.format(
        label=LABEL,
        nudge_script=NUDGE_SCRIPT,
        log_out=SKILL_DIR / "housekeeping.launchagent.out.log",
        log_err=SKILL_DIR / "housekeeping.launchagent.err.log",
    )


def install(dry_run: bool = False) -> int:
    plist_body = render_plist()

    if dry_run:
        print(plist_body)
        return 0

    LAUNCH_AGENTS.mkdir(parents=True, exist_ok=True)
    PLIST_PATH.write_text(plist_body)
    print(f"Wrote {PLIST_PATH}")

    # Unload if already loaded (in case of re-install)
    subprocess.run(
        ["launchctl", "unload", str(PLIST_PATH)],
        capture_output=True,
    )
    result = subprocess.run(
        ["launchctl", "load", str(PLIST_PATH)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"WARNING: launchctl load returned {result.returncode}")
        print(result.stderr)
    else:
        print("LaunchAgent loaded. Will fire Saturday 10:00 IST (weekly).")

    # Sanity
    lst = subprocess.run(
        ["launchctl", "list"],
        capture_output=True, text=True,
    )
    if LABEL in lst.stdout:
        print(f"Verified: {LABEL} is loaded.")
    else:
        print(f"WARNING: {LABEL} not visible in launchctl list.")

    return 0


def uninstall() -> int:
    if not PLIST_PATH.exists():
        print(f"No plist at {PLIST_PATH} — nothing to uninstall.")
        return 0
    subprocess.run(["launchctl", "unload", str(PLIST_PATH)], capture_output=True)
    PLIST_PATH.unlink()
    print(f"Unloaded and removed {PLIST_PATH}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--uninstall", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if args.uninstall:
        return uninstall()
    return install(dry_run=args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
