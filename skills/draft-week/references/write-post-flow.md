# write-post-flow

Detailed steps for `draft-week write-post`. Loaded only when drafting one post.

## Inputs

1. **Entry ID** — UUID from `idea-bank.json`.
2. **Channel + format** — e.g., `linkedin-text-post`, `x-thread`, `instagram-carousel`.
3. **Optional**: voice framework override, credential override, target audience (global / US / AU / SG / IN).

## Step 1: Load entry + match slot

Load entry by ID. If a calendar file for the current week has a slot for this entry, pull `scheduled_at`, `voice_framework`, `credential_anchor_candidate` from there. Otherwise pick defaults per the routing table below.

## Step 2: Channel routing

Map `channel` + `format` to char limit key in `platform-specs.md`:

| Channel-format key | Hard cap | Sweet spot | Hook fold |
|---|---|---|---|
| linkedin-text-post | 3000 | 1200-1800 | 210 |
| linkedin-carousel-slide | 250 | 100-200 | — |
| linkedin-carousel-caption | 1500 | 300-800 | — |
| x-tweet | 280 | 240-280 | — |
| x-thread-tweet | 280 (each) | 200-270 | — |
| instagram-caption | 2200 | 150-400 | 125 |
| instagram-reel-caption | 2200 | 60-150 | — |
| facebook-post | 5000 | 400-1000 | — |
| whatsapp-status | 700 | 50-300 | — |

## Step 3: Voice framework selection (auto-pick by entry type)

| Entry type | Default framework |
|---|---|
| client-win | Hormozi (Value Equation) |
| insight (LP audit) | Dickie Bush 3x3 |
| insight (general) | Naval (Compression) for X, Graham (Plain English) for LI |
| experiment | Graham |
| failure | Schafer (Conversational vulnerability) |
| build-log | Naval for X, Graham for LI |
| client-comm | Schafer |
| observation | Naval (X), Graham (LI) |
| trend | Graham |
| peer-pattern | (do not draft directly — feeds hook selection) |

Full framework rules in `voice-frameworks.md`.

## Step 4: Hook generation (3 candidates A/B/C)

Pull from `references/hook-library.md` + `brand/references/hooks.json`. Pick 3 patterns from DIFFERENT categories that fit the entry type. Each ≤210 chars for LinkedIn, tighter for X.

Adapt the formula to specific entry content. Show A/B/C labeled options. Wait for user pick before drafting body.

If running in a non-interactive ritual (cron-driven), pick option A (highest confidence).

## Step 5: Body draft

Apply in order:
1. **Structure template** from `platform-specs.md` (e.g., LI-text 7-block template).
2. **Voice framework** rules.
3. **Credential anchoring** per `credential-anchoring.md` — check `credential-usage-log.json`, pick unused credential within 30 days, apply 1 of 5 anchor types.
4. **AI-theme weaving** per `ai-integration.md` — if entry mentions Claude / Perplexity / Higgsfield / etc., name the tool + quantify time saved.
5. **Regional tone** per `regional-nuances.md` — default Confident Pragmatism + USD; tailor only if `target_audience` specified.

## Step 6: Save with frontmatter

Filename: `brand/queue/pending-approval/YYYY-MM-DD-<entry_id>-<channel>-<format>.md`

Frontmatter (see `frontmatter-spec.md`):

```yaml
---
channel: linkedin
format: text-post
entry_id: 3a3c9bac
pillar: Landing-Page Conversion Craft
voice_framework: Graham (Plain English)
hook_pattern: 'Category 1 #4 (counterintuitive benchmark anchored)'
credential_anchored: thrive_188
ai_theme_applied: false
status: drafted
validator_status: pending
posting_status: scheduled
scheduled_at: '2026-05-04T09:00:00+05:30'
scheduled_day: Monday
repurpose_source: null
repurposed_into: []
---
```

## Step 7: Validate

```bash
python3 scripts/validate_post.py <draft-path>
```

- Exit 0 → mark `validator_status: clean (NNN chars, exit 0)`.
- Exit 1 → list warnings, mark `validator_status: warnings (NNN chars, exit 1)`. Ship OK.
- Exit 2 → BLOCK. Edit the body, re-run validator. Never ship a draft with exit 2.

## Step 8: Update credential-usage-log

If a credential was anchored, append the entry ID + date to `brand/_engine/credential-usage-log.json`.

## Anti-patterns

- Do NOT use em dashes. Use periods, line breaks, or "—" replaced with " - " or new line.
- Do NOT use hype words (unlock, revolutionize, game-changer, etc.).
- Do NOT use engagement bait (comment yes, follow for more, tag a friend, etc.).
- Do NOT exceed channel char limits.
- Do NOT invent metrics. If a number is fuzzy, leave it out.
- Do NOT credential-anchor every post. Cadence is 1-2/week, not every post.
