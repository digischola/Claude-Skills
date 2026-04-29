#!/usr/bin/env python3
"""
render_ad_copy_dashboard.py — generates a unified HTML dashboard
for ad-copywriter outputs at the program folder root.

Reads from:
  - {program}/_engine/working/ad-copy-report.md     (ad copy variants)
  - {program}/_engine/working/image-prompts.md      (image prompts)
  - {program}/_engine/working/video-storyboards.md  (video storyboards)
  - {program}/_engine/working/creative-brief.json   (campaigns + personas + gate audit)
  - {program}/_engine/brand-config.json             (single-program)
    OR {client-root}/_engine/brand-config.json      (multi-program — _engine/ at client root)

Writes:
  - {program}/ad-copy-dashboard.html                (presentable, folder root)

Usage:
  python3 render_ad_copy_dashboard.py "<path-to-program-folder>"

Example:
  python3 render_ad_copy_dashboard.py "/Users/digischola/Desktop/Sri Krishna Mandir/Weekend Love Feast"

Generalizes across all clients. Brand-themed via brand-config.json. Works in any
future client/program folder that has the four input files in _engine/working/.
"""

import json
import re
import sys
import html
from pathlib import Path
from datetime import datetime


def find_brand_config(program_dir: Path) -> dict:
    """Probe single-program then multi-program locations for brand-config.json."""
    candidates = [
        program_dir / "_engine" / "brand-config.json",
        program_dir.parent / "_engine" / "brand-config.json",
    ]
    for c in candidates:
        if c.exists():
            with open(c) as f:
                return json.load(f)
    # Fallback minimal brand
    return {
        "businessName": program_dir.parent.name,
        "colors": {
            "primaryAccent": "#3B9EFF",
            "secondaryAccent": "#1f3671",
            "darkText": "#0f172a",
            "lightBackground": "#f8fafc",
        },
        "fontFamily": "Inter",
        "fontSecondary": "Georgia",
    }


def parse_ad_copy_report(md_path: Path) -> list:
    """Parse ad-copy-report.md into structured ad data."""
    if not md_path.exists():
        return []
    text = md_path.read_text()
    ads = []
    # Each ad block starts with "## Ad N — <name>"
    ad_pattern = re.compile(r"^## Ad \d+ — (.+?)$", re.MULTILINE)
    matches = list(ad_pattern.finditer(text))
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        block = text[start:end]
        ad = {"name": m.group(1).strip(), "block": block}
        # Extract Framework, Audience, Persona, Format, ID
        for k, label in [
            ("framework", r"\*\*Framework:\*\*\s*(.+)"),
            ("audience", r"\*\*Audience:\*\*\s*(.+)"),
            ("persona", r"\*\*Persona:\*\*\s*(.+)"),
            ("format", r"\*\*Format:\*\*\s*(.+)"),
            ("id", r"\*\*ID:\*\*\s*`([^`]+)`"),
            ("cta", r"### CTA:\s*`([^`]+)`"),
        ]:
            mm = re.search(label, block)
            ad[k] = mm.group(1).strip() if mm else ""
        # Extract primary text variants — each "**V1 — ..."
        primary_texts = []
        for vmatch in re.finditer(
            r"\*\*(V\d+)[^*]+\*\*\s*\n>\s*(.+?)\n\*\[(.+?)\]\s*·\s*(\d+)\s*chars\*",
            block,
            re.DOTALL,
        ):
            primary_texts.append({
                "label": vmatch.group(1),
                "text": vmatch.group(2).strip(),
                "source": vmatch.group(3),
                "chars": int(vmatch.group(4)),
            })
        ad["primary_texts"] = primary_texts
        # Extract headlines table rows
        headlines = []
        for hm in re.finditer(
            r"\|\s*(H\d+)\s*\|\s*([^|]+?)\s*\|\s*(\d+)\s*\|\s*\[([^\]]+)\]",
            block,
        ):
            headlines.append({
                "label": hm.group(1),
                "text": hm.group(2).strip(),
                "chars": int(hm.group(3)),
                "source": hm.group(4),
            })
        ad["headlines"] = headlines
        # Extract descriptions
        descriptions = []
        for dm in re.finditer(
            r"\|\s*(D\d+)\s*\|\s*([^|]+?)\s*\|\s*(\d+)\s*\|\s*\[([^\]]+)\]",
            block,
        ):
            descriptions.append({
                "label": dm.group(1),
                "text": dm.group(2).strip(),
                "chars": int(dm.group(3)),
                "source": dm.group(4),
            })
        ad["descriptions"] = descriptions
        ads.append(ad)
    return ads


