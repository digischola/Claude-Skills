# Offerings Cross-Check & Gated-Prerequisite Protocol

This reference governs **Gate A** (Phase-0 leakage prevention) and **Gate B** (service-offering verification) in ad-copywriter. Both gates exist because the 2026-04-26 Living Flow Yoga session almost shipped 60+ headlines/descriptions/sitelinks/callouts to Google Ads claiming services that the business does not offer (free trial, prenatal yoga, chair yoga, trimester-safe modifications). Every downstream skill (market-research → paid-media-strategy → ad-copywriter → campaign-setup) treated *market search demand* as equivalent to *service offering*. None cross-checked back to the business's documented offerings.

## When the gates fire

Both gates run at **Step 4 (ad copy generation)** and again at **Step 8 (validate)**. Generation-time gates strip claims before they hit the report; validation-time gates fail-loud if anything slipped through.

---

## Gate A — Phase-0 leakage prevention

### Trigger conditions (any one fires Gate A)

The skill MUST switch to gated-output mode when the upstream creative-brief carries **any** of:

1. Top-level field `do_not_launch_until_phase_0_complete: true`
2. Any element of `phase_0_prerequisites[]` with `status: "GATED"` or `status: "BLOCKED"` or `status: "PENDING"`
3. Top-level field `verdict: "DO-NOT-LAUNCH"` or `"BEST-CASE"` or `"GATED"`
4. Top-level field `framing: "best-case"` (case-insensitive)

### Mandatory output split when Gate A fires

Two output files, not one:

| File | Audience | Contents |
|---|---|---|
| `ad-copy-best-case.md` | Strategy / forward planning | Full creative brief realised, gated claims included, **prominent banner** at top: "BEST CASE — DO NOT IMPORT until Phase 0 complete" |
| `ad-copy-current-state.md` | Production / campaign-setup | Gated claims **stripped**, ad groups reframed against verified offerings only, banner: "Current-state copy — safe for production import" |

The CSV (`google-ads.csv` / `meta-ads.csv`) is generated **only from the current-state file**. Never from best-case.

### Gated-claim phrases (auto-strip list)

When Gate A fires, the skill scans every headline / description / sitelink / callout / snippet value against the brief's `phase_0_prerequisites[].name` and `phase_0_prerequisites[].claim_phrases[]`. Common phrases that recur across wellness/yoga/fitness clients:

- `free trial`, `7-day free trial`, `14-day free trial`, `try free`, `start free`, `free week`
- Specific SKU references that don't yet exist in the business's booking system
- "Available 24/7" / "instant access" claims for businesses that haven't built on-demand library
- Free-shipping / money-back-guarantee claims for businesses without that policy
- App-feature claims (offline mode, download class) when no app exists

If a phrase matches and the corresponding prerequisite is GATED, **strip from current-state output**, keep in best-case output, and log to the report's audit section.

---

## Gate B — Service-offering cross-check

### Trigger conditions (always-on)

Gate B runs on **every** ad-copywriter session. Not gated by brief flags. Source of truth:

1. `{client}/_engine/wiki/offerings.md` (single-program client)
2. `{client-root}/_engine/wiki/offerings.md` (multi-program client — `_engine/` at the client root, formerly `_shared/`)
3. If neither exists, fall back to `{client-root}/_engine/wiki/business.md` Section "Offerings" / "Services"

### Cross-check protocol

For every persona, ad group name, headline, description, callout, snippet value, and proof claim that mentions a **specific service / class style / modality / format**, the skill must verify that exact service appears in offerings.md.

The check is fuzzy-match (lemma-aware): "prenatal yoga" matches "Pre-Postnatal Yoga"; "vinyasa" matches "Vinyasa Flow"; "beginners" matches "Beginners Class". But "chair yoga" does NOT match "Vinyasa Flow / Yin / Beginners / Yang to Yin" — fail.

### Common false-claim categories to pre-filter

Cross-industry recurring traps (search demand exists, business may not offer):

