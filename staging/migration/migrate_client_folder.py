#!/usr/bin/env python3
"""
Migrate a client folder from the old layout to the `_engine/` convention.

OLD layout (any of):
  {Client}/                              ← single-program (or program inside multi-program)
    wiki/                                ← knowledge graph
    sources/                             ← raw inputs
    working/                             ← intermediate files
    outputs/                             ← presentable HTML/MP4/PDF (some clients)
    deliverables/                        ← legacy mixed bin (some clients)
    wiki-config.json                     ← config
    {top-level files}

  {Client}/                              ← multi-program
    _shared/                             ← cross-program backend
      wiki/
      sources/
      working/                           ← may or may not exist
      deliverables/
      wiki-config.json
    {Program A}/                         ← each program: same single-program shape
      wiki/, sources/, working/, outputs/, ...

NEW layout:
  {Client}/
    {presentables}.html, .mp4, .pdf, .csv     ← at root
    campaign-setup/                            ← folder bundle at root
    _engine/                                   ← was _shared/, or new
      wiki/
      sources/
      working/
      brand-config.json                        ← was _shared/deliverables/brand-config.json
      wiki-config.json
    {Program A}/
      {presentables}.html, .mp4, .pdf, .csv   ← at program root
      _engine/
        wiki/
        sources/
        working/
        wiki-config.json

Usage:
    python3 migrate_client_folder.py --dry-run "/Users/digischola/Desktop/{Client Name}"
    python3 migrate_client_folder.py "/Users/digischola/Desktop/{Client Name}"

The script:
  1. Detects single-program vs multi-program (presence of program subfolders or _shared/)
  2. For each scope (client root for single-program, _shared+each program for multi-program):
     - Creates _engine/
     - Moves wiki/, sources/, working/ inside _engine/
     - Moves wiki-config.json inside _engine/
     - Hoists presentable files from outputs/ to scope root
     - Reconciles deliverables/ — HTML/PDF/MP4/CSV bundles to root, MD/JSON to _engine/working/
  3. For multi-program:
     - Renames _shared/ to _engine/ at client root
     - Hoists _shared/deliverables/brand-config.json to _engine/brand-config.json
     - Reconciles _shared/deliverables/ contents per the same rules
  4. Logs every move to {scope}/_engine/wiki/log.md (append-only)
  5. Special-case: leaves Sri Krishna Mandir's site/ alone (read-only Lovable mirror)

After migration, run validators:
  python3 ~/Desktop/.claude/skills/business-analysis/scripts/validate_all.py "{Client}/_engine"
  (and for each program in multi-program clients)
"""

import argparse
import datetime
import json
import shutil
import sys
from pathlib import Path

PRESENTABLE_EXTENSIONS = {'.html', '.mp4', '.mov', '.webm', '.pdf', '.png', '.jpg', '.jpeg', '.csv'}
PRESENTABLE_FOLDERS = {'campaign-setup'}
PRESERVED_SPECIAL = {'site'}  # Sri Krishna Mandir's read-only Lovable mirror

DRY_RUN = False
LOG_LINES = []
SKIP_PROGRAMS = set()


def log(msg, indent=0):
    line = ' ' * indent + msg
    print(line)
    LOG_LINES.append(line)


def is_presentable_file(path: Path) -> bool:
    if not path.is_file():
        return False
    return path.suffix.lower() in PRESENTABLE_EXTENSIONS


def is_presentable_folder(path: Path) -> bool:
    if not path.is_dir():
        return False
    if path.name in PRESENTABLE_FOLDERS:
        return True
    # Folder bundle: has its own index.html + assets
    if (path / 'index.html').is_file() and any(
        c.is_dir() and c.name in {'assets', 'images', 'css', 'js'} for c in path.iterdir()
    ):
        return True
    return False


def safe_move(src: Path, dst: Path):
    if DRY_RUN:
        log(f'[dry-run] mv "{src}" -> "{dst}"', indent=4)
        return
    if dst.exists():
        log(f'[SKIP] target exists: {dst}', indent=4)
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dst))
    log(f'mv "{src.name}" -> "{dst.relative_to(src.parent.parent) if src.parent.parent in dst.parents else dst}"', indent=4)


