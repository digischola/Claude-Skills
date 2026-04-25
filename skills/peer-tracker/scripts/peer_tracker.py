#!/usr/bin/env python3
"""
Peer Tracker — keeps post-writer/references/creator-study.md fresh.

Sub-commands:
  list             Show all 15 tracked creators + their last refresh status
  rotation-due     Return creator names due for refresh this Sunday (4-5 names)
  apply-refresh    Apply a findings JSON to one creator (updates creator-study.md + bumps log)
  stats            Per-pillar refresh coverage + silent/pivoted counts
  validate-creator-study  Parse creator-study.md, report any structural issues

Usage:
  python3 peer_tracker.py list
  python3 peer_tracker.py rotation-due --week 2026-W17
  python3 peer_tracker.py apply-refresh --creator "Peep Laja" --findings '{"status":"active",...}'
  python3 peer_tracker.py stats
  python3 peer_tracker.py validate-creator-study
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

DEFAULT_BRAND = Path("/Users/digischola/Desktop/Digischola")
SKILL_DIR = Path("/Users/digischola/Desktop/Claude Skills/skills/peer-tracker")
CREATOR_STUDY_PATH = Path("/Users/digischola/Desktop/Claude Skills/skills/post-writer/references/creator-study.md")
REFRESH_LOG = SKILL_DIR / "data" / "refresh-log.json"
TRACKED_CREATORS_MD = SKILL_DIR / "references" / "tracked-creators.md"

# Default rotation: 4 per week, 5 every 4th week → 17 slots covers 15 creators with 2-week buffer
DEFAULT_BATCH_SIZE = 4


def ist() -> timezone:
    return timezone(timedelta(hours=5, minutes=30), name="IST")


def now_ist_iso() -> str:
    return datetime.now(ist()).isoformat()


# ── Tracked creators (parsed from references/tracked-creators.md) ─────────


def parse_tracked_creators() -> list[dict]:
    """Parse the 15-creator tables from tracked-creators.md."""
    if not TRACKED_CREATORS_MD.exists():
        sys.exit(f"Tracked creators file missing: {TRACKED_CREATORS_MD}")
    text = TRACKED_CREATORS_MD.read_text()
    creators = []
    current_pillar = None
    table_row_re = re.compile(r"^\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*$")
    for line in text.splitlines():
        ml = line.strip()
        if ml.startswith("## Pillar"):
            current_pillar = ml.split("—")[-1].strip() if "—" in ml else ml
            continue
        m = table_row_re.match(line)
        if not m:
            continue
        col1, col2, col3, col4, col5 = (g.strip() for g in m.groups())
        # Skip header + separator rows
        if col1.lower() in ("creator", "---") or col1.startswith("---"):
            continue
        creators.append({
            "name": col1,
            "primary_handle": col2,
            "channels": col3,
            "pillar": col4,
            "niche": col5,
        })
    return creators


# ── Refresh log ──────────────────────────────────────────────────────────


def read_refresh_log() -> dict:
    if not REFRESH_LOG.exists():
        return {"creators": {}, "current_rotation_week": 1}
    return json.loads(REFRESH_LOG.read_text())


def write_refresh_log(log: dict) -> None:
    REFRESH_LOG.parent.mkdir(parents=True, exist_ok=True)
    REFRESH_LOG.write_text(json.dumps(log, indent=2))


def init_refresh_log_for_creator(log: dict, name: str) -> None:
    if name not in log["creators"]:
        log["creators"][name] = {"last_refreshed_at": None, "status": "unknown"}


# ── Rotation logic ───────────────────────────────────────────────────────


def get_rotation_due(batch_size: int = DEFAULT_BATCH_SIZE) -> list[str]:
    """Return creator names due for refresh this Sunday, sorted oldest-first."""
    creators = parse_tracked_creators()
    log = read_refresh_log()
    for c in creators:
        init_refresh_log_for_creator(log, c["name"])

    # Sort by last_refreshed_at (None = oldest)
    def sort_key(name: str):
        r = log["creators"][name].get("last_refreshed_at")
        if r is None:
            return datetime.min.replace(tzinfo=ist())
        try:
            dt = datetime.fromisoformat(r)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=ist())
            return dt
        except ValueError:
            return datetime.min.replace(tzinfo=ist())

    names = sorted([c["name"] for c in creators], key=sort_key)
    return names[:batch_size]


# ── Creator-study.md parsing + updating ──────────────────────────────────


CREATOR_HEADING_RE = re.compile(r"^### (.+)$", re.MULTILINE)


def find_creator_section(text: str, name: str) -> tuple[int, int] | None:
    """Return (start_idx, end_idx) of the creator's section in creator-study.md."""
    matches = list(CREATOR_HEADING_RE.finditer(text))
    for i, m in enumerate(matches):
        if m.group(1).strip() == name:
            start = m.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            return start, end
    return None


