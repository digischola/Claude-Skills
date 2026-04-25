---
name: scheduler-publisher
description: "Final-version cron-driven scheduler that ships Digischola posts from brand/queue/pending-approval/ to live social channels at their scheduled_at time. Two posting modes: (1) AUTONOMOUS via the official LinkedIn UGC API — posts ship while the user sleeps. (2) NOTIFICATION-ONLY via macOS notifications + clipboard + Finder reveal for X + Instagram + Facebook + WhatsApp Status — zero Meta API exposure (Meta API flags accounts even for legitimate use); X moved here 2026-04-20 because console.x.com migrated to pay-per-use and dropped the free tier. User does the final 15-30 second post manually for those channels. Runs every 5 min via macOS LaunchAgent. Tokens in macOS Keychain. Asia/Kolkata default time zone. Captures posted_at + platform_url back to draft frontmatter for performance-review. Use when user says: schedule, publish, ship, post now, when does X post, set up LinkedIn API, install scheduler, mark published, ship the week. Do NOT trigger for: drafting copy (use post-writer), planning week slots (use content-calendar), creating visuals (use visual-generator), measuring after publish (use performance-review)."
---

# Scheduler Publisher

Final-version cron scheduler. Ships drafts to live channels. LinkedIn + X autonomous via official APIs; IG + FB + WhatsApp via macOS notification (zero Meta API exposure). Runs every 5 minutes via LaunchAgent.

## Context Loading

**Brand wiki:**
- `Desktop/Digischola/brand/brand-identity.md` — for caption defaults
- `Desktop/Digischola/brand/voice-guide.md` — emoji policy / client-naming
- `Desktop/Digischola/brand/channel-playbook.md` — per-channel posting time defaults

**Skill references:**
- `references/linkedin-api-setup.md` — one-time Developer app + OAuth walkthrough (~15 min)
- `references/x-api-setup.md` — X Developer app + OAuth (~10 min)
- `references/notification-permissions.md` — macOS notification entitlements
- `references/token-storage.md` — Keychain via `keyring` lib
- `references/failure-handling.md` — retry policy, frontmatter status state machine
- `references/launchagent-troubleshooting.md`
- `references/feedback-loop.md`

**Shared context:**
- `.claude/shared-context/analyst-profile.md`

## Inputs

1. **Drafts in `brand/queue/pending-approval/`** with frontmatter: `channel`, `format`, `entry_id`, `scheduled_at` (ISO 8601 with TZ).
2. **Optional `visual_assets_dir:` frontmatter** pointing at rendered media.
3. **Calendar at `brand/calendars/YYYY-WXX.md`** that `apply_calendar.py` reads to write `scheduled_at` onto each draft.

## State Machine (per draft frontmatter)

