#!/usr/bin/env python3
"""
Eval Runner for Business Analysis Skill

Runs targeted, deterministic tests against the skill's scripts.
These are NOT full-workflow evals (those are in evals.json for LLM-level testing).
These are unit-level tests for the scripts that do the heavy lifting.

Usage:
    python run_evals.py                    # run all tests
    python run_evals.py extract_brand      # run only extract_brand tests
    python run_evals.py crawl              # run only crawl tests

Output:
    PASS/FAIL per test, summary at end
"""

import sys
import json
import os
import re

# Add scripts dir to path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)


def test_extract_brand_grayscale():
    """HSL grayscale detection must classify dark greens/navies as chromatic."""
    from extract_brand import is_grayscale, hex_to_hsl

    tests = [
        # (hex, expected_grayscale, description)
        ("#313131", True, "pure dark gray"),
        ("#ffffff", True, "white"),
        ("#000000", True, "black"),
        ("#808080", True, "mid gray"),
        ("#b5aea5", True, "warm gray (S=9.8%)"),
        ("#2a3832", False, "Deep Forest Green (S=14%) — brand color, not gray"),
        ("#1e3a6e", False, "navy blue (S=57%)"),
        ("#e71c24", False, "vivid red (S=83%)"),
        ("#c0a797", False, "Soft Sand (S=22%)"),
        ("#f4c96b", False, "saffron gold (S=86%)"),
        ("#7a00df", False, "vivid purple (S=100%)"),
        ("#ebe8e5", False, "Whisper Grey (S=13%) — warm-tinted, part of brand palette"),
    ]

    passed = 0
    failed = 0
    for hex_color, expected, desc in tests:
        result = is_grayscale(hex_color)
        _, s, _ = hex_to_hsl(hex_color)
        if result == expected:
            passed += 1
        else:
            failed += 1
            print(f"  FAIL: {hex_color} ({desc}) — got {'grayscale' if result else 'chromatic'}, "
                  f"expected {'grayscale' if expected else 'chromatic'} (S={s}%)")

    return passed, failed


def test_extract_brand_wp_preset_filter():
    """WordPress preset colors must be in the filter set."""
    from extract_brand import WP_PRESET_COLORS

    must_filter = [
        "#0693e3",  # vivid-cyan-blue
        "#ff6900",  # luminous-vivid-orange
        "#cf2e2e",  # vivid-red
        "#fcb900",  # luminous-vivid-amber
        "#00d084",  # vivid-green-cyan
        "#9b51e0",  # vivid-purple
        "#abb8c3",  # cyan-bluish-gray
    ]

    passed = 0
    failed = 0
    for color in must_filter:
        if color in WP_PRESET_COLORS:
            passed += 1
        else:
            failed += 1
            print(f"  FAIL: {color} not in WP_PRESET_COLORS — would leak as brand color")

    return passed, failed


def test_extract_brand_utility_color_filter():
    """Material Design / Bootstrap utility colors must be filtered."""
    from extract_brand import UTILITY_STATUS_COLORS

    must_filter = [
        "#d32f2f",  # MD Red 700 (error)
        "#4caf50",  # MD Green 500 (success)
        "#f44336",  # MD Red 500
        "#ff9800",  # MD Orange 500 (warning)
        "#2196f3",  # MD Blue 500 (info)
        "#dc3545",  # Bootstrap danger
        "#28a745",  # Bootstrap success
        "#ffc107",  # Bootstrap warning
    ]

    passed = 0
    failed = 0
    for color in must_filter:
        if color in UTILITY_STATUS_COLORS:
            passed += 1
        else:
            failed += 1
            print(f"  FAIL: {color} not in UTILITY_STATUS_COLORS — would leak as brand color")

    return passed, failed


def test_extract_brand_icon_font_filter():
    """Icon fonts must not be reported as brand fonts."""
    from extract_brand import ICON_FONTS

    must_filter = ["icomoon", "fontawesome", "dashicons", "material icons"]

    passed = 0
    failed = 0
    for font in must_filter:
        if font in ICON_FONTS:
            passed += 1
        else:
            failed += 1
            print(f"  FAIL: '{font}' not in ICON_FONTS — would report as brand font")

    return passed, failed


def test_extract_brand_utility_var_names():
    """Utility CSS variable names must be filtered."""
    from extract_brand import UTILITY_VAR_NAMES

    must_filter = ["--red", "--green", "--error", "--success", "--warning", "--danger"]

    passed = 0
    failed = 0
    for var in must_filter:
        if var in UTILITY_VAR_NAMES:
            passed += 1
        else:
            failed += 1
            print(f"  FAIL: '{var}' not in UTILITY_VAR_NAMES — would leak as brand color")

    return passed, failed


