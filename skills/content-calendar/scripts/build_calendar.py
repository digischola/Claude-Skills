#!/usr/bin/env python3
"""
Generate a weekly content calendar for the Digischola personal brand.

Reads the brand wiki + idea-bank, applies rotation rules from
references/cadence-templates.md and references/rotation-rules.md,
detects gaps per references/gap-detection.md, writes a week file to
brand/calendars/YYYY-WXX.md, and flips matched entries from raw to shaped.

Usage:
  python3 build_calendar.py <brand_folder>
  python3 build_calendar.py <brand_folder> --week 2026-04-20
  python3 build_calendar.py <brand_folder> --theme "Landing-Page Conversion Craft"
  python3 build_calendar.py <brand_folder> --dry-run

Exit codes:
  0 = calendar generated
  1 = generated with warnings (gaps flagged)
  2 = BLOCKED (empty bank or queue backlog)
"""

import argparse
import json
import re
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path


PILLARS = {
    "Landing-Page Conversion Craft": "LP-Craft",
    "Solo Freelance Ops": "Solo-Ops",
    "Small-Budget Paid Media": "Paid-Media",
}

AI_TAGS = {"claude", "perplexity", "remotion", "lovable", "wabo", "canva", "ai",
           "ai-workflow", "claude-code"}


def iso_week_string(d: date) -> str:
    year, week, _ = d.isocalendar()
    return f"{year}-W{week:02d}"


def next_monday(ref: date = None) -> date:
    ref = ref or date.today()
    days_ahead = (0 - ref.weekday()) % 7
    if days_ahead == 0:
        days_ahead = 7
    return ref + timedelta(days=days_ahead)


def load_pillars_status(brand_folder: Path):
    p = brand_folder / "brand" / "_engine" / "wiki" / "pillars.md"
    if not p.exists():
        return False, "pillars.md missing"
    head = p.read_text(errors="replace").splitlines()[:20]
    for line in head:
        m = re.match(r"\s*(?:\*\*)?Status(?:\*\*)?\s*[:=]\s*(.+?)\s*(?:\*\*)?$",
                     line, flags=re.IGNORECASE)
        if m:
            s = m.group(1).strip().upper()
            if "LOCKED" in s:
                return True, None
            return False, f"pillars.md status is '{m.group(1).strip()}'. Needs LOCKED."
    return False, "pillars.md has no Status: line"


def load_idea_bank(brand_folder: Path):
    p = brand_folder / "brand" / "_engine" / "idea-bank.json"
    with open(p) as f:
        return json.load(f)


def count_pending_approval(brand_folder: Path) -> int:
    q = brand_folder / "brand" / "queue" / "pending-approval"
    if not q.exists():
        return 0
    return len([f for f in q.iterdir() if f.is_file() and f.suffix == ".md"])


def entry_is_ai_themed(entry) -> bool:
    tags = [t.lower() for t in entry.get("tags", [])]
    if any(t in AI_TAGS for t in tags):
        return True
    raw = entry.get("raw_note", "").lower()
    return any(name in raw for name in AI_TAGS)


