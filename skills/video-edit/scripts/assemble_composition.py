#!/usr/bin/env python3
"""
assemble_composition.py — turn a content-plan.json into a full HyperFrames index.html.

Usage:
  python3 assemble_composition.py <content-plan.json> <project-dir>

Reads:
  <content-plan.json> — the director's output (see references/content-plan-schema.md)
  project-dir/assets/source.mp4 (referenced by content-plan)
  project-dir/assets/transcript.json (optional — required if any caption-wordpop beat omits
                                      per-word start/end and wants auto-fill)

Writes:
  project-dir/index.html — the assembled composition, ready for `npx hyperframes lint + render`

No external deps. Python 3.9+ stdlib only.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any


# ---------------------------------------------------------------------------
# Brand token resolution
# ---------------------------------------------------------------------------

def color(brand: Dict[str, Any], name_or_hex: str) -> str:
    """Resolve 'primary' / 'success' etc. against brand palette, or pass hex through."""
    if not name_or_hex:
        return brand.get("fg", "#F8FAFC")
    if name_or_hex.startswith("#"):
        return name_or_hex
    return brand.get(name_or_hex, name_or_hex)


# ---------------------------------------------------------------------------
# Shared CSS — fonts + root + reusable utility classes
# ---------------------------------------------------------------------------

def head(plan: Dict[str, Any]) -> str:
    b = plan["brand"]
    w = plan["target_dims"]["width"]
    h = plan["target_dims"]["height"]
    dur = plan["duration_sec"]
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width={w}, height={h}" />
  <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
  <style>
    @import url("{b['fonts_import']}");
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    html, body {{
      margin: 0; width: {w}px; height: {h}px;
      overflow: hidden; background: {b['bg']}; color: {b['fg']};
    }}
    #root {{ position: relative; width: {w}px; height: {h}px; background: {b['bg']}; }}

    /* ---- hook card ---- */
    #hook {{
      position: absolute; inset: 0; z-index: 30;
      display: flex; flex-direction: column; justify-content: center; align-items: center;
      padding: 120px 80px; gap: 40px; text-align: center; background: {b['bg']};
    }}
    #hook .glow {{
      position: absolute; inset: -20%;
      background:
        radial-gradient(circle at 50% 40%, rgba(59,158,255,0.22), transparent 55%),
        radial-gradient(circle at 70% 80%, rgba(107,184,255,0.18), transparent 60%);
      filter: blur(44px); z-index: 0;
    }}
    #hook .content {{ position: relative; z-index: 1; display: flex; flex-direction: column; gap: 36px; align-items: center; }}
    #hook .main {{
      font-family: "{b['font_display']}", sans-serif; font-weight: 700; font-size: 120px;
      line-height: 1.02; letter-spacing: -0.02em; text-transform: uppercase;
      background: linear-gradient(135deg, {b['primary']} 0%, {b['primary_glow']} 100%);
      -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent;
      max-width: 920px;
    }}
    #hook .sub {{
      font-family: "{b['font_heading']}", sans-serif; font-weight: 600; font-size: 40px;
      letter-spacing: 0.14em; text-transform: uppercase; color: {b['muted']};
      max-width: 860px;
    }}

    /* ---- video stage ---- */
    .video-stage {{ position: absolute; inset: 0; z-index: 1; overflow: hidden; }}
    .video-stage video {{
      position: absolute; width: 100%; height: 100%;
      object-fit: cover; object-position: center center;
    }}
    .video-dim {{ position: absolute; inset: 0; background: #000; opacity: 0; pointer-events: none; }}

    /* ---- captions (phrase + wordpop share these base styles) ---- */
    .caption {{
      position: absolute; left: 0; right: 0;
      bottom: 420px; padding: 0 64px; text-align: center;
      display: flex; flex-wrap: wrap; justify-content: center; gap: 14px 20px;
      z-index: 12; overflow: visible; will-change: opacity, transform;
    }}
    .caption .w {{
      font-family: "{b['font_body']}", sans-serif; font-weight: 500; font-size: 58px;
      line-height: 1.12; color: {b['fg']}; text-shadow: 0 3px 20px rgba(0,0,0,0.85);
      display: inline-block; transform-origin: center center;
      will-change: transform, opacity, color;
    }}
    .caption .w.accent {{
      font-family: "{b['font_heading']}", sans-serif; font-weight: 700; color: {b['primary']};
      text-transform: uppercase; letter-spacing: 0.04em;
    }}
    .caption .w.metric {{
      font-family: "{b['font_display']}", sans-serif; font-weight: 700; color: {b['primary']};
    }}

    /* ---- B-roll: landing page (Safari chrome wrap) ---- */
    .broll-lp {{
      position: absolute; inset: 60px 40px 180px; overflow: hidden;
      border-radius: 22px; z-index: 14; background: #F5F7FA;
      box-shadow: 0 50px 140px rgba(0,0,0,0.65), 0 16px 50px rgba(0,0,0,0.4);
      border: 1px solid #D1D5DB;
    }}
    .broll-lp .chrome-bar {{
      position: absolute; top: 0; left: 0; right: 0; height: 92px;
      background: #F5F5F7; border-bottom: 1px solid #D1D5DB;
      display: flex; align-items: center; padding: 0 24px; gap: 18px; z-index: 3;
    }}
    .broll-lp .chrome-bar .lights {{ display: flex; gap: 10px; }}
    .broll-lp .chrome-bar .lights span {{
      width: 16px; height: 16px; border-radius: 50%; display: block;
    }}
    .broll-lp .chrome-bar .lights .l1 {{ background: #FF5F57; }}
    .broll-lp .chrome-bar .lights .l2 {{ background: #FEBC2E; }}
    .broll-lp .chrome-bar .lights .l3 {{ background: #28C840; }}
    .broll-lp .chrome-bar .url {{
      flex: 1; height: 52px; background: #fff; border: 1px solid #D1D5DB; border-radius: 12px;
      display: flex; align-items: center; padding: 0 20px; gap: 10px;
      font-family: "Inter", -apple-system, system-ui, sans-serif; font-size: 22px; color: #1F2937; font-weight: 500;
    }}
    .broll-lp .viewport {{ position: absolute; top: 92px; left: 0; right: 0; bottom: 0; overflow: hidden; }}
    .broll-lp .page {{
      position: absolute; top: 0; left: 0; right: 0; width: 100%;
      background: #fff; color: #0B1220;
      font-family: "Inter", "{b['font_body']}", system-ui, sans-serif;
      padding: 60px 80px 120px;
      display: flex; flex-direction: column; gap: 56px;
      min-height: 240%;
    }}
    .broll-lp .nav {{ display: flex; justify-content: space-between; align-items: center;
      padding-bottom: 24px; border-bottom: 1px solid #E5E7EB; }}
    .broll-lp .nav .brand {{
      font-family: "{b['font_display']}", sans-serif; font-weight: 700; font-size: 32px; letter-spacing: 0.02em;
    }}
    .broll-lp .nav .brand .hl {{ color: {b['primary']}; }}
    .broll-lp .nav .menu {{ display: flex; gap: 32px; font-size: 20px; color: #6B7280; }}
    .broll-lp .hero {{ display: flex; flex-direction: column; gap: 28px; padding-top: 28px; }}
    .broll-lp .hero h1 {{
      font-family: "{b['font_heading']}", sans-serif; font-weight: 700; font-size: 82px;
      line-height: 1.08; letter-spacing: -0.02em; color: #0B1220;
    }}
    .broll-lp .hero p {{ font-size: 28px; line-height: 1.45; color: #4B5563; max-width: 90%; }}
    .broll-lp .hero .cta {{
      display: inline-block; background: {b['primary']}; color: #fff;
      padding: 18px 36px; border-radius: 12px;
      font-family: "{b['font_heading']}", sans-serif; font-weight: 600; font-size: 22px;
      letter-spacing: 0.08em; text-transform: uppercase; align-self: flex-start;
    }}
    .broll-lp .features {{ display: grid; grid-template-columns: 1fr 1fr; gap: 28px; margin-top: 40px; }}
    .broll-lp .features .card {{
      background: #F3F4F6; border-radius: 16px; padding: 28px; height: 240px;
      display: flex; flex-direction: column; gap: 14px;
    }}
    .broll-lp .features .card .icon {{
      width: 52px; height: 52px; border-radius: 12px; background: {b['primary']};
      display: flex; align-items: center; justify-content: center;
      color: #fff; font-family: "{b['font_heading']}", sans-serif; font-weight: 700; font-size: 28px;
    }}
    .broll-lp .features .card .t {{
      font-family: "{b['font_heading']}", sans-serif; font-weight: 700; font-size: 22px;
      color: #0B1220; line-height: 1.15;
    }}
    .broll-lp .features .card .line {{
      height: 10px; background: #D1D5DB; border-radius: 4px;
    }}
    .broll-lp .features .card .line.short {{ width: 60%; }}
    .broll-lp .trust {{
      display: flex; justify-content: space-between; align-items: center;
      padding: 28px 12px; gap: 24px;
      border-top: 1px solid #E5E7EB; border-bottom: 1px solid #E5E7EB;
      margin-top: 24px;
    }}
    .broll-lp .trust .logo {{
      font-family: "{b['font_heading']}", sans-serif; font-weight: 700; font-size: 22px;
      color: #9CA3AF; letter-spacing: 0.02em;
    }}
    .broll-lp .form {{ background: #F9FAFB; border-radius: 16px; padding: 48px;
      display: flex; flex-direction: column; gap: 22px; margin-top: 40px; }}
    .broll-lp .form .title {{ font-size: 32px; font-weight: 600; color: #0B1220; }}
    .broll-lp .form .field {{ height: 72px; background: #fff; border: 1px solid #E5E7EB; border-radius: 10px; }}
    .broll-lp .cursor {{ position: absolute; width: 32px; height: 44px; z-index: 5; pointer-events: none;
      filter: drop-shadow(0 2px 6px rgba(0,0,0,0.3)); }}

    /* ---- Watermark mask (covers bottom-right HeyGen/Synthesia/Gemini-style avatar mark) ---- */
    #watermark-mask {{
      position: absolute; right: 24px; bottom: 24px;
      width: 320px; height: 86px;
      background: {b['card_bg']}; border: 1px solid {b['border']};
      border-radius: 12px; z-index: 16;
      display: flex; align-items: center; justify-content: center; gap: 14px;
      padding: 0 22px;
      font-family: "{b['font_display']}", sans-serif; font-weight: 700;
      font-size: 32px; letter-spacing: 0.04em;
      color: {b['fg']};
    }}
    #watermark-mask .hl {{ color: {b['primary']}; }}

    /* ---- B-roll: form shrinking ---- */
    .form-shrink {{
      position: absolute; inset: 80px 60px 180px; overflow: hidden; z-index: 14;
      border-radius: 22px; background: #fff;
      box-shadow: 0 50px 140px rgba(0,0,0,0.65), 0 16px 50px rgba(0,0,0,0.4);
      border: 1px solid #D1D5DB;
      padding: 60px 72px; display: flex; flex-direction: column; gap: 28px;
      font-family: "Inter", -apple-system, system-ui, sans-serif;
    }}
    .form-shrink .fs-title {{
      font-family: "{b['font_heading']}", sans-serif; font-weight: 700; font-size: 44px;
      color: #0B1220; line-height: 1.1;
    }}
    .form-shrink .fs-sub {{ font-size: 22px; color: #6B7280; margin-top: -14px; }}
    .form-shrink .fs-fields {{ display: flex; flex-direction: column; gap: 18px; }}
    .form-shrink .fs-field {{ display: flex; flex-direction: column; gap: 6px;
      will-change: opacity, transform, height; overflow: hidden; transform-origin: top center; }}
    .form-shrink .fs-field label {{ font-size: 18px; font-weight: 500; color: #374151; letter-spacing: 0.02em; }}
    .form-shrink .fs-field .input {{ height: 62px; background: #F9FAFB; border: 1px solid #E5E7EB; border-radius: 10px; }}
    .form-shrink .fs-cta {{ display: inline-block; background: {b['primary']}; color: #fff;
      padding: 18px 38px; border-radius: 12px; margin-top: 10px;
      font-family: "{b['font_heading']}", sans-serif; font-weight: 600; font-size: 22px;
      letter-spacing: 0.08em; text-transform: uppercase; align-self: flex-start; }}
    .form-shrink .fs-callout {{
      position: absolute; right: 8%; top: 40%;
      font-family: "{b['font_display']}", sans-serif; font-weight: 700; font-size: 200px;
      line-height: 0.95; filter: drop-shadow(0 0 24px rgba(74,222,128,0.45));
      opacity: 0; transform: scale(0.6) rotate(-6deg); letter-spacing: -0.02em;
    }}

    /* ---- metric hero ---- */
    .metric-hero {{
      position: absolute; inset: 0; z-index: 22;
      display: flex; flex-direction: column; justify-content: center; align-items: center;
      padding: 80px; text-align: center; gap: 40px;
      background: radial-gradient(ellipse at 50% 50%, rgba(74,222,128,0.14), rgba(0,0,0,0.92) 62%);
    }}
    .metric-hero .num {{
      font-family: "{b['font_display']}", sans-serif; font-weight: 700; font-size: 260px;
      line-height: 0.9; letter-spacing: -0.04em;
      max-width: 100%; padding: 0 40px;
      filter: drop-shadow(0 0 36px rgba(74,222,128,0.55));
      white-space: nowrap;
    }}
    .metric-hero .label {{
      font-family: "{b['font_heading']}", sans-serif; font-weight: 600; font-size: 52px;
      letter-spacing: 0.18em; text-transform: uppercase; color: {b['fg']};
    }}

    /* ---- arrow callout ---- */
    .arrow-box {{ position: absolute; inset: 0; z-index: 21; pointer-events: none; will-change: opacity; }}
    .arrow-svg {{ position: absolute; inset: 0; width: 100%; height: 100%; overflow: visible; }}
    .arrow-label {{
      position: absolute;
      font-family: "{b['font_heading']}", sans-serif; font-weight: 700; font-size: 38px;
      letter-spacing: 0.08em; text-transform: uppercase;
      color: #fff; background: #0b1220;
      padding: 14px 22px; border-radius: 10px;
      box-shadow: 0 8px 24px rgba(0,0,0,0.45);
    }}

    /* ---- takeover text ---- */
    .takeover {{
      position: absolute; inset: 0; z-index: 23;
      display: flex; justify-content: center; align-items: center;
      padding: 80px; text-align: center;
      background: rgba(0,0,0,0.85);
      font-family: "{b['font_display']}", sans-serif; font-weight: 700;
      line-height: 1.0; letter-spacing: -0.02em;
      filter: drop-shadow(0 0 24px rgba(255,45,85,0.5));
    }}

    /* ---- brand chip (unified lower-third + watermark cover) ---- */
    /* Positioned to cover HeyGen/Synthesia/Gemini-style avatar-tool watermark at bottom-right */
    #lower-third {{
      position: absolute; right: 0; bottom: 0; width: 460px; height: 200px;
      padding: 42px 32px;
      background: {b['card_bg']}; border: 1px solid {b['border']};
      border-top-left-radius: 16px;
      display: flex; flex-direction: column; justify-content: center; gap: 8px;
      z-index: 15;
      box-shadow: -16px -16px 40px rgba(0,0,0,0.4);
    }}
    #lower-third .primary {{
      font-family: "{b['font_heading']}", sans-serif; font-weight: 700; font-size: 36px;
      letter-spacing: 0.04em; text-transform: uppercase; color: {b['fg']};
      line-height: 1.1;
    }}
    #lower-third .secondary {{
      font-family: "{b['font_heading']}", sans-serif; font-weight: 500; font-size: 24px;
      letter-spacing: 0.1em; text-transform: uppercase; color: {b['muted']};
      line-height: 1.2;
    }}
    #lower-third .secondary .hl {{ color: {b['primary']}; }}

    /* ---- payoff ---- */
    #payoff {{
      position: absolute; inset: 0; z-index: 30;
      display: flex; flex-direction: column; justify-content: center; align-items: center;
      padding: 120px 80px; gap: 48px; text-align: center; background: {b['bg']};
    }}
    #payoff .glow {{
      position: absolute; inset: -20%;
      background: radial-gradient(ellipse at 50% 72%, rgba(59,158,255,0.3), transparent 58%);
      filter: blur(30px); z-index: 0;
    }}
    #payoff .content {{ position: relative; z-index: 1; display: flex; flex-direction: column; gap: 48px; align-items: center; }}
    #payoff .cta {{
      font-family: "{b['font_heading']}", sans-serif; font-weight: 600; font-size: 54px;
      letter-spacing: 0.08em; text-transform: uppercase; color: {b['primary']};
      max-width: 820px; line-height: 1.15;
    }}
    #payoff .wordmark {{
      font-family: "{b['font_display']}", sans-serif; font-weight: 700; font-size: 120px;
      letter-spacing: 0.04em; color: {b['fg']}; line-height: 1;
    }}
    #payoff .wordmark .hl {{ color: {b['primary']}; }}
    #payoff .url {{
      font-family: "{b['font_heading']}", sans-serif; font-weight: 500; font-size: 34px;
      letter-spacing: 0.24em; text-transform: uppercase; color: {b['muted']};
    }}
  </style>
</head>
<body>
  <div id="root" data-composition-id="main" data-start="0" data-duration="{dur}" data-width="{w}" data-height="{h}">
"""


