# Paid Media Strategy — Dashboard Templates

## Template Selection Decision Tree

```
How many platforms?
├── ONE platform → template-single-platform.html
└── TWO platforms
    ├── Both launch simultaneously? → template-dual-simultaneous.html
    └── One launches first, other joins later? → template-dual-phased.html
```

| File | Use When | Example |
|------|----------|---------|
| `template-single-platform.html` | Google-only OR Meta-only | Budget < $1.5K, single channel focus |
| `template-dual-simultaneous.html` | Both platforms launching together | Budget > $3K, creative ready for both |
| `template-dual-phased.html` | One platform first, second joins later | Budget < $3K, zero creative on one platform, phased rollout |

## Styling (applies to ALL templates)

Styling is NOT template-specific. ALL templates support light/dark mode via `.light-mode`/`.dark-mode` body class. Brand colors and fonts are injected via CSS custom properties from `brand-config.json`. See `references/dashboard-specs.md` Brand-Config Priority section.

## Features
Chart.js 4.x (UMD), CSS custom properties with neutral defaults, collapsible sections, tooltips (.tip/.tiptext), copy buttons, fadeUp animations, responsive grid layout. Placeholder syntax: `{{VARIABLE_NAME}}`.
