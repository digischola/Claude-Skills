#!/usr/bin/env python3
"""
Shared dashboard generator for all skills.
Takes an HTML template, populates placeholders with data, applies brand colors.

Usage (CLI):
    python generate_dashboard.py <template_path> <data_json_path> [brand_config_path] [output_path]

Usage (module):
    from generate_dashboard import generate_dashboard
    html = generate_dashboard(template_path, data_dict, brand_config_dict)

Placeholder syntax:
    {{KEY}}           — required, shows [MISSING: KEY] if not in data
    {{KEY|default}}   — optional, falls back to default value
    <!-- {{KEY}} -->  — block placeholder (same replacement rules)

Brand config mapping (brand-config.json key → CSS custom property):
    primary      → --primary          secondary    → --secondary
    dark_bg      → --dark             dark_card    → --dark-card
    dark_surface → --dark-surface     text_color   → --text
    font_family  → --font             font_heading → --font-heading
    Auto-generates: --primary-hover (primary darkened 15%)
"""

import json
import re
import sys
import os

# ── Brand config key → CSS custom property ──────────────────────────────────
BRAND_CSS_MAP = {
    'primary': '--primary',
    'secondary': '--secondary',
    'dark_bg': '--dark',
    'dark_card': '--dark-card',
    'dark_surface': '--dark-surface',
    'text_color': '--text',
    'font_family': '--font',
    'font_heading': '--font-heading',
}

# ── Color utilities ─────────────────────────────────────────────────────────

def darken_hex(hex_color, factor=0.85):
    """Darken a hex color by a factor (0-1). factor=0.85 means 15% darker."""
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 3:
        hex_color = ''.join(c * 2 for c in hex_color)
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    r, g, b = int(r * factor), int(g * factor), int(b * factor)
    return f'#{r:02x}{g:02x}{b:02x}'

def lighten_hex(hex_color, factor=0.15):
    """Lighten a hex color by blending toward white. factor=0.15 means 15% lighter."""
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 3:
        hex_color = ''.join(c * 2 for c in hex_color)
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    r, g, b = int(r + (255 - r) * factor), int(g + (255 - g) * factor), int(b + (255 - b) * factor)
    return f'#{r:02x}{g:02x}{b:02x}'

# ── Placeholder replacement ─────────────────────────────────────────────────

PLACEHOLDER_RE = re.compile(r'\{\{([A-Z_][A-Z0-9_]*?)(?:\|([^}]*))?\}\}')

def replace_placeholders(html, data):
    """
    Replace all {{KEY|default}} placeholders in html using data dict.
    Returns (result_html, warnings_list).
    """
    warnings = []

    def _replace(match):
        key = match.group(1)
        default = match.group(2)  # None if no pipe, '' if empty default
        if key in data:
            return str(data[key])
        if default is not None:
            return default
        warnings.append(f'[MISSING: {key}] — no value in data and no default in template')
        return f'[MISSING: {key}]'

    result = PLACEHOLDER_RE.sub(_replace, html)
    return result, warnings

# ── Brand color injection ───────────────────────────────────────────────────

def build_brand_css(brand_config):
    """
    Convert brand-config.json dict into CSS custom property declarations.
    Auto-generates hover variant for primary color.
    """
    if not brand_config:
        return ''
    lines = []
    for config_key, css_var in BRAND_CSS_MAP.items():
        value = brand_config.get(config_key)
        if value:
            lines.append(f'  {css_var}: {value};')
    # Auto-generate hover variant
    primary = brand_config.get('primary')
    if primary and primary.startswith('#'):
        lines.append(f'  --primary-hover: {darken_hex(primary, 0.85)};')
    if not lines:
        return ''
    return ':root {\n' + '\n'.join(lines) + '\n}'

def apply_brand_colors(html, brand_config):
    """
    Inject brand CSS into the HTML.
    Step 1: Replace brand-related placeholders (PRIMARY_COLOR, DARK_BG, etc.).
    Step 2: Inject a <style>:root { --primary: ...; }</style> block into <head>
            so templates using CSS custom properties (var(--primary)) get branded.
    """
    if not brand_config:
        return html
    # Step 1 — direct placeholder replacement for common brand keys
    brand_placeholders = {
        'PRIMARY_COLOR': brand_config.get('primary', ''),
        'PRIMARY_HOVER': darken_hex(brand_config['primary'], 0.85) if brand_config.get('primary', '').startswith('#') else '',
        'DARK_BG': brand_config.get('dark_bg', ''),
        'DARK_CARD': brand_config.get('dark_card', ''),
        'DARK_SURFACE': brand_config.get('dark_surface', ''),
    }
    brand_data = {k: v for k, v in brand_placeholders.items() if v}
    html, _ = replace_placeholders(html, brand_data)

    # Step 2 — inject CSS custom properties into <head>
    brand_css = build_brand_css(brand_config)
    if brand_css:
        style_block = f'<style id="brand-tokens">\n{brand_css}\n</style>'
        # Inject immediately before </head> so it can override template defaults.
        # Case-insensitive match; preserve original tag casing.
        head_close = re.search(r'</head\s*>', html, flags=re.IGNORECASE)
        if head_close:
            insert_at = head_close.start()
            html = html[:insert_at] + style_block + '\n' + html[insert_at:]
        else:
            # Malformed template with no </head> — prepend so colors still apply.
            html = style_block + '\n' + html
    return html

# ── Main generator ──────────────────────────────────────────────────────────

def generate_dashboard(template_path, data, brand_config=None):
    """
    Generate a final HTML dashboard from template + data + optional brand config.

    Args:
        template_path: Path to HTML template file.
        data: Dict of placeholder key → value.
        brand_config: Optional dict from brand-config.json.

    Returns:
        Final HTML string.
    """
    with open(template_path, 'r', encoding='utf-8') as f:
        html = f.read()

    # Step 1: Apply brand colors (replaces brand-specific placeholders)
    if brand_config:
        html = apply_brand_colors(html, brand_config)

    # Step 2: Replace all remaining placeholders with data
    html, warnings = replace_placeholders(html, data)

    # Step 3: Validate — warn about any remaining placeholders
    remaining = PLACEHOLDER_RE.findall(html)
    if remaining:
        for key, default in remaining:
            warnings.append(f'Unreplaced placeholder after processing: {{{{{key}}}}}')

    if warnings:
        print(f'⚠ Dashboard warnings ({len(warnings)}):', file=sys.stderr)
        for w in warnings:
            print(f'  - {w}', file=sys.stderr)

    return html

# ── CLI entry point ─────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    template_path = sys.argv[1]
    data_json_path = sys.argv[2]
    brand_config_path = sys.argv[3] if len(sys.argv) > 3 else None
    output_path = sys.argv[4] if len(sys.argv) > 4 else None

    # Load data
    with open(data_json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Load brand config
    brand_config = None
    if brand_config_path and os.path.exists(brand_config_path):
        with open(brand_config_path, 'r', encoding='utf-8') as f:
            brand_config = json.load(f)

    # Generate
    result = generate_dashboard(template_path, data, brand_config)
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(result)
        print(f'Dashboard written to {output_path}', file=sys.stderr)
    else:
        print(result)

if __name__ == '__main__':
    main()
