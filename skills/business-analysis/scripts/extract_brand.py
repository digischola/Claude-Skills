#!/usr/bin/env python3
"""
Brand Identity Extractor for Business Analysis Skill

Fetches a client website URL and extracts:
- Primary, secondary, and background colors (from CSS, Tailwind classes, CSS vars)
- Font families (from CSS, Google Fonts, @font-face in external stylesheets)
- Logo URL (from meta tags, og:image, JSON-LD, or common selectors)
- Favicon URL

Key capabilities:
- Fetches and parses EXTERNAL CSS stylesheets (critical for WP/theme-based sites)
- Filters out WordPress default preset colors (present on ALL WP sites)
- Validates Google Fonts imports against actual CSS font-family usage
- Detects @font-face custom fonts from external stylesheets
- Uses HSL saturation for grayscale detection (not naive RGB spread)
- Detects WP-specific brand signals (synced block colors, custom vars, theme.json)

Usage:
    python extract_brand.py https://www.example.com

Output:
    JSON object with extracted brand config to stdout
"""

import sys
import json
import re
import math
from urllib.request import urlopen, Request
from urllib.parse import urljoin
from collections import Counter
from html.parser import HTMLParser


# ──────────────────────────────────────────────────────────────
# Tailwind color palette → hex mapping (v3.x, subset)
# ──────────────────────────────────────────────────────────────
TAILWIND_COLORS = {
    "slate-50": "#f8fafc", "slate-100": "#f1f5f9", "slate-200": "#e2e8f0",
    "slate-300": "#cbd5e8", "slate-400": "#94a3b8", "slate-500": "#64748b",
    "slate-600": "#475569", "slate-700": "#334155", "slate-800": "#1e293b",
    "slate-900": "#0f172a", "slate-950": "#020617",
    "gray-50": "#f9fafb", "gray-100": "#f3f4f6", "gray-200": "#e5e7eb",
    "gray-300": "#d1d5db", "gray-400": "#9ca3af", "gray-500": "#6b7280",
    "gray-600": "#4b5563", "gray-700": "#374151", "gray-800": "#1f2937",
    "gray-900": "#111827", "gray-950": "#030712",
    "zinc-50": "#fafafa", "zinc-100": "#f4f4f5", "zinc-200": "#e4e4e7",
    "zinc-300": "#d4d4d8", "zinc-400": "#a1a1aa", "zinc-500": "#71717a",
    "zinc-600": "#52525b", "zinc-700": "#3f3f46", "zinc-800": "#27272a",
    "zinc-900": "#18181b", "zinc-950": "#09090b",
    "neutral-50": "#fafafa", "neutral-100": "#f5f5f5", "neutral-200": "#e5e5e5",
    "neutral-300": "#d4d4d4", "neutral-400": "#a3a3a3", "neutral-500": "#737373",
    "neutral-600": "#525252", "neutral-700": "#404040", "neutral-800": "#262626",
    "neutral-900": "#171717", "neutral-950": "#0a0a0a",
    "red-500": "#ef4444", "red-600": "#dc2626", "red-700": "#b91c1c",
    "orange-500": "#f97316", "orange-600": "#ea580c",
    "amber-500": "#f59e0b", "amber-600": "#d97706",
    "green-500": "#22c55e", "green-600": "#16a34a",
    "blue-500": "#3b82f6", "blue-600": "#2563eb",
    "indigo-500": "#6366f1", "indigo-600": "#4f46e5",
    "purple-500": "#a855f7", "purple-600": "#9333ea",
    "pink-500": "#ec4899", "pink-600": "#db2777",
}

TAILWIND_COLOR_PREFIXES = [
    "bg-", "text-", "border-", "ring-", "from-", "to-", "via-",
    "hover:bg-", "hover:text-", "hover:border-",
    "focus:bg-", "focus:text-", "focus:ring-",
    "dark:bg-", "dark:text-",
]

# ──────────────────────────────────────────────────────────────
# WordPress Default Preset Colors — present on EVERY WP site.
# Source: WordPress core wp-includes/theme.json (Gutenberg defaults)
# ──────────────────────────────────────────────────────────────
WP_PRESET_COLORS = {
    "#000000", "#ffffff", "#1e1e1e",
    "#cf2e2e",  # vivid-red
    "#ff6900",  # luminous-vivid-orange
    "#fcb900",  # luminous-vivid-amber
    "#7bdcb5",  # light-green-cyan
    "#00d084",  # vivid-green-cyan
    "#8ed1fc",  # pale-cyan-blue
    "#0693e3",  # vivid-cyan-blue
    "#9b51e0",  # vivid-purple
    "#abb8c3",  # cyan-bluish-gray
    "#eb6eb7",  # vivid-pink
    "#f78da7",  # pale-pink
}

WP_PRESET_VAR_PATTERN = re.compile(
    r'--wp--preset--(?:color|gradient|font-size|spacing)', re.IGNORECASE
)

WP_BRAND_VAR_PATTERNS = [
    re.compile(r'--wp-block-synced-color', re.IGNORECASE),
    re.compile(r'--wp--custom--[\w-]*color[\w-]*', re.IGNORECASE),
    re.compile(r'--wp--custom--[\w-]*accent[\w-]*', re.IGNORECASE),
    re.compile(r'--wp--custom--[\w-]*brand[\w-]*', re.IGNORECASE),
    re.compile(r'--theme-[\w-]*color[\w-]*', re.IGNORECASE),
    re.compile(r'--primary[\w-]*', re.IGNORECASE),
    re.compile(r'--accent[\w-]*', re.IGNORECASE),
    re.compile(r'--brand[\w-]*', re.IGNORECASE),
]

