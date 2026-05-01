---
name: draft-week
description: "Single drafting engine for the Digischola personal brand. Reads idea-bank.json, produces ready-to-publish drafts saved to brand/queue/pending-approval/ with scheduled_at frontmatter so scheduler-publisher picks them up. Four modes: (1) plan-week — pick 10-12 idea-bank entries, build the week's calendar with pillar rotation across LinkedIn/X/Instagram/Facebook. (2) write-post — turn one shaped entry into one channel-specific draft using voice frameworks + hook library + credential anchoring. (3) repurpose — adapt an existing draft for other channels preserving the source hook. (4) case-study — coordinated 4-deliverable bundle from a client-win entry (LI carousel + X thread + blog + IG carousel). All drafts pass validate_post.py (em-dash, hype, bait, char limits) before saving. Use when user says: draft this, write a post, plan next week, content calendar, weekly plan, repurpose, adapt for X, case study, client win, ship a post about X, draft-week. Do NOT trigger for: capturing raw ideas (use ideas-in), publishing (use scheduler-publisher), creating visuals (use visual-generator), client ad copy (use ad-copywriter)."
---

# draft-week

One skill, four modes. Everything that produces a markdown draft for the personal brand. Downstream `scheduler-publisher` only ships what this skill saves to `brand/queue/pending-approval/`.

## Modes

| Mode | Trigger | Output |
|---|---|---|
| `plan-week` | "plan next week", "build the calendar", "weekly plan", Wednesday ritual | `brand/calendars/YYYY-WXX.md` (10-12 slots) |
| `write-post` | "draft this", "write a post", entry-id arg | One `.md` file in `brand/queue/pending-approval/` |
| `repurpose` | "repurpose", "adapt for X", "make IG variant" | One or more `.md` files in pending-approval/ with `repurpose_source` frontmatter |
| `case-study` | "case study", "client win", "Thrive case study" | A `case-study-<entry_id>/` directory with 4 coordinated drafts |

## Context loading (every mode)

Read once before doing anything:

- `Desktop/Digischola/brand/_engine/wiki/pillars.md` — must be `Status: LOCKED`. If not, abort.
- `Desktop/Digischola/brand/_engine/wiki/voice-guide.md`
- `Desktop/Digischola/brand/_engine/wiki/credentials.md`
- `Desktop/Digischola/brand/_engine/wiki/icp.md`
- `Desktop/Digischola/brand/_engine/wiki/channel-playbook.md`
- `Desktop/Digischola/brand/_engine/idea-bank.json`
- Skill references in `references/` — load only the ones the active mode needs.
- `.claude/shared-context/analyst-profile.md`
- `.claude/shared-context/accuracy-protocol.md`
- `.claude/shared-context/copywriting-rules.md`

If `pillars.md` is not LOCKED, abort with: "Pillars not approved. Run personal-brand-dna first."

## Mode 1: plan-week

Read `references/plan-week-flow.md`. Summary:

1. Determine target week (next Mon → Sun unless overridden).
2. Filter idea-bank to `status: raw` or `shaped`. Score each by recency × pillar-fit × format-fit.
3. Apply pillar rotation: Mon LP Craft / Wed Solo Ops / Fri Small-Budget Paid Media / weekend mixed.
4. Assign 10-12 slots across LinkedIn (3-4) + X (4-5) + Instagram (1-2) + Facebook (1-2). One idea may fan out to 2-3 channels (auto-repurpose flag).
5. Detect gaps: pillar shortage (if a pillar has 0 idea-bank entries), AI-theme cadence (need 1 AI-tool name per week minimum), volume gap (under 10 slots).
6. Write `brand/calendars/YYYY-WXX.md` with one section per slot: `entry_id`, `channel`, `format`, `scheduled_at`, `pillar`, `repurpose_target` (if any).
7. Flip used entries to `status: shaped` via `scripts/draft_io.py`.

## Mode 2: write-post

Read `references/write-post-flow.md` for full procedure. Summary:

