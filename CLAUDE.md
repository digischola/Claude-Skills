# Mayank Verma — Universal Session Rules

These rules apply to EVERY session, every skill, every output. Non-negotiable.

## Who I Am

AI-based digital marketing freelancer. Pre-marketing research and campaign development for Meta + Google Ads. Based in Gurugram, Haryana. See `.claude/shared-context/analyst-profile.md` for full context.

## Skill Tracks (Always Active)

Two separate skill groups, two separate contexts. Never mix them.

1. **Client-skills track** — skills for doing marketing work FOR clients (market-research, business-analysis, landing-page-audit, ad-copywriter, campaign-setup, landing-page-builder, paid-media-strategy, post-launch-optimization, and future client-delivery skills).
   - Strategic context: `.claude/shared-context/strategic-context.md`
   - Client deliverables: `Desktop/{Client Name}/{Project or Business}/`

2. **Personal-brand track** — skills for growing Digischola as Mayank's own brand (personal-brand-dna, work-capture, and the ~13 planned personal-brand suite skills).
   - Strategic context: `Desktop/Digischola/strategic-context.md`
   - Brand wiki: `Desktop/Digischola/brand/`

Session-close updates and cross-session learnings go to the track-specific strategic-context file. The two tracks never share data except for `.claude/shared-context/analyst-profile.md`, `accuracy-protocol.md`, and `skill-architecture-standards.md` (universal).

## Accuracy Protocol (Always Active)

Three rules apply to ALL research, analysis, and data extraction — regardless of which skill is running. See `.claude/shared-context/accuracy-protocol.md` for the full protocol.

1. **Blank when uncertain.** If a data point is ambiguous, missing, or contradictory — leave it BLANK with a one-sentence reason. Never fill gaps with reasonable guesses.
2. **3x penalty.** A wrong answer is 3x more damaging than a blank. When in doubt, leave it blank.
3. **Source label everything.** Every finding gets tagged: `[EXTRACTED]` (directly from source) or `[INFERRED]` (your synthesis — state the evidence). Inferred is fine, but it must be labeled.

## Skill Architecture Standards (Always Active)

Every skill built or modified in any session must follow these standards. See `.claude/shared-context/skill-architecture-standards.md` for the full framework.

- SKILL.md under 200 lines — it's a table of contents, not an encyclopedia
- Progressive disclosure — heavy detail goes in references/, loaded only when needed
- YAML frontmatter with clear trigger words, anti-triggers, and outcome description
- References folder for domain knowledge, scripts folder for executable code, assets for templates
- Business context personalization — every skill reads shared-context/analyst-profile.md
- Feedback loop — every skill has a Learnings & Rules section that captures session insights
- Skill coordination — outputs structured so downstream skills can consume them
- Eval-ready — test cases defined in evals/evals.json

## Formatting Preferences

- No salutations, no fluff
- Simple, direct language
- No tabular format in prose (tables OK for benchmark data and comparisons)
- Outputs should feel like a senior strategist briefing
- Dashboard/HTML outputs: dark mode, client branding, aggressive animations, premium feel

## Protected Files (Do Not Modify)

The following files define universal standards and must NEVER be edited, overwritten, or rewritten by any session or skill — even if asked to "improve" or "rebuild" a skill. These are permanent rules, not templates:

- `.claude/CLAUDE.md` (this file)
- `.claude/shared-context/accuracy-protocol.md`
- `.claude/shared-context/skill-architecture-standards.md`
- `.claude/shared-context/analyst-profile.md`

Everything else — SKILL.md files, reference files, scripts, assets, evals — can be created, modified, or deleted as needed. Only the above four files are locked.

If a user explicitly asks to update these files, confirm the specific change before making it. Never modify them as a side effect of another task.

## Skill Auto-Update Rule (Always Active)

When ANY file inside a skill folder is modified (scripts/, references/, assets/, templates), the following MUST happen **immediately as part of the same fix** — not deferred to session close, not as a separate step:

1. **Update SKILL.md** — if the fix changes how a step works, update that step's description in SKILL.md.
2. **Write learnings** — add a dated entry to the skill's Learnings & Rules section describing what broke, why, and what was fixed. Format: `[DATE] [CLIENT TYPE] Finding → Action`.
3. **Update wiki** — if the fix affects a client deliverable that was already generated (e.g., brand-config.json with wrong colors), update the wiki files too.

These three actions are part of the fix. A fix without them is incomplete. Do not wait for the user to ask "did the skill get updated?" — that means the rule was violated.

## Skill Protocol Supremacy (Always Active)

When a skill is invoked, its steps are executed literally — not adapted, abbreviated, or short-circuited by judgment. Analyst judgment interprets data *within* the skill's framework, never substitutes for a missing step or overrides the skill's procedure.

If a skill step fails, produces ambiguous data, or hits a scenario the skill doesn't cover:

1. **Stop the skill run.** Do not improvise a workaround to push through.
2. **Log the gap** as a skill-improvement candidate in the Learnings & Rules section.
3. **Patch the skill** per the 7+3 rule (SKILL.md, references/, scripts/, evals/, feedback loop).
4. **Re-run the skill** with the patched protocol.

Never silently paper over a protocol gap with judgment and ship — that's how skills stop learning. The goal is to make skills more capable, and that only happens when their gaps become visible.

**What counts as "judgment substitution" (not allowed):**
- Skipping a mandatory step because it felt harder than expected
- Interpreting ambiguous output as definitive findings without the skill's cross-check procedure
- Inventing missing protocols ad-hoc instead of adding them to the skill
- Trusting one data source over another when the skill doesn't specify priority

**What counts as "judgment within framework" (allowed and required):**
- Choosing which severity tier fits a finding per the scoring rubric
- Adapting ad copy to the specific brand voice per the creative brief
- Picking competitor names to seed into a research prompt
- Weighing which fix to recommend first when multiple are valid

## Session Start Audit (Always Active)

When activating any skill at the start of a session:

1. Check the skill's `scripts/` folder modification dates against the last Learnings & Rules entry date in SKILL.md.
2. If any script is newer than the last learning entry, a previous session likely modified the script without updating learnings. Run a **retroactive feedback loop** before proceeding: read the script changes, write missing learnings, update SKILL.md step descriptions if needed.

## Mandatory Session Close Protocol

Every skill session MUST end with these steps — no exceptions, even if the user says "that's fine" or tries to close early:

1. **Validate outputs.** If the skill has a `scripts/validate_output.py`, run it against all deliverables. Fix any CRITICAL failures before delivery.
2. **Run feedback loop.** Review what worked, what didn't, and capture learnings in the skill's Learnings & Rules section. See the skill's `references/feedback-loop.md` for format.
3. **Flag downstream connections.** Note which other skills can consume this output (e.g., "research ready for meta-ad-copywriter").
4. **Update the strategic-context file for the active skill's track** if any business decisions, client changes, revenue updates, or roadmap shifts happened during the session:
   - Client-skills track: `.claude/shared-context/strategic-context.md`
   - Personal-brand track: `Desktop/Digischola/strategic-context.md`
   
   See the "Skill Tracks" section at the top of this file.

If a session is interrupted or cut short, the next session that activates the same skill must run the feedback loop retroactively.

## Client Work Structure

Client deliverables are organized as: `{Client Name}/{Project or Business}/` on Desktop. Research, dashboards, brand configs go into the client folder — not loose on Desktop.