def test_extract_brand_font_normalization():
    """Font weight suffixes must be stripped: Gilroy-Bold → Gilroy."""
    import re
    weight_suffixes = re.compile(
        r'[-\s]?(thin|extralight|ultralight|light|regular|normal|book|'
        r'medium|semibold|demibold|bold|extrabold|ultrabold|black|heavy|'
        r'italic|oblique|condensed|expanded|narrow|wide)$',
        re.IGNORECASE
    )

    tests = [
        ("Gilroy-Bold", "Gilroy"),
        ("Gilroy-Medium", "Gilroy"),
        ("Gilroy-SemiBold", "Gilroy"),
        ("quincy-cf", "quincy-cf"),  # no weight suffix
        ("Playfair Display", "Playfair Display"),  # no suffix
        ("Montserrat-Light", "Montserrat"),
        ("Roboto-Italic", "Roboto"),
    ]

    passed = 0
    failed = 0
    for input_name, expected in tests:
        result = weight_suffixes.sub('', input_name).strip(' -')
        if result == expected:
            passed += 1
        else:
            failed += 1
            print(f"  FAIL: '{input_name}' → '{result}', expected '{expected}'")

    return passed, failed


def test_extract_brand_css_var_color_names():
    """CSS variables named as colors (--navy, --gold) must be captured.
    Tests the full pipeline: UTILITY_VAR_NAMES filter first, then color_names match."""
    from extract_brand import UTILITY_VAR_NAMES

    color_names = [
        'red', 'blue', 'green', 'yellow', 'orange', 'purple', 'pink',
        'navy', 'gold', 'cream', 'sand', 'forest', 'sky', 'rose',
        'saffron', 'amber', 'coral', 'mint', 'peach',
    ]

    test_vars = [
        ("--navy", True),
        ("--gold", True),
        ("--cream", True),
        ("--navy-2", True),       # starts with --navy-
        ("--pink-light", True),   # starts with --pink-
        ("--gold-light", True),   # starts with --gold-
        ("--cream-warm", True),   # starts with --cream-
        ("--red", False),         # in UTILITY_VAR_NAMES — filtered before color_names check
        ("--green", False),       # in UTILITY_VAR_NAMES — filtered before color_names check
        ("--spacing-lg", False),  # not a color name
        ("--font-size", False),   # not a color name
    ]

    passed = 0
    failed = 0
    for var_name, expected_match in test_vars:
        vn = var_name.lower()
        # Mirror actual script pipeline: skip utility vars first, then check color names
        if vn in UTILITY_VAR_NAMES:
            is_match = False
        else:
            is_match = any(vn == f'--{cn}' or vn.startswith(f'--{cn}-')
                           or vn.endswith(f'-{cn}') for cn in color_names)
        if is_match == expected_match:
            passed += 1
        else:
            failed += 1
            status = "matched" if is_match else "not matched"
            expected_str = "match" if expected_match else "no match"
            print(f"  FAIL: '{var_name}' {status}, expected {expected_str}")

    return passed, failed


def test_validate_output_exists():
    """validate_output.py must exist and be importable."""
    passed = 0
    failed = 0
    try:
        validate_path = os.path.join(SCRIPT_DIR, "validate_output.py")
        if os.path.exists(validate_path):
            passed += 1
        else:
            failed += 1
            print("  FAIL: validate_output.py does not exist")
    except Exception as e:
        failed += 1
        print(f"  FAIL: {e}")

    return passed, failed


def test_init_wiki_exists():
    """init_wiki.py must exist."""
    passed = 0
    failed = 0
    wiki_path = os.path.join(SCRIPT_DIR, "init_wiki.py")
    if os.path.exists(wiki_path):
        passed += 1
    else:
        failed += 1
        print("  FAIL: init_wiki.py does not exist")

    return passed, failed


def test_lint_wiki_exists():
    """lint_wiki.py must exist."""
    passed = 0
    failed = 0
    lint_path = os.path.join(SCRIPT_DIR, "lint_wiki.py")
    if os.path.exists(lint_path):
        passed += 1
    else:
        failed += 1
        print("  FAIL: lint_wiki.py does not exist")

    return passed, failed


