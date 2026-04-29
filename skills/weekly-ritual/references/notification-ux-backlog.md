# Notification UX Backlog

Logged 2026-04-22 by user. Do NOT implement mid-session — batch these at end-of-cycle.

---

## ✅ STATUS: IMPLEMENTED (2026-04-22, same-day)

All 7 items shipped in a single batch. Option C + terminal-notifier landed:

- **Central helper:** `skills/shared-scripts/notify.py`
  - `notify(title, message, *, subtitle, open_url, sound, group, activate, reveal)` — prefers terminal-notifier (click-to-open), falls back to osascript (banner-only) if not installed.
  - `notify_reviewable_artifact(...)` — wraps the "produced-something-reviewable" pattern: finds the draft in pending-approval by entry_id, ensures review_queue.py is running (spawns in background if not), fires click-to-URL with `#draft-<filename>` anchor. Used by render_html_carousel / render_html_mp4 / generate_reel.

- **review_queue.py:** card anchors (`id="draft-<stem>"`) + client-side hash navigation. URLs with `#draft-X` scroll + highlight. If the anchored draft is hidden by the NEEDS_ATTENTION filter, auto-redirects to `?all=1` preserving the hash. Also swapped in the shared helper for its own open/done banners.

- **render_html_carousel.py:** preview.html gone. Notification click lands on the draft card in review_queue.

- **render_html_mp4.py:** added missing notification with same click-to-review-card pattern.

- **generate_reel.py:** replaced inline osascript with notify_reviewable_artifact.

- **apply_calendar.py:** banner click opens the calendar `.md` file in the user's editor.

- **tick.py + publishers/manual.py:** autonomous LinkedIn ship fires `fire_ship_success_notification` (click opens posted_url). Failures fire `fire_failure_notification(..., draft_path=draft)` (click reveals draft in Finder). Overdue manual-channel re-notifications (`fire_overdue_reminder`) also reveal the draft. Token-expiring notification reveals the setup script.

- **push_notify.py:** already click-capable via ntfy / Slack / Telegram URL fields. No change needed — flagged complete.

- **weekly_ritual.py (cron):** generates `brand/_engine/weekly-ritual/launcher-<day>.html` on each fire — Chrome page with the ritual prompt (copy button), what-happens-next, current queue state, last-run timestamps. Banner click opens this page via file:// URL.

- **performance-review weekly_review.py:** adds click-to-open banner pointing at the freshly-written `brand/performance/YYYY-WXX.md`.

**Dependency installed:** `terminal-notifier` at `/opt/homebrew/bin/terminal-notifier` (brew package, MIT, already on machine — helper probes for it at call time).

