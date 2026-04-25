# Platform Adaptations — per-channel rules

How the shared 6-stage narrative arc maps to each of the 4 deliverables. Same content, different format constraints.

## LinkedIn Carousel (8-10 slides)

**Aspect:** 1080×1350 (4:5 portrait — feed-friendly)
**Total slides:** 8-10
**Visual style:** Digischola dark mode (#000 bg, #3B9EFF accent, Orbitron/Space Grotesk/Manrope), corner brackets, DIGISCHOLA logo

**Slide allocation:**
| Slide | Stage | Content |
|---|---|---|
| 1 | Hook | Headline metric (Orbitron 200pt+). Verbatim across all 4 deliverables. |
| 2 | Setup | Client + period + baseline. Brief mono-labeled data table. |
| 3 | Problem | The specific failure with quantified pain. |
| 4-6 | Fix | One change per slide (numbered 01/02/03). Big number + 1-2 line desc. |
| 7 | Result | The outcome metrics. BIG. Match Slide 1's hook. |
| 8 | Lesson | The takeaway in 1-2 lines. |
| 9 (opt) | CTA | Subtle question. |

**Caption (separate, posted with the carousel):** 150-300 chars summarizing the case + arrow to Slide 1.

**Anti-patterns:**
- Don't render internal IDs (entry_id, source_id) on slides
- Don't use Manrope for headings (body text only)
- Don't put the CTA on Slide 1 (kills hook strength)

## X Thread (8-12 tweets)

**Tweet length:** ≤280 chars each
**Total tweets:** 8-12 (12 is upper bound; longer threads see drop-off)
**Visual:** Optional 1-2 image attachments (e.g., before/after screenshot on Tweet 7)

**Tweet allocation:**
| Tweet | Stage | Content |
|---|---|---|
| 1 | Hook | Headline metric + 1-line summary. ≤280 chars. Must match LI Slide 1 verbatim. |
| 2-3 | Setup | Client + period + baseline. Compact. |
| 4 | Problem | The failure quantified. |
| 5 | Diagnosis | Where the friction was (1-2 sentences). |
| 6 | Fix #1 | First specific change. |
| 7 | Fix #2 | Second specific change. |
| 8 | Fix #3 | Third specific change. |
| 9 | Result | Outcome metrics. Match the hook. |
| 10 | Lesson | The takeaway. |
| 11 (opt) | CTA | Soft question or invitation to engage. |

**Anti-patterns:**
- Don't number tweets manually (X auto-shows 1/N)
- Don't link out in Tweet 1 (X de-prioritizes link-tweets); save links for end
- Don't break a single sentence across 2 tweets

## Blog Post (1500-2500 words)

**Format:** Markdown for digischola.in/blog OR LinkedIn newsletter
**Word count:** 1500-2500 (sweet spot 1800-2200)
**Visual:** 1 hero image, 1-2 charts/screenshots inline

**Section allocation:**
| H Level | Stage | Word target | Content |
|---|---|---|---|
| H1 | Hook | (title) | Headline metric — must match LI Slide 1 verbatim |
| Intro paragraph | Setup | 200-300 | Client + period + baseline. Pulls reader in. |
| H2 — The Problem | Problem | 300-400 | The failure. Why standard advice didn't fix it. |
| H2 — Diagnosis | Diagnosis | 300-400 | The investigative process. Root causes. |
| H2 — The Fix: Three Changes | Fix | 600-800 | Three H3 subsections, one per change. Each H3 is 200-300 words. |
| H2 — The Result | Result | 200-300 | Outcome metrics. Trend description. Chart caption if image. |
| H2 — What This Means For You | Lesson | 200-300 | The generalized insight. |
| Closing paragraph | CTA (opt) | 50-100 | Soft question or "if you want a similar audit, here's how to reach me" |

**Anti-patterns:**
- Don't use academic / corporate tone — this is Mayank's voice (operator, performance-credibility)
- Don't include >3 changes in Fix
- Don't end with "thanks for reading" or "follow me" — that's bait

## Instagram Carousel (8-10 slides)

**Aspect:** 1080×1350 (4:5 portrait)
**Total slides:** 8-10
**Visual style:** Same Digischola brand BUT visual-heavier (more whitespace, bigger numbers, less text per slide)

**Slide allocation (similar to LI but bigger numbers / less text):**
| Slide | Stage | Content |
|---|---|---|
| 1 | Hook | THE BIG NUMBER (Orbitron 280pt+). Single hook line below. |
| 2 | Setup | 1 line of client context. Visual-led. |
| 3 | Problem | 1 contrarian sentence. Big type. |
| 4-6 | Fix | One change per slide. Number 01/02/03 huge, 1-line description. |
| 7 | Result | Outcome numbers HUGE. Match hook. |
| 8 | Lesson | Short takeaway, big type. |
| 9 (opt) | Logo + CTA | DIGISCHOLA logo + soft question. |

**Caption (separate, posted with the carousel):** 100-200 chars + 5-10 hashtags
- Hashtags: #LandingPageOptimization #CRO #DigitalMarketing #WellnessMarketing (depends on pillar)

**Anti-patterns:**
- Don't put more than 1-2 sentences per slide (IG audience scrolls fast)
- Don't use long horizontal text (vertical / center-stacked is the IG aesthetic)
- Don't include data tables (too dense for IG)

## Cross-deliverable consistency rules

These MUST be identical across all 4:

1. **Headline metric** (e.g., "188%") — verbatim in LI Slide 1, X Tweet 1, Blog H1, IG Slide 1
2. **All numbers referenced** (e.g., "21% CTR", "1.2% conversion", "37% lower CPS") — same numbers, same precision
3. **Client identifier** (named OR anonymized) — same form everywhere
4. **The 3 changes** — same 3, same order, same wording (per-platform brevity OK)
5. **The lesson** — same core insight, even if phrased differently per platform
6. **Pillar tag** — all 4 frontmatter has the same pillar slug

`validate_case_study.py` enforces these.

## Suggested scheduling cadence

When all 4 deliverables are ready:
- LI carousel: Mon 09:00 IST (peak engagement)
- X thread: Tue 11:00 IST (separate day so audience overlap doesn't cause fatigue)
- Blog post: Wed 18:00 IST (newsletter window)
- IG carousel: Sat 10:00 IST (weekend visual scroll)

Spread over a week so each gets full visibility, with cross-promotion (blog can be linked from a Tweet 11; IG bio can mention "blog post in profile link").
