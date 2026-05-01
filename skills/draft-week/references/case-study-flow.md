# case-study-flow

Detailed steps for `draft-week case-study`. Loaded only when bundling a 4-deliverable case study.

## Inputs

- One `client-win` entry from `idea-bank.json` with quantified outcome.
- Required fields on entry: client_handle, metrics (specific numbers), context (what was changed), result (outcome).

If any required field is BLANK per accuracy-protocol, abort with: "Missing <field>. Capture more detail before bundling case study."

## The shared narrative arc (Setup → Problem → Diagnosis → Fix → Result → Lesson)

Build this once, then adapt to 4 deliverables.

| Beat | Length | Content |
|---|---|---|
| Setup | 1-2 lines | Who the client is (anonymized handle), what category. |
| Problem | 2-4 lines | The specific bottleneck. Quantify before-state. |
| Diagnosis | 3-5 lines | What you saw, framework you applied. |
| Fix | 4-6 lines | Specific changes made. Use "before / after" pairs. |
| Result | 2-3 lines | After-state metrics. Match accuracy-protocol — exact numbers. |
| Lesson | 1-2 lines | The transferable insight (this is the hook for next case). |

## Deliverables

### 1. LinkedIn carousel (8-10 slides)

| Slide | Content |
|---|---|
| 1 (cover) | Hook headline + outcome metric. ≤120 chars. Big text. |
| 2 | Setup — client + context. |
| 3 | Problem — quantified before-state. |
| 4 | Diagnosis — framework callout. |
| 5-7 | Fix — specific changes (one per slide). |
| 8 | Result — after-state metrics. |
| 9 | Lesson — the takeaway. |
| 10 (CTA) | Soft CTA — "DM if you have a similar LP." |

Caption: 600-1000 chars, hook from slide 1, body teases the carousel, CTA.

### 2. X thread (8-12 tweets)

```
Tweet 1: Hook + headline metric
Tweet 2: Setup
Tweet 3: Problem
Tweet 4-5: Diagnosis
Tweet 6-9: Fix (one change per tweet)
Tweet 10: Result
Tweet 11: Lesson
Tweet 12: Soft CTA + thread anchor reference
```

Each tweet 200-270 chars. Use `## Tweet N` headers.

### 3. Long-form blog (1500-2500 words)

For LinkedIn newsletter or `digischola.in/blog`. Structure:

- H1 = Lesson framed as a question or claim
- H2 sections matching the narrative arc
- Inline data callouts for before/after metrics
- A "What I'd do differently" section between Fix and Result (only blog-exclusive)
- Closing CTA: link to a related post or LP audit offer

### 4. Instagram carousel (8-10 slides)

Same structure as LI carousel but visual-first. Heavier image, lighter text per slide. Caption ≤2200 chars but ≤400 sweet spot.

## Coordination manifest

Save all 4 deliverables in `brand/queue/pending-approval/case-study-<entry_id>/` directory. Add a `manifest.json`:

```json
{
  "entry_id": "<id>",
  "case_name": "<short slug>",
  "deliverables": [
    {"channel": "linkedin", "format": "carousel", "file": "linkedin-carousel.md", "scheduled_at": "..."},
    {"channel": "x", "format": "thread", "file": "x-thread.md", "scheduled_at": "..."},
    {"channel": "blog", "format": "long-form", "file": "blog.md", "scheduled_at": "..."},
    {"channel": "instagram", "format": "carousel", "file": "instagram-carousel.md", "scheduled_at": "..."}
  ],
  "shared_hook": "<hook text>",
  "shared_metrics": ["+188%", "-37%"],
  "shared_lesson": "<lesson text>"
}
```

Schedule deliverables 1-3 days apart, not the same day.

## Validation

Run `validate_post.py` on each `.md` file. All four must pass exit 0 or 1.

Cross-check: hook and metrics must match across all 4 deliverables. If a metric is "+188%" in one and "+190%" in another, FAIL — recheck the entry for the canonical number.

## Anti-patterns

- Do NOT reuse a case study published in the last 90 days.
- Do NOT use the real client name unless the entry has explicit consent flag.
- Do NOT round metrics inconsistently across deliverables.
- Do NOT ship a case study without a "lesson" — that's the part that compounds for future content.
