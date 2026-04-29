#!/usr/bin/env python3
"""
Wiki Linter for Market Research Skill
Checks a client wiki for health issues: stale pages, contradictions,
orphan sources, persistent gaps, and confidence decay.

Usage:
    python lint_wiki.py <client_folder>
    python lint_wiki.py <client_folder> --verbose

Example:
    python lint_wiki.py "Desktop/Gargi Modi/CrownTech"
"""

import sys
import re
import json
from pathlib import Path
from datetime import datetime, timedelta


WIKI_PAGES = [
    "business.md", "market.md", "competitors.md", "audience.md",
    "benchmarks.md", "digital-presence.md", "strategy.md"
]

# Pages expected when lint runs on a multi-program `type: program` folder.
# Shared brand DNA pages (business.md, digital-presence.md etc.) live in
# `../../_engine/wiki/` (the client-root _engine/), not in the program folder itself.
PROGRAM_WIKI_PAGES_DEFAULT = ["strategy.md"]

STALENESS_THRESHOLD_DAYS = 90


def detect_wiki_pages(client_path):
    """Return the list of wiki pages this folder is expected to contain.

    For standard (single-program) wikis: full WIKI_PAGES list.
    For multi-program program folders (`_engine/wiki-config.json` `type: program`):
    only the pages registered in wiki-config.json (or strategy.md default).
    """
    config_path = client_path / "_engine" / "wiki-config.json"
    if config_path.exists():
        try:
            cfg = json.loads(config_path.read_text(encoding="utf-8"))
            if cfg.get("type") == "program":
                pages_field = cfg.get("pages", [])
                if isinstance(pages_field, list) and pages_field:
                    return [f"{p}.md" for p in pages_field]
                if isinstance(pages_field, dict) and pages_field:
                    return [f"{slug}.md" for slug in pages_field.keys()]
                return PROGRAM_WIKI_PAGES_DEFAULT
        except json.JSONDecodeError:
            pass
    return WIKI_PAGES


def check_wiki_exists(client_path):
    """Verify _engine/{wiki,sources} folder structure exists."""
    wiki_path = client_path / "_engine" / "wiki"
    sources_path = client_path / "_engine" / "sources"
    issues = []

    if not wiki_path.exists():
        issues.append(("CRITICAL", "_engine/wiki/ folder missing — run init_wiki.py first"))
        return issues, False

    if not sources_path.exists():
        issues.append(("WARNING", "_engine/sources/ folder missing — no raw sources stored"))

    expected_pages = detect_wiki_pages(client_path)
    for page in expected_pages:
        if not (wiki_path / page).exists():
            issues.append(("WARNING", f"_engine/wiki/{page} missing"))

    if not (wiki_path / "index.md").exists():
        issues.append(("WARNING", "_engine/wiki/index.md missing — no table of contents"))

    if not (wiki_path / "log.md").exists():
        issues.append(("WARNING", "_engine/wiki/log.md missing — no change history"))

    return issues, True


def check_empty_pages(client_path):
    """Find wiki pages that are still empty templates."""
    wiki_path = client_path / "_engine" / "wiki"
    issues = []

    for page in detect_wiki_pages(client_path):
        filepath = wiki_path / page
        if not filepath.exists():
            continue
        content = filepath.read_text(encoding="utf-8")
        # Check if page is essentially empty (just template scaffolding)
        stripped = re.sub(r'#.*\n|---\n|\*.*\*|\{.*\}|>\s*\n', '', content).strip()
        if len(stripped) < 50:
            issues.append(("WARNING", f"_engine/wiki/{page} is still an empty template — needs data ingestion"))

    return issues


