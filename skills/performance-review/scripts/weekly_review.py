#!/usr/bin/env python3
"""
Generate the weekly performance review report.

Reads brand/performance/log.json, computes rolling 30-day baselines per channel,
buckets last-7-days posts (Hit/Above/Below/Flop), and writes the week's report
to brand/performance/YYYY-WXX.md.

If there are <21 days of total data for a channel, that channel runs in
"Collecting baseline" mode (no bucketing, raw numbers only). If ≥56 days of
data exist, the report also emits promotion/deprecation suggestions per
scoring-rules.md.

Usage:
  python3 weekly_review.py
  python3 weekly_review.py --week 2026-04-20
  python3 weekly_review.py --brand-folder /custom/path

Exit codes:
  0 = report generated
  1 = no data in log (nothing to review)
"""

import argparse
import json
import statistics
import sys
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

# Shared notify helper (click-through)
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "shared-scripts"))
try:
    from notify import notify as _notify  # type: ignore
except ImportError:
    _notify = None


def iso_week_string(d: date) -> str:
    y, w, _ = d.isocalendar()
    return f"{y}-W{w:02d}"


def monday_of_current_week(ref: date = None) -> date:
    ref = ref or date.today()
    return ref - timedelta(days=ref.weekday())


def parse_iso(s: str) -> datetime:
    # Handle both +00:00 and Z suffixes
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    return datetime.fromisoformat(s)


def load_log(brand_folder: Path):
    p = brand_folder / "brand" / "performance" / "log.json"
    if not p.exists():
        return None
    with open(p) as f:
        return json.load(f)


def baseline_mode_for_channel(entries_for_channel, now_dt):
    """Decide mode: Collecting (0-20d), Active early (21-55d), Active mature (56+d)."""
    if not entries_for_channel:
        return "no_data", 0
    oldest = min(parse_iso(e["published_at"]) for e in entries_for_channel)
    days = (now_dt - oldest).days
    if days < 21:
        return "collecting", days
    if days < 56:
        return "active_early", days
    return "active_mature", days


def compute_baseline(entries_for_channel, now_dt, window_days=30):
    """Median weighted_score over entries within last window_days. Excludes `excluded` entries."""
    cutoff = now_dt - timedelta(days=window_days)
    eligible = [
        e for e in entries_for_channel
        if not e.get("excluded") and parse_iso(e["published_at"]) >= cutoff
    ]
    if len(eligible) < 5:
        return None, len(eligible)
    scores = [e["weighted_score"] for e in eligible]
    return statistics.median(scores), len(eligible)


def bucket_entry(score, sorted_scores):
    """Return HIT/ABOVE/BELOW/FLOP given the channel's sorted scores for percentile."""
    if not sorted_scores:
        return "COLLECTING"
    n = len(sorted_scores)
    rank = sum(1 for s in sorted_scores if s <= score)
    pct = rank / n
    if pct >= 0.80:
        return "HIT"
    if pct >= 0.50:
        return "ABOVE"
    if pct >= 0.20:
        return "BELOW"
    return "FLOP"


def bucket_points(bucket):
    return {"HIT": 2, "ABOVE": 1, "BELOW": -1, "FLOP": -2, "COLLECTING": 0}.get(bucket, 0)


def aggregate_pattern_scores(weekly_posts_with_buckets, all_recent_by_pattern):
    """Aggregate bucket points per pattern (hook, framework, recipe source, slot)."""
    patterns = defaultdict(lambda: {"points": 0, "count": 0, "hits": 0, "flops": 0})
    for post, bucket in weekly_posts_with_buckets:
        pts = bucket_points(bucket)
        for key, dim in [
            (post.get("hook_category"), "hook"),
            (post.get("voice_framework"), "framework"),
            (post.get("pillar"), "pillar"),
            (post.get("repurpose_source"), "recipe"),
        ]:
            if not key:
                continue
            k = f"{dim}:{key}"
            patterns[k]["points"] += pts
            patterns[k]["count"] += 1
            if bucket == "HIT":
                patterns[k]["hits"] += 1
            if bucket == "FLOP":
                patterns[k]["flops"] += 1
    return dict(patterns)


