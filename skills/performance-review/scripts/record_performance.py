#!/usr/bin/env python3
"""
Record performance metrics for a single posted draft.

Reads the post file's frontmatter for context (entry_id, channel, hook_category,
voice_framework, repurpose_source, pillar). Accepts metrics as JSON. Validates
against the channel's schema. Computes weighted_score. Appends to
brand/performance/log.json and stamps the post file frontmatter with a
`performance: {...}` field.

Usage:
  python3 record_performance.py <post_file> --metrics '{"impressions": 1200, "comments": 5, ...}'
  python3 record_performance.py <post_file> --metrics-file metrics.json
  python3 record_performance.py <post_file> --published-at 2026-04-20T09:30:00Z --metrics '{...}'

Exit codes:
  0 = recorded cleanly
  1 = validation error (metrics schema mismatch, missing frontmatter fields)
  2 = post file or log file issue
"""

import argparse
import json
import re
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path


# Channel weighted-score formulas. Match metrics-schema.md.
SCORERS = {
    "linkedin": {
        "required": ["impressions", "reactions", "comments", "reshares", "saves"],
        "score": lambda m: (
            m.get("comments", 0) * 15
            + m.get("saves", 0) * 10
            + m.get("reshares", 0) * 8
            + m.get("reactions", 0) * 1
        ),
    },
    "x": {
        "required": ["impressions", "replies", "retweets", "likes", "bookmarks"],
        "score": lambda m: (
            m.get("replies", 0) * 10
            + m.get("retweets", 0) * 8
            + m.get("bookmarks", 0) * 6
            + m.get("quote_tweets", 0) * 7
            + m.get("likes", 0) * 1
        ),
    },
    "instagram": {
        # feed post scoring; reels override below
        "required": ["reach", "likes", "comments", "saves", "shares"],
        "score": lambda m: (
            m.get("saves", 0) * 15
            + m.get("shares", 0) * 10
            + m.get("comments", 0) * 5
            + m.get("likes", 0) * 1
        ),
    },
    "instagram-reel": {
        "required": ["plays", "reach", "likes", "comments", "saves", "shares"],
        "score": lambda m: (
            m.get("saves", 0) * 15
            + m.get("shares", 0) * 10
            + m.get("comments", 0) * 5
            + m.get("likes", 0) * 1
            + (m.get("completion_rate", 0) or 0) * 20
        ),
    },
    "instagram-story": {
        "required": ["views"],
        "score": lambda m: (
            m.get("replies", 0) * 20
            + m.get("taps_back", 0) * 5
            + m.get("views", 0) * 1
            - m.get("exits", 0) * 2
        ),
    },
    "facebook": {
        "required": ["reach", "reactions", "comments", "shares"],
        "score": lambda m: (
            m.get("shares", 0) * 10
            + m.get("comments", 0) * 8
            + m.get("reactions", 0) * 1
        ),
    },
    "whatsapp-status": {
        "required": ["views"],
        "score": lambda m: m.get("replies", 0) * 20 + m.get("views", 0) * 1,
    },
    "whatsapp-channel": {
        "required": ["views", "reactions", "forwards"],
        "score": lambda m: (
            m.get("forwards", 0) * 15
            + m.get("reactions", 0) * 3
            + m.get("views", 0) * 1
        ),
    },
}


def parse_frontmatter(text: str):
    meta, body = {}, text
    if text.startswith("---\n"):
        parts = text.split("---\n", 2)
        if len(parts) >= 3:
            for line in parts[1].splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    meta[k.strip()] = v.strip()
            body = parts[2]
    return meta, body.strip()


def resolve_channel_key(channel: str, fmt: str) -> str:
    """Pick the right SCORERS key given channel + format combination."""
    c = (channel or "").lower()
    f = (fmt or "").lower()
    if c == "instagram" and "reel" in f:
        return "instagram-reel"
    if c == "instagram" and "story" in f:
        return "instagram-story"
    if c == "instagram":
        return "instagram"
    if c == "whatsapp" and "channel" in f:
        return "whatsapp-channel"
    if c == "whatsapp":
        return "whatsapp-status"
    return c  # linkedin, x, facebook


def validate_metrics(metrics: dict, scorer_key: str):
    scorer = SCORERS.get(scorer_key)
    if not scorer:
        return [f"Unknown channel/format scorer key '{scorer_key}'. Supported: {sorted(SCORERS.keys())}"]
    errors = []
    for req in scorer["required"]:
        if req not in metrics:
            errors.append(f"Missing required metric '{req}' for {scorer_key}")
        elif not isinstance(metrics[req], (int, float)):
            errors.append(f"Metric '{req}' must be numeric")
    return errors


