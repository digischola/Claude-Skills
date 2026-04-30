# Voice Library Sector Seeds

Pre-built starter voice patterns per business sector. Loaded by business-analysis Step 7 (Voice Library Extraction) when a NEW client has no historic creative data — provides Tier 1 of the three-tier bootstrap (sector-default + founder-voice + competitor-anti-pattern).

## File naming

`{sector}.json` — one file per sector. Sectors mirror the existing `business-analysis/references/sector-lenses/` set so a client tagged with a sector lens automatically gets the matching voice seed.

| Sector lens | Voice seed |
|---|---|
| `wellness-retreats.md` | `wellness-retreats.json` |
| `local-services.md` | `local-services.json` |
| `restaurant-food-service.md` | `restaurant-food-service.json` |
| `saas-software.md` | `saas-b2b.json` |
| `professional-services-b2b.md` | `professional-services.json` |
| `temple-cultural-org.md` | `temple-cultural-org.json` |
| (no matching lens) | `_default.json` |

## Schema

Each sector seed follows the same schema as `voice-library.json` (per `~/.claude/shared-context/voice-library-spec.md`), but with these differences:

- `extracted_from`: marked as `"method": "sector_seed"` with no client-specific metric — this is universal sector wisdom, not extracted from a specific campaign
- `bootstrapping`: not applicable (this is the seed itself)
- `client`: not set (template)
- `headline_patterns`: 4-6 patterns proven across the sector (cite originator/source where useful)
- `forbidden_phrases`: includes both universal ban list AND sector-specific traps (e.g. "world-class spa" for wellness, "next-gen platform" for SaaS)
- `competitor_voice_reference`: empty by default; gets populated per-client during onboarding

## When a sector is added

1. Create `{sector}.json` from the template (start by copying `_default.json`)
2. Tune headline_patterns + forbidden_phrases + cta_verb_noun_pairs for the sector
3. Add a one-liner row to the table above
4. Update `business-analysis/references/voice-library-extraction.md` Tier-1 mapping if needed
5. Test on a new client of that sector → log learnings if patterns miss

## Maturity

These are starter floors, not ceilings. Once a client onboards, runs campaigns, and post-launch-optimization gathers performance data, the **client's own voice-library.json overrides the sector seed**. The seed is just to prevent the cold-start problem.

If a sector seed's patterns repeatedly underperform across multiple clients in that sector, that's signal to refine the seed itself — log the pattern in `_skill-corrections-log.md` (mistake type: `other` with subtag `sector-seed-refinement`) and update the seed file.
