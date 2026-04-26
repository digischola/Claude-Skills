#!/usr/bin/env python3
"""
campaign-setup validator.

Validates generated bulk-import CSVs for Google Ads Editor and Meta Ads Manager.

CRITICAL failures block delivery. WARNING items surface in the pre-launch checklist.

Checks:
- Character limits per platform
- Schema column names present
- Placeholder tokens (<REPLACE_ME_...>) logged as WARNING (must be in checklist) not CRITICAL
- Orphan references (ad group → non-existent campaign)
- Duplicate entity names within same parent
- URL format (must be HTTPS, must resolve in sanity scan)
- Required fields populated
- Import order consistency

Usage:
  python scripts/validate_output.py <deliverables_root>

Example:
  python scripts/validate_output.py "/Users/me/Desktop/Retreat House/Retreat House/deliverables/campaign-setup"
"""

from __future__ import annotations

import csv
import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

# ---------- result collection ----------

results: list[tuple[str, str, str]] = []  # (severity, area, message)

def log(severity: str, area: str, message: str) -> None:
    results.append((severity, area, message))

# ---------- character limits ----------

GOOGLE_LIMITS = {
    "Headline": 30,
    "Description": 90,
    "Path 1": 15,
    "Path 2": 15,
    "Sitelink Text": 25,
    "Sitelink Description 1": 35,
    "Sitelink Description 2": 35,
    "Callout Text": 25,
    "Value": 25,  # structured snippet values
}

# Google Ads Personalized Advertising Restrictions — health / financial / employment / housing
# categories that auto-reject at Editor import. See references/restricted-keyword-categories.md
# for the full pattern catalog and reframing recipes. Triggered by 2026-04-26 Living Flow case
# (`yoga for back pain sydney` rejected at import as "Health category not accepted").
# Format: (compiled_pattern, category_label, suggested_reframing)
RESTRICTED_KEYWORD_PATTERNS = [
    # Health conditions (yoga / wellness / fitness / therapy)
    (re.compile(r'\byoga\s+for\s+(back|neck|joint|hip|shoulder)\s+pain\b'),
     'health-condition (musculoskeletal pain)',
     '"yoga for desk workers" / "mobility yoga" / "stretching yoga"'),
    (re.compile(r'\byoga\s+for\s+(anxiety|depression|stress|insomnia|adhd|ptsd|autism)\b'),
     'mental-health condition',
     '"calming yoga" / "restorative yoga" / "evening yoga"'),
    (re.compile(r'\byoga\s+for\s+(arthritis|fibromyalgia|sciatica|migraines?|chronic\s+pain)\b'),
     'health condition (chronic)',
     '"gentle yoga for seniors" / "low-impact yoga" / "slow flow yoga"'),
    (re.compile(r'\byoga\s+for\s+(weight\s+loss|fertility)\b'),
     'weight/reproductive health',
     '"yoga for fitness" / "power yoga" / DROP if reproductive'),
    (re.compile(r'\b(weight\s+loss|lose\s+\d+\s*(?:pounds|kg|lbs)|belly\s+fat)\b'),
     'weight-loss claim',
     '"fitness program" / "body transformation" / "core workout"'),
    (re.compile(r'\btherapy\s+for\s+(depression|ptsd|addiction|eating\s+disorder|anxiety)\b'),
     'mental-health diagnosis',
     'DROP — diagnosis-targeted; reframe as "online therapist" / "talk therapy"'),
    # Financial / employment / housing (Personalized Ads policy)
    (re.compile(r'\b(bad\s+credit|debt\s+consolidation\s+poor\s+credit|low.?income|section\s+8|unemployed\s+jobs)\b'),
     'financial / employment / housing status',
     'DROP — protected attribute targeting'),
    (re.compile(r'\b(no\s+degree|dropout|high\s+school\s+dropout)\s+(job|career|loan)\b'),
     'education-attainment status',
     'DROP — protected attribute targeting'),
]

