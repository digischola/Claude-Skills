#!/usr/bin/env python3
"""
audit_skill.py — Dry-run housekeeping checker for visual-generator.

DOES NOT DELETE ANYTHING. Reports only. Human confirms + executes the cleanup.

Checks:
  1. SKILL.md line count (should be <200 per 7+3 standards)
  2. SKILL.md references the real reference files (no broken or stale links)
  3. Every file in references/ is referenced by SKILL.md or by another reference
  4. Every script in scripts/ is referenced by SKILL.md or called by another script
  5. Learnings & Rules log contains entries for the latest architecture (v7.3)
  6. No legacy stack mentions in SKILL.md that don't match the current pipeline
     (Hyperframes, Veo, Kling, Meta AI, Midjourney, SadTalker, MuseTalk)
  7. evals/evals.json exists and parses as JSON

Usage:
  python3 audit_skill.py                   # audit visual-generator
  python3 audit_skill.py --verbose         # show file-by-file detail
  python3 audit_skill.py --skill <name>    # audit a different skill

Exit codes:
  0 — clean (or only warnings)
  1 — at least one FAIL (missing file, broken reference, SKILL.md over budget)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

CURRENT_STACK_KEYWORDS = {"remotion", "hyperframes", "chatterbox", "ffmpeg"}
# v7.4: hyperframes MOVED to current stack (dual-engine). Remaining deprecated list:
DEPRECATED_STACK_KEYWORDS = {
    "veo", "kling", "meta ai", "midjourney",
    "sadtalker", "musetalk", "wav2lip", "nano banana",
}
CURRENT_VERSION_TAG = "v7.4"
SKILL_MD_MAX_LINES = 200


def audit_skill(skill_dir: Path, verbose: bool = False) -> int:
    fails = []
    warns = []
    oks = []

    skill_md = skill_dir / "SKILL.md"
    references_dir = skill_dir / "references"
    scripts_dir = skill_dir / "scripts"
    evals_dir = skill_dir / "evals"

    # ── Check 1: SKILL.md exists + line count ───────────────────────────────
    if not skill_md.exists():
        fails.append(f"SKILL.md missing at {skill_md}")
        return _print_report(skill_dir, fails, warns, oks, verbose)

    skill_text = skill_md.read_text(encoding="utf-8")
    line_count = len(skill_text.splitlines())
    if line_count > SKILL_MD_MAX_LINES:
        warns.append(
            f"SKILL.md is {line_count} lines — 7+3 standard says <{SKILL_MD_MAX_LINES}. "
            "Move detail to references/."
        )
    else:
        oks.append(f"SKILL.md line count: {line_count} (under {SKILL_MD_MAX_LINES})")

    # ── Check 2: Referenced files exist ─────────────────────────────────────
    ref_pattern = re.compile(r"references/([a-zA-Z0-9\-_]+\.md)")
    script_pattern = re.compile(r"scripts/([a-zA-Z0-9\-_]+\.py)")
    skill_referenced_refs = set(ref_pattern.findall(skill_text))
    skill_referenced_scripts = set(script_pattern.findall(skill_text))

    if references_dir.exists():
        for ref in skill_referenced_refs:
            if not (references_dir / ref).exists():
                fails.append(f"SKILL.md references references/{ref} but file is missing")
    if scripts_dir.exists():
        for s in skill_referenced_scripts:
            if not (scripts_dir / s).exists():
                fails.append(f"SKILL.md references scripts/{s} but file is missing")

    # ── Check 3: Unreferenced reference files ───────────────────────────────
    if references_dir.exists():
        all_refs = [p.name for p in references_dir.glob("*.md")]
        unref_refs = set(all_refs) - skill_referenced_refs
        if unref_refs:
            warns.append(
                "References not linked from SKILL.md (consider documenting or archiving):\n    - "
                + "\n    - ".join(sorted(unref_refs))
            )
        else:
            oks.append(f"All {len(all_refs)} reference files linked from SKILL.md")

    # ── Check 4: Unreferenced scripts ───────────────────────────────────────
    if scripts_dir.exists():
        all_scripts = [p.name for p in scripts_dir.glob("*.py") if not p.name.startswith("_")]
        # Script may be called by another script, not just SKILL.md — check callers
        scripts_text = "\n".join(p.read_text(encoding="utf-8", errors="ignore")
                                  for p in scripts_dir.glob("*.py"))
        unref_scripts = []
        for s in all_scripts:
            if s in skill_referenced_scripts:
                continue
            # Check if another script imports or invokes it
            stem = s.removesuffix(".py")
            if stem in scripts_text or s in scripts_text:
                continue
            unref_scripts.append(s)
        if unref_scripts:
            warns.append(
                "Scripts not referenced anywhere (consider archiving):\n    - "
                + "\n    - ".join(sorted(unref_scripts))
            )
        else:
            oks.append(f"All {len(all_scripts)} scripts referenced (SKILL.md or peer script)")

    # ── Check 5: Learnings contain current version ──────────────────────────
    if CURRENT_VERSION_TAG.lower() in skill_text.lower():
        oks.append(f"Learnings & Rules log mentions {CURRENT_VERSION_TAG}")
    else:
        warns.append(
            f"Learnings & Rules log does not mention {CURRENT_VERSION_TAG}. "
            "If the pipeline shipped this architecture, add an entry."
        )

    # ── Check 6: Deprecated stack keywords in SKILL.md (active sections) ────
    # Scan only NON-learnings sections for deprecated names — history is fine to keep.
    learning_split = re.split(r"##\s+Learnings\s*&\s*Rules", skill_text, maxsplit=1,
                               flags=re.IGNORECASE)
    active_section = learning_split[0] if len(learning_split) == 2 else skill_text
    found_deprecated = []
    for kw in DEPRECATED_STACK_KEYWORDS:
        # Word-boundary-ish check; skip if kw appears as part of "deprecated" context
        hits = [m.start() for m in re.finditer(re.escape(kw), active_section, re.IGNORECASE)]
        for h in hits:
            ctx = active_section[max(0, h-80):h+len(kw)+80].lower()
            if ("deprecated" in ctx or "do not use" in ctx or "archive" in ctx
                    or "do not" in ctx or "❌" in ctx or "never use" in ctx
                    or "rejected" in ctx):
                continue
            found_deprecated.append(kw)
            break
    if found_deprecated:
        warns.append(
            "SKILL.md active sections mention deprecated stack: "
            + ", ".join(sorted(set(found_deprecated)))
            + ". Mark as deprecated or remove."
        )
    else:
        oks.append("SKILL.md active sections are clean of deprecated stack names")

    # ── Check 7: evals.json parses ──────────────────────────────────────────
    evals_path = evals_dir / "evals.json"
    if evals_path.exists():
        try:
            evals_data = json.loads(evals_path.read_text(encoding="utf-8"))
            if isinstance(evals_data, list):
                n_cases = len(evals_data)
            elif isinstance(evals_data, dict):
                n_cases = len(evals_data.get("evals", [])) or len(evals_data.get("cases", []))
            else:
                n_cases = 0
            oks.append(f"evals.json parses OK ({n_cases} cases)")
            if n_cases == 0:
                warns.append("evals.json has 0 cases — populate with at least 1 test.")
        except json.JSONDecodeError as e:
            fails.append(f"evals.json fails to parse: {e}")
    else:
        warns.append("evals/evals.json is missing — 7+3 requires eval cases.")

    return _print_report(skill_dir, fails, warns, oks, verbose)


def _print_report(skill_dir: Path, fails, warns, oks, verbose: bool) -> int:
    print(f"\n═══ Skill Audit — {skill_dir.name} ═══\n")

    if oks and verbose:
        print("✓ PASS:")
        for o in oks:
            print(f"  • {o}")
        print()

    if warns:
        print("⚠ WARNINGS (not blocking, review):")
        for w in warns:
            print(f"  • {w}")
        print()

    if fails:
        print("✗ FAIL:")
        for f in fails:
            print(f"  • {f}")
        print()

    summary = f"{len(oks)} pass · {len(warns)} warn · {len(fails)} fail"
    print(f"Summary: {summary}\n")
    return 1 if fails else 0


def main():
    ap = argparse.ArgumentParser(description="Dry-run housekeeping audit for a skill folder.")
    ap.add_argument("--skill", default="visual-generator",
                    help="Skill folder name under Desktop/Claude Skills/skills/")
    ap.add_argument("--skills-root", type=Path,
                    default=Path("/Users/digischola/Desktop/Claude Skills/skills"),
                    help="Root containing skill folders")
    ap.add_argument("--verbose", "-v", action="store_true",
                    help="Also show PASS items")
    args = ap.parse_args()

    skill_dir = args.skills_root / args.skill
    if not skill_dir.exists():
        sys.exit(f"Skill folder not found: {skill_dir}")

    sys.exit(audit_skill(skill_dir, verbose=args.verbose))


if __name__ == "__main__":
    main()
