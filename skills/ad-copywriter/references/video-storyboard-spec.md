# Video Storyboard Specification

Load this file in Step 7 of the ad-copywriter skill. Defines frame structure, duration templates, voiceover scripting rules, and hook patterns.

## Storyboard Structure

Each video ad gets one storyboard. Each storyboard contains:
1. **Video metadata** — format, duration, platform, aspect ratio, AIDA mapping
2. **Frame-by-frame breakdown** — 4-6 frames per video
3. **Combined VO script** — one continuous text block for pasting into AI Studio

## Frame Template (5 Layers)

Every frame must include ALL 5 layers:

```
### Frame [N] — [AIDA stage] ([timestamp])

**Visual:** [Gemini image prompt for this frame — full prompt including prefix]
**Motion:** [Camera/animation direction for video tool]
**Text Overlay:** [Copy that appears on screen — short, punchy, ≤ 8 words]
**Voiceover:** [Clean script for AI voice — see VO rules below]
**Voice Direction:** [Tone/pace note for voice model selection — separate from VO text]
**Music:** [Mood/energy level — e.g., "ambient, building energy" or "upbeat, confident"]
```

### Layer Details

**Visual:** Full Gemini image prompt following image-prompt-patterns.md structure. This is the key frame that will be generated as an image, then animated. Include the campaign's `image_gen_prompt_prefix`.

**Motion:** Direction for animation/video tool (Runway, Kling, etc.):
- `slow zoom in` — builds intimacy, draws viewer in
- `slow zoom out` — reveals scope, establishes environment
- `pan left/right` — shows breadth, follows action
- `static with parallax` — subtle depth movement, premium feel
- `slow tilt up` — reveals scale, creates awe
- `tracking shot` — follows subject movement
- `crossfade from previous` — smooth transition between scenes

**Text Overlay:** On-screen text that reinforces or replaces VO for sound-off viewing. Rules:
- Maximum 8 words per frame
- Use brand font style from creative brief
- Numbers stay numeric (e.g., "$74K" not "seventy-four thousand")
- Contrasts with visual (white text on dark, dark text on light)
- Position: top or bottom safe zone

**Voiceover:** See VO Scripting Rules section below.

**Voice Direction:** NOT part of the VO text — this is metadata for voice model selection:
- Tone: warm, authoritative, conversational, energetic, calm
- Pace: slow and measured, natural, upbeat
- Example: "Warm, conversational, slight pause before the CTA"

