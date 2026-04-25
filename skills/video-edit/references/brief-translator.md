# Brief Translator — Plain English → Aesthetic Preset

The user speaks in outcomes ("make it feel premium", "Gen-Z punchy", "testimonial that builds trust"). This file maps those phrases to one of the 8 presets in [aesthetic-presets.md](aesthetic-presets.md).

## Translation Table

If user says…                                                      → preset
------------------------------------------------------------------  | -------------------
premium / Apple / cinematic / spacious / luxury / calm confident    | **apple-premium**
punchy / high-energy / Gen-Z / TikTok-style / fast cuts / bold      | **gen-z-punchy**
clean / corporate / B2B / professional / safe / restrained          | **corporate-clean**
warm / documentary / story-driven / organic / grainy / muted        | **documentary-warm**
demo / product tour / SaaS / screen-record / chrome mockup          | **tech-demo**
testimonial / interview / client story / quote-driven / trust       | **testimonial-trust**
sales / course / hook-heavy / scroll-stopping / urgency / CTA       | **course-sell**
event / recap / highlight reel / after-movie / music-driven         | **event-recap**

## If User Gives Multiple Signals

- If they combine **audience feel** (premium / Gen-Z / corporate) with a **content type** (testimonial / demo / event), prefer the content type when it appears in the table. Example: "premium testimonial" → testimonial-trust (not apple-premium), because the structural fit matters more than the surface aesthetic. Then override the preset's color/font defaults with "premium" signals.
- If they say "make it like <Brand>", map the brand reference:
  - Apple / Airbnb / Stripe → apple-premium
  - Duolingo / MrBeast / Alex Hormozi → gen-z-punchy or course-sell
  - Rolex / Bentley / IBM → corporate-clean
  - Nike docu / Patagonia → documentary-warm
  - Linear / Notion / Vercel → tech-demo
- If the brief is genuinely vague ("make it good", "spice it up"), fall back to **corporate-clean** and tell the user: *"Going with a safe premium look. Say the word if you want it punchier or more cinematic."*

## Inferring Content Type from the Source Video

You can often skip asking the user. Use source-probe.json + a quick glance at the video:
- **Talking-head, single person, static bg** → testimonial-trust or apple-premium (lean premium if duration > 45s)
- **Screen recording with cursor movement** → tech-demo
- **Multiple scenes, music bed already present** → event-recap
- **Punchy short (<25s), vertical 9:16** → gen-z-punchy
- **Corporate-office setting, suit/meeting room** → corporate-clean
- **Outdoor, handheld, human subjects** → documentary-warm

If aspect is 9:16 and duration <25s, bias toward gen-z-punchy regardless of content signal unless user explicitly asked for premium.

## Overrides

User-supplied brand colors or fonts ALWAYS win over preset defaults. If the client folder has a `brand-config.json` or `DESIGN.md`, read it first — preset becomes a motion/pacing guide only.

## What the Translator Outputs

After choosing a preset, emit a structured brief for step 5 (hyperframes authoring):

```json
{
  "preset": "<preset-name>",
  "preset_reasoning": "<one sentence — why this preset fits>",
  "design_overrides": {
    "colors": [ ... from brand-config if present ],
    "fonts": [ ... from brand-config if present ]
  },
  "caption_style": "<minimal-centered | animated-kinetic | lower-third | marker-sweep>",
  "narrative_arc": "<hook-framer | testimonial-trust-arc | case-study-arc | product-demo-arc | event-recap-arc>",
  "motion_density": "low | medium | high",
  "source_role": "<primary | secondary | split-screen>"
}
```

motion_density ranges:
- **low** — apple-premium, documentary-warm, corporate-clean, testimonial-trust
- **medium** — tech-demo, event-recap
- **high** — gen-z-punchy, course-sell

Pass this structured brief + source-probe.json + cuts.json + the original plain-English brief when invoking `/hyperframes`.
