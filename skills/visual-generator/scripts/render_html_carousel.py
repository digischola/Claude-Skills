#!/usr/bin/env python3
"""
Render a Claude Design carousel HTML export into per-slide PNG files.

Reads brand/queue/assets/<source-id>/source.html (the Claude Design handoff
HTML containing N <section class="slide"> elements), extracts each slide,
builds a standalone HTML per slide at native 1080x1350 (CSS overrides to
disable preview scaling, tweaks panel, and page header), then invokes
Chrome headless to screenshot each slide at full brand-size.

Usage:
  python3 render_html_carousel.py --source-id iskm-ry25
  python3 render_html_carousel.py --source-id iskm-ry25 --width 1080 --height 1350
  python3 render_html_carousel.py --source-id my-id --font-wait-ms 4000

Output: brand/queue/assets/<source-id>/slide-1.png ... slide-N.png

Requires Chrome installed. Defaults to macOS path; override with --chrome.
"""

import argparse
import re
import subprocess
import sys
import tempfile
from pathlib import Path

# Shared notify helper with click-through (terminal-notifier under the hood)
# Path is relative to this file: visual-generator/scripts/ → skills/ → shared-scripts/
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "shared-scripts"))
try:
    from notify import notify as _notify, notify_reviewable_artifact  # type: ignore
except ImportError:
    _notify = None
    notify_reviewable_artifact = None

CHROME_DEFAULT_MAC = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

# CSS overrides that neutralize preview-only styling + hide tweaks panel + page header
OVERRIDE_CSS = """
<style id="render-overrides">
  html, body { margin: 0 !important; padding: 0 !important; background: #0a0a0a; overflow: hidden; }
  .carousel {
    display: block !important;
    grid-template-columns: none !important;
    gap: 0 !important;
    max-width: none !important;
    margin: 0 !important;
  }
  .slide {
    transform: none !important;
    margin: 0 !important;
    width: 1080px !important;
    height: 1350px !important;
    display: block !important;
  }
  .page-header, #tweaks { display: none !important; }
</style>
"""

# Replace the inline <script> that does window.parent.postMessage (breaks in headless)
SCRIPT_NEUTRALIZE = "<script>/* neutralized for headless render */</script>"


def extract_head(text: str) -> str:
    m = re.search(r"<head>(.*?)</head>", text, re.DOTALL)
    return m.group(1) if m else ""


def extract_slides(text: str):
    return re.findall(
        r'(<section class="slide[^"]*"\s+data-screen-label="slide-\d+"[^>]*>.*?</section>)',
        text, re.DOTALL,
    )


def build_slide_html(head: str, slide_section: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
{head}
{OVERRIDE_CSS}
</head>
<body>
<div class="carousel">
{slide_section}
</div>
{SCRIPT_NEUTRALIZE}
</body>
</html>
"""


def render_slide(chrome_path: str, html_path: Path, png_path: Path,
                 width: int, height: int, font_wait_ms: int,
                 timeout: int = 60) -> bool:
    cmd = [
        chrome_path,
        "--headless=new",
        "--disable-gpu",
        "--hide-scrollbars",
        "--no-sandbox",
        f"--screenshot={png_path}",
        f"--window-size={width},{height}",
        "--default-background-color=00000000",
        f"--virtual-time-budget={font_wait_ms}",
        f"file://{html_path}",
    ]
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=timeout, text=True)
    except subprocess.TimeoutExpired:
        print(f"  TIMEOUT rendering {png_path.name}", file=sys.stderr)
        return False
    if png_path.exists() and png_path.stat().st_size > 0:
        return True
    print(f"  FAILED rendering {png_path.name}", file=sys.stderr)
    print("  stderr tail:", (r.stderr or "")[-300:], file=sys.stderr)
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--brand-folder", type=Path,
                    default=Path("/Users/digischola/Desktop/Digischola"))
    ap.add_argument("--source-id", required=True,
                    help="Source id whose assets folder contains source.html")
    ap.add_argument("--source-html", type=Path, default=None,
                    help="Override path to the HTML to render (defaults to <brand>/brand/queue/assets/<source-id>/source.html)")
    ap.add_argument("--width", type=int, default=1080)
    ap.add_argument("--height", type=int, default=1350)
    ap.add_argument("--font-wait-ms", type=int, default=3000,
                    help="virtual-time-budget for Chrome to load Google Fonts before screenshot")
    ap.add_argument("--chrome", default=CHROME_DEFAULT_MAC)
    args = ap.parse_args()

    out_dir = args.brand_folder / "brand" / "queue" / "assets" / args.source_id
    if not out_dir.exists():
        sys.exit(f"Assets folder not found: {out_dir}")

    src = args.source_html or (out_dir / "source.html")
    if not src.exists():
        sys.exit(f"Source HTML not found: {src}. Did you drop the Claude Design export there?")

    text = src.read_text(errors="replace")
    head = extract_head(text)
    slides = extract_slides(text)
    if not slides:
        sys.exit("No <section class=\"slide\" data-screen-label=\"slide-N\"> elements found.")
    print(f"Found {len(slides)} slide section(s).")

    if not Path(args.chrome).exists():
        sys.exit(f"Chrome not found at {args.chrome}. Pass --chrome <path>.")

    with tempfile.TemporaryDirectory(prefix="render_carousel_") as td:
        tmp = Path(td)
        fails = 0
        for i, slide in enumerate(slides, 1):
            slide_html = build_slide_html(head, slide)
            slide_html_path = tmp / f"slide-{i}.html"
            slide_html_path.write_text(slide_html)
            png_path = out_dir / f"slide-{i}.png"
            print(f"Rendering slide {i}... ", end="", flush=True)
            ok = render_slide(args.chrome, slide_html_path, png_path,
                              args.width, args.height, args.font_wait_ms)
            if ok:
                print(f"OK  ({png_path.stat().st_size} bytes)")
            else:
                fails += 1

    if fails:
        print(f"\n{fails} slide(s) failed. See stderr above.", file=sys.stderr)
        if _notify is not None:
            _notify(
                f"Carousel render FAILED: {out_dir.name}",
                f"{fails} of {len(slides)} slides failed. Check stderr for details.",
                subtitle="Digischola", sound="Basso",
                group="digischola-render",
            )
        sys.exit(1)
    print(f"\nAll {len(slides)} slides rendered to {out_dir}")

    # Click-to-open notification (patched 2026-04-22 batch per notification-UX
    # backlog item #7): instead of a standalone preview.html that doesn't
    # support Approve/Edit/Reject, land the user in review_queue.py on the
    # specific draft's card. review_queue is started in background if it
    # isn't already running.
    try:
        if notify_reviewable_artifact is not None:
            notify_reviewable_artifact(
                title=f"Carousel rendered: {out_dir.name}",
                body=f"{len(slides)} slides ready for review.",
                entry_id=args.source_id,
                brand_folder=args.brand_folder,
                subtitle="Digischola",
                sound="Glass",
                visual_only=True,
            )
        elif _notify is not None:
            # Fallback: notify without anchor
            _notify(
                f"Carousel rendered: {out_dir.name}",
                f"{len(slides)} slides. Open review UI to approve.",
                subtitle="Digischola", sound="Glass",
                open_url="http://127.0.0.1:8765/",
                group="digischola-render",
            )
    except Exception as e:
        # Never let a notify-failure break the render output
        print(f"  (notification failed: {e})", file=sys.stderr)


if __name__ == "__main__":
    main()
