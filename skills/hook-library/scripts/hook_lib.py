#!/usr/bin/env python3
"""
Hook Library — CLI for the hook-pattern catalog.

Sub-commands:
  list         List patterns matching filters (--tier, --pillar, --channel, --category, --limit, --json)
  get          Get full details on one pattern by id
  search       Fuzzy search across name + description + examples
  promote      Move pattern up a tier (logs reason)
  demote       Move pattern down a tier (logs reason)
  mark-used    Increment use_count + update last_used_at
  add          Add a new pattern from JSON payload (defaults to Tier 3 unless overridden)
  sync-from-post-writer  Parse post-writer/references/hook-library.md, populate data/hooks.json
  export       Regenerate post-writer's hook-library.md from data/hooks.json
  suggest-tier-moves  Compute auto-promotion / demotion suggestions from performance signals
  stats        Per-tier per-pillar counts + most/least-used patterns
  promotion-log  Show recent tier change history

Usage:
  python3 hook_lib.py sync-from-post-writer
  python3 hook_lib.py list --tier 1 --pillar lp-craft --json
  python3 hook_lib.py get numbers-hero
  python3 hook_lib.py promote numbers-hero --reason "4 HITs in 28d on LI"
  python3 hook_lib.py stats
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from difflib import SequenceMatcher
from pathlib import Path

SKILL_DIR = Path("/Users/digischola/Desktop/Claude Skills/skills/hook-library")
HOOKS_JSON = SKILL_DIR / "data" / "hooks.json"
PROMOTION_LOG = SKILL_DIR / "data" / "promotion-log.json"
POST_WRITER_REF = Path("/Users/digischola/Desktop/Claude Skills/skills/post-writer/references/hook-library.md")

PILLAR_SLUGS = {
    "lp-craft": "Landing-Page Conversion Craft",
    "solo-ops": "Solo Freelance Ops",
    "paid-media": "Small-Budget Paid Media",
}

CATEGORY_NAMES = {
    "curiosity": "Curiosity / Open-Loop",
    "contrarian": "Counterintuitive / Contrarian",
    "data": "Data / Metric-Before-Context",
    "story": "Story / Moment-in-Time",
    "question": "Question",
    "list": "List / Framework",
    "personal-stake": "Personal Stake / Vulnerable",
    "authority": "Authority / Credentials-Forward",
}

TIER_1_CAP_PER_PILLAR = 8
TIER_3_CAP_PER_PILLAR = 5

CHANNEL_CODES = {
    "li": "linkedin", "linkedin": "linkedin",
    "x": "x", "twitter": "x",
    "ig": "instagram", "instagram": "instagram",
    "fb": "facebook", "facebook": "facebook",
    "wa": "whatsapp", "whatsapp": "whatsapp",
}


def ist() -> timezone:
    return timezone(timedelta(hours=5, minutes=30), name="IST")


def now_ist_iso() -> str:
    return datetime.now(ist()).isoformat()


# ── Catalog I/O ──────────────────────────────────────────────────────────


def read_catalog() -> dict:
    if not HOOKS_JSON.exists():
        return {"schema_version": "1.0", "patterns": []}
    return json.loads(HOOKS_JSON.read_text())


def write_catalog(catalog: dict) -> None:
    HOOKS_JSON.parent.mkdir(parents=True, exist_ok=True)
    tmp = HOOKS_JSON.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(catalog, indent=2, ensure_ascii=False))
    tmp.replace(HOOKS_JSON)


def read_promotion_log() -> list:
    if not PROMOTION_LOG.exists():
        return []
    try:
        return json.loads(PROMOTION_LOG.read_text())
    except json.JSONDecodeError:
        return []


def append_promotion_log(entry: dict) -> None:
    log = read_promotion_log()
    log.append(entry)
    PROMOTION_LOG.parent.mkdir(parents=True, exist_ok=True)
    PROMOTION_LOG.write_text(json.dumps(log, indent=2))


# ── Pattern lookup helpers ───────────────────────────────────────────────


def find_pattern(catalog: dict, pattern_id: str) -> tuple[int, dict] | None:
    for i, p in enumerate(catalog.get("patterns", [])):
        if p.get("id") == pattern_id:
            return i, p
    return None


def normalize_id(name: str) -> str:
    """Convert 'The Brutal Truth Text Post' → 'brutal-truth-text-post'."""
    s = name.lower()
    s = re.sub(r"[^a-z0-9 -]", "", s)
    s = re.sub(r"\s+", "-", s.strip())
    s = re.sub(r"-+", "-", s)
    s = re.sub(r"^(the|a|an)-", "", s)
    return s


def channel_short_to_long(s: str) -> list[str]:
    """'LI, X' → ['linkedin', 'x']"""
    parts = [p.strip().lower() for p in re.split(r"[,/]", s) if p.strip()]
    return [CHANNEL_CODES.get(p, p) for p in parts]


# ── sync-from-post-writer ────────────────────────────────────────────────


CATEGORY_HEADER_RE = re.compile(r"^## Category (\d+):\s*(.+?)$", re.MULTILINE)
TABLE_ROW_RE = re.compile(r"^\|\s*(\d+)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*$")


def parse_post_writer_reference() -> list[dict]:
    """Parse the markdown table format in post-writer/references/hook-library.md."""
    if not POST_WRITER_REF.exists():
        sys.exit(f"post-writer reference not found: {POST_WRITER_REF}")
    text = POST_WRITER_REF.read_text()

    # Map category name → slug (best-effort by keyword)
    name_to_slug = {
        "curiosity": "curiosity",
        "contrarian": "contrarian",
        "counterintuitive": "contrarian",
        "data": "data",
        "story": "story",
        "moment-in-time": "story",
        "question": "question",
        "list": "list",
        "framework": "list",
        "personal stake": "personal-stake",
        "vulnerable": "personal-stake",
        "authority": "authority",
        "credentials": "authority",
    }

    def category_to_slug(name: str) -> str:
        n = name.lower()
        for k, v in name_to_slug.items():
            if k in n:
                return v
        return "uncategorized"

    patterns = []
    sections = re.split(r"^## Category \d+:\s*(.+?)$", text, flags=re.MULTILINE)
    # sections: [pre, "Cat 1 name", "table body", "Cat 2 name", "table body", ...]
    for i in range(1, len(sections), 2):
        cat_name = sections[i].strip()
        cat_slug = category_to_slug(cat_name)
        body = sections[i + 1] if i + 1 < len(sections) else ""

        for line in body.splitlines():
            m = TABLE_ROW_RE.match(line)
            if not m:
                continue
            num = m.group(1)
            formula = m.group(2).strip()
            example = m.group(3).strip()
            channel_str = m.group(4).strip()
            best_for = m.group(5).strip()

            # Skip header / separator rows
            if num.lower() in ("#", "---") or formula.lower() in ("formula",):
                continue
            if not num.isdigit():
                continue

            # Generate id from a slug of formula's first 4-5 words
            first_words = " ".join(re.findall(r"[A-Za-z0-9]+", formula))[:50]
            pid = normalize_id(first_words) or f"pattern-{num}"

            channels = channel_short_to_long(channel_str)
            patterns.append({
                "id": pid,
                "name": formula[:60].rstrip(".") if len(formula) > 60 else formula.rstrip("."),
                "category": cat_slug,
                "tier": 2,  # Initial sync: everything starts at Tier 2
                "description": "",
                "formula": formula,
                "examples": [example],
                "best_for": {
                    "pillars": [],  # filled by infer_pillars below
                    "channels": channels,
                    "formats": [],
                },
                "originator": "",
                "credential_anchor_required": False,
                "voice_framework": "",
                "notes": f"From post-writer/references/hook-library.md row #{num}, best_for: {best_for}",
                "tier_history": [],
                "last_used_at": None,
                "use_count": 0,
                "performance_signal": None,
                "archived": False,
                "added_at": now_ist_iso(),
                "source_row_number": int(num),
            })

    # Infer pillars from category + best_for context
    for p in patterns:
        notes = (p.get("notes") or "").lower()
        pillars = []
        if any(k in notes for k in ["lp", "landing page", "cro", "conversion"]):
            pillars.append("lp-craft")
        if any(k in notes for k in ["solo", "freelance", "ops", "operator", "agency"]):
            pillars.append("solo-ops")
        if any(k in notes for k in ["paid media", "ad", "meta", "google ads", "campaign"]):
            pillars.append("paid-media")
        # Fall back: assign by category default
        if not pillars:
            cat = p.get("category")
            if cat in ("data", "list", "framework"):
                pillars = ["lp-craft", "paid-media"]  # data + lists fit both
            elif cat in ("personal-stake", "story"):
                pillars = ["solo-ops"]
            else:
                pillars = ["lp-craft"]
        p["best_for"]["pillars"] = list(dict.fromkeys(pillars))

    return patterns


def cmd_sync_from_post_writer(args):
    new_patterns = parse_post_writer_reference()
    catalog = read_catalog()
    existing_ids = {p["id"] for p in catalog.get("patterns", [])}

    added = 0
    updated = 0
    for p in new_patterns:
        if p["id"] in existing_ids:
            # Update non-tier fields (keep tier from catalog)
            for i, ex in enumerate(catalog["patterns"]):
                if ex["id"] == p["id"]:
                    # Preserve tier, tier_history, performance_signal, use_count, last_used_at
                    preserved = {k: ex.get(k) for k in
                                 ("tier", "tier_history", "performance_signal", "use_count", "last_used_at", "added_at")}
                    catalog["patterns"][i] = {**p, **preserved}
                    updated += 1
        else:
            catalog["patterns"].append(p)
            added += 1
    write_catalog(catalog)
    print(f"\n✓ sync-from-post-writer complete")
    print(f"  Added: {added} new patterns")
    print(f"  Updated: {updated} existing patterns")
    print(f"  Total in catalog: {len(catalog['patterns'])}")


# ── list / get / search ──────────────────────────────────────────────────


def cmd_list(args):
    catalog = read_catalog()
    rows = catalog.get("patterns", [])
    if args.tier:
        rows = [r for r in rows if r.get("tier") == args.tier]
    if args.pillar:
        rows = [r for r in rows if args.pillar in (r.get("best_for") or {}).get("pillars", [])]
    if args.channel:
        chan = CHANNEL_CODES.get(args.channel.lower(), args.channel.lower())
        rows = [r for r in rows if chan in (r.get("best_for") or {}).get("channels", [])]
    if args.category:
        rows = [r for r in rows if r.get("category") == args.category]
    if not args.include_archived:
        rows = [r for r in rows if not r.get("archived")]

    if args.limit:
        rows = rows[: args.limit]

    if args.json:
        print(json.dumps(rows, indent=2, ensure_ascii=False))
        return

    print(f"\n{len(rows)} patterns matching filters:\n")
    print(f"  {'tier':4s} {'id':35s} {'category':16s} {'pillars':25s} use")
    print("  " + "-" * 80)
    for r in rows:
        pillars = ",".join(r.get("best_for", {}).get("pillars", []))[:25]
        cat = r.get("category", "?")[:16]
        print(f"  T{r.get('tier', '?'):<3d} {r.get('id', '?')[:35]:35s} {cat:16s} {pillars:25s} {r.get('use_count', 0)}")


def cmd_get(args):
    catalog = read_catalog()
    found = find_pattern(catalog, args.pattern_id)
    if not found:
        sys.exit(f"Pattern not found: {args.pattern_id}")
    print(json.dumps(found[1], indent=2, ensure_ascii=False))


def cmd_search(args):
    catalog = read_catalog()
    query = args.query.lower()
    scored = []
    for p in catalog.get("patterns", []):
        text = " ".join([
            p.get("name", ""), p.get("description", ""), p.get("formula", ""),
            " ".join(p.get("examples", [])), p.get("category", "")
        ]).lower()
        # Substring match boost + fuzzy ratio
        substring_score = 1.0 if query in text else 0.0
        fuzzy_score = SequenceMatcher(None, query, text[:500]).ratio()
        score = substring_score + fuzzy_score
        if score > 0.3:
            scored.append((score, p))
    scored.sort(key=lambda x: -x[0])
    if args.limit:
        scored = scored[:args.limit]
    print(f"\n{len(scored)} matches for '{args.query}':\n")
    for s, p in scored:
        print(f"  [{s:.2f}] T{p.get('tier','?')} {p.get('id'):35s} {p.get('name')}")


# ── promote / demote / mark-used ─────────────────────────────────────────


def _change_tier(catalog: dict, pattern_id: str, to_tier: int, reason: str, source: str) -> str:
    found = find_pattern(catalog, pattern_id)
    if not found:
        return f"NOT FOUND: {pattern_id}"
    i, p = found
    from_tier = p.get("tier", 2)
    if from_tier == to_tier:
        return f"NO-OP: {pattern_id} is already T{to_tier}"

    # Cap enforcement
    if to_tier == 1:
        # Count current Tier 1 in same pillar
        for pillar in p.get("best_for", {}).get("pillars", []):
            count = sum(1 for q in catalog["patterns"]
                        if q.get("tier") == 1 and pillar in (q.get("best_for") or {}).get("pillars", []))
            if count >= TIER_1_CAP_PER_PILLAR:
                return f"REFUSED: pillar {pillar} already has {count} Tier 1 patterns (cap {TIER_1_CAP_PER_PILLAR}). Demote one first."
    if to_tier == 3:
        for pillar in p.get("best_for", {}).get("pillars", []):
            count = sum(1 for q in catalog["patterns"]
                        if q.get("tier") == 3 and pillar in (q.get("best_for") or {}).get("pillars", []))
            if count >= TIER_3_CAP_PER_PILLAR:
                return f"REFUSED: pillar {pillar} already has {count} Tier 3 patterns (cap {TIER_3_CAP_PER_PILLAR})."

    p["tier"] = to_tier
    history_entry = {
        "from_tier": from_tier,
        "to_tier": to_tier,
        "reason": reason,
        "source": source,
        "timestamp": now_ist_iso(),
    }
    p.setdefault("tier_history", []).append(history_entry)
    catalog["patterns"][i] = p

    log_entry = {"pattern_id": pattern_id, **history_entry}
    append_promotion_log(log_entry)
    return f"changed: {pattern_id} T{from_tier} → T{to_tier} (reason: {reason})"


def cmd_promote(args):
    catalog = read_catalog()
    found = find_pattern(catalog, args.pattern_id)
    if not found:
        sys.exit(f"Pattern not found: {args.pattern_id}")
    current_tier = found[1].get("tier", 2)
    to_tier = args.to_tier or max(1, current_tier - 1)
    msg = _change_tier(catalog, args.pattern_id, to_tier, args.reason, args.source)
    if "REFUSED" in msg or "NOT FOUND" in msg:
        print(msg)
        sys.exit(1)
    write_catalog(catalog)
    print(msg)


def cmd_demote(args):
    catalog = read_catalog()
    found = find_pattern(catalog, args.pattern_id)
    if not found:
        sys.exit(f"Pattern not found: {args.pattern_id}")
    current_tier = found[1].get("tier", 2)
    to_tier = args.to_tier or min(3, current_tier + 1)
    msg = _change_tier(catalog, args.pattern_id, to_tier, args.reason, args.source)
    if "NOT FOUND" in msg:
        print(msg)
        sys.exit(1)
    write_catalog(catalog)
    print(msg)


def cmd_mark_used(args):
    catalog = read_catalog()
    found = find_pattern(catalog, args.pattern_id)
    if not found:
        sys.exit(f"Pattern not found: {args.pattern_id}")
    i, p = found
    p["use_count"] = (p.get("use_count") or 0) + 1
    p["last_used_at"] = now_ist_iso()
    catalog["patterns"][i] = p
    write_catalog(catalog)
    print(f"marked used: {args.pattern_id} (count={p['use_count']}, last={p['last_used_at'][:19]})")


# ── add / export / stats / promotion-log ─────────────────────────────────


def cmd_add(args):
    catalog = read_catalog()
    payload = json.loads(args.json)
    if "id" not in payload:
        sys.exit("Pattern must have 'id'")
    if find_pattern(catalog, payload["id"]):
        sys.exit(f"Pattern already exists: {payload['id']}")
    payload.setdefault("tier", args.tier or 3)
    payload.setdefault("added_at", now_ist_iso())
    payload.setdefault("use_count", 0)
    payload.setdefault("last_used_at", None)
    payload.setdefault("performance_signal", None)
    payload.setdefault("archived", False)
    payload.setdefault("tier_history", [])
    catalog["patterns"].append(payload)
    write_catalog(catalog)
    print(f"added: {payload['id']} as T{payload['tier']} (source: {args.source or 'manual'})")


def cmd_export(args):
    catalog = read_catalog()
    patterns = catalog.get("patterns", [])
    out = args.out or POST_WRITER_REF
    lines = ["# Hook Library (auto-generated by hook-library skill)\n"]
    lines.append(f"Source: data/hooks.json. Last regenerated: {now_ist_iso()[:10]}\n")
    lines.append(f"Total patterns: {len(patterns)} ({sum(1 for p in patterns if p.get('tier')==1)} Tier 1, "
                 f"{sum(1 for p in patterns if p.get('tier')==2)} Tier 2, "
                 f"{sum(1 for p in patterns if p.get('tier')==3)} Tier 3)\n")
    by_cat = {}
    for p in patterns:
        by_cat.setdefault(p.get("category", "uncategorized"), []).append(p)
    for cat, plist in by_cat.items():
        cat_name = CATEGORY_NAMES.get(cat, cat.title())
        lines.append(f"\n## {cat_name}\n")
        lines.append("| Tier | id | Formula | Channels | Pillars |")
        lines.append("|---|---|---|---|---|")
        for p in plist:
            chans = ",".join(p.get("best_for", {}).get("channels", []))
            pills = ",".join(p.get("best_for", {}).get("pillars", []))
            lines.append(f"| T{p.get('tier','?')} | {p.get('id')} | {p.get('formula','')[:80]} | {chans} | {pills} |")
    Path(out).write_text("\n".join(lines))
    print(f"exported to {out}")


def cmd_stats(args):
    catalog = read_catalog()
    patterns = catalog.get("patterns", [])
    by_tier = {}
    by_pillar_tier = {}
    by_category = {}
    for p in patterns:
        t = p.get("tier", "?")
        by_tier[t] = by_tier.get(t, 0) + 1
        for pillar in p.get("best_for", {}).get("pillars", []):
            key = (pillar, t)
            by_pillar_tier[key] = by_pillar_tier.get(key, 0) + 1
        by_category[p.get("category", "?")] = by_category.get(p.get("category", "?"), 0) + 1

    print(f"\nTotal patterns: {len(patterns)}\n")
    print("By tier:")
    for t in sorted(by_tier.keys(), key=lambda x: (isinstance(x, int), x)):
        print(f"  T{t}: {by_tier[t]}")
    print("\nBy pillar × tier:")
    pillars = sorted({pt[0] for pt in by_pillar_tier.keys()})
    for pillar in pillars:
        line = f"  {pillar}:"
        for tier in (1, 2, 3):
            line += f"  T{tier}={by_pillar_tier.get((pillar, tier), 0)}"
        # Mark cap-warnings
        t1_count = by_pillar_tier.get((pillar, 1), 0)
        if t1_count >= TIER_1_CAP_PER_PILLAR:
            line += f"  [T1 AT CAP]"
        t3_count = by_pillar_tier.get((pillar, 3), 0)
        if t3_count >= TIER_3_CAP_PER_PILLAR:
            line += f"  [T3 AT CAP]"
        print(line)
    print("\nBy category:")
    for c, n in sorted(by_category.items(), key=lambda x: -x[1]):
        cat_label = CATEGORY_NAMES.get(c, c)
        print(f"  {cat_label}: {n}")
    # Most-used + least-used
    sorted_by_use = sorted(patterns, key=lambda p: -(p.get("use_count") or 0))
    if sorted_by_use:
        print("\nMost used (top 3):")
        for p in sorted_by_use[:3]:
            print(f"  {p.get('id'):35s} use_count={p.get('use_count', 0)}")


def cmd_promotion_log(args):
    log = read_promotion_log()
    if not log:
        print("No tier changes logged yet.")
        return
    rows = log[-(args.limit or 10):]
    print(f"\nLast {len(rows)} tier changes:\n")
    for entry in rows:
        ts = entry.get("timestamp", "?")[:19]
        print(f"  {ts}  {entry.get('pattern_id'):35s} T{entry.get('from_tier')}→T{entry.get('to_tier')} "
              f"(src={entry.get('source','?')}) {entry.get('reason','')}")


def cmd_suggest_tier_moves(args):
    """Suggest auto-promotion / demotion based on performance signals.
    Heuristic: requires performance_signal field populated by performance-review's record-performance hook."""
    catalog = read_catalog()
    suggestions = {"to_promote_to_tier_1": [], "to_demote_from_tier_1": []}
    for p in catalog.get("patterns", []):
        sig = p.get("performance_signal") or {}
        hits_28d = sig.get("hits_28d", 0)
        flops_28d = sig.get("flops_28d", 0)
        belows_28d = sig.get("belows_28d", 0)

        # Promote: 4 HITs / 0 FLOPs in 28d AND currently T2 or T3
        if p.get("tier") in (2, 3) and hits_28d >= 4 and flops_28d == 0:
            suggestions["to_promote_to_tier_1"].append({
                "id": p["id"],
                "reason": f"{hits_28d} HITs / 0 FLOPs in 28d",
            })
        # Demote: 3+ FLOPs in 21d OR 4+ BELOWs in 28d AND currently T1
        if p.get("tier") == 1 and (flops_28d >= 3 or belows_28d >= 4):
            suggestions["to_demote_from_tier_1"].append({
                "id": p["id"],
                "reason": f"{flops_28d} FLOPs / {belows_28d} BELOWs in 28d",
            })
    if args.json:
        print(json.dumps(suggestions, indent=2))
    else:
        print(f"\nSuggested promotions: {len(suggestions['to_promote_to_tier_1'])}")
        for s in suggestions["to_promote_to_tier_1"]:
            print(f"  PROMOTE {s['id']:35s} ({s['reason']})")
        print(f"\nSuggested demotions: {len(suggestions['to_demote_from_tier_1'])}")
        for s in suggestions["to_demote_from_tier_1"]:
            print(f"  DEMOTE  {s['id']:35s} ({s['reason']})")


