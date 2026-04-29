#!/usr/bin/env python3
"""Client-shareability validator.

Scans files for internal-process commentary that shouldn't appear in
client-facing deliverables. Patterns + rationale documented in
shared-context/client-shareability.md.

Usage:
    python3 ~/.claude/scripts/check_client_shareability.py {client_folder}
    python3 ~/.claude/scripts/check_client_shareability.py {file1} {file2} ...

Exits with non-zero if any CRITICAL pollution is detected. WARNING-only
findings (less certain) are reported but don't fail the check.

Updated 2026-04-29 for `_engine/` convention: client-facing files now sit at
folder root; `_engine/` is exempt (skill-only state).
"""

import sys
import re
import os
from pathlib import Path

# CRITICAL — these patterns are unambiguous internal commentary.
# Any match in a client-facing file fails validation.
CRITICAL_PATTERNS = [
    (r'\[Correction\s+\d{4}-\d{2}-\d{2}\]', 'date-stamped correction block'),
    (r'Pre-Launch Audit\s*\(\d{4}-\d{2}-\d{2}\)', 'dated pre-launch audit section'),
    (r'Reality Check Applied', 'reality-check audit framing'),
    (r'Earlier drafts? (cited|said|claimed|stated)', 'earlier-drafts admission'),
    (r'\(Was [^)]*at \$[\d.]+\s*assumed', 'was-vs-real CPC parenthetical'),
    (r'Updated \d{4}-\d{2}-\d{2} with (real|new|corrected|the actual)', 'date-stamped update note'),
    (r'(refreshed|revised|corrected) \d{4}-\d{2}-\d{2}', 'date-stamped revision note'),
    (r'Course Correction\s*·\s*(Disproven|Strengthened|Reframed)', 'course-correction tile framing'),
    (r'DISPROVEN by (keyword|data|research)', 'disproven framing'),
    (r'False [Cc]laims? removed', 'false-claims-removed audit'),
    (r'\d+ RSA mentions? stripped', 'stripped-mentions audit'),
    (r'AG\d+ reframed from', 'ad-group reframe note'),
    (r'\d+ keywords? dropped (during|after)', 'keywords-dropped audit'),
    (r'ACL §\d+', 'ACL legal-section reference'),
    (r'inflated \d+×', 'inflation-factor admission'),
    (r'Perplexity (conflated|hallucinat)', 'Perplexity-error admission'),
    (r'(was|were|earlier)\s+misattributed', 'misattribution admission'),
    # Note: "fabricated X" is intentionally NOT in the pattern set —
    # legitimate audit findings reference fabricated client content
    # ("no fabricated spot counts", "fabricated testimonials remain visible").
    # Use the Perplexity / hallucinat / inflated patterns above to catch the real
    # internal-process admissions.
    (r'\w+\s*→\s*\S+-\S+\s*skill', 'skill-name leakage'),
    (r'Run\s+\S+-\S+\s+skill', 'skill-name leakage (run instruction)'),
    (r'do_not_launch_until_phase_0', 'internal flag leakage'),
    (r'Gate\s+[AB]\s+FIRED', 'validator-gate reference'),
    (r'BEST CASE\s*[—-]\s*DO NOT LAUNCH', 'verdict banner leakage'),
    (r'phase_0_prerequisites', 'internal flag leakage'),
    (r'sitting unused', 'internal-status commentary'),
    (r'skill bug', 'internal skill-bug reference'),
    (r'silently ship', 'internal process commentary'),
]

# Files that are EXEMPT — these are intentionally internal
EXEMPT_PATHS = [
    '/_engine/',
    '/.claude/',
    '/.git/',
]


def is_exempt(path: str) -> bool:
    return any(seg in path for seg in EXEMPT_PATHS)


def is_client_facing(path: Path) -> bool:
    """Heuristic: is this path in a client-facing location?

    Under the `_engine/` convention, presentables sit at folder root and skill
    internals live inside `_engine/`. Client-facing = anything NOT under _engine/
    that's an HTML/MD/TXT file at folder root or inside a presentable bundle.
    """
    s = str(path)
    if is_exempt(s):
        return False
    if path.suffix.lower() not in {'.html', '.md', '.txt'}:
        return False
    return True


def scan_file(path: Path) -> list:
    """Return list of (line_no, pattern_label, snippet) findings."""
    try:
        text = path.read_text(encoding='utf-8', errors='ignore')
    except (OSError, UnicodeDecodeError):
        return []
    findings = []
    for line_no, line in enumerate(text.splitlines(), 1):
        for pattern, label in CRITICAL_PATTERNS:
            m = re.search(pattern, line, re.IGNORECASE)
            if m:
                snippet = line.strip()
                if len(snippet) > 120:
                    snippet = snippet[:120] + '...'
                findings.append((line_no, label, snippet))
    return findings


def collect_files(target: Path) -> list:
    """If target is a folder, walk for client-facing files; if a file, just it."""
    if target.is_file():
        return [target] if is_client_facing(target) else []
    if not target.is_dir():
        return []
    files = []
    for p in target.rglob('*'):
        if not p.is_file():
            continue
        if not is_client_facing(p):
            continue
        files.append(p)
    return files


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    targets = [Path(arg) for arg in sys.argv[1:]]
    all_files = []
    for t in targets:
        all_files.extend(collect_files(t))

    if not all_files:
        print('No client-facing files found in target(s).')
        sys.exit(0)

    print(f'Scanning {len(all_files)} client-facing file(s)...\n')

    total_findings = 0
    polluted_files = 0
    for f in all_files:
        findings = scan_file(f)
        if not findings:
            continue
        polluted_files += 1
        total_findings += len(findings)
        rel = f
        try:
            rel = f.relative_to(Path('/Users/digischola/Desktop'))
        except ValueError:
            pass
        print(f'X {rel}')
        for line_no, label, snippet in findings[:5]:
            print(f'   line {line_no}: {label}')
            print(f'      {snippet}')
        if len(findings) > 5:
            print(f'   ... +{len(findings) - 5} more')
        print()

    if total_findings == 0:
        print(f'OK All {len(all_files)} files clean - no internal commentary detected.')
        sys.exit(0)
    else:
        print(f'FAIL {polluted_files}/{len(all_files)} files contain internal commentary')
        print(f'   {total_findings} total finding(s).')
        print('\nSee shared-context/client-shareability.md for the full rule + remediation.')
        sys.exit(1)


if __name__ == '__main__':
    main()
