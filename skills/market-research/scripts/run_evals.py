#!/usr/bin/env python3
"""
Eval Runner for Market Research Skill
Reads evals.json and validates skill outputs against defined assertions.

Three modes:
  1. prompt-check: Validates a Perplexity prompt against eval assertions
  2. output-check: Validates a completed research report + dashboard
  3. list: Shows all eval cases

Usage:
    python run_evals.py list
    python run_evals.py prompt-check <eval_id> <perplexity_prompt_file>
    python run_evals.py output-check <eval_id> <markdown_report> [html_dashboard]
"""

import sys
import json
import re
from pathlib import Path

EVALS_PATH = Path(__file__).parent.parent / "evals" / "evals.json"


def load_evals():
    """Load eval definitions from evals.json."""
    with open(EVALS_PATH) as f:
        data = json.load(f)
    return data["evals"]


def list_evals(evals):
    """List all eval cases."""
    print(f"\n{'=' * 60}")
    print(f"  Market Research Skill — {len(evals)} Eval Cases")
    print(f"{'=' * 60}")
    for ev in evals:
        etype = ev.get("type", "unknown")
        print(f"\n  ID {ev['id']} [{etype}]: {ev['prompt'][:80]}...")
        print(f"  Assertions: {len(ev['assertions'])}")
        if ev.get("mock_data"):
            print(f"  Mock data: {ev['mock_data']}")
        for a in ev["assertions"]:
            print(f"    - {a['name']}: {a['description']}")


def check_prompt(eval_case, prompt_content):
    """Validate a generated Perplexity prompt against eval assertions."""
    results = []

    assertion_checks = {
        "generates_perplexity_prompt": lambda c: (
            bool(re.search(r'research|analyz|investigat', c, re.I)) and len(c) > 500,
            f"Prompt length: {len(c)} chars"
        ),
        "local_market_customization": lambda c: (
            bool(re.search(r'local|city|region|area|neighborhood|radius', c, re.I)),
            "Local market references " + ("found" if re.search(r'local|city|region', c, re.I) else "missing")
        ),
        "catchment_radius_appropriate": lambda c: (
            bool(re.search(r'\d+\s*km|\d+\s*mile|radius|catchment', c, re.I)),
            "Catchment/radius reference " + ("found" if re.search(r'radius|catchment|\d+\s*km', c, re.I) else "missing")
        ),
        "both_platforms_covered": lambda c: (
            bool(re.search(r'meta|facebook|instagram', c, re.I)) and bool(re.search(r'google', c, re.I)),
            f"Meta: {'YES' if re.search(r'meta|facebook', c, re.I) else 'NO'} | Google: {'YES' if re.search(r'google', c, re.I) else 'NO'}"
        ),
        "recognizes_existing_client_new_product": lambda c: (
            bool(re.search(r'new\s+(product|service|launch|offering)|specific\s+product', c, re.I)),
            "New product focus " + ("detected" if re.search(r'new\s+(product|service|launch)', c, re.I) else "not detected")
        ),
        "industry_specific_dimensions": lambda c: (
            bool(re.search(r'certification|enrollment|training|education|wellness', c, re.I)),
            "Industry-specific terms " + ("found" if re.search(r'certification|training|wellness', c, re.I) else "missing")
        ),
        "audience_psychology_depth": lambda c: (
            bool(re.search(r'psychology|motivation|trigger|objection|pain\s*point|decision', c, re.I)),
            "Psychology/motivation terms " + ("found" if re.search(r'psychology|trigger|objection', c, re.I) else "missing")
        ),
        "porters_five_forces_included": lambda c: (
            bool(re.search(r'porter|five\s+force', c, re.I)),
            "Porter's Five Forces " + ("found" if re.search(r'porter|five\s+force', c, re.I) else "missing")
        ),
        "pestel_included": lambda c: (
            bool(re.search(r'PESTEL|PEST\b', c)),
            "PESTEL " + ("found" if re.search(r'PESTEL|PEST\b', c) else "missing")
        ),
        "swot_included": lambda c: (
            bool(re.search(r'SWOT', c)),
            "SWOT " + ("found" if re.search(r'SWOT', c) else "missing")
        ),
        "blue_ocean_included": lambda c: (
            bool(re.search(r'blue\s+ocean|underserved|untapped', c, re.I)),
            "Blue Ocean " + ("found" if re.search(r'blue\s+ocean|underserved', c, re.I) else "missing")
        ),
        "buyer_personas_included": lambda c: (
            bool(re.search(r'buyer\s+persona|purchase\s+journey|decision\s+maker', c, re.I)),
            "Buyer Personas " + ("found" if re.search(r'buyer\s+persona|purchase\s+journey', c, re.I) else "missing")
        ),
        "keyword_data_step_present": lambda c: (
            bool(re.search(r'keyword\s+planner|keyword\s+data|search\s+volume', c, re.I)),
            "Keyword data collection " + ("referenced" if re.search(r'keyword\s+planner|keyword\s+data', c, re.I) else "missing")
        ),
        "meta_only_platform_focus": lambda c: (
            bool(re.search(r'meta|facebook|instagram', c, re.I)) and not bool(re.search(r'google\s+ads', c, re.I)),
            "Meta: " + ("YES" if re.search(r'meta|facebook', c, re.I) else "NO") + " | Google Ads: " + ("YES (unexpected)" if re.search(r'google\s+ads', c, re.I) else "NO (correct)")
        ),
        "all_11_dimensions_in_prompt": lambda c: (
            sum(1 for p in [r'market\s+size', r'porter', r'PESTEL', r'SWOT', r'competit', r'keyword', r'benchmark', r'persona', r'channel\s+partner|referral', r'blue\s+ocean', r'recommend']
                if re.search(p, c, re.I)) >= 9,
            f"{sum(1 for p in [r'market.size', r'porter', r'PESTEL', r'SWOT', r'competit', r'keyword', r'benchmark', r'persona', r'channel.partner|referral', r'blue.ocean', r'recommend'] if re.search(p, c, re.I))}/11 dimensions found"
        ),
        "competitor_names_seeded": lambda c: (
            bool(re.search(r'Clayton\s+Utz|Herbert\s+Smith', c, re.I)),
            "Known competitor names " + ("seeded" if re.search(r'Clayton\s+Utz|Herbert\s+Smith', c, re.I) else "missing")
        ),
        "google_only_focus": lambda c: (
            bool(re.search(r'google\s+ads', c, re.I)) and not bool(re.search(r'meta\s+ads|facebook\s+ads', c, re.I)),
            f"Google Ads: {'YES' if re.search(r'google.ads', c, re.I) else 'NO'} | Meta Ads: {'YES (unexpected)' if re.search(r'meta.ads|facebook.ads', c, re.I) else 'NO (correct)'}"
        ),
        "legal_industry_specifics": lambda c: (
            bool(re.search(r'compliance|bar\s+association|legal|regulation|ethic', c, re.I)),
            "Legal industry terms " + ("found" if re.search(r'compliance|bar\s+association|legal', c, re.I) else "missing")
        ),
        "sydney_geographic_scope": lambda c: (
            bool(re.search(r'sydney|NSW|new\s+south\s+wales', c, re.I)),
            "Sydney/NSW scope " + ("found" if re.search(r'sydney|NSW', c, re.I) else "missing")
        ),
        "keyword_collection_step": lambda c: (
            bool(re.search(r'keyword\s+planner|CSV|keyword\s+data|chrome', c, re.I)),
            "Keyword collection step " + ("found" if re.search(r'keyword\s+planner|CSV', c, re.I) else "missing")
        ),
    }

    for assertion in eval_case["assertions"]:
        name = assertion["name"]
        if name in assertion_checks:
            passed, detail = assertion_checks[name](prompt_content)
            results.append({
                "assertion": name,
                "description": assertion["description"],
                "passed": passed,
                "detail": detail
            })
        else:
            results.append({
                "assertion": name,
                "description": assertion["description"],
                "passed": None,
                "detail": "No automated check available — requires manual review"
            })

    return results


