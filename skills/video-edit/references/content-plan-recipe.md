# Content-Plan Recipe — How to Generate content-plan.json

This is the reference the skill reads (via Claude inside a running session, OR by `content_plan_brain.py` calling the API) to produce a valid content-plan.json from a probe + transcript + brief.

## Required inputs

| Input | Source |
|---|---|
| source-probe.json | from `probe_source.sh` — dims, duration, aspect, silent segments |
| transcript.json | word-level whisper output |
| brand config | `Desktop/<Client>/brand/brand-identity.md` for Digischola; client-specific for others |
| brief | one-line creative direction from the user |
| speaker name + title | from brand config or user-supplied |
| face-bboxes.json | optional, from `analyze_source.py` |

## Output

Valid content-plan.json matching [content-plan-schema.md](content-plan-schema.md). Composition total duration = source duration + 2.3s (1.2s hook + 1.1s payoff tail).

## Director rules (non-negotiable)

1. **Never em dashes** in on-screen text. Use comma or full stop.
2. **UPPERCASE** any CTA, hook title, lower-third primary text.
3. **Hook leads with context, not orphan number.** Bad: "+120%" (no context before voice). Good: "THE 5-SECOND RULE" with subline.
4. **Hero metric** → `metric-hero` beat (full-screen takeover) at its spoken timestamp. Value = integer; prefix/suffix as separate fields.
5. **Captions match transcript word-level.** Do NOT invent timings. Copy word `start`/`end` from transcript exactly.
6. **Emphasis classes per word:**
   - `"metric"` — numbers, percentages, dollar amounts, big integers (Orbitron display font)
   - `"accent"` — verbs/hooks/action words that deserve brand-color emphasis (Space Grotesk uppercase)
   - `"word"` — everything else (Manrope body)
7. **Cutaways at topic words:**
   - "landing page" / "page" / "scrolls" → `broll-landing-page` (duration 2.5-3.5s)
   - "form" / "fields" / "form length" → `broll-form-shrinking` (duration 1.2-1.6s)
8. **Zoom-punch** on face at 2-3 emphasis moments (typically hook setup, CTA, closing question). Default intensity `"subtle"`.
9. **Takeover text** for dramatic beats (e.g. "you've lost them"). Use `accent_danger` color for negative, `success` for positive.
10. **Video-dim** accompanying every `metric-hero` beat (same start, matches duration).
11. **Lower-third** — always start at source-video `clip_start` with duration covering full `clip_duration`. Primary = speaker name UPPERCASE. Secondary = title + brand with `|` marking the highlight split ("FOUNDER · DIGI|SCHOLA").
12. **Payoff** — always included. Starts at source-video end, duration 1.1-1.4s. CTA = action phrase UPPERCASE, wordmark with `|`, url.

## Standard beat ordering

```
hook (0 - 1.2s)
source-video (1.2 - 1.2 + src_dur)
captions for every transcript phrase (1.2 + word_start → word_end)
broll cutaways at topic-matched moments
arrow-callouts on top of B-roll (optional, only if you can pick meaningful points)
takeover-text for dramatic negative/positive beats
video-dim + metric-hero pair at the hero metric moment
zoom-punch beats on face at 2-3 emphasis moments
lower-third (1.2 → source end)
payoff (source end → total end)
```

## Grouping transcript into captions

- Target 3-5 words per caption group
- Break on sentence boundaries (periods, question marks)
- Break on silence gaps > 150ms between words
- Keep metric words + their context in the same group ("lifts conversion by 120%" = one group)
- Give each group a `duration` = (last_word.end - first_word.start) + 0.15s buffer

## Picking the hook

Read the transcript. Identify:
- **Hero claim** — the biggest number or most provocative statement
- **Topic frame** — the category/rule this claim belongs to

Hook's `main` = topic frame in UPPERCASE (not the hero number — save that for the takeover at its spoken moment).
Hook's `sub` = a one-line tease referencing what's about to unfold.

Example from LP Craft Reel:
- Speaker says: "I audited 40 landing pages, most lose visitors in 5 seconds, form length reduction lifts conversion by 120%."
- Hero claim: `+120%`, hero moment: when they say "by 120%"
- Topic frame: the 5-second rule
- ✓ Hook main: "THE 5-SECOND<br/>RULE"
- ✓ Hook sub: "Why 40 wellness landing pages fail"
- ✓ Metric-hero takeover at the "120%" word timestamp, full screen

## B-roll cue picking

For each B-roll beat, set:
- `start` = ~0.2s BEFORE the trigger phrase (B-roll covers speaker while they're about to say the concept)
- `duration` = 2.5-3.0s so viewer reads the mockup
- `scroll_to` = -700 (reduced from default -1400 so hero stays visible; increase only for "scroll through" beats)
- `url` = memorable-looking fake domain matching the client's pillar context (e.g. "acme.co" for generic SaaS, "retreat.co" for wellness)
- `page_title` / `page_copy` = intentionally generic/vague (the point is that most LPs sound like this)

## Arrow callout cue picking

Only add arrow callouts if you can pick meaningful 2D coordinates. Rules:
- `from` = [x, y] on the arrow tail
- `to` = [x, y] where the arrow points (the thing being critiqued)
- `control` = roughly midpoint with slight curve offset
- `label` = 2-3 words UPPERCASE
- `label_pos` = object with `left`, `right`, `top`, `bottom` (pick 2 for position)

Leave out arrows if you can't compute meaningful coordinates. A missing arrow is better than a wrong arrow.

## Composite validation checklist

Before writing the JSON file, self-check:
- [ ] Every `duration` > 0
- [ ] `start + duration` of every beat ≤ `duration_sec` of the plan
- [ ] No two same-track clips overlap (caption-phrase and caption-wordpop both use track 5 — they must not overlap timestamps)
- [ ] Every metric word in the transcript has a corresponding accent/metric class in captions
- [ ] Hook's main text ≤ 30 chars per line (add `<br/>` for multi-line)
- [ ] Lower-third covers full source-video window
- [ ] Payoff starts exactly at source-video end
- [ ] No em dashes anywhere in text fields (scan `main`, `sub`, `label`, `cta`, `text` fields)
- [ ] Total composition duration = source duration + 2.3

## Fallback pattern (if anything's unclear)

Minimum viable plan:
1. Hook with topic frame from brief
2. Source video
3. One caption-phrase per transcript sentence
4. Lower-third for the source window
5. Payoff
6. No B-roll, no metric-hero, no arrows

This always produces a clean subtitled-video output if the brain can't reason about cutaways. Better than nothing.
