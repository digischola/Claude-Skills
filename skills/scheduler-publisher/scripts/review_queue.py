#!/usr/bin/env python3
"""
Local review UI for Digischola draft queue.

Scans brand/queue/pending-approval/ + serves a dark-mode HTML review page on
localhost. Per-draft cards with approve/edit/reject buttons that write
`posting_status: approved|rejected|edit_requested` to frontmatter over AJAX.

Fires macOS notifications on open + on done.

Usage:
  python3 review_queue.py                  # port 8765, opens Safari/default browser
  python3 review_queue.py --port 9090
  python3 review_queue.py --no-open
  python3 review_queue.py --brand-folder /path/to/Digischola

Stops itself after you click "Done" (or Ctrl+C).
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import subprocess
import sys
import threading
import time
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
# shared notification helper lives at skills/shared-scripts/notify.py
# (two ../.. up from scheduler-publisher/scripts/ → skills/)
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "shared-scripts"))

import frontmatter_io as fio  # type: ignore
from tick import DEFAULT_BRAND  # type: ignore
from notify import notify as _notify  # type: ignore  # shared helper with click-through


# ── Styling: Digischola brand ─────────────────────────────────────────────

PRIMARY = "#3B9EFF"
BG = "#0A0F1C"
CARD_BG = "#111827"
BORDER = "#1F2937"
TEXT = "#E5E7EB"
MUTED = "#9CA3AF"
APPROVE = "#10B981"
REJECT = "#EF4444"
EDIT = "#F59E0B"

CHANNEL_BADGE = {
    "linkedin":  ("#0A66C2", "in"),
    "x":         ("#000000", "𝕏"),
    "instagram": ("#E4405F", "ig"),
    "facebook":  ("#1877F2", "f"),
    "whatsapp":  ("#25D366", "wa"),
}


# ── macOS helpers ──────────────────────────────────────────────────────────

def notify(title: str, subtitle: str, message: str, sound: str = "Glass",
           open_url: str = None, group: str = None) -> None:
    """Thin wrapper over the shared notify helper. Keeps the old signature
    intact so existing call sites don't have to change, while adding a
    click-to-open URL (patched 2026-04-22 — banners should never be
    dead-ends; every notification should have a clickable action)."""
    _notify(
        title, message,
        subtitle=subtitle,
        open_url=open_url,
        sound=sound,
        group=group or "digischola-review",
    )


def open_in_editor(path: Path) -> None:
    # Try VS Code, then default editor, then TextEdit
    for cmd in (["code", str(path)], ["open", "-t", str(path)], ["open", str(path)]):
        try:
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return
        except FileNotFoundError:
            continue


# ── Draft scanning ─────────────────────────────────────────────────────────

# ── Asset scanning (images + videos) ───────────────────────────────────────

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
VIDEO_EXTS = {".mp4", ".mov", ".webm", ".m4v"}


def scan_assets_for_entry(brand_folder: Path, entry_id: str, fm: dict) -> dict:
    """Scan all asset dirs that match the draft's entry_id.
    Looks in brand/queue/assets/<entry_id>*/ (supports suffixed variants
    like '4e4eed15-anim', '4e4eed15-reel-v2' that Mayank uses for multiple
    renders of the same source idea).
    Returns dict with 'images' and 'videos', each a list of (rel_path, filename) tuples
    where rel_path is usable by the /assets/<rel_path> HTTP endpoint.
    """
    result = {"images": [], "videos": []}
    if not entry_id:
        return result
    assets_root = brand_folder / "brand" / "queue" / "assets"
    if not assets_root.exists():
        return result

    # Primary: exact match on entry_id (and variants like <entry_id>-anim, <entry_id>-reel-v2)
    matching_dirs = []
    for d in sorted(assets_root.iterdir()):
        if d.is_dir() and (d.name == entry_id or d.name.startswith(f"{entry_id}-")):
            matching_dirs.append(d)

    for d in matching_dirs:
        for f in sorted(d.iterdir()):
            if not f.is_file():
                continue
            ext = f.suffix.lower()
            rel = f"{d.name}/{f.name}"
            if ext in IMAGE_EXTS:
                result["images"].append((rel, f.name, d.name))
            elif ext in VIDEO_EXTS:
                result["videos"].append((rel, f.name, d.name))
    return result


def scan_drafts(brand_folder: Path) -> list[dict]:
    pending = brand_folder / "brand" / "queue" / "pending-approval"
    if not pending.exists():
        return []
    drafts = []
    for p in sorted(pending.glob("*.md")):
        try:
            fm, body = fio.read(p)
        except Exception:
            continue
        if fm.get("posting_status") in {"posted", "approved", "rejected"}:
            pass  # still render, but marked
        entry_id = fm.get("entry_id") or ""
        # Only attach visuals when the draft's format actually uses them.
        # Prevents cross-contamination where a text-post card for entry X
        # displays the carousel slides of a different draft that shares X.
        # Patched 2026-04-22 — user caught it during W18 review.
        VISUAL_FORMATS = {
            "carousel", "reel", "reel-script", "animated-graphic",
            "animated", "quote-card", "story", "video",
        }
        draft_format = (fm.get("format") or "").strip().lower()
        visual_dir_key = fm.get("visual_assets_dir")
        if draft_format in VISUAL_FORMATS or visual_dir_key:
            assets = scan_assets_for_entry(brand_folder, entry_id, fm)
            # If visual_assets_dir is explicitly set, trust it: only show assets
            # from that exact dir, not every dir starting with entry_id.
            if visual_dir_key:
                target = str(Path(visual_dir_key).name).rstrip("/")
                assets["images"] = [t for t in assets["images"] if t[2] == target]
                assets["videos"] = [t for t in assets["videos"] if t[2] == target]
        else:
            assets = {"images": [], "videos": []}
        drafts.append({
            "filename": p.name,
            "path": str(p),
            "channel": (fm.get("channel") or "").lower(),
            "format": fm.get("format") or "",
            "entry_id": entry_id,
            "pillar": fm.get("pillar") or "",
            "hook_category": fm.get("hook_category") or "",
            "voice_framework": fm.get("voice_framework") or "",
            "scheduled_at": fm.get("scheduled_at") or "",
            "scheduled_day": fm.get("scheduled_day") or "",
            "scheduled_week": fm.get("scheduled_week") or "",
            "posting_status": fm.get("posting_status") or "draft",
            "validator_status": fm.get("validator_status") or "",
            "repurpose_source": fm.get("repurpose_source") or "",
            "visual_brief_needed": bool(fm.get("visual_brief_needed")),
            "body": body.strip(),
            "images": assets["images"],
            "videos": assets["videos"],
        })
    # Sort by scheduled_at if present, else by filename
    drafts.sort(key=lambda d: (d["scheduled_at"] or d["filename"]))
    return drafts


# ── HTML render ────────────────────────────────────────────────────────────

def render_page(drafts: list[dict], brand_folder: Path) -> str:
    drafts_by_status = {}
    for d in drafts:
        drafts_by_status.setdefault(d["posting_status"], []).append(d)

    cards = []
    for d in drafts:
        cards.append(render_card(d))

    total = len(drafts)
    pending = sum(1 for d in drafts if d["posting_status"] == "draft")
    approved = sum(1 for d in drafts if d["posting_status"] == "approved")
    rejected = sum(1 for d in drafts if d["posting_status"] == "rejected")
    edit_req = sum(1 for d in drafts if d["posting_status"] == "edit_requested")

    return f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>Digischola draft review</title>
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;700&family=Orbitron:wght@600;900&family=Space+Grotesk:wght@500;700&display=swap" rel="stylesheet" />
<style>
 :root {{
   --pr: {PRIMARY}; --bg: {BG}; --card: {CARD_BG}; --border: {BORDER};
   --text: {TEXT}; --muted: {MUTED}; --approve: {APPROVE};
   --reject: {REJECT}; --edit: {EDIT};
 }}
 * {{ box-sizing: border-box; }}
 html, body {{ margin: 0; padding: 0; background: var(--bg); color: var(--text); font-family: 'Manrope', system-ui; font-size: 15px; line-height: 1.55; }}
 header {{ position: sticky; top: 0; z-index: 10; background: rgba(10,15,28,0.92); backdrop-filter: blur(10px); border-bottom: 1px solid var(--border); padding: 16px 24px; display: flex; align-items: center; justify-content: space-between; gap: 24px; }}
 h1 {{ font-family: 'Orbitron', sans-serif; font-weight: 900; font-size: 20px; margin: 0; letter-spacing: 0.5px; background: linear-gradient(90deg, var(--pr), #7ec5ff); -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent; }}
 .counter {{ display: flex; gap: 18px; align-items: center; font-family: 'Space Grotesk', sans-serif; font-size: 14px; }}
 .counter .pill {{ display: inline-flex; align-items: center; gap: 6px; padding: 6px 12px; border-radius: 999px; background: rgba(255,255,255,0.05); border: 1px solid var(--border); }}
 .counter .pill.approve {{ color: var(--approve); border-color: rgba(16,185,129,0.3); }}
 .counter .pill.reject {{ color: var(--reject); border-color: rgba(239,68,68,0.3); }}
 .counter .pill.edit {{ color: var(--edit); border-color: rgba(245,158,11,0.3); }}
 .counter .pill.pending {{ color: var(--muted); }}
 #done-btn {{ padding: 10px 20px; background: var(--pr); color: white; border: none; border-radius: 8px; font-family: 'Space Grotesk', sans-serif; font-weight: 700; cursor: pointer; font-size: 14px; transition: background 0.15s; }}
 #done-btn:hover {{ background: #5eaeff; }}
 #done-btn:disabled {{ opacity: 0.4; cursor: not-allowed; }}
 main {{ max-width: 960px; margin: 0 auto; padding: 24px; display: flex; flex-direction: column; gap: 18px; }}
 .card {{ background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 20px; transition: border-color 0.2s, transform 0.15s; }}
 .card:hover {{ border-color: rgba(59,158,255,0.3); }}
 .card.approved {{ border-color: rgba(16,185,129,0.4); background: rgba(16,185,129,0.04); }}
 .card.rejected {{ border-color: rgba(239,68,68,0.4); background: rgba(239,68,68,0.04); opacity: 0.6; }}
 .card.edit_requested {{ border-color: rgba(245,158,11,0.4); background: rgba(245,158,11,0.04); }}
 .card-head {{ display: flex; align-items: center; gap: 12px; flex-wrap: wrap; margin-bottom: 12px; }}
 .channel-badge {{ display: inline-flex; align-items: center; justify-content: center; width: 32px; height: 32px; border-radius: 8px; color: white; font-family: 'Orbitron', sans-serif; font-weight: 900; font-size: 13px; }}
 .meta {{ display: flex; flex-direction: column; gap: 2px; }}
 .meta .top {{ font-family: 'Space Grotesk', sans-serif; font-weight: 700; font-size: 15px; }}
 .meta .sub {{ font-size: 12px; color: var(--muted); }}
 .tags {{ margin-left: auto; display: flex; gap: 6px; flex-wrap: wrap; }}
 .tag {{ font-size: 11px; padding: 3px 8px; border-radius: 6px; background: rgba(255,255,255,0.06); color: var(--muted); font-family: 'Space Grotesk', sans-serif; }}
 .tag.pillar {{ color: var(--pr); background: rgba(59,158,255,0.08); }}
 .tag.warn {{ color: var(--edit); background: rgba(245,158,11,0.08); }}
 .hook {{ font-family: 'Space Grotesk', sans-serif; font-weight: 700; font-size: 17px; line-height: 1.4; color: var(--text); margin: 12px 0; padding: 12px 16px; background: rgba(59,158,255,0.05); border-left: 3px solid var(--pr); border-radius: 4px; white-space: pre-wrap; }}
 .body-wrap {{ margin-top: 12px; }}
 .body {{ white-space: pre-wrap; font-family: 'Manrope', system-ui; color: var(--text); font-size: 14.5px; line-height: 1.65; max-height: 200px; overflow: hidden; position: relative; transition: max-height 0.3s; }}
 .body.expanded {{ max-height: none; }}
 .body::after {{ content: ''; position: absolute; left: 0; right: 0; bottom: 0; height: 50px; background: linear-gradient(to bottom, transparent, var(--card)); pointer-events: none; transition: opacity 0.3s; }}
 .body.expanded::after {{ opacity: 0; }}
 .card.approved .body::after, .card.rejected .body::after, .card.edit_requested .body::after {{ background: transparent; }}
 .expand-btn {{ margin-top: 4px; background: none; color: var(--pr); border: none; cursor: pointer; font-family: 'Space Grotesk', sans-serif; font-size: 13px; padding: 4px 0; }}
 .actions {{ display: flex; gap: 10px; margin-top: 16px; padding-top: 16px; border-top: 1px solid var(--border); }}
 .btn {{ flex: 1; padding: 10px 16px; border: 1px solid var(--border); background: transparent; color: var(--text); border-radius: 8px; font-family: 'Space Grotesk', sans-serif; font-weight: 700; font-size: 14px; cursor: pointer; transition: all 0.15s; }}
 .btn:hover {{ transform: translateY(-1px); }}
 .btn.approve:hover, .btn.approve.active {{ background: var(--approve); color: white; border-color: var(--approve); }}
 .btn.reject:hover, .btn.reject.active {{ background: var(--reject); color: white; border-color: var(--reject); }}
 .btn.edit:hover, .btn.edit.active {{ background: var(--edit); color: white; border-color: var(--edit); }}
 .status-line {{ margin-top: 10px; font-size: 13px; color: var(--muted); font-family: 'Space Grotesk', sans-serif; }}
 .status-line.approved {{ color: var(--approve); }}
 .status-line.rejected {{ color: var(--reject); }}
 .status-line.edit_requested {{ color: var(--edit); }}
 footer {{ text-align: center; padding: 40px 20px; color: var(--muted); font-size: 12px; font-family: 'Space Grotesk', sans-serif; }}
 .empty {{ text-align: center; padding: 80px 20px; color: var(--muted); }}
 .media {{ margin-top: 18px; }}
 .media-label {{ font-family: 'Space Grotesk', sans-serif; font-size: 11px; text-transform: uppercase; letter-spacing: 2px; color: var(--muted); margin-bottom: 10px; }}
 .media-group {{ margin-top: 14px; }}
 .image-strip {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 10px; }}
 .image-strip a {{ display: block; border-radius: 10px; overflow: hidden; border: 1px solid var(--border); transition: border-color 0.15s, transform 0.15s; }}
 .image-strip a:hover {{ border-color: var(--pr); transform: scale(1.02); }}
 .image-strip img {{ width: 100%; aspect-ratio: 4/5; object-fit: cover; display: block; background: #000; }}
 .image-strip .caption {{ font-size: 10px; font-family: 'Space Grotesk', sans-serif; color: var(--muted); padding: 4px 8px; background: var(--bg); }}
 .video-strip {{ display: flex; flex-direction: column; gap: 12px; }}
 .video-strip video {{ width: 100%; max-height: 600px; background: #000; border-radius: 10px; border: 1px solid var(--border); }}
 .video-strip .v-caption {{ font-size: 12px; font-family: 'Space Grotesk', sans-serif; color: var(--muted); }}
 .lightbox {{ display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.92); z-index: 1000; padding: 40px; align-items: center; justify-content: center; cursor: zoom-out; }}
 .lightbox.open {{ display: flex; }}
 .lightbox img {{ max-width: 95%; max-height: 95vh; object-fit: contain; }}
 /* Hash-target card highlight — when a notification deep-links to #draft-X */
 .card.hash-target {{ box-shadow: 0 0 0 2px var(--pr), 0 0 40px rgba(59,158,255,0.25); animation: pulse 1.2s ease-out; }}
 @keyframes pulse {{ 0% {{ box-shadow: 0 0 0 0 var(--pr), 0 0 0 rgba(59,158,255,0); }} 100% {{ box-shadow: 0 0 0 2px var(--pr), 0 0 40px rgba(59,158,255,0.25); }} }}
</style>
</head><body>
<header>
  <h1>DIGISCHOLA · DRAFT REVIEW</h1>
  <div class="counter">
    <span class="pill pending"><span id="c-pending">{pending}</span> pending</span>
    <span class="pill approve">✓ <span id="c-approved">{approved}</span></span>
    <span class="pill edit">✏ <span id="c-edit">{edit_req}</span></span>
    <span class="pill reject">✗ <span id="c-rejected">{rejected}</span></span>
    <button id="done-btn" onclick="finish()">Done</button>
  </div>
</header>
<main>
  {"".join(cards) if cards else '<div class="empty">No drafts in pending-approval/. Queue is empty.</div>'}
</main>
<div class="lightbox" id="lightbox" onclick="closeLightbox()"><img id="lightbox-img" src="" /></div>
<footer>
  Reviewing <code>{html.escape(str(brand_folder))}/brand/queue/pending-approval/</code> · {total} drafts · port {{PORT}}
</footer>
<script>
function openLightbox(src) {{
  const lb = document.getElementById('lightbox');
  document.getElementById('lightbox-img').src = src;
  lb.classList.add('open');
}}
function closeLightbox() {{
  document.getElementById('lightbox').classList.remove('open');
}}
document.addEventListener('keydown', e => {{
  if (e.key === 'Escape') closeLightbox();
}});
async function act(action, file, btn) {{
  const card = btn.closest('.card');
  const res = await fetch('/' + action + '/' + encodeURIComponent(file), {{ method: 'POST' }});
  if (!res.ok) {{ alert('Failed: ' + res.statusText); return; }}
  const data = await res.json();
  card.className = 'card ' + data.status;
  card.querySelectorAll('.btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  const sl = card.querySelector('.status-line') || (() => {{
    const el = document.createElement('div');
    el.className = 'status-line';
    card.appendChild(el);
    return el;
  }})();
  sl.className = 'status-line ' + data.status;
  sl.textContent = {{approved:'✓ Approved', rejected:'✗ Rejected', edit_requested:'✏ Edit requested (file opened in editor)'}}[data.status] || data.status;
  updateCounters();
}}
function updateCounters() {{
  const cards = document.querySelectorAll('.card');
  let pending=0, approved=0, edit=0, rejected=0;
  cards.forEach(c => {{
    if (c.classList.contains('approved')) approved++;
    else if (c.classList.contains('rejected')) rejected++;
    else if (c.classList.contains('edit_requested')) edit++;
    else pending++;
  }});
  document.getElementById('c-pending').textContent = pending;
  document.getElementById('c-approved').textContent = approved;
  document.getElementById('c-edit').textContent = edit;
  document.getElementById('c-rejected').textContent = rejected;
  document.getElementById('done-btn').disabled = (pending + edit) > 0 && approved + rejected + edit === 0;
}}
function toggle(id) {{
  const b = document.getElementById(id);
  const btn = event.target;
  b.classList.toggle('expanded');
  btn.textContent = b.classList.contains('expanded') ? 'Collapse' : 'Expand';
}}
async function finish() {{
  await fetch('/finish', {{ method: 'POST' }});
  document.body.innerHTML = '<div style="padding:60px;text-align:center;font-family:Space Grotesk;"><h2 style="color:#3B9EFF">Review complete.</h2><p>Summary notification fired. Scheduler-publisher takes over from here.</p><p style="margin-top:40px;color:#9CA3AF;font-size:13px;">You can close this tab.</p></div>';
  setTimeout(() => window.close(), 2000);
}}
// Hash deep-link handler: when a notification click opens the page with
// #draft-<filename>, scroll to that card + highlight it.
// If the card doesn't exist in the current filtered view (it's been approved
// or scheduled), auto-redirect to ?all=1 keeping the hash so the user still
// lands on it.
function handleHashNav() {{
  const hash = window.location.hash;
  if (!hash || !hash.startsWith('#draft-')) return;
  const id = hash.slice(1);
  const el = document.getElementById(id);
  if (el) {{
    el.classList.add('hash-target');
    el.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
    setTimeout(() => el.classList.remove('hash-target'), 3000);
  }} else {{
    // Card not in current view — likely hidden by NEEDS_ATTENTION filter.
    // Flip to ?all=1 preserving the hash so user still sees their target.
    const qs = new URLSearchParams(window.location.search);
    if (qs.get('all') !== '1') {{
      window.location.replace('/?all=1' + hash);
    }}
  }}
}}
window.addEventListener('DOMContentLoaded', handleHashNav);
window.addEventListener('hashchange', handleHashNav);
</script>
</body></html>"""


