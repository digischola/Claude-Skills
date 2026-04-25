# Aesthetic Presets — 8 Opinionated Looks

Each preset is a full DESIGN.md specification. When the translator picks one, emit this DESIGN.md into the hyperframes project directory so `/hyperframes` honors it. Brand overrides (from client brand-config.json) win.

All color suggestions are baselines — when client brand colors exist, substitute primary/accent and keep the motion + typography scales.

---

## apple-premium

**Feel**: cinematic, spacious, confident. Think Apple keynote, product launch films.

- **Colors**: deep graphite `#0A0A0A`, near-white text `#F5F5F7`, accent blue `#0071E3` (or brand primary)
- **Typography**: SF Pro Display (system-ui fallback), Inter Tight. Title 96–120px, subtitle 36–42px, captions 42px
- **Motion**: slow confident easing (power2.inOut, 0.8–1.2s entrances), parallax depth on text, long crossfades
- **Captions**: centered, single-line, fade in per word, large type, white on black
- **LUT**: gentle filmic (lifted blacks, soft highlights)
- **What NOT to do**: stroke borders, drop shadows, emoji, bouncy eases, color-pop highlights

---

## gen-z-punchy

**Feel**: scroll-stopping, chaotic, energetic. Think TikTok creators, MrBeast cold opens.

- **Colors**: high-contrast electric — black `#000`, white `#FFF`, yellow `#FFEB3B`, hot pink `#FF2D92`
- **Typography**: Anton, Archivo Black, Neue Machina. Titles 140–180px ALL CAPS, captions 80–100px
- **Motion**: hard cuts, zoom punches (+5% every 2–3s), chromatic aberration on beats, bouncy eases (back.out)
- **Captions**: animated word-by-word with color pops on keywords, shake on emphasis
- **Beat sync**: if music bed present, sync cuts + caption entrances to detected beats via audio-reactive
- **What NOT to do**: slow fades, elegant serif fonts, muted palettes, long sustained frames

---

## corporate-clean

**Feel**: B2B professional, restrained, brand-safe.

- **Colors**: neutral navy `#0D1B2A`, white bg `#FFFFFF`, brand primary (from client config)
- **Typography**: Inter, IBM Plex Sans. Titles 72–96px, body 32–38px, captions 38px
- **Motion**: gentle slide-ins (power1.out, 0.4s), subtle fades, no zoom or shake
- **Captions**: lower-third or bottom-centered, simple fade, brand primary color
- **Lower thirds**: name + title bar for every speaker segment
- **What NOT to do**: chaotic transitions, emoji, ALL-CAPS everywhere, color-pop keywords, aggressive beat sync

---

## documentary-warm

**Feel**: organic, story-driven, intimate. Think Patagonia films, NYT docs.

- **Colors**: warm ochre `#C08457`, cream `#F3EADD`, deep forest `#2C3A2B`, dust blue `#6B8CA8`
- **Typography**: Source Serif Pro for titles, Inter for captions. Title 84px, caption 38px
- **Motion**: slow typography reveals (power2.out, 1.2s+), film grain overlay, vignette on source video, slight sepia LUT
- **Captions**: minimal, bottom-third, fade in line-by-line
- **LUT**: warm filmic (crushed shadows, warm midtones)
- **What NOT to do**: neon colors, shake, ALL CAPS, beat sync, fast cuts

---

## tech-demo

**Feel**: SaaS product tour. Think Linear, Notion, Vercel launch videos.

- **Colors**: dark canvas `#0D1117`, accent cyan `#00D4FF`, ui-green `#3FB950`, warn-amber `#E3B341`
- **Typography**: Inter, JetBrains Mono for code snippets. Title 96px, UI labels 28–32px
- **Motion**: chrome browser mockup wrapping source video (Safari or generic), cursor trails, zoom punches on CTAs, data callouts
- **Captions**: overlay boxes with UI-style borders, fade in/out, accent-cyan highlights for product-name keywords
- **Chrome wrap**: auto-detect if source is a screen recording — if yes, wrap in a realistic browser frame with URL bar
- **What NOT to do**: chaotic motion, emoji, serif fonts, warm LUT

---

## testimonial-trust

**Feel**: client story, quote-driven. Builds credibility.

- **Colors**: deep navy `#102A43` bg, white `#FFF` text, brand accent for pull quotes
- **Typography**: Inter for body, Source Serif Pro for pull quotes. Title 72px, quote 60px italic, caption 38px
- **Motion**: slow pan on source video (ken burns), pull-quote entrances (power2.out, 0.6s), name/title lower-third fades
- **Captions**: bottom-centered, brand-safe fade, auto-highlighted keywords (metric mentions like "+188%", "40 hours/week") in brand accent
- **Lower thirds**: name + role + company, persistent for first 3s of each speaker segment
- **What NOT to do**: shake, beat sync, ALL CAPS, emoji, chaotic color pops

---

## course-sell

**Feel**: high-converting sales video. Hook-heavy, benefit-driven, urgent.

- **Colors**: black bg `#0B0B0B`, electric yellow `#FFD60A`, crimson accent `#C8102E`, white text
- **Typography**: Anton for hook + CTA, Inter for body. Hook 140px, benefit callouts 80px, CTA 120px
- **Motion**: zoom punches on hooks, callout pops (back.out, 0.3s), progress bar at bottom for "X of Y benefits", urgency countdown if relevant
- **Captions**: animated, hook-first, benefit keywords in yellow
- **Beat sync**: if music bed, sync major callouts to drops
- **What NOT to do**: calm sustained frames, elegant serifs, muted palettes, understated CTAs

---

## event-recap

**Feel**: highlight reel, after-movie. Music-driven energy builds.

- **Colors**: palette sampled from event theme — default to warm gold `#D4AF37`, deep plum `#3E1E47`, white
- **Typography**: Playfair Display for event name, Inter for date/location. Title 120px, date 48px
- **Motion**: music-synced cuts, date/location stamps, energy build (slow open → accelerating cuts → hero shot), light leaks between segments
- **Captions**: minimal — mostly the event name + date + location stamps
- **LUT**: cinematic teal-orange
- **What NOT to do**: heavy text blocks, UI-style overlays, monologue captions, low-energy sustained frames (this is a highlight reel — keep moving)

---

## Motion Density Quick-Reference

| Preset | Cuts per 10s | Zoom punches | Caption animation | Beat sync |
|--------|--------------|--------------|-------------------|-----------|
| apple-premium     | 1–2 | none    | word-fade   | no  |
| gen-z-punchy      | 4–6 | heavy   | kinetic     | yes |
| corporate-clean   | 1–2 | none    | line-fade   | no  |
| documentary-warm  | 1–2 | none    | line-fade   | no  |
| tech-demo         | 2–3 | medium  | ui-box      | no  |
| testimonial-trust | 1–2 | none    | keyword-hl  | no  |
| course-sell       | 3–5 | heavy   | kinetic     | yes |
| event-recap       | 3–5 | medium  | stamp       | yes |