# ──────────────────────────────────────────────────────────────
# Common Utility/Status Colors — used for error/success/warning/info states.
# Present on millions of sites via Material Design, Bootstrap, etc.
# NOT brand colors — filter from brand extraction results.
# ──────────────────────────────────────────────────────────────
UTILITY_STATUS_COLORS = {
    # Material Design status colors
    "#f44336",  # MD Red 500
    "#e53935",  # MD Red 600
    "#d32f2f",  # MD Red 700
    "#c62828",  # MD Red 800
    "#b71c1c",  # MD Red 900
    "#ff5252",  # MD Red A200
    "#ff1744",  # MD Red A400
    "#4caf50",  # MD Green 500
    "#43a047",  # MD Green 600
    "#388e3c",  # MD Green 700
    "#2e7d32",  # MD Green 800
    "#66bb6a",  # MD Green 400
    "#81c784",  # MD Green 300
    "#ff9800",  # MD Orange 500 (warning)
    "#fb8c00",  # MD Orange 600
    "#f57c00",  # MD Orange 700
    "#ef6c00",  # MD Orange 800
    "#2196f3",  # MD Blue 500 (info)
    "#1e88e5",  # MD Blue 600
    "#1976d2",  # MD Blue 700
    "#ff5722",  # MD Deep Orange 500
    "#ff6f00",  # MD Amber 900
    # Bootstrap status colors
    "#dc3545",  # Bootstrap danger
    "#28a745",  # Bootstrap success
    "#ffc107",  # Bootstrap warning
    "#17a2b8",  # Bootstrap info
    "#007bff",  # Bootstrap primary (generic blue)
    "#6c757d",  # Bootstrap secondary (gray)
    "#fd7e14",  # Bootstrap orange
    "#20c997",  # Bootstrap teal
    # Common alert/notification colors
    "#ff0000",  # pure red
    "#00ff00",  # pure green
    "#cc0000",  # dark red
    "#008000",  # dark green
    "#ff3333",  # error red
    "#33cc33",  # success green
}

# CSS variable names that indicate utility/status usage (not brand)
UTILITY_VAR_NAMES = {
    "--red", "--green", "--blue", "--error", "--success", "--warning",
    "--info", "--danger", "--alert", "--valid", "--invalid",
    "--error-color", "--success-color", "--warning-color", "--info-color",
    "--danger-color", "--alert-color", "--text-dark", "--text-muted",
    "--text-light", "--white", "--black",
}

# ──────────────────────────────────────────────────────────────
# Platform Default Colors — framework/builder defaults, NOT brand choices.
# Similar to WP_PRESET_COLORS but for non-WordPress platforms.
# ──────────────────────────────────────────────────────────────
PLATFORM_DEFAULT_COLORS = {
    # Webflow defaults
    "#3898ec",  # Webflow default link blue
    "#2895f7",  # Webflow link blue variant
    "#0082f3",  # Webflow focus/interactive blue
    "#1a1b1f",  # Webflow default dark text
    "#f5f5f5",  # Webflow default light bg
    "#36a7ff",  # Webflow hover blue variant
    # Squarespace defaults
    "#2b2b2b",  # Squarespace default dark
    # Wix defaults
    "#116dff",  # Wix default blue
    "#3899ec",  # Wix editor blue (nearly identical to Webflow)
    # Shopify defaults
    "#008060",  # Shopify green
    "#004c3f",  # Shopify dark green
}

# CSS selectors that indicate a color is a platform default, not brand
PLATFORM_DEFAULT_SELECTORS = {
    ".w-", "w-button", "w-nav", "w-input", "w-select",  # Webflow
    ".sqs-", ".sqsp-",  # Squarespace
    ".wix-", "._",  # Wix
}

# Generic font names to filter out when looking for brand-specific fonts
# ──────────────────────────────────────────────────────────────
# Prominent CSS selectors — colors used on these are likely brand, not utility.
# If a color would be filtered as utility but appears on these selectors,
# it gets rescued as a brand candidate.
# ──────────────────────────────────────────────────────────────
PROMINENT_SELECTORS = {
    # Layout/structural
    'body', 'html', 'header', 'footer', 'nav', 'main', 'aside',
    # Headings
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    # Links and buttons
    'a', 'button', '.btn', '.button', '.cta',
    # Common brand areas
    '.hero', '.banner', '.header', '.navbar', '.nav', '.logo', '.brand',
    '.site-header', '.site-footer', '.site-title', '.site-nav',
    '.menu', '.main-menu', '.primary-menu',
    # WP-specific prominent areas
    '.entry-title', '.page-title', '.site-branding',
    '.wp-block-heading', '.wp-block-cover',
}

# Minimum number of prominent selector hits to rescue a utility color
PROMINENCE_THRESHOLD = 2

GENERIC_FONTS = {
    "sans-serif", "serif", "monospace", "cursive", "fantasy",
    "system-ui", "-apple-system", "blinkmacsystemfont", "ui-sans-serif",
    "ui-serif", "ui-monospace", "segoe ui", "roboto", "helvetica neue",
    "arial", "noto sans", "liberation sans", "helvetica", "oxygen",
    "ubuntu", "cantarell", "fira sans", "droid sans", "apple color emoji",
    "segoe ui emoji", "segoe ui symbol", "noto color emoji",
    "inherit", "initial", "unset", "var(--ff-base)", "var(--ff-heading)",
}

# Icon font libraries — NOT text fonts, must be excluded
ICON_FONTS = {
    "icomoon", "fontawesome", "font awesome", "fa-solid", "fa-regular",
    "fa-brands", "material icons", "material symbols", "dashicons",
    "genericons", "wp-block-library", "eleganticons", "etline",
    "themify", "linearicons", "simple-line-icons", "ionicons",
    "typicons", "entypo", "feather", "glyphicons",
    "webflow-icons", "bootstrap-icons", "boxicons", "remixicon",
    "phosphor", "tabler-icons", "lucide", "heroicons",
    "swiper-icons", "slick", "owl-icons", "flickity-icons",
}


# ══════════════════════════════════════════════════════════════
# Color utilities — HSL-based grayscale detection
# ══════════════════════════════════════════════════════════════

def normalize_hex(color):
    color = color.lower().strip()
    if len(color) == 4:
        color = f"#{color[1]*2}{color[2]*2}{color[3]*2}"
    return color


def hex_to_hsl(hex_color):
    """Convert hex to HSL. Returns (h: 0-360, s: 0-100, l: 0-100)."""
    hex_color = normalize_hex(hex_color)
    try:
        r = int(hex_color[1:3], 16) / 255
        g = int(hex_color[3:5], 16) / 255
        b = int(hex_color[5:7], 16) / 255
    except (ValueError, IndexError):
        return (0, 0, 50)

    mx = max(r, g, b)
    mn = min(r, g, b)
    l = (mx + mn) / 2

    if mx == mn:
        h = s = 0
    else:
        d = mx - mn
        s = d / (2 - mx - mn) if l > 0.5 else d / (mx + mn)
        if mx == r:
            h = (g - b) / d + (6 if g < b else 0)
        elif mx == g:
            h = (b - r) / d + 2
        else:
            h = (r - g) / d + 4
        h /= 6

    return (round(h * 360), round(s * 100, 1), round(l * 100, 1))


