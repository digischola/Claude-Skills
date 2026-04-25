#!/usr/bin/env python3
"""
weekly_skill_report.py — aggregates the daily skill-audit JSONL into a weekly markdown report.

Reads ~/.claude-skill-audit.jsonl (produced by daily_skill_audit.py), filters last 7 days,
emits scripts/logs/skill-audit-WYY.md showing:
  - Trend: clean count over the week
  - Top violation rules
  - Skills that improved vs regressed vs stayed-flagged
  - Per-skill compliance status

Usage:
  weekly_skill_report.py            Produce this week's report.
  weekly_skill_report.py --print    Print the report to stdout instead of writing to file.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

HOME = Path.home()
REPO_ROOT = Path(__file__).resolve().parent.parent
AUDIT_LOG = HOME / ".claude-skill-audit.jsonl"
REPORT_DIR = REPO_ROOT / "scripts" / "logs"


def load_runs() -> list[dict]:
    if not AUDIT_LOG.is_file():
        return []
    rows: list[dict] = []
    for line in AUDIT_LOG.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
            if d.get("ok"):
                rows.append(d)
        except json.JSONDecodeError:
            pass
    return rows


def build_report() -> str:
    today = dt.date.today()
    cutoff = today - dt.timedelta(days=7)
    iso_year, iso_week, _ = today.isocalendar()

    runs = load_runs()
    week_runs = [
        r for r in runs
        if dt.datetime.fromisoformat(r["timestamp"]).date() >= cutoff
    ]

    lines: list[str] = []
    lines.append(f"# Skill Audit Report — Week {iso_year}-W{iso_week:02d}")
    lines.append("")
    lines.append(f"Coverage: {cutoff.isoformat()} → {today.isoformat()}")
    lines.append(f"Audit runs in window: {len(week_runs)}")
    lines.append("")

    if not week_runs:
        lines.append("_No audits in this window. Daily audit may not be running yet._")
        return "\n".join(lines)

    first = week_runs[0]
    last = week_runs[-1]

    lines.append("## Compliance Trend")
    lines.append(f"- Start of week: {first['skills_clean']}/{first['skills_audited']} clean — "
                 f"{first['total_critical']} CRIT, {first['total_warning']} WARN, "
                 f"{first['total_info']} INFO")
    lines.append(f"- End of week:   {last['skills_clean']}/{last['skills_audited']} clean — "
                 f"{last['total_critical']} CRIT, {last['total_warning']} WARN, "
                 f"{last['total_info']} INFO")
    delta_clean = last["skills_clean"] - first["skills_clean"]
    arrow = "↑" if delta_clean > 0 else ("↓" if delta_clean < 0 else "→")
    lines.append(f"- Net: {arrow} {delta_clean:+d} skills clean")
    lines.append("")

    rule_counts: Counter[str] = Counter()
    for skill in last.get("per_skill", []):
        for rule in skill.get("rules", []):
            rule_counts[rule] += 1

    if rule_counts:
        lines.append("## Top Violation Rules (latest run)")
        for rule, count in rule_counts.most_common(10):
            lines.append(f"- `{rule}` × {count}")
        lines.append("")

    first_per: dict[str, dict] = {s["name"]: s for s in first.get("per_skill", [])}
    last_per: dict[str, dict] = {s["name"]: s for s in last.get("per_skill", [])}

    improved: list[str] = []
    regressed: list[str] = []
    flagged: list[str] = []

    for name, s in last_per.items():
        last_total = s["critical"] + s["warning"] + s["info"]
        f0 = first_per.get(name, {"critical": 0, "warning": 0, "info": 0})
        first_total = f0["critical"] + f0["warning"] + f0["info"]
        if last_total < first_total:
            improved.append(f"{name} ({first_total} → {last_total})")
        elif last_total > first_total:
            regressed.append(f"{name} ({first_total} → {last_total})")
        elif last_total > 0:
            flagged.append(f"{name} ({last_total} findings, unchanged)")

    if improved:
        lines.append(f"## Improved ({len(improved)})")
        for s in improved:
            lines.append(f"- ✓ {s}")
        lines.append("")
    if regressed:
        lines.append(f"## Regressed ({len(regressed)})")
        for s in regressed:
            lines.append(f"- ✗ {s}")
        lines.append("")
    if flagged:
        lines.append(f"## Persistently Flagged ({len(flagged)})")
        for s in flagged:
            lines.append(f"- ⚠ {s}")
        lines.append("")

    clean_skills = [s["name"] for s in last.get("per_skill", [])
                    if s["critical"] + s["warning"] + s["info"] == 0]
    if clean_skills:
        lines.append(f"## Clean Skills ({len(clean_skills)})")
        for s in clean_skills:
            lines.append(f"- ✓ {s}")

    return "\n".join(lines)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--print", dest="print_only", action="store_true")
    args = p.parse_args()

    report = build_report()

    if args.print_only:
        print(report)
        return 0

    today = dt.date.today()
    iso_year, iso_week, _ = today.isocalendar()
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    path = REPORT_DIR / f"skill-audit-{iso_year}-W{iso_week:02d}.md"
    path.write_text(report)
    print(f"Report written: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
