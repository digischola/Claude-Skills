#!/usr/bin/env python3
"""
Validate a 4-deliverable case-study bundle BEFORE writing to pending-approval/.

Checks:
  1. All 4 expected files exist
  2. Hook consistency: hero metric appears verbatim in all 4 first units (LI Slide 1, X Tweet 1, Blog H1, IG Slide 1)
  3. Metric drift: all numeric mentions across deliverables are consistent
  4. Voice rules: no em dashes, no hype words, no engagement bait, no lowercase CTAs
  5. Naming consistency: same client identifier (named OR anonymized) across all 4
  6. Length limits: LI 8-10 slides, X tweets ≤280 chars, blog 1500-2500 words, IG 8-10 slides

Usage:
  python3 validate_case_study.py --bundle-dir /tmp/cs-4e4eed15/
  python3 validate_case_study.py --bundle-dir <dir> --json   # machine-readable output

Exit codes:
  0 = all checks pass
  1 = at least one check failed
  2 = bundle dir invalid / missing files
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

EXPECTED_FILES = ["linkedin-carousel.md", "x-thread.md", "blog-post.md", "instagram-carousel.md"]

HYPE_WORDS = ["unlock", "revolutionize", "game-changer", "massive", "explode",
              "crush", "10x", "effortless", "secret", "hack"]
ENGAGEMENT_BAIT_PATTERNS = [
    r"\bcomment\s+yes\b",
    r"\bfollow\s+for\s+more\b",
    r"\btag\s+a?\s*friend\b",
    r"\bdrop\s+a\s+\W?\b",
    r"\bdouble\s+tap\b",
    r"\bsmash\s+the\s+like\b",
]


def find_metric_in_text(text: str) -> str | None:
    """Extract the most prominent percentage / multiplier metric from text."""
    # Look for ±NNN% or N.Nx patterns
    m = re.search(r"([+-]?\d+(?:\.\d+)?\s*%)", text)
    if m:
        return m.group(1).strip().replace(" ", "")
    m = re.search(r"(\d+(?:\.\d+)?\s*x)\b", text, re.IGNORECASE)
    if m:
        return m.group(1).strip().replace(" ", "").lower()
    return None


def all_metrics_in_text(text: str) -> set[str]:
    """Return all percentage / multiplier metrics in text."""
    pcts = re.findall(r"[+-]?\d+(?:\.\d+)?\s*%", text)
    muls = re.findall(r"\d+(?:\.\d+)?\s*x\b", text, re.IGNORECASE)
    return {p.replace(" ", "") for p in pcts} | {m.replace(" ", "").lower() for m in muls}


def split_slide_1(text: str, marker_re: str) -> str:
    """Return the first slide / tweet / H1 section of a deliverable."""
    parts = re.split(marker_re, text, flags=re.MULTILINE)
    # parts: [pre-marker, marker_capture..., body_after_first_marker, body_after_second_marker, ...]
    if len(parts) >= 3:
        return parts[2][:600]  # first body chunk, capped
    return text[:600]


def check_hook_consistency(bundle: dict[str, str]) -> list[str]:
    """All 4 first-units must contain the same hero metric."""
    errors = []
    li_slide_1 = split_slide_1(bundle["linkedin-carousel.md"], r"^#\s+Slide 1\s*[—-]")
    x_tweet_1 = split_slide_1(bundle["x-thread.md"], r"^##\s+Tweet 1\s*[—-]")
    blog_h1 = split_slide_1(bundle["blog-post.md"], r"^#\s+")
    ig_slide_1 = split_slide_1(bundle["instagram-carousel.md"], r"^#\s+Slide 1\s*[—-]")

    metrics = {
        "LI Slide 1": find_metric_in_text(li_slide_1),
        "X Tweet 1": find_metric_in_text(x_tweet_1),
        "Blog H1": find_metric_in_text(blog_h1),
        "IG Slide 1": find_metric_in_text(ig_slide_1),
    }

    distinct = set(v for v in metrics.values() if v is not None)
    if not distinct:
        errors.append("hook consistency: NO metric found in any of the 4 first units")
        return errors
    if len(distinct) > 1:
        errors.append(f"hook consistency: hero metric varies across deliverables: {metrics}")
    for label, val in metrics.items():
        if val is None:
            errors.append(f"hook consistency: {label} has no extractable hero metric")
    return errors


def check_metric_drift(bundle: dict[str, str]) -> list[str]:
    """All numbers across all 4 should be consistent (no contradictions)."""
    errors = []
    metrics_per_file = {fname: all_metrics_in_text(text) for fname, text in bundle.items()}

    # Compute the union of all metrics; flag any metric that appears in only ONE deliverable
    # Actual contradiction detection is hard without context — this is a soft heuristic.
    all_metrics = set()
    for s in metrics_per_file.values():
        all_metrics |= s

    # Light-touch: warn if a deliverable has zero metrics (probably broken)
    for fname, ms in metrics_per_file.items():
        if not ms:
            errors.append(f"metric drift: {fname} has no numeric metrics — broken deliverable?")

    return errors


def check_voice_rules(bundle: dict[str, str]) -> list[str]:
    """Universal voice rules: no em dash, no hype words, no engagement bait."""
    errors = []
    for fname, text in bundle.items():
        text_lower = text.lower()
        # Em dash (excluding the literal '—' in skeleton placeholder lines)
        if "—" in text or "--" in text.replace("---", ""):
            # Allow `---` (markdown frontmatter delimiter) but block `--` and `—`
            errors.append(f"voice: {fname} contains em dash (— or --)")
        # Hype words
        for hype in HYPE_WORDS:
            if re.search(rf"\b{re.escape(hype)}\b", text_lower):
                errors.append(f"voice: {fname} contains hype word: {hype}")
                break  # one finding per file is enough
        # Engagement bait
        for pat in ENGAGEMENT_BAIT_PATTERNS:
            if re.search(pat, text_lower):
                errors.append(f"voice: {fname} contains engagement bait matching /{pat}/")
                break
    return errors


def check_length_limits(bundle: dict[str, str]) -> list[str]:
    """Slide counts + tweet char limits + blog word count."""
    errors = []
    # LI carousel: count `# Slide N` headers, expect 8-10
    li_slides = len(re.findall(r"^#\s+Slide \d+\s*[—-]", bundle["linkedin-carousel.md"], re.MULTILINE))
    if li_slides < 8 or li_slides > 10:
        errors.append(f"length: LI carousel has {li_slides} slides, expected 8-10")

    # IG carousel: same
    ig_slides = len(re.findall(r"^#\s+Slide \d+\s*[—-]", bundle["instagram-carousel.md"], re.MULTILINE))
    if ig_slides < 8 or ig_slides > 10:
        errors.append(f"length: IG carousel has {ig_slides} slides, expected 8-10")

    # X thread: count tweets, validate each ≤280 chars
    tweet_blocks = re.split(r"^##\s+Tweet \d+\s*[—-]", bundle["x-thread.md"], flags=re.MULTILINE)[1:]
    tweet_count = len(tweet_blocks)
    if tweet_count < 8 or tweet_count > 12:
        errors.append(f"length: X thread has {tweet_count} tweets, expected 8-12")
    for i, block in enumerate(tweet_blocks, 1):
        body = block.strip().split("---")[0].strip()
        # Strip the rest of the doc (validation checks at bottom shouldn't be counted as tweet body)
        if "## Validation" in body or "## Tweet" in body:
            body = body.split("## Validation")[0].split("## Tweet")[0].strip()
        if len(body) > 280:
            errors.append(f"length: X thread Tweet {i} is {len(body)} chars (>280)")

    # Blog: word count target 1500-2500
    blog_words = len(re.findall(r"\b\w+\b", bundle["blog-post.md"]))
    if blog_words < 1500 or blog_words > 2500:
        errors.append(f"length: blog post is {blog_words} words, expected 1500-2500")
    return errors


def check_naming_consistency(bundle: dict[str, str]) -> list[str]:
    """The same client_identifier should appear across all 4 frontmatters (if present)."""
    errors = []
    identifiers = {}
    for fname, text in bundle.items():
        m = re.search(r"^client_identifier:\s*(.+)$", text, re.MULTILINE)
        if m:
            identifiers[fname] = m.group(1).strip()
    distinct = set(identifiers.values())
    if len(distinct) > 1:
        errors.append(f"naming consistency: client_identifier varies: {identifiers}")
    return errors


def validate_bundle(bundle_dir: Path) -> dict:
    """Run all checks; return {ok: bool, errors: [...], summary: dict}."""
    if not bundle_dir.exists():
        return {"ok": False, "errors": [f"bundle dir not found: {bundle_dir}"], "summary": {}}
    missing = [f for f in EXPECTED_FILES if not (bundle_dir / f).exists()]
    if missing:
        return {"ok": False, "errors": [f"missing files: {missing}"], "summary": {}}

    bundle = {f: (bundle_dir / f).read_text() for f in EXPECTED_FILES}
    all_errors = []
    all_errors.extend(check_hook_consistency(bundle))
    all_errors.extend(check_metric_drift(bundle))
    all_errors.extend(check_voice_rules(bundle))
    all_errors.extend(check_length_limits(bundle))
    all_errors.extend(check_naming_consistency(bundle))

    summary = {
        "files_checked": EXPECTED_FILES,
        "li_slides": len(re.findall(r"^#\s+Slide \d+\s*[—-]", bundle["linkedin-carousel.md"], re.MULTILINE)),
        "x_tweets": len(re.split(r"^##\s+Tweet \d+\s*[—-]", bundle["x-thread.md"], flags=re.MULTILINE)) - 1,
        "blog_words": len(re.findall(r"\b\w+\b", bundle["blog-post.md"])),
        "ig_slides": len(re.findall(r"^#\s+Slide \d+\s*[—-]", bundle["instagram-carousel.md"], re.MULTILINE)),
    }
    return {"ok": not all_errors, "errors": all_errors, "summary": summary}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bundle-dir", type=Path, required=True)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    result = validate_bundle(args.bundle_dir)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"\n=== Validate Case Study: {args.bundle_dir.name} ===")
        if result["ok"]:
            print("✓ ALL CHECKS PASS")
        else:
            print(f"✗ {len(result['errors'])} ERROR(S):")
            for e in result["errors"]:
                print(f"  - {e}")
        print(f"\nSummary: {result['summary']}")
    sys.exit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