def parse_image_prompts(md_path: Path) -> list:
    """Parse image-prompts.md (2026-04-28 dual-format mandate).

    Per `references/image-prompt-patterns.md`, every prompt block has:
      - "## Image N — <id-with-card-label>" heading
      - "**ID:** `<id>`" line
      - "**Aspect ratio:** ..." line
      - "**Priority:** ..." line
      - "**`requires_reference_image`:** true|false" line
      - "**`reference_subject`:** <text>" line
      - "### Spec-prose format" section with a fenced code block
      - "### JSON format" section with a fenced ```json code block

    Falls back to legacy single-format / `{prefix}`-placeholder format if the new
    headers aren't found, so older clients still render. Returns list of dicts.
    """
    if not md_path.exists():
        return []
    text = md_path.read_text()

    # Extract brand prefix once for legacy fallback
    legacy_prefix = ""
    pm = re.search(
        r"## Brand[^\n]*prefix.*?\n\n>\s*(.+?)\n\n",
        text,
        re.DOTALL,
    )
    if pm:
        legacy_prefix = pm.group(1).strip()

    prompts = []
    img_heading_re = re.compile(r"^## Image \d+ — (.+?)$", re.MULTILINE)
    matches = list(img_heading_re.finditer(text))
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        block = text[start:end]
        heading = m.group(1).strip()

        # New-format metadata extraction
        meta = {}
        for key, pattern in [
            ("id_field", r"\*\*ID:\*\*\s*`([^`]+)`"),
            ("aspect_ratio", r"\*\*Aspect ratio:\*\*\s*(.+)"),
            ("priority", r"\*\*Priority:\*\*\s*(.+)"),
            ("requires_reference_image", r"\*\*`?requires_reference_image`?:\*\*\s*(\w+)"),
            ("reference_subject", r"\*\*`?reference_subject`?:\*\*\s*(.+)"),
        ]:
            mm = re.search(pattern, block)
            if mm:
                meta[key] = mm.group(1).strip()

        ref_required = str(meta.get("requires_reference_image", "false")).lower() == "true"
        ref_subject = meta.get("reference_subject", "").strip()

        # Find spec-prose code block (after "### Spec-prose format")
        prose_text = ""
        pm = re.search(
            r"###\s+Spec-prose format[^\n]*\n+```[a-z]*\n(.+?)\n```",
            block,
            re.DOTALL | re.IGNORECASE,
        )
        if pm:
            prose_text = pm.group(1).strip()

        # Find JSON block (after "### JSON format")
        json_text = ""
        # Skip the intro instruction line (the "Generate one image..." paragraph)
        jm = re.search(
            r"###\s+JSON format[^\n]*\n+(?:[^\n]*\n+)?```json?\n(.+?)\n```",
            block,
            re.DOTALL | re.IGNORECASE,
        )
        if jm:
            json_text = jm.group(1).strip()

        if prose_text or json_text:
            # New dual-format mode
            prompts.append({
                "id": meta.get("id_field", heading),
                "card_label": heading,
                "aspect_ratio": meta.get("aspect_ratio", ""),
                "priority": meta.get("priority", ""),
                "requires_reference_image": ref_required,
                "reference_subject": ref_subject if ref_required else "",
                "prose_format": prose_text,
                "json_format": json_text,
                "format_mode": "dual",
                # Legacy fields kept for backwards-compat with downstream consumers
                "prompt_with_prefix": prose_text or json_text,
                "raw_prompt": prose_text or json_text,
            })
            continue

        # Legacy single-format fallback (pre-2026-04-28 image-prompts.md)
        sub_heading_re = re.compile(r"^### (.+?)$", re.MULTILINE)
        sub_matches = list(sub_heading_re.finditer(block))
        legacy_subs = []
        if sub_matches:
            for j, sm in enumerate(sub_matches):
                ss = sm.start()
                se = sub_matches[j + 1].start() if j + 1 < len(sub_matches) else len(block)
                sub_block = block[ss:se]
                qm = re.search(r">\s*(.+?)\n\n\*Word count", sub_block, re.DOTALL)
                if qm:
                    raw = qm.group(1).strip()
                    legacy_subs.append({
                        "card_label": sm.group(1).strip(),
                        "raw_prompt": raw,
                        "prompt_with_prefix": raw.replace("{prefix}", legacy_prefix),
                    })
        else:
            qm = re.search(r">\s*(.+?)\n\n\*Word count", block, re.DOTALL)
            if qm:
                raw = qm.group(1).strip()
                legacy_subs.append({
                    "card_label": "",
                    "raw_prompt": raw,
                    "prompt_with_prefix": raw.replace("{prefix}", legacy_prefix),
                })

        for sub in legacy_subs:
            prompts.append({
                "id": heading,
                "card_label": sub["card_label"] or heading,
                "aspect_ratio": "",
                "priority": "",
                "requires_reference_image": False,
                "reference_subject": "",
                "prose_format": sub["prompt_with_prefix"],
                "json_format": "",
                "format_mode": "legacy",
                "prompt_with_prefix": sub["prompt_with_prefix"],
                "raw_prompt": sub["raw_prompt"],
            })
    return prompts


def parse_video_storyboards(md_path: Path) -> list:
    """Parse video-storyboards.md into structured storyboard data."""
    if not md_path.exists():
        return []
    text = md_path.read_text()
    storyboards = []
    pattern = re.compile(r"^## Storyboard \d+ — (.+?)$", re.MULTILINE)
    matches = list(pattern.finditer(text))
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        block = text[start:end]
        sb = {"name": m.group(1).strip(), "block": block}
        # Extract metadata
        for k, label in [
            ("audience", r"\*\*Audience:\*\*\s*(.+)"),
            ("persona", r"\*\*Persona:\*\*\s*(.+)"),
            ("duration", r"\*\*Duration:\*\*\s*(.+)"),
            ("aspect_ratio", r"\*\*Aspect ratio:\*\*\s*(.+)"),
            ("audio", r"\*\*Audio:\*\*\s*(.+)"),
        ]:
            mm = re.search(label, block)
            sb[k] = mm.group(1).strip() if mm else ""
        # Extract combined VO script
        vom = re.search(
            r"### Combined VO script.*?\n\n>\s*(.+?)(?:\n\n|$)",
            block,
            re.DOTALL,
        )
        sb["vo_script"] = vom.group(1).strip() if vom else ""
        # Extract frames — "#### Frame N (M:SS to M:SS) — <label>"
        frames = []
        fp = re.compile(r"^#### Frame \d+ \(([^)]+)\) — (.+?)$", re.MULTILINE)
        fmatches = list(fp.finditer(block))
        for j, fm in enumerate(fmatches):
            fs = fm.start()
            fe = fmatches[j + 1].start() if j + 1 < len(fmatches) else len(block)
            frame_block = block[fs:fe]
            frame = {
                "timing": fm.group(1).strip(),
                "label": fm.group(2).strip(),
            }
            for k, label in [
                ("visual", r"\*\*Visual\*\*\s*\|\s*([^|]+?)\s*\|"),
                ("motion", r"\*\*Motion\*\*\s*\|\s*([^|]+?)\s*\|"),
                ("text_overlay", r"\*\*Text overlay\*\*\s*\|\s*([^|]+?)\s*\|"),
                ("voiceover", r"\*\*Voiceover\*\*\s*\|\s*([^|]+?)\s*\|"),
                ("voice_direction", r"\*\*Voice direction\*\*\s*\|\s*([^|]+?)\s*\|"),
                ("music", r"\*\*Music\*\*\s*\|\s*([^|]+?)\s*\|"),
            ]:
                mm = re.search(label, frame_block)
                frame[k] = mm.group(1).strip() if mm else ""
            frames.append(frame)
        sb["frames"] = frames
        storyboards.append(sb)
    return storyboards