def load_log(brand_folder: Path):
    p = brand_folder / "brand" / "performance" / "log.json"
    if not p.exists():
        return {
            "schema_version": "1.0",
            "description": "Append-only log of post performance records. Consumed by weekly_review.py.",
            "entries": [],
        }
    with open(p) as f:
        return json.load(f)


def save_log(brand_folder: Path, log: dict):
    p = brand_folder / "brand" / "performance" / "log.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".json.tmp")
    with open(tmp, "w") as f:
        json.dump(log, f, indent=2)
    tmp.replace(p)


def update_post_frontmatter(post_file: Path, performance_record: dict):
    text = post_file.read_text(errors="replace")
    meta, body = parse_frontmatter(text)

    # Attach a compact performance summary (not the full record; that's in the log)
    summary = {
        "weighted_score": performance_record["weighted_score"],
        "impressions": performance_record["metrics"].get("impressions") or performance_record["metrics"].get("reach") or performance_record["metrics"].get("views") or 0,
        "recorded_at": performance_record["recorded_at"],
    }
    meta["performance"] = json.dumps(summary, separators=(",", ":"))

    fm_lines = ["---"]
    for k, v in meta.items():
        fm_lines.append(f"{k}: {v}")
    fm_lines.append("---")
    new_text = "\n".join(fm_lines) + "\n" + body + "\n"
    post_file.write_text(new_text)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("post_file", type=Path)
    ap.add_argument("--metrics", type=str, help="JSON string of metrics")
    ap.add_argument("--metrics-file", type=Path, help="Path to JSON file with metrics")
    ap.add_argument("--published-at", type=str,
                    help="ISO timestamp of when the post was published (default: now)")
    ap.add_argument("--brand-folder", type=Path,
                    default=Path("/Users/digischola/Desktop/Digischola"))
    ap.add_argument("--exclude", action="store_true",
                    help="Mark record as excluded from baseline computation")
    args = ap.parse_args()

    if not args.post_file.exists():
        sys.exit(f"Post file not found: {args.post_file}")

    # Load metrics
    if args.metrics_file:
        with open(args.metrics_file) as f:
            metrics = json.load(f)
    elif args.metrics:
        metrics = json.loads(args.metrics)
    else:
        sys.exit("Must supply --metrics JSON string or --metrics-file")

    # Read post frontmatter
    text = args.post_file.read_text(errors="replace")
    meta, _ = parse_frontmatter(text)

    required_fm = ["entry_id", "channel", "format", "pillar"]
    missing = [f for f in required_fm if f not in meta]
    if missing:
        print(f"  ERROR: post frontmatter missing fields: {missing}", file=sys.stderr)
        sys.exit(1)

    scorer_key = resolve_channel_key(meta["channel"], meta["format"])
    errors = validate_metrics(metrics, scorer_key)
    if errors:
        for e in errors:
            print(f"  ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    # Compute weighted score
    scorer = SCORERS[scorer_key]
    weighted_score = scorer["score"](metrics)

    # Build record
    now_iso = datetime.now(timezone.utc).isoformat()
    record = {
        "id": str(uuid.uuid4()),
        "recorded_at": now_iso,
        "published_at": args.published_at or now_iso,
        "post_file": str(args.post_file),
        "entry_id": meta.get("entry_id"),
        "channel": meta.get("channel"),
        "format": meta.get("format"),
        "scorer_key": scorer_key,
        "hook_category": meta.get("hook_category"),
        "voice_framework": meta.get("voice_framework"),
        "pillar": meta.get("pillar"),
        "repurpose_source": meta.get("repurpose_source"),
        "metrics": metrics,
        "weighted_score": weighted_score,
        "excluded": args.exclude,
    }

    # Append to log
    log = load_log(args.brand_folder)
    log["entries"].append(record)
    log["last_updated"] = now_iso
    save_log(args.brand_folder, log)

    # Stamp post frontmatter
    update_post_frontmatter(args.post_file, record)

    print(f"Recorded: {args.post_file.name}")
    print(f"  scorer: {scorer_key}")
    print(f"  weighted_score: {weighted_score}")
    print(f"  total log entries: {len(log['entries'])}")


if __name__ == "__main__":
    main()
