#!/usr/bin/env python3
"""
Push-notification fan-out for scheduler-publisher.

At scheduled_at, after the local macOS notification fires, we also push the
same alert to phone / chat apps so Mayank doesn't miss posts when away from Mac.

Three providers, all free (no paid APIs):

  1. ntfy.sh   — free public topic, no auth. iOS + Android apps.
                 Config: NTFY_TOPIC env var OR ~/.config/digischola/ntfy_topic
  2. Slack     — free webhook URL from any Slack workspace.
                 Config: SLACK_WEBHOOK_URL env var
  3. Telegram  — free bot + chat_id.
                 Config: TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID env vars

If no provider is configured, this module is a no-op (returns silently).
If multiple are configured, all of them fire (redundant = resilient).

WhatsApp is intentionally NOT supported:
  - WhatsApp Business API requires paid plan
  - Unofficial libs (whatsapp-web.js, yowsup) get accounts banned
  - Same reason Meta API is off-limits for this scheduler

Usage as module:
    from push_notify import fire_push
    fire_push(title="IG carousel ready", body="Caption preview ...", url="https://...")

Usage as CLI (for testing):
    python3 push_notify.py --title "Test" --body "Hello"
    python3 push_notify.py --config   # print current provider config status
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Optional
from urllib import request, error, parse

CONFIG_DIR = Path.home() / ".config" / "digischola"
NTFY_TOPIC_FILE = CONFIG_DIR / "ntfy_topic"
NTFY_SERVER = "https://ntfy.sh"   # public instance; free


# ── Provider config readers ────────────────────────────────────────────────

def _ntfy_topic() -> Optional[str]:
    """Read ntfy topic from env or config file."""
    topic = os.environ.get("NTFY_TOPIC", "").strip()
    if topic:
        return topic
    if NTFY_TOPIC_FILE.exists():
        return NTFY_TOPIC_FILE.read_text(encoding="utf-8").strip() or None
    return None


def _slack_webhook() -> Optional[str]:
    wh = os.environ.get("SLACK_WEBHOOK_URL", "").strip()
    return wh or None


def _telegram_cfg() -> Optional[tuple[str, str]]:
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    if token and chat_id:
        return (token, chat_id)
    return None


def config_status() -> dict:
    return {
        "ntfy":     {"configured": bool(_ntfy_topic()),    "topic":    _ntfy_topic() or "(none)"},
        "slack":    {"configured": bool(_slack_webhook()), "webhook":  "(set)" if _slack_webhook() else "(none)"},
        "telegram": {"configured": bool(_telegram_cfg()),  "chat_id":  (_telegram_cfg() or [None,"(none)"])[1]},
    }


# ── HTTP helper ────────────────────────────────────────────────────────────

def _post(url: str, data: bytes, headers: dict, timeout: int = 5) -> tuple[int, str]:
    req = request.Request(url, data=data, headers=headers, method="POST")
    try:
        with request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except error.HTTPError as e:
        return e.code, (e.read() or b"").decode("utf-8", errors="replace")
    except Exception as e:
        return 0, str(e)


# ── Provider fire ──────────────────────────────────────────────────────────

def _fire_ntfy(title: str, body: str, url: Optional[str]) -> tuple[bool, str]:
    topic = _ntfy_topic()
    if not topic:
        return (False, "not_configured")
    headers = {
        "Title": title.encode("utf-8").decode("latin-1", errors="replace"),
        "Priority": "high",
        "Tags": "bell,mega",
    }
    if url:
        # ntfy supports a Click header so tapping the push opens a URL
        headers["Click"] = url
    status, resp = _post(f"{NTFY_SERVER}/{topic}", body.encode("utf-8"), headers)
    return (200 <= status < 300, f"ntfy http {status}: {resp[:100]}")


def _fire_slack(title: str, body: str, url: Optional[str]) -> tuple[bool, str]:
    webhook = _slack_webhook()
    if not webhook:
        return (False, "not_configured")
    text = f"*{title}*\n{body}"
    if url:
        text += f"\n<{url}|Open composer>"
    payload = json.dumps({"text": text}).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    status, resp = _post(webhook, payload, headers)
    return (200 <= status < 300, f"slack http {status}: {resp[:100]}")


def _fire_telegram(title: str, body: str, url: Optional[str]) -> tuple[bool, str]:
    cfg = _telegram_cfg()
    if not cfg:
        return (False, "not_configured")
    token, chat_id = cfg
    text = f"*{title}*\n{body}"
    if url:
        text += f"\n[Open composer]({url})"
    api_url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = json.dumps({
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True,
    }).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    status, resp = _post(api_url, payload, headers)
    return (200 <= status < 300, f"telegram http {status}: {resp[:100]}")


# ── Public API ─────────────────────────────────────────────────────────────

def fire_push(title: str, body: str, url: Optional[str] = None,
              silent_failure: bool = True) -> dict:
    """Fire to all configured providers. Returns {provider: {sent, reason}}."""
    results = {}
    for name, fn in (("ntfy", _fire_ntfy), ("slack", _fire_slack), ("telegram", _fire_telegram)):
        sent, reason = fn(title, body, url)
        results[name] = {"sent": sent, "reason": reason}
        if not sent and not silent_failure and reason != "not_configured":
            print(f"  push[{name}] FAILED: {reason}", file=sys.stderr)
    return results


# ── CLI ────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--title", default="Scheduler-publisher test")
    ap.add_argument("--body", default="Push test from scheduler-publisher.")
    ap.add_argument("--url", default=None)
    ap.add_argument("--config", action="store_true", help="Show provider config status and exit")
    args = ap.parse_args()

    if args.config:
        for prov, info in config_status().items():
            flag = "✓" if info["configured"] else "✗"
            extra = next((v for k, v in info.items() if k != "configured"), "")
            print(f"  {flag} {prov:10} {extra}")
        return

    results = fire_push(args.title, args.body, args.url, silent_failure=False)
    for prov, r in results.items():
        print(f"  {prov:10} {'✓' if r['sent'] else '✗'}  {r['reason']}")


if __name__ == "__main__":
    main()
