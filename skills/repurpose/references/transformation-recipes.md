# Transformation Recipes

9 source → target channel transformations supported in v1. Each recipe specifies: structural shape, length budget, what to preserve from source, what to adapt.

The universal rule across every transformation: **preserve the source hook's core claim and specific numbers**. The wrapper format changes; the substance does not.

---

## Recipe 1: LinkedIn text-post → X thread

**Structure:**
- 5-7 tweets total
- **Tweet 1:** source hook (adapted to <270 chars) + "Here is what..." payoff preview
- **Tweets 2-N:** one point or moment per tweet, one beat at a time
- **Last tweet:** close (insight or question from source, not a CTA)

**Length budget:** 200-270 chars per tweet (validator hard-caps at 280)

**Preservation rules:**
- First 2 tweets together carry the full promise of the source hook
- All specific numbers, client descriptors, dates, tool names preserved verbatim
- No engagement bait, no em dashes, no hype words (validator enforces)

**Adapt:**
- Line-break patterns drop (X ignores multi-line spacing in threads)
- Slightly tighter sentences than LI; active voice dominates
- Shift "Most \"ad problems\" are landing page problems in disguise" style closes to the final tweet

**Anti-patterns:**
- Do not stretch a 900-char LI post into 8 tweets. Use exactly as many tweets as the content requires (usually 5-7).
- Do not repeat the same idea across multiple tweets just to pad.

---

## Recipe 2: LinkedIn text-post → Instagram carousel

**Structure:**
- 7-10 slides
- **Slide 1 (hook):** source hook as large title text (4-8 words of the hook; full hook in caption)
- **Slides 2-3 (context):** setup, 25-40 words per slide
- **Slides 4-N (body):** one point or moment per slide, 20-35 words per slide
- **Last slide (CTA):** soft question or "What is your take?" prompt matching source close

