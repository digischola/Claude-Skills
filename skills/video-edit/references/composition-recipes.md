# Composition Recipes — Narrative Arc Templates

Five arcs. Pick one based on source content + preset. Pass to `/hyperframes` as structural guidance.

## hook-framer (default for gen-z-punchy, course-sell)

0.0–1.5s   | HOOK title card (one line, ALL CAPS, zoom punch, big caption)
1.5–3.0s   | Source video starts — speaker/B-roll, caption sync begins
3.0–last-3 | Source video with kinetic captions + periodic zoom punches every ~4s
last-3–0   | Payoff card (CTA, next-step, or punchline) — overlay on fading source

Works when source is ≤60s. For longer, insert 2–3 "section break" cards mid-timeline.

## testimonial-trust-arc (default for testimonial-trust)

0.0–1.2s   | Name + title lower-third fades in over source pre-roll (no speech yet or B-roll)
1.2–end-2  | Source video full, lower-third persists 3s then fades, pull-quote overlays at emphasis moments
end-2–0    | Client logo or company name card, brand primary color bg, gentle fade

Use ken-burns slow pan on source (1.03x over 20s) if footage is static.

## case-study-arc (default for apple-premium when content is a client win)

0.0–2.0s   | Setup card: client name + the problem (big serif, centered)
2.0–5.0s   | Source: speaker introducing the challenge
5.0–15s    | Source + data callout overlays (metric numbers animate in — e.g., "$14k MRR → $41k MRR")
15s–end-3  | Source: speaker narrating resolution + kinetic captions on key phrases
end-3–0    | Result card: big metric, brand accent color, payoff statement

## product-demo-arc (default for tech-demo)

0.0–2.0s   | Product name title card on dark bg
2.0–end-4  | Source (screen recording) wrapped in Safari chrome, cursor trail visible, UI callouts (arrows, boxes) fade in/out as speaker mentions features
end-4–end  | Feature list summary card (3–5 bullets, staggered stagger-entrance) + URL/CTA

If source is 9:16, stack chrome vertical-phone instead of Safari desktop.

## event-recap-arc (default for event-recap)

0.0–1.5s   | Black, audio swells, event title fades up
1.5–3.0s   | Date + location stamp (bottom), first hero shot with slow push
3.0–end-4  | Source B-roll montage — cuts sync to music beats, occasional speaker clips with lower-thirds, light leaks between
end-4–end  | Event logo + "See you next year" card or next-event CTA

---

## How the Translator Maps Preset → Arc

Preset default arcs (override if user gives contrary signal):

| Preset             | Default Arc               |
|--------------------|---------------------------|
| apple-premium      | case-study-arc            |
| gen-z-punchy       | hook-framer               |
| corporate-clean    | testimonial-trust-arc     |
| documentary-warm   | case-study-arc            |
| tech-demo          | product-demo-arc          |
| testimonial-trust  | testimonial-trust-arc     |
| course-sell        | hook-framer               |
| event-recap        | event-recap-arc           |

If source duration < 15s, always fall back to hook-framer (not enough runway for other arcs). If source > 180s, add a mid-timeline "chapter break" card every ~60s using the arc's title-card style.

---

## Passing the Arc to `/hyperframes`

When invoking `/hyperframes`, include in the prompt:

- The arc name (verbatim — e.g., "use the testimonial-trust-arc")
- The keep_segments timeline from cuts.json so hyperframes knows where source plays
- The DESIGN.md (colors, typography, motion rules from the preset)
- The speaker-identified transcript (from `/hyperframes-cli transcribe`)
- The client brand-config.json if it exists
- The list of key emphasis moments the user wants to highlight (if stated)

`/hyperframes` will produce the HTML composition + GSAP timeline. Do not attempt to author it yourself — delegate fully.
