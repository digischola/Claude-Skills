#!/usr/bin/env python3
"""
Wiki Content Quality Linter for Business Analysis Skill

Goes deeper than validate_output.py — checks content quality, not just structure.
Validates source labels, BLANK field explanations, metadata headers, change history,
and cross-page consistency.

Usage:
    python lint_wiki.py <client_folder_path>
    python lint_wiki.py <client_folder_path> --fix    # suggest fixes (no auto-edit)

Output:
    Per-page lint results with severity: ERROR, WARN, INFO
    Summary with pass/fail count
"""

import sys
import re
import json
from pathlib import Path


# Pages that should have [EXTRACTED]/[INFERRED] labels when populated
LABELED_PAGES = ["business.md", "brand-identity.md", "digital-presence.md", "offerings.md"]

# Pages that should have metadata headers
HEADER_PAGES = ["business.md", "brand-identity.md", "digital-presence.md", "offerings.md"]

# Standard wiki sections
STANDARD_SECTIONS = {
    "Key Findings", "Details", "Gaps & Unknowns",
    "Marketing Implications", "Change History"
}


def is_template(content):
    """Check if page is still an empty template."""
    return "No data ingested yet" in content or len(content.strip()) < 100


def lint_metadata_header(page_name, content):
    """Check for metadata header: > Last updated: ... | Sources: ... | Confidence: ..."""
    issues = []
    if is_template(content):
        return issues

    header_pattern = r'^>\s*Last updated:.*\|.*Sources:.*\|.*Confidence:'
    if not re.search(header_pattern, content, re.MULTILINE):
        issues.append(("ERROR", page_name, "Missing metadata header (> Last updated: ... | Sources: ... | Confidence: ...)"))
    else:
        # Check confidence value
        conf_match = re.search(r'Confidence:\s*(HIGH|MEDIUM|LOW|PENDING)', content)
        if not conf_match:
            issues.append(("WARN", page_name, "Metadata header has non-standard Confidence value (should be HIGH/MEDIUM/LOW/PENDING)"))
        elif conf_match.group(1) == "PENDING":
            issues.append(("WARN", page_name, "Page has not been populated yet (Confidence: PENDING)"))

    return issues


def lint_source_labels(page_name, content):
    """Check that data points have [EXTRACTED] or [INFERRED] labels."""
    issues = []
    if is_template(content):
        return issues

    lines = content.split('\n')
    labeled_lines = 0
    data_lines = 0

    for line in lines:
        stripped = line.strip()
        # Skip headers, empty lines, metadata, change history entries
        if not stripped or stripped.startswith('#') or stripped.startswith('>'):
            continue
        if stripped.startswith('- 20') and ':' in stripped:  # Change history entry
            continue
        if stripped.startswith('<!--') or stripped.startswith('-->'):
            continue

        # Data lines: bullet points and bold-prefixed lines with actual content
        if stripped.startswith('- ') and len(stripped) > 10:
            data_lines += 1
            if '[EXTRACTED]' in stripped or '[INFERRED]' in stripped:
                labeled_lines += 1
        elif stripped.startswith('**') and len(stripped) > 15:
            data_lines += 1
            if '[EXTRACTED]' in stripped or '[INFERRED]' in stripped:
                labeled_lines += 1

    if data_lines > 0:
        ratio = labeled_lines / data_lines
        if ratio < 0.3:
            issues.append(("ERROR", page_name,
                           f"Only {labeled_lines}/{data_lines} data points have source labels ({ratio:.0%})"))
        elif ratio < 0.6:
            issues.append(("WARN", page_name,
                           f"{labeled_lines}/{data_lines} data points labeled ({ratio:.0%}) — aim for >60%"))

    return issues