META_LIMITS = {
    # Body 125 = soft truncation warning (Meta max ~500 — copy survives truncation is OK)
    # Title 40 / Link Description 27 = hard renderable limits, CRITICAL if exceeded
    "Body": 125,
    "Title": 40,
    "Link Description": 27,
    "Card Headline": 27,
    "Card Description": 27,
}
# Fields where exceeding the limit is a soft-truncation WARNING, not CRITICAL
META_SOFT_LIMITS = {"Body"}

PLACEHOLDER_RE = re.compile(r"<REPLACE_ME[_A-Z0-9]*>")
URL_RE = re.compile(r"^https://[^\s]+$")

# ---------- helpers ----------

def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return [dict(row) for row in reader]

def check_char_limit(value: str, limit: int, context: str, area: str, soft: bool = False) -> None:
    if value is None or value == "":
        return
    if PLACEHOLDER_RE.search(value):
        return  # placeholders handled separately
    if len(value) > limit:
        severity = "WARNING" if soft else "CRITICAL"
        note = " (soft — will truncate on delivery)" if soft else ""
        log(severity, area, f"{context}: {len(value)} chars (max {limit}){note} — '{value[:60]}...'")

def scan_placeholders(rows: list[dict], area: str, csv_name: str) -> int:
    count = 0
    for idx, row in enumerate(rows, start=2):  # header is row 1
        for col, val in row.items():
            if val and PLACEHOLDER_RE.search(str(val)):
                count += 1
                log("WARNING", area, f"{csv_name} row {idx} col '{col}': placeholder {PLACEHOLDER_RE.search(str(val)).group(0)} must be resolved before launch")
    return count

def check_required(row: dict, required_cols: list[str], row_idx: int, area: str, csv_name: str) -> None:
    for col in required_cols:
        val = row.get(col, "")
        if val is None or str(val).strip() == "":
            log("CRITICAL", area, f"{csv_name} row {row_idx}: required column '{col}' is empty")

def check_schema(rows: list[dict], expected_cols: set[str], area: str, csv_name: str) -> None:
    if not rows:
        return
    actual = set(rows[0].keys())
    missing = expected_cols - actual
    if missing:
        log("CRITICAL", area, f"{csv_name}: missing expected columns {sorted(missing)}")

def check_dupes(rows: list[dict], key_cols: list[str], area: str, csv_name: str) -> None:
    keys = [tuple((row.get(c) or "").strip() for c in key_cols) for row in rows]
    counter = Counter(keys)
    for key, count in counter.items():
        if count > 1 and all(part for part in key):
            log("CRITICAL", area, f"{csv_name}: duplicate {key_cols}={key} appears {count} times")

def check_url(value: str, row_idx: int, col: str, area: str, csv_name: str) -> None:
    if not value or PLACEHOLDER_RE.search(value):
        return
    if not URL_RE.match(value):
        log("CRITICAL", area, f"{csv_name} row {row_idx} col '{col}': URL '{value}' is not HTTPS or malformed")

# ---------- Google Ads validators ----------

