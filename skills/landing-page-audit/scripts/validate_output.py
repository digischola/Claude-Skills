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

    # 13. Chart.js dataset vs textual score consistency
    # The dashboard renders numeric scores in two places: the text body (e.g. "7.5/10" or
    # `{{CRO_SCORE}}/10`) and the Chart.js calls (createGauge(id, 7.5, 10) or
    # createRadar(id, labels, [7, 8, 6, ...])). If they disagree, the client sees mismatched
    # numbers. This check verifies every textual score is represented in at least one
    # Chart.js numeric argument, and that overall = CRO·0.4 + Visual·0.3 + Persuasion·0.3
    # within ±0.5 tolerance.
    text_scores = [float(m) for m in re.findall(r'(?<![\d.])(\d{1,2}(?:\.\d)?)\s*/\s*10\b', html)]
    text_scores_set = set(round(s, 1) for s in text_scores)
    chart_scores = set()
    for m in re.finditer(r'createGauge\s*\(\s*[\'"][^\'"]+[\'"]\s*,\s*([\d.]+)\s*,\s*(\d+)', html):
        chart_scores.add(round(float(m.group(1)), 1))
    for m in re.finditer(r'createRadar\s*\(\s*[\'"][^\'"]+[\'"]\s*,\s*\[[^\]]*\]\s*,\s*\[([^\]]+)\]', html):
        for val in m.group(1).split(','):
            val = val.strip()
            if re.match(r'^-?[\d.]+$', val):
                chart_scores.add(round(float(val), 1))
    if text_scores_set and chart_scores:
        missing = text_scores_set - chart_scores
        if missing:
            # Only flag if >1 score missing — allow small decimal-rounding drift
            if len(missing) > 1:
                results["CRITICAL"].append(
                    f"Chart.js datasets don't include textual scores: {sorted(missing)}. "
                    f"Chart has {sorted(chart_scores)}, text shows {sorted(text_scores_set)}. "
                    f"Dashboard will display inconsistent numbers."
                )
            else:
                results["WARNING"].append(
                    f"One textual score {sorted(missing)} not found in Chart.js data — "
                    f"may be rounding, verify manually"
                )
        else:
            results["PASS"].append(f"Chart.js datasets match textual scores ({len(text_scores_set)} values)")
        # Weighted-average sanity check.
        # Prefer the createGauge values (unambiguous), falling back to text regex with
        # "overall" / "conversion readiness" keywords.
        gauge_overall = re.search(r'createGauge\s*\(\s*[\'"]gaugeOverall[\'"]\s*,\s*([\d.]+)', html)
        gauge_cro = re.search(r'createGauge\s*\(\s*[\'"]gaugeCRO[\'"]\s*,\s*([\d.]+)', html)
        gauge_vis = re.search(r'createGauge\s*\(\s*[\'"]gaugeVisual[\'"]\s*,\s*([\d.]+)', html)
        gauge_per = re.search(r'createGauge\s*\(\s*[\'"]gaugePersuasion[\'"]\s*,\s*([\d.]+)', html)
        if all([gauge_overall, gauge_cro, gauge_vis, gauge_per]):
            overall = float(gauge_overall.group(1))
            expected = float(gauge_cro.group(1)) * 0.4 + float(gauge_vis.group(1)) * 0.3 + float(gauge_per.group(1)) * 0.3
            if abs(overall - expected) > 0.5:
                results["CRITICAL"].append(
                    f"Overall score {overall} doesn't match weighted average "
                    f"(CRO×0.4 + Visual×0.3 + Persuasion×0.3 = {expected:.2f}). "
                    f"Difference {abs(overall - expected):.2f} exceeds 0.5 tolerance."
                )
            else:
                results["PASS"].append(
                    f"Overall score {overall} matches weighted average {expected:.2f} ✓"
                )

    # 14. Screenshot marker → issue list consistency
    # Each numbered marker on the screenshot should correspond to an issue in the list
    # with matching number and severity color. Red = CRITICAL, yellow = MAJOR, green = MINOR.
    # The skill's templates use <div class="marker critical|major|minor">N</div>.
    markers = re.findall(
        r'<div[^>]*class\s*=\s*"[^"]*\bmarker\s+(critical|major|minor)\b[^"]*"[^>]*>\s*(\d+)\s*</div>',
        html, re.IGNORECASE
    )
    # Extract issue list entries: `### N. title` or numbered items with severity tags
    issue_entries = []
    for m in re.finditer(
        r'(?i)(?:###\s*|issue\s*#?\s*|<h[34][^>]*>\s*(?:<[^>]+>)?)(\d+)[\.\s]+([^<\n]{3,100})',
        html
    ):
        issue_num = int(m.group(1))
        surrounding = html[max(0, m.start() - 200):m.end() + 500].lower()
        sev = None
        if 'critical' in surrounding or '🔴' in surrounding:
            sev = 'critical'
        elif 'major' in surrounding or '🟡' in surrounding:
            sev = 'major'
        elif 'minor' in surrounding or '🟢' in surrounding:
            sev = 'minor'
        issue_entries.append((issue_num, sev))
    marker_nums = {int(n) for _, n in markers}
    issue_nums_with_severity = {(n, s) for n, s in issue_entries if s in ('critical', 'major', 'minor')}
    critical_major_issues = {n for n, s in issue_nums_with_severity if s in ('critical', 'major')}
    if markers:
        orphan_markers = marker_nums - {n for n, _ in issue_entries}
        if orphan_markers:
            results["WARNING"].append(
                f"Screenshot marker(s) with no matching issue: {sorted(orphan_markers)}"
            )
        # CRITICAL/MAJOR issues should have markers (MINOR is optional)
        missing_markers = critical_major_issues - marker_nums
        if missing_markers:
            results["WARNING"].append(
                f"CRITICAL/MAJOR issue(s) without screenshot marker: {sorted(missing_markers)}"
            )
        # Severity-class match
        class_by_num = {int(n): cls.lower() for cls, n in markers}
        mismatches = []
        for num, sev in issue_entries:
            if num in class_by_num and sev and class_by_num[num] != sev:
                mismatches.append(f"#{num} (marker={class_by_num[num]}, issue={sev})")
        if mismatches:
            results["WARNING"].append(
                f"Marker severity doesn't match issue severity for: {', '.join(mismatches[:5])}"
            )
        if not orphan_markers and not missing_markers and not mismatches:
            results["PASS"].append(
                f"Screenshot markers consistent with issues ({len(markers)} markers, "
                f"{len(critical_major_issues)} CRITICAL/MAJOR)"
            )
    elif critical_major_issues:
        results["WARNING"].append(
            f"{len(critical_major_issues)} CRITICAL/MAJOR issues but no screenshot markers found"
        )

    # 15. Companion markdown findings report must exist (SKILL.md Step 5b)
    # Pattern: {page-name}-landing-page-audit.html → {page-name}-audit-findings.md
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
