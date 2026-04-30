#!/usr/bin/env python3
"""Ad Copywriter — Output Validation Script

Usage: python3 validate_output.py <file1> [file2] [file3] ...
Files are detected by name pattern. Default short-name forms (preferred):
  ad-copy-report.md            → Ad copy report
  ad-copy-best-case.md         → Ad copy report (Gate A best-case)
  ad-copy-current-state.md     → Ad copy report (Gate A current-state)
  google-ads.csv               → Google Ads CSV
  meta-ads.csv                 → Meta Ads CSV
  image-prompts.md             → Image generation prompts
  video-storyboards.md         → Video storyboards
  creative-brief.json          → Upstream creative brief

Backwards-compat: legacy `{client}-`prefixed forms (e.g., `iskm-ad-copy-report.md`,
`thrive-google-ads.csv`) are also detected via substring match. Prefer the short
form for new client folders — folder location already encodes client + program.
"""

import sys
import os
import re
import csv
import json
from io import StringIO

criticals = []
warnings = []
infos = []
total_criticals = 0
total_warnings = 0

# Optional upstream creative brief (from paid-media-strategy). When present,
# it unlocks cross-validation: image_gen_prompt_prefix usage, message_match_notes
# echoed in copy, etc. Populated by main() before validators run.
CREATIVE_BRIEF = None

# Offerings.md content for Gate B service-offering cross-check.
# Populated by main() — looks up {client}/_engine/wiki/offerings.md (single-program)
# or {client-root}/_engine/wiki/offerings.md (multi-program) based on file path of inputs.
# See references/offerings-cross-check.md for protocol.
OFFERINGS_TEXT = None
OFFERINGS_PATH = None

# Track whether the analyst supplied both -best-case and -current-state outputs
# when Gate A fires. Populated by classify_file().
HAS_BEST_CASE_REPORT = False
HAS_CURRENT_STATE_REPORT = False

def log_critical(msg): criticals.append(msg)
def log_warning(msg): warnings.append(msg)
def log_info(msg): infos.append(msg)

def flush_logs():
    global total_criticals, total_warnings
    for msg in criticals: print(f"  🚨 [CRITICAL] {msg}")
    for msg in warnings: print(f"  ⚠️ [WARNING] {msg}")
    for msg in infos: print(f"  ℹ️ [INFO] {msg}")
    total_criticals += len(criticals)
    total_warnings += len(warnings)
    criticals.clear(); warnings.clear(); infos.clear()

def classify_file(path):
    global HAS_BEST_CASE_REPORT, HAS_CURRENT_STATE_REPORT
    name = os.path.basename(path).lower()
    if 'ad-copy-best-case' in name:
        HAS_BEST_CASE_REPORT = True
        return 'report_best_case'
    if 'ad-copy-current-state' in name:
        HAS_CURRENT_STATE_REPORT = True
        return 'report_current_state'
    if 'ad-copy-report' in name: return 'report'
    if 'google-ads' in name and name.endswith('.csv'): return 'google_csv'
    if 'meta-ads' in name and name.endswith('.csv'): return 'meta_csv'
    if 'image-prompts' in name: return 'image_prompts'
    if 'video-storyboard' in name: return 'video_storyboards'
    if 'creative-brief' in name and name.endswith('.json'): return 'creative_brief'
    if name.endswith('.html') and ('ad-copy-dashboard' in name or 'prompt-library' in name): return 'dashboard'
    return None


def _find_offerings_md(input_paths):
    """Walk up from any input path to find _engine/wiki/offerings.md.

    Used by Gate B (service-offering cross-check). Searches the new `_engine/` layout
    for both single-program and multi-program (where `_engine/` sits at the client
    root) clients. Returns (text, path) or (None, None).
    See references/offerings-cross-check.md for protocol.
    """
    candidates = []
    for ip in input_paths:
        cur = os.path.dirname(os.path.abspath(ip))
        # Walk up max 5 levels from each input file
        for _ in range(5):
            for sub in ('_engine/wiki/offerings.md', '_engine/wiki/business.md'):
                cand = os.path.join(cur, sub)
                if cand not in candidates:
                    candidates.append(cand)
            parent = os.path.dirname(cur)
            if parent == cur:
                break
            cur = parent
    for cand in candidates:
        if os.path.exists(cand):
            try:
                with open(cand, 'r', encoding='utf-8') as f:
                    return f.read(), cand
            except OSError:
                pass
    return None, None


def _detect_gate_a_triggers(brief):
    """Return list of Gate A trigger reasons (empty = not gated).

    See references/offerings-cross-check.md §"Gate A — Trigger conditions".
    """
    if not isinstance(brief, dict):
        return []
    triggers = []
    if brief.get('do_not_launch_until_phase_0_complete') is True:
        triggers.append('do_not_launch_until_phase_0_complete=true')
    prereqs = brief.get('phase_0_prerequisites') or []
    if isinstance(prereqs, list):
        gated = [p for p in prereqs if isinstance(p, dict)
                 and str(p.get('status', '')).upper() in {'GATED', 'BLOCKED', 'PENDING'}]
        if gated:
            triggers.append(f'{len(gated)} phase_0_prerequisites with GATED/BLOCKED/PENDING status')
    verdict = str(brief.get('verdict', '')).upper()
    if verdict in {'DO-NOT-LAUNCH', 'DO_NOT_LAUNCH', 'BEST-CASE', 'BEST_CASE', 'GATED'}:
        triggers.append(f'verdict={verdict}')
    framing = str(brief.get('framing', '')).lower()
    if 'best-case' in framing or 'best case' in framing:
        triggers.append(f'framing={framing}')
    return triggers


# Default gated-claim phrases that recur across wellness/yoga/fitness clients.
# Per references/offerings-cross-check.md, the brief's
# phase_0_prerequisites[].claim_phrases[] takes precedence; this is a fallback list.
DEFAULT_GATED_PHRASES = [
    'free trial', '7-day free trial', '14-day free trial', '7 day free trial',
    'try free', 'start free', 'free week', 'free month',
    'no credit card', 'cancel anytime free',
]


def _collect_gated_phrases(brief):
    """Extract claim_phrases from gated phase_0_prerequisites; fall back to defaults."""
    phrases = set()
    if isinstance(brief, dict):
        for p in brief.get('phase_0_prerequisites') or []:
            if not isinstance(p, dict):
                continue
            if str(p.get('status', '')).upper() not in {'GATED', 'BLOCKED', 'PENDING'}:
                continue
            for ph in p.get('claim_phrases') or []:
                if isinstance(ph, str) and ph.strip():
                    phrases.add(ph.strip().lower())
            # Use the prerequisite name itself as a phrase
            name = p.get('name')
            if isinstance(name, str) and name.strip():
                phrases.add(name.strip().lower())
    if not phrases:
        phrases = set(DEFAULT_GATED_PHRASES)
    return phrases