| Sector | Search-demand cluster | Verify against offerings |
|---|---|---|
| Yoga / wellness | prenatal, postnatal, chair yoga, kids yoga, restorative, Bikram, hot yoga, ashtanga, kundalini, aerial | Does business teach this style with a qualified instructor? |
| Therapy / mental health | EMDR, IFS, CBT, DBT, somatic, ketamine-assisted | Is the practitioner certified for this modality? |
| Fitness / gym | personal training, group classes, CrossFit, F45, reformer pilates, mat pilates | Is this a current class on the timetable? |
| Beauty / spa | hydrafacial, microneedling, laser hair removal, IPL, chemical peel | Is this on the service menu with a price? |
| Restaurants | gluten-free menu, vegan menu, halal, kosher, kids menu, takeaway, delivery | Is this an actual menu offering? |
| Retreats | airport transfer, vegetarian-only, alcohol-free, ayurvedic, silent | Is this in the inclusions list? |

### Recovery options when Gate B fails

Three options, in order of preference:

1. **Drop the claim** — remove the persona / ad group / headline. Replace with a verified alternative.
2. **Reframe to verified offering** — "yoga for back pain" → "yoga for desk workers" (verified as accessible Beginners class).
3. **Wrap as `<<UNVERIFIED-CLAIM:phrase>>`** — last-resort token that campaign-setup validator hard-fails on. Forces analyst-in-the-loop decision.

Never silently ship. The 3x penalty rule (kernel `accuracy-protocol.md`) applies: a wrong claim in a Google Ads campaign can produce ACL §18/§29 false-advertising exposure plus reputation damage — far worse than a blank ad group.

---

## Validator behaviour (scripts/validate_output.py)

The validator implements both gates programmatically:

**Gate A check:**
- Loads creative-brief.json (already done since 2026-04-16)
- Detects any of the 4 trigger conditions above
- If fired AND only one ad-copy-report file exists (no `-best-case` / `-current-state` split), CRITICAL fail
- If fired AND CSV contains gated-claim phrases from `phase_0_prerequisites[].claim_phrases`, CRITICAL fail per row

**Gate B check:**
- Loads `_engine/wiki/offerings.md` (single-program) or `{client-root}/_engine/wiki/offerings.md` (multi-program)
- Extracts canonical offering names (lemma-normalised)
- Scans report + CSV for service-claim phrases
- For each unmatched claim, CRITICAL fail with the specific phrase + offerings file path so the analyst can reconcile

**Soft-fail conditions:**
- `_engine/wiki/offerings.md` does not exist → WARNING ("Gate B unverified — no offerings.md found"). Do not block.
- creative-brief.json does not exist → INFO ("Gate A skipped — no brief"). Standalone-mode runs are exempt.

---

## Logging requirements

Every Gate A / Gate B fire MUST be written to the ad-copy report's audit section:

```markdown
## Gate Audit (auto-generated)

**Gate A — Phase-0 leakage:** [FIRED / NOT FIRED]
- Triggers: [list]
- Output split: best-case + current-state files generated
- Stripped phrases: [list]

**Gate B — Service-offering cross-check:** [PASSED / FAILED]
- Offerings source: {path}
- Verified claims: [count]
- Stripped/reframed claims: [list with reason]
```

This audit trail is what lets the next analyst trust the deliverable without re-auditing every claim.

---

## Why both gates, not one

Gate A and Gate B catch *different* failure modes:

- **Gate A** = brief explicitly says "this isn't built yet" but skill produces production copy anyway (Living Flow free-trial case).
- **Gate B** = brief implies a service exists because market data shows demand, but business doesn't offer it (Living Flow prenatal case).

A brief can pass Gate A (no Phase-0 prerequisites flagged) and still fail Gate B (e.g., creative brief listed "Pregnancy/Pre-Postnatal" as a persona based on keyword volume, but offerings.md doesn't list prenatal yoga). Both gates required.
