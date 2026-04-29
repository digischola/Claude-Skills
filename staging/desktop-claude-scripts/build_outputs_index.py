#!/usr/bin/env python3
"""
Auto-generate index.html for client folders under the `_engine/` convention.

Scans every active client/program folder and writes a clickable index.html that
lists every presentable (HTML / MP4 / PDF / CSV bundle) sitting at the folder
root. Skill internals live in `_engine/` and are NOT listed in the index.

Folder shape:
  {Client}/[{Program}/]
    {presentables}.{html,mp4,pdf,csv}    <- listed in index
    campaign-setup/                        <- folder bundle (listed)
    _engine/                               <- skill-only state (NOT listed)
    index.html                             <- this file (auto-generated)
    start.command                          <- local server launcher

For multi-program clients (detected by presence of `_engine/` at root AND
program subfolders), the top-level client folder gets an index.html linking to
each program's index.

Usage:
  python3 ~/.claude/scripts/build_outputs_index.py "{Client A}" "{Client B}" ...

Adopted 2026-04-29 (replaces the prior `outputs/` migration mode).
"""

import argparse
import datetime
from pathlib import Path

PRESENTABLE_EXTENSIONS = {'.html', '.mp4', '.mov', '.webm', '.pdf', '.png', '.jpg', '.jpeg', '.csv'}
PRESENTABLE_FOLDERS = {'campaign-setup'}
SKIP_NAMES = {'_engine', '.git', '.DS_Store', '__pycache__', 'node_modules', 'site',
              'index.html', 'start.command', '.gitignore'}


def log(msg, indent=0):
    print(' ' * indent + msg)


def is_skip(path: Path) -> bool:
    if path.name in SKIP_NAMES:
        return True
    if path.name.startswith('.'):
        return True
    return False


def _looks_like_bundle(folder: Path) -> bool:
    """Folder bundle = has its own index.html (e.g. landing-page-builder output)."""
    return (folder / 'index.html').is_file()


