#!/usr/bin/env python3
"""
Generate a paste-ready visual brief from a source draft.

Reads a source file (usually from brand/queue/pending-approval/) and the target
format, produces a structured markdown brief that the user pastes into Claude
Design or uses to prompt Hyperframes. Brief includes engine selection,
brand context reminder, source content extracted per format, animation direction
where relevant, and render format guidance.

Usage:
  python3 generate_brief.py <source_file> --target carousel
  python3 generate_brief.py <source_file> --target quote-card
  python3 generate_brief.py <source_file> --target reel-script
  python3 generate_brief.py <source_file> --target animated-graphic

Exit codes:
  0 = brief written to brand/queue/briefs/
  1 = source file missing or malformed frontmatter
"""

import argparse
import re
import sys
from datetime import date, datetime, timezone
from pathlib import Path


SUPPORTED_TARGETS = {
    "carousel": {
        "engine": "Claude Design",
        "aspect": "4:5 portrait (1080x1350)",
        "slides": "7-10",
        "caption_chars": "150-300",
        "render_output": "PNG sequence via handoff to Claude Code",
        "animated": False,
    },
    "quote-card": {
        "engine": "Claude Design",
        "aspect": "1:1 square (1080x1080)",
        "slides": "1",
        "caption_chars": "100-200",
        "render_output": "Single PNG via handoff to Claude Code",
        "animated": False,
    },
    "animated-graphic": {
        "engine": "Claude Design",
        "aspect": "9:16 vertical (1080x1920) or 1:1 square (1080x1080)",
        "duration_sec": "10-20",
        "render_output": "MP4 via handoff to Claude Code (HTML with CSS anim → browser → ffmpeg)",
        "animated": True,
    },
    "reel-script": {
        "engine": "Hyperframes",
        "aspect": "9:16 vertical (1080x1920)",
        "duration_sec": "30-90",
        "render_output": "MP4 via Hyperframes render command (HTML → browser → ffmpeg)",
        "animated": True,
    },
    "story": {
        "engine": "Claude Design",
        "aspect": "9:16 vertical (1080x1920)",
        "slides": "1-5",
        "render_output": "PNG per slide via handoff to Claude Code",
        "animated": False,
    },
}


BRAND_BLOCK = """## Brand context (Digischola)

Use the Digischola brand memory. Core specs:
- Background: #000000 (dark mode only for Digischola)
- Primary accent: #3B9EFF (CTAs, metric callouts, hooks)
- Success green: #4ADE80 (positive metric numbers only; use sparingly)
- Text: #F8FAFC (primary) / #9BA8B9 (muted support only)
- Fonts: Orbitron Bold (display / hero text), Space Grotesk SemiBold (headings / CTAs UPPERCASE), Manrope Regular (body)
- Logo: DIGISCHOLA with SCHOLA in #3B9EFF on dark
- Aesthetic: tech-forward dark mode, operator-style, performance-credibility

Never use:
- Em dashes in any rendered text
- Hype words (unlock, revolutionize, game-changer)
- Engagement bait (Comment YES, Follow for more)
- Manrope for headings (body only)
- Lowercase CTAs

Never render these in any visible slide chrome (they are internal metadata only, audience must not see them):
- entry_id values (e.g., `iskm-ry25`, `thrive-ep3`, any short slug ID)
- source-id values, UUIDs, or any alphanumeric ID-looking strings
- `SRC`, `SRC_ID`, `END`, or similar internal labels
- Page-header chrome that exposes source identifiers

Acceptable chrome replacements if you need a label: category tags like "CASE STUDY", "PLAYBOOK", year markers like "2025", or the handle "@DIGISCHOLA".
"""


def parse_frontmatter(text: str):
    meta, body = {}, text
    if text.startswith("---\n"):
        parts = text.split("---\n", 2)
        if len(parts) >= 3:
            for line in parts[1].splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    meta[k.strip()] = v.strip()
            body = parts[2]
    return meta, body.strip()


def split_carousel_slides(body: str):
    """If the source is already a carousel spec with '## Slide N' headers, split accordingly.
    Otherwise return the whole body as a single paragraph that the engine must divide."""
    parts = re.split(r"^##\s+Slide\s+\d+[^\n]*\n", body, flags=re.MULTILINE)
    if len(parts) > 1:
        # pre-slide content + per-slide content
        return [p.strip() for p in parts if p.strip()]
    return None


