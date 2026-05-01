#!/usr/bin/env python3
"""render_dashboard.py — assemble dashboard.html from manifest + scores + concept-board.

Brand-themed (reads brand-config.json if present), dark mode, side-by-side variants
with scores + 'use this one' marker, copy-prompt and download buttons.

Usage:
    python3 render_dashboard.py <working_dir> --client-folder <path> [--out <html_path>]
"""
import argparse
import html
import json
import sys
from datetime import datetime
from pathlib import Path


DEFAULT_BRAND = {
    "primary": "#3B9EFF",
    "accent": "#4ADE80",
    "warning": "#EF4444",
    "bg": "#0a0a0a",
    "bg_card": "#161616",
    "text": "#f0f0f0",
    "text_muted": "#888",
    "font_heading": "Manrope, system-ui, sans-serif",
    "font_body": "system-ui, sans-serif",
}


def load_brand(client_folder: Path) -> dict:
    candidates = [
        client_folder / "_engine" / "brand-config.json",
        client_folder / "_engine" / "wiki" / "brand-identity.json",
        client_folder.parent / "_engine" / "brand-config.json",
    ]
    for c in candidates:
        if c.exists():
            try:
                data = json.loads(c.read_text())
                colors = data.get("colors", {})
                fonts = data.get("fonts", {})
                return {**DEFAULT_BRAND, **{k: v for k, v in colors.items() if v}, **{f"font_{k}": v for k, v in fonts.items() if v}}
            except Exception:
                pass
    return DEFAULT_BRAND


