# Skill Coordination

Landing page audit is a **standalone terminal skill** — it produces a client-facing dashboard as the final deliverable. Its outputs are not consumed by other skills.

---

## Input Dependencies

| Dependency | Source Skill | What It Provides | Required? |
|---|---|---|---|
| `brand-config.json` | business-analysis | Brand colors (primary, dark, accent), fonts, logo URL | Optional — falls back to default dark theme if missing |

### How brand-config.json is used

If a `brand-config.json` exists in the client folder (produced by the business-analysis skill), the landing-page-audit skill reads it to:

1. Set CSS custom properties (`--primary`, `--dark`, etc.) in the dashboard template
2. Apply brand-consistent colors to Chart.js gauges and radar charts
3. Match the dashboard aesthetic to the client's visual identity

If no brand-config exists, the skill uses a professional default dark theme (blue accent on slate background) and notes in the deliverable that brand colors were not available.

### Where to find brand-config.json

```
{Client Name}/{Project or Business}/deliverables/brand-config.json
```

Or check the client folder root if the project structure varies.

---

## Output

The skill produces a single HTML file saved to:

```
{Client Name}/{Project or Business}/deliverables/{page-name}-landing-page-audit.html
```

This is a self-contained static HTML dashboard (no external dependencies except Chart.js CDN). It can be:
- Opened directly in a browser
- Deployed to Netlify/Vercel for client sharing
- Attached to an email or project management tool

No wiki updates. No JSON artifacts for other skills. No downstream flags that require action.