def lint_blank_fields(page_name, content):
    """Check BLANK fields have explanations."""
    issues = []
    if is_template(content):
        return issues

    # BLANK should be followed by — or - or : or ( with explanation
    blanks_total = len(re.findall(r'BLANK', content))
    blanks_explained = len(re.findall(r'BLANK\s*[—\-–:(]\s*\S', content))
    blanks_unexplained = blanks_total - blanks_explained

    if blanks_unexplained > 0:
        issues.append(("ERROR", page_name,
                       f"{blanks_unexplained} BLANK field(s) without explanation (must have reason after — or :)"))

    return issues


def lint_change_history(page_name, content):
    """Check Change History section exists and has entries."""
    issues = []
    if is_template(content):
        return issues

    if '## Change History' not in content:
        issues.append(("ERROR", page_name, "Missing '## Change History' section"))
        return issues

    # Check for at least one dated entry after Change History
    history_section = content.split('## Change History')[-1]
    dated_entries = re.findall(r'- \d{4}-\d{2}-\d{2}:', history_section)
    if not dated_entries:
        issues.append(("WARN", page_name, "Change History section has no dated entries"))

    return issues


def lint_standard_sections(page_name, content):
    """Check that populated pages have the standard wiki sections.
    offerings.md is exempt — it uses per-offering H2 headings instead of standard sections.
    Pages with 3+ custom H2 sections are considered fully populated — skip 'Details' check
    since the template placeholder has been replaced with real content sections."""
    issues = []
    if is_template(content):
        return issues

    # offerings.md has its own structure (per-offering sections)
    if page_name == "offerings.md":
        return issues

    present_sections = set(re.findall(r'^## (.+)', content, re.MULTILINE))

    # If page has 3+ H2 sections, it's fully populated — skip 'Details' requirement
    # The 'Details' section is a template placeholder, not needed once real content exists
    skip_details = len(present_sections) >= 3

    for section in STANDARD_SECTIONS:
        if section not in present_sections:
            if section == "Details" and skip_details:
                continue
            severity = "WARN" if section in ("Marketing Implications", "Gaps & Unknowns") else "ERROR"
            issues.append((severity, page_name, f"Missing standard section: ## {section}"))

    return issues


def lint_index_page(wiki_dir):
    """Check index.md references all wiki pages."""
    issues = []
    index_path = wiki_dir / "index.md"
    if not index_path.exists():
        issues.append(("ERROR", "index.md", "index.md does not exist"))
        return issues

    index_content = index_path.read_text()

    # Find all .md files in wiki (except index.md and log.md)
    wiki_pages = [f.name for f in wiki_dir.glob("*.md") if f.name not in ("index.md", "log.md")]

    for page in wiki_pages:
        if page not in index_content:
            issues.append(("WARN", "index.md", f"Page '{page}' exists in wiki/ but not referenced in index.md"))

    return issues


def lint_log_page(wiki_dir):
    """Check log.md has entries and downstream flags."""
    issues = []
    log_path = wiki_dir / "log.md"
    if not log_path.exists():
        issues.append(("ERROR", "log.md", "log.md does not exist"))
        return issues

    content = log_path.read_text()
    if is_template(content):
        issues.append(("WARN", "log.md", "log.md is still empty template"))
        return issues

    # Check for downstream flag
    if not re.search(r'ready for|downstream|market-research', content, re.IGNORECASE):
        issues.append(("WARN", "log.md", "No downstream skill connection flagged"))

    return issues


def lint_wiki_config(client_dir):
    """Check wiki-config.json page registry matches actual files."""
    issues = []
    config_path = client_dir / "wiki-config.json"
    wiki_dir = client_dir / "wiki"

    if not config_path.exists():
        issues.append(("ERROR", "wiki-config.json", "wiki-config.json does not exist"))
        return issues

    try:
        config = json.loads(config_path.read_text())
    except json.JSONDecodeError:
        issues.append(("ERROR", "wiki-config.json", "Invalid JSON"))
        return issues

    registered_pages = set(config.get("pages", {}).keys())
    actual_pages = {f.stem for f in wiki_dir.glob("*.md") if f.name not in ("index.md", "log.md")}

    # Pages on disk but not registered
    unregistered = actual_pages - registered_pages
    for page in unregistered:
        issues.append(("WARN", "wiki-config.json", f"Page '{page}.md' exists on disk but not registered in wiki-config.json"))

    # Pages registered but not on disk
    orphan_registrations = registered_pages - actual_pages
    for page in orphan_registrations:
        issues.append(("ERROR", "wiki-config.json", f"Page '{page}' registered in config but file missing from wiki/"))

    return issues