def is_grayscale(hex_color):
    """Use HSL saturation. S < 10% = grayscale."""
    _, s, _ = hex_to_hsl(hex_color)
    return s < 10


def get_luminance(hex_color):
    hex_color = normalize_hex(hex_color)
    try:
        r = int(hex_color[1:3], 16) / 255
        g = int(hex_color[3:5], 16) / 255
        b = int(hex_color[5:7], 16) / 255
        return 0.299 * r + 0.587 * g + 0.114 * b
    except (ValueError, IndexError):
        return 0.5


# ══════════════════════════════════════════════════════════════
# HTTP fetch helper
# ══════════════════════════════════════════════════════════════

def fetch_url(url, timeout=10, max_bytes=500_000):
    """Fetch a URL with size limit. Returns str or None."""
    headers = {"User-Agent": "Mozilla/5.0 (compatible; BrandExtractor/1.0)"}
    try:
        req = Request(url, headers=headers)
        with urlopen(req, timeout=timeout) as resp:
            data = resp.read(max_bytes)
            return data.decode("utf-8", errors="replace")
    except Exception:
        return None


# ══════════════════════════════════════════════════════════════
# HTML Parser
# ══════════════════════════════════════════════════════════════

class BrandExtractor(HTMLParser):
    def __init__(self, base_url):
        super().__init__()
        self.base_url = base_url
        # Colors
        self.colors = []               # (source, hex_color)
        self.tailwind_colors = []      # (prefix, color_name, hex_color)
        self.wp_brand_colors = []      # (var_name, hex_color)
        self.wp_preset_colors_found = []
        # Fonts
        self.fonts = []                # individual font names from font-family rules
        self.css_font_families = []    # raw font-family declaration strings
        self.font_face_fonts = []      # fonts from @font-face declarations
        self.tailwind_fonts = []
        self.google_fonts = []
        # Assets
        self.logo_url = None
        self.favicon_url = None
        self.og_image = None
        self.json_ld_logo = None
        self.json_ld_data = []
        # State
        self.in_style = False
        self.style_content = ""
        self._in_json_ld = False
        self._json_ld_content = ""
        self.all_classes = []
        self.is_wordpress = False
        self.is_webflow = False
        self.is_squarespace = False
        self.is_wix = False
        # External stylesheets to fetch
        self.stylesheet_urls = []
        # Prominence tracking: maps hex_color → set of selectors it appears on
        self.color_selectors = {}  # {hex_color: {selector1, selector2, ...}}
        # Accent vs text usage tracking
        self.accent_usage = Counter()  # colors used in background-color, border, etc.
        self.text_usage = Counter()    # colors used in color: property
        # Rescued utility colors — would have been filtered but appear on prominent selectors
        self.rescued_utility_colors = []  # (var_name_or_source, hex_color, prominent_selectors)

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)

        # Collect classes for Tailwind detection
        if "class" in attrs_dict:
            self.all_classes.append(attrs_dict["class"])
            cls_lower = attrs_dict["class"].lower()
            if any(sig in cls_lower for sig in ["wp-", "wordpress", "elementor", "woocommerce"]):
                self.is_wordpress = True
            if any(sig in cls_lower for sig in ["w-layout", "w-nav", "w-container", "w-button"]):
                self.is_webflow = True
            if any(sig in cls_lower for sig in ["sqs-", "sqsp-"]):
                self.is_squarespace = True

        if tag == "meta":
            prop = attrs_dict.get("property", "") or attrs_dict.get("name", "")
            content = attrs_dict.get("content", "")
            if prop in ("og:image", "twitter:image") and content:
                self.og_image = urljoin(self.base_url, content)
            if prop == "theme-color" and content:
                self.colors.append(("theme-color", content.strip()))
            if attrs_dict.get("name", "") == "generator" and "wordpress" in content.lower():
                self.is_wordpress = True

        if tag == "link":
            rel = attrs_dict.get("rel", "")
            href = attrs_dict.get("href", "")
            if "icon" in rel and href:
                self.favicon_url = urljoin(self.base_url, href)
            if "stylesheet" in rel and href:
                full_url = urljoin(self.base_url, href)
                if "fonts.googleapis.com" in href:
                    self.google_fonts.append(href)
                else:
                    self.stylesheet_urls.append(full_url)
            if href and "/wp-content/" in href:
                self.is_wordpress = True
            if href and "website-files.com" in href:
                self.is_webflow = True

        if tag == "style":
            self.in_style = True
            self.style_content = ""

        if tag == "script":
            if attrs_dict.get("type", "") == "application/ld+json":
                self._in_json_ld = True
                self._json_ld_content = ""

        if tag == "img":
            src = attrs_dict.get("src", "")
            alt = attrs_dict.get("alt", "").lower()
            cls = attrs_dict.get("class", "").lower()
            if any(kw in alt + cls for kw in ["logo", "brand", "site-logo"]):
                self.logo_url = urljoin(self.base_url, src)

    def handle_data(self, data):
        if self.in_style:
            self.style_content += data
        if self._in_json_ld:
            self._json_ld_content += data

    def handle_endtag(self, tag):
        if tag == "style" and self.in_style:
            self.in_style = False
            self._parse_css(self.style_content)
        if tag == "script" and self._in_json_ld:
            self._in_json_ld = False
            self._parse_json_ld(self._json_ld_content)

    def _parse_json_ld(self, content):
        """Extract logo from JSON-LD structured data. Handles @graph arrays."""
        try:
            data = json.loads(content)
            self.json_ld_data.append(data)
            items = []
            if isinstance(data, list):
                items = data
            elif isinstance(data, dict):
                items = [data]
                if "@graph" in data and isinstance(data["@graph"], list):
                    items.extend(data["@graph"])
            for item in items:
                if not isinstance(item, dict):
                    continue
                logo = item.get("logo")
                if isinstance(logo, str) and logo:
                    self.json_ld_logo = urljoin(self.base_url, logo)
                elif isinstance(logo, dict):
                    logo_url = logo.get("url") or logo.get("contentUrl")
                    if logo_url:
                        self.json_ld_logo = urljoin(self.base_url, logo_url)
                if item.get("@type") == "Organization" and not self.json_ld_logo:
                    img = item.get("image")
                    if isinstance(img, str) and img:
                        self.json_ld_logo = urljoin(self.base_url, img)
                    elif isinstance(img, dict):
                        img_url = img.get("url") or img.get("contentUrl")
                        if img_url:
                            self.json_ld_logo = urljoin(self.base_url, img_url)
        except (json.JSONDecodeError, TypeError):
            pass

    def _build_color_selector_map(self, css):
        """Build a mapping of hex colors to the CSS selectors they appear in.
        Also tracks which CSS properties use each color (color vs background-color).
        Used for prominence-based rescue and accent vs text detection."""
        # Parse CSS rule blocks: selector { ... properties ... }
        # Simple regex — handles most cases, not a full CSS parser
        rule_pattern = re.compile(r'([^{}]+?)\{([^{}]+)\}', re.DOTALL)
        for match in rule_pattern.finditer(css):
            selector_str = match.group(1).strip().lower()
            properties = match.group(2)

            # Extract selectors (split by comma for grouped selectors)
            selectors = [s.strip() for s in selector_str.split(',')]

            # Find all hex colors in these properties
            hex_colors = re.findall(r'#(?:[0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b', properties)

            for c in hex_colors:
                c_lower = normalize_hex(c)
                if c_lower not in self.color_selectors:
                    self.color_selectors[c_lower] = set()
                for sel in selectors:
                    self.color_selectors[c_lower].add(sel)

            # Track accent usage: background-color, border-color, background
            # vs text usage: color (without prefix)
            accent_props = re.findall(
                r'(?:background-color|background|border-color|border|outline-color|box-shadow)\s*:\s*[^;]*'
                r'(#(?:[0-9a-fA-F]{6}|[0-9a-fA-F]{3}))\b',
                properties, re.IGNORECASE
            )
            text_props = re.findall(
                r'(?<![a-z-])color\s*:\s*[^;]*(#(?:[0-9a-fA-F]{6}|[0-9a-fA-F]{3}))\b',
                properties, re.IGNORECASE
            )
            for c in accent_props:
                c_lower = normalize_hex(c)
                if not hasattr(self, 'accent_usage'):
                    self.accent_usage = Counter()
                self.accent_usage[c_lower] += 1
            for c in text_props:
                c_lower = normalize_hex(c)
                if not hasattr(self, 'text_usage'):
                    self.text_usage = Counter()
                self.text_usage[c_lower] += 1

    def _check_prominence(self, hex_color):
        """Check if a color is used on prominent selectors.
        Returns list of matching prominent selectors, or empty list."""
        selectors = self.color_selectors.get(hex_color, set())
        prominent_hits = []
        for sel in selectors:
            for prom in PROMINENT_SELECTORS:
                # Check if the prominent selector appears in the CSS selector
                # e.g., ".site-header .logo" contains ".logo"
                if prom in sel:
                    prominent_hits.append(sel)
                    break
        return prominent_hits

    def _parse_css(self, css):
        """Parse CSS content for colors, fonts, and @font-face declarations."""
        # Detect WP via CSS content
        if '--wp--preset--' in css or 'wp-block' in css:
            self.is_wordpress = True

        # Build color-to-selector map for prominence checking
        self._build_color_selector_map(css)

        # ── @font-face: extract custom font names ──
        font_face_blocks = re.findall(
            r'@font-face\s*\{([^}]+)\}', css, re.IGNORECASE | re.DOTALL
        )
        for block in font_face_blocks:
            ff_match = re.search(r'font-family\s*:\s*([^;]+)', block)
            if ff_match:
                name = ff_match.group(1).strip().strip("'\"")
                if name and name.lower() not in GENERIC_FONTS:
                    self.font_face_fonts.append(name)

        # ── CSS variable declarations ──
        all_css_vars = re.findall(r'(--[\w-]+)\s*:\s*([^;}{]+)', css)
        for var_name, var_value in all_css_vars:
            var_value = var_value.strip()
            hex_match = re.match(r'(#(?:[0-9a-fA-F]{6}|[0-9a-fA-F]{3}))\b', var_value)
            if not hex_match:
                continue
            hex_color = hex_match.group(1).lower()

            if WP_PRESET_VAR_PATTERN.match(var_name):
                self.wp_preset_colors_found.append((var_name, hex_color))
                continue

            is_brand_var = False
            for pattern in WP_BRAND_VAR_PATTERNS:
                if pattern.match(var_name):
                    self.wp_brand_colors.append((var_name, hex_color))
                    is_brand_var = True
                    break
            if not is_brand_var:
                vn = var_name.lower()

                # Check utility/status variable names (--red, --error, etc.)
                # BUT rescue if the color appears on prominent selectors
                is_utility_var = vn in UTILITY_VAR_NAMES
                is_utility_color = hex_color in UTILITY_STATUS_COLORS

                if is_utility_var or is_utility_color:
                    prominent_hits = self._check_prominence(hex_color)
                    if len(prominent_hits) >= PROMINENCE_THRESHOLD:
                        # Color is used prominently — likely a real brand color
                        # despite the generic variable name or matching a utility hex
                        self.rescued_utility_colors.append(
                            (var_name, hex_color, prominent_hits[:5])
                        )
                        self.colors.append(("css-var-rescued", hex_color))
                    # Either way, skip normal processing for utility matches
                    continue

                # Capture CSS vars that are likely brand colors:
                # 1. Names containing color-related keywords
                # 2. Names that ARE color names (--navy, --gold, etc.)
                # 3. Names containing common brand-palette terms (--cream, --sand, etc.)
                color_keywords = [
                    'color', 'bg', 'primary', 'secondary', 'accent', 'brand',
                    'background', 'foreground', 'surface', 'highlight', 'hover',
                ]
                color_names = [
                    'red', 'blue', 'green', 'yellow', 'orange', 'purple', 'pink',
                    'violet', 'indigo', 'teal', 'cyan', 'magenta', 'coral', 'salmon',
                    'navy', 'gold', 'cream', 'sand', 'forest', 'sky', 'rose',
                    'crimson', 'scarlet', 'maroon', 'burgundy', 'olive', 'lime',
                    'aqua', 'mint', 'peach', 'ivory', 'charcoal', 'slate',
                    'saffron', 'amber', 'rust', 'wine', 'plum', 'sage',
                ]
                has_keyword = any(kw in vn for kw in color_keywords)
                is_color_name = any(vn == f'--{cn}' or vn.startswith(f'--{cn}-')
                                    or vn.endswith(f'-{cn}') for cn in color_names)
                if has_keyword or is_color_name:
                    self.colors.append(("css-var", hex_color))

        # ── Inline hex colors (outside CSS variable declarations) ──
        css_no_vars = re.sub(r'--[\w-]+\s*:\s*[^;}{]+', '', css)
        # Also strip @font-face blocks to avoid counting font URLs as colors
        css_no_vars = re.sub(r'@font-face\s*\{[^}]+\}', '', css_no_vars, flags=re.DOTALL)
        hex_colors = re.findall(r'#(?:[0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b', css_no_vars)
        for c in hex_colors:
            c_lower = c.lower()
            if self.is_wordpress and c_lower in WP_PRESET_COLORS:
                self.wp_preset_colors_found.append(("inline", c_lower))
                continue
            if c_lower in UTILITY_STATUS_COLORS:
                prominent_hits = self._check_prominence(c_lower)
                if len(prominent_hits) >= PROMINENCE_THRESHOLD:
                    self.rescued_utility_colors.append(
                        ("inline-css", c_lower, prominent_hits[:5])
                    )
                    self.colors.append(("css-hex-rescued", c_lower))
                continue
            self.colors.append(("css-hex", c))

        # ── RGB/RGBA colors ──
        rgb_colors = re.findall(r'rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)', css_no_vars)
        for r, g, b in rgb_colors:
            hex_c = f"#{int(r):02x}{int(g):02x}{int(b):02x}"
            if self.is_wordpress and hex_c in WP_PRESET_COLORS:
                continue
            self.colors.append(("css-rgb", hex_c))

        # ── Font-family from CSS rules (not @font-face) ──
        # Remove @font-face blocks first so we only get actual usage rules
        css_no_fontface = re.sub(r'@font-face\s*\{[^}]+\}', '', css, flags=re.DOTALL)
        font_matches = re.findall(r'font-family\s*:\s*([^;}{]+)', css_no_fontface)
        for fm in font_matches:
            fonts = [f.strip().strip("'\"") for f in fm.split(",")]
            self.fonts.extend(fonts)
            self.css_font_families.append(fm.strip())

        # ── WP font-family CSS variables ──
        wp_font_vars = re.findall(
            r'--wp--preset--font-family--[\w-]+\s*:\s*([^;}{]+)', css
        )
        for fm in wp_font_vars:
            fm = fm.strip()
            fonts = [f.strip().strip("'\"") for f in fm.split(",")]
            self.fonts.extend(fonts)
            self.css_font_families.append(fm)

    def fetch_external_css(self, max_sheets=10):
        """Fetch and parse external CSS stylesheets.
        Prioritizes theme/custom CSS over vendor/plugin CSS."""
        # Sort: theme CSS first, then custom, then plugins
        def priority(url):
            url_lower = url.lower()
            if '/theme' in url_lower or 'style.css' in url_lower:
                return 0  # theme CSS — highest priority
            if 'custom' in url_lower or 'main' in url_lower or 'global' in url_lower:
                return 1
            if '/plugin' in url_lower or '/elementor/' in url_lower:
                return 2
            return 1

        sorted_urls = sorted(self.stylesheet_urls, key=priority)
        fetched = 0
        fetched_urls = []

        for css_url in sorted_urls[:max_sheets]:
            css_text = fetch_url(css_url, timeout=8, max_bytes=500_000)
            if css_text:
                self._parse_css(css_text)
                fetched += 1
                fetched_urls.append(css_url)

                # Also follow @import rules in the CSS
                imports = re.findall(r'@import\s+(?:url\(["\']?([^"\')\s]+)["\']?\)|["\']([^"\']+)["\'])', css_text)
                for imp1, imp2 in imports[:3]:
                    imp_url = urljoin(css_url, imp1 or imp2)
                    imp_css = fetch_url(imp_url, timeout=5, max_bytes=300_000)
                    if imp_css:
                        self._parse_css(imp_css)
                        fetched += 1

        return fetched, fetched_urls

    def extract_tailwind(self):
        """Parse collected class attributes for Tailwind utility classes."""
        all_class_str = " ".join(self.all_classes)
        classes = all_class_str.split()
        for cls in classes:
            for prefix in TAILWIND_COLOR_PREFIXES:
                if cls.startswith(prefix):
                    color_part = cls[len(prefix):]
                    if color_part in TAILWIND_COLORS:
                        self.tailwind_colors.append(
                            (prefix.rstrip("-:"), color_part, TAILWIND_COLORS[color_part])
                        )
            if cls.startswith("font-"):
                font_name = cls[5:]
                if font_name in ("sans", "serif", "mono"):
                    self.tailwind_fonts.append(font_name)

    def _parse_google_fonts_url(self, url):
        families = []
        matches = re.findall(r'family=([^&:]+)', url)
        for m in matches:
            name = m.replace("+", " ").split(":")[0]
            families.append(name)
        return families


