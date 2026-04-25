# Client Naming Policy

Per voice-guide.md, Mayank's client-naming policy is **Conservative**. Default is anonymize unless the client + metrics are publicly displayed on digischola.in.

## Public-allowed (named freely)

Clients whose metrics are publicly displayed on the digischola.in case studies page. These can be named in case studies + posts:

| Client | Public metric | Industry |
|---|---|---|
| **Thrive Retreats** (Colo Heights NSW) | +188% Meta sales / -37% CPS in 90 days | Wellness retreat |
| **Happy Buddha Retreats** (same founder Athil) | (referenced as sister property) | Wellness retreat |
| **ISKM Singapore** | Ratha Yatra 2025 +65% registrations / +40% attendance | Spiritual / festival |
| **Samir's Indian Kitchen** (Surry Hills Sydney) | Restaurant launch case study | Restaurant |
| **Chart & Chime** (Ranga Devi) | (referenced for music education) | Music education |
| **CrownTECH** (Toronto) | (B2B referenced in services list) | B2B services |

If you're writing a case study about one of these clients AND citing only the publicly-displayed metrics, you can name them freely. Add a credit line: "Source: digischola.in/case-studies".

## Anonymization rules (everyone else)

For any client NOT in the table above, OR for metrics NOT publicly displayed (e.g., internal CRO test results, unpublished campaign performance), use anonymization:

### Anonymization templates by industry

| Industry | Anonymized form |
|---|---|
| Wellness retreat | "a wellness retreat client" + region (NSW, Goa, Bali, etc.) |
| Yoga studio | "a yoga studio client" + region |
| Restaurant | "a restaurant client" + city |
| B2B SaaS | "a B2B SaaS client" + industry vertical (fintech, edtech, etc.) |
| E-commerce | "an e-commerce brand" + category (apparel, beauty, etc.) |
| Spiritual / cultural | "a cultural-event organizer" or "a spiritual community" |
| Hospitality | "a boutique hotel" + region |
| Local services | "a local services provider" + service type |

### Anonymization examples

✓ Good (anonymized):
- "A wellness retreat client in NSW Australia. 90 days. Starting at 21% Meta CTR but 1.2% landing-page conversion."
- "A boutique hotel in coastal Goa. 60 days. Bookings down 30% from same period last year."
- "A B2B fintech client. 45 days. Lead form converting at 0.8%."

✗ Bad (over-anonymized — too vague to be credible):
- "A client in some industry."
- "A business I worked with."

✗ Bad (under-anonymized — leaks identifying detail):
- "A wellness retreat client in NSW Australia run by Athil." (Names the founder.)
- "A 30-room boutique hotel in coastal Goa called [name]." (Identifies the property.)

## Decision logic in case_study.py

```python
if client_name in PUBLIC_NAMED_CLIENTS:
    if all(metric in PUBLIC_METRICS[client_name] for metric in metrics_used):
        # Allow naming
        identifier = client_name + " (" + region + ")"
        credit = "Source: digischola.in/case-studies"
    else:
        # Some metrics are private — anonymize even if client is publicly known
        identifier = anonymize(industry, region)
        credit = ""
else:
    identifier = anonymize(industry, region)
    credit = ""
```

`validate_case_study.py` checks:
1. The same identifier is used in all 4 deliverables
2. If named: only public metrics are cited (no leaking of private numbers)
3. If anonymized: no detail that would let a reader identify the client (founder name, exact address, distinct branding)

## When in doubt → anonymize

If unsure whether a client / metric is public, default to anonymization. Mayank can always add the name manually before publishing if he confirms permission.

## Cross-skill impact

- `post-writer` enforces the same Conservative policy for single-channel drafts. case-study-generator inherits this for all 4 deliverables.
- `repurpose` follows the source draft's identifier — if the source named the client, variants name them too.
- `case-study-generator` has its OWN policy enforcement because it generates from idea-bank entries (not from existing drafts), so it has to make the naming decision fresh.