def validate_gate_a(files, brief):
    """Gate A — Phase-0 leakage prevention.

    If brief flags a gated launch state, output MUST be split into best-case +
    current-state reports, and CSV must be generated from current-state only.
    See references/offerings-cross-check.md §Gate A.
    """
    if not brief:
        log_info("Gate A skipped — no creative brief loaded")
        return False

    triggers = _detect_gate_a_triggers(brief)
    if not triggers:
        log_info("Gate A — not fired (brief has no Phase-0 / DO-NOT-LAUNCH / BEST-CASE flags)")
        return False

    log_info(f"Gate A FIRED — triggers: {', '.join(triggers)}")

    # Require both best-case + current-state files
    if not (HAS_BEST_CASE_REPORT and HAS_CURRENT_STATE_REPORT):
        if 'report' in files:
            log_critical(
                f"Gate A fired but only single ad-copy-report found. "
                f"Required: *-ad-copy-best-case.md AND *-ad-copy-current-state.md. "
                f"See references/offerings-cross-check.md §Gate A. "
                f"Fix: split the deliverable — best-case keeps gated claims; current-state strips them."
            )
        else:
            log_critical(
                "Gate A fired but no ad-copy report found at all. "
                "Generate both *-ad-copy-best-case.md and *-ad-copy-current-state.md."
            )

    # Scan CSVs for gated-claim phrases
    gated_phrases = _collect_gated_phrases(brief)
    for csv_key in ('google_csv', 'meta_csv'):
        if csv_key not in files:
            continue
        with open(files[csv_key], 'r', encoding='utf-8') as f:
            csv_text = f.read().lower()
        leaked = [p for p in gated_phrases if p in csv_text]
        if leaked:
            log_critical(
                f"Gate A leak — {csv_key} contains gated-claim phrases that should be stripped "
                f"from production CSV: {leaked[:5]}. Move these to best-case file only."
            )
    return True


# Service-claim phrase patterns for Gate B. Each pattern's match must appear
# in offerings.md (lemma-fuzzy). Patterns ordered by specificity — yoga-specific
# first, then general wellness/fitness/therapy. Extend per sector as needed.
SERVICE_CLAIM_PATTERNS = [
    # Yoga / wellness modalities
    (r'\bprenatal\s+yoga\b', 'prenatal yoga'),
    (r'\bpostnatal\s+yoga\b', 'postnatal yoga'),
    (r'\bpre[- ]postnatal\b', 'pre/postnatal yoga'),
    (r'\bchair\s+yoga\b', 'chair yoga'),
    (r'\bkids\s+yoga\b', 'kids yoga'),
    (r'\baerial\s+yoga\b', 'aerial yoga'),
    (r'\bhot\s+yoga\b', 'hot yoga'),
    (r'\bbikram\b', 'bikram yoga'),
    (r'\bashtanga\b', 'ashtanga yoga'),
    (r'\bkundalini\b', 'kundalini yoga'),
    (r'\brestorative\s+yoga\b', 'restorative yoga'),
    (r'\btrimester[- ]safe\b', 'trimester-safe modifications'),
    (r'\bpregnancy[- ]safe\b', 'pregnancy-safe modifications'),
    # Therapy / mental health modalities
    (r'\bemdr\b', 'EMDR therapy'),
    (r'\bketamine[- ]assisted\b', 'ketamine-assisted therapy'),
    (r'\bsomatic\s+(?:experiencing|therapy)\b', 'somatic therapy'),
    # Fitness specifics
    (r'\bcrossfit\b', 'CrossFit'),
    (r'\bf45\b', 'F45'),
    (r'\breformer\s+pilates\b', 'reformer pilates'),
    # Beauty / spa
    (r'\bhydrafacial\b', 'hydrafacial'),
    (r'\bmicroneedling\b', 'microneedling'),
    (r'\bchemical\s+peel\b', 'chemical peel'),
]


def validate_gate_b(files):
    """Gate B — Service-offering cross-check.

    Every service-claim phrase in copy must trace back to offerings.md. Fuzzy match.
    See references/offerings-cross-check.md §Gate B.
    """
    if not OFFERINGS_TEXT:
        log_warning(
            "Gate B unverified — no offerings.md found in {client}/_engine/wiki/ "
            "(single-program) or {client-root}/_engine/wiki/ (multi-program). "
            "Service claims in ad copy could not be cross-checked. "
            "See references/offerings-cross-check.md §Gate B."
        )
        return

    offerings_lower = OFFERINGS_TEXT.lower()

    # Aggregate copy text from all production outputs (skip best-case which is
    # forward-planning, not production).
    copy_text = ''
    for key in ('report', 'report_current_state', 'google_csv', 'meta_csv'):
        if key in files:
            try:
                with open(files[key], 'r', encoding='utf-8') as f:
                    copy_text += '\n' + f.read()
            except OSError:
                pass

    if not copy_text.strip():
        log_info("Gate B skipped — no production copy files to scan")
        return

    copy_lower = copy_text.lower()
    failed_claims = []
    verified_claims = []
    for pattern, label in SERVICE_CLAIM_PATTERNS:
        if not re.search(pattern, copy_lower):
            continue
        # Claim is in copy. Now check offerings.md.
        # Lemma-fuzzy: try the label, also try its head word.
        head_word = label.split()[0]
        if re.search(pattern, offerings_lower) or head_word.lower() in offerings_lower:
            verified_claims.append(label)
        else:
            failed_claims.append(label)

    if failed_claims:
        log_critical(
            f"Gate B FAILED — {len(failed_claims)} service claim(s) in ad copy not found in "
            f"offerings.md ({OFFERINGS_PATH}): {failed_claims}. "
            f"Either drop the claim, reframe to a verified offering, or wrap as "
            f"<<UNVERIFIED-CLAIM:phrase>>. See references/offerings-cross-check.md §Gate B."
        )
    if verified_claims:
        log_info(f"Gate B — {len(verified_claims)} service claim(s) verified against offerings.md: {verified_claims}")
    if not failed_claims and not verified_claims:
        log_info(f"Gate B — no specific service claims detected (offerings source: {OFFERINGS_PATH})")

def _brief_collect_strings(node, keys):
    """Walk the creative brief dict and collect all string values for given keys."""
    found = []
    if isinstance(node, dict):
        for k, v in node.items():
            if k in keys and isinstance(v, str) and v.strip():
                found.append(v.strip())
            elif isinstance(v, (dict, list)):
                found.extend(_brief_collect_strings(v, keys))
    elif isinstance(node, list):
        for item in node:
            found.extend(_brief_collect_strings(item, keys))
    return found

def _significant_phrases(text, min_word_len=4):
    """Extract significant words/phrases from free text for fuzzy presence matching."""
    # Tokenize on non-word chars; keep words >= min_word_len chars (skips 'a', 'the', etc.)
    words = re.findall(r"[A-Za-z][A-Za-z'-]+", text)
    return [w.lower() for w in words if len(w) >= min_word_len]

def validate_report(path):
    with open(path, 'r') as f:
        content = f.read()
    lines = content.strip().split('\n')

    if len(lines) < 50:
        log_critical(f"Report too short — {len(lines)} lines (minimum 50 expected)")

    # Source labels
    brief_count = content.count('[BRIEF]')
    generated_count = content.count('[GENERATED]')
    adapted_count = content.count('[ADAPTED]')
    total_labels = brief_count + generated_count + adapted_count
    if total_labels < 5:
        log_warning(f"Low source label count ({total_labels}) — expect [BRIEF], [GENERATED], [ADAPTED] on copy blocks")

    # Framework mentions
    frameworks = []
    for fw in ['PAS', 'BAB', 'AIDA', 'Feature-Benefit-Proof', 'Social Proof Stack', 'Before-After-Bridge', 'Problem-Agitate-Solution']:
        if fw in content:
            frameworks.append(fw)

    # Count ad copy blocks (look for headlines)
    headline_blocks = len(re.findall(r'(?i)headline|H\d{1,2}:', content))

    # Creative-brief cross-check: message_match_notes must be echoed in the copy.
    # The brief's landing_page.message_match_notes captures what the LP hero repeats from
    # the ad — losing this alignment is a proven conversion killer (+20-35% lift cited).
    # Approach: extract message_match_notes strings; require at least 50% of significant
    # words (≥4 chars) to appear somewhere in the copy report.
    if CREATIVE_BRIEF:
        mm_notes = _brief_collect_strings(CREATIVE_BRIEF, {'message_match_notes'})
        if mm_notes:
            misses = []
            content_lower = content.lower()
            for note in mm_notes:
                sig_words = list(set(_significant_phrases(note)))
                if not sig_words:
                    continue
                hits = sum(1 for w in sig_words if w in content_lower)
                coverage = hits / len(sig_words)
                if coverage < 0.5:
                    misses.append(f"'{note[:50]}...' ({hits}/{len(sig_words)} words in copy, {coverage:.0%})")
            if misses:
                log_warning(f"Message match weak — creative brief message_match_notes under-represented in copy ({len(misses)} note(s)): {misses[:2]}")
            else:
                log_info(f"Message match verified — {len(mm_notes)} message_match_notes echoed in copy")

    log_info(f"Report stats: {len(lines)} lines, {total_labels} source labels, frameworks: {', '.join(frameworks) or 'none detected'}")

