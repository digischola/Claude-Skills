---
name: personal-brand-dna
description: "Extracts the complete DNA of a personal brand (owner's or a client's personal brand) from CLI transcripts, live website, memory files, analyst profile, and brand guide — then produces a structured brand wiki (voice-guide, pillars, icp, channel-playbook, brand-identity, credentials) that every downstream personal-brand skill reads from. Use when user mentions: personal brand, my brand, build my brand, brand foundation, brand wiki, brand DNA, voice extraction, content pillars, start my social media brand, or when the user provides their own website + asks for brand analysis to build social content from. Also trigger when a new personal-brand folder on Desktop needs initialization. Do NOT trigger for: client business analysis (use business-analysis), market research, ad copy writing, landing-page audit, or content writing for already-established brands (use post-writer downstream)."
---

# Personal Brand DNA Extraction

Extract the complete DNA of a personal brand from all available sources and produce the structured brand wiki every downstream personal-brand skill reads from. Foundation skill — run once when the brand is initialized, refresh pillars quarterly or when positioning shifts.

## Context Loading

Read these shared-context files before starting:
- `shared-context/analyst-profile.md` — workflow, voice standards, quality bar
- `shared-context/accuracy-protocol.md` — 3 accuracy rules for all data handling
- `shared-context/output-structure.md` — Digischola uses queue-based structure (NOT outputs/working/ split); after content drops, run `python3 ~/.claude/scripts/build_digischola_index.py` to refresh the index

If a personal-brand wiki already exists at `Desktop/{Brand}/brand/_engine/wiki/`, read `brand-wiki.md` first. This may be a refresh, not a fresh build.

## Inputs (5 sources — missing any is allowed but flagged)

1. **Analyst profile** — `.claude/shared-context/analyst-profile.md`
2. **CLI transcripts** — `~/.claude/projects/<project-hash>/*.jsonl`
3. **Memory files** — `~/.claude/projects/<project-hash>/memory/*.md`
4. **Website** — brand's own URL
5. **Brand guide** — design system (colors, fonts) if the user has one

## Process

### Step 1: Wiki Folder Setup

Create `Desktop/{Brand Name}/brand/_engine/wiki/` and `Desktop/{Brand Name}/brand/_engine/_mining/`.

### Step 2: Mine CLI Transcripts

Run `scripts/mine_transcripts.py`. Customize `KNOWN_ENTITIES` for the brand's client/project list before running (seed from analyst profile + memory files). Outputs to `_engine/_mining/`:
- `voice-samples.txt` — up to 120 representative user utterances
- `work-topics.json` — entity + keyword frequencies (highest-frequency terms = strongest pillar candidates)
- `session-summaries.json` — per-session first/last snippets

### Step 3: Website Render (Chrome MCP fallback is mandatory for SPAs)

WebFetch the brand URL first. If body content is <500 chars OR shows signs of a React/Lovable/GPT-Engineer SPA, fall back to Chrome MCP via the chain in `references/fallback-chain.md`:
1. `mcp__Claude_in_Chrome__tabs_context_mcp` with `createIfEmpty: true`
2. `mcp__Claude_in_Chrome__navigate` to the URL
3. `mcp__Claude_in_Chrome__read_page` with depth 20 (accessibility tree — catches nav, services, testimonials, case studies, form options)
4. `mcp__Claude_in_Chrome__get_page_text` for body content

Extract: positioning taglines, navigation structure, service list, testimonials, case studies with metrics, partner logos, contact info, social links, awards/credentials, visible tone.

### Step 4: Voice Extraction

Read `_engine/_mining/voice-samples.txt`. Identify:
- **Universal rules** — scan for explicit user corrections ("don't", "stop", "no", "not") which become hard rules
- **Sentence patterns per register** — Strategist / Operator / BTS
- **Signature moves** — specific vocabulary, framing choices, credential anchoring

Draft `voice-guide.md`. Tag universal rules as [EXTRACTED] with the transcript sample number as source.

### Step 5: Credentials & Identity Lock

From website render + brand guide, extract and write:
- `brand-identity.md` (colors, fonts, logo, UI rules) — LOCKED immediately
- `credentials.md` (awards, scale stats, testimonials, verified metrics) — LOCKED immediately

These are public-source, no approval gate needed.

### Step 6: Pillar Candidate Generation

Follow `references/pillar-generation-framework.md`:
1. Cluster high-frequency entities + keywords from `_engine/_mining/work-topics.json` into 3-5 rough themes
2. Overlay trends: light WebSearch for "rising in {niche}" + "saturated in {niche}" + "underserved in {niche}"
3. Produce 5-7 candidate pillars, each with: thesis, why-it-wins (data-backed), content types, audience fit
4. Mark the 3 strongest as "Strong yes"; flag 1-2 as "pick one for variety"; flag any as "skip for now" with rationale
5. Write to `pillars.md` with `Status: AWAITING APPROVAL`

The skill does NOT choose final pillars. It proposes. User approves 3-5 in a follow-up turn before `pillars.md` can lock.

