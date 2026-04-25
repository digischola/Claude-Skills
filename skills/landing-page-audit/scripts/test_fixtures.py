#!/usr/bin/env python3
"""
test_fixtures.py — Run detect_target_profile.py against every fixture and assert.

Usage: python3 test_fixtures.py
Exit code: 0 if all pass, 1 if any fixture classifies wrong.

Called by health_check.py as the capture-protocol smoke test.
"""

import os
import sys
import json
import subprocess


SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURES_DIR = os.path.join(SKILL_DIR, "evals", "fixtures")
DETECTOR = os.path.join(SKILL_DIR, "scripts", "detect_target_profile.py")
RECIPES_DIR = os.path.join(SKILL_DIR, "references", "capture-recipes")

# Each fixture filename → expected profile
EXPECTATIONS = {
    "react-spa-countup.html": "react-spa-countup",
    "elementor-wordpress.html": "elementor-wordpress",
    "static-html.html": "static-html",
    "wordpress-generic.html": "wordpress-generic",
}


def run_detector(fixture_path: str) -> dict:
    result = subprocess.run(
        [sys.executable, DETECTOR, fixture_path],
        capture_output=True, text=True, timeout=10,
    )
    if result.returncode != 0:
        return {"error": result.stderr}
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"error": f"bad JSON: {result.stdout}"}


def main():
    print("=" * 60)
    print("  FIXTURE TESTS — landing-page-audit")
    print("=" * 60)

    results = []
    for fixture_name, expected_profile in EXPECTATIONS.items():
        fixture_path = os.path.join(FIXTURES_DIR, fixture_name)
        if not os.path.exists(fixture_path):
            print(f"  ✗ MISSING: {fixture_name}")
            results.append((fixture_name, False, "missing fixture"))
            continue

        out = run_detector(fixture_path)
        if "error" in out:
            print(f"  ✗ ERROR: {fixture_name} — {out['error']}")
            results.append((fixture_name, False, out["error"]))
            continue

        actual = out.get("profile")
        ok = actual == expected_profile
        mark = "✓" if ok else "✗"
        print(f"  {mark} {fixture_name}")
        print(f"    expected: {expected_profile}")
        print(f"    actual:   {actual}")
        if not ok:
            print(f"    signals:  {out.get('signals', [])}")
        results.append((fixture_name, ok, actual))

    # Verify each recipe file exists for the expected profiles
    print()
    print("  Recipe playbook presence:")
    recipe_ok = True
    for expected_profile in set(EXPECTATIONS.values()):
        recipe_path = os.path.join(RECIPES_DIR, f"{expected_profile}.md")
        if os.path.exists(recipe_path):
            print(f"  ✓ {expected_profile}.md")
        else:
            print(f"  ✗ {expected_profile}.md — MISSING")
            recipe_ok = False

    # Summary
    passed = sum(1 for _, ok, _ in results if ok)
    total = len(results)
    print()
    print("=" * 60)
    if passed == total and recipe_ok:
        print(f"  ✅ ALL PASS — {passed}/{total} fixtures + all recipes present")
        print("=" * 60)
        return 0
    else:
        print(f"  ❌ FAIL — {passed}/{total} fixtures correct, recipes OK: {recipe_ok}")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
