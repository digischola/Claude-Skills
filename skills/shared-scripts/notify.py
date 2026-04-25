"""
Centralized macOS notification helper for the Digischola skill suite.

Every script that needs to notify the user should import and use this module
instead of inlining its own osascript / terminal-notifier calls.

Design goals
------------
1. **Every notification has a click-to-action.**
   Plain banners that sit there with nothing clickable are a UX dead-end. The
   user sees the banner, forgets what to do next, dismisses it, work gets lost.
   So `notify()` strongly prefers `open_url` — that's the handoff the click
   actually performs.

2. **One helper, many callers.** This module is imported by
   scheduler-publisher, weekly-ritual, visual-generator, performance-review,
   etc. Change behavior here → every skill picks it up.

3. **Graceful fallback.** If `terminal-notifier` (the brew package that
   supports `-open <url>`) isn't installed, fall back to plain osascript
   (banner-only, no click). Never crash the caller over a missing notifier.

Interface
---------
    notify(
        title,              # required — "Sunday ritual complete"
        message,            # required — body of the banner (1-2 short lines)
        *,
        subtitle=None,      # optional small second line (osascript
                            #   `subtitle`, terminal-notifier `-subtitle`)
        open_url=None,      # str — when user clicks banner, open this URL/path
                            #   in the default handler. Supports http(s)://,
                            #   file://, or absolute fs path (auto-converted).
        sound="Glass",      # macOS system sound name ("Glass", "Basso",
                            #   "Hero", "Ping", etc.) or None for silent
        group=None,         # terminal-notifier group id — replaces prior
                            #   banner with same group (useful for progress
                            #   updates that shouldn't stack)
        activate=None,      # bundle id to bring to front when clicked
                            #   (e.g., "com.google.Chrome", "com.apple.finder")
        reveal=None,        # filesystem path — click reveals this file in
                            #   Finder (uses `open -R` behavior). Takes
                            #   precedence over open_url when set.
    )

Returns
-------
    dict with {"ok": bool, "backend": "terminal-notifier"|"osascript"|"none",
              "error": str|None}. Never raises.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Optional

# Where terminal-notifier should live when installed via Homebrew on Apple Silicon
TERMINAL_NOTIFIER_PATHS = [
    "/opt/homebrew/bin/terminal-notifier",   # Apple Silicon brew
    "/usr/local/bin/terminal-notifier",      # Intel brew
]


def _find_terminal_notifier() -> Optional[str]:
    """Return path to terminal-notifier binary, or None if not installed."""
    # Prefer the explicit paths (faster than PATH lookup)
    for p in TERMINAL_NOTIFIER_PATHS:
        if Path(p).exists():
            return p
    # Fall back to $PATH
    found = shutil.which("terminal-notifier")
    return found  # None if not found anywhere


def _normalize_url(open_url: Optional[str]) -> Optional[str]:
    """
    terminal-notifier `-open` accepts http(s):// directly, but for local
    filesystem paths we need `file://` prefix. Also handles paths that were
    passed as Path objects (stringify first).
    """
    if not open_url:
        return None
    s = str(open_url).strip()
    if not s:
        return None
    # Already a URL?
    if s.startswith(("http://", "https://", "file://", "mailto:", "ftp://")):
        return s
    # Looks like an absolute fs path → file://
    if s.startswith("/"):
        return f"file://{s}"
    # Relative path — resolve to absolute then file://
    p = Path(s).resolve()
    return f"file://{p}"


def _osascript_notify(title: str, message: str, subtitle: Optional[str],
                      sound: Optional[str]) -> dict:
    """Pure-macOS fallback (no click-through). Always available on macOS."""
    parts = [f'display notification "{_escape_as(message)}"',
             f'with title "{_escape_as(title)}"']
    if subtitle:
        parts.append(f'subtitle "{_escape_as(subtitle)}"')
    if sound:
        parts.append(f'sound name "{_escape_as(sound)}"')
    script = " ".join(parts)
    try:
        r = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, text=True, timeout=5,
        )
        if r.returncode != 0:
            return {"ok": False, "backend": "osascript",
                    "error": (r.stderr or "").strip()}
        return {"ok": True, "backend": "osascript", "error": None}
    except Exception as e:
        return {"ok": False, "backend": "osascript", "error": str(e)}


def _escape_as(s: str) -> str:
    """Escape for AppleScript double-quoted string."""
    return (s or "").replace("\\", "\\\\").replace('"', '\\"')


def notify(
    title: str,
    message: str,
    *,
    subtitle: Optional[str] = None,
    open_url: Optional[str] = None,
    sound: Optional[str] = "Glass",
    group: Optional[str] = None,
    activate: Optional[str] = None,
    reveal: Optional[str] = None,
) -> dict:
    """
    Fire a macOS notification. Returns dict with {ok, backend, error}.

    Prefers `terminal-notifier` (supports click-to-open); falls back to
    osascript (banner-only) if terminal-notifier isn't installed. Never raises.
    """
    # Reveal takes precedence over open_url when both set — reveal wraps
    # the path in a special AppleScript that opens Finder focused on it.
    tn_path = _find_terminal_notifier()

    if tn_path is None:
        # No terminal-notifier → osascript banner (no click-through possible)
        return _osascript_notify(title, message, subtitle, sound)

    # Build terminal-notifier command
    cmd = [tn_path, "-title", title, "-message", message]
    if subtitle:
        cmd += ["-subtitle", subtitle]
    if sound:
        cmd += ["-sound", sound]
    if group:
        cmd += ["-group", group]

    # Reveal wins over open_url: use -execute to run `open -R <path>`
    if reveal:
        reveal_path = str(reveal)
        # `open -R` reveals the file in a Finder window
        cmd += ["-execute", f'/usr/bin/open -R "{reveal_path}"']
    elif activate:
        cmd += ["-activate", activate]
        if open_url:
            # activate + open: open the url/file THEN bring app forward
            normalized = _normalize_url(open_url)
            if normalized:
                cmd += ["-open", normalized]
    elif open_url:
        normalized = _normalize_url(open_url)
        if normalized:
            cmd += ["-open", normalized]

    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        if r.returncode != 0:
            # terminal-notifier failed — fall back to osascript so user at
            # least sees the banner
            fallback = _osascript_notify(title, message, subtitle, sound)
            fallback["error"] = (
                f"terminal-notifier exit {r.returncode}: "
                f"{(r.stderr or '').strip()[:200]}"
            )
            return fallback
        return {"ok": True, "backend": "terminal-notifier", "error": None}
    except subprocess.TimeoutExpired:
        return {"ok": False, "backend": "terminal-notifier",
                "error": "timeout"}
    except Exception as e:
        # Last resort: osascript
        fallback = _osascript_notify(title, message, subtitle, sound)
        fallback["error"] = f"terminal-notifier exception: {e}"
        return fallback


def has_click_through() -> bool:
    """Probe: does this machine support clickable banners (terminal-notifier)?"""
    return _find_terminal_notifier() is not None


# ─────────────────────────────────────────────────────────────────────────────
# Reviewable-artifact helper
#
# Rule locked in backlog 2026-04-22 item #7: any time a skill produces a
# reviewable artifact (draft text, rendered carousel, rendered reel), the
# notification must land the user in a UI where they can Approve/Edit/Reject
# that specific artifact inline — NOT a standalone preview page.
#
# This helper does the heavy lifting so producer scripts just call one
# function:
#
#     from notify import notify_reviewable_artifact
#     notify_reviewable_artifact(
#         title="Carousel rendered",
#         body="8 slides · entry 6ad745b7",
#         entry_id="6ad745b7",
#         brand_folder=brand_folder,
#     )
#
# Behavior:
#   1. Finds the draft in pending-approval/ that matches entry_id + is a
#      visual format (carousel / reel / etc.)
#   2. Ensures review_queue.py is running on REVIEW_PORT (spawns it if not).
#   3. Builds URL http://127.0.0.1:<port>/#draft-<filename-without-ext>
#   4. Fires notify(title, body, open_url=url)
#
# If no matching draft is found, falls back to opening the root review URL.
# ─────────────────────────────────────────────────────────────────────────────

REVIEW_PORT = 8765
REVIEW_QUEUE_SCRIPT = (
    "/Users/digischola/Desktop/Claude Skills/skills/"
    "scheduler-publisher/scripts/review_queue.py"
)
VISUAL_FORMATS = {
    "carousel", "reel", "reel-script", "animated-graphic",
    "animated", "quote-card", "story", "video",
}


def _review_queue_running(port: int = REVIEW_PORT) -> bool:
    """True if something is listening on localhost:<port>."""
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.3)
    try:
        s.connect(("127.0.0.1", port))
        return True
    except Exception:
        return False
    finally:
        try:
            s.close()
        except Exception:
            pass


def _ensure_review_queue(port: int = REVIEW_PORT, wait_s: float = 2.0) -> bool:
    """Start review_queue.py in background if not already running.

    Returns True if server is up by the time we return, False if we gave up.
    """
    import time
    if _review_queue_running(port):
        return True
    if not Path(REVIEW_QUEUE_SCRIPT).exists():
        return False
    # Spawn detached so the server outlives this caller
    try:
        subprocess.Popen(
            ["python3", REVIEW_QUEUE_SCRIPT,
             "--port", str(port), "--no-open", "--no-notify"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except Exception:
        return False
    # Wait (briefly) for port to come up
    deadline = time.monotonic() + wait_s
    while time.monotonic() < deadline:
        if _review_queue_running(port):
            return True
        time.sleep(0.1)
    return _review_queue_running(port)


def _find_draft_filename(brand_folder: Path, entry_id: str,
                         visual_only: bool = False) -> Optional[str]:
    """Find a draft .md in pending-approval/ whose entry_id matches.

    If visual_only is True, restrict to drafts whose `format` is a visual
    format (carousel / reel / etc.). Returns the filename (not full path), or
    None if no match.
    """
    import re
    pending = Path(brand_folder) / "brand" / "queue" / "pending-approval"
    if not pending.exists() or not entry_id:
        return None
    entry_id_clean = str(entry_id).strip().strip("'\"")
    # Accept entry_id in frontmatter as either bare or quoted
    for p in sorted(pending.glob("*.md")):
        try:
            text = p.read_text(errors="replace")
        except Exception:
            continue
        # Only scan the frontmatter block (between leading ---)
        head_m = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
        head = head_m.group(1) if head_m else text[:2000]
        # entry_id line
        id_m = re.search(
            r"^\s*entry_id\s*:\s*['\"]?(\S+?)['\"]?\s*$", head, re.MULTILINE,
        )
        if not id_m or id_m.group(1) != entry_id_clean:
            continue
        if visual_only:
            fmt_m = re.search(
                r"^\s*format\s*:\s*['\"]?(\S+?)['\"]?\s*$",
                head, re.MULTILINE,
            )
            fmt = (fmt_m.group(1).lower() if fmt_m else "")
            if fmt not in VISUAL_FORMATS:
                continue
        return p.name
    return None


def notify_reviewable_artifact(
    *,
    title: str,
    body: str,
    entry_id: Optional[str] = None,
    brand_folder=None,
    draft_filename: Optional[str] = None,
    subtitle: str = "Digischola",
    sound: str = "Glass",
    visual_only: bool = True,
    port: int = REVIEW_PORT,
    start_server: bool = True,
) -> dict:
    """Notify about a newly-produced reviewable artifact (draft / visual).

    Click lands on the specific draft card in review_queue.py — so user can
    Approve / Edit / Reject inline. Starts the review server if needed.
    """
    # Resolve the draft filename (unless caller gave it explicitly)
    filename = draft_filename
    if not filename and brand_folder and entry_id:
        filename = _find_draft_filename(
            Path(brand_folder), entry_id, visual_only=visual_only,
        )
    # Ensure the review UI is up
    if start_server:
        _ensure_review_queue(port=port)
    # Build URL — with anchor if we know the draft, else root
    url = f"http://127.0.0.1:{port}/"
    if filename:
        stem = filename[:-3] if filename.endswith(".md") else filename
        url = f"{url}#draft-{stem}"
    return notify(
        title, body,
        subtitle=subtitle,
        open_url=url,
        sound=sound,
        group="digischola-review",
    )


# CLI for quick testing:
#   python3 notify.py "Title" "Message" --open http://example.com
if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("title")
    ap.add_argument("message")
    ap.add_argument("--subtitle")
    ap.add_argument("--open", dest="open_url")
    ap.add_argument("--reveal")
    ap.add_argument("--sound", default="Glass")
    ap.add_argument("--group")
    ap.add_argument("--activate")
    args = ap.parse_args()
    result = notify(
        args.title, args.message,
        subtitle=args.subtitle,
        open_url=args.open_url,
        reveal=args.reveal,
        sound=args.sound,
        group=args.group,
        activate=args.activate,
    )
    print(result)
