#!/usr/bin/env python3
"""
detect_target_profile.py — Fingerprint a landing page and return the capture recipe ID.

Usage:
  python3 detect_target_profile.py <url_or_html_path>
  python3 detect_target_profile.py --html "<html string>"

Output (JSON):
  {
    "profile": "react-spa-countup" | "elementor-wordpress" | "webflow" | "squarespace" |
               "shopify" | "wordpress-generic" | "static-html",
    "recipe_path": "references/capture-recipes/<profile>.md",
    "signals": [...human-readable list of what matched...],
    "warnings": [...optional caveats...]
  }

Called from Step 0 of SKILL.md as the session-start profile detection.
"""

import sys
import os
import re
import json
import urllib.request


# Detection rules in priority order. First match wins.
# Each rule: (profile_id, [signals], [any_of_patterns])
#   patterns match against the raw HTML as substrings (case-insensitive).
RULES = [
    (
        "react-spa-countup",
        [
            "gpt-engineer-file-uploads",
            r'/assets/index-[A-Z0-9]{6,}\.(?:js|css)',  # Vite/React build artifacts
            "data-count",
            "stat-number",
        ],
    ),
    (
        "elementor-wordpress",
        [
            "elementor-widget-container",
            "wp-content/plugins/elementor",
            "elementor-kit-",
            r'class="elementor\s',
        ],
    ),
    (
        "webflow",
        [
            "data-wf-site",
            "webflow.io",
            "webflow.css",
        ],
    ),
    (
        "squarespace",
        [
            "static.squarespace.com",
            "squarespace-cdn.com",
            'data-controller="SiteLoader"',
        ],
    ),
    (
        "shopify",
        [
            "cdn.shopify.com",
            "shopify-section",
            "Shopify.theme",
        ],
    ),
    (
        "wordpress-generic",
        [
            "/wp-content/",
            "/wp-includes/",
            "wp-json",
        ],
    ),
]


def _match_any(html_lower: str, patterns: list) -> list:
    """Return the list of patterns that matched (for signal reporting)."""
    hits = []
    for p in patterns:
        if p.startswith("r'") or any(c in p for c in "\\[({"):
            if re.search(p, html_lower, re.IGNORECASE):
                hits.append(p)
        else:
            if p.lower() in html_lower:
                hits.append(p)
    return hits


def detect(html: str) -> dict:
    """Return {profile, recipe_path, signals, warnings}."""
    html_lower = html.lower()
    warnings = []

    # Special case: react-spa with CountUp gets more specific detection
    # because "wordpress-generic" would otherwise match pages with /wp-content/
    # but no Elementor — we want wordpress-generic to be the fallback for
    # plain WP, not a false positive for React SPAs that embed WP assets.

    for profile, patterns in RULES:
        hits = _match_any(html_lower, patterns)
        # Require at least 2 hits to avoid single-token false positives
        if len(hits) >= 2 or (len(hits) == 1 and len(patterns) == 1):
            # Cross-check: react-spa-countup must not also be elementor
            if profile == "react-spa-countup" and "elementor-widget-container" in html_lower:
                warnings.append(
                    "Mixed signals: React SPA markers + Elementor markers. "
                    "Treating as react-spa-countup (newer stack takes precedence)."
                )
            return {
                "profile": profile,
                "recipe_path": f"references/capture-recipes/{profile}.md",
                "signals": hits,
                "warnings": warnings,
            }

    # Nothing matched — plain static HTML
    return {
        "profile": "static-html",
        "recipe_path": "references/capture-recipes/static-html.md",
        "signals": [],
        "warnings": warnings,
    }


def _fetch(url: str) -> str:
    """Fetch HTML. Uses urllib; no external deps."""
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 audit-pre-flight"})
    with urllib.request.urlopen(req, timeout=15) as r:
        raw = r.read()
    # Try utf-8, fall back to latin-1 for binary-safe read
    try:
        return raw.decode("utf-8", errors="replace")
    except Exception:
        return raw.decode("latin-1", errors="replace")


def main():
    args = sys.argv[1:]
    if not args:
        print("Usage: python3 detect_target_profile.py <url_or_html_path>")
        print("       python3 detect_target_profile.py --html '<raw html>'")
        sys.exit(2)

    if args[0] == "--html":
        html = " ".join(args[1:])
    elif args[0].startswith(("http://", "https://")):
        html = _fetch(args[0])
    elif os.path.isfile(args[0]):
        with open(args[0], "r", encoding="utf-8", errors="replace") as f:
            html = f.read()
    else:
        print(f"Not a URL, file, or --html flag: {args[0]}")
        sys.exit(2)

    result = detect(html)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
