#!/usr/bin/env python3
"""
Validate a drafted post against Digischola brand rules + platform constraints.

Usage:
  python3 validate_post.py <post_file_path>
  python3 validate_post.py <post_file_path> --channel linkedin-text
  python3 validate_post.py <post_file_path> --verbose

Exit codes:
  0 = clean (all hard rules pass, no warnings)
  1 = warnings (soft rules flagged, review recommended but not blocking)
  2 = CRITICAL (hard rules violated, post cannot ship)

Post file format:
  Markdown file with YAML frontmatter specifying channel + format.
  Frontmatter example:
  ---
  channel: linkedin
  format: text-post
  entry_id: abc-123
  ---
  [post body]
"""

import argparse
import re
import sys
from pathlib import Path


CHANNEL_LIMITS = {
    "linkedin-text": {"max_chars": 3000, "sweet_spot": (1200, 1800), "hook_fold": 210},
    "linkedin-carousel-slide": {"max_chars": 250, "sweet_spot": (100, 200)},
    "linkedin-carousel-caption": {"max_chars": 1500, "sweet_spot": (300, 800)},
    "x-tweet": {"max_chars": 280, "sweet_spot": (240, 280)},
    "x-thread-tweet": {"max_chars": 280, "sweet_spot": (200, 270)},
    "instagram-caption": {"max_chars": 2200, "sweet_spot": (150, 400), "hook_fold": 125},
    "instagram-reel-caption": {"max_chars": 2200, "sweet_spot": (60, 150)},
    "facebook-post": {"max_chars": 5000, "sweet_spot": (400, 1000)},
    "whatsapp-status": {"max_chars": 700, "sweet_spot": (50, 300)},
    "whatsapp-channel": {"max_chars": 4096, "sweet_spot": (100, 600)},
}

# Universal bans (from voice-guide.md)
EM_DASH_CHARS = ["\u2014", "\u2013"]  # em dash + en dash

HYPE_WORDS = [
    "unlock", "revolutionize", "revolutionary", "game-changer", "game changer",
    "in today's fast-paced world", "in today's digital landscape",
    "ever wondered", "let me tell you", "here's the truth",
    "one weird trick", "ultimate guide", "mind-blowing", "mind blowing",
    "cutting-edge", "cutting edge",
]

# AI-tell transitions (voice-frameworks.md)
AI_TELL_PHRASES = [
    "furthermore", "moreover", "in conclusion", "additionally",
    "on the other hand", "that being said", "it's important to note",
    "it is worth noting", "in summary",
]

# Engagement-bait patterns (platform-specs.md)
ENGAGEMENT_BAIT = [
    r"\bcomment\s+yes\b",
    r"\bcomment\s+below\b",
    r"\bfollow\s+for\s+more\b",
    r"\btag\s+a\s+friend\b",
    r"\bshare\s+if\s+you\s+agree\b",
]


def parse_post(path: Path):
    """Extract frontmatter metadata + body from the post file."""
    text = path.read_text(errors="replace")
    meta = {}
    body = text

    if text.startswith("---\n"):
        parts = text.split("---\n", 2)
        if len(parts) >= 3:
            for line in parts[1].splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    meta[k.strip()] = v.strip()
            body = parts[2]

    return meta, body.strip()


def count_chars(body: str) -> int:
    """Char count excluding trailing whitespace, matching platform counters."""
    return len(body.rstrip())


def check_em_dashes(body: str):
    """HARD RULE: em dashes forbidden universally."""
    hits = []
    for ch in EM_DASH_CHARS:
        for i, line in enumerate(body.splitlines(), 1):
            if ch in line:
                hits.append((i, ch, line.strip()[:80]))
    return hits


def check_hype_words(body: str):
    """HARD RULE: hype words banned."""
    low = body.lower()
    hits = []
    for word in HYPE_WORDS:
        if word in low:
            hits.append(word)
    return hits


def check_ai_tells(body: str):
    """SOFT WARNING: AI-tell transitions."""
    low = body.lower()
    hits = []
    for phrase in AI_TELL_PHRASES:
        # boundary match
        if re.search(r"\b" + re.escape(phrase) + r"\b", low):
            hits.append(phrase)
    return hits


def check_engagement_bait(body: str):
    """SOFT WARNING: engagement bait patterns (LinkedIn shadowban risk)."""
    low = body.lower()
    hits = []
    for pattern in ENGAGEMENT_BAIT:
        if re.search(pattern, low):
            hits.append(pattern)
    return hits


def check_char_limits(body: str, channel: str):
    """HARD RULE (hard cap) + SOFT WARNING (sweet spot)."""
    if channel not in CHANNEL_LIMITS:
        return None, None, None
    limits = CHANNEL_LIMITS[channel]
    n = count_chars(body)
    over = n > limits["max_chars"]
    lo, hi = limits["sweet_spot"]
    off_sweet = n < lo or n > hi
    return n, over, off_sweet


def split_thread_tweets(body: str):
    """Split a thread draft into individual tweet bodies.
    Recognizes '## Tweet N' section headers. Returns list of tweet bodies (stripped)."""
    parts = re.split(r"^##\s+Tweet\s+\d+[^\n]*\n", body, flags=re.MULTILINE)
    # parts[0] is pre-first-tweet (usually blank or intro). parts[1:] are tweets.
    return [p.strip() for p in parts[1:] if p.strip()]


def check_thread_char_limits(body: str):
    """For x-thread channel: validate each tweet body against 280-char cap + sweet spot."""
    tweets = split_thread_tweets(body)
    if not tweets:
        return None
    results = []
    for i, t in enumerate(tweets, 1):
        n = len(t.rstrip())
        over = n > 280
        off_sweet = n < 100 or n > 270
        results.append({"tweet": i, "chars": n, "over": over, "off_sweet": off_sweet})
    return results