def build_week_slots(week_start: date, theme: str = None):
    """Phase 1 slot grid. Returns a list of slot dicts."""
    def day(offset):
        d = week_start + timedelta(days=offset)
        return {"date": d.isoformat(), "weekday": d.strftime("%a")}

    base = [
        # Monday
        {**day(0), "channel": "linkedin", "format": "text-post",
         "pillar_lock": "Landing-Page Conversion Craft", "flex": False,
         "slot_id": "mon-li"},
        # Tuesday
        {**day(1), "channel": "x", "format": "thread",
         "pillar_lock": None, "flex": False, "repurpose_of": "mon-li",
         "slot_id": "tue-x-thread"},
        {**day(1), "channel": "x", "format": "single",
         "pillar_lock": None, "flex": True, "slot_id": "tue-x-fresh"},
        # Wednesday
        {**day(2), "channel": "linkedin", "format": "text-post",
         "pillar_lock": "Solo Freelance Ops", "flex": False,
         "slot_id": "wed-li"},
        {**day(2), "channel": "x", "format": "single",
         "pillar_lock": None, "flex": False, "repurpose_of": "wed-li",
         "slot_id": "wed-x"},
        # Thursday
        {**day(3), "channel": "linkedin", "format": "carousel",
         "pillar_lock": None, "flex": True, "slot_id": "thu-li-carousel"},
        {**day(3), "channel": "x", "format": "single",
         "pillar_lock": None, "flex": True, "slot_id": "thu-x-fresh"},
        # Friday
        {**day(4), "channel": "linkedin", "format": "text-post",
         "pillar_lock": "Small-Budget Paid Media", "flex": False,
         "slot_id": "fri-li"},
        {**day(4), "channel": "x", "format": "thread",
         "pillar_lock": None, "flex": False, "repurpose_of": "fri-li",
         "slot_id": "fri-x-thread"},
        # Saturday
        {**day(5), "channel": "instagram", "format": "reel-or-carousel",
         "pillar_lock": None, "flex": True, "repurpose_candidate": True,
         "slot_id": "sat-ig"},
        {**day(5), "channel": "x", "format": "single",
         "pillar_lock": None, "flex": True, "slot_id": "sat-x"},
        # Sunday
        {**day(6), "channel": "none", "format": "engagement-outbound-day",
         "pillar_lock": None, "flex": False, "slot_id": "sun-rest"},
    ]

    if theme:
        # Themed week: override Mon/Wed/Fri pillar locks to the same theme
        for s in base:
            if s.get("pillar_lock"):
                s["pillar_lock"] = theme
        base[0]["theme_override"] = theme

    return base


def find_entry_for_pillar(entries, pillar, used_ids):
    """Pick freshest raw entry matching pillar, not already used."""
    candidates = [e for e in entries
                  if e.get("suggested_pillar") == pillar
                  and e["id"] not in used_ids]
    if not candidates:
        return None
    candidates.sort(key=lambda e: e.get("captured_at", ""), reverse=True)
    return candidates[0]


def find_best_flex_entry(entries, used_ids, pillar_count):
    """Pick best flex entry favoring under-represented pillars."""
    available = [e for e in entries if e["id"] not in used_ids]
    if not available:
        return None

    def priority(e):
        p = e.get("suggested_pillar")
        # lower pillar_count → higher priority
        under_rep = -pillar_count.get(p, 0)
        freshness = e.get("captured_at", "")
        return (under_rep, freshness)

    available.sort(key=priority, reverse=True)
    return available[0]


# ─────────────────────────────────────────────────────────────────────────────
# Ambiguous-format resolver
#
# Some slot specs (e.g., Sat IG) use `reel-or-carousel` as a placeholder that
# used to push the format decision downstream to Step 6 (visual-generator).
# That broke Skill Protocol Supremacy — downstream had no framework to pick,
# so it always defaulted to carousel, meaning Digischola never shipped a Reel.
#
# Patched 2026-04-22: the calendar now commits to exactly ONE format at build
# time, applying a deterministic content-driven rule:
#
#   DEFAULT: reel  (IG Reels reach non-followers; carousels mostly don't —
#                   default must serve algorithmic growth)
#   OVERRIDE to carousel when entry is DATA-HEAVY (numbers, thresholds,
#     benchmarks, tiers — these don't narrate well in 30 seconds)
#
# The resolution reason is stored on the slot so the calendar markdown can
# show "picked reel because no heavy-numeric signals".
# ─────────────────────────────────────────────────────────────────────────────

AMBIGUOUS_FORMATS = {"reel-or-carousel"}