def validate_google_csv(path):
    with open(path, 'r') as f:
        content = f.read()

    reader = csv.reader(StringIO(content))
    rows = list(reader)
    if len(rows) < 2:
        log_critical("Google CSV has no data rows")
        return

    header = [h.strip().lower() for h in rows[0]]
    rsa_count = 0
    headline_violations = []
    desc_violations = []
    path_violations = []
    total_headlines = 0
    total_descs = 0

    for row_idx, row in enumerate(rows[1:], 2):
        if len(row) < len(header):
            continue

        row_dict = dict(zip(header, row))
        rsa_count += 1

        # Check headlines (H1-H15 or Headline 1-15)
        for i in range(1, 16):
            for key_pattern in [f'h{i}', f'headline {i}', f'headline{i}']:
                val = row_dict.get(key_pattern, '').strip()
                if val:
                    total_headlines += 1
                    if len(val) > 30:
                        headline_violations.append(f"Row {row_idx}, H{i}: '{val}' ({len(val)} chars, max 30)")
                    elif len(val) > 28:
                        log_warning(f"Row {row_idx}, H{i}: '{val}' ({len(val)} chars — close to 30 limit)")

        # Check descriptions (D1-D4)
        for i in range(1, 5):
            for key_pattern in [f'd{i}', f'description {i}', f'description{i}']:
                val = row_dict.get(key_pattern, '').strip()
                if val:
                    total_descs += 1
                    if len(val) > 90:
                        desc_violations.append(f"Row {row_idx}, D{i}: '{val[:40]}...' ({len(val)} chars, max 90)")

        # Check path fields
        for key_pattern in ['path 1', 'path1', 'path 2', 'path2']:
            val = row_dict.get(key_pattern, '').strip()
            if val and len(val) > 15:
                path_violations.append(f"Row {row_idx}: path '{val}' ({len(val)} chars, max 15)")

    for v in headline_violations:
        log_critical(f"Headline over 30 chars: {v}")
    for v in desc_violations:
        log_critical(f"Description over 90 chars: {v}")
    for v in path_violations:
        log_critical(f"Path over 15 chars: {v}")

    if rsa_count > 0 and total_headlines / rsa_count < 8:
        log_warning(f"Average {total_headlines/rsa_count:.0f} headlines per RSA (Google recommends 8-10 minimum)")

    log_info(f"Google CSV stats: {rsa_count} RSAs, {total_headlines} headlines, {total_descs} descriptions")

def validate_meta_csv(path):
    with open(path, 'r') as f:
        content = f.read()

    reader = csv.reader(StringIO(content))
    rows = list(reader)
    if len(rows) < 2:
        log_critical("Meta CSV has no data rows")
        return

    header = [h.strip().lower() for h in rows[0]]
    ad_count = 0
    missing_primary = 0
    long_primary = 0
    long_headline = 0
    long_desc = 0
    ab_variants = 0

    for row_idx, row in enumerate(rows[1:], 2):
        if len(row) < len(header):
            continue
        row_dict = dict(zip(header, row))
        ad_count += 1

        primary = row_dict.get('primary text', '').strip()
        headline = row_dict.get('headline', '').strip()
        desc = row_dict.get('description', '').strip()
        ad_name = row_dict.get('ad name', '').strip()

        if not primary:
            missing_primary += 1
        elif len(primary) > 125:
            long_primary += 1

        if headline and len(headline) > 40:
            long_headline += 1
        if desc and len(desc) > 30:
            long_desc += 1

        if re.search(r'hook[- ]?[ab]|variant[- ]?[ab]|test[- ]?[ab]', ad_name, re.I):
            ab_variants += 1

    if missing_primary > 0:
        log_critical(f"{missing_primary} Meta ads missing primary text")
    if long_primary > 0:
        log_warning(f"{long_primary} Meta ads with primary text over 125 chars (will be truncated in feed)")
    if long_headline > 0:
        log_warning(f"{long_headline} Meta ads with headline over 40 chars")
    if long_desc > 0:
        log_warning(f"{long_desc} Meta ads with description over 30 chars")

    log_info(f"Meta CSV stats: {ad_count} ads, {ab_variants} A/B variants detected")