# ── CLI plumbing ─────────────────────────────────────────────────────────


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_list = sub.add_parser("list")
    p_list.add_argument("--tier", type=int, choices=[1, 2, 3])
    p_list.add_argument("--pillar", choices=list(PILLAR_SLUGS.keys()))
    p_list.add_argument("--channel")
    p_list.add_argument("--category")
    p_list.add_argument("--limit", type=int)
    p_list.add_argument("--json", action="store_true")
    p_list.add_argument("--include-archived", action="store_true")
    p_list.set_defaults(func=cmd_list)

    p_get = sub.add_parser("get")
    p_get.add_argument("pattern_id")
    p_get.set_defaults(func=cmd_get)

    p_search = sub.add_parser("search")
    p_search.add_argument("query")
    p_search.add_argument("--limit", type=int, default=10)
    p_search.set_defaults(func=cmd_search)

    p_pro = sub.add_parser("promote")
    p_pro.add_argument("pattern_id")
    p_pro.add_argument("--reason", required=True)
    p_pro.add_argument("--to-tier", type=int, choices=[1, 2, 3])
    p_pro.add_argument("--source", default="manual")
    p_pro.set_defaults(func=cmd_promote)

    p_dem = sub.add_parser("demote")
    p_dem.add_argument("pattern_id")
    p_dem.add_argument("--reason", required=True)
    p_dem.add_argument("--to-tier", type=int, choices=[1, 2, 3])
    p_dem.add_argument("--source", default="manual")
    p_dem.set_defaults(func=cmd_demote)

    p_mu = sub.add_parser("mark-used")
    p_mu.add_argument("--id", dest="pattern_id", required=True)
    p_mu.set_defaults(func=cmd_mark_used)

    p_add = sub.add_parser("add")
    p_add.add_argument("--json", required=True)
    p_add.add_argument("--tier", type=int, choices=[1, 2, 3])
    p_add.add_argument("--source", default="manual")
    p_add.set_defaults(func=cmd_add)

    p_sync = sub.add_parser("sync-from-post-writer")
    p_sync.set_defaults(func=cmd_sync_from_post_writer)

    p_exp = sub.add_parser("export")
    p_exp.add_argument("--target", choices=["post-writer"], default="post-writer")
    p_exp.add_argument("--out", type=Path)
    p_exp.set_defaults(func=cmd_export)

    p_stat = sub.add_parser("stats")
    p_stat.set_defaults(func=cmd_stats)

    p_log = sub.add_parser("promotion-log")
    p_log.add_argument("--limit", type=int, default=10)
    p_log.set_defaults(func=cmd_promotion_log)

    p_sug = sub.add_parser("suggest-tier-moves")
    p_sug.add_argument("--window", default="28d")
    p_sug.add_argument("--json", action="store_true")
    p_sug.set_defaults(func=cmd_suggest_tier_moves)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