def migrate_scope(scope: Path, scope_label: str, is_client_root_in_multi: bool = False):
    """Migrate a single scope folder (single-program client, or _shared/, or one program).

    For is_client_root_in_multi=True, the scope is actually the original `_shared/` folder
    that is being renamed to `_engine/` at client root. We don't operate on a "scope"
    folder per se — we restructure the parent.
    """
    log(f'\n--- Migrating scope: {scope_label} ({scope}) ---')

    engine = scope / '_engine'

    if not DRY_RUN:
        engine.mkdir(exist_ok=True)

    # 1. Move wiki/ -> _engine/wiki/
    wiki_old = scope / 'wiki'
    wiki_new = engine / 'wiki'
    if wiki_old.is_dir() and wiki_old != wiki_new:
        safe_move(wiki_old, wiki_new)

    # 2. Move sources/ -> _engine/sources/
    sources_old = scope / 'sources'
    sources_new = engine / 'sources'
    if sources_old.is_dir() and sources_old != sources_new:
        safe_move(sources_old, sources_new)

    # 3. Move working/ -> _engine/working/
    working_old = scope / 'working'
    working_new = engine / 'working'
    if working_old.is_dir() and working_old != working_new:
        safe_move(working_old, working_new)

    # 4. Move wiki-config.json -> _engine/wiki-config.json
    cfg_old = scope / 'wiki-config.json'
    cfg_new = engine / 'wiki-config.json'
    if cfg_old.is_file() and cfg_old != cfg_new:
        safe_move(cfg_old, cfg_new)

    # 5. Hoist outputs/ contents to scope root, then remove outputs/
    outputs = scope / 'outputs'
    if outputs.is_dir():
        for child in sorted(outputs.iterdir()):
            if child.name == '.DS_Store':
                if not DRY_RUN:
                    child.unlink()
                continue
            target = scope / child.name
            safe_move(child, target)
        try:
            if not DRY_RUN:
                outputs.rmdir()
                log(f'removed empty outputs/', indent=4)
        except OSError as e:
            log(f'!! could not remove outputs/: {e}', indent=4)

    # 6. Reconcile deliverables/ — HTML/PDF/MP4/CSV bundles to root, MD/JSON to _engine/working/
    deliverables = scope / 'deliverables'
    if deliverables.is_dir():
        engine_working = engine / 'working'
        if not DRY_RUN:
            engine_working.mkdir(exist_ok=True)
        for child in sorted(deliverables.iterdir()):
            if child.name == '.DS_Store':
                if not DRY_RUN:
                    child.unlink()
                continue
            if is_presentable_folder(child) or is_presentable_file(child):
                target = scope / child.name
            elif child.is_dir():
                # Other dir bundle (treat as working scratch)
                target = engine_working / child.name
            else:
                # Markdown / JSON / intermediate CSV / etc.
                target = engine_working / child.name
            safe_move(child, target)
        try:
            if not DRY_RUN:
                deliverables.rmdir()
                log(f'removed empty deliverables/', indent=4)
        except OSError as e:
            log(f'!! could not remove deliverables/: {e}', indent=4)


def detect_program_subdirs(client_dir: Path):
    """Detect program subfolders (have wiki/ or outputs/ or deliverables/ or _engine/)."""
    programs = []
    for child in sorted(client_dir.iterdir()):
        if not child.is_dir():
            continue
        if child.name.startswith('.') or child.name.startswith('_'):
            continue
        if child.name in PRESERVED_SPECIAL:
            continue
        if is_presentable_folder(child):
            continue
        # Looks like a program if it has the legacy markers
        if any((child / sub).is_dir() for sub in ('wiki', 'outputs', 'deliverables', 'working', '_engine')):
            programs.append(child)
    return programs