### Step 7: ICP & Channel Playbook Drafts

`icp.md` — service ICP (from client archetypes) + content ICP (from pillar audience fits). Map each pillar to one or more content-ICP segments (B1, B2, B3, B4 by convention).

`channel-playbook.md` — phased activation based on CURRENT follower counts (ask user if not stated). Default phases:
- **Phase 1 (wks 1-6):** activate the warmest channel first; cold channels run repurpose-only
- **Phase 2 (wks 7-12):** activate secondary channels once Phase 1 has traction
- **Phase 3 (wks 13+):** optimize via `performance-review` data

Include a "Bio & Link Hygiene" checklist for Week 1.

### Step 8: Wiki Index + Config

Write `_engine/wiki/brand-wiki.md` (master index, file status table) and `_engine/wiki-config.json` (metadata for validators, downstream reader list, approval gates). Seed `_engine/idea-bank.json` as empty for `work-capture`.

### Step 9: Present Approval Gate

Surface for explicit user approval:
- 5-7 pillar candidates with your recommendation
- Voice universal rules (especially surprising ones)
- Phase 1 channel plan
- Any positioning tension / bridge recommendation

Wait for user approval of 3-5 pillars before any downstream skill (post-writer, content-calendar, etc.) can consume the wiki.

### Step 10: Feedback Loop

Read `references/feedback-loop.md`. Capture what worked/didn't. Add dated learning below (30 lines max).

## Output Checklist

- [ ] `Desktop/{Brand}/brand/_engine/wiki/` created with 9 files
- [ ] Every data point tagged `[EXTRACTED]`, `[INFERRED]`, or `[INTAKE]` per accuracy protocol
- [ ] Missing data shows `BLANK — reason` (never guessed)
- [ ] `_engine/wiki/brand-identity.md` and `_engine/wiki/credentials.md` LOCKED (public-source only)
- [ ] `_engine/wiki/voice-guide.md` has a Universal Rules section with explicit user corrections quoted
- [ ] `_engine/wiki/pillars.md` has 5-7 candidates with recommendation flagged and positioning tension (if any) called out
- [ ] `_engine/wiki/channel-playbook.md` reflects actual follower counts per channel (not assumptions)
- [ ] `_engine/wiki-config.json` lists all downstream readers
- [ ] User explicitly approves pillars before lock (Step 9 gate)

## Learnings & Rules

<!--
Format: [DATE] [CONTEXT] Finding → Action. Keep under 30 lines. Prune quarterly.
See references/feedback-loop.md for protocol.
-->
- [2026-04-18] [Initial build — Digischola] WebFetch returned near-empty for Lovable-hosted digischola.in (~100 chars of body). Chrome MCP `read_page` + `get_page_text` unlocked full nav, 6 services, 3 case studies with metrics, 6 testimonials, partner logos, contact form options. → Rule: for Lovable, GPT-Engineer, Vercel-hosted React SPAs, skip WebFetch and go directly to Chrome MCP. Codified in Step 3 + references/fallback-chain.md.
- [2026-04-18] [Initial build — Digischola] Positioning tension surfaced between site copy (traditional credentials play) and CLI working voice (AI-native operator building MarketingOS). → Rule: when these diverge, propose a positioning BRIDGE in pillars.md rather than forcing a choice. The bridge typically anchors the strongest pillar.
- [2026-04-18] [Initial build — Digischola] Universal voice rule extracted from a single explicit user correction ("no em dashes, make it human", CLI sample #54). → Rule: scan transcripts specifically for "don't", "stop", "no", "not" directives addressed to Claude. These convert to universal rules faster than pattern analysis across 100 samples.
- [2026-04-18] [Initial build — Digischola] Wiki files I generated contained 71 em dashes despite the universal rule they documented. Stripped via sed " — " → ". " + manual touch-ups for rule-demonstration lines and table cells. → Rule: the skill must scan its own wiki outputs for forbidden characters before handing off for approval. Added to Step 8 responsibility (wiki-config validators).
- [2026-04-18] [Location — verified empirically] Tried nesting at `.claude/skills/personal-brand/personal-brand-dna/` for visual grouping with work-capture. Claude Code skill discovery is strictly one level deep under `.claude/skills/`: the skill list did NOT pick up the nested skills. Flattened back to `.claude/skills/personal-brand-dna/` (which resolves via symlink to the `Claude Skills` Git repo). Grouping option kept: rename `work-capture` → `personal-brand-work-capture` for alphabetical clustering with `personal-brand-dna`. → Rule: never nest skills inside subfolders under `.claude/skills/`; use naming prefixes for visual grouping instead.
- [2026-04-29] [STRUCTURAL REFACTOR] Folder convention changed: skill internals (idea-bank.json, brand DNA wiki, _mining, _research, media assets, configs) now live in `Digischola/brand/_engine/` subfolder; daily-workflow folders (queue/, calendars/, performance/, videos/, social-images/) stay at top of `Digischola/brand/`. → Updated all path references in SKILL.md, references/, scripts/, evals/.
