#!/usr/bin/env python3
"""
Wiki Initializer for Market Research & Business Analysis Skills

Supports three modes:
  1. Single-program (default): Standard client folder with wiki/deliverables/sources
  2. Shared init (--shared): Creates _shared/ folder for multi-program clients
  3. Program init (--program): Creates per-program folder under existing client

Usage:
    # Single-program client (default)
    python init_wiki.py "/path/to/Client/Business" "BusinessName" "ProjectName"

    # Multi-program: init shared brand DNA
    python init_wiki.py "/path/to/Client" "BusinessName" --shared

    # Multi-program: init a new program under existing client
    python init_wiki.py "/path/to/Client" "BusinessName" --program "Program Name"

    # Migrate existing single-program to multi-program
    python init_wiki.py "/path/to/Client/ExistingBusiness" "BusinessName" --migrate "Program Name"

    # Detect structure type
    python init_wiki.py "/path/to/Client" --detect
"""

import sys
import json
import shutil
import argparse
from pathlib import Path
from datetime import date


# Pages that belong in _shared/ (business DNA — same across all programs)
SHARED_PAGES = {
    "business": "Business Fundamentals",
    "brand-identity": "Brand Identity",
    "digital-presence": "Digital Presence & Ad Landscape",
    "offerings": "Products, Services & Offerings",
}

# Pages that belong per-program (research — different per program)
PROGRAM_PAGES = {
    "strategy": "Market Research & Strategy",
}

# Legacy: all pages together for single-program mode
ALL_PAGES = {**SHARED_PAGES, **PROGRAM_PAGES}


def create_wiki_page(wiki_dir, slug, title, name, today):
    """Create a single wiki page with template structure."""
    content = f"""# {title} — {name}

> Last updated: {today} | Sources: 0 | Confidence: PENDING

## Key Findings

_No data ingested yet._

## Details

_Awaiting source material._

## Gaps & Unknowns

_All dimensions are gaps until first ingest._

## Marketing Implications

_Will be populated after findings are analyzed._

## Change History

- {today}: Page created (empty template)
"""
    (wiki_dir / f"{slug}.md").write_text(content, encoding="utf-8")


def create_index(wiki_dir, name, pages, today, index_type="standard"):
    """Create the index.md catalog page."""
    page_list = "\n".join(
        f"- [{title}]({slug}.md) — Awaiting data — Last updated: {today}"
        for slug, title in pages.items()
    )

    if index_type == "shared":
        header = f"# {name} — Shared Knowledge Index\n\nThis is the shared brand DNA for all programs under {name}."
        programs_section = "\n## Programs\n\n_No programs initialized yet._\n"
    elif index_type == "program":
        header = f"# {name} — Program Knowledge Index\n\nProgram-specific research. Shared brand DNA lives in `../_shared/wiki/`."
        programs_section = ""
    else:
        header = f"# {name} — Knowledge Index"
        programs_section = ""

    content = f"""{header}

Last updated: {today}
Sources ingested: 0

## Pages

{page_list}
{programs_section}
## Sources

_No sources ingested yet._
"""
    (wiki_dir / "index.md").write_text(content, encoding="utf-8")


def create_log(wiki_dir, name, page_count, today, log_type="standard"):
    """Create the log.md timeline."""
    if log_type == "shared":
        init_msg = f"Wiki _shared/ created with {page_count} brand DNA pages"
    elif log_type == "program":
        init_msg = f"Program wiki created with {page_count} research pages"
    else:
        init_msg = f"Wiki created with {page_count} template pages"

    content = f"""# {name} — Change Log

## {today}

- **INIT** {init_msg}
"""
    (wiki_dir / "log.md").write_text(content, encoding="utf-8")


def create_config(config_path, business_name, project_name, pages, today,
                  config_type="standard", parent=None, programs=None):
    """Create wiki-config.json."""
    config = {
        "type": config_type,
        "business_name": business_name,
        "created": today,
        "last_updated": today,
        "pages": list(pages.keys()),
    }

    if config_type == "shared":
        config["programs"] = programs or []
        config["brand_config"] = "deliverables/brand-config.json"
    elif config_type == "program":
        config["program_name"] = project_name
        config["parent"] = parent or "../_shared"
        config["sources_ingested"] = 0
        config["brand_config"] = "../_shared/deliverables/brand-config.json"
    else:
        config["project"] = project_name
        config["sources_ingested"] = 0
        config["brand_config"] = "deliverables/brand-config.json"

    config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")


