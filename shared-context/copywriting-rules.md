# Copywriting Rules — Universal

Status: KERNEL · applies to ALL skills that produce written or spoken content, across BOTH the personal-brand track AND the client-skills track.

Read this file at the start of any skill run that produces:
- Ad copy (Google RSA, Meta primary text/headlines)
- Voice-overs / video scripts
- Landing-page copy (hero, body, CTA, microcopy)
- Social posts (any channel, any client)
- Email / WhatsApp message copy
- Carousel slides, Reel captions, infographic text

These rules are universal. They apply equally to a B2B SaaS founder, a wellness retreat, a Hindu temple event, and a fitness coach. They apply regardless of brand voice. **Brand voice traits (em-dash policy, hype-word tolerance, register choices) live in each brand's own voice file. These rules sit above all of that.**

---

## Rule 0 — User-Relevance (always run first)

**Test every word with: does the BUYER care about this, or am I adding it because it makes US look complete?**

If only the seller cares — cut it entirely. Don't fix it, don't reword it, don't rephrase it. Cut.

### Why this is rule 0
It's the cheapest filter. Cutting an irrelevant claim takes one keystroke. Fixing it takes five rounds of revision and still produces seller-side noise.

### Common failures (real examples that have shipped)

| Seller-side noise | Why the buyer doesn't care | Action |
|---|---|---|
| "Razorpay UPI" / "paid via Razorpay" | They learn the gateway at checkout. It does not increase their willingness to buy | Cut |
| "Production HTML" / "HTML + copy" / "responsive code" | They want a thing that works on their site, not a file-format spec | Cut or replace with outcome ("ready to plug into your site") |
| "Six audits a week" (capacity stat) | They read it as "you have inventory" not "I am scarce — buy now" | Replace with scarcity framing ("Six slots open this week") |
| "InitiateCheckout optimized" / "Conversion API installed" | Internal media-buying jargon | Cut from public-facing copy entirely |
| "Built with React/Tailwind/Lovable" | They want a working page, not a tech stack | Cut |
| "We use the latest AI tools" | Vague seller flex | Cut, OR replace with what the buyer gets ("audit done in 24h instead of 2 weeks") |

### What survives Rule 0 (and should)

Anything the buyer USES TO DECIDE: their pain, their outcome, their trust shortcuts (named credentials), price, timeline, risk reversal, named results.

**Example contrast (same product, both are accurate):**
- Seller-side: `Custom hero rebuild · HTML + copy · Razorpay UPI · 7-day refund window`
- Buyer-side: `New hero, ready to ship · ₹4,999 · 24 hours · full refund if I miss`

---

## Rule 1 — Context-Completeness

**Every claim must answer "X of WHAT?" without leaning on the prior sentence or the on-screen visual.**

Crisp delivery is fine. **Stripped delivery is not.** A claim that only makes sense if the viewer already has context fails this rule.

### Test
Read the claim aloud in isolation. If a stranger asks "what?" — the claim is incomplete.

### Common failures

| Stripped claim | Stranger's reaction | Fixed |
|---|---|---|
| "10+ years" | 10+ years of WHAT? | `10+ years in paid media` |
| "200 audits" | audits of WHAT? | `200+ landing pages audited` |
| "$1B+ ad spend" | spent how? on what? | `$1B+ in ad spend managed` |
| "Drop your URL" | for WHAT? | `Drop your URL to start` |
| "7-day refund" | refund of WHAT? | `7-day money-back` or `Full refund if I miss` |
| "28 findings" | findings about WHAT? | `28 ranked findings on your page` |

### When in doubt
A chip in a sound-off feed view, a banner pulled out of context, a screenshot of one slide — these all break carry-forward. Build every claim to stand alone.

---

## Rule 2 — Spoken Cadence (anti-staccato)

**Applies to: every spoken-delivery context — VOs, Reels, podcasts, video ads, TTS narration.**
Does NOT apply to written long-form (LinkedIn paragraphs, blog posts) where staccato can be deliberate emphasis.

**Don't deliver claims as comma-separated noun-phrase bullets when spoken.** Connect them with verbs, conjunctions, prepositions. Bullet-spoken language sounds like reading slides, not narrating.

### Failure pattern
Three or more 1–3-word noun-phrase fragments in a row, separated by periods, with no connective tissue.

### Examples

| Bullet-spoken (wrong for VO) | Connected (right for VO) |
|---|---|
| `Google. Accenture. The rest.` | `Performance marketer for Google, Accenture, and others.` |
| `Hero rebuild included. Razorpay UPI.` | (cut entirely per Rule 0) |
| `₹4,999. Twenty-four hours. Submit your URL.` | `₹4,999, twenty-four hours. Drop your URL to start.` |
| `Six audits per week. Two left.` | `Six slots a week, two left this week.` |

### Exception — deliberate emphasis
Three short claims CAN work spoken IF each is a complete sentence with subject/verb context:
- `Ex-Google performance marketer.` (role)
- `Ten plus years in paid media.` (tenure + discipline)
- `One billion dollars in ad spend managed.` (scale + verb)

Each fragment is a full claim, not a noun phrase. The cadence reads as deliberate, not bullet-list.

---

## Rule 3 — Specific Anchors over Generic Adjectives

**Replace generic praise words with the specific number, named tool, or named entity that proves the claim.**

### Failure → fix examples

| Generic | Specific anchor |
|---|---|
| "extensive experience" | `$1B+ in ad spend managed` |
| "many clients" | `200+ landing pages audited` |
| "fast turnaround" | `24 hours` |
| "robust toolkit" | (name the actual tool, or cut) |
| "proven results" | `+188% Meta sales · +37% lower CPA` (one real result, anonymized per attribution rules) |
| "AI-powered" | `audit done in 20 minutes instead of 2 weeks` (the time-savings IS the AI claim) |

### Why this rule comes after Rule 0
You can have specific anchors that are still seller-side noise. "Built with Tailwind v3.4" is specific AND irrelevant. Run Rule 0 first to cut the irrelevance, then Rule 3 to swap remaining vagueness for specifics.

---

## Rule order is not optional

Apply in this order on every draft:

1. **Rule 0 — User-Relevance** (cut the irrelevant)
2. **Rule 1 — Context-Completeness** (anchor every claim)
3. **Rule 2 — Spoken Cadence** (only for spoken contexts; flow the connections)
4. **Rule 3 — Specific Anchors** (swap generic for specific)

Then apply brand-specific voice rules (em-dash policy, hype-word ban, register choice).

---

## How skills consume this file

Every skill that produces copy or voice-over MUST:

1. Read this file at the start of the run
2. Apply Rules 0–3 to every draft before the brand voice layer
3. Optionally call `validate_voice.py` (when present) as a hard gate before shipping

Skills affected: `ad-copywriter`, `post-writer`, `repurpose`, `landing-page-builder`, `case-study-generator`, `visual-generator` (for caption text), any future `video-voiceover` skill.

---

## Maintenance

This file is part of the protected kernel. Edit only via the authorized workflow:

```bash
./scripts/verify_kernel.sh --unlock
# edit copywriting-rules.md
./scripts/verify_kernel.sh --update    # regenerates baseline + re-locks
```

Never edit as a side effect of another task.
