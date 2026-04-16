#!/usr/bin/env python3
"""
Master Validation Runner for Business Analysis Skill

Runs all three validators in sequence:
1. run_evals.py    — unit tests for extract_brand.py filtering logic
2. validate_output.py — structural checks on client deliverables
3. lint_wiki.py    — content quality checks on wiki pages

Usage:
    python validate_all.py <client_folder_path>

    # Skip client checks (just run evals)
    python validate_all.py --evals-only

Exit codes:
    0 = all passed
    1 = failures found
"""

import sys
import os
import subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def run_script(name, args=None):
    """Run a Python script and return (success, output)."""
    cmd = [sys.executable, os.path.join(SCRIPT_DIR, name)]
    if args:
        cmd.extend(args)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        output = result.stdout + result.stderr
        return result.returncode == 0, output.strip()
    except subprocess.TimeoutExpired:
        return False, f"{name} timed out after 60 seconds"
    except Exception as e:
        return False, f"{name} failed to run: {e}"


def main():
    evals_only = "--evals-only" in sys.argv
    client_dir = None

    for arg in sys.argv[1:]:
        if not arg.startswith("--"):
            client_dir = arg
            break

    if not evals_only and not client_dir:
        print("Usage: python validate_all.py <client_folder_path>")
        print("       python validate_all.py --evals-only")
        sys.exit(1)

    print("=" * 60)
    print("  MASTER VALIDATION")
    print("=" * 60)

    all_passed = True
    results = []

    # ── 1. Unit tests (always run) ──
    print("\n[1/3] Running unit tests (run_evals.py)...")
    success, output = run_script("run_evals.py")
    results.append(("Unit Tests", success))
    print(output)
    if not success:
        all_passed = False

    if evals_only:
        print("\n" + "=" * 60)
        if all_passed:
            print("  RESULT: Unit tests passed.")
        else:
            print("  RESULT: Unit test failures found.")
        print("=" * 60)
        sys.exit(0 if all_passed else 1)

    # ── 2. Output validation ──
    print(f"\n[2/3] Running output validation (validate_output.py)...")
    success, output = run_script("validate_output.py", [client_dir])
    results.append(("Output Validation", success))
    print(output)
    if not success:
        all_passed = False

    # ── 3. Wiki content lint ──
    print(f"\n[3/3] Running wiki content lint (lint_wiki.py)...")
    success, output = run_script("lint_wiki.py", [client_dir])
    results.append(("Wiki Lint", success))
    print(output)
    if not success:
        all_passed = False

    # ── Summary ──
    print("\n" + "=" * 60)
    print("  SUMMARY")
    print("=" * 60)
    for name, passed in results:
        icon = "✓" if passed else "✗"
        status = "PASSED" if passed else "FAILED"
        print(f"  {icon} {name}: {status}")

    print("=" * 60)
    if all_passed:
        print("  ALL CHECKS PASSED — ready for delivery.")
    else:
        print("  FAILURES FOUND — fix before delivery.")
    print("=" * 60)

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
