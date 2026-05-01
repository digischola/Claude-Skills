# feedback-loop

End-of-session protocol for `ideas-in`. Run before closing the skill (per Mandatory Session Close Protocol in CLAUDE.md).

## Steps

1. **Validate idea-bank** — `python3 scripts/validate_idea_bank.py --brand-folder /Users/digischola/Desktop/Digischola`. Fix any CRITICAL failures before delivery.
2. **Count entries by type + status** — print summary so user sees idea-bank growth.
3. **Capture insights** — anything that surprised you this run? Add to SKILL.md Learnings & Rules section. Format: `[YYYY-MM-DD] [mode] Finding → Action`.
4. **Flag downstream connection** — note which entries are ready for `draft-week` to pick up.
5. **Update strategic-context** if any business decisions were made. Track: `Desktop/Digischola/strategic-context.md`.

## What counts as a learning worth saving

- A capture pattern that the type taxonomy didn't cover well.
- A WebSearch query that returned consistent garbage for a pillar (rewrite the query).
- A peer creator who pivoted and should be reclassified or dropped from rotation.
- A dedup heuristic that fired on a real trend (refine the threshold).

## What does NOT belong here

- Per-entry notes (those go in the entry itself).
- Trivial typos or one-off bugs (just fix and move on).
- Anything that should live in the brand wiki (voice rules, pillars).