def validate_image_prompts(path):
    with open(path, 'r') as f:
        content = f.read()

    # Find prompt blocks
    prompts = re.findall(r'(?:```|>)\s*(.+?)(?:```|\n\n)', content, re.DOTALL)
    if not prompts:
        # Try line-based detection
        prompts = re.findall(r'(?:Prompt|prompt):\s*(.+?)(?:\n\n|\n(?:Aspect|Text|Priority))', content, re.DOTALL)

    total_prompts = max(len(prompts), content.lower().count('prompt'))
    short_prompts = sum(1 for p in prompts if len(p.split()) < 30)

    # Check for aspect ratio mentions
    aspect_mentions = len(re.findall(r'\d+:\d+|aspect ratio|4:5|9:16|1:1|1\.91:1|16:9', content, re.I))
    if aspect_mentions < 2:
        log_warning("Few aspect ratio mentions in image prompts — ensure each prompt specifies ratio")

    p1_count = content.upper().count('P1')
    p2_count = content.upper().count('P2')

    if short_prompts > 0:
        log_warning(f"{short_prompts} image prompts under 30 words (may be too short for quality output)")

    # 2026-04-28 mandates from references/image-prompt-patterns.md:
    # (1) Standalone-prompt mandate — no [universal prefix] placeholders
    # (2) Dual-format mandate — both spec-prose and JSON forms per cell
    # (3) Reference-image flagging — requires_reference_image / reference_subject metadata
    placeholder_hits = re.findall(r'\[universal prefix\]|\{prefix\}|\[prefix\]|\[image_gen_prompt_prefix\]', content, re.I)
    if placeholder_hits:
        log_critical(f"{len(placeholder_hits)} unresolved prefix placeholder(s) in image prompts — every prompt must be standalone-complete (per 2026-04-28 standalone-prompt mandate)")

    json_format_present = bool(re.search(r'JSON\s+format|"output":\s*\{|"brand_system":\s*\{|"text_elements":\s*\[', content))
    spec_prose_present = bool(re.search(r'Spec-prose\s+format|BRAND DESIGN SYSTEM|COMPOSITION GRID', content, re.I))
    if not (json_format_present and spec_prose_present):
        missing = []
        if not json_format_present: missing.append("JSON")
        if not spec_prose_present: missing.append("spec-prose")
        log_warning(f"Dual-format mandate not met — missing {' + '.join(missing)} format. Per 2026-04-28 rule, every image prompt MUST exist in both forms for analyst tool-fit testing.")

    ref_flag_hits = re.findall(r'requires_reference_image|reference_subject|reference_image_attached', content, re.I)
    if not ref_flag_hits:
        log_warning("No reference-image metadata found (`requires_reference_image` / `reference_subject`). Per 2026-04-28 rule, every prompt must carry reference flags so the dashboard can surface attachment requirements. Flag `false` is also a valid value — but the field must exist.")

    # Designer-brain mandate (2026-04-29) — seven required blocks per prompt
    # See references/image-prompt-patterns.md §"Designer-brain mandate" for full spec.
    # Hard-floor: every prompt MUST include all seven blocks (or explicitly mark a block
    # as `intentionally omitted because <reason>`). Quality scoring layered on top.
    seven_blocks = {
        'BRAND DESIGN SYSTEM': r'BRAND DESIGN SYSTEM|"brand_system"\s*:',
        'COMPOSITION GRID': r'COMPOSITION GRID|COMPOSITION ARCHITECTURE|"composition(_grid)?"\s*:',
        'SUBJECT (frame coordinates)': r'SUBJECT(\b|\s)|"subject"\s*:',
        'LIGHT + SURFACE': r'LIGHT(\s|\+|/)|LIGHTING(\s|/|:)|photography_style|"light(ing)?"\s*:|hardness|falloff',
        'TEXT ELEMENTS': r'TEXT ELEMENTS|EMBEDDED TEXT|HEADLINE TEXT|"text_elements"\s*:|exact_copy',
        'DECORATIVE / VECTOR': r'DECORATIVE|VECTOR ELEMENTS|MOTIF|gradient|motif|"decorative_elements"\s*:|"vector_(elements|vocabulary)"\s*:|intentionally omitted',
        'NEGATIVE CONSTRAINTS + RENDER QUALITY': r'NEGATIVE\b|"negative_constraints"\s*:|RENDER QUALITY|"render_quality"\s*:',
    }
    block_block_pattern = re.compile(r'(?:^## Image \d+|^## Cell \d+)', re.MULTILINE)
    block_starts = [m.start() for m in block_block_pattern.finditer(content)]
    block_starts.append(len(content))
    per_prompt_misses = []
    quality_scores = []
    for i in range(len(block_starts) - 1):
        prompt_text = content[block_starts[i]:block_starts[i + 1]]
        # Skip if this is the file header before any prompts
        if i == 0 and 'Image 1' not in prompt_text and 'Cell 1' not in prompt_text:
            continue
        missing = []
        for block_name, pattern in seven_blocks.items():
            if not re.search(pattern, prompt_text, re.I):
                missing.append(block_name)
        # Quality score — counts depth markers per prompt
        depth_markers = {
            'pixel_coordinates': len(re.findall(r'\d+\s*px|\d+×\d+|\d+x\d+\s*pixels|columns?\s*\d', prompt_text, re.I)),
            'hex_colors': len(re.findall(r'#[0-9a-f]{3,8}\b', prompt_text, re.I)),
            'typography_specs': len(re.findall(r'weight\s*\d{3}|font[:_-]\w+|letter[- ]spacing|size:\s*\d+', prompt_text, re.I)),
            'light_direction': len(re.findall(r'\d+°|hardness|falloff|backlit|side-light|from upper|cinematic light', prompt_text, re.I)),
            'exact_copy_strings': len(re.findall(r'exact_copy|Exact copy:', prompt_text, re.I)),
            'negative_count': len(re.findall(r'No [A-Z]\w+|negative_constraints', prompt_text)),
        }
        depth_score = sum(min(v, 5) for v in depth_markers.values())  # cap each at 5; max ~30
        quality_scores.append(depth_score)
        # Get prompt label for reporting
        label_match = re.search(r'^## (Image \d+|Cell \d+)[^\n]*', prompt_text, re.MULTILINE)
        label = label_match.group(0).strip('# ').strip() if label_match else f'block-{i}'
        if missing:
            per_prompt_misses.append((label, missing))

    if per_prompt_misses:
        for label, missing_blocks in per_prompt_misses[:10]:  # cap report
            log_critical(f"Designer-brain HARD FLOOR violation in '{label}': missing required block(s) {missing_blocks}. See references/image-prompt-patterns.md §Designer-brain mandate. Mark intentionally-omitted blocks explicitly.")
        if len(per_prompt_misses) > 10:
            log_critical(f"... and {len(per_prompt_misses) - 10} more prompts with missing required blocks.")
    elif quality_scores:
        avg_score = sum(quality_scores) / len(quality_scores)
        min_score = min(quality_scores)
        log_info(f"Designer-brain depth: avg score {avg_score:.1f}/30, min {min_score}/30 across {len(quality_scores)} prompts (hard floor: all 7 blocks present).")
        if avg_score < 12:
            log_warning(f"Designer-brain quality score average {avg_score:.1f}/30 is shallow. Reference floor (Digischola Self-Audit) averages 22+. Consider adding pixel coordinates, hex colors, typography weights, light direction in degrees, exact_copy strings, explicit negative constraints.")
        if min_score < 8:
            shallow_idx = [i for i, s in enumerate(quality_scores) if s < 8]
            log_warning(f"{len(shallow_idx)} prompt(s) under quality floor 8/30 — these prompts have all 7 blocks but the blocks are sparse. Designer-brain depth needed: pixel coordinates, hex specifics, typography weights, light direction.")

    # Creative-brief cross-check: image_gen_prompt_prefix must flow through.
    # image-prompt-patterns.md Rule #1: never deviate from the prefix. Without this
    # check, a skill run can silently drop the brand-consistent prompt prefix and
    # produce off-brand imagery despite the brief's instruction.
    if CREATIVE_BRIEF:
        prefixes = _brief_collect_strings(CREATIVE_BRIEF, {'image_gen_prompt_prefix'})
        if prefixes:
            # Normalize both sides — strip punctuation, collapse whitespace — then
            # check if a 5-word distinctive window from the prefix appears in the content.
            # Prevents false positives from comma/hyphen differences between brief and prompts.
            content_tokens = ' '.join(_significant_phrases(content, min_word_len=3))
            missing_prefixes = []
            for prefix in prefixes:
                words = _significant_phrases(prefix, min_word_len=3)
                if not words:
                    continue
                window_size = min(5, len(words))
                found = any(
                    ' '.join(words[i:i+window_size]) in content_tokens
                    for i in range(len(words) - window_size + 1)
                )
                if not found:
                    missing_prefixes.append(prefix[:60] + ('...' if len(prefix) > 60 else ''))
            if missing_prefixes:
                log_critical(f"image_gen_prompt_prefix from creative brief not found in image prompts ({len(missing_prefixes)} prefix(es) missing): {missing_prefixes[:2]}")
            else:
                log_info(f"Image prompt prefix(es) from creative brief verified in output ({len(prefixes)} checked)")

    log_info(f"Image prompts stats: ~{total_prompts} prompts, {p1_count} P1, {p2_count} P2")

