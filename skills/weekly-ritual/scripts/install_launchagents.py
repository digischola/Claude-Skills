#!/usr/bin/env python3
"""
Install the Weekly Ritual macOS LaunchAgent.

Single plist with two StartCalendarInterval entries:
  Wednesday 09:00 IST → plan next cycle (historical name: "sunday" ritual)
  Monday    18:00 IST → review previous cycle (historical name: "friday" ritual)

(weekly_ritual.py auto-detects which day to fire from the weekday.)

History: 2026-04-22 Mayank shifted the posting cycle from Mon→Sun to Thu→Wed
(starting ship on Thursday, resting on Wednesday). Rituals moved accordingly
so review fires at day-5-of-cycle and planning fires on rest-day (same
relative positions as the original). The ritual labels `sunday` and `friday`
are preserved internally to avoid breaking the state file + SKILL chain; the
weekdays they fire on are the ONLY thing that changed.

  NEW cadence (locked 2026-04-22):
  - Mon 18:00 IST → review_queue + weekly_review for the previous cycle's 11 posts
  - Wed 09:00 IST → plan next cycle; first ship Thu 09:00 IST

Usage:
  python3 install_launchagents.py
  python3 install_launchagents.py --force
  python3 install_launchagents.py --status
  python3 install_launchagents.py --uninstall

Note on TCC: this script reuses the same /usr/bin/python3 that scheduler-publisher
uses. Full Disk Access for python3 was already granted there — no new grant needed.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

LABEL = "com.digischola.weekly-ritual"
PLIST_PATH = Path.home() / "Library" / "LaunchAgents" / f"{LABEL}.plist"
RITUAL_SCRIPT = Path("/Users/digischola/Desktop/Claude Skills/skills/weekly-ritual/scripts/weekly_ritual.py")
BRAND_FOLDER = Path("/Users/digischola/Desktop/Digischola")
PYTHON_DEFAULT = "/opt/homebrew/bin/python3"


PLIST_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{label}</string>

    <key>ProgramArguments</key>
    <array>
        <string>{python}</string>
        <string>{ritual_script}</string>
        <string>--day</string>
        <string>auto</string>
        <string>--brand-folder</string>
        <string>{brand_folder}</string>
    </array>

    <!-- Two cron triggers in one plist: Wed 09:00 (plan) + Mon 18:00 (review) IST -->
    <!-- macOS uses local time. Confirm system tz is IST or adjust. -->
    <!-- Shifted 2026-04-22: was Sun 09:00 + Fri 18:00 when cycle was Mon→Sun. -->
    <!-- Now cycle is Thu→Wed so rituals moved to preserve day-of-cycle semantics. -->
    <key>StartCalendarInterval</key>
    <array>
        <dict>
            <key>Weekday</key><integer>3</integer>   <!-- Wednesday 09:00 IST: Wednesday Planning (internal key: sunday) -->
            <key>Hour</key><integer>9</integer>
            <key>Minute</key><integer>0</integer>
        </dict>
        <dict>
            <key>Weekday</key><integer>1</integer>   <!-- Monday 18:00 IST: Monday Review (internal key: friday) -->
            <key>Hour</key><integer>18</integer>
            <key>Minute</key><integer>0</integer>
        </dict>
    </array>

    <key>RunAtLoad</key>
    <false/>

    <key>KeepAlive</key>
    <false/>

    <key>ThrottleInterval</key>
    <integer>30</integer>

    <key>StandardOutPath</key>
    <string>{stdout}</string>

    <key>StandardErrorPath</key>
    <string>{stderr}</string>

    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin</string>
        <key>HOME</key>
        <string>{home}</string>
    </dict>
</dict>
</plist>
"""


def find_python() -> str:
    for cand in (PYTHON_DEFAULT, shutil.which("python3"), "/usr/bin/python3"):
        if cand and Path(cand).exists():
            return cand
    sys.exit("No python3 found.")


def render_plist() -> str:
    return PLIST_TEMPLATE.format(
        label=LABEL,
        python=find_python(),
        ritual_script=str(RITUAL_SCRIPT),
        brand_folder=str(BRAND_FOLDER),
        stdout=str(BRAND_FOLDER / "weekly-ritual.stdout.log"),
        stderr=str(BRAND_FOLDER / "weekly-ritual.stderr.log"),
        home=str(Path.home()),
    )


def is_loaded() -> bool:
    r = subprocess.run(["launchctl", "list", LABEL], capture_output=True, text=True)
    return r.returncode == 0


def unload():
    subprocess.run(["launchctl", "unload", str(PLIST_PATH)], capture_output=True, text=True)


def load() -> bool:
    r = subprocess.run(["launchctl", "load", str(PLIST_PATH)], capture_output=True, text=True)
    if r.returncode != 0:
        print(f"  launchctl load stderr: {r.stderr}", file=sys.stderr)
        return False
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="Overwrite existing plist")
    ap.add_argument("--uninstall", action="store_true")
    ap.add_argument("--status", action="store_true")
    args = ap.parse_args()

    if args.status:
        print(f"Plist: {PLIST_PATH}  exists={PLIST_PATH.exists()}")
        print(f"Loaded in launchctl: {is_loaded()}")
        if PLIST_PATH.exists():
            print("\nContent:")
            print(PLIST_PATH.read_text())
        return

    if args.uninstall:
        if PLIST_PATH.exists():
            unload()
            PLIST_PATH.unlink()
            print(f"Removed {PLIST_PATH}")
        else:
            print("Already uninstalled.")
        return

    if PLIST_PATH.exists() and not args.force:
        sys.exit(f"Plist already exists at {PLIST_PATH}. Pass --force to overwrite.")

    PLIST_PATH.parent.mkdir(parents=True, exist_ok=True)
    PLIST_PATH.write_text(render_plist())
    print(f"✓ Wrote {PLIST_PATH}")

    if is_loaded():
        unload()
    if load():
        print(f"✓ Loaded into launchctl as {LABEL}")
        print(f"  Wednesday 09:00 IST → Wednesday Planning ritual (clipboard: 'run wednesday planning')")
        print(f"  Monday    18:00 IST → Monday Review ritual (clipboard: 'run monday review')")
        print(f"  Logs: {BRAND_FOLDER}/weekly-ritual.log")
        print(f"\nVerify: launchctl list | grep {LABEL}")
    else:
        sys.exit("launchctl load failed")


if __name__ == "__main__":
    main()
