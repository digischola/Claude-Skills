# Reference Image Protocol

When the analyst provides a reference-image folder, the skill inventories it, tags every image, and uses it to anchor brand consistency, handle sacred subjects safely, and reuse character identity across creatives.

## Folder structure (recommended)

If the analyst hasn't pre-organized, the inventory step accepts any flat folder and tags every image. But the recommended layout for fastest tag accuracy:

```
{client}/Reference Library/
├── deities/                  ← sacred subjects, treat as untouchable input
├── devotees-consent-ok/      ← real faces with media-release consent
├── prasadam/                 ← food photography
├── temple-interior/          ← atmospheric scenes (no faces)
├── kirtan-events/            ← event documentation
├── festivals/                ← named festival photo sets
├── decorative/               ← garlands, lotus, mridanga, atmospheric props
├── product/                  ← non-religious clients: product shots
├── people-portraits/         ← non-religious clients: founder/team headshots
└── locations/                ← venue / location shots
```

Subfolder names hint at tags but do not constrain — the inventory step still reads each image.

## Inventory output: reference-manifest.json

```json
{
  "folder_root": "/Users/digischola/Desktop/ISKM Singapore/Reference Library/",
  "scanned_at": "2026-05-01T...",
  "total_files": 47,
  "total_unique": 45,
  "duplicates_skipped": 2,
  "uploaded_to_higgsfield": 45,
  "images": [
    {
      "id": "deity-radha-krishna-01",
      "filename": "deities/radha-krishna-altar.jpg",
      "absolute_path": "/Users/digischola/Desktop/ISKM Singapore/Reference Library/deities/radha-krishna-altar.jpg",
      "sha256": "abc123...",
      "dimensions": {"width": 4032, "height": 3024},
      "aspect_ratio": "4:3",
      "file_size_bytes": 3845221,
      "uploaded_at": "2026-05-01T...",
      "higgsfield_uuid": "uuid-from-media_upload",
      "tags": {
        "subject_type": "deity",
        "contains_face": false,
        "contains_human": false,
        "sacred": true,
        "consent_status": "n/a",
        "usage_scope": "input_only_no_redraw",
        "ai_redraw_allowed": false,
        "auto_attach_to_concepts_with_intent": ["sacred_composite"]
      },
      "tag_confidence": "high",
      "tag_notes": "Centrally framed deity altar — never AI-redraw. Composite-into-design only."
    },
    {
      "id": "devotee-aarti-01",
      "filename": "devotees-consent-ok/aarti-evening.jpg",
      "tags": {
        "subject_type": "devotee_human",
        "contains_face": true,
        "contains_human": true,
        "sacred": false,
        "consent_status": "cleared",
        "usage_scope": "reference_or_subject",
        "ai_redraw_allowed": true,
        "auto_attach_to_concepts_with_intent": ["ugc", "lifestyle", "atmospheric"]
      },
      "tag_confidence": "high",
      "tag_notes": "Cleared for paid use per consent folder. Can be used as subject or style reference."
    },
    {
      "id": "prasadam-thali-01",
      "filename": "prasadam/sunday-thali-warm.jpg",
      "tags": {
        "subject_type": "food_object",
        "contains_face": false,
        "contains_human": false,
        "sacred": false,
        "consent_status": "n/a",
        "usage_scope": "reference_or_subject",
        "ai_redraw_allowed": true,
        "auto_attach_to_concepts_with_intent": ["cover_slide", "atmospheric", "lifestyle"]
      }
    }
  ]
}
```

## Tag fields

| Field                 | Values                                               | Notes                                  |
|-----------------------|------------------------------------------------------|----------------------------------------|
| `subject_type`        | `deity` / `scripture` / `devotee_human` / `staff_human` / `client_team` / `client_founder` / `talent_model` / `food_object` / `product_object` / `building_exterior` / `interior_atmospheric` / `decorative_object` / `landscape` / `text_only` / `mixed` | Drives routing and guardrails |
| `contains_face`       | true / false                                         | Triggers consent check                 |
| `contains_human`      | true / false                                         | Used for consent rules                 |
| `sacred`              | true / false                                         | If true → input_only_no_redraw         |
| `consent_status`      | `cleared` / `pending` / `unknown` / `n/a` / `denied` | If face present, cleared required for paid use |
| `usage_scope`         | `input_only_no_redraw` / `reference_or_subject` / `unknown` | Locks ai_redraw_allowed |
| `ai_redraw_allowed`   | true / false                                         | False blocks model from regenerating subject |
| `auto_attach_to_concepts_with_intent` | array of intents                       | Auto-attaches this reference when matching concept appears |

