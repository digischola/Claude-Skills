#!/usr/bin/env python3
"""
Validate paid-media-strategy skill outputs.
Usage: python validate_output.py <report.md> <dashboard.html> [media-plan.csv]
"""

import sys
import os
import re
import json

def validate_report(filepath):
    """Validate the strategy markdown report."""
    issues = {"CRITICAL": [], "WARNING": [], "INFO": []}

    if not os.path.exists(filepath):
        issues["CRITICAL"].append(f"Report file not found: {filepath}")
        return issues

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.split('\n')

    # Check required sections
    required_sections = [
        "Campaign Architecture",
        "Bidding Strategy",
        "Audience",
        "Budget Allocation",
        "Creative Direction",
        "Conversion",
        "KPI",
        "Phase"
    ]

    for section in required_sections:
        if section.lower() not in content.lower():
            issues["CRITICAL"].append(f"Missing required section: {section}")

    # Check for source labels
    extracted_count = content.count("[EXTRACTED]")
    inferred_count = content.count("[INFERRED]")
    blank_count = content.lower().count("[blank")
    total_labels = extracted_count + inferred_count + blank_count

    if total_labels < 10:
        issues["CRITICAL"].append(f"Insufficient source labels: {total_labels} found (minimum 10 expected)")

    # Check for decision rationale (not just listing strategies)
    rationale_patterns = [
        r'\bbecause\b', r'\bsince\b', r'\bgiven\b', r'\brationale\b',
        r'\bwhy\b', r'\bthis means\b', r'\btherefore\b', r'\bthe reason\b',
        r'\bdue to\b', r'\bbased on\b', r'\bat this budget\b', r'\bat \$',
        r'\bwith only\b', r'\bwhich means\b', r'\bso that\b',
        r'\bthe logic\b', r'\bwe recommend .+ because\b',
    ]
    rationale_count = sum(
        len(re.findall(p, content, re.IGNORECASE)) for p in rationale_patterns
    )

    if rationale_count < 10:
        issues["WARNING"].append(f"Low decision rationale count ({rationale_count}) — strategy should explain WHY, not just WHAT (minimum 10 expected)")

    # Check for data-supported / directional labels
    data_supported = content.lower().count("data-supported")
    directional = content.lower().count("directional")

    if data_supported + directional < 3:
        issues["WARNING"].append(f"Missing recommendation labels: {data_supported} data-supported, {directional} directional (minimum 3 total)")

    # Check for What to Watch sections
    watch_count = content.lower().count("what to watch")
    if watch_count < 3:
        issues["WARNING"].append(f"Only {watch_count} 'What to Watch' sections found (expected at least 3)")

    # Check for platform specificity
    google_mentions = content.lower().count("google")
    meta_mentions = content.lower().count("meta")

    if google_mentions < 5 and meta_mentions < 5:
        issues["WARNING"].append("Low platform-specific content — strategy should be platform-specific, not generic")

    # Check executive summary exists
    if "executive summary" not in content.lower():
        issues["WARNING"].append("Missing Executive Summary section")

    # Check for placeholder text
    placeholders = re.findall(r'\{[^}]+\}', content)
    template_placeholders = [p for p in placeholders if not p.startswith('{#')]
    if len(template_placeholders) > 0:
        issues["CRITICAL"].append(f"Unfilled template placeholders found: {template_placeholders[:5]}")

    issues["INFO"].append(f"Report stats: {len(lines)} lines, {extracted_count} [EXTRACTED], {inferred_count} [INFERRED], {blank_count} BLANK")

    return issues


