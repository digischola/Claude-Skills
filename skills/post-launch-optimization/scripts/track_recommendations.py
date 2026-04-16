#!/usr/bin/env python3
"""Layer 11 Session Memory tracker.

Parses a previous optimization report, extracts recommended actions
([KILL]/[SCALE]/[TEST]/[ADJUST]/[NEGATIVE]), and produces an
implementation-tracker section for the current report. The current skill
caller passes live entity state (ad status, budget, etc.) as a JSON file
so this script can mark each action as IMPLEMENTED / NOT_IMPLEMENTED /
PARTIAL / UNVERIFIABLE.

Usage (module):
    from track_recommendations import extract_actions, audit_implementation
    prior = extract_actions(open("last-report.md").read())
    audit = audit_implementation(prior, current_state={...})

Usage (CLI):
    python track_recommendations.py <previous-report.md> [current-state.json]

current-state.json schema:
    {
      "ads":       { "<ad_name>":       { "status": "ACTIVE|PAUSED|DELETED", "last_status_change": "2026-04-16" } },
      "ad_sets":   { "<ad_set_name>":   { "daily_budget": 35.0 } },
      "campaigns": { "<campaign_name>": { "daily_budget": 200.0, "status": "ENABLED|PAUSED" } },
      "keywords":  { "<keyword_text>":  { "status": "ACTIVE|NEGATIVE" } }
    }
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional


ACTION_TYPES = ("KILL", "SCALE", "TEST", "ADJUST", "NEGATIVE", "PAUSE", "WINNER", "NO_WINNER", "NEED_MORE_DATA")


@dataclass
class PriorAction:
    """One action the previous report asked the analyst to take."""
    action: str                  # KILL / SCALE / TEST / ADJUST / NEGATIVE / PAUSE
    entity_type: str             # ad / ad_set / campaign / keyword / (unknown)
    entity_name: Optional[str]   # best-effort extraction
    raw_line: str                # source line for traceability
    details: str = ""            # free-form reason text that followed the action


@dataclass
class AuditEntry:
    """Result of checking a single prior action against current state."""
    action: str
    entity_type: str
    entity_name: Optional[str]
    status: str                  # IMPLEMENTED | NOT_IMPLEMENTED | PARTIAL | UNVERIFIABLE
    note: str
    source_line: str


# ── Extraction ───────────────────────────────────────────────────────────────

# [ACTION] Campaign/Ad Set/Ad Name: details...
# Tolerant: accept any separator between action tag and entity name.
_ACTION_LINE_RE = re.compile(
    r"\[(" + "|".join(ACTION_TYPES) + r")(?::[^\]]+)?\]"   # [KILL] or [WINNER:B] etc.
    r"\s*([^\n]+)", re.IGNORECASE
)


def _guess_entity(fragment: str) -> tuple[str, Optional[str]]:
    """Pick entity_type and a best-effort entity_name from the freeform fragment.
    Returns (entity_type, entity_name_or_None).

    Name extraction: always prefer a quoted name (double or single quote) if one
    appears after the type keyword — this survives punctuation in the name itself.
    Falls back to a bare-word regex if no quoted name is present.
    """
    lower = fragment.lower()

    def _quoted_after(keyword_re: str) -> Optional[str]:
        m = re.search(keyword_re + r'\s+["\']([^"\']+)["\']', fragment, re.IGNORECASE)
        return m.group(1) if m else None

    def _bare_after(keyword_re: str) -> Optional[str]:
        m = re.search(
            keyword_re + r"\s+([\w\- \u2013\u2014/]+?)(?:\s*[.,:→(]|\s*$)",
            fragment, re.IGNORECASE,
        )
        return m.group(1).strip() if m else None

    if re.search(r"\b(?:keyword|neg\s*kw|negative\s+keyword)s?\b", lower):
        name = _quoted_after(r"keywords?")
        return "keyword", name

    if "ad set" in lower or "ad-set" in lower or "adset" in lower:
        name = _quoted_after(r"ad[\s-]?sets?") or _bare_after(r"ad[\s-]?sets?")
        return "ad_set", name

    if re.search(r"\bcampaign\b", lower):
        name = _quoted_after(r"campaigns?") or _bare_after(r"campaigns?")
        return "campaign", name

    if re.search(r"\b(?:ad|creative|ad name)\b", lower):
        # Quoted ad name is the common case (e.g. Ad "Emily_TT_Hero_v1")
        name = _quoted_after(r"ads?") or _bare_after(r"ads?")
        return "ad", name

    return "unknown", None


def extract_actions(report_text: str) -> list[PriorAction]:
    """Pull every actionable line out of a previous report."""
    actions: list[PriorAction] = []
    for m in _ACTION_LINE_RE.finditer(report_text):
        action = m.group(1).upper()
        rest = m.group(2).strip()
        entity_type, entity_name = _guess_entity(rest)
        # Split entity portion from the rationale text following a separator
        details_match = re.search(r"[→:]\s*(.+)$", rest)
        details = details_match.group(1).strip() if details_match else ""
        actions.append(PriorAction(
            action=action,
            entity_type=entity_type,
            entity_name=entity_name,
            raw_line=m.group(0).strip(),
            details=details,
        ))
    return actions


# ── Audit ────────────────────────────────────────────────────────────────────

def audit_implementation(prior: list[PriorAction], current_state: dict) -> list[AuditEntry]:
    """Check each prior action against current_state; return an audit table."""
    ads = current_state.get("ads", {})
    ad_sets = current_state.get("ad_sets", {})
    campaigns = current_state.get("campaigns", {})
    keywords = current_state.get("keywords", {})

    entries: list[AuditEntry] = []
    for a in prior:
        status, note = _audit_one(a, ads, ad_sets, campaigns, keywords)
        entries.append(AuditEntry(
            action=a.action,
            entity_type=a.entity_type,
            entity_name=a.entity_name,
            status=status,
            note=note,
            source_line=a.raw_line,
        ))
    return entries


def _audit_one(a: PriorAction, ads: dict, ad_sets: dict, campaigns: dict, keywords: dict) -> tuple[str, str]:
    name = a.entity_name
    # Without an entity name we can't verify — but we still surface the action.
    if not name:
        return "UNVERIFIABLE", "no entity name extracted from report — check manually"

    # KILL / PAUSE — expect status changed away from ACTIVE/ENABLED
    if a.action in ("KILL", "PAUSE"):
        if a.entity_type == "ad":
            ad = ads.get(name)
            if not ad:
                return "UNVERIFIABLE", f"ad '{name}' not found in current state"
            if ad.get("status", "").upper() in ("PAUSED", "DELETED", "ARCHIVED"):
                return "IMPLEMENTED", f"status={ad['status']}"
            return "NOT_IMPLEMENTED", f"ad still {ad.get('status', 'unknown')} — expected paused/deleted"
        if a.entity_type == "campaign":
            c = campaigns.get(name)
            if not c:
                return "UNVERIFIABLE", f"campaign '{name}' not found"
            if c.get("status", "").upper() in ("PAUSED", "REMOVED"):
                return "IMPLEMENTED", f"status={c['status']}"
            return "NOT_IMPLEMENTED", f"campaign still {c.get('status', 'unknown')}"
        return "UNVERIFIABLE", f"can't infer entity type for {a.entity_type}"

    # SCALE / ADJUST — expect a budget increase (scale) or any budget change (adjust)
    if a.action in ("SCALE", "ADJUST"):
        if a.entity_type == "ad_set":
            s = ad_sets.get(name)
            if not s:
                return "UNVERIFIABLE", f"ad set '{name}' not found"
            prior_budget = _extract_number_from_details(a.details, kind="prior")
            current_budget = s.get("daily_budget")
            if prior_budget and current_budget:
                if a.action == "SCALE" and current_budget > prior_budget:
                    return "IMPLEMENTED", f"budget raised to ${current_budget}"
                if a.action == "ADJUST" and abs(current_budget - prior_budget) > 0.01:
                    return "IMPLEMENTED", f"budget changed to ${current_budget}"
                return "NOT_IMPLEMENTED", f"budget unchanged at ${current_budget}"
            return "UNVERIFIABLE", "prior/current budget not extractable — check manually"
        if a.entity_type == "campaign":
            c = campaigns.get(name)
            if not c:
                return "UNVERIFIABLE", f"campaign '{name}' not found"
            return "UNVERIFIABLE", f"campaign budget verification requires historical snapshot"
        return "UNVERIFIABLE", "entity type unclear for SCALE/ADJUST"

    # NEGATIVE — expect keyword added to negative list
    if a.action == "NEGATIVE":
        if a.entity_type == "keyword" and name:
            k = keywords.get(name)
            if k and k.get("status", "").upper() == "NEGATIVE":
                return "IMPLEMENTED", "keyword is now negative"
            if k:
                return "NOT_IMPLEMENTED", f"keyword status is {k.get('status', 'unknown')} — not negative"
            return "UNVERIFIABLE", f"keyword '{name}' not in current state"
        return "UNVERIFIABLE", "negative keyword target not extracted"

    # TEST — tests don't always resolve in one cycle; report as informational
    if a.action == "TEST":
        return "UNVERIFIABLE", "tests require a full cycle — re-check once sample size met"

    # WINNER/NO_WINNER/NEED_MORE_DATA are outcome tags — not actions to implement
    if a.action in ("WINNER", "NO_WINNER", "NEED_MORE_DATA"):
        return "UNVERIFIABLE", f"[{a.action}] is an outcome tag, not an action"

    return "UNVERIFIABLE", f"unhandled action type: {a.action}"


def _extract_number_from_details(details: str, kind: str = "prior") -> Optional[float]:
    """Pull a dollar amount from a details string like 'raise $20 → $35'."""
    # Match two $N values separated by an arrow — take the first for 'prior', second for 'current'
    m = re.search(r"\$?(\d+(?:\.\d+)?)\s*(?:→|->|to)\s*\$?(\d+(?:\.\d+)?)", details)
    if m:
        return float(m.group(1)) if kind == "prior" else float(m.group(2))
    return None


# ── Report formatter ─────────────────────────────────────────────────────────

def format_audit(entries: list[AuditEntry]) -> str:
    """Render a markdown table of audit results for inclusion in the new report."""
    if not entries:
        return "_No prior actions found in previous report._"
    lines = [
        "| # | Action | Entity | Status | Note |",
        "|---|--------|--------|--------|------|",
    ]
    icon = {
        "IMPLEMENTED": "✅",
        "NOT_IMPLEMENTED": "❌",
        "PARTIAL": "🟡",
        "UNVERIFIABLE": "⚪",
    }
    for i, e in enumerate(entries, 1):
        name = e.entity_name or "—"
        lines.append(
            f"| {i} | {e.action} | {e.entity_type}: {name} | "
            f"{icon.get(e.status, '')} {e.status} | {e.note} |"
        )
    # Summary
    implemented = sum(1 for e in entries if e.status == "IMPLEMENTED")
    not_impl = sum(1 for e in entries if e.status == "NOT_IMPLEMENTED")
    unverif = sum(1 for e in entries if e.status == "UNVERIFIABLE")
    lines.append("")
    lines.append(
        f"**Implementation rate:** {implemented}/{len(entries)} actions completed "
        f"({not_impl} not implemented, {unverif} unverifiable)."
    )
    return "\n".join(lines)


# ── CLI ──────────────────────────────────────────────────────────────────────

def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__.strip())
        return 1
    report_path = sys.argv[1]
    state_path = sys.argv[2] if len(sys.argv) > 2 else None

    with open(report_path, "r", encoding="utf-8") as f:
        report_text = f.read()
    actions = extract_actions(report_text)

    state = {}
    if state_path:
        with open(state_path, "r", encoding="utf-8") as f:
            state = json.load(f)

    audit = audit_implementation(actions, state)
    print(f"Extracted {len(actions)} prior action(s) from {report_path}")
    print()
    print(format_audit(audit))
    return 0


if __name__ == "__main__":
    sys.exit(main())
