# Image Prompt Patterns Reference

Load this file in Step 6 of the ad-copywriter skill. Also load `references/creative-research.md` for performance-backed rules.

Defines prompt structure, per-format templates, performance rules, and brand consistency rules for AI image generation (Gemini).

## Performance Rules (from creative-research.md — apply to EVERY prompt)

These override aesthetic preferences when they conflict:

1. **Light/mid-light backgrounds.** Dark images underperform by 70% in purchase rate. Allow darker moods for architecture/luxury but keep focal element clearly separated from background.
2. **High contrast mandatory.** +32% CTR, -21% CPC vs muted schemes. Subject must pop from background.
3. **No text overlay for Google Display/Demand Gen.** Google explicitly says avoid overlaid text/logos. For Google placements, generate clean product/outcome imagery only.
4. **Meta text overlay = concise.** Short, bold, high-contrast headline in modest area. Not heavy text blocks.
5. **Subject occupies 50-70% of frame.** Never >80% empty space. Leave 20-30% for text zone (Meta) or breathing room.
6. **Interior shots outperform exteriors** for architecture/real estate engagement. Use exterior for establishing/scroll-stop, interior for conversion-focused placements.
7. **Faces: vertical-dependent.** Architecture/design → product imagery wins for direct response (faces for UGC/testimonials only). Wellness/services → faces build trust.
8. **Gaze direction matters.** Lifestyle/emotional ads → averted gaze (into scene). Expert/B2B → direct gaze to camera. Product showcase → subject looks at product.
9. **Photorealism trumps artistic style.** Include "ultra-realistic photograph" + specific lens (35mm establishing, 85mm portrait) + "cinematic lighting." AI images perform as well as real photos when realistic.
10. **Keep prompts to 1-3 concise sentences** after the prefix. Overly long prompts produce noisy/inconsistent results. Specify: subject, lighting/lens, composition, aspect ratio, text zone.

## Prompt Architecture

Every image prompt follows this structure:

```
[image_gen_prompt_prefix from creative brief] + [scene/subject in 1-2 sentences] + [lens + lighting in 1 sentence] + [composition + text zone instruction]
```

**Prompt length target:** 40-80 words after the prefix. Previous prompts were 85-140 words — research shows shorter, more specific prompts produce more consistent results.

## Standalone-prompt mandate (MANDATORY — added 2026-04-27)

The deliverable file MUST present each prompt as a complete, copy-pasteable string. The user opens the file, hits Copy on one cell, pastes into Gemini, and the prompt is ready to run.