def collect_presentables(folder: Path):
    """List presentable files / folder bundles at folder root."""
    items = []
    for child in sorted(folder.iterdir()):
        if is_skip(child):
            continue
        if child.is_dir():
            if child.name in PRESENTABLE_FOLDERS or _looks_like_bundle(child):
                items.append({
                    'kind': classify_for_index(child),
                    'name': child.name,
                    'href': f'{child.name}/',
                    'is_dir': True,
                    'child_count': sum(
                        1 for f in child.rglob('*')
                        if f.is_file() and f.name != '.DS_Store'
                    ),
                })
            continue
        if child.suffix.lower() in PRESENTABLE_EXTENSIONS:
            items.append({
                'kind': classify_for_index(child),
                'name': child.name,
                'href': child.name,
                'is_dir': False,
                'size_kb': max(1, child.stat().st_size // 1024),
            })
    return items


def classify_for_index(path: Path) -> str:
    name = path.name.lower()
    if path.is_dir():
        if 'campaign-setup' in name:
            return 'Campaign bulk-import'
        return 'Folder bundle'
    if name.endswith(('.mp4', '.mov', '.webm')):
        return 'Video'
    if name.endswith('.pdf'):
        return 'Document'
    if name.endswith('.csv'):
        return 'CSV'
    if name.endswith(('.png', '.jpg', '.jpeg')):
        return 'Image'
    if name.endswith('.html'):
        if 'audit' in name:
            return 'Audit dashboard'
        if 'research' in name:
            return 'Research dashboard'
        if 'strategy' in name:
            return 'Strategy dashboard'
        if 'landing-page' in name or 'lp' in name or 'page' in name:
            return 'Landing page'
        return 'Dashboard'
    return 'Other'


START_COMMAND_TEMPLATE = '''#!/bin/bash
# Auto-generated. Double-click to launch index in a local browser session.
# Closes when you press Ctrl+C in the Terminal window that opens.
cd "$(dirname "$0")"
PORT=$(python3 -c 'import socket; s=socket.socket(); s.bind(("", 0)); print(s.getsockname()[1]); s.close()')
echo "Starting local server on port $PORT..."
python3 -m http.server $PORT >/dev/null 2>&1 &
SERVER_PID=$!
sleep 1
open "http://localhost:$PORT/index.html"
echo ""
echo "Index open at http://localhost:$PORT/"
echo "Press Ctrl+C in this window when done."
trap "kill $SERVER_PID 2>/dev/null; echo ''; echo 'Server stopped.'; exit 0" INT
wait $SERVER_PID
'''


def write_start_command(folder: Path):
    cmd_path = folder / 'start.command'
    cmd_path.write_text(START_COMMAND_TEMPLATE, encoding='utf-8')
    cmd_path.chmod(0o755)


def render_index(title: str, items: list, is_root: bool = False, programs: list = None) -> str:
    today = datetime.date.today().isoformat()

    groups = {}
    for item in items:
        groups.setdefault(item['kind'], []).append(item)

    group_order = [
        'Research dashboard', 'Strategy dashboard', 'Audit dashboard',
        'Landing page', 'Video', 'Document', 'Campaign bulk-import',
        'Dashboard', 'Folder bundle', 'CSV', 'Image', 'Other'
    ]
    ordered_groups = [(g, groups[g]) for g in group_order if g in groups]
    for g in groups:
        if g not in [og[0] for og in ordered_groups]:
            ordered_groups.append((g, groups[g]))

    cards_html = []
    for group_name, group_items in ordered_groups:
        cards_html.append(f'<h2>{group_name}</h2><div class="grid">')
        for item in group_items:
            meta = f'{item["child_count"]} files' if item.get('is_dir') else f'{item["size_kb"]} KB'
            cards_html.append(f'''
                <a class="card" href="{item['href']}">
                    <div class="card-name">{item['name']}</div>
                    <div class="card-meta">{meta}</div>
                </a>
            ''')
        cards_html.append('</div>')

    if is_root and programs:
        prog_html = '<h2>Programs</h2><div class="grid">'
        for prog in programs:
            prog_html += f'''
                <a class="card card-program" href="{prog}/index.html">
                    <div class="card-name">{prog}</div>
                    <div class="card-meta">Program folder</div>
                </a>
            '''
        prog_html += '</div>'
        cards_html.insert(0, prog_html)

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} — Index</title>
<style>
:root {{
    --bg: #0e1116;
    --surface: #161b22;
    --border: #30363d;
    --text: #e6edf3;
    --muted: #8b949e;
    --accent: #58a6ff;
    --accent-hover: #79b8ff;
}}
* {{ box-sizing: border-box; }}
body {{
    margin: 0; padding: 40px 24px;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif;
    background: var(--bg); color: var(--text);
    max-width: 1100px; margin: 0 auto;
}}
header {{ margin-bottom: 32px; padding-bottom: 24px; border-bottom: 1px solid var(--border); }}
h1 {{ font-size: 28px; margin: 0 0 4px; font-weight: 600; }}
.sub {{ color: var(--muted); font-size: 14px; }}
h2 {{
    font-size: 13px; text-transform: uppercase; letter-spacing: 0.08em;
    color: var(--muted); margin: 32px 0 12px; font-weight: 600;
}}
.grid {{
    display: grid; gap: 12px;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
}}
.card {{
    display: block; padding: 16px 18px;
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 8px; text-decoration: none; color: var(--text);
    transition: border-color 0.15s, transform 0.15s;
}}
.card:hover {{ border-color: var(--accent); transform: translateY(-1px); }}
.card-name {{ font-size: 14px; font-weight: 500; margin-bottom: 4px; word-break: break-word; }}
.card-meta {{ color: var(--muted); font-size: 12px; }}
.card-program {{ background: linear-gradient(135deg, #1f2937 0%, #161b22 100%); }}
footer {{ margin-top: 48px; color: var(--muted); font-size: 12px; }}
.banner {{
    background: rgba(240, 136, 62, 0.08); border: 1px solid rgba(240, 136, 62, 0.3);
    border-radius: 8px; padding: 12px 16px; margin-bottom: 24px;
    color: #f0883e; font-size: 13px;
}}
.banner code {{ background: rgba(0,0,0,0.3); padding: 2px 6px; border-radius: 4px; color: #ffd6a8; }}
</style>
</head>
<body>
<header>
    <h1>{title}</h1>
    <div class="sub">Index · generated {today}</div>
</header>
<div class="banner" id="file-banner" style="display:none">
    ⚠ Links not opening? Browsers block file:// navigation for security.
    Quit this tab, then <strong>double-click <code>start.command</code></strong> in this folder instead.
    It launches a local server so all links (HTML, images, MP4 videos, carousel folders) open correctly.
</div>
<script>
if (location.protocol === 'file:') {{
    document.getElementById('file-banner').style.display = 'block';
}}
</script>
{''.join(cards_html) or '<p class="sub">No presentables yet.</p>'}
<footer>
    <p>This file is auto-generated. Skill internals (markdown reports, JSON briefs, intermediate CSVs) are in <code>_engine/</code>.</p>
</footer>
</body>
</html>
'''


def build_program_index(program_dir: Path):
    items = collect_presentables(program_dir)
    log(f'\nProgram: {program_dir.name}')
    log(f'{len(items)} presentables', indent=2)
    html = render_index(program_dir.name, items, is_root=False)
    (program_dir / 'index.html').write_text(html, encoding='utf-8')
    write_start_command(program_dir)
    log('wrote index.html + start.command', indent=2)


def has_engine(folder: Path) -> bool:
    return (folder / '_engine').is_dir()


def detect_program_subdirs(client_dir: Path):
    """A program subdir has its own _engine/ (new) or wiki/ (un-migrated, fallback).

    Program detection takes priority over bundle detection: a program folder
    has _engine/ AND an auto-generated index.html (which would otherwise mark
    it as a "presentable bundle"). Check program markers first.
    """
    programs = []
    for child in sorted(client_dir.iterdir()):
        if not child.is_dir():
            continue
        if child.name in SKIP_NAMES or child.name.startswith('.') or child.name == '_engine':
            continue
        # Program markers first — a program always has _engine/ or wiki/.
        if has_engine(child) or (child / 'wiki').is_dir() or (child / 'outputs').is_dir():
            programs.append(child)
            continue
        # Otherwise skip presentable bundles (folders with own index.html that aren't programs).
        if child.name in PRESENTABLE_FOLDERS or _looks_like_bundle(child):
            continue
    return programs


def build_client_index(client_dir: Path):
    log(f'\n{"="*60}\nClient: {client_dir.name}\n{"="*60}')

    program_subdirs = detect_program_subdirs(client_dir)

    if program_subdirs:
        log(f'Multi-program: {len(program_subdirs)} programs')
        for prog in program_subdirs:
            build_program_index(prog)
        client_items = collect_presentables(client_dir)
        programs = [p.name for p in program_subdirs]
        html = render_index(client_dir.name, client_items, is_root=True, programs=programs)
        (client_dir / 'index.html').write_text(html, encoding='utf-8')
        write_start_command(client_dir)
        log(f'\nwrote top-level index.html + start.command (links to {len(programs)} programs, {len(client_items)} client-wide items)', indent=2)
    else:
        build_program_index(client_dir)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('clients', nargs='*', help='Client folder paths')
    args = parser.parse_args()

    for client_path in args.clients:
        client_dir = Path(client_path)
        if not client_dir.is_dir():
            log(f'!! not a directory: {client_path}')
            continue
        build_client_index(client_dir)


if __name__ == '__main__':
    main()
