# Output Format Specification

Load this file in Steps 4-7 of the ad-copywriter skill. Defines the exact structure and format of all 5 deliverables.

## Deliverable 1: Ad Copy Report (.md)

**Filename:** `ad-copy-report.md` (in `_engine/working/` — folder location encodes client + program)

### Structure

```markdown
# {Business Name} — Ad Copy Report

Generated: {date}
Mode: {Downstream from creative brief | Standalone}
Platforms: {Google, Meta, or Both}
Campaigns: {count}

---

## Campaign: {Campaign Name}

### Framework: {PAS | BAB | Feature-Benefit-Proof | AIDA | Social Proof Stack}

**Target Persona:** {persona name} — {one-line description}
**Campaign Objective:** {objective from creative brief}
**Key Hooks:** {hooks used}

---

### Google RSA — Ad Group: {Ad Group Name}

**Headlines (15):**
| # | Headline | Chars | Source | Pin |
|---|----------|-------|--------|-----|
| H1 | {headline text} | {count} | [BRIEF] | Pin H1 |
| H2 | {headline text} | {count} | [GENERATED] | — |
| ... | ... | ... | ... | ... |
| H15 | {headline text} | {count} | [ADAPTED] | — |

**Descriptions (4):**
| # | Description | Chars | Source | Pin |
|---|-------------|-------|--------|-----|
| D1 | {description text} | {count} | [BRIEF] | Pin D1 |
| ... | ... | ... | ... | ... |

**Path Fields:** Path 1: {text} ({chars}) | Path 2: {text} ({chars})
**Final URL:** {url}
**Pinning Notes:** {why H1 and D1 are pinned}

---

### Meta Ad — {Ad Name with A/B label}

**Primary Text:** [GENERATED]
{primary text — full text, note char count}
({char count} chars {— "will truncate in feed" if > 125})

**Headline:** {headline} ({chars} chars)
**Description:** {description} ({chars} chars)
**CTA Button:** {Learn More | Book Now | Shop Now | etc.}
**Landing URL:** {url}

[Repeat for each A/B variant]

---

[Repeat for each campaign]
```

### Report Quality Rules
- Every copy block labeled: `[BRIEF]`, `[GENERATED]`, or `[ADAPTED]`
- Character counts shown for every headline, description, and primary text
- Minimum 50 lines total
- Framework stated per campaign section
- Pinning recommendations included for Google RSAs

---

## Deliverable 2: Google Ads CSV

**Filename:** `google-ads.csv` (in `_engine/working/`)

### Columns (in order)

```
Campaign, Ad Group, H1, H2, H3, H4, H5, H6, H7, H8, H9, H10, H11, H12, H13, H14, H15, D1, D2, D3, D4, Path 1, Path 2, Final URL, Pin Notes
```

### Rules
- One row per RSA (one RSA per ad group typically)
- H1-H15: each ≤ 30 characters — **CRITICAL, validate every cell**
- D1-D4: each ≤ 90 characters — **CRITICAL, validate every cell**
- Path 1, Path 2: each ≤ 15 characters
- Campaign names must match the ad copy report exactly
- Empty headline cells are OK (minimum 3 headlines, recommend 10-15)
- CSV must be valid — proper quoting for commas within cell values
- No BOM character at start of file

### Character Limit Validation

Before writing the CSV, run this check on every cell:
1. Strip leading/trailing whitespace
2. Count characters (not bytes)
3. If headline > 30 → CRITICAL failure, rewrite
4. If headline > 28 → WARNING (close to limit)
5. If description > 90 → CRITICAL failure, rewrite
6. If path > 15 → CRITICAL failure, rewrite

---

## Deliverable 3: Meta Ads CSV

**Filename:** `meta-ads.csv` (in `_engine/working/`)

### Columns (in order)

```
Campaign, Ad Set, Ad Name, Primary Text, Headline, Description, CTA, Format, Landing URL
```

