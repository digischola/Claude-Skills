#!/usr/bin/env python3
"""
Landing Page Builder — Output Validator
Validates HTML prototype and page-spec JSON.

Usage:
  python3 validate_output.py <landing-page.html> [page-spec.json]
"""

import sys
import os
import re
import json

# ── Counters ──
critical = 0
warning = 0
info = 0

def log(level, msg):
    global critical, warning, info
    prefix = {"CRITICAL": "  ❌", "WARNING": "  ⚠️", "INFO": "  ℹ️"}
    tag = {"CRITICAL": "[CRITICAL]", "WARNING": "[WARNING]", "INFO": "[INFO]"}
    print(f"{prefix.get(level, '  ')} {tag.get(level, '')} {msg}")
    if level == "CRITICAL": critical += 1
    elif level == "WARNING": warning += 1
    elif level == "INFO": info += 1

# ── HTML Validation ──
def validate_html(path):
    print(f"\n{'='*60}")
    print(f"  Landing Page HTML")
    print(f"{'='*60}")

    if not os.path.exists(path):
        log("CRITICAL", f"File not found: {path}")
        return

    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        html = f.read()

    size_kb = len(html.encode('utf-8')) / 1024
    lower = html.lower()

    # ── Size check ──
    if size_kb > 500:
        log("CRITICAL", f"File size {size_kb:.0f}KB exceeds 500KB limit")
    elif size_kb > 150:
        log("WARNING", f"File size {size_kb:.0f}KB exceeds 150KB prototype target")
    else:
        log("INFO", f"File size: {size_kb:.0f}KB")

    # ── Structural checks ──
    has_doctype = '<!doctype html>' in lower or '<!DOCTYPE html>' in html
    has_viewport = 'viewport' in lower
    has_charset = 'charset' in lower
    has_title = '<title>' in lower

    if not has_doctype:
        log("CRITICAL", "Missing <!DOCTYPE html>")
    if not has_viewport:
        log("CRITICAL", "Missing viewport meta tag — page won't be mobile-responsive")
    if not has_charset:
        log("WARNING", "Missing charset declaration")
    if not has_title:
        log("WARNING", "Missing <title> tag")

    # ── Semantic structure ──
    semantic_tags = ['<header', '<main', '<section', '<footer']
    found_semantic = [t for t in semantic_tags if t in lower]
    if len(found_semantic) < 3:
        log("WARNING", f"Only {len(found_semantic)}/4 semantic tags found ({', '.join(found_semantic)}). Lovable portability may suffer.")
    else:
        log("INFO", f"Semantic tags: {len(found_semantic)}/4 ({', '.join(found_semantic)})")

    # ── Section count ──
    section_count = lower.count('<section')
    if section_count < 3:
        log("CRITICAL", f"Only {section_count} <section> tags — landing page needs at least 4-6 sections")
    else:
        log("INFO", f"Section count: {section_count}")

    # ── CTA checks ──
    cta_patterns = [
        r'(?:reserve|book|register|apply|schedule|get|start|join|download|check)\s',
        r'(?:my|your)\s+(?:spot|place|seat|call|guide|journey)',
    ]
    cta_found = False
    for pattern in cta_patterns:
        if re.search(pattern, lower):
            cta_found = True
            break

    # Also check for button/a tags with action text
    button_count = lower.count('<button') + lower.count('role="button"')
    cta_link_count = len(re.findall(r'<a[^>]*(?:class|href)[^>]*>(?:reserve|book|register|apply|schedule|get|start|join|download|check)', lower))

    total_ctas = button_count + cta_link_count
    if total_ctas == 0:
        log("CRITICAL", "No CTA buttons or links found")
    elif total_ctas < 2:
        log("WARNING", f"Only {total_ctas} CTA element(s) — should repeat CTAs throughout page")
    else:
        log("INFO", f"CTA elements: {total_ctas}")

    # ── Above-the-fold check (proxy: check if h1 exists early in <body>) ──
    # Strip <head>, <style>, <script> blocks before measuring H1 position so inline
    # CSS/JS doesn't inflate document length and create false "H1 too late" warnings.
    body_match = re.search(r'<body[^>]*>', lower)
    if body_match:
        body_content = html[body_match.end():]
        body_lower = body_content.lower()
        # Strip inline <style> and <script> blocks
        stripped = re.sub(r'<style[^>]*>.*?</style>', '', body_lower, flags=re.DOTALL)
        stripped = re.sub(r'<script[^>]*>.*?</script>', '', stripped, flags=re.DOTALL)
    else:
        stripped = lower
        body_content = html

    h1_match = re.search(r'<h1[^>]*>', stripped)
    if not h1_match:
        log("CRITICAL", "No <h1> headline found")
    else:
        h1_pos = h1_match.start()
        content_len = len(stripped) if stripped else 1
        h1_pct = (h1_pos / content_len) * 100
        if h1_pct > 25:
            log("WARNING", f"H1 appears at {h1_pct:.0f}% of body content — may not be above fold")
        else:
            log("INFO", f"H1 position: {h1_pct:.0f}% into body content (good)")

    # ── Required page components ──
    components = {
        'hero': bool(re.search(r'(?:hero|banner)', lower)),
        'social_proof': bool(re.search(r'(?:testimonial|review|proof|quote)', lower)),
        'cta_section': total_ctas >= 1,
        'faq': bool(re.search(r'(?:faq|frequently|question)', lower)),
        'pricing': bool(re.search(r'(?:pricing|investment|price|package|tier)', lower)),
        'form': bool(re.search(r'<form|<input', lower)),
    }
    found_components = sum(1 for v in components.values() if v)
    missing = [k for k, v in components.items() if not v]

    if found_components < 3:
        log("CRITICAL", f"Only {found_components}/6 key components found. Missing: {', '.join(missing)}")
    elif missing:
        log("WARNING", f"Missing components: {', '.join(missing)} ({found_components}/6 found)")
    else:
        log("INFO", f"All 6 key components found")

    # ── Responsive design checks ──
    has_media_query = '@media' in lower
    has_flexbox = 'display:flex' in lower.replace(' ', '') or 'display: flex' in lower
    has_grid = 'display:grid' in lower.replace(' ', '') or 'display: grid' in lower

    if not has_media_query:
        log("WARNING", "No @media queries found — may not be responsive")
    if not (has_flexbox or has_grid):
        log("WARNING", "No flexbox or grid layout detected")

    # ── Animation checks ──
    has_animation = '@keyframes' in lower or 'animation:' in lower or 'animation-' in lower
    has_transition = 'transition:' in lower or 'transition-' in lower
    has_reduced_motion = 'prefers-reduced-motion' in lower

    if has_animation or has_transition:
        log("INFO", f"Animations: {'keyframes ' if has_animation else ''}{'transitions' if has_transition else ''}")
        if not has_reduced_motion:
            log("WARNING", "Has animations but missing prefers-reduced-motion media query (accessibility)")
    else:
        log("WARNING", "No animations or transitions — page may feel static")

    # ── Performance checks ──
    reflow_props = re.findall(r'animation[^}]*(?:width|height|top|left|right|bottom|margin|padding)', lower)
    if reflow_props:
        log("WARNING", f"Possible layout-triggering animation detected — prefer transform/opacity")

    # ── Accessibility checks ──
    img_tags = re.findall(r'<img[^>]*>', lower)
    imgs_without_alt = [i for i in img_tags if 'alt=' not in i]
    if imgs_without_alt:
        log("WARNING", f"{len(imgs_without_alt)} <img> tag(s) missing alt attribute")

    aria_count = lower.count('aria-')
    if aria_count == 0 and total_ctas > 0:
        log("WARNING", "No ARIA attributes found — consider adding for interactive elements")

    # ── Copy quality checks ──
    # Check for generic CTA text
    generic_ctas = re.findall(r'>(?:submit|click here|learn more|send)<', lower)
    if generic_ctas:
        log("WARNING", f"Generic CTA text found: {', '.join(set(generic_ctas))} — use action+benefit CTAs")

    # Check for "Lorem ipsum" or placeholder text
    if 'lorem ipsum' in lower or 'placeholder' in lower.split('<style')[0] if '<style' in lower else lower:
        log("CRITICAL", "Placeholder/Lorem ipsum text detected — copy not generated")

    # ── External dependencies ──
    external_deps = re.findall(r'(?:src|href)=["\']https?://[^"\']+', html)
    font_deps = [d for d in external_deps if 'font' in d.lower()]
    other_deps = [d for d in external_deps if 'font' not in d.lower() and 'favicon' not in d.lower()]
    if other_deps:
        log("WARNING", f"{len(other_deps)} external dependencies (non-font) — page should work offline")

    # ────────────────────────────────────────────────
    # Mobile readiness checks (references/mobile-readiness-checklist.md)
    # ────────────────────────────────────────────────
    print(f"\n  ── Mobile readiness ──")

    # Body font-size check (prevent iOS zoom on input focus)
    body_font = re.search(r'body\s*\{[^}]*font-size\s*:\s*(\d+)', lower)
    if body_font:
        body_px = int(body_font.group(1))
        if body_px < 16:
            log("CRITICAL", f"Body font-size {body_px}px < 16px — iOS will auto-zoom on input focus")
        else:
            log("INFO", f"Body font-size: {body_px}px")

    # Mobile-first media query check
    min_width_queries = len(re.findall(r'@media\s*\(min-width', lower))
    max_width_queries = len(re.findall(r'@media\s*\(max-width', lower))
    if max_width_queries > min_width_queries and max_width_queries > 0:
        log("WARNING", f"Uses max-width media queries ({max_width_queries}) more than min-width ({min_width_queries}) — prefer mobile-first")
    elif min_width_queries > 0:
        log("INFO", f"Mobile-first CSS: {min_width_queries} min-width queries")

    # Fluid typography check on display headlines
    h1_style_blocks = re.findall(r'h1\s*\{[^}]+\}|h1[^{]*\{[^}]+font-size[^;}]+[;}]', lower)
    has_clamp_h1 = any('clamp(' in b for b in h1_style_blocks)
    if h1_style_blocks and not has_clamp_h1:
        log("WARNING", "h1 font-size not using clamp() — headlines won't scale fluidly across viewports")

    # Form autocomplete check (CRITICAL for mobile autofill)
    form_blocks = re.findall(r'<form[^>]*>.*?</form>', html, re.DOTALL | re.IGNORECASE)
    if form_blocks:
        for form_idx, form_html in enumerate(form_blocks):
            inputs = re.findall(r'<input[^>]*>', form_html, re.IGNORECASE)
            selects = re.findall(r'<select[^>]*>', form_html, re.IGNORECASE)
            fields = inputs + selects
            fields_without_autocomplete = []
            for f in fields:
                f_lower = f.lower()
                # Skip hidden / submit / button inputs
                if 'type="hidden"' in f_lower or 'type="submit"' in f_lower or 'type="button"' in f_lower:
                    continue
                if 'autocomplete=' not in f_lower:
                    # Extract name attribute for reporting
                    name_match = re.search(r'name\s*=\s*"([^"]+)"', f, re.IGNORECASE)
                    name = name_match.group(1) if name_match else 'unnamed'
                    fields_without_autocomplete.append(name)
            if fields_without_autocomplete:
                log("CRITICAL", f"Form {form_idx+1}: {len(fields_without_autocomplete)} field(s) missing autocomplete attribute ({', '.join(fields_without_autocomplete)}) — mobile autofill will not work")

            # Input type check (email/tel should use correct type)
            for f in inputs:
                f_lower = f.lower()
                name_match = re.search(r'name\s*=\s*"([^"]+)"', f, re.IGNORECASE)
                name = name_match.group(1).lower() if name_match else ''
                if 'email' in name and 'type="email"' not in f_lower:
                    log("WARNING", f"Input named '{name}' should use type=\"email\" for mobile keyboard")
                if 'phone' in name or name == 'tel':
                    if 'type="tel"' not in f_lower:
                        log("WARNING", f"Input named '{name}' should use type=\"tel\" for mobile keyboard")

    # Image loading attributes
    for img in img_tags:
        img_lower = img.lower()
        # Skip hero image (first img) — it shouldn't lazy-load
        is_hero = img_tags.index(img) == 0
        if not is_hero and 'loading=' not in img_lower:
            log("WARNING", "Below-fold <img> missing loading=\"lazy\" — hurts mobile performance")
            break
    imgs_without_dims = [i for i in img_tags if not (re.search(r'\swidth\s*=', i, re.IGNORECASE) and re.search(r'\sheight\s*=', i, re.IGNORECASE))]
    if imgs_without_dims:
        log("WARNING", f"{len(imgs_without_dims)} <img> tag(s) missing width/height attributes — risks CLS on mobile")

    # Placeholder <div> standing in for hero image
    hero_block_match = re.search(r'<section[^>]*hero[^>]*>.*?</section>', html, re.DOTALL | re.IGNORECASE)
    if hero_block_match:
        hero_html = hero_block_match.group(0)
        has_real_img = bool(re.search(r'<img\s', hero_html, re.IGNORECASE))
        has_bg_image = 'background-image' in hero_html.lower() or 'background:url' in hero_html.lower().replace(' ', '')
        placeholder_div = bool(re.search(r'class\s*=\s*"[^"]*(?:placeholder|hero-visual-ph|ph-)', hero_html, re.IGNORECASE))
        if placeholder_div and not (has_real_img or has_bg_image):
            log("WARNING", "Hero section uses placeholder <div> instead of <img>/background-image — flag in notes_for_lovable or replace before delivery")

    # Mobile nav check — if desktop nav exists, must have mobile alternative
    has_nav = bool(re.search(r'<nav[^>]*>', lower))
    if has_nav:
        # Desktop nav typically hidden on mobile via `nav { display:none }` + `@media (min-width: X) { nav { display:flex/block } }`
        nav_hidden_pattern = re.search(r'nav\s*\{[^}]*display\s*:\s*none', lower)
        has_hamburger = bool(re.search(r'(?:hamburger|menu-toggle|mobile-menu|nav-toggle)', lower)) or bool(re.search(r'<button[^>]*aria-expanded[^>]*(?:menu|nav)', lower, re.IGNORECASE))
        has_mobile_sticky = 'mobile-cta' in lower or 'sticky-cta' in lower
        if nav_hidden_pattern and not (has_hamburger or has_mobile_sticky):
            log("WARNING", "Desktop <nav> is hidden on mobile with no hamburger menu or sticky CTA — mobile users stranded")

    # Tap target check on primary CTA buttons (approximate via padding)
    btn_pads = re.findall(r'\.btn\s*\{[^}]*padding\s*:\s*(\d+)px\s+(\d+)px', lower)
    for (v, h) in btn_pads[:1]:  # check first .btn rule
        # estimate effective hit area: padding*2 + text ~14px
        v_total = int(v) * 2 + 14
        if v_total < 40:
            log("WARNING", f"Primary .btn vertical padding {v}px yields ~{v_total}px hit area — below 44px tap target")
        else:
            log("INFO", f"Primary .btn tap area: ~{v_total}px (≥44px required)")

    log("INFO", f"HTML stats: {size_kb:.0f}KB, {section_count} sections, {total_ctas} CTAs, {found_components}/6 components")


