#!/usr/bin/env python3
"""
Weekly Ritual cron entry — fires macOS notification + clipboard-copies the ritual prompt.

Invoked by ~/Library/LaunchAgents/com.digischola.weekly-ritual.plist at:
  Wednesday 09:00 IST → planning ritual (internal label: "sunday")
  Monday    18:00 IST → review ritual   (internal label: "friday")

The actual ritual chain runs in Claude Code when the user pastes the clipboard
prompt. This script's only job: tell the user "it's time" and pre-fill the
trigger phrase so they don't have to remember it.

Naming (see SKILL.md Learnings 2026-04-24):
  - User-facing names: "Wednesday Planning" + "Monday Review".
  - Internal labels kept as neutral legacy keys `sunday`/`friday` so state.json,
    launcher-HTML paths, and prompt-constant names don't have to migrate.
  - CLI `--day` accepts planning|wednesday|sunday interchangeably (all → plan
    ritual) and review|monday|friday interchangeably (all → review ritual).

Idempotency: refuses to fire twice within a 12h window (state file).

Usage:
  python3 weekly_ritual.py --day planning       # fires Wednesday Planning notification
  python3 weekly_ritual.py --day review         # fires Monday Review notification
  python3 weekly_ritual.py --day wednesday      # alias for --day planning
  python3 weekly_ritual.py --day monday         # alias for --day review
  python3 weekly_ritual.py --day sunday         # legacy alias for --day planning
  python3 weekly_ritual.py --day friday         # legacy alias for --day review
  python3 weekly_ritual.py --day auto           # auto-detect from current weekday
  python3 weekly_ritual.py --day planning --once # bypass idempotency check (manual fire)
  python3 weekly_ritual.py --day planning --dry-run
  python3 weekly_ritual.py --status             # print state file contents
"""

from __future__ import annotations

import argparse
import html as html_mod
import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Shared notify helper (click-through). weekly-ritual sits at skills/weekly-ritual/scripts/;
# the helper is at skills/shared-scripts/ — up two levels.
sys.path.insert(
    0, str(Path(__file__).resolve().parents[2] / "shared-scripts"),
)
try:
    from notify import notify as _notify  # type: ignore
except ImportError:
    _notify = None


DEFAULT_BRAND = Path("/Users/digischola/Desktop/Digischola")
STATE_FILENAME = "weekly-ritual.state.json"
LOG_FILENAME = "weekly-ritual.log"
IDEMPOTENCY_HOURS = 12


# ── IST helpers ──────────────────────────────────────────────────────────

def ist() -> timezone:
    return timezone(timedelta(hours=5, minutes=30), name="IST")


def now_ist() -> datetime:
    return datetime.now(ist())


# ── Day-of-week helper ───────────────────────────────────────────────────

WEEKDAY_NAMES = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


def auto_detect_day() -> str | None:
    """Return 'sunday' (plan) or 'friday' (review) if today matches the
    current ritual cadence; else None.

    Cadence shifted 2026-04-22 from Mon→Sun weeks to Thu→Wed weeks:
      - WEDNESDAY 09:00 IST → plan next cycle       (historical: "sunday" ritual)
      - MONDAY    18:00 IST → review previous cycle (historical: "friday" ritual)

    Labels `sunday` / `friday` are preserved internally because the state
    file, SKILL.md chain references, and launcher-html paths all use them.
    Only the weekday mapping changed; semantics are identical.
    """
    today = now_ist().strftime("%A").lower()
    # Current cadence (post-2026-04-22 shift)
    if today == "wednesday":
        return "sunday"   # plan ritual fires on Wednesday
    if today == "monday":
        return "friday"   # review ritual fires on Monday
    # Historical cadence (pre-shift) — kept for manual --day auto triggers on
    # cycle-change weekends only. If you see Sun/Fri firing the wrong ritual
    # after a cycle change, clear the plist + reinstall.
    if today == "sunday":
        return "sunday"
    if today == "friday":
        return "friday"
    return None


# ── State file ───────────────────────────────────────────────────────────

def state_path(brand_folder: Path) -> Path:
    return brand_folder / STATE_FILENAME


def read_state(brand_folder: Path) -> dict:
    p = state_path(brand_folder)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text())
    except Exception:
        return {}


def write_state(brand_folder: Path, state: dict) -> None:
    p = state_path(brand_folder)
    p.write_text(json.dumps(state, indent=2, default=str))