## Religious-brand guardrails (HARD)

These rules fire automatically during inventory tagging:

1. **`subject_type=deity`** OR **`subject_type=scripture`** OR **`sacred=true`** → set `usage_scope=input_only_no_redraw`, `ai_redraw_allowed=false`. Skill never asks model to regenerate the subject. Concept must use composite-into-design pattern (background generated, sacred subject overlaid post-gen).
2. **`contains_face=true` AND `consent_status` ∈ {pending, unknown, denied}`** → blocked from paid-ad use. Inventory flags. Analyst must move to `consent-ok/` subfolder OR provide written confirmation in `_engine/working/<entry>/consent-override.md`.
3. **AI-portrait without reference**: if no reference image is attached AND concept tag includes `human_subject` → fail voice-check, require either a reference or explicit `synthetic_human_ok: true` flag.
4. **Inappropriate descriptors**: prompts containing words like `seductive`, `erotic`, `provocative` near `deity` / `devotee` / sacred subject → CRITICAL fail.

## Consent confirmation flow

When inventory finds a face image without a clear consent signal (not in `consent-ok/` subfolder, no `consent.csv` mapping):

1. Inventory marks `consent_status: "unknown"`, `usage_scope: "unknown"`
2. Skill prints to console: `N face images need consent confirmation. Move to consent-ok/ OR add to consent.csv OR write consent-override.md`
3. Skill blocks generation queue from using these references until resolved
4. Optional shortcut: a `consent.csv` at folder root mapping `filename,consent_status,notes` lets analyst batch-clear

## Consent CSV format

```csv
filename,consent_status,notes
devotee-aarti-01.jpg,cleared,Aarti consented 2026-04-15 paid ad use
devotee-temple-volunteer-03.jpg,cleared,Volunteer consented 2026-03-20 ongoing
devotee-festival-crowd-12.jpg,denied,Crowd shot — individual face visible, blur required
```

Inventory step reads consent.csv first, then falls back to subfolder rule, then `unknown`.

## Auto-attachment to concepts

When `parse_brief.py` reads a concept and the concept includes a tag in any reference image's `auto_attach_to_concepts_with_intent` array, that reference is automatically added to the concept's `reference_image_ids[]`.

Example:
- Concept `01-prasadam-invite` has `intent: cover_slide`, tags `[prasadam, atmospheric]`
- Reference `prasadam/sunday-thali-warm.jpg` has `auto_attach_to_concepts_with_intent: ["cover_slide", "atmospheric", "lifestyle"]`
- Result: `prasadam-thali-01` is auto-attached as `reference_role: style`

Analyst can override with explicit `reference_image_ids` in the brief.

## Reference role semantics

| `reference_role`           | Meaning                                                            | Best models                            |
|----------------------------|--------------------------------------------------------------------|----------------------------------------|
| `none`                     | No reference (text-to-image only)                                  | Any                                    |
| `style`                    | Use for style transfer — colors, mood, lighting                    | nano_banana_*, flux_kontext, seedream  |
| `composition`              | Match the layout / framing                                         | flux_kontext, seedream_v4_5            |
| `subject_lock`             | Same subject, edit surround (e.g., character consistency)          | soul_cast, flux_kontext, soul_2        |
| `subject_lock_no_redraw`   | Sacred reference — composite into design post-gen                  | soul_location (background only)        |

## Sacred composite workflow (post-generation)

When a concept uses `subject_lock_no_redraw`:

1. Generate background + decorative + typography frame via `soul_location` or `nano_banana_flash` with explicit "no human or deity figures" in prompt
2. After download, run `scripts/composite_sacred.py <generated.png> <reference_deity.jpg> --placement centered_60pct --output final.png`
3. Validator confirms the composited PNG is the deliverable; raw generated background is kept in `_engine/working/<entry>/raw/` for audit

## Re-inventory triggers

Run `inventory_references.py` again when:
- Folder contents change (new images added, old removed)
- A new client's folder is provided (one-time per client)
- Tag confidence flags `low` for >5 images (manual review needed)

Inventory is idempotent — re-runs on the same folder skip already-uploaded images (matched by sha256), re-tag only if image changed.