# ══════════════════════════════════════════════════════════════
# Main extraction
# ══════════════════════════════════════════════════════════════

def extract_brand(url):
    """Main extraction function."""
    html = fetch_url(url, timeout=15, max_bytes=2_000_000)
    if not html:
        return {
            "error": f"Could not fetch {url}",
            "warnings": ["FETCH_FAILED: Could not load the website."],
            "businessName": "", "colors": {}, "fontFamily": "",
            "logoUrl": None, "faviconUrl": None,
            "extraction_method": "none", "confidence": "NONE"
        }

    parser = BrandExtractor(url)
    parser.feed(html)
    parser.extract_tailwind()

    # ── Fetch external CSS stylesheets (the critical step for WP/theme sites) ──
    ext_css_count, ext_css_urls = parser.fetch_external_css(max_sheets=10)

    warnings = []
    extraction_method = []

    if ext_css_count > 0:
        extraction_method.append(f"external-css({ext_css_count})")

    # ══════════════════════════════════════
    # COLOR EXTRACTION (priority order)
    # ══════════════════════════════════════

    primary = None
    secondary = None
    background = None
    light_background = None
    dark_text = None
    light_text = None
    accent_colors = []  # collect all non-gray, non-preset colors with counts

    # Step 1: Tailwind classes
    if parser.tailwind_colors:
        extraction_method.append("tailwind")
        tw_counts = Counter()
        for prefix, color_name, hex_val in parser.tailwind_colors:
            tw_counts[color_name] += 1
        chromatic_tw = [(name, count) for name, count in tw_counts.most_common()
                        if not is_grayscale(TAILWIND_COLORS[name])]
        if chromatic_tw:
            primary = TAILWIND_COLORS[chromatic_tw[0][0]]
            if len(chromatic_tw) > 1:
                secondary = TAILWIND_COLORS[chromatic_tw[1][0]]

    # Step 2: WP brand-specific CSS variables (LOWER priority than theme CSS)
    # --wp-block-synced-color is a Gutenberg editor accent, not necessarily the brand primary.
    # Add as accent candidates but don't force as primary — let theme CSS colors win.
    if parser.wp_brand_colors:
        extraction_method.append("wp-brand-vars")
        chromatic_wp = [(name, normalize_hex(c)) for name, c in parser.wp_brand_colors
                        if not is_grayscale(c)]
        for name, c in chromatic_wp:
            accent_colors.append(("wp-brand", c))

    # Step 3: All CSS colors (inline + external, platform defaults filtered)
    css_colors = [(normalize_hex(c), src) for src, c in parser.colors if c.startswith("#")]
    if parser.is_wordpress:
        css_colors = [(c, src) for c, src in css_colors if c not in WP_PRESET_COLORS]

    # Filter platform defaults (Webflow blue, Squarespace dark, etc.)
    is_any_platform = parser.is_webflow or parser.is_squarespace or parser.is_wix
    platform_filtered = []
    if is_any_platform:
        css_colors_clean = []
        for c, src in css_colors:
            if c in PLATFORM_DEFAULT_COLORS:
                platform_filtered.append(c)
            else:
                css_colors_clean.append((c, src))
        css_colors = css_colors_clean

    if css_colors:
        extraction_method.append("css")
        chromatic_css = [c for c, _ in css_colors if not is_grayscale(c)]
        grayscale_css = [c for c, _ in css_colors if is_grayscale(c)]

        chromatic_counts = Counter(chromatic_css)
        grayscale_counts = Counter(grayscale_css)

        # Add all chromatic colors as accent candidates
        for color, count in chromatic_counts.most_common(20):
            accent_colors.append(("css", color))

        # ── Prominence-weighted ranking ──
        # Score = frequency + (3 × prominent selector hits) + (5 × accent usage) - (2 × text-only usage)
        # Accent usage = background-color, border-color, etc. → strong brand signal
        # Text-only colors (body text, paragraph text) are structural, not brand accent
        def prominence_score(color):
            freq = chromatic_counts.get(color, 0)
            prominent_hits = len(parser._check_prominence(color))
            accent_count = parser.accent_usage.get(color, 0)
            text_count = parser.text_usage.get(color, 0)
            # Boost accent colors, demote text-only colors
            accent_bonus = accent_count * 5
            text_penalty = text_count * 2 if accent_count == 0 else 0  # Only penalize if ONLY used as text
            return freq + (prominent_hits * 3) + accent_bonus - text_penalty

        if not primary and chromatic_counts:
            ranked = sorted(chromatic_counts.keys(), key=prominence_score, reverse=True)
            primary = ranked[0]
            # Secondary must be a different hue family (>30° apart)
            if len(ranked) > 1 and not secondary:
                h1, _, _ = hex_to_hsl(primary)
                for candidate in ranked[1:]:
                    h2, _, _ = hex_to_hsl(candidate)
                    hue_diff = min(abs(h1 - h2), 360 - abs(h1 - h2))
                    if hue_diff > 30:
                        secondary = candidate
                        break
                # Fallback: if all same hue family, pick the next most prominent
                if not secondary:
                    secondary = ranked[1]

        if not background and grayscale_counts:
            darkest = min(grayscale_counts.keys(), key=get_luminance)
            if get_luminance(darkest) < 0.3:
                background = darkest
            # Also find the lightest grayscale as background color
            lightest = max(grayscale_counts.keys(), key=get_luminance)
            if get_luminance(lightest) > 0.8:
                light_background = lightest

    # Step 4: Theme-color meta tag
    theme_colors = [normalize_hex(c) for src, c in parser.colors if src == "theme-color"]
    if theme_colors:
        extraction_method.append("meta-theme")
        if not primary:
            primary = theme_colors[0]

    # ── Determine primary/secondary from all accent candidates ──
    # Count unique chromatic colors across all sources
    if accent_colors and (not primary or not secondary):
        accent_counts = Counter(c for _, c in accent_colors)
        sorted_accents = accent_counts.most_common()
        if not primary and sorted_accents:
            primary = sorted_accents[0][0]
        if not secondary:
            # Secondary should be a different color family from primary
            for color, count in sorted_accents:
                if color != primary:
                    secondary = color
                    break

    # ══════════════════════════════════════
    # FONT EXTRACTION
    # ══════════════════════════════════════
    font_family = None
    font_secondary = None
    font_warnings = []

    # Step 1: @font-face custom fonts (HIGHEST signal — site explicitly loads them)
    if parser.font_face_fonts:
        # Normalize font names: "Gilroy-Bold" → "Gilroy", "Gilroy-Medium" → "Gilroy"
        # Group by base family name (strip weight/style suffixes)
        weight_suffixes = re.compile(
            r'[-\s]?(thin|extralight|ultralight|light|regular|normal|book|'
            r'medium|semibold|demibold|bold|extrabold|ultrabold|black|heavy|'
            r'italic|oblique|condensed|expanded|narrow|wide)$',
            re.IGNORECASE
        )
        def is_icon_font(name):
            """Check if a font name is an icon font (supports partial matching)."""
            n = name.lower()
            if n in ICON_FONTS:
                return True
            # Partial match for versioned names like "Font Awesome 6 Brands"
            for icon in ICON_FONTS:
                if icon in n or n in icon:
                    return True
            return False

        base_names = {}  # lowercase_base → original_first_seen
        for f in parser.font_face_fonts:
            f_lower = f.lower()
            if f_lower in GENERIC_FONTS or is_icon_font(f):
                continue
            base = weight_suffixes.sub('', f).strip(' -')
            base_lower = base.lower()
            if is_icon_font(base):
                continue
            if base_lower not in base_names:
                base_names[base_lower] = base

        # Deduplicate while preserving order
        seen = set()
        unique_ff = []
        for base_lower, base_name in base_names.items():
            if base_lower not in seen and base_lower not in GENERIC_FONTS:
                seen.add(base_lower)
                unique_ff.append(base_name)

        if unique_ff:
            # Check which @font-face fonts are actually USED in CSS rules
            all_css_fonts_lower = " ".join(parser.css_font_families).lower()
            used_ff = [f for f in unique_ff if f.lower() in all_css_fonts_lower]

            if used_ff:
                font_family = used_ff[0]
                if len(used_ff) > 1:
                    font_secondary = used_ff[1]
                extraction_method.append("font-face-validated")
            else:
                # @font-face defined but not referenced in CSS rules we found
                # Still report them — they're loaded for a reason
                font_family = unique_ff[0]
                if len(unique_ff) > 1:
                    font_secondary = unique_ff[1]
                extraction_method.append("font-face")
                font_warnings.append(
                    f"FONT_FACE_UNVALIDATED: {', '.join(unique_ff[:3])} loaded via @font-face "
                    f"but not found in CSS font-family rules we parsed. May be used via JS or "
                    f"external CSS we didn't fetch."
                )

    # Step 2: Google Fonts — validate against CSS usage
    google_font_names = []
    for gf_url in parser.google_fonts:
        families = parser._parse_google_fonts_url(gf_url)
        google_font_names.extend(families)

    validated_google_fonts = []
    if google_font_names:
        all_css_fonts_lower = " ".join(parser.css_font_families).lower()
        for gf_name in google_font_names:
            if gf_name.lower() in all_css_fonts_lower:
                validated_google_fonts.append(gf_name)

        if validated_google_fonts:
            if not font_family:
                font_family = validated_google_fonts[0]
            if not font_secondary and len(validated_google_fonts) > 1:
                font_secondary = validated_google_fonts[1]
            extraction_method.append("google-fonts-validated")
        else:
            font_warnings.append(
                f"GOOGLE_FONT_UNUSED: {', '.join(google_font_names)} imported via <link> "
                f"but not found in any CSS font-family rule. Likely vestigial."
            )

    # Step 3: CSS font-family declarations (non-generic)
    if not font_family and parser.fonts:
        specific = [f for f in parser.fonts
                    if f.strip() and f.lower() not in GENERIC_FONTS
                    and not f.startswith("var(")]
        if specific:
            font_counts = Counter(specific)
            top_fonts = font_counts.most_common(3)
            font_family = top_fonts[0][0]
            if len(top_fonts) > 1 and not font_secondary:
                font_secondary = top_fonts[1][0]
            extraction_method.append("css-font")

    # Step 4: System font stack fallback
    if not font_family and parser.fonts:
        system_indicators = {"system-ui", "-apple-system", "Segoe UI"}
        if any(f in system_indicators for f in parser.fonts):
            font_family = "system-ui"
            extraction_method.append("system-font-stack")

    warnings.extend(font_warnings)

    # ── Rescued utility colors note ──
    if parser.rescued_utility_colors:
        extraction_method.append("prominence-rescue")
        for var_name, hex_color, hits in parser.rescued_utility_colors:
            warnings.append(
                f"UTILITY_RESCUED: {var_name} ({hex_color}) would normally be filtered as "
                f"utility/status color, but appears on {len(hits)} prominent selector(s): "
                f"{', '.join(hits[:3])}. Included as brand candidate."
            )

    # ══════════════════════════════════════
    # LOGO
    # ══════════════════════════════════════
    logo = parser.json_ld_logo or parser.logo_url or parser.og_image

    # ══════════════════════════════════════
    # BUSINESS NAME
    # ══════════════════════════════════════
    title_match = re.search(r"<title[^>]*>([^<]+)</title>", html, re.IGNORECASE)
    business_name = title_match.group(1).strip().split("|")[0].strip() if title_match else ""

    # ══════════════════════════════════════
    # WARNINGS
    # ══════════════════════════════════════
    if parser.is_wordpress:
        wp_filtered = len(parser.wp_preset_colors_found)
        if wp_filtered > 0:
            warnings.append(
                f"WP_PRESET_FILTERED: Filtered out {wp_filtered} WordPress default preset color(s)."
            )
    if platform_filtered:
        platform_name = "Webflow" if parser.is_webflow else "Squarespace" if parser.is_squarespace else "Wix" if parser.is_wix else "platform"
        warnings.append(
            f"PLATFORM_DEFAULT_FILTERED: Filtered {len(platform_filtered)} {platform_name} "
            f"default color(s): {', '.join(sorted(set(platform_filtered))[:5])}."
        )
    if not primary:
        warnings.append("PRIMARY_COLOR: Could not extract. Manual inspection needed.")
    if not secondary:
        warnings.append("SECONDARY_COLOR: Could not extract.")
    if not background:
        warnings.append("BACKGROUND: Could not determine.")
    if not font_family:
        warnings.append("FONT: No font detected. Check site manually.")
    if not logo:
        warnings.append("LOGO: No logo found.")

    # Confidence
    has_colors = bool(primary)
    has_font = bool(font_family)
    has_external_css = ext_css_count > 0
    if has_colors and has_font and has_external_css:
        confidence = "HIGH"
    elif has_colors and has_font:
        confidence = "MEDIUM"
    elif has_colors or has_font:
        confidence = "LOW"
    else:
        confidence = "NONE"

    # ══════════════════════════════════════
    # ANOMALIES — flags for human review
    # ══════════════════════════════════════
    anomalies = []

    # 1. No external CSS fetched — brand data might be incomplete
    if ext_css_count == 0:
        anomalies.append({
            "type": "NO_EXTERNAL_CSS",
            "severity": "high",
            "message": "Zero external stylesheets fetched. Brand colors/fonts may be missing. "
                       "Site might load styles via JS, inline-only, or Tailwind.",
            "action": "Check site manually or ask client for brand guide."
        })

    # 2. All top colors are grayscale — might be a monochrome brand or extraction issue
    chromatic_count = len([c for _, c in accent_colors])
    if chromatic_count == 0:
        anomalies.append({
            "type": "ALL_GRAYSCALE",
            "severity": "high",
            "message": "No chromatic colors found. Either site is truly monochrome or "
                       "brand colors are loaded via JS/images not captured by CSS parsing.",
            "action": "Inspect site visually. Check if brand colors are in images/SVGs only."
        })

    # 3. Prominence rescue triggered — borderline colors included
    if parser.rescued_utility_colors:
        rescued_list = [f"{vn} ({hx})" for vn, hx, _ in parser.rescued_utility_colors]
        anomalies.append({
            "type": "UTILITY_COLORS_RESCUED",
            "severity": "medium",
            "message": f"These colors would normally be filtered as utility/status but appear "
                       f"on prominent selectors: {', '.join(rescued_list)}. Verify they are "
                       f"actual brand colors, not coincidental usage.",
            "action": "Compare against brand guide or client confirmation."
        })

    # 4. No fonts detected at all
    if not font_family and not parser.font_face_fonts and not google_font_names:
        anomalies.append({
            "type": "NO_FONTS_DETECTED",
            "severity": "high",
            "message": "No fonts found via @font-face, Google Fonts, or CSS font-family rules.",
            "action": "Site may use system fonts or load fonts via JS. Check manually."
        })

    # 5. Google Fonts imported but none validated — all vestigial
    if google_font_names and not validated_google_fonts:
        anomalies.append({
            "type": "ALL_GOOGLE_FONTS_VESTIGIAL",
            "severity": "medium",
            "message": f"Google Fonts imported ({', '.join(google_font_names)}) but none found in "
                       f"CSS font-family rules. Likely leftover from theme switch.",
            "action": "Do not report these as brand fonts. Check @font-face fonts instead."
        })

    # 6. Very few colors found — possible incomplete extraction
    total_colors_found = len(set(c for _, c in parser.colors))
    if total_colors_found < 3 and ext_css_count > 0:
        anomalies.append({
            "type": "FEW_COLORS",
            "severity": "low",
            "message": f"Only {total_colors_found} unique color(s) extracted from {ext_css_count} "
                       f"stylesheet(s). Site may use images/gradients for color or dynamic theming.",
            "action": "Review site visually to check for missing palette colors."
        })

    # 7. No logo found
    if not logo:
        anomalies.append({
            "type": "NO_LOGO",
            "severity": "low",
            "message": "No logo URL found via JSON-LD, img[alt=logo], og:image, or favicon.",
            "action": "Check site header manually. Logo may be a CSS background or inline SVG."
        })

    # 8. Primary and secondary are very similar colors
    if primary and secondary:
        h1, s1, l1 = hex_to_hsl(primary)
        h2, s2, l2 = hex_to_hsl(secondary)
        hue_diff = min(abs(h1 - h2), 360 - abs(h1 - h2))
        if hue_diff < 15 and abs(l1 - l2) < 15:
            anomalies.append({
                "type": "SIMILAR_PRIMARY_SECONDARY",
                "severity": "medium",
                "message": f"Primary ({primary}) and secondary ({secondary}) are very similar "
                           f"(hue diff: {hue_diff}°, lightness diff: {abs(l1-l2):.0f}%). "
                           f"Might be shades of the same color, not two distinct brand colors.",
                "action": "Check if the real secondary is a different color family entirely."
            })

    # 9. Webflow/Squarespace visual editor — most styling invisible to CSS parsing
    if parser.is_webflow or parser.is_squarespace:
        platform = "Webflow" if parser.is_webflow else "Squarespace"
        anomalies.append({
            "type": "VISUAL_EDITOR_SITE",
            "severity": "medium",
            "message": f"{platform} site detected. {platform} stores most custom colors/styling "
                       f"via its visual editor, not in CSS rules. Extracted colors may be "
                       f"incomplete — review allChromaticColors array and verify against the "
                       f"live site visually.",
            "action": f"Open the site and compare visually. The allChromaticColors array "
                      f"contains all colors found — manually pick the correct primary/secondary "
                      f"if the auto-ranked ones don't match."
        })

    # ══════════════════════════════════════
    # BUILD RESULT
    # ══════════════════════════════════════
    colors = {}
    if primary:
        colors["primaryAccent"] = primary
    if secondary:
        colors["secondaryAccent"] = secondary
    if background:
        colors["darkText"] = background
    if light_background:
        colors["lightBackground"] = light_background

    # Include all unique chromatic colors found for manual review
    # Ensure primary and secondary are always included at front
    chromatic_seed = []
    if primary:
        chromatic_seed.append(normalize_hex(primary))
    if secondary:
        chromatic_seed.append(normalize_hex(secondary))
    chromatic_seed.extend(normalize_hex(c) for _, c in accent_colors)
    all_chromatic = list(dict.fromkeys(chromatic_seed))[:12]

    result = {
        "businessName": business_name,
        "colors": colors,
        "allChromaticColors": all_chromatic,
        "fontFamily": font_family or "",
        "fontSecondary": font_secondary or "",
        "logoUrl": logo,
        "faviconUrl": parser.favicon_url,
        "extraction_method": extraction_method,
        "confidence": confidence,
        "warnings": warnings,
        "is_wordpress": parser.is_wordpress,
        "is_webflow": parser.is_webflow,
        "is_squarespace": parser.is_squarespace,
        "platform_defaults_filtered": list(set(platform_filtered)) if is_any_platform else [],
        "external_css_fetched": ext_css_count,
        "font_face_fonts_found": list(dict.fromkeys(parser.font_face_fonts))[:10],
        "anomalies": anomalies,
    }

    if parser.is_wordpress:
        result["wp_debug"] = {
            "preset_colors_filtered": [
                {"var": name, "hex": val}
                for name, val in parser.wp_preset_colors_found[:10]
            ],
            "brand_vars_detected": [
                {"var": name, "hex": val}
                for name, val in parser.wp_brand_colors
            ],
            "google_fonts_imported": google_font_names,
            "google_fonts_validated": validated_google_fonts,
            "external_css_urls": ext_css_urls[:5],
        }

    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python extract_brand.py <URL>")
        sys.exit(1)

    url = sys.argv[1]
    if not url.startswith("http"):
        url = "https://" + url

    result = extract_brand(url)
    print(json.dumps(result, indent=2))

    # Summary to stderr
    import sys as _sys
    _sys.stderr.write(f"\n--- Brand Extraction Summary ---\n")
    _sys.stderr.write(f"Confidence: {result['confidence']}\n")
    _sys.stderr.write(f"Methods: {', '.join(result['extraction_method']) or 'none'}\n")
    _sys.stderr.write(f"Primary: {result['colors'].get('primaryAccent', 'none')}\n")
    _sys.stderr.write(f"Secondary: {result['colors'].get('secondaryAccent', 'none')}\n")
    _sys.stderr.write(f"Font: {result['fontFamily'] or 'none'}\n")
    _sys.stderr.write(f"Font 2: {result['fontSecondary'] or 'none'}\n")
    _sys.stderr.write(f"@font-face: {', '.join(result['font_face_fonts_found']) or 'none'}\n")
    _sys.stderr.write(f"External CSS: {result['external_css_fetched']} sheets\n")
    if result['warnings']:
        _sys.stderr.write(f"Warnings:\n")
        for w in result['warnings']:
            _sys.stderr.write(f"  ! {w}\n")