# Keyword signals that lean an entry toward CAROUSEL (data-heavy).
CAROUSEL_KEYWORDS = {
    "benchmark", "benchmarks", "median", "percentile", "percentile:",
    "threshold", "thresholds", "tier", "tiers", "floor",
    "minimum", "maximum", "avg", "average", "mean",
    "statistics", "stats", "data", "rate", "rates",
    "conversion rate", "ctr", "cpa", "roas", "cpm",
    "budget", "spend",
}

# Tag signals pushing to CAROUSEL.
CAROUSEL_TAGS = {
    "benchmark", "data", "stats", "research", "study", "numbers",
}

# Tag signals pushing to REEL (story / transformation / demo).
REEL_TAGS = {
    "case-study", "transformation", "win", "behind-the-scenes",
    "demo", "story", "testimonial",
}


def _count_numeric_signals(text: str) -> int:
    """Count strong numeric signals in text — percentages, dollar figures,
    multi-digit numbers. 3+ signals = data-heavy."""
    if not text:
        return 0
    count = 0
    # Percentages: "12 percent", "5%", "8%-12%"
    count += len(re.findall(r"\b\d+\s*(?:%|percent|pct)\b", text, re.IGNORECASE))
    # Dollar figures: "$300", "$50/day", "$1,000"
    count += len(re.findall(r"\$\s*\d[\d,]*(?:\.\d+)?", text))
    # Range patterns: "3 to 8", "3-8", "300-500"
    count += len(re.findall(r"\b\d+\s*(?:to|-)\s*\d+\b", text, re.IGNORECASE))
    # Multi-digit numbers (3+ digits, often meaningful: 2026, 300, 1500)
    count += len(re.findall(r"\b\d{3,}\b", text))
    return count


def resolve_ambiguous_format(slot: dict) -> tuple[str, str]:
    """Return (resolved_format, reason). Only called when slot.format is in
    AMBIGUOUS_FORMATS. Falls back to `reel` (algorithmic default) unless the
    entry signals data-heavy, in which case `carousel`."""
    if slot.get("format") not in AMBIGUOUS_FORMATS:
        return slot["format"], ""

    raw_format = slot["format"]
    tags = {(t or "").lower() for t in (slot.get("tags") or [])}
    summary = (slot.get("entry_summary") or "").lower()

    # Tag-based override first — explicit trumps implicit
    if tags & REEL_TAGS:
        return "reel", f"tag signal (reel): {sorted(tags & REEL_TAGS)}"
    if tags & CAROUSEL_TAGS:
        return "carousel", f"tag signal (carousel): {sorted(tags & CAROUSEL_TAGS)}"

    # Keyword signal in summary
    hits = [kw for kw in CAROUSEL_KEYWORDS if kw in summary]
    if hits:
        return "carousel", f"keyword signal: {hits[:3]}"

    # Numeric density
    numeric_signals = _count_numeric_signals(slot.get("entry_summary") or "")
    if numeric_signals >= 3:
        return "carousel", f"{numeric_signals} numeric signals (data-heavy)"

    # Default: reel (IG growth bias). This is the rule we want to hit most
    # weeks — it's what creates algorithmic surface area on Instagram.
    return "reel", f"default (no data-heavy signals; IG growth priority)"