**Music:** Energy progression through the video:
- Frame 1: ambient/low energy (don't compete with hook)
- Middle frames: building/moderate
- Final frame: peak energy or resolved/warm

## Duration Templates

### 6-Second Bumper (YouTube, Meta Stories)

| Frame | AIDA | Duration | Purpose |
|---|---|---|---|
| 1 | Attention | 0-2s | Hook — single strong visual + text |
| 2 | Interest + Desire | 2-4s | Core value prop |
| 3 | Action | 4-6s | Brand + CTA |

3 frames. No voiceover (too short for VO to land). Text overlay carries all messaging.

### 15-Second Ad (Meta Feed/Reels, YouTube Pre-Roll)

| Frame | AIDA | Duration | Purpose |
|---|---|---|---|
| 1 | Attention | 0-3s | Hook — pattern interrupt |
| 2 | Interest | 3-7s | Key feature/benefit |
| 3 | Desire | 7-11s | Proof/transformation |
| 4 | Action | 11-15s | CTA + brand |

4 frames. VO works but must be tight — ~35-40 words total.

### 30-Second Ad (YouTube, Meta In-Stream)

| Frame | AIDA | Duration | Purpose |
|---|---|---|---|
| 1 | Attention | 0-5s | Hook — establish problem or aspiration |
| 2 | Interest | 5-12s | Develop the story, show features |
| 3 | Interest/Desire | 12-18s | Deepen — more proof, more detail |
| 4 | Desire | 18-24s | Transformation/social proof moment |
| 5 | Action | 24-30s | CTA + brand + urgency |

5 frames. VO has room to breathe — ~70-80 words total.

## Voiceover Scripting Rules (Critical)

The VO text will be pasted directly into an AI voice tool (Google AI Studio, ElevenLabs, etc.). It must be **clean text only**.

### DO
- Write natural, conversational sentences
- Use contractions (you're, it's, don't, we've)
- Keep sentences short (8-15 words ideal)
- Write numbers as words in VO ("seventy-four thousand dollars" not "$74K")
- Use punctuation for pacing: periods for full stops, commas for brief pauses, em-dashes for emphasis pauses
- End with a clear, spoken CTA ("Visit retreat house dot com dot au to book your site assessment")
- Spell out URLs phonetically ("retreat house dot com dot ay you")

### DO NOT
- No parentheticals: ~~(pause)~~ ~~(enthusiastically)~~ ~~(read slowly)~~
- No stage directions: ~~[EMPHASIS]~~ ~~[Beat]~~ ~~[Softly]~~
- No reading instructions: ~~"Read with warmth"~~ ~~"Say this part slowly"~~
- No ALL CAPS for emphasis (AI voice tools can't interpret caps as volume)
- No sound effects written out: ~~"[SFX: whoosh]"~~
- No pronunciation guides inline: ~~"Ananda (ah-NAN-da)"~~

All tone/pace/emphasis guidance goes in the **Voice Direction** layer, NOT in the VO text.

### VO Word Count Guide

| Duration | VO Words | Pace |
|---|---|---|
| 6s bumper | 0 (text only) | N/A |
| 15s | 35-40 words | ~2.5 words/sec |
| 30s | 70-80 words | ~2.5 words/sec |
| 60s | 140-155 words | ~2.5 words/sec |

## Hook Patterns (Frame 1)

Frame 1 must stop the scroll. These hook patterns work for different campaign types:

### Question Hook
"What if your backyard could earn seventy-four thousand dollars a year?"
Best for: problem-solving products, ROI angles

### Contrast Hook
"You spend fifty weeks working — and two weeks pretending to rest."
Best for: transformation/wellness, BAB framework

### Stat Hook
"Eighty-nine percent of remote workers say they'd pay more for a dedicated home office."
Best for: data-driven audiences, B2B

### Visual Surprise Hook
[No VO — striking visual does the work. Text overlay only.]
Best for: 6s bumpers, architecture/design products, food/fashion

### Authority Hook
"Featured in Dezeen, the world's most popular architecture magazine."
Best for: premium products, authority-driven audiences

### Outcome Hook
"In seven days, ninety-four percent of our guests report lasting calm."
Best for: wellness, coaching, education — proof of transformation

## Combined VO Script Section

At the bottom of every storyboard, include a combined VO script:

```
## Combined Voiceover Script

[All frame voiceover text concatenated into one continuous block. 
No frame markers. No stage directions. Just the spoken text, 
in order, with natural punctuation. 
This block is copy-paste ready for AI Studio.]
```

This is critical — the user pastes this directly into the AI voice tool. It must read as one continuous, natural script.

## Platform-Specific Notes

### Meta Reels/Stories (9:16)
- Hook in first 1.5 seconds (earlier than other formats)
- Sound-on assumed but design for sound-off (text overlays carry meaning)
- Vertical composition, subject centered
- CTA button at bottom — leave space in final frame

### Meta Feed (4:5 or 1:1)
- Autoplay, sound-off default
- Text overlays are primary communication (VO is bonus)
- First frame IS the thumbnail — must work as a static image too
- Captions/subtitles layer recommended

### YouTube Pre-Roll (16:9)
- 5-second skip threshold — hook must land before second 5
- Sound-on assumed
- VO carries primary message
- End card with subscribe/CTA in final 5 seconds

### Google Discovery/Display (1.91:1)
- Typically static or subtle animation (not full video)
- If animated: 3 frames max, 6s total, no VO
- Text overlay is the entire message
