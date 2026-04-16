#!/usr/bin/env python3
"""
Eval Runner for Paid Media Strategy Skill
Reads evals.json and validates skill outputs against defined assertions.

Modes:
  1. output-check: Validates deliverables (MD report, HTML dashboard, CSV media plan)
  2. structure-check: Validates client folder structure (wiki updated, downstream flags)
  3. list: Shows all eval cases

Usage:
    python run_evals.py list
    python run_evals.py output-check <eval_id> <md_report> <html_dashboard> [csv_plan]
    python run_evals.py structure-check <eval_id> <client_folder>
"""

import sys
import json
import re
from pathlib import Path

EVALS_PATH = Path(__file__).parent.parent / "evals" / "evals.json"


def load_evals():
    with open(EVALS_PATH) as f:
        data = json.load(f)
    return data["evals"]


def list_evals(evals):
    print("\n" + "=" * 60)
    print("  Paid Media Strategy Skill — %d Eval Cases" % len(evals))
    print("=" * 60)
    for ev in evals:
        print("\n  ID %d: %s..." % (ev["id"], ev["prompt"][:80]))
        print("  Assertions: %d" % len(ev["assertions"]))
        for a in ev["assertions"]:
            print("    - %s: %s" % (a["name"], a["description"]))


def _yn(val):
    return "YES" if val else "NO"


def check_output(eval_case, md, html, csv_content=None):
    """Validate completed deliverables against eval assertions."""
    results = []

    def _platform_specific():
        has_meta = bool(re.search(r'meta|facebook|instagram', md, re.I))
        has_google_camp = bool(re.search(r'google\s+ads\s+campaign', md, re.I))
        passed = has_meta and not has_google_camp
        detail = "Meta refs: %s | Google campaign refs: %s" % (_yn(has_meta), "YES (unexpected)" if has_google_camp else "NO (correct)")
        return passed, detail

    def _cross_platform():
        g = bool(re.search(r'google', md, re.I))
        m = bool(re.search(r'meta|facebook', md, re.I))
        pct = bool(re.search(r'\d+\s*[%/]', md))
        detail = "Google: %s | Meta: %s | Split %%: %s" % (_yn(g), _yn(m), "found" if pct else "check manually")
        return g and m and pct, detail

    def _decision_logic():
        count = len(re.findall(r'because|since|reason|rationale|why', md, re.I))
        return count >= 5, "%d rationale markers found (need 5+)" % count

    def _guided_questions():
        count = len(re.findall(r'\?\s*$|\?\s*\n', md, re.MULTILINE))
        total_q = len(re.findall(r'\?', md))
        return count >= 3, "%d question marks found" % total_q

    def _source_labels():
        count = len(re.findall(r'\[EXTRACTED\]|\[INFERRED\]', md))
        return count >= 5, "%d source labels found (need 5+)" % count

    def _phased():
        p1 = bool(re.search(r'phase\s*1', md, re.I))
        p2 = bool(re.search(r'phase\s*2', md, re.I))
        p3 = bool(re.search(r'phase\s*3', md, re.I))
        detail = "Phase 1: %s | Phase 2: %s | Phase 3: %s" % (_yn(p1), _yn(p2), _yn(p3))
        return p1 and p2 and p3, detail

    def _b2b_sales_cycle():
        found = bool(re.search(r'sales\s+cycle|lead\s+quality|nurtur|offline\s+conversion', md, re.I))
        return found, "B2B cycle terms " + ("found" if found else "missing")

    def _wiki_consumed():
        count = len(re.findall(r'\[EXTRACTED\]', md))
        return count >= 3, "%d [EXTRACTED] labels (wiki data references)" % count

    def _chartjs_umd():
        found = html is not None and bool(re.search(r'chart\.umd|chart\.js', html, re.I))
        return found, "Chart.js UMD " + ("found" if found else "MISSING") + " in dashboard"

    def _app_specific():
        found = bool(re.search(r'app\s+promotion|app\s+install|AAC|advantage\+\s+app', md, re.I))
        return found, "App campaign terms " + ("found" if found else "missing")

    def _tracking():
        found = bool(re.search(r'SDK|MMP|SKAN|attribution|pixel|CAPI', md, re.I))
        return found, "Tracking terms " + ("found" if found else "missing")

    def _advantage_plus():
        found = bool(re.search(r'advantage\+|advantage\s+plus|ASC|AAC', md, re.I))
        return found, "Advantage+ references " + ("found" if found else "missing")

    def _creative_app():
        found = bool(re.search(r'demo\s+video|UGC|app\s+store|screenshot|testimonial', md, re.I))
        return found, "App creative terms " + ("found" if found else "missing")

    def _budget_rec():
        found = bool(re.search(r'CPI|cost\s+per\s+install|budget.*\$|unit\s+economics', md, re.I))
        return found, "Budget/unit economics terms " + ("found" if found else "missing")

    assertion_checks = {
        "platform_specific": _platform_specific,
        "cross_platform_allocation": _cross_platform,
        "decision_logic_explained": _decision_logic,
        "guided_questions_asked": _guided_questions,
        "budget_math_correct": lambda: _check_budget_math(md),
        "budget_recommendation": _budget_rec,
        "source_labels_present": _source_labels,
        "phased_execution": _phased,
        "b2b_sales_cycle": _b2b_sales_cycle,
        "wiki_consumed": _wiki_consumed,
        "csv_produced": lambda: _check_csv(csv_content),
        "chartjs_umd": _chartjs_umd,
        "app_specific_logic": _app_specific,
        "tracking_prerequisite": _tracking,
        "advantage_plus_qualification": _advantage_plus,
        "creative_app_focused": _creative_app,
    }

    for assertion in eval_case["assertions"]:
        name = assertion["name"]
        if name in assertion_checks:
            passed, detail = assertion_checks[name]()
            results.append({"assertion": name, "description": assertion["description"],
                            "passed": passed, "detail": detail})
        else:
            results.append({"assertion": name, "description": assertion["description"],
                            "passed": None, "detail": "No automated check — requires manual review"})
    return results