### Rules
- One row per ad variant
- Ad Name format: `{Campaign}-{Persona}-{Hook/Variant}` (e.g., "Prospecting-DesignBuyer-HookA")
- Primary Text: flag if > 125 chars (truncation in feed)
- Headline: ≤ 40 characters
- Description: ≤ 30 characters
- CTA: standard Meta CTA values (Learn More, Book Now, Shop Now, Sign Up, Contact Us, Download, Get Quote, Subscribe)
- Format: Single Image, Carousel, Video, Collection
- A/B variants reflected in Ad Name labels (HookA/HookB, VariantA/VariantB)
- Campaign names must match the ad copy report exactly

### Carousel-Specific

For carousel ads, include additional columns or note in Ad Name:
- Each card gets its own row with card number in Ad Name: `{Campaign}-{Persona}-Carousel-Card1`
- Or single row with pipe-separated headlines: `Headline 1 | Headline 2 | Headline 3`
- Preferred: separate rows per card (cleaner for bulk upload)

---

## Deliverable 4: Image Prompts (.md)

**Filename:** `image-prompts.md` (in `_engine/working/`)

### Structure

```markdown
# {Business Name} — Image Generation Prompts

Generated: {date}
Image Tool: Gemini
Total Prompts: {count}

---

## Campaign: {Campaign Name}

### Prompt 1 — {Persona/Angle} — {Aspect Ratio} [P1]

**Placement:** {Meta Feed / Google Display / Stories / etc.}
**Aspect Ratio:** {4:5 / 9:16 / 1:1 / 1.91:1}
**Priority:** {P1 / P2}

> {Full Gemini prompt — starts with image_gen_prompt_prefix, includes scene, composition, 
> lighting, aspect ratio instruction, text overlay zone instruction. Minimum 30 words.}

**Text Overlay Copy:** "{the text that will be placed on this image}"
**Overlay Position:** {Top 20% / Bottom 15% / Left third / etc.}

---

[Repeat for each prompt]
```

### Quality Rules
- Every prompt starts with the campaign's `image_gen_prompt_prefix`
- Aspect ratio specified in both metadata AND within the prompt text
- Text overlay zone instruction included
- Minimum 30 words per prompt
- P1/P2 priority from creative brief formats
- Prompts vary by persona angle — no copy-paste of the same prompt with different labels

---

## Deliverable 5: Video Storyboards (.md)

**Filename:** `video-storyboards.md` (in `_engine/working/`)

### Structure

```markdown
# {Business Name} — Video Storyboards

Generated: {date}
Videos: {count}
Voice Tool: AI Studio

---

## Video 1: {Video Name/Description}

**Duration:** {6s / 15s / 30s}
**Platform:** {Meta Reels / YouTube Pre-Roll / etc.}
**Aspect Ratio:** {9:16 / 16:9 / 4:5}
**Framework:** AIDA
**Target Persona:** {persona}

### Frame 1 — Attention (0-3s)

**Visual:** {full Gemini image prompt for this frame}
**Motion:** {camera/animation direction}
**Text Overlay:** {on-screen copy, ≤ 8 words}
**Voiceover:** {clean VO text — no stage directions}
**Voice Direction:** {tone/pace for model selection}
**Music:** {mood/energy}

### Frame 2 — Interest (3-7s)
[... same structure ...]

[... all frames ...]

---

## Combined Voiceover Script — Video 1

{All VO text concatenated. No frame markers. No directions. 
Just the spoken words in order. Copy-paste ready for AI Studio.}

---

[Repeat for each video]
```

### Quality Rules
- Every frame has all 5 layers (Visual, Motion, Text Overlay, Voiceover, Voice Direction, Music)
- VO text is clean — no parentheticals, no stage directions, no ALL CAPS
- Voice Direction is separate from VO text
- Combined VO script at bottom of each storyboard
- Word count matches duration (~2.5 words/sec)
- Frame count matches duration template (see video-storyboard-spec.md)
