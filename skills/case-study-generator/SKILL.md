---
name: case-study-generator
description: "Specialized content engine for client wins. Takes one client-win entry from idea-bank.json (Thrive +188% Meta sales, ISKM +65% Ratha Yatra registrations, etc.) and produces a coordinated 4-deliverable bundle: (1) LinkedIn carousel (8-10 slides), (2) X thread (8-12 tweets), (3) long-form blog post (1500-2500 words for digischola.in/blog or LI newsletter), (4) Instagram carousel (8-10 visual slides). All 4 share the same hook + metrics + Setup→Problem→Diagnosis→Fix→Result→Lesson narrative arc, with platform-specific adaptations. Validates hook consistency across deliverables + metric accuracy + voice rules (no em dashes, no hype, no engagement bait, Conservative client naming) before bundling. Outputs a `case-study-<entry_id>/` directory in pending-approval/ with all 4 files + a coordination manifest. Each deliverable is independently schedulable by scheduler-publisher. Use when user says: case study, client win, turn this win into content, case study from <entry>, make a Thrive case study, ISKM case study, content from client result. Do NOT trigger for: drafting one platform's post (use post-writer), repurposing an already-drafted post (use repurpose), planning the week (use content-calendar), capturing a new client win (use work-capture)."
---

# Case Study Generator

Specialized engine for high-leverage client wins. Produces 4 coordinated content pieces from one client story, all sharing the same hook + metrics + narrative arc. Higher production value than post-writer; rarer in cadence (1-2 client wins per month worth this treatment).

## Why specialized vs post-writer + repurpose

post-writer + repurpose generates platform variants that share a hook but each is independently structured. case-study-generator enforces a **single coordinated narrative** (Setup → Problem → Diagnosis → Fix → Result → Lesson) across all 4 deliverables. The result reads like a multi-channel campaign, not 4 standalone posts.

Quality bar is also higher: stronger structure, more rigorous metric verification, blog post depth, visual-generator briefs that match across LI + IG carousels.

## Context Loading

**Brand wiki:**
- `Desktop/Digischola/brand/voice-guide.md` — Conservative client-naming policy
- `Desktop/Digischola/brand/credentials.md` — public client mentions allowed
- `Desktop/Digischola/brand/idea-bank.json` — source client-win entries
- `Desktop/Digischola/brand/pillars.md` — must be LOCKED

**Shared context:**
- `.claude/shared-context/analyst-profile.md` — workflow, voice standards, formatting preferences

**Skill references:**
- `references/case-study-structure.md` — Setup → Problem → Diagnosis → Fix → Result → Lesson framework
- `references/platform-adaptations.md` — per-channel rules (slide count, tweet length, blog headers, IG visual density)
- `references/client-naming-policy.md` — Conservative anonymization unless metrics are publicly displayed
- `references/evidence-packaging.md` — how to surface metrics + visuals + quotes consistently
- `references/feedback-loop.md`

**Skill templates (assets/templates/):**
- `li-carousel-skeleton.md` — 8-10 slide outline
- `x-thread-skeleton.md` — 8-12 tweet outline
- `blog-skeleton.md` — H2/H3 structure for 1500-2500 words
- `ig-carousel-skeleton.md` — visual-heavy 8-10 slide outline

**Other skills consumed:**
- `post-writer/scripts/validate_post.py` — reused for hard-rule validation per deliverable
- `visual-generator/scripts/generate_brief.py` — invoked to create the LI + IG carousel briefs
- `scheduler-publisher/scripts/apply_calendar.py` — schedules each deliverable independently

## Process

### Step 1 — Pick a source

User invokes with one of:
- `python3 scripts/case_study.py prepare --entry-id 4e4eed15`
- "create a case study from entry 4e4eed15"
- "make a case study for Thrive Retreats"

Script reads idea-bank.json, finds the entry, validates it's a client-win (`type: client-win` OR has `client` + `outcomes` fields), aborts if not.

### Step 2 — Apply naming policy

Per `references/client-naming-policy.md`:
- If client name + metrics are publicly displayed on digischola.in (case studies page) → name allowed (e.g., "Thrive Retreats", "ISKM Singapore")
- If metrics are public BUT name is not on the site → anonymize (e.g., "a wellness retreat client in NSW")
- If metrics are NOT public → use anonymized form + skip the most identifying details

Public-allowed clients (from credentials.md):
- Thrive Retreats (+188% Meta sales / -37% CPS, 90 days)
- ISKM Singapore (Ratha Yatra +65% registrations / +40% attendance)
- Happy Buddha Retreats (same founder Athil)
- Samir's Indian Kitchen (Surry Hills Sydney)
- Chart & Chime
- CrownTECH (Toronto)

### Step 3 — Generate 4 deliverables in Claude

Claude (this session) reads:
1. The source entry from idea-bank
2. The 4 templates in `assets/templates/`
3. `references/case-study-structure.md` for the narrative arc
4. `references/platform-adaptations.md` for per-channel rules

Then produces 4 drafts in parallel, each following its skeleton + the shared narrative arc:

**LinkedIn carousel** (8-10 slides):
- Slide 1: Hook (the headline metric + 1-line result)
- Slide 2: Setup (client, period, baseline numbers)
- Slide 3: Problem (what wasn't working)
- Slides 4-6: Diagnosis + Fix (3 specific changes)
- Slide 7: Result (numbers + curve)
- Slide 8: Lesson (the takeaway for the audience)
- Slide 9 (optional): Subtle CTA

**X thread** (8-12 tweets):
- Tweet 1: Hook (must match LI Slide 1)
- Tweets 2-3: Setup
- Tweet 4: Problem
- Tweets 5-7: Diagnosis + Fix (one tweet per change)
- Tweet 8-9: Result
- Tweet 10: Lesson
- Tweet 11 (optional): Soft CTA

**Blog post** (1500-2500 words):
- H1: Hook (verbatim same)
- Intro paragraph (200-300 words): Setup
- H2 — The Problem (300-400 words)
- H2 — Diagnosis: Where the Friction Was (300-400 words)
- H2 — The Fix: Three Changes (600-800 words; H3 per change)
- H2 — The Result (200-300 words with chart description)
- H2 — What This Means For You (200-300 words; the lesson)
- Optional CTA paragraph

**IG carousel** (8-10 slides):
- Same narrative as LI but visual-heavier (more whitespace, bigger numbers)
- Slide 1: Big hook number (e.g., "188%" in Orbitron 280pt)
- Slide 2-7: Same flow, 1 main point per slide max
- Slide 8: Logo + soft CTA

### Step 4 — Validate all 4

Run `validate_case_study.py` which checks:
1. **Hook consistency**: Slide 1 of LI carousel + Tweet 1 + Blog H1 + Slide 1 of IG carousel — all 4 must contain the same headline metric verbatim (e.g., "188%")
2. **Metric drift**: All metrics referenced are identical across deliverables
3. **Voice rules**: No em dashes, no hype words, no engagement bait, no lowercase CTAs
4. **Naming consistency**: Same client identifier (named OR anonymized) across all 4
5. **Length limits**: LI carousel 8-10 slides, X thread tweets ≤280 chars each, blog 1500-2500 words, IG carousel 8-10 slides
6. **Pillar consistency**: All 4 are tagged with the same pillar from source entry

If any check fails: surface to Claude for re-generation. Do not write to pending-approval until clean.

### Step 5 — Bundle to pending-approval

Write to `brand/queue/pending-approval/case-study-<entry_id>/`:
- `linkedin-carousel.md` (with frontmatter: channel=linkedin, format=carousel, entry_id=<id>, case_study_bundle=<id>)
- `x-thread.md` (channel=x, format=x-thread)
- `blog-post.md` (channel=blog, format=long-form)
- `instagram-carousel.md` (channel=instagram, format=carousel)
- `manifest.json` (links all 4 + records the source entry + naming decision + validation pass)

Plus invoke `visual-generator/scripts/generate_brief.py` for the LI + IG carousels → briefs land in `brand/queue/briefs/`.

### Step 6 — Catalog + report

Print a summary:
- 4 deliverables written, paths
- 2 visual briefs generated, paths
- Suggested scheduling: LI Mon 09:00 IST, X-thread Tue 11:00, IG carousel Sat 10:00, blog Wed (newsletter)
- Cross-promotion notes: "X thread links to blog; IG carousel teases blog; LI carousel is standalone"

## Output Checklist

- [ ] Source entry exists in idea-bank.json AND is a client-win
- [ ] 4 deliverables written to `pending-approval/case-study-<id>/`
- [ ] 2 visual briefs generated (LI + IG)
- [ ] Manifest.json written
- [ ] All 4 pass validate_case_study.py
- [ ] Hook + metrics + naming consistent across all 4

## Anti-patterns

- Do NOT write a case study from a non-client-win entry (e.g., a framework or hot take). Use post-writer instead.
- Do NOT auto-publish — case studies are high-stakes, always require Mayank's review before scheduling.
- Do NOT name a client whose metrics aren't on digischola.in publicly. Conservative anonymization is the default.
- Do NOT vary the headline metric across deliverables (Slide 1 LI says "188%", X thread Tweet 1 must also say "188%" verbatim).
- Do NOT skip the lesson section — without "What this means for you", a case study reads as a brag rather than a teaching post.
- Do NOT include >3 named change interventions in the Fix section. Audiences glaze at >3 bullet points; pick the 3 most impactful changes even if you made 7.
- Do NOT use em dashes anywhere in any deliverable.

## Learnings & Rules

<!--
Format: [DATE] [CONTEXT] Finding → Action. Keep under 30 lines.
-->
- [2026-04-20] [Initial build] Built as the specialized engine for client wins (1-2 per month). 4-deliverable bundle: LI carousel, X thread, blog post, IG carousel. All share the same hook + metrics + Setup→Problem→Diagnosis→Fix→Result→Lesson narrative arc. validate_case_study.py enforces hook consistency + metric drift + voice rules + length limits + naming consistency before bundling. Output bundle goes to `pending-approval/case-study-<entry_id>/` so scheduler-publisher ships each deliverable independently. visual-generator's generate_brief.py invoked for LI + IG carousel renders.
- [2026-04-20] [Public clients allowed] Per `credentials.md`: Thrive Retreats, ISKM Singapore, Happy Buddha Retreats, Samir's Indian Kitchen, Chart & Chime, CrownTECH have publicly-displayed metrics on digischola.in — these names are allowed in case studies. Any other client → Conservative anonymization (e.g., "a wellness retreat client in NSW").
- [2026-04-20] [Cross-skill] Reads from idea-bank.json (work-capture's data store). Reuses post-writer's validate_post.py for hard-rule per-deliverable validation. Invokes visual-generator's generate_brief.py for the carousel briefs. Outputs feed scheduler-publisher (each deliverable independently scheduleable). performance-review measures engagement per-deliverable to inform which case-study format formulation works best (carousel vs thread vs blog vs IG).