def match_slots_to_entries(slots, raw_entries):
    """Main matching algorithm. Returns (filled_slots, matched_ids, gap_alerts)."""
    used_ids = set()
    pillar_count = {p: 0 for p in PILLARS}
    filled = []
    gap_alerts = []

    # Pass 1: pillar-locked slots
    for s in slots:
        if s.get("pillar_lock") and not s.get("repurpose_of"):
            entry = find_entry_for_pillar(raw_entries, s["pillar_lock"], used_ids)
            if entry:
                s["entry_id"] = entry["id"]
                s["entry_type"] = entry["type"]
                s["entry_summary"] = entry["raw_note"][:120] + (
                    "..." if len(entry["raw_note"]) > 120 else "")
                s["tags"] = entry.get("tags", [])
                used_ids.add(entry["id"])
                pillar_count[s["pillar_lock"]] += 1
            else:
                gap_alerts.append({
                    "severity": "CRITICAL",
                    "slot": s["slot_id"],
                    "message": f"{s['weekday']} {s['channel']} {s['format']} slot locked to pillar '{s['pillar_lock']}' but no raw entry matches. Fix: capture a {s['pillar_lock']} moment via work-capture.",
                })
        filled.append(s)

    # Pass 2: repurpose slots (inherit entry_id from source slot)
    by_slot_id = {s["slot_id"]: s for s in filled}
    for s in filled:
        src = s.get("repurpose_of")
        if src and src in by_slot_id:
            source_slot = by_slot_id[src]
            if source_slot.get("entry_id"):
                s["entry_id"] = source_slot["entry_id"]
                s["entry_type"] = source_slot["entry_type"]
                s["entry_summary"] = source_slot["entry_summary"]
                s["tags"] = source_slot.get("tags", [])
                s["is_repurpose"] = True

    # Pass 3: Saturday IG repurpose (pick a strong LI slot to repurpose from)
    sat_ig = by_slot_id.get("sat-ig")
    if sat_ig and not sat_ig.get("entry_id"):
        # pick Monday LI or Friday LI, whichever is filled
        for src_id in ["mon-li", "fri-li", "wed-li", "thu-li-carousel"]:
            src = by_slot_id.get(src_id)
            if src and src.get("entry_id"):
                sat_ig["entry_id"] = src["entry_id"]
                sat_ig["entry_type"] = src["entry_type"]
                sat_ig["entry_summary"] = src["entry_summary"]
                sat_ig["tags"] = src.get("tags", [])
                sat_ig["is_repurpose"] = True
                sat_ig["repurpose_of"] = src_id
                break

    # Pass 4: flex slots (Thu LI carousel, fresh X tweets)
    for s in filled:
        if s.get("flex") and not s.get("entry_id") and s["channel"] != "none":
            entry = find_best_flex_entry(raw_entries, used_ids, pillar_count)
            if entry:
                s["entry_id"] = entry["id"]
                s["entry_type"] = entry["type"]
                s["entry_summary"] = entry["raw_note"][:120] + (
                    "..." if len(entry["raw_note"]) > 120 else "")
                s["tags"] = entry.get("tags", [])
                used_ids.add(entry["id"])
                p = entry.get("suggested_pillar")
                if p:
                    pillar_count[p] = pillar_count.get(p, 0) + 1
            else:
                # soft gap — flex slots don't get CRITICAL, they just stay empty
                gap_alerts.append({
                    "severity": "INFO",
                    "slot": s["slot_id"],
                    "message": f"{s['weekday']} {s['channel']} {s['format']} flex slot has no available entry. Will ship the week without this slot.",
                })

    # Pass 5: resolve ambiguous formats (e.g., "reel-or-carousel" → "reel" or
    # "carousel" based on entry characteristics). Patched 2026-04-22 — used to
    # punt the decision to Step 6 (visual-generator), but downstream had no
    # rule so it always defaulted to carousel, meaning Digischola never
    # shipped a Reel. See resolve_ambiguous_format() for the rule.
    for s in filled:
        if s.get("format") in AMBIGUOUS_FORMATS and s.get("entry_id"):
            original_format = s["format"]
            resolved, reason = resolve_ambiguous_format(s)
            s["format"] = resolved
            s["format_was_ambiguous"] = original_format
            s["format_resolution_reason"] = reason

    return filled, used_ids, gap_alerts, pillar_count