def is_idempotent_skip(brand_folder: Path, day: str) -> tuple[bool, str]:
    """Return (should_skip, reason). True if last fire was within IDEMPOTENCY_HOURS."""
    state = read_state(brand_folder)
    last = state.get(f"last_fired_{day}")
    if not last:
        return False, ""
    try:
        last_dt = datetime.fromisoformat(last)
    except ValueError:
        return False, ""
    if last_dt.tzinfo is None:
        last_dt = last_dt.replace(tzinfo=ist())
    age = now_ist() - last_dt
    if age < timedelta(hours=IDEMPOTENCY_HOURS):
        return True, f"last fired {age.total_seconds() / 3600:.1f}h ago (within {IDEMPOTENCY_HOURS}h window)"
    return False, ""


# ── macOS clipboard + notification ───────────────────────────────────────

def copy_to_clipboard(text: str) -> bool:
    try:
        proc = subprocess.run(["pbcopy"], input=text.encode("utf-8"), check=True, timeout=5)
        return proc.returncode == 0
    except Exception as e:
        print(f"  clipboard error: {e}", file=sys.stderr)
        return False


def send_notification(title: str, subtitle: str, message: str, sound: str = "Glass",
                      open_url: str | None = None) -> bool:
    """Fire a macOS notification — prefers the shared notify helper which
    gives click-to-open banners via terminal-notifier. Falls back to osascript.
    """
    if _notify is not None:
        result = _notify(
            title, message,
            subtitle=subtitle, sound=sound,
            open_url=open_url,
            group="digischola-ritual",
        )
        if result.get("ok"):
            return True
        print(f"  notification helper fallback: {result.get('error')}", file=sys.stderr)

    # Fallback: bare osascript (no click-through)
    def esc(s: str) -> str:
        return s.replace("\\", "\\\\").replace('"', '\\"')
    script = (
        f'display notification "{esc(message)}" '
        f'with title "{esc(title)}" '
        f'subtitle "{esc(subtitle)}" '
        f'sound name "{esc(sound)}"'
    )
    try:
        proc = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=10)
        if proc.returncode != 0:
            print(f"  notification error: {proc.stderr}", file=sys.stderr)
            return False
        return True
    except Exception as e:
        print(f"  notification error: {e}", file=sys.stderr)
        return False


# ── Launcher HTML generator ──────────────────────────────────────────────

def _quick_status(brand_folder: Path) -> dict:
    """Lightweight probe of the brand wiki + queue so the launcher page can
    show useful context without depending on other skills."""
    pending = brand_folder / "brand" / "queue" / "pending-approval"
    published = brand_folder / "brand" / "queue" / "published"
    calendars = brand_folder / "brand" / "calendars"
    ib = brand_folder / "brand" / "idea-bank.json"
    pending_count = len(list(pending.glob("*.md"))) if pending.exists() else 0
    published_count = len(list(published.glob("*.md"))) if published.exists() else 0
    calendars_list = []
    if calendars.exists():
        calendars_list = sorted(p.name for p in calendars.glob("*.md"))[-3:]
    ib_count = "?"
    if ib.exists():
        try:
            data = json.loads(ib.read_text())
            entries = data.get("entries", data) if isinstance(data, dict) else data
            ib_count = str(len(entries)) if isinstance(entries, list) else "?"
        except Exception:
            ib_count = "?"
    return {
        "pending_drafts": pending_count,
        "published_posts": published_count,
        "recent_calendars": calendars_list,
        "idea_bank_entries": ib_count,
    }


def build_launcher_html(day: str, prompt: str, brand_folder: Path,
                        state: dict) -> str:
    """Generate a self-contained launcher HTML page.

    User clicks the cron banner → this page opens in Chrome. Page shows:
    - Ritual prompt in large copy-to-clipboard box
    - One-line reminder of what will happen next
    - Status pulled from state.json + brand/ queue
    """
    status = _quick_status(brand_folder)
    day_title = DAY_DISPLAY.get(day, day.title())
    next_hint = (
        "Claude will: trend-research → peer-tracker → build next week's calendar → "
        "draft + repurpose → visual briefs → apply_calendar to schedule."
        if day == "sunday"
        else "Claude will: collect last week's metrics → weekly_review HIT/ABOVE/BELOW/FLOP → "
             "surface promote/deprecate suggestions across hook-library + voice frameworks."
    )
    last_fired = state.get(f"last_fired_{day}", "never")
    last_completed = state.get(f"last_completed_{day}", "never")
    last_week = state.get("last_calendar_week", "—")

    # Recent calendars (last 3)
    cals_html = ""
    if status["recent_calendars"]:
        items = "".join(
            f'<li>{html_mod.escape(c)}</li>' for c in status["recent_calendars"]
        )
        cals_html = f'<ul class="cal-list">{items}</ul>'
    else:
        cals_html = '<p class="muted">No calendars yet.</p>'

    prompt_esc = html_mod.escape(prompt)
    return f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8" />