def validate_video_storyboards(path):
    with open(path, 'r') as f:
        content = f.read()

    # Count frames
    frames = re.findall(r'(?i)frame\s*\d+', content)
    videos = re.findall(r'(?i)(?:video|storyboard)\s*(?:\d+|#\d+|:)', content)

    # Check voiceover (accept **Voiceover:** markdown-bold form too; strip leading/trailing asterisks from label)
    vo_sections = re.findall(r'(?i)\*{0,2}voiceover:\*{0,2}\s*(.+)', content)
    frames_without_vo = len(frames) - len(vo_sections)

    # Check for stage directions in VO (bad for AI voice)
    stage_direction_pattern = r'(?i)\(.*?\)|\[.*?\]|read with|say with|emphasis on|pause here'
    stage_directions = re.findall(stage_direction_pattern, '\n'.join(vo_sections))

    if stage_directions:
        log_warning(f"Voiceover contains stage directions ({len(stage_directions)} found) — AI voice tools need clean text only: {stage_directions[:3]}")

    if frames_without_vo > 0:
        log_warning(f"{frames_without_vo} frames missing voiceover text")

    # Check text overlay (accept **Text Overlay:** markdown-bold form too)
    text_overlays = re.findall(r'(?i)\*{0,2}text overlay:\*{0,2}\s*(.+)', content)

    # Check for combined VO script
    has_combined_vo = bool(re.search(r'(?i)combined|full.*script|complete.*voiceover|vo.*script', content))
    if not has_combined_vo:
        log_warning("No combined VO script section found — needed for pasting into AI Studio")

    # Word count of all VO
    total_vo_words = sum(len(s.split()) for s in vo_sections)

    # Per-frame VO word count vs duration budget. Spec from video-storyboard-spec.md:
    # 6s bumper = 0 words, 15s = 35-40 words total, 30s = 70-80 words total.
    # Frame-level: assume ~3s per frame average; flag if a single frame's VO > 25 words
    # (unreadable at AI-voice pace) or entire storyboard exceeds 30s video budget (~90 words).
    per_frame_word_counts = [len(s.split()) for s in vo_sections]
    bloated_frames = [n for n in per_frame_word_counts if n > 25]
    if bloated_frames:
        log_warning(f"{len(bloated_frames)} frame(s) with >25 words of VO — too dense for ~3s frame pace; AI voice will feel rushed")
    # Total VO vs implied duration. Look for explicit duration hints in content.
    duration_match = re.search(r'(\d{1,3})\s*(?:s\b|second|sec\b)', content.lower())
    if duration_match and total_vo_words > 0:
        declared_sec = int(duration_match.group(1))
        # Rough budget: ~2.5 words/second for AI voice; flag if >20% over budget.
        budget = int(declared_sec * 2.5 * 1.2)
        if total_vo_words > budget:
            log_warning(f"Total VO ~{total_vo_words} words for ~{declared_sec}s video — exceeds {budget}-word budget (2.5 wps AI voice pace)")

    log_info(f"Video storyboard stats: ~{max(len(videos),1)} videos, {len(frames)} frames, {len(vo_sections)} VO sections, {total_vo_words} VO words")

def validate_format_aspect_consistency(image_prompts_path, creative_brief_path=None):
    """Cross-check image-prompts.md aspect ratios against creative-brief.json format_priority.

    Patched 2026-04-30 after WLF-AD-01 carousel cards shipped at 4:5 (single-image format)
    instead of 1:1 (Meta carousel mandatory). Reference image-prompt-patterns.md line 329:
    "1:1 Square — Feed Fallback / Carousel Cards" — rule already documented but not enforced.

    Format → required aspect ratio mapping (Meta + Google specs):
      - carousel / carousel_5_card / lp_redirect_carousel  → 1:1 ONLY (all cards must match)
      - single_image                                         → 4:5 preferred (1:1 acceptable)
      - single_image_1_1                                     → 1:1
      - video_15s_reel / video_9_16_reel / vertical          → 9:16
      - video_1_1                                            → 1:1
      - google_display                                       → 1.91:1 or 1:1
      - google_display_square                                → 1:1
    """
    if not os.path.exists(image_prompts_path):
        return
    with open(image_prompts_path, 'r') as f:
        prompts_text = f.read()

    brief = None
    if creative_brief_path and os.path.exists(creative_brief_path):
        try:
            with open(creative_brief_path, 'r') as f:
                brief = json.load(f)
        except (json.JSONDecodeError, IOError):
            pass

    # Build format → required aspect map from creative-brief
    creative_aspect_map = {}  # creative_id → set of allowed aspect ratios
    if brief:
        for creative in brief.get("creatives", []):
            cid = creative.get("id", "")
            formats = creative.get("format_priority", [])
            allowed_aspects = set()
            for fmt in formats:
                fmt_lower = fmt.lower()
                if "carousel" in fmt_lower:
                    allowed_aspects.add("1:1")
                elif "9_16" in fmt_lower or "9:16" in fmt_lower or "reel" in fmt_lower or "story" in fmt_lower:
                    allowed_aspects.add("9:16")
                elif "1_1" in fmt_lower or "1:1" in fmt_lower or "square" in fmt_lower:
                    allowed_aspects.add("1:1")
                elif "single_image" in fmt_lower or "feed" in fmt_lower:
                    allowed_aspects.update(["4:5", "1:1"])
                elif "1.91" in fmt_lower or "display" in fmt_lower:
                    allowed_aspects.add("1.91:1")
            if allowed_aspects:
                creative_aspect_map[cid] = allowed_aspects

    # Parse image-prompts.md for prompt blocks: heading + their aspect ratio
    # Pattern: "## Prompt N — {creative_id}-CARD-N" or "## Prompt N — {creative_id}"
    prompt_blocks = re.findall(
        r'^## Prompt \d+\s+[—-]\s+([A-Z][A-Z0-9-]*)\b.*?(?=^## Prompt|\Z)',
        prompts_text,
        re.MULTILINE | re.DOTALL,
    )
    full_blocks = re.split(r'^## Prompt \d+\s+[—-]\s+', prompts_text, flags=re.MULTILINE)[1:]

    mismatches = []
    for block in full_blocks:
        # First line is the heading: "{CREATIVE_ID} (...)"
        heading_m = re.match(r'([A-Z][A-Z0-9-]*)', block)
        if not heading_m:
            continue
        prompt_id = heading_m.group(1)
        # Strip "-CARD-N" suffix to get parent creative ID
        parent_id = re.sub(r'-CARD-\d+$', '', prompt_id)

        # Find aspect ratio in this prompt block
        aspect_m = re.search(r'(?:Aspect(?:\s+ratio)?|aspect_ratio)["\s:*]+(\d+:\d+(?:\.\d+)?|1\.91:1)', block)
        if not aspect_m:
            continue
        actual_aspect = aspect_m.group(1)

        # Check against creative-brief.json mapping
        if parent_id in creative_aspect_map:
            allowed = creative_aspect_map[parent_id]
            if actual_aspect not in allowed:
                mismatches.append({
                    "prompt_id": prompt_id,
                    "parent_creative": parent_id,
                    "actual_aspect": actual_aspect,
                    "allowed_aspects": sorted(allowed),
                })

    if mismatches:
        for m in mismatches:
            log_critical(
                f"Aspect-ratio mismatch: {m['prompt_id']} uses {m['actual_aspect']}, "
                f"but parent creative {m['parent_creative']}'s format_priority requires "
                f"{'/'.join(m['allowed_aspects'])}. Reference: image-prompt-patterns.md §carousel-cards-1:1-rule."
            )
    else:
        log_info(f"Format/aspect-ratio cross-check passed ({len(creative_aspect_map)} creatives mapped from creative-brief.json)")