def render_card(d: dict) -> str:
    channel = d["channel"].lower()
    badge_color, badge_txt = CHANNEL_BADGE.get(channel, ("#374151", "?"))
    file_enc = urllib.parse.quote(d["filename"])

    body_preview = d["body"]
    lines = body_preview.split("\n")
    hook_lines = []
    rest_lines = []
    for line in lines:
        if line.strip() and not line.strip().startswith(("#", "-", "*", ">")):
            hook_lines.append(line)
            if len(hook_lines) >= 2 and line.strip():
                break
    # Hook = first 2 non-empty, non-markdown lines
    non_empty = [l for l in lines if l.strip()]
    hook = "\n".join(non_empty[:2]) if non_empty else "(no hook found)"
    rest = "\n".join(lines)

    # Time display
    sched = d["scheduled_at"]
    if sched:
        try:
            sched_display = sched.replace("T", " ").split("+")[0][:16] + " IST"
        except Exception:
            sched_display = sched
    else:
        sched_display = "not scheduled"
    day = d["scheduled_day"] or ""
    week = d["scheduled_week"] or ""

    pillar = d["pillar"]
    fmt = d["format"]
    status = d["posting_status"]
    status_class = status if status in {"approved","rejected","edit_requested"} else "draft"

    tags_html = ""
    if pillar:
        tags_html += f'<span class="tag pillar">{html.escape(pillar)}</span>'
    if fmt:
        tags_html += f'<span class="tag">{html.escape(fmt)}</span>'
    if d["repurpose_source"]:
        tags_html += f'<span class="tag">repurpose</span>'
    if d["visual_brief_needed"]:
        tags_html += f'<span class="tag warn">needs visual</span>'
    if d["validator_status"] and d["validator_status"] != "pending":
        cls = "warn" if d["validator_status"] != "clean" else ""
        tags_html += f'<span class="tag {cls}">validator: {html.escape(d["validator_status"])}</span>'

    status_line = ""
    if status == "approved":
        status_line = '<div class="status-line approved">✓ Approved</div>'
    elif status == "rejected":
        status_line = '<div class="status-line rejected">✗ Rejected</div>'
    elif status == "edit_requested":
        status_line = '<div class="status-line edit_requested">✏ Edit requested (file opened in editor)</div>'

    body_id = f"b-{abs(hash(d['filename']))}"

    approve_active = " active" if status == "approved" else ""
    reject_active = " active" if status == "rejected" else ""
    edit_active = " active" if status == "edit_requested" else ""

    media_html = render_media_block(d)

    # Anchor id for deep-linking from notifications:
    # http://127.0.0.1:8765/#draft-<filename-without-ext>
    # Render-complete / notify banners in visual-generator + tick + push_notify
    # point to this anchor so the click lands on the right card, not the top of
    # the page.
    stem = re.sub(r"\.md$", "", d["filename"])
    anchor_id = f"draft-{stem}"

    return f"""
  <div class="card {status_class}" id="{anchor_id}" data-filename="{html.escape(d['filename'])}">
    <div class="card-head">
      <div class="channel-badge" style="background: {badge_color}">{badge_txt}</div>
      <div class="meta">
        <div class="top">{html.escape(day)} · {html.escape(sched_display)}</div>
        <div class="sub">{html.escape(d['filename'])}</div>
      </div>
      <div class="tags">{tags_html}</div>
    </div>
    <div class="hook">{html.escape(hook)}</div>
    <div class="body-wrap">
      <div class="body" id="{body_id}">{html.escape(rest)}</div>
      <button class="expand-btn" onclick="toggle('{body_id}')">Expand</button>
    </div>
    {media_html}
    <div class="actions">
      <button class="btn approve{approve_active}" onclick="act('approve','{file_enc}',this)">✓ Approve</button>
      <button class="btn edit{edit_active}" onclick="act('edit','{file_enc}',this)">✏ Edit</button>
      <button class="btn reject{reject_active}" onclick="act('reject','{file_enc}',this)">✗ Reject</button>
    </div>
    {status_line}
  </div>
"""


