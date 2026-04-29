# Multi-Program Client Structure

When a client has multiple programs, products, or business lines that need independent research, the folder structure splits into **shared** (brand DNA) and **per-program** (research, strategy, deliverables).

---

## When to Use Multi-Program Structure

**Use multi-program when:**
- Client launches a new product/service line with different competitors, keywords, or audience
- Client has distinct business divisions (e.g., B2C retail + B2B wholesale)
- Client operates multiple brands under one parent company
- User explicitly says "run analysis for [specific program]" on an existing client

**Stay single-program when:**
- Single product with multiple audience segments (handle via segment filters in paid-media-strategy)
- Same product, different geographies (handle via location targeting)
- Minor product variations (e.g., color options, sizes)

**Decision test:** "Would the competitor list change?" If yes → multi-program. If no → single-program with segment filters.

---

## Folder Structure

### Single-Program (default)
```
Desktop/{Client Name}/{Business Name}/
├── {name}-research-dashboard.html    ← presentables at folder root
└── _engine/
    ├── wiki/
    │   ├── index.md
    │   ├── log.md
    │   ├── business.md
    │   ├── brand-identity.md
    │   ├── digital-presence.md
    │   ├── offerings.md
    │   ├── strategy.md               ← research lives here
    │   └── ...
    ├── working/
    │   └── {name}-market-research.md
    ├── sources/
    ├── brand-config.json
    └── wiki-config.json
```

### Multi-Program
```
Desktop/{Client Name}/
├── _engine/                              ← client-wide internals (formerly `_shared/`)
│   ├── wiki/
│   │   ├── index.md                      ← master index linking all programs
│   │   ├── log.md                        ← client-wide changes only
│   │   ├── business.md                   ← core business DNA
│   │   ├── brand-identity.md             ← visual identity, fonts, colors
│   │   ├── digital-presence.md           ← website, social, analytics
│   │   └── offerings.md                  ← all offerings overview (links to program wikis)
│   ├── brand-config.json                 ← single source of truth for brand
│   └── wiki-config.json                  ← type: "shared", programs: [list]
│
├── {Program 1 Name}/                     ← per-program research
│   ├── {program}-research-dashboard.html ← program presentables at program root
│   └── _engine/
│       ├── wiki/
│       │   ├── index.md                  ← program-specific index
│       │   ├── log.md                    ← program-specific changes
│       │   ├── strategy.md               ← market research for this program
│       │   └── ...                       ← any dimension pages needed
│       ├── working/
│       │   └── {program}-market-research.md
│       ├── sources/
│       └── wiki-config.json              ← type: "program", parent: "../_engine"
│
├── {Program 2 Name}/
│   ├── {program}-research-dashboard.html
│   └── _engine/
│       ├── wiki/
│       ├── working/
│       ├── sources/
│       └── wiki-config.json
```

---

## What Lives Where

| Content | Single-Program | Multi-Program |
|---|---|---|
| Brand colors, fonts, logo | `_engine/brand-config.json` | `_engine/brand-config.json` (at client root) |
| Business fundamentals | `_engine/wiki/business.md` | `_engine/wiki/business.md` (at client root) |
| Brand identity | `_engine/wiki/brand-identity.md` | `_engine/wiki/brand-identity.md` (at client root) |
| Digital presence | `_engine/wiki/digital-presence.md` | `_engine/wiki/digital-presence.md` (at client root) |
| Offerings overview | `_engine/wiki/offerings.md` | `_engine/wiki/offerings.md` (at client root) |
| Market research / strategy | `_engine/wiki/strategy.md` | `{Program}/_engine/wiki/strategy.md` |
| Keyword data | `_engine/sources/keyword_data_*.json` | `{Program}/_engine/sources/keyword_data_*.json` |
| Perplexity research | `_engine/sources/perplexity-*.md` | `{Program}/_engine/sources/perplexity-*.md` |
| Markdown report (internal) | `_engine/working/` | `{Program}/_engine/working/` |
| HTML dashboard (presentable) | folder root | `{Program}/` (program root) |
| Competitor audit | `_engine/wiki/strategy.md` | `{Program}/_engine/wiki/strategy.md` |

