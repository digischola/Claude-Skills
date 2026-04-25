#!/usr/bin/env python3
"""
TOW Path B Reel prompt packet generator (Claude-driven, Gemini Pro paste-target).

Reads:
  - A Reel-format draft .md file (must have format: reel + scene breakdown)
  - brand/face-lock.md (CHARACTER LOCK BLOCK + skin enhancer + negative prompt)
  - brand/voice-lock.md (reference samples for clone_voice.py)

Outputs:
  - One HTML "Reel packet" page at /tmp/reel-packet-<entry_id>.html
  - Auto-generated voiceover.mp3 via clone_voice.py (when F5-TTS is installed)

The HTML packet shows everything Mayank needs in one place:
  - Reel caption (with Copy button — paste in IG composer)
  - Scene-by-scene cards, each with:
      * VO line + on-screen text
      * Reference photo recommendation (from face-lock.md table)
      * Nano Banana Pro image prompt (Copy + paste in Gemini)
      * Veo 3.1 video prompt (Copy + paste in Google Flow)
  - Voiceover script (Copy)
  - Inline <audio> player for clone_voice.py-generated voiceover.mp3
  - Final assembly button (calls assemble_reel.py once scene MP4s downloaded)

Usage:
    python3 generate_tow_prompts.py --draft <path-to-reel-draft.md>
    python3 generate_tow_prompts.py --draft ... --no-open
    python3 generate_tow_prompts.py --draft ... --skip-vo   # don't auto-render VO

Pipeline assumption: post-writer produces the Reel draft with frontmatter +
a "## Scene breakdown" section parseable by `parse_scenes`.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import subprocess
import sys
import urllib.parse as urlparse
from pathlib import Path

DEFAULT_BRAND = Path("/Users/digischola/Desktop/Digischola")
PRIMARY = "#3B9EFF"
BG = "#0A0F1C"
CARD_BG = "#111827"
BORDER = "#1F2937"
TEXT = "#E5E7EB"
MUTED = "#9CA3AF"
GREEN = "#10B981"
GOLD = "#F59E0B"


# ── Frontmatter + scene parsing ────────────────────────────────────────────

def read_md(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}, text
    _, fm_block, body = text.split("---\n", 2)
    fm = {}
    for line in fm_block.splitlines():
        if ":" in line and not line.startswith(" "):
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip().strip("'\"")
    return fm, body.lstrip()


def parse_caption(body: str) -> str:
    m = re.search(r"## Caption[^\n]*\n(.*?)(?=\n## |\Z)", body, re.DOTALL)
    return m.group(1).strip() if m else ""


def parse_vo_script(body: str) -> str:
    m = re.search(r"## Voiceover script[^\n]*\n(.*?)(?=\n## |\Z)", body, re.DOTALL)
    return m.group(1).strip() if m else ""


def parse_scenes(body: str) -> list[dict]:
    """Extract Scene 1, Scene 2, ... blocks under '## Scene breakdown'."""
    sec = re.search(r"## Scene breakdown[^\n]*\n(.*?)(?=\n## |\Z)", body, re.DOTALL)
    if not sec:
        return []
    text = sec.group(1)
    scenes = []
    scene_matches = list(re.finditer(r"### Scene (\d+)[^\n]*\n(.*?)(?=\n### Scene |\Z)", text, re.DOTALL))
    total = len(scene_matches)
    for idx, m in enumerate(scene_matches):
        n = int(m.group(1))
        block = m.group(2).strip()
        heading_line = re.search(rf"### Scene {n}([^\n]*)", text).group(1).lower()
        # Field extractor — matches "- VO: ..." style bullets
        def field(label, default=""):
            mm = re.search(rf"-\s*{label}[:\s]+(.+?)(?=\n-\s|\Z)", block, re.DOTALL | re.IGNORECASE)
            return mm.group(1).strip() if mm else default
        scene = {
            "n": n,
            "vo": field("VO"),
            "visual": field("Visual"),
            "reference": field("Reference"),
            "mood": field("Mood"),
            "overlay": field(r"On-screen text overlay"),
            "heading": heading_line,
        }
        scene["scene_type"] = classify_scene_type(scene, idx, total)
        scene["duration_sec"] = DURATION_BY_TYPE.get(scene["scene_type"], 4.0)
        scenes.append(scene)
    return scenes


# ── Scene classification + per-type durations ─────────────────────────────

# 7 scene types. Drives engine routing in assemble_reel.py + emotion mapping in clone_voice.py.
# v6 "Faceless Premium" pipeline: hook/cta become kinetic-text motion graphics
# (Hyperframes auto-generated), founder_face DEPRECATED for body scenes,
# outro is the new final scene that brings face back via static Ken Burns + logo.
DURATION_BY_TYPE = {
    "hook": 2.5,          # kinetic-hook template — punch text
    "problem_beat": 4.0,  # Meta AI B-roll cutaway (free, unlimited regens)
    "face_body": 4.5,     # Kling Standard/Pro face-body + lip-sync (v7)
    "founder_face": 4.0,  # DEPRECATED body scene — kept for v5 backward compat
    "insight_beat": 4.5,  # kinetic-insight template — thesis reveal
    "data_reveal": 3.5,   # data-reveal template — count-up
    "cta": 4.0,           # outro-card template — face Ken Burns + CTA text overlay
    "outro": 3.5,         # outro-card template — brand mark + logo reveal
}

# Draft-author-controlled labels after the em-dash in scene headings.
# e.g. "### Scene 2 (6-13 sec) — Problem" → problem_beat
HEADING_LABEL_MAP = {
    "hook": "hook",
    "problem": "problem_beat",
    "tension": "problem_beat",
    "b-roll": "problem_beat",
    "broll": "problem_beat",
    "cutaway": "problem_beat",
    "the rule": "insight_beat",
    "the shift": "insight_beat",
    "the truth": "insight_beat",
    "the lesson": "insight_beat",
    "insight": "insight_beat",
    "the data": "data_reveal",
    "data": "data_reveal",
    "stat": "data_reveal",
    "stat reveal": "data_reveal",
    "proof": "data_reveal",
    "cta": "cta",
    "close": "cta",
    "handoff": "cta",
    "outro": "outro",
    "brand mark": "outro",
    "sign-off": "outro",
    # v7 face-body scene (Kling) — use when Mayank is ON SCREEN talking
    "face-body": "face_body",
    "face body": "face_body",
    "mayank on camera": "face_body",
    "mayank speaking": "face_body",
    "talking head": "face_body",
    "founder": "founder_face",  # v5 legacy — kept for backward compat
}

# Fallback content cues (only used when heading label is missing/unrecognized)
CLASSIFIER_CUES = {
    "data_reveal": [r"\+?\s*\d+\s*%", r"\bconversion by\b", r"\bcount[- ]?up\b"],
    "cta": [r"\bcta\b", r"audit yours", r"click the link", r"\blink in bio\b", r"\bdm me\b", r"\bcomment below\b", r"\bsave this\b"],
    "insight_beat": [r"here's the rule", r"here's why", r"\bthe rule\b", r"\bthe shift\b"],
    "problem_beat": [r"problem is real", r"\btension\b"],
    "founder_face": [r"\bmayank\b", r"face-\d"],
}

HEADING_LABEL_RE = re.compile(r"—\s*([A-Za-z][A-Za-z\s]*?)\s*$")


def extract_heading_label(heading_line: str) -> str:
    """Pull label after the em-dash in '(0-6 sec) — Hook' → 'hook'."""
    m = HEADING_LABEL_RE.search(heading_line.strip())
    return m.group(1).strip().lower() if m else ""


def classify_scene_type(scene: dict, idx: int, total: int) -> str:
    """Route each scene to one of 6 types. Heading label > content cues > positional default.

    The draft author controls the primary signal via scene-heading labels like
    "### Scene 3 — The rule". Content cues only fire when the heading is unlabeled.
    """
    # 1. Heading label (authoritative — draft author intent)
    label = extract_heading_label(scene.get("heading", ""))
    if label in HEADING_LABEL_MAP:
        return HEADING_LABEL_MAP[label]

    # 2. Content cues on VO + overlay + mood (visual excluded — too many false positives)
    haystack = " ".join([
        scene.get("vo", ""),
        scene.get("overlay", ""),
        scene.get("mood", ""),
    ]).lower()
    for scene_type in ("data_reveal", "cta", "insight_beat", "problem_beat", "founder_face"):
        for cue in CLASSIFIER_CUES[scene_type]:
            if re.search(cue, haystack, re.IGNORECASE):
                return scene_type

    # 3. Positional defaults
    if idx == 0:
        return "hook"
    if idx == total - 1:
        return "cta"
    return "founder_face"


def parse_face_lock(brand: Path) -> dict:
    p = brand / "brand" / "face-lock.md"
    if not p.exists():
        return {"character_block": "", "skin_block": "", "negative": ""}
    text = p.read_text(encoding="utf-8")
    def grab(header):
        # Find the header, then the FIRST code block after it (allowing any prose between)
        m = re.search(rf"## {header}[^\n]*\n", text)
        if not m:
            return ""
        rest = text[m.end():]
        # Stop at next "## " (next major section)
        next_section = re.search(r"\n## ", rest)
        slice_end = next_section.start() if next_section else len(rest)
        section = rest[:slice_end]
        # Grab first ```...``` inside this section
        cb = re.search(r"```\w*\n(.*?)```", section, re.DOTALL)
        return cb.group(1).strip() if cb else ""
    return {
        "character_block": grab("CHARACTER LOCK BLOCK"),
        "skin_block": grab("SKIN ENHANCER SUFFIX"),
        "negative": grab("NEGATIVE PROMPT"),
    }


# ── Prompt builders (Nano Banana Pro + Veo 3.1) ────────────────────────────

def build_nano_banana_prompt(scene: dict, face: dict, draft_meta: dict) -> str:
    """Compose the Nano Banana Pro prompt: scene + character + skin + negative.

    v4 CHANGE: text overlay is NO LONGER rendered into the image. Hyperframes
    + ffmpeg drawtext handle kinetic text in post-production. The Nano Banana
    pass now generates clean, text-free images that feel like real photos.
    If the scene is data_reveal or insight_beat, we don't even generate a face
    image — those are 100% Hyperframes-rendered motion graphics.
    """
    scene_type = scene.get("scene_type", "founder_face")

    # Data reveals and kinetic-insight scenes don't need a face image at all
    if scene_type in ("data_reveal", "insight_beat"):
        return f"""[SCENE TYPE: {scene_type}]