def validate_carousel_card_count(image_prompts_path, creative_brief_path=None):
    """Cross-check carousel card count: brief's `carousel_N_card` must match N CARD-X prompts.

    Patched 2026-04-30 after WLF-AD-01 shipped 4 carousel cards (CARD-1, 2, 4, 5) when
    creative-brief.json specified `format_priority: ["carousel_5_card", ...]` — analyst-brain
    decided 4 cards told the story, no validator caught the gap. Same failure class as the
    4:5/1:1 aspect bug: brief format-spec ignored at authoring time, no enforcement.

    Detection rule:
      - Parse creative-brief.json for creatives whose format_priority contains `carousel_N_card`
        (or `carousel_N_card_static`) where N is an integer.
      - For each such creative, count distinct `{creative_id}-CARD-K` prompts in image-prompts.md.
      - CRITICAL on count mismatch (expected N, found M ≠ N).
      - Also CRITICAL if CARD-K indices have gaps (e.g. CARD-1, 2, 4, 5 missing CARD-3).
      - `lp_redirect_carousel` / bare `carousel` (no _N_card pattern) → WARNING only (count implicit).
    """
    if not os.path.exists(image_prompts_path):
        return
    with open(image_prompts_path, 'r') as f:
        prompts_text = f.read()

    brief = None
    if creative_brief_path and os.path.exists(creative_brief_path):
        try:
            with open(creative_brief_path, 'r') as f:
                brief = json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    if not brief:
        return

    # Build creative_id → expected_card_count map.
    # Rule: only enforce the P1 (primary) format — format_priority[0]. P2+ formats are
    # advisory/optional per SKILL.md Step 6 "P1/P2 priority" convention. If P1 is
    # `carousel_N_card`, N is mandatory. If P1 is bare `carousel`/`lp_redirect_carousel`,
    # warn only. If P1 is non-carousel, even P2 carousel is advisory (skip enforcement).
    expected_counts = {}  # creative_id → int (expected card count)
    soft_carousel = []    # creative_id list — P1 is bare carousel, no N specified
    for creative in brief.get("creatives", []):
        cid = creative.get("id", "")
        formats = creative.get("format_priority", [])
        if not formats:
            continue
        primary = formats[0].lower()
        m = re.search(r'carousel_(\d+)_card', primary)
        if m:
            expected_counts[cid] = int(m.group(1))
        elif "carousel" in primary:
            soft_carousel.append(cid)
        # else: P1 is non-carousel → even if P2 is carousel, treat as advisory; skip

    if not expected_counts and not soft_carousel:
        log_info("Carousel card-count check skipped — no P1 carousel formats in creative-brief.json")
        return

    # Count distinct CARD-K indices per creative_id in image-prompts.md.
    # ID aliasing: prompts often use a stem prefix (e.g. `WLF-AD-01-CARD-1`) where the brief's
    # full creative_id is `WLF-AD-01-FAMILY-FUTURE`. We accept either:
    #   (a) full match: `{full_cid}-CARD-N`
    #   (b) stem match: first 3 dash-segments of `{cid}` followed by `-CARD-N`
    #       (e.g. `WLF-AD-01` from `WLF-AD-01-FAMILY-FUTURE`)
    card_pattern = re.compile(r'\b([A-Z][A-Z0-9-]*?)-CARD-(\d+)\b')
    found_cards_by_id = {}  # exact-id-match → set of K
    for m in card_pattern.finditer(prompts_text):
        prompt_cid, k = m.group(1), int(m.group(2))
        found_cards_by_id.setdefault(prompt_cid, set()).add(k)

    def cards_for_creative(cid):
        """Resolve cards belonging to a creative_id, accepting stem-prefix matches."""
        if cid in found_cards_by_id:
            return found_cards_by_id[cid]
        # Try the 3-segment stem (e.g. WLF-AD-01 from WLF-AD-01-FAMILY-FUTURE)
        parts = cid.split("-")
        if len(parts) >= 3:
            stem = "-".join(parts[:3])
            if stem in found_cards_by_id:
                return found_cards_by_id[stem]
        return set()

    issues_found = False
    for cid, expected_n in expected_counts.items():
        cards = sorted(cards_for_creative(cid))
        if not cards:
            log_critical(
                f"Carousel card count: {cid} requires {expected_n} cards "
                f"(`carousel_{expected_n}_card` in brief) but ZERO `{cid}-CARD-N` prompts "
                f"found in image-prompts.md."
            )
            issues_found = True
            continue
        if len(cards) != expected_n:
            log_critical(
                f"Carousel card count mismatch: {cid} requires {expected_n} cards "
                f"(`carousel_{expected_n}_card` in brief) but only {len(cards)} authored "
                f"({cid}-CARD-{','.join(str(c) for c in cards)}). Author the missing cards "
                f"or correct the brief's format_priority."
            )
            issues_found = True
            continue
        # Count matches but check for gaps in indices: must be contiguous 1..N
        expected_indices = set(range(1, expected_n + 1))
        actual_indices = set(cards)
        if actual_indices != expected_indices:
            missing = sorted(expected_indices - actual_indices)
            extra = sorted(actual_indices - expected_indices)
            msg = f"Carousel card indices not contiguous 1..{expected_n} for {cid}: "
            if missing:
                msg += f"missing CARD-{','.join(str(c) for c in missing)}"
            if extra:
                msg += f" extra CARD-{','.join(str(c) for c in extra)}"
            log_critical(msg)
            issues_found = True

    for cid in soft_carousel:
        if not cards_for_creative(cid):
            log_warning(
                f"Carousel format declared for {cid} but no `{cid}-CARD-N` prompts found "
                f"(format_priority lists bare `carousel` / `lp_redirect_carousel` — "
                f"card count not explicit; verify intent)."
            )

    if not issues_found:
        log_info(
            f"Carousel card-count check passed "
            f"({len(expected_counts)} numbered carousel + {len(soft_carousel)} soft carousel)"
        )