# ---------------------------------------------------------------------------
# Beat → (HTML, JS) renderers
# ---------------------------------------------------------------------------

def render_wordmark(text: str) -> str:
    """"DIGI|SCHOLA" → "DIGI<span class='hl'>SCHOLA</span>" """
    if "|" not in text:
        return text
    before, after = text.split("|", 1)
    return f'{before}<span class="hl">{after}</span>'


def beat_hook(beat: Dict[str, Any], brand: Dict[str, Any]) -> (str, str):
    s, d = beat["start"], beat["duration"]
    html = f"""  <div id="hook" class="clip" data-start="{s}" data-duration="{d}" data-track-index="30">
    <div class="glow"></div>
    <div class="content">
      <div class="main" id="hook-main">{beat['main']}</div>
      <div class="sub" id="hook-sub">{beat['sub']}</div>
    </div>
  </div>"""
    js = f"""
  tl.from("#hook .glow", {{ opacity: 0, scale: 0.9, duration: 0.8, ease: "power2.inOut" }}, {s + 0.05});
  tl.from("#hook-main", {{ y: 60, opacity: 0, duration: 0.55, ease: "power2.out" }}, {s + 0.15});
  tl.from("#hook-sub", {{ y: 24, opacity: 0, duration: 0.45, ease: "power2.out" }}, {s + 0.40});"""
    return html, js