This scene is built 100% via Hyperframes motion graphics — no Nano Banana image needed.
Skip this scene for Gemini. Move to the next scene.

(Hyperframes will auto-generate: {'big-number count-up with brand-colored chart' if scene_type == 'data_reveal' else 'full-screen kinetic typography for the insight line'}.)"""

    return f"""Generate a vertical 9:16 photorealistic image, 1080x1920, for an Instagram Reel scene.

SCENE: {scene['visual']}

CHARACTER:
{face['character_block']}

COMPOSITION: Leave the top third and bottom fifth of the frame visually calm and uncluttered — these zones are reserved for motion-graphic text overlays added in post. Place the subject in the middle third. No hands-near-face unless scene specifies. Subject should feel photographed, not posed.

NO TEXT IN IMAGE: Do NOT render any text, captions, labels, numbers, or on-screen graphics in the image. The scene must be purely photographic — text overlays are added later via motion graphics. If the scene description mentions an overlay, IGNORE that text in the image itself.

STYLE:
{face['skin_block']}

NEGATIVE:
{face['negative']}, no text in image, no captions, no labels, no numbers rendered in scene, no on-screen typography, no watermarks"""


def build_veo_prompt(scene: dict, draft_meta: dict, face: dict | None = None) -> str:
    """Compose the Veo 3.1 Fast video prompt.

    v5 CHANGE: For founder_face / hook / cta scenes, we now DO want Veo to
    generate lip-synced dialogue (native Veo 3.1 feature via `"quoted speech"`
    in the prompt). We strip Veo's audio later and overlay ChatterBox's cloned
    voice via align_veo_to_vo.py — the mouth movements already match the words
    so lip-sync holds when we swap the voice track.

    For non-speaking scenes (problem_beat B-roll), we still suppress dialogue.
    Motion-graphic scene types (data_reveal, insight_beat) skip Veo entirely.
    """
    scene_type = scene.get("scene_type", "founder_face")
    face = face or {"character_block": "", "negative": ""}

    # Motion-graphic scenes — Hyperframes handles these, skip Veo
    if scene_type in ("data_reveal", "insight_beat"):
        return f"""[SCENE TYPE: {scene_type}]

