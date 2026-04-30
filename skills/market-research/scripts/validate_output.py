#!/usr/bin/env python3
"""
Output Validator for Market Research Skill
Checks markdown reports and HTML dashboards against quality assertions.
Run after every research session to catch quality gaps before delivery.

Usage:
    python validate_output.py <markdown_report_path> [html_dashboard_path]
"""

import sys
import re
from pathlib import Path


def validate_markdown(filepath):
    """Validate a market research markdown report against quality assertions."""
    content = Path(filepath).read_text(encoding="utf-8")
    results = []

    # 1. Source labels present
    # Accepts bare `[EXTRACTED]` / `[INFERRED]` AND citation-suffixed variants
    # like `[EXTRACTED — Source Name [42]]`, `[EXTRACTED from business.md]`,
    # `[INFERRED — reasoning]`. The latter is more rigorous than the former.
    # Pattern: open bracket → label → optional whitespace + non-`]` content → close bracket.
    extracted_count = len(re.findall(r'\[EXTRACTED(?:[\s—:\-][^\]]*)?\]', content))
    inferred_count = len(re.findall(r'\[INFERRED(?:[\s—:\-][^\]]*)?\]', content))
    total_labels = extracted_count + inferred_count
    results.append({
        "assertion": "source_labels_present",
        "passed": total_labels >= 10,
        "detail": f"{extracted_count} EXTRACTED, {inferred_count} INFERRED ({total_labels} total)",
        "severity": "CRITICAL" if total_labels < 5 else "WARNING" if total_labels < 10 else "OK"
    })

    # 2. Blank fields with reasons (not silently omitted)
    blank_count = len(re.findall(r'\[?BLANK', content, re.IGNORECASE))
    results.append({
        "assertion": "blank_fields_documented",
        "passed": blank_count >= 1,
        "detail": f"{blank_count} BLANK fields found (expect at least a few gaps in any research)",
        "severity": "WARNING" if blank_count == 0 else "OK"
    })

    # 3. Confidence ratings per section
    confidence_count = len(re.findall(r'\*?\*?Confidence:?\s*\*?\*?\s*(HIGH|MEDIUM|LOW)', content, re.IGNORECASE))
    if confidence_count == 0:
        # Fallback: check for inline confidence mentions
        confidence_count = len(re.findall(r'(HIGH|MEDIUM|LOW)\s*(confidence|—)', content, re.IGNORECASE))
    results.append({
        "assertion": "confidence_ratings_present",
        "passed": confidence_count >= 8,
        "detail": f"{confidence_count} confidence ratings found (expect 11 for all dimensions)",
        "severity": "CRITICAL" if confidence_count == 0 else "WARNING" if confidence_count < 8 else "OK"
    })

    # 4. All 10 research dimensions covered
    # SCOPE BOUNDARY (2026-04-30): market-research stops at Dimension 10 (Blue Ocean).
    # Strategic Recommendations belong to paid-media-strategy. Do NOT add an 11th check here.
    dimensions = [
        ("Market Size & Demand", r'[Mm]arket\s+[Ss]ize|TAM|SAM|SOM'),
        ("Porter's Five Forces", r'[Pp]orter|[Ff]ive\s+[Ff]orce'),
        ("PESTEL Analysis", r'PESTEL|PEST\b'),
        ("SWOT Analysis", r'SWOT'),
        ("Competitive Landscape", r'[Cc]ompetitiv'),
        ("Search Demand / Audience & Targeting", r'[Kk]eyword|[Ss]earch\s+[Dd]emand|[Aa]udience\s*(?:&|and)\s*[Tt]argeting|[Aa]udience\s+[Tt]argeting'),
        ("Platform Benchmarks", r'[Bb]enchmark|[Uu]nit\s+[Ee]conomic'),
        ("Buyer Personas", r'[Bb]uyer\s+[Pp]ersona|[Pp]urchase\s+[Jj]ourney'),
        ("Channel Partners & Referral", r'[Cc]hannel\s+[Pp]artner|[Rr]eferral\s+[Ee]cosystem'),
        ("Blue Ocean Opportunities", r'[Bb]lue\s+[Oo]cean|[Uu]nderserved'),
    ]
    found_dimensions = []
    missing_dimensions = []
    for name, pattern in dimensions:
        if re.search(pattern, content):
            found_dimensions.append(name)
        else:
            missing_dimensions.append(name)

    results.append({
        "assertion": "all_11_dimensions_covered",
        "passed": len(missing_dimensions) == 0,
        "detail": f"{len(found_dimensions)}/11 dimensions found" + (f" | Missing: {', '.join(missing_dimensions)}" if missing_dimensions else ""),
        "severity": "CRITICAL" if len(missing_dimensions) > 3 else "WARNING" if missing_dimensions else "OK"
    })

    # 5. Platform coverage (based on what client needs)
    has_meta = bool(re.search(r'[Mm]eta\s+[Aa]ds?|[Ff]acebook\s+[Aa]ds?|CPM|ROAS', content))
    has_google = bool(re.search(r'[Gg]oogle\s+[Aa]ds?|CPC|[Ss]earch\s+[Aa]ds?', content))
    results.append({
        "assertion": "platform_coverage",
        "passed": has_meta or has_google,
        "detail": f"Meta: {'YES' if has_meta else 'NO'} | Google: {'YES' if has_google else 'NO'}",
        "severity": "CRITICAL" if not has_meta and not has_google else "OK"
    })

    # 6. Marketing implications per section
    implications_count = len(re.findall(r'[Mm]arketing\s+[Ii]mplication', content))
    results.append({
        "assertion": "marketing_implications_per_section",
        "passed": implications_count >= 8,
        "detail": f"{implications_count} 'Marketing Implications' sections found (expect 11)",
        "severity": "CRITICAL" if implications_count == 0 else "WARNING" if implications_count < 8 else "OK"
    })

    # 7. Recommendation labels (data-supported / directional)
    data_supported = len(re.findall(r'data-supported', content, re.IGNORECASE))
    directional = len(re.findall(r'directional', content, re.IGNORECASE))
    total_labels_rec = data_supported + directional
    results.append({
        "assertion": "recommendation_labels",
        "passed": total_labels_rec >= 2,
        "detail": f"{data_supported} data-supported, {directional} directional labels",
        "severity": "WARNING" if total_labels_rec == 0 else "OK"
    })

    # 8. No guessing language (red flags)
    guess_patterns = [
        r'(?<!\[)probably\s+around',
        r'(?<!\[)we\s+can\s+assume',
        r'(?<!\[)likely\s+approximately',
        r'(?<!\[)rough\s+estimate',
        r'(?<!\[)safe\s+to\s+say',
    ]
    guess_flags = []
    for pattern in guess_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        guess_flags.extend(matches)

    results.append({
        "assertion": "no_unlabeled_guessing",
        "passed": len(guess_flags) == 0,
        "detail": f"Found {len(guess_flags)} guessing phrases not wrapped in [INFERRED]" + (f": {guess_flags[:3]}" if guess_flags else ""),
        "severity": "WARNING" if guess_flags else "OK"
    })

    # 9. Executive summary present
    has_exec = bool(re.search(r'[Ee]xecutive\s+[Ss]ummary', content))
    results.append({
        "assertion": "executive_summary_present",
        "passed": has_exec,
        "detail": "Executive Summary found" if has_exec else "No Executive Summary section",
        "severity": "WARNING" if not has_exec else "OK"
    })

    # 10. Data gaps section present
    has_gaps = bool(re.search(r'[Dd]ata\s+[Gg]aps|[Ll]imitation', content))
    results.append({
        "assertion": "data_gaps_section",
        "passed": has_gaps,
        "detail": "Data Gaps & Limitations section found" if has_gaps else "No Data Gaps section — needed for honest assessment",
        "severity": "WARNING" if not has_gaps else "OK"
    })

    # 11. GBP review-count gate (local-business primary-source verification).
    # See references/local-business-verification.md. Triggered by 2026-04-25 Living Flow
    # case: Perplexity reported 1,235 Google reviews; reality was 67. The 1,235 was
    # MindBody votes surfaced in GBP "Reviews from the web" panel.
    # Approach: scan for review-count claims with N >= 200; require a verification
    # tag ([VERIFIED] / [GBP] / [EXTRACTED — GBP] / "GBP screenshot") within
    # ~100 chars, otherwise flag as WARNING.
    review_pattern = re.compile(
        r'(\d{1,3}(?:,\d{3})+|\d{3,})\s*(?:[+\s]*)?\b'
        r'(?:google\s+(?:business\s+profile\s+)?review|gbp\s+review|business\s+profile\s+review)',
        re.IGNORECASE
    )
    suspicious_review_claims = []
    for m in review_pattern.finditer(content):
        n_str = m.group(1).replace(',', '')
        try:
            n = int(n_str)
        except ValueError:
            continue
        if n < 200:
            continue
        start = max(0, m.start() - 100)
        end = min(len(content), m.end() + 100)
        window = content[start:end]
        verified = bool(re.search(
            r'\[VERIFIED|\[GBP\b|\[EXTRACTED\s*[—\-]\s*GBP|GBP\s+screenshot|GBP\s+verified|primary[- ]source\s+verified',
            window, re.IGNORECASE
        ))
        if not verified:
            suspicious_review_claims.append((n, m.group(0)[:60]))
    if suspicious_review_claims:
        details = "; ".join(f"{n} reviews ('{snippet}...')" for n, snippet in suspicious_review_claims[:3])
        results.append({
            "assertion": "gbp_review_count_verification",
            "passed": False,
            "detail": (
                f"{len(suspicious_review_claims)} review-count claim(s) ≥200 without GBP verification tag. "
                f"Watch for MindBody/ClassPass/Booking.com 'Reviews from the web' conflation. "
                f"See references/local-business-verification.md. Flagged: {details}"
            ),
            "severity": "WARNING"
        })
    else:
        results.append({
            "assertion": "gbp_review_count_verification",
            "passed": True,
            "detail": "No unverified large review counts detected (or all carry [VERIFIED]/[GBP] tags)",
            "severity": "OK"
        })

    return results