def beat_source_video(beat: Dict[str, Any], brand: Dict[str, Any]) -> (str, str):
    src = beat["source_asset"]
    s, d = beat["start"], beat["duration"]
    html = f"""  <div class="video-stage" id="video-stage">
    <video id="src-video" class="clip" data-start="{s}" data-duration="{d}" data-track-index="0"
           src="{src}" muted playsinline crossorigin="anonymous"></video>
    <div class="video-dim" id="video-dim"></div>
  </div>
  <audio id="src-audio" class="clip" data-start="{s}" data-duration="{d}" data-track-index="1"
         data-volume="1" src="{src}"></audio>"""
    return html, ""


def beat_caption_phrase(beat: Dict[str, Any], brand: Dict[str, Any], idx: int) -> (str, str):
    s, d = beat["start"], beat["duration"]
    cid = f"cap-{idx}"
    spans = "".join(
        f'<span class="w {w.get("class","word") if w.get("class","word")!="word" else ""}">{w["text"]}</span>'
        for w in beat["words"]
    )
    html = f'  <div id="{cid}" class="caption clip" data-start="{s}" data-duration="{d}" data-track-index="5">{spans}</div>'
    js = f"""
  tl.from("#{cid}", {{ y: 24, opacity: 0, duration: 0.3, ease: "power2.out" }}, {s + 0.02});"""
    return html, js


