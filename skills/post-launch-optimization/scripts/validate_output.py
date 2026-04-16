#!/usr/bin/env python3
"""Post-Launch Optimization — Output Validation Script

Usage: python3 validate_output.py <file1> [file2] ...
Files are detected by name pattern:
  *-optimization-report.md  → Optimization report
  *-optimization-dashboard.html → Dashboard
  *optimization-config.json → Client config
"""

import sys
import os
import re
import json

criticals = []
warnings = []
infos = []
total_criticals = 0
total_warnings = 0

def log_critical(msg): criticals.append(msg)
def log_warning(msg): warnings.append(msg)
def log_info(msg): infos.append(msg)

def flush_logs():
    global total_criticals, total_warnings
    for msg in criticals: print(f"  \U0001f6a8 [CRITICAL] {msg}")
    for msg in warnings: print(f"  \u26a0\ufe0f [WARNING] {msg}")
    for msg in infos: print(f"  \u2139\ufe0f [INFO] {msg}")
    total_criticals += len(criticals)
    total_warnings += len(warnings)
    criticals.clear(); warnings.clear(); infos.clear()


def classify_file(path):
    name = os.path.basename(path).lower()
    if 'optimization-report' in name and name.endswith('.md'): return 'report'
    if 'optimization-dashboard' in name and name.endswith('.html'): return 'dashboard'
    if 'optimization-config' in name and name.endswith('.json'): return 'config'
    return None


def validate_report(path):
    with open(path, 'r') as f:
        content = f.read()
    lines = content.strip().split('\n')

    if len(lines) < 30:
        log_critical(f"Report too short — {len(lines)} lines (minimum 30 expected)")

    # Check required sections
    required_sections = [
        ('Executive Summary', 'executive summary'),
        ('Account Health', 'account health'),
        ('Top Actions', 'top actions'),
    ]
    for label, pattern in required_sections:
        if not re.search(pattern, content, re.I):
            log_critical(f"Missing required section: {label}")

    # Check source labels
    data_labels = content.count('[DATA]')
    calc_labels = content.count('[CALCULATED]')
    bench_labels = content.count('[BENCHMARK]')
    inferred_labels = content.count('[INFERRED]')
    total_labels = data_labels + calc_labels + bench_labels + inferred_labels
    if total_labels < 3:
        log_warning(f"Low source label count ({total_labels}) — every finding needs a source label")

    # Check for action items
    kill_count = len(re.findall(r'\[KILL\]', content))
    scale_count = len(re.findall(r'\[SCALE\]', content))
    test_count = len(re.findall(r'\[TEST\]', content))
    adjust_count = len(re.findall(r'\[ADJUST\]', content))
    negative_count = len(re.findall(r'\[NEGATIVE\]', content))
    total_actions = kill_count + scale_count + test_count + adjust_count + negative_count

    # Check health status indicators
    green_count = content.count('\U0001f7e2')
    amber_count = content.count('\U0001f7e1')
    red_count = content.count('\U0001f534')
    baseline_count = content.upper().count('BASELINE')

    # Check executive summary length
    exec_match = re.search(r'## Executive Summary\s*\n(.*?)(?=\n## |\n---)', content, re.DOTALL)
    if exec_match:
        exec_lines = [l for l in exec_match.group(1).strip().split('\n') if l.strip()]
        if len(exec_lines) > 7:
            log_warning(f"Executive summary too long ({len(exec_lines)} lines, target <=5)")

    # Check for priority scores
    priority_scores = re.findall(r'\[Score:\s*(\d+)\]', content)

    # Layer coverage check
    layers_found = set()
    layer_keywords = {
        'health': ['health check', 'account health', 'health status'],
        'diagnosis': ['diagnosis', 'campaign performance', 'ad set analysis'],
        'prescription': ['top actions', 'kill', 'scale', 'prescription'],
        'creative': ['creative', 'fatigue', 'hook rate', 'hold rate'],
        'testing': ['test', 'testing recommendation'],
        'competitive': ['competitive', 'auction insight', 'competitor'],
        'benchmark': ['benchmark', 'industry'],
        'cross_platform': ['cross-platform', 'cross platform', 'unified'],
        'trend': ['trend', 'improving', 'degrading', 'stable'],
        'priority': ['priority', 'score:', 'impact'],
        'memory': ['since last', 'previous analysis', 'baseline'],
    }
    content_lower = content.lower()
    for layer, keywords in layer_keywords.items():
        if any(kw in content_lower for kw in keywords):
            layers_found.add(layer)

    log_info(f"Report stats: {len(lines)} lines, {total_labels} source labels, "
             f"{total_actions} action items, {len(priority_scores)} priority scores")
    log_info(f"Health status: {green_count} green, {amber_count} amber, {red_count} red, "
             f"{baseline_count} baseline")
    log_info(f"Layers covered: {len(layers_found)}/11 — {', '.join(sorted(layers_found))}")

    missing_layers = set(layer_keywords.keys()) - layers_found
    if missing_layers and baseline_count == 0:
        log_warning(f"Layers not detected: {', '.join(sorted(missing_layers))}")