def validate_voice_library_compliance(image_prompts_path, ad_copy_report_path, creative_brief_path, voice_library_path):
    """Cross-check generated copy against client voice-library.json.

    Bedrock added 2026-04-30 after WLF flag: 5 carousel cards / 5 different trust-line strings /
    3× "Reserve a seat" CTA reuse / fresh-invented headlines drifting from proven $0.71 CPL voice.
    Spec: ~/.claude/shared-context/voice-library-spec.md.

    Five sub-checks (see spec §"Validator rules"):
      1. event_facts.canonical_string appears (≥80% similarity) on every variant of an event campaign
      2. heading word-count ≤ voice_rules.max_headline_words
      3. no voice_rules.forbidden_phrases anywhere in generated copy
      4. when creative-brief sets voice_anchor.pattern_id, generated headline broadly matches the pattern's max_words
      5. cta_pill copy matches a verb+noun pair from voice-library; generic "Reserve now" / "Learn More" / "Click here"
         on a designated CTA card = CRITICAL; >40% of carousel cards using the SAME generic CTA = WARNING
    """
    if not os.path.exists(voice_library_path):
        log_warning(
            f"voice-library.json not found at {voice_library_path} — bedrock voice-compliance check "
            f"skipped. business-analysis Step 8 must run first to populate the library."
        )
        return
    try:
        with open(voice_library_path, 'r') as f:
            voice = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        log_warning(f"Could not parse voice-library.json: {e}")
        return

    brief = None
    if os.path.exists(creative_brief_path):
        try:
            with open(creative_brief_path, 'r') as f:
                brief = json.load(f)
        except (json.JSONDecodeError, IOError):
            pass

    voice_rules = voice.get("voice_rules", {})
    forbidden = [p.lower() for p in voice_rules.get("forbidden_phrases", [])]
    max_headline_words = int(voice_rules.get("max_headline_words", 12))
    max_cta_words = int(voice_rules.get("max_cta_words", 5))

    # Combine generated text we want to scan
    text_blobs = []
    for p in (image_prompts_path, ad_copy_report_path):
        if os.path.exists(p):
            with open(p, 'r') as f:
                text_blobs.append(f.read())
    full_text = "\n".join(text_blobs).lower()

    # CHECK 3 — forbidden phrases
    forbidden_hits = [p for p in forbidden if p in full_text]
    if forbidden_hits:
        for p in forbidden_hits:
            log_critical(
                f"Voice-library FORBIDDEN phrase '{p}' appeared in generated copy. "
                f"Source: voice-library.json voice_rules.forbidden_phrases. Rewrite to remove."
            )

    # CHECK 1 — event-fact anchor consistency (only when brief declares event campaign type).
    # Updated 2026-04-30 to accept per_card_variants_allowed for schedule_walk carousels —
    # each card may have its OWN time-specific event component (e.g. 5pm gathering / 5:30 class /
    # 6:30 ārati / 7:15 feast) rather than repeating one canonical line. The check now accepts
    # ANY of the brief's allowed variants, not just the strict canonical_string.
    event_facts = (brief or {}).get("event_facts") if brief else None
    if event_facts and event_facts.get("must_appear_on_every_variant"):
        canonical = (event_facts.get("canonical_string") or "").lower().strip()
        # Build the list of acceptable trust-line strings: canonical + per_card_variants_allowed
        acceptable_variants = [canonical] if canonical else []
        for v in (event_facts.get("per_card_variants_allowed") or []):
            v_low = v.lower().strip()
            if v_low and v_low not in acceptable_variants:
                acceptable_variants.append(v_low)
        if acceptable_variants and image_prompts_path and os.path.exists(image_prompts_path):
            with open(image_prompts_path, 'r') as f:
                prompts_text = f.read()
            blocks = re.split(r'^## Prompt \d+\s+[—-]\s+', prompts_text, flags=re.MULTILINE)[1:]
            misses = []
            for i, block in enumerate(blocks, start=1):
                block_low = block.lower()
                # For each variant, compute token overlap. Pass if ANY variant clears 50% threshold.
                best_ratio = 0.0
                best_variant = ""
                for variant in acceptable_variants:
                    var_tokens = [t for t in re.split(r'\W+', variant) if len(t) >= 3]
                    if not var_tokens:
                        continue
                    hits = sum(1 for t in var_tokens if t in block_low)
                    ratio = hits / len(var_tokens)
                    if ratio > best_ratio:
                        best_ratio = ratio
                        best_variant = variant
                if best_ratio < 0.5:
                    label_m = re.match(r'([A-Z0-9-]+)', block)
                    label = label_m.group(1) if label_m else f"prompt {i}"
                    misses.append((label, round(best_ratio, 2)))
            if misses:
                variants_count = len(acceptable_variants)
                for label, ratio in misses:
                    log_critical(
                        f"Voice-library event_facts: {label} did not match any of the "
                        f"{variants_count} accepted trust-line variants (best overlap {ratio:.0%}, need ≥50%). "
                        f"Either add a per_card_variant to creative-brief.json event_facts.per_card_variants_allowed, "
                        f"or rewrite the prompt's trust line to include day/time/place tokens from one of the variants."
                    )

    # CHECK 2 — headline cadence (max words). Sample exact_copy heading entries from image-prompts.
    if image_prompts_path and os.path.exists(image_prompts_path):
        with open(image_prompts_path, 'r') as f:
            prompts_text = f.read()
        # Match lines like:  "exact_copy": "While they learn, so do you." within a heading block
        for m in re.finditer(r'"id":\s*"heading[^"]*"[^}]*?"exact_copy":\s*"([^"]+)"', prompts_text):
            headline = m.group(1)
            wc = len(headline.split())
            if wc > max_headline_words:
                log_critical(
                    f"Voice-library max_headline_words={max_headline_words} exceeded: "
                    f"'{headline}' is {wc} words. Tighten or split."
                )

    # CHECK 5 — CTA semantic-specificity. Count generic vs specific.
    cta_pairs = voice.get("cta_verb_noun_pairs", [])
    valid_verbs = {p.get("verb", "").lower() for p in cta_pairs}
    valid_pairs_strs = []
    for p in cta_pairs:
        v = p.get("verb", "")
        for n in (p.get("nouns") or []):
            valid_pairs_strs.append(f"{v} {n}".lower())

    if image_prompts_path and os.path.exists(image_prompts_path):
        with open(image_prompts_path, 'r') as f:
            prompts_text = f.read()
        cta_copies = re.findall(r'"id":\s*"cta_pill"[^}]*?"exact_copy":\s*"([^"]+)"', prompts_text)
        if cta_copies:
            generic_re = re.compile(r'^\s*(reserve now|learn more|click here|book now|sign up|shop now)\s*[→\->\s]*$', re.IGNORECASE)
            generic_hits = [c for c in cta_copies if generic_re.search(c)]
            if generic_hits:
                # Count by exact value to detect repetition
                from collections import Counter
                counts = Counter(c.strip() for c in cta_copies)
                most_common, n = counts.most_common(1)[0]
                if n / len(cta_copies) > 0.4 and len(cta_copies) >= 3:
                    log_warning(
                        f"CTA reuse: '{most_common}' appears on {n}/{len(cta_copies)} prompts "
                        f"(>40% of carousel set). Voice-library cta_verb_noun_pairs.object_specificity_rule "
                        f"requires noun to match each card's visual subject."
                    )
            # Strict pair check (advisory)
            unmatched = [c for c in cta_copies if c.strip().lower() not in valid_pairs_strs and not generic_re.search(c)]
            if unmatched:
                log_warning(
                    f"CTA pills not in voice-library cta_verb_noun_pairs: {unmatched[:3]}{'...' if len(unmatched) > 3 else ''}. "
                    f"Verify these are intentional voice extensions; if so, add to voice-library."
                )

    if not forbidden_hits:
        log_info(
            f"Voice-library compliance: {len(voice.get('headline_patterns', []))} patterns, "
            f"{len(cta_pairs)} CTA pairs, {len(forbidden)} forbidden-phrase rules "
            f"(bootstrapping={voice.get('bootstrapping')})"
        )


def validate_dashboard(path):
    """Validate the ad-copy HTML dashboard."""
    if not os.path.exists(path):
        log_critical(f"Dashboard file not found: {path}")
        return
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    issues = []
    if 'copyText(' not in content:
        issues.append("missing copyText() helper for clipboard buttons")
    if 'class="copy-btn"' not in content and 'copy-btn' not in content:
        issues.append("no .copy-btn elements found")
    required_sections = ['ads', 'prompts', 'storyboards', 'gate']
    missing_anchors = [s for s in required_sections if f'id="{s}"' not in content]
    if missing_anchors:
        issues.append(f"missing section anchors: {missing_anchors}")
    # Template-placeholder check — looks for genuine `{{IDENTIFIER}}` pattern
    # (uppercase-letter + uppercase/underscore body + close braces). Bare `}}` from
    # nested CSS @media / @keyframes blocks should NOT trigger this.
    if re.search(r"\{\{\s*[A-Z][A-Z0-9_]*\s*\}\}", content):
        issues.append("unrendered template placeholders {{IDENTIFIER}} present")
    if len(content) < 5000:
        issues.append(f"dashboard suspiciously small ({len(content)} chars) — likely missing data")
    if issues:
        for issue in issues:
            log_warning(f"Dashboard: {issue}")
    log_info(f"Dashboard stats: {len(content)} chars, {content.count('copy-btn')} copy buttons")


def check_dashboard_presence(files):
    """Check that the dashboard exists at the program folder root."""
    # Probe: any input file in _engine/working/ implies the program folder is two levels up.
    program_dir = None
    for fpath in files.values():
        p = os.path.abspath(fpath)
        # Walk up to find _engine/working/
        if os.sep + '_engine' + os.sep + 'working' + os.sep in p:
            program_dir = p.split(os.sep + '_engine' + os.sep + 'working' + os.sep)[0]
            break
    if not program_dir:
        return  # Can't determine — skip silently
    candidates = [
        os.path.join(program_dir, 'ad-copy-dashboard.html'),
        os.path.join(program_dir, 'prompt-library.html'),
    ]
    for c in candidates:
        if os.path.exists(c):
            log_info(f"Dashboard present at: {c}")
            return
    log_critical(
        f"Dashboard MISSING at folder root ({program_dir}). "
        "Run scripts/render_ad_copy_dashboard.py to generate. See SKILL.md Step 7.5."
    )


