#!/usr/bin/env python3
"""
Render a Claude Design animated-graphic HTML export into an MP4 video.

Flow:
  1. Read brand/queue/assets/<source-id>/source.html (the Claude Design handoff
     HTML containing CSS keyframe animation at the target aspect).
  2. Open it in Playwright headless Chromium at the requested viewport
     (default 1080x1920 for 9:16 Reels/Stories, or 1080x1080 for square).
  3. Record video for --duration-sec seconds.
  4. Playwright writes a WebM. Use ffmpeg to remux to MP4 (H.264 + AAC silent
     track) — MP4 is what IG / LI / FB / X want natively.

Usage:
  python3 render_html_mp4.py --source-id thrive-ep3 --duration-sec 15
  python3 render_html_mp4.py --source-id thrive-ep3 --aspect 1:1 --duration-sec 10
  python3 render_html_mp4.py --source-id some-id --source-html path/to/anim.html

Requires:
  - Playwright Python (pip install playwright) + chromium (playwright install chromium)
  - ffmpeg on PATH (brew install ffmpeg)

Output: brand/queue/assets/<source-id>/animated.mp4
"""

import argparse
import http.server
import shutil
import socket
import socketserver
import subprocess
import sys
import threading
from pathlib import Path

# Shared notify helper (click-through)
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "shared-scripts"))
try:
    from notify import notify as _notify, notify_reviewable_artifact  # type: ignore
except ImportError:
    _notify = None
    notify_reviewable_artifact = None

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sys.exit("Playwright not installed. Run: pip3 install playwright && python3 -m playwright install chromium")


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a, **kw):
        pass  # silence stdout


def _start_local_server(serve_dir: Path):
    """Start a threaded HTTP server rooted at serve_dir. Returns (httpd, port)."""
    port = _free_port()

    class Handler(_QuietHandler):
        def __init__(self, *a, **kw):
            super().__init__(*a, directory=str(serve_dir), **kw)

    httpd = socketserver.ThreadingTCPServer(("127.0.0.1", port), Handler)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    return httpd, port


ASPECTS = {
    "9:16": (1080, 1920),
    "1:1":  (1080, 1080),
    "4:5":  (1080, 1350),
    "16:9": (1920, 1080),
}


def record_webm(source_html: Path, webm_dir: Path, width: int, height: int,
                duration_ms: int, font_wait_ms: int = 1500,
                via_http: bool = True, verbose: bool = False) -> Path:
    """Open the HTML in headless Chromium, record for duration_ms, return the WebM path.

    via_http=True serves source_html's parent directory over a local HTTP server and
    navigates via http://127.0.0.1:PORT/<filename>. This is REQUIRED for any HTML that
    uses Babel Standalone (`<script type="text/babel" src="...">`) because Chromium
    blocks `fetch()` from `file://` origin, which breaks Babel's loader.
    """
    webm_dir.mkdir(parents=True, exist_ok=True)
    httpd = None
    try:
        if via_http:
            httpd, port = _start_local_server(source_html.parent)
            nav_url = f"http://127.0.0.1:{port}/{source_html.name}"
        else:
            nav_url = f"file://{source_html.resolve()}"
        if verbose:
            print(f"  nav: {nav_url}")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={"width": width, "height": height},
                record_video_dir=str(webm_dir),
                record_video_size={"width": width, "height": height},
                device_scale_factor=1,
            )
            page = context.new_page()

            if verbose:
                page.on("pageerror", lambda err: print(f"  [pageerror] {err}", file=sys.stderr))
                page.on("console", lambda msg: print(f"  [console.{msg.type}] {msg.text}", file=sys.stderr)
                        if msg.type in ("error", "warning") else None)

            page.goto(nav_url)
            # give Google Fonts + Babel transpile + React mount time to kick off
            page.wait_for_timeout(font_wait_ms)
            # then record for the requested duration
            page.wait_for_timeout(duration_ms)
            page.close()
            context.close()
            browser.close()
    finally:
        if httpd:
            httpd.shutdown()

    # Playwright names the file with a random hash. Take the newest .webm.
    webms = sorted(webm_dir.glob("*.webm"), key=lambda p: p.stat().st_mtime)
    if not webms:
        sys.exit("Playwright did not produce a WebM. Check the HTML loads in a browser.")
    return webms[-1]