def migrate_client(client_dir: Path):
    log(f'\n{"="*70}\nClient: {client_dir.name}\n{"="*70}')

    shared = client_dir / '_shared'
    is_multi = shared.is_dir() or len(detect_program_subdirs(client_dir)) > 0

    if is_multi:
        log('Multi-program client detected.')

        # Step 1: locate the "client engine" folder. It's either _shared/ (legacy,
        # to be renamed) or _engine/ (already migrated). We process its internals
        # FIRST while it still has its original name, then rename if needed.
        engine_at_root = client_dir / '_engine'
        if shared.is_dir() and engine_at_root.is_dir():
            log(f'!! both _shared/ and _engine/ exist at {client_dir} — manual review needed', indent=2)
            sys.exit(2)

        client_engine = shared if shared.is_dir() else engine_at_root

        if client_engine.is_dir():
            # Process deliverables/ inside the client-engine folder: md/json stay inside
            # working/ (will become _engine/working/), presentables hoist to client root,
            # brand-config.json goes to client-engine/ root.
            inner_deliverables = client_engine / 'deliverables'
            inner_outputs = client_engine / 'outputs'
            inner_working = client_engine / 'working'

            if inner_deliverables.is_dir():
                log(f'reconcile {client_dir.name}/{client_engine.name}/deliverables/ ...')
                if not DRY_RUN:
                    inner_working.mkdir(exist_ok=True)
                for child in sorted(inner_deliverables.iterdir()):
                    if child.name == '.DS_Store':
                        if not DRY_RUN:
                            child.unlink()
                        continue
                    if child.name == 'brand-config.json':
                        # Special: brand-config goes to client-engine root (top of _engine/)
                        target = client_engine / 'brand-config.json'
                    elif is_presentable_file(child) or is_presentable_folder(child):
                        target = client_dir / child.name
                    elif child.is_dir():
                        target = inner_working / child.name
                    else:
                        target = inner_working / child.name
                    safe_move(child, target)
                try:
                    if not DRY_RUN:
                        inner_deliverables.rmdir()
                        log(f'removed empty {client_engine.name}/deliverables/', indent=4)
                except OSError as e:
                    log(f'!! could not remove {client_engine.name}/deliverables/: {e}', indent=4)

            if inner_outputs.is_dir():
                log(f'hoist {client_dir.name}/{client_engine.name}/outputs/ contents to client root ...')
                for child in sorted(inner_outputs.iterdir()):
                    if child.name == '.DS_Store':
                        if not DRY_RUN:
                            child.unlink()
                        continue
                    target = client_dir / child.name
                    safe_move(child, target)
                try:
                    if not DRY_RUN:
                        inner_outputs.rmdir()
                        log(f'removed empty {client_engine.name}/outputs/', indent=4)
                except OSError as e:
                    log(f'!! could not remove {client_engine.name}/outputs/: {e}', indent=4)

        # Step 2: NOW rename _shared/ -> _engine/ at client root (after internal reconciliation)
        if shared.is_dir():
            log(f'rename _shared/ -> _engine/ at client root')
            if not DRY_RUN:
                shared.rename(engine_at_root)
            else:
                log(f'[dry-run] mv "{shared}" -> "{engine_at_root}"', indent=4)

        # Step 2: migrate each program subdir (skipping any in SKIP_PROGRAMS)
        programs = detect_program_subdirs(client_dir)
        for prog in programs:
            if prog.name in SKIP_PROGRAMS:
                log(f'\n--- SKIPPING program: {prog.name} (per --skip-program flag) ---')
                continue
            migrate_scope(prog, f'program: {prog.name}')
    else:
        log('Single-program client detected.')
        migrate_scope(client_dir, 'client root')

    # Append migration log
    write_log(client_dir)


def write_log(client_dir: Path):
    log_dir = client_dir / '_engine' / 'wiki'
    log_path = log_dir / 'log.md'
    if DRY_RUN:
        log(f'\n[dry-run] would append migration entry to {log_path}')
        return
    log_dir.mkdir(parents=True, exist_ok=True)
    today = datetime.date.today().isoformat()
    block = f'\n## {today} _engine/ migration\n\n'
    block += '\n'.join('- ' + ln for ln in LOG_LINES)
    block += '\n'
    if log_path.exists():
        existing = log_path.read_text(encoding='utf-8')
        log_path.write_text(existing + block, encoding='utf-8')
    else:
        log_path.write_text('# Wiki Log\n' + block, encoding='utf-8')
    print(f'\nappended migration entry to {log_path}')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--skip-program', action='append', default=[],
                        help='Program folder name to skip (e.g. "Weekend Love Feast"). Repeatable.')
    parser.add_argument('clients', nargs='+', help='Client folder paths')
    args = parser.parse_args()

    global DRY_RUN, SKIP_PROGRAMS
    DRY_RUN = args.dry_run
    SKIP_PROGRAMS = set(args.skip_program)

    if DRY_RUN:
        log('=== DRY RUN — no files will be moved ===\n')

    for client_path in args.clients:
        global LOG_LINES
        LOG_LINES = []
        client_dir = Path(client_path)
        if not client_dir.is_dir():
            log(f'!! not a directory: {client_path}')
            continue
        migrate_client(client_dir)


if __name__ == '__main__':
    main()
