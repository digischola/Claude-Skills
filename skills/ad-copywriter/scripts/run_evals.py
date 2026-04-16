#!/usr/bin/env python3
"""Ad Copywriter — Eval Runner

Usage:
  python3 run_evals.py output-check <file1> [file2] ...   — validate deliverables against format specs
  python3 run_evals.py structure-check                     — verify skill folder structure is complete
  python3 run_evals.py list                                — list all eval cases from evals.json
"""

import sys
import os
import json
import subprocess

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVALS_PATH = os.path.join(SKILL_DIR, 'evals', 'evals.json')
VALIDATOR_PATH = os.path.join(SKILL_DIR, 'scripts', 'validate_output.py')


def load_evals():
    if not os.path.exists(EVALS_PATH):
        print(f"  Error: evals.json not found at {EVALS_PATH}")
        return None
    with open(EVALS_PATH, 'r') as f:
        return json.load(f)


def cmd_list():
    """List all eval cases."""
    data = load_evals()
    if not data:
        return

    print(f"Ad Copywriter — {len(data['evals'])} Eval Cases\n")
    for ev in data['evals']:
        print(f"  ID {ev['id']}: {ev['prompt'][:80]}...")
        print(f"       Assertions: {len(ev['assertions'])}")
        for a in ev['assertions']:
            print(f"         - {a['name']}: {a['description'][:70]}")
        print()


def cmd_structure_check():
    """Verify skill folder has all required files."""
    print("Ad Copywriter — Structure Check\n")

    required_files = [
        ('SKILL.md', 'Skill definition'),
        ('evals/evals.json', 'Eval test cases'),
        ('scripts/validate_output.py', 'Output validator'),
        ('scripts/run_evals.py', 'Eval runner'),
        ('references/copywriting-frameworks.md', 'Framework definitions'),
        ('references/image-prompt-patterns.md', 'Image prompt patterns'),
        ('references/video-storyboard-spec.md', 'Video storyboard spec'),
        ('references/output-format-spec.md', 'Output format spec'),
        ('references/feedback-loop.md', 'Feedback loop protocol'),
        ('assets/README.md', 'Assets documentation'),
    ]

    all_pass = True
    for rel_path, desc in required_files:
        full_path = os.path.join(SKILL_DIR, rel_path)
        exists = os.path.exists(full_path)
        status = "PASS" if exists else "FAIL"
        icon = "OK" if exists else "MISSING"
        print(f"  [{icon:7s}] {rel_path:45s} — {desc}")
        if not exists:
            all_pass = False

    # Check SKILL.md line count
    skill_path = os.path.join(SKILL_DIR, 'SKILL.md')
    if os.path.exists(skill_path):
        with open(skill_path, 'r') as f:
            lines = len(f.readlines())
        if lines > 200:
            print(f"\n  [WARNING] SKILL.md is {lines} lines (max 200)")
            all_pass = False
        else:
            print(f"\n  SKILL.md: {lines} lines (under 200 limit)")

    # Check evals count
    data = load_evals()
    if data:
        print(f"  Evals: {len(data['evals'])} test cases")

    # Check cross-references to paid-media-strategy
    pms_refs = os.path.join(os.path.dirname(SKILL_DIR), 'paid-media-strategy', 'references')
    cross_refs = ['google-ads-system.md', 'meta-ads-system.md']
    print(f"\n  Cross-skill references (paid-media-strategy):")
    for ref in cross_refs:
        ref_path = os.path.join(pms_refs, ref)
        exists = os.path.exists(ref_path)
        icon = "OK" if exists else "MISSING"
        print(f"  [{icon:7s}] paid-media-strategy/references/{ref}")

    print(f"\n  {'PASS — all files present' if all_pass else 'FAIL — missing files detected'}")


def cmd_output_check(files):
    """Run validate_output.py against provided deliverable files."""
    if not os.path.exists(VALIDATOR_PATH):
        print(f"  Error: validate_output.py not found at {VALIDATOR_PATH}")
        sys.exit(1)

    print("Ad Copywriter — Output Validation\n")

    # Filter to existing files
    valid_files = []
    for f in files:
        if os.path.exists(f):
            valid_files.append(f)
        else:
            print(f"  Warning: File not found: {f}")

    if not valid_files:
        print("  No valid files to validate.")
        sys.exit(1)

    # Run validator
    cmd = [sys.executable, VALIDATOR_PATH] + valid_files
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(result.stderr)

    # Check for CRITICAL in output
    if 'CRITICAL' in result.stdout:
        print("\n  RESULT: FAIL — critical issues found. Fix before delivery.")
        sys.exit(1)
    else:
        print("\n  RESULT: PASS — no critical issues.")
        sys.exit(0)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1]

    if command == 'list':
        cmd_list()
    elif command == 'structure-check':
        cmd_structure_check()
    elif command == 'output-check':
        if len(sys.argv) < 3:
            print("  Usage: run_evals.py output-check <file1> [file2] ...")
            sys.exit(1)
        cmd_output_check(sys.argv[2:])
    else:
        print(f"  Unknown command: {command}")
        print(__doc__)
        sys.exit(1)


if __name__ == '__main__':
    main()