def beat_caption_wordpop(beat: Dict[str, Any], brand: Dict[str, Any], idx: int) -> (str, str):
    s, d = beat["start"], beat["duration"]
    cid = f"wp-{idx}"
    fg = brand["fg"]
    primary = brand["primary"]

    spans = []
    for i, w in enumerate(beat["words"]):
        cls = w.get("class", "word")
        extra = f" {cls}" if cls != "word" else ""
        spans.append(
            f'<span id="{cid}-w-{i}" class="w{extra}" style="opacity:0;">{w["text"]}</span>'
        )
    html = f'  <div id="{cid}" class="caption clip" data-start="{s}" data-duration="{d}" data-track-index="5">{"".join(spans)}</div>'

    js_lines = [f'\n  tl.from("#{cid}", {{ opacity: 0, duration: 0.18, ease: "power2.out" }}, {s + 0.02});']
    for i, w in enumerate(beat["words"]):
        w_start = w.get("start", s + (i * d / max(1, len(beat["words"]))))
        w_end = w.get("end", w_start + 0.18)
        cls = w.get("class", "word")
        resting_color = brand["primary"] if cls == "metric" else fg
        # Entry pop
        js_lines.append(
            f'  tl.fromTo("#{cid}-w-{i}", {{ opacity: 0, scale: 0.80 }}, '
            f'{{ opacity: 1, scale: 1.0, duration: 0.22, ease: "back.out(1.6)" }}, {w_start});'
        )
        # Active emphasis
        js_lines.append(
            f'  tl.to("#{cid}-w-{i}", {{ scale: 1.08, color: "{primary}", duration: 0.12, ease: "power2.out", overwrite: "auto" }}, {w_start});'
        )
        # Return to resting
        js_lines.append(
            f'  tl.to("#{cid}-w-{i}", {{ scale: 1.0, color: "{resting_color}", duration: 0.18, ease: "power2.inOut", overwrite: "auto" }}, {w_end});'
        )
    js_lines.append(
        f'  tl.to("#{cid}", {{ opacity: 0, duration: 0.22, ease: "power2.in", overwrite: "auto" }}, {s + d - 0.24});'
    )
    return html, "".join(js_lines)


