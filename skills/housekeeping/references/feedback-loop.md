# Feedback Loop — Housekeeping

After every housekeeping run, capture what was learned. Append entries to SKILL.md "Learnings & Rules" section. Keep under 30 lines total — prune quarterly.

## Entry format

```
[YYYY-MM-DD] [tier:RULE_ID] One-sentence finding → One-sentence action
```

## When to write an entry

Write an entry when any of these happened during the run:

1. **Misfire:** a file was flagged but user said Keep. Why? Was the rule too aggressive? Missing exemption?
2. **Near-miss:** a PROTECTED file was almost flagged (scan.py caught it only because of double-check). Rule ordering or path-pattern issue.
3. **New bloat pattern discovered:** something large and rebuildable showed up that no rule covers. Add rule.
4. **Promotion candidate:** a LIKELY-BLOAT rule has fired 8+ times across 3 months with 100% "Quarantine all" approval. Promote to AUTO-BLOAT.
5. **Demotion candidate:** an AUTO-BLOAT rule got "Keep" responses 2+ times consecutively. Demote to LIKELY-BLOAT and investigate.
6. **Quarantine bloat:** quarantine itself is >5GB. Tighten keep-days or review what's in there.
7. **Schedule drift:** LaunchAgent didn't fire at expected time. OS was asleep, plist malformed, etc.

## Examples

```
[2026-04-27] [LIKELY:old-published-drafts] 180-day threshold flagged 12 drafts user wanted to keep for brand-storyboard reference → Promoted threshold to 365 days.
[2026-05-04] [AUTO:ds_store] 33 .DS_Store entries auto-quarantined and re-created within 3 hours by Finder → Rule kept; added note that high re-creation rate is expected.
[2026-05-11] [AMBIGUOUS:orphan-client] "Shreyas Retreat" folder AMBIGUOUS — checking strategic-context confirmed this is a legit client in pre-sales → Added "Shreyas Retreat" to known-client set in cleanup-rules.md and scan.py.
[2026-06-01] [QUARANTINE] Quarantine at 4.8 GB after 8 weekly runs, mostly remotion-studio intermediates → Tightened AUTO-BLOAT for remotion intermediates from 30d to 14d.
```

## What NOT to write

- Generic observations ("cleaned up successfully").
- Per-file notes (belong in housekeeping.log).
- Repeats of rules already documented in cleanup-rules.md (put there instead).

## Rule promotion workflow

When promoting LIKELY → AUTO:
1. Edit `references/cleanup-rules.md` — move rule between sections.
2. Edit `scripts/scan.py` — update `CATEGORY` assignment for that pattern.
3. Write learning entry with rationale.
4. Re-run `evals/evals.json` after change to confirm fixture behavior.

When demoting AUTO → LIKELY:
1. Same three files.
2. In the learning entry, note the two specific cases where user said "Keep".

## Session-close steps (copy-paste template)

```
## Learnings & Rules
- [YYYY-MM-DD] [tier:RULE_ID] Finding → Action
```

## Protocol Supremacy note

Per CLAUDE.md Skill Protocol Supremacy: if during a run a situation occurs that the skill doesn't handle (ambiguous new folder type, rule conflict, quarantine full, etc.) — STOP the run, log the gap, patch the skill, rerun. Never paper over with ad-hoc judgment during a cleanup that's actively deleting things.