| `posting_status` | Meaning | Set by |
|---|---|---|
| _(absent)_ | Draft, not scheduled | post-writer / repurpose |
| `scheduled` | `scheduled_at` set, awaiting tick | apply_calendar.py |
| `posting` | Tick is currently publishing (lock held) | tick.py |
| `notified` | Manual channel: notification fired, awaiting user confirmation | publishers/manual.py |
| `posted` | Live; `posted_at` + `platform_url` set | publishers/* on success |
| `failed` | All retries exhausted | tick.py on permanent failure |
| `manual_publish_overdue` | 48h after notification, still not confirmed | tick.py |

Files transition `posted` → moved to `brand/queue/published/`.

## Process

### Step 1: One-time setup

```bash
python3 scripts/setup_channel.py linkedin   # OAuth dev app → Keychain
python3 scripts/setup_channel.py x          # OAuth dev app → Keychain
python3 scripts/install_launchagent.py      # writes ~/Library/LaunchAgents/com.digischola.scheduler.plist + loads
```

### Step 2: Apply calendar to drafts

```bash
python3 scripts/apply_calendar.py --week 2026-W17
```

Reads `brand/calendars/2026-W17.md`, finds matching pending-approval drafts by `entry_id`, writes `scheduled_at` from the calendar slot to each frontmatter. Idempotent — re-runnable.

### Step 3: Tick (autonomous, every 5 min via LaunchAgent)

`tick.py` runs every 5 minutes. Per tick:
1. Acquire `/tmp/digischola-scheduler.lock` (fcntl flock) — prevent concurrent ticks
2. Scan `pending-approval/` for drafts with `scheduled_at <= now(IST)` AND status in {`scheduled`, `failed_retry_due`}
3. For each draft, dispatch to publisher per `channel`:
   - `linkedin` → `publishers/linkedin.py` (autonomous API)
   - `x` → `publishers/x.py` (autonomous API)
   - `instagram` / `facebook` / `whatsapp` → `publishers/manual.py` (notification only)
4. On API success: update frontmatter (`posted_at`, `platform_url`, `posting_status: posted`), move file to `published/`
5. On API failure: increment `posting_attempts`, set retry-after with exponential backoff (5s, 30s, 2m), then permanent fail at attempt 4
6. Log every action to `brand/scheduler.log`; failures additionally to `brand/scheduler-failures.log`

### Step 4: Manual confirm (IG / FB / WhatsApp)

After scheduler fires the macOS notification + clipboard-copy + Finder-reveal at `scheduled_at`:
- User publishes manually in the native app (~30 sec)
- User runs `python3 scripts/confirm_published.py <draft.md>` (or clicks the follow-up notification's action)
- TUI prompts for the live URL → writes `posted_at`, `platform_url`, `posting_status: posted`, moves to `published/`

If 24h passes without confirmation, scheduler re-notifies. At 48h, marks `manual_publish_overdue` and stops bothering (visible in next `ship_week.py`).

### Step 5: Manual triggers (anytime)

```bash
python3 scripts/ship_now.py <draft.md>          # fire immediately, ignore scheduled_at
python3 scripts/ship_week.py                     # show week's schedule + status
python3 scripts/confirm_published.py <draft.md>  # mark a manual-channel post as published
```

## Output Checklist

- [ ] LinkedIn + X tokens in Keychain (via setup_channel.py)
- [ ] LaunchAgent loaded (visible in `launchctl list | grep digischola`)
- [ ] Drafts in pending-approval have valid frontmatter (channel, scheduled_at)
- [ ] After publish: `posted_at`, `platform_url`, `posting_status` all set
- [ ] File moved from pending-approval/ to published/
- [ ] Log entry in scheduler.log

## Anti-patterns

- Do NOT use unofficial Meta libs (Instagrapi, browser automation, Phantombuster). Even with proper Business account, Meta has been increasingly aggressive about flagging API access from automation tools — ban risk is non-zero. Use macOS notifications instead.
- Do NOT post the same draft to multiple channels from one file. Each channel is a separate file (post-writer / repurpose enforce this).
- Do NOT skip the file lock in tick.py — concurrent ticks will double-post.
- Do NOT store tokens in plaintext anywhere. Always Keychain via `keyring`.
- Do NOT bypass `--dry-run` mode when iterating on a publisher implementation.
- Do NOT hardcode time zone — read from `--tz` flag or default to `Asia/Kolkata`.
- Do NOT post if `posting_status == posting` (in flight) or `posted` (already shipped) or `failed` (permanent). Only `scheduled` or `failed_retry_due` proceed.

## Learnings & Rules

<!--
Format: [DATE] [CONTEXT] Finding → Action. Keep under 30 lines. Prune quarterly.
See references/feedback-loop.md for protocol + context tags.
-->
- [2026-04-22] [review_queue.py deadlock — user caught it during first live W18 review] Server used single-threaded `HTTPServer`; Chrome's 4 keep-alive connections deadlocked the event loop, so Approve/Edit/Reject button POSTs hung forever. Fix: swapped to `ThreadingHTTPServer` (import + instantiation, 2 one-char diffs). Button POSTs now respond in <10ms. Also observed `_serve_asset` throws uncaught exception on /assets/* when the referenced file is missing; cosmetic noise in logs but doesn't crash handler thread on ThreadingHTTPServer. Candidate follow-up: wrap `_serve_asset` file read in try/except(BrokenPipeError, FileNotFoundError) and return 404/204 cleanly. Rule locked: any localhost review UI MUST use ThreadingHTTPServer — single-thread + keep-alive + 10+ draft cards = guaranteed deadlock.
- [2026-04-19] [Initial build] Built as final-version skill per Mayank's "no v1 thinking" directive. LinkedIn + X autonomous via official APIs (sanctioned, no ban risk). IG + FB + WhatsApp routed through macOS notification + clipboard + Finder reveal (NOT Meta Business Suite via headless browser, NOT Meta Graph API — Meta has been flagging accounts even for legitimate API use, per Mayank's direct concern). LaunchAgent every 5 min. Time zone Asia/Kolkata. Tokens in macOS Keychain via `keyring` lib. State machine: scheduled → posting → posted | failed | notified → posted | manual_publish_overdue.
- [2026-04-19] [Architecture] LinkedIn carousel posts go through DOCUMENT media type — slide PNGs from visual-generator are stitched into a single PDF (via Pillow) then uploaded as document. X carousel = native multi-image attach (up to 4 per tweet, threading for >4). LinkedIn video upload uses asset-register + PUT-binary flow; X video uses chunked v1.1 media upload then attach to v2 tweet.
- [2026-04-19] [Failure handling] Retry policy: attempt 1 → wait 5s → attempt 2 → wait 30s → attempt 3 → wait 2min → attempt 4 (permanent fail). On permanent fail: write `posting_failed: <reason>` + `posting_status: failed`, fire macOS notification, NEVER auto-move to published/. User must intervene (fix + mark `posting_status: scheduled` to retry from scratch).
- [2026-04-20] [LinkedIn] API version pin in `publishers/linkedin.py` MUST be a currently-active LinkedIn version (YYYYMM). LinkedIn keeps ~12-15 months alive then sunsets older ones. First verify run with pinned `202402` failed: `426 NONEXISTENT_VERSION "Requested version 20240201 is not active"`. Bumped to `202604` (current month). Add a quarterly maintenance check: bump `API_VERSION` constant to current month every 3-6 months. The OAuth flow itself uses unversioned `/v2/userinfo` so OAuth still succeeds even when REST version is sunset — the failure only appears at first publish attempt. Sentinel for the future: if scheduler-failures.log shows HTTP 426 from `api.linkedin.com/rest/*`, bump API_VERSION.
- [2026-04-20] [LinkedIn] Auto-delete on verify works via `DELETE /v2/ugcPosts/{URL_ENCODED_URN}` with the same Bearer token + `X-Restli-Protocol-Version: 2.0.0`. Returns `204 No Content` on success. The verify script now URL-encodes the URN extracted from the post URL and deletes after a 3-sec delay. Confirmed end-to-end on Mayank's account 2026-04-20: post `urn:li:share:7451776658753093632` posted then deleted (204) with no feed leakage observed.
- [2026-04-20] [X] X API migrated to console.x.com pay-per-use. The old free tier (1,500 posts/month via developer.x.com) is sunset — `developer.x.com/en/portal/dashboard` redirects to `console.x.com`. New accounts start with $0 credits + "Auto Recharge unavailable" until a payment method is added. Even with the free starter credits some accounts get, posting reliably requires funded credits. Per Mayank's free-tools-only directive, X moved from AUTONOMOUS to NOTIFICATION-ONLY (same as IG/FB/WhatsApp). `tick.py` publisher_map: `"x"` → `manual_pub.publish_draft`. `publishers/x.py` is dormant in repo for the day X re-introduces free posting OR Mayank funds credits — flip back is one line. `publishers/manual.py` extended with X composer URL `https://x.com/compose/post` and notification copy. `setup_channel.py x` is deprecated (still works, but stores tokens that the scheduler no longer reads).
- [2026-04-20] [X console form-fill] Attempted automated form-fill via Claude in Chrome MCP on the X dev account-creation form (console.x.com/onboarding). Two friction points: (1) React controlled inputs ignore raw `.value` sets — needed `nativeInputValueSetter` + dispatched 'input' event to make Submit enable. (2) Even after Submit was enabled and clicked, X server returned "Failed to create account" — likely bot-detection triggered by the visible "Claude started debugging this browser" banner. Mayank completed the onboarding manually after that. Lesson: dev-portal forms with strict bot detection (X, Stripe, etc.) need manual user submission; MCP form-fill is fine for low-friction forms (LinkedIn dev portal worked end-to-end via terminal-based OAuth, no MCP needed).
- [2026-04-20] [apply_calendar schema] Caught during first live Sunday ritual test. Two bugs. **Bug 1**: parse_calendar's SLOT_RE only matched the legacy `- 09:00 linkedin entry_id` line format, but content-calendar actually writes a pipe-table with columns `| Mon | date | channel | format | pillar | entry_id | ...`. Fixed by adding a table-row parser path that triggers when `line.startswith("|") and line.count("|") >= 6`, with per-channel default posting times (LI 09:00, X 11:00, IG 18:00, FB 18:30, WA 20:00 IST). **Bug 2**: find_draft fallback `channel in name_lower` was too permissive — a draft named `...-linkedin-text-post.md` matched channel "x" because "x" is a substring of "text". Fixed by splitting filename on dashes/underscores/dots and requiring `channel in segments` for a match. Symptom: Wed x slot wrote its scheduled_at onto the Wed LI file, overwriting LI's 09:00 with 11:00. Both bugs now covered by the retest: 11/11 slots route to correct files. Add a cross-skill eval: build a calendar with LI + X same-entry-id pair, apply_calendar, verify each file gets its own scheduled_at.
- [2026-04-20] [Review UI] Mayank flagged that reviewing drafts in .md files is manually impossible. Built `scripts/review_queue.py` — local HTTP server at localhost:8765 serving a dark-mode card-per-draft UI with Approve / Edit (opens in VS Code) / Reject buttons that write `posting_status: approved|rejected|edit_requested` to frontmatter over AJAX. Fires ONE batch macOS notification at server start ("N drafts ready for review"). Extended for media: static asset endpoint at `/assets/<rel-path>` with HTTP 206 byte-range for video seek, detects `brand/queue/assets/<entry_id>*/` auto-populating inline image strips + `<video controls>` embeds per card. Click image → lightbox. Wired into weekly-ritual Sunday Step 6.5 (between visual briefs and apply_calendar). First live use 2026-04-20: reviewed 18 drafts (11 W18 + 7 leftover) in ~3 minutes; 17 approved, 1 edit_requested. Replaces the "open 11 markdown files and read them" pain permanently.
- [2026-04-20] [Push notifications] Mayank flagged that macOS notification is insufficient when away from Mac. Built `scripts/push_notify.py` (fan-out to ntfy.sh + Slack webhook + Telegram bot) + `scripts/setup_push.py` (interactive wizard; `--ntfy-random` generates an unguessable topic). ntfy.sh is the primary: free public service, no account, free iOS + Android apps. Config lives at `~/.config/digischola/ntfy_topic`. Wired into `publishers/manual.py` alongside the existing macOS notification. Skipped WhatsApp intentionally: WhatsApp Business API requires paid plan; unofficial libs (whatsapp-web.js) get accounts banned. First live test 2026-04-20: push HTTP 200 delivered to topic `digischola-13346f0834741dd3` (message id Pd4NofnKLNfY).
- [2026-04-20] [Assisted publishing] Mayank asked if Chrome can be driven automatically to paste + upload when he misses a notification. Answer: **no for autonomous cron-triggered browser automation** (same ban risk as Meta API — platforms flag headless/automated sessions). Built `scripts/assist_publish.py` for the SAFE on-demand path: when Mayank is in a Claude session, Claude runs `assist_publish.py list --json`, gets all overdue manual posts with composer URLs + absolute asset paths + captions, then uses Claude-in-Chrome MCP tools to drive his logged-in browser step-by-step (navigate, fill, file_upload). User watches and clicks the final Post/Share button — Claude never submits. Platforms see a human session with a visible extension, not a bot. Skips LinkedIn (UGC API handles it). First list output 2026-04-20: 10 overdue (6 X + 2 IG + 1 FB + 1 X from leftover).
- [2026-04-20] [Notification click-target] `osascript display notification` makes notifications appear to come from Script Editor (the osascript "sender"). Clicking the notification opens Script Editor. Fix: installed `terminal-notifier` via Homebrew + updated `send_notification()` to prefer terminal-notifier when the binary exists at `/opt/homebrew/bin/terminal-notifier`, using `-sender com.apple.finder` for a Finder icon + `-open <url>` so click = open composer URL. Falls back to osascript if terminal-notifier is missing. Verified 2026-04-20: IG carousel notification now opens instagram.com on click instead of Script Editor.
- [2026-04-20] [Finder activation] `open -R <path>` reveals the folder but doesn't activate Finder, so the window ends up buried behind Chrome. Fix: follow `open -R` with `osascript -e 'tell application "Finder" to activate'`. Verified Finder now comes to front with slides visible.
- [2026-04-20] [URL-intent composer pre-fill] Mayank flagged that clicking notification opens composer empty (text in clipboard requires manual Cmd+V). Built `composer_url_for(channel, caption)` in `manual.py`: for X uses `https://x.com/intent/post?text=<urlencoded>` which pre-fills caption in the composer; for WhatsApp uses `https://wa.me/?text=<urlencoded>`. IG + FB intentionally use static URL — Instagram blocks URL-based caption / image pre-fill for security, Facebook's sharer.php is share-with-quote not post composer. Verified 2026-04-20 on live X intent URL: paragraphs preserved, caption appears in composer ready to click Post.
- [2026-04-20] [X contenteditable pitfall] Attempted to paste caption into X's composer via `form_input` — failed because X uses a React/Draft.js contenteditable div, not `<input>`/`<textarea>`. `document.execCommand('insertText', false, text)` with `\n\n` separators dropped all but the last paragraph (Draft.js block-structure issue). Workaround: use URL-intent URL (`x.com/intent/post?text=`) for simple caption injection; reserve Chrome MCP `javascript_tool` for when asset upload + caption together are needed via `assist_publish.py`.
- [2026-04-20] [Cron interval] Changed scheduler LaunchAgent from `StartInterval: 300` (every 5 min) to `StartCalendarInterval` firing at `:00` and `:30` of every hour. Reason: Mayank flagged 5 min was too frequent for the actual cadence (posts fire at :00 times — 09:00, 11:00, 18:00 IST — so 5 min polling wastes 95% of ticks). New interval = max 30 min delay from scheduled_at to actual post, and ticks fire at exact clock times (cleaner logs, deterministic). Confirmed 2026-04-20: reloaded + tick on load scanned 0 due drafts in 60ms, next fires at 09:00 + 09:30. Auto-start behavior unchanged: on laptop reboot + login, RunAtLoad=true fires tick immediately, then StartCalendarInterval resumes normal schedule. Caveat: Mac must be awake at scheduled_at (existing tradeoff documented).
- [2026-04-20] [Post packet HTML] Mayank flagged the final gap: even after clicking the notification and reaching the composer, he couldn't locate the image/video files for that specific post. Built `scripts/post_packet.py`: at scheduled_at, renders a single dark-mode HTML page per draft showing (1) caption with one-click Copy button (also auto-copies on page load) + "Open composer" link with URL-intent pre-fill, (2) numbered channel-specific "How to post" instructions, (3) live thumbnail grid of all associated image/video assets (from `brand/queue/assets/<entry_id>*/`), each with Download button + Copy-path button + absolute file path displayed, (4) asset folder path + Reveal-in-Finder. Opens in default browser automatically via `subprocess.run(["open", ...])`. Wired into `publishers/manual.py:publish_draft` so it auto-opens alongside notification + clipboard + Finder + composer. Verified 2026-04-20 end-to-end on IG carousel draft `f80273f7`: 8 slide thumbnails rendered correctly, caption auto-copied, instructions shown. Closes the "where are the files" gap permanently.
- [2026-04-22] [Notification-UX batch] All scheduler-publisher notifications now have click-to-action via `shared-scripts/notify.py`. **review_queue.py:** each draft card gets `id="draft-<filename-stem>"`; URLs with `#draft-X` deep-link, highlight, and auto-flip `?all=1` if the target is filtered by NEEDS_ATTENTION. Also swapped inline osascript out of `notify()`. **apply_calendar.py:** banner click opens the calendar `.md` file in the editor. **tick.py:** autonomous ship now fires `fire_ship_success_notification(channel, entry_id, posted_url)` (click opens the live post URL). Failures pass `draft_path=draft` to `fire_failure_notification`. Overdue reminders and token-expiring banners also reveal the relevant file in Finder. All new helpers live in `publishers/manual.py`. The cross-skill contract (any producer script calling `notify_reviewable_artifact` in shared-scripts auto-spawns review_queue on port 8765 and deep-links to the draft card) means visual-generator + other skills can't forget the click-to-review handoff.
- [2026-04-22] [Downstream dependency — posted_url is load-bearing for performance-review] performance-review's new Windsor-native flow (`pull_performance_windsor.py` built same day) matches Windsor rows → published drafts by the draft's `posted_url` field (primary) with timestamp-nearest-neighbor as fallback. That field is written by **THIS** skill: `fio.mark_posted(draft, result.url, via="api")` for autonomous LinkedIn ships, and `confirm_published.py` for manual-channel posts after user pastes the live URL. Rule: any new autonomous publisher added to `publishers/` must call `mark_posted` with the live URL as the second arg, and any new manual-channel post type must have a confirm-step that captures the URL. Missing posted_url → performance-review falls back to ±2h timestamp matching (works but fuzzy). Pin: don't skip URL capture even "temporarily" — it breaks Windsor attribution on that post forever, since Windsor rows don't include Digischola entry_ids.
- [2026-04-23] [First live autonomous ship — user missed the banner, lid-closed] At 09:27 IST on Thu 04-23 the first autonomous LinkedIn post shipped successfully to `https://www.linkedin.com/feed/update/urn:li:share:7452928616910336000`. scheduler.log shows: "scanned: 1 due drafts → ✓ 6118bbc9 → linkedin → <url> → tick end: posted=1". Draft moved to `queue/published/`. But user asked "didn't receive any notification" — laptop lid was closed. Root cause: Mac was in Power Nap (LaunchAgent fires + ships post during intermittent wake) but no active display session → terminal-notifier banner went to Notification Center history with no visible pop-up. User opened lid ~2h later, banner was already stacked/expired in Notification Center. **Rule locked:** local macOS banners are unreliable when the user isn't in front of the Mac; every meaningful ship/failure/overdue/token-expiring notification must ALSO push to phone. Fix shipped same session: added `_push_to_phone()` helper in `publishers/manual.py` + wired it into `fire_ship_success_notification`, `fire_failure_notification`, `fire_overdue_reminder`, `fire_token_expiring_notification`. `fire_post_ready_notification` already had push fan-out (wired 2026-04-20). Push goes via push_notify.fire_push() → ntfy.sh (topic `digischola-13346f0834741dd3`) + Slack + Telegram — silent-failure so a missing provider config doesn't block the local banner. Push is strictly additive, not a replacement: local banner still fires, phone gets a second signal. Retroactive smoke-test fired: both banner + ntfy push delivered for the 09:27 ship.
- [2026-04-25] [StartInterval=900 deployed — fixes lid-closed missed-slot loss permanently] User opened Mac lid at 11:20 IST Sat 04-25 to find: (1) LinkedIn post baf468bc still `posting_status: scheduled` (should have shipped at 09:00 IST), (2) X tweet baf468bc-repurpose still `posting_status: scheduled` (should have notified at 11:00 IST). scheduler.log: zero ticks between 04-23 12:00 IST and 04-25 11:21 IST. Root cause: deployed plist `~/Library/LaunchAgents/com.digischola.scheduler.plist` was using `StartCalendarInterval` at :00 / :30 of every hour — a wall-clock trigger that doesn't replay on wake. Fix: ran `python3 install_launchagent.py --force --interval 900` to redeploy plist with `StartInterval: 900` (15-min relative-seconds timer). Behavior change: instead of "fire at this clock time", launchd now fires "every 900s since last fire" — which means on wake, if 900s+ have elapsed since last tick, launchd fires immediately. Max latency between scheduled_at and ship is now ~15 min regardless of sleep state. The PLIST_TEMPLATE in install_launchagent.py was already using StartInterval (lines 46-47); the deployed plist had drifted to StartCalendarInterval via a manual edit in a prior session — running `install_launchagent.py --force` restored intent. Catch-up tick at 11:21:35 IST shipped both due posts: LinkedIn `urn:li:share:7453682107194839040` (autonomous) + X notification fired (manual paste). **Rule locked:** never deploy `StartCalendarInterval` for cron-driven publishers — `StartInterval` is the correct default because (a) wake-replay is automatic, (b) max-latency is bounded by interval (15 min), (c) cleaner reasoning about "did we miss a slot." `StartCalendarInterval` is only appropriate for nudge-style notifications (weekly-ritual, housekeeping) where missing a single weekly slot isn't catastrophic. `install_launchagent.py --force --interval 900` is the canonical install command going forward; never edit the deployed plist manually.
- [2026-04-24] [post_packet asset bleed — text-only packets displayed sibling repurpose's carousel slides] User opened `/tmp/post-packet-6118bbc9-x.html` for today's 11:00 IST X thread and saw a 9-slide image grid ("9 assets (9 images)") even though X threads are text-only and he had never generated images for that post. Root cause: `scan_assets(brand_folder, entry_id)` in `scripts/post_packet.py` collected every file under `brand/queue/assets/<entry_id>/` with no format filter. Entry `6118bbc9` is repurposed across (a) Mon LI text-post, (b) Fri X thread, (c) Tue IG carousel — all three share the same entry_id directory, and the IG carousel's 9 slides bled into the two text-only packets. Fix: added `TEXT_ONLY_FORMATS` constant (keyed by `(channel, fmt)` pairs — x:tweet/single/thread, linkedin:text-post/text, facebook:text-post/text, whatsapp:text/text-post) + `is_text_only()` helper + updated `scan_assets()` signature to `scan_assets(brand_folder, entry_id, channel, fmt)` with an early return `[]` when the pair is in the set. Call site at `render_packet_html` line 113 updated to pass channel + fmt through. Verified: regenerated 6118bbc9 X thread packet — 0 asset cards, renders "No assets for this post. Caption-only." instead of 9 slides. Size dropped 17772 → 8543 bytes. 1e2b7840 X single packet was already clean (no assets in its entry folder) — confirming the fix is a surgical gate, not a broader behavioral change. **Rule:** anytime an entry_id is shared across text + media formats via repurpose, text-formats must not pick up the media siblings' assets. The format-pair whitelist is the contract; add new channels/formats to `TEXT_ONLY_FORMATS` as they land (e.g. future `threads:text` if Meta Threads is added). Cross-skill: repurpose.py already writes separate drafts with correct format frontmatter — this fix is downstream of that contract, no repurpose changes needed.