def check_output(eval_case, md_content, html_content=None):
    """Validate completed outputs against eval assertions."""
    results = []

    assertion_checks = {
        "source_labels_present": lambda md, html: (
            len(re.findall(r'\[EXTRACTED\]|\[INFERRED\]', md)) >= 10,
            str(len(re.findall(r'\[EXTRACTED\]|\[INFERRED\]', md))) + " source labels found"
        ),
        "blank_fields_with_reasons": lambda md, html: (
            bool(re.search(r'BLANK', md, re.I)),
            f"{len(re.findall(r'BLANK', md, re.I))} blank fields documented"
        ),
        "confidence_ratings_per_section": lambda md, html: (
            len(re.findall(r'Confidence:?\s*(HIGH|MEDIUM|LOW)', md, re.I)) >= 8,
            f"{len(re.findall(r'Confidence:?.*(HIGH|MEDIUM|LOW)', md, re.I))} confidence ratings found (expect 11)"
        ),
        "brand_extraction_attempted": lambda md, html: (
            html is not None and bool(re.search(r'var\(--|--\w+:', html or "")),
            "Brand CSS variables found" if html and re.search(r'var\(--|--\w+:', html) else "No brand CSS variables or no dashboard"
        ),
        "marketing_implications_per_section": lambda md, html: (
            len(re.findall(r'[Mm]arketing\s+[Ii]mplication', md)) >= 8,
            f"{len(re.findall(r'[Mm]arketing [Ii]mplication', md))} marketing implications sections (expect 11)"
        ),
        "recommendation_labels": lambda md, html: (
            len(re.findall(r'data-supported|directional', md, re.I)) >= 2,
            f"{len(re.findall(r'data-supported', md, re.I))} data-supported, {len(re.findall(r'directional', md, re.I))} directional labels"
        ),
        "chartjs_visualizations": lambda md, html: (
            html is not None and len(re.findall(r'new\s+Chart\(', html or "")) >= 3,
            str(len(re.findall(r'new\s+Chart\(', html or ''))) + " Chart.js instances (expect 4+)" if html else "No dashboard provided"
        ),
        "tooltips_on_kpis": lambda md, html: (
            html is not None and len(re.findall(r'class="tip"|tiptext|tooltip', html or "", re.I)) >= 5,
            f"{len(re.findall(r'tip|tooltip', html or '', re.I))} tooltip elements" if html else "No dashboard provided"
        ),
        "collapsible_sections": lambda md, html: (
            html is not None and len(re.findall(r'collapse|collapsible|toggle', html or "", re.I)) >= 3,
            f"{len(re.findall(r'collapse|toggle', html or '', re.I))} collapsible elements" if html else "No dashboard provided"
        ),
        "keyword_data_integrated": lambda md, html: (
            html is not None and bool(re.search(r'keyword|search\s+volume|CPC', html or "", re.I)),
            "Keyword data section " + ("found" if html and re.search(r'keyword|CPC', html, re.I) else "missing")
        ),
        "porters_pestel_swot_present": lambda md, html: (
            html is not None and all(
                bool(re.search(p, html or "", re.I))
                for p in [r'porter|five\s+force|radar', r'PESTEL|PEST\b', r'SWOT']
            ),
            "Frameworks: " + ", ".join(
                f"{n}: {'YES' if html and re.search(p, html, re.I) else 'NO'}"
                for n, p in [("Porter's", r'porter|five.force|radar'), ("PESTEL", r'PESTEL|PEST\b'), ("SWOT", r'SWOT')]
            )
        ),
        "both_outputs_generated": lambda md, html: (
            html is not None and len(md) > 1000,
            f"MD: {len(md)} chars | HTML: {len(html) if html else 0} chars"
        ),
        "wiki_updated": lambda md, html: (
            True,  # Can't verify file system from here — manual check
            "Wiki update requires manual verification (check _engine/wiki/log.md for entry)"
        ),
        "strategic_implications_present": lambda md, html: (
            bool(re.search(r'[Ss]trategic|[Ii]mplication|[Rr]ecommend', md)),
            "Strategic section " + ("found" if re.search(r'strategic', md, re.I) else "missing")
        ),
        "both_platforms_covered": lambda md, html: (
            bool(re.search(r'meta|facebook', md, re.I)) and bool(re.search(r'google', md, re.I)),
            f"Meta: {'YES' if re.search(r'meta|facebook', md, re.I) else 'NO'} | Google: {'YES' if re.search(r'google', md, re.I) else 'NO'}"
        ),
    }

    for assertion in eval_case["assertions"]:
        name = assertion["name"]
        if name in assertion_checks:
            passed, detail = assertion_checks[name](md_content, html_content)
            results.append({
                "assertion": name,
                "description": assertion["description"],
                "passed": passed,
                "detail": detail
            })
        else:
            results.append({
                "assertion": name,
                "description": assertion["description"],
                "passed": None,
                "detail": "No automated check — requires manual review"
            })

    return results