def update_creator_section(text: str, name: str, findings: dict) -> tuple[str, str]:
    """Return (updated_text, status_msg). Updates Reach / Signature format / Last refreshed / Recent samples in place."""
    pos = find_creator_section(text, name)
    if pos is None:
        return text, f"NOT FOUND: {name} has no section in creator-study.md"
    start, end = pos
    section = text[start:end]

    # Extract existing fields for backwards compat
    reach_match = re.search(r"^- \*\*Reach:\*\*\s*(.+)$", section, re.MULTILINE)
    signature_match = re.search(r"^- \*\*Signature format:\*\*\s*(.+)$", section, re.MULTILINE)

    # Update Reach if reach_update provided
    if findings.get("reach_update") and reach_match:
        new_reach = findings["reach_update"]
        section = re.sub(r"^- \*\*Reach:\*\*\s*.+$",
                         f"- **Reach:** {new_reach}", section, count=1, flags=re.MULTILINE)

    # Append hook pattern delta to Signature format (don't replace)
    if findings.get("hook_pattern_delta") and signature_match:
        existing = signature_match.group(1).strip()
        delta = findings["hook_pattern_delta"]
        if delta not in existing:
            new_sig = f"{existing}  +  {delta}"
            section = re.sub(r"^- \*\*Signature format:\*\*\s*.+$",
                             f"- **Signature format:** {new_sig}", section, count=1, flags=re.MULTILINE)

    # Strip any previous "Last refreshed" / "Recent samples" subsections
    section = re.sub(r"^- \*\*Last refreshed:\*\*.*?(?=\n###|\n\n##|\Z)",
                     "", section, flags=re.MULTILINE | re.DOTALL)
    section = re.sub(r"^- \*\*Recent samples:\*\*.*?(?=\n###|\n\n##|\Z)",
                     "", section, flags=re.MULTILINE | re.DOTALL)

    # Append new "Last refreshed" + "Recent samples"
    refresh_line = (
        f"- **Last refreshed:** {findings.get('refreshed_at', now_ist_iso())[:10]} "
        f"({findings.get('status', 'active')}, {len(findings.get('recent_posts', []))} posts last 30d)"
    )

    sample_lines = []
    for p in findings.get("recent_posts", [])[:3]:
        date = p.get("date", "?")
        summary = (p.get("summary") or "")[:120]
        url = p.get("url", "")
        sample_lines.append(f"  - {date}: {summary} [{url}]" if url else f"  - {date}: {summary}")
    samples_block = "- **Recent samples:**\n" + "\n".join(sample_lines) if sample_lines else "- **Recent samples:** (none in last 30 days)"

    notes_block = ""
    if findings.get("notes"):
        notes_block = f"- **Note ({findings.get('refreshed_at', '')[:10]}):** {findings['notes']}\n"

    # Trim trailing whitespace then append
    section_clean = section.rstrip() + "\n" + refresh_line + "\n" + samples_block + "\n" + notes_block + "\n"

    new_text = text[:start] + section_clean + text[end:]
    return new_text, f"updated {name}"


def apply_refresh(name: str, findings: dict) -> str:
    if not CREATOR_STUDY_PATH.exists():
        return f"creator-study.md not found at {CREATOR_STUDY_PATH}"
    text = CREATOR_STUDY_PATH.read_text()
    new_text, msg = update_creator_section(text, name, findings)
    if "NOT FOUND" in msg:
        return msg
    CREATOR_STUDY_PATH.write_text(new_text)
    # Update refresh log
    log = read_refresh_log()
    init_refresh_log_for_creator(log, name)
    log["creators"][name]["last_refreshed_at"] = findings.get("refreshed_at", now_ist_iso())
    log["creators"][name]["status"] = findings.get("status", "active")
    if findings.get("topic_drift"):
        log["creators"][name]["topic_drift"] = findings["topic_drift"]
    write_refresh_log(log)
    return msg


