#!/usr/bin/env python3
"""
Manual publisher — for Instagram, Facebook, WhatsApp Status.

Zero Meta API exposure (Meta API can flag accounts even when used correctly).
At scheduled_at:
  1. Fire a macOS notification with the entry_id + caption preview
  2. Copy the full caption to the clipboard
  3. Reveal the asset folder in Finder (so user can drag the rendered MP4/PNGs)
  4. Open the platform's web composer in the default browser

User then publishes manually in the native app or web (~30 sec). They confirm via
`confirm_published.py` which captures the live URL and updates frontmatter.

Returns PublishResult(status="notified") on success.
"""

from __future__ import annotations

import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

# Import push_notify + post_packet from sibling scripts/ dir
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
try:
    import push_notify  # type: ignore
except Exception:
    push_notify = None
try:
    import post_packet  # type: ignore
except Exception:
    post_packet = None


@dataclass
class PublishResult:
    status: str          # "notified" | "failed"
    url: Optional[str] = None
    reason: Optional[str] = None
    retry_after_sec: int = 0


# Where the user actually composes. When possible we use URL-intent patterns
# that pre-fill the caption via URL param — no paste needed, just click Post.
#
# Per-channel:
#   X       → intent URL pre-fills text via ?text=<urlencoded>. Verified 2026-04-20.
#   WhatsApp → wa.me/?text= pre-fills WA Web. whatsapp:// scheme for phone.
#   Instagram → no URL-intent support (security). Opens app home; user clicks +.
#                Still benefits from clipboard + Finder reveal of assets.
#   Facebook → sharer.php exists but is for link-share-with-quote, not a regular
#              post. We keep the plain URL; caption is in clipboard for paste.
#
# Intent URL callable per channel — takes caption, returns ready-to-open URL.
import urllib.parse as _urlparse

def _x_intent_url(caption: str) -> str:
    # Truncate if over X free limit (280 chars), show first-block only for thread drafts
    first_block = caption.strip().split("\n\n")[0] if caption else ""
    primary = caption if len(caption) <= 280 else first_block
    return f"https://x.com/intent/post?text={_urlparse.quote(primary)}"

def _whatsapp_intent_url(caption: str) -> str:
    return f"https://wa.me/?text={_urlparse.quote(caption)}"


# Static fallback URLs used when we don't need caption pre-fill (IG / FB).
STATIC_COMPOSER_URLS = {
    "instagram": "https://www.instagram.com/",   # no intent API; user clicks +
    "facebook": "https://www.facebook.com/",     # same
    "whatsapp": "https://web.whatsapp.com/",     # overridden by intent when caption present
    "x": "https://x.com/compose/post",           # overridden by intent
    "twitter": "https://x.com/compose/post",
}

# Back-compat export (older callers, tests)
COMPOSER_URLS = STATIC_COMPOSER_URLS


def composer_url_for(channel: str, caption: str) -> str:
    """Return the best composer URL for this channel + caption.
    Prefers intent URL (pre-fills caption) when the channel supports it."""
    c = (channel or "").lower()
    if c in ("x", "twitter") and caption:
        return _x_intent_url(caption)
    if c == "whatsapp" and caption:
        return _whatsapp_intent_url(caption)
    return STATIC_COMPOSER_URLS.get(c, "")

# Platform-specific notification copy
NOTIFICATION_COPY = {
    "instagram": ("Instagram post ready", "Caption copied. Asset folder open. Open IG to post."),
    "facebook": ("Facebook post ready", "Caption copied. Asset folder open. Open FB to post."),
    "whatsapp": ("WhatsApp Status ready", "Caption copied. Asset folder open. Open WhatsApp."),
    "x": ("X post ready", "Caption copied. Asset folder open. X composer opening in browser."),
    "twitter": ("X post ready", "Caption copied. Asset folder open. X composer opening in browser."),
}


def _osascript(script: str) -> tuple[int, str, str]:
    proc = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True, text=True, timeout=10,
    )
    return proc.returncode, proc.stdout, proc.stderr


def copy_to_clipboard(text: str) -> bool:
    """pbcopy text to clipboard. Safe even with Unicode."""
    try:
        proc = subprocess.run(
            ["pbcopy"], input=text.encode("utf-8"), check=True, timeout=5,
        )
        return proc.returncode == 0
    except Exception:
        return False