def parse_gate_audit(md_path: Path) -> dict:
    """Pull the Gate Audit summary from ad-copy-report.md."""
    if not md_path.exists():
        return {}
    text = md_path.read_text()
    gate = {}
    am = re.search(r"## Gate Audit \(auto-generated\).*?(?=\n## |\Z)", text, re.DOTALL)
    if not am:
        return gate
    block = am.group(0)
    if "NO TRIGGERS FIRED" in block:
        gate["gate_a"] = "NO TRIGGERS FIRED"
    elif "TRIGGERS FIRED" in block:
        gate["gate_a"] = "TRIGGERS FIRED"
    if "ALL CLAIMS VERIFIED" in block:
        gate["gate_b"] = "ALL CLAIMS VERIFIED"
    # Pull voice + char-limit summary lines
    gate["voice_audit"] = []
    for line in block.split("\n"):
        if line.startswith("- ") and "✓" in line and (
            "Em dashes" in line
            or "Engagement bait" in line
            or "Hype" in line
            or "deity" in line
            or "Headlines" in line
            or "Descriptions" in line
            or "Primary text" in line
            or "ISKCON" in line.lower() or "ISKCON" in line
        ):
            gate["voice_audit"].append(line.lstrip("- ").rstrip())
    return gate


def js_escape(s: str) -> str:
    """Escape for embedding in single-quoted JS string inside HTML attribute."""
    return s.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n").replace("\r", "")


def html_escape(s: str) -> str:
    return html.escape(str(s), quote=True)


