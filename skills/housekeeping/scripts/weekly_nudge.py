#!/usr/bin/env python3
"""
weekly_nudge.py — Fire the macOS notification + clipboard prompt for the weekly cleanup.

Invoked by LaunchAgent at Saturday 10:00 IST. Mirrors weekly-ritual's nudge pattern:
notification + clipboard prompt + update state file. User pastes the prompt into
Claude Code when they're ready to run the cleanup.

Never deletes anything. Purely a UX nudge.
"""
from __future__ import annotations
import json
import os
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

HOME = Path(os.path.expanduser("~"))
SKILL_DIR = Path(__file__).resolve().parent.parent
STATE_FILE = SKILL_DIR / "housekeeping.state.json"

IST = timezone(timedelta(hours=5, minutes=30))
PROMPT = "run housekeeping"


def osascript(script: str) -> None:
    try:
        subprocess.run(["osascript", "-e", script], check=False, timeout=10)
    except Exception:
        pass


def pbcopy(text: str) -> None:
    try:
        subprocess.run(["pbcopy"], input=text.encode("utf-8"), check=False, timeout=5)
    except Exception:
        pass


def main() -> int:
    now = datetime.now(IST)

    # Read last-fire state; skip if fired within 12 hours (idempotency)
    if STATE_FILE.exists():
        try:
            state = json.loads(STATE_FILE.read_text())
            last = state.get("last_nudged_at")
            if last:
                last_dt = datetime.fromisoformat(last)
                if (now - last_dt).total_seconds() < 12 * 3600:
                    print("Skipping nudge — fired within last 12h", file=sys.stderr)
                    return 0
        except Exception:
            pass

    # Fire notification
    osascript(
        'display notification "Time to run weekly cleanup. Prompt copied to clipboard — '
        'paste in Claude Code." with title "Housekeeping" sound name "Submarine"'
    )

    # Clip prompt
    pbcopy(PROMPT)

    # Update state
    state = {}
    if STATE_FILE.exists():
        try:
            state = json.loads(STATE_FILE.read_text())
        except Exception:
            state = {}
    state["last_nudged_at"] = now.isoformat(timespec="seconds")
    STATE_FILE.write_text(json.dumps(state, indent=2))

    print(f"Nudge fired at {now.isoformat(timespec='seconds')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