def check_sentence_variance(body: str):
    """SOFT WARNING: 5+ consecutive sentences of uniform length = AI cadence."""
    # split by sentence-ish boundaries
    sentences = re.split(r"(?<=[.!?])\s+", body.strip())
    sentences = [s for s in sentences if s.strip()]
    if len(sentences) < 5:
        return None

    # count words per sentence
    lengths = [len(s.split()) for s in sentences]

    # sliding window of 5 — flag if variance < 3 words
    flagged_windows = []
    for i in range(len(lengths) - 4):
        window = lengths[i : i + 5]
        if max(window) - min(window) < 3:
            flagged_windows.append((i + 1, i + 5, window))

    return flagged_windows


def check_specific_numbers(body: str):
    """SOFT WARNING: post has zero specific numbers (likely too generic)."""
    # look for digit sequences, percentages, currency
    has_digits = bool(re.search(r"\d+", body))
    return not has_digits


def check_linkedin_hook(body: str, channel: str):
    """SOFT WARNING: LinkedIn hook should be under 210 chars (truncation fold)."""
    if channel != "linkedin-text":
        return None
    lines = [l for l in body.splitlines() if l.strip()]
    if not lines:
        return None
    # first 2 non-empty lines
    first_block = "\n".join(lines[:2])
    if len(first_block) > 210:
        return len(first_block)
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("post_file", type=Path)
    ap.add_argument("--channel", type=str, default=None,
                    help="Override channel if not in frontmatter")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    if not args.post_file.exists():
        sys.exit(f"Post file not found: {args.post_file}")

    meta, body = parse_post(args.post_file)

    # Channel key resolution:
    # - If --channel is passed, it is the definitive key (user override).
    # - Otherwise, combine frontmatter channel + format (e.g., linkedin + text-post).
    if args.channel:
        channel_key = args.channel.lower()
    else:
        channel = meta.get("channel", "").lower()
        fmt = meta.get("format", "").lower()
        if channel and fmt:
            channel_key = f"{channel}-{fmt}".replace("--", "-")
        else:
            channel_key = channel

    critical = []
    warnings = []

    # HARD RULES (exit 2 if violated)
    em = check_em_dashes(body)
    if em:
        critical.append(f"Em dashes found on {len(em)} line(s). FIRST HIT: line {em[0][0]} contains '{em[0][1]}': {em[0][2]}")

    hype = check_hype_words(body)
    if hype:
        critical.append(f"Hype words detected (banned per voice-guide.md): {hype}")

    bait = check_engagement_bait(body)
    if bait:
        critical.append(f"Engagement bait patterns detected (LinkedIn shadowban risk): {bait}")

    # Thread mode: validate each tweet separately, NOT the whole file against single-tweet cap.
    if channel_key == "x-thread":
        thread_results = check_thread_char_limits(body)
        if thread_results is None:
            critical.append("Channel is x-thread but no '## Tweet N' section headers found. Cannot split tweets.")
        else:
            char_count = sum(r["chars"] for r in thread_results)
            over_tweets = [r for r in thread_results if r["over"]]
            off_sweet_tweets = [r for r in thread_results if r["off_sweet"] and not r["over"]]
            if over_tweets:
                for r in over_tweets:
                    critical.append(f"Tweet {r['tweet']} is {r['chars']} chars, exceeds 280 hard cap.")
            if off_sweet_tweets:
                for r in off_sweet_tweets:
                    warnings.append(f"Tweet {r['tweet']} is {r['chars']} chars, outside sweet spot (100-270).")
            if args.verbose:
                for r in thread_results:
                    print(f"  Tweet {r['tweet']}: {r['chars']} chars")
    else:
        char_count, over_limit, off_sweet = check_char_limits(body, channel_key)
        if over_limit:
            critical.append(f"Char count {char_count} exceeds hard cap for {channel_key}.")

        # SOFT WARNINGS (exit 1 if present)
        if off_sweet and char_count is not None:
            lo, hi = CHANNEL_LIMITS[channel_key]["sweet_spot"]
            warnings.append(f"Char count {char_count} outside sweet spot ({lo}-{hi}) for {channel_key}.")

    ai_tells = check_ai_tells(body)
    if ai_tells:
        warnings.append(f"AI-tell transitions detected: {ai_tells}")

    variance = check_sentence_variance(body)
    if variance:
        warnings.append(f"Uniform sentence length in {len(variance)} window(s) — human voice needs more variance.")

    if check_specific_numbers(body):
        warnings.append("No specific numbers in post. Voice-guide prefers concrete over generic.")

    hook_len = check_linkedin_hook(body, channel_key)
    if hook_len:
        warnings.append(f"LinkedIn hook ({hook_len} chars) exceeds truncation fold (210). First line(s) will be cut off.")

    # Output
    print(f"\n=== validate_post.py :: {args.post_file.name} ===")
    print(f"Channel: {channel_key or '(unspecified)'}")
    if char_count is not None:
        print(f"Char count: {char_count}")

    if critical:
        print(f"\n  CRITICAL ({len(critical)}):")
        for c in critical:
            print(f"    - {c}")
    if warnings:
        print(f"\n  WARNING ({len(warnings)}):")
        for w in warnings:
            print(f"    - {w}")

    if not critical and not warnings:
        print("\n  All checks passed. Post is clean.")
        sys.exit(0)
    if critical:
        print("\nPost BLOCKED. Fix critical issues before shipping.")
        sys.exit(2)
    print("\nPost has soft warnings. Review recommended but not blocking.")
    sys.exit(1)


if __name__ == "__main__":
    main()
