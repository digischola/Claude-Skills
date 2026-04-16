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
    name = os.path.basename(path).lower()
    if 'ad-copy-report' in name: return 'report'
    if 'google-ads' in name and name.endswith('.csv'): return 'google_csv'
    if 'meta-ads' in name and name.endswith('.csv'): return 'meta_csv'
    if 'image-prompts' in name: return 'image_prompts'
    if 'video-storyboard' in name: return 'video_storyboards'
    if 'creative-brief' in name and name.endswith('.json'): return 'creative_brief'
    return None

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

    global CREATIVE_BRIEF
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

    print("🔍 Ad Copywriter — Output Validation")
    for ftype, fpath in files.items():
        print(f"   {ftype:20s}: {fpath}")

    validators = [
        ('report', 'Ad Copy Report', validate_report),
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

    # Final summary
    print(f"\n{'='*60}")
    if total_criticals > 0:
        print(f"  ❌ Validation FAILED — {total_criticals} critical issue(s), {total_warnings} warning(s)")
    else:
        print(f"  ✅ Validation passed — no critical issues ({total_warnings} warning(s))")

if __name__ == '__main__':
    main()
