#!/usr/bin/env python3
"""
Output Validator for Business Analysis Skill

Checks that all required deliverables are present and meet quality standards.

Usage:
    python validate_output.py <client_folder_path>

Example:
    python validate_output.py "/path/to/Desktop/Thrive Retreat/Thrive Retreat"
"""

import sys
import json
import re
from pathlib import Path


def check_folder_structure(client_dir):
    """Check client folder has required directories."""
    required = ["sources", "wiki", "deliverables"]
    missing = [d for d in required if not (client_dir / d).is_dir()]
    if missing:
        return "CRITICAL", f"Missing directories: {', '.join(missing)}"
    return "PASS", "All required directories present"


def check_wiki_pages(client_dir):
    """Check base wiki pages exist."""
    wiki_dir = client_dir / "wiki"
    required_pages = ["business.md", "brand-identity.md", "digital-presence.md", "offerings.md", "index.md", "log.md"]
    missing = [p for p in required_pages if not (wiki_dir / p).exists()]
    if missing:
        return "CRITICAL", f"Missing wiki pages: {', '.join(missing)}"
    return "PASS", f"All {len(required_pages)} base wiki pages present"


def check_brand_config(client_dir):
    """Check brand-config.json exists and has required fields."""
    config_path = client_dir / "deliverables" / "brand-config.json"
    if not config_path.exists():
        return "CRITICAL", "brand-config.json not found in deliverables/"

    try:
        config = json.loads(config_path.read_text())
    except json.JSONDecodeError:
        return "CRITICAL", "brand-config.json is not valid JSON"

    # Check for color data
    colors = config.get("colors", {})
    if not colors:
        return "WARNING", "brand-config.json has no colors extracted"

    if "primaryAccent" not in colors:
        return "WARNING", "brand-config.json missing primaryAccent color"

    return "PASS", f"brand-config.json valid with {len(colors)} colors"


def check_wiki_config(client_dir):
    """Check wiki-config.json exists and is valid."""
    config_path = client_dir / "wiki-config.json"
    if not config_path.exists():
        return "CRITICAL", "wiki-config.json not found"

    try:
        config = json.loads(config_path.read_text())
    except json.JSONDecodeError:
        return "CRITICAL", "wiki-config.json is not valid JSON"

    required_fields = ["business_name", "created", "last_updated", "pages"]
    missing = [f for f in required_fields if f not in config]
    if missing:
        return "WARNING", f"wiki-config.json missing fields: {', '.join(missing)}"

    return "PASS", "wiki-config.json valid"


def check_source_labels(client_dir):
    """Check wiki pages have EXTRACTED/INFERRED labels."""
    wiki_dir = client_dir / "wiki"
    pages_to_check = ["business.md", "brand-identity.md", "digital-presence.md", "offerings.md"]
    labeled_count = 0
    total_pages = 0

    for page in pages_to_check:
        path = wiki_dir / page
        if not path.exists():
            continue
        content = path.read_text()
        total_pages += 1
        # Skip empty template pages
        if "No data ingested yet" in content:
            continue
        if re.search(r'\[EXTRACTED\]|\[INFERRED\]', content):
            labeled_count += 1

    if total_pages == 0:
        return "CRITICAL", "No wiki pages found to check"

    # Only flag if pages have content but no labels
    populated = total_pages - sum(
        1 for p in pages_to_check
        if (wiki_dir / p).exists() and "No data ingested yet" in (wiki_dir / p).read_text()
    )

    if populated > 0 and labeled_count == 0:
        return "CRITICAL", "Populated wiki pages have no [EXTRACTED] or [INFERRED] labels"

    if populated > 0 and labeled_count < populated:
        return "WARNING", f"Only {labeled_count}/{populated} populated pages have source labels"

    return "PASS", f"Source labels present in {labeled_count} populated pages"


def check_blank_fields(client_dir):
    """Check that BLANK fields have explanations."""
    wiki_dir = client_dir / "wiki"
    issues = []

    for md_file in wiki_dir.glob("*.md"):
        if md_file.name in ("index.md", "log.md"):
            continue
        content = md_file.read_text()
        # Find BLANK markers without explanations
        blanks = re.findall(r'BLANK(?!\s*[—\-–:])', content)
        if blanks:
            issues.append(f"{md_file.name}: {len(blanks)} BLANK field(s) without explanation")

    if issues:
        return "WARNING", "; ".join(issues)
    return "PASS", "All BLANK fields have explanations"


