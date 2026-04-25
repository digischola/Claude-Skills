#!/usr/bin/env python3
"""
cleanup.py — Execute approved deletions by moving them to quarantine.

NEVER deletes directly. ALWAYS moves to Desktop/.housekeeping-quarantine/{date}/.
Writes manifest.json per date-folder for rollback.

Input: approved-plan.json — a JSON object with:
    {
      "approved_paths": ["/absolute/path", ...],
      "run_date": "YYYY-MM-DD"  (optional, default today IST)
    }

Usage:
    python3 cleanup.py --plan approved-plan.json --execute
    python3 cleanup.py --plan approved-plan.json --dry-run  (default)
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import shutil
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

HOME = Path(os.path.expanduser("~"))
DESKTOP = HOME / "Desktop"
QUARANTINE_ROOT = DESKTOP / ".housekeeping-quarantine"
SKILL_DIR = Path(__file__).resolve().parent.parent
LOG_FILE = SKILL_DIR / "housekeeping.log"

IST = timezone(timedelta(hours=5, minutes=30))


def log(msg: str) -> None:
    ts = datetime.now(IST).isoformat(timespec="seconds")
    line = f"[{ts}] {msg}\n"
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a") as f:
        f.write(line)
    print(line.rstrip(), file=sys.stderr)


def flatten_path(src: Path) -> str:
    """Convert /abs/path to flattened name safe as a filesystem entry."""
    parts = src.parts
    # Drop leading '/'
    if parts and parts[0] == "/":
        parts = parts[1:]
    flat = "__".join(parts)
    # Cap length at 240 bytes to leave room for suffix
    if len(flat.encode("utf-8")) > 240:
        h = hashlib.sha256(flat.encode("utf-8")).hexdigest()[:8]
        flat = flat.encode("utf-8")[:200].decode("utf-8", errors="ignore") + f"__TRUNC_{h}"
    return flat


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    try:
        with p.open("rb") as f:
            while True:
                chunk = f.read(65536)
                if not chunk:
                    break
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return ""


def size_of(p: Path) -> int:
    if p.is_dir():
        total = 0
        for root, _, files in os.walk(p, onerror=lambda e: None):
            for f in files:
                try:
                    total += (Path(root) / f).lstat().st_size
                except OSError:
                    pass
        return total
    try:
        return p.lstat().st_size
    except OSError:
        return 0


# Defense in depth — even if scan.py sent something PROTECTED, catch it here
PROTECTED_NAMES = {
    "SKILL.md", "CLAUDE.md",
    "pillars.md", "voice-guide.md", "brand-identity.md", "credentials.md",
    "channel-playbook.md", "icp.md", "brand-wiki.md", "wiki-config.json",
    "idea-bank.json", "credential-usage-log.json", "weekly-ritual.state.json",
    "housekeeping.state.json", "scheduler.log", "scheduler-failures.log",
    "housekeeping.log", "analyst-profile.md", "accuracy-protocol.md",
    "skill-architecture-standards.md", "strategic-context.md",
}

PROTECTED_PATH_SEGMENTS = {
    "/shared-context/", "/shared-scripts/",
    "/.git/",
}

# Rule IDs from scan.py that permit moving a file even when it would otherwise
# be caught by the client-deliverable safety net. Requires the plan to label
# the path with one of these rule_ids.
DELIVERABLE_OVERRIDE_RULE_IDS = {
    "superseded-deliverable",
}


def is_protected(p: Path, allow_deliverable: bool = False) -> tuple[bool, str]:
    name = p.name
    if name in PROTECTED_NAMES:
        return True, f"protected filename: {name}"
    s = str(p) + "/"
    for seg in PROTECTED_PATH_SEGMENTS:
        if seg in s:
            return True, f"protected segment: {seg}"
    # Skill architecture subdirs
    parts = p.parts
    if "Claude Skills" in parts and "skills" in parts:
        idx = parts.index("skills")
        # .../Claude Skills/skills/{skill}/{sub}/... — protect if sub in {references, scripts, assets, evals}
        if len(parts) > idx + 2 and parts[idx + 2] in ("references", "scripts", "assets", "evals"):
            return True, f"skill architecture: .../{parts[idx+1]}/{parts[idx+2]}/"
    # Client wiki
    if "wiki" in parts and "Desktop" in parts:
        return True, "client wiki"
    # Client deliverables (preserve all .md/.html/.json/.csv/.pdf)
    if "deliverables" in parts and "Desktop" in parts and not p.is_dir():
        if p.suffix.lower() in (".md", ".html", ".json", ".csv", ".pdf"):
            if allow_deliverable:
                # Scan tier explicitly flagged this deliverable for user review
                # (e.g., superseded-deliverable) AND the user approved via AskUserQuestion.
                # Safety net yields to explicit intent.
                return False, ""
            return True, f"client deliverable {p.suffix}"
    return False, ""


def move_to_quarantine(src: Path, date_dir: Path, manifest: list, rule_id: str = "") -> bool:
    allow_deliverable = rule_id in DELIVERABLE_OVERRIDE_RULE_IDS
    protected, reason = is_protected(src, allow_deliverable=allow_deliverable)
    if protected:
        log(f"REFUSED (PROTECTED: {reason}): {src}")
        return False

    if not src.exists():
        log(f"SKIP (not found): {src}")
        return False

    flat = flatten_path(src)
    dest = date_dir / "items" / flat
    dest.parent.mkdir(parents=True, exist_ok=True)

    size = size_of(src)
    is_dir = src.is_dir()
    sha = "" if is_dir else sha256_file(src)

    try:
        shutil.move(str(src), str(dest))
    except Exception as e:
        log(f"ERROR moving {src}: {e}")
        return False

    manifest.append({
        "original_path": str(src),
        "quarantine_path": str(dest),
        "size_bytes": size,
        "sha256": sha,
        "is_dir": is_dir,
        "quarantined_at": datetime.now(IST).isoformat(timespec="seconds"),
    })
    log(f"QUARANTINED ({size} bytes): {src} -> {dest}")
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", required=True, help="Path to approved-plan.json")
    ap.add_argument("--execute", action="store_true", help="Actually move files (default: dry-run)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    dry_run = args.dry_run or not args.execute

    plan = json.loads(Path(args.plan).read_text())
    # approved_paths may be a list of strings (paths) OR list of {path, rule_id} dicts.
    # Dicts let the user opt specific rule_ids past the deliverable safety net.
    raw = plan.get("approved_paths", [])
    entries: list[tuple[Path, str]] = []
    for item in raw:
        if isinstance(item, str):
            entries.append((Path(item), ""))
        elif isinstance(item, dict):
            entries.append((Path(item["path"]), item.get("rule_id", "")))
    paths = [e[0] for e in entries]
    run_date = plan.get("run_date") or datetime.now(IST).strftime("%Y-%m-%d")

    if not paths:
        log("No approved paths in plan. Nothing to do.")
        return 0

    date_dir = QUARANTINE_ROOT / run_date
    manifest_path = date_dir / "manifest.json"

    if dry_run:
        print(f"DRY RUN — would quarantine {len(paths)} items to {date_dir}/")
        total = 0
        for p, rid in entries:
            allow = rid in DELIVERABLE_OVERRIDE_RULE_IDS
            protected, reason = is_protected(p, allow_deliverable=allow)
            status = f"SKIP ({reason})" if protected else "QUARANTINE"
            s = size_of(p) if p.exists() else 0
            total += 0 if protected else s
            print(f"  [{status}] {p}  ({s} bytes)")
        print(f"Total would-be quarantined: {total} bytes")
        return 0

    date_dir.mkdir(parents=True, exist_ok=True)

    # Load existing manifest if re-running on same day
    manifest = []
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text())
        except Exception:
            log(f"Warning: could not parse existing manifest at {manifest_path}; starting fresh")
            manifest = []

    log(f"=== cleanup run start: {run_date}, {len(paths)} paths ===")
    moved = 0
    for p, rid in entries:
        if move_to_quarantine(p, date_dir, manifest, rule_id=rid):
            moved += 1

    manifest_path.write_text(json.dumps(manifest, indent=2))
    log(f"=== cleanup run end: moved {moved}/{len(paths)} ===")

    print(f"Quarantined {moved}/{len(paths)} items to {date_dir}/")
    print(f"Manifest: {manifest_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
