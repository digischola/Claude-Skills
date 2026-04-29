#!/usr/bin/env python3
"""
Digischola personal-brand index builder.

Generates ~/Desktop/Digischola/index.html — a single double-clickable entry point
showing what needs Mayank's attention right now:

- queue/pending-approval/ items grouped by channel/format (LinkedIn / X / Instagram / Reel)
- Latest calendar (this week's plan)
- Latest performance review (last week's analysis)
- Quick-link tiles to videos/, social-images/, _engine/idea-bank.json

Unlike the client folder builder (build_outputs_index.py), Digischola already has
good queue separation. This script doesn't reorganize files — it just creates a
front-door dashboard that aggregates pointers.

Run after: post-writer drafts new content / repurpose creates variants /
visual-generator ships a video / weekly-ritual fires.

Usage:
    python3 ~/.claude/scripts/build_digischola_index.py

Updated 2026-04-29 for `_engine/` convention: idea-bank.json, brand DNA wiki,
weekly-ritual.state.json, and skill scratch folders moved into brand/_engine/.
Queue, calendars, performance, videos, social-images stay at brand/ root.
"""

import json
import re
import sys
from datetime import date, datetime
from pathlib import Path

ROOT = Path('/Users/digischola/Desktop/Digischola')
BRAND = ROOT / 'brand'
ENGINE = BRAND / '_engine'

CHANNEL_PATTERNS = [
    ('LinkedIn carousel', re.compile(r'linkedin-carousel', re.I)),
    ('LinkedIn text', re.compile(r'linkedin-text', re.I)),
    ('LinkedIn video', re.compile(r'linkedin-video', re.I)),
    ('X thread', re.compile(r'x-thread', re.I)),
    ('X single', re.compile(r'x-single', re.I)),
    ('Instagram carousel', re.compile(r'instagram-carousel', re.I)),
    ('Instagram Reel', re.compile(r'instagram-reel', re.I)),
    ('Facebook', re.compile(r'facebook', re.I)),
    ('WhatsApp', re.compile(r'whatsapp', re.I)),
    ('Video / Reel (MP4)', re.compile(r'\.mp4$', re.I)),
    ('Other', re.compile(r'.*')),
]


def channel_for(name: str) -> str:
    for label, pat in CHANNEL_PATTERNS:
        if pat.search(name):
            return label
    return 'Other'


def is_repurpose(name: str) -> bool:
    return 'repurpose' in name.lower()


def days_since(path: Path) -> int:
    return (datetime.now() - datetime.fromtimestamp(path.stat().st_mtime)).days


def fmt_size(path: Path) -> str:
    n = path.stat().st_size
    if n < 1024:
        return f'{n} B'
    if n < 1024 * 1024:
        return f'{n // 1024} KB'
    return f'{n / (1024 * 1024):.1f} MB'


def collect_pending() -> list:
    pending_dir = BRAND / 'queue' / 'pending-approval'
    if not pending_dir.is_dir():
        return []
    items = []
    for p in sorted(pending_dir.iterdir()):
        if p.name.startswith('.'):
            continue
        if p.is_dir():
            child_count = sum(1 for _ in p.rglob('*') if _.is_file())
            items.append({
                'name': p.name,
                'href': f'brand/queue/pending-approval/{p.name}/',
                'channel': 'Case study bundle',
                'meta': f'{child_count} files',
                'is_repurpose': False,
                'age_days': days_since(p),
                'is_dir': True,
            })
        else:
            items.append({
                'name': p.name,
                'href': f'brand/queue/pending-approval/{p.name}',
                'channel': channel_for(p.name),
                'meta': fmt_size(p),
                'is_repurpose': is_repurpose(p.name),
                'age_days': days_since(p),
                'is_dir': False,
            })
    return items


def collect_calendars() -> list:
    d = BRAND / 'calendars'
    if not d.is_dir():
        return []
    return sorted(
        [p for p in d.iterdir() if p.suffix == '.md' and not p.name.startswith('.')],
        key=lambda p: p.name,
        reverse=True,
    )


def collect_performance() -> list:
    d = BRAND / 'performance'
    if not d.is_dir():
        return []
    return sorted(
        [p for p in d.iterdir() if p.suffix == '.md' and not p.name.startswith('.')],
        key=lambda p: p.name,
        reverse=True,
    )


def collect_recent_videos() -> list:
    """5 most-recently-modified MP4 files across brand/videos/ and queue/."""
    videos = []
    for sub in ('videos', 'queue/pending-approval', 'queue/published'):
        d = BRAND / sub
        if not d.is_dir():
            continue
        for p in d.rglob('*.mp4'):
            videos.append(p)
    videos.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return videos[:5]