def render_dashboard(
    program_dir: Path,
    business_name: str,
    program_name: str,
    brand: dict,
    ads: list,
    image_prompts: list,
    storyboards: list,
    gate: dict,
    creative_brief: dict,
) -> str:
    colors = brand.get("colors", {})
    primary = colors.get("primaryAccent", "#3B9EFF")
    secondary = colors.get("secondaryAccent", "#1f3671")
    dark = colors.get("darkText", "#071442")
    light = colors.get("lightBackground", "#f8eae1")
    chromatic = brand.get("allChromaticColors", [primary, secondary, dark])
    accent_alt = chromatic[3] if len(chromatic) > 3 else primary
    font_body = brand.get("fontFamily", "Inter")
    font_display = brand.get("fontSecondary", "Georgia")
    logo_url = brand.get("logoUrl", "")
    today = datetime.now().strftime("%Y-%m-%d")

    # Compute hero KPIs
    total_primary = sum(len(a["primary_texts"]) for a in ads)
    total_headlines = sum(len(a["headlines"]) for a in ads)
    total_descriptions = sum(len(a["descriptions"]) for a in ads)

    # Brand logo block
    if logo_url:
        logo_html = f'<div class="brand-logo"><img src="{html_escape(logo_url)}" alt="{html_escape(business_name)}"></div>'
    else:
        logo_html = f'<div class="brand-logo brand-logo-text">{html_escape(business_name[:2].upper())}</div>'

    # Gate audit pill
    gate_a = gate.get("gate_a", "UNKNOWN")
    gate_b = gate.get("gate_b", "UNKNOWN")
    gate_a_pill = (
        '<span class="pill pill-good">Gate A: NO TRIGGERS FIRED</span>'
        if gate_a == "NO TRIGGERS FIRED"
        else '<span class="pill pill-bad">Gate A: TRIGGERS FIRED</span>'
    )
    gate_b_pill = (
        '<span class="pill pill-good">Gate B: ALL CLAIMS VERIFIED</span>'
        if gate_b == "ALL CLAIMS VERIFIED"
        else '<span class="pill pill-warn">Gate B: PARTIAL</span>'
    )

    # Build ad cards
    ad_cards = []
    for ad in ads:
        primary_html = []
        for v in ad["primary_texts"]:
            esc = html_escape(v["text"])
            jstxt = js_escape(v["text"])
            primary_html.append(f"""
              <div class="copy-block">
                <div class="copy-meta">
                  <span class="variant-label">{html_escape(v['label'])}</span>
                  <span class="char-count">{v['chars']} chars</span>
                  <span class="src-tag">[{html_escape(v['source'])}]</span>
                  <button class="copy-btn" onclick="copyText('{jstxt}', this)">📋 Copy</button>
                </div>
                <div class="copy-text">{esc}</div>
              </div>
            """)
        primary_block = "".join(primary_html)

        headlines_rows = []
        for h in ad["headlines"]:
            esc = html_escape(h["text"])
            jstxt = js_escape(h["text"])
            headlines_rows.append(f"""
              <tr>
                <td class="lbl">{html_escape(h['label'])}</td>
                <td>{esc}</td>
                <td class="num">{h['chars']}</td>
                <td><span class="src-tag-sm">[{html_escape(h['source'])}]</span></td>
                <td><button class="copy-btn-sm" onclick="copyText('{jstxt}', this)">📋</button></td>
              </tr>
            """)
        headlines_table = "".join(headlines_rows)

        desc_rows = []
        for d in ad["descriptions"]:
            esc = html_escape(d["text"])
            jstxt = js_escape(d["text"])
            desc_rows.append(f"""
              <tr>
                <td class="lbl">{html_escape(d['label'])}</td>
                <td>{esc}</td>
                <td class="num">{d['chars']}</td>
                <td><span class="src-tag-sm">[{html_escape(d['source'])}]</span></td>
                <td><button class="copy-btn-sm" onclick="copyText('{jstxt}', this)">📋</button></td>
              </tr>
            """)
        desc_table = "".join(desc_rows)

        cta_btn = ""
        if ad.get("cta"):
            cta_text = ad["cta"]
            cta_btn = f'<span class="cta-pill">CTA: {html_escape(cta_text)}</span>'

        ad_cards.append(f"""
          <article class="ad-card">
            <header class="ad-head">
              <div class="ad-id">{html_escape(ad.get('id',''))}</div>
              <h3>{html_escape(ad['name'])}</h3>
              <div class="ad-meta">
                <span class="meta-pill"><b>Framework:</b> {html_escape(ad.get('framework',''))}</span>
                <span class="meta-pill"><b>Audience:</b> {html_escape(ad.get('audience',''))}</span>
                <span class="meta-pill"><b>Persona:</b> {html_escape(ad.get('persona',''))}</span>
                <span class="meta-pill"><b>Format:</b> {html_escape(ad.get('format',''))}</span>
                {cta_btn}
              </div>
            </header>

            <h4 class="sub">Primary text variants</h4>
            <div class="copy-grid">{primary_block}</div>

            <details class="ad-details">
              <summary class="collapse-btn">Headlines ({len(ad['headlines'])} variants, ≤40 chars each)</summary>
              <div class="collapse-body">
                <table class="copy-table">
                  <thead><tr><th>#</th><th>Headline</th><th>Chars</th><th>Source</th><th>Copy</th></tr></thead>
                  <tbody>{headlines_table}</tbody>
                </table>
              </div>
            </details>

            <details class="ad-details">
              <summary class="collapse-btn">Descriptions ({len(ad['descriptions'])} variants, ≤30 chars each)</summary>
              <div class="collapse-body">
                <table class="copy-table">
                  <thead><tr><th>#</th><th>Description</th><th>Chars</th><th>Source</th><th>Copy</th></tr></thead>
                  <tbody>{desc_table}</tbody>
                </table>
              </div>
            </details>
          </article>
        """)
    ad_cards_html = "".join(ad_cards)

    # Build image prompt cards (2026-04-28 dual-format mandate)
    prompt_cards = []
    for idx, p in enumerate(image_prompts):
        label = p.get("card_label") or p.get("id") or f"Image {idx+1}"
        is_dual = p.get("format_mode") == "dual"
        ref_required = bool(p.get("requires_reference_image"))
        ref_subject = p.get("reference_subject", "")
        meta_pills = []
        if p.get("aspect_ratio"):
            meta_pills.append(f'<span class="prompt-meta-pill">{html_escape(p["aspect_ratio"])}</span>')
        if p.get("priority"):
            meta_pills.append(f'<span class="prompt-meta-pill">{html_escape(p["priority"])}</span>')
        meta_pills_html = "".join(meta_pills)

        # Reference badge (animated paperclip if attachment required)
        ref_badge = ""
        if ref_required:
            ref_badge = (
                '<div class="ref-badge"><span class="ref-clip">📎</span>'
                f'<span class="ref-label">Attach: {html_escape(ref_subject or "reference image")}</span></div>'
            )

        cid = f"prompt-{idx+1}"

        if is_dual and (p.get("prose_format") or p.get("json_format")):
            prose = p.get("prose_format", "")
            json_text = p.get("json_format", "")
            esc_prose = html_escape(prose)
            esc_json = html_escape(json_text)
            prose_id = f"{cid}-prose"
            json_id = f"{cid}-json"
            # Default tab: spec-prose (more readable; JSON tab toggle for modern AI tools).
            # Copy buttons use copyFrom() pattern — read textContent from the rendered element
            # rather than embedding content inside an onclick attribute. Prevents the
            # double-quote-in-JSON breaking the HTML attribute.
            prompt_cards.append(f"""
              <article class="prompt-card{' has-ref' if ref_required else ''}">
                <header class="prompt-head">
                  <div class="prompt-id">{html_escape(p.get('id',''))}</div>
                  <h4>{html_escape(label)}</h4>
                  <div class="prompt-meta-row">{meta_pills_html}</div>
                  {ref_badge}
                </header>
                <div class="tab-bar">
                  <button class="tab-btn" data-card="{cid}" data-tab="json" onclick="switchTab(this)">JSON</button>
                  <button class="tab-btn active" data-card="{cid}" data-tab="prose" onclick="switchTab(this)">Spec-prose</button>
                </div>
                <div class="prompt-body tab-panel" data-card="{cid}" data-tab="prose" id="{prose_id}">{esc_prose}</div>
                <div class="prompt-body tab-panel hidden" data-card="{cid}" data-tab="json" id="{json_id}">{esc_json}</div>
                <div class="prompt-foot">
                  <button class="copy-btn" onclick="copyFrom('{prose_id}', this)">📋 Copy spec-prose</button>
                  <button class="copy-btn" onclick="copyFrom('{json_id}', this)">📋 Copy JSON</button>
                </div>
              </article>
            """)
        else:
            # Legacy single-format fallback — also uses copyFrom() pattern for safety
            full = p.get("prompt_with_prefix") or p.get("prose_format") or ""
            esc_full = html_escape(full)
            full_id = f"{cid}-full"
            prompt_cards.append(f"""
              <article class="prompt-card{' has-ref' if ref_required else ''}">
                <header class="prompt-head">
                  <div class="prompt-id">{html_escape(p.get('id',''))}</div>
                  <h4>{html_escape(label)}</h4>
                  <div class="prompt-meta-row">{meta_pills_html}</div>
                  {ref_badge}
                </header>
                <div class="prompt-body" id="{full_id}">{esc_full}</div>
                <div class="prompt-foot">
                  <button class="copy-btn" onclick="copyFrom('{full_id}', this)">📋 Copy full prompt</button>
                </div>
              </article>
            """)
    prompt_cards_html = "".join(prompt_cards) if prompt_cards else '<p class="empty">No image prompts produced.</p>'

    # Build video storyboard cards
    storyboard_html = []
    for sb in storyboards:
        frames_html = []
        for fr in sb["frames"]:
            frames_html.append(f"""
              <div class="frame-card">
                <div class="frame-head">
                  <span class="frame-time">{html_escape(fr.get('timing',''))}</span>
                  <span class="frame-label">{html_escape(fr.get('label',''))}</span>
                </div>
                <table class="frame-layers">
                  <tr><th>Visual</th><td>{html_escape(fr.get('visual',''))}</td></tr>
                  <tr><th>Motion</th><td>{html_escape(fr.get('motion',''))}</td></tr>
                  <tr><th>Text overlay</th><td>{html_escape(fr.get('text_overlay',''))}</td></tr>
                  <tr><th>Voiceover</th><td>{html_escape(fr.get('voiceover',''))}</td></tr>
                  <tr><th>Voice direction</th><td>{html_escape(fr.get('voice_direction',''))}</td></tr>
                  <tr><th>Music</th><td>{html_escape(fr.get('music',''))}</td></tr>
                </table>
              </div>
            """)
        frames_block = "".join(frames_html)
        vo_script = sb.get("vo_script", "")
        vo_html = ""
        if vo_script:
            esc_vo = html_escape(vo_script)
            js_vo = js_escape(vo_script)
            vo_html = f"""
              <div class="vo-block">
                <div class="vo-head"><b>Combined VO script (paste into ElevenLabs / Google AI Studio)</b>
                  <button class="copy-btn" onclick="copyText('{js_vo}', this)">📋 Copy VO</button>
                </div>
                <div class="vo-text">{esc_vo}</div>
              </div>
            """
        storyboard_html.append(f"""
          <article class="storyboard-card">
            <header class="storyboard-head">
              <h3>{html_escape(sb['name'])}</h3>
              <div class="storyboard-meta">
                <span class="meta-pill"><b>Audience:</b> {html_escape(sb.get('audience',''))}</span>
                <span class="meta-pill"><b>Persona:</b> {html_escape(sb.get('persona',''))}</span>
                <span class="meta-pill"><b>Duration:</b> {html_escape(sb.get('duration',''))}</span>
                <span class="meta-pill"><b>Aspect:</b> {html_escape(sb.get('aspect_ratio',''))}</span>
              </div>
            </header>
            <div class="frames-grid">{frames_block}</div>
            {vo_html}
          </article>
        """)
    storyboard_block = "".join(storyboard_html) if storyboard_html else '<p class="empty">No video storyboards produced.</p>'

    # Voice audit list
    voice_audit_items = "".join(
        f"<li>{html_escape(line)}</li>" for line in gate.get("voice_audit", [])
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html_escape(business_name)} {html_escape(program_name)} — Ad Copy Dashboard</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans:ital,wght@0,300..800;1,300..800&family=Noto+Sans+Devanagari:wght@300..800&family=Cardo:ital,wght@0,400;0,700;1,400&family=Inter:wght@300..800&display=swap" rel="stylesheet">
<style>
  :root {{
    --primary:{primary};
    --secondary:{secondary};
    --dark:{dark};
    --dark-2:{dark}cc;
    --light:{light};
    --accent-alt:{accent_alt};
    --primary-soft:rgba(0,0,0,0.04);
    --line:rgba(0,0,0,0.08);
    --line-strong:rgba(0,0,0,0.16);
    --card:#ffffff;
    --card-2:#f8fafc;
    --ink:#0f172a;
    --muted:#64748b;
    --good:#16a34a;
    --warn:#ea580c;
    --bad:#dc2626;
    --font-body:'{font_body}','Noto Sans','Inter',system-ui,sans-serif;
    --font-display:'{font_display}','Cardo',Georgia,serif;
  }}
  *{{box-sizing:border-box;margin:0;padding:0}}
  html{{scroll-behavior:smooth}}
  body{{font-family:var(--font-body);background:#fafaf7;color:var(--ink);line-height:1.6;-webkit-font-smoothing:antialiased}}
  .container{{max-width:1280px;margin:0 auto;padding:0 24px}}

  header.topbar{{position:sticky;top:0;z-index:100;background:rgba(255,255,255,0.95);backdrop-filter:blur(12px);border-bottom:1px solid var(--line);padding:14px 0}}
  .topbar-row{{display:flex;justify-content:space-between;align-items:center;gap:16px}}
  .brand{{display:flex;align-items:center;gap:12px}}
  .brand-logo{{width:42px;height:42px;border-radius:8px;background:#fff;display:flex;align-items:center;justify-content:center;padding:4px;flex-shrink:0;border:1px solid var(--line)}}
  .brand-logo img{{max-width:100%;max-height:100%;object-fit:contain}}
  .brand-logo-text{{background:var(--primary);color:#fff;font-weight:800;font-family:var(--font-display)}}
  .brand-name{{font-weight:700;font-size:15px;letter-spacing:0.2px}}
  .brand-sub{{font-size:11px;color:var(--muted);letter-spacing:0.5px;text-transform:uppercase}}
  nav.nav-links{{display:flex;gap:18px;font-size:13px;color:var(--muted);overflow-x:auto}}
  nav.nav-links a{{color:var(--muted);text-decoration:none}}
  nav.nav-links a:hover{{color:var(--primary)}}
  @media (max-width:900px){{nav.nav-links{{display:none}}}}

  .hero{{padding:64px 0 40px}}
  .hero-eyebrow{{display:inline-block;padding:6px 14px;background:var(--primary-soft);border:1px solid var(--line);border-radius:999px;color:var(--primary);font-size:11px;font-weight:700;letter-spacing:1.2px;text-transform:uppercase;margin-bottom:24px}}
  h1{{font-family:var(--font-display);font-weight:700;font-size:clamp(30px,5vw,52px);line-height:1.05;letter-spacing:-0.5px;margin-bottom:18px;color:var(--ink)}}
  .hero-lede{{font-size:16px;color:var(--muted);max-width:760px;margin-bottom:32px}}
  .hero-tags{{display:flex;flex-wrap:wrap;gap:10px;margin-bottom:36px}}
  .hero-tag{{padding:7px 14px;background:var(--card);border:1px solid var(--line);border-radius:999px;font-size:12px}}
  .hero-tag b{{color:var(--primary)}}

  .kpi-row{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}}
  @media (max-width:800px){{.kpi-row{{grid-template-columns:repeat(2,1fr)}}}}
  .kpi{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:20px}}
  .kpi-label{{font-size:11px;color:var(--muted);letter-spacing:1px;text-transform:uppercase;margin-bottom:8px}}
  .kpi-value{{font-family:var(--font-display);font-size:32px;color:var(--ink);font-weight:700}}
  .kpi-value .unit{{font-size:13px;color:var(--primary);margin-left:4px;font-weight:400}}
  .kpi-sub{{font-size:11px;color:var(--muted);margin-top:4px}}

  section{{padding:48px 0;border-top:1px solid var(--line)}}
  .section-tag{{display:inline-block;padding:5px 12px;background:var(--primary-soft);color:var(--primary);font-size:10px;font-weight:700;letter-spacing:1.4px;text-transform:uppercase;border-radius:999px;margin-bottom:14px}}
  h2{{font-family:var(--font-display);font-size:clamp(22px,3vw,32px);margin-bottom:14px;letter-spacing:-0.3px}}
  .section-lede{{font-size:14px;color:var(--muted);max-width:760px;margin-bottom:24px}}

  .ad-card{{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:24px;margin-bottom:18px}}
  .ad-head{{margin-bottom:18px;padding-bottom:14px;border-bottom:1px solid var(--line)}}
  .ad-id{{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:11px;color:var(--muted);letter-spacing:0.4px}}
  .ad-card h3{{font-family:var(--font-display);font-size:22px;margin:6px 0 12px;color:var(--ink)}}
  .ad-meta{{display:flex;flex-wrap:wrap;gap:8px}}
  .meta-pill{{display:inline-block;padding:5px 11px;background:var(--card-2);border:1px solid var(--line);border-radius:999px;font-size:12px;color:var(--ink)}}
  .meta-pill b{{color:var(--primary);font-weight:700;margin-right:3px}}
  .cta-pill{{display:inline-block;padding:5px 11px;background:var(--primary);color:#fff;border-radius:999px;font-size:12px;font-weight:700}}

  .sub{{font-size:11px;color:var(--primary);text-transform:uppercase;letter-spacing:1.2px;margin:14px 0 12px;font-weight:700}}

  .copy-grid{{display:grid;gap:10px}}
  .copy-block{{background:var(--card-2);border:1px solid var(--line);border-radius:10px;padding:14px}}
  .copy-meta{{display:flex;align-items:center;gap:10px;margin-bottom:8px;flex-wrap:wrap}}
  .variant-label{{font-family:ui-monospace,monospace;font-size:11px;font-weight:700;color:var(--primary);background:var(--primary-soft);padding:3px 8px;border-radius:6px}}
  .char-count{{font-size:11px;color:var(--muted)}}
  .src-tag{{font-size:10px;color:var(--muted);font-style:italic}}
  .src-tag-sm{{font-size:10px;color:var(--muted);font-style:italic}}
  .copy-text{{font-size:14px;color:var(--ink);line-height:1.55}}

  .copy-btn{{margin-left:auto;background:var(--card);border:1px solid var(--line-strong);color:var(--ink);padding:5px 11px;border-radius:6px;font-size:11px;cursor:pointer;font-weight:600;transition:all 0.15s}}
  .copy-btn:hover{{background:var(--primary-soft);border-color:var(--primary);color:var(--primary)}}
  .copy-btn-sm{{background:transparent;border:1px solid var(--line);color:var(--muted);padding:3px 8px;border-radius:5px;font-size:11px;cursor:pointer;transition:all 0.15s}}
  .copy-btn-sm:hover{{background:var(--primary-soft);border-color:var(--primary);color:var(--primary)}}

  .copy-table{{width:100%;border-collapse:collapse;margin-top:10px;font-size:13px}}
  .copy-table th{{background:var(--card-2);text-align:left;padding:10px 12px;font-size:10px;text-transform:uppercase;letter-spacing:0.6px;color:var(--muted);font-weight:700;border-bottom:1px solid var(--line)}}
  .copy-table td{{padding:9px 12px;border-bottom:1px solid var(--line);color:var(--ink);vertical-align:middle}}
  .copy-table td.lbl{{font-family:ui-monospace,monospace;font-weight:700;color:var(--primary);font-size:11px}}
  .copy-table td.num{{font-family:ui-monospace,monospace;font-size:11px;color:var(--muted);text-align:right;width:60px}}
  .copy-table tr:last-child td{{border-bottom:none}}
  .copy-table tr:hover td{{background:var(--primary-soft)}}

  details.ad-details{{margin:14px 0 0 0;background:transparent;padding:0;border:none}}
  summary.collapse-btn{{cursor:pointer;font-size:12px;font-weight:700;color:var(--primary);padding:10px 14px;background:var(--primary-soft);border-radius:8px;list-style:none;transition:all 0.15s}}
  summary.collapse-btn::-webkit-details-marker{{display:none}}
  summary.collapse-btn:before{{content:'▸';display:inline-block;margin-right:8px;transition:transform 0.2s}}
  details[open] summary.collapse-btn:before{{transform:rotate(90deg)}}
  summary.collapse-btn:hover{{background:rgba(0,0,0,0.04)}}
  .collapse-body{{padding:8px 0 0 0}}

  .prompt-grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:14px}}
  @media (max-width:800px){{.prompt-grid{{grid-template-columns:1fr}}}}
  .prompt-card{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:18px;position:relative}}
  .prompt-card.has-ref{{border-color:#f59e0b}}
  .prompt-head{{margin-bottom:10px}}
  .prompt-id{{font-family:ui-monospace,monospace;font-size:10px;color:var(--muted);letter-spacing:0.3px}}
  .prompt-card h4{{font-family:var(--font-display);font-size:16px;margin:4px 0 8px;color:var(--ink)}}
  .prompt-meta-row{{display:flex;gap:6px;flex-wrap:wrap;margin-top:6px}}
  .prompt-meta-pill{{display:inline-block;padding:3px 9px;background:var(--card-2);border:1px solid var(--line);border-radius:999px;font-size:10px;color:var(--muted);font-weight:600;letter-spacing:0.3px}}

  /* Reference-image badge — animated paperclip pulse */
  .ref-badge{{margin-top:10px;padding:8px 12px;background:rgba(245,158,11,0.10);border:1px solid #f59e0b;border-radius:8px;display:flex;align-items:center;gap:8px;font-size:12px;color:#92400e;animation:refPulse 2.4s ease-in-out infinite}}
  @keyframes refPulse {{0%,100%{{box-shadow:0 0 0 0 rgba(245,158,11,0.45)}}50%{{box-shadow:0 0 0 6px rgba(245,158,11,0)}}}}
  .ref-clip{{font-size:14px;animation:refClipBob 1.4s ease-in-out infinite}}
  @keyframes refClipBob {{0%,100%{{transform:rotate(-12deg)}}50%{{transform:rotate(12deg)}}}}
  .ref-label{{font-weight:600}}

  /* Tabs for prompt format toggle (Spec-prose / JSON) */
  .tab-bar{{display:flex;gap:0;margin:12px 0 0;border-bottom:1px solid var(--line)}}
  .tab-btn{{background:transparent;border:none;border-bottom:2px solid transparent;color:var(--muted);padding:8px 14px;font-size:11px;font-weight:700;letter-spacing:0.6px;text-transform:uppercase;cursor:pointer;transition:all 0.15s;font-family:var(--font-body)}}
  .tab-btn:hover{{color:var(--ink)}}
  .tab-btn.active{{color:var(--primary);border-bottom-color:var(--primary)}}
  .tab-panel.hidden{{display:none}}

  .prompt-body{{background:var(--card-2);border:1px solid var(--line);border-top:none;border-radius:0 0 8px 8px;padding:13px;font-size:11px;line-height:1.55;color:var(--ink);white-space:pre-wrap;font-family:ui-monospace,SFMono-Regular,monospace;max-height:280px;overflow-y:auto}}
  .prompt-foot{{margin-top:10px;display:flex;gap:8px;justify-content:flex-end;flex-wrap:wrap}}

  .storyboard-card{{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:24px;margin-bottom:18px}}
  .storyboard-head{{margin-bottom:18px;padding-bottom:14px;border-bottom:1px solid var(--line)}}
  .storyboard-head h3{{font-family:var(--font-display);font-size:20px;margin-bottom:10px}}
  .storyboard-meta{{display:flex;flex-wrap:wrap;gap:8px}}
  .frames-grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:12px;margin-bottom:18px}}
  @media (max-width:800px){{.frames-grid{{grid-template-columns:1fr}}}}
  .frame-card{{background:var(--card-2);border:1px solid var(--line);border-radius:10px;padding:14px}}
  .frame-head{{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;padding-bottom:7px;border-bottom:1px solid var(--line)}}
  .frame-time{{font-family:ui-monospace,monospace;font-size:11px;color:var(--primary);font-weight:700}}
  .frame-label{{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:0.5px;font-weight:700}}
  .frame-layers{{width:100%;font-size:12px}}
  .frame-layers th{{text-align:left;color:var(--primary);font-weight:700;padding:4px 8px 4px 0;width:90px;vertical-align:top;font-size:11px}}
  .frame-layers td{{padding:4px 0;color:var(--ink);vertical-align:top;line-height:1.45}}
  .vo-block{{background:var(--primary-soft);border:1px solid var(--line);border-radius:10px;padding:14px}}
  .vo-head{{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;font-size:12px;color:var(--ink)}}
  .vo-text{{font-size:13px;color:var(--ink);line-height:1.55;font-style:italic}}

  .pill{{display:inline-block;padding:4px 10px;border-radius:999px;font-size:11px;font-weight:700;letter-spacing:0.4px}}
  .pill-good{{background:rgba(22,163,74,0.12);color:var(--good);border:1px solid rgba(22,163,74,0.25)}}
  .pill-warn{{background:rgba(234,88,12,0.12);color:var(--warn);border:1px solid rgba(234,88,12,0.25)}}
  .pill-bad{{background:rgba(220,38,38,0.12);color:var(--bad);border:1px solid rgba(220,38,38,0.25)}}

  .audit-list{{list-style:none;margin-top:12px}}
  .audit-list li{{padding:7px 12px;background:var(--card);border:1px solid var(--line);border-radius:8px;margin-bottom:6px;font-size:12px;color:var(--ink)}}

  footer{{padding:36px 0 24px;text-align:center;color:var(--muted);font-size:12px;border-top:1px solid var(--line);margin-top:24px}}
  .empty{{padding:24px;color:var(--muted);font-style:italic;text-align:center;background:var(--card);border:1px dashed var(--line);border-radius:10px}}

  .toast{{position:fixed;bottom:24px;right:24px;padding:12px 16px;background:var(--ink);color:#fff;border-radius:8px;font-size:13px;opacity:0;transform:translateY(8px);transition:all 0.2s;z-index:1000}}
  .toast.show{{opacity:1;transform:translateY(0)}}
</style>
</head>
<body>

<header class="topbar">
  <div class="container topbar-row">
    <div class="brand">
      {logo_html}
      <div>
        <div class="brand-name">{html_escape(business_name)} {html_escape(program_name)} — Ad Copy Dashboard</div>
        <div class="brand-sub">Ad copywriter output · {today}</div>
      </div>
    </div>
    <nav class="nav-links">
      <a href="#overview">Overview</a>
      <a href="#ads">Ads</a>
      <a href="#prompts">Image Prompts</a>
      <a href="#storyboards">Video</a>
      <a href="#gate">Gate Audit</a>
    </nav>
  </div>
</header>

<section class="hero" id="overview">
  <div class="container">
    <span class="hero-eyebrow">Ad Copywriter · Production-Ready Output</span>
    <h1>{html_escape(business_name)} {html_escape(program_name)}</h1>
    <p class="hero-lede">Pasteable ad copy for Meta Ads Manager, image prompts for Gemini / Midjourney, and video storyboards with VO scripts ready for ElevenLabs / Google AI Studio. Every variant character-limit-validated, every service-claim cross-checked against offerings.md.</p>

    <div class="hero-tags">
      {gate_a_pill} {gate_b_pill}
    </div>

    <div class="kpi-row">
      <div class="kpi">
        <div class="kpi-label">Ads</div>
        <div class="kpi-value">{len(ads)}</div>
        <div class="kpi-sub">distinct creative angles</div>
      </div>
      <div class="kpi">
        <div class="kpi-label">Primary text variants</div>
        <div class="kpi-value">{total_primary}</div>
        <div class="kpi-sub">{total_headlines} headlines · {total_descriptions} descriptions</div>
      </div>
      <div class="kpi">
        <div class="kpi-label">Image prompts</div>
        <div class="kpi-value">{len(image_prompts)}</div>
        <div class="kpi-sub">brand-prefix locked, ready for Gemini</div>
      </div>
      <div class="kpi">
        <div class="kpi-label">Video storyboards</div>
        <div class="kpi-value">{len(storyboards)}</div>
        <div class="kpi-sub">frame-by-frame, VO scripts included</div>
      </div>
    </div>
  </div>
</section>

<section id="ads">
  <div class="container">
    <span class="section-tag">Ad Copy</span>
    <h2>Five angles. Production-ready copy.</h2>
    <p class="section-lede">Click 📋 to copy any variant straight to clipboard. Headlines and descriptions in collapsibles below each ad.</p>
    {ad_cards_html}
  </div>
</section>

<section id="prompts">
  <div class="container">
    <span class="section-tag">Image Prompts</span>
    <h2>Brand-locked prompts for AI image generation</h2>
    <p class="section-lede">Each prompt embeds the brand visual_direction prefix from creative-brief.json. Paste into Gemini, Google AI Studio, Midjourney v6+, or hand to a designer. Light-background bias, high-contrast composition, top 20% clean for headline overlay.</p>
    <div class="prompt-grid">{prompt_cards_html}</div>
  </div>
</section>

<section id="storyboards">
  <div class="container">
    <span class="section-tag">Video Storyboards</span>
    <h2>Frame-by-frame, sound-off-designed</h2>
    <p class="section-lede">Text appears in first 3 seconds (+46% purchase rate). Every key message has matching text overlay (85% of viewers watch muted). Combined VO scripts at the bottom of each storyboard paste directly into ElevenLabs or Google AI Studio.</p>
    {storyboard_block}
  </div>
</section>

<section id="gate">
  <div class="container">
    <span class="section-tag">Gate Audit</span>
    <h2>Voice rules and offering cross-checks</h2>
    <p class="section-lede">Both gates passed for this run. Below is the inline voice / character / sensitivity audit captured at generation time.</p>
    <ul class="audit-list">
      {voice_audit_items if voice_audit_items else '<li>No voice-audit lines extracted from ad-copy-report.md.</li>'}
    </ul>
  </div>
</section>

<footer>
  <div class="container">
    <p>{html_escape(business_name)} {html_escape(program_name)} · Ad Copy Dashboard · Generated {today}</p>
    <p style="margin-top:6px;font-size:11px">Source: <code>_engine/working/ad-copy-report.md</code> + <code>image-prompts.md</code> + <code>video-storyboards.md</code> + <code>creative-brief.json</code></p>
  </div>
</footer>

<div class="toast" id="toast">Copied to clipboard</div>

<script>
function copyText(t, btn) {{
  navigator.clipboard.writeText(t).then(() => {{
    const toast = document.getElementById('toast');
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 1400);
    if (btn) {{
      const orig = btn.textContent;
      btn.textContent = '✓ Copied';
      setTimeout(() => {{ btn.textContent = orig; }}, 1200);
    }}
  }}).catch(() => {{}});
}}

// copyFrom — reads textContent from a rendered element by ID and copies it.
// Used for long content (image prompts, VO scripts) where embedding the text
// inside an onclick="..." attribute would break the HTML when the content
// contains double quotes (JSON, etc).
function copyFrom(elementId, btn) {{
  const el = document.getElementById(elementId);
  if (!el) return;
  copyText(el.textContent, btn);
}}

function switchTab(btn) {{
  const card = btn.dataset.card;
  const tab = btn.dataset.tab;
  document.querySelectorAll('.tab-btn[data-card="' + card + '"]').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  document.querySelectorAll('.tab-panel[data-card="' + card + '"]').forEach(p => {{
    if (p.dataset.tab === tab) p.classList.remove('hidden');
    else p.classList.add('hidden');
  }});
}}
</script>
</body>
</html>
"""


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 render_ad_copy_dashboard.py <program-folder>")
        sys.exit(1)
    program_dir = Path(sys.argv[1]).resolve()
    if not program_dir.is_dir():
        print(f"Not a directory: {program_dir}")
        sys.exit(1)

    working = program_dir / "_engine" / "working"
    if not working.is_dir():
        print(f"Missing _engine/working/ in {program_dir}")
        sys.exit(1)

    # Detect business + program names
    program_name = program_dir.name
    business_name = program_dir.parent.name

    # Read brand-config (probes single-program then multi-program)
    brand = find_brand_config(program_dir)

    # Parse inputs
    ads = parse_ad_copy_report(working / "ad-copy-report.md")
    if not ads:
        # Fall back to legacy filenames if needed
        for legacy in working.glob("*ad-copy-report.md"):
            ads = parse_ad_copy_report(legacy)
            if ads:
                break
    image_prompts = parse_image_prompts(working / "image-prompts.md")
    if not image_prompts:
        for legacy in working.glob("*image-prompts.md"):
            image_prompts = parse_image_prompts(legacy)
            if image_prompts:
                break
    storyboards = parse_video_storyboards(working / "video-storyboards.md")
    if not storyboards:
        for legacy in working.glob("*video-storyboards.md"):
            storyboards = parse_video_storyboards(legacy)
            if storyboards:
                break
    gate = parse_gate_audit(working / "ad-copy-report.md")

    creative_brief = {}
    cb_path = working / "creative-brief.json"
    if cb_path.exists():
        with open(cb_path) as f:
            creative_brief = json.load(f)

    if not ads and not image_prompts and not storyboards:
        print("No ad-copywriter outputs found in _engine/working/. Run Steps 4-7 first.")
        sys.exit(1)

    html_out = render_dashboard(
        program_dir=program_dir,
        business_name=business_name,
        program_name=program_name,
        brand=brand,
        ads=ads,
        image_prompts=image_prompts,
        storyboards=storyboards,
        gate=gate,
        creative_brief=creative_brief,
    )

    out_path = program_dir / "ad-copy-dashboard.html"
    out_path.write_text(html_out)
    print(f"Wrote {out_path}")
    print(f"  Ads: {len(ads)}")
    print(f"  Image prompts: {len(image_prompts)}")
    print(f"  Storyboards: {len(storyboards)}")


if __name__ == "__main__":
    main()