Skip Veo for this scene — Hyperframes will auto-generate a motion graphic
({'big-number count-up with brand-colored chart' if scene_type == 'data_reveal' else 'full-screen kinetic typography'}).
Move to the next scene."""

    # Speaking scenes (founder_face / hook / cta) — lip-synced dialogue
    if scene_type in ("founder_face", "hook", "cta"):
        vo_line = scene.get("vo", "").strip().strip('"').strip()
        # Escape any internal double quotes (Veo prompt uses them as dialogue delimiters)
        vo_line = vo_line.replace('"', "'")
        return f"""Generate an 8-second vertical 9:16 cinematic video clip at 1080x1920.

CHARACTER (locked identity — must look exactly like this across the clip):
{face.get('character_block', '')}

SCENE: {scene['visual']}

DIALOGUE (lip-synced): Mayank says, "{vo_line}"

Natural speaking pace. Mouth moves accurately for each word. Eyes direct to camera unless scene specifies otherwise. Natural micro-expressions. Subtle head movement. NO SUBTITLES, NO CAPTIONS, NO TEXT OVERLAY on the video. Normal conversational cadence.

AUDIO: Generate the spoken dialogue with clear, natural male voice. Confident but not forced. No music, no sound effects, no background noise. (We will strip your audio and overlay cloned voice in post — but we need your voice so your lip-sync tracks the right words.)

CAMERA: 50mm lens feel, shallow depth of field, eye-level, subtle handheld stability.

PRESERVE: identity, face structure, outfit, lighting from the character description above. Keep every frame photographic and brand-consistent. No cartoon / CGI / uncanny-valley feel."""

    # problem_beat and other non-speaking scenes — silent B-roll
    return f"""Animate this image into a 5-7 second vertical 9:16 cinematic video clip.

AUDIO: NO DIALOGUE. NO SPEECH. Subject is visible but NOT SPEAKING. Lips remain closed. Silent clip or subtle ambient room tone only. The voiceover is added in post — do NOT generate any vocal audio.

MOTION: subtle handheld feel. Cinematic pan or slight push-in matching the mood. No exaggerated motion. Premium feel, not TikTok-fast.

SCENE: {scene['visual']}

PRESERVE: identity, outfit, lighting, environment from the input image. Character must look identical to the reference frame. End on a clean held frame for hard-cut to next scene.