def validate_google(root: Path) -> None:
    area = "GOOGLE"
    google_dir = root / "google-ads"
    if not google_dir.exists():
        log("INFO", area, "google-ads/ directory not present — skipping Google validation")
        return

    campaigns = read_csv(google_dir / "01-campaigns.csv")
    ad_groups = read_csv(google_dir / "02-ad-groups.csv")
    keywords = read_csv(google_dir / "03-keywords.csv")
    rsas = read_csv(google_dir / "04-responsive-search-ads.csv")
    sitelinks = read_csv(google_dir / "05-sitelink-extensions.csv")
    callouts = read_csv(google_dir / "06-callout-extensions.csv")
    snippets = read_csv(google_dir / "07-structured-snippets.csv")
    negatives = read_csv(google_dir / "08-negative-keywords.csv")

    # ----- campaigns -----
    check_schema(campaigns, {"Campaign", "Campaign Type", "Campaign Status", "Budget", "Bid Strategy Type"}, area, "01-campaigns.csv")
    check_dupes(campaigns, ["Campaign"], area, "01-campaigns.csv")
    for i, row in enumerate(campaigns, start=2):
        check_required(row, ["Campaign", "Campaign Type", "Campaign Status", "Budget", "Bid Strategy Type"], i, area, "01-campaigns.csv")
        budget = row.get("Budget", "")
        if budget and not PLACEHOLDER_RE.search(budget):
            try:
                if float(budget) <= 0:
                    log("CRITICAL", area, f"01-campaigns.csv row {i}: Budget must be > 0")
            except ValueError:
                log("CRITICAL", area, f"01-campaigns.csv row {i}: Budget '{budget}' is not a valid decimal")
        if "$" in budget or "AUD" in budget.upper() or "USD" in budget.upper():
            log("CRITICAL", area, f"01-campaigns.csv row {i}: Budget must not contain currency symbols")

    campaign_names = {row.get("Campaign", "") for row in campaigns}

    # ----- ad groups -----
    check_schema(ad_groups, {"Campaign", "Ad Group", "Ad Group Status"}, area, "02-ad-groups.csv")
    check_dupes(ad_groups, ["Campaign", "Ad Group"], area, "02-ad-groups.csv")
    for i, row in enumerate(ad_groups, start=2):
        check_required(row, ["Campaign", "Ad Group", "Ad Group Status"], i, area, "02-ad-groups.csv")
        c = row.get("Campaign", "")
        if c and c not in campaign_names and not PLACEHOLDER_RE.search(c):
            log("CRITICAL", area, f"02-ad-groups.csv row {i}: Campaign '{c}' not found in 01-campaigns.csv")

    ad_group_keys = {(row.get("Campaign", ""), row.get("Ad Group", "")) for row in ad_groups}

    # ----- keywords -----
    check_schema(keywords, {"Campaign", "Ad Group", "Keyword", "Criterion Type", "Status"}, area, "03-keywords.csv")
    for i, row in enumerate(keywords, start=2):
        check_required(row, ["Campaign", "Ad Group", "Keyword", "Criterion Type", "Status"], i, area, "03-keywords.csv")
        key = (row.get("Campaign", ""), row.get("Ad Group", ""))
        if all(key) and key not in ad_group_keys:
            log("CRITICAL", area, f"03-keywords.csv row {i}: Ad group '{key[1]}' not found under campaign '{key[0]}'")
        ct = row.get("Criterion Type", "")
        if ct and ct not in {"Exact", "Phrase", "Broad", "Negative Exact", "Negative Phrase", "Negative Broad"}:
            log("CRITICAL", area, f"03-keywords.csv row {i}: invalid Criterion Type '{ct}'")
        # Restricted-keyword pre-filter (Personalized Advertising Restrictions).
        # Auto-rejected at Editor import for health/financial/employment/housing categories.
        # See references/restricted-keyword-categories.md for full pattern list + reframing recipes.
        # Only applied to positive keywords; negatives are exempt (they SHOULD reference these terms).
        kw_text = (row.get("Keyword", "") or "").lower()
        if kw_text and not ct.startswith("Negative"):
            for pattern, label, reframe in RESTRICTED_KEYWORD_PATTERNS:
                if re.search(pattern, kw_text):
                    log("CRITICAL", area,
                        f"03-keywords.csv row {i}: keyword '{kw_text}' matches restricted category "
                        f"({label}) — Google's Personalized Advertising Restrictions auto-reject this at import. "
                        f"Suggested reframe: {reframe}. See references/restricted-keyword-categories.md.")
                    break

    # ----- RSAs -----
    check_schema(rsas, {"Campaign", "Ad Group", "Ad Type", "Ad Status", "Final URL", "Headline 1", "Description 1", "Description 2"}, area, "04-responsive-search-ads.csv")
    ad_groups_with_rsa = set()
    for i, row in enumerate(rsas, start=2):
        check_required(row, ["Campaign", "Ad Group", "Final URL", "Headline 1", "Description 1", "Description 2"], i, area, "04-responsive-search-ads.csv")
        ad_groups_with_rsa.add((row.get("Campaign", ""), row.get("Ad Group", "")))
        check_url(row.get("Final URL", ""), i, "Final URL", area, "04-responsive-search-ads.csv")
        for h in range(1, 16):
            val = row.get(f"Headline {h}", "")
            check_char_limit(val, GOOGLE_LIMITS["Headline"], f"Headline {h} row {i}", area)
        for d in range(1, 5):
            val = row.get(f"Description {d}", "")
            check_char_limit(val, GOOGLE_LIMITS["Description"], f"Description {d} row {i}", area)
        check_char_limit(row.get("Path 1", ""), GOOGLE_LIMITS["Path 1"], f"Path 1 row {i}", area)
        check_char_limit(row.get("Path 2", ""), GOOGLE_LIMITS["Path 2"], f"Path 2 row {i}", area)
        # headline count
        non_empty_headlines = sum(1 for h in range(1, 16) if (row.get(f"Headline {h}") or "").strip())
        if non_empty_headlines < 3:
            log("CRITICAL", area, f"04-responsive-search-ads.csv row {i}: needs at least 3 headlines, has {non_empty_headlines}")
        elif non_empty_headlines < 10:
            log("WARNING", area, f"04-responsive-search-ads.csv row {i}: only {non_empty_headlines} headlines — Google recommends 10+")
        # pinned headlines to position 1
        pinned_to_1 = sum(1 for h in range(1, 16) if str(row.get(f"Headline {h} position", "")).strip() == "1")
        if pinned_to_1 > 2:
            log("WARNING", area, f"04-responsive-search-ads.csv row {i}: {pinned_to_1} headlines pinned to position 1 (max recommended: 2)")

    # ad groups missing RSAs
    for key in ad_group_keys:
        if key not in ad_groups_with_rsa:
            log("CRITICAL", area, f"Ad group '{key[1]}' (campaign '{key[0]}') has no RSA — each ad group requires at least 1")

    # ----- extensions -----
    if sitelinks:
        check_schema(sitelinks, {"Asset Type", "Status", "Sitelink Text", "Final URL"}, area, "05-sitelink-extensions.csv")
        per_campaign = Counter()
        for i, row in enumerate(sitelinks, start=2):
            check_char_limit(row.get("Sitelink Text", ""), GOOGLE_LIMITS["Sitelink Text"], f"Sitelink Text row {i}", area)
            check_char_limit(row.get("Description 1", ""), GOOGLE_LIMITS["Sitelink Description 1"], f"Sitelink Desc 1 row {i}", area)
            check_char_limit(row.get("Description 2", ""), GOOGLE_LIMITS["Sitelink Description 2"], f"Sitelink Desc 2 row {i}", area)
            check_url(row.get("Final URL", ""), i, "Final URL", area, "05-sitelink-extensions.csv")
            per_campaign[row.get("Campaign", "") or "<account-level>"] += 1
        for campaign, count in per_campaign.items():
            if count < 4:
                log("WARNING", area, f"Sitelinks: campaign '{campaign}' has only {count} sitelinks (recommended minimum: 4)")

    if callouts:
        check_schema(callouts, {"Asset Type", "Status", "Callout Text"}, area, "06-callout-extensions.csv")
        per_campaign = Counter()
        for i, row in enumerate(callouts, start=2):
            check_char_limit(row.get("Callout Text", ""), GOOGLE_LIMITS["Callout Text"], f"Callout row {i}", area)
            per_campaign[row.get("Campaign", "") or "<account-level>"] += 1
        for campaign, count in per_campaign.items():
            if count < 4:
                log("WARNING", area, f"Callouts: campaign '{campaign}' has only {count} callouts (recommended minimum: 4)")

    if snippets:
        # 2026-04-26 fix: Editor's parser rejects per-column Value 1/Value 2/... format
        # with "There are too few values for a structured snippet" — even when 3+ values
        # are populated. Required format: single `Snippet Values` column with `;`-delimited
        # values. See references/google-ads-editor-schema.md §7.
        valid_headers = {"Amenities", "Brands", "Courses", "Degree Programs", "Destinations", "Featured Hotels", "Insurance Coverage", "Models", "Neighborhoods", "Service Catalog", "Services", "Shows", "Styles", "Types"}
        snippet_columns = set(snippets[0].keys()) if snippets else set()
        per_column_format = any(c.startswith("Value ") and c[6:].strip().isdigit() for c in snippet_columns)
        semicolon_format = "Snippet Values" in snippet_columns
        if per_column_format and not semicolon_format:
            log("CRITICAL", area, "07-structured-snippets.csv uses per-column Value 1/Value 2/... format — REJECTED by Ads Editor parser. Required: single 'Snippet Values' column, semicolon-delimited (`Vinyasa;Yin;Beginners`). See references/google-ads-editor-schema.md §7.")
        if semicolon_format:
            check_schema(snippets, {"Asset Type", "Status", "Header", "Snippet Values"}, area, "07-structured-snippets.csv")
            for i, row in enumerate(snippets, start=2):
                if row.get("Header", "") and row.get("Header", "") not in valid_headers:
                    log("CRITICAL", area, f"07-structured-snippets.csv row {i}: Header '{row.get('Header')}' not in Google's fixed header list")
                raw = row.get("Snippet Values", "") or ""
                values = [v.strip() for v in raw.split(";") if v.strip()]
                if len(values) < 3:
                    log("CRITICAL", area, f"07-structured-snippets.csv row {i}: 'Snippet Values' has only {len(values)} value(s) — minimum 3 required. Use `;` to delimit (e.g. `Vinyasa;Yin;Beginners`)")
                for idx, v in enumerate(values, start=1):
                    check_char_limit(v, GOOGLE_LIMITS["Value"], f"Snippet value {idx} row {i}", area)
        elif per_column_format:
            # Schema-level critical already logged above. Don't double-fail per-row.
            for i, row in enumerate(snippets, start=2):
                if row.get("Header", "") and row.get("Header", "") not in valid_headers:
                    log("CRITICAL", area, f"07-structured-snippets.csv row {i}: Header '{row.get('Header')}' not in Google's fixed header list")

    if negatives:
        check_schema(negatives, {"Keyword", "Criterion Type"}, area, "08-negative-keywords.csv")
        for i, row in enumerate(negatives, start=2):
            ct = row.get("Criterion Type", "")
            if ct and ct not in {"Negative Exact", "Negative Phrase", "Negative Broad"}:
                log("CRITICAL", area, f"08-negative-keywords.csv row {i}: Criterion Type must be a Negative variant, got '{ct}'")

    # ----- placeholder scan -----
    total_placeholders = 0
    for name, rows in [
        ("01-campaigns.csv", campaigns),
        ("02-ad-groups.csv", ad_groups),
        ("03-keywords.csv", keywords),
        ("04-responsive-search-ads.csv", rsas),
        ("05-sitelink-extensions.csv", sitelinks),
        ("06-callout-extensions.csv", callouts),
        ("07-structured-snippets.csv", snippets),
        ("08-negative-keywords.csv", negatives),
    ]:
        total_placeholders += scan_placeholders(rows, area, name)

    if total_placeholders > 0:
        log("INFO", area, f"Total {total_placeholders} placeholder tokens in Google CSVs — confirm all are listed in pre-launch-checklist.md Section 0")

