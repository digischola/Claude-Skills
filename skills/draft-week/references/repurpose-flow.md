# repurpose-flow

Detailed steps for `draft-week repurpose`. Loaded only when adapting a draft for other channels.

## Source-target pairs

| Source | Target |
|---|---|
| LinkedIn-text-post | X-thread, IG-carousel, IG-Reel-script, FB-post, WA-status |
| X-thread | LinkedIn-text-post, IG-carousel |
| LinkedIn-carousel | X-thread, IG-carousel, FB-post |
| Case-study LI carousel | X-thread, blog excerpt, IG-carousel |

## Hard rules

- **Preserve the source hook verbatim.** The first 1-2 lines of the source are the hook. Use them word-for-word in the target. Adapt only what comes after.
- **Preserve credentials and metrics verbatim.** Don't paraphrase numbers.
- **Validate per target.** Run `validate_post.py --channel <target-key>` on each variant.

## Adaptation patterns

### LI-text → X-thread

- Hook becomes Tweet 1 (≤270 chars).
- Body sections become Tweets 2-N (200-270 chars each).
- Add a closer Tweet with the same CTA as the source.
- Total 5-12 tweets.
- Use `## Tweet 1`, `## Tweet 2` ... section headers (validator expects them).

### LI-text → IG-carousel

- Hook becomes Slide 1 cover (≤250 chars, big text).
- Each body section becomes one slide (≤250 chars).
- Add a final CTA slide.
- 6-10 slides.
- Caption gets a 150-300 char teaser + same hook + light hashtag pack.

### LI-text → IG-Reel-script

- Hook becomes 0-3s on-screen text + opening line.
- Body distilled to 5-8 spoken lines, 30-45 seconds total.
- Visual cues per line written in `[brackets]`.
- Caption ≤150 chars.

### LI-text → WA-status

- Hook + 1-2 punchy lines. Total ≤300 chars.
- Tracking via the Status format (no link, just text + maybe an image).

### LI-text → FB-post

- Hook + body, slightly looser tone (FB tolerates more lines and emoji-light).
- 400-1000 char sweet spot.

### X-thread → LI-text-post

- Combine all tweets into one narrative. Add transitions.
- Rewrite into the LI 7-block structure: hook, context, framework, example, contrast, lesson, CTA.
- 1200-1800 char sweet spot.

## Frontmatter

Each variant must set:

```yaml
repurpose_source: <source-filename>.md
repurposed_into: []  # empty in the variant
```

The SOURCE draft also gets updated:

```yaml
repurposed_into:
  - <variant-1-filename>.md
  - <variant-2-filename>.md
```

## Step-by-step

1. Load source draft (must exist in `pending-approval/` or `published/`).
2. Extract the hook (first 1-2 non-empty lines of body) and the metrics block.
3. For each target channel, run the matching adaptation pattern.
4. Save target as `YYYY-MM-DD-<entry_id>-<target-channel>-<format>-repurpose.md`.
5. Run `validate_post.py` on each.
6. Update source frontmatter `repurposed_into:` list.

## Anti-patterns

- Do NOT change the hook — that defeats the cross-channel coherence the algorithm rewards.
- Do NOT post the same exact body verbatim to two channels — algorithms penalize duplicate detection.
- Do NOT repurpose a draft that hasn't passed validate_post.py exit 0/1 yet.
- Do NOT auto-schedule repurposed variants on the same day as the source — space them 1-3 days apart.