def validate_dashboard(filepath):
    """Validate the HTML strategy dashboard."""
    issues = {"CRITICAL": [], "WARNING": [], "INFO": []}

    if not os.path.exists(filepath):
        issues["CRITICAL"].append(f"Dashboard file not found: {filepath}")
        return issues

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check Chart.js CDN - MUST be UMD build
    if "chart.min.js" in content and "chart.umd.min.js" not in content:
        issues["CRITICAL"].append("WRONG Chart.js CDN: using chart.min.js (ESM) instead of chart.umd.min.js (UMD). Charts will break.")

    if "cdnjs.cloudflare.com" in content and "chart" in content.lower():
        issues["CRITICAL"].append("Chart.js loaded from cdnjs (ESM-only). Must use jsdelivr UMD build.")

    if "cdn.jsdelivr.net/npm/chart.js" not in content and "chart" in content.lower():
        issues["WARNING"].append("Chart.js not loaded from recommended jsdelivr CDN")

    # Check for CSS custom properties (brand color system)
    has_css_vars = bool(re.search(r'--[\w-]+:\s*#[0-9a-fA-F]', content))
    if not has_css_vars:
        issues["WARNING"].append("No CSS custom properties for colors found — dashboard should use CSS variables for theming")

    # Check for tooltips
    tooltip_count = content.count('class="tip"') + content.count("class='tip'")
    if tooltip_count < 5:
        issues["WARNING"].append(f"Only {tooltip_count} tooltips found (minimum 5 expected for strategy dashboard)")

    # Check for copy buttons — count actual button/span elements, not CSS declarations
    # Match elements like <button class="copy-btn" onclick="copyText(...)"> or similar
    copy_btn_elements = re.findall(r'<(?:button|span)[^>]*(?:copy-btn|copyText\()[^>]*>', content)
    copy_btn_count = len(copy_btn_elements)
    if copy_btn_count < 3:
        issues["WARNING"].append(f"Only {copy_btn_count} copy button elements found (strategy dashboard should have copy buttons on actionable elements)")

    # Check for collapsible sections
    collapsible_count = content.count('collapse-btn') + content.count('collapse-body')
    if collapsible_count < 4:
        issues["WARNING"].append(f"Only {collapsible_count} collapsible element references found")

    # Check for Chart.js canvas elements
    canvas_count = content.count('<canvas')
    if canvas_count < 2:
        issues["WARNING"].append(f"Only {canvas_count} chart canvas elements found (minimum 2 expected: budget + funnel)")

    # Check for placeholder text
    if "Lorem ipsum" in content or "placeholder" in content.lower():
        issues["CRITICAL"].append("Placeholder text found in dashboard")

    # Check for unreplaced {{PLACEHOLDER}} template variables
    unreplaced = re.findall(r'\{\{[A-Z_]+(?:\|[^}]*)?\}\}', content)
    if unreplaced:
        issues["CRITICAL"].append(f"Unreplaced template placeholders found: {', '.join(set(unreplaced))}")

    # Verify Chart.js UMD build specifically
    html_lower = content.lower()
    if 'chart.js' in html_lower and 'chart.umd.min.js' not in content:
        issues["CRITICAL"].append("Chart.js detected but NOT using UMD build — will fail with 'Chart is not defined'")

    # Check required sections exist
    required_sections = ["Campaign", "Budget", "Audience", "Creative", "Timeline", "KPI"]
    for section in required_sections:
        if section.lower() not in content.lower():
            issues["WARNING"].append(f"Section reference missing in dashboard: {section}")

    # Check for responsive meta tag
    if 'viewport' not in content:
        issues["WARNING"].append("Missing viewport meta tag for responsive design")

    # Brand-config compliance check.
    # Dashboard HTML now sits at the client folder root; brand-config.json lives in
    # _engine/brand-config.json (single-program) or {client-root}/_engine/brand-config.json (multi-program).
    # Walk up looking for the nearest _engine/ folder.
    dashboard_dir = os.path.dirname(os.path.abspath(filepath))
    brand_config_path = None
    cur = dashboard_dir
    for _ in range(5):
        cand = os.path.join(cur, "_engine", "brand-config.json")
        if os.path.exists(cand):
            brand_config_path = cand
            break
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent
    if brand_config_path is None:
        brand_config_path = os.path.join(dashboard_dir, "_engine", "brand-config.json")
    if os.path.exists(brand_config_path):
        try:
            with open(brand_config_path, 'r', encoding='utf-8') as bc:
                brand_config = json.load(bc)
            # Check if dashboard uses generic defaults when brand-config specifies different colors
            generic_defaults = ['#3b82f6', '#8b5cf6', '#6366f1', '#0ea5e9', '#14b8a6']
            brand_colors = []
            colors_obj = brand_config.get("colors", {})
            for v in colors_obj.values():
                if isinstance(v, str) and v.startswith("#"):
                    brand_colors.append(v.lower())
            is_monochromatic = all(c in ('#000000', '#ffffff', '#000', '#fff') for c in brand_colors)
            if not is_monochromatic:
                found_generics = [g for g in generic_defaults if g in content.lower()]
                if found_generics:
                    issues["WARNING"].append(
                        f"Brand-config specifies non-default colors but dashboard uses generic defaults: {', '.join(found_generics)}. "
                        f"Consider using brand-derived colors instead."
                    )
            else:
                # Monochromatic brand — generic defaults are acceptable, just note it
                issues["INFO"].append("Monochromatic brand detected — generic accent defaults acceptable")
        except (json.JSONDecodeError, KeyError) as e:
            issues["WARNING"].append(f"Could not parse brand-config.json: {e}")

    # Light-section contrast check
    # Find color declarations on light backgrounds that are lighter than #6b7280 (107,114,128)
    light_color_issues = []
    # Extract all hex color values used as text color (in CSS or inline styles)
    # Look for patterns in non-dark sections: color: #hex where hex is lighter than threshold
    hex_colors_in_css = re.findall(r'color:\s*#([0-9a-fA-F]{6})\b', content)
    hex_colors_in_css += re.findall(r'color:\s*#([0-9a-fA-F]{3})\b', content)
    threshold_brightness = 107 + 114 + 128  # sum of RGB for #6b7280
    for hc in hex_colors_in_css:
        if len(hc) == 3:
            r, g, b = int(hc[0]*2, 16), int(hc[1]*2, 16), int(hc[2]*2, 16)
        else:
            r, g, b = int(hc[0:2], 16), int(hc[2:4], 16), int(hc[4:6], 16)
        # Only flag colors that are clearly light text (grey-ish, not white on dark)
        # Skip very light colors (likely on dark backgrounds: #888, #999, #aaa, #ccc etc.)
        if r > 200 and g > 200 and b > 200:
            continue  # White/near-white text — probably on dark background
        if r + g + b > threshold_brightness and r + g + b < 600:
            light_color_issues.append(f"#{hc}")
    # Also check CSS custom property --grey if it resolves to a light value
    grey_var_match = re.search(r'--grey:\s*#([0-9a-fA-F]{3,6})', content)
    if grey_var_match:
        gh = grey_var_match.group(1)
        if len(gh) == 3:
            gr, gg, gb = int(gh[0]*2, 16), int(gh[1]*2, 16), int(gh[2]*2, 16)
        else:
            gr, gg, gb = int(gh[0:2], 16), int(gh[2:4], 16), int(gh[4:6], 16)
        if gr + gg + gb > threshold_brightness and gr + gg + gb < 600:
            # Check if --grey is used in non-dark contexts
            grey_usages = len(re.findall(r'color:\s*var\(--grey\)', content))
            if grey_usages > 0:
                light_color_issues.append(f"var(--grey) = #{gh} ({grey_usages} usages)")
    if light_color_issues:
        unique_issues = list(set(light_color_issues))
        issues["WARNING"].append(
            f"Low contrast text on light background — colors lighter than #6b7280 found: "
            f"{', '.join(unique_issues[:5])}. Consider using #374151 or darker."
        )

    issues["INFO"].append(f"Dashboard stats: {len(content)} chars, {canvas_count} charts, {tooltip_count} tooltips, {copy_btn_count} copy buttons")

    return issues


