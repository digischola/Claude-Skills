# Client Wiki Schema (Dynamic Page Model)

Every client gets a persistent wiki — a living knowledge base that compounds across sessions and skills. Based on the LLM Wiki pattern.

---

## Per-Client Folder Structure

```
{Client Name}/
├── {Business Name}/
│   ├── {presentable}.html          ← Final outputs for client/team (HTML/PDF/MP4 at folder root)
│   ├── {presentable}.pdf
│   └── _engine/                    ← Skill internals (everything Mayank doesn't double-click)
│       ├── sources/                ← Raw, immutable inputs
│       │   ├── website-crawl-YYYY-MM-DD.json
│       │   ├── client-brief.md
│       │   ├── perplexity-YYYY-MM-DD.md
│       │   └── ...
│       ├── wiki/                   ← LLM-maintained, compounds over time
│       │   ├── index.md            ← Content catalog with page registry
│       │   ├── log.md              ← Append-only chronological record
│       │   ├── business.md         ← Business fundamentals (owner: business-analysis)
│       │   ├── brand-identity.md   ← Brand colors, fonts, voice (owner: business-analysis)
│       │   ├── digital-presence.md ← Digital audit (owner: business-analysis)
│       │   ├── offerings.md        ← All offerings documented (owner: business-analysis)
│       │   ├── market.md           ← Added by market-research skill
│       │   ├── competitors.md      ← Added by market-research skill
│       │   ├── audience.md         ← Added by market-research skill
│       │   ├── benchmarks.md       ← Added by market-research skill
│       │   ├── strategy-implications.md ← Added by market-research skill
│       │   └── {any-new-page}.md   ← Added by any skill as needed
│       ├── working/                ← Intermediate skill output (md reports, json briefs)
│       ├── brand-config.json       ← Skill-managed config files
│       └── wiki-config.json        ← Wiki metadata with dynamic page registry
```

---

## Dynamic Page Model

### How It Works
- Business analysis creates base pages during init (business, brand-identity, digital-presence, offerings)
- Any skill can add new pages by:
  1. Creating the .md file in `_engine/wiki/`
  2. Registering it in `_engine/wiki-config.json` under "pages"
  3. Adding an entry to index.md under "Dynamic Pages"
  4. Logging the creation in log.md

### Adding a Page (for any skill)
```python
# 1. Create the page file
wiki_dir / "new-page.md"  # with standard template (wiki_dir = _engine/wiki/)

# 2. Register in _engine/wiki-config.json
config["pages"]["new-page"] = {
    "title": "Page Title",
    "owner": "skill-name",
    "created": today,
    "last_updated": today,
}

# 3. Add to index.md under Dynamic Pages
# - [Page Title](new-page.md) — Summary — Last updated: date — Owner: skill-name

# 4. Log in log.md
# - **ADD PAGE** new-page.md created by skill-name
```

### Page Ownership
- The "owner" skill is responsible for the page's structure and primary content
- Any skill can UPDATE any page (add findings, update sections)
- When updating another skill's page, log the change with your skill name

---

## Wiki Page Format (All Pages)

```markdown
# {Page Title}

> Last updated: {date} | Sources: {count} | Confidence: {HIGH/MEDIUM/LOW}

## Key Findings
{Bulleted findings with [EXTRACTED] or [INFERRED] labels}

## Details
{Deeper analysis by sub-topic}

## Gaps & Unknowns
{BLANK fields with reasons — carried forward until filled}

## Marketing Implications
{What this means for campaigns}

## Change History
- {date}: Initial creation by {skill-name} from {source}
- {date}: Updated {section} by {skill-name} from {source}
```

---

## Key Principles

1. **Sources are immutable.** Raw inputs in `_engine/sources/` never get modified.
2. **Wiki pages compound.** New data updates existing pages — doesn't replace them.
3. **Gaps carry forward.** BLANK fields stay visible until filled by new data.
4. **Cross-references.** Pages link to each other when findings overlap.
5. **Source traceability.** Every claim traces back to a specific source file.
6. **One wiki per business.** Different businesses for the same client get separate wikis.
7. **Dynamic growth.** Any skill can add pages. The wiki grows with the relationship.
8. **Offerings scope downstream.** Market research, ad copy, campaign strategy all operate per-offering within the shared wiki.
