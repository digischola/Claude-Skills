#!/usr/bin/env python3
"""
Wiki Initializer for Business Analysis Skill

Creates the per-client wiki folder structure with base template pages.
Other skills add their own pages dynamically — this script only creates
the business analysis foundation pages.

Usage:
    python init_wiki.py <client_folder_path> <business_name> [project_name]

Example:
    python init_wiki.py "/path/to/Desktop/Thrive Retreat/Thrive Retreat" "Thrive Retreat"
"""

import sys
import json
from pathlib import Path
from datetime import date


# Base pages created by business analysis.
# Other skills add pages dynamically by registering in index.md and wiki-config.json.
BASE_PAGES = {
    "business": "Business Fundamentals",
    "brand-identity": "Brand Identity & Visual Language",
    "digital-presence": "Digital Presence Audit",
    "offerings": "Products, Services & Offerings",
}


def create_wiki_page(wiki_dir, slug, title, business_name, today):
    """Create a single wiki page with template structure."""
    content = f"""# {title}

> Last updated: {today} | Sources: 0 | Confidence: PENDING

## Key Findings

_No data ingested yet._

## Details

_Awaiting source material._

## Gaps & Unknowns

_All dimensions are gaps until first extraction._

## Marketing Implications

_Will be populated after findings are analyzed._

## Change History

- {today}: Page created (empty template) by business-analysis skill
"""
    (wiki_dir / f"{slug}.md").write_text(content, encoding="utf-8")


def create_index(wiki_dir, business_name, today):
    """Create the index.md catalog page."""
    page_list = "\n".join(
        f"- [{title}]({slug}.md) — Awaiting data — Last updated: {today} — Owner: business-analysis"
        for slug, title in BASE_PAGES.items()
    )
    content = f"""# {business_name} — Knowledge Index

Last updated: {today}
Sources ingested: 0

## Pages

{page_list}

## Dynamic Pages

_Other skills will register their pages here. Format:_
_- [Page Title](filename.md) — Summary — Last updated: date — Owner: skill-name_

## Sources

_No sources ingested yet._
"""
    (wiki_dir / "index.md").write_text(content, encoding="utf-8")


def create_log(wiki_dir, business_name, today):
    """Create the log.md timeline."""
    content = f"""# {business_name} — Change Log

## {today}

- **INIT** Wiki created by business-analysis skill with {len(BASE_PAGES)} base pages: {', '.join(BASE_PAGES.keys())}
"""
    (wiki_dir / "log.md").write_text(content, encoding="utf-8")


def create_config(client_dir, business_name, project_name, today):
    """Create wiki-config.json with dynamic page registry."""
    config = {
        "business_name": business_name,
        "project": project_name,
        "created": today,
        "last_updated": today,
        "sources_ingested": 0,
        "brand_config": "deliverables/brand-config.json",
        "pages": {
            slug: {
                "title": title,
                "owner": "business-analysis",
                "created": today,
                "last_updated": today,
            }
            for slug, title in BASE_PAGES.items()
        },
    }
    (client_dir / "wiki-config.json").write_text(
        json.dumps(config, indent=2), encoding="utf-8"
    )


def main():
    if len(sys.argv) < 3:
        print("Usage: python init_wiki.py <client_folder_path> <business_name> [project_name]")
        print('Example: python init_wiki.py "./Thrive Retreat/Thrive Retreat" "Thrive Retreat"')
        sys.exit(1)

    client_dir = Path(sys.argv[1])
    business_name = sys.argv[2]
    project_name = sys.argv[3] if len(sys.argv) > 3 else business_name
    today = date.today().isoformat()

    # Create directories
    wiki_dir = client_dir / "wiki"
    sources_dir = client_dir / "sources"
    deliverables_dir = client_dir / "deliverables"

    for d in [wiki_dir, sources_dir, deliverables_dir]:
        d.mkdir(parents=True, exist_ok=True)

    # Check if wiki already exists
    if (wiki_dir / "index.md").exists():
        print(f"Wiki already exists at {wiki_dir}")
        print("Use the skill's update flow to add data, not init.")
        sys.exit(0)

    # Create all base wiki pages
    for slug, title in BASE_PAGES.items():
        create_wiki_page(wiki_dir, slug, title, business_name, today)
        print(f"  Created wiki/{slug}.md")

    # Create index, log, config
    create_index(wiki_dir, business_name, today)
    print("  Created wiki/index.md")

    create_log(wiki_dir, business_name, today)
    print("  Created wiki/log.md")

    create_config(client_dir, business_name, project_name, today)
    print("  Created wiki-config.json")

    print(f"\nWiki initialized for {business_name}")
    print(f"  Location: {wiki_dir}")
    print(f"  Base pages: {len(BASE_PAGES)} (business, brand-identity, digital-presence, offerings)")
    print(f"  Dynamic pages: other skills will add their own pages")
    print(f"  Ready for business analysis extraction")


if __name__ == "__main__":
    main()
