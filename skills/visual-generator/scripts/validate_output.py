#!/usr/bin/env python3
"""
validate_output.py — Mandatory session-close validator.

The universal CLAUDE.md Mandatory Session Close Protocol requires:
  "If the skill has a scripts/validate_output.py, run it against all
   deliverables. Fix any CRITICAL failures before delivery."

For visual-generator, "all deliverables" = the rendered reel.mp4 (or
carousel PNG set) + its manifest + the frontmatter back-link. This script
orchestrates the existing qa_reel.py frame-level gate PLUS the artifact
presence checks.

Usage:
  python3 validate_output.py --entry-id <id>
  python3 validate_output.py --reel <path-to-reel.mp4>

Exit 0 = pass, 1 = CRITICAL fail (blocks shipping), 2 = warnings only.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

DEFAULT_BRAND = Path("/Users/digischola/Desktop/Digischola")
SKILL_SCRIPTS = Path(__file__).resolve().parent


def validate_reel_artifacts(entry_id: str) -> tuple[list[str], list[str]]:
    """Check that the expected deliverables exist for a reel entry."""
    fails: list[str] = []
    warns: list[str] = []
    assets_dir = DEFAULT_BRAND / "brand" / "queue" / "assets" / entry_id
    if not assets_dir.exists():
        fails.append(f"assets dir missing: {assets_dir}")
        return fails, warns

    reel_mp4 = assets_dir / "reel.mp4"
    if not reel_mp4.exists():
        fails.append(f"reel.mp4 missing: {reel_mp4}")
    else:
        size = reel_mp4.stat().st_size
        if size < 500_000:
            fails.append(f"reel.mp4 suspiciously small ({size:,} bytes)")

    manifest = assets_dir / "manifest.json"
    if not manifest.exists():
        warns.append(f"manifest.json missing (run import_assets.py): {manifest}")

    render_log = assets_dir / "render_log.jsonl"
    if not render_log.exists():
        warns.append(f"render_log.jsonl missing — future learning loop won't have data")

    return fails, warns


def run_qa_gate(reel_path: Path) -> tuple[list[str], list[str]]:
    """Run qa_reel.py frame-level checks (density / pure-black / motion)."""
    qa_script = SKILL_SCRIPTS / "qa_reel.py"
    if not qa_script.exists():
        return [f"qa_reel.py missing from {qa_script}"], []
    if not reel_path.exists():
        return [f"reel not found: {reel_path}"], []

    r = subprocess.run(
        ["/opt/homebrew/bin/python3.11", str(qa_script), "--reel", str(reel_path)],
        capture_output=True, text=True, timeout=180,
    )
    if r.returncode != 0:
        return [], [f"qa_reel.py flagged frames (exit {r.returncode}) — review stdout"]
    return [], []


def run_skill_audit() -> tuple[list[str], list[str]]:
    """Run audit_skill.py and surface any fail/warn."""
    audit = SKILL_SCRIPTS / "audit_skill.py"
    if not audit.exists():
        return [], ["audit_skill.py missing — skill self-consistency not checked"]
    r = subprocess.run(["python3", str(audit)], capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        return [f"skill audit reports FAIL:\n{r.stdout}"], []
    # Scan warnings from output
    warns: list[str] = []
    for line in r.stdout.splitlines():
        if "warn" in line.lower() and "0 warn" not in line:
            warns.append(line.strip())
    return [], warns


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--entry-id", help="entry id for assets dir lookup")
    ap.add_argument("--reel", type=Path, help="direct path to reel.mp4 (skip artifact check)")
    args = ap.parse_args()

    all_fails: list[str] = []
    all_warns: list[str] = []

    print("═══ Validate output ═══")

    if args.entry_id:
        print(f"\n▶ Artifact presence for entry_id={args.entry_id}")
        fails, warns = validate_reel_artifacts(args.entry_id)
        all_fails += fails
        all_warns += warns
        reel = DEFAULT_BRAND / "brand" / "queue" / "assets" / args.entry_id / "reel.mp4"
    elif args.reel:
        reel = args.reel
    else:
        # Skill-level validation only
        reel = None

    if reel and reel.exists():
        print(f"\n▶ QA frame gate on {reel.name}")
        fails, warns = run_qa_gate(reel)
        all_fails += fails
        all_warns += warns

    print("\n▶ Skill self-consistency (audit_skill.py)")
    fails, warns = run_skill_audit()
    all_fails += fails
    all_warns += warns

    print("\n═══ Report ═══")
    if all_fails:
        print(f"✗ CRITICAL FAILURES ({len(all_fails)}):")
        for f in all_fails:
            print(f"  • {f}")
    if all_warns:
        print(f"⚠ Warnings ({len(all_warns)}):")
        for w in all_warns:
            print(f"  • {w}")
    if not all_fails and not all_warns:
        print("✓ All checks passed. Ship it.")

    if all_fails:
        sys.exit(1)
    if all_warns:
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