def idea_bank_summary() -> dict:
    p = ENGINE / 'idea-bank.json'
    if not p.is_file():
        return {'count': 0, 'href': None}
    try:
        data = json.loads(p.read_text(encoding='utf-8'))
        if isinstance(data, list):
            count = len(data)
        elif isinstance(data, dict) and 'entries' in data:
            count = len(data['entries'])
        else:
            count = 0
        return {'count': count, 'href': 'brand/_engine/idea-bank.json'}
    except (json.JSONDecodeError, OSError):
        return {'count': 0, 'href': 'brand/_engine/idea-bank.json'}


def published_recent_count(days: int = 7) -> int:
    d = BRAND / 'queue' / 'published'
    if not d.is_dir():
        return 0
    cutoff = datetime.now().timestamp() - (days * 86400)
    return sum(1 for p in d.iterdir() if p.is_file() and not p.name.startswith('.') and p.stat().st_mtime > cutoff)


def render() -> str:
    today = date.today().isoformat()
    pending = collect_pending()
    calendars = collect_calendars()
    performance = collect_performance()
    videos = collect_recent_videos()
    ideas = idea_bank_summary()
    shipped_7d = published_recent_count(7)

    pending_groups: dict = {}
    for item in pending:
        pending_groups.setdefault(item['channel'], []).append(item)

    channel_order = [
        'LinkedIn carousel', 'LinkedIn text', 'LinkedIn video',
        'X thread', 'X single',
        'Instagram carousel', 'Instagram Reel',
        'Facebook', 'WhatsApp',
        'Video / Reel (MP4)', 'Case study bundle', 'Other',
    ]
    ordered = [(c, pending_groups[c]) for c in channel_order if c in pending_groups]
    for c in pending_groups:
        if c not in [oc[0] for oc in ordered]:
            ordered.append((c, pending_groups[c]))

    stat_pending = len(pending)
    stat_repurposes = sum(1 for i in pending if i['is_repurpose'])
    stat_originals = stat_pending - stat_repurposes

    pending_html = []
    for channel, items in ordered:
        pending_html.append(f'<h3>{channel} <span class="count">{len(items)}</span></h3><div class="grid">')
        for item in items:
            tag = ' <span class="tag tag-repurpose">repurpose</span>' if item['is_repurpose'] else ''
            age = 'today' if item['age_days'] == 0 else f"{item['age_days']}d ago"
            pending_html.append(f'''
                <a class="card" href="{item['href']}">
                    <div class="card-name">{item['name']}{tag}</div>
                    <div class="card-meta">{item['meta']} · {age}</div>
                </a>
            ''')
        pending_html.append('</div>')

    featured_cards = []
    if calendars:
        featured_cards.append(f'''
            <a class="card card-featured card-calendar" href="brand/calendars/{calendars[0].name}">
                <div class="card-label">This week's calendar</div>
                <div class="card-name">{calendars[0].stem}</div>
                <div class="card-meta">Open week plan</div>
            </a>
        ''')
    if performance:
        featured_cards.append(f'''
            <a class="card card-featured card-perf" href="brand/performance/{performance[0].name}">
                <div class="card-label">Last performance review</div>
                <div class="card-name">{performance[0].stem}</div>
                <div class="card-meta">Open weekly review</div>
            </a>
        ''')

    videos_html = ''
    if videos:
        videos_html = '<h2>Recent videos / Reels <span class="count">' + str(len(videos)) + '</span></h2><div class="grid">'
        for v in videos:
            try:
                rel = v.relative_to(ROOT)
            except ValueError:
                continue
            videos_html += f'''
                <a class="card card-video" href="{rel}">
                    <div class="card-name">{v.name}</div>
                    <div class="card-meta">{fmt_size(v)} · {days_since(v)}d ago</div>
                </a>
            '''
        videos_html += '</div>'

    quick_links = [
        ('brand/queue/published/', 'Published archive', f'{shipped_7d} shipped in last 7d'),
        (ideas['href'], 'Idea bank', f'{ideas["count"]} entries' if ideas['count'] else 'View raw JSON'),
        ('brand/social-images/', 'Social images', 'Carousels & quote cards'),
        ('brand/videos/', 'Video projects', 'Edits & raw projects'),
        ('strategic-context.md', 'Strategic context', 'Brand strategy doc'),
    ]
    quick_html = '<h2>Quick links</h2><div class="grid">'
    for href, name, meta in quick_links:
        if href is None:
            continue
        quick_html += f'''
            <a class="card card-tool" href="{href}">
                <div class="card-name">{name}</div>
                <div class="card-meta">{meta}</div>
            </a>
        '''
    quick_html += '</div>'

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Digischola — Personal Brand Index</title>
<style>
:root {{
    --bg: #0e1116;
    --surface: #161b22;
    --surface-2: #1c2230;
    --border: #30363d;
    --text: #e6edf3;
    --muted: #8b949e;
    --accent: #58a6ff;
    --accent-warm: #f0883e;
    --accent-success: #3fb950;
}}
* {{ box-sizing: border-box; }}
body {{
    margin: 0; padding: 40px 24px;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif;
    background: var(--bg); color: var(--text);
    max-width: 1100px; margin: 0 auto;
}}
header {{ margin-bottom: 24px; padding-bottom: 24px; border-bottom: 1px solid var(--border); }}
h1 {{ font-size: 28px; margin: 0 0 8px; font-weight: 600; }}
.sub {{ color: var(--muted); font-size: 14px; }}
.stats {{ display: flex; gap: 20px; margin-top: 12px; flex-wrap: wrap; }}
.stat {{ font-size: 13px; color: var(--muted); }}
.stat strong {{ color: var(--text); font-size: 18px; font-weight: 600; margin-right: 6px; }}
h2 {{
    font-size: 13px; text-transform: uppercase; letter-spacing: 0.08em;
    color: var(--muted); margin: 36px 0 14px; font-weight: 600;
}}
h3 {{
    font-size: 13px; color: var(--text); margin: 20px 0 10px; font-weight: 600;
    display: flex; align-items: center; gap: 8px;
}}
.count {{
    background: var(--surface-2); color: var(--muted);
    padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 500;
}}
.grid {{
    display: grid; gap: 12px;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
}}
.card {{
    display: block; padding: 14px 16px;
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 8px; text-decoration: none; color: var(--text);
    transition: border-color 0.15s, transform 0.15s;
}}
.card:hover {{ border-color: var(--accent); transform: translateY(-1px); }}
.card-name {{ font-size: 13px; font-weight: 500; margin-bottom: 4px; word-break: break-word; line-height: 1.4; }}
.card-meta {{ color: var(--muted); font-size: 11px; }}
.card-label {{ color: var(--muted); font-size: 10px; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 4px; }}
.card-featured {{
    padding: 18px 20px;
    background: linear-gradient(135deg, var(--surface-2) 0%, var(--surface) 100%);
    border-color: var(--accent);
}}
.card-featured .card-name {{ font-size: 16px; }}
.card-calendar {{ border-color: var(--accent); }}
.card-perf {{ border-color: var(--accent-success); }}
.card-video {{ background: var(--surface-2); }}
.card-tool {{ background: transparent; }}
.tag {{
    display: inline-block; padding: 1px 7px; margin-left: 6px;
    border-radius: 4px; font-size: 10px; font-weight: 500; vertical-align: middle;
}}
.tag-repurpose {{ background: rgba(240, 136, 62, 0.15); color: var(--accent-warm); }}
footer {{ margin-top: 48px; padding-top: 20px; border-top: 1px solid var(--border); color: var(--muted); font-size: 12px; }}
.section-featured {{ display: grid; gap: 12px; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); margin-bottom: 8px; }}
</style>
</head>
<body>
<header>
    <h1>Digischola</h1>
    <div class="sub">Personal brand index · generated {today}</div>
    <div class="stats">
        <div class="stat"><strong>{stat_pending}</strong>pending approval</div>
        <div class="stat"><strong>{stat_originals}</strong>originals</div>
        <div class="stat"><strong>{stat_repurposes}</strong>repurposes</div>
        <div class="stat"><strong>{shipped_7d}</strong>shipped in last 7d</div>
    </div>
</header>

{'<h2>This week</h2><div class="section-featured">' + ''.join(featured_cards) + '</div>' if featured_cards else ''}

<h2>Pending approval — needs your review</h2>
{''.join(pending_html) or '<p class="sub">Nothing pending. Inbox zero.</p>'}

{videos_html}

{quick_html}

<footer>
    <p>This file is auto-generated. Re-run after content drafts/ships:
       <code>python3 ~/.claude/scripts/build_digischola_index.py</code></p>
</footer>
</body>
</html>
'''


def main():
    if not ROOT.is_dir():
        print(f'!! Digischola folder not found: {ROOT}')
        sys.exit(1)
    html = render()
    out = ROOT / 'index.html'
    out.write_text(html, encoding='utf-8')
    print(f'wrote {out}')


if __name__ == '__main__':
    main()
