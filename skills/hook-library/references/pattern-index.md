# Pattern Index — 8 Categories

Overview of the 35+ hook patterns organized by category. The full machine-readable catalog is in `data/hooks.json` (after `sync-from-post-writer`). This file is a human-friendly index.

## Category 1 — Curiosity / Open-Loop (4 patterns)

Creates cognitive tension. Reader must click "See more" or expand to resolve.

- **What-If Reframe** — "What if I told you [common belief] is completely wrong?"
- **Stopped-Doing Confession** — "I stopped [common practice]. My [metric] finally started landing."
- **Single-Shift Realization** — "One [specific thing] completely shifted how I think about [topic]."
- **Hidden-Reason Diagnosis** — "The hidden reason your [asset] is failing."

**Best for:** Counterintuitive insights, LP audits, AI-workflow posts, diagnosis posts.

## Category 2 — Counterintuitive / Contrarian (4 patterns)

Contradicts common belief. Triggers debate (essential for X's 30-min velocity window).

- **Wrong-Advice Reset** — "[Common advice] is wrong. Here is what actually works:"
- **Stop-Trying-To Reframe** — "Stop trying to [common goal]. Seriously."
- **Best-Pros-Avoid Inversion** — "The best [professionals] I know barely use [common tool]."
- **Overrated-Reframe** — "[Common practice] is highly overrated. Focus on [alternative] instead."

**Best for:** X (debate-sparking), strategy reframes, freelance-ops contrarian takes.

## Category 3 — Data / Metric-Before-Context (4 patterns)

Specific numbers lead. Instant credibility.

- **Numbers Hero** — "[Metric] more [outcome]. Here is what I changed."
- **Single-Lever Result** — "[Metric] increase. From one [small change]. Here is what I did."
- **Small-Budget Hero** — "How a [$small budget] generated [specific outcome] in [timeframe]."
- **Inbound-Zero-Outreach** — "[Number] inbound leads. Zero outreach. Here is the system."

**Best for:** Case studies (LI carousel especially), small-budget paid media, funnel/solo ops posts.

## Category 4 — Story / Moment-in-Time (4 patterns)

Past-tense narrative. Humans resolve tension.

- **Setting-In-Place Open** — "I was sitting in [place], staring at [problem]."
- **Call-Duration Reveal** — "The call lasted [duration]. I knew by minute [number] it was over."
- **Quick-Task-Bigger-Outcome** — "It was supposed to be a quick [task]. It turned into [bigger outcome]."
- **Notification-Pivot** — "The [notification] came through at [time]. Everything changed."

**Best for:** Long-form LinkedIn lessons, client craft stories, scope-creep narratives.

## Category 5 — Question (4 patterns)

Invites participation. Drives long-form comments.

- **Worst-Advice Solicit** — "What is the worst [industry] advice you have ever received?"
- **Role-Wish-You-Knew** — "[Role]: What do you wish you knew before [milestone]?"
- **Have-You-Noticed Open** — "Have you ever noticed that [observation]?"
- **Best-Practice-Abandoned** — "What is a best practice in [field] that you abandoned?"

**Best for:** Community engagement on LinkedIn, peer debate on X.

## Category 6 — List / Framework (4 patterns)

Scannable. Screams utility.

- **Things-I-Would-Differently** — "[Number] things I would do differently if I were starting today."
- **Common-Mistakes-Fix** — "[Number] [niche] mistakes I see every week (and how to fix them)."
- **N-Step-Framework** — "A [number]-step framework to achieve [outcome]."
- **Lessons-From-High-Volume** — "[Number] lessons from [high-volume experience]."

**Best for:** LI carousels, frameworks, AI workflow posts, credentials + value combo.

## Category 7 — Personal Stake / Vulnerable (4 patterns)

(See post-writer's hook-library.md for detail; populated via sync.)

**Best for:** Trust-building, founder-voice posts, Indian operator perspective.

## Category 8 — Authority / Credentials-Forward (variable, ~4-7 patterns)

(See post-writer's hook-library.md for detail.)

**Best for:** Establishing performance-credibility, ex-Google + $1B+ managed framing.

## Total

**35-40 patterns** depending on what's currently in post-writer's reference. Run `python3 scripts/hook_lib.py stats` for the live count per category + tier.

## How to query

```bash
# All patterns in a category
python3 scripts/hook_lib.py list --category contrarian

# Tier 1 patterns for a specific pillar+channel
python3 scripts/hook_lib.py list --tier 1 --pillar lp-craft --channel linkedin

# Patterns matching a keyword
python3 scripts/hook_lib.py search "framework"

# Full details on one
python3 scripts/hook_lib.py get numbers-hero
```