def validate_csv(filepath):
    """Validate the CSV media plan."""
    issues = {"CRITICAL": [], "WARNING": [], "INFO": []}

    if not os.path.exists(filepath):
        issues["WARNING"].append(f"CSV media plan not found: {filepath} (optional but recommended)")
        return issues

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = [l.strip() for l in content.split('\n') if l.strip()]

    # Check for required sections
    sections = ["Campaign Overview", "Ad Group", "Ad Set", "Budget Projection", "KPI"]
    found_sections = sum(1 for s in sections if s.lower() in content.lower())

    if found_sections < 2:
        issues["WARNING"].append(f"Only {found_sections} of expected CSV sections found")

    # Check campaign names consistency
    # Look for campaign names in overview section and check they appear in ad group section
    campaign_names = set()
    in_overview = False
    for line in lines:
        if "campaign overview" in line.lower():
            in_overview = True
            continue
        if in_overview and line.startswith("Section:"):
            break
        if in_overview and "," in line and not line.startswith("Campaign Name"):
            name = line.split(",")[0].strip()
            if name:
                campaign_names.add(name)

    if len(campaign_names) < 2:
        issues["WARNING"].append(f"Only {len(campaign_names)} campaigns found in CSV")

    # Check for source labels in KPI section
    if "[EXTRACTED]" not in content and "[INFERRED]" not in content:
        issues["WARNING"].append("No source labels found in CSV KPI targets")

    issues["INFO"].append(f"CSV stats: {len(lines)} lines, {len(campaign_names)} campaigns detected")

    return issues


