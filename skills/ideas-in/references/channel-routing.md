# channel-routing

Type → suggested channels + format candidates. Used by capture mode to pre-fill the entry. `draft-week` makes the final routing call when assigning a calendar slot.

## Defaults

| Type | Pillar bias | Best channels | Format candidates |
|---|---|---|---|
| client-win | LP Craft, Paid Media | LinkedIn-text, X-thread, Instagram-carousel | LI-post, X-thread, IG-carousel |
| insight | any | LinkedIn-text, X-single | LI-post, X-tweet |
| experiment | any | LinkedIn-text, X-thread | LI-post, X-thread |
| failure | any | LinkedIn-text | LI-post (long-form vulnerability) |
| build-log | Solo Ops | LinkedIn-text, X-thread, WhatsApp-status | LI-post, X-thread, WA-status |
| client-comm | LP Craft, Paid Media | LinkedIn-text | LI-post |
| observation | any | X-single, LinkedIn-text | X-tweet, LI-post |
| trend | matches pillar of origin | LinkedIn-text, X-single | LI-post, X-tweet |
| peer-pattern | matches creator's lane | reference only | (not posted directly — feeds draft-week's hook selection) |

## Pillar inference

If the note mentions:
- "landing page", "LP", "hero", "form", "CTA", "above the fold" → **Landing-Page Conversion Craft**
- "Meta ads", "Google ads", "ROAS", "CPA", "creative test", "budget split" → **Small-Budget Paid Media**
- "freelance", "solo", "client mgmt", "ops stack", "AI workflow", "tools", "pricing" → **Solo Freelance Ops**

If multiple match → pick the dominant signal in the note. If none match → ask user.

## Format-fit notes

- **LI-carousel** is heavy. Reserve for client-wins with 6+ teachable slides or a multi-step framework.
- **X-thread** for narrative arcs (5-12 tweets). For one-liner insights, X-single.
- **IG-Reel** is video — only suggest if the entry has a visual hook (mockup teardown, before/after, on-screen text reveal). Otherwise IG-carousel or skip IG.
- **WhatsApp-status** for quick build-logs and behind-the-scenes. Disposable, not high effort.
