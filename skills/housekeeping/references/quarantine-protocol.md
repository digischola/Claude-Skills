# Quarantine Protocol

Housekeeping never uses `rm -rf`. Every approved deletion goes to quarantine first. Only the `purge_quarantine.py` step ever permanently removes data from disk, and it only touches entries older than 7 days.

## Structure

```
Desktop/.housekeeping-quarantine/
├── 2026-04-27/
│   ├── manifest.json
│   └── items/
│       ├── Desktop__Digischola__brand___engine___mining__voice-samples.txt
│       ├── Desktop__Digischola__brand___engine___research__trends__2026-W08/
│       └── ...
├── 2026-04-20/
│   └── ...
└── 2026-04-13/  (purged after this run — older than 7 days)
```

- One date-folder per housekeeping run, `YYYY-MM-DD` (IST).
- `manifest.json` per date-folder records every quarantined item: original path, quarantine path, size in bytes, SHA256, classification tier, rule id, timestamp.
- `items/` holds the actual content. File paths are flattened: `/` → `__`. Directories preserve their name and contents.

## Flattening

Path flattening rules:
- Separator: `/` in original → `__` in quarantine filename.
- Leading `/` dropped (it's always under a known root).
- Hidden files/dirs keep their leading `.` (e.g., `.DS_Store` becomes `Desktop__Digischola__brand__.DS_Store`).
- Max filename length 250 bytes; longer names truncated with `…{sha8}` suffix and the full original path preserved in manifest.

## Lifecycle

- **Day 0:** item moved from original path → quarantine. Logged to `housekeeping.log`. Manifest entry written.
- **Day 0-7:** item recoverable via `rollback.py`.
- **Day 7+:** `purge_quarantine.py` permanently removes the whole date-folder. Final deletion logged. After this, item is truly gone.

## Rollback flow

```
python3 scripts/rollback.py --date 2026-04-27
python3 scripts/rollback.py --date 2026-04-27 --pattern "*.csv"
python3 scripts/rollback.py --date 2026-04-27 --path "Desktop/Digischola/brand/_engine/_mining/voice-samples.txt"
python3 scripts/rollback.py --date 2026-04-27 --dry-run
```

- Reads `manifest.json`, matches requested items, moves each back to its original path.
- **Destination-conflict handling:** if a file now exists at the original path (created since quarantine), rollback FAILS LOUDLY for that item — does not overwrite. User must resolve manually (rename one, then rerun).
- Dry-run prints what would be restored without moving anything.

## Purge flow

```
python3 scripts/purge_quarantine.py
python3 scripts/purge_quarantine.py --dry-run
python3 scripts/purge_quarantine.py --keep-days 14   # extend retention for a run
```

- Lists all date-folders under quarantine root.
- Deletes any older than `keep_days` (default 7).
- Logs the permanent deletion with byte total.
- Dry-run prints what would purge without touching disk.

## Invariants

1. **No direct deletion.** `cleanup.py` only *moves*. Only `purge_quarantine.py` ever calls `shutil.rmtree` or `os.remove`, and only on quarantine-subpaths.
2. **Manifest must match disk.** `validate_output.py` cross-checks every manifest entry against the filesystem after a run. If diverged (manual user intervention), it reports the discrepancy but doesn't fix automatically.
3. **PROTECTED paths never enter quarantine.** If scan.py misclassifies a PROTECTED path as deletable, cleanup.py double-checks and refuses the move (defense in depth).
4. **Quarantine root never gets purged wholesale.** Individual date-folders purge. The root `Desktop/.housekeeping-quarantine/` itself persists forever.
5. **Cross-volume moves okay.** `shutil.move` handles cross-volume copy+delete transparently.

## Why 7 days

- Long enough for Mayank to notice something missing (one full weekly cycle plus buffer).
- Short enough that quarantine doesn't become a permanent second copy of everything (defeats the point of cleanup).
- Configurable per run via `--keep-days` on purge_quarantine.
- Extend case-by-case when Mayank is traveling or otherwise offline.

## Emergency stop

If housekeeping is actively running and you need to halt:
- Claude session: interrupt normally. `cleanup.py` processes items serially and logs each action; whatever's logged is done, whatever's not is not.
- LaunchAgent: `launchctl unload ~/Library/LaunchAgents/com.mayank.housekeeping.plist` disables future nudges. Re-enable via `launchctl load`.
