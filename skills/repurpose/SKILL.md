---
name: repurpose
description: "Takes an existing drafted or published post from one channel and adapts it for other channels while preserving the source hook verbatim. LinkedIn text-post → X thread, Instagram carousel, Reel script, WhatsApp Status, Facebook; X thread → LinkedIn; and 6 other source→target pairs. Saves variants to Desktop/Digischola/brand/queue/pending-approval/ with repurpose_source frontmatter. Validates each variant against post-writer's hard rules (no em dashes, hype, bait, char caps). Updates source draft frontmatter with repurposed_into list. Use when user says: repurpose, adapt this for X, turn this LinkedIn post into a thread, make an IG carousel from this, variants for other channels, multi-channel, cross-post. Do NOT trigger for: raw ideas from idea-bank (use post-writer instead), fresh drafting (use post-writer), weekly planning (use content-calendar), capture new moment (use work-capture), publishing (future scheduler-publisher)."
---

# Repurpose

Take a drafted or already-published post on one channel and adapt it to fit other channels. The hook is preserved. Only the wrapper (structure, length, format) changes.

## Context Loading

Read before starting:

**Brand wiki (required):**
- `Desktop/Digischola/brand/pillars.md` — Status MUST be LOCKED
- `Desktop/Digischola/brand/voice-guide.md` — registers per channel + Conservative client-naming + Restrained emoji policy
- `Desktop/Digischola/brand/brand-identity.md` — visual rules for carousels and Reels

**Skill references (this skill):**
- `references/transformation-recipes.md` — the 9 source→target recipes
- `references/hook-preservation.md` — when to keep vs. adapt the hook

**Upstream skill references (post-writer):**
- `post-writer/references/platform-specs.md` — channel char caps + structure templates
- `post-writer/references/voice-frameworks.md` — voice register per channel

**Shared context:**
- `.claude/shared-context/analyst-profile.md`

## Inputs

