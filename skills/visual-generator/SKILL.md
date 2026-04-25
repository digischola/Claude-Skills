---
name: visual-generator
description: "Digischola visual production — two paths. (A) Static graphics (carousels, quote cards, animated graphics) via Claude Design handoff → render_html_carousel.py / render_html_mp4.py. (B) 30-sec Reels via Remotion-first programmatic video with UI-mockup design language (Cody Plofker teardown aesthetic — realistic browser chrome, landing page mockups, eye-gaze trails, data callouts) — NO photographs except static outro portrait, NO AI image generation. Stack: Remotion (React video), Paper Design mesh shaders, ChatterBox (voice cloning), free BGM (Pixabay/Mixkit), ffmpeg polish, automated QA gate. Use when user says: generate visual, make a carousel, create a Reel, render a quote card, design brief, visual for this post, make a video, carousel for IG, Reel script. Do NOT trigger for: drafting post copy (use post-writer), planning the week (use content-calendar), capturing an idea (use work-capture), client visual work (use business-analysis / landing-page-builder)."
---

# Visual Generator (v7.4 — dual-engine)

Two clean paths. Neither uses generative AI images. Everything is code-rendered, brand-locked, fully deterministic.

- **Path A — Static graphics** (carousels, quote cards, animated graphics) via Claude Design handoff. Unchanged since v6. Works.
- **Path B — 30-sec Reels** (v7.4 dual-engine). Each scene routes to the engine that's best for it:
  - **Remotion** renders UI-mockup teardown scenes (hook / problem_beat / insight_beat / data_reveal / outro) using the v7.3 React primitive library (BrowserCycler, LandingPageMockup, FormReducer, LiftChart, GazeTrail, CalloutArrow, etc.). Deterministic per-frame interpolation + spring physics.
  - **Hyperframes** renders social-platform overlay scenes (x_post_overlay, instagram_follow, tiktok_follow, reddit_overlay, spotify_now_playing, macos_notification, yt_subscribe_cta) using the shadcn-style catalog blocks (`hyperframes add <block>`). HTML+GSAP with deterministic `tl.seek()`.
  - One static portrait on outro only; no other photographs; no AI image generation anywhere.
  - Creative gate: `references/motion-design-playbook.md`. Primitive catalog: `references/ui-mockup-vocabulary.md`. Dual-engine architecture: `references/v7-pipeline-architecture.md`.

**Consistency discipline**: both engines read `brand/remotion-studio/src/theme/design-tokens.json` (single source of truth for palette / fonts / easing / duration). Run `scripts/build_shared_tokens.py` to regenerate `brand/hyperframes-scenes/shared/tokens.css` after any token edit. Scene routing: `scripts/scene_spec.py::SCENE_ROUTING`. Render log captured per scene to `brand/queue/assets/<entry_id>/render_log.jsonl` for future learning.

## Context Loading

