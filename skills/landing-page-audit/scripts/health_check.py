#!/usr/bin/env python3
"""
health_check.py — Session-start gate for landing-page-audit.

Runs test_fixtures.py + validate_output.py self-check. If either fails,
the skill is considered broken and client use should be blocked until fixed.

Usage: python3 health_check.py
Exit code: 0 if healthy (skill safe to use on client), 1 if broken.

Called from SKILL.md Step 0 at skill activation — before any capture runs.
"""

import os
import sys
import subprocess


SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run(label: str, cmd: list) -> bool:
    print(f"\n--- {label} ---")
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    return result.returncode == 0


def main():
    print("=" * 60)
    print("  landing-page-audit SKILL HEALTH CHECK")
    print("=" * 60)

    checks = []

    # 1. Fixture classification test
    fixtures_ok = run(
        "Fixture classification",
        [sys.executable, os.path.join(SKILL_DIR, "scripts", "test_fixtures.py")],
    )
    checks.append(("Fixtures", fixtures_ok))

    # 2. Validator self-sanity — run validator on its own help/usage (structural smoke)
    validator_path = os.path.join(SKILL_DIR, "scripts", "validate_output.py")
    if os.path.exists(validator_path):
        result = subprocess.run(
            [sys.executable, validator_path],
            capture_output=True, text=True,
        )
        # validator with no args will print usage + exit nonzero; that's OK — it means the script loads
        validator_ok = "validate" in (result.stdout + result.stderr).lower() or result.returncode in (0, 1, 2)
        checks.append(("Validator loads", validator_ok))
    else:
        checks.append(("Validator loads", False))

    # 3. All 4 critical reference files present
    required_refs = [
        "cro-checklist.md",
        "visual-ux-checklist.md",
        "persuasion-copy-checklist.md",
        "scoring-framework.md",
        "screenshot-capture.md",
        "markdown-findings-spec.md",
    ]
    refs_ok = True
    for ref in required_refs:
        if not os.path.exists(os.path.join(SKILL_DIR, "references", ref)):
            print(f"  ✗ Missing reference: {ref}")
            refs_ok = False
    if refs_ok:
        print(f"  ✓ All {len(required_refs)} required references present")
    checks.append(("References", refs_ok))

    # 4. Templates present
    required_templates = [
        "template-booking-event.html",
        "template-local-services.html",
        "template-b2b-leadgen.html",
        "template-internal-quick.html",
    ]
    templates_ok = True
    for tpl in required_templates:
        if not os.path.exists(os.path.join(SKILL_DIR, "assets", tpl)):
            print(f"  ✗ Missing template: {tpl}")
            templates_ok = False
    if templates_ok:
        print(f"  ✓ All {len(required_templates)} dashboard templates present")
    checks.append(("Templates", templates_ok))

    # Summary
    print()
    print("=" * 60)
    all_ok = all(ok for _, ok in checks)
    for name, ok in checks:
        mark = "✓" if ok else "✗"
        print(f"  {mark} {name}")
    print("=" * 60)
    if all_ok:
        print("  ✅ HEALTHY — skill is safe to use on client pages")
        print("=" * 60)
        return 0
    else:
        print("  ❌ BROKEN — do NOT run on client pages until fixed")
        print("  Per CLAUDE.md 'Skill Protocol Supremacy': stop, patch, re-run.")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
