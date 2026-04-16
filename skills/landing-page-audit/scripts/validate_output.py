#!/usr/bin/env python3
"""
Validation script for Landing Page Audit dashboard output.
Checks for required sections, scoring accuracy, and content completeness.

Usage: python validate_output.py <dashboard_html_path>
"""

import sys
import re
import os
from pathlib import Path


def validate_dashboard(html_path: str) -> dict:
    """Validate the audit dashboard HTML file."""
    results = {"CRITICAL": [], "WARNING": [], "INFO": [], "PASS": []}

    if not os.path.exists(html_path):
        results["CRITICAL"].append(f"Dashboard file not found: {html_path}")
        return results

    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()

    html_lower = html.lower()

    # --- CRITICAL CHECKS ---

    # 1. Chart.js UMD build (not ESM)
    if "chart.umd.min.js" in html:
        results["PASS"].append("Chart.js UMD build used correctly")
    elif "chart.min.js" in html or "chart.js" in html_lower:
        results["CRITICAL"].append(
            "Chart.js loaded but NOT using UMD build. "
            "Must use: cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"
        )
    else:
        results["CRITICAL"].append("Chart.js not found — scores need visualizations")

    # 2. Score sections present
    score_sections = {
        "Overall Conversion Readiness": r"conversion\s*readiness|overall\s*score",
        "CRO Fundamentals": r"cro\s*fundamental",
        "Visual UI/UX": r"visual\s*ui|visual\s*ux|ui\s*/\s*ux",
        "Persuasion & Copy": r"persuasion|copy\s*(&|and)\s*persuasion",
    }
    for name, pattern in score_sections.items():
        if re.search(pattern, html_lower):
            results["PASS"].append(f"Score section found: {name}")
        else:
            results["CRITICAL"].append(f"Missing score section: {name}")

    # 3. Numeric scores present (look for X/10 or X.X/10 patterns)
    score_pattern = r'\b\d+\.?\d*\s*/\s*10\b'
    scores_found = re.findall(score_pattern, html)
    if len(scores_found) >= 4:
        results["PASS"].append(f"Found {len(scores_found)} score values")
    elif len(scores_found) > 0:
        results["WARNING"].append(
            f"Only {len(scores_found)} scores found — expected at least 4 "
            "(overall + 3 pillars)"
        )
    else:
        results["CRITICAL"].append("No numeric scores (X/10) found in dashboard")

    # 4. Issue severity markers
    severity_checks = {
        "CRITICAL issues": r"critical|🔴",
        "MAJOR issues": r"major|🟡",
        "MINOR issues": r"minor|🟢",
    }
    for name, pattern in severity_checks.items():
        if re.search(pattern, html_lower) or re.search(pattern, html):
            results["PASS"].append(f"Severity level found: {name}")
        else:
            results["WARNING"].append(f"Missing severity level: {name}")

    # 5. Fix recommendations present
    fix_indicators = [
        r"recommend",
        r"current\s*:",
        r"fix\s*:",
        r"rewrite",
        r"change\s+to",
        r"replace\s+with",
    ]
    fix_count = sum(1 for p in fix_indicators if re.search(p, html_lower))
    if fix_count >= 3:
        results["PASS"].append("Fix recommendations appear substantive")
    elif fix_count > 0:
        results["WARNING"].append(
            "Few fix recommendation indicators found — "
            "ensure recommendations are specific, not vague"
        )
    else:
        results["CRITICAL"].append(
            "No fix recommendations detected — every finding needs a specific fix"
        )

    # --- WARNING CHECKS ---

    # 6. Collapsible sections
    if "collapse" in html_lower or "toggle" in html_lower or "accordion" in html_lower:
        results["PASS"].append("Collapsible sections detected")
    else:
        results["WARNING"].append("No collapsible sections found — detail should be expandable")

    # 7. Tooltips
    if "tiptext" in html_lower or "tooltip" in html_lower:
        results["PASS"].append("Tooltips detected")
    else:
        results["WARNING"].append("No tooltips found — scores should have explanatory tooltips")

    # 8. Dark mode
    dark_indicators = [
        r"background.*#0[0-9a-f]",
        r"background.*#1[0-9a-f]",
        r"background.*#2[0-9a-f]",
        r"--dark",
        r"dark-mode",
        r"bg-dark",
        r"background.*rgb\s*\(\s*[0-3]\d",
    ]
    if any(re.search(p, html_lower) for p in dark_indicators):
        results["PASS"].append("Dark mode styling detected")
    else:
        results["WARNING"].append("Dark mode not clearly detected — dashboard should use dark theme")

    # 9. Brand config integration
    if "brand" in html_lower or "--primary" in html or "var(--" in html:
        results["PASS"].append("CSS custom properties / brand integration detected")
    else:
        results["WARNING"].append(
            "No brand config integration detected — "
            "check if brand-config.json colors are applied"
        )

    # 10. Screenshot / image section
    if "<img" in html_lower or "screenshot" in html_lower or "annotated" in html_lower:
        results["PASS"].append("Screenshot/image section detected")
    else:
        results["WARNING"].append(
            "No screenshot section detected — "
            "dashboard should show annotated page screenshots"
        )

    # 11. No placeholder text
    placeholders = [
        r"\[placeholder\]",
        r"\[todo\]",
        r"\[insert",
        r"lorem ipsum",
        r"xxx",
        r"\[tbd\]",
    ]
    for p in placeholders:
        if re.search(p, html_lower):
            results["CRITICAL"].append(f"Placeholder text found: matches pattern '{p}'")

    # 12. No unreplaced template variables — cover {{X}}, {X}, [X], and ${X} syntax variants
    # (different templates in the wild use different conventions; single-brace and square-bracket
    # forms would slip through the original {{...}}-only check)
    unreplaced = []
    for pattern, label in [
        (r'\{\{[A-Z_][A-Z0-9_]*(?:\|[^}]*)?\}\}', '{{...}}'),
        (r'\{[A-Z_][A-Z0-9_]{2,}\}', '{...}'),       # >=3 char keys to avoid matching CSS like {color:red}
        (r'\[[A-Z_][A-Z0-9_]{2,}\]', '[...]'),       # same guard
        (r'\$\{[A-Z_][A-Z0-9_]*\}', '${...}'),
    ]:
        hits = re.findall(pattern, html)
        if hits:
            unreplaced.append(f"{label}: {', '.join(set(hits))}")
    if unreplaced:
        results["CRITICAL"].append(f"Unreplaced template placeholders: {' | '.join(unreplaced)}")
    else:
        results["PASS"].append("All placeholder variants replaced ({{...}}, {...}, [...], ${...})")

    # --- INFO ---

    # File size check
    size_kb = os.path.getsize(html_path) / 1024
    results["INFO"].append(f"Dashboard file size: {size_kb:.1f} KB")
    if size_kb < 10:
        results["WARNING"].append("File seems very small — may be incomplete")

    # 13. Companion markdown findings report must exist (SKILL.md Step 5b)
    # Pattern: {page-name}-landing-page-audit.html → {page-name}-audit-findings.md
    # The HTML dashboard is great for client presentation, but the MD is what downstream
    # skills + email + client calls need. Skipping it = findings locked in HTML only.
    md_path = re.sub(r'-landing-page-audit\.html$', '-audit-findings.md', html_path)
    if md_path == html_path:
        # Filename didn't follow the expected pattern; try a looser fallback.
        md_path = os.path.splitext(html_path)[0] + '-findings.md'
    if os.path.exists(md_path):
        results["PASS"].append(f"Markdown findings report present: {os.path.basename(md_path)}")
    else:
        results["CRITICAL"].append(
            f"Markdown findings report missing: expected {os.path.basename(md_path)} "
            "alongside HTML dashboard (required by SKILL.md Step 5b)"
        )

    return results