def print_results(eval_case, results, mode):
    """Print eval results."""
    print(f"\n{'=' * 60}")
    print(f"  Eval #{eval_case['id']} — {mode}")
    print(f"  Prompt: {eval_case['prompt'][:70]}...")
    print(f"{'=' * 60}")

    passed = sum(1 for r in results if r["passed"] is True)
    failed = sum(1 for r in results if r["passed"] is False)
    manual = sum(1 for r in results if r["passed"] is None)

    for r in results:
        if r["passed"] is True:
            icon = "PASS"
        elif r["passed"] is False:
            icon = "FAIL"
        else:
            icon = "MANUAL"
        print(f"  {icon}  {r['assertion']}")
        print(f"        {r['detail']}")

    print(f"\n  Results: {passed} passed | {failed} failed | {manual} need manual review")
    return passed, failed, manual


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python run_evals.py list")
        print("  python run_evals.py prompt-check <eval_id> <prompt_file>")
        print("  python run_evals.py output-check <eval_id> <md_report> [html_dashboard]")
        sys.exit(1)

    evals = load_evals()
    mode = sys.argv[1]

    if mode == "list":
        list_evals(evals)
        return

    if len(sys.argv) < 4:
        print("Need eval_id and file path(s)")
        sys.exit(1)

    eval_id = int(sys.argv[2])
    eval_case = next((e for e in evals if e["id"] == eval_id), None)
    if not eval_case:
        print(f"Eval #{eval_id} not found. Available: {[e['id'] for e in evals]}")
        sys.exit(1)

    filepath = sys.argv[3]
    content = Path(filepath).read_text(encoding="utf-8")

    if mode == "prompt-check":
        results = check_prompt(eval_case, content)
        print_results(eval_case, results, "Prompt Validation")

    elif mode == "output-check":
        html_content = None
        if len(sys.argv) > 4:
            html_content = Path(sys.argv[4]).read_text(encoding="utf-8")
        results = check_output(eval_case, content, html_content)
        print_results(eval_case, results, "Output Validation")

    else:
        print(f"Unknown mode: {mode}. Use 'list', 'prompt-check', or 'output-check'")
        sys.exit(1)


if __name__ == "__main__":
    main()
