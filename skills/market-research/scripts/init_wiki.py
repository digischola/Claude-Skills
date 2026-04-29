#!/usr/bin/env python3
"""
Wiki Initializer for Market Research & Business Analysis Skills

Supports three modes:
  1. Single-program (default): Standard client folder with _engine/{wiki,sources,working}
  2. Shared init (--shared): Creates client-root _engine/ for multi-program clients
  3. Program init (--program): Creates per-program folder under existing client

Folder convention (2026-04-29 _engine refactor):
  - Skill internals (wiki/, sources/, working/, configs) live under _engine/
  - Presentables (HTML/PDF/MP4/CSV bundles) live at the folder root
  - Multi-program shared internals live in the CLIENT-ROOT _engine/ (formerly _shared/)

Usage:
    # Single-program client (default)
    python init_wiki.py "/path/to/Client/Business" "BusinessName" "ProjectName"

    # Multi-program: init client-root _engine/ (shared brand DNA)
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


# Pages that belong in the client-root _engine/ (business DNA — same across all programs)
SHARED_PAGES = {
    "business": "Business Fundamentals",
    "brand-identity": "Brand Identity",
    "digital-presence": "Digital Presence & Ad Landscape",
    "offerings": "Products, Services & Offerings",
}

# Pages that belong per-program (research + briefs — different per program)
PROGRAM_PAGES = {
    "strategy": "Market Research & Strategy",
    "briefs": "Client Briefs — What Was Asked",
}

# Legacy: all pages together for single-program mode
ALL_PAGES = {**SHARED_PAGES, **PROGRAM_PAGES}


def create_wiki_page(wiki_dir, slug, title, name, today):
    """Create a single wiki page with template structure."""
    if slug == "briefs":
        # Briefs page is append-only; uses different template (no Marketing Implications etc.)
        content = f"""# {title} — {name}

> Append-only log of client requests. Latest `[ACTIVE]` entry drives current strategy.
> Skills downstream of business-analysis MUST read this file and anchor recommendations to active brief(s).

## How to use this page

- **New ask from client?** Append a new dated entry below. Mark it `[ACTIVE]`.
- **Supersedes a prior ask?** Mark the prior entry `[SUPERSEDED by YYYY-MM-DD]`. Don't delete.
- **Verbatim is sacred.** Capture the client's actual words first. Parsed fields go below.
- **Source labels:** Tag verbatim as `[EXTRACTED]` (client-sent text) or `[INFERRED]` (paraphrased from a call) per accuracy protocol.

## Briefs

_No briefs captured yet. Append below as they arrive._

<!--
Template for new entries:

## YYYY-MM-DD — Short title  [ACTIVE]

**Received via:** WhatsApp / email / call notes / etc.
**Date received:** YYYY-MM-DD
**Channel:** [the inbound channel]

**Verbatim** `[EXTRACTED]`:
> "Client's exact words go here, unedited."

**Parsed:**
- Campaigns: [list]
- Budget: [amount + cadence]
- Featured products: [from offerings.md]
- Audience: [geo, demographics, segments]
- Constraints: [time, infrastructure, scope limits client specified]
- Open questions: [things to clarify before strategy]
-->

## Change History

