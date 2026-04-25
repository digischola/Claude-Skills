#!/usr/bin/env python3
"""
daily_skill_audit.py — runs lint_skills.py daily, appends results to a JSONL log.

Closes Gap 5 (skill-quality telemetry): per-skill compliance state captured over time so
regressions are detectable without waiting for content-performance signal.

Output: ~/.claude-skill-audit.jsonl — one line per run, with summary + per-skill counts.

Usage:
  daily_skill_audit.py            Run audit, append to log, print summary.
  daily_skill_audit.py --status   Show log location and recent stats.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
from pathlib import Path

HOME = Path.home()
REPO_ROOT = Path(__file__).resolve().parent.parent
LINTER = REPO_ROOT / "scripts" / "lint_skills.py"
AUDIT_LOG = HOME / ".claude-skill-audit.jsonl"


def run_audit() -> dict:
    timestamp = dt.datetime.now().isoformat(timespec="seconds")

    tmp_json = HOME / ".claude-skill-audit-tmp.json"
    try:
        result = subprocess.run(
            ["/usr/bin/python3", str(LINTER), "--quiet", "--json", str(tmp_json)],
            capture_output=True, text=True, timeout=60,
        )
        if not tmp_json.is_file():
            return {
                "timestamp": timestamp,
                "ok": False,
                "error": "linter did not produce JSON output",
                "stderr": result.stderr[-500:],
            }
        data = json.loads(tmp_json.read_text())
    finally:
        tmp_json.unlink(missing_ok=True)

    summary = {
        "timestamp": timestamp,
        "ok": True,
        "skills_audited": data.get("skills_audited", 0),
        "skills_clean": 0,
        "total_critical": 0,
        "total_warning": 0,
        "total_info": 0,
        "per_skill": [],
    }

    for r in data.get("reports", []):
        crit = sum(1 for f in r["findings"] if f["severity"] == "CRITICAL")
        warn = sum(1 for f in r["findings"] if f["severity"] == "WARNING")
        info = sum(1 for f in r["findings"] if f["severity"] == "INFO")
        clean = (crit + warn + info) == 0
        if clean:
            summary["skills_clean"] += 1
        summary["total_critical"] += crit
        summary["total_warning"] += warn
        summary["total_info"] += info
        summary["per_skill"].append({
            "name": r["name"],
            "critical": crit,
            "warning": warn,
            "info": info,
            "rules": [f["rule"] for f in r["findings"]],
        })

    return summary


def append_log(summary: dict) -> None:
    with AUDIT_LOG.open("a") as f:
        f.write(json.dumps(summary) + "\n")


def show_status() -> None:
    print(f"Audit log: {AUDIT_LOG}")
    if not AUDIT_LOG.is_file():
        print("(empty — no audits run yet)")
        return
    rows = [json.loads(l) for l in AUDIT_LOG.read_text().splitlines() if l.strip()]
    print(f"Total runs: {len(rows)}")
    if rows:
        latest = rows[-1]
        print(f"Latest:    {latest.get('timestamp')}")
        print(f"  audited: {latest.get('skills_audited')}")
        print(f"  clean:   {latest.get('skills_clean')}")
        print(f"  CRITICAL/WARNING/INFO: "
              f"{latest.get('total_critical')}/{latest.get('total_warning')}/{latest.get('total_info')}")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--status", action="store_true")
    args = p.parse_args()

    if args.status:
        show_status()
        return 0

    summary = run_audit()
    append_log(summary)

    if not summary.get("ok"):
        print(f"Audit FAILED: {summary.get('error')}")
        return 1

    print(
        f"[{summary['timestamp']}] "
        f"{summary['skills_clean']}/{summary['skills_audited']} clean — "
        f"CRITICAL: {summary['total_critical']}, "
        f"WARNING: {summary['total_warning']}, "
        f"INFO: {summary['total_info']}"
    )
    return 1 if summary["total_critical"] else 0


if __name__ == "__main__":
    sys.exit(main())