**Tested end-to-end:** helper smoke-test fired a click-to-open banner (https://example.com) successfully. All patched modules import cleanly.

**Rule is now enforced:** `notify_reviewable_artifact` encapsulates the "land on draft card in review UI" behavior — producer scripts can't forget it.

---

## The core principle

**Every notification must have a clickable action that does the next step.** Informational banners with no click-through are a UX dead-end — user sees the banner, can't remember what command to paste, dismisses it, work gets lost.

## Specific asks (all locked by user on 2026-04-22)

### 1. Review gate notifications (`scheduler-publisher/review_queue.py`)
**Current:** Banner says "N drafts ready for review". Click does nothing. User has to manually navigate to http://127.0.0.1:8765.

**Required:** Click the banner → browser tab with review UI opens. Even better: notification has Approve All / Reject All / Open UI action buttons.

### 2. Weekly-ritual cron notifications (`weekly-ritual/scripts/weekly_ritual.py`)
**Current:** Sun 09:00 + Fri 18:00 fires banner + silently copies `"run sunday ritual"` to clipboard. User has to:
- Remember that clipboard was copied
- Remember to open Claude Code
- Remember to paste

**Required:** Click the banner → opens a page in Chrome with:
- The ritual prompt pre-filled (for copy OR direct paste-to-Claude-Code via URL scheme)
- A one-line reminder of what will happen next
- Status pulled from last run (state.json)

Fallback acceptable: click opens the Claude Code app and drops the prompt into a new chat via deep link (if Claude Code supports a URL scheme).

### 3. Render-complete notifications (`visual-generator/scripts/render_html_carousel.py`, `render_html_mp4.py`)
**Current (post-patch):** Banner + auto-opens preview.html in Chrome. Works, but notification click itself is dead.

**Required:** Click the banner → same preview.html opens in Chrome (dedupe, but click should be the explicit handoff, not just the auto-open).

### 4. Calendar-applied notifications (`scheduler-publisher/apply_calendar.py`)
**Current (post-patch):** Banner says "N posts scheduled". Click does nothing.

**Required:** Click → opens the calendar markdown (`brand/calendars/YYYY-WXX.md`) in editor OR a formatted HTML view of the week.

### 5. Ship / failure notifications (`scheduler-publisher/tick.py`)
**Current:** Banner fires per shipped post / per failure. Click does nothing.

**Required:** Click → opens posted_url in browser for autonomous posts, OR reveals the draft file in Finder for notify-only channels so user can finish the manual 30-sec post.

### 6. Friday performance-review trigger
**Current:** Cron fires Fri 18:00 banner + clipboard. Same dead-end as #2.

**Required:** Click → opens the W-1 performance dashboard (the previous week's metrics) so user has context before they paste the ritual prompt.

## Implementation shortlist (for the batch run)

**Option A — `terminal-notifier` (brew package, MIT):**
- `brew install terminal-notifier`
- Supports `-open <url>`, `-execute <command>`, `-activate <bundle-id>`
- Replace all `osascript display notification` calls with `terminal-notifier -title ... -message ... -open <click-url>`
- Pros: simple, battle-tested, widely used. Cons: external dependency.

**Option B — PyObjC + `NSUserNotification` (or `UNUserNotificationCenter`):**
- Pure Python, no brew dependency.
- Supports action buttons (Approve/Reject/Edit inline from banner).
- Pros: richest UX, no external deps. Cons: macOS-only, more code to write, needs a background daemon for action handling (bounces into the shipped process).

**Option C — Centralized notify helper module:**
- Build a `shared/notify.py` used by all skills.
- Interface: `notify(title, subtitle, body, *, open_url=None, action_buttons=None, sound="Glass")`.
- Internally picks terminal-notifier if present, falls back to osascript banner-only if not.
- Every skill imports this ONE helper instead of inlining osascript strings.

**Recommendation when the batch hits:** Option C + terminal-notifier. Fallback is clean on machines without the brew package. Single-helper means the 5+ scripts in 3 skills don't drift.

## Skills affected (all get the new helper)

- `weekly-ritual/scripts/weekly_ritual.py` (cron notifications)
- `scheduler-publisher/scripts/review_queue.py` (already has notify() — replace)
- `scheduler-publisher/scripts/apply_calendar.py` (patched today — replace)
- `scheduler-publisher/scripts/tick.py` (ship + failure)
- `scheduler-publisher/scripts/push_notify.py` (cross-device already, but local fallback should also be clickable)
- `visual-generator/scripts/render_html_carousel.py` (patched today — replace)
- `visual-generator/scripts/render_html_mp4.py` (needs patching)
- `visual-generator/scripts/generate_reel.py` (needs patching for reel completion)
- `performance-review/scripts/weekly_review.py` (needs patching for review-ready notification)

## 7. Visual preview parity with review_queue (added 2026-04-22)

**Current state:** `render_html_carousel.py` generates a `preview.html` in the output dir showing only images (no caption, no buttons). Opens in Chrome on render-complete. But the scheduler-publisher already has a proper review UI at `review_queue.py` which shows caption + body + images + Approve/Edit/Reject buttons per draft.

**Gap:** Two different preview UIs exist. The lightweight `preview.html` looks fine but doesn't let the user act on what they see (no buttons, no context). User correctly flagged this when reviewing W18 fresh visuals.

**Required:** When a render completes, the auto-opened URL should be the review UI card for that specific draft (e.g., `http://127.0.0.1:8765/#draft-2026-05-02-6118bbc9-instagram-carousel-repurpose`) — with caption + body + buttons — NOT a standalone image-grid preview.html.

**Implementation at batch time:**
1. `render_html_carousel.py` stops generating its own preview.html
2. Instead: if review_queue.py isn't running, start it; then open `http://127.0.0.1:8765/#<draft-basename>` which scrolls to that draft's card
3. Add an anchor/fragment handler in review_queue.py's HTML (each card gets `id="draft-<filename-without-ext>"`)
4. Same approach for Remotion reel renders (`render_html_mp4.py`, `generate_reel.py`)

**Rule locked:** Any time Claude produces a reviewable artifact (draft text, rendered carousel, rendered reel), the notification + auto-open MUST land in a UI where the user can Approve/Edit/Reject that specific artifact inline. No standalone "here's what it looks like" pages that don't support action.

## When to do the batch

End of this Sunday's pipeline cycle OR start of next Sunday (before 09:00 cron fires for the W19 ritual). Not mid-run.