def render_media_block(d: dict) -> str:
    images = d.get("images", [])
    videos = d.get("videos", [])
    if not images and not videos:
        return ""

    # Group by asset dir (so multiple renders of the same source stay separate)
    from collections import OrderedDict
    image_groups = OrderedDict()
    for rel, fname, dname in images:
        image_groups.setdefault(dname, []).append((rel, fname))
    video_groups = OrderedDict()
    for rel, fname, dname in videos:
        video_groups.setdefault(dname, []).append((rel, fname))

    parts = ['<div class="media">']

    for dname, items in image_groups.items():
        parts.append(f'<div class="media-group">')
        parts.append(f'<div class="media-label">🖼 IMAGES · {html.escape(dname)} · {len(items)} slide(s)</div>')
        parts.append('<div class="image-strip">')
        for rel, fname in items:
            parts.append(
                f'<a href="#" onclick="openLightbox(\'/assets/{urllib.parse.quote(rel)}\');return false;">'
                f'<img src="/assets/{urllib.parse.quote(rel)}" loading="lazy" alt="{html.escape(fname)}" />'
                f'<div class="caption">{html.escape(fname)}</div>'
                f'</a>'
            )
        parts.append('</div></div>')

    for dname, items in video_groups.items():
        parts.append(f'<div class="media-group">')
        parts.append(f'<div class="media-label">🎬 VIDEOS · {html.escape(dname)} · {len(items)} file(s)</div>')
        parts.append('<div class="video-strip">')
        for rel, fname in items:
            parts.append(
                f'<div><div class="v-caption">{html.escape(fname)}</div>'
                f'<video controls preload="metadata" src="/assets/{urllib.parse.quote(rel)}"></video></div>'
            )
        parts.append('</div></div>')

    parts.append('</div>')
    return "".join(parts)