def beat_broll_landing_page(beat: Dict[str, Any], brand: Dict[str, Any], idx: int) -> (str, str):
    s, d = beat["start"], beat["duration"]
    bid = f"broll-lp-{idx}"
    url = beat.get("url", "example.com")
    title = beat.get("page_title", "Your hero headline goes here")
    copy = beat.get("page_copy", "Supporting sentence.")
    cta = beat.get("cta_text", "GET STARTED")
    scroll_from = beat.get("scroll_from", 0)
    scroll_to = beat.get("scroll_to", -1400)
    cursor_from = beat.get("cursor_from", "18%")
    cursor_to = beat.get("cursor_to", "70%")

    html = f"""  <div id="{bid}" class="broll-lp clip" data-start="{s}" data-duration="{d}" data-track-index="8">
    <div class="chrome-bar">
      <div class="lights"><span class="l1"></span><span class="l2"></span><span class="l3"></span></div>
      <div class="url">🔒 {url}</div>
    </div>
    <div class="viewport">
      <div class="page" id="{bid}-page">
        <div class="nav">
          <div class="brand">ACME<span class="hl">.CO</span></div>
          <div class="menu"><span>Product</span><span>Pricing</span><span>Login</span></div>
        </div>
        <div class="hero">
          <h1>{title}</h1>
          <p>{copy}</p>
          <span class="cta">{cta}</span>
        </div>
        <div class="features">
          <div class="card">
            <div class="icon">S</div>
            <div class="t">Seamless Setup</div>
            <div class="line"></div><div class="line short"></div>
          </div>
          <div class="card">
            <div class="icon">⚡</div>
            <div class="t">Lightning Fast</div>
            <div class="line"></div><div class="line short"></div>
          </div>
          <div class="card">
            <div class="icon">✓</div>
            <div class="t">Enterprise Grade</div>
            <div class="line"></div><div class="line short"></div>
          </div>
          <div class="card">
            <div class="icon">☁</div>
            <div class="t">Cloud Native</div>
            <div class="line"></div><div class="line short"></div>
          </div>
        </div>
        <div class="trust">
          <div class="logo">ACME</div>
          <div class="logo">NORTHWIND</div>
          <div class="logo">CONTOSO</div>
          <div class="logo">INITECH</div>
          <div class="logo">STARK</div>
        </div>
        <div class="form">
          <div class="title">Tell us about you</div>
          <div class="field"></div><div class="field"></div><div class="field"></div>
          <div class="field"></div><div class="field"></div><div class="field"></div>
        </div>
      </div>
    </div>
    <svg class="cursor" id="{bid}-cursor" viewBox="0 0 32 44" fill="none"
         style="left: 58%; top: {cursor_from};">
      <path d="M2 2L2 34L10 26L14.5 38L19 36L14.5 24L26 24L2 2Z" fill="#FFFFFF" stroke="#0B1220" stroke-width="2" stroke-linejoin="round"/>
    </svg>
  </div>"""
    js = f"""
  tl.from("#{bid}", {{ opacity: 0, duration: 0.25, ease: "power2.out" }}, {s + 0.02});
  tl.fromTo("#{bid}-page", {{ y: {scroll_from} }}, {{ y: {scroll_to}, duration: {d - 0.4}, ease: "power1.inOut" }}, {s + 0.15});
  tl.fromTo("#{bid}-cursor", {{ top: "{cursor_from}" }}, {{ top: "{cursor_to}", duration: {d - 0.4}, ease: "power1.inOut" }}, {s + 0.15});
  tl.to("#{bid}", {{ opacity: 0, duration: 0.3, ease: "power2.in", overwrite: "auto" }}, {s + d - 0.32});"""
    return html, js