def validate_cross_file_consistency(report_path, csv_path):
    """Validate consistency between the strategy report and CSV media plan."""
    issues = {"CRITICAL": [], "WARNING": [], "INFO": []}

    if not os.path.exists(report_path):
        issues["WARNING"].append("Cannot run cross-file checks — report not found")
        return issues
    if not os.path.exists(csv_path):
        issues["WARNING"].append("Cannot run cross-file checks — CSV not found")
        return issues

    with open(report_path, 'r', encoding='utf-8') as f:
        report_content = f.read()
    with open(csv_path, 'r', encoding='utf-8') as f:
        csv_content = f.read()

    csv_lines = [l.strip() for l in csv_content.split('\n') if l.strip()]

    # --- Extract campaign names from CSV (Campaign Overview section) ---
    csv_campaigns = {}  # name -> {platform, daily_budget}
    in_overview = False
    overview_header = None
    for line in csv_lines:
        if "campaign overview" in line.lower():
            in_overview = True
            continue
        if in_overview and line.lower().startswith("section:"):
            break
        if in_overview:
            parts = [p.strip() for p in line.split(",")]
            if parts and parts[0].lower() == "campaign name":
                overview_header = parts
                continue
            if overview_header and len(parts) >= 6 and parts[0]:
                name = parts[0]
                platform = parts[1] if len(parts) > 1 else ""
                # Daily budget is typically column index 5 (Daily Budget)
                daily_str = parts[5] if len(parts) > 5 else "0"
                # Parse numeric value from budget string (handle "$5", "5", "$28–62", etc.)
                daily_nums = re.findall(r'[\d.]+', daily_str)
                daily_budget = float(daily_nums[0]) if daily_nums else 0.0
                csv_campaigns[name] = {
                    "platform": platform,
                    "daily_budget": daily_budget
                }

    # --- Extract campaign names from report ---
    # Strategy: look for campaign names in markdown tables with "Campaign" column headers
    # and in campaign detail tables (Campaign | Platform | Type | ...)
    report_campaigns = set()
    report_lines = report_content.split('\n')
    in_campaign_table = False
    campaign_col_idx = -1
    for line in report_lines:
        stripped = line.strip()
        # Detect markdown table header row with "Campaign" column
        if '|' in stripped and re.search(r'\bCampaign\b', stripped, re.IGNORECASE):
            cols = [c.strip() for c in stripped.split('|')]
            for idx, col in enumerate(cols):
                if re.match(r'^campaign\s*$', col, re.IGNORECASE) or re.match(r'^campaign\s+name', col, re.IGNORECASE):
                    campaign_col_idx = idx
                    in_campaign_table = True
                    break
            continue
        # Separator row (|---|---|...)
        if in_campaign_table and '|' in stripped and re.match(r'^[\s|:-]+$', stripped):
            continue
        # Data row
        if in_campaign_table and '|' in stripped:
            cols = [c.strip() for c in stripped.split('|')]
            if campaign_col_idx < len(cols):
                cell = cols[campaign_col_idx].strip()
                # Skip empty, header-like, or total rows
                if cell and cell.lower() not in ('', 'campaign', 'campaign name', '---') \
                        and not cell.startswith('**Total') and not cell.startswith('*'):
                    # Clean bold markers
                    clean = re.sub(r'\*+', '', cell).strip()
                    if clean:
                        report_campaigns.add(clean)
            continue
        # If we hit a non-table line, reset
        if in_campaign_table and '|' not in stripped and stripped:
            in_campaign_table = False
            campaign_col_idx = -1

    # Also look for naming-convention patterns like XX_Platform_Something
    convention_names = re.findall(r'\b[A-Z]{2,}_(?:Google|Meta|FB|IG)_\w+', report_content)
    for cn in convention_names:
        report_campaigns.add(cn)

    # Normalize campaign names for comparison (lowercase, strip extra whitespace)
    def normalize(name):
        return re.sub(r'\s+', ' ', name.strip().lower().replace('\u2014', '-').replace('\u2013', '-'))

    report_norm = {normalize(n): n for n in report_campaigns}
    csv_norm = {normalize(n): n for n in csv_campaigns}

    # --- Check a: Campaign count match ---
    # Use CSV campaign count as the authoritative count since it's structured
    csv_count = len(csv_campaigns)
    # For report, count unique campaign names that also appear in the campaign details table
    # (the 1.2 table with Platform, Type, Objective columns)
    # Filter report_campaigns to just those from the main architecture table (not budget breakdowns)
    if csv_count > 0 and len(report_campaigns) > 0:
        # Only flag if counts are substantially different
        if len(report_norm) != csv_count:
            # Check if report has MORE campaigns (may include phase-specific budget rows)
            # Only flag as warning if CSV has campaigns not reflected in report
            issues["INFO"].append(
                f"Campaign count: {len(report_norm)} unique names in report, {csv_count} in CSV"
            )
        else:
            issues["INFO"].append(f"Campaign count matches: {csv_count} campaigns in both files")

    # --- Check b: Campaign name match ---
    csv_only = set(csv_norm.keys()) - set(report_norm.keys())
    report_only = set(report_norm.keys()) - set(csv_norm.keys())

    # For names that don't exactly match, accept ONLY structured prefix/suffix variants
    # (e.g. "Meta Prospecting — Leads" vs "Prospecting — Leads"). Previous substring
    # match was too loose — "Summer" would match "Summer Sale Campaign" even if those
    # were distinct entities.
    def _is_structured_variant(a, b):
        if a == b:
            return True
        # Enforce minimum overlap ratio so "A" never matches "A Much Longer Name"
        shorter, longer = (a, b) if len(a) <= len(b) else (b, a)
        if len(shorter) / max(len(longer), 1) < 0.6:
            return False
        for sep in (' — ', ' – ', ' - ', ': ', ' | ', ' / '):
            if longer.endswith(sep + shorter) or longer.startswith(shorter + sep):
                return True
        return False

    unmatched_csv = set()
    for cn in csv_only:
        if not any(_is_structured_variant(cn, rn) for rn in report_norm):
            unmatched_csv.add(csv_norm[cn])

    unmatched_report = set()
    for rn in report_only:
        if not any(_is_structured_variant(rn, cn) for cn in csv_norm):
            unmatched_report.add(report_norm[rn])

    if unmatched_csv:
        issues["WARNING"].append(
            f"Campaigns in CSV but not found in report: {', '.join(sorted(unmatched_csv))}"
        )
    if unmatched_report:
        # Only warn for names that look like real campaign names (not budget table labels)
        real_unmatched = [n for n in unmatched_report
                         if not n.startswith('Meta ') or len(n) > 6]
        if real_unmatched:
            issues["WARNING"].append(
                f"Campaigns in report but not found in CSV: {', '.join(sorted(real_unmatched))}"
            )

    if not unmatched_csv and not unmatched_report:
        issues["INFO"].append("All campaign names match between report and CSV")

    # --- Check c: Budget total match ---
    # Extract monthly budget from report — look for "$X,XXX/mo" or total monthly rows
    report_budgets = []
    # Pattern 1: "$X,XXX/mo" or "$X,XXX–$X,XXX/mo"
    mo_matches = re.findall(r'\$\s?([\d,]+(?:\.\d+)?)\s*(?:/mo|per\s*month)', report_content, re.IGNORECASE)
    for m in mo_matches:
        val = float(m.replace(',', ''))
        report_budgets.append(val)

    # Pattern 2: Look for "Monthly Budget" header mention like "$1,000–$2,000"
    budget_range = re.findall(r'Monthly\s+Budget[:\s]*.*?\$\s?([\d,]+)', report_content, re.IGNORECASE)
    for b in budget_range:
        val = float(b.replace(',', ''))
        if val not in report_budgets:
            report_budgets.append(val)

    # Pattern 3: Look for "**Total**" rows in budget tables with monthly value
    total_matches = re.findall(r'\*\*Total\*\*[^|]*\|[^|]*\|\s*\*\*\$?([\d,]+(?:\.\d+)?)\*\*', report_content)
    report_total_monthly = None
    for tm in total_matches:
        val = float(tm.replace(',', ''))
        if val > 0:
            report_total_monthly = val
            break  # Use the first total found (Phase 1)

    # CSV: sum daily budgets * 30
    csv_daily_total = sum(c["daily_budget"] for c in csv_campaigns.values())
    csv_monthly_estimate = csv_daily_total * 30

    if report_total_monthly and csv_monthly_estimate > 0:
        diff_pct = abs(report_total_monthly - csv_monthly_estimate) / report_total_monthly * 100
        if diff_pct > 15:
            issues["WARNING"].append(
                f"Budget mismatch: report total ${report_total_monthly:.0f}/mo vs CSV daily sum "
                f"(${csv_daily_total:.0f}/day × 30 = ${csv_monthly_estimate:.0f}/mo) — "
                f"{diff_pct:.0f}% difference"
            )
        else:
            issues["INFO"].append(
                f"Budget consistent: report ${report_total_monthly:.0f}/mo vs CSV ${csv_monthly_estimate:.0f}/mo "
                f"({diff_pct:.0f}% difference)"
            )
    elif csv_monthly_estimate > 0:
        # Couldn't extract a clear total from report — try matching against range
        if report_budgets:
            min_budget = min(report_budgets)
            max_budget = max(report_budgets)
            if csv_monthly_estimate < min_budget * 0.85 or csv_monthly_estimate > max_budget * 1.15:
                issues["WARNING"].append(
                    f"Budget may be inconsistent: CSV daily sum = ${csv_monthly_estimate:.0f}/mo, "
                    f"report budget range ${min_budget:.0f}–${max_budget:.0f}"
                )
            else:
                issues["INFO"].append(
                    f"Budget within range: CSV ${csv_monthly_estimate:.0f}/mo falls within "
                    f"report range ${min_budget:.0f}–${max_budget:.0f}"
                )
        else:
            issues["INFO"].append(
                f"Could not extract monthly budget total from report for comparison. "
                f"CSV daily sum: ${csv_daily_total:.0f}/day (${csv_monthly_estimate:.0f}/mo)"
            )

    # --- Check d: Platform consistency ---
    # Extract platforms from report
    report_platforms = set()
    if re.search(r'\bgoogle\s*ads\b', report_content, re.IGNORECASE):
        report_platforms.add("google")
    if re.search(r'\bmeta\s*ads\b', report_content, re.IGNORECASE):
        report_platforms.add("meta")
    # Also check "Platform Focus" line
    platform_focus = re.search(r'Platform\s+Focus[:\s]*(.+)', report_content, re.IGNORECASE)
    if platform_focus:
        focus_text = platform_focus.group(1).lower()
        if "google" in focus_text:
            report_platforms.add("google")
        if "meta" in focus_text:
            report_platforms.add("meta")

    # Extract platforms from CSV campaigns
    csv_platforms = set()
    for camp in csv_campaigns.values():
        plat = camp["platform"].strip().lower()
        if "google" in plat:
            csv_platforms.add("google")
        if "meta" in plat:
            csv_platforms.add("meta")

    report_only_platforms = report_platforms - csv_platforms
    csv_only_platforms = csv_platforms - report_platforms

    if report_only_platforms:
        issues["WARNING"].append(
            f"Platforms in report but not in CSV campaigns: {', '.join(sorted(report_only_platforms))}"
        )
    if csv_only_platforms:
        issues["WARNING"].append(
            f"Platforms in CSV but not mentioned in report: {', '.join(sorted(csv_only_platforms))}"
        )
    if not report_only_platforms and not csv_only_platforms and report_platforms:
        issues["INFO"].append(f"Platform consistency: both files reference {', '.join(sorted(report_platforms))}")

    return issues