def generate_suggestions(pattern_scores, mode):
    """Per promotion-rules.md thresholds. Only emits if mode == active_mature."""
    if mode != "active_mature":
        return []
    suggestions = []
    for pattern, data in pattern_scores.items():
        dim, name = pattern.split(":", 1)
        pts = data["points"]
        n = data["count"]

        # Promotion thresholds per dimension
        if dim == "hook" and pts >= 6 and n >= 3:
            suggestions.append({
                "priority": "P1",
                "type": "promote",
                "pattern": f"Hook Category: {name}",
                "target": "post-writer/references/hook-library.md",
                "edit": f"Add 'Tier 1' tag next to rows in category {name}",
                "evidence": f"Net +{pts} over {n} posts, {data['hits']} HITs, {data['flops']} FLOPs",
            })
        if dim == "framework" and pts >= 4 and n >= 3:
            suggestions.append({
                "priority": "P1",
                "type": "promote",
                "pattern": f"Voice Framework: {name}",
                "target": "post-writer/references/voice-frameworks.md",
                "edit": f"Add performance note: 'net +{pts} over {n} uses'",
                "evidence": f"Net +{pts} over {n} posts, {data['hits']} HITs",
            })
        if dim == "pillar" and pts >= 6 and n >= 4:
            suggestions.append({
                "priority": "P2",
                "type": "reinforce",
                "pattern": f"Pillar: {name}",
                "target": "brand/_engine/wiki/channel-playbook.md",
                "edit": "Consider increasing this pillar's cadence share",
                "evidence": f"Net +{pts} over {n} posts",
            })
        # Deprecation thresholds
        if dim == "hook" and pts <= -4 and n >= 2:
            suggestions.append({
                "priority": "P2",
                "type": "deprecate",
                "pattern": f"Hook Category: {name}",
                "target": "post-writer/references/hook-library.md",
                "edit": f"Strikethrough rows in category {name} with note",
                "evidence": f"Net {pts} over {n} posts, {data['flops']} FLOPs",
            })
        if dim == "framework" and pts <= -3 and n >= 2:
            suggestions.append({
                "priority": "P2",
                "type": "deprecate",
                "pattern": f"Voice Framework: {name}",
                "target": "post-writer/references/voice-frameworks.md",
                "edit": "Add review-needed note",
                "evidence": f"Net {pts} over {n} posts",
            })
    # Sort by priority
    suggestions.sort(key=lambda s: s["priority"])
    return suggestions


