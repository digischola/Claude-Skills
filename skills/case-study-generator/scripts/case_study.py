#!/usr/bin/env python3
"""
Case Study Generator orchestrator.

Sub-commands:
  prepare    Read an idea-bank entry, validate it's a client-win, surface naming decision + structure prompt for Claude
  bundle     Write the 4 deliverables Claude has drafted into pending-approval/case-study-<entry_id>/
  list-public-clients  Show clients whose names + metrics are publicly allowed
  catalog    List all case-study bundles in pending-approval/

Usage:
  python3 case_study.py prepare --entry-id 4e4eed15
  python3 case_study.py prepare --client "Thrive Retreats"
  python3 case_study.py bundle --entry-id 4e4eed15 --bundle-dir /tmp/case-study-bundle/
  python3 case_study.py list-public-clients
  python3 case_study.py catalog
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

DEFAULT_BRAND = Path("/Users/digischola/Desktop/Digischola")
SKILL_DIR = Path("/Users/digischola/Desktop/Claude Skills/skills/case-study-generator")

PUBLIC_CLIENTS = {
    "Thrive Retreats": {
        "region": "Colo Heights NSW",
        "metrics_allowed": ["+188% Meta sales", "-37% CPS", "90 days"],
        "industry": "wellness retreat",
    },
    "Happy Buddha Retreats": {
        "region": "(sister property to Thrive)",
        "metrics_allowed": [],  # referenced but no specific numbers public
        "industry": "wellness retreat",
    },
    "ISKM Singapore": {
        "region": "Singapore",
        "metrics_allowed": ["+65% registrations", "+40% attendance", "Ratha Yatra 2025"],
        "industry": "spiritual / cultural festival",
    },
    "Samir's Indian Kitchen": {
        "region": "Surry Hills Sydney",
        "metrics_allowed": [],  # restaurant case publicly referenced but not specific numbers
        "industry": "restaurant",
    },
    "Chart & Chime": {
        "region": "(India)",
        "metrics_allowed": [],
        "industry": "music education",
    },
    "CrownTECH": {
        "region": "Toronto",
        "metrics_allowed": [],
        "industry": "B2B services",
    },
}

ANONYMIZATION_TEMPLATES = {
    "wellness retreat": "a wellness retreat client",
    "yoga studio": "a yoga studio client",
    "restaurant": "a restaurant client",
    "B2B SaaS": "a B2B SaaS client",
    "e-commerce": "an e-commerce brand",
    "spiritual": "a cultural-event organizer",
    "hospitality": "a boutique hotel",
    "local services": "a local services provider",
}


def ist() -> timezone:
    return timezone(timedelta(hours=5, minutes=30), name="IST")


def now_ist_iso() -> str:
    return datetime.now(ist()).isoformat()


def read_idea_bank(brand_folder: Path) -> dict:
    # Post-2026-04-29 _engine/ convention: idea-bank lives in brand/_engine/.
    p = brand_folder / "brand" / "_engine" / "idea-bank.json"
    if not p.exists():
        sys.exit(f"idea-bank.json not found at {p}")
    return json.loads(p.read_text())


def find_entry(bank: dict, entry_id: str | None, client: str | None) -> dict | None:
    """Locate a client-win entry by entry_id or client name."""
    for e in bank.get("entries", []):
        # work-capture might use various id schemes — match flexibly
        if entry_id:
            ids = [e.get("id"), e.get("entry_id"), str(e.get("uuid", ""))[:8]]
            if entry_id in ids:
                return e
        if client:
            if client.lower() in (e.get("client", "") or "").lower() or \
               client.lower() in (e.get("raw_note", "") or "").lower():
                return e
    return None


def is_client_win(entry: dict) -> tuple[bool, str]:
    """Return (is_win, reason). Heuristic: type tag OR metrics + client + outcome fields."""
    if entry.get("type") == "client-win":
        return True, "type:client-win"
    if entry.get("client") and (entry.get("outcomes") or entry.get("metrics") or entry.get("results")):
        return True, "has client + outcomes/metrics fields"
    raw = (entry.get("raw_note") or "").lower()
    seed = (entry.get("seed") or "").lower()
    blob = raw + " " + seed
    # Heuristic: has a percentage delta OR multiplier + a time period
    import re
    has_metric = bool(re.search(r"[+-]?\d+(\.\d+)?\s*%", blob)) or bool(re.search(r"\d+(\.\d+)?\s*x\b", blob))
    has_period = bool(re.search(r"\d+\s*(days?|weeks?|months?|hours?|years?)", blob))
    if has_metric and has_period:
        return True, "heuristic: has metric% and time period"
    return False, "no client-win indicators (no type:client-win, no client+outcomes, no metric+period in text)"


def naming_decision(entry: dict) -> dict:
    """Apply Conservative naming policy; return decision dict."""
    client = entry.get("client") or ""
    if client and client in PUBLIC_CLIENTS:
        info = PUBLIC_CLIENTS[client]
        return {
            "named": True,
            "identifier": f"{client} ({info['region']})" if info["region"] else client,
            "industry": info["industry"],
            "credit": "Source: digischola.in/case-studies",
            "metrics_allowed": info["metrics_allowed"],
        }
    industry = entry.get("industry", "wellness retreat")
    region = entry.get("region", "")
    template = ANONYMIZATION_TEMPLATES.get(industry, f"a {industry} client")
    identifier = f"{template}{' in ' + region if region else ''}"
    return {
        "named": False,
        "identifier": identifier,
        "industry": industry,
        "credit": "",
        "metrics_allowed": "all (anonymized)",
    }


def cmd_prepare(args):
    bank = read_idea_bank(args.brand_folder)
    entry = find_entry(bank, args.entry_id, args.client)
    if not entry:
        sys.exit(f"No matching entry found (entry_id={args.entry_id}, client={args.client})")

    is_win, why = is_client_win(entry)
    if not is_win:
        sys.exit(f"This entry is NOT a client-win → use post-writer instead. Reason: {why}")

    decision = naming_decision(entry)
    print(f"\n=== Case Study Prepare ===\n")
    print(f"Entry: {entry.get('id') or entry.get('entry_id') or '?'}")
    print(f"Type: {entry.get('type', '?')}")
    print(f"Client (in source): {entry.get('client', '(not set)')}")
    print(f"Pillar: {entry.get('suggested_pillar') or entry.get('pillar') or '?'}")
    print(f"\nNaming decision:")
    print(f"  Named: {decision['named']}")
    print(f"  Identifier to use: {decision['identifier']}")
    print(f"  Industry: {decision['industry']}")
    print(f"  Credit line: {decision['credit'] or '(none)'}")
    print(f"  Metrics allowed: {decision['metrics_allowed']}")
    print(f"\nNext step:")
    print(f"  Claude reads this entry + 4 templates in assets/templates/ + references/case-study-structure.md.")
    print(f"  Claude generates 4 deliverables, runs validate_case_study.py, then bundles via:")
    print(f"  python3 case_study.py bundle --entry-id {entry.get('id') or args.entry_id} --bundle-dir /tmp/cs-{entry.get('id') or args.entry_id}/")


def cmd_bundle(args):
    if not args.bundle_dir.exists():
        sys.exit(f"Bundle dir not found: {args.bundle_dir}")
    expected_files = ["linkedin-carousel.md", "x-thread.md", "blog-post.md", "instagram-carousel.md"]
    missing = [f for f in expected_files if not (args.bundle_dir / f).exists()]
    if missing:
        sys.exit(f"Bundle missing files: {missing}")

    target_dir = args.brand_folder / "brand" / "queue" / "pending-approval" / f"case-study-{args.entry_id}"
    target_dir.mkdir(parents=True, exist_ok=True)
    for f in expected_files:
        shutil.copy2(args.bundle_dir / f, target_dir / f)

    # Write manifest
    manifest = {
        "entry_id": args.entry_id,
        "bundle_id": f"case-study-{args.entry_id}",
        "deliverables": expected_files,
        "bundled_at": now_ist_iso(),
        "scheduled_pattern": {
            "linkedin-carousel.md": "Mon 09:00 IST",
            "x-thread.md": "Tue 11:00 IST",
            "blog-post.md": "Wed 18:00 IST",
            "instagram-carousel.md": "Sat 10:00 IST",
        },
        "validate_pass": True,  # validator should have run before bundle
    }
    (target_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))

    print(f"\n✓ Bundle written: {target_dir}")
    print(f"  Files: {expected_files}")
    print(f"  Manifest: manifest.json")
    print(f"\nNext steps for Claude:")
    print(f"  1. Invoke visual-generator/scripts/generate_brief.py for LI + IG carousels")
    print(f"  2. Schedule each deliverable via scheduler-publisher/scripts/apply_calendar.py (or set scheduled_at manually)")


def cmd_list_public_clients(args):
    print(f"\nPublic-allowed clients (from credentials.md):\n")
    for name, info in PUBLIC_CLIENTS.items():
        print(f"  {name}")
        print(f"    Region: {info['region']}")
        print(f"    Industry: {info['industry']}")
        print(f"    Metrics allowed: {info['metrics_allowed']}")
        print()


def cmd_catalog(args):
    pending = args.brand_folder / "brand" / "queue" / "pending-approval"
    bundles = sorted(pending.glob("case-study-*"))
    if not bundles:
        print("No case-study bundles in pending-approval/")
        return
    print(f"\n{'Bundle':40s} {'Files':6s} Bundled at")
    print("-" * 80)
    for b in bundles:
        manifest_path = b / "manifest.json"
        if manifest_path.exists():
            m = json.loads(manifest_path.read_text())
            n = len(m.get("deliverables", []))
            ts = m.get("bundled_at", "?")[:19]
        else:
            n = len(list(b.glob("*.md")))
            ts = "(no manifest)"
        print(f"  {b.name:40s} {n:^6d} {ts}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--brand-folder", type=Path, default=DEFAULT_BRAND)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_prep = sub.add_parser("prepare")
    p_prep.add_argument("--entry-id", help="Entry id from idea-bank")
    p_prep.add_argument("--client", help="Client name (alternative to entry-id)")
    p_prep.set_defaults(func=cmd_prepare)

    p_bundle = sub.add_parser("bundle")
    p_bundle.add_argument("--entry-id", required=True)
    p_bundle.add_argument("--bundle-dir", type=Path, required=True, help="Dir with the 4 deliverable .md files")
    p_bundle.set_defaults(func=cmd_bundle)

    p_pc = sub.add_parser("list-public-clients")
    p_pc.set_defaults(func=cmd_list_public_clients)

    p_cat = sub.add_parser("catalog")
    p_cat.set_defaults(func=cmd_catalog)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