CAMERA: 50mm lens feel, shallow depth of field, eye-level."""


def build_kling_prompt(scene: dict, draft_meta: dict, face: dict | None = None) -> str:
    """Compose the Kling Pro video prompt for face_body scenes (v7).

    Kling's Lip Sync + Image/Subject Reference + Motion Control tools give us
    tight lip-sync (±200ms) with subject consistency across scenes — fixing
    Veo's seconds-level drift problem. Workflow: Mayank pastes this prompt in
    Kling's Image-to-Video tool, uploads a face-samples/face-NN.jpg reference,
    picks a camera move, Kling generates face+body+lips-moving MP4, Mayank
    downloads as scene-N-kling.mp4. Lip Sync tool is a separate step if the
    base generation's lips drift.

    HARD RULE: No text, no captions, no numbers, no UI elements in the prompt.
    Kling will render garbled text if asked. All text comes from Hyperframes
    overlay, composited in post.
    """
    scene_type = scene.get("scene_type", "face_body")
    # ONLY face_body + legacy founder_face use Kling. hook/cta/outro are
    # pure Hyperframes (kinetic typography + outro-card). data_reveal +
    # insight_beat are pure Hyperframes. problem_beat uses Meta AI.
    if scene_type not in ("face_body", "founder_face"):
        return ""

    face = face or {"character_block": "", "negative": ""}
    vo_line = scene.get("vo", "").strip().strip('"').strip().replace('"', "'")
    visual = scene.get("visual", "").strip()
    mood = scene.get("mood", "").strip()
    duration = DURATION_BY_TYPE.get(scene_type, 4.5)

    # Infer camera move from mood or default to subtle push-in
    camera_move = "slow cinematic push-in on eyes, 1 ft/sec"
    mood_lower = mood.lower()
    if any(c in mood_lower for c in ["handoff", "close", "confident close", "pull"]):
        camera_move = "slow pull-back from medium to wide, 1 ft/sec"
    elif "static" in mood_lower or "held" in mood_lower or "authority" in mood_lower:
        camera_move = "static eye-level 50mm lens, locked"
    elif "warm" in mood_lower or "opening" in mood_lower:
        camera_move = "very subtle handheld drift, 0.5 ft/sec"

    return f"""KLING PROMPT — face-body scene (paste into Kling Pro Image-to-Video + Lip Sync)

REFERENCE IMAGE: upload {scene.get('reference', 'face-01.jpg')} from brand/face-samples/ as the subject reference.

SCENE (visual only, NO text, NO captions, NO UI elements, NO numbers on screen):
{visual}

SUBJECT IDENTITY (must be preserved exactly — upload the reference photo):
{face.get('character_block', '').strip() or 'See reference image — match identity, skin, hair, eyebrows, facial structure, outfit exactly.'}

DIALOGUE (for Lip Sync tool — paste the audio + this text after base video renders):
"{vo_line}"

CAMERA: {camera_move}. 50mm lens feel, shallow depth of field, eye-level. Subtle natural blinks + micro-expressions. No exaggerated head movement.

MOOD: {mood or 'confident, warm, authoritative'}

DURATION: {duration} seconds

FORMAT: 9:16 vertical, 1080x1920, 720p or 1080p OK.

HARD CONSTRAINTS:
- NO text on screen. NO captions. NO numbers. NO logos. NO UI mockups.
- NO background text or signs with legible characters.
- Text overlays are added in post via Hyperframes — leave the frame clean.
- Pure photographic feel. No cartoon, no CGI, no uncanny-valley.

WORKFLOW:
1. Kling → "Image to Video" tool → upload reference photo + paste visual+camera description above.
2. Wait for 720p generation (~60-90 sec on Standard, faster on Pro).
3. Kling → "Lip Sync" tool → upload the generated video + the ChatterBox voiceover chunk for this scene + paste the DIALOGUE text above.
4. Download final → save as scene-{scene['n']}-kling.mp4 in brand/queue/assets/{draft_meta.get('entry_id', '<entry>')}/
5. Next assembler run auto-aligns duration + muxes with ChatterBox VO via align_kling_to_vo.py (trim-only, no re-alignment needed)."""


def build_meta_ai_prompt(scene: dict, draft_meta: dict) -> str:
    """Compose the Meta AI Imagine / image-to-video prompt for problem_beat scenes (v7).

    Meta AI (meta.ai / WhatsApp Meta AI / Instagram Meta AI) is free + unlimited,
    so quality-per-clip concerns disappear — Mayank regenerates until happy.
    Used ONLY for generic problem_beat cutaways (empty desk, laptop screen,
    scattered papers, shadowy office). NO humans with recognizable faces, NO
    text on screen.

    HARD RULE (enforced in the prompt): zero text in frame. Diffusion models
    garble typography. All text comes from Hyperframes overlay in post.
    """
    scene_type = scene.get("scene_type", "")
    if scene_type != "problem_beat":
        return ""

    visual = scene.get("visual", "").strip()
    mood = scene.get("mood", "").strip()
    duration = DURATION_BY_TYPE.get("problem_beat", 4.0)

    return f"""META AI PROMPT — problem-beat B-roll (paste into meta.ai or WhatsApp/IG Meta AI)

Step 1 — generate the still image via Meta AI Imagine:

"{visual} — cinematic 9:16 vertical frame, shallow depth of field, dim moody lighting, muted desaturated color grade, 50mm lens feel, film-grain texture. Empty of people and faces unless explicitly requested. {f'Mood: {mood}.' if mood else ''} IMPORTANT: absolutely NO text, NO captions, NO numbers, NO labels, NO UI text, NO signage with legible characters, NO letters on screens or monitors, NO writing on paper, NO logos. Pure atmospheric visual — text will be added in post-production. Avoid cartoon, illustration, CGI — photorealistic only."

Step 2 — animate the image via Meta AI's image-to-video feature:

"Animate this still into a {duration}-second silent video clip. Subtle {_motion_hint(mood)}. No camera cuts, no major movement, no people walking into frame. Preserve the mood and composition. End on a clean held frame so it hard-cuts cleanly to the next scene. Keep the no-text rule — if any text appears in the motion, regenerate."

Step 3 — download as MP4 → save to:
brand/queue/assets/{draft_meta.get('entry_id', '<entry>')}/scene-{scene['n']}-broll.mp4

Regeneration policy: Meta AI is free + unlimited. If the first clip has any text, drift, garbled visuals, or wrong mood — regenerate until clean. Expected: 2-4 attempts per scene to land a keeper.