def init_single_program(client_dir, business_name, project_name, today):
    """Initialize a standard single-program client folder."""
    wiki_dir = client_dir / "wiki"
    for d in [wiki_dir, client_dir / "sources", client_dir / "deliverables"]:
        d.mkdir(parents=True, exist_ok=True)

    if (wiki_dir / "index.md").exists():
        print(f"Wiki already exists at {wiki_dir}")
        print("Use INGEST operation to add new data, not init.")
        return False

    for slug, title in ALL_PAGES.items():
        create_wiki_page(wiki_dir, slug, title, business_name, today)
        print(f"  Created wiki/{slug}.md")

    create_index(wiki_dir, business_name, ALL_PAGES, today)
    print("  Created wiki/index.md")
    create_log(wiki_dir, business_name, len(ALL_PAGES), today)
    print("  Created wiki/log.md")
    create_config(client_dir / "wiki-config.json", business_name, project_name,
                  ALL_PAGES, today)
    print("  Created wiki-config.json")

    print(f"\nSingle-program wiki initialized for {business_name}")
    print(f"  Location: {wiki_dir}")
    print(f"  Pages: {len(ALL_PAGES)}")
    return True


def init_shared(client_dir, business_name, today):
    """Initialize the _shared/ folder for multi-program clients."""
    shared_dir = client_dir / "_shared"
    wiki_dir = shared_dir / "wiki"
    for d in [wiki_dir, shared_dir / "deliverables"]:
        d.mkdir(parents=True, exist_ok=True)

    if (wiki_dir / "index.md").exists():
        print(f"Shared wiki already exists at {wiki_dir}")
        return False

    for slug, title in SHARED_PAGES.items():
        create_wiki_page(wiki_dir, slug, title, business_name, today)
        print(f"  Created _shared/wiki/{slug}.md")

    create_index(wiki_dir, business_name, SHARED_PAGES, today, index_type="shared")
    print("  Created _shared/wiki/index.md")
    create_log(wiki_dir, business_name, len(SHARED_PAGES), today, log_type="shared")
    print("  Created _shared/wiki/log.md")
    create_config(shared_dir / "wiki-config.json", business_name, "",
                  SHARED_PAGES, today, config_type="shared")
    print("  Created _shared/wiki-config.json")

    print(f"\nShared brand DNA initialized for {business_name}")
    print(f"  Location: {shared_dir}")
    print(f"  Pages: {len(SHARED_PAGES)}")
    return True


def init_program(client_dir, business_name, program_name, today):
    """Initialize a new program folder under a multi-program client."""
    shared_dir = client_dir / "_shared"
    if not shared_dir.exists():
        print(f"ERROR: _shared/ not found at {shared_dir}")
        print("Run with --shared first to create the shared brand DNA folder.")
        return False

    program_dir = client_dir / program_name
    wiki_dir = program_dir / "wiki"
    for d in [wiki_dir, program_dir / "sources", program_dir / "deliverables"]:
        d.mkdir(parents=True, exist_ok=True)

    if (wiki_dir / "index.md").exists():
        print(f"Program wiki already exists at {wiki_dir}")
        print("Use INGEST operation to add new data, not init.")
        return False

    for slug, title in PROGRAM_PAGES.items():
        create_wiki_page(wiki_dir, slug, title, f"{business_name} — {program_name}", today)
        print(f"  Created {program_name}/wiki/{slug}.md")

    create_index(wiki_dir, f"{business_name} — {program_name}",
                 PROGRAM_PAGES, today, index_type="program")
    print(f"  Created {program_name}/wiki/index.md")
    create_log(wiki_dir, f"{business_name} — {program_name}",
               len(PROGRAM_PAGES), today, log_type="program")
    print(f"  Created {program_name}/wiki/log.md")
    create_config(program_dir / "wiki-config.json", business_name, program_name,
                  PROGRAM_PAGES, today, config_type="program", parent="../_shared")
    print(f"  Created {program_name}/wiki-config.json")

    # Update shared config with new program
    shared_config_path = shared_dir / "wiki-config.json"
    if shared_config_path.exists():
        shared_config = json.loads(shared_config_path.read_text(encoding="utf-8"))
        if program_name not in shared_config.get("programs", []):
            shared_config.setdefault("programs", []).append(program_name)
            shared_config["last_updated"] = today
            shared_config_path.write_text(json.dumps(shared_config, indent=2), encoding="utf-8")
            print(f"  Updated _shared/wiki-config.json — added program '{program_name}'")

    # Update shared index with program link
    shared_index = shared_dir / "wiki" / "index.md"
    if shared_index.exists():
        content = shared_index.read_text(encoding="utf-8")
        if "_No programs initialized yet._" in content:
            content = content.replace(
                "_No programs initialized yet._",
                f"- [{program_name}](../../{program_name}/wiki/index.md) — Initialized {today}"
            )
        elif f"[{program_name}]" not in content:
            # Append to programs list
            content = content.replace(
                "\n## Sources",
                f"- [{program_name}](../../{program_name}/wiki/index.md) — Initialized {today}\n\n## Sources"
            )
        shared_index.write_text(content, encoding="utf-8")

    print(f"\nProgram wiki initialized for {program_name}")
    print(f"  Location: {program_dir}")
    print(f"  Pages: {len(PROGRAM_PAGES)}")
    print(f"  Brand config: ../_shared/deliverables/brand-config.json")
    return True