# ---------- Meta Ads validators ----------

def validate_meta(root: Path) -> None:
    area = "META"
    meta_dir = root / "meta-ads"
    if not meta_dir.exists():
        log("INFO", area, "meta-ads/ directory not present — skipping Meta validation")
        return

    bulk_path = meta_dir / "meta-bulk-import.csv"
    rows = read_csv(bulk_path)

    # Meta Objective → valid ad-set Optimization Goals (Marketing API 2024+ ODAX).
    # Mismatches are silently rejected at import time with vague errors, so catching them
    # here saves launch-day headaches.
    OBJECTIVE_TO_VALID_GOALS = {
        "OUTCOME_AWARENESS": {"REACH", "BRAND_AWARENESS", "IMPRESSIONS", "AD_RECALL_LIFT", "THRUPLAY"},
        "OUTCOME_TRAFFIC": {"LINK_CLICKS", "LANDING_PAGE_VIEWS", "IMPRESSIONS", "REACH", "QUALITY_CALL"},
        "OUTCOME_ENGAGEMENT": {"POST_ENGAGEMENT", "PAGE_LIKES", "EVENT_RESPONSES", "THRUPLAY",
                                "VIDEO_VIEWS", "REPLIES", "CONVERSATIONS", "QUALITY_CALL"},
        "OUTCOME_LEADS": {"LEAD_GENERATION", "QUALITY_LEAD", "OFFSITE_CONVERSIONS",
                           "LANDING_PAGE_VIEWS", "CONVERSATIONS", "SUBSCRIBERS", "QUALITY_CALL"},
        "OUTCOME_APP_PROMOTION": {"APP_INSTALLS", "OFFSITE_CONVERSIONS", "LINK_CLICKS", "VALUE"},
        "OUTCOME_SALES": {"OFFSITE_CONVERSIONS", "VALUE", "LANDING_PAGE_VIEWS", "CONVERSATIONS",
                           "LINK_CLICKS"},
    }

    if not rows:
        log("WARNING", area, "meta-bulk-import.csv is empty or missing")
    else:
        # First pass: build Campaign Name → Objective map from CAMPAIGN-level rows
        campaign_objectives = {}
        for row in rows:
            level = (row.get("Level") or "").strip().upper()
            if level == "CAMPAIGN":
                name = (row.get("Campaign Name") or "").strip()
                obj = (row.get("Objective") or "").strip().upper()
                if name and obj:
                    campaign_objectives[name] = obj

        # Distinguish by Level column
        for i, row in enumerate(rows, start=2):
            level = (row.get("Level") or "").strip().upper()
            # ── AD_SET-level Optimization Goal enum check ──
            if level == "AD_SET":
                goal = (row.get("Optimization Goal") or "").strip().upper()
                parent_camp = (row.get("Campaign Name") or "").strip()
                parent_obj = campaign_objectives.get(parent_camp, "").upper()
                if goal and parent_obj:
                    valid_goals = OBJECTIVE_TO_VALID_GOALS.get(parent_obj)
                    if valid_goals is not None and goal not in valid_goals:
                        log("CRITICAL", area,
                            f"meta-bulk-import.csv row {i}: Optimization Goal '{goal}' invalid for "
                            f"Objective '{parent_obj}' (parent campaign '{parent_camp}'). "
                            f"Valid goals: {sorted(valid_goals)}")
                    elif valid_goals is None:
                        log("WARNING", area,
                            f"meta-bulk-import.csv row {i}: unrecognized Objective '{parent_obj}' — "
                            f"cannot validate Optimization Goal enum")
            if level == "AD" or row.get("Ad Name"):
                check_char_limit(row.get("Body", ""), META_LIMITS["Body"], f"Body row {i}", area, soft=True)
                check_char_limit(row.get("Title", ""), META_LIMITS["Title"], f"Title row {i}", area)
                check_char_limit(row.get("Link Description", ""), META_LIMITS["Link Description"], f"Link Description row {i}", area)
                check_url(row.get("Link", ""), i, "Link", area, "meta-bulk-import.csv")
                # required fields at ad level
                for col in ["Ad Name", "Ad Status", "Creative Type", "Page ID", "Body", "Link", "Call to Action"]:
                    val = row.get(col, "")
                    if val is None or str(val).strip() == "":
                        log("CRITICAL", area, f"meta-bulk-import.csv row {i} (Ad): required column '{col}' empty")
                # creative hash/ID presence
                ctype = (row.get("Creative Type") or "").strip().upper()
                if ctype == "SINGLE_IMAGE" and not (row.get("Image Hash") or "").strip():
                    log("CRITICAL", area, f"meta-bulk-import.csv row {i}: SINGLE_IMAGE ad requires Image Hash")
                if ctype == "SINGLE_VIDEO" and not (row.get("Video ID") or "").strip():
                    log("CRITICAL", area, f"meta-bulk-import.csv row {i}: SINGLE_VIDEO ad requires Video ID")
            # status enum
            status = (row.get("Ad Status") or row.get("Ad Set Status") or row.get("Campaign Status") or "").upper()
            if status and status not in {"ACTIVE", "PAUSED", "DELETED", "ARCHIVED", ""}:
                log("CRITICAL", area, f"meta-bulk-import.csv row {i}: invalid status '{status}'")

        scan_placeholders(rows, area, "meta-bulk-import.csv")

    # creative manifest check
    manifest = meta_dir / "creative-upload-manifest.md"
    if not manifest.exists():
        log("WARNING", area, "creative-upload-manifest.md missing — Meta bulk import requires pre-uploaded assets")
    else:
        content = manifest.read_text(encoding="utf-8")
        pending = content.count("<PENDING_UPLOAD>")
        if pending > 0:
            log("WARNING", area, f"creative-upload-manifest.md: {pending} assets still marked <PENDING_UPLOAD> — upload to Asset Library and replace hashes before import")

    blueprint = meta_dir / "campaign-blueprint.md"
    if not blueprint.exists():
        log("WARNING", area, "campaign-blueprint.md missing — required as manual-build fallback when bulk import fails")