<title>Digischola · {day_title} Ritual Launcher</title>
<link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;700&family=Orbitron:wght@700;900&family=Space+Grotesk:wght@500;700&display=swap" rel="stylesheet" />
<style>
 :root {{
   --pr: #3B9EFF; --bg: #0A0F1C; --card: #111827; --border: #1F2937;
   --text: #E5E7EB; --muted: #9CA3AF; --approve: #10B981;
 }}
 * {{ box-sizing: border-box; }}
 html, body {{ margin:0; padding:0; background: var(--bg); color: var(--text);
              font-family: 'Manrope', system-ui; font-size: 16px; }}
 main {{ max-width: 780px; margin: 0 auto; padding: 48px 28px 80px; }}
 h1 {{ font-family: 'Orbitron', sans-serif; font-weight: 900; font-size: 28px;
       margin: 0 0 8px 0; letter-spacing: 1px;
       background: linear-gradient(90deg, var(--pr), #7ec5ff);
       -webkit-background-clip: text; background-clip: text;
       -webkit-text-fill-color: transparent; }}
 .subtitle {{ color: var(--muted); font-family: 'Space Grotesk', sans-serif;
              letter-spacing: 0.1em; text-transform: uppercase; font-size: 12px;
              margin-bottom: 40px; }}
 .card {{ background: var(--card); border: 1px solid var(--border);
          border-radius: 14px; padding: 28px; margin-bottom: 20px; }}
 .card h2 {{ font-family: 'Space Grotesk', sans-serif; font-size: 14px;
             color: var(--muted); text-transform: uppercase;
             letter-spacing: 0.15em; margin: 0 0 16px 0; }}
 .prompt-box {{ font-family: 'SF Mono', Menlo, monospace; font-size: 22px;
               color: var(--pr); background: rgba(59,158,255,0.05);
               border: 1px dashed var(--pr); border-radius: 10px;
               padding: 20px 24px; margin-bottom: 16px;
               word-break: break-word; }}
 button.copy {{ padding: 12px 24px; background: var(--pr); color: white;
                border: none; border-radius: 8px;
                font-family: 'Space Grotesk', sans-serif; font-weight: 700;
                font-size: 15px; cursor: pointer; transition: background 0.15s; }}
 button.copy:hover {{ background: #5eaeff; }}
 button.copy.copied {{ background: var(--approve); }}
 .hint {{ color: var(--muted); font-size: 14px; line-height: 1.6;
          margin-top: 12px; }}
 .status-grid {{ display: grid; grid-template-columns: repeat(2, 1fr);
                 gap: 14px; margin-top: 12px; }}
 .stat {{ padding: 14px 16px; border: 1px solid var(--border);
          border-radius: 10px; }}
 .stat .label {{ color: var(--muted); font-size: 12px;
                 font-family: 'Space Grotesk', sans-serif;
                 text-transform: uppercase; letter-spacing: 0.1em;
                 margin-bottom: 6px; }}
 .stat .val {{ font-size: 22px; font-weight: 700;
               font-family: 'Space Grotesk', sans-serif; }}
 .cal-list {{ margin: 8px 0 0 0; padding-left: 20px; font-size: 14px;
              color: var(--muted); }}
 .muted {{ color: var(--muted); font-size: 14px; }}
 code {{ font-family: 'SF Mono', Menlo, monospace; font-size: 13px;
         background: rgba(255,255,255,0.04); padding: 2px 6px;
         border-radius: 4px; }}
 footer {{ margin-top: 40px; color: var(--muted); font-size: 12px;
           font-family: 'Space Grotesk', sans-serif; }}
</style>
</head><body><main>
  <h1>{day_title.upper()} RITUAL · READY</h1>
  <div class="subtitle">Digischola · {now_ist().strftime("%A, %d %b %Y · %H:%M IST")}</div>

  <div class="card">
    <h2>Step 1 · Paste this into Claude Code</h2>
    <div class="prompt-box" id="prompt">{prompt_esc}</div>
    <button class="copy" id="copyBtn" onclick="copyPrompt()">Copy prompt to clipboard</button>
    <p class="hint">Prompt is already on your clipboard — the cron fired <code>pbcopy</code>.
       Paste (⌘V) into Claude Code to start the {day_title} chain.</p>
  </div>

  <div class="card">
    <h2>What happens next</h2>
    <p>{next_hint}</p>
  </div>

  <div class="card">
    <h2>Current state</h2>
    <div class="status-grid">
      <div class="stat">
        <div class="label">Drafts in pending-approval</div>
        <div class="val">{status['pending_drafts']}</div>
      </div>
      <div class="stat">
        <div class="label">Posts published</div>
        <div class="val">{status['published_posts']}</div>
      </div>
      <div class="stat">
        <div class="label">Idea-bank entries</div>
        <div class="val">{status['idea_bank_entries']}</div>
      </div>
      <div class="stat">
        <div class="label">Last calendar week</div>
        <div class="val" style="font-size:18px">{html_mod.escape(last_week)}</div>
      </div>
    </div>
    <h2 style="margin-top:28px">Recent calendars</h2>
    {cals_html}
  </div>

  <div class="card">
    <h2>Last ritual fire</h2>
    <p class="muted">Last fired: <code>{html_mod.escape(str(last_fired))}</code></p>
    <p class="muted">Last completed: <code>{html_mod.escape(str(last_completed))}</code></p>
  </div>

  <footer>Generated by weekly_ritual.py · cron launcher page.</footer>
</main>
<script>
async function copyPrompt() {{
  const txt = document.getElementById('prompt').textContent.trim();
  try {{
    await navigator.clipboard.writeText(txt);
    const btn = document.getElementById('copyBtn');
    btn.textContent = '✓ Copied — paste into Claude Code';
    btn.classList.add('copied');
    setTimeout(() => {{
      btn.textContent = 'Copy prompt to clipboard';
      btn.classList.remove('copied');
    }}, 2500);
  }} catch (e) {{
    alert('Copy failed — select the prompt text manually: ' + e);
  }}
}}
</script>
</body></html>"""


def write_launcher_html(brand_folder: Path, day: str, prompt: str,
                        state: dict) -> Path:
    """Materialize the launcher HTML at brand/weekly-ritual/launcher-<day>.html
    and return the path. Called right before notification so the banner click
    lands on a fresh page."""
    out_dir = brand_folder / "brand" / "weekly-ritual"
    out_dir.mkdir(parents=True, exist_ok=True)
    html = build_launcher_html(day, prompt, brand_folder, state)
    out = out_dir / f"launcher-{day}.html"
    out.write_text(html, encoding="utf-8")
    return out


# ── Logging ──────────────────────────────────────────────────────────────

def log_line(brand_folder: Path, message: str) -> None:
    log = brand_folder / LOG_FILENAME
    with open(log, "a", encoding="utf-8") as f:
        f.write(f"{now_ist().isoformat()}  {message}\n")


# ── Ritual prompts ───────────────────────────────────────────────────────
#
# User-facing trigger phrases: "run wednesday planning" / "run monday review".
# Constant names kept as SUNDAY_*/FRIDAY_* for internal continuity — renaming
# them would force a state-file migration for zero functional win.

SUNDAY_PROMPT = "run wednesday planning"
FRIDAY_PROMPT = "run monday review"

# Human-readable names for each internal key. Used in notifications + launcher.
DAY_DISPLAY = {
    "sunday": "Wednesday Planning",
    "friday": "Monday Review",
}

SUNDAY_NOTIFICATION = {
    "title": "Wednesday planning ready",
    "subtitle": "Open Claude Code and paste from clipboard",
    "message": f"Prompt copied: '{SUNDAY_PROMPT}'",
}

FRIDAY_NOTIFICATION = {
    "title": "Monday review ready",
    "subtitle": "Open Claude Code and paste from clipboard",
    "message": f"Prompt copied: '{FRIDAY_PROMPT}'",
}


# ── Main ─────────────────────────────────────────────────────────────────

def fire_ritual(brand_folder: Path, day: str, dry_run: bool, force: bool) -> int:
    if day not in ("sunday", "friday"):
        print(f"Unknown day: {day}", file=sys.stderr)
        return 2

    # Idempotency check
    if not force:
        skip, reason = is_idempotent_skip(brand_folder, day)
        if skip:
            log_line(brand_folder, f"{day} skipped: {reason}")
            print(f"Skipped {day} ritual: {reason}")
            return 0

    prompt = SUNDAY_PROMPT if day == "sunday" else FRIDAY_PROMPT
    notif = SUNDAY_NOTIFICATION if day == "sunday" else FRIDAY_NOTIFICATION

    if dry_run:
        display = DAY_DISPLAY.get(day, day.title())
        print(f"[DRY-RUN] would fire {display} (internal key: {day})")
        print(f"  notification: {notif['title']} | {notif['subtitle']} | {notif['message']}")
        print(f"  clipboard: {prompt}")
        return 0

    # 1. Copy prompt to clipboard
    if not copy_to_clipboard(prompt):
        log_line(brand_folder, f"{day} clipboard copy FAILED")
        return 1

    # 2. Generate launcher HTML page (backlog 2026-04-22 item #2 + #6):
    #    click on the banner lands on a Chrome page showing the ritual
    #    prompt + status + what-happens-next — no more dead-end banners.
    state = read_state(brand_folder)
    launcher_path = write_launcher_html(brand_folder, day, prompt, state)

    # 3. Fire notification (click-to-open launcher page)
    launcher_url = f"file://{launcher_path.resolve()}"
    if not send_notification(notif["title"], notif["subtitle"], notif["message"],
                             open_url=launcher_url):
        log_line(brand_folder, f"{day} notification FAILED")
        return 1

    # 4. Update state
    state[f"last_fired_{day}"] = now_ist().isoformat()
    write_state(brand_folder, state)

    display = DAY_DISPLAY.get(day, day.title())
    log_line(brand_folder, f"{day} fired (notification + clipboard '{prompt}' + launcher={launcher_path.name})")
    print(f"✓ {display} fired. Notification displayed; prompt '{prompt}' copied to clipboard.")
    print(f"  Launcher page: {launcher_path}")
    return 0


def show_status(brand_folder: Path) -> int:
    state = read_state(brand_folder)
    print(f"State file: {state_path(brand_folder)}")
    if not state:
        print("  (no state recorded yet)")
        return 0
    for k, v in state.items():
        print(f"  {k}: {v}")
    today_ist = now_ist().strftime("%A").lower()
    print(f"\nToday (IST): {today_ist}")
    auto_day = auto_detect_day()
    if auto_day:
        display = DAY_DISPLAY.get(auto_day, auto_day)
        print(f"  Today is a ritual day → would fire: {display} (internal key: {auto_day})")
    else:
        print(f"  Today is NOT a ritual day (rituals fire Wednesday + Monday; "
              f"legacy Sun/Fri still accepted for one-shot `--day auto` runs)")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--brand-folder", type=Path, default=DEFAULT_BRAND)
    ap.add_argument("--day",
                    choices=["planning", "wednesday", "sunday",
                             "review", "monday", "friday",
                             "auto"],
                    default="auto",
                    help="Which ritual to fire. Plan ritual: planning|wednesday|sunday. "
                         "Review ritual: review|monday|friday. 'auto' detects from "
                         "today's weekday in IST.")
    ap.add_argument("--once", "--force", action="store_true",
                    help="Bypass idempotency check (re-fire even if last fire was <12h ago)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--status", action="store_true",
                    help="Print state file contents and exit")
    args = ap.parse_args()

    # Normalize --day alias to the internal neutral key (kept as legacy labels).
    _DAY_ALIAS = {
        "planning": "sunday",
        "wednesday": "sunday",
        "sunday": "sunday",
        "review": "friday",
        "monday": "friday",
        "friday": "friday",
        "auto": "auto",
    }
    args.day = _DAY_ALIAS[args.day]

    if args.status:
        sys.exit(show_status(args.brand_folder))

    if args.day == "auto":
        detected = auto_detect_day()
        if detected is None:
            log_line(args.brand_folder, f"auto: today is not a ritual day; nothing to fire")
            print(f"Today is not a ritual day (Sunday or Friday). Nothing to fire.")
            sys.exit(0)
        args.day = detected
        print(f"Auto-detected day: {args.day}")

    sys.exit(fire_ritual(args.brand_folder, args.day, args.dry_run, args.once))


if __name__ == "__main__":
    main()