def lint_offerings_depth(wiki_dir):
    """Check offerings.md has per-offering detail, not just a list."""
    issues = []
    path = wiki_dir / "offerings.md"
    if not path.exists() or is_template(path.read_text()):
        return issues

    content = path.read_text()

    # Count H2 sections (each offering should be H2 or H3)
    h2_sections = re.findall(r'^## .+', content, re.MULTILINE)
    non_standard = [h for h in h2_sections if h.replace('## ', '').strip() not in STANDARD_SECTIONS]

    if len(non_standard) < 1:
        issues.append(("WARN", "offerings.md", "No distinct offering sections found (each offering should be ## heading)"))

    # Check for depth markers: pricing, target audience, USP
    depth_markers = ['target audience', 'pricing', 'price', 'usp', 'differentiator', 'booking']
    found = sum(1 for m in depth_markers if m.lower() in content.lower())
    if found < 2:
        issues.append(("WARN", "offerings.md",
                       f"Only {found}/{len(depth_markers)} offering detail markers found — may lack depth"))

    return issues


def main():
    if len(sys.argv) < 2:
        print("Usage: python lint_wiki.py <client_folder_path>")
        sys.exit(1)

    client_dir = Path(sys.argv[1])
    wiki_dir = client_dir / "wiki"

    if not wiki_dir.is_dir():
        print(f"ERROR: {wiki_dir} is not a directory")
        sys.exit(1)

    show_fix = "--fix" in sys.argv

    all_issues = []

    # Lint each content page
    for page_name in LABELED_PAGES:
        path = wiki_dir / page_name
        if not path.exists():
            all_issues.append(("ERROR", page_name, "File does not exist"))
            continue

        content = path.read_text()

        if page_name in HEADER_PAGES:
            all_issues.extend(lint_metadata_header(page_name, content))

        all_issues.extend(lint_source_labels(page_name, content))
        all_issues.extend(lint_blank_fields(page_name, content))
        all_issues.extend(lint_change_history(page_name, content))
        all_issues.extend(lint_standard_sections(page_name, content))

    # Lint structural pages
    all_issues.extend(lint_index_page(wiki_dir))
    all_issues.extend(lint_log_page(wiki_dir))
    all_issues.extend(lint_wiki_config(client_dir))
    all_issues.extend(lint_offerings_depth(wiki_dir))

    # Print results
    print(f"\nWiki Content Lint: {client_dir.name}")
    print("=" * 60)

    if not all_issues:
        print("  All checks passed — wiki content quality is clean.")
        print("=" * 60)
        sys.exit(0)

    counts = {"ERROR": 0, "WARN": 0, "INFO": 0}
    current_page = None

    for severity, page, message in sorted(all_issues, key=lambda x: (x[1], x[0])):
        if page != current_page:
            current_page = page
            print(f"\n  {page}:")
        icon = {"ERROR": "✗", "WARN": "⚠", "INFO": "ℹ"}[severity]
        print(f"    {icon} [{severity}] {message}")
        counts[severity] += 1

    print(f"\n{'=' * 60}")
    print(f"  Results: {counts['ERROR']} errors, {counts['WARN']} warnings, {counts['INFO']} info")
    print("=" * 60)

    if counts["ERROR"] > 0:
        print("\nFix ERRORs before delivery.")
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
