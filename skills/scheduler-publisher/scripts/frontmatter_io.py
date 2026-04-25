#!/usr/bin/env python3
"""
Read/write YAML frontmatter on draft markdown files.

Drafts in brand/queue/pending-approval/ have frontmatter like:

    ---
    channel: linkedin
    format: text-post
    entry_id: 4e4eed15
    pillar: Landing-Page Conversion Craft
    scheduled_at: 2026-04-22T09:00:00+05:30
    posting_status: scheduled
    ---
    body text here

This module:
- parses that frontmatter into a Python dict
- updates fields and rewrites the file preserving body
- handles JSON-style values (e.g., `posting_attempts: 0`, lists, dicts)

We avoid pyyaml as a hard dep — implement a minimal but correct parser/writer
for the patterns post-writer / repurpose / scheduler-publisher actually emit.
For complex YAML (nested structures), pyyaml is used if available.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

try:
    import yaml  # type: ignore
    HAVE_YAML = True
except ImportError:
    HAVE_YAML = False


FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?\n)---\s*\n(.*)$", re.DOTALL)


def parse(text: str) -> tuple[dict, str]:
    """Return (frontmatter_dict, body_str)."""
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}, text
    fm_text, body = m.group(1), m.group(2)

    if HAVE_YAML:
        try:
            data = yaml.safe_load(fm_text) or {}
            if not isinstance(data, dict):
                data = {}
            return data, body
        except Exception:
            pass

    # Minimal parser: handles `key: scalar` and `key: {json}` and `key: [json]`
    data: dict = {}
    for line in fm_text.splitlines():
        line = line.rstrip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        key = key.strip()
        val = val.strip()
        if not val:
            data[key] = None
            continue
        # JSON-style dict / list
        if (val.startswith("{") and val.endswith("}")) or (val.startswith("[") and val.endswith("]")):
            try:
                data[key] = json.loads(val)
                continue
            except json.JSONDecodeError:
                pass
        # Numeric
        if val.lstrip("-").isdigit():
            data[key] = int(val)
            continue
        try:
            data[key] = float(val)
            continue
        except ValueError:
            pass
        # Quoted string
        if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
            data[key] = val[1:-1]
            continue
        # Bare string
        data[key] = val
    return data, body


def serialize(fm: dict, body: str) -> str:
    """Serialize frontmatter + body back to a markdown file string."""
    if HAVE_YAML:
        fm_text = yaml.safe_dump(fm, default_flow_style=False, sort_keys=False, allow_unicode=True)
    else:
        fm_text = _serialize_minimal(fm)
    if not fm_text.endswith("\n"):
        fm_text += "\n"
    if not body.startswith("\n"):
        body = body
    return f"---\n{fm_text}---\n{body}"


def _serialize_minimal(fm: dict) -> str:
    lines = []
    for k, v in fm.items():
        if v is None:
            lines.append(f"{k}:")
        elif isinstance(v, (dict, list)):
            lines.append(f"{k}: {json.dumps(v, ensure_ascii=False)}")
        elif isinstance(v, bool):
            lines.append(f"{k}: {str(v).lower()}")
        elif isinstance(v, (int, float)):
            lines.append(f"{k}: {v}")
        else:
            s = str(v)
            # Quote if contains chars that confuse YAML readers
            if any(c in s for c in [":", "#", "[", "]", "{", "}", "&", "*", "!", "|", ">", "'", '"', "%", "@", "`"]):
                s = json.dumps(s, ensure_ascii=False)
            lines.append(f"{k}: {s}")
    return "\n".join(lines) + "\n"


# ── File-level convenience ────────────────────────────────────────────────


def read(path: Path) -> tuple[dict, str]:
    return parse(path.read_text(encoding="utf-8"))


def write(path: Path, fm: dict, body: str) -> None:
    path.write_text(serialize(fm, body), encoding="utf-8")


def update_fields(path: Path, **updates) -> dict:
    """Read file, merge updates into frontmatter, write back. Returns new fm."""
    fm, body = read(path)
    fm.update(updates)
    write(path, fm, body)
    return fm


# ── Status state-machine helpers ──────────────────────────────────────────


def now_ist_iso() -> str:
    """ISO 8601 timestamp in Asia/Kolkata."""
    from datetime import timezone as tz_mod
    try:
        from zoneinfo import ZoneInfo
        ist = ZoneInfo("Asia/Kolkata")
    except ImportError:
        # Fallback: fixed +05:30 offset
        from datetime import timedelta
        ist = tz_mod(timedelta(hours=5, minutes=30), name="IST")
    return datetime.now(ist).isoformat()


def parse_iso(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def mark_posting(path: Path) -> None:
    update_fields(path, posting_status="posting", posting_started_at=now_ist_iso())


def mark_posted(path: Path, url: str, via: str = "api") -> None:
    update_fields(
        path,
        posting_status="posted",
        posted_at=now_ist_iso(),
        platform_url=url,
        published_via=via,
    )


def mark_notified(path: Path) -> None:
    update_fields(
        path,
        posting_status="notified",
        notified_at=now_ist_iso(),
    )


def mark_failed(path: Path, reason: str, attempts: int) -> None:
    update_fields(
        path,
        posting_status="failed",
        posting_failure_reason=reason,
        posting_attempts=attempts,
        posting_failed_at=now_ist_iso(),
    )


def mark_retry_due(path: Path, reason: str, attempts: int, retry_after_sec: int) -> None:
    """Schedule a retry by updating attempts + next-retry timestamp."""
    from datetime import timedelta
    next_retry = datetime.now(timezone.utc) + timedelta(seconds=retry_after_sec)
    update_fields(
        path,
        posting_status="failed",  # so a normal scan won't pick it up
        posting_failure_reason=reason,
        posting_attempts=attempts,
        posting_next_retry_at=next_retry.isoformat(),
    )


def is_due(fm: dict, now_utc: datetime) -> bool:
    """True if this draft should be picked up by tick.py."""
    status = fm.get("posting_status")
    if status not in ("scheduled", None) and status != "failed":
        # in-flight, posted, notified, manual_publish_overdue → skip
        if status == "scheduled":
            pass
        else:
            # 'failed' may be retry-eligible if posting_next_retry_at is past
            if status == "failed":
                next_retry = parse_iso(fm.get("posting_next_retry_at"))
                if next_retry and next_retry.tzinfo is None:
                    next_retry = next_retry.replace(tzinfo=timezone.utc)
                if not next_retry or now_utc < next_retry:
                    return False
            else:
                return False
    if status is None:
        return False  # not yet scheduled
    sched = parse_iso(fm.get("scheduled_at"))
    if sched is None:
        return False
    if sched.tzinfo is None:
        # Assume IST if naive
        from datetime import timedelta
        sched = sched.replace(tzinfo=timezone(timedelta(hours=5, minutes=30)))
    return sched <= now_utc


# ── CLI for inspection ────────────────────────────────────────────────────


def main():
    import argparse
    ap = argparse.ArgumentParser(description="Read/inspect a draft's frontmatter.")
    ap.add_argument("path", type=Path)
    ap.add_argument("--field", help="Print only this field's value")
    args = ap.parse_args()
    fm, _body = read(args.path)
    if args.field:
        print(fm.get(args.field, "(unset)"))
    else:
        print(json.dumps(fm, indent=2, default=str))


if __name__ == "__main__":
    main()