def render(working_dir: Path, client_folder: Path, out_path: Path) -> int:
    cb_path = working_dir / "concept-board.json"
    manifest_path = working_dir / "manifest.json"
    scores_path = working_dir / "scores.json"
    if not cb_path.exists() or not manifest_path.exists():
        print("x concept-board.json + manifest.json required", file=sys.stderr)
        return 1
    cb = json.loads(cb_path.read_text())
    manifest = json.loads(manifest_path.read_text())
    scores = json.loads(scores_path.read_text()) if scores_path.exists() else {"scores": {}}
    score_lookup = scores.get("scores", {})

    brand = load_brand(client_folder)

    # Build per-concept sections
    gens_by_concept: dict[str, list[dict]] = {}
    for g in manifest["generations"]:
        gens_by_concept.setdefault(g["concept_id"], []).append(g)

    sections_html: list[str] = []
    for concept in cb["concepts"]:
        cid = concept["concept_id"]
        gens = gens_by_concept.get(cid, [])
        cards: list[str] = []
        for g in gens:
            png_rel = Path(g["output_path"]).resolve()
            try:
                png_link = png_rel.relative_to(out_path.parent.resolve())
            except ValueError:
                png_link = png_rel
            score_key = f"{cid}/{g['variation_id']}/{g['aspect']}"
            score_data = score_lookup.get(score_key, {})
            total_score = score_data.get("total", "—")
            score_color = brand["accent"] if isinstance(total_score, (int, float)) and total_score >= 80 else (brand["primary"] if isinstance(total_score, (int, float)) and total_score >= 60 else brand["warning"])
            cards.append(f"""
            <div class="card" data-cid="{html.escape(cid)}" data-vid="{html.escape(g['variation_id'])}" data-aspect="{html.escape(g['aspect'])}">
              <div class="card-header">
                <div class="card-title">{html.escape(g['variation_id'])} <span class="aspect-badge">{html.escape(g['aspect'])}</span></div>
                <div class="card-score" style="color:{score_color}">{total_score if total_score != '—' else '—'}<span class="score-of">/100</span></div>
              </div>
              <div class="card-img-wrap">
                <img src="{html.escape(str(png_link))}" alt="{html.escape(cid)} {html.escape(g['variation_id'])}" loading="lazy">
              </div>
              <div class="card-meta">
                <div><span class="meta-k">model</span> {html.escape(g['model'])}</div>
                <div><span class="meta-k">credits</span> {g.get('credits_used', 0)}</div>
                {f'<div><span class="meta-k">refs</span> {", ".join(g.get("reference_image_ids") or []) or "—"}</div>' if g.get('reference_image_ids') else ''}
              </div>
              {f'<div class="card-scores">{render_score_bars(score_data, brand)}</div>' if score_data else ''}
              <details class="card-prompt"><summary>prompt</summary><pre>{html.escape(g['prompt'])}</pre></details>
              <div class="card-actions">
                <button class="btn-pick" onclick="markPick('{html.escape(cid)}','{html.escape(g['variation_id'])}','{html.escape(g['aspect'])}')">use this one</button>
              </div>
            </div>
            """)

        sections_html.append(f"""
        <section class="concept">
          <header class="concept-header">
            <h2>{html.escape(concept['concept_name'])}</h2>
            <div class="concept-meta">{html.escape(cid)} · intent: {html.escape(concept.get('intent', ''))}</div>
            <p class="concept-direction">{html.escape(concept.get('creative_direction', ''))}</p>
          </header>
          <div class="cards-grid">
            {''.join(cards)}
          </div>
        </section>
        """)

    title = f"{cb.get('client', '')} — {cb.get('project', 'Image Creatives')}"
    css = f"""
      :root {{
        --primary: {brand['primary']};
        --accent: {brand['accent']};
        --warning: {brand['warning']};
        --bg: {brand['bg']};
        --bg-card: {brand['bg_card']};
        --text: {brand['text']};
        --text-muted: {brand['text_muted']};
        --font-h: {brand['font_heading']};
        --font-b: {brand['font_body']};
      }}
      * {{ box-sizing: border-box; margin: 0; padding: 0; }}
      body {{ background: var(--bg); color: var(--text); font-family: var(--font-b); padding: 32px; }}
      h1 {{ font-family: var(--font-h); font-size: 36px; margin-bottom: 4px; letter-spacing: -0.02em; }}
      .subtitle {{ color: var(--text-muted); margin-bottom: 32px; font-size: 15px; }}
      .stats {{ display: flex; gap: 24px; margin-bottom: 32px; padding: 16px 20px; background: var(--bg-card); border-radius: 12px; border: 1px solid #2a2a2a; }}
      .stat {{ display: flex; flex-direction: column; }}
      .stat-v {{ font-size: 24px; font-weight: 700; font-family: var(--font-h); }}
      .stat-k {{ font-size: 11px; text-transform: uppercase; color: var(--text-muted); letter-spacing: 0.06em; margin-top: 2px; }}
      section.concept {{ margin-bottom: 48px; }}
      .concept-header h2 {{ font-family: var(--font-h); font-size: 24px; margin-bottom: 4px; }}
      .concept-meta {{ color: var(--text-muted); font-size: 12px; margin-bottom: 12px; font-family: monospace; }}
      .concept-direction {{ color: #bbb; max-width: 800px; line-height: 1.5; margin-bottom: 24px; font-size: 14px; }}
      .cards-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 16px; }}
      .card {{ background: var(--bg-card); border: 1px solid #2a2a2a; border-radius: 14px; overflow: hidden; transition: transform 0.18s ease, border-color 0.18s ease; }}
      .card:hover {{ transform: translateY(-2px); border-color: var(--primary); }}
      .card.picked {{ border-color: var(--accent); border-width: 2px; }}
      .card-header {{ display: flex; justify-content: space-between; align-items: center; padding: 12px 14px; }}
      .card-title {{ font-family: var(--font-h); font-weight: 600; font-size: 13px; }}
      .aspect-badge {{ background: #222; padding: 2px 8px; border-radius: 6px; font-size: 10px; color: var(--text-muted); margin-left: 4px; }}
      .card-score {{ font-family: var(--font-h); font-weight: 700; font-size: 18px; }}
      .score-of {{ color: var(--text-muted); font-size: 11px; font-weight: 400; }}
      .card-img-wrap {{ background: #0a0a0a; }}
      .card-img-wrap img {{ width: 100%; display: block; }}
      .card-meta {{ display: flex; gap: 16px; padding: 10px 14px; font-size: 11px; color: var(--text-muted); border-top: 1px solid #1f1f1f; flex-wrap: wrap; }}
      .meta-k {{ color: #555; text-transform: uppercase; font-size: 10px; letter-spacing: 0.05em; margin-right: 4px; }}
      .card-scores {{ padding: 8px 14px; border-top: 1px solid #1f1f1f; font-size: 11px; }}
      .score-bar {{ display: flex; justify-content: space-between; margin: 4px 0; }}
      .score-bar-fill {{ display: inline-block; height: 6px; background: var(--primary); border-radius: 3px; vertical-align: middle; margin-left: 8px; }}
      .card-prompt {{ padding: 8px 14px; border-top: 1px solid #1f1f1f; }}
      .card-prompt summary {{ font-size: 11px; color: var(--text-muted); cursor: pointer; text-transform: uppercase; letter-spacing: 0.05em; }}
      .card-prompt pre {{ font-size: 10px; color: #888; white-space: pre-wrap; padding-top: 8px; max-height: 200px; overflow-y: auto; font-family: monospace; }}
      .card-actions {{ padding: 10px 14px; border-top: 1px solid #1f1f1f; }}
      .btn-pick {{ background: transparent; color: var(--primary); border: 1px solid var(--primary); padding: 6px 12px; border-radius: 6px; font-size: 11px; cursor: pointer; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; transition: all 0.15s; }}
      .btn-pick:hover {{ background: var(--primary); color: var(--bg); }}
      .card.picked .btn-pick {{ background: var(--accent); color: var(--bg); border-color: var(--accent); }}
      footer {{ margin-top: 48px; padding-top: 24px; border-top: 1px solid #2a2a2a; color: var(--text-muted); font-size: 11px; text-align: center; }}
    """

    js = """
      const PICKS_KEY = 'ai-image-gen-picks';
      function loadPicks() { return JSON.parse(localStorage.getItem(PICKS_KEY) || '{}'); }
      function savePicks(p) { localStorage.setItem(PICKS_KEY, JSON.stringify(p)); }
      function markPick(cid, vid, aspect) {
        const picks = loadPicks();
        const key = cid + '|' + aspect;
        picks[key] = vid;
        savePicks(picks);
        applyPicks();
      }
      function applyPicks() {
        const picks = loadPicks();
        document.querySelectorAll('.card').forEach(card => {
          const cid = card.dataset.cid;
          const vid = card.dataset.vid;
          const aspect = card.dataset.aspect;
          const key = cid + '|' + aspect;
          if (picks[key] === vid) card.classList.add('picked');
          else card.classList.remove('picked');
        });
      }
      document.addEventListener('DOMContentLoaded', applyPicks);
    """

    total_gens = len(manifest["generations"])
    total_credits = sum(g.get("credits_used", 0) for g in manifest["generations"])
    by_model: dict[str, int] = {}
    for g in manifest["generations"]:
        by_model[g["model"]] = by_model.get(g["model"], 0) + 1
    top_models = ", ".join(f"{m} ({n})" for m, n in sorted(by_model.items(), key=lambda kv: -kv[1])[:3])

    body = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{html.escape(title)}</title>