def print_results(name, issues):
    """Print validation results for a file."""
    print(f"\n{'='*60}")
    print(f"  {name}")
    print(f"{'='*60}")

    has_critical = len(issues["CRITICAL"]) > 0

    for level in ["CRITICAL", "WARNING", "INFO"]:
        for msg in issues[level]:
            emoji = {"CRITICAL": "❌", "WARNING": "⚠️", "INFO": "ℹ️"}[level]
            print(f"  {emoji} [{level}] {msg}")

    if not any(issues.values()):
        print("  ✅ No issues found")

    return has_critical


def validate_creative_brief_presence(report_path):
    """Step 5.5 produces creative-brief.json (default short name; legacy
    `{client}-creative-brief.json` accepted as backwards-compat). Downstream skills
    (ad-copywriter, landing-page-builder, campaign-setup) depend on it. Missing =
    silent pipeline break."""
    issues = {"CRITICAL": [], "WARNING": [], "INFO": []}
    working_dir = os.path.dirname(os.path.abspath(report_path))
    # Prefer the new short name; fall back to any legacy *-creative-brief.json.
    candidates = []
    if os.path.exists(os.path.join(working_dir, 'creative-brief.json')):
        candidates.append('creative-brief.json')
    candidates.extend([
        f for f in os.listdir(working_dir)
        if f.endswith('-creative-brief.json') and f != 'creative-brief.json'
    ])
    if not candidates:
        issues["CRITICAL"].append(
            "No creative-brief.json (or legacy *-creative-brief.json) found in _engine/working/ — "
            "Step 5.5 output missing; downstream ad-copywriter/landing-page-builder/campaign-setup "
            "will run in degraded mode"
        )
    else:
        # Basic structural validation
        path = os.path.join(working_dir, candidates[0])
        try:
            import json as _json
            with open(path, 'r', encoding='utf-8') as f:
                brief = _json.load(f)
            required = ['business_name', 'campaigns']
            missing = [k for k in required if k not in brief]
            if missing:
                issues["CRITICAL"].append(f"Creative brief missing required keys: {missing}")
            campaigns = brief.get('campaigns', [])
            if not isinstance(campaigns, list) or len(campaigns) == 0:
                issues["CRITICAL"].append("Creative brief has no campaigns array or empty campaigns")
            else:
                # Require at least one campaign to have visual_direction.image_gen_prompt_prefix
                with_prefix = [c for c in campaigns if isinstance(c, dict)
                               and c.get('visual_direction', {}).get('image_gen_prompt_prefix')]
                if not with_prefix:
                    issues["WARNING"].append(
                        "No campaign has visual_direction.image_gen_prompt_prefix — "
                        "ad-copywriter image prompts will lack brand consistency"
                    )
                issues["INFO"].append(f"Creative brief: {candidates[0]} ({len(campaigns)} campaign(s))")
        except (OSError, ValueError) as e:
            issues["CRITICAL"].append(f"Creative brief exists but failed to parse: {e}")
    return issues


