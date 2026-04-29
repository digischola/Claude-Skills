#!/usr/bin/env python3
"""Ad Copywriter — Output Validation Script

Usage: python3 validate_output.py <file1> [file2] [file3] ...
Files are detected by name pattern:
  *-ad-copy-report.md    → Ad copy report
  *-google-ads.csv       → Google Ads CSV
  *-meta-ads.csv         → Meta Ads CSV
  *-image-prompts.md     → Image generation prompts
  *-video-storyboards.md → Video storyboards
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

    # Final summary
    print(f"\n{'='*60}")
    if total_criticals > 0:
        print(f"  ❌ Validation FAILED — {total_criticals} critical issue(s), {total_warnings} warning(s)")
        sys.exit(1)
    else:
        print(f"  ✅ Validation passed — no critical issues ({total_warnings} warning(s))")

if __name__ == '__main__':
    main()