# ── HTTP handler ───────────────────────────────────────────────────────────

class ReviewHandler(BaseHTTPRequestHandler):
    brand_folder: Path = None  # set by server
    done_event: threading.Event = None
    port: int = 8765

    def log_message(self, fmt, *a):
        pass  # silence access log

    def _set_status_in_frontmatter(self, filename: str, status: str) -> bool:
        path = self.brand_folder / "brand" / "queue" / "pending-approval" / filename
        if not path.exists():
            return False
        fm, body = fio.read(path)
        fm["posting_status"] = status
        fio.write(path, fm, body)
        return True

    def _send_json(self, code: int, obj: dict):
        data = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        # Parse optional query params.
        path_only = self.path.split("?", 1)[0]
        qs = urllib.parse.parse_qs(self.path.split("?", 1)[1]) if "?" in self.path else {}
        show_all = qs.get("all", ["0"])[0] in ("1", "true", "yes")
        if path_only == "/" or path_only == "":
            drafts = scan_drafts(self.brand_folder)
            # Default filter (added 2026-04-22 — user caught that subsequent-pass
            # reviews should hide already-approved drafts, not re-show all 11).
            # NEEDS_ATTENTION = drafts that still need the user's eyes.
            # DONE_STATUSES are hidden unless ?all=1 in URL.
            NEEDS_ATTENTION = {"draft", "drafted", "rejected", "edit_requested"}
            DONE_STATUSES = {"approved", "scheduled", "notified", "posted", "manual_publish_overdue"}
            total = len(drafts)
            if not show_all:
                filtered = [d for d in drafts if d["posting_status"] in NEEDS_ATTENTION]
                hidden = total - len(filtered)
                drafts = filtered
            else:
                hidden = 0
            html_page = render_page(drafts, self.brand_folder).replace("{PORT}", str(self.port))
            # Inject a filter banner at top so user knows N drafts are hidden.
            if hidden > 0 and not show_all:
                banner = (
                    f'<div style="background:#1E2540;border-bottom:1px solid #3B9EFF;'
                    f'padding:10px 24px;font-family:system-ui,sans-serif;font-size:13px;'
                    f'color:#F1F5F9;text-align:center;">'
                    f'Showing <strong>{len(drafts)}</strong> draft(s) that need attention · '
                    f'<strong>{hidden}</strong> already-approved/scheduled hidden · '
                    f'<a href="/?all=1" style="color:#3B9EFF;">Show all {total}</a>'
                    f'</div>'
                )
                html_page = html_page.replace("<body>", "<body>" + banner, 1)
            elif show_all:
                banner = (
                    f'<div style="background:#1E2540;border-bottom:1px solid #4ADE80;'
                    f'padding:10px 24px;font-family:system-ui,sans-serif;font-size:13px;'
                    f'color:#F1F5F9;text-align:center;">'
                    f'Showing all <strong>{total}</strong> drafts · '
                    f'<a href="/" style="color:#4ADE80;">Show only pending</a>'
                    f'</div>'
                )
                html_page = html_page.replace("<body>", "<body>" + banner, 1)
            data = html_page.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        elif self.path == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
        elif self.path.startswith("/assets/"):
            self._serve_asset(urllib.parse.unquote(self.path[len("/assets/"):]))
        else:
            self.send_response(404)
            self.end_headers()

    def _serve_asset(self, rel_path: str):
        """Serve a file from brand/queue/assets/<rel_path> safely."""
        assets_root = (self.brand_folder / "brand" / "queue" / "assets").resolve()
        target = (assets_root / rel_path).resolve()
        # Path traversal guard
        try:
            target.relative_to(assets_root)
        except ValueError:
            self.send_response(403); self.end_headers(); return
        if not target.exists() or not target.is_file():
            self.send_response(404); self.end_headers(); return
        mime = {
            ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
            ".webp": "image/webp", ".gif": "image/gif",
            ".mp4": "video/mp4", ".mov": "video/quicktime",
            ".webm": "video/webm", ".m4v": "video/x-m4v",
        }.get(target.suffix.lower(), "application/octet-stream")
        size = target.stat().st_size
        # Range support for video seeking
        range_header = self.headers.get("Range")
        if range_header and range_header.startswith("bytes="):
            try:
                spec = range_header.split("=", 1)[1]
                start_s, end_s = spec.split("-", 1)
                start = int(start_s) if start_s else 0
                end = int(end_s) if end_s else size - 1
                end = min(end, size - 1)
                length = end - start + 1
                self.send_response(206)
                self.send_header("Content-Type", mime)
                self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
                self.send_header("Accept-Ranges", "bytes")
                self.send_header("Content-Length", str(length))
                self.end_headers()
                with open(target, "rb") as f:
                    f.seek(start)
                    self.wfile.write(f.read(length))
                return
            except Exception:
                pass
        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(size))
        self.send_header("Accept-Ranges", "bytes")
        self.end_headers()
        with open(target, "rb") as f:
            self.wfile.write(f.read())

    def do_POST(self):
        m = re.match(r"^/(approve|reject|edit)/(.+)$", self.path)
        if m:
            action, filename = m.group(1), urllib.parse.unquote(m.group(2))
            status_map = {"approve": "approved", "reject": "rejected", "edit": "edit_requested"}
            status = status_map[action]
            ok = self._set_status_in_frontmatter(filename, status)
            if action == "edit" and ok:
                open_in_editor(self.brand_folder / "brand" / "queue" / "pending-approval" / filename)
            self._send_json(200 if ok else 404, {"status": status, "ok": ok})
            return
        if self.path == "/finish":
            drafts = scan_drafts(self.brand_folder)
            approved = sum(1 for d in drafts if d["posting_status"] == "approved")
            rejected = sum(1 for d in drafts if d["posting_status"] == "rejected")
            edit_req = sum(1 for d in drafts if d["posting_status"] == "edit_requested")
            notify(
                "Draft review complete",
                f"{approved} approved, {edit_req} edit, {rejected} rejected",
                "Scheduler-publisher will ship approved drafts at their scheduled times.",
            )
            self._send_json(200, {"ok": True, "approved": approved, "edit": edit_req, "rejected": rejected})
            # Signal main loop to exit after a short delay so browser receives response
            if self.done_event:
                threading.Timer(0.5, self.done_event.set).start()
            return
        self.send_response(404)
        self.end_headers()


