# Pillar Generation Framework

How to convert mined work-history data + trend signals into 5-7 content pillar candidates.

## Inputs

1. `_mining/work-topics.json` — entity + keyword frequencies
2. `_mining/voice-samples.txt` — what the owner actually talks about
3. Website extraction — services, case studies, credentials
4. Analyst profile — workflow, client types
5. Trend signals — optional WebSearch for niche-specific rising/saturated/underserved topics

## Framework

### Step 1 — Cluster work-history signals

Group entities + keywords from `work-topics.json` by theme. Typical clusters that emerge:
- **Tooling / systems** (keyword: skill, automation, workflow, prompt, agent) — if "skill" or equivalent dominates the corpus, this is a "building AI ops" pillar candidate
- **Service delivery** (keyword: client, campaign, funnel, creative, ad copy) — day-to-day execution work
- **Specific craft areas** (keyword: landing page, conversion, hook, carousel) — pillar-worthy niche expertise
- **Operator life** (keyword: freelance, pricing, time, scope, client management) — positioning as a solo operator
- **Industry vertical** (entity: client names clustered by industry) — vertical expertise becomes a pillar if 2+ clients share the industry

Rule of thumb: any theme with >15 keyword mentions across sessions or 3+ entity clusters deserves a pillar candidate.

### Step 2 — Overlay trend signals

Light WebSearch (or reference knowledge) for:
- "rising topics in {owner's niche} 2026" — agentic AI, operator mode, small-team systems tend to surface
- "saturated content in {niche}" — generic prompts, ChatGPT tips, AI tool roundups
- "underserved audiences in {niche}" — non-US markets, small budgets, solo operators

Each candidate pillar gets tagged: `rides-rising`, `underserved-wedge`, or `saturated-risk`. Prefer pillars that ride rising or underserved waves; avoid saturated.

### Step 3 — Positioning bridge (when needed)

If website positioning and CLI-work positioning diverge (common when website is credentials-heavy but daily work has shifted to AI-native), propose a BRIDGE pillar that combines both:
- "{Old credential} → {new work}" framing
- Example: "Ex-Google → building MarketingOS"

The bridge usually becomes the strongest pillar because it's rare to have both the old credential AND the new distinction.

### Step 4 — Candidate structure (for each pillar)

Each candidate in `pillars.md` must contain:
1. **Thesis** — single-sentence positioning claim
2. **Why this wins** — 3-4 bullets with data backing (CLI mention count, website evidence, trend tag, credential fit)
3. **Content types** — concrete post formats (skill unveil, audit case study, build log, etc.)
4. **Audience fit** — which content-ICP segments (B1-B4) it serves

### Step 5 — Recommendation

Flag candidates as:
- **Strong yes (3):** the core 3 pillars — most distinctive, data-dense, evergreen
- **Pick one of these (1-2):** variety options with different audience trade-offs (e.g., "lead-gen focus" vs "referral focus")
- **Skip for now:** pillars that are better as TAGS applied across other pillars, or premature given current brand stage

Always flag a recommended final set of 3-4 with rationale. The user makes the final call.

## Anti-patterns

- **Do not propose a pillar because it sounds trendy.** If there's no CLI evidence or case-study evidence, skip it.
- **Do not propose 10+ candidates.** 5-7 is the ceiling; more creates decision paralysis.
- **Do not promise "everyone needs this" pillars.** Broad = generic = no audience.
- **Do not recommend a pillar the owner has explicitly de-prioritized** (e.g., if user said "no YouTube long-form", don't propose a video-tutorial pillar).
- **Do not stack all pillars around the same audience.** Mix: one broad, one niche, one contrarian.

## Output format

Write candidates to `pillars.md` with:
- Status banner (AWAITING APPROVAL)
- Positioning tension section (if applicable)
- Candidates numbered [1]-[7]
- Recommendation block with proposed final set
- Trend overlay notes
- Learnings & Rules placeholder