def print_results(results: dict) -> int:
    """Print validation results and return exit code."""
    print("\n" + "=" * 60)
    print("LANDING PAGE AUDIT — OUTPUT VALIDATION")
    print("=" * 60)

    exit_code = 0

    for level in ["CRITICAL", "WARNING", "INFO", "PASS"]:
        items = results[level]
        if not items:
            continue

        icons = {"CRITICAL": "❌", "WARNING": "⚠️", "INFO": "ℹ️", "PASS": "✅"}
        print(f"\n{icons[level]} {level} ({len(items)})")
        print("-" * 40)
        for item in items:
            print(f"  {item}")

        if level == "CRITICAL" and items:
            exit_code = 1

    print("\n" + "=" * 60)
    critical_count = len(results["CRITICAL"])
    warning_count = len(results["WARNING"])
    pass_count = len(results["PASS"])

    if critical_count == 0:
        print(f"✅ PASSED — {pass_count} checks passed, {warning_count} warnings")
    else:
        print(f"❌ FAILED — {critical_count} critical issues must be fixed before delivery")
    print("=" * 60 + "\n")

    return exit_code


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python validate_output.py <dashboard_html_path>")
        sys.exit(1)

    dashboard_path = sys.argv[1]
    results = validate_dashboard(dashboard_path)
    exit_code = print_results(results)
    sys.exit(exit_code)