1. **Source file path** (required) — a markdown file in `Desktop/Digischola/brand/queue/pending-approval/` with YAML frontmatter (channel, format, entry_id, pillar).
2. **Target channels** (optional; default: all channels NOT matching source). Comma-separated list e.g. `x-thread,instagram-carousel,whatsapp-status`.
3. **Hook mode** (optional; default: `preserve`). Alternatives: `adapted` with reason, or `new` to generate fresh hooks per target (exits this skill's scope; redirects to post-writer).

## Process

### Step 1: Inspect source

Run `scripts/repurpose_post.py inspect <source_file>`. Returns JSON: source channel, format, pillar, entry_id, body char count, extracted hook, recommended default targets, channel budgets.

If source file does not exist OR lacks YAML frontmatter OR lacks `entry_id` / `pillar` fields: abort with a clear message.

### Step 2: Determine targets

If user specified targets, use those. Else use `default_targets` from inspect.

**Phase gate:** if target includes `whatsapp-status` or `whatsapp-channel` AND `channel-playbook.md` shows WA still in "dark" Phase 1, warn but proceed only if user confirms. Default Phase 1 (weeks 1-6): skip WA targets silently unless explicitly requested.

### Step 3: Apply transformation recipe per target

For each target channel, look up the recipe in `references/transformation-recipes.md` (e.g., `LinkedIn text-post → X thread`). Draft the variant following:

1. **Structure:** the recipe's structural shape (e.g., X thread = 5-7 tweets, IG carousel = 7-10 slides).
2. **Length:** per-channel char budget from platform-specs.md.
3. **Preservation:** source hook's core claim, specific numbers, client descriptors, tool names per `hook-preservation.md`.
4. **Adaptation:** channel-native formatting only (line breaks, slide structure, caption hook).
5. **Policy compliance:** em dash ban, hype word ban, engagement bait ban, Conservative client naming, Restrained emoji policy (LI/X/FB = 0 emojis; IG/WA = functional only).

### Step 4: Save each variant

For each drafted variant, write the body to a temp file, then run:

```
python3 scripts/repurpose_post.py save <source_file> \
  --target <channel-format> \
  --body-file <temp-variant.md> \
  --hook-preservation <preserved|adapted: reason>
```

Script writes the variant to `queue/pending-approval/` with frontmatter:

```yaml
---
channel: <target-channel>
format: <target-format>
entry_id: <inherited from source>
pillar: <inherited from source>
repurpose_source: <source filename>
hook_preservation: preserved | adapted (reason)
validator_status: pending
---
```

Variant filename format: `YYYY-MM-DD-<entry_id_8>-<target>-<format>-repurpose.md`

### Step 5: Link + validate

After all variants are saved, run:

```
python3 scripts/repurpose_post.py link <source_file> \
  --variants <v1> <v2> <v3> ...
```

Script:
1. Adds `repurposed_into: [list of variant filenames]` + `repurposed_at: <ISO timestamp>` to source frontmatter.
2. Runs `post-writer/scripts/validate_post.py` on each variant.
3. Reports CLEAN / WARN / CRITICAL per variant.

### Step 6: Handle validator failures

If any variant exits CRITICAL (em dash, hype word, engagement bait, hard char cap):
- Identify the specific violation from validator output
- Rewrite that section of the variant (Claude judgment)
- Save the revised version (overwrites via `save` subcommand)
- Re-run link to re-validate

Do NOT ship variants that fail CRITICAL.

### Step 7: Feedback loop

Read `references/feedback-loop.md`. Add dated learning if:
- User rewrote a variant heavily (recipe needs tightening)
- User reverted a hook adaptation (should have preserved)
- A target channel pair consistently produces CRITICAL failures
- Conservative naming edge case surfaced

## Output Checklist

- [ ] Source file exists with valid frontmatter (channel, format, entry_id, pillar)
- [ ] Target channel list resolved (default or user-specified)
- [ ] Phase gate enforced for WA targets (Phase 1 skip unless override)
- [ ] Each variant drafted using the recipe from transformation-recipes.md
- [ ] Source hook preserved in every variant (or adaptation logged with reason)
- [ ] Each variant saved to `queue/pending-approval/` via `save` subcommand
- [ ] Source frontmatter updated with `repurposed_into: [...]` + `repurposed_at: <time>`
- [ ] Each variant passes post-writer's validate_post.py (exit 0 or 1 per variant, never 2)

## Anti-patterns

- Do NOT generate a new hook unless `--hook-mode new` was explicitly passed. Use post-writer for fresh hooks.
- Do NOT copy-paste the source body across channels. Every variant applies the target's structural recipe.
- Do NOT skip the validator. If a variant fails, rewrite and re-validate.
- Do NOT ship variants that violate Conservative client naming (anonymize anywhere the source was case-study-permitted but the variant goes deeper into operational details).
- Do NOT target channels in a phase they should not be active in (WA in Phase 1 = skip).
- Do NOT write variants outside `queue/pending-approval/` — that is the approval gate.

## Learnings & Rules

<!--
Format: [DATE] [CONTEXT] Finding → Action. Keep under 30 lines. Prune quarterly.
See references/feedback-loop.md for protocol + context tags.
-->
- [2026-04-18] [Initial build] 9 recipes seeded: LI-text→X-thread, LI-text→IG-carousel, LI-text→IG-reel, LI-text→WA-status, LI-text→FB, LI-carousel→X-thread, LI-carousel→IG-carousel, X-thread→LI-text, X-single→LI-text. Hook preservation is default. Validator reused from post-writer (no duplicate). Phase gate blocks WA targets in Phase 1 by default.
- [2026-04-18] [Scope decision] Source input is queue-only (not pasted text). v2 candidate: add pasted-text mode after 5+ queue-repurposes prove the core flow.
- [2026-04-18] [Design decision] Repurpose auto-links source to children (`repurposed_into`). Enables performance-review to trace which source posts spawn which variants, and later attribute engagement to transformation recipes.