# ── Main ───────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--brand-folder", type=Path, default=DEFAULT_BRAND)
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--no-open", action="store_true", help="Don't auto-open browser")
    ap.add_argument("--no-notify", action="store_true", help="Don't fire macOS notification")
    args = ap.parse_args()

    drafts = scan_drafts(args.brand_folder)
    if not drafts:
        print("No drafts found in pending-approval/. Nothing to review.")
        sys.exit(0)

    pending = sum(1 for d in drafts if d["posting_status"] == "draft")
    print(f"Found {len(drafts)} drafts ({pending} pending review).")

    done_event = threading.Event()
    ReviewHandler.brand_folder = args.brand_folder
    ReviewHandler.done_event = done_event
    ReviewHandler.port = args.port

    try:
        server = ThreadingHTTPServer(("127.0.0.1", args.port), ReviewHandler)
    except OSError as e:
        sys.exit(f"Port {args.port} in use. Try --port 8766. ({e})")

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    url = f"http://127.0.0.1:{args.port}/"
    print(f"Review UI running at {url}")

    total_images = sum(len(d["images"]) for d in drafts)
    total_videos = sum(len(d["videos"]) for d in drafts)
    media_line = []
    if total_images:
        media_line.append(f"{total_images} images")
    if total_videos:
        media_line.append(f"{total_videos} videos")
    media_str = " + " + " + ".join(media_line) if media_line else ""

    if not args.no_notify:
        notify(
            "Drafts ready for review",
            f"{len(drafts)} drafts{media_str}",
            "Click to open the review UI.",
            open_url=url,
        )
    print(f"Media attached: {total_images} images, {total_videos} videos")

    if not args.no_open:
        webbrowser.open(url)

    print("Waiting for 'Done' (or Ctrl+C to exit)...")
    try:
        done_event.wait()
    except KeyboardInterrupt:
        print("\nInterrupted.")
    finally:
        server.shutdown()
        print("Review server stopped.")


if __name__ == "__main__":
    main()
