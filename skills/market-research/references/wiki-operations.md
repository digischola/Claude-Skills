# Wiki Operations

Three core operations that maintain the client wiki. These can be triggered explicitly or as part of the market-research skill workflow.

---

## 1. INGEST — Process New Source Material

**When:** New data arrives (Perplexity output, CSV export, client brief, campaign performance data, call notes)

**Process:**

1. Save the raw source to `sources/` with descriptive filename and date: `perplexity-2026-04-07.md`, `google-ads-march-2026.csv`, `client-brief-initial.md`

2. Read the source material completely. On first pass, identify which wiki pages are affected.

3. For each affected wiki page:
   - Read the current page
   - Identify what's new, what updates existing data, what contradicts existing data
   - **New data** → add to relevant section with source label and source reference
   - **Updated data** → replace old value, note the change in Change History ("Updated CPC from $5-15 estimate to $8.40 actual — source: google-ads-march-2026.csv")
   - **Contradictory data** → flag both values, note the contradiction, keep both until resolved
   - **Gap-filling data** → move item from Gaps & Unknowns to the relevant section, update confidence rating

4. Apply accuracy protocol on every data point being added:
   - [EXTRACTED] with source file reference
   - [INFERRED] with evidence trail
   - BLANK stays blank until real data arrives

5. Update `log.md` with what changed
6. Update `index.md` with new source and updated page summaries
7. Update `wiki-config.json` (last_updated, sources_ingested count)

**Source Type Handling:**

| Source Type | What to Extract | Wiki Pages Affected |
|---|---|---|
| Perplexity research | All 6 dimensions | All pages (initial creation or major update) |
| Google Ads CSV | CPC, CTR, conversions, search terms | benchmarks.md, audience.md, strategy.md |
| Meta Ads CSV | CPM, ROAS, audience insights, creative performance | benchmarks.md, audience.md, strategy.md |
| Client brief/call notes | Business context, goals, constraints | business.md, strategy.md |
| Competitor discovery | New competitor info, ad library findings | competitors.md, strategy.md |
| Google Business Profile | Reviews, ratings, local presence | digital-presence.md, competitors.md |

---

## 2. QUERY — Ask Questions Against the Wiki

**When:** User asks a strategic question, needs a synthesis, or wants to generate content from existing knowledge

**Process:**

1. Read relevant wiki pages (use index.md to identify which pages to load)
2. Synthesize an answer from existing wiki knowledge
3. Apply accuracy protocol — if the answer requires data the wiki doesn't have, say so
4. Optionally write the synthesis as a new section in strategy.md or a standalone deliverable in deliverables/

**Example queries:**
- "What messaging angles haven't we tested for CrownTech?"
- "Compare CrownTech's actual CPC to the initial estimates"
- "What are the top 3 positioning gaps based on everything we know?"
- "Generate a creative brief based on the wiki" (→ output to deliverables/, feeds into meta-ad-copywriter)

**Key rule:** Queries read from the wiki but can also write back. If a query produces a useful synthesis, offer to save it as a strategy update.

---

## 3. LINT — Health-Check the Wiki

**When:** Periodically (every 3-4 sessions with a client), or when the user asks, or during session wrap-up

**Process:**

Check for:

1. **Stale data** — findings older than 6 months in fast-moving dimensions (benchmarks, competitors, digital presence). Flag for refresh.

2. **Contradictions** — two wiki pages claiming different things about the same data point. Resolve or flag.

3. **Orphan data** — findings that don't connect to any marketing implication. Either add the "so what" or mark for review.

4. **Persistent gaps** — BLANK fields that have been blank across 3+ source ingestions. Escalate — these may need targeted research.

5. **Confidence decay** — sections rated HIGH confidence that are now 6+ months old should be downgraded to MEDIUM until refreshed.

6. **Cross-reference integrity** — if competitors.md mentions a competitor that should affect strategy.md, verify the connection exists.

**Output:** A lint report appended to log.md with findings and recommended actions:

```markdown
## {date} — LINT REPORT
- STALE: benchmarks.md CPC data is from April 2026, now 6 months old → recommend refresh
- CONTRADICTION: audience.md says primary age 25-44 but Meta Ads CSV shows 35-54 performing best → resolve
- GAP: competitors.md still has BLANK for Competitor X pricing after 3 ingestions → needs manual research
- OK: business.md, market.md, strategy.md — no issues found
```

---

## Operation Triggers in Skill Workflow

| Skill Step | Wiki Operation | What Happens |
|---|---|---|
| Step 3 (Analyze Perplexity) | INGEST | Parse output into wiki pages |
| Step 5 (Generate Report) | QUERY | Synthesize report from wiki data |
| Step 6 (Generate Dashboard) | QUERY | Build dashboard JSON from wiki data |
| Step 8 (Session Wrap-up) | LINT (light) | Quick check for contradictions and gaps |
| User drops a CSV | INGEST | Update benchmarks + audience from performance data |
| User asks a question | QUERY | Answer from wiki, optionally write back |
| Every 3-4 sessions | LINT (full) | Comprehensive health check |
