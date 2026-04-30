# Image Prompt Patterns Reference

## Table of Contents

- [Designer-brain mandate](#designer-brain-mandate-mandatory--added-2026-04-29) — seven required blocks per prompt
- [Prompt structure](#prompt-structure)
- [Per-format templates](#per-format-templates)
- [Performance rules](#performance-rules)
- [Brand consistency rules](#brand-consistency-rules)
- [Negative constraints](#negative-constraints)
- [Validator hooks](#validator-hooks)

Load this file in Step 6 of the ad-copywriter skill. Also load `references/creative-research.md` for performance-backed rules.

Defines prompt structure, per-format templates, performance rules, and brand consistency rules for AI image generation (Gemini).

## Designer-brain mandate (MANDATORY — added 2026-04-29)

**The skill must think like a top-tier brand-spec director writing for a senior graphic designer, not like a scene-describer for a text-to-image model.** Every prompt below this line is a design hand-off, not a vibes paragraph.

The Digischola Self-Audit prompt library is the reference floor for "designer-brain depth": pixel-anchored composition grids, exact-copy strings with type / weight / size / colour / position, gradient and overlay specifications, vector flourish vocabulary, light direction with hardness and falloff, surface materials, negative constraints. The same depth applies to every client — the *vocabulary* changes per business (paisley motifs for a temple, dashboard gauges for a SaaS audit, woven-cotton textures for a wellness retreat) but the *depth* never drops.

### The seven required blocks per prompt (HARD FLOOR — validator CRITICAL-fails if any missing)

Every spec-prose AND JSON prompt MUST include all seven, or explicitly mark a block as `intentionally omitted because <reason>`:

1. **BRAND DESIGN SYSTEM** — palette (named hex roles: background / accent / primary-text / body-text / panel / etc), typography (display font + weight + letter-spacing, body font + weight), photography style (lens, focal length where applicable, depth-of-field cue, lighting direction archetype, shadow treatment), motif vocabulary the brand uses (e.g. "paisley flourish" / "dashboard gauge" / "woven texture")
2. **COMPOSITION GRID** — aspect ratio + exact pixel dimensions, grid system (12-column with gutters / rule-of-thirds / golden-spiral), zone breakdown by % or pixel ranges (top zone / middle zone / bottom zone), outer margins in pixels
3. **SUBJECT** — what's in the frame, with frame coordinates ("face positioned so eyes land on upper-left rule-of-thirds intersection" not "in the background"), rendered surface materials, colour grading direction
4. **LIGHT + SURFACE** — light direction with degrees ("upper-left at -45°"), hardness (0=hard / 1=soft), falloff direction, surface materials touched by the light ("matte black desk surface" / "brushed cotton mat" / "polished marble"), atmospheric notes (steam / haze / golden cast)
5. **TEXT ELEMENTS** — every embedded text piece as a structured block: `exact_copy` / font + weight / size in px / colour as hex / position as anchor + offset in px / letter-spacing if non-default. Special-character emphasis (₹ glyph colour, → arrow size, • bullet weight) called out explicitly
6. **DECORATIVE / VECTOR ELEMENTS** — gradient overlays (linear / radial / mesh, colour stops with position %, opacity), section dividers, sectional bands, motif placements with size / opacity / corner anchor, callout arrows, dashed lines, badge geometry — drawn from the brand's vector vocabulary (see Sector Vocabulary Library below). If a card is intentionally minimal, declare `decorative_elements: none — minimalist register intentional` to satisfy the validator
7. **NEGATIVE CONSTRAINTS** + **RENDER QUALITY** — explicit exclusions (no <competitor logos> / no <sensitive imagery for the platform> / no <off-brand stock cliches>) AND a final clause stating render fidelity ("Premium polished advertising creative for Meta feed placement, magazine-grade colour grading, suitable for slow scroll-stop")

### The four input signals — adaptation logic the skill applies per prompt

The same brand can produce wildly different prompts depending on these four signals. The skill MUST read all four for every prompt and let them shift the spec choices.

**Signal 1 — Conversion goal** (read from `creative-brief.json` `campaigns[].primary_conversion_event`):
- `Lead` / `RSVP` / `CompleteRegistration` → single CTA prominence; trust-strip integration; reduce decorative noise around the form-action surface; "no-friction" visual cues (cream gradient bands, soft golden pulls)
- `Purchase` → product detail focus; price + arrow + CTA button as a tightly-grouped unit; texture/material fidelity raised; trust-pillars (rating, reviews, refund) inline-chip-stacked
- `App Install` → screen-mockup hero treatment; OS chrome shown; rating-stars badge; download-CTA prominence
- `Awareness / Reach` → editorial mood; copy-light; subject-led storytelling; minimal CTA

**Signal 2 — Emotional register** (infer from creative angle / persona / brand voice):
- **Calm / contemplative** → soft natural light (hardness 0.4+), low-saturation palette, italic display typography, sparse decorative flourish, breathing whitespace, single-subject framing
- **Aspirational / warm** → golden-hour light (+200-400K), saturated cream/gold palette, mid-frequency decorative motifs, family / community subjects, soft gradient bands
- **Urgent / scroll-stop** → high-contrast palette, bold display weight (700+), shorter type stack, sharp-edged composition zones, ambient glow accents, high-impact CTA pill
- **Authoritative / educational** → flat / frontal subject framing, monospace or serif body typography, data-led decorative system (charts, gauges, callouts), restrained palette
- **Devotional / cultural** → warm interior light, gold + navy + cream brand palette, traditional motif corners (paisley / lotus / geometric border), Sanskrit/devanagari punctuation as decorative typography, no figurative deity close-ups

**Signal 3 — Audience tier** (read from `creative-brief.json` audience metadata):
- **Cold prospecting** → maximum scroll-stop impact: high contrast, bold subject, embedded headline larger size, decorative system simplified to one strong motif, single CTA
- **Lookalike (warm-cold)** → editorial register: subject-led, mid-decoration, lighter type weight, secondary supporting copy allowed
- **Warm retargeting** → intimate framing (closer crop, faces visible), more sensory detail (steam, texture, food close-ups), softer lighting, narrative-style copy, reference to prior campaign engagement allowed in copy ("you came for X, here's Y")
- **Customer / retention** → established-relationship register: insider language, sponsorship/upsell CTAs, tighter brand-system adherence (no scroll-stop tricks), refined typography

**Signal 4 — Cultural / sector context** (derive from brand-config.json + offerings.md):
- **Temple / cultural-org** (ISKM): paisley motifs, gold + navy + cream, Sanskrit punctuation, golden-hour interior, no deity close-ups in cold/LAL, family / community subjects
- **SaaS / B2B audit** (Digischola): pure black background, sky-blue accents, dashboard gauges + leak-marker dashed circles + sky-blue annotation lines, monospace + Space Grotesk type stack, founder portrait with reference attachment, ₹ glyph + → arrow as design elements
- **Wellness / retreat**: cream-and-sage palette, hand-drawn brushstroke flourishes, woven-cotton textures, soft natural light, body-led subjects, italic serif display
- **Local services / fitness / studio**: action photography, motion blur on movement, branded apparel, before-after split screens, results-stat callouts, bold sans-serif display
- **Restaurant / food**: overhead flatlay or 45° plate angle, steam visible, hand-serving framing, warm wood / linen surfaces, ASMR-style sensory detail
- **D2C product**: clean studio backdrop or contextual lifestyle, packaging as hero, colour-graded to match brand palette, ingredient/feature callouts via thin-line annotations
- **Professional services / B2B**: editorial portrait, neutral palette, credibility chips (years / clients / certifications), restrained typography, single CTA pill

The skill picks one or more cell entries from this library for every prompt. If the client's sector isn't listed, the skill infers from offerings.md + brand-config.json and authors a custom vocabulary block — flagged as `[INFERRED sector vocabulary — confirm with analyst]` in the prompt header.

### Designer-brain authoring process (sequence the skill follows for each prompt)

1. **Read four signals.** Conversion goal, emotional register (from creative angle), audience tier, sector context.
2. **Derive design system floor.** Read `brand-config.json` `design_system` (or fall back to `colors` + `fontFamily` + infer the rest from sector vocabulary).
3. **Layer campaign overrides.** Read `creative-brief.json` `visual_direction.design_system_overrides` for this campaign — campaign-specific palette tilt, motif emphasis, type-scale shift.
4. **Author the seven blocks.** For each block, make a design choice the four signals justify. Don't copy-paste a template; *think* — would a top art director put a gold gradient band here, or a sharp navy divider? Why?
5. **Embellish with authority.** If brief is silent, the skill adds gradient overlays / vector motifs / typography emphasis that the brand vocabulary supports and the campaign goal requires. Author flourishes that serve scroll-stop, hierarchy, or emotional register — not decoration for its own sake.
6. **Negative constraints from sector + Meta policy.** Pull negative constraints from sector vocabulary (no Krishna close-ups for temple cold/LAL; no founder face for product-led prompts; no Google logo for ex-Google credibility creative) plus universal Meta sensitive-content policy.
7. **Render quality clause.** Final sentence in both spec-prose and JSON ends with a fidelity directive matching the placement.

### Design-system schema floor (in brand-config.json)

The brand-config.json `design_system` block defines the floor every prompt inherits. If absent, the skill scaffolds a minimum from existing `colors` + `fontFamily` + sector inference, and writes it back to brand-config.json so subsequent runs build on the locked floor.

```json
{
  "design_system": {
    "palette": {
      "background": "#ffffff",
      "accent_primary": "#f1c66e",
      "accent_secondary": "#1f3671",
      "headline_text": "#071442",
      "body_text": "#1f3671",
      "panel_bg": "#f8eae1"
    },
    "typography": {
      "display_font": "Cardo",
      "display_weight": "italic-regular",
      "display_letter_spacing": "-0.01em",
      "body_font": "Noto Sans",
      "body_weight": 400,
      "type_scale": {"hero": 56, "h1": 42, "h2": 32, "body": 18, "caption": 14}
    },
    "photography": {
      "default_lens": "35mm",
      "default_lighting": "warm interior natural light, hardness 0.4",
      "default_falloff": "soft cream falloff into navy shadow",
      "default_grading": "+200K warm, +20% saturation"
    },
    "motif_library": [
      "paisley flourish (gold, 64x64px corner accent, 15% opacity)",
      "geometric border pattern (gold, 8px height, top/bottom strip)",
      "Sanskrit devanagari punctuation as decorative typography",
      "warm cream gradient overlay (linear, vertical, #f8eae1cc to transparent)"
    ],
    "vector_vocabulary": ["dot bullet (gold, 8px circle)", "gold thin divider line (1-2px, 30/100/30 opacity gradient through height)"],
    "emphasis_rules": {
      "special_characters": "₹ glyph in accent_primary; → arrow same size as adjacent text",
      "hierarchy_separator": "8px gold dot bullet between phrases",
      "trust_chips": "rounded-pill border 1px accent_primary, dark panel_bg, body_font 600 18px"
    },
    "render_quality_clause": "Premium editorial advertising creative, magazine-grade colour grading, suitable for slow scroll-stop"
  }
}
```

The `creative-brief.json` `visual_direction.design_system_overrides` block lets paid-media-strategy author campaign-specific deviations on top:

```json
{
  "visual_direction": {
    "design_system_overrides": {
      "palette_tilt": "shift accent toward crimson #d31f36 for festival emphasis",
      "motif_emphasis": "festival garland motif takes priority over paisley for this campaign",
      "type_scale_shift": "+20% display size for scroll-stop in cold-prospecting tier",
      "emotional_register_lock": "aspirational warmth"
    }
  }
}
```

If neither file has a design_system block, the skill scaffolds a sector-default floor and writes it back to `brand-config.json` (logged in `_engine/wiki/log.md` as a SKILL-AUTHORED entry).

---

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

## Reference-image flagging (MANDATORY — added 2026-04-28, sector-aware defaults 2026-04-29)

Every prompt MUST carry these metadata fields:

- `requires_reference_image: true | false`
- `reference_subject: string` — what the analyst must attach (e.g., "Mayank's portrait photo")
- `reference_file_id: string | null` — the manifest entry ID (e.g., `WLF-REF-CLASS-HALL`) when an actual file exists in the client's reference manifest
- `reference_file_path: string | null` — relative path to the file when known

**Sector-aware reference-flag default (added 2026-04-29 — replaces the prior universal "generic = false" fallback).** Reference images are brand-consistency anchors, not optional decoration. Without them, every Gemini render produces a slightly different room, slightly different teacher, slightly different food vessel — death for brand recognition across 6-8 quarterly creatives. The skill MUST apply this sector default unless the prompt depicts an abstract concept with no specific real-world subject:

| Sector | Default for `requires_reference_image` | Reference subjects expected in manifest |
|---|---|---|
| Temple / cultural-org | **TRUE** for prompts depicting interior space, congregation, kirtana, prasadam, classes | Actual temple hall interior, class space, prasadam serving moment, kirtana lead, devotee community shots |
| SaaS / B2B audit | **TRUE** for founder-portrait creatives; **FALSE** for UI/dashboard mockups (those are conceptual) | Founder face, team headshots; UI mockups can be conceptual |
| D2C product | **TRUE** always — product packaging is the brand | Product packaging shot, lifestyle context with the product |
| Wellness retreat | **TRUE** for venue exterior + treatment-room interior; **FALSE** for abstract lifestyle | Actual retreat venue, treatment room, signature practice space |
| Local services / studio | **TRUE** for storefront + studio interior | Actual storefront / studio space, signature class moment |
| Restaurant / food | **TRUE** for plated dishes + interior | Plated signature dish, restaurant interior, chef portrait |
| Professional services / B2B | **TRUE** for team / founder portrait creatives | Founder + senior team headshots |

**The skill must override the sector default only with explicit reason in the prompt header, e.g.:**
- `requires_reference_image: false — abstract conceptual illustration, no real-world subject depicted`
- `requires_reference_image: false — text-only typographic card, no photographic content`

A bare `requires_reference_image: false` without a reason on a sector that defaults to TRUE is a validator CRITICAL fail.

### Reference manifest convention (MANDATORY when sector-default is TRUE)

The skill maintains a manifest at `{client-folder}/_engine/references/images/manifest.json` that lists every available reference image, its subject, source location, license, and suggested-prompts. The manifest is the single source of truth for `reference_file_id` lookups in prompts.

Manifest schema:

```json
{
  "version": "1.0",
  "client": "<business name>",
  "program": "<program name or null for single-program>",
  "references": [
    {
      "id": "WLF-REF-CLASS-HALL",
      "subject": "Bhagavad-Gita class in actual ISKM Geylang temple hall — adult discourse with notebooks visible",
      "file_path": "<relative path from manifest.json to actual file, OR external URL>",
      "source": "Lovable mirror gallery / client-supplied / generated and approved 2026-04-28",
      "license": "Owned by client (ISKM Singapore) — use across all ISKM creatives",
      "suggested_for_prompts": ["WLF-AD-01-CARD-2", "WLF-AD-04-BEGINNERS-WISDOM"],
      "deity_imagery": false,
      "audience_safe_for_cold_LAL": true,
      "audience_restriction_note": null
    }
  ]
}
```

**Per-prompt reference resolution at authoring time:**

1. The skill reads `manifest.json`.
2. For each prompt, the skill matches by `suggested_for_prompts` OR by subject overlap.
3. The matched reference's `id`, `subject`, and `file_path` are written into the prompt's metadata header.
4. The dashboard (`scripts/render_ad_copy_dashboard.py`) renders an animated reference badge with the `reference_subject` text and (if available) a small thumbnail / "open" link to the file.

**`audience_safe_for_cold_LAL` flag**: this is a Meta-policy + brand-voice gate. References that include deity close-ups (Krishna, Radha, Nṛsiṁhadeva) get flagged `false` — the skill must NOT use them in cold/LAL prompts. They can be used in strict-retarget prompts (Festival Follow-On targeting Nṛsiṁha pixel) where audience self-selected and rejection risk is lower.

If a sector-defaults-TRUE prompt has no matching reference in the manifest, the skill writes `requires_reference_image: true` + `reference_file_id: null` + `reference_subject: <description of what to attach>`. The dashboard surfaces this as a "MISSING REFERENCE" state with a different badge colour, prompting the analyst to upload before generating.

This logic generalizes across all clients — whatever subject specificity the brand demands (founder face / product packaging / venue exterior / team headshots / temple interior), the same flag system + manifest applies.

## HTML dashboard deliverable (MANDATORY — added 2026-04-27, expanded 2026-04-28, broader scope 2026-04-29)

Alongside the markdown image-prompts file, the skill MUST also generate `ad-copy-dashboard.html` (at the client/program folder root — folder location already encodes client + program) via `scripts/render_ad_copy_dashboard.py`. The dashboard now covers ALL ad-copywriter outputs in one presentable, not just image prompts:

- **Hero KPIs:** ads count, variants count, image-prompts count, storyboards count + Gate A/B status pills
- **Per-ad cards:** framework + persona + audience + format + ID + primary-text variants with 📋 Copy buttons + headlines/descriptions in collapsibles + CTA pill
- **Image prompt grid:** one card per prompt with full prompt visible (brand visual_direction prefix substituted) + 📋 Copy full prompt button per card
- **Video storyboards:** frame-by-frame layer tables (Visual / Motion / Text overlay / Voiceover / Voice direction / Music) + Combined VO script with dedicated copy button
- **Gate audit summary:** voice / character / sensitivity audit list extracted from the inline `## Gate Audit` section of `ad-copy-report.md`
- Brand-config-derived styling (read from `_engine/brand-config.json` at the client root)
- Mobile-readable (founder may copy from phone)

The MD files remain as the analyst-readable archives. The HTML is the production tool.

**Legacy filename `prompt-library.html`:** earlier versions of this reference declared a narrower image-only dashboard called `prompt-library.html`. As of 2026-04-29 the dashboard is broader (ad copy + prompts + storyboards + Gate audit unified) and renamed to `ad-copy-dashboard.html`. Validator accepts both names for backwards-compat.

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

### 1:1 Square — Carousel Cards (MANDATORY) / Feed Fallback

> **🛑 LOAD-BEARING RULE (validator-enforced, patched 2026-04-30):** When a creative's `format_priority` in `creative-brief.json` includes `carousel`, `carousel_5_card`, `lp_redirect_carousel`, or any value containing the substring `carousel`, EVERY card MUST be 1:1 (1080×1080). Meta requires uniform aspect ratio across all cards in a carousel — mixing 4:5 with 1:1 breaks the unit. Default to 4:5 only when format is `single_image` / `feed`. `validate_format_aspect_consistency()` in `scripts/validate_output.py` cross-checks every prompt's aspect against the brief's `format_priority` per creative_id and CRITICAL-fails on mismatch. See `SKILL.md` Step 6 for the full format → aspect mapping table.

```
[prefix]. [Subject/scene in 1-2 sentences]. Ultra-realistic photograph, shot on [lens]mm, 
[lighting]. 1:1 square, tight framing with subject filling 70% of frame. 
Clean space in [bottom-left/top-right] quadrant for text overlay. High contrast.
```

Research note: Carousel cards = 1:1 ONLY (Meta unit-of-card mandate). 1:1 also works as a feed fallback when 4:5 is unavailable; tighter framing works better in square.

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
