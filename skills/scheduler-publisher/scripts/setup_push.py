#!/usr/bin/env python3
"""
Interactive wizard to set up push notifications for scheduler-publisher.

Primary: ntfy.sh (free, no account, iOS + Android app is free).
Optional: Slack webhook, Telegram bot. Skips WhatsApp (paid / ban risk).

Usage:
  python3 setup_push.py               # interactive
  python3 setup_push.py --ntfy-random # generate random ntfy topic non-interactively
  python3 setup_push.py --status      # print current provider config
  python3 setup_push.py --test        # fire a test push to all configured providers
"""

from __future__ import annotations

import argparse
import secrets
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import push_notify  # type: ignore


CONFIG_DIR = push_notify.CONFIG_DIR
NTFY_TOPIC_FILE = push_notify.NTFY_TOPIC_FILE


def _ensure_config_dir():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def random_ntfy_topic() -> str:
    """Generate an unguessable ntfy topic. 16 hex chars = 64 bits of entropy."""
    return f"digischola-{secrets.token_hex(8)}"


def setup_ntfy_interactive() -> bool:
    print("\n── ntfy.sh push setup ──────────────────────────────────────\n")
    existing = push_notify._ntfy_topic()
    if existing:
        print(f"Already configured: topic = {existing}")
        ans = input("Replace? [y/N] ").strip().lower()
        if ans != "y":
            return True

    print("""
How ntfy.sh works:
  - Free public service, no account needed.
  - You pick a random unguessable topic name.
  - Install the free 'ntfy' iOS or Android app.
  - In the app, Subscribe → enter the same topic name.
  - scheduler-publisher POSTs to https://ntfy.sh/<your-topic>
  - You get a push notification on your phone with the caption.

  iOS app: https://apps.apple.com/app/ntfy/id1625396347
  Android: https://play.google.com/store/apps/details?id=io.heckel.ntfy

Security: anyone who knows the topic name can push to it. Keep it secret.
A random 16-char hex topic is effectively un-guessable.
""")
    ans = input("Generate a random topic now? [Y/n] ").strip().lower()
    if ans == "n":
        topic = input("Enter your own topic name: ").strip()
        if not topic:
            print("Empty topic, skipping.")
            return False
    else:
        topic = random_ntfy_topic()
        print(f"\n  Generated topic: {topic}")

    _ensure_config_dir()
    NTFY_TOPIC_FILE.write_text(topic + "\n", encoding="utf-8")
    print(f"\n  Saved to {NTFY_TOPIC_FILE}")
    print(f"\n  Now on your phone:")
    print(f"    1. Install the ntfy app (links above)")
    print(f"    2. Tap + → Subscribe to topic")
    print(f"    3. Topic name: {topic}")
    print(f"    4. Leave server as ntfy.sh (default)")
    print(f"    5. Save")
    print(f"\n  Test in 30 sec with:  python3 setup_push.py --test")
    return True


def setup_slack_interactive() -> bool:
    print("\n── Slack push setup (optional) ──────────────────────────────\n")
    if push_notify._slack_webhook():
        print("  Already configured (SLACK_WEBHOOK_URL set).")
        return True
    print("""
How Slack Incoming Webhooks work:
  1. Go to https://api.slack.com/apps → Create New App → From scratch
  2. Pick a workspace you own (or any you can add apps to)
  3. Enable "Incoming Webhooks"
  4. Add New Webhook to Workspace → pick a channel (or create #digischola-posts)
  5. Copy the webhook URL

Then add to your shell profile (~/.zshrc or ~/.bash_profile):
  export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."

LaunchAgent needs this env var too. Edit the plist:
  ~/Library/LaunchAgents/com.digischola.scheduler.plist
  Add inside <dict>:
    <key>EnvironmentVariables</key>
    <dict>
      <key>SLACK_WEBHOOK_URL</key>
      <string>https://hooks.slack.com/services/...</string>
    </dict>
""")
    ans = input("Skip Slack for now? [Y/n] ").strip().lower()
    return ans != "n"


def setup_telegram_interactive() -> bool:
    print("\n── Telegram push setup (optional) ──────────────────────────\n")
    if push_notify._telegram_cfg():
        print("  Already configured.")
        return True
    print("""
How Telegram bot notifications work:
  1. On Telegram, message @BotFather → /newbot → follow prompts
  2. Copy the bot token (looks like 123456:ABC-xyz...)
  3. Start a chat with your new bot (search @YourBotName_bot → Start)
  4. Get your chat_id: open https://api.telegram.org/bot<TOKEN>/getUpdates
     in a browser, send any message to your bot, refresh. Find "chat":{"id":NNN,...}

Then add to your shell profile:
  export TELEGRAM_BOT_TOKEN="123456:ABC..."
  export TELEGRAM_CHAT_ID="NNN"

LaunchAgent needs these env vars too (same plist edit pattern as Slack above).
""")
    ans = input("Skip Telegram for now? [Y/n] ").strip().lower()
    return ans != "n"


def status():
    print("\n── scheduler-publisher push config ──────────────────────────\n")
    for prov, info in push_notify.config_status().items():
        flag = "✓" if info["configured"] else "✗"
        if prov == "ntfy" and info["configured"]:
            print(f"  {flag} ntfy       topic: {info['topic']}")
            print(f"     Push URL: https://ntfy.sh/{info['topic']}")
        elif prov == "slack":
            print(f"  {flag} slack      webhook: {info['webhook']}")
        elif prov == "telegram":
            print(f"  {flag} telegram   chat_id: {info['chat_id']}")
        else:
            print(f"  {flag} {prov}")
    print()


def test():
    print("\n── firing test push ────────────────────────────────────────\n")
    results = push_notify.fire_push(
        title="scheduler-publisher test",
        body="If you see this, push notifications are working. Tap to open composer URL.",
        url="https://x.com/compose/post",
        silent_failure=False,
    )
    for prov, r in results.items():
        print(f"  {prov:10} {'✓' if r['sent'] else '✗'}  {r['reason']}")
    print()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ntfy-random", action="store_true",
                    help="Generate random ntfy topic non-interactively")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--test", action="store_true")
    args = ap.parse_args()

    if args.status:
        status()
        return
    if args.test:
        test()
        return
    if args.ntfy_random:
        topic = random_ntfy_topic()
        _ensure_config_dir()
        NTFY_TOPIC_FILE.write_text(topic + "\n", encoding="utf-8")
        print(f"Generated + saved: {topic}")
        print(f"Config path: {NTFY_TOPIC_FILE}")
        print(f"\nOn your phone: install ntfy app, subscribe to topic '{topic}'.")
        print(f"Test: python3 {Path(__file__).name} --test")
        return

    # Interactive full wizard
    print("╔══════════════════════════════════════════════════════════╗")
    print("║  scheduler-publisher push notification setup             ║")
    print("║  Free-only: ntfy.sh primary + optional Slack + Telegram  ║")
    print("╚══════════════════════════════════════════════════════════╝")
    setup_ntfy_interactive()
    setup_slack_interactive()
    setup_telegram_interactive()
    print("\n── Done ────────────────────────────────────────────────────")
    status()
    print("Next:  python3 setup_push.py --test  (fires a test to all configured providers)")


if __name__ == "__main__":
    main()