def validate_html(filepath):
    """Validate an HTML dashboard against quality assertions."""
    content = Path(filepath).read_text(encoding="utf-8")
    results = []

    # 1. Not using default/placeholder colors
    has_placeholder = '__PRIMARY_COLOR__' in content or '__BRAND_CONFIG_PLACEHOLDER__' in content
    results.append({
        "assertion": "no_placeholder_values",
        "passed": not has_placeholder,
        "detail": "Placeholders found — brand config not injected" if has_placeholder else "No placeholders — brand config injected",
        "severity": "CRITICAL" if has_placeholder else "OK"
    })

    # 2. Chart.js present
    has_chartjs = bool(re.search(r'chart\.js|Chart\.js|chartjs|new\s+Chart\(', content))
    results.append({
        "assertion": "chartjs_present",
        "passed": has_chartjs,
        "detail": "Chart.js found" if has_chartjs else "No Chart.js — dashboard should use data visualizations, not just cards",
        "severity": "CRITICAL" if not has_chartjs else "OK"
    })

    # 3. Chart instances (expect multiple: radar, bar, line, doughnut)
    chart_instances = len(re.findall(r'new\s+Chart\(', content))
    results.append({
        "assertion": "multiple_charts",
        "passed": chart_instances >= 3,
        "detail": f"{chart_instances} Chart.js instances found (expect 4+ for Porter's radar, market bar, funnel, budget doughnut)",
        "severity": "WARNING" if chart_instances < 3 else "OK"
    })

    # 4. Tooltips present
    tooltip_count = len(re.findall(r'class="tip"|tiptext|tooltip', content, re.IGNORECASE))
    results.append({
        "assertion": "tooltips_present",
        "passed": tooltip_count >= 5,
        "detail": f"{tooltip_count} tooltip elements found (expect tooltips on every KPI)",
        "severity": "CRITICAL" if tooltip_count == 0 else "WARNING" if tooltip_count < 5 else "OK"
    })

    # 5. Collapsible sections present
    collapsible_count = len(re.findall(r'collapse-btn|collapse-body|collapsible|toggle\(this\)', content))
    results.append({
        "assertion": "collapsible_sections",
        "passed": collapsible_count >= 3,
        "detail": f"{collapsible_count} collapsible elements found",
        "severity": "WARNING" if collapsible_count < 3 else "OK"
    })

    # 6. Navigation structure
    nav_links = len(re.findall(r'href="#\w', content))
    results.append({
        "assertion": "navigation_structure",
        "passed": nav_links >= 8,
        "detail": f"{nav_links} nav links found (expect 12+ for all sections)",
        "severity": "WARNING" if nav_links < 8 else "OK"
    })

    # 7. Has animations/transitions
    has_animations = bool(re.search(r'@keyframes|animation:|transition:', content))
    results.append({
        "assertion": "animations_present",
        "passed": has_animations,
        "detail": "CSS animations found" if has_animations else "No animations detected",
        "severity": "WARNING" if not has_animations else "OK"
    })

    # 8. Source indicators present
    has_source_indicators = bool(re.search(r'extracted|inferred|source-tag|source-label|Data not available|tip.*tiptext', content, re.IGNORECASE))
    results.append({
        "assertion": "source_indicators_in_dashboard",
        "passed": has_source_indicators,
        "detail": "Source indicators found" if has_source_indicators else "No source indicators — accuracy protocol not reflected in UI",
        "severity": "WARNING" if not has_source_indicators else "OK"
    })

    # 9. No duplicate variable declarations
    js_vars = re.findall(r'(?:const|let|var)\s+(researchData|brandConfig)\s*=', content)
    duplicates = {v for v in js_vars if js_vars.count(v) > 1}
    results.append({
        "assertion": "no_duplicate_js_variables",
        "passed": len(duplicates) == 0,
        "detail": f"Duplicate declarations found for: {', '.join(duplicates)}" if duplicates else "No duplicate JS variable declarations",
        "severity": "CRITICAL" if duplicates else "OK"
    })

    # 10. No __PLACEHOLDER__ data left
    data_placeholder = bool(re.search(r'__\w+_PLACEHOLDER__', content))
    results.append({
        "assertion": "no_data_placeholders",
        "passed": not data_placeholder,
        "detail": "Data placeholders still present — template not fully populated" if data_placeholder else "All placeholders replaced with data",
        "severity": "CRITICAL" if data_placeholder else "OK"
    })

    # 10b. No unreplaced {{PLACEHOLDER}} template variables
    unreplaced = re.findall(r'\{\{[A-Z_]+(?:\|[^}]*)?\}\}', content)
    results.append({
        "assertion": "no_unreplaced_template_placeholders",
        "passed": len(unreplaced) == 0,
        "detail": f"Unreplaced template placeholders found: {', '.join(set(unreplaced))}" if unreplaced else "All {{PLACEHOLDER}} variables replaced",
        "severity": "CRITICAL" if unreplaced else "OK"
    })

    # 10c. Chart.js UMD build verification
    html_lower = content.lower()
    if 'chart.js' in html_lower and 'chart.umd.min.js' not in content:
        results.append({
            "assertion": "chartjs_umd_build",
            "passed": False,
            "detail": "Chart.js detected but NOT using UMD build — will fail with 'Chart is not defined'",
            "severity": "CRITICAL"
        })
    else:
        results.append({
            "assertion": "chartjs_umd_build",
            "passed": True,
            "detail": "Chart.js UMD build used correctly" if 'chart.umd.min.js' in content else "No Chart.js detected (N/A)",
            "severity": "OK"
        })

    # 11. Keyword data section present
    has_keyword_section = bool(re.search(r'[Kk]eyword|[Ss]earch\s+[Vv]olume|CPC', content))
    results.append({
        "assertion": "keyword_data_section",
        "passed": has_keyword_section,
        "detail": "Keyword/search data section found" if has_keyword_section else "No keyword data section — should integrate platform CSV data",
        "severity": "WARNING" if not has_keyword_section else "OK"
    })

    # 12. Strategic frameworks present (Porter's, PESTEL, SWOT)
    frameworks = {
        "Porter's": bool(re.search(r'[Pp]orter|[Ff]ive\s+[Ff]orce|radar', content)),
        "PESTEL": bool(re.search(r'PESTEL|PEST\b', content)),
        "SWOT": bool(re.search(r'SWOT', content)),
    }
    found_fw = [k for k, v in frameworks.items() if v]
    missing_fw = [k for k, v in frameworks.items() if not v]
    results.append({
        "assertion": "strategic_frameworks_present",
        "passed": len(missing_fw) == 0,
        "detail": f"{len(found_fw)}/3 frameworks found" + (f" | Missing: {', '.join(missing_fw)}" if missing_fw else ""),
        "severity": "CRITICAL" if len(missing_fw) > 1 else "WARNING" if missing_fw else "OK"
    })

    # 13. CSS custom properties from brand config
    has_css_vars = bool(re.search(r'--blue:|--dark:|--text:|var\(--', content))
    results.append({
        "assertion": "brand_css_variables",
        "passed": has_css_vars,
        "detail": "CSS custom properties from brand config found" if has_css_vars else "No CSS custom properties — dashboard may be using hardcoded defaults",
        "severity": "WARNING" if not has_css_vars else "OK"
    })

    return results