def render_report(week_start: date, entries_by_channel, now_dt, suggestions, flags):
    iso = iso_week_string(week_start)
    lines = []
    lines.append(f"# Performance Review. Week of {week_start.isoformat()} ({iso})")
    lines.append("")
    lines.append(f"Generated: {date.today().isoformat()}")
    lines.append("")

    total_week = sum(len(v["weekly"]) for v in entries_by_channel.values())
    if total_week == 0:
        lines.append("## No posts to review")
        lines.append("")
        lines.append("No posts were recorded in the last 7 days. Run `record_performance.py` after shipping to log metrics.")
        return "\n".join(lines) + "\n"

    # Week summary
    lines.append("## Week summary")
    lines.append("")
    lines.append(f"- Posts reviewed: {total_week}")
    top_hit = None
    top_flop = None
    for ch, v in entries_by_channel.items():
        for post, bucket in v["weekly_with_buckets"]:
            if bucket == "HIT":
                if not top_hit or post["weighted_score"] > top_hit["weighted_score"]:
                    top_hit = post
            if bucket == "FLOP":
                if not top_flop or post["weighted_score"] < top_flop["weighted_score"]:
                    top_flop = post
    if top_hit:
        lines.append(f"- Top hit: `{Path(top_hit['post_file']).name}` ({top_hit['channel']}, score {top_hit['weighted_score']})")
    if top_flop:
        lines.append(f"- Biggest flop: `{Path(top_flop['post_file']).name}` ({top_flop['channel']}, score {top_flop['weighted_score']})")
    lines.append("")

    # Per-channel
    lines.append("## By channel")
    lines.append("")
    for ch, v in sorted(entries_by_channel.items()):
        mode = v["mode"]
        baseline = v["baseline"]
        n_recent = v["baseline_n"]
        lines.append(f"### {ch} ({mode}, {v['days']} days of data)")
        if baseline is None:
            lines.append(f"- Insufficient data for baseline ({n_recent} eligible posts; need 5+).")
        else:
            lines.append(f"- 30-day baseline median: {baseline} (n={n_recent})")
        lines.append("")
        lines.append("| Post | Bucket | Score | Impressions | Hook | Framework |")
        lines.append("|---|---|---|---|---|---|")
        for post, bucket in v["weekly_with_buckets"]:
            imp = post["metrics"].get("impressions") or post["metrics"].get("reach") or post["metrics"].get("views") or "-"
            hook = post.get("hook_category") or "-"
            fw = post.get("voice_framework") or "-"
            name = Path(post["post_file"]).name
            lines.append(f"| `{name}` | {bucket} | {post['weighted_score']} | {imp} | {hook} | {fw} |")
        lines.append("")

    # Flags
    if flags:
        lines.append("## Flags")
        lines.append("")
        for f in flags:
            lines.append(f"- **{f['type']}**: {f['message']}")
        lines.append("")

    # Suggestions
    lines.append("## Suggestions")
    lines.append("")
    if not suggestions:
        # Determine if any channel is mature
        any_mature = any(v["mode"] == "active_mature" for v in entries_by_channel.values())
        if not any_mature:
            lines.append("No suggestions yet. Channels need 56+ days of data to trigger promotion/deprecation logic.")
        else:
            lines.append("No patterns crossed promotion or deprecation thresholds this week.")
        lines.append("")
    else:
        lines.append("Review each suggestion and apply manually per `promotion-rules.md`. v1 is advisory only.")
        lines.append("")
        for s in suggestions:
            lines.append(f"### [{s['priority']}] {s['type'].upper()}: {s['pattern']}")
            lines.append(f"- Target: `{s['target']}`")
            lines.append(f"- Edit: {s['edit']}")
            lines.append(f"- Evidence: {s['evidence']}")
            lines.append("")

    lines.append("---")
    lines.append("Generated by performance-review skill. Source: `brand/performance/log.json`. Apply suggestions manually; v1 is advisory.")
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--brand-folder", type=Path,
                    default=Path("/Users/digischola/Desktop/Digischola"))
    ap.add_argument("--week", type=str, default=None,
                    help="Monday of target week (YYYY-MM-DD). Default: current week.")
    args = ap.parse_args()

    log = load_log(args.brand_folder)
    if log is None or not log.get("entries"):
        # Windsor pull is the primary path as of 2026-04-22; record_performance.py
        # is the manual fallback. Point the user at the right recipe.
        print(
            "BLOCKED: performance log is empty. Populate it first, one of:\n"
            "  (1) Windsor pull (preferred):\n"
            "      python3 pull_performance_windsor.py plan --days 7 --output /tmp/plan.json\n"
            "      # then have Claude execute each job via Windsor MCP → results.json\n"
            "      python3 pull_performance_windsor.py merge --plan /tmp/plan.json --results /tmp/results.json\n"
            "  (2) Manual fallback (if Windsor unavailable):\n"
            "      python3 record_performance.py <post.md> --metrics '{...}'\n"
            "See references/windsor-field-map.md for the connector+field reference."
        )
        sys.exit(1)

    # Determine week
    if args.week:
        week_start = datetime.strptime(args.week, "%Y-%m-%d").date()
    else:
        week_start = monday_of_current_week()
    week_end = week_start + timedelta(days=7)

    now_dt = datetime.now(timezone.utc)

    # Group entries by channel
    by_channel_all = defaultdict(list)
    for e in log["entries"]:
        if e.get("excluded"):
            continue
        by_channel_all[e["channel"]].append(e)

    entries_by_channel = {}
    for ch, entries in by_channel_all.items():
        mode, days = baseline_mode_for_channel(entries, now_dt)
        baseline, baseline_n = compute_baseline(entries, now_dt)

        # Filter to this week's posts
        weekly = [
            e for e in entries
            if week_start <= parse_iso(e["published_at"]).date() < week_end
        ]

        # Bucket each weekly post using the last-30-days sorted scores
        cutoff = now_dt - timedelta(days=30)
        recent_scores = sorted([
            e["weighted_score"] for e in entries
            if parse_iso(e["published_at"]) >= cutoff and not e.get("excluded")
        ])
        weekly_with_buckets = [
            (e, bucket_entry(e["weighted_score"], recent_scores)
             if mode in ("active_early", "active_mature") else "COLLECTING")
            for e in weekly
        ]

        entries_by_channel[ch] = {
            "mode": mode,
            "days": days,
            "baseline": baseline,
            "baseline_n": baseline_n,
            "weekly": weekly,
            "weekly_with_buckets": weekly_with_buckets,
        }

    # Aggregate pattern scores across all channels
    all_weekly_with_buckets = []
    for v in entries_by_channel.values():
        all_weekly_with_buckets.extend(v["weekly_with_buckets"])
    pattern_scores = aggregate_pattern_scores(all_weekly_with_buckets, by_channel_all)

    # Determine overall mode (most mature channel)
    any_mature = any(v["mode"] == "active_mature" for v in entries_by_channel.values())
    overall_mode = "active_mature" if any_mature else (
        "active_early" if any(v["mode"] == "active_early" for v in entries_by_channel.values())
        else "collecting"
    )
    suggestions = generate_suggestions(pattern_scores, overall_mode)

    # Flags (hook_overexposed, pillar_imbalance, etc.)
    flags = []
    # hook overexposure check
    hook_counts = Counter(
        p.get("hook_category") for v in entries_by_channel.values()
        for p in v["weekly"] if p.get("hook_category")
    )
    total_with_hook = sum(hook_counts.values())
    if total_with_hook >= 5:
        for hook, cnt in hook_counts.items():
            if cnt / total_with_hook >= 0.4:
                flags.append({
                    "type": "hook_overexposed",
                    "message": f"{hook} used in {cnt}/{total_with_hook} posts this week ({cnt/total_with_hook*100:.0f}%). Consider rotating.",
                })
    # pillar imbalance
    pillar_counts = Counter(
        p.get("pillar") for v in entries_by_channel.values()
        for p in v["weekly"] if p.get("pillar")
    )
    total_with_pillar = sum(pillar_counts.values())
    if total_with_pillar >= 4:
        for p, cnt in pillar_counts.items():
            if cnt / total_with_pillar >= 0.6:
                flags.append({
                    "type": "pillar_imbalance",
                    "message": f"Pillar '{p}' was {cnt}/{total_with_pillar} posts this week ({cnt/total_with_pillar*100:.0f}%).",
                })

    # Render
    md = render_report(week_start, entries_by_channel, now_dt, suggestions, flags)

    iso = iso_week_string(week_start)
    out_path = args.brand_folder / "brand" / "performance" / f"{iso}.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(md)

    print(f"Report written: {out_path}")
    print(f"Overall mode: {overall_mode}")
    print(f"Suggestions: {len(suggestions)}")
    print(f"Flags: {len(flags)}")

    # Click-to-open notification (2026-04-22 UX batch per backlog #6):
    # previously the weekly-review ran silently; now the banner click opens
    # the freshly-written markdown report in the user's editor.
    if _notify is not None:
        try:
            total_entries = sum(len(v) for v in entries_by_channel.values())
            _notify(
                f"Weekly review: {iso}",
                f"{total_entries} posts · {len(suggestions)} suggestions · "
                f"overall {overall_mode}. Click to open report.",
                subtitle="Digischola",
                sound="Glass",
                open_url=str(out_path.resolve()),
                group="digischola-review",
            )
        except Exception as e:
            print(f"  (notification failed: {e})", file=sys.stderr)


if __name__ == "__main__":
    main()
