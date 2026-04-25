#!/usr/bin/env python3
"""
lint_skills.py — validate every skill against the 7 architecture standards.

Reads ~/Claude-Skills/skills/* (excluding helper folders) and checks each skill against
the rules defined in shared-context/skill-architecture-standards.md.

Severity tiers:
  CRITICAL — exit 1, blocks any session-start or pre-commit gate
  WARNING  — print but exit 0; should be fixed but not blocking
  INFO     — informational; pattern hints

Usage:
  lint_skills.py                Run linter, print human report, exit 0/1
  lint_skills.py --quiet        Suppress per-skill detail; show summary only
  lint_skills.py --json PATH    Also write structured JSON output
  lint_skills.py --skill NAME   Lint a single skill by name

The 7 standards (see skill-architecture-standards.md for full text):
  L1 Core structure     — SKILL.md exists
  L2 Progressive        — SKILL.md <= 200 lines; references >300 lines should have TOC
  L3 YAML frontmatter   — name + description; description mentions triggers + anti-triggers
  L4 Personalization    — references analyst-profile.md or shared-context
  L5 Evaluation         — evals/evals.json exists with >= 2 well-formed cases
  L6 Self-improvement   — Learnings & Rules section in SKILL.md
  L7 Coordination       — outputs structured for downstream skills (not auto-checkable; skipped)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "skills"

# Folders inside skills/ that are NOT skills (helper code, shared utilities, etc.)
NON_SKILL_FOLDERS = {"shared-scripts"}

CRITICAL = "CRITICAL"
WARNING = "WARNING"
INFO = "INFO"


@dataclass
class Finding:
    severity: str
    rule: str
    message: str


@dataclass
class SkillReport:
    name: str
    path: str
    findings: list[Finding] = field(default_factory=list)

    def add(self, severity: str, rule: str, message: str) -> None:
        self.findings.append(Finding(severity, rule, message))

    @property
    def critical_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == CRITICAL)

    @property
    def warning_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == WARNING)

    @property
    def info_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == INFO)

    @property
    def is_clean(self) -> bool:
        return not self.findings


def parse_yaml_frontmatter(text: str) -> tuple[dict, int] | tuple[None, int]:
    """Parse the leading --- ... --- YAML block. Returns (parsed_dict, body_start_line)."""
    if not text.startswith("---"):
        return None, 0

    lines = text.splitlines()
    end_idx = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_idx = i
            break
    if end_idx is None:
        return None, 0

    yaml_body = "\n".join(lines[1:end_idx])
    parsed: dict = {}
    current_key = None
    current_value: list[str] = []

    for raw in yaml_body.splitlines():
        if not raw.strip():
            continue
        m = re.match(r"^([a-zA-Z_][\w-]*)\s*:\s*(.*)$", raw)
        if m and not raw.startswith(" "):
            if current_key is not None:
                parsed[current_key] = "\n".join(current_value).strip().strip('"').strip("'")
            current_key = m.group(1)
            current_value = [m.group(2)]
        else:
            if current_key is not None:
                current_value.append(raw)
    if current_key is not None:
        parsed[current_key] = "\n".join(current_value).strip().strip('"').strip("'")

    return parsed, end_idx + 1


def lint_skill(skill_dir: Path) -> SkillReport:
    name = skill_dir.name
    report = SkillReport(name=name, path=str(skill_dir))

    skill_md = skill_dir / "SKILL.md"

    # L1: SKILL.md must exist
    if not skill_md.is_file():
        report.add(CRITICAL, "L1.skill-md-exists", f"SKILL.md not found in {skill_dir}")
        return report

    text = skill_md.read_text()
    line_count = len(text.splitlines())

    # L2: SKILL.md size
    if line_count > 200:
        report.add(
            WARNING,
            "L2.skill-md-line-limit",
            f"SKILL.md is {line_count} lines (limit 200). Move detail to references/.",
        )

    # L3: YAML frontmatter
    yaml, body_start = parse_yaml_frontmatter(text)
    if yaml is None:
        report.add(CRITICAL, "L3.yaml-present", "SKILL.md has no YAML frontmatter (--- ... ---).")
        body = text
    else:
        body = "\n".join(text.splitlines()[body_start:])

        if "name" not in yaml or not yaml.get("name", "").strip():
            report.add(CRITICAL, "L3.yaml-name", "YAML frontmatter missing `name` field.")
        elif yaml["name"].strip() != name:
            report.add(
                WARNING,
                "L3.yaml-name-matches",
                f"YAML name `{yaml['name'].strip()}` does not match folder name `{name}`.",
            )

        desc = yaml.get("description", "").strip()
        if not desc:
            report.add(CRITICAL, "L3.yaml-description", "YAML frontmatter missing `description` field.")
        else:
            if len(desc) < 200:
                report.add(
                    WARNING,
                    "L3.description-substantive",
                    f"description is only {len(desc)} chars; aim for >=200 with triggers and anti-triggers.",
                )
            if not re.search(r"\b(use when|trigger when|when user)\b", desc, re.IGNORECASE):
                report.add(
                    WARNING,
                    "L3.description-triggers",
                    "description should include trigger phrases (e.g. 'Use when:' / 'Trigger when:').",
                )
            if not re.search(r"\b(do not (trigger|use)|don't (trigger|use)|skip:|anti-trigger)\b", desc, re.IGNORECASE):
                report.add(
                    WARNING,
                    "L3.description-anti-triggers",
                    "description should include anti-triggers (e.g. 'Do NOT trigger for ...').",
                )

    # L4: Business personalization — must reference analyst-profile or shared-context
    if not re.search(r"analyst-profile\.md|shared-context", text):
        report.add(
            WARNING,
            "L4.personalization",
            "SKILL.md does not reference analyst-profile.md or shared-context — risk of generic output.",
        )

    # L5: Evaluation
    evals_dir = skill_dir / "evals"
    evals_json = evals_dir / "evals.json"
    if not evals_json.is_file():
        report.add(WARNING, "L5.evals-exist", "evals/evals.json not found.")
    else:
        try:
            data = json.loads(evals_json.read_text())
            cases = data.get("evals", []) if isinstance(data, dict) else []
            if len(cases) < 2:
                report.add(
                    WARNING,
                    "L5.evals-min-cases",
                    f"evals/evals.json has {len(cases)} cases (minimum 2).",
                )
            for i, case in enumerate(cases):
                if "prompt" not in case:
                    report.add(WARNING, "L5.evals-shape", f"eval #{i} missing `prompt` field.")
                if "assertions" not in case or not case.get("assertions"):
                    report.add(WARNING, "L5.evals-shape", f"eval #{i} missing `assertions`.")
        except json.JSONDecodeError as e:
            report.add(CRITICAL, "L5.evals-valid-json", f"evals/evals.json is not valid JSON: {e}")

    # L6: Learnings & Rules section
    if not re.search(r"^##\s+Learnings\s*&\s*Rules", text, re.MULTILINE | re.IGNORECASE):
        report.add(
            WARNING,
            "L6.learnings-section",
            "Missing `## Learnings & Rules` section in SKILL.md (required for feedback loop).",
        )

    # L2 (continued): reference files >300 lines should have TOC
    references_dir = skill_dir / "references"
    if references_dir.is_dir():
        for ref in sorted(references_dir.rglob("*.md")):
            ref_text = ref.read_text()
            ref_lines = len(ref_text.splitlines())
            if ref_lines > 300:
                head = "\n".join(ref_text.splitlines()[:30]).lower()
                has_toc = "table of contents" in head or "## contents" in head or "- [" in head
                if not has_toc:
                    report.add(
                        INFO,
                        "L2.reference-toc",
                        f"references/{ref.relative_to(references_dir)} is {ref_lines} lines — add a TOC at top.",
                    )

    return report


def discover_skills() -> list[Path]:
    if not SKILLS_DIR.is_dir():
        print(f"ERROR: {SKILLS_DIR} not found", file=sys.stderr)
        sys.exit(2)
    return sorted(
        d for d in SKILLS_DIR.iterdir()
        if d.is_dir() and not d.name.startswith(".") and d.name not in NON_SKILL_FOLDERS
    )


def render_human(reports: list[SkillReport], quiet: bool) -> None:
    total_critical = sum(r.critical_count for r in reports)
    total_warning = sum(r.warning_count for r in reports)
    total_info = sum(r.info_count for r in reports)
    clean = [r for r in reports if r.is_clean]

    if not quiet:
        for r in reports:
            if r.is_clean:
                print(f"✓ {r.name}")
                continue
            print(f"✗ {r.name}")
            for f in r.findings:
                marker = {"CRITICAL": "  ✗", "WARNING": "  ⚠", "INFO": "  ·"}[f.severity]
                print(f"{marker} [{f.severity}] {f.rule}: {f.message}")

    print()
    print("=" * 60)
    print(f"Skills audited: {len(reports)}    Clean: {len(clean)}")
    print(f"CRITICAL: {total_critical}    WARNING: {total_warning}    INFO: {total_info}")
    print("=" * 60)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--quiet", action="store_true", help="summary only")
    p.add_argument("--json", metavar="PATH", help="also write JSON report to PATH")
    p.add_argument("--skill", metavar="NAME", help="lint a single skill by name")
    args = p.parse_args()

    skills = discover_skills()
    if args.skill:
        skills = [s for s in skills if s.name == args.skill]
        if not skills:
            print(f"ERROR: skill `{args.skill}` not found", file=sys.stderr)
            return 2

    reports = [lint_skill(s) for s in skills]

    render_human(reports, args.quiet)

    if args.json:
        out = {
            "skills_audited": len(reports),
            "reports": [
                {
                    "name": r.name,
                    "path": r.path,
                    "findings": [asdict(f) for f in r.findings],
                }
                for r in reports
            ],
        }
        Path(args.json).write_text(json.dumps(out, indent=2))

    total_critical = sum(r.critical_count for r in reports)
    return 1 if total_critical else 0


if __name__ == "__main__":
    sys.exit(main())