ALTERNATIVE FREE TOOLS (equivalent quality, pick whichever is fastest for you): Luma Dream Machine (free daily credits), Pika Labs (free tier), Hailuo MiniMax (free generous tier). All output to the same scene-{scene['n']}-broll.mp4 filename — assembler doesn't care which tool rendered it."""


def _motion_hint(mood: str) -> str:
    """Infer the right subtle motion description for a problem_beat from mood."""
    m = mood.lower()
    if "tension" in m or "frustration" in m:
        return "slow push-in, camera drifts closer (parallax reveal)"
    if "cold" in m or "quiet" in m or "empty" in m:
        return "static frame with subtle particle/dust motion in air"
    if "urgency" in m or "scrolling" in m:
        return "slow pan left-to-right across the scene"
    return "very subtle handheld drift, 0.5 ft/sec"


def build_vo_prompt_for_elevenlabs(vo_script: str) -> str:
    """ElevenLabs Alphav3-format VO prompt with emotion tags preserved."""
    return f"""Generate voiceover audio using ElevenLabs Alphav3 model.

VOICE: my cloned voice (use Voice ID: <YOUR_VOICE_ID>)
PACE: confident, measured, slight UGC energy on hooks. Allow natural breath pauses between sentences.
EMOTION: tags in [brackets] should drive delivery — neutral, direct, measured, firm, confident, etc.

SCRIPT (preserve emotion tags inline, render natural pauses between scene-line groups):

{vo_script}"""


# ── HTML packet ────────────────────────────────────────────────────────────

def render_packet(draft_path: Path, fm: dict, body: str, brand: Path,
                  scenes: list[dict], face: dict, vo_script: str,
                  caption: str, voiceover_path: Path | None) -> str:
    entry_id = fm.get("entry_id", "unknown")
    duration = fm.get("duration_target_sec", "30")

    # Per-scene cards
    scene_cards = []
    for s in scenes:
        scene_type_s = s.get("scene_type", "")
        nano_prompt = build_nano_banana_prompt(s, face, fm)
        veo_prompt = build_veo_prompt(s, fm, face)
        kling_prompt = build_kling_prompt(s, fm, face)      # v7: face_body
        meta_ai_prompt = build_meta_ai_prompt(s, fm)        # v7: problem_beat
        ref_recommendation = s.get("reference", "face-01.jpg")
        # Build reference photo paths (parse e.g. "face-02.jpg + face-01.jpg")
        ref_files = re.findall(r"face-\d+\.jpg", ref_recommendation)
        ref_blocks = []
        for f in ref_files:
            p = brand / "brand" / "face-samples" / f
            if p.exists():
                file_url = f"file://{urlparse.quote(str(p))}"
                ref_blocks.append(
                    f'<a href="{html.escape(file_url)}" target="_blank" class="ref-thumb">'
                    f'<img src="{html.escape(file_url)}" alt="{html.escape(f)}" />'
                    f'<span>{html.escape(f)}</span></a>'
                )
        ref_html = '<div class="ref-grid">' + "".join(ref_blocks) + '</div>' if ref_blocks else '<div class="muted">(no matching reference photos)</div>'

        scene_cards.append(f"""
        <div class="scene-card">
          <div class="scene-head">
            <div class="scene-num">SCENE {s['n']}</div>
            <div class="scene-mood">{html.escape(s.get('mood', ''))}</div>
          </div>
          <div class="vo-line">"{html.escape(s.get('vo', ''))}"</div>
          <div class="visual-desc">{html.escape(s.get('visual', ''))}</div>
          {f'<div class="overlay-tag">📺 Overlay: <b>{html.escape(s.get("overlay", ""))}</b></div>' if s.get('overlay') else ''}

          <div class="ref-section">
            <div class="ref-label">📎 Upload to Gemini alongside the prompt</div>
            {ref_html}
          </div>

          <div class="prompt-section">
            <div class="prompt-label">
              <span>🎨 Nano Banana Pro image prompt</span>
              <button class="copy-btn" onclick="copyPrompt('nb-{s['n']}')">📋 Copy</button>
            </div>
            <pre class="prompt-text" id="nb-{s['n']}">{html.escape(nano_prompt)}</pre>
            <a class="paste-link" href="https://aistudio.google.com/" target="_blank">→ Paste in Google AI Studio (Gemini Nano Banana Pro)</a>
          </div>

          {f'''<div class="prompt-section" style="border-left:3px solid #3B9EFF;">
            <div class="prompt-label">
              <span>🎭 Kling Pro — face-body + Lip Sync <span style="background:#3B9EFF;color:#000;padding:2px 8px;border-radius:4px;font-size:11px;margin-left:8px;">v7 PRIMARY for face scenes</span></span>
              <button class="copy-btn" onclick="copyPrompt('kling-{s['n']}')">📋 Copy</button>
            </div>
            <pre class="prompt-text" id="kling-{s['n']}">{html.escape(kling_prompt)}</pre>
            <a class="paste-link" href="https://app.klingai.com/global/" target="_blank">→ Open Kling AI (Image-to-Video + Lip Sync tools)</a>
          </div>''' if kling_prompt else ''}

          {f'''<div class="prompt-section" style="border-left:3px solid #4ADE80;">
            <div class="prompt-label">
              <span>🎥 Meta AI — problem-beat B-roll <span style="background:#4ADE80;color:#000;padding:2px 8px;border-radius:4px;font-size:11px;margin-left:8px;">FREE · UNLIMITED REGENS</span></span>
              <button class="copy-btn" onclick="copyPrompt('meta-{s['n']}')">📋 Copy</button>
            </div>
            <pre class="prompt-text" id="meta-{s['n']}">{html.escape(meta_ai_prompt)}</pre>
            <a class="paste-link" href="https://www.meta.ai/" target="_blank">→ Open meta.ai (Imagine + Animate)</a>
          </div>''' if meta_ai_prompt else ''}

          <div class="prompt-section" style="opacity:0.6;">
            <div class="prompt-label">
              <span>🎬 Veo 3.1 video prompt <span style="background:#666;color:#fff;padding:2px 8px;border-radius:4px;font-size:11px;margin-left:8px;">v5 LEGACY · skip for face_body/problem_beat</span></span>
              <button class="copy-btn" onclick="copyPrompt('veo-{s['n']}')">📋 Copy</button>
            </div>
            <pre class="prompt-text" id="veo-{s['n']}">{html.escape(veo_prompt)}</pre>
            <a class="paste-link" href="https://labs.google/fx/tools/flow" target="_blank">→ Paste in Google Flow (Veo 3.1) with Nano Banana as starting frame</a>
          </div>
        </div>
        """)

    voiceover_html = ""
    if voiceover_path and voiceover_path.exists():
        vo_url = f"file://{urlparse.quote(str(voiceover_path))}"
        voiceover_html = f"""
        <div class="vo-rendered">
          <h3>🔊 Voiceover MP3 (auto-generated via F5-TTS)</h3>
          <audio controls src="{html.escape(vo_url)}" style="width:100%; margin-top:12px;"></audio>
          <p class="muted" style="font-size:12px; margin-top:8px;">{html.escape(str(voiceover_path))} · {voiceover_path.stat().st_size:,} bytes</p>
        </div>
        """
    else:
        voiceover_html = f"""
        <div class="vo-pending">
          <h3>🔊 Voiceover script (F5-TTS not yet rendered)</h3>
          <pre class="prompt-text" id="vo-script">{html.escape(vo_script)}</pre>
          <button class="copy-btn" onclick="copyPrompt('vo-script')">📋 Copy script</button>
          <p class="muted" style="font-size:13px; margin-top:12px;">Run from terminal once F5-TTS is installed:</p>
          <code class="cmd">python3 visual-generator/scripts/clone_voice.py --draft {html.escape(str(draft_path))}</code>
          <p class="muted" style="font-size:13px; margin-top:8px;">Or paste the script above into ElevenLabs (paid tier required for voice cloning).</p>
        </div>
        """

    # Assembly section (final ffmpeg stitching after Mayank renders Veo scenes)
    assets_dir = brand / "brand" / "queue" / "assets" / entry_id
    assembly_html = f"""
    <div class="assembly-section">
      <h3>📦 Final assembly (after you render the {len(scenes)} Veo scenes)</h3>
      <ol>
        <li>Save each rendered Veo MP4 into <code>{html.escape(str(assets_dir))}</code> as <code>scene-1.mp4</code> … <code>scene-{len(scenes)}.mp4</code> in order.</li>
        <li>Make sure <code>voiceover.mp3</code> is also in that folder (auto-generated above, or render via clone_voice.py).</li>
        <li>Run from terminal:
          <pre class="cmd">python3 visual-generator/scripts/assemble_reel.py --draft {html.escape(str(draft_path))}</pre>
        </li>
        <li>Final MP4 lands at <code>{html.escape(str(assets_dir))}/reel.mp4</code> — review_queue.py shows it inline for approval.</li>
      </ol>
    </div>
    """

    return f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>Reel packet · {html.escape(entry_id)}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;700&family=Orbitron:wght@600;900&family=Space+Grotesk:wght@500;700&display=swap" rel="stylesheet">
