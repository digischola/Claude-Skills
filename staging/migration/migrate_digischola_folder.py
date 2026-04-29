#!/usr/bin/env python3
"""
Migrate the Digischola personal-brand folder to the `_engine/` convention.

OLD layout:
  Digischola/
    index.html
    strategic-context.md
    *.log
    tools/
    brand/
      _mining/, _research/                          ← skill scratch
      brand-identity.md, brand-wiki.md              ← brand DNA wiki (md)
      channel-playbook.md, credentials.md
      icp.md, pillars.md
      voice-guide.md, voice-flavor.md, voice-lock.md
      idea-bank.json
      weekly-ritual.state.json
      wiki-config.json
      face-samples/, voice-samples/, music/
      hyperframes-scenes/, remotion-studio/
      weekly-ritual/                                ← logs/state subdir
      queue/                                        ← daily review surface
      calendars/                                    ← weekly plans
      performance/                                  ← weekly reviews
      videos/                                       ← finished video projects
      social-images/                                ← finished images

NEW layout (Mayank's daily review surface stays at brand/ top):
  Digischola/
    index.html
    strategic-context.md
    *.log
    tools/
    brand/
      queue/                                        ← STAYS at top
      calendars/                                    ← STAYS at top
      performance/                                  ← STAYS at top
      videos/                                       ← STAYS at top
      social-images/                                ← STAYS at top
      _engine/
        wiki/
          brand-identity.md, brand-wiki.md          ← brand DNA wiki moves here
          channel-playbook.md, credentials.md
          icp.md, pillars.md
          voice-guide.md, voice-flavor.md, voice-lock.md
        _mining/
        _research/
        idea-bank.json
        weekly-ritual.state.json
        wiki-config.json
        face-samples/, voice-samples/, music/      ← media assets used by skills
        hyperframes-scenes/, remotion-studio/      ← build projects
        weekly-ritual/                              ← logs/state
        log.md                                      ← migration audit trail

Usage:
    python3 migrate_digischola_folder.py --dry-run
    python3 migrate_digischola_folder.py
"""

import argparse
import datetime
import shutil
import sys
from pathlib import Path

ROOT = Path('/Users/digischola/Desktop/Digischola')
BRAND = ROOT / 'brand'

# Items that move to brand/_engine/wiki/ (brand DNA markdown)
BRAND_DNA_FILES = [
    'brand-identity.md',
    'brand-wiki.md',
    'channel-playbook.md',
    'credentials.md',
    'icp.md',
    'pillars.md',
    'voice-guide.md',
    'voice-flavor.md',
    'voice-lock.md',
]

# Items that move to brand/_engine/ (top of engine)
ENGINE_FILES = [
    'idea-bank.json',
    'weekly-ritual.state.json',
    'wiki-config.json',
]

# Folders that move to brand/_engine/
ENGINE_FOLDERS = [
    '_mining',
    '_research',
    'face-samples',
    'voice-samples',
    'music',
    'hyperframes-scenes',
    'remotion-studio',
    'weekly-ritual',
]

# Folders that STAY at brand/ top
TOP_LEVEL_FOLDERS = [
    'queue',
    'calendars',
    'performance',
    'videos',
    'social-images',
]

DRY_RUN = False
LOG_LINES = []


def log(msg, indent=0):
    line = ' ' * indent + msg
    print(line)
    LOG_LINES.append(line)


def safe_move(src: Path, dst: Path):
    if DRY_RUN:
        log(f'[dry-run] mv "{src}" -> "{dst}"', indent=2)
        return
    if dst.exists():
        log(f'[SKIP] target exists: {dst}', indent=2)
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dst))
    log(f'mv {src.name} -> {dst.relative_to(BRAND)}', indent=2)


def migrate():
    log(f'\n{"="*70}\nDigischola personal-brand migration\n{"="*70}')

    if not BRAND.is_dir():
        print(f'!! brand folder not found: {BRAND}')
        sys.exit(1)

    engine = BRAND / '_engine'
    engine_wiki = engine / 'wiki'

    if not DRY_RUN:
        engine.mkdir(exist_ok=True)
        engine_wiki.mkdir(exist_ok=True)

    log(f'\n--- Brand DNA wiki files -> _engine/wiki/ ---')
    for fname in BRAND_DNA_FILES:
        src = BRAND / fname
        if src.is_file():
            safe_move(src, engine_wiki / fname)
        else:
            log(f'(no {fname})', indent=2)

    log(f'\n--- Skill state files -> _engine/ ---')
    for fname in ENGINE_FILES:
        src = BRAND / fname
        if src.is_file():
            safe_move(src, engine / fname)
        else:
            log(f'(no {fname})', indent=2)

    log(f'\n--- Skill scratch / media folders -> _engine/ ---')
    for fname in ENGINE_FOLDERS:
        src = BRAND / fname
        if src.is_dir():
            safe_move(src, engine / fname)
        else:
            log(f'(no {fname})', indent=2)

    log(f'\n--- Workflow surface (staying at brand/ top) ---')
    for fname in TOP_LEVEL_FOLDERS:
        src = BRAND / fname
        if src.is_dir():
            log(f'OK {fname}/ stays at brand/ top', indent=2)
        else:
            log(f'(no {fname}/)', indent=2)

    write_log()


def write_log():
    log_path = BRAND / '_engine' / 'log.md'
    if DRY_RUN:
        log(f'\n[dry-run] would append migration entry to {log_path}')
        return
    log_path.parent.mkdir(parents=True, exist_ok=True)
    today = datetime.date.today().isoformat()
    block = f'\n## {today} _engine/ migration\n\n'
    block += '\n'.join('- ' + ln for ln in LOG_LINES)
    block += '\n'
    if log_path.exists():
        existing = log_path.read_text(encoding='utf-8')
        log_path.write_text(existing + block, encoding='utf-8')
    else:
        log_path.write_text('# Digischola Brand Engine Log\n' + block, encoding='utf-8')
    print(f'\nappended migration entry to {log_path}')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()

    global DRY_RUN
    DRY_RUN = args.dry_run

    if DRY_RUN:
        log('=== DRY RUN — no files will be moved ===\n')

    migrate()


if __name__ == '__main__':
    main()