1. Load entry by `entry_id` from idea-bank.json.
2. Channel routing: combine `channel` + `format` to a key (e.g., `linkedin-text-post`). Match to char limits in `references/platform-specs.md`.
3. Voice framework selection per `references/voice-frameworks.md` (auto-pick by entry type).
4. Generate 3 hook candidates from `references/hook-library.md` + `brand/references/hooks.json`. Show A/B/C, wait for pick.
5. Apply structure template, voice framework, credential anchoring (`references/credential-anchoring.md`), regional tone (`references/regional-nuances.md`), AI-theme weaving (`references/ai-integration.md`).
6. Save to `brand/queue/pending-approval/YYYY-MM-DD-<entry_id>-<channel>-<format>.md` with frontmatter (see `references/frontmatter-spec.md`).
7. Run `python3 scripts/validate_post.py <draft>` — must exit 0 or 1. Exit 2 = block.

## Mode 3: repurpose

Read `references/repurpose-flow.md`. Summary:

1. Load source draft (must already exist in pending-approval/ or published/).
2. Determine target channels (default: LinkedIn → X-thread + IG-carousel; X-thread → LinkedIn).
3. Preserve source hook verbatim. Adapt body to target platform's char limits + structure template.
4. Save each variant with frontmatter `repurpose_source: <source-filename>` so scheduler doesn't double-post.
5. Validate each variant.
6. Update source draft's frontmatter `repurposed_into: [list]`.

## Mode 4: case-study

Read `references/case-study-flow.md`. Summary:

1. Load `client-win` entry by ID.
2. Build a Setup → Problem → Diagnosis → Fix → Result → Lesson narrative arc once.
3. Adapt to 4 deliverables sharing the same hook + metrics: LI carousel (8-10 slides) + X thread (8-12 tweets) + blog (1500-2500 words) + IG carousel (8-10 slides).
4. Save into `brand/queue/pending-approval/case-study-<entry_id>/` directory + manifest.
5. Each deliverable validates independently.

## Frontmatter required on every saved draft

```yaml
---
channel: linkedin | x | instagram | facebook | whatsapp
format: text-post | carousel | thread | tweet | reel | status
entry_id: <8-char id from idea-bank>
pillar: <pillar name>
voice_framework: <Bush | Hormozi | Perell | Naval | Graham | Schafer>
hook_pattern: '<category #N (descriptor)>'
credential_anchored: <none | thrive_188 | iskm_65 | ...>
ai_theme_applied: true | false
status: drafted
validator_status: <set after running validate_post.py>
posting_status: scheduled | manual_publish_overdue | published
scheduled_at: '<ISO8601 IST>'
scheduled_day: Mon | Tue | ... | Sun
repurpose_source: <filename or null>
repurposed_into: []
---
```

## Validation

After ANY draft saved, run `scripts/validate_post.py <draft>`:
- Exit 0 = clean (no warnings, ship)
- Exit 1 = warnings (review recommended, ship OK)
- Exit 2 = CRITICAL (em dash / hype word / engagement bait / char limit) — fix before save

`scripts/validate_calendar.py` validates calendar files — slot count, pillar distribution, channel mix, date sanity.

## Coordination

- Upstream: reads `idea-bank.json` (filled by `ideas-in`).
- Downstream: `scheduler-publisher` reads `pending-approval/`. `visual-generator` reads draft frontmatter for visual briefs.
- `weekly-ritual` Wed 09:00 IST chains: `ideas-in trend-scan` → `ideas-in peer-scan` → `draft-week plan-week` → `draft-week write-post` (per slot) → `draft-week repurpose` → `visual-generator`.

## Learnings & Rules

Capture insights here per the 7+3 rule. Format: `[YYYY-MM-DD] [mode] Finding → Action`.

- [2026-05-01] [overhaul] Merged content-calendar + post-writer + repurpose + case-study-generator into draft-week. References preserved from post-writer. → All drafting goes through this single skill; no parallel paths.

## Feedback loop

See `references/feedback-loop.md` for end-of-session protocol.