def validate_cross_file(files):
    """Check consistency between report and CSVs."""
    report_content = ''
    google_campaigns = set()
    meta_campaigns = set()

    if 'report' in files:
        with open(files['report'], 'r') as f:
            report_content = f.read()

    if 'google_csv' in files:
        with open(files['google_csv'], 'r') as f:
            reader = csv.reader(f)
            rows = list(reader)
            if len(rows) > 1:
                header = [h.strip().lower() for h in rows[0]]
                camp_idx = next((i for i, h in enumerate(header) if 'campaign' in h), None)
                if camp_idx is not None:
                    google_campaigns = set(row[camp_idx].strip() for row in rows[1:] if len(row) > camp_idx and row[camp_idx].strip())

    if 'meta_csv' in files:
        with open(files['meta_csv'], 'r') as f:
            reader = csv.reader(f)
            rows = list(reader)
            if len(rows) > 1:
                header = [h.strip().lower() for h in rows[0]]
                camp_idx = next((i for i, h in enumerate(header) if 'campaign' in h), None)
                if camp_idx is not None:
                    meta_campaigns = set(row[camp_idx].strip() for row in rows[1:] if len(row) > camp_idx and row[camp_idx].strip())

    all_csv_campaigns = google_campaigns | meta_campaigns
    if report_content and all_csv_campaigns:
        missing_in_report = [c for c in all_csv_campaigns if c not in report_content]
        if missing_in_report:
            log_warning(f"Campaign names in CSV but not found in report: {missing_in_report}")

    if all_csv_campaigns:
        log_info(f"Cross-file: {len(google_campaigns)} Google campaigns, {len(meta_campaigns)} Meta campaigns in CSVs")

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    global CREATIVE_BRIEF, OFFERINGS_TEXT, OFFERINGS_PATH
    files = {}
    for path in sys.argv[1:]:
        if not os.path.exists(path):
            print(f"  ⚠️  File not found: {path}")
            continue
        file_type = classify_file(path)
        if file_type:
            files[file_type] = path
        else:
            print(f"  ⚠️  Could not classify: {os.path.basename(path)}")

    # Pre-load creative brief (if supplied) so per-file validators can cross-reference.
    if 'creative_brief' in files:
        try:
            with open(files['creative_brief'], 'r', encoding='utf-8') as f:
                CREATIVE_BRIEF = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"  ⚠️  Creative brief load failed ({e}) — cross-validation disabled")
            CREATIVE_BRIEF = None

    # Pre-load offerings.md for Gate B service-offering cross-check.
    # Walks up from any input file to locate {client}/_engine/wiki/offerings.md
    # (single-program) or {client-root}/_engine/wiki/offerings.md (multi-program).
    OFFERINGS_TEXT, OFFERINGS_PATH = _find_offerings_md(list(files.values()))

    print("🔍 Ad Copywriter — Output Validation")
    for ftype, fpath in files.items():
        print(f"   {ftype:20s}: {fpath}")
    if OFFERINGS_PATH:
        print(f"   {'offerings_source':20s}: {OFFERINGS_PATH}")

    validators = [
        ('report', 'Ad Copy Report', validate_report),
        ('report_best_case', 'Ad Copy — Best Case (forward planning)', validate_report),
        ('report_current_state', 'Ad Copy — Current State (production)', validate_report),
        ('google_csv', 'Google Ads CSV', validate_google_csv),
        ('meta_csv', 'Meta Ads CSV', validate_meta_csv),
        ('image_prompts', 'Image Prompts', validate_image_prompts),
        ('video_storyboards', 'Video Storyboards', validate_video_storyboards),
        ('dashboard', 'Ad Copy Dashboard (HTML)', validate_dashboard),
    ]

    for file_key, label, validator_fn in validators:
        if file_key in files:
            print(f"\n{'='*60}")
            print(f"  {label}")
            print(f"{'='*60}")
            validator_fn(files[file_key])
            flush_logs()

    if len(files) > 1:
        print(f"\n{'='*60}")
        print("  Cross-File Consistency")
        print(f"{'='*60}")
        validate_cross_file(files)
        flush_logs()

    # Format/aspect-ratio cross-check (patched 2026-04-30 — catches carousel-must-be-1:1 violations)
    if 'image_prompts' in files:
        # Try to find creative-brief.json next to image-prompts.md
        ip_dir = os.path.dirname(os.path.abspath(files['image_prompts']))
        cb_path = os.path.join(ip_dir, 'creative-brief.json')
        if os.path.exists(cb_path):
            print(f"\n{'='*60}")
            print("  Format / Aspect-Ratio Cross-Check")
            print(f"{'='*60}")
            validate_format_aspect_consistency(files['image_prompts'], cb_path)
            flush_logs()

            # Carousel card-count cross-check (patched 2026-04-30 — catches carousel_5_card spec'd
            # but only 4 cards authored, or non-contiguous CARD-1,2,4,5 indices missing CARD-3)
            print(f"\n{'='*60}")
            print("  Carousel Card-Count Cross-Check")
            print(f"{'='*60}")
            validate_carousel_card_count(files['image_prompts'], cb_path)
            flush_logs()

            # Voice-library compliance (bedrock 2026-04-30 — cross-skill voice anchoring)
            # Resolve voice-library.json: try program-folder wiki first, then client-root wiki (multi-program)
            print(f"\n{'='*60}")
            print("  Voice-Library Compliance (bedrock)")
            print(f"{'='*60}")
            # image_prompts path: <client>/<program>/_engine/working/image-prompts.md
            engine_dir = os.path.dirname(os.path.dirname(os.path.abspath(files['image_prompts'])))   # <program>/_engine
            program_folder = os.path.dirname(engine_dir)                                              # <program>
            client_root = os.path.dirname(program_folder)                                             # <client>
            vl_program = os.path.join(engine_dir, 'wiki', 'voice-library.json')                      # single-program
            vl_client_root = os.path.join(client_root, '_engine', 'wiki', 'voice-library.json')      # multi-program
            voice_library_path = vl_program if os.path.exists(vl_program) else vl_client_root
            ad_copy_md = files.get('ad_copy_report') or files.get('ad_copy') or ''
            validate_voice_library_compliance(
                files['image_prompts'], ad_copy_md, cb_path, voice_library_path
            )
            flush_logs()

    # Gate A — Phase-0 leakage prevention
    print(f"\n{'='*60}")
    print("  Gate A — Phase-0 Leakage Prevention")
    print(f"{'='*60}")
    validate_gate_a(files, CREATIVE_BRIEF)
    flush_logs()

    # Gate B — Service-offering cross-check (always-on)
    print(f"\n{'='*60}")
    print("  Gate B — Service-Offering Cross-Check")
    print(f"{'='*60}")
    validate_gate_b(files)
    flush_logs()

    # Dashboard presence check (Step 7.5)
    print(f"\n{'='*60}")
    print("  Dashboard Presence (Step 7.5)")
    print(f"{'='*60}")
    check_dashboard_presence(files)
    flush_logs()

    # Final summary
    print(f"\n{'='*60}")
    if total_criticals > 0:
        print(f"  ❌ Validation FAILED — {total_criticals} critical issue(s), {total_warnings} warning(s)")
        sys.exit(1)
    else:
        print(f"  ✅ Validation passed — no critical issues ({total_warnings} warning(s))")

if __name__ == '__main__':
    main()