**FORBIDDEN patterns** (these create copy-paste friction at the user's end):
- `[universal prefix]` placeholder inside a prompt block, expecting the user to mentally substitute
- Per-cell metadata (aspect ratio, text-overlay zone, performance priority) ABOVE the prompt block but not IN it
- A single shared prefix block at the top of the file with each cell appending body-only text below

**REQUIRED format per cell:**
1. Cell heading
2. ONE code block containing the FULL prompt: prefix substituted in, scene description, lens + lighting, aspect-ratio instruction embedded as natural language.
3. Metadata BELOW the code block (priority, intended placement, reference-image requirement) — never above.

## Embedded text rendering (REVISED 2026-04-28)

**Modern models (Gemini 2+, ChatGPT-Imagen 2, Meta AI 2025+) render embedded text reliably.** A/B test on 2026-04-27 confirmed: all 4 permutations (Gemini × ChatGPT, JSON × prose) rendered exact chip text + headline + ₹ + → button correctly on the first try.

DO write embedded text into prompts when the design calls for it — exact copy strings, font specs, positions, sizes. The previous "leave clean space for post-production overlay" rule is REVERTED for typography-heavy creatives. Use post-production overlay only when the analyst explicitly prefers Figma control over AI rendering.

## Dual-format mandate (MANDATORY — added 2026-04-28)

Every prompt MUST be available in TWO formats:

1. **Spec-prose format** — designer-brief-style natural language with named sections (BRAND DESIGN SYSTEM / COMPOSITION GRID / SUBJECT / TEXT ELEMENTS / NEGATIVE EXCLUSIONS).
2. **JSON format** — structured object with the same content, fields-as-constraints, prefixed with one instruction line: `Generate one image based on this design specification. Treat every field as a constraint. Use the exact_copy strings verbatim — render them as visible typography, not as concepts.`

A/B test result (2026-04-27): JSON and prose tied on Gemini, prose edged JSON on ChatGPT. Different analysts and different cells will favor different formats. The HTML prompt library MUST present both formats per card with a tab toggle.

## Reference-image flagging (MANDATORY — added 2026-04-28)

Every prompt MUST carry two metadata fields the HTML library renders as an animated badge:

- `requires_reference_image: true | false`
- `reference_subject: string` — describes WHAT the user must attach (e.g., "Mayank's portrait photo", "actual product packaging shot", "venue exterior photo", "team member headshot")

**When to flag `true`:**
- Founder / team-member portraits — for likeness consistency across creatives
- Product shots — when the brand sells a specific physical product
- Venue / location shots — when a specific place is being depicted
- Custom logos or brand artifacts — when the artifact is unique and non-typographic

**When to flag `false`:**
- Generic UI / dashboard / chart mockups (abstract, no specific real-world subject)
- Conceptual illustrations
- Abstract data visualizations
- Stock-style scenes with no specific likeness requirement

The HTML library MUST render flagged cards with a pulsing/animated badge in the card head, the reference subject visible at a glance. The analyst should not have to dig into the JSON to discover a card needs an attachment.

This logic generalizes across all clients — whatever subject specificity the brand demands (founder face for personal-brand clients, product packaging for D2C clients, venue exteriors for event/wellness clients, team member headshots for professional services), the same flag system applies.

## HTML prompt-library deliverable (MANDATORY — added 2026-04-27, expanded 2026-04-28)

Alongside the markdown image-prompts file, the skill MUST also generate `{business-name}-prompt-library.html` — a one-page dashboard with:

- One card per prompt (cell)
- **Two-tab toggle per card: JSON / Spec-prose** — both formats with their own copy buttons
- Per-card "Copy full prompt" button per format tab (one click → clipboard)
- Per-card metadata visible at a glance: aspect ratio, priority, intended placement
- **Animated reference-image badge** on cards where `requires_reference_image: true` (pulse animation, sky-blue or amber accent, paperclip icon, "Attach: {reference_subject}" text)
- Filter chips (priority, angle, reference-required-only)
- Brand-config-derived styling (read from `deliverables/brand-config.json`)
- Mobile-readable (founder may copy from phone)

The MD file remains as the analyst-readable archive. The HTML is the production tool.

**Validation (CRITICAL):**
- HTML must NOT contain `[universal prefix]` placeholder strings inside any prompt block
- Every prompt block must be a self-contained complete prompt
- Every prompt card must have a working `navigator.clipboard.writeText()` button per format tab
- Every card with `requires_reference_image: true` must render the animated badge

### Component Breakdown

1. **Prefix** (from creative brief `visual_direction.image_gen_prompt_prefix`): Sets the persistent style, color palette, and mood across all images for this campaign. Never modify the prefix — append to it.

2. **Scene/Subject**: What's happening in the image. Varies per persona angle, campaign, and ad variant. 1-2 sentences max.

3. **Lens + Lighting**: Specific camera spec (e.g., "shot on 35mm, f/2.8, cinematic golden hour side-light"). One sentence.

4. **Composition + Text Zone**: Framing, aspect ratio, and where to leave space. One sentence. For Google placements, omit text zone instruction.

**Two-version strategy:** For each concept, consider generating two versions — centered subject (for Google/organic) and off-center subject (for Meta with text overlay). AI models partially respect text-zone instructions.

## Aspect Ratio Specifications

| Placement | Ratio | Pixels (min) | Use Case |
|---|---|---|---|
| Meta Feed (square) | 1:1 | 1080x1080 | Instagram/Facebook feed |
| Meta Feed (vertical) | 4:5 | 1080x1350 | Instagram feed (preferred — more screen real estate) |
| Stories/Reels | 9:16 | 1080x1920 | Instagram/Facebook Stories, Reels |
| Google Display | 1.91:1 | 1200x628 | GDN responsive display, Discovery |
| Google Display (square) | 1:1 | 1200x1200 | GDN responsive display |
| YouTube | 16:9 | 1920x1080 | Video thumbnails, YouTube ads |

**Priority assignment:**
- P1 = Must-have for campaign launch. Generate first.
- P2 = Nice-to-have, generate if time allows. A/B test variants, secondary placements.

Source these from creative brief `campaigns[].formats[].priority`.

## Prompt Templates by Format

### 4:5 Vertical — Meta Feed (Primary Format)

```
[prefix]. [Subject/scene in 1-2 sentences]. Ultra-realistic photograph, shot on [lens]mm, 
[lighting]. 4:5 vertical composition, subject occupies 60% of frame, 
clean space at top 20% for text overlay. [Light/mid-light background bias].
```

Research note: 4:5 outperforms 1:1 by 10-30% CTR in mobile feed. Default format for Meta.

### 9:16 Full Vertical — Stories/Reels

```
[prefix]. [Subject/scene in 1-2 sentences]. Ultra-realistic photograph, shot on [lens]mm, 
[lighting]. 9:16 vertical composition, subject centered in middle 60%. 
Clean space at top 15% and bottom 15% for headline and CTA. 
[Light/mid-light background or high-contrast mood].
```

Research note: Lower CPM than feed but more volatile CPA. Hook must land in first 1.5s — make the image itself the pattern interrupt.

### 1:1 Square — Feed Fallback / Carousel Cards

```
[prefix]. [Subject/scene in 1-2 sentences]. Ultra-realistic photograph, shot on [lens]mm, 
[lighting]. 1:1 square, tight framing with subject filling 70% of frame. 
Clean space in [bottom-left/top-right] quadrant for text overlay. High contrast.
```

Research note: Use as fallback or for carousel cards. Tighter framing works better in square.

### 1.91:1 Landscape — Google Display/Demand Gen

```
[prefix]. [Subject/scene in 1-2 sentences]. Ultra-realistic photograph, shot on [lens]mm, 
[lighting]. 1.91:1 landscape, subject on [left/right] third using rule of thirds. 
Clean composition. NO text overlay, NO logos — Google uses its own headlines.
```

Research note: Google explicitly recommends no overlaid text. Product/outcome should be the entire focus. Upload multiple ratios — advertisers running all ratios get better optimization.

## Style Vocabulary

Use precise visual language. Avoid vague terms.

### Lighting
- **Golden hour** — warm, low-angle sunlight, long shadows
- **Soft diffused** — overcast or shade, even illumination, no harsh shadows
- **Dramatic side-light** — strong directional light from one side, deep shadows
- **Backlit** — subject silhouetted or rim-lit against bright background
- **Studio flat** — even, shadowless lighting (product photography)
- **Ambient interior** — natural light through windows, warm tones

### Camera/Composition
- **Wide establishing shot** — shows full environment, subject small in frame
- **Medium shot** — subject fills ~50% of frame, environment visible
- **Close-up detail** — tight on texture, material, craftsmanship
- **Overhead/flat lay** — top-down view, works for products and food
- **Low angle** — camera below subject, creates sense of scale/authority
- **Eye-level** — natural, relatable perspective
- **Shallow depth of field** — subject sharp, background blurred (f/1.8-2.8 feel)
- **Deep focus** — everything sharp, front to back (f/8-16 feel)

### Mood/Atmosphere
- **Warm and inviting** — amber tones, soft textures, natural materials
- **Cool and minimal** — blue-white palette, clean lines, negative space
- **Vibrant and energetic** — saturated colors, dynamic composition
- **Moody and premium** — dark tones, selective lighting, luxury feel
- **Fresh and natural** — greens, earth tones, outdoor settings
- **Professional and clean** — neutral palette, structured composition

## Brand Consistency Rules

1. **Never deviate from the prefix.** The `image_gen_prompt_prefix` sets brand-level style. Every prompt for that campaign starts with it.

2. **Color guidance from creative brief.** Check `visual_direction.color_guidance` — if it says "warm earth tones," don't generate prompts with cool blue palettes.

3. **Reference matching.** Check `visual_direction.references` for style references (e.g., "Dezeen architectural photography"). Use these as style anchors.

4. **Avoid list.** Check `visual_direction.avoid` — if it says "no stock photo aesthetics," ensure prompts specify authentic, editorial-style photography.

5. **Per-persona variation.** Same brand style, different subjects:
   - Design-focused persona → focus on architectural details, materials, craftsmanship
   - ROI-focused persona → focus on lifestyle outcome, rental income context, property value
   - Lifestyle persona → focus on people enjoying the space, experiential moments

## Text Overlay Zones

Ads need space for text. Every prompt must specify where to leave clean space.

| Placement | Recommended Text Zone | Instruction |
|---|---|---|
| Feed (4:5, 1:1) | Top 20% | "Leave clean negative space in the top 20% of the frame for headline text overlay" |
| Stories/Reels (9:16) | Top 15% + Bottom 15% | "Clean space at top 15% for headline and bottom 15% for CTA button" |
| Display (1.91:1) | Left or right third | "Subject on [left/right] third, clean space on opposite side for text overlay" |
| Video thumbnail | Center or lower third | "Clean lower third for title text overlay" |

## Prompt Quality Checklist

Before including any image prompt in the deliverable:

**Structural (must-have):**
- [ ] Starts with the campaign's `image_gen_prompt_prefix`
- [ ] Specifies exact aspect ratio
- [ ] Includes specific lens (35mm/50mm/85mm) and lighting direction
- [ ] 40-80 words after the prefix (not bloated, not skeletal)
- [ ] Matches the persona angle for this ad variant
- [ ] Respects `visual_direction.avoid` list

**Performance (research-backed):**
- [ ] Light/mid-light background bias (dark images -70% purchase rate)
- [ ] High contrast between subject and background
- [ ] Subject occupies 50-70% of frame (not lost in empty space)
- [ ] Meta placements: includes text overlay zone instruction
- [ ] Google placements: NO text overlay, NO logos — clean imagery only
- [ ] Architecture/design: includes "ultra-realistic photograph" for photorealism
- [ ] Face/gaze direction matches vertical rule (if faces present)
- [ ] Interior shots included for architecture (outperform exteriors for engagement)

**Two-version consideration:**
- [ ] For key concepts: consider off-center version (Meta + text) AND centered version (Google/organic)