def test_lint_wiki_blank_detection():
    """lint_wiki.py BLANK detection must catch unexplained BLANKs."""
    from lint_wiki import lint_blank_fields

    # Content with explained BLANKs (should pass)
    good_content = """# Test Page
> Last updated: 2026-04-09 | Sources: 1 | Confidence: HIGH

## Key Findings
- Revenue: BLANK — needs client intake
- Capacity: BLANK (not visible on website)
- Staff count: BLANK - likely more than visible
"""
    issues = lint_blank_fields("test.md", good_content)
    passed = 0
    failed = 0
    if len(issues) == 0:
        passed += 1
    else:
        failed += 1
        print(f"  FAIL: Explained BLANKs should not trigger errors, got {len(issues)} issues")

    # Content with unexplained BLANKs (should fail)
    bad_content = """# Test Page
> Last updated: 2026-04-09 | Sources: 1 | Confidence: HIGH

## Key Findings
- Post frequency: BLANK
- Engagement: BLANK
"""
    issues = lint_blank_fields("test.md", bad_content)
    if len(issues) > 0:
        passed += 1
    else:
        failed += 1
        print("  FAIL: Unexplained BLANKs should trigger errors")

    return passed, failed


# ══════════════════════════════════════
# Test runner
# ══════════════════════════════════════

def test_extract_brand_prominence_rescue():
    """Utility colors used on prominent selectors should be rescued as brand candidates."""
    from extract_brand import BrandExtractor, PROMINENCE_THRESHOLD

    passed = 0
    failed = 0

    # Test 1: --red used on h1, header, .hero → should be rescued (3 prominent hits >= threshold)
    parser = BrandExtractor("https://example.com")
    css_prominent = """
    h1 { color: #d32f2f; }
    header { background-color: #d32f2f; }
    .hero { border-color: #d32f2f; }
    --red: #d32f2f;
    """
    parser._parse_css(css_prominent)
    rescued_colors = [c for _, c, _ in parser.rescued_utility_colors]
    if "#d32f2f" in rescued_colors:
        passed += 1
    else:
        failed += 1
        print("  FAIL: #d32f2f on h1/header/.hero should be rescued but wasn't")

    # Test 2: --red used only in .error-message → should NOT be rescued (not prominent)
    parser2 = BrandExtractor("https://example.com")
    css_not_prominent = """
    .error-message { color: #d32f2f; }
    --red: #d32f2f;
    """
    parser2._parse_css(css_not_prominent)
    rescued_colors2 = [c for _, c, _ in parser2.rescued_utility_colors]
    if "#d32f2f" not in rescued_colors2:
        passed += 1
    else:
        failed += 1
        print("  FAIL: #d32f2f on .error-message only should NOT be rescued")

    # Test 3: --green used on body and nav → should be rescued
    parser3 = BrandExtractor("https://example.com")
    css_green_prominent = """
    body { background-color: #4caf50; }
    nav { color: #4caf50; }
    .sidebar { color: #4caf50; }
    --green: #4caf50;
    """
    parser3._parse_css(css_green_prominent)
    rescued_colors3 = [c for _, c, _ in parser3.rescued_utility_colors]
    if "#4caf50" in rescued_colors3:
        passed += 1
    else:
        failed += 1
        print("  FAIL: #4caf50 on body/nav should be rescued but wasn't")

    # Test 4: Inline utility hex on prominent selectors → should be rescued
    parser4 = BrandExtractor("https://example.com")
    css_inline_prominent = """
    h1 { color: #dc3545; }
    h2 { color: #dc3545; }
    .btn { background: #dc3545; }
    """
    parser4._parse_css(css_inline_prominent)
    rescued_colors4 = [c for _, c, _ in parser4.rescued_utility_colors]
    if "#dc3545" in rescued_colors4:
        passed += 1
    else:
        failed += 1
        print("  FAIL: Bootstrap danger #dc3545 on h1/h2/.btn should be rescued")

    return passed, failed


def test_extract_brand_platform_default_filter():
    """Platform default colors (Webflow blue, etc.) must be filtered on detected platforms."""
    from extract_brand import PLATFORM_DEFAULT_COLORS

    test_cases = [
        ("#3898ec", True),   # Webflow default link blue
        ("#2895f7", True),   # Webflow link blue variant
        ("#0082f3", True),   # Webflow focus blue
        ("#116dff", True),   # Wix default blue
        ("#008060", True),   # Shopify green
        ("#e71c24", False),  # NOT a platform default (Thrive brand red)
        ("#fd5b2c", False),  # NOT a platform default (Quoti orange)
        ("#ffdede", False),  # NOT a platform default (Quoti peach)
    ]

    passed = 0
    failed = 0
    for color, expected_is_default in test_cases:
        is_default = color.lower() in PLATFORM_DEFAULT_COLORS
        if is_default == expected_is_default:
            passed += 1
        else:
            failed += 1
            status = "is default" if is_default else "not default"
            expected = "default" if expected_is_default else "not default"
            print(f"  FAIL: {color} {status}, expected {expected}")

    return passed, failed