def beat_broll_form_shrinking(beat: Dict[str, Any], brand: Dict[str, Any], idx: int) -> (str, str):
    s, d = beat["start"], beat["duration"]
    bid = f"fs-{idx}"
    title = beat.get("form_title", "Request a demo")
    fields_long = beat["fields_long"]
    fields_keep = set(beat.get("fields_keep", []))
    callout_text = beat.get("callout_text", "−66%")
    callout_color = color(brand, beat.get("callout_color", "success"))

    fields_html = "".join(
        f'<div class="fs-field" data-keep="{"true" if f in fields_keep else "false"}">'
        f'<label>{f}</label><div class="input"></div></div>'
        for f in fields_long
    )

    html = f"""  <div id="{bid}" class="form-shrink clip" data-start="{s}" data-duration="{d}" data-track-index="8">
    <div class="fs-title">{title}</div>
    <div class="fs-sub">Fill out the form to get started.</div>
    <div class="fs-fields" id="{bid}-fields">{fields_html}</div>
    <span class="fs-cta">SUBMIT</span>
    <div class="fs-callout" id="{bid}-callout" style="color: {callout_color};">{callout_text}</div>
  </div>"""
    js = f"""
  tl.from("#{bid}", {{ opacity: 0, scale: 0.96, y: 20, duration: 0.4, ease: "power3.out" }}, {s + 0.02});
  tl.to("#{bid} .fs-field[data-keep='false']", {{
    opacity: 0, scaleY: 0, height: 0, marginTop: 0, marginBottom: 0,
    duration: 0.55, stagger: 0.08, ease: "power2.inOut",
    transformOrigin: "top center", overwrite: "auto"
  }}, {s + 0.55});
  tl.to("#{bid}-callout", {{ opacity: 1, scale: 1.0, rotate: 0, duration: 0.45, ease: "back.out(1.8)", overwrite: "auto" }}, {s + 1.0});
  tl.to("#{bid}", {{ opacity: 0, duration: 0.3, ease: "power2.in", overwrite: "auto" }}, {s + d - 0.32});"""
    return html, js


def beat_metric_hero(beat: Dict[str, Any], brand: Dict[str, Any], idx: int) -> (str, str):
    s, d = beat["start"], beat["duration"]
    bid = f"mh-{idx}"
    prefix = beat.get("prefix", "")
    suffix = beat.get("suffix", "")
    target = beat["target_value"]
    label = beat.get("label", "")
    num_color = color(brand, beat.get("color", "primary"))

    html = f"""  <div id="{bid}" class="metric-hero clip" data-start="{s}" data-duration="{d}" data-track-index="22">
    <div class="num" id="{bid}-num" style="color: {num_color};">{prefix}<span id="{bid}-v">0</span>{suffix}</div>
    <div class="label">{label}</div>
  </div>"""
    js = f"""
  tl.from("#{bid}", {{ opacity: 0, duration: 0.3, ease: "power2.out" }}, {s + 0.02});
  tl.from("#{bid}-num", {{ scale: 0.5, duration: 0.55, ease: "back.out(1.6)" }}, {s + 0.05});
  (function() {{
    var p = {{ v: 0 }};
    tl.to(p, {{
      v: {target}, duration: 0.9, ease: "power3.out",
      onUpdate: function() {{
        var el = document.getElementById("{bid}-v");
        if (el) el.textContent = Math.round(p.v);
      }}
    }}, {s + 0.12});
  }})();
  tl.from("#{bid} .label", {{ y: 24, opacity: 0, duration: 0.4, ease: "power2.out" }}, {s + 0.42});
  tl.to("#{bid}", {{ scale: 1.03, duration: 0.35, ease: "power2.out", overwrite: "auto" }}, {s + d * 0.55});
  tl.to("#{bid}", {{ scale: 1.0, duration: 0.3, ease: "power2.inOut", overwrite: "auto" }}, {s + d * 0.55 + 0.35});
  tl.to("#{bid}", {{ opacity: 0, duration: 0.35, ease: "power2.in", overwrite: "auto" }}, {s + d - 0.38});"""
    return html, js