def validate_dashboard(path):
    with open(path, 'r') as f:
        content = f.read()

    file_size = os.path.getsize(path)
    if file_size > 200000:
        log_warning(f"Dashboard file size {file_size/1000:.0f}KB (target <150KB)")

    # Check for dark mode
    if '#0a0a0a' not in content and '#1a1a1a' not in content and 'dark' not in content.lower():
        log_warning("Dashboard may not have dark mode styling")

    # Check for all 9 required components per output-format-spec.md
    components = {
        'header bar': bool(re.search(r'header|client.*name.*date|analysis.*number|overall.*health', content, re.I)),
        'health cards': bool(re.search(r'health.*card|status.*card|health.*status', content, re.I)),
        'spend pacing gauge': bool(re.search(r'pacing|gauge|budget.*consumed|budget.*progress', content, re.I)),
        'action priority cards': bool(re.search(r'action.*card|priority.*card|action.*priority|impact.*score', content, re.I)),
        'campaign ranking table': bool(re.search(r'campaign.*rank|campaign.*table|sortable.*campaign', content, re.I)),
        'creative grid': bool(re.search(r'creative.*grid|winner.*loser|top.*bottom.*creative', content, re.I)),
        'trend sparklines': bool(re.search(r'sparkline|trend.*chart|trend.*line|line.*chart', content, re.I)),
        'benchmark comparison': bool(re.search(r'benchmark.*chart|benchmark.*bar|client.*vs.*industry|benchmark.*comparison', content, re.I)),
        'cross-platform comparison': bool(re.search(r'cross.?platform|side.?by.?side|platform.*comparison', content, re.I)),
    }

    # Also check animation separately (design rule, not a component)
    if not re.search(r'@keyframes|animation|transition', content, re.I):
        log_warning("Dashboard missing animations (required: fade-in, counter, pulse)")

    missing = [k for k, v in components.items() if not v]
    if missing:
        log_critical(f"Dashboard missing required components ({len(missing)}/9): {', '.join(missing)}")

    # Check for embedded data
    if '<script' not in content:
        log_warning("No script tag found — dashboard needs embedded data for interactivity")

    log_info(f"Dashboard stats: {file_size/1000:.0f}KB, "
             f"components found: {sum(components.values())}/9")


def validate_config(path):
    with open(path, 'r') as f:
        try:
            config = json.load(f)
        except json.JSONDecodeError as e:
            log_critical(f"Invalid JSON in config: {e}")
            return

    required_keys = ['client_name', 'platforms', 'budget', 'targets']
    for key in required_keys:
        if key not in config:
            log_critical(f"Missing required config key: {key}")

    # Check platforms
    platforms = config.get('platforms', {})
    for platform, pconfig in platforms.items():
        if 'windsor_connector' not in pconfig:
            log_critical(f"Platform {platform} missing windsor_connector")
        if 'account_ids' not in pconfig:
            log_critical(f"Platform {platform} missing account_ids")
        if 'conversion_event' not in pconfig:
            log_critical(f"Platform {platform} missing conversion_event")

    # Check budget
    budget = config.get('budget', {})
    if not budget.get('monthly_total_aud'):
        log_warning("No monthly budget set — pacing calculations will be skipped")

    # Check targets
    targets = config.get('targets', {})
    mode = targets.get('mode')
    if mode not in ('baseline', 'fixed'):
        log_warning(f"Unknown target mode: {mode} (expected 'baseline' or 'fixed')")

    # Baseline date sanity check — detect stale config from a prior analysis
    # that wasn't updated. If baseline_set_date is more than ~100 days old and mode
    # is still 'baseline', the analyst is running decisions against stale baselines.
    # If it's in the future, something is broken. If history is empty but mode is baseline,
    # this is legitimately the first run — don't warn.
    baseline_date_str = targets.get('baseline_set_date')
    history = config.get('analysis_history', [])
    if baseline_date_str and mode == 'baseline':
        try:
            from datetime import datetime, timezone
            baseline_date = datetime.fromisoformat(baseline_date_str.replace('Z', '+00:00'))
            now = datetime.now(baseline_date.tzinfo or timezone.utc)
            age_days = (now - baseline_date).days
            if age_days < 0:
                log_critical(f"baseline_set_date {baseline_date_str} is in the future — config broken")
            elif age_days > 100 and len(history) >= 4:
                log_warning(
                    f"Baseline is {age_days} days old with {len(history)} prior analyses — "
                    f"consider recalibrating baselines (analysis-framework.md: every 4 analyses)"
                )
            else:
                log_info(f"Baseline age: {age_days} day(s), {len(history)} prior analysis(es)")
        except (ValueError, TypeError) as e:
            log_warning(f"Could not parse baseline_set_date '{baseline_date_str}': {e}")
    elif mode == 'baseline' and not baseline_date_str and history:
        log_warning(
            f"targets.mode is 'baseline' but baseline_set_date is missing while "
            f"{len(history)} prior analyses exist — config out of sync"
        )

    log_info(f"Config stats: {config.get('client_name', 'unknown')}, "
             f"platforms: {list(platforms.keys())}, "
             f"mode: {mode}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    files = {}
    for path in sys.argv[1:]:
        if not os.path.exists(path):
            print(f"  \u26a0\ufe0f  File not found: {path}")
            continue
        file_type = classify_file(path)
        if file_type:
            files[file_type] = path
        else:
            print(f"  \u26a0\ufe0f  Could not classify: {os.path.basename(path)}")

    print("\U0001f50d Post-Launch Optimization — Output Validation")
    for ftype, fpath in files.items():
        print(f"   {ftype:20s}: {fpath}")

    validators = [
        ('report', 'Optimization Report', validate_report),
        ('dashboard', 'Optimization Dashboard', validate_dashboard),
        ('config', 'Client Config', validate_config),
    ]

    for file_key, label, validator_fn in validators:
        if file_key in files:
            print(f"\n{'='*60}")
            print(f"  {label}")
            print(f"{'='*60}")
            validator_fn(files[file_key])
            flush_logs()

    # Final summary
    print(f"\n{'='*60}")
    if total_criticals > 0:
        print(f"  \u274c Validation FAILED — {total_criticals} critical issue(s), {total_warnings} warning(s)")
    else:
        print(f"  \u2705 Validation passed — no critical issues ({total_warnings} warning(s))")


if __name__ == '__main__':
    main()