- {today}: Page created (empty template)
"""
    else:
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
        header = f"# {name} — Program Knowledge Index\n\nProgram-specific research. Shared brand DNA lives in `../../_engine/wiki/` (at the client root)."
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
        init_msg = f"Client-root _engine/ wiki created with {page_count} brand DNA pages"
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
        config["brand_config"] = "brand-config.json"
    elif config_type == "program":
        config["program_name"] = project_name
        # parent path is relative to {Program}/_engine/ → up two levels to client root, then into _engine/
        config["parent"] = parent or "../../_engine"
        config["sources_ingested"] = 0
        config["brand_config"] = "../../_engine/brand-config.json"
    else:
        config["project"] = project_name
        config["sources_ingested"] = 0
        config["brand_config"] = "brand-config.json"

    config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")


def init_single_program(client_dir, business_name, project_name, today):
    """Initialize a standard single-program client folder under _engine/."""
    engine_dir = client_dir / "_engine"
    wiki_dir = engine_dir / "wiki"
    for d in [wiki_dir, engine_dir / "sources", engine_dir / "working"]:
        d.mkdir(parents=True, exist_ok=True)

    if (wiki_dir / "index.md").exists():
        print(f"Wiki already exists at {wiki_dir}")
        print("Use INGEST operation to add new data, not init.")
        return False

    for slug, title in ALL_PAGES.items():
        create_wiki_page(wiki_dir, slug, title, business_name, today)
        print(f"  Created _engine/wiki/{slug}.md")

    create_index(wiki_dir, business_name, ALL_PAGES, today)
    print("  Created _engine/wiki/index.md")
    create_log(wiki_dir, business_name, len(ALL_PAGES), today)
    print("  Created _engine/wiki/log.md")
    create_config(engine_dir / "wiki-config.json", business_name, project_name,
                  ALL_PAGES, today)
    print("  Created _engine/wiki-config.json")

    print(f"\nSingle-program wiki initialized for {business_name}")
    print(f"  Location: {wiki_dir}")
    print(f"  Pages: {len(ALL_PAGES)}")
    return True


def init_shared(client_dir, business_name, today):
    """Initialize the client-root _engine/ folder for multi-program clients
    (formerly _shared/ — shared brand DNA)."""
    shared_dir = client_dir / "_engine"
    wiki_dir = shared_dir / "wiki"
    for d in [wiki_dir, shared_dir / "working", shared_dir / "sources"]:
        d.mkdir(parents=True, exist_ok=True)

    if (wiki_dir / "index.md").exists():
        print(f"Shared wiki already exists at {wiki_dir}")
        return False

    for slug, title in SHARED_PAGES.items():
        create_wiki_page(wiki_dir, slug, title, business_name, today)
        print(f"  Created _engine/wiki/{slug}.md")

    create_index(wiki_dir, business_name, SHARED_PAGES, today, index_type="shared")
    print("  Created _engine/wiki/index.md")
    create_log(wiki_dir, business_name, len(SHARED_PAGES), today, log_type="shared")
    print("  Created _engine/wiki/log.md")
    create_config(shared_dir / "wiki-config.json", business_name, "",
                  SHARED_PAGES, today, config_type="shared")
    print("  Created _engine/wiki-config.json")

    print(f"\nShared brand DNA initialized for {business_name}")
    print(f"  Location: {shared_dir}")
    print(f"  Pages: {len(SHARED_PAGES)}")
    return True


def init_program(client_dir, business_name, program_name, today):
    """Initialize a new program folder under a multi-program client.
    Each program gets its own {Program}/_engine/{wiki,sources,working}."""
    shared_dir = client_dir / "_engine"
    if not shared_dir.exists():
        print(f"ERROR: client-root _engine/ not found at {shared_dir}")
        print("Run with --shared first to create the shared brand DNA folder.")
        return False

    program_dir = client_dir / program_name
    program_engine = program_dir / "_engine"
    wiki_dir = program_engine / "wiki"
    for d in [wiki_dir, program_engine / "sources", program_engine / "working"]:
        d.mkdir(parents=True, exist_ok=True)

    if (wiki_dir / "index.md").exists():
        print(f"Program wiki already exists at {wiki_dir}")
        print("Use INGEST operation to add new data, not init.")
        return False

    for slug, title in PROGRAM_PAGES.items():
        create_wiki_page(wiki_dir, slug, title, f"{business_name} — {program_name}", today)
        print(f"  Created {program_name}/_engine/wiki/{slug}.md")

    create_index(wiki_dir, f"{business_name} — {program_name}",
                 PROGRAM_PAGES, today, index_type="program")
    print(f"  Created {program_name}/_engine/wiki/index.md")
    create_log(wiki_dir, f"{business_name} — {program_name}",
               len(PROGRAM_PAGES), today, log_type="program")
    print(f"  Created {program_name}/_engine/wiki/log.md")
    create_config(program_engine / "wiki-config.json", business_name, program_name,
                  PROGRAM_PAGES, today, config_type="program", parent="../../_engine")
    print(f"  Created {program_name}/_engine/wiki-config.json")

    # Update shared config with new program
    shared_config_path = shared_dir / "wiki-config.json"
    if shared_config_path.exists():
        shared_config = json.loads(shared_config_path.read_text(encoding="utf-8"))
        if program_name not in shared_config.get("programs", []):
            shared_config.setdefault("programs", []).append(program_name)
            shared_config["last_updated"] = today
            shared_config_path.write_text(json.dumps(shared_config, indent=2), encoding="utf-8")
            print(f"  Updated _engine/wiki-config.json — added program '{program_name}'")

    # Update shared index with program link
    shared_index = shared_dir / "wiki" / "index.md"
    if shared_index.exists():
        content = shared_index.read_text(encoding="utf-8")
        # Link from {Client}/_engine/wiki/index.md → {Client}/{Program}/_engine/wiki/index.md
        program_link = f"../../{program_name}/_engine/wiki/index.md"
        if "_No programs initialized yet._" in content:
            content = content.replace(
                "_No programs initialized yet._",
                f"- [{program_name}]({program_link}) — Initialized {today}"
            )
        elif f"[{program_name}]" not in content:
            # Append to programs list
            content = content.replace(
                "\n## Sources",
                f"- [{program_name}]({program_link}) — Initialized {today}\n\n## Sources"
            )
        shared_index.write_text(content, encoding="utf-8")

    print(f"\nProgram wiki initialized for {program_name}")
    print(f"  Location: {program_dir}")
    print(f"  Pages: {len(PROGRAM_PAGES)}")
    print(f"  Brand config: ../../_engine/brand-config.json")
    return True


def migrate_to_multi(existing_dir, business_name, program_name, today):
    """Migrate an existing single-program client to multi-program structure.
    The existing program's _engine/ stays in place; the client-root _engine/ is created
    and the four shared brand-DNA pages + brand-config.json copy up."""
    client_dir = existing_dir.parent
    shared_dir = client_dir / "_engine"

    if shared_dir.exists():
        print(f"ERROR: client-root _engine/ already exists at {shared_dir}")
        print("Client is already multi-program. Use --program to add a new program.")
        return False

    print(f"Migrating {business_name} to multi-program structure...")
    print(f"  Existing program folder: {existing_dir.name}")
    print(f"  Will become first program: {existing_dir.name}")

    # 1. Create client-root _engine/
    init_shared(client_dir, business_name, today)

    # 2. Copy shared files from existing program's _engine/ to the client-root _engine/
    existing_engine = existing_dir / "_engine"
    existing_wiki = existing_engine / "wiki"
    shared_wiki = shared_dir / "wiki"

    files_to_move_wiki = ["business.md", "brand-identity.md", "digital-presence.md", "offerings.md"]
    files_to_move_root = ["brand-config.json"]

    for fname in files_to_move_wiki:
        src = existing_wiki / fname
        dst = shared_wiki / fname
        if src.exists():
            # Overwrite the empty template with actual content
            shutil.copy2(str(src), str(dst))
            print(f"  Copied {existing_dir.name}/_engine/wiki/{fname} → _engine/wiki/{fname}")

    for fname in files_to_move_root:
        src = existing_engine / fname
        dst = shared_dir / fname
        if src.exists():
            shutil.copy2(str(src), str(dst))
            print(f"  Copied {existing_dir.name}/_engine/{fname} → _engine/{fname}")

    # 3. Update existing program's wiki-config.json
    existing_config_path = existing_engine / "wiki-config.json"
    if existing_config_path.exists():
        config = json.loads(existing_config_path.read_text(encoding="utf-8"))
        config["type"] = "program"
        config["program_name"] = existing_dir.name
        config["parent"] = "../../_engine"
        config["brand_config"] = "../../_engine/brand-config.json"
        config["last_updated"] = today
        existing_config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")
        print(f"  Updated {existing_dir.name}/_engine/wiki-config.json → type: program")

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
        f"- [{existing_dir.name}](../../{existing_dir.name}/_engine/wiki/index.md) — Migrated {today}"
    )
    shared_index.write_text(content, encoding="utf-8")

    # 6. Log migration
    log_entry = f"- **MIGRATION** Converted from single-program to multi-program. Brand DNA moved to client-root _engine/. Existing research remains in {existing_dir.name}/_engine/.\n"

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
    print(f"  client-root _engine/ created with brand DNA")
    print(f"  {existing_dir.name}/ updated as first program")
    print(f"  Ready to add new programs with --program")
    return True


def detect_structure(client_dir):
    """Detect whether a client folder is single-program, multi-program, or new.
    Multi-program: client-root _engine/wiki-config.json with type: shared.
    Single-program: any sub-business has _engine/wiki-config.json."""
    client_dir = Path(client_dir)

    if not client_dir.exists():
        print(f"NOT_FOUND — {client_dir} does not exist")
        return "not_found"

    shared_dir = client_dir / "_engine"
    shared_config = shared_dir / "wiki-config.json"
    if shared_dir.exists() and shared_config.exists():
        config = json.loads(shared_config.read_text(encoding="utf-8"))
        if config.get("type") == "shared":
            programs = config.get("programs", [])
            print(f"MULTI_PROGRAM — {len(programs)} program(s): {', '.join(programs)}")
            print(f"  Shared: {shared_dir}")
            for p in programs:
                prog_dir = client_dir / p
                status = "EXISTS" if prog_dir.exists() else "MISSING"
                print(f"  Program '{p}': {status}")
            return "multi_program"

    # Check subdirectories for _engine/wiki-config.json (single-program)
    for subdir in client_dir.iterdir():
        if not subdir.is_dir() or subdir.name == "_engine":
            continue
        sub_config = subdir / "_engine" / "wiki-config.json"
        if sub_config.exists():
            config = json.loads(sub_config.read_text(encoding="utf-8"))
            ctype = config.get("type", "standard")
            print(f"SINGLE_PROGRAM — {subdir.name}/ (type: {ctype})")
            print(f"  Wiki: {subdir / '_engine' / 'wiki'}")
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
                       help='Initialize client-root _engine/ folder for multi-program client (formerly _shared/)')
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
