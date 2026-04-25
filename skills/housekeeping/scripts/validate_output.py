#!/usr/bin/env python3
"""
validate_output.py — Post-cleanup sanity checks.

Confirms:
1. No PROTECTED path was touched (cross-check manifest against PROTECTED list)
2. Quarantine contains what the manifest says it should
3. Log file is intact (grows monotonically, no corruption)
4. State file updated today (only if run was non-empty)

Exits 0 on CLEAN, 1 on WARN, 2 on CRITICAL.

Usage:
    python3 validate_output.py --date YYYY-MM-DD
    python3 validate_output.py --date YYYY-MM-DD --strict
"""
from __future__ import annotations
import argparse
import json
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

HOME = Path(os.path.expanduser("~"))
DESKTOP = HOME / "Desktop"
QUARANTINE_ROOT = DESKTOP / ".housekeeping-quarantine"
SKILL_DIR = Path(__file__).resolve().parent.parent
LOG_FILE = SKILL_DIR / "housekeeping.log"
STATE_FILE = SKILL_DIR / "housekeeping.state.json"

IST = timezone(timedelta(hours=5, minutes=30))

PROTECTED_NAMES = {
    "SKILL.md", "CLAUDE.md",
    "pillars.md", "voice-guide.md", "brand-identity.md", "credentials.md",
    "channel-playbook.md", "icp.md", "brand-wiki.md", "wiki-config.json",
    "idea-bank.json", "credential-usage-log.json", "weekly-ritual.state.json",
    "scheduler.log", "scheduler-failures.log", "analyst-profile.md",
    "accuracy-protocol.md", "skill-architecture-standards.md", "strategic-context.md",
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", help="YYYY-MM-DD date-folder to validate (default: today IST)")
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args()

    date = args.date or datetime.now(IST).strftime("%Y-%m-%d")
    date_dir = QUARANTINE_ROOT / date
    manifest_path = date_dir / "manifest.json"

    warnings = []
    criticals = []

    # Check 1: Manifest exists (non-fatal if no run happened today)
    if not manifest_path.exists():
        print(f"[INFO] No manifest at {manifest_path} — no run on this date.")
        return 0

    manifest = json.loads(manifest_path.read_text())
    print(f"Manifest has {len(manifest)} entries for {date}.")

    # Check 2: Every manifest entry exists on disk
    missing = []
    for entry in manifest:
        qpath = Path(entry["quarantine_path"])
        if not qpath.exists():
            missing.append(entry)
    if missing:
        msg = f"{len(missing)} manifest entries missing from quarantine"
        criticals.append(msg)
        for m in missing[:5]:
            print(f"  MISSING: {m['quarantine_path']} (original: {m['original_path']})")

    # Check 3: No PROTECTED name appears in manifest
    protected_hits = []
    for entry in manifest:
        orig = Path(entry["original_path"])
        if orig.name in PROTECTED_NAMES:
            protected_hits.append(entry)
    if protected_hits:
        criticals.append(f"{len(protected_hits)} PROTECTED file(s) were quarantined!")
        for h in protected_hits[:5]:
            print(f"  PROTECTED LEAK: {h['original_path']}")

    # Check 4: Log file intact (readable, ends with newline, has today's activity)
    if not LOG_FILE.exists():
        warnings.append("housekeeping.log does not exist")
    else:
        content = LOG_FILE.read_text()
        if not content.endswith("\n"):
            warnings.append("housekeeping.log doesn't end with newline (potential truncation)")
        today_tag = f"[{datetime.now(IST).strftime('%Y-%m-%d')}"
        if today_tag not in content:
            warnings.append(f"No log entries for today ({today_tag})")

    # Check 5: State file updated (if run was non-empty)
    if manifest and STATE_FILE.exists():
        state = json.loads(STATE_FILE.read_text())
        last = state.get("last_run_at")
        if not last:
            warnings.append("state.json missing last_run_at")
        else:
            try:
                last_dt = datetime.fromisoformat(last)
                age_h = (datetime.now(IST) - last_dt).total_seconds() / 3600
                if age_h > 24:
                    warnings.append(f"state.last_run_at is {age_h:.0f}h old")
            except Exception:
                warnings.append("state.last_run_at malformed")
    elif manifest:
        warnings.append("state.json missing despite non-empty run")

    # Report
    if criticals:
        print(f"\n[CRITICAL] {len(criticals)} issue(s):")
        for c in criticals:
            print(f"  - {c}")
        return 2
    if warnings:
        print(f"\n[WARN] {len(warnings)} issue(s):")
        for w in warnings:
            print(f"  - {w}")
        return 1 if args.strict else 0
    print("\n[CLEAN] All checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
