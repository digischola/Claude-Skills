# Accuracy & Sourcing Protocol

Universal protocol that applies to every skill, every research task, every data extraction. These rules exist because AI models become more confidently wrong as they get smarter — the "honesty gap." For work that informs real ad spend and client decisions, confident wrong answers cost money and trust.

---

## Rule 1: Blank When Uncertain

When analyzing any data source (Perplexity output, client docs, web research, CSV reports), if a data point is ambiguous, missing, contradictory, or you're not confident in the interpretation:

**Leave the field BLANK** and add a one-sentence explanation of WHY it's blank.

Do not:
- Present an estimate as fact
- Use national averages as local data without disclosure
- Fill gaps with "reasonable" assumptions
- Give confidence scores as an alternative (the AI can lie about confidence too)

Instead, give the user:
- A blank value
- A reason why it's blank
- Enough context to decide if they want to investigate further

**Example:**
```
Average CPA for this market: [BLANK — Perplexity provided a national average of $12.40 for restaurants, but no data specific to the Gurugram/NCR market. National figure may not reflect local competition.]
```

---

## Rule 2: 3x Penalty for Wrong Data

Internal framing: **a wrong data point is 3x more damaging than a blank field.**

Before filling any data point, ask:
- Is this directly stated in the source? → Fill it, label [EXTRACTED]
- Am I extrapolating from tangentially related data? → Leave blank or label [INFERRED] with evidence
- Would a different interpretation yield a different number? → Leave blank with explanation

This is especially critical for:
- **Benchmark numbers** (CPM, CPC, ROAS) — wrong benchmarks set wrong expectations
- **Competitor pricing** — wrong pricing leads to wrong positioning
- **Market size estimates** — wrong sizing leads to wrong budget recommendations
- **Audience demographics** — wrong demographics lead to wrong targeting
- **Financial data from client docs** — wrong extraction leads to wrong decisions

---

## Rule 3: Source Label Everything

Every finding across all outputs must carry one of two labels:

### [EXTRACTED]
The data point comes directly from the source document/tool with a citation. Strongest evidence level.

**Format:** `[EXTRACTED] Average CPC for restaurant keywords in Australia is $1.82 (source: WordStream 2024 benchmarks via Perplexity)`

### [INFERRED]
You derived this conclusion by synthesizing multiple data points, applying industry knowledge, or interpreting patterns. May be valid, but involves your judgment.

**Format:** `[INFERRED] Based on the 4.2 Google rating with 180 reviews (vs competitor average of 3.8), this business has a strong trust advantage for ad creative. (Evidence: Google review data from competitive analysis)`

### Mixed Sources
When a finding is part extracted, part inferred — label both parts separately. Both tags can appear in the same paragraph.

---

## Safety Net for Complex Tasks

Even when instructions say "only extract from source," AI will drift toward inferring on complex, multi-step tasks. To catch this:

- Add a source column/tag to every data point (EXTRACTED vs INFERRED)
- For INFERRED items, always include a one-sentence evidence trail
- This makes it easy to skim outputs: check the inferred items, trust the extracted ones

---

## Applying Across Skills

### In Research Skills (market-research, competitor analysis)
- Tag every finding in the markdown report
- Blank fields appear in reports with explanations (not silently omitted)
- Confidence ratings per section: HIGH / MEDIUM / LOW
- Dashboard source indicators: green dot = EXTRACTED, amber dot = INFERRED, dashed = BLANK

### In Ad Copy Skills (meta-ad-copywriter)
- Claims in ad copy should be backed by extracted data (don't invent statistics)
- If no social proof data exists, note it as a gap rather than fabricating numbers

### In Data Analysis Skills (performance reporting, CSV analysis)
- Every extracted metric gets a source label
- Calculated/derived metrics get [INFERRED] with formula shown
- Missing data cells stay blank with reason, not filled with averages

### In Document/Presentation Skills
- Facts cited in documents must trace back to a source
- Recommendations based on inferred patterns should be marked as such