def check_offerings_documented(client_dir):
    """Check offerings.md has at least one offering section."""
    offerings_path = client_dir / "wiki" / "offerings.md"
    if not offerings_path.exists():
        return "CRITICAL", "offerings.md not found"

    content = offerings_path.read_text()
    if "No data ingested yet" in content:
        return "WARNING", "offerings.md is still empty template"

    # Count H2 sections (each offering should be an H2)
    offerings = re.findall(r'^## .+', content, re.MULTILINE)
    # Exclude standard section headers
    standard = {"## Key Findings", "## Details", "## Gaps & Unknowns", "## Marketing Implications", "## Change History"}
    actual_offerings = [o for o in offerings if o.strip() not in standard]

    if len(actual_offerings) == 0:
        return "WARNING", "No offerings documented in offerings.md"

    return "PASS", f"{len(actual_offerings)} offering(s) documented"


def check_digital_presence(client_dir):
    """Check digital-presence.md has been populated."""
    dp_path = client_dir / "wiki" / "digital-presence.md"
    if not dp_path.exists():
        return "CRITICAL", "digital-presence.md not found"

    content = dp_path.read_text()
    if "No data ingested yet" in content:
        return "WARNING", "digital-presence.md is still empty template"

    # Check for key sections
    key_terms = ["website", "social", "google business"]
    found = sum(1 for term in key_terms if term.lower() in content.lower())
    if found < 2:
        return "WARNING", f"digital-presence.md only covers {found}/3 key areas (website, social, Google Business)"

    return "PASS", "Digital presence audit populated"


def check_prioritization(client_dir):
    """Check offering prioritization analysis exists."""
    business_path = client_dir / "wiki" / "business.md"
    if not business_path.exists():
        return "WARNING", "business.md not found"

    content = business_path.read_text()
    if "prioritization" in content.lower() or "priority" in content.lower():
        return "PASS", "Offering prioritization analysis present"

    return "WARNING", "No offering prioritization analysis found in business.md"


def check_downstream_flag(client_dir):
    """Check log.md has a downstream connection flag."""
    log_path = client_dir / "wiki" / "log.md"
    if not log_path.exists():
        return "WARNING", "log.md not found"

    content = log_path.read_text()
    if "ready for" in content.lower() or "market-research" in content.lower() or "downstream" in content.lower():
        return "PASS", "Downstream skill connection flagged"

    return "WARNING", "No downstream skill connection flagged in log.md"


def check_index_updated(client_dir):
    """Check index.md has been updated from template."""
    index_path = client_dir / "wiki" / "index.md"
    if not index_path.exists():
        return "CRITICAL", "index.md not found"

    content = index_path.read_text()
    if "Sources ingested: 0" in content:
        return "WARNING", "index.md still shows 0 sources ingested"

    return "PASS", "index.md updated with source count"


def main():
    if len(sys.argv) < 2:
        print("Usage: python validate_output.py <client_folder_path>")
        sys.exit(1)

    client_dir = Path(sys.argv[1])
    if not client_dir.is_dir():
        print(f"ERROR: {client_dir} is not a directory")
        sys.exit(1)

    checks = [
        ("Folder Structure", check_folder_structure),
        ("Wiki Pages", check_wiki_pages),
        ("Brand Config", check_brand_config),
        ("Wiki Config", check_wiki_config),
        ("Source Labels", check_source_labels),
        ("BLANK Fields", check_blank_fields),
        ("Offerings Documented", check_offerings_documented),
        ("Digital Presence", check_digital_presence),
        ("Offering Prioritization", check_prioritization),
        ("Downstream Flag", check_downstream_flag),
        ("Index Updated", check_index_updated),
    ]

    print(f"Business Analysis Validation: {client_dir.name}")
    print("=" * 60)

    results = {"PASS": 0, "WARNING": 0, "CRITICAL": 0}

    for name, check_fn in checks:
        status, message = check_fn(client_dir)
        results[status] += 1
        icon = {"PASS": "✓", "WARNING": "⚠", "CRITICAL": "✗"}[status]
        print(f"  {icon} [{status}] {name}: {message}")

    print("=" * 60)
    print(f"Results: {results['PASS']} passed, {results['WARNING']} warnings, {results['CRITICAL']} critical")

    if results["CRITICAL"] > 0:
        print("\nACTION REQUIRED: Fix critical failures before delivery.")
        sys.exit(1)
    elif results["WARNING"] > 0:
        print("\nWARNINGS present — review before delivery.")
        sys.exit(0)
    else:
        print("\nAll checks passed.")
        sys.exit(0)


if __name__ == "__main__":
    main()
