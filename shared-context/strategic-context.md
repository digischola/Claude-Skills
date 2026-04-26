# Strategic Context — Mayank Verma

Read this file at the start of any session involving business planning, growth strategy, client work, or skill roadmap decisions.

Last updated: 2026-04-16

---

## Current Clients & Revenue

- **Thrive Retreat** (Kingscliff, NSW, Australia) — Meta Ads management, ~AUD $2,000/month
- **Happy Buddha Retreat** (Australia) — Meta Ads management, ~AUD $1,400/month
- **ISKM / Sri Krishna Mandir** (Singapore) — Meta Ads, SGD $500/month
- **Salt Air Cinema** (Australia) — Agency subcontract, AUD $10/hr, ~8-10 hrs/month
- **Living Flow Yoga Ashfield** (Inner West Sydney, NSW) — Onboarded 2026-04-25. Google Ads only. AUD $300/month. Two-campaign brief, split into multi-program structure: (1) **Local Studio - Inner West Sydney** ($150/mo; LAUNCH-READY pending Mayank's GA4 + conversion-event setup), (2) **Live-stream AU-wide** ($150/mo; LAUNCHING WITH KNOWN STRUCTURAL LOSS as research spend per client decision 2026-04-26). Natalie Ristoski, 7 teachers, MindBody booking. **Trust signal correction (2026-04-25):** real GBP shows 67 Google reviews + 1,235 MindBody votes + 21 Facebook votes (NOT 1,235 Google reviews as Perplexity initially misattributed). Combined trust profile is competitive-not-dominant. Cross-link: Winter Cocoon Retreat hosted at Thrive Retreats venue (existing client). Files at `Desktop/Yoga Ashfield/` (multi-program). Full pipeline complete 2026-04-26: business-analysis → market-research (with keyword data) → landing-page-builder → landing-page-audit → paid-media-strategy → ad-copywriter → campaign-setup. **Both campaigns ship against `/pricing/`** (existing page) per client decision; dedicated LPs (Local Studio LP built but not deployed; Live-stream LP not built) become Phase 2 optimization recommendations. **Live-stream has hard 14-day CPA-$80 kill gate** documented in launch runbook. Pre-launch blockers (Mayank): GA4 install + Google Ads conversion event wired to MindBody return.
- **Gargi** — Pre-sales phase, not yet active

FY25-26 total revenue: ~27 lakh INR
Primary income: wellness/retreat niche (Thrive + Happy Buddha = ~65% of revenue)

## Capacity

15-20 hours/week available for client + system work.

## Upwork Profile

- URL: https://www.upwork.com/freelancers/~01b5666cac54b34dfd
- 100% Job Success Score
- Rate: $50/hr
- Background: Total 10+ Yr Experience, Ex-Google (4 years), Ex-Accenture (3 years), MBA(Marketing) - Symbiosis, B.Tech(Computer Science) - BIT Mesra
- Strongest niche signal: wellness/retreats

## Pain Points (from deep interview, April 2026)

1. **Iteration loop** — spends excessive time iterating AI outputs instead of shipping
2. **Post-launch confidence** — no systematic framework for optimization decisions after campaigns go live
3. **Time allocation** — 60%+ time building tools/systems vs earning from clients
4. **Quality inconsistency** — output quality varies without standardized processes

## Skills Built So Far

- **business-analysis** — Fully built. Crawl + WebFetch + brand extraction + digital presence + offerings. Visual verification gate for VISUAL_EDITOR_SITE anomalies. MONOCHROMATIC_SITE anomaly type. Location: `Desktop/.claude/skills/business-analysis/`
- **market-research** — 10/10, fully built with wiki pattern, 23-check validator, lint script, evals, meta-interest-database (329 interests). Mandatory wiki context injection (booking model). Both-platforms Perplexity prompt variant. Location: `Desktop/.claude/skills/market-research/`
- **paid-media-strategy** — 9/10. Battle-tested on Retreat House (2026-04-12). 7-step process: wiki check → guided questions → platform strategy → report → dashboard → creative brief JSON → CSV → wiki update. 3 dashboard templates (single, dual-simultaneous, dual-phased). Brand-config gate for dashboard styling. Creative brief outputs: visual direction with AI image gen prompts, landing page mapping, A/B testing plan, proof element hierarchy. Cross-file consistency validator. Location: `Desktop/.claude/skills/paid-media-strategy/`
- **ad-copywriter** — Battle-tested on Retreat House (2026-04-13). 8-step process: input check → guided questions (standalone) → load specs → generate copy → platform CSVs → image prompts → video storyboards → validate & wiki. Dual mode (downstream from creative brief or standalone). 5 reference files, validator with cross-file consistency, 5 evals. Outputs: ad copy report, Google CSV, Meta CSV, image prompts (Gemini), video storyboards (AI Studio VO). Location: `Desktop/.claude/skills/ad-copywriter/`
- **post-launch-optimization** — Built (2026-04-16). 11-layer analysis engine: health check, diagnosis, prescription, creative intelligence, testing framework, competitive context, benchmarking, cross-platform, trend analysis, action prioritization, session memory. Data via Windsor.ai MCP (direct API — no CSV exports). Outputs: optimization report (.md) + HTML dashboard per client. Fire check mode for quick scans. Connected accounts: Thrive (Meta), ISKM (Meta), Happy Buddha (Google), Thrive (Google). Location: `Desktop/.claude/skills/post-launch-optimization/`
- **landing-page-audit** — Built. CRO + UI/UX + persuasion/copy audit. Scores and priority-ranked recommendations.
- **landing-page-builder** — Built (2026-04-16). 7-step process: mode detection → page type classification → copy generation → HTML prototype → page spec JSON → wiki update → validate. 4 page types (retreat booking, workshop event, lead gen, teacher training). Dual mode (standalone or downstream from creative brief/audit). 2 research reference files (landing-page-research.md from 99 sources, copy-frameworks.md from 53 sources), validator, 5 evals. Outputs: HTML prototype + page-spec JSON for Lovable rebuild. Location: `Desktop/.claude/skills/landing-page-builder/`
- **campaign-setup** — Built + battle-tested on Retreat House (2026-04-16). 9-step process: upstream input check → context load → intake (AskUserQuestion for account IDs, conversion names, existing audiences, UTM template, exclusions, schedule, extensions content) → Google Ads Editor CSVs (8 files: campaigns, ad groups, keywords, RSAs, sitelinks, callouts, snippets, negatives) → Meta Ads Manager bulk import (single CSV + creative manifest + manual-build blueprint fallback) → pre-launch checklist (phase-gated sign-offs) → launch runbook (T-24h prep + phased monitoring) → validate → wiki + downstream flag. No third-party MCP or write-API dependency — pure bulk-import files the user uploads via official UIs. 4 reference files (google-ads-editor-schema, meta-bulk-import-schema, pre-launch-checklist-template, launch-runbook-template, skill-coordination, feedback-loop), validator (enforces char limits, placeholder tokens, orphan refs, URL format, duplicates, pinning constraints, min-count rules, schema columns; Meta Body treated as SOFT limit — truncation warning not CRITICAL), 5 evals. Location: `Desktop/.claude/skills/campaign-setup/`

## Creative Production Workflow

- **Images:** Generated via Gemini (AI image generation). Creative brief JSON contains `image_gen_prompt_prefix` per campaign for brand-consistent prompts.
- **Videos:** No automated pipeline yet. Planned: generate key frames via AI → animate with Runway/Kling → stitch in CapCut.
- **Landing pages:** Claude generates HTML prototypes → client approval → rebuild in Lovable → deploy to Netlify. NOT Vercel.
- **Design tool:** Canva MCP connected for branded design generation.
- **Key principle:** Everything is AI-managed. No manual design work except final production in Lovable.

## Client Projects in Progress

- **Thrive Retreats** — post-launch-optimization Analysis #1 (baseline) completed (2026-04-16). Windsor.ai MCP connected for both Meta + Google. Baselines: Meta CPA $122.66, Google CPA $123.42, Blended ROAS 3.93x. Key flags: Teacher Training frequency 3.57, Emily creative dependency, Google CVR 1.2%. Files at: `Desktop/Thrive Retreat/Thrive Retreat/`

_Note: Test and one-off project folders (Gwinganna, Magic Receipt, Retreat House, Sri Krishna Mandir, CrownTech) were cleaned up on 2026-04-16. Rerun the relevant skills if any of them come back as active work — the wiki compounds from scratch so nothing is permanently lost._

## Roadmap

**Next skill to build:** Reporting pipeline (Looker Studio templates) OR 2026 growth plan + Upwork positioning strategy — priority TBD.

**Future skills (priority order TBD):**
- Reporting pipeline (Looker Studio templates)
- 2026 growth plan + Upwork positioning strategy
- Client QBR / performance review automation

## 2026 Growth Targets

TBD — to be defined in upcoming planning session.

## Strategic Shifts Logged

- **[2026-04-22] Loomer Meta-ad-shutdown rule — locked across both tracks.** Jon Loomer published 2026-03-19 "AI-Related Ad Account Shutdowns, Meta AI Chat, and More" reporting advertisers (Naman Bansal lost 17 accounts) getting Meta ad accounts shut down for connecting to AI agents through third-party connectors. Mechanism per Loomer: Meta's detection flags large API-call volume from AI tools as automated abuse. **Rule locked for client-skills track:** All Windsor.ai pulls from Claude are READ-ONLY. Never issue write operations to Meta Ads Manager via any MCP. `post-launch-optimization` was already structured this way (outputs reports, not API mutations); rule is now explicit and must not be relaxed even if "safe MCP" products (e.g., Madgicx) come to market — only relax after independent verification the product doesn't trip Meta's detection. When a client ad account receives a Business Manager warning about unusual API activity, pause Windsor pulls for that account and fall back to CSV export for the analysis cycle. Same rule mirrored in the personal-brand track for Digischola organic FB + IG via `performance-review`. **Client risk exposure:** ISKM SG + Thrive Retreats Meta ad accounts are revenue-critical (currently connected on Windsor for post-launch-optimization pulls); a Meta shutdown would cascade to those client relationships. Mitigation: we're already read-only, so the risk surface is Windsor's own relationship with Meta (out of our control but Windsor has strong incentive to comply with Meta's terms).
