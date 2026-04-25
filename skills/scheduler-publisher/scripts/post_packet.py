#!/usr/bin/env python3
"""
Post packet generator.

At scheduled_at, alongside the macOS notification + clipboard + Finder reveal,
also generate a per-draft HTML "post packet" and open it in the default browser.

The packet is a single dark-mode page that shows in ONE place:
  - Channel + scheduled time + draft filename
  - The caption with a giant "Copy caption" button (2 clicks → paste in composer)
  - All assets (image thumbnails + video players) with:
      * Direct download button per file
      * Absolute file path (reveal in Finder)
      * "Drag these to the composer" instruction
  - One button "→ Open composer" (X intent URL with caption pre-filled, IG/FB/WA
    launchers)
  - One button "→ Reveal assets folder in Finder" (for drag-drop to composer)

Solves the problem where the user can't locate the image/video files for
the post after clicking the notification.

Usage (as module):
    from post_packet import render_and_open
    path = render_and_open(fm, body, brand_folder)
    # Opens /tmp/post-packet-<entry_id>-<channel>.html in default browser
    # Returns the path

Usage (CLI, for testing):
    python3 post_packet.py --draft <path-to-draft-md>
"""

from __future__ import annotations

import argparse
import html
import shlex
import subprocess
import sys
import urllib.parse as urlparse
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
import frontmatter_io as fio  # type: ignore

try:
    from publishers.manual import composer_url_for, STATIC_COMPOSER_URLS  # type: ignore
except Exception:
    def composer_url_for(channel: str, caption: str) -> str:  # fallback
        return {"x": "https://x.com/compose/post",
                "instagram": "https://www.instagram.com/",
                "facebook": "https://www.facebook.com/",
                "whatsapp": "https://web.whatsapp.com/"}.get(channel, "")
    STATIC_COMPOSER_URLS = {}


IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
VIDEO_EXTS = {".mp4", ".mov", ".webm", ".m4v"}

PRIMARY = "#3B9EFF"
BG = "#0A0F1C"
CARD_BG = "#111827"
BORDER = "#1F2937"
TEXT = "#E5E7EB"
MUTED = "#9CA3AF"
GREEN = "#10B981"


# Formats that are text-only on their native channel — they must NEVER pick
# up sibling assets from the same entry_id folder, even if that entry has a
# carousel / reel / image-post repurpose elsewhere. Keyed by channel to avoid
# future ambiguity (e.g. a hypothetical "single" image-post vs an X single).
TEXT_ONLY_FORMATS = {
    ("x", "tweet"),
    ("x", "single"),
    ("x", "thread"),
    ("twitter", "tweet"),
    ("twitter", "single"),
    ("twitter", "thread"),
    ("linkedin", "text-post"),
    ("linkedin", "text"),
    ("facebook", "text-post"),
    ("facebook", "text"),
    ("whatsapp", "text"),
    ("whatsapp", "text-post"),
}


def is_text_only(channel: str, fmt: str) -> bool:
    return ((channel or "").lower(), (fmt or "").lower()) in TEXT_ONLY_FORMATS


def scan_assets(brand_folder: Path, entry_id: str,
                channel: str = "", fmt: str = "") -> list[tuple[str, Path]]:
    """Return list of (kind, path) for all assets matching this entry_id.

    Text-only formats (X tweet/thread, LinkedIn text-post, etc.) return [] even
    if `assets/<entry_id>/` contains slides — those slides belong to a sibling
    repurpose (e.g. an IG carousel) sharing the same entry_id. Without this
    gate, text-only packets display the carousel slides and the user may think
    they need to attach them. See scheduler-publisher Learnings 2026-04-24.
    """
    if is_text_only(channel, fmt):
        return []
    assets_root = brand_folder / "brand" / "queue" / "assets"
    if not assets_root.exists() or not entry_id:
        return []
    out: list[tuple[str, Path]] = []
    for d in sorted(assets_root.iterdir()):
        if not d.is_dir():
            continue
        if d.name != entry_id and not d.name.startswith(f"{entry_id}-"):
            continue
        for f in sorted(d.iterdir()):
            if not f.is_file():
                continue
            ext = f.suffix.lower()
            if ext in IMAGE_EXTS:
                out.append(("image", f))
            elif ext in VIDEO_EXTS:
                out.append(("video", f))
    return out