def check_stale_pages(client_path):
    """Find wiki pages not updated in over STALENESS_THRESHOLD_DAYS days."""
    wiki_path = client_path / "_engine" / "wiki"
    issues = []
    now = datetime.now()

    for page in detect_wiki_pages(client_path):
        filepath = wiki_path / page
        if not filepath.exists():
            continue

        # Check file modification time
        mtime = datetime.fromtimestamp(filepath.stat().st_mtime)
        age_days = (now - mtime).days

        if age_days > STALENESS_THRESHOLD_DAYS:
            issues.append(("WARNING", f"_engine/wiki/{page} last updated {age_days} days ago — may need refresh"))

        # Also check for explicit date stamps in content
        content = filepath.read_text(encoding="utf-8")
        dates = re.findall(r'(\d{4}-\d{2}-\d{2})', content)
        if dates:
            latest = max(dates)
            try:
                latest_dt = datetime.strptime(latest, "%Y-%m-%d")
                content_age = (now - latest_dt).days
                if content_age > STALENESS_THRESHOLD_DAYS:
                    issues.append(("INFO", f"_engine/wiki/{page} newest date reference is {latest} ({content_age} days old)"))
            except ValueError:
                pass

    return issues


def check_metadata_headers(client_path):
    """Validate metadata headers on wiki pages (Confidence values, etc.)."""
    wiki_path = client_path / "_engine" / "wiki"
    issues = []

    for page in WIKI_PAGES:
        filepath = wiki_path / page
        if not filepath.exists():
            continue
        content = filepath.read_text(encoding="utf-8")

        # Check for metadata header with Confidence field
        header_match = re.search(r'^>\s*Last updated:.*\|.*Sources:.*\|.*Confidence:', content, re.MULTILINE)
        if not header_match:
            continue  # No metadata header — other checks handle missing structure

        # Validate confidence value
        conf_match = re.search(r'Confidence:\s*(HIGH|MEDIUM|LOW|PENDING)', content)
        if not conf_match:
            issues.append(("WARNING", f"_engine/wiki/{page} has non-standard Confidence value (should be HIGH/MEDIUM/LOW/PENDING)"))
        elif conf_match.group(1) == "PENDING":
            issues.append(("WARNING", f"_engine/wiki/{page} has not been populated yet (Confidence: PENDING)"))

    return issues


def check_orphan_sources(client_path):
    """Find source files not referenced in any wiki page."""
    sources_path = client_path / "_engine" / "sources"
    wiki_path = client_path / "_engine" / "wiki"
    issues = []

    if not sources_path.exists():
        return issues

    # Collect all wiki content
    wiki_content = ""
    for page in WIKI_PAGES + ["index.md", "log.md"]:
        filepath = wiki_path / page
        if filepath.exists():
            wiki_content += filepath.read_text(encoding="utf-8")

    # Check each source file
    for source_file in sources_path.iterdir():
        if source_file.name.startswith("."):
            continue
        if source_file.name not in wiki_content and source_file.stem not in wiki_content:
            issues.append(("WARNING", f"_engine/sources/{source_file.name} not referenced in any wiki page — orphan source"))

    return issues


def check_gaps(client_path):
    """Find persistent gaps (BLANK / unknown / TBD markers) in wiki pages."""
    wiki_path = client_path / "_engine" / "wiki"
    issues = []
    gap_patterns = [
        r'\[?BLANK\]?',
        r'\{.*TBD.*\}',
        r'\{.*unknown.*\}',
        r'Data not available',
        r'No data found',
        r'\[needs?\s+research\]',
    ]

    total_gaps = 0
    for page in WIKI_PAGES:
        filepath = wiki_path / page
        if not filepath.exists():
            continue
        content = filepath.read_text(encoding="utf-8")
        page_gaps = 0
        for pattern in gap_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            page_gaps += len(matches)
        if page_gaps > 0:
            total_gaps += page_gaps
            issues.append(("INFO", f"_engine/wiki/{page} has {page_gaps} gap markers — consider filling with new sources"))

    if total_gaps > 10:
        issues.append(("WARNING", f"Total {total_gaps} gaps across wiki — significant knowledge holes remain"))

    return issues