def split_thread_tweets(body: str):
    parts = re.split(r"^##\s+Tweet\s+\d+[^\n]*\n", body, flags=re.MULTILINE)
    if len(parts) > 1:
        return [p.strip() for p in parts if p.strip()]
    return None


def extract_hook(body: str) -> str:
    lines = [l for l in body.splitlines() if l.strip()]
    return "\n".join(lines[:2]) if lines else ""


def render_carousel_brief(meta, body, entry_id, source_path: Path):
    slides = split_carousel_slides(body)
    tweets = split_thread_tweets(body) if slides is None else None

    lines = []
    lines.append(f"# Visual Brief: {entry_id} → IG Carousel")
    lines.append("")
    lines.append("## Engine")
    lines.append(f"Claude Design at claude.ai/design. Paste this entire brief into a new project. "
                 f"Iterate until satisfied, then hand off to Claude Code for render.")
    lines.append("")
    lines.append(BRAND_BLOCK)
    lines.append("## Target format")
    lines.append("- Aspect: 4:5 portrait (1080x1350 per slide)")
    lines.append("- Slide count: 7-10 total")
    lines.append("- First slide: large hook text (Orbitron, 40-60pt)")
    lines.append("- Numbered slide markers on slides 2+ (e.g., '1/8' top corner)")
    lines.append("- Each body slide: 20-40 words max")
    lines.append("- Last slide: soft close + CTA hint")
    lines.append("- Caption (posted with carousel): 150-300 chars")
    lines.append("")
    lines.append("## Source content")
    lines.append("")
    if slides:
        lines.append("Slides pre-structured in source. Use as-is:")
        lines.append("")
        for i, s in enumerate(slides, 1):
            lines.append(f"### Input Slide {i}")
            lines.append(s)
            lines.append("")
    else:
        lines.append("Source is a long-form post. Structure it into 7-10 slides:")
        lines.append("- Slide 1: the hook from the source (first 1-2 lines)")
        lines.append("- Slides 2-3: context / setup")
        lines.append("- Slides 4-N: one body point each")
        lines.append("- Last slide: the source's close / question")
        lines.append("")
        lines.append("### Source body")
        lines.append(body)
        lines.append("")
    lines.append("## Visual treatment per slide type")
    lines.append("- Hook slide: large Orbitron, blue accent on key number (e.g., '188%' in #3B9EFF or Success green #4ADE80)")
    lines.append("- Metric slide: one big number, Orbitron, centered, minimal supporting text")
    lines.append("- List slide: numbered item, Space Grotesk heading + Manrope body, ample whitespace")
    lines.append("- Close slide: question or observation, Space Grotesk, soft CTA")
    lines.append("")
    lines.append("## Render format")
    lines.append("After iterating in Claude Design, hand off to Claude Code to render each slide as PNG (1080x1350).")
    lines.append("Save output to: `brand/queue/assets/<source-id>/slide-N.png`")
    lines.append("")
    return "\n".join(lines) + "\n"


def render_quote_card_brief(meta, body, entry_id, source_path: Path):
    hook = extract_hook(body)
    lines = []
    lines.append(f"# Visual Brief: {entry_id} → Quote Card")
    lines.append("")
    lines.append("## Engine")
    lines.append("Claude Design at claude.ai/design.")
    lines.append("")
    lines.append(BRAND_BLOCK)
    lines.append("## Target format")
    lines.append("- Aspect: 1:1 square (1080x1080)")
    lines.append("- Single PNG output")
    lines.append("- Composition: large quote text (Space Grotesk SemiBold, 32-48pt) centered")
    lines.append("- Attribution: Mayank Verma / Digischola (Manrope, 16-20pt, bottom right)")
    lines.append("- Dark background (#000000 or the Hero gradient)")
    lines.append("- Subtle Primary Blue (#3B9EFF) accent element (underline, corner mark, or dot)")
    lines.append("- Logo wordmark (DIGISCHOLA with SCHOLA in blue) small in one corner")
    lines.append("")
    lines.append("## Quote")
    lines.append(f"> {hook}")
    lines.append("")
    lines.append("## Attribution")
    lines.append("Mayank Verma · Digischola")
    lines.append("")
    lines.append("## Render format")
    lines.append("Hand off to Claude Code. Output single PNG (1080x1080) to `brand/queue/assets/<source-id>/quote.png`.")
    lines.append("")
    return "\n".join(lines) + "\n"