def beat_arrow_callout(beat: Dict[str, Any], brand: Dict[str, Any], idx: int) -> (str, str):
    s, d = beat["start"], beat["duration"]
    bid = f"arr-{idx}"
    fx, fy = beat["from"]
    tx, ty = beat["to"]
    cx, cy = beat.get("control", [(fx + tx) // 2, min(fy, ty) - 120])
    label = beat.get("label", "")
    lpos = beat.get("label_pos", {"right": 60, "top": fy - 30})
    lpos_css = "; ".join(f"{k}: {v}px" for k, v in lpos.items())
    arr_color = color(brand, beat.get("color", "accent_danger"))

    html = f"""  <div id="{bid}" class="arrow-box clip" data-start="{s}" data-duration="{d}" data-track-index="11">
    <svg class="arrow-svg" viewBox="0 0 1080 1920" preserveAspectRatio="none">
      <defs>
        <marker id="ahead-{bid}" viewBox="0 0 12 12" refX="6" refY="6" markerWidth="8" markerHeight="8" orient="auto-start-reverse">
          <path d="M0,0 L12,6 L0,12 Z" fill="{arr_color}"/>
        </marker>
      </defs>
      <path id="{bid}-p" d="M {fx} {fy} Q {cx} {cy} {tx} {ty}"
            stroke="{arr_color}" stroke-width="8" stroke-linecap="round" fill="none"
            marker-end="url(#ahead-{bid})"
            style="stroke-dasharray: 2000; stroke-dashoffset: 2000;"/>
    </svg>
    <div class="arrow-label" style="{lpos_css}; color:#fff;">{label}</div>
  </div>"""
    js = f"""
  tl.from("#{bid}", {{ opacity: 0, duration: 0.15 }}, {s + 0.02});
  tl.fromTo("#{bid}-p", {{ attr: {{ "stroke-dashoffset": 2000 }} }}, {{ attr: {{ "stroke-dashoffset": 0 }}, duration: 0.65, ease: "power2.out" }}, {s + 0.05});
  tl.to("#{bid}", {{ opacity: 0, duration: 0.3, ease: "power2.in", overwrite: "auto" }}, {s + d - 0.32});"""
    return html, js


def beat_zoom_punch(beat: Dict[str, Any], brand: Dict[str, Any]) -> (str, str):
    s = beat["start"]
    target = beat.get("target", "#video-stage")
    intensity = beat.get("intensity", "medium")
    hold = beat.get("hold", 0.2)
    recovery = beat.get("recovery", 0.6)

    presets = {
        "subtle": {"scale": 1.04, "shake": 0, "in_dur": 0.18, "ease": "power2.out"},
        "medium": {"scale": 1.08, "shake": 2, "in_dur": 0.14, "ease": "power3.out"},
        "hard":   {"scale": 1.14, "shake": 5, "in_dur": 0.10, "ease": "expo.out"},
    }
    p = presets.get(intensity, presets["medium"])

    js_lines = [f'\n  tl.to("{target}", {{ scale: {p["scale"]}, duration: {p["in_dur"]}, ease: "{p["ease"]}", overwrite: "auto" }}, {s});']
    if p["shake"] > 0 and hold > 0.15:
        shake_start = s + p["in_dur"]
        js_lines.append(f'  tl.to("{target}", {{ x: {p["shake"]}, y: {-p["shake"]*0.6}, duration: {hold*0.25}, ease: "power1.inOut" }}, {shake_start});')
        js_lines.append(f'  tl.to("{target}", {{ x: {-p["shake"]*0.8}, y: {p["shake"]*0.4}, duration: {hold*0.25}, ease: "power1.inOut" }}, {shake_start + hold*0.25});')
        js_lines.append(f'  tl.to("{target}", {{ x: 0, y: 0, duration: {hold*0.25}, ease: "power1.out" }}, {shake_start + hold*0.5});')
    js_lines.append(f'  tl.to("{target}", {{ scale: 1.0, x: 0, y: 0, duration: {recovery}, ease: "power2.inOut", overwrite: "auto" }}, {s + p["in_dur"] + hold});')
    return "", "".join(js_lines)


def beat_takeover_text(beat: Dict[str, Any], brand: Dict[str, Any], idx: int) -> (str, str):
    s, d = beat["start"], beat["duration"]
    bid = f"tk-{idx}"
    text = beat["text"].replace("\n", "<br/>")
    col = color(brand, beat.get("color", "accent_danger"))
    size = beat.get("size_px", 160)
    font = beat.get("font", brand["font_display"])

    html = f"""  <div id="{bid}" class="takeover clip" data-start="{s}" data-duration="{d}" data-track-index="25"
       style="font-size: {size}px; color: {col}; font-family: '{font}', sans-serif;">
    <div>{text}</div>
  </div>"""
    js = f"""
  tl.from("#{bid}", {{ scale: 1.15, opacity: 0, duration: 0.25, ease: "power3.out" }}, {s + 0.02});
  tl.to("#{bid}", {{ opacity: 0, duration: 0.3, ease: "power2.in", overwrite: "auto" }}, {s + d - 0.32});"""
    return html, js


def beat_video_dim(beat: Dict[str, Any], brand: Dict[str, Any]) -> (str, str):
    s, d = beat["start"], beat["duration"]
    target_opacity = beat.get("target_opacity", 0.55)
    js = f"""
  tl.to("#video-dim", {{ opacity: {target_opacity}, duration: 0.4, ease: "power2.out", overwrite: "auto" }}, {s});
  tl.to("#video-dim", {{ opacity: 0, duration: 0.4, ease: "power2.out", overwrite: "auto" }}, {s + d});"""
    return "", js


def beat_lower_third(beat: Dict[str, Any], brand: Dict[str, Any]) -> (str, str):
    s, d = beat["start"], beat["duration"]
    primary = beat["primary"]
    secondary = render_wordmark(beat["secondary"])

    html = f"""  <div id="lower-third" class="clip" data-start="{s}" data-duration="{d}" data-track-index="7">
    <div class="primary">{primary}</div>
    <div class="secondary">{secondary}</div>
  </div>"""
    js = f"""
  tl.from("#lower-third", {{ x: 40, opacity: 0, duration: 0.5, ease: "power2.out" }}, {s + 0.02});"""
    return html, js


def beat_watermark_mask(beat: Dict[str, Any], brand: Dict[str, Any]) -> (str, str):
    """Small Digischola-branded chip covering bottom-right corner where HeyGen/Synthesia
    avatar tools place their watermark. Runs for the full source-video window."""
    s, d = beat["start"], beat["duration"]
    wordmark = render_wordmark(beat.get("wordmark", "DIGI|SCHOLA"))
    html = f"""  <div id="watermark-mask" class="clip" data-start="{s}" data-duration="{d}" data-track-index="16">
    {wordmark}
  </div>"""
    js = f"""
  tl.from("#watermark-mask", {{ opacity: 0, duration: 0.25, ease: "power2.out" }}, {s + 0.02});"""
    return html, js


def beat_payoff(beat: Dict[str, Any], brand: Dict[str, Any]) -> (str, str):
    s, d = beat["start"], beat["duration"]
    cta = beat["cta"]
    wordmark = render_wordmark(beat["wordmark"])
    url = beat.get("url", "")

    html = f"""  <div id="payoff" class="clip" data-start="{s}" data-duration="{d}" data-track-index="31">
    <div class="glow"></div>
    <div class="content">
      <div class="cta">{cta}</div>
      <div class="wordmark">{wordmark}</div>
      <div class="url">{url}</div>
    </div>
  </div>"""
    js = f"""
  tl.from("#payoff .glow", {{ opacity: 0, scale: 0.9, duration: 0.8, ease: "power2.inOut" }}, {s + 0.05});
  tl.from("#payoff .cta", {{ y: 40, opacity: 0, duration: 0.55, ease: "power3.out" }}, {s + 0.12});
  tl.from("#payoff .wordmark", {{ y: 50, opacity: 0, duration: 0.6, ease: "expo.out" }}, {s + 0.28});
  tl.from("#payoff .url", {{ y: 20, opacity: 0, duration: 0.5, ease: "power2.out" }}, {s + 0.45});
  tl.to("#src-video", {{ opacity: 0, duration: 0.4, ease: "power2.out", overwrite: "auto" }}, {s - 0.05});"""
    return html, js


# Dispatch
BEAT_RENDERERS = {
    "hook":               lambda b, br, i: beat_hook(b, br),
    "source-video":       lambda b, br, i: beat_source_video(b, br),
    "caption-phrase":     lambda b, br, i: beat_caption_phrase(b, br, i),
    "caption-wordpop":    lambda b, br, i: beat_caption_wordpop(b, br, i),
    "broll-landing-page": lambda b, br, i: beat_broll_landing_page(b, br, i),
    "broll-form-shrinking": lambda b, br, i: beat_broll_form_shrinking(b, br, i),
    "metric-hero":        lambda b, br, i: beat_metric_hero(b, br, i),
    "arrow-callout":      lambda b, br, i: beat_arrow_callout(b, br, i),
    "zoom-punch":         lambda b, br, i: beat_zoom_punch(b, br),
    "takeover-text":      lambda b, br, i: beat_takeover_text(b, br, i),
    "video-dim":          lambda b, br, i: beat_video_dim(b, br),
    "lower-third":        lambda b, br, i: beat_lower_third(b, br),
    "watermark-mask":     lambda b, br, i: beat_watermark_mask(b, br),
    "payoff":             lambda b, br, i: beat_payoff(b, br),
}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def assemble(plan_path: Path, project_dir: Path) -> Path:
    plan = json.loads(plan_path.read_text())
    brand = plan["brand"]

    html_parts = [head(plan)]
    js_parts = []

    for i, beat in enumerate(plan["beats"]):
        bt = beat["type"]
        renderer = BEAT_RENDERERS.get(bt)
        if not renderer:
            print(f"WARN: unknown beat type: {bt}", file=sys.stderr)
            continue
        h, j = renderer(beat, brand, i)
        if h:
            html_parts.append(h)
        if j:
            js_parts.append(j)

    html_parts.append("""  </div>
  <script>
    window.__timelines = window.__timelines || {};
    var tl = gsap.timeline({ paused: true });
""")
    html_parts.append("".join(js_parts))
    html_parts.append("""
    window.__timelines["main"] = tl;
  </script>
</body>
</html>
""")

    out = project_dir / "index.html"
    out.write_text("".join(html_parts))
    return out


def main() -> int:
    if len(sys.argv) < 3:
        print("usage: assemble_composition.py <content-plan.json> <project-dir>")
        return 1
    plan_path = Path(sys.argv[1])
    project_dir = Path(sys.argv[2])
    if not plan_path.is_file():
        print(f"ERROR: plan not found: {plan_path}", file=sys.stderr)
        return 1
    if not project_dir.is_dir():
        print(f"ERROR: project dir not found: {project_dir}", file=sys.stderr)
        return 1
    out = assemble(plan_path, project_dir)
    print(f"assembled: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