def check_contradictions(client_path):
    """Basic contradiction detection: same metric with different values across pages."""
    wiki_path = client_path / "_engine" / "wiki"
    issues = []

    # Collect all numbers with context from each page
    page_numbers = {}
    for page in WIKI_PAGES:
        filepath = wiki_path / page
        if not filepath.exists():
            continue
        content = filepath.read_text(encoding="utf-8")
        # Find patterns like "market size: $X" or "X% growth" or "$X billion"
        numbers = re.findall(r'(\$[\d,.]+\s*(?:billion|million|B|M)?|\d+\.?\d*%)', content, re.I)
        page_numbers[page] = numbers

    # Cross-check: if market.md says "$2.8B" and strategy.md says "$3.5B", flag it
    all_dollar_amounts = {}
    for page, numbers in page_numbers.items():
        for num in numbers:
            if num.startswith('$'):
                key = num.lower().replace(',', '').replace(' ', '')
                if key not in all_dollar_amounts:
                    all_dollar_amounts[key] = []
                all_dollar_amounts[key].append(page)

    # This is a basic check — real contradiction detection would need NLP
    # For now, just flag if the same exact number appears in multiple pages (potential redundancy)
    for num, pages in all_dollar_amounts.items():
        if len(pages) > 2:
            issues.append(("INFO", f"Value {num} appears in {len(pages)} pages ({', '.join(pages)}) — verify consistency"))

    return issues


def check_wiki_config(client_path):
    """Verify _engine/wiki-config.json is present and valid."""
    config_path = client_path / "_engine" / "wiki-config.json"
    issues = []

    if not config_path.exists():
        issues.append(("WARNING", "_engine/wiki-config.json missing — no metadata for this wiki"))
        return issues

    try:
        with open(config_path) as f:
            config = json.load(f)

        required_fields = ["business_name", "created_date"]
        for field in required_fields:
            if field not in config:
                issues.append(("WARNING", f"_engine/wiki-config.json missing '{field}' field"))

    except json.JSONDecodeError:
        issues.append(("CRITICAL", "_engine/wiki-config.json is invalid JSON"))

    return issues


def print_results(issues, verbose=False):
    """Print lint results."""
    print(f"\n{'=' * 60}")
    print(f"  Wiki Lint Results")
    print(f"{'=' * 60}")

    critical = [i for i in issues if i[0] == "CRITICAL"]
    warnings = [i for i in issues if i[0] == "WARNING"]
    info = [i for i in issues if i[0] == "INFO"]

    if not issues:
        print("\n  All clear — wiki is healthy.")
        return 0

    for severity, message in critical:
        print(f"  CRITICAL  {message}")

    for severity, message in warnings:
        print(f"  WARNING   {message}")

    if verbose:
        for severity, message in info:
            print(f"  INFO      {message}")
    elif info:
        print(f"\n  ({len(info)} info items hidden — use --verbose to see)")

    print(f"\n  Summary: {len(critical)} critical | {len(warnings)} warnings | {len(info)} info")
    print(f"{'=' * 60}")

    return 1 if critical else 0


def main():
    if len(sys.argv) < 2:
        print("Usage: python lint_wiki.py <client_folder> [--verbose]")
        print("Example: python lint_wiki.py 'Desktop/Gargi Modi/CrownTech'")
        sys.exit(1)

    client_path = Path(sys.argv[1])
    verbose = "--verbose" in sys.argv

    if not client_path.exists():
        print(f"Client folder not found: {client_path}")
        sys.exit(1)

    all_issues = []

    # Run all checks
    structure_issues, wiki_exists = check_wiki_exists(client_path)
    all_issues.extend(structure_issues)

    if wiki_exists:
        all_issues.extend(check_empty_pages(client_path))
        all_issues.extend(check_metadata_headers(client_path))
        all_issues.extend(check_stale_pages(client_path))
        all_issues.extend(check_orphan_sources(client_path))
        all_issues.extend(check_gaps(client_path))
        all_issues.extend(check_contradictions(client_path))
        all_issues.extend(check_wiki_config(client_path))

    exit_code = print_results(all_issues, verbose)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