def render_reel_brief(meta, body, entry_id, source_path: Path):
    tweets = split_thread_tweets(body)
    lines = []
    lines.append(f"# Visual Brief: {entry_id} → Reel (Hyperframes)")
    lines.append("")
    lines.append("## Engine")
    lines.append("Hyperframes at `/Users/digischola/Desktop/Digischola/brand/_engine/hyperframes-scenes/`.")
    lines.append("Use the built-in 'make a video' skill. Start Claude Code inside hyperframes-scenes. Paste this brief as input.")
    lines.append("")
    lines.append(BRAND_BLOCK)
    lines.append("## Target format")
    lines.append("- Aspect: 9:16 vertical (1080x1920)")
    lines.append("- Duration: 30-60 seconds (aim for 45 sec default)")
    lines.append("- Frame rate: 30fps")
    lines.append("- Audio: instrumental background (free royalty-free track); voiceover optional v2")
    lines.append("- No face cam in v1 (transcription deferred; use written script + animated graphics only)")
    lines.append("")
    lines.append("## Reel structure (hook-body-close)")
    lines.append("")
    lines.append("**Hook (0-3 sec):** source's first line, displayed as overlay text. Big, blue, center. Jump cut into the first body beat.")
    lines.append("")
    lines.append("**Body beats (3-40 sec):** one point every 5-8 sec. Jump cuts between beats (per 2026 IG Reel best practice: cuts every 3-5 sec for +32% engagement). Visual treatment per beat:")
    lines.append("- Metric beats: big number callout (Orbitron, #3B9EFF or #4ADE80), supporting caption below")
    lines.append("- Insight beats: Space Grotesk heading + Manrope body text, centered")
    lines.append("- Transition beats: Primary Blue gradient reveal, logo wordmark")
    lines.append("")
    lines.append("**Close (last 5 sec):** soft question or insight on screen. Loop cue at the end (text like 'worth re-watching?').")
    lines.append("")
    lines.append("## Source content")
    lines.append("")
    if tweets:
        lines.append("Source is already thread-structured. Use each tweet as a beat:")
        lines.append("")
        for i, t in enumerate(tweets, 1):
            lines.append(f"### Beat {i}")
            lines.append(t)
            lines.append("")
    else:
        lines.append("### Source body")
        lines.append(body)
        lines.append("")
        lines.append("Split this into 5-7 beats. First beat = source hook. Last beat = source close.")
        lines.append("")
    lines.append("## Animation direction")
    lines.append("- Tempo: punchy, jump cuts every 3-5 seconds")
    lines.append("- Entrance animations: fade + slide-up for text blocks")
    lines.append("- Exit animations: fade + scale for metric callouts")
    lines.append("- Global: subtle grain or noise overlay for tech-forward feel")
    lines.append("- Logo: appears in first 3 sec + last 3 sec, small top-left")
    lines.append("")
    lines.append("## Render format")
    lines.append("MP4, H.264 + AAC, 1080x1920, 30fps, ~5-10 MB target file size (Reel-compatible).")
    lines.append("Save output to `brand/queue/assets/<source-id>/reel.mp4`.")
    lines.append("")
    lines.append("## After render")
    lines.append("Run `scripts/import_assets.py <reel.mp4> --source-id <id>` to catalog into queue.")
    lines.append("")
    return "\n".join(lines) + "\n"


def render_animated_graphic_brief(meta, body, entry_id, source_path: Path):
    hook = extract_hook(body)
    lines = []
    lines.append(f"# Visual Brief: {entry_id} → Animated Graphic")
    lines.append("")
    lines.append("## Engine")
    lines.append("Claude Design at claude.ai/design. Paste brief, iterate, hand off to Claude Code.")
    lines.append("")
    lines.append(BRAND_BLOCK)
    lines.append("## Target format")
    lines.append("- Aspect: 9:16 vertical (for Stories / Reels thumbnail) OR 1:1 square")
    lines.append("- Duration: 10-20 seconds")
    lines.append("- Loop-friendly (seamless end → start)")
    lines.append("- HTML output with CSS animations; no face cam")
    lines.append("")
    lines.append("## Source / hook")
    lines.append(f"> {hook}")
    lines.append("")
    lines.append("## Animation direction")
    lines.append("- Hook appears in first 1.5 sec (big, center, blue accent)")
    lines.append("- Supporting lines fade in one at a time, 2-sec each")
    lines.append("- Close with logo reveal + subtle gradient")
    lines.append("")
    lines.append("## Render format")
    lines.append("MP4 via handoff to Claude Code. Save output to `brand/queue/assets/<source-id>/animated.mp4`.")
    lines.append("")
    return "\n".join(lines) + "\n"