def migrate_to_multi(existing_dir, business_name, program_name, today):
    """Migrate an existing single-program client to multi-program structure."""
    client_dir = existing_dir.parent
    shared_dir = client_dir / "_shared"

    if shared_dir.exists():
        print(f"ERROR: _shared/ already exists at {shared_dir}")
        print("Client is already multi-program. Use --program to add a new program.")
        return False

    print(f"Migrating {business_name} to multi-program structure...")
    print(f"  Existing program folder: {existing_dir.name}")
    print(f"  Will become first program: {existing_dir.name}")

    # 1. Create _shared/
    init_shared(client_dir, business_name, today)

    # 2. Move shared files from existing to _shared/
    existing_wiki = existing_dir / "wiki"
    shared_wiki = shared_dir / "wiki"
    shared_deliverables = shared_dir / "deliverables"

    files_to_move_wiki = ["business.md", "brand-identity.md", "digital-presence.md", "offerings.md"]
    files_to_move_deliverables = ["brand-config.json"]

    for fname in files_to_move_wiki:
        src = existing_wiki / fname
        dst = shared_wiki / fname
        if src.exists():
            # Overwrite the empty template with actual content
            shutil.copy2(str(src), str(dst))
            print(f"  Copied wiki/{fname} → _shared/wiki/{fname}")

    for fname in files_to_move_deliverables:
        src = existing_dir / "deliverables" / fname
        dst = shared_deliverables / fname
        if src.exists():
            shutil.copy2(str(src), str(dst))
            print(f"  Copied deliverables/{fname} → _shared/deliverables/{fname}")

    # 3. Update existing program's wiki-config.json
    existing_config_path = existing_dir / "wiki-config.json"
    if existing_config_path.exists():
        config = json.loads(existing_config_path.read_text(encoding="utf-8"))
        config["type"] = "program"
        config["program_name"] = existing_dir.name
        config["parent"] = "../_shared"
        config["brand_config"] = "../_shared/deliverables/brand-config.json"
        config["last_updated"] = today
        existing_config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")
        print(f"  Updated {existing_dir.name}/wiki-config.json → type: program")

    # 4. Register existing as first program in shared config
    shared_config_path = shared_dir / "wiki-config.json"
    shared_config = json.loads(shared_config_path.read_text(encoding="utf-8"))
    shared_config["programs"] = [existing_dir.name]
    shared_config["last_updated"] = today
    shared_config_path.write_text(json.dumps(shared_config, indent=2), encoding="utf-8")

    # 5. Update shared index
    shared_index = shared_dir / "wiki" / "index.md"
    content = shared_index.read_text(encoding="utf-8")
    content = content.replace(
        "_No programs initialized yet._",
        f"- [{existing_dir.name}](../../{existing_dir.name}/wiki/index.md) — Migrated {today}"
    )
    shared_index.write_text(content, encoding="utf-8")

    # 6. Log migration
    log_entry = f"- **MIGRATION** Converted from single-program to multi-program. Brand DNA moved to _shared/. Existing research remains in {existing_dir.name}/.\n"

    shared_log = shared_dir / "wiki" / "log.md"
    log_content = shared_log.read_text(encoding="utf-8")
    log_content = log_content.replace(
        f"- **INIT**",
        f"{log_entry}- **INIT**"
    )
    shared_log.write_text(log_content, encoding="utf-8")

    existing_log = existing_wiki / "log.md"
    if existing_log.exists():
        log_content = existing_log.read_text(encoding="utf-8")
        log_content = log_content.replace(
            f"\n## {today}\n",
            f"\n## {today}\n\n{log_entry}",
            1
        )
        # If today's date section doesn't exist, prepend
        if log_entry not in log_content:
            log_content = log_content.replace(
                "\n## ",
                f"\n## {today}\n\n{log_entry}\n## ",
                1
            )
        existing_log.write_text(log_content, encoding="utf-8")

    print(f"\nMigration complete.")
    print(f"  _shared/ created with brand DNA")
    print(f"  {existing_dir.name}/ updated as first program")
    print(f"  Ready to add new programs with --program")
    return True