<style>
 * {{ box-sizing: border-box; }}
 html, body {{ margin: 0; padding: 0; background: {BG}; color: {TEXT}; font-family: 'Manrope', system-ui; font-size: 15px; line-height: 1.55; }}
 .wrap {{ max-width: 980px; margin: 0 auto; padding: 32px 24px 80px; }}
 header {{ display: flex; align-items: center; justify-content: space-between; padding: 16px 0 24px; border-bottom: 1px solid {BORDER}; margin-bottom: 32px; }}
 h1 {{ font-family: 'Orbitron'; font-weight: 900; font-size: 22px; letter-spacing: 1.5px; margin: 0; background: linear-gradient(90deg, {PRIMARY}, #7ec5ff); -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent; }}
 .meta {{ font-family: 'Space Grotesk'; font-size: 13px; color: {MUTED}; margin-top: 4px; }}
 h2 {{ font-family: 'Space Grotesk'; font-weight: 700; font-size: 12px; letter-spacing: 2px; text-transform: uppercase; color: {MUTED}; margin: 36px 0 14px; }}
 h3 {{ font-family: 'Space Grotesk'; font-weight: 700; font-size: 16px; color: {TEXT}; margin: 0 0 12px; }}

 .caption-box {{ background: {CARD_BG}; border: 1px solid {BORDER}; border-radius: 12px; padding: 22px 26px; }}
 .caption-box pre {{ white-space: pre-wrap; font-family: 'Manrope'; font-size: 16px; margin: 0; }}

 .scene-card {{ background: {CARD_BG}; border: 1px solid {BORDER}; border-radius: 14px; padding: 24px; margin-bottom: 22px; }}
 .scene-head {{ display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; }}
 .scene-num {{ font-family: 'Orbitron'; font-weight: 900; font-size: 14px; letter-spacing: 3px; color: {PRIMARY}; }}
 .scene-mood {{ font-family: 'Space Grotesk'; font-size: 12px; color: {MUTED}; font-style: italic; }}
 .vo-line {{ font-family: 'Space Grotesk'; font-weight: 700; font-size: 18px; color: {TEXT}; padding: 14px 18px; background: rgba(59,158,255,0.06); border-left: 3px solid {PRIMARY}; border-radius: 6px; margin-bottom: 14px; }}
 .visual-desc {{ font-family: 'Manrope'; font-size: 14px; color: {MUTED}; line-height: 1.6; margin-bottom: 12px; }}
 .overlay-tag {{ font-family: 'Space Grotesk'; font-size: 13px; color: {GOLD}; padding: 8px 12px; background: rgba(245,158,11,0.06); border-radius: 6px; margin-bottom: 16px; }}

 .ref-section {{ margin: 18px 0; padding-top: 18px; border-top: 1px dashed {BORDER}; }}
 .ref-label {{ font-family: 'Space Grotesk'; font-size: 11px; letter-spacing: 1.5px; text-transform: uppercase; color: {MUTED}; margin-bottom: 12px; }}
 .ref-grid {{ display: flex; gap: 12px; flex-wrap: wrap; }}
 .ref-thumb {{ display: flex; flex-direction: column; gap: 6px; text-decoration: none; color: {MUTED}; font-size: 11px; font-family: 'Space Grotesk'; transition: opacity 0.15s; }}
 .ref-thumb:hover {{ opacity: 0.85; }}
 .ref-thumb img {{ width: 100px; aspect-ratio: 4/5; object-fit: cover; border-radius: 8px; border: 1px solid {BORDER}; display: block; background: #000; }}

 .prompt-section {{ margin: 16px 0; padding-top: 16px; border-top: 1px dashed {BORDER}; }}
 .prompt-label {{ display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; font-family: 'Space Grotesk'; font-weight: 700; font-size: 14px; color: {TEXT}; }}
 .prompt-text {{ background: rgba(0,0,0,0.35); border: 1px solid {BORDER}; border-radius: 8px; padding: 14px 16px; font-family: 'SF Mono', Monaco, monospace; font-size: 12px; line-height: 1.55; color: {TEXT}; white-space: pre-wrap; word-wrap: break-word; max-height: 220px; overflow-y: auto; margin: 0; }}
 .copy-btn {{ padding: 6px 14px; background: {PRIMARY}; color: white; border: none; border-radius: 6px; font-family: 'Space Grotesk'; font-weight: 700; font-size: 12px; cursor: pointer; }}
 .copy-btn:hover {{ filter: brightness(1.15); }}
 .copy-btn.copied {{ background: {GREEN}; }}
 .paste-link {{ display: inline-block; margin-top: 10px; color: {PRIMARY}; text-decoration: none; font-size: 13px; font-family: 'Space Grotesk'; font-weight: 500; }}
 .paste-link:hover {{ text-decoration: underline; }}

 .vo-rendered, .vo-pending, .assembly-section {{ background: {CARD_BG}; border: 1px solid {BORDER}; border-radius: 14px; padding: 24px; margin-top: 24px; }}
 .vo-pending .cmd, .assembly-section .cmd {{ display: block; background: rgba(0,0,0,0.4); border: 1px solid {BORDER}; border-radius: 6px; padding: 10px 14px; font-family: monospace; font-size: 12px; color: {PRIMARY}; margin-top: 8px; overflow-x: auto; }}
 .assembly-section ol {{ margin: 12px 0 0; padding-left: 22px; line-height: 1.8; font-size: 14px; color: {TEXT}; }}
 .assembly-section code {{ background: rgba(0,0,0,0.3); padding: 2px 8px; border-radius: 4px; font-size: 12px; color: {PRIMARY}; }}

 .muted {{ color: {MUTED}; }}
 .toast {{ position: fixed; top: 20px; right: 20px; background: {GREEN}; color: white; padding: 12px 20px; border-radius: 8px; font-family: 'Space Grotesk'; font-weight: 700; font-size: 14px; opacity: 0; transition: opacity 0.2s; pointer-events: none; }}
 .toast.show {{ opacity: 1; }}

 .step-banner {{ background: rgba(59,158,255,0.06); border: 1px solid rgba(59,158,255,0.25); border-left: 4px solid {PRIMARY}; border-radius: 8px; padding: 16px 20px; margin: 24px 0; }}
 .step-banner h3 {{ margin: 0 0 8px; font-family: 'Space Grotesk'; font-size: 13px; text-transform: uppercase; letter-spacing: 1.5px; color: {PRIMARY}; }}
 .step-banner ol {{ margin: 0; padding-left: 22px; line-height: 1.8; font-size: 14px; }}
</style>
</head><body>

<div class="toast" id="toast">Copied</div>

<div class="wrap">
  <header>
    <div>
      <h1>REEL PACKET</h1>
      <div class="meta">{html.escape(entry_id)} · {html.escape(str(duration))} sec · {len(scenes)} scenes · {html.escape(fm.get('pillar', ''))}</div>
    </div>
  </header>

  <div class="step-banner">
    <h3>🎯 Your workflow</h3>
    <ol>
      <li>Per scene: copy Nano Banana Pro prompt + upload the recommended face-NN.jpg → paste in Gemini → download generated image</li>
      <li>Per scene: copy Veo 3.1 prompt + upload the Nano Banana image as starting frame → paste in Google Flow → download MP4</li>
      <li>Save scene MP4s to <code>brand/queue/assets/{html.escape(entry_id)}/scene-1.mp4</code> … <code>scene-{len(scenes)}.mp4</code></li>
      <li>Voiceover auto-renders via F5-TTS (see below). Otherwise paste VO script into ElevenLabs.</li>
      <li>Run <code>assemble_reel.py</code> to stitch. Final MP4 lands in the queue for review.</li>
    </ol>
  </div>

  <h2>Caption (for IG composer)</h2>
  <div class="caption-box">
    <pre id="caption">{html.escape(caption)}</pre>
    <button class="copy-btn" style="margin-top:12px" onclick="copyPrompt('caption')">📋 Copy caption</button>
  </div>

  <h2>Scene-by-scene prompts</h2>
  {"".join(scene_cards)}

  <h2>Voiceover</h2>
  {voiceover_html}

  <h2>Final assembly</h2>
  {assembly_html}
</div>

<script>
function copyPrompt(id) {{
  const el = document.getElementById(id);
  const text = el.textContent;
  navigator.clipboard.writeText(text).then(() => {{
    showToast('Copied: ' + text.slice(0, 40) + '...');
    // Find the button that triggered + flash it
    if (event && event.target) {{
      event.target.classList.add('copied');
      const oldText = event.target.textContent;
      event.target.textContent = '✓ Copied';
      setTimeout(() => {{
        event.target.classList.remove('copied');
        event.target.textContent = oldText;
      }}, 1400);
    }}
  }}).catch(e => alert('Copy failed: ' + e.message));
}}
function showToast(msg) {{
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 1400);
}}
</script>
</body></html>"""


# ── Voice rendering integration ────────────────────────────────────────────

def try_render_voiceover(brand: Path, draft_path: Path, vo_script: str,
                         out_path: Path) -> Path | None:
    """Try to call clone_voice.py. Returns out_path if success, None if F5-TTS missing."""
    try:
        importlib_check = subprocess.run(
            [sys.executable, "-c", "import f5_tts"],
            capture_output=True, timeout=10,
        )
        if importlib_check.returncode != 0:
            print("  F5-TTS not yet installed → skipping voiceover render. Pending pip install.")
            return None
    except Exception:
        return None

    out_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        subprocess.run([
            sys.executable,
            str(Path(__file__).parent / "clone_voice.py"),
            "--text", vo_script,
            "--out", str(out_path),
        ], check=True, timeout=300)
        return out_path if out_path.exists() else None
    except Exception as e:
        print(f"  clone_voice.py failed: {e}", file=sys.stderr)
        return None


# ── CLI ────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--draft", required=True, type=Path)
    ap.add_argument("--brand-folder", type=Path, default=DEFAULT_BRAND)
    ap.add_argument("--no-open", action="store_true")
    ap.add_argument("--skip-vo", action="store_true",
                    help="Don't auto-render voiceover even if F5-TTS is available.")
    args = ap.parse_args()

    if not args.draft.exists():
        sys.exit(f"Draft not found: {args.draft}")

    fm, body = read_md(args.draft)
    if fm.get("format", "").lower() != "reel":
        print(f"⚠ Draft format is '{fm.get('format')}', not 'reel'. Continuing anyway.")

    scenes = parse_scenes(body)
    if not scenes:
        sys.exit("No scenes parsed. Draft must have a '## Scene breakdown' section with '### Scene N' blocks.")
    caption = parse_caption(body)
    vo_script = parse_vo_script(body)
    face = parse_face_lock(args.brand_folder)
    if not face["character_block"]:
        print("⚠ brand/face-lock.md missing or no CHARACTER LOCK BLOCK. Image prompts will be incomplete.")

    entry_id = fm.get("entry_id", "unknown")
    assets_dir = args.brand_folder / "brand" / "queue" / "assets" / entry_id
    voiceover_path = assets_dir / "voiceover.mp3"

    # Try rendering VO unless skipped
    if not args.skip_vo and vo_script and not voiceover_path.exists():
        print("Attempting to auto-render voiceover via F5-TTS...")
        rendered = try_render_voiceover(args.brand_folder, args.draft, vo_script, voiceover_path)
        if rendered:
            print(f"✓ Voiceover saved: {rendered}")
        else:
            voiceover_path = None
    elif voiceover_path.exists():
        print(f"  Existing voiceover found: {voiceover_path}")
    else:
        voiceover_path = None

    # Render packet
    out_path = Path(f"/tmp/reel-packet-{entry_id}.html")
    out_path.write_text(
        render_packet(args.draft, fm, body, args.brand_folder,
                      scenes, face, vo_script, caption, voiceover_path),
        encoding="utf-8",
    )
    print(f"\n✓ Reel packet written: {out_path}")
    print(f"  {len(scenes)} scenes, caption + VO + reference photos + ready-to-paste prompts")

    if not args.no_open:
        subprocess.run(["open", str(out_path)], check=False)

    # Notify
    subprocess.run(["osascript", "-e",
                    f'display notification "Reel packet ready · {len(scenes)} scenes" '
                    f'with title "TOW Reel pipeline" sound name "Glass"'],
                   capture_output=True, timeout=5)


if __name__ == "__main__":
    main()