def _check_budget_math(md):
    dailies = re.findall(r'\$(\d+(?:,\d{3})*(?:\.\d+)?)\s*/?\s*day', md, re.I)
    monthlies = re.findall(r'\$(\d+(?:,\d{3})*(?:\.\d+)?)\s*/?\s*month', md, re.I)
    if not dailies and not monthlies:
        return False, "No daily/monthly budget figures found"
    return True, "%d daily + %d monthly budget refs found" % (len(dailies), len(monthlies))


def _check_csv(csv_content):
    if csv_content is None:
        return False, "No CSV file provided"
    required = ["campaign", "budget", "objective"]
    lower = csv_content.lower()
    found = [col for col in required if col in lower]
    missing = [col for col in required if col not in lower]
    if missing:
        return False, "Columns found: %s | Missing: %s" % (found, missing)
    return True, "All required columns present: %s" % found


def check_structure(eval_case, client_folder):
    """Validate client folder structure — wiki updated, downstream flags."""
    results = []
    cf = Path(client_folder)

    wiki = cf / "wiki"
    wiki_exists = wiki.is_dir() and any(wiki.iterdir()) if wiki.is_dir() else False
    results.append({"assertion": "wiki_updated", "passed": wiki_exists,
                     "detail": "wiki/ dir: " + ("exists with files" if wiki_exists else "MISSING or empty")})

    strat = wiki / "strategy.md" if wiki.is_dir() else cf / "wiki" / "strategy.md"
    results.append({"assertion": "strategy_in_wiki", "passed": strat.exists(),
                     "detail": "wiki/strategy.md: " + ("exists" if strat.exists() else "MISSING")})

    deliv = cf / "deliverables"
    has_md = any(deliv.glob("*strategy*.md")) if deliv.is_dir() else False
    has_html = any(deliv.glob("*dashboard*.html")) if deliv.is_dir() else False
    has_csv = (any(deliv.glob("*media-plan*.csv")) or any(deliv.glob("*media_plan*.csv"))) if deliv.is_dir() else False
    results.append({"assertion": "deliverables_complete", "passed": has_md and has_html,
                     "detail": "MD: %s | HTML: %s | CSV: %s" % (_yn(has_md), _yn(has_html), _yn(has_csv))})

    downstream = False
    for fp in [wiki / "log.md", wiki / "strategy.md", strat]:
        if fp.exists():
            content = fp.read_text(encoding="utf-8", errors="ignore")
            if re.search(r'downstream|ad-copywriter|campaign-setup', content, re.I):
                downstream = True
                break
    results.append({"assertion": "downstream_flagged", "passed": downstream,
                     "detail": "Downstream skill connections " + ("flagged" if downstream else "NOT flagged in wiki")})

    return results


def print_results(eval_case, results, mode):
    print("\n" + "=" * 60)
    print("  Eval #%d — %s" % (eval_case["id"], mode))
    print("  Prompt: %s..." % eval_case["prompt"][:70])
    print("=" * 60)

    passed = sum(1 for r in results if r["passed"] is True)
    failed = sum(1 for r in results if r["passed"] is False)
    manual = sum(1 for r in results if r["passed"] is None)

    for r in results:
        tag = "PASS" if r["passed"] is True else ("FAIL" if r["passed"] is False else "MANUAL")
        print("  [%s]  %s" % (tag, r["assertion"]))
        print("          %s" % r["detail"])

    print("\n  Results: %d passed | %d failed | %d manual review" % (passed, failed, manual))
    return failed


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python run_evals.py list")
        print("  python run_evals.py output-check <eval_id> <md_report> <html_dashboard> [csv_plan]")
        print("  python run_evals.py structure-check <eval_id> <client_folder>")
        sys.exit(1)

    evals = load_evals()
    mode = sys.argv[1]

    if mode == "list":
        list_evals(evals)
        return

    if len(sys.argv) < 3:
        print("Need eval_id and file path(s)")
        sys.exit(1)

    eval_id = int(sys.argv[2])
    eval_case = next((e for e in evals if e["id"] == eval_id), None)
    if not eval_case:
        print("Eval #%d not found. Available: %s" % (eval_id, [e["id"] for e in evals]))
        sys.exit(1)

    if mode == "output-check":
        if len(sys.argv) < 5:
            print("Need: <eval_id> <md_report> <html_dashboard> [csv_plan]")
            sys.exit(1)
        md = Path(sys.argv[3]).read_text(encoding="utf-8")
        html = Path(sys.argv[4]).read_text(encoding="utf-8")
        csv_content = Path(sys.argv[5]).read_text(encoding="utf-8") if len(sys.argv) > 5 else None
        results = check_output(eval_case, md, html, csv_content)
        failures = print_results(eval_case, results, "Output Validation")
        sys.exit(1 if failures > 0 else 0)

    elif mode == "structure-check":
        if len(sys.argv) < 4:
            print("Need: <eval_id> <client_folder>")
            sys.exit(1)
        results = check_structure(eval_case, sys.argv[3])
        failures = print_results(eval_case, results, "Structure Validation")
        sys.exit(1 if failures > 0 else 0)

    else:
        print("Unknown mode: %s. Use 'list', 'output-check', or 'structure-check'" % mode)
        sys.exit(1)


if __name__ == "__main__":
    main()