# ---------- checklist + runbook ----------

def validate_checklist_and_runbook(root: Path) -> None:
    area = "CHECKLIST"
    checklist = root / "pre-launch-checklist.md"
    if not checklist.exists():
        log("CRITICAL", area, "pre-launch-checklist.md missing")
    else:
        content = checklist.read_text(encoding="utf-8")
        if "placeholder" not in content.lower() and "<REPLACE_ME" not in content:
            log("WARNING", area, "pre-launch-checklist.md: missing Section 0 (Placeholder Tokens) — placeholders may not be tracked")
        if "Sign-Off" not in content and "sign-off" not in content.lower():
            log("WARNING", area, "pre-launch-checklist.md: missing Final Sign-Off section")

    runbook = root / "launch-runbook.md"
    if not runbook.exists():
        log("CRITICAL", area, "launch-runbook.md missing")
    else:
        content = runbook.read_text(encoding="utf-8")
        required_phases = ["Pre-Upload Prep", "Google Ads Editor", "Meta Ads Manager", "Post-Launch"]
        for phase in required_phases:
            if phase.lower() not in content.lower():
                log("WARNING", area, f"launch-runbook.md: phase '{phase}' section appears missing")

# ---------- main ----------

def main():
    if len(sys.argv) < 2:
        print("Usage: python validate_output.py <deliverables_campaign_setup_root>")
        sys.exit(2)
    root = Path(sys.argv[1]).expanduser().resolve()
    if not root.exists():
        print(f"ERROR: {root} does not exist")
        sys.exit(2)

    validate_google(root)
    validate_meta(root)
    validate_checklist_and_runbook(root)

    # summary
    severity_counts = Counter(r[0] for r in results)
    critical = severity_counts.get("CRITICAL", 0)
    warning = severity_counts.get("WARNING", 0)
    info = severity_counts.get("INFO", 0)

    print(f"\n=== campaign-setup validator ===")
    print(f"Root: {root}")
    print(f"CRITICAL: {critical}   WARNING: {warning}   INFO: {info}\n")

    for sev in ("CRITICAL", "WARNING", "INFO"):
        sev_results = [r for r in results if r[0] == sev]
        if not sev_results:
            continue
        print(f"--- {sev} ---")
        for _, area, msg in sev_results:
            print(f"  [{area}] {msg}")
        print()

    sys.exit(1 if critical > 0 else 0)

if __name__ == "__main__":
    main()
