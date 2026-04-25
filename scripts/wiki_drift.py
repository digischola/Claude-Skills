#!/usr/bin/env python3
"""
wiki_drift.py — snapshot key wiki files, surface changes over time.

Wikis are the load-bearing identity store: voice-guide, brand-config, ICP, pillars,
strategic-context. Skill outputs are tested against wiki state. If a wiki file changes
silently and a downstream skill keeps producing the old voice, that's drift.

This script:
  - Daily: takes a SHA-256 + size snapshot of each tracked wiki file, appends to
    ~/.claude-wiki-snapshots.jsonl (one line per file per day).
  - Weekly (Sunday): emits a markdown drift report at
    ~/Claude-Skills/scripts/logs/wiki-drift-WYY.md showing what changed in the last 7 days.

Tracked files (configurable below):
  - ~/Desktop/Digischola/brand/* (personal-brand wiki)
  - ~/Desktop/Digischola/strategic-context.md
  - ~/Claude-Skills/shared-context/strategic-context.md (skills strategic context — not kernel)

Usage:
  wiki_drift.py                Take snapshot. If today is Sunday, also emit weekly report.
  wiki_drift.py --snapshot     Only take snapshot (no report).
  wiki_drift.py --report       Only emit report (no snapshot).
  wiki_drift.py --status       Show what's tracked and current snapshot count.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

HOME = Path.home()
REPO_ROOT = Path(__file__).resolve().parent.parent
SNAPSHOT_LOG = HOME / ".claude-wiki-snapshots.jsonl"
REPORT_DIR = REPO_ROOT / "scripts" / "logs"

TRACKED: list[Path] = [
    HOME / "Desktop" / "Digischola" / "brand" / "voice-guide.md",
    HOME / "Desktop" / "Digischola" / "brand" / "pillars.md",
    HOME / "Desktop" / "Digischola" / "brand" / "icp.md",
    HOME / "Desktop" / "Digischola" / "brand" / "credentials.md",
    HOME / "Desktop" / "Digischola" / "brand" / "channel-playbook.md",
    HOME / "Desktop" / "Digischola" / "brand" / "brand-identity.md",
    HOME / "Desktop" / "Digischola" / "brand" / "idea-bank.json",
    HOME / "Desktop" / "Digischola" / "strategic-context.md",
    REPO_ROOT / "shared-context" / "strategic-context.md",
]


def notify(title: str, msg: str) -> None:
    try:
        subprocess.run(
            ["/usr/bin/osascript", "-e",
             f'display notification "{msg}" with title "{title}" sound name "Funk"'],
            check=False, capture_output=True, timeout=5,
        )
    except Exception:
        pass


def hash_file(p: Path) -> tuple[str, int] | None:
    if not p.is_file():
        return None
    h = hashlib.sha256()
    size = 0
    with p.open("rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
            size += len(chunk)
    return h.hexdigest(), size


def take_snapshot() -> int:
    today = dt.date.today().isoformat()
    rows: list[dict] = []
    for p in TRACKED:
        result = hash_file(p)
        if result is None:
            rows.append({
                "date": today, "path": str(p), "exists": False,
                "sha256": None, "size": None,
            })
        else:
            sha, size = result
            rows.append({
                "date": today, "path": str(p), "exists": True,
                "sha256": sha, "size": size,
            })

    with SNAPSHOT_LOG.open("a") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")
    return len(rows)


def load_snapshots() -> list[dict]:
    if not SNAPSHOT_LOG.is_file():
        return []
    rows: list[dict] = []
    for line in SNAPSHOT_LOG.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return rows


def emit_report() -> Path | None:
    """Emit a markdown report covering the last 7 days of snapshots."""
    rows = load_snapshots()
    if not rows:
        return None

    today = dt.date.today()
    cutoff = today - dt.timedelta(days=7)
    iso_year, iso_week, _ = today.isocalendar()

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORT_DIR / f"wiki-drift-{iso_year}-W{iso_week:02d}.md"

    by_path: dict[str, list[dict]] = {}
    for r in rows:
        d = dt.date.fromisoformat(r["date"])
        if d >= cutoff:
            by_path.setdefault(r["path"], []).append(r)

    drifted: list[tuple[str, str, str]] = []  # (path, old_sha, new_sha)
    stable: list[str] = []
    missing: list[str] = []

    for path, observations in by_path.items():
        observations.sort(key=lambda x: x["date"])
        first = observations[0]
        last = observations[-1]
        if not last.get("exists"):
            missing.append(path)
        elif not first.get("exists") and last.get("exists"):
            drifted.append((path, "(did not exist)", last["sha256"][:12]))
        elif first.get("sha256") != last.get("sha256"):
            drifted.append((path, first["sha256"][:12], last["sha256"][:12]))
        else:
            stable.append(path)

    lines: list[str] = []
    lines.append(f"# Wiki Drift Report — {today.isoformat()} (W{iso_week:02d})")
    lines.append("")
    lines.append(f"Coverage: {cutoff.isoformat()} to {today.isoformat()} ({len(by_path)} tracked files)")
    lines.append("")

    lines.append(f"## Drifted ({len(drifted)})")
    if drifted:
        for path, old, new in drifted:
            short = path.replace(str(HOME), "~")
            lines.append(f"- `{short}` — {old} → {new}")
    else:
        lines.append("_None._")
    lines.append("")

    lines.append(f"## Missing ({len(missing)})")
    if missing:
        for path in missing:
            short = path.replace(str(HOME), "~")
            lines.append(f"- `{short}` — file not present in latest snapshot")
    else:
        lines.append("_None._")
    lines.append("")

    lines.append(f"## Stable ({len(stable)})")
    for path in stable:
        short = path.replace(str(HOME), "~")
        lines.append(f"- `{short}`")
    lines.append("")

    report_path.write_text("\n".join(lines))

    if drifted or missing:
        notify(
            "Wiki Drift Report",
            f"{len(drifted)} drifted, {len(missing)} missing — see {report_path.name}"
        )

    return report_path


def show_status() -> None:
    print(f"Snapshot log: {SNAPSHOT_LOG}")
    rows = load_snapshots()
    print(f"Total snapshot rows: {len(rows)}")
    if rows:
        dates = sorted({r["date"] for r in rows})
        print(f"Earliest: {dates[0]}")
        print(f"Latest:   {dates[-1]}")
    print()
    print("Tracked files:")
    for p in TRACKED:
        marker = "✓" if p.is_file() else "✗"
        short = str(p).replace(str(HOME), "~")
        print(f"  {marker} {short}")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--snapshot", action="store_true", help="snapshot only")
    p.add_argument("--report", action="store_true", help="report only")
    p.add_argument("--status", action="store_true", help="show tracked files and snapshot stats")
    args = p.parse_args()

    if args.status:
        show_status()
        return 0

    do_snapshot = args.snapshot or not (args.report or args.snapshot)
    do_report = args.report or (not args.snapshot and dt.date.today().weekday() == 6)
    # weekday: Sunday == 6 (Mon=0)

    if do_snapshot:
        n = take_snapshot()
        print(f"Snapshotted {n} files at {dt.date.today().isoformat()}.")

    if do_report:
        path = emit_report()
        if path:
            print(f"Report: {path}")
        else:
            print("No snapshots yet — skipping report.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
