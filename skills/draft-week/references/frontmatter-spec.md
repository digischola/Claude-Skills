# frontmatter-spec

Required YAML frontmatter on every draft saved to `brand/queue/pending-approval/`. Scheduler-publisher reads these fields to decide what to ship and when.

## Required fields

| Field | Type | Values | Notes |
|---|---|---|---|
| `channel` | str | `linkedin` \| `x` \| `instagram` \| `facebook` \| `whatsapp` | Lowercase. |
| `format` | str | `text-post` \| `carousel` \| `thread` \| `tweet` \| `single` \| `reel` \| `caption` \| `status` \| `channel` \| `long-form` | Lowercase. |
| `entry_id` | str (8) | UUID prefix from idea-bank.json | Lookup key. |
| `pillar` | str | one of the 3 brand pillars | Exact match to pillars.md. |
| `voice_framework` | str | `Bush` \| `Hormozi` \| `Perell` \| `Naval` \| `Graham` \| `Schafer` (with descriptor in parens) | e.g., `Graham (Plain English)`. |
| `hook_pattern` | str | `'Category N #M (descriptor)'` | Pulled from hook-library.md. Quote because contains `#`. |
| `credential_anchored` | str | `none` \| `<credential_id>` | e.g., `thrive_188`. |
| `ai_theme_applied` | bool | `true` \| `false` | True if a named AI tool appears in the body. |
| `status` | str | `drafted` \| `repurposed` | Always `drafted` on initial save. |
| `validator_status` | str | `pending` \| `clean (NNN chars, exit 0)` \| `warnings (NNN, exit 1)` \| `BLOCKED` | Updated by validate_post.py. |
| `posting_status` | str | `scheduled` \| `posted` \| `manual_publish_overdue` \| `failed` | Set to `scheduled` on save; scheduler updates. |
| `scheduled_at` | str (ISO8601) | `'2026-05-04T09:00:00+05:30'` | Quote — has colons. IST timezone. |
| `scheduled_day` | str | `Mon` ... `Sun` (or full names) | Human-readable day. |

## Optional fields

| Field | Type | Notes |
|---|---|---|
| `repurpose_source` | str | Filename of source draft for repurposed variants. `null` for originals. |
| `repurposed_into` | list | Filenames of derived variants. `[]` until repurpose runs. |
| `posting_started_at` | str | Set by scheduler when notification fires. |
| `notified_at` | str | Set by scheduler on first notification. |
| `last_renotified_at` | str | Set on re-notification (cooldown gating). |
| `manual_overdue_at` | str | Set when notification cycle gives up. |
| `posted_at` | str | Set when scheduler confirms post. |
| `platform_url` | str | URL to live post. Read by performance-review. |
| `target_audience` | str | `global` \| `US` \| `AU` \| `SG` \| `IN` |
| `case_study_bundle` | str | If part of a case-study, references the bundle dir. |

## Example: LinkedIn text post

```yaml
---
channel: linkedin
format: text-post
entry_id: 3a3c9bac
pillar: Landing-Page Conversion Craft
voice_framework: Graham (Plain English)
hook_pattern: 'Category 1 #4 (counterintuitive benchmark anchored)'
credential_anchored: thrive_188
ai_theme_applied: false
status: drafted
validator_status: clean (1432 chars, exit 0)
posting_status: scheduled
scheduled_at: '2026-05-04T09:00:00+05:30'
scheduled_day: Monday
repurpose_source: null
repurposed_into: []
---
```

## Example: X thread (repurposed)

```yaml
---
channel: x
format: thread
entry_id: 3a3c9bac
pillar: Landing-Page Conversion Craft
voice_framework: Naval (Compression)
hook_pattern: 'Category 1 #4 (counterintuitive benchmark anchored)'
credential_anchored: thrive_188
ai_theme_applied: false
status: repurposed
validator_status: clean (8 tweets, exit 0)
posting_status: scheduled
scheduled_at: '2026-05-05T09:30:00+05:30'
scheduled_day: Tuesday
repurpose_source: 2026-05-04-3a3c9bac-linkedin-text-post.md
repurposed_into: []
---
```

## Anti-patterns

- Do NOT save a draft without `scheduled_at`. Scheduler ignores undated drafts.
- Do NOT use unquoted ISO timestamps — YAML breaks on colons.
- Do NOT mix channel and format inconsistently across same-week drafts.
- Do NOT set `posting_status: posted` manually — only the scheduler sets that.
