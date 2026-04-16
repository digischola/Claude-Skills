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
├── wiki/
│   ├── index.md
│   ├── log.md
│   ├── business.md
│   ├── brand-identity.md
│   ├── digital-presence.md
│   ├── offerings.md
│   ├── strategy.md          ← research lives here
│   └── ...
├── deliverables/
│   ├── brand-config.json
│   ├── {name}-market-research.md
│   └── {name}-research-dashboard.html
├── sources/
└── wiki-config.json
```

### Multi-Program
```
Desktop/{Client Name}/
├── _shared/                          ← shared brand DNA (created by business-analysis)
│   ├── wiki/
│   │   ├── index.md                  ← master index linking all programs
│   │   ├── log.md                    ← shared-level changes only
│   │   ├── business.md               ← core business DNA
│   │   ├── brand-identity.md         ← visual identity, fonts, colors
│   │   ├── digital-presence.md       ← website, social, analytics
│   │   └── offerings.md              ← all offerings overview (links to program wikis)
│   ├── deliverables/
│   │   └── brand-config.json         ← single source of truth for brand
│   └── wiki-config.json              ← type: "shared", programs: [list]
│
├── {Program 1 Name}/                 ← per-program research
│   ├── wiki/
│   │   ├── index.md                  ← program-specific index
│   │   ├── log.md                    ← program-specific changes
│   │   ├── strategy.md               ← market research for this program
│   │   └── ...                       ← any dimension pages needed
│   ├── deliverables/
│   │   ├── {program}-market-research.md
│   │   └── {program}-research-dashboard.html
│   ├── sources/
│   └── wiki-config.json              ← type: "program", parent: "../_shared"
│
├── {Program 2 Name}/
│   ├── wiki/
│   ├── deliverables/
│   ├── sources/
│   └── wiki-config.json
```

---

## What Lives Where

| Content | Single-Program | Multi-Program |
|---|---|---|
| Brand colors, fonts, logo | `deliverables/brand-config.json` | `_shared/deliverables/brand-config.json` |
| Business fundamentals | `wiki/business.md` | `_shared/wiki/business.md` |
| Brand identity | `wiki/brand-identity.md` | `_shared/wiki/brand-identity.md` |
| Digital presence | `wiki/digital-presence.md` | `_shared/wiki/digital-presence.md` |
| Offerings overview | `wiki/offerings.md` | `_shared/wiki/offerings.md` |
| Market research / strategy | `wiki/strategy.md` | `{Program}/wiki/strategy.md` |
| Keyword data | `sources/keyword_data_*.json` | `{Program}/sources/keyword_data_*.json` |
| Perplexity research | `sources/perplexity-*.md` | `{Program}/sources/perplexity-*.md` |
| Report + dashboard | `deliverables/` | `{Program}/deliverables/` |
| Competitor audit | `wiki/strategy.md` | `{Program}/wiki/strategy.md` |

**Rule:** Anything that's the same across all programs → `_shared/`. Anything that changes per program → `{Program}/`.

---

## Detection Logic (for skills)

### Step 1 of any skill:
```
1. User provides client name + program name (or just client name)
2. Check Desktop/{Client Name}/ exists
   a. If not → new client, ask: single program or multi-program?
   b. If yes → check for _shared/ folder
      - _shared/ exists → multi-program client, ask which program
      - _shared/ doesn't exist → single-program client
        - If user wants a NEW program → convert to multi-program (see Migration below)
3. Set working paths:
   - shared_dir = _shared/ (or root if single-program)
   - program_dir = {Program Name}/ (or root if single-program)
   - brand_config = shared_dir/deliverables/brand-config.json
   - wiki_dir = program_dir/wiki/
```

### Reading brand config:
- Single-program: `{client-folder}/deliverables/brand-config.json`
- Multi-program: `{client-folder}/_shared/deliverables/brand-config.json`
- Skills always check `_shared/` first, fall back to root

---

## Migration: Single → Multi-Program

When an existing single-program client needs a second program:

1. Create `_shared/` directory with wiki/, deliverables/ subfolders
2. **Move** (not copy) shared files from existing program folder to `_shared/`:
   - `wiki/business.md` → `_shared/wiki/business.md`
   - `wiki/brand-identity.md` → `_shared/wiki/brand-identity.md`
   - `wiki/digital-presence.md` → `_shared/wiki/digital-presence.md`
   - `wiki/offerings.md` → `_shared/wiki/offerings.md`
   - `deliverables/brand-config.json` → `_shared/deliverables/brand-config.json`
3. Create `_shared/wiki/index.md` (master index)
4. Create `_shared/wiki-config.json` with `type: "shared"`
5. Update existing program's `wiki-config.json` with `type: "program"`, `parent: "../_shared"`
6. Create new program folder with init_wiki.py `--program` flag
7. Log migration in both `_shared/wiki/log.md` and existing program's `wiki/log.md`

---

## Wiki Config Schema

### Shared config (`_shared/wiki-config.json`):
```json
{
  "type": "shared",
  "business_name": "Client Business",
  "created": "2026-04-12",
  "last_updated": "2026-04-12",
  "programs": ["Program 1", "Program 2"],
  "brand_config": "deliverables/brand-config.json",
  "pages": ["business", "brand-identity", "digital-presence", "offerings"]
}
```

### Program config (`{Program}/wiki-config.json`):
```json
{
  "type": "program",
  "program_name": "Program 1",
  "business_name": "Client Business",
  "parent": "../_shared",
  "created": "2026-04-12",
  "last_updated": "2026-04-12",
  "sources_ingested": 0,
  "brand_config": "../_shared/deliverables/brand-config.json",
  "pages": ["strategy"]
}
```

---

## Cross-Program Intelligence

When running research for Program 2 after Program 1 is complete:
- Check Program 1's strategy.md for reusable insights (market size, PESTEL, some buyer personas may overlap)
- Flag shared findings with `[SHARED from {Program 1}]` tag
- Don't duplicate — reference: "See {Program 1}/wiki/strategy.md Section 3 for PESTEL analysis (applies to both programs)"
- Each program gets its own competitor table, keyword data, and benchmarks — never share these

---

## Downstream Skill Behavior

All downstream skills (paid-media-strategy, meta-ad-copywriter, etc.) must:
1. Read brand from `_shared/` (or root for single-program)
2. Read program-specific strategy from `{Program}/wiki/`
3. Output deliverables to `{Program}/deliverables/`
4. Reference both shared business context AND program-specific research
