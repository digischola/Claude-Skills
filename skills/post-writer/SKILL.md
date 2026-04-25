---
name: post-writer
description: "Top-tier social post writer for the Digischola personal brand. Takes an idea-bank entry and produces ready-to-publish drafts for LinkedIn (text / carousel / video), X (single / thread), Instagram (caption / Reel caption), Facebook, and WhatsApp (Status / Channel). Applies voice-guide rules, credential anchoring cadence, hook library patterns, voice frameworks (Dickie Bush, Hormozi, Perell, Naval, Graham, Schafer), platform-specific algorithm preferences, and regional tone. Runs validate_post.py to enforce hard rules (no em dashes, no hype words, no engagement bait, char limits). Saves drafts to Desktop/Digischola/brand/queue/pending-approval/ for user review. Use when user says: write a post, draft this, turn this idea into a LinkedIn post, write me an X thread, draft LI from idea bank, post-writer, ship a post about X. Do NOT trigger for: client ad copy (use ad-copywriter), repurposing an existing post across channels (use repurpose — future skill), writing a landing page (use landing-page-builder), scheduling (use scheduler-publisher — future skill)."
---

# Post Writer

Turn an idea-bank entry into a ready-to-publish draft for a specific channel and format in Mayank's voice. Top-tier writer built on 2026 Perplexity research + 6 codified voice frameworks + 35 hook patterns + platform-specific rules. Hard-rule validator blocks posts that violate brand voice rules.

## Context Loading

Read these before drafting anything:

**Brand wiki (required):**
- `Desktop/Digischola/brand/pillars.md` — Status must be LOCKED
- `Desktop/Digischola/brand/voice-guide.md` — three registers + universal rules
- `Desktop/Digischola/brand/credentials.md` — trust anchors + verified metrics
- `Desktop/Digischola/brand/icp.md` — audience fit per pillar
- `Desktop/Digischola/brand/idea-bank.json` — source entries

**Skill references (required):**
- `references/platform-specs.md` — algorithm rules, length, structure templates per channel
- `references/hook-library.md` — 35 hook patterns across 9 categories
- `references/creator-study.md` — 15 named creators to draw inspiration from (not copy)
- `references/ai-integration.md` — AI-as-theme patterns + anti-patterns
- `references/credential-anchoring.md` — 5 anchor types + cadence rules
- `references/voice-frameworks.md` — Dickie Bush 3x3, Hormozi, Perell, Naval, Graham, Schafer
- `references/regional-nuances.md` — Indian operator serving AU/SG/NA

**Shared context:**
- `.claude/shared-context/analyst-profile.md`
- `.claude/shared-context/accuracy-protocol.md`

If pillars.md is not LOCKED, abort with: "Pillars not approved. Run personal-brand-dna first."

## Inputs

1. **Entry ID** (preferred) — a UUID from idea-bank.json
2. **Raw note** (fallback) — a user-provided note that gets captured via work-capture first, then drafted
3. **Target channels** — one or more of: `linkedin-text`, `linkedin-carousel`, `linkedin-video`, `x-single`, `x-thread`, `instagram-caption`, `instagram-reel`, `facebook-post`, `whatsapp-status`, `whatsapp-channel`
4. **Optional overrides** — target audience (global / US / AU / SG / IN), voice framework (default: auto-select per entry type), credential to anchor (default: auto-decide)

## Process

### Step 1: Validate pillars lock

Read `pillars.md` first 20 lines. If `Status:` line does not contain `LOCKED`, abort with an explicit message pointing user to `personal-brand-dna`.

### Step 2: Load entry

Read entry from idea-bank.json by ID. Extract `type`, `raw_note`, `suggested_pillar`, `channel_fit`, `format_candidates`, `tags`.

### Step 3: Channel routing

For each target channel, match to a `channel-format` key from `platform-specs.md` char-limit table. Default routing by entry type if user did not specify:

| Entry type | Default channels |
|---|---|
| client-win | linkedin-text + x-thread + instagram-carousel |
| insight | linkedin-text + x-single |
| experiment | linkedin-text + x-thread |
| failure | linkedin-text only (vulnerability works best long-form) |
| build-log | linkedin-text + x-thread + whatsapp-status |
| client-comm | linkedin-text |
| observation | x-single + linkedin-text |

### Step 4: Select voice framework

Use the framework-to-content-type table in `references/voice-frameworks.md`:
- LP audits → Dickie Bush 3x3
- Case studies → Hormozi Value Equation
- Manifesto / thought leadership → Perell + Naval
- Freelance-ops insight → Graham (Plain English)
- Vulnerable stories → Schafer (Conversational)
- X tight tweets → Naval (Compression)

### Step 5: Generate 3 hook candidates

From `references/hook-library.md`, pick 3 patterns from DIFFERENT categories that fit the entry type (see the entry-type-to-hook-category map at bottom of hook-library.md). Adapt each pattern to the specific entry content. Each under 210 chars for LinkedIn; tighter for X.

Do not commit to one hook. Present 3 options labeled A/B/C, wait for user pick.

### Step 6: Draft the post

Once hook is picked (or for non-hook channels like IG carousel slides), apply:

