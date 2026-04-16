# Assets — Landing Page Audit

Pre-built HTML dashboard templates. These are the final output scaffolds — the skill populates `{{PLACEHOLDER}}` variables with audit data. Never generate HTML from scratch.

## Templates

| File | Page Type | When to Use |
|---|---|---|
| `template-local-services.html` | Restaurant, wellness, salon, local service | Trust & social proof panel (reviews, testimonials, photos) |
| `template-booking-event.html` | Retreat, workshop, training, event | Urgency checklist + transformation narrative (before → after) |
| `template-b2b-leadgen.html` | IT, consulting, professional services | Credibility panel (certs, case studies) + form field analysis |
| `template-internal-quick.html` | Any (internal use) | Compact, no animations, print-friendly. For pre-campaign checks. |

## Template Selection

Default to client-facing (first three). Use internal-quick only when explicitly requested. Choose based on business type identified during intake.

## Key Technical Notes

- Chart.js 4.x UMD build hardcoded: `cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js`
- All CSS inline — no external stylesheets
- All JS vanilla — no frameworks
- Dark mode default with CSS custom properties for brand color overrides
- Screenshot container uses `:has(img)` to conditionally set min-height