def detect_distribution_gaps(raw_entries, pillar_count, total_used):
    """Check for ai-theme, pillar-distribution, total-volume gaps."""
    alerts = []

    # AI theme cadence (target ~1 in 3 on LinkedIn)
    li_slots_filled = sum(1 for c in pillar_count.values() if c > 0) * 4 / 3
    ai_entries = [e for e in raw_entries if entry_is_ai_themed(e)]
    if len(raw_entries) >= 4 and len(ai_entries) == 0:
        alerts.append({
            "severity": "WARNING",
            "slot": "week",
            "message": "No AI-themed entries this cycle. The brand's AI-native-operator positioning is at risk. Capture an AI workflow moment (Claude / Perplexity / Lovable / Remotion).",
        })

    # Pillar shortage checks (for NEXT week planning)
    pillar_raw_counts = {}
    for e in raw_entries:
        p = e.get("suggested_pillar")
        if p:
            pillar_raw_counts[p] = pillar_raw_counts.get(p, 0) + 1

    for p in PILLARS:
        n = pillar_raw_counts.get(p, 0)
        if n == 0:
            alerts.append({
                "severity": "CRITICAL",
                "slot": "pillar-bank",
                "message": f"Pillar '{p}' has 0 raw entries in the bank. Capture at least 1 before next week.",
            })
        elif n == 1:
            alerts.append({
                "severity": "WARNING",
                "slot": "pillar-bank",
                "message": f"Pillar '{p}' has only 1 raw entry. Bank is thin for this pillar.",
            })

    # Total volume
    total_raw = len(raw_entries)
    if 1 <= total_raw <= 3:
        alerts.append({
            "severity": "CRITICAL",
            "slot": "volume",
            "message": f"Only {total_raw} raw entries in bank. Phase 1 weeks ideally need 6-10. Capture more via work-capture.",
        })
    elif 4 <= total_raw <= 6:
        alerts.append({
            "severity": "WARNING",
            "slot": "volume",
            "message": f"{total_raw} raw entries. Healthy Phase 1 weeks use 6-10. Capture more before next week.",
        })

    return alerts