def main():
    if len(sys.argv) < 3:
        print("Usage: python validate_output.py <report.md> <dashboard.html> [media-plan.csv]")
        sys.exit(1)

    report_path = sys.argv[1]
    dashboard_path = sys.argv[2]
    csv_path = sys.argv[3] if len(sys.argv) > 3 else None

    print("\n🔍 Paid Media Strategy — Output Validation")
    print(f"   Report:    {report_path}")
    print(f"   Dashboard: {dashboard_path}")
    if csv_path:
        print(f"   CSV:       {csv_path}")

    has_critical = False

    has_critical |= print_results("Strategy Report", validate_report(report_path))
    has_critical |= print_results("Strategy Dashboard", validate_dashboard(dashboard_path))
    has_critical |= print_results("Creative Brief (Step 5.5)", validate_creative_brief_presence(report_path))

    if csv_path:
        has_critical |= print_results("CSV Media Plan", validate_csv(csv_path))
        has_critical |= print_results("Cross-File Consistency", validate_cross_file_consistency(report_path, csv_path))

    print(f"\n{'='*60}")
    if has_critical:
        print("  ❌ CRITICAL issues found — fix before delivery")
        sys.exit(1)
    else:
        print("  ✅ Validation passed — no critical issues")
        sys.exit(0)


if __name__ == "__main__":
    main()