# ── CLI ──────────────────────────────────────────────────────────────────


def cmd_list(args):
    creators = parse_tracked_creators()
    log = read_refresh_log()
    print(f"\n{'Creator':25s} {'Pillar':12s} {'Status':10s} {'Last refreshed':25s}")
    print("-" * 80)
    for c in creators:
        name = c["name"]
        info = log.get("creators", {}).get(name, {})
        status = info.get("status", "unknown")
        last = info.get("last_refreshed_at") or "never"
        if last != "never":
            last = last[:10]
        # Detect pillar from full pillar string
        pillar = c["pillar"][:12]
        print(f"{name:25s} {pillar:12s} {status:10s} {last:25s}")
    print(f"\nTotal: {len(creators)} tracked creators")


def cmd_rotation_due(args):
    names = get_rotation_due(args.batch_size)
    if args.json:
        print(json.dumps({"this_week": names, "week": args.week}, indent=2))
    else:
        print(f"Due this Sunday ({args.week}):")
        for n in names:
            print(f"  - {n}")


def cmd_apply_refresh(args):
    findings = json.loads(args.findings)
    if "refreshed_at" not in findings:
        findings["refreshed_at"] = now_ist_iso()
    if "creator" not in findings:
        findings["creator"] = args.creator
    msg = apply_refresh(args.creator, findings)
    print(msg)
    sys.exit(0 if "updated" in msg else 1)


def cmd_stats(args):
    log = read_refresh_log()
    creators = parse_tracked_creators()
    total = len(creators)
    by_status = {}
    refreshed_recently = 0
    cutoff = datetime.now(ist()) - timedelta(days=35)
    for c in creators:
        info = log.get("creators", {}).get(c["name"], {})
        s = info.get("status", "unknown")
        by_status[s] = by_status.get(s, 0) + 1
        last = info.get("last_refreshed_at")
        if last:
            try:
                dt = datetime.fromisoformat(last)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=ist())
                if dt >= cutoff:
                    refreshed_recently += 1
            except ValueError:
                pass
    print(f"Total tracked: {total}")
    print(f"Refreshed in last 35d: {refreshed_recently} ({100 * refreshed_recently // max(total, 1)}%)")
    print("\nBy status:")
    for s, n in sorted(by_status.items()):
        print(f"  {s}: {n}")


def cmd_validate(args):
    if not CREATOR_STUDY_PATH.exists():
        sys.exit(f"creator-study.md missing: {CREATOR_STUDY_PATH}")
    text = CREATOR_STUDY_PATH.read_text()
    creators = parse_tracked_creators()
    missing = []
    found = []
    for c in creators:
        if find_creator_section(text, c["name"]):
            found.append(c["name"])
        else:
            missing.append(c["name"])
    print(f"creator-study.md sections found: {len(found)}/{len(creators)}")
    if missing:
        print("\nMissing sections (peer-tracker can't update these):")
        for n in missing:
            print(f"  - {n}")
        sys.exit(1)
    print("\nAll 15 tracked creators have sections in creator-study.md.")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_list = sub.add_parser("list")
    p_list.set_defaults(func=cmd_list)

    p_rot = sub.add_parser("rotation-due")
    p_rot.add_argument("--week", default="")
    p_rot.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    p_rot.add_argument("--json", action="store_true")
    p_rot.set_defaults(func=cmd_rotation_due)

    p_app = sub.add_parser("apply-refresh")
    p_app.add_argument("--creator", required=True)
    p_app.add_argument("--findings", required=True, help="JSON payload")
    p_app.set_defaults(func=cmd_apply_refresh)

    p_stat = sub.add_parser("stats")
    p_stat.set_defaults(func=cmd_stats)

    p_val = sub.add_parser("validate-creator-study")
    p_val.set_defaults(func=cmd_validate)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
