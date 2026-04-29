# Perplexity Prompt Templates (Mode 2 — Deep Research)

Used when WebSearch isn't deep enough. User runs Perplexity manually with these prompts and pastes responses back. Triggered via `scripts/trend_research.py prompt`.

## Template — Pillar 1 (Landing-Page Conversion Craft)

```
Research the most discussed landing-page conversion trends of the LAST 14 DAYS in the digital marketing community. Focus on these niches: wellness retreats, yoga / spiritual centers, hospitality, B2B SaaS lead-gen, e-commerce.

For each of the top 5 trending topics, return EXACTLY this structure:

## Topic [N] — [short name]
- **What it is**: 2-3 sentence factual summary
- **Why it's trending**: 1 sentence (e.g., new study released, viral post, controversial take)
- **Quantitative insight**: 1 stat or benchmark with source URL (no fabricated stats — only cite sources you can verify)
- **Top expert post / source**: URL + author name + 1-line summary
- **Contrarian take (if any)**: 1-2 sentences with source
- **Pillar fit**: 1 sentence on why this fits "Landing-Page Conversion Craft" for an Indian solo freelancer serving wellness/spiritual/hospitality/B2B clients
- **Suggested hook angle for Mayank** (Digischola, Indian Ex-Google freelancer): 1 line in his voice — operator, data-led, no em dashes, no hype words like "unlock" or "revolutionize"

EXCLUDE: WordPress plugin reviews, AMP / instant pages, generic "improve your website" listicles, anything older than 14 days.

ONLY include topics with at least 1 verifiable URL.
```

## Template — Pillar 2 (Solo Freelance Ops)

```
Research the most discussed solo-freelancer-marketing-operator trends of the LAST 14 DAYS. Focus on these niches: indie freelancers running marketing for clients, AI-augmented solo agencies (using Claude / Cursor / etc.), pricing models for productized services, India-based or LATAM-based global freelancers competing with US/EU agencies.

For each of the top 5 trending topics, return EXACTLY this structure:

## Topic [N] — [short name]
- **What it is**: 2-3 sentence factual summary
- **Why it's trending**: 1 sentence
- **Quantitative insight**: 1 stat or benchmark with source URL (verified only)
- **Top expert post / source**: URL + author + 1-line summary
- **Contrarian take (if any)**: 1-2 sentences with source
- **Pillar fit**: 1 sentence on why this fits "Solo Freelance Ops" for a Gurugram-based Ex-Google operator running Meta + Google Ads for global wellness/hospitality/B2B clients
- **Suggested hook angle for Mayank** (his voice: operator, honest economics, AI-as-theme not product, no em dashes, no hype): 1 line

EXCLUDE: crypto / web3 freelance, cold-email-only tactics, "passive income" framings, anything older than 14 days.

ONLY include topics with at least 1 verifiable URL.
```

## Template — Pillar 3 (Small-Budget Paid Media)

```
Research the most discussed small-budget paid-media trends of the LAST 14 DAYS. Focus on these niches: $10-$50/day Meta + Google Ads campaigns, SMB account structure, creative testing on tight budgets, retargeting on small lists, attribution for SMB.

For each of the top 5 trending topics, return EXACTLY this structure:

## Topic [N] — [short name]
- **What it is**: 2-3 sentence factual summary
- **Why it's trending**: 1 sentence
- **Quantitative insight**: 1 stat or benchmark with source URL (verified only)
- **Top expert post / source**: URL + author + 1-line summary
- **Contrarian take (if any)**: 1-2 sentences with source
- **Pillar fit**: 1 sentence on why this fits "Small-Budget Paid Media" for a Gurugram-based Ex-Google freelancer managing $10-50/day Meta + Google Ads for global wellness/hospitality/B2B SMB clients
- **Suggested hook angle for Mayank** (his voice: operator, performance-credibility, $1B+ managed, AI-as-theme, no em dashes, no hype): 1 line

EXCLUDE: "$5/day get rich" hype, TikTok Shop tactics, "scaling to 7 figures" framings, anything older than 14 days.

ONLY include topics with at least 1 verifiable URL.
```

## Ingestion of Perplexity response

After Mayank pastes the response into `brand/_engine/_research/trends/<week>/<pillar>-response.md`, run:

```bash
python3 scripts/trend_research.py ingest-perplexity \
  --pillar lp-craft \
  --week 2026-W17
```

The script:
1. Reads the response file
2. Splits on `## Topic [N]` headers
3. Parses each topic into the candidate schema (seed, hook_candidate, source_urls, etc.)
4. Sets `relevance_score` based on whether the response includes a "Suggested hook angle" + URL count (3+ URLs → 5, 1-2 URLs → 4, no URLs but pillar-fit → 3)
5. Dedupes against existing idea-bank
6. Appends survivors to `_engine/idea-bank.json`
7. Logs to `brand/_engine/_research/trends/<week>/scan-log.md`

## When to use Mode 2 vs Mode 1

| Situation | Mode |
|---|---|
| Weekly Sunday cadence | 1 (autonomous) |
| Launching a new pillar focus | 2 (deep) |
| Preparing a quarterly content theme | 2 |
| Planning a case-study series | 2 |
| Mayank wants a "deep dive" before drafting big posts | 2 |

Mode 2 takes ~15 min of Mayank's attention (3 Perplexity round-trips + paste-back). Mode 1 takes 0 min (Claude does everything).
