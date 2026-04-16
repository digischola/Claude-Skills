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
from io import StringIO

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
    return None

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
