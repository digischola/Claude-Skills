# Restricted Keyword Categories — Pre-Filter

Google Ads' Personalized Advertising Restrictions auto-reject keywords that imply a sensitive category — health conditions, financial hardship, employment, housing, education attainment. Triggered at Editor import with errors like "Health category not accepted" or "Personalized advertising restrictions apply." Pre-filtering at generation time is cheaper than post-import fixes because the rejected keyword propagates through ad copy + media plan + dashboard + creative brief CSV before the rejection surfaces.

This reference exists because the 2026-04-26 Living Flow Yoga session hit this with `yoga for back pain sydney` (rejected as health-condition). Affected sectors: yoga, fitness, wellness, therapy, healthcare, financial-aid education, employment services.

## How the gate fires

Validator runs at Step 8 against `03-keywords.csv`. Each keyword is regex-scanned against the restricted-pattern list. CRITICAL fail per match with the recommended reframing.

## Restricted patterns + reframing recipes

### Health conditions (most common for wellness/yoga/fitness/therapy)

| Restricted keyword pattern | Why rejected | Approved reframing |
|---|---|---|
| `yoga for back pain` / `yoga for neck pain` / `pain relief yoga` | Health condition | `yoga for desk workers` / `mobility yoga` / `stretching yoga` |
| `yoga for anxiety` / `yoga for stress` / `anxiety yoga` | Mental health | `calming yoga` / `restorative yoga` / `slow yoga` |
| `yoga for depression` / `mood-lifting yoga` | Mental health | `gentle yoga` / `wellbeing yoga` |
| `yoga for arthritis` / `yoga for joint pain` | Health condition | `gentle yoga for seniors` / `low-impact yoga` |
| `yoga for fibromyalgia` / `yoga for chronic pain` | Health condition | `restorative yoga` / `slow flow yoga` |
| `yoga for weight loss` / `slim yoga` | Weight/body | `yoga for fitness` / `power yoga` / `vinyasa flow` |
| `yoga for fertility` / `fertility yoga` | Reproductive health | DROP — no clean reframe; market-specific |
| `yoga for migraines` / `headache yoga` | Health condition | `restorative yoga` / `relaxation yoga` |
| `yoga for sciatica` | Health condition | `lower-back yoga` / `hip mobility yoga` |
| `yoga for insomnia` / `sleep yoga` | Health-adjacent | `evening yoga` / `bedtime yoga` (intent-only, no claim) |
| `yoga for adhd` / `yoga for autism` | Mental health diagnosis | DROP — diagnosis-targeted not allowed |
| `yoga for ptsd` / `trauma-informed yoga` | Mental health | DROP unless instructor is certified + claim is verified |

### Therapy / mental health

| Restricted | Approved |
|---|---|
| `therapy for depression` / `depression therapy` | `online therapist` / `talk therapy` |
| `therapy for ptsd` | DROP — diagnosis-targeted |
| `addiction recovery therapy` | DROP — restricted-vertical |
| `eating disorder therapy` | DROP — restricted-vertical |

### Fitness / weight loss

| Restricted | Approved |
|---|---|
| `weight loss program` / `lose 20 pounds` | `fitness program` / `body transformation` |
| `belly fat workout` / `lose belly fat` | `core workout` / `abs workout` |
| `obesity workout` | DROP — health-condition-targeted |

### Healthcare / pharma (always DROP)

These cannot run on Google Ads paid search at all without medical-vertical approval:

- Prescription drug names
- Specific disease names ("diabetes", "cancer", "HIV")
- Body-part-specific surgery/procedure searches
- Mental health diagnostic terms when paired with treatment claims

### Financial / employment / housing (per Personalized Ads policy)

- Employment status: `unemployed jobs` / `low-income jobs` → DROP
- Credit/debt status: `bad credit loans` / `debt consolidation poor credit` → DROP
- Housing: `low-income apartments` / `section 8 housing` → DROP
- Education attainment: `no degree job` / `dropout career` → DROP

## Pre-filter algorithm (validator)

Each keyword in `03-keywords.csv` is scanned:

```python
RESTRICTED_PATTERNS = [
    (r'\byoga\s+for\s+(back|neck|joint)\s+pain\b', 'health-condition (back/neck/joint pain)'),
    (r'\byoga\s+for\s+(anxiety|depression|stress|insomnia|adhd|ptsd|autism)\b', 'mental-health condition'),
    (r'\byoga\s+for\s+(arthritis|fibromyalgia|sciatica|migraines?|chronic\s+pain)\b', 'health condition'),
    (r'\byoga\s+for\s+(weight\s+loss|fertility)\b', 'weight/reproductive health'),
    (r'\b(weight\s+loss|lose\s+\d+\s*(pounds|kg|lbs)|belly\s+fat)\b', 'weight loss claim'),
    (r'\btherapy\s+for\s+(depression|ptsd|addiction|eating\s+disorder)\b', 'mental-health diagnosis'),
    (r'\b(bad\s+credit|debt\s+consolidation\s+poor\s+credit|low.income|section\s+8|unemployed)\b', 'financial/employment status'),
    # ... extend per sector
]
```

CRITICAL fail per match with the keyword + restricted category + suggested reframing from the recipes above.

## When to drop vs reframe

- **Reframe** when the underlying intent is reachable via approved language (back pain → desk workers, anxiety → calming yoga). Most cases.
- **Drop** when the search-term itself encodes a protected attribute and no clean approved phrasing exists (PTSD-specific therapy, fertility-specific yoga, addiction-specific anything).

When in doubt: drop. Editor will reject the keyword anyway, and the dropped keyword becomes one less variable to debug at launch.

## Coverage gap (sector-specific reframing)

The list above covers wellness/yoga/fitness/therapy/healthcare/finance/employment. When onboarding a new sector with potential exposure (insurance, legal, gambling, alcohol, religion, cannabis, weight-loss-supplements, fertility products, hearing aids, mobility aids), extend `RESTRICTED_PATTERNS` and update this reference.

The 3x penalty rule applies — better to drop a keyword than to ship it and have it propagate through every downstream deliverable until import-time rejection.
