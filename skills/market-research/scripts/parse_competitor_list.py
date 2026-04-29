#!/usr/bin/env python3
"""
Parse competitor names from strategy.md wiki page.
Used by Meta Ad Library audit to get the list of competitors to check.

Usage:
    python parse_competitor_list.py /path/to/_engine/wiki/strategy.md

Output:
    JSON array of competitor objects to stdout:
    [
        {
            "name": "Häuslein",
            "url_encoded": "H%C3%A4uslein",
            "meta_ad_library_url": "https://www.facebook.com/ads/library/?active_status=all&ad_type=all&country=AU&q=H%C3%A4uslein",
            "ads_active": null
        },
        ...
    ]

Options:
    --country CODE    ISO country code for Meta Ad Library URL (default: AU)
    --limit N         Max competitors to return (default: 10)
    --json            Output as JSON (default)
    --names           Output names only, one per line

Exit codes:
    0 = success
    1 = file not found or unreadable
    2 = no competitor table found
    3 = no competitors extracted
"""

import sys
import re
import json
import urllib.parse
import argparse
from pathlib import Path
from typing import Optional, List


def find_competitor_table(content: str) -> Optional[List[str]]:
    """
    Find the Competitive Landscape markdown table in strategy.md.

    Looks for a section header containing 'Competitive Landscape' or 'Competitor'
    followed by a markdown table. Returns the table rows as a list of strings,
    or None if no table is found.
    """
    lines = content.split("\n")

    # Find the Competitive Landscape section
    section_start = None
    for i, line in enumerate(lines):
        # Match ## 5. Competitive Landscape or similar variations
        if re.match(
            r"^#{1,3}\s*\d*\.?\s*(Competitive Landscape|Competitors?)\b",
            line,
            re.IGNORECASE,
        ):
            section_start = i
            break

    if section_start is None:
        return None

    # Find the markdown table within this section
    # Table starts with a header row containing | and is followed by a separator row |---|
    table_lines = []
    in_table = False
    header_found = False

    for i in range(section_start, len(lines)):
        line = lines[i].strip()

        # Stop if we hit the next section (## heading that isn't a sub-section of competitors)
        if i > section_start and re.match(r"^#{1,2}\s+\d+\.", line):
            break

        # Detect table header row
        if not in_table and "|" in line and not line.startswith("|-"):
            # Check if the next line is a separator
            if i + 1 < len(lines) and re.match(
                r"^\s*\|[-\s|]+\|\s*$", lines[i + 1].strip()
            ):
                in_table = True
                header_found = True
                table_lines.append(line)  # header row
                continue

        if in_table:
            if "|" in line:
                table_lines.append(line)
            elif line == "":
                # Empty line might be within table context, keep going briefly
                continue
            else:
                # Non-table content, we're done
                break

    return table_lines if table_lines else None


def parse_table_rows(table_lines: list[str]) -> list[dict]:
    """
    Parse markdown table lines into competitor data.

    Expects format:
    | Company | Location | Price Range | Positioning | Key Differentiator | Ads Active |
    |---|---|---|---|---|---|
    | Häuslein | Sunshine Coast, QLD | $99K–$150K | ... | ... | BLANK |

    Returns list of dicts with at minimum 'name' key.
    """
    if len(table_lines) < 3:
        # Need header + separator + at least one data row
        return []

    # Parse header to find column indices
    header_cells = [
        cell.strip() for cell in table_lines[0].split("|") if cell.strip()
    ]

    # Find the company/name column (usually first)
    name_col = 0
    for i, header in enumerate(header_cells):
        if header.lower() in ("company", "competitor", "name", "brand", "business"):
            name_col = i
            break

    # Find the ads active column if it exists
    ads_col = None
    for i, header in enumerate(header_cells):
        if "ads" in header.lower() or "active" in header.lower():
            ads_col = i
            break

    # Skip header (index 0) and separator (index 1), parse data rows
    competitors = []
    for line in table_lines[2:]:
        cells = [cell.strip() for cell in line.split("|") if cell.strip()]
        if not cells:
            continue

        if name_col >= len(cells):
            continue

        name = cells[name_col].strip()

        # Skip empty names, header remnants, or separator rows
        if not name or name.startswith("---") or name.lower() in ("company", "competitor", "name"):
            continue

        competitor = {
            "name": name,
            "ads_active": None,
        }

        # Check if ads column has existing data
        if ads_col is not None and ads_col < len(cells):
            ads_value = cells[ads_col].strip()
            if ads_value and ads_value.upper() != "BLANK":
                competitor["ads_active"] = ads_value

        competitors.append(competitor)

    return competitors


def build_meta_ad_library_url(name: str, country: str = "AU") -> str:
    """Build Meta Ad Library search URL for a competitor name."""
    encoded = urllib.parse.quote(name, safe="")
    return (
        f"https://www.facebook.com/ads/library/"
        f"?active_status=all&ad_type=all&country={country}&q={encoded}"
    )


def main():
    parser = argparse.ArgumentParser(
        description="Extract competitor names from strategy.md for Meta Ad Library audit"
    )
    parser.add_argument(
        "strategy_file",
        help="Path to strategy.md wiki file",
    )
    parser.add_argument(
        "--country",
        default="AU",
        help="ISO country code for Meta Ad Library URL (default: AU)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Max competitors to return (default: 10)",
    )
    parser.add_argument(
        "--names",
        action="store_true",
        help="Output names only, one per line (default: JSON)",
    )

    args = parser.parse_args()

    # Read strategy.md
    strategy_path = Path(args.strategy_file)
    if not strategy_path.exists():
        print(f"Error: File not found: {strategy_path}", file=sys.stderr)
        sys.exit(1)

    try:
        content = strategy_path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        sys.exit(1)

    # Find competitor table
    table_lines = find_competitor_table(content)
    if table_lines is None:
        print(
            "Error: No Competitive Landscape table found in strategy.md",
            file=sys.stderr,
        )
        sys.exit(2)

    # Parse competitors
    competitors = parse_table_rows(table_lines)
    if not competitors:
        print("Error: No competitors extracted from table", file=sys.stderr)
        sys.exit(3)

    # Apply limit
    competitors = competitors[: args.limit]

    # Add URL-encoded names and Meta Ad Library URLs
    for comp in competitors:
        comp["url_encoded"] = urllib.parse.quote(comp["name"], safe="")
        comp["meta_ad_library_url"] = build_meta_ad_library_url(
            comp["name"], args.country
        )

    # Output
    if args.names:
        for comp in competitors:
            print(comp["name"])
    else:
        print(json.dumps(competitors, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