**Brand wiki (LOCKED, read first):**
- `Desktop/Digischola/brand/brand-identity.md` — colors (#3B9EFF accent, #4ADE80 success, #EF4444 warning), fonts (Orbitron / Space Grotesk / Manrope), logo, UI rules
- `Desktop/Digischola/brand/voice-guide.md` — emoji policy (Restrained), client-naming (Conservative)
- `Desktop/Digischola/brand/voice-lock.md` — ChatterBox voice-clone reference corpus
- `Desktop/Digischola/brand/pillars.md` — status must be LOCKED

**Skill references:**
- `references/motion-design-playbook.md` — **creative gate for Path B**. Every new reel scene must hit this bar.
- `references/engine-selection.md` — Path A vs Path B decision tree
- `references/claude-design-workflow.md` — Path A brief + handoff flow (carousels)
- `references/remotion-guide.md` — Path B project structure, composition patterns, CLI
- `references/ui-mockup-vocabulary.md` — Path B primitive catalog (10 UIMockups — BrowserFrame, LandingPageMockup, FormReducer, LiftChart, GazeTrail, etc.)
- `references/v7-pipeline-architecture.md` — Path B end-to-end dataflow (draft → VO → timestamps → render → stitch → QA)
- `references/voice-cloning-setup.md` — ChatterBox install + invocation
- `references/feedback-loop.md`

**Shared context:**
- `.claude/shared-context/analyst-profile.md`

## Inputs

1. **Source draft** (required) — markdown file in `Desktop/Digischola/brand/queue/pending-approval/` with YAML frontmatter (channel, format, entry_id, pillar). Produced by post-writer or repurpose.
2. **Target format** (required) — `carousel` / `quote-card` / `animated-graphic` / `story` → Path A; `reel-script` → Path B.

## Path A — Static graphics (Claude Design)

Unchanged from v6. For carousels, quote cards, story cards, and short animated graphics.

1. `scripts/generate_brief.py <source-file> --target <target>` → structured brief at `brand/queue/briefs/`
2. User pastes the brief body into `claude.ai/design`, iterates, clicks Hand off → gets a render command
3. User pastes command into Claude Code → `render_html_carousel.py` (for PNG slides) or `render_html_mp4.py` (for single animated MP4)
4. `scripts/import_assets.py` → normalized filenames + manifest.json in `brand/queue/assets/<entry_id>/`
5. Update source-draft frontmatter with `visual_assets_dir:`

## Path B — Reels (Remotion-first, v7)

Creative standard: `references/motion-design-playbook.md` (non-negotiable gate).

### Step 1: Validate preconditions

- `brand/remotion-studio/` is set up (one-time install, see `references/remotion-guide.md`)
- `brand-identity.md` LOCKED
- `voice-lock.md` exists (ChatterBox corpus enrolled)
- Source draft has `## Scene breakdown` section with 4-6 scenes
- BGM track available at `brand/music/<pillar-slug>.mp3` (optional — omit for silent+VO-only)

### Step 2: Generate voiceover

Run `scripts/clone_voice.py --draft <source>` → `brand/queue/assets/<entry_id>/voiceover.mp3` via ChatterBox. Emotion tags like `[firm]` / `[measured]` / `[confident]` drive per-chunk exaggeration/cfg parameters.

### Step 3: Parse scenes + classify

Run `scripts/generate_reel.py --draft <source>` which:
1. Parses scene breakdown (reuses `parse_scenes()` logic ported from `.archive-v6/generate_tow_prompts.py`)
2. Classifies each scene type from heading label: `hook` / `problem_beat` / `insight_beat` / `data_reveal` / `cta` / `outro`
3. Maps each scene_type → Remotion composition name + duration
4. Emits a per-reel Remotion props JSON at `brand/remotion-studio/props/<entry_id>.json`

### Step 4: Render each scene via Remotion

`generate_reel.py` invokes Remotion CLI per scene:
```
cd brand/remotion-studio && npx remotion render <CompositionName> \
  --props=<tempfile>.json \
  <assets>/scene-<N>-rmt.mp4
```
The 5 v7.3 compositions (UI-mockup aesthetic — see `references/ui-mockup-vocabulary.md`):
- `KineticHook` (2.9s) — BrowserCycler (rapid LP flips) + Counter (0→N linear) + KaraokeCaption School A + MeshGradient
- `ProblemBeat` (3.3s) — BrowserFrame + LandingPageMockup(wellness-bad) + GazeTrail dropping off + Stopwatch + CalloutArrow(warning)
- `InsightBeat` (5.0s) — BrowserFrame + LandingPageMockup(wellness-good) + FoldLine + GazeTrail holding above fold
- `DataReveal` (3.8s) — FormReducer (9→3) + Counter (+N%) + LiftChart + CalloutArrow(accent)
- `OutroCard` (3.8s) — face-01.jpg in iOS-icon rounded square + @handle + centered CTA + URL + DigischolaLogo

### Step 5: Stitch + polish

`generate_reel.py` runs final ffmpeg pass (port of `.archive-v6/assemble_reel.py`'s POLISH_FILTER + flash + BGM ducking):
- Concat scene-N-rmt.mp4 files
- Interleave 2-frame white flash between pairs
- Apply `POLISH_FILTER` (eq + vignette + grain)
- Mix VO + BGM with `sidechaincompress` ducking
- Output: `brand/queue/assets/<entry_id>/reel.mp4`

### Step 6: Automated QA gate

`scripts/qa_reel.py --reel <reel.mp4>` extracts frames @ 2fps and runs 3 checks (ffmpeg signalstats + SSIM):
- `visual_density ≥ 0.08` — frame is not empty
- `pure_black_ratio ≤ 0.92` — frame is not black-hole
- `frame_delta ≥ 0.01` — motion is present (not stuck)

Non-zero exit prints failing frame numbers; orchestrator warns before shipping.

### Step 7: Import + cross-link

- `scripts/import_assets.py` writes manifest.json
- Update source-draft frontmatter with `visual_assets_dir:`

### Step 8: Feedback loop

Read `references/feedback-loop.md`. Log any motion-design-playbook violations, UI-mockup primitive gaps, Remotion render failures, BGM licensing issues, voiceover drift.

## Output Checklist

- [ ] pillars.md LOCKED
- [ ] Motion Design Playbook reviewed (Path B only)
- [ ] Source draft has valid frontmatter + scene breakdown (Path B)
- [ ] Voiceover rendered via ChatterBox (Path B)
- [ ] Rendered assets in `brand/queue/assets/<entry_id>/`
- [ ] Manifest written with brief linkage
- [ ] Source draft frontmatter updated with `visual_assets_dir:`
- [ ] No photographic imagery in reel body (Path B — only outro face allowed)
- [ ] No em dashes in rendered text anywhere

## Downstream Connections

Outputs consumed by other personal-brand skills:
- `brand/queue/assets/<entry_id>/reel.mp4` or `carousel/slide-N.png` → **scheduler-publisher** ships to channels (reads `visual_assets_dir:` frontmatter key on the source draft)
- `brand/queue/assets/<entry_id>/render_log.jsonl` → **performance-review** reads to correlate per-scene engine (remotion / hyperframes) with engagement outcomes; after 10+ reels the weekly-ritual can flag per-scene_type engine tier moves
- `brand/queue/assets/<entry_id>/manifest.json` → any skill consuming the asset set can discover kind (reel / carousel), SHA, brief linkage
- `source draft frontmatter: visual_assets_dir:` → written back by `import_assets.py` so post-writer / repurpose know the asset set exists

Upstream producers (this skill reads):
- **post-writer** / **repurpose** / **case-study-generator** — produce the source draft with `## Scene breakdown` (Path B) or `## Slide N` sections (Path A)
- **personal-brand-dna** — produced brand-identity.md + voice-lock.md + pillars.md LOCKED gate
- **content-calendar** — may pre-assign `visual_type:` frontmatter key on the draft

Cross-skill flag: when parsing a draft, if `## Scene breakdown` is missing but channel is LinkedIn-video / IG-Reel, flag "post-writer should add a scene breakdown" rather than inventing one.

## Anti-patterns

- ❌ Do NOT use generative AI image tools (Kling, Meta AI, Veo, Nano Banana, Midjourney, DALL-E) for reel scenes. Path B is code-rendered only.
- ❌ Do NOT render photographs into reel scenes. Exception: `brand/face-samples/face-01.jpg` on outro only.
- ❌ Do NOT invent brand colors or fonts. Use brand-identity.md LOCKED specs.
- ❌ Do NOT use em dashes in any rendered text (universal rule).
- ❌ Do NOT render internal IDs (entry_id, UUIDs) in visible slide/scene chrome.
- ❌ Do NOT use paid APIs. v7 stack is $0 marginal cost.
- ❌ Do NOT build templates that violate the Motion Design Playbook (linear easing, solid bg, default fade-in, mixed 3-weight type). If it doesn't feel like Jack Butcher / Linear / Vercel / Framer quality, it's Tier 2 experimental at best.

## Learnings & Rules

<!--
Format: [DATE] [CONTEXT] Finding → Action. Keep the most recent ~20 entries.
See references/feedback-loop.md for protocol + context tags.
Quarterly housekeeping: run scripts/audit_skill.py to flag stale references / orphan scripts / missing version tags.
-->
- [2026-04-22] [v7.4 DUAL-ENGINE — Remotion + Hyperframes coexist, rule-based routing by scene_type] After two DataReveal + KineticHook bakeoff comparisons (tie-or-lose outcomes for Hyperframes vs v7.3 Remotion UI-mockup scenes) AND reading HeyGen's full Hyperframes docs + the Remotion vs Hyperframes article, decision was made NOT to replace Remotion but to ADD Hyperframes as a second engine. Rationale: each has different best cases — Remotion for UI-mockup teardown with deterministic React primitives; Hyperframes for social-platform-native overlays via its catalog blocks (x-post, instagram-follow, tiktok-follow, reddit-post, spotify-card, macos-notification, yt-lower-third) which Remotion has no counterpart for. Shipped: (1) `brand/remotion-studio/src/theme/design-tokens.json` as single source of truth for palette/fonts/easing/durations; (2) `scripts/build_shared_tokens.py` regenerates `brand/hyperframes-scenes/shared/tokens.css` from the JSON + validates brand.ts parity; (3) `scripts/scene_spec.py` with normalized Scene dataclass + SCENE_ROUTING + HYPERFRAMES_CATALOG_MAP; (4) `generate_reel.py` extended with `render_scene_hyperframes()` + dual-engine main loop that routes per scene_type + appends render events to `<entry_id>/render_log.jsonl`; (5) `brand/hyperframes-scenes/` project initialized with x-post catalog block pre-installed + tokens.css linked. Rule locked: both engines read tokens.json — no engine gets to drift on palette/fonts/easing/durations. Learning hook: after 10+ reels, performance-review skill can read render_log.jsonl and surface engine preferences per scene_type.
- [2026-04-21] [v7.3 DESIGN PIVOT — UI-mockup aesthetic (Cody Plofker direction)] After geometric abstractions shipped in v7.1 and Mayank reviewed the reel ("worst design i have seen — when someone is talking about landing page, a landing page scrolling with hover animations can visualize an actual landing page mockup"), the geometric/kinetic direction was abandoned mid-pipeline. New direction: realistic browser mockups + landing pages + form animations + eye-gaze trails + callout arrows — every scene should feel like watching Cody Plofker teardown a live LP. Built 10 UIMockup primitives in `brand/remotion-studio/src/components/UIMockups.tsx` (BrowserFrame, LandingPageMockup with 5 variants, Counter with pace option, Cursor, GazeTrail, FoldLine, CalloutArrow, BrowserCycler, FormReducer, LiftChart). All 5 compositions rewritten to compose these primitives. Subtitles shrunk 96→56px (School B default) / 72px (School A), anchor dropped 1760→1560 for lower-third position. Docs added: `references/ui-mockup-vocabulary.md` (primitive catalog), `references/v7-pipeline-architecture.md` (end-to-end dataflow), `references/remotion-guide.md` (studio structure + CLI). Rule locked: **Path B always uses realistic UI mockups, never generic geometric abstractions. Design discussions happen in user's language ("landing page with hover animations") not technical jargon ("stagger containers").**
- [2026-04-21] [v7.3 POLISH bugs fixed] Three end-of-session fixes: (1) CalloutArrow label `"9 \u2192 3 fields"` was escaped in JSON → replaced with literal Unicode `→` character; (2) ProblemBeat stopwatch block + callout label overlapped — moved callout fromY 300→420 to sit below stopwatch; (3) Counter Expo-Out easing settled early in Hook scene (hit 40 at frame 45 of 87) — added `pace="linear"` prop so it ticks uniformly across scene duration. Verified frame-by-frame: hook counter paces 7→22→40 across scene, problem callout label sits cleanly below stopwatch, data arrow renders "9 → 3 fields" correctly.
- [2026-04-21] [v7.2 QA gate wired as post-render step] Built `scripts/qa_reel.py` running 3 checks on frames extracted at 2fps: visual_density ≥ 0.08 (empty-frame detector via ffmpeg signalstats Yavg/Yvar), pure_black_ratio ≤ 0.92 (bg-dominated detector), frame_delta ≥ 0.01 (motion presence via SSIM between consecutive frames). `generate_reel.py` invokes qa_reel.py after stitch; non-zero exit warns without blocking. On wellness-LP smoke, 39/39 frames passed after v7.2 build. Rule: QA gate catches shape-level failures (black hole, empty, stuck); human review still needed for creative-intent match.
- [2026-04-21] [v7.2 KaraokeCaption rewrite — bypass + sticky-active] `createTikTokStyleCaptions` from @remotion/captions grouped 6 words with tight inter-word gaps onto one page, overflowing 900px max-width. Fix: bypassed it — built `groupIntoPages(words, maxWordsPerPage)` with hard caps (School A = 1 word/page, School B = 2 words/page). Also added sticky-active rule in RenderedPage: `const stickyActiveIdx = page.tokens.reduce((best, t, idx) => currentTimeMs >= t.fromMs ? idx : best, -1);` — last-started word stays highlighted until next word starts, no dead-state where all words are dim. Rule: when @remotion library behavior doesn't fit our design, bypass with local logic rather than layering workarounds on top.
- [2026-04-21] [v7.1 Remotion scaffold shipped — geometric-first, later pivoted] First Remotion build with MeshGradient (Paper Design shaders), KaraokeCaption three-school framework, 5 compositions (all geometric: SceneAccent + stagger containers). Required `setChromiumOpenGlRenderer("angle")` in remotion.config.ts — without it, Paper shaders crash with "WebGL not supported." Scene durations tuned (hook 2.9s, problem 3.3s, insight 5.0s, data 3.8s, outro 3.8s) with ~300-500ms buffer past VO last word to avoid mid-word cuts. TypeScript cast pattern: `component={X as unknown as React.ComponentType<Record<string, unknown>>}`. Direction later rejected (see 2026-04-21 v7.3 DESIGN PIVOT entry) — geometric abstractions replaced with UI mockups.
- [2026-04-21] [v7 REBUILD — Remotion-first, geometric-only] After v6 faceless polish + v7 tri-stack audit exposed compounding complexity (3500+ lines across 14 scripts, raw-scene-visual injection bugs in Kling/Meta AI prompts, 7 layered versions of code with no pruning discipline), Mayank chose to rebuild Path B from scratch. New architecture: **Remotion-primary, Hyperframes deprecated, ChatterBox voice, free BGM, geometric/kinetic visual language — no photos except static outro portrait, no AI image generation anywhere.** Creative standard locked in `references/motion-design-playbook.md` with 5 named easing curves, 4-beat per-scene structure, 12 Tier-1 templates, hard "never-do" list (linear easing, stock/AI photos, em dashes, off-palette colors, motion without meaning). Kept: `generate_brief.py` + `render_html_carousel.py` + `render_html_mp4.py` (Path A carousels, works). Archived: `assemble_reel.py` + `generate_tow_prompts.py` to `.archive-v6/` for port reference (POLISH_FILTER + parse_scenes). Deleted: `enroll_face.py`, `extract_vo_chunk.py`, `build_motion_scene.py`, `face-lock.md`, 7 face portraits (kept face-01 for outro), all test-reel artifacts. Rule locked: versions that pivot get their dead code deleted in the same session — no more layered-version accretion.
- [2026-04-21] [Dead-code prune — 3.7 GB freed, v5/v5.5 paths removed] Deleted align_veo_to_vo.py + lipsync_scene.py + brand/_lipsync/ (SadTalker/MuseTalk/Wav2Lip + venv, 3.7 GB) + .v5-backup/ (21 MB) + voiceover-f5.mp3. Code cleanup: removed auto_align_veo() + auto_render_lipsync() from assemble_reel.py, simplified precedence from 7 tiers to 5. Regression test passed on wellness-LP reel. Rule: when a version is pivoted away from, the NEXT session deletes the dead code in the same turn as the pivot entry.
- [2026-04-21] [v6 build — polish pipeline + kinetic-hook + outro-card + flash transitions + BGM ducking] Shipped POLISH_FILTER (eq + vignette + grain), generate_flash_clip() (2-frame white between scenes), resolve_bgm() + _mux_audio() with sidechaincompress ducking, kinetic-hook + outro-card Hyperframes templates. All CLI flags default to ON. **Archived 2026-04-21 to .archive-v6/assemble_reel.py — ffmpeg chain will be ported to Path B stitching step.**
- [2026-04-21] [Session 3g — Hyperframes template library + lip-sync infrastructure] Shipped chart-bars / icon-grid / quote-card Hyperframes templates. SadTalker CPU inference benchmarked at 23 min/clip — not viable for shipping. Deleted 2026-04-21 in v7 rebuild.
- [2026-04-21] [TOW v4 — Hyperframes motion-graphic scene templates + auto-invoke] data-reveal + kinetic-insight Hyperframes templates + parametric placeholder substitution via build_motion_scene.py. **Deleted 2026-04-21 in v7 rebuild** — port to Remotion compositions in Phase 6.
- [2026-04-21] [TOW v2 — ChatterBox replaces F5-TTS as primary engine] Chatterbox MIT-licensed, native exaggeration + cfg_weight knobs, 63.75% preference vs ElevenLabs. EMOTION_PARAMS map ties 15 emotion tags to (exag, cfg, ref_sample_id). **ACTIVE in v7 — clone_voice.py kept unchanged.**
- [2026-04-21] [clone_voice VO extraction bugs] Two patches: (1) MULTILINE regex for `## Voiceover script` heading strip, (2) clean_for_tts() strips [emotion] tags before TTS (they leaked as spoken words in F5-TTS). Rule: strip anything non-speakable from text BEFORE sending to synthesizer.
- [2026-04-21] [ffmpeg bugs fixed in assemble_reel.py] Three ffmpeg gotchas: (1) force_original_aspect_ratio accepts `decrease`/`increase` only, use cover-semantics via scale+crop, (2) arg ordering — all `-i` inputs before codec/filter/map options, (3) `-f lavfi` before `-i anullsrc`. Rule: `[base flags] → [all -i] → [codecs/maps] → [output]`.
- [2026-04-21] [F5-TTS + Python 3.9 incompatibility] F5-TTS and modern ML libs require Python 3.10+. Fix: `brew install python@3.11` and use `/opt/homebrew/bin/python3.11` for all ML scripts. clone_voice.py auto-re-execs if launched under 3.9.
- [2026-04-21] [Face enrollment + face-lock] enroll_face.py built a dark-mode wizard for 8-angle face corpus. **Deleted 2026-04-21 in v7 rebuild** — geometric-first stack only uses face-01.jpg for outro.
- [2026-04-21] [Voice cloning infrastructure] enroll_voice.py + clone_voice.py. **voice-samples/ corpus and both scripts KEPT in v7.**
- [2026-04-19] [Path A full loop proven] Claude Design bundle → render_html_mp4.py → 9:16/1080x1920/15s/1.1 MB MP4 for 4e4eed15-anim. **Path A unchanged in v7.**
- [2026-04-19] [Path B full loop proven via Hyperframes] Original Hyperframes path rendered 45-sec 4e4eed15 reel at 1080x1920 in 1m51s. **Superseded by Remotion in v7.**
- [2026-04-19] [Render pipeline] First Claude Design handoff for ISKM Ratha Yatra carousel succeeded. render_html_carousel.py parses `<section class="slide">` + per-slide standalone HTML + Chrome headless at 1080x1350. **Active in v7 Path A.**
- [2026-04-19] [Brief template gap → NO INTERNAL IDS rule] Fixed generate_brief.py BRAND_BLOCK to explicitly forbid entry_id/source-id/UUID text in visible chrome. Active rule.
- [2026-04-19] [Initial build] v1 ships as thin orchestrator: brief-gen + asset-import only. Free-only stack.
- [2026-04-22] [Notification-UX batch] Renderers now use `shared-scripts/notify.py:notify_reviewable_artifact()` instead of inline osascript. **render_html_carousel.py:** dropped the standalone `preview.html` generator — the click target is now `http://127.0.0.1:8765/#draft-<filename>` in review_queue where caption + body + Approve/Edit/Reject buttons sit on the same page. Helper auto-spawns review_queue.py if not running. **render_html_mp4.py:** added the missing notification (it had none) with same click-to-review-card pattern. **generate_reel.py:** replaced the old `osascript display notification "Reel v7 ready"` with the helper. Fail-case notifications use sound "Basso". No more dead-end render banners — every render lands on a draft card where the user can act.