def encode_mp4(webm: Path, mp4: Path, ffmpeg: str = "ffmpeg",
               skip_sec: float = 0.0, duration_sec: float = None) -> bool:
    """Remux WebM → MP4 (H.264 yuv420p + silent AAC track) for IG/LI compatibility.

    anullsrc is an infinite silent stream; `-shortest` makes the output end when
    the video input ends (NOT the audio). Do NOT pass `-t 0.1` to anullsrc —
    that would cap the output at 0.1s.

    skip_sec: trim leading N seconds of the WebM from the MP4 output. Used to
    drop the React/Babel warm-up period so the user sees the animation from frame 1.
    duration_sec: if provided, cap output to this many seconds.
    """
    cmd = [ffmpeg, "-y"]
    if skip_sec > 0:
        cmd += ["-ss", str(skip_sec)]
    cmd += ["-i", str(webm)]
    if duration_sec:
        cmd += ["-t", str(duration_sec)]
    cmd += [
        "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
        "-shortest",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-profile:v", "main",
        "-level", "4.0",
        "-movflags", "+faststart",
        "-crf", "20",
        "-c:a", "aac",
        "-b:a", "128k",
        str(mp4),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print("ffmpeg stderr tail:", r.stderr[-600:], file=sys.stderr)
        return False
    if not mp4.exists() or mp4.stat().st_size < 1024:
        return False
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--brand-folder", type=Path,
                    default=Path("/Users/digischola/Desktop/Digischola"))
    ap.add_argument("--source-id", required=True,
                    help="Source id whose assets folder contains source.html")
    ap.add_argument("--source-html", type=Path, default=None,
                    help="Override path to the HTML to render (defaults to <brand>/brand/queue/assets/<source-id>/source.html)")
    ap.add_argument("--aspect", choices=sorted(ASPECTS.keys()), default="9:16",
                    help="Output aspect ratio (9:16 for Reels/Stories, 1:1 for square)")
    ap.add_argument("--duration-sec", type=float, default=15.0,
                    help="Recording duration in seconds")
    ap.add_argument("--font-wait-ms", type=int, default=1500,
                    help="Pre-recording wait for Google Fonts + Babel transpile + React mount to finish")
    ap.add_argument("--output-name", default="animated.mp4",
                    help="Output filename inside the assets folder")
    ap.add_argument("--ffmpeg", default="ffmpeg")
    ap.add_argument("--no-http", action="store_true",
                    help="Use file:// instead of spinning up a local HTTP server (breaks Babel Standalone loaders)")
    ap.add_argument("--verbose", action="store_true",
                    help="Log page errors + console.error/warning from headless Chrome")
    args = ap.parse_args()

    assets_dir = args.brand_folder / "brand" / "queue" / "assets" / args.source_id
    if not assets_dir.exists():
        sys.exit(f"Assets folder not found: {assets_dir}")

    src = args.source_html or (assets_dir / "source.html")
    if not src.exists():
        sys.exit(f"Source HTML not found: {src}. Did you drop the Claude Design export there?")

    if not shutil.which(args.ffmpeg):
        sys.exit(f"ffmpeg not on PATH (looked for '{args.ffmpeg}'). Install: brew install ffmpeg")

    width, height = ASPECTS[args.aspect]
    duration_ms = int(args.duration_sec * 1000)

    # Record WebM into a temp subdir, then convert to MP4 at final path.
    webm_dir = assets_dir / "_webm_tmp"
    try:
        print(f"Recording {width}x{height} for {args.duration_sec}s from {src.name}...")
        webm = record_webm(src, webm_dir, width, height, duration_ms, args.font_wait_ms,
                           via_http=not args.no_http, verbose=args.verbose)
        print(f"  WebM: {webm.name} ({webm.stat().st_size} bytes)")

        mp4 = assets_dir / args.output_name
        print(f"Encoding MP4 → {mp4.name} (trimming {args.font_wait_ms}ms warm-up)...")
        skip_sec = args.font_wait_ms / 1000.0
        if not encode_mp4(webm, mp4, args.ffmpeg,
                          skip_sec=skip_sec, duration_sec=args.duration_sec):
            sys.exit("MP4 encode failed.")
        print(f"  MP4: {mp4.name} ({mp4.stat().st_size} bytes)")
    finally:
        # Clean up temp WebM directory
        if webm_dir.exists():
            shutil.rmtree(webm_dir, ignore_errors=True)

    print(f"\nDone. Output: {assets_dir / args.output_name}")

    # Click-to-open notification (2026-04-22 UX batch per backlog #3 + #7):
    # land the user in review_queue.py on this draft's card, not a
    # standalone preview. Fallback to plain banner if helper missing.
    try:
        output_path = assets_dir / args.output_name
        if notify_reviewable_artifact is not None:
            notify_reviewable_artifact(
                title=f"MP4 rendered: {assets_dir.name}",
                body=f"{args.duration_sec}s · {args.aspect} · Review + approve.",
                entry_id=args.source_id,
                brand_folder=args.brand_folder,
                subtitle="Digischola",
                sound="Glass",
                visual_only=True,
            )
        elif _notify is not None:
            _notify(
                f"MP4 rendered: {assets_dir.name}",
                f"{args.duration_sec}s · {args.aspect}. Click to open review UI.",
                subtitle="Digischola", sound="Glass",
                open_url="http://127.0.0.1:8765/",
                group="digischola-render",
            )
    except Exception as e:
        print(f"  (notification failed: {e})", file=sys.stderr)


if __name__ == "__main__":
    main()
