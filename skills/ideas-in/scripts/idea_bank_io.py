"""Shared IO for idea-bank.json. Used by capture.py, scan_trends.py, scan_peers.py."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "2.0"

VALID_TYPES = {
    "client-win",
    "insight",
    "experiment",
    "failure",
    "build-log",
    "client-comm",
    "observation",
    "trend",
    "peer-pattern",
}

VALID_STATUS = {"raw", "shaped", "published"}


def bank_path(brand_folder: Path) -> Path:
    return brand_folder / "brand" / "_engine" / "idea-bank.json"


def load(brand_folder: Path) -> dict:
    p = bank_path(brand_folder)
    if not p.exists():
        return {
            "schema_version": SCHEMA_VERSION,
            "description": "Content candidates fed by ideas-in skill.",
            "entries": [],
        }
    return json.loads(p.read_text())


def save(brand_folder: Path, data: dict) -> None:
    p = bank_path(brand_folder)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_id() -> str:
    return str(uuid.uuid4())[:8]


def append_entry(brand_folder: Path, entry: dict) -> str:
    if entry.get("type") not in VALID_TYPES:
        raise ValueError(f"Invalid type: {entry.get('type')}. Valid: {sorted(VALID_TYPES)}")
    entry.setdefault("id", make_id())
    entry.setdefault("captured_at", now_iso())
    entry.setdefault("status", "raw")
    if entry["status"] not in VALID_STATUS:
        raise ValueError(f"Invalid status: {entry['status']}")

    data = load(brand_folder)
    data["entries"].append(entry)
    save(brand_folder, data)
    return entry["id"]


def find_by_id(brand_folder: Path, entry_id: str) -> dict | None:
    for e in load(brand_folder)["entries"]:
        if e.get("id") == entry_id:
            return e
    return None


def update_status(brand_folder: Path, entry_id: str, status: str) -> bool:
    if status not in VALID_STATUS:
        raise ValueError(f"Invalid status: {status}")
    data = load(brand_folder)
    for e in data["entries"]:
        if e.get("id") == entry_id:
            e["status"] = status
            save(brand_folder, data)
            return True
    return False


def dedup_url(brand_folder: Path, url: str) -> bool:
    """Return True if url already in bank."""
    for e in load(brand_folder)["entries"]:
        if e.get("source_url") == url:
            return True
    return False


def counts_by_type(brand_folder: Path) -> dict[str, int]:
    out: dict[str, int] = {}
    for e in load(brand_folder)["entries"]:
        out[e.get("type", "unknown")] = out.get(e.get("type", "unknown"), 0) + 1
    return out


def counts_by_status(brand_folder: Path) -> dict[str, int]:
    out: dict[str, int] = {}
    for e in load(brand_folder)["entries"]:
        out[e.get("status", "unknown")] = out.get(e.get("status", "unknown"), 0) + 1
    return out