1. **Structure template** from `platform-specs.md` for that channel/format
2. **Voice framework** from Step 4
3. **Credential anchoring decision** per `references/credential-anchoring.md`:
   - Check `credential-usage-log.json` (create if missing): which credentials used in last 30 days?
   - If entry warrants credential + available credential unused, apply one of 5 anchor types
   - If no credential fits, skip and rely on bio-level anchoring
4. **AI-theme weaving** per `references/ai-integration.md`:
   - If entry mentions AI tools (Claude, Perplexity, etc.), apply one of the working patterns
   - Name tools, quantify time saved, keep human-in-edit-seat
5. **Regional tone** per `references/regional-nuances.md`:
   - Default to Confident Pragmatism + USD
   - Only tailor if the target audience is specified

### Step 7: Validate

Run `scripts/validate_post.py <draft_file> --channel <channel-key>`. Three outcomes:

- Exit 0: clean, save to queue
- Exit 1: soft warnings (sentence uniformity, AI-tell transitions, off-sweet-spot length) — log warnings in draft file header, still save
- Exit 2: CRITICAL (em dash, hype word, engagement bait, hard char cap exceeded) — do NOT save. Show user the violations + auto-regenerate one corrected version.

### Step 8: Save to queue

Save clean drafts to `Desktop/Digischola/brand/queue/pending-approval/` with this naming:
`{YYYY-MM-DD}-{entry_id_8chars}-{channel-key}.md`

Frontmatter format:

```yaml
---
channel: linkedin
format: text-post
entry_id: abc-12345
pillar: Landing-Page Conversion Craft
voice_framework: Dickie Bush 3x3
credential_anchored: ex-google (lesson-anchor)
ai_theme_applied: true
validator_status: clean
chars: 1456
hook_options:
  - A: [Data hook text]
  - B: [Counterintuitive hook text]
  - C: [Question hook text]
selected_hook: A
---

[Final post body]
```

### Step 9: Update credential log

If a credential was anchored, append to `Desktop/Digischola/brand/credential-usage-log.json`:

```json
{
  "ex-google": [{"date": "2026-04-18", "post-id": "abc-12345", "anchor-type": "lesson-anchor"}],
  ...
}
```

Create the file if it does not exist.

### Step 10: Feedback loop

Read `references/feedback-loop.md`. If the user rejected a hook, voice framework, or credential choice during the session, log it in SKILL.md Learnings & Rules.

## Output Checklist

- [ ] pillars.md LOCKED check passed (abort if not)
- [ ] Entry loaded from idea-bank.json OR captured fresh via work-capture
- [ ] Each target channel produces a draft with frontmatter + body
- [ ] 3 hook candidates offered per channel, user picks before final draft
- [ ] Voice framework applied (named in frontmatter)
- [ ] Credential decision logged (anchored or skipped, with reason)
- [ ] validate_post.py exit 0 or 1 for every saved draft (never 2)
- [ ] Draft saved to queue/pending-approval/ with correct filename
- [ ] credential-usage-log.json updated if anchored

## Anti-patterns

- Do NOT publish or schedule. This skill only drafts. Publishing is scheduler-publisher's job (future skill).
- Do NOT commit to one hook. Always present 3, let user pick.
- Do NOT bypass validate_post.py. If exit 2, fix and regenerate, never force-save.
- Do NOT reuse a credential that was anchored in the last 30 days.
- Do NOT mimic a creator's voice from creator-study.md. Mimic their format structure only.
- Do NOT ship posts that have zero specific numbers, names, or dates. The voice-guide demands specificity.

## Learnings & Rules

<!--
Format: [DATE] [CONTEXT] Finding → Action. Keep under 30 lines. Prune quarterly.
See references/feedback-loop.md for protocol and context tags.
-->
- [2026-04-18] [Initial build] Skill built from Perplexity deep research (458 lines) + brand wiki (8 LOCKED files). Seeded: 35 hook patterns, 15 creator studies, 6 voice frameworks, 5 credential anchor types. Validator enforces em-dash + hype-word + engagement-bait + char-cap as hard rules; flags AI-tell transitions + uniform sentence variance + off-sweet-spot length as soft warnings.
- [2026-04-18] [Design decision] Static v1 of creator-study.md. Will be refreshed live by `peer-tracker` skill (see `Desktop/Digischola/strategic-context.md` under "Design Notes for Future Skills").
- [2026-04-18] [Validator bug caught in first test] `validate_post.py` was concatenating frontmatter channel + format even when `--channel` override was provided, producing keys like "linkedin-text-text-post" that did not match `CHANNEL_LIMITS`. Char limit checks were silently skipping. Fix: `--channel` override is now definitive; frontmatter channel+format only used when override absent. Re-tested clean + dirty posts; all gates work.
- [2026-04-18] [Validator thread-mode upgrade] First X thread draft revealed that validator treated threads as single posts, summing all tweet bodies against the 280-char cap. Added `x-thread` channel mode with `split_thread_tweets()` + `check_thread_char_limits()` functions that split on `## Tweet N` section headers and validate each tweet independently. Universal checks (em dash, hype, bait) still run across full file. Also caught em dashes in my own section headers (`## Tweet 2 (setup — the problem)`); swapped all hyphens in headers to colons.
- [2026-04-18] [Policy decision logged to voice-guide.md] User chose Conservative client-naming + Restrained emoji policy during first post-writer demo. Both codified in voice-guide.md with dedicated sections. All future post-writer runs should read these sections before drafting.