def reveal_in_finder(path: Path) -> bool:
    """Open Finder, select the path, AND bring Finder to front."""
    if not path.exists():
        return False
    try:
        subprocess.run(["open", "-R", str(path)], check=True, timeout=5)
        # open -R reveals but doesn't activate — Finder can end up behind other apps.
        # Follow up with explicit activation so the user actually sees the window.
        subprocess.run(
            ["osascript", "-e", 'tell application "Finder" to activate'],
            capture_output=True, timeout=5,
        )
        return True
    except Exception:
        return False


def open_url(url: str) -> bool:
    try:
        subprocess.run(["open", url], check=True, timeout=5)
        return True
    except Exception:
        return False


TERMINAL_NOTIFIER = "/opt/homebrew/bin/terminal-notifier"


def send_notification(title: str, subtitle: str, message: str, sound: str = "Glass",
                      open_url: Optional[str] = None,
                      execute: Optional[str] = None,
                      sender: str = "com.apple.finder") -> bool:
    """Display a macOS notification. Prefers terminal-notifier (clickable) when
    available; falls back to osascript (no click action — opens Script Editor)."""
    # Try terminal-notifier first — supports click-to-open-URL + custom sender bundle
    # so clicking the notification doesn't open Script Editor.
    from pathlib import Path as _Path
    if _Path(TERMINAL_NOTIFIER).exists():
        cmd = [TERMINAL_NOTIFIER,
               "-title", title,
               "-subtitle", subtitle,
               "-message", message,
               "-sound", sound,
               "-sender", sender]
        if open_url:
            cmd.extend(["-open", open_url])
        elif execute:
            cmd.extend(["-execute", execute])
        try:
            rc = subprocess.run(cmd, capture_output=True, text=True, timeout=10).returncode
            if rc == 0:
                return True
        except Exception:
            pass  # fall through to osascript
    # Fallback: osascript (no click-to-open — Script Editor opens on click)
    def esc(s: str) -> str:
        return s.replace("\\", "\\\\").replace('"', '\\"')
    script = (
        f'display notification "{esc(message)}" '
        f'with title "{esc(title)}" '
        f'subtitle "{esc(subtitle)}" '
        f'sound name "{esc(sound)}"'
    )
    rc, _, err = _osascript(script)
    if rc != 0:
        print(f"  notification failed: {err}", file=sys.stderr)
        return False
    return True


def fire_post_ready_notification(channel: str, entry_id: str, caption: str,
                                 assets_dir: Optional[Path], composer_url: Optional[str]) -> bool:
    title, subtitle = NOTIFICATION_COPY.get(channel, (f"{channel.title()} post ready", "Caption copied."))
    preview = caption[:80].replace("\n", " ")
    message = f"{entry_id}: {preview}…" if len(caption) > 80 else f"{entry_id}: {preview}"

    # Side effects in order
    copied = copy_to_clipboard(caption)
    revealed = reveal_in_finder(assets_dir) if assets_dir else False
    opened = open_url(composer_url) if composer_url else False

    # Click the notification → opens the composer URL (no more Script Editor).
    notified = send_notification(title, subtitle, message, sound="Glass",
                                 open_url=composer_url)

    # Fan-out to push providers (ntfy/Slack/Telegram) so user isn't blocked on
    # being in front of Mac. No-op if no providers configured.
    if push_notify is not None:
        try:
            push_notify.fire_push(
                title=title,
                body=f"{entry_id}\n\n{caption[:500]}",
                url=composer_url,
                silent_failure=True,
            )
        except Exception as e:
            print(f"  push_notify exception (ignored): {e}", file=sys.stderr)

    # If copy or reveal failed, still notify but adjust subtitle
    if not copied:
        send_notification(title, "Copy to clipboard FAILED — paste from draft manually",
                          message, sound="Funk")
    return notified


def _push_to_phone(title: str, body: str, url: Optional[str] = None) -> None:
    """Fire to ntfy.sh / Slack / Telegram in addition to the local Mac banner.
    Patched 2026-04-23 — user reported missing the first-ship banner because
    laptop lid was closed. Local banners go to Notification Center history
    when the Mac is in Power Nap, which the user can easily miss. Push-to-
    phone gives a second signal that works regardless of Mac state.
    Silent failure: if push isn't configured OR network is down, the local
    banner still fired, so we don't want to block on push. Never raises."""
    if push_notify is None:
        return
    try:
        push_notify.fire_push(title, body, url, silent_failure=True)
    except Exception as e:
        print(f"  push fan-out failed (non-fatal): {e}", file=sys.stderr)


