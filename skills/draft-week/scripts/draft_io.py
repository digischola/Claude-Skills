#!/usr/bin/env python3
"""Draft IO helpers: parse/write YAML frontmatter, flip idea-bank entry status.

Usage:
  python3 draft_io.py --flip-shaped <entry_id> --brand-folder <path>
  python3 draft_io.py --read-frontmatter <draft.md>
  python3 draft_io.py --set-frontmatter <draft.md> --key validator_status --value "clean (310 chars, exit 0)"
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def parse_frontmatter(md_path: Path) -> tuple[dict[str, str], str]:
    text = md_path.read_text(errors="replace")
    if not text.startswith("---\n"):
        return {}, text
    parts = text.split("---\n", 2)
    if len(parts) < 3:
        return {}, text
    meta: dict[str, str] = {}
    for line in parts[1].splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    return meta, parts[2]


def write_frontmatter(md_path: Path, meta: dict[str, str], body: str) -> None:
    out = "---\n"
    for k, v in meta.items():
        out += f"{k}: {v}\n"
    out += "---\n"
    out += body if body.startswith("\n") else "\n" + body
    md_path.write_text(out)


def set_frontmatter_key(md_path: Path, key: str, value: str) -> None:
    meta, body = parse_frontmatter(md_path)
    meta[key] = value
    write_frontmatter(md_path, meta, body)


def flip_idea_bank_status(brand_folder: Path, entry_id: str, new_status: str) -> bool:
    bank_path = brand_folder / "brand" / "_engine" / "idea-bank.json"
    data = json.loads(bank_path.read_text())
    for e in data.get("entries", []):
        if e.get("id") == entry_id:
            e["status"] = new_status
            bank_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
            return True
    return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--brand-folder", type=Path)
    ap.add_argument("--flip-shaped", help="Entry ID to flip raw → shaped")
    ap.add_argument("--flip-published", help="Entry ID to flip shaped → published")
    ap.add_argument("--read-frontmatter", type=Path)
    ap.add_argument("--set-frontmatter", type=Path)
    ap.add_argument("--key")
    ap.add_argument("--value")
    args = ap.parse_args()

    if args.flip_shaped:
        if not args.brand_folder:
            sys.exit("--brand-folder required with --flip-shaped")
        ok = flip_idea_bank_status(args.brand_folder, args.flip_shaped, "shaped")
        print(f"flip-shaped {args.flip_shaped}: {'ok' if ok else 'NOT FOUND'}")
        return 0 if ok else 1

    if args.flip_published:
        if not args.brand_folder:
            sys.exit("--brand-folder required with --flip-published")
        ok = flip_idea_bank_status(args.brand_folder, args.flip_published, "published")
        print(f"flip-published {args.flip_published}: {'ok' if ok else 'NOT FOUND'}")
        return 0 if ok else 1

    if args.read_frontmatter:
        meta, body = parse_frontmatter(args.read_frontmatter)
        print(json.dumps(meta, indent=2))
        return 0

    if args.set_frontmatter:
        if not args.key or args.value is None:
            sys.exit("--key and --value required with --set-frontmatter")
        set_frontmatter_key(args.set_frontmatter, args.key, args.value)
        print(f"set {args.key}={args.value!r} in {args.set_frontmatter.name}")
        return 0

    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
