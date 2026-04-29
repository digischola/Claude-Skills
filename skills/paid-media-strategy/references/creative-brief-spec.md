# Creative Brief JSON Specification

Machine-readable handoff from paid-media-strategy to ad-copywriter skill. Generated after the strategy report, populated from wiki data + strategy synthesis.

## Schema

```json
{
  "business_name": "string — from _engine/wiki/business.md",
  "date": "ISO 8601 date (YYYY-MM-DD)",
  "campaigns": [
    {
      "campaign_name": "string — matches strategy report campaign names exactly",
      "platform": "Google|Meta",
      "phase": 1|2|3,
      "objective": "string — campaign objective (Conversions, Leads, Sales, etc.)",
      "personas": [
        {
          "persona_name": "string — matches wiki persona name exactly",
          "messaging_angle": "string — 1-sentence core angle for this persona in this campaign",
          "pain_points": ["string — 2-4 pain points from wiki persona concerns"],
          "hooks": ["string — 3-5 hook options (first 3 seconds of video / headline of static)"],
          "cta": "string — primary CTA text for this persona",
          "tone": "string — tone descriptor (aspirational, practical, ROI-driven, etc.)"
        }
      ],
      "formats": [
        {
          "format_type": "RSA|Responsive Display|Single Image|Carousel|Video|Instant Form",
          "specs": "string — dimensions, character limits, or technical requirements",
          "quantity_needed": "number — how many variants needed",
          "priority": "P1|P2|P3"
        }
      ],
      "visual_direction": {
        "style": "lifestyle photography | product shots | architectural | illustrated | mixed",
        "mood": "string — e.g. 'warm natural, premium, editorial'",
        "color_guidance": "string — ad-specific palette derived from brand-config",
        "references": ["string — mood/aesthetic references"],
        "avoid": ["string — visual styles to explicitly avoid"],
        "image_gen_prompt_prefix": "string — reusable AI image generation prompt prefix enforcing brand consistency"
      },
      "landing_page": {
        "url": "string | null",
        "page_type": "existing_website | dedicated_lp | instant_form | none",
        "message_match_notes": "string — what the LP headline/hero must echo from the ad",
        "conversion_action": "string — form submit, brochure download, phone call, etc."
      },
      "ab_testing": {
        "priority_variable": "hook | image | cta | audience | format",
        "test_pairs": [
          {
            "variable": "string — what's being tested",
            "variant_a": "string",
            "variant_b": "string",
            "success_metric": "CTR | conversion_rate | CPA | ROAS",
            "min_sample": "string — minimum conversions/impressions before calling winner"
          }
        ]
      }
    }
  ],
  "proof_elements": [
    {
      "type": "media_mention | certification | testimonial | stat | award | case_study",
      "content": "string — the actual proof text",
      "source": "string — where it comes from",
      "use_in_campaigns": ["campaign_name"],
      "priority": "P1|P2|P3"
    }
  ],
  "brand_voice": {
    "tone": "string — overall brand tone from _engine/wiki/brand analysis",
    "do": ["string — messaging principles to follow"],
    "dont": ["string — messaging pitfalls to avoid"]
  },
  "competitor_angles": ["string — what competitors are saying that we should counter or avoid"]
}
```

## Field Source Labels

