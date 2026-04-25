#!/usr/bin/env python3
"""
validate_transcript.py — flag metric-like words in a word-level transcript
so the operator can confirm Whisper heard them correctly BEFORE render.

Whisper occasionally mishears numbers (e.g. "120%" heard as "130%"). A wrong
metric in a published Reel is unfixable. This gate catches them upfront.

Usage:
  python3 validate_transcript.py <transcript.json> [--auto-fix <corrections.json>]

Behaviour:
  - Scans every word token for metric-like patterns
  - Prints a human-readable warning block listing each flagged word + timestamp
  - Exits 0 always (advisory, not blocking) so the chain continues

A flag is any token matching:
  - Percentages:    "120%", "+130%", "-5%"
  - Dollar amounts: "$40", "$1k", "$2.5M"
  - Multipliers:    "3x", "10X"
  - Big numbers:    standalone integers >= 10 ("40", "100", "1200")
"""

import json
import re
import sys
from pathlib import Path

PCT_RE        = re.compile(r"^[+\-]?\d+(\.\d+)?%$")
DOLLAR_RE     = re.compile(r"^\$\d+(\.\d+)?[kKmMbB]?$")
MULTIPLIER_RE = re.compile(r"^\d+(\.\d+)?[xX]$")
BIG_INT_RE    = re.compile(r"^\d{2,}$")  # 10+


def flag_word(text: str) -> str:
    """Return a reason string if this token is metric-like, else empty."""
    t = text.strip(",.!?;:()[]\"'")
    if PCT_RE.match(t):
        return "percentage"
    if DOLLAR_RE.match(t):
        return "dollar amount"
    if MULTIPLIER_RE.match(t):
        return "multiplier"
    if BIG_INT_RE.match(t):
        return "large integer"
    return ""


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: validate_transcript.py <transcript.json>")
        return 1

    path = Path(sys.argv[1])
    if not path.is_file():
        print(f"ERROR: transcript not found: {path}", file=sys.stderr)
        return 1

    words = json.loads(path.read_text())
    flagged = []
    for w in words:
        text = w.get("text", "") or w.get("word", "")
        reason = flag_word(text)
        if reason:
            flagged.append({
                "text": text,
                "start": w.get("start", 0.0),
                "reason": reason,
            })

    if not flagged:
        print(f"[transcript-validate] {path.name}: no metric words detected")
        return 0

    print(f"\n[transcript-validate] {path.name}: {len(flagged)} metric-like word(s) flagged.")
    print("Confirm Whisper heard these correctly before rendering — a wrong number in a published Reel is unfixable.\n")
    for f in flagged:
        print(f"  ⚠  @ {f['start']:>6.2f}s   [{f['reason']:>14}]   {f['text']!r}")
    print()
    print("If any are wrong: edit the 'text' field in transcript.json and re-run.")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
