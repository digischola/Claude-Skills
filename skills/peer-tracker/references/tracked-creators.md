# Tracked Creators (15)

The 15 creators peer-tracker refreshes monthly. Sourced from post-writer's initial Perplexity research (2026-04-18). Add / remove via manual edit of this file — peer-tracker reads it as the source of truth for the rotation.

## Pillar 1 — LP Craft / CRO

| Creator | Primary handle | Channels | Pillar | Niche |
|---|---|---|---|---|
| Peep Laja | @peeplaja | LinkedIn, X | LP Craft | B2B messaging strategy, harsh CRO truths |
| Jon MacDonald | @jonmacdonald | LinkedIn, X | LP Craft | E-commerce UX, CRO without discounts |
| Harry Dry | @harrydry | LinkedIn, X, Newsletter (marketingexamples.com) | LP Craft | Bite-sized visual copywriting examples |
| Rishabh Dev | @rishabhdev | LinkedIn | LP Craft | Systematic content ops, B2B growth |
| Julian Shapiro | @julian | X | LP Craft | Reverse-engineering growth tactics, LP psychology |

## Pillar 2 — Solo Freelance Ops

| Creator | Primary handle | Channels | Pillar | Niche |
|---|---|---|---|---|
| Shreya Pattar | @shreya-pattar (LI), @shreyapattar (IG) | LinkedIn, Instagram | Solo Ops | Freelancer economics, Indian operator |
| Varun Mayya | @varunmayya | LinkedIn, X, YouTube | Solo Ops | AI-native operations, Indian tech solo entrepreneurship |
| Dickie Bush | @dickiebush | X | Solo Ops | Ship 30 for 30, writing-as-business |
| Justin Welsh | @justinwelsh | LinkedIn, X | Solo Ops | Solopreneur economics, content systems |
| Jack Butcher | @jackbutcher | X | Solo Ops | Visualize Value, productized service design |
| Joly Tematio | @jolytematio | LinkedIn | Solo Ops | LATAM solo ops, freelance pricing |

## Pillar 3 — Small-Budget Paid Media

| Creator | Primary handle | Channels | Pillar | Niche |
|---|---|---|---|---|
| Barry Hott | @barryhott | LinkedIn, X | Paid Media | DTC + SMB Meta media buying |
| Chase Dimond | @chasedimond | LinkedIn, X | Paid Media | Email marketing + paid media for DTC |
| Cody Plofker | @codyplofker | X, LinkedIn | Paid Media | Performance marketing director / DTC ops |
| Sam Piliero | @sampiliero | LinkedIn, X | Paid Media | DTC + SMB media buyer |

## Per-creator search query templates

Used by `references/refresh-strategy.md` for WebSearch.

```
Generic: "{creator_name}" LinkedIn 2026 best post
LinkedIn-only: site:linkedin.com "{creator_handle}" 2026
X-only: site:x.com OR site:twitter.com "{creator_handle}" 2026
Newsletter (Harry Dry): site:marketingexamples.com 2026
YouTube (Varun Mayya): site:youtube.com "{creator_name}" 2026
```

## Adding / removing creators

To add: append a row to the right pillar's table. peer-tracker picks them up on the next rotation. Add their initial entry to `post-writer/references/creator-study.md` first (Mayank's manual research).

To remove: delete the row + the corresponding section in creator-study.md. Update `data/refresh-log.json` to remove their entry (otherwise rotation logic breaks).

To pause: change Channels column to `paused` — peer-tracker skips paused creators in rotation.

## Quarterly review

Every 3 months, audit:
- Are all 15 still active? (Check `status: silent` flags from refresh-log.)
- Are any pivoted off-pillar? (Drop or replace.)
- Are there new high-signal creators worth adding? (Aim for 5 per pillar, balanced.)
- Are reach numbers still accurate? (Update creator-study.md if creator crossed a major threshold.)

The list shouldn't grow past 18 creators (more = WebSearch/refresh time bloats).