**Rule:** Anything that's the same across all programs → client-root `_engine/`. Anything that changes per program → `{Program}/_engine/`.

---

## Detection Logic (for skills)

### Step 1 of any skill:
```
1. User provides client name + program name (or just client name)
2. Check Desktop/{Client Name}/ exists
   a. If not → new client, ask: single program or multi-program?
   b. If yes → check for _engine/wiki-config.json with type: "shared"
      - Shared config exists → multi-program client, ask which program
      - Doesn't exist → single-program client
        - If user wants a NEW program → convert to multi-program (see Migration below)
3. Set working paths:
   - client_engine = {Client}/_engine/ (client-wide for multi-program; equals scope_engine for single-program)
   - scope_engine = {Program}/_engine/ for multi-program; {Client}/{Business}/_engine/ for single-program
   - brand_config = client_engine/brand-config.json
   - wiki_dir = scope_engine/wiki/
```

### Reading brand config:
- Single-program: `{client-folder}/{business}/_engine/brand-config.json`
- Multi-program: `{client-folder}/_engine/brand-config.json` (at the client root)
- Skills always check the client-root `_engine/` first, fall back to scope `_engine/`

---

## Migration: Single → Multi-Program

When an existing single-program client needs a second program:

1. Create the client-root `_engine/` directory with wiki/ subfolder
2. **Move** (not copy) shared files from existing program's `_engine/` to the client-root `_engine/`:
   - `{Business}/_engine/wiki/business.md` → `{Client}/_engine/wiki/business.md`
   - `{Business}/_engine/wiki/brand-identity.md` → `{Client}/_engine/wiki/brand-identity.md`
   - `{Business}/_engine/wiki/digital-presence.md` → `{Client}/_engine/wiki/digital-presence.md`
   - `{Business}/_engine/wiki/offerings.md` → `{Client}/_engine/wiki/offerings.md`
   - `{Business}/_engine/brand-config.json` → `{Client}/_engine/brand-config.json`
3. Create `{Client}/_engine/wiki/index.md` (master index)
4. Create `{Client}/_engine/wiki-config.json` with `type: "shared"`
5. Update existing program's `_engine/wiki-config.json` with `type: "program"`, `parent: "../_engine"`
6. Create new program folder with init_wiki.py `--program` flag
7. Log migration in both `{Client}/_engine/wiki/log.md` and existing program's `_engine/wiki/log.md`

---

## Wiki Config Schema

### Shared config (`{Client}/_engine/wiki-config.json`):
```json
{
  "type": "shared",
  "business_name": "Client Business",
  "created": "2026-04-12",
  "last_updated": "2026-04-12",
  "programs": ["Program 1", "Program 2"],
  "brand_config": "brand-config.json",
  "pages": ["business", "brand-identity", "digital-presence", "offerings"]
}
```

### Program config (`{Program}/_engine/wiki-config.json`):
```json
{
  "type": "program",
  "program_name": "Program 1",
  "business_name": "Client Business",
  "parent": "../../_engine",
  "created": "2026-04-12",
  "last_updated": "2026-04-12",
  "sources_ingested": 0,
  "brand_config": "../../_engine/brand-config.json",
  "pages": ["strategy"]
}
```

---

## Cross-Program Intelligence

When running research for Program 2 after Program 1 is complete:
- Check Program 1's strategy.md for reusable insights (market size, PESTEL, some buyer personas may overlap)
- Flag shared findings with `[SHARED from {Program 1}]` tag
- Don't duplicate — reference: "See {Program 1}/_engine/wiki/strategy.md Section 3 for PESTEL analysis (applies to both programs)"
- Each program gets its own competitor table, keyword data, and benchmarks — never share these

---

## Downstream Skill Behavior

All downstream skills (paid-media-strategy, meta-ad-copywriter, etc.) must:
1. Read brand from `{Client}/_engine/brand-config.json` (multi-program) or `{Client}/{Business}/_engine/brand-config.json` (single-program)
2. Read program-specific strategy from `{Program}/_engine/wiki/`
3. Output presentables (HTML/PDF/MP4) to the program folder root; output internals (md reports, json briefs) to `{Program}/_engine/working/`
4. Reference both shared business context AND program-specific research