<style>{css}</style>
</head>
<body>
<h1>{html.escape(title)}</h1>
<div class="subtitle">image creative review · generated {datetime.now().strftime("%Y-%m-%d %H:%M")}</div>

<div class="stats">
  <div class="stat"><span class="stat-v">{total_gens}</span><span class="stat-k">generations</span></div>
  <div class="stat"><span class="stat-v">{len(cb['concepts'])}</span><span class="stat-k">concepts</span></div>
  <div class="stat"><span class="stat-v">{total_credits}</span><span class="stat-k">credits used</span></div>
  <div class="stat"><span class="stat-v">{html.escape(cb.get('goal', '—'))}</span><span class="stat-k">goal</span></div>
  <div class="stat" style="flex:1"><span class="stat-v" style="font-size:14px;font-weight:400">{html.escape(top_models)}</span><span class="stat-k">top models</span></div>
</div>

{''.join(sections_html)}

<footer>
  Click "use this one" on each concept × aspect to mark winners. Picks saved locally.<br>
  Final picks → move to <code>creatives/&lt;date-name&gt;/</code> at client folder root for campaign-setup.
</footer>

<script>{js}</script>
</body>
</html>
"""
    out_path.write_text(body)
    print(f"  Dashboard rendered: {out_path}")
    return 0


def render_score_bars(score_data: dict, brand: dict) -> str:
    dims = ["brand_voice_fit", "visual_hierarchy", "cta_readability", "sector_sensitivity", "variation_differentiation"]
    out = []
    for d in dims:
        v = score_data.get(d)
        if v is None:
            continue
        pct = max(0, min(100, int(v) * 5))  # assume 0-20 scale
        out.append(f'<div class="score-bar"><span>{d.replace("_", " ")}</span><span>{v} <span class="score-bar-fill" style="width:{pct//2}px"></span></span></div>')
    return "".join(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("working_dir")
    ap.add_argument("--client-folder", required=True, help="Path to client/project root for brand-config lookup")
    ap.add_argument("--out", help="Dashboard HTML output path; defaults to <client-folder>/<date>-image-creatives-dashboard.html")
    args = ap.parse_args()

    wd = Path(args.working_dir)
    client_folder = Path(args.client_folder)
    out = Path(args.out) if args.out else client_folder / f"{datetime.now().strftime('%Y-%m-%d')}-image-creatives-dashboard.html"
    return render(wd, client_folder, out)


if __name__ == "__main__":
    sys.exit(main())