def fire_overdue_reminder(channel: str, entry_id: str, hours_since: int,
                          draft_path: Optional[Path] = None) -> bool:
    title = f"Did you post the {channel.title()}?"
    subtitle = f"{entry_id} · {hours_since}h since notification"
    message = "Click to open the draft file to finish posting."
    # Click action: reveal the draft in Finder so user can paste caption + publish.
    # Patched 2026-04-22 notification-UX batch: overdue banners used to
    # reference confirm_published.py but didn't open anything — dead-end.
    execute = None
    if draft_path is not None and Path(draft_path).exists():
        execute = f'/usr/bin/open -R "{draft_path}"'
    ok = send_notification(title, subtitle, message, sound="Funk",
                           execute=execute)
    _push_to_phone(title, f"{subtitle}. {message}")
    return ok


def fire_failure_notification(channel: str, entry_id: str, reason: str,
                              draft_path: Optional[Path] = None) -> bool:
    title = f"{channel.title()} post FAILED"
    subtitle = f"{entry_id} · 3 retries exhausted"
    message = f"Reason: {reason[:100]}. Click to open the draft."
    # Click action: reveal the draft file so user can inspect / retry / escalate.
    execute = None
    if draft_path is not None and Path(draft_path).exists():
        execute = f'/usr/bin/open -R "{draft_path}"'
    ok = send_notification(title, subtitle, message, sound="Basso",
                           execute=execute)
    _push_to_phone(title, f"{subtitle}. {message}")
    return ok


def fire_token_expiring_notification(channel: str, days_left: int) -> bool:
    title = f"{channel.title()} token expires in {days_left} days"
    subtitle = "Click to open the setup script"
    message = f"Re-run setup_{channel}.py to refresh the token."
    # Click action: reveal the setup script in Finder.
    setup_script = Path(__file__).resolve().parent.parent / f"setup_{channel}.py"
    execute = None
    if setup_script.exists():
        execute = f'/usr/bin/open -R "{setup_script}"'
    ok = send_notification(title, subtitle, message, sound="Funk",
                           execute=execute)
    _push_to_phone(title, message)
    return ok


def fire_ship_success_notification(channel: str, entry_id: str,
                                   posted_url: Optional[str]) -> bool:
    """Banner for autonomous-channel successful ships (LinkedIn API).
    Click opens the live post URL in the default browser so user can verify
    the post rendered correctly and jump to metrics collection later.
    Added 2026-04-22 notification-UX batch: autonomous ships were silent, the
    user only saw a log line.
    Patched 2026-04-23: also pushes to phone (ntfy.sh/Slack/Telegram) via
    push_notify so the user doesn't miss a ship that happened while lid was
    closed.
    """
    title = f"{channel.title()} post shipped"
    subtitle = f"{entry_id}"
    if posted_url:
        message = "Click to view the live post."
        ok = send_notification(title, subtitle, message, sound="Glass",
                               open_url=posted_url)
        _push_to_phone(title, f"{subtitle} — {posted_url}", url=posted_url)
    else:
        ok = send_notification(title, subtitle, "Shipped via API.",
                               sound="Glass")
        _push_to_phone(title, f"{subtitle} — shipped via API.")
    return ok


# ── Dispatch from a draft ─────────────────────────────────────────────────


def publish_draft(fm: dict, body: str, brand_folder: Path) -> PublishResult:
    """Fire the notification + clipboard + Finder reveal. Returns 'notified' status.
    The actual publish is done manually by the user in the native app."""
    channel = fm.get("channel", "instagram")
    entry_id = fm.get("entry_id", "unknown")
    caption = body.strip()

    assets_dir_rel = (
        fm.get("visual_assets_dir")
        or fm.get("visual_assets_dir_anim")
        or fm.get("visual_assets_dir_reel_v2")
    )
    assets_path: Optional[Path] = None
    if assets_dir_rel:
        candidate = Path(assets_dir_rel)
        if not candidate.is_absolute():
            candidate = brand_folder / assets_dir_rel
        if candidate.exists():
            assets_path = candidate

    composer_url = composer_url_for(channel, caption)

    # Render + open the post packet (single page with caption + thumbnails + composer link)
    packet_path = None
    if post_packet is not None:
        try:
            packet_path = post_packet.render_and_open(fm, body, brand_folder)
        except Exception as e:
            print(f"  post_packet render failed (continuing): {e}", file=sys.stderr)

    success = fire_post_ready_notification(
        channel=channel,
        entry_id=entry_id,
        caption=caption,
        assets_dir=assets_path,
        composer_url=composer_url,
    )
    if not success:
        return PublishResult(status="failed", reason="notification_dispatch_failed")
    return PublishResult(status="notified")
