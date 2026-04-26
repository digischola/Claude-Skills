#!/usr/bin/env python3
"""
Install the macOS LaunchAgent that fires `tick.py` every 5 minutes.

Writes ~/Library/LaunchAgents/com.digischola.scheduler.plist and loads it via
launchctl. Idempotent — safe to re-run after edits (use --force to overwrite).

Usage:
  python3 install_launchagent.py
  python3 install_launchagent.py --force          # overwrite existing
  python3 install_launchagent.py --interval 600   # tick every 10 min instead of 5
  python3 install_launchagent.py --uninstall
  python3 install_launchagent.py --status
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

LABEL = "com.digischola.scheduler"
PLIST_PATH = Path.home() / "Library" / "LaunchAgents" / f"{LABEL}.plist"
TICK_SCRIPT = Path("/Users/digischola/Desktop/Claude Skills/skills/scheduler-publisher/scripts/tick.py")
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
        <string>{tick_script}</string>
        <string>--brand-folder</string>
        <string>{brand_folder}</string>
    </array>

    <key>StartInterval</key>
    <integer>{interval}</integer>

    <key>RunAtLoad</key>
    <true/>

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
    """Return the absolute path to python3 we should use in the plist."""
    for cand in (PYTHON_DEFAULT, shutil.which("python3"), "/usr/bin/python3"):
        if cand and Path(cand).exists():
            return cand
    sys.exit("No python3 found. Install Homebrew + python3 first.")


def render_plist(interval: int) -> str:
    return PLIST_TEMPLATE.format(
        label=LABEL,
        python=find_python(),
        tick_script=str(TICK_SCRIPT),
        brand_folder=str(BRAND_FOLDER),
        interval=interval,
        stdout=str(Path.home() / "Library" / "Logs" / "digischola" / "scheduler.stdout.log"),
        stderr=str(Path.home() / "Library" / "Logs" / "digischola" / "scheduler.stderr.log"),
        home=str(Path.home()),
    )


def is_loaded() -> bool:
    r = subprocess.run(["launchctl", "list", LABEL], capture_output=True, text=True)
    return r.returncode == 0


def unload():
    subprocess.run(["launchctl", "unload", str(PLIST_PATH)], capture_output=True, text=True)


def load():
    r = subprocess.run(["launchctl", "load", str(PLIST_PATH)], capture_output=True, text=True)
    if r.returncode != 0:
        print(f"  launchctl load stderr: {r.stderr}", file=sys.stderr)
        return False
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--interval", type=int, default=300, help="Seconds between ticks (default 300 = 5min)")
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
    plist_content = render_plist(args.interval)
    PLIST_PATH.write_text(plist_content)
    print(f"✓ Wrote {PLIST_PATH}")

    if is_loaded():
        unload()
    if load():
        print(f"✓ Loaded into launchctl as {LABEL}")
        print(f"  Will tick every {args.interval}s")
        print(f"  Logs: {BRAND_FOLDER}/scheduler.log")
        print(f"  stdout: {BRAND_FOLDER}/scheduler.stdout.log")
        print(f"  stderr: {BRAND_FOLDER}/scheduler.stderr.log")
        print(f"\nVerify:  launchctl list | grep {LABEL}")
    else:
        sys.exit("launchctl load failed; see stderr above")


if __name__ == "__main__":
    main()