def render_calendar_markdown(week_start: date, slots, gap_alerts,
                             pillar_count, raw_entries, theme=None):
    iso_week = iso_week_string(week_start)
    lines = []
    lines.append(f"# Content Calendar. Week of {week_start.isoformat()} ({iso_week})")
    lines.append("")
    lines.append(f"Status: DRAFT (auto-generated {date.today().isoformat()})")
    lines.append("Phase: 1 (LinkedIn reactivation, weeks 1-6)")
    if theme:
        lines.append(f"Theme override: {theme} (all Mon/Wed/Fri slots)")
    else:
        lines.append("Mode: balanced (pillars rotated Mon/Wed/Fri)")
    lines.append("")

    # Weekly overview table
    lines.append("## Weekly overview")
    lines.append("")
    lines.append("| Day | Date | Channel | Format | Pillar | Entry | Type | Is Repurpose |")
    lines.append("|---|---|---|---|---|---|---|---|")
    resolved_rows = []  # collect format-resolution notes for an inline caption
    for s in slots:
        if s["channel"] == "none":
            lines.append(f"| {s['weekday']} | {s['date']} | (rest) | {s['format']} | - | - | - | - |")
            continue
        pillar = s.get("pillar_lock") or "flex"
        entry_id = s.get("entry_id") or "GAP"
        entry_id_short = entry_id[:8] if entry_id != "GAP" else "GAP"
        entry_type = s.get("entry_type") or "-"
        is_repurpose = "yes" if s.get("is_repurpose") else "no"
        # Show resolved format; if it was ambiguous, append a ‡ marker
        format_display = s["format"]
        if s.get("format_was_ambiguous"):
            format_display = f"{s['format']} ‡"
            resolved_rows.append(
                f"- `{s['slot_id']}` · was `{s['format_was_ambiguous']}` → "
                f"**{s['format']}** ({s.get('format_resolution_reason', 'no reason')})"
            )
        lines.append(f"| {s['weekday']} | {s['date']} | {s['channel']} | "
                     f"{format_display} | {pillar} | {entry_id_short} | "
                     f"{entry_type} | {is_repurpose} |")
    lines.append("")
    # Explain any ambiguous-format resolutions inline (transparency: the user
    # should know WHY a reel-or-carousel slot resolved to carousel or reel).
    if resolved_rows:
        lines.append("**Format resolutions** (‡):")
        lines.extend(resolved_rows)
        lines.append("")

    # Run-order (which slots to trigger post-writer on, in priority order)
    lines.append("## Run post-writer on these, in priority order")
    lines.append("")
    priority_order = ["mon-li", "wed-li", "fri-li", "thu-li-carousel",
                      "tue-x-thread", "wed-x", "fri-x-thread", "sat-ig",
                      "tue-x-fresh", "thu-x-fresh", "sat-x"]
    slot_by_id = {s["slot_id"]: s for s in slots}
    n = 1
    for slot_id in priority_order:
        s = slot_by_id.get(slot_id)
        if s and s.get("entry_id"):
            marker = "(repurpose)" if s.get("is_repurpose") else "(primary)"
            lines.append(f"{n}. **{s['weekday']} {s['channel']} {s['format']}** "
                         f"{marker}: entry `{s['entry_id'][:8]}` "
                         f"({s.get('entry_type', '?')}) - {s.get('entry_summary', '')}")
            n += 1
    if n == 1:
        lines.append("(no slots filled; see gap alerts)")
    lines.append("")

    # Gap alerts
    lines.append("## Gap alerts")
    lines.append("")
    if not gap_alerts:
        lines.append("None. Week is fully planned.")
    else:
        critical = [g for g in gap_alerts if g["severity"] == "CRITICAL"]
        warning = [g for g in gap_alerts if g["severity"] == "WARNING"]
        info = [g for g in gap_alerts if g["severity"] == "INFO"]

        for bucket, label in [(critical, "CRITICAL"), (warning, "WARNING"), (info, "INFO")]:
            if bucket:
                lines.append(f"### {label}")
                lines.append("")
                for g in bucket:
                    lines.append(f"- `{g['slot']}`: {g['message']}")
                lines.append("")

    # Distribution summary
    lines.append("## Distribution summary")
    lines.append("")
    lines.append(f"- Total raw entries in bank: {len(raw_entries)}")
    lines.append(f"- Slots filled: {sum(1 for s in slots if s.get('entry_id'))} of {len(slots) - 1}")
    lines.append(f"- LinkedIn posts: {sum(1 for s in slots if s['channel'] == 'linkedin' and s.get('entry_id'))} of 4")
    lines.append(f"- X posts: {sum(1 for s in slots if s['channel'] == 'x' and s.get('entry_id'))} of 6")
    lines.append(f"- Instagram posts: {sum(1 for s in slots if s['channel'] == 'instagram' and s.get('entry_id'))} of 1")
    lines.append(f"- Pillar coverage: {dict(pillar_count)}")
    ai_filled = sum(1 for s in slots
                    if s.get("tags") and any(t.lower() in AI_TAGS for t in s["tags"]))
    lines.append(f"- AI-themed slots: {ai_filled} (target: ~1 of 3 LinkedIn posts)")
    lines.append("")

    lines.append("---")
    lines.append(f"Generated by content-calendar skill. Source: brand/_engine/idea-bank.json. Pillars: LOCKED. Re-run after capturing more entries to fill gaps.")

    return "\n".join(lines) + "\n"