| Field | Source | Notes |
|---|---|---|
| `business_name` | [EXTRACTED] _engine/wiki/business.md | Direct extraction |
| `date` | [EXTRACTED] session date | Auto-generated |
| `campaigns[].campaign_name` | [EXTRACTED] strategy report | Must match report campaign names |
| `campaigns[].platform` | [EXTRACTED] strategy report | Google or Meta |
| `campaigns[].phase` | [EXTRACTED] strategy report | Phase 1, 2, or 3 |
| `campaigns[].objective` | [EXTRACTED] strategy report | Platform-specific objective |
| `campaigns[].personas[].persona_name` | [EXTRACTED] _engine/wiki/audiences.md or _engine/wiki/strategy.md | Must match wiki persona names |
| `campaigns[].personas[].messaging_angle` | [INFERRED] strategy synthesis | Derived from persona + campaign intersection |
| `campaigns[].personas[].pain_points` | [EXTRACTED] wiki persona concerns | Direct from persona research |
| `campaigns[].personas[].hooks` | [INFERRED] strategy creative direction | Synthesized from strategy report Section 5 |
| `campaigns[].personas[].cta` | [INFERRED] strategy + conversion setup | Based on primary conversion action |
| `campaigns[].personas[].tone` | [INFERRED] brand voice + persona match | Tone varies by persona |
| `campaigns[].formats[]` | [EXTRACTED] strategy report creative direction | Format specs from platform references |
| `brand_voice.tone` | [EXTRACTED] _engine/wiki/business.md or brand-config.json | Overall brand positioning |
| `brand_voice.do` | [INFERRED] wiki + strategy synthesis | Derived from brand strengths and positioning |
| `brand_voice.dont` | [INFERRED] competitor analysis + brand positioning | Derived from competitive gaps and brand risks |
| `competitor_angles` | [EXTRACTED] _engine/wiki/competitors.md + strategy report | What competitors emphasize in their messaging |
| `campaigns[].visual_direction.style` | [INFERRED] brand + product type | Architectural for premium products, lifestyle for services |
| `campaigns[].visual_direction.mood` | [INFERRED] brand-config.json | Derived from brand personality and visual identity |
| `campaigns[].visual_direction.color_guidance` | [EXTRACTED] brand-config manual_override | Direct from brand-config color notes |
| `campaigns[].visual_direction.references` | [EXTRACTED] wiki media/brand mentions | Publications, existing creative, competitor examples |
| `campaigns[].visual_direction.avoid` | [INFERRED] competitor analysis + brand positioning | Counter-position against category defaults |
| `campaigns[].visual_direction.image_gen_prompt_prefix` | [INFERRED] all visual direction fields | Synthesized into reusable AI prompt prefix |
| `campaigns[].landing_page.url` | [EXTRACTED] _engine/wiki/business.md or _engine/wiki/offerings.md | Direct page URL |
| `campaigns[].landing_page.page_type` | [INFERRED] strategy report | Based on conversion setup and platform |
| `campaigns[].landing_page.message_match_notes` | [INFERRED] hook + LP alignment | Ad hook must echo on LP hero |
| `campaigns[].landing_page.conversion_action` | [EXTRACTED] strategy report | From conversion setup section |
| `campaigns[].ab_testing` | [INFERRED] strategy synthesis | Priority test variables per campaign phase |
| `proof_elements[]` | [EXTRACTED] _engine/wiki/business.md + _engine/wiki/offerings.md | Media mentions, certifications, stats from wiki |

## Validation Rules

1. Every `campaign_name` must appear in the strategy report.
2. Every `persona_name` must appear in the wiki audiences/personas section.
3. `hooks` array must have 3-5 entries per persona per campaign.
4. `pain_points` array must have 2-4 entries per persona.
5. `formats` must include at least one P1 entry per campaign.
6. `brand_voice.do` and `brand_voice.dont` must each have 3-5 entries.
7. `competitor_angles` must have 3-5 entries.
8. Every campaign must have `visual_direction` with at least `style`, `mood`, and `image_gen_prompt_prefix`.
9. Every campaign must have `landing_page` with `page_type` specified.
10. Phase 1 campaigns must have at least 1 `ab_testing.test_pairs` entry.
11. `proof_elements` must have 3+ entries with at least one P1.
12. `image_gen_prompt_prefix` must be a usable prompt (30+ words, includes style/mood/color/setting).

## Usage by Downstream Skills

The **ad-copywriter skill** reads this JSON to:
- Generate platform-specific ad copy per campaign and persona
- Match tone and hooks to each persona segment
- Respect brand voice constraints
- Counter competitor messaging angles
- Produce the correct number of creative variants per format
- Use `image_gen_prompt_prefix` to generate AI image prompts alongside copy
- Use `landing_page.message_match_notes` to ensure ad→LP message match
- Use `ab_testing.test_pairs` to generate A/B variant copy
- Incorporate `proof_elements` by priority into ad copy and image overlays

The **campaign-setup skill** uses `campaigns[].formats[]` to determine ad formats and `landing_page.url` for destination URLs.

The **landing-page-builder skill** (future) reads `landing_page` fields to determine which campaigns need dedicated LPs vs existing pages.