def print_results(label, results):
    """Print validation results."""
    print(f"\n{'=' * 60}")
    print(f"  {label}")
    print(f"{'=' * 60}")

    passed = sum(1 for r in results if r["passed"])
    total = len(results)
    critical_fails = [r for r in results if not r["passed"] and r["severity"] == "CRITICAL"]

    for r in results:
        icon = "PASS" if r["passed"] else "FAIL"
        severity = f" [{r['severity']}]" if not r["passed"] else ""
        print(f"  {icon}{severity}  {r['assertion']}")
        print(f"         {r['detail']}")

    print(f"\n  Score: {passed}/{total} passed", end="")
    if critical_fails:
        print(f" | {len(critical_fails)} CRITICAL failures — fix before delivery")
    elif passed == total:
        print(" | All checks passed")
    else:
        print(" | Warnings present — review before delivery")

    return passed, total, len(critical_fails)


def main():
    if len(sys.argv) < 2:
        print("Usage: python validate_output.py <markdown_report> [html_dashboard]")
        sys.exit(1)

    md_path = sys.argv[1]
    html_path = sys.argv[2] if len(sys.argv) > 2 else None

    total_passed = 0
    total_checks = 0
    total_critical = 0

    # Validate markdown
    if Path(md_path).exists():
        md_results = validate_markdown(md_path)
        p, t, c = print_results(f"Markdown Report: {Path(md_path).name}", md_results)
        total_passed += p
        total_checks += t
        total_critical += c
    else:
        print(f"File not found: {md_path}")

    # Validate HTML if provided
    if html_path and Path(html_path).exists():
        html_results = validate_html(html_path)
        p, t, c = print_results(f"HTML Dashboard: {Path(html_path).name}", html_results)
        total_passed += p
        total_checks += t
        total_critical += c
    elif html_path:
        print(f"File not found: {html_path}")

    # Summary
    print(f"\n{'=' * 60}")
    print(f"  TOTAL: {total_passed}/{total_checks} passed | {total_critical} critical failures")
    print(f"{'=' * 60}")

    # Exit code: 1 if any critical failures
    sys.exit(1 if total_critical > 0 else 0)


if __name__ == "__main__":
    main()