def flip_entry_statuses(brand_folder: Path, matched_ids, iso_week):
    p = brand_folder / "brand" / "_engine" / "idea-bank.json"
    with open(p) as f:
        bank = json.load(f)
    changed = 0
    for e in bank["entries"]:
        if e["id"] in matched_ids:
            e["status"] = "shaped"
            e["scheduled_week"] = iso_week
            changed += 1
    bank["last_updated"] = datetime.now(timezone.utc).isoformat()
    tmp = p.with_suffix(".json.tmp")
    with open(tmp, "w") as f:
        json.dump(bank, f, indent=2)
    tmp.replace(p)
    return changed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("brand_folder", type=Path)
    ap.add_argument("--week", type=str, default=None,
                    help="Monday of target week (ISO date YYYY-MM-DD). Default: next Monday.")
    ap.add_argument("--theme", type=str, default=None,
                    help="Themed week override: pillar name. All Mon/Wed/Fri slots get this pillar.")
    ap.add_argument("--dry-run", action="store_true",
                    help="Generate + print but do not write calendar file or flip statuses")
    args = ap.parse_args()

    # Pillars must be LOCKED
    ok, reason = load_pillars_status(args.brand_folder)
    if not ok:
        print(f"  BLOCKED: {reason}", file=sys.stderr)
        sys.exit(2)

    # Determine week
    if args.week:
        week_start = datetime.strptime(args.week, "%Y-%m-%d").date()
        if week_start.weekday() != 0:
            print(f"  ERROR: --week must be a Monday. {args.week} is a {week_start.strftime('%A')}.",
                  file=sys.stderr)
            sys.exit(1)
    else:
        week_start = next_monday()

    iso_week = iso_week_string(week_start)

    # Load idea-bank
    bank = load_idea_bank(args.brand_folder)
    raw_entries = [e for e in bank.get("entries", [])
                   if e.get("status") == "raw" and not e.get("scheduled_week")]

    # BLOCK checks
    if len(raw_entries) == 0:
        print("  BLOCKED: idea-bank has 0 raw entries. Run work-capture first.", file=sys.stderr)
        sys.exit(2)

    queue_count = count_pending_approval(args.brand_folder)
    if queue_count > 10:
        print(f"  BLOCKED: {queue_count} drafts pending approval. Clear the queue first.",
              file=sys.stderr)
        sys.exit(2)

    # Theme validation
    if args.theme and args.theme not in PILLARS:
        print(f"  ERROR: --theme must be one of {list(PILLARS.keys())}", file=sys.stderr)
        sys.exit(1)

    # Build + match
    slots = build_week_slots(week_start, args.theme)
    slots, matched_ids, slot_gap_alerts, pillar_count = match_slots_to_entries(
        slots, raw_entries)

    # Detect distribution gaps
    dist_alerts = detect_distribution_gaps(raw_entries, pillar_count, matched_ids)
    all_alerts = slot_gap_alerts + dist_alerts

    # Render markdown
    md = render_calendar_markdown(week_start, slots, all_alerts,
                                  pillar_count, raw_entries, args.theme)

    # Write
    cal_path = args.brand_folder / "brand" / "calendars" / f"{iso_week}.md"
    if args.dry_run:
        print(md)
        print(f"\n[DRY RUN] Would write to {cal_path}")
        print(f"[DRY RUN] Would flip {len(matched_ids)} entries to shaped + scheduled_week={iso_week}")
    else:
        cal_path.parent.mkdir(parents=True, exist_ok=True)
        cal_path.write_text(md)
        changed = flip_entry_statuses(args.brand_folder, matched_ids, iso_week)
        print(f"Calendar written: {cal_path}")
        print(f"Entries flipped to shaped: {changed}")

    # Exit code
    critical = [g for g in all_alerts if g["severity"] == "CRITICAL"]
    if critical:
        print(f"\nWARN: {len(critical)} critical gap(s). Calendar generated with gaps.")
        sys.exit(1)
    warning = [g for g in all_alerts if g["severity"] == "WARNING"]
    if warning:
        print(f"\nNote: {len(warning)} warning(s). Review gap alerts in the calendar file.")
        sys.exit(1)
    print("\nAll checks passed. Week is fully planned.")
    sys.exit(0)


if __name__ == "__main__":
    main()
