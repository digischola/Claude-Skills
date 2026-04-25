# LaunchAgent Troubleshooting

The scheduler runs as a macOS LaunchAgent at `~/Library/LaunchAgents/com.digischola.scheduler.plist`. Here's how to verify, debug, stop, and restart it.

## Verify it's loaded

```bash
launchctl list | grep digischola
```

Expected output (single line):
```
12345  0  com.digischola.scheduler
```

- First column: PID (process ID) — `-` if not currently running, a number if mid-tick
- Second column: last exit code — `0` for success
- Third column: label

If no output, the agent isn't loaded. Re-run:
```bash
python3 scripts/install_launchagent.py
```

## See recent ticks

```bash
tail -50 /Users/digischola/Desktop/Digischola/brand/scheduler.log
```

You should see a new entry every 5 minutes. If gaps > 6 min, the agent isn't ticking.

## See macOS-level errors

```bash
log show --last 1h --predicate 'subsystem == "com.digischola.scheduler" OR (process == "python3" AND eventMessage CONTAINS "tick.py")' --info --style compact
```

This pulls everything macOS logged about our scheduler — agent start/stop, exit codes, stdout/stderr from `tick.py`.

## Stop the scheduler temporarily

```bash
launchctl unload ~/Library/LaunchAgents/com.digischola.scheduler.plist
```

Verify it's gone:
```bash
launchctl list | grep digischola   # should be empty
```

## Resume

```bash
launchctl load ~/Library/LaunchAgents/com.digischola.scheduler.plist
```

## Permanent uninstall

```bash
launchctl unload ~/Library/LaunchAgents/com.digischola.scheduler.plist
rm ~/Library/LaunchAgents/com.digischola.scheduler.plist
# Optionally also nuke tokens:
python3 scripts/setup_channel.py --reset all
```

## Common issues

### "Operation not permitted" when loading
macOS Big Sur+ requires Full Disk Access for LaunchAgents to read most paths. Open **System Settings → Privacy & Security → Full Disk Access** and add Terminal.app (or whichever shell you ran `install_launchagent.py` from).

### Agent loads but never ticks
Check the plist's `ProgramArguments` — first element must be the absolute path to `python3`. On Apple Silicon Macs with Homebrew Python, this is typically `/opt/homebrew/bin/python3`. Check:
```bash
which python3
```
If different from what's in the plist, regenerate:
```bash
python3 scripts/install_launchagent.py --force
```

### Agent ticks but logs say "No drafts due"
Drafts must have `scheduled_at` in the past AND `posting_status: scheduled`. Check a draft:
```bash
head -20 /Users/digischola/Desktop/Digischola/brand/queue/pending-approval/<file>.md
```
If `scheduled_at` is missing, run `apply_calendar.py`. If `posting_status` is set to anything other than `scheduled` (e.g., still empty after calendar apply), inspect — likely a bug in the calendar parser.

### "tick.py: command not found" in logs
The plist's `WorkingDirectory` should be the brand folder, but the script path must be absolute to the skill. Re-run `install_launchagent.py --force` to regenerate with absolute paths.

### Mac asleep / closed lid
LaunchAgents fire only when the user is logged in AND the system is awake. If your lid is closed, agent sleeps with the system. To get true 24/7 scheduling, run on a different always-on machine OR add a Cloudflare Worker (free tier) to act as the cron — see `references/cloudflare-fallback.md` (future).

## Manual tick (for debugging)

You can fire a tick by hand without waiting for the LaunchAgent:
```bash
python3 /Users/digischola/Desktop/Claude\ Skills/skills/scheduler-publisher/scripts/tick.py --once
```

Or with extra verbosity:
```bash
python3 .../tick.py --once --verbose --dry-run
```

`--dry-run` shows what WOULD happen without actually posting or moving files.