def render_story_brief(meta, body, entry_id, source_path: Path):
    hook = extract_hook(body)
    lines = []
    lines.append(f"# Visual Brief: {entry_id} → Instagram Story")
    lines.append("")
    lines.append("## Engine")
    lines.append("Claude Design.")
    lines.append("")
    lines.append(BRAND_BLOCK)
    lines.append("## Target format")
    lines.append("- Aspect: 9:16 (1080x1920)")
    lines.append("- 1-5 slides; 7 seconds per slide")
    lines.append("- Single-message focus per slide")
    lines.append("")
    lines.append("## Source")
    lines.append(f"> {hook}")
    lines.append("")
    lines.append("## Render format")
    lines.append("PNG per slide. Save to `brand/queue/assets/<source-id>/story-N.png`.")
    lines.append("")
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source_file", type=Path)
    ap.add_argument("--target", required=True, choices=sorted(SUPPORTED_TARGETS.keys()),
                    help="Target visual format")
    ap.add_argument("--brand-folder", type=Path,
                    default=Path("/Users/digischola/Desktop/Digischola"))
    args = ap.parse_args()

    if not args.source_file.exists():
        sys.exit(f"Source file not found: {args.source_file}")

    text = args.source_file.read_text(errors="replace")
    meta, body = parse_frontmatter(text)

    entry_id = meta.get("entry_id", args.source_file.stem)
    entry_short = entry_id[:8] if len(entry_id) > 8 else entry_id

    if args.target == "carousel":
        brief = render_carousel_brief(meta, body, entry_short, args.source_file)
    elif args.target == "quote-card":
        brief = render_quote_card_brief(meta, body, entry_short, args.source_file)
    elif args.target == "reel-script":
        brief = render_reel_brief(meta, body, entry_short, args.source_file)
    elif args.target == "animated-graphic":
        brief = render_animated_graphic_brief(meta, body, entry_short, args.source_file)
    elif args.target == "story":
        brief = render_story_brief(meta, body, entry_short, args.source_file)
    else:
        sys.exit(f"Unsupported target: {args.target}")

    briefs_dir = args.brand_folder / "brand" / "queue" / "briefs"
    briefs_dir.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()
    brief_path = briefs_dir / f"{today}-{entry_short}-{args.target}-brief.md"
    brief_path.write_text(brief)

    # Front-matter prefix for downstream tooling
    fm_lines = [
        "---",
        f"source_file: {args.source_file}",
        f"source_channel: {meta.get('channel', 'unknown')}",
        f"source_format: {meta.get('format', 'unknown')}",
        f"target_engine: {SUPPORTED_TARGETS[args.target]['engine']}",
        f"target_format: {args.target}",
        f"entry_id: {meta.get('entry_id', 'unknown')}",
        f"pillar: {meta.get('pillar', 'unknown')}",
        f"generated_at: {datetime.now(timezone.utc).isoformat()}",
        "---",
        "",
    ]
    brief_path.write_text("\n".join(fm_lines) + brief)

    print(f"Brief written: {brief_path}")
    print(f"  target: {args.target}")
    print(f"  engine: {SUPPORTED_TARGETS[args.target]['engine']}")
    print(f"  source: {args.source_file.name}")
    print()
    print("Next steps:")
    spec = SUPPORTED_TARGETS[args.target]
    if spec["engine"] == "Claude Design":
        print(f"  1. Open claude.ai/design, paste the brief body into a new project.")
        print(f"  2. Iterate, then 'Hand off to Claude Code' for the render command.")
        print(f"  3. Run that command in Claude Code to render HTML → {spec['render_output']}.")
        print(f"  4. Run import_assets.py to catalog the output into queue.")
    else:  # Hyperframes
        print(f"  1. cd into /Users/digischola/Desktop/Digischola/brand/_engine/hyperframes-scenes/")
        print(f"  2. Start Claude Code there. Invoke 'make a video' skill with this brief.")
        print(f"  3. Iterate on localhost preview. Approve and render to MP4.")
        print(f"  4. Run import_assets.py on the output MP4 to catalog into queue.")


if __name__ == "__main__":
    main()