def test_extract_brand_hue_diff_secondary():
    """Secondary color must be from a different hue family (>30° apart) when possible."""
    from extract_brand import hex_to_hsl

    test_pairs = [
        # (primary, candidate, should_be_different_hue)
        ("#3898ec", "#5d6c7b", False),  # Both blue family (hue diff ~2°)
        ("#3898ec", "#ffff00", True),   # Blue vs yellow — different
        ("#e71c24", "#2a3832", True),   # Red vs green — different
        ("#ffdede", "#fd5b2c", False),  # Peach (hue ~0°) vs orange (hue ~13°) — same red-orange family
        ("#4caf50", "#388e3c", False),  # Both green shades
    ]

    passed = 0
    failed = 0
    for primary, candidate, expected_diff in test_pairs:
        h1, _, _ = hex_to_hsl(primary)
        h2, _, _ = hex_to_hsl(candidate)
        hue_diff = min(abs(h1 - h2), 360 - abs(h1 - h2))
        is_different = hue_diff > 30
        if is_different == expected_diff:
            passed += 1
        else:
            failed += 1
            print(f"  FAIL: {primary} vs {candidate}: hue_diff={hue_diff}°, "
                  f"got {'different' if is_different else 'similar'}, "
                  f"expected {'different' if expected_diff else 'similar'}")

    return passed, failed


def test_extract_brand_webflow_icon_filter():
    """Webflow icon fonts and other modern icon libraries must be filtered."""
    from extract_brand import ICON_FONTS

    test_fonts = [
        ("webflow-icons", True),
        ("bootstrap-icons", True),
        ("boxicons", True),
        ("Obviously", False),    # Real brand font
        ("Switzer", False),      # Real brand font
        ("Gilroy", False),       # Real brand font
    ]

    passed = 0
    failed = 0
    for font, expected_is_icon in test_fonts:
        is_icon = font.lower() in ICON_FONTS or any(
            icon in font.lower() or font.lower() in icon for icon in ICON_FONTS
        )
        if is_icon == expected_is_icon:
            passed += 1
        else:
            failed += 1
            status = "icon font" if is_icon else "not icon"
            expected = "icon font" if expected_is_icon else "not icon"
            print(f"  FAIL: '{font}' detected as {status}, expected {expected}")

    return passed, failed


ALL_TESTS = {
    "extract_brand": [
        ("grayscale_detection", test_extract_brand_grayscale),
        ("wp_preset_filter", test_extract_brand_wp_preset_filter),
        ("utility_color_filter", test_extract_brand_utility_color_filter),
        ("icon_font_filter", test_extract_brand_icon_font_filter),
        ("utility_var_names", test_extract_brand_utility_var_names),
        ("font_normalization", test_extract_brand_font_normalization),
        ("css_var_color_names", test_extract_brand_css_var_color_names),
        ("prominence_rescue", test_extract_brand_prominence_rescue),
        ("platform_default_filter", test_extract_brand_platform_default_filter),
        ("hue_diff_secondary", test_extract_brand_hue_diff_secondary),
        ("webflow_icon_filter", test_extract_brand_webflow_icon_filter),
    ],
    "infrastructure": [
        ("validate_output_exists", test_validate_output_exists),
        ("init_wiki_exists", test_init_wiki_exists),
        ("lint_wiki_exists", test_lint_wiki_exists),
    ],
    "lint_wiki": [
        ("blank_detection", test_lint_wiki_blank_detection),
    ],
}


def run_tests(filter_group=None):
    total_passed = 0
    total_failed = 0

    for group_name, tests in ALL_TESTS.items():
        if filter_group and filter_group != group_name:
            continue

        print(f"\n{'='*50}")
        print(f"  {group_name}")
        print(f"{'='*50}")

        for test_name, test_fn in tests:
            try:
                p, f = test_fn()
                total_passed += p
                total_failed += f
                status = "PASS" if f == 0 else "FAIL"
                print(f"  [{status}] {test_name} ({p} passed, {f} failed)")
            except Exception as e:
                total_failed += 1
                print(f"  [ERROR] {test_name}: {e}")

    print(f"\n{'='*50}")
    print(f"  TOTAL: {total_passed} passed, {total_failed} failed")
    print(f"{'='*50}")

    return total_failed == 0


if __name__ == "__main__":
    filter_group = sys.argv[1] if len(sys.argv) > 1 else None
    success = run_tests(filter_group)
    sys.exit(0 if success else 1)