def detect_structure(client_dir):
    """Detect whether a client folder is single-program, multi-program, or new."""
    client_dir = Path(client_dir)

    if not client_dir.exists():
        print(f"NOT_FOUND — {client_dir} does not exist")
        return "not_found"

    shared_dir = client_dir / "_shared"
    if shared_dir.exists() and (shared_dir / "wiki-config.json").exists():
        config = json.loads((shared_dir / "wiki-config.json").read_text(encoding="utf-8"))
        programs = config.get("programs", [])
        print(f"MULTI_PROGRAM — {len(programs)} program(s): {', '.join(programs)}")
        print(f"  Shared: {shared_dir}")
        for p in programs:
            prog_dir = client_dir / p
            status = "EXISTS" if prog_dir.exists() else "MISSING"
            print(f"  Program '{p}': {status}")
        return "multi_program"

    # Check subdirectories for wiki-config.json (single-program)
    for subdir in client_dir.iterdir():
        if subdir.is_dir() and (subdir / "wiki-config.json").exists():
            config = json.loads((subdir / "wiki-config.json").read_text(encoding="utf-8"))
            ctype = config.get("type", "standard")
            print(f"SINGLE_PROGRAM — {subdir.name}/ (type: {ctype})")
            print(f"  Wiki: {subdir / 'wiki'}")
            return "single_program"

    print(f"NEW_CLIENT — No wiki found in {client_dir}")
    return "new_client"


def main():
    parser = argparse.ArgumentParser(
        description='Wiki Initializer — supports single-program and multi-program clients'
    )
    parser.add_argument('path', help='Client or project folder path')
    parser.add_argument('business_name', nargs='?', default='', help='Business name')
    parser.add_argument('project_name', nargs='?', default='', help='Project name (single-program only)')

    group = parser.add_mutually_exclusive_group()
    group.add_argument('--shared', action='store_true',
                       help='Initialize _shared/ folder for multi-program client')
    group.add_argument('--program', metavar='NAME',
                       help='Initialize a new program folder under existing client')
    group.add_argument('--migrate', metavar='NAME',
                       help='Migrate existing single-program to multi-program')
    group.add_argument('--detect', action='store_true',
                       help='Detect client structure type')

    args = parser.parse_args()
    client_dir = Path(args.path)
    today = date.today().isoformat()

    if args.detect:
        detect_structure(client_dir)
        return

    if not args.business_name:
        parser.error("business_name is required (except with --detect)")

    if args.shared:
        init_shared(client_dir, args.business_name, today)
    elif args.program:
        init_program(client_dir, args.business_name, args.program, today)
    elif args.migrate:
        migrate_to_multi(client_dir, args.business_name, args.migrate, today)
    else:
        project_name = args.project_name or args.business_name
        init_single_program(client_dir, args.business_name, project_name, today)


if __name__ == "__main__":
    main()