CHANNEL_META = {
    "linkedin":  ("LINKEDIN",  "#0A66C2", "in"),
    "x":         ("X",         "#000000", "𝕏"),
    "twitter":   ("X",         "#000000", "𝕏"),
    "instagram": ("INSTAGRAM", "#E4405F", "ig"),
    "facebook":  ("FACEBOOK",  "#1877F2", "f"),
    "whatsapp":  ("WHATSAPP",  "#25D366", "wa"),
}


def render_packet_html(fm: dict, body: str, brand_folder: Path) -> str:
    channel = (fm.get("channel") or "").lower()
    channel_name, channel_color, channel_icon = CHANNEL_META.get(channel, (channel.upper(), "#374151", "?"))
    entry_id = fm.get("entry_id") or "unknown"
    fmt = fm.get("format") or ""
    pillar = fm.get("pillar") or ""
    scheduled_at = fm.get("scheduled_at") or ""
    sched_display = scheduled_at[:16].replace("T", " ") + " IST" if scheduled_at else "now"
    caption = (body or "").strip()
    composer_url = composer_url_for(channel, caption)
    static_url = STATIC_COMPOSER_URLS.get(channel, composer_url)

    assets = scan_assets(brand_folder, entry_id, channel=channel, fmt=fmt)
    first_asset_dir = assets[0][1].parent if assets else None

    assets_html_blocks = []
    for kind, path in assets:
        file_url = f"file://{urlparse.quote(str(path))}"
        fname = path.name
        finder_reveal_cmd = f"open -R {shlex.quote(str(path))}"
        if kind == "image":
            assets_html_blocks.append(f"""
            <div class="asset-card">
              <a href="{html.escape(file_url)}" target="_blank" class="thumb-wrap">
                <img src="{html.escape(file_url)}" alt="{html.escape(fname)}" />
              </a>
              <div class="asset-meta">
                <div class="asset-name">{html.escape(fname)}</div>
                <div class="asset-path">{html.escape(str(path))}</div>
                <div class="asset-actions">
                  <a class="btn small" href="{html.escape(file_url)}" download>↓ Download</a>
                  <button class="btn small ghost" onclick="copyPath('{html.escape(str(path))}')">Copy path</button>
                </div>
              </div>
            </div>""")
        else:  # video
            assets_html_blocks.append(f"""
            <div class="asset-card video">
              <video controls preload="metadata" src="{html.escape(file_url)}"></video>
              <div class="asset-meta">
                <div class="asset-name">{html.escape(fname)}</div>
                <div class="asset-path">{html.escape(str(path))}</div>
                <div class="asset-actions">
                  <a class="btn small" href="{html.escape(file_url)}" download>↓ Download</a>
                  <button class="btn small ghost" onclick="copyPath('{html.escape(str(path))}')">Copy path</button>
                </div>
              </div>
            </div>""")

    assets_block = "".join(assets_html_blocks) if assets_html_blocks else ""
    assets_count = len(assets)
    assets_summary = ""
    if assets:
        images_count = sum(1 for k, _ in assets if k == "image")
        videos_count = sum(1 for k, _ in assets if k == "video")
        parts = []
        if images_count:
            parts.append(f"{images_count} image{'s' if images_count > 1 else ''}")
        if videos_count:
            parts.append(f"{videos_count} video{'s' if videos_count > 1 else ''}")
        assets_summary = " + ".join(parts)

    folder_path = str(first_asset_dir) if first_asset_dir else ""

    caption_escaped = html.escape(caption)

    return f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>Post packet · {html.escape(channel_name)} · {html.escape(entry_id)}</title>
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;700&family=Orbitron:wght@600;900&family=Space+Grotesk:wght@500;700&display=swap" rel="stylesheet" />
<style>
 * {{ box-sizing: border-box; }}
 html, body {{ margin: 0; padding: 0; background: {BG}; color: {TEXT}; font-family: 'Manrope', system-ui; font-size: 15px; line-height: 1.55; }}
 .wrap {{ max-width: 1080px; margin: 0 auto; padding: 32px 24px 80px; }}
 header {{ display: flex; gap: 16px; align-items: center; padding: 20px 0; border-bottom: 1px solid {BORDER}; margin-bottom: 28px; }}
 .channel-badge {{ display: inline-flex; align-items: center; justify-content: center; width: 48px; height: 48px; border-radius: 12px; color: white; font-family: 'Orbitron', sans-serif; font-weight: 900; font-size: 18px; background: {channel_color}; }}
 .head-meta {{ flex: 1; }}
 .head-meta .channel {{ font-family: 'Orbitron', sans-serif; font-weight: 900; font-size: 20px; letter-spacing: 2px; background: linear-gradient(90deg, {PRIMARY}, #7ec5ff); -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent; }}
 .head-meta .sub {{ color: {MUTED}; font-family: 'Space Grotesk', sans-serif; font-size: 14px; margin-top: 2px; }}
 .head-meta .sub .sep {{ color: {BORDER}; padding: 0 8px; }}
 h2 {{ font-family: 'Space Grotesk', sans-serif; font-weight: 700; font-size: 14px; letter-spacing: 2px; text-transform: uppercase; color: {MUTED}; margin: 32px 0 12px; }}
 .cap-box {{ background: {CARD_BG}; border: 1px solid {BORDER}; border-radius: 14px; padding: 24px; position: relative; }}
 .cap-box pre {{ white-space: pre-wrap; word-wrap: break-word; font-family: 'Manrope', system-ui; font-size: 16px; line-height: 1.65; margin: 0; color: {TEXT}; }}
 .cap-actions {{ display: flex; gap: 10px; margin-top: 20px; flex-wrap: wrap; }}
 .btn {{ display: inline-flex; align-items: center; gap: 8px; padding: 12px 20px; background: {PRIMARY}; color: white; border: none; border-radius: 10px; font-family: 'Space Grotesk', sans-serif; font-weight: 700; font-size: 14px; cursor: pointer; text-decoration: none; transition: filter 0.15s, transform 0.15s; }}
 .btn:hover {{ filter: brightness(1.15); transform: translateY(-1px); }}
 .btn.large {{ padding: 16px 28px; font-size: 16px; }}
 .btn.ghost {{ background: transparent; border: 1px solid {BORDER}; color: {TEXT}; }}
 .btn.ghost:hover {{ border-color: {PRIMARY}; color: {PRIMARY}; }}
 .btn.small {{ padding: 6px 12px; font-size: 12px; border-radius: 6px; }}
 .btn.ok {{ background: {GREEN}; }}
 .copied {{ color: {GREEN} !important; animation: flash 0.5s ease; }}
 @keyframes flash {{ 0% {{ transform: scale(1); }} 50% {{ transform: scale(1.05); }} 100% {{ transform: scale(1); }} }}
 .primary-action {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin: 20px 0 10px; }}
 .asset-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 16px; }}
 .asset-card {{ background: {CARD_BG}; border: 1px solid {BORDER}; border-radius: 12px; overflow: hidden; transition: border-color 0.2s; }}
 .asset-card:hover {{ border-color: {PRIMARY}; }}
 .asset-card .thumb-wrap {{ display: block; background: #000; }}
 .asset-card img {{ width: 100%; aspect-ratio: 4/5; object-fit: cover; display: block; }}
 .asset-card.video video {{ width: 100%; max-height: 400px; display: block; background: #000; }}
 .asset-meta {{ padding: 12px; }}
 .asset-name {{ font-family: 'Space Grotesk'; font-weight: 700; font-size: 13px; color: {TEXT}; word-break: break-all; }}
 .asset-path {{ font-size: 11px; color: {MUTED}; word-break: break-all; margin: 6px 0 10px; font-family: monospace; }}
 .asset-actions {{ display: flex; gap: 6px; flex-wrap: wrap; }}
 .no-assets {{ color: {MUTED}; font-style: italic; padding: 24px; background: {CARD_BG}; border-radius: 10px; border: 1px dashed {BORDER}; }}
 .instructions {{ background: rgba(59,158,255,0.08); border: 1px solid rgba(59,158,255,0.25); border-left: 4px solid {PRIMARY}; border-radius: 10px; padding: 18px 22px; margin: 24px 0; }}
 .instructions h3 {{ margin: 0 0 10px; font-family: 'Space Grotesk'; font-size: 14px; text-transform: uppercase; letter-spacing: 1px; color: {PRIMARY}; }}
 .instructions ol {{ margin: 0; padding-left: 24px; line-height: 1.8; }}
 .toast {{ position: fixed; top: 24px; right: 24px; background: {GREEN}; color: white; padding: 14px 22px; border-radius: 10px; font-family: 'Space Grotesk'; font-weight: 700; font-size: 14px; opacity: 0; transform: translateY(-10px); transition: all 0.25s; pointer-events: none; }}
 .toast.show {{ opacity: 1; transform: translateY(0); }}
</style>
</head>
<body>

<div class="toast" id="toast">Copied</div>

<div class="wrap">
  <header>
    <div class="channel-badge">{channel_icon}</div>
    <div class="head-meta">
      <div class="channel">{html.escape(channel_name)} · {html.escape(fmt)}</div>
      <div class="sub">
        {html.escape(entry_id)}<span class="sep">·</span>
        {html.escape(sched_display)}<span class="sep">·</span>
        {html.escape(pillar) if pillar else 'no pillar'}
        {f'<span class="sep">·</span>{assets_count} assets ({html.escape(assets_summary)})' if assets else ''}
      </div>
    </div>
  </header>

  <h2>Caption</h2>
  <div class="cap-box">
    <pre id="caption">{caption_escaped}</pre>
    <div class="cap-actions">
      <button class="btn" id="copy-btn" onclick="copyCaption()">📋 Copy caption</button>
      {f'<a class="btn ghost" href="{html.escape(composer_url)}" target="_blank">→ Open composer (text pre-filled)</a>' if channel in ("x","twitter","whatsapp") else f'<a class="btn ghost" href="{html.escape(static_url)}" target="_blank">→ Open composer</a>'}
    </div>
  </div>

  {"".join([
    '<div class="instructions"><h3>🎬 How to post</h3><ol>',
    '<li>Click <b>Copy caption</b> above.</li>',
  ])}
  {_instructions_for_channel(channel, assets, composer_url, static_url, folder_path)}
  </ol></div>

  <h2>Assets {f'({assets_count})' if assets else ''}</h2>
  {f'<div class="asset-grid">{assets_block}</div>' if assets_block else '<div class="no-assets">No assets for this post. Caption-only.</div>'}

  {f'<h2>Folder</h2><div class="cap-box"><code style="color:{MUTED}">{html.escape(folder_path)}</code><div class="cap-actions"><button class="btn ghost" onclick="revealFolder()">→ Reveal in Finder</button></div></div>' if folder_path else ''}
</div>

<script>
const FOLDER = {repr(folder_path)};
const CAPTION = document.getElementById('caption').textContent;

function showToast(msg) {{
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 1400);
}}

async function copyCaption() {{
  try {{
    await navigator.clipboard.writeText(CAPTION);
    const btn = document.getElementById('copy-btn');
    btn.textContent = '✓ Copied';
    btn.classList.add('copied');
    showToast('Caption copied to clipboard');
    setTimeout(() => {{ btn.textContent = '📋 Copy caption'; btn.classList.remove('copied'); }}, 2000);
  }} catch (e) {{
    alert('Copy failed: ' + e.message);
  }}
}}

async function copyPath(path) {{
  try {{
    await navigator.clipboard.writeText(path);
    showToast('Path copied');
  }} catch (e) {{ alert('Copy failed: ' + e.message); }}
}}

function revealFolder() {{
  // Browsers can't open Finder directly. Guide user to use the path.
  navigator.clipboard.writeText(FOLDER);
  showToast('Folder path copied — paste in Finder (Cmd+Shift+G)');
}}

// Auto-copy caption on page load so Cmd+V in composer just works
window.addEventListener('load', () => {{
  navigator.clipboard.writeText(CAPTION).catch(() => {{}});
}});
</script>
</body></html>"""


def _instructions_for_channel(channel: str, assets: list, composer_url: str, static_url: str, folder_path: str) -> str:
    has_assets = bool(assets)
    if channel in ("x", "twitter"):
        if has_assets:
            return (
                f'<li>Click <b>→ Open composer</b> — X composer will open with caption already typed.</li>'
                f'<li>In X composer, click the image icon and select the {len(assets)} file(s) below (or drag from the Reveal-in-Finder folder).</li>'
                f'<li>Click <b>Post</b>.</li>'
            )
        return (
            '<li>Click <b>→ Open composer</b> — X composer will open with caption already typed.</li>'
            '<li>Click <b>Post</b>. Done.</li>'
        )
    if channel == "instagram":
        if has_assets:
            return (
                '<li>Click <b>→ Open composer</b> — instagram.com opens. Click the <b>+</b> button at the top, then <b>Post</b>.</li>'
                f'<li>Drag all {len(assets)} slides from the asset cards below (or from Finder folder) into the IG upload area. Order is preserved by filename.</li>'
                '<li>Paste caption into the caption field (Cmd+V).</li>'
                '<li>Click <b>Share</b>.</li>'
            )
        return (
            '<li>Click <b>→ Open composer</b> — instagram.com opens.</li>'
            '<li>Click <b>+</b> → <b>Post</b>, upload your own image, paste caption, Share.</li>'
        )
    if channel == "facebook":
        return (
            '<li>Click <b>→ Open composer</b> — facebook.com opens.</li>'
            '<li>Click the status box at top of feed.</li>'
            f'<li>{"Paste caption (Cmd+V), then attach the asset file(s) below." if has_assets else "Paste caption (Cmd+V)."}</li>'
            '<li>Click <b>Post</b>.</li>'
        )
    if channel == "whatsapp":
        return (
            '<li>Click <b>→ Open composer</b> — WhatsApp Web opens a chat with text pre-filled.</li>'
            '<li>Attach image/video if needed (paperclip icon).</li>'
            '<li>Hit send.</li>'
        )
    return (
        '<li>Click <b>→ Open composer</b>.</li>'
        '<li>Paste caption (Cmd+V) and attach any assets below.</li>'
    )


def render_and_open(fm: dict, body: str, brand_folder: Path) -> Path:
    """Render packet to /tmp, open in default browser, return path."""
    entry_id = fm.get("entry_id") or "unknown"
    channel = (fm.get("channel") or "unknown").lower()
    out_path = Path(f"/tmp/post-packet-{entry_id}-{channel}.html")
    out_path.write_text(render_packet_html(fm, body, brand_folder), encoding="utf-8")
    try:
        subprocess.run(["open", str(out_path)], check=False, timeout=5)
    except Exception:
        pass
    return out_path


# ── CLI ────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--draft", required=True, type=Path, help="Path to draft markdown file")
    ap.add_argument("--brand-folder", type=Path,
                    default=Path("/Users/digischola/Desktop/Digischola"))
    ap.add_argument("--no-open", action="store_true")
    args = ap.parse_args()

    if not args.draft.exists():
        sys.exit(f"Not found: {args.draft}")
    fm, body = fio.read(args.draft)
    out = render_packet_html(fm, body, args.brand_folder)
    entry_id = fm.get("entry_id") or "unknown"
    channel = (fm.get("channel") or "unknown").lower()
    out_path = Path(f"/tmp/post-packet-{entry_id}-{channel}.html")
    out_path.write_text(out, encoding="utf-8")
    print(f"Wrote: {out_path}")
    if not args.no_open:
        subprocess.run(["open", str(out_path)], check=False)


if __name__ == "__main__":
    main()
