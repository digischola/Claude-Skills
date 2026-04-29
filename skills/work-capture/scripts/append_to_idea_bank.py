#!/usr/bin/env python3
"""
Append a validated entry to the personal-brand idea-bank.json.

Usage:
  python3 append_to_idea_bank.py <brand_folder> <entry_json_string>
  python3 append_to_idea_bank.py <brand_folder> --from-file entry.json

Enforces two gates before writing:
  1. pillars.md must be marked 'Status: LOCKED' (approval gate from personal-brand-dna)
  2. entry must conform to the schema (required fields + enum values)

Atomic write (temp file + rename). Bypass gate 1 with --force-unlocked for test fixtures.
"""

import argparse
import json
import re
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

REQUIRED_FIELDS = {
    "type",
    "raw_note",
    "suggested_pillar",
    "channel_fit",
    "format_candidates",
}

ALLOWED_TYPES = {
    "client-win", "insight", "experiment", "failure",
    "build-log", "client-comm", "observation",
}

ALLOWED_CHANNELS = {
    "LinkedIn", "Instagram", "X", "Facebook",
    "WA-Status", "WA-Channel",
}

ALLOWED_FORMATS = {
    "LI-post", "LI-carousel", "LI-video",
    "IG-carousel", "IG-reel", "IG-story", "IG-post",
    "X-tweet", "X-thread",
    "WA-status", "WA-channel-post",
    "FB-post",
}

ALLOWED_STATUSES = {"raw", "shaped", "drafted", "scheduled", "posted", "killed"}


def check_pillars_locked(brand_folder: Path):
    """
    Enforce the pillar-approval gate before any entry can be captured.
    Reads brand/_engine/wiki/pillars.md, scans the first 20 lines for a 'Status:' marker.
    Allowed value: LOCKED. Blocked: AWAITING APPROVAL, DRAFT, or anything else.
    """
    pillars_path = brand_folder / "brand" / "_engine" / "wiki" / "pillars.md"
    if not pillars_path.exists():
        return False, f"pillars.md not found at {pillars_path}. Run personal-brand-dna first."

    head = pillars_path.read_text(errors="replace").splitlines()[:20]
    status_line = None
    for line in head:
        m = re.match(
            r"\s*(?:\*\*)?Status(?:\*\*)?\s*[:=]\s*(.+?)\s*(?:\*\*)?$",
            line,
            flags=re.IGNORECASE,
        )
        if m:
            status_line = m.group(1).strip()
            break

    if status_line is None:
        return False, (
            "pillars.md missing a 'Status: ...' line in the first 20 lines. "
            "After approving pillars, set the status banner to 'Status: LOCKED'."
        )

    s_upper = status_line.upper()
    if "LOCKED" in s_upper:
        return True, None
    if "AWAITING APPROVAL" in s_upper or "DRAFT" in s_upper:
        return False, (
            f"pillars.md status is '{status_line}'. "
            "Approve pillars in personal-brand-dna and change status to 'LOCKED' before capturing."
        )
    return False, f"pillars.md status unclear ('{status_line}'). Expected 'LOCKED'."


def validate(entry):
    errors = []
    missing = REQUIRED_FIELDS - set(entry.keys())
    if missing:
        errors.append(f"Missing required fields: {sorted(missing)}")

    if "type" in entry and entry["type"] not in ALLOWED_TYPES:
        errors.append(f"Invalid type {entry['type']!r}. Allowed: {sorted(ALLOWED_TYPES)}")

    for ch in entry.get("channel_fit", []) or []:
        if ch not in ALLOWED_CHANNELS:
            errors.append(f"Invalid channel {ch!r}. Allowed: {sorted(ALLOWED_CHANNELS)}")

    for fmt in entry.get("format_candidates", []) or []:
        if fmt not in ALLOWED_FORMATS:
            errors.append(f"Invalid format {fmt!r}. Allowed: {sorted(ALLOWED_FORMATS)}")

    status = entry.get("status", "raw")
    if status not in ALLOWED_STATUSES:
        errors.append(f"Invalid status {status!r}. Allowed: {sorted(ALLOWED_STATUSES)}")

    raw = entry.get("raw_note", "").strip()
    if len(raw) < 20:
        errors.append("raw_note too short (<20 chars). Preserve context.")

    return errors


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("brand_folder", type=Path,
                    help="e.g. /Users/digischola/Desktop/Digischola")
    ap.add_argument("entry", nargs="?", help="entry JSON string")
    ap.add_argument("--from-file", type=Path, help="load entry JSON from file")
    ap.add_argument("--force-unlocked", action="store_true",
                    help="bypass pillars-LOCKED gate (only for test fixture seeding)")
    args = ap.parse_args()

    if args.from_file:
        with open(args.from_file) as f:
            entry = json.load(f)
    elif args.entry:
        entry = json.loads(args.entry)
    else:
        sys.exit("Must supply entry JSON as argument or --from-file")

    # Gate 1: pillars must be LOCKED.
    if not args.force_unlocked:
        ok, reason = check_pillars_locked(args.brand_folder)
        if not ok:
            print(f"  BLOCKED: {reason}", file=sys.stderr)
            sys.exit(2)

    # Gate 2: entry schema.
    errors = validate(entry)
    if errors:
        for e in errors:
            print(f"  ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    idea_bank_path = args.brand_folder / "brand" / "_engine" / "idea-bank.json"
    if not idea_bank_path.exists():
        sys.exit(f"idea-bank.json not found at {idea_bank_path}. Run personal-brand-dna first.")

    with open(idea_bank_path) as f:
        bank = json.load(f)

    entry.setdefault("id", str(uuid.uuid4()))
    entry.setdefault("captured_at", datetime.now(timezone.utc).isoformat())
    entry.setdefault("status", "raw")

    bank.setdefault("entries", []).append(entry)
    bank["last_updated"] = datetime.now(timezone.utc).isoformat()

    tmp_path = idea_bank_path.with_suffix(".json.tmp")
    with open(tmp_path, "w") as f:
        json.dump(bank, f, indent=2)
    tmp_path.replace(idea_bank_path)

    print(f"Appended entry {entry['id'][:8]} to {idea_bank_path}")
    print(f"  type: {entry['type']}")
    print(f"  pillar: {entry['suggested_pillar']}")
    print(f"  channels: {entry['channel_fit']}")
    print(f"  total entries: {len(bank['entries'])}")


if __name__ == "__main__":
    main()