**Visual spec (per brand-identity.md):**
- 4:5 aspect ratio (1080 x 1350 or portrait)
- Black background (#000000)
- Primary text white (#F8FAFC)
- Accent callouts in Primary Blue (#3B9EFF)
- Metric callouts in Success green (#4ADE80)
- Orbitron for hero slide title, Space Grotesk for body headings, Manrope for slide body text

**Caption length:** 150-300 chars, pulling viewers into carousel. First line = hook echo. No hashtag spam (max 3 relevant).

**Preservation rules:**
- Every concrete number gets its own slide (slide 4 = "188% more sales", slide 5 = "37% lower cost per sale")
- Client descriptors preserved per Conservative naming (anonymize unless it's a case-study repost)

**Adapt:**
- LI paragraphs become slide-sized bites
- Whitespace of LI becomes slide breaks
- IG caption is a hook, not a copy-paste of the LI body

---

## Recipe 3: LinkedIn text-post → Instagram Reel script

**Structure:**
- 30-60 second voiceover script
- **Hook (0-1.5 sec):** source hook in first line, spoken or caption-overlaid
- **Payoff preview (1.5-5 sec):** promise what the viewer learns
- **Body (5-45 sec):** 3-5 points, one every 5-8 seconds
- **Close (last 5 sec):** soft insight or question, plus loop cue ("worth the watch again?")

**Visual direction:**
- Jump cuts every 3-5 seconds (platform-specs.md +32% engagement signal)
- Vertical 9:16 (1080 x 1920)
- Brand dark mode + Primary Blue accents
- On-screen text reinforces spoken hook

**Format the output as:**

```
## Voiceover script
[hook line]
[payoff preview]
[body beat 1]
[body beat 2]
...
[close line]

## B-roll notes
0:00-0:03 [visual cue]
0:03-0:06 [visual cue]
...

## On-screen text overlays
0:00 "{hook}"
0:05 "{first key number}"
...
```

**Preservation rules:**
- Hook line is spoken verbatim or overlaid as text
- Specific numbers appear as on-screen text callouts

**Adapt:**
- Long LI paragraphs compress into single-sentence beats
- Conversational spoken-word tone, not formal written

---

## Recipe 4: LinkedIn text-post → WhatsApp Status

**Structure:**
- Single visual + 40-60 word caption
- **Visual:** screenshot of the LI post OR a quote card pulling the hook
- **Caption:** "Today..." framing if posted same day OR "{Day}'s build/insight:" framing

**Length budget:** 200-400 chars caption max

**Preservation rules:**
- The source hook condensed to 1-2 sentences
- Drop specific non-essential numbers (WA audience is warm, they know you)
- Keep the client descriptor only if it's already public

**Adapt:**
- Tone shifts to Register 3 (BTS). "I worked on X today. Saw Y pattern. Fixing Z tomorrow."
- Informal, punctuation is looser, even small typos OK (per voice-guide.md Register 3)

**Example conversion (Thrive LP audit LI post → WA Status):**

```
[screenshot of LI post thumbnail]

Today's drop: a wellness client's LP went from 1.2% to 2.4% conversion in 48 hours.
Three changes. All copy-level.
Full breakdown on LinkedIn (link in bio).
```

---

## Recipe 5: LinkedIn text-post → Facebook post

**Structure:** essentially identical to source LI post, small adjustments for FB reach algorithm.

**Adapt:**
- If source is < 700 chars, expand with 1-2 more context lines (FB rewards longer original content per platform-specs.md)
- Paragraph breaks preserved
- External links OK in post body (FB does not penalize the way LI does)
- Emoji policy: 0 (same as LI per Restrained policy)

**Preservation:**
- Full source content
- Source hook exact

---

## Recipe 6: LinkedIn carousel → X thread

**Structure:**
- 1 tweet per slide if slides ≤ 7
- 1 tweet per 2 slides if slides > 7 (combine slide 4+5 into one tweet)
- Tweet 1 = hook from slide 1
- Final tweet = close from last slide

**Length budget:** standard X thread rules (200-270 chars per tweet)

**Preservation:**
- Slide-level callouts (metrics, quotes, key phrases) survive
- Carousel narrative arc preserved in thread order

**Adapt:**
- Visual-only slides become text descriptors
- Multi-element slides (title + metric + callout) become single-sentence summaries

---

## Recipe 7: LinkedIn carousel → Instagram carousel

**Structure:** mostly 1:1 port with layout adjustments.

**Adapt:**
- LI carousel aspect (1200 x 1500) may be 1:1 square or 4:5 portrait; IG carousel must be 4:5 portrait for feed real estate
- LI's "document" PDF-style polish adapts to IG's more visual + brand-colored style
- Add slide numbers for IG (1/7, 2/7, etc.) — LI doesn't need them, IG users scroll-to-peek
- Caption is 150-300 chars with hook echo

**Preservation:**
- Slide order, text content, metrics, structure

---

## Recipe 8: X thread → LinkedIn text-post

**Structure:**
- Source thread → single LI post
- Combine tweets into paragraphs with whitespace
- **Expand hook:** 1 tweet of ~240 chars becomes 2-3 lines opening LI post
- **Body:** each tweet becomes a paragraph. Short paragraphs (1-2 sentences).
- **Close:** final tweet becomes close question

**Length budget:** 1200-1800 chars total (LI sweet spot)

**Preservation:**
- All numbers, quotes, insights from thread
- Thread's narrative arc

**Adapt:**
- Add 1-2 connector sentences that weren't needed on X (threads have implicit flow; LI needs slightly more hand-holding)
- Each tweet becomes a paragraph with 1-2 blank lines around it

---

## Recipe 9: X single tweet → LinkedIn text-post

**Structure:**
- Original tweet text becomes the hook (lines 1-2)
- Expand with 2-3 paragraphs of context, example, or implication
- Close with a question or observation

**Length budget:** 800-1400 chars (LI sweet spot on shorter end since source was compact)

**Preservation:**
- Exact tweet text as hook where possible

**Adapt:**
- Add a real example or concrete scenario
- Add the "so what" implication the tweet leaves implied

---

## Default channel selection when user does not specify

Given a source channel, the default targets are all channels NOT in the source:

| Source channel | Default targets |
|---|---|
| LinkedIn text-post | X thread, Instagram carousel, Instagram Reel, WhatsApp Status, Facebook |
| LinkedIn carousel | X thread, Instagram carousel |
| X single tweet | LinkedIn, Instagram caption |
| X thread | LinkedIn, Instagram carousel |
| Instagram carousel | LinkedIn carousel, X thread |
| WhatsApp Status | (rare source; leave to user discretion) |

The user can override with explicit target list.

## What NOT to do

- **Never translate to a channel that does not match brand policy.** WhatsApp is dark in Phase 1 (weeks 1-6). If today is Phase 1 and target is WA, warn the user and skip unless they override.
- **Never copy-paste.** Every variant must actually use the recipe's structural transformation. If the source and target are nearly identical (like LI → FB), still normalize for the channel.
- **Never strip the hook's specific anchors.** Numbers, client descriptors, tool names stay.
- **Never lose the source voice register.** LI Strategist voice stays strategist across variants. WA Status drops to BTS because the format demands it, not because we lose the voice.