# ── Page Spec JSON Validation ──
def validate_spec(path):
    print(f"\n{'='*60}")
    print(f"  Page Spec JSON")
    print(f"{'='*60}")

    if not os.path.exists(path):
        log("INFO", "No page-spec.json provided (optional)")
        return

    try:
        with open(path, 'r', encoding='utf-8') as f:
            spec = json.load(f)
    except json.JSONDecodeError as e:
        log("CRITICAL", f"Invalid JSON: {e}")
        return

    required_keys = ['page_type', 'client_name', 'page_title', 'sections', 'cta_primary']
    missing = [k for k in required_keys if k not in spec]
    if missing:
        log("CRITICAL", f"Missing required keys: {', '.join(missing)}")
    else:
        log("INFO", f"All required keys present")

    # Check page type
    valid_types = ['retreat_booking', 'workshop_event', 'lead_gen', 'teacher_training']
    if 'page_type' in spec and spec['page_type'] not in valid_types:
        log("WARNING", f"Page type '{spec['page_type']}' not in standard types: {', '.join(valid_types)}")

    # Check sections
    if 'sections' in spec:
        section_count = len(spec['sections'])
        page_type = spec.get('page_type', '')
        min_sections = {'retreat_booking': 10, 'workshop_event': 6, 'lead_gen': 4, 'teacher_training': 8}
        expected_min = min_sections.get(page_type, 4)
        if section_count < expected_min:
            log("WARNING", f"Only {section_count} sections for {page_type} (expected {expected_min}+)")
        else:
            log("INFO", f"Sections: {section_count} (min {expected_min} for {page_type})")

    # Check brand
    if 'brand' in spec:
        brand = spec['brand']
        if 'accent_color' not in brand:
            log("WARNING", "No accent_color in brand config")
    else:
        log("WARNING", "No brand config in spec")

    log("INFO", f"Spec: {spec.get('client_name', 'unknown')} / {spec.get('page_type', 'unknown')}")


# ── Main ──
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 validate_output.py <landing-page.html> [page-spec.json]")
        sys.exit(1)

    html_path = sys.argv[1]
    spec_path = sys.argv[2] if len(sys.argv) > 2 else None

    print(f"🔍 Landing Page Builder — Output Validation")
    print(f"   html: {html_path}")
    if spec_path:
        print(f"   spec: {spec_path}")

    validate_html(html_path)
    if spec_path:
        validate_spec(spec_path)

    print(f"\n{'='*60}")
    if critical > 0:
        print(f"  ❌ Validation FAILED — {critical} critical, {warning} warning(s)")
        sys.exit(1)
    else:
        print(f"  ✅ Validation passed — no critical issues ({warning} warning(s))")
        sys.exit(0)
