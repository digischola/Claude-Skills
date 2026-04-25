# macOS Notification Permissions

The scheduler uses native macOS notifications for IG/FB/WhatsApp manual-channel posts and for failure alerts. We use `osascript` (built into macOS, no install required) to display notifications.

## First-run grant

The first time `tick.py` fires a notification, macOS will show a one-time popup:

> "Script Editor" wants to display notifications

Click **Allow**. (The popup says "Script Editor" because `osascript` runs under that bundle ID by default. This is normal — Apple's design.)

After that grant, no further popups; notifications appear in the upper-right corner and Notification Center.

## Verify notifications work

```bash
osascript -e 'display notification "Test from Digischola scheduler" with title "Scheduler" subtitle "Setup OK" sound name "Glass"'
```

A notification should appear within 1 second. If not, open **System Settings → Notifications → Script Editor** and toggle "Allow Notifications" to ON.

## Why not `terminal-notifier`?

`terminal-notifier` is a popular brew package for richer notifications (custom action buttons, app icon). We avoided it to keep dependencies minimal — `osascript` ships with macOS and supports everything we need (title, subtitle, sound). If you later want custom action buttons (e.g., "Mark Published" directly from the notification banner), `brew install terminal-notifier` and the publishers will auto-detect it.

## What the notifications look like

**Manual-channel post ready (IG/FB/WhatsApp):**
> **Instagram post ready**
> 4e4eed15 · "188% more Meta sales..."
> Caption copied to clipboard. Asset folder open in Finder.
> _click → opens browser to instagram.com_

**Manual-channel follow-up (24h after initial):**
> **Did you post the IG carousel?**
> 4e4eed15 · scheduled at 09:00 yesterday
> Run: confirm_published.py <file>

**Autonomous post failure:**
> **LinkedIn post FAILED**
> 4e4eed15 · 3 retries exhausted
> Reason: 401 token expired
> Action: re-run setup_channel.py linkedin

**Token expiring soon (proactive):**
> **LinkedIn token expires in 6 days**
> Re-run setup_channel.py linkedin to refresh

## Sound choices

| Event | Sound |
|---|---|
| Manual-channel post ready | `Glass` (gentle ping) |
| Successful autonomous post | _silent_ (no sound; only Notification Center entry) |
| Failure | `Basso` (negative tone) |
| Token-expiring warning | `Funk` (attention) |

Override via `--sound` flag on `tick.py` if needed.
