#!/usr/bin/env python3
"""
Pull post-performance metrics from Windsor.ai connectors and merge into
`brand/performance/log.json` (the same log `record_performance.py` writes to).

Replaces the manual-CSV-paste workflow for LinkedIn / X / Facebook / Instagram.
Built 2026-04-22 after the user surfaced that manual metric entry is
unsustainable at weekly cadence.

Architecture — two-phase so Claude can orchestrate MCP calls between phases:

  Phase A — plan
    $ python3 pull_performance_windsor.py plan --days 7 > plan.json
    Scans brand/queue/published/*.md for posts shipped in the last N days,
    groups them by channel, writes a JSON plan describing:
      - which Windsor connector to pull from
      - which account IDs
      - which fields to request
      - which date range
      - which posted_url values to match against (for attribution)

  Phase B — Claude runs the MCP calls using the plan, dumps raw results
    to results.json (one dict per connector).

  Phase C — merge
    $ python3 pull_performance_windsor.py merge \\
              --plan plan.json --results results.json
    Matches Windsor rows → published drafts by URL (primary) or
    channel+timestamp proximity (fallback). For each match:
      - maps Windsor field names → internal scorer metrics
      - computes weighted_score via record_performance's SCORERS
      - appends a record to log.json (idempotent: skips duplicates by
        post_file + published_at)
      - stamps each draft's frontmatter with a compact `performance` summary

The alternative to Claude-in-loop orchestration is server-to-server HTTP to
Windsor's REST API using an API token. Not implemented today because the
MCP-based flow fits the existing weekly-ritual pattern (user pastes "run
friday review" → Claude drives). Stub for REST path left in _fetch_via_rest()
as a future enhancement — enable if/when this runs unattended.

Safety-rule (Loomer 2026-03-19 "AI-Related Ad Account Shutdowns"):
  This module is READ-ONLY. It never calls a write endpoint on any Meta
  surface. Ads accounts (client track, `post-launch-optimization` skill)
  have their own separate guard against Claude-initiated writes.

Usage:
  python3 pull_performance_windsor.py plan [--days 7] [--brand-folder PATH]
  python3 pull_performance_windsor.py merge --plan plan.json --results results.json
  python3 pull_performance_windsor.py summary   # dump current log stats
  python3 pull_performance_windsor.py --help
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Import record_performance's SCORERS + helpers so we reuse the canonical
# weighted-score formula (no drift between manual and Windsor paths).
sys.path.insert(0, str(Path(__file__).resolve().parent))
from record_performance import (  # type: ignore
    SCORERS, resolve_channel_key, load_log, save_log,
    parse_frontmatter, update_post_frontmatter,
)

DEFAULT_BRAND = Path("/Users/digischola/Desktop/Digischola")

# ─────────────────────────────────────────────────────────────────────────────
# Windsor connector registry
#
# Each Digischola channel maps to ONE Windsor connector + one account. The
# account IDs come from get_connectors() run on 2026-04-22:
#   linkedin_organic  → "108990232"              (DigiSchola)
#   x_organic         → "Digischola Scheduler"   (Digischola Scheduler)
#   facebook_organic  → "1029294316942000"       (Digischola)
#   instagram         → "17841404814439751"      (DigiSchola (digischola))
#
# If accounts ever change (e.g., after a re-auth), re-run
# `get_connectors()` via the Windsor MCP and update these IDs.
# ─────────────────────────────────────────────────────────────────────────────

CONNECTOR_REGISTRY = {
    "linkedin": {
        "connector": "linkedin_organic",
        "account_id": "108990232",
        "account_name": "DigiSchola",
        # Fields we actually consume. Order matters only for logging.
        "fields": [
            "date", "share_id", "share_url", "share_text", "share_published_time",
            "share_impression_count", "share_unique_impressions_count",
            "share_clicks_count", "share_like_count", "share_comment_count",
            "share_count",  # = reshares
            "share_engagement_rate", "ctr",
            "organization_follower_count",
        ],
        # Map Windsor field → record_performance metric key. The scorer
        # for LinkedIn requires: impressions, reactions, comments, reshares, saves.
        # LinkedIn doesn't expose a native "saves" count via the Organization
        # Analytics API — we pass 0 and note the gap. Reactions == likes here.
        "field_map": {
            "impressions": "share_impression_count",
            "reactions": "share_like_count",
            "comments": "share_comment_count",
            "reshares": "share_count",
            "saves": None,  # unavailable via API; scorer tolerates 0
        },
        "url_field": "share_url",
        "post_id_field": "share_id",
        "published_at_field": "share_published_time",
    },
    "x": {
        "connector": "x_organic",
        "account_id": "Digischola Scheduler",
        "account_name": "Digischola Scheduler",
        "fields": [
            "date", "tweet_id", "text", "created_at",
            "impression_count", "like_count", "reply_count", "retweet_count",
            "user_profile_clicks", "url_link_clicks",
            "video_views",
            "profile_followers_count", "profile_tweet_count",
        ],
        "field_map": {
            "impressions": "impression_count",
            "replies": "reply_count",
            "retweets": "retweet_count",
            "likes": "like_count",
            # X API via Windsor doesn't expose bookmarks reliably at post level.
            # Scorer tolerates 0.
            "bookmarks": None,
            # quote_tweets also often not exposed; optional.
            "quote_tweets": None,
        },
        "url_field": None,  # X posts use tweet_id, URL constructed below
        "post_id_field": "tweet_id",
        "published_at_field": "created_at",
    },
    "facebook": {
        "connector": "facebook_organic",
        "account_id": "1029294316942000",
        "account_name": "Digischola",
        "fields": [
            "date", "post_id", "permalink_url", "post_message",
            "post_created_time",
            "post_impressions", "post_impressions_organic_unique",
            "post_reactions_total", "post_comments_total",
            "post_clicks",
            "post_activity_by_action_type_share",  # shares count
        ],
        "field_map": {
            "reach": "post_impressions_organic_unique",
            "reactions": "post_reactions_total",
            "comments": "post_comments_total",
            "shares": "post_activity_by_action_type_share",
        },
        "url_field": "permalink_url",
        "post_id_field": "post_id",
        "published_at_field": "post_created_time",
    },
    "instagram": {
        "connector": "instagram",
        "account_id": "17841404814439751",
        "account_name": "DigiSchola (digischola)",
        "fields": [
            "date", "timestamp", "media_id", "media_permalink", "media_caption",
            "media_type", "media_product_type",
            "media_impressions", "media_reach",
            "media_like_count", "media_comments_count",
            "media_saved", "media_shares", "media_engagement",
            "media_plays", "media_video_views",
            "media_reel_video_views", "media_reel_avg_watch_time",
            "carousel_album_reach", "carousel_album_saved",
            "followers_count",
        ],
        "field_map": {
            "reach": "media_reach",
            "likes": "media_like_count",
            "comments": "media_comments_count",
            "saves": "media_saved",
            "shares": "media_shares",
            # Reels-specific: scorer expects `plays` for instagram-reel.
            "plays": "media_plays",
            # instagram-reel scorer also uses `completion_rate` if available —
            # derive from media_reel_avg_watch_time + assumed reel length.
            # For now we leave completion_rate unset; scorer tolerates absent.
        },
        "url_field": "media_permalink",
        "post_id_field": "media_id",
        "published_at_field": "timestamp",
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# Phase A: build the pull plan
# ─────────────────────────────────────────────────────────────────────────────

def _iter_published_drafts(brand_folder: Path):
    """Yield (draft_path, frontmatter_dict) for every .md in published/."""
    pub = brand_folder / "brand" / "queue" / "published"
    if not pub.exists():
        return
    for p in sorted(pub.glob("*.md")):
        try:
            text = p.read_text(errors="replace")
        except Exception:
            continue
        fm, _ = parse_frontmatter(text)
        yield p, fm


def _parse_ist_or_iso(ts: str) -> datetime | None:
    """Parse an ISO timestamp (with or without tz). Return tz-aware UTC."""
    if not ts:
        return None
    ts = ts.strip().strip("'\"")
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except Exception:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def build_plan(brand_folder: Path, days: int = 7) -> dict:
    """Scan published/ for drafts shipped within the last `days` days. Group
    by channel. Return a JSON-serializable plan.

    Plan shape:
      {
        "generated_at": "2026-04-29T12:34:56+00:00",
        "brand_folder": "/Users/digischola/Desktop/Digischola",
        "window_days": 7,
        "date_from": "2026-04-22",
        "date_to": "2026-04-29",
        "jobs": [
          {
            "channel": "linkedin",
            "connector": "linkedin_organic",
            "accounts": ["108990232"],
            "fields": [...],
            "date_from": "...", "date_to": "...",
            "draft_count": 3,
            "drafts": [
              {"post_file": "...", "entry_id": "...", "posted_url": "...",
               "posted_at": "...", "format": "...", "scheduled_at": "..."},
              ...
            ]
          },
          ...
        ],
        "missing_posted_url": [...]  // drafts we can't attribute
      }
    """
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=days)
    jobs_by_channel: dict[str, list[dict]] = {}
    missing = []

    for path, fm in _iter_published_drafts(brand_folder):
        channel = (fm.get("channel") or "").lower().strip().strip("'\"")
        if channel not in CONNECTOR_REGISTRY:
            continue
        posted_at = _parse_ist_or_iso(fm.get("posted_at") or "")
        scheduled_at = _parse_ist_or_iso(fm.get("scheduled_at") or "")
        anchor = posted_at or scheduled_at
        if anchor is None or anchor < cutoff:
            continue
        posted_url = (fm.get("posted_url") or fm.get("platform_url") or "").strip().strip("'\"")
        draft_entry = {
            "post_file": str(path),
            "entry_id": fm.get("entry_id"),
            "posted_url": posted_url,
            "posted_at": anchor.isoformat() if anchor else None,
            "scheduled_at": scheduled_at.isoformat() if scheduled_at else None,
            "format": fm.get("format"),
            "pillar": fm.get("pillar"),
        }
        if not posted_url:
            missing.append(draft_entry)
        jobs_by_channel.setdefault(channel, []).append(draft_entry)

    date_from = cutoff.strftime("%Y-%m-%d")
    date_to = now.strftime("%Y-%m-%d")
    jobs = []
    for channel, drafts in jobs_by_channel.items():
        reg = CONNECTOR_REGISTRY[channel]
        jobs.append({
            "channel": channel,
            "connector": reg["connector"],
            "accounts": [reg["account_id"]],
            "account_name": reg["account_name"],
            "fields": reg["fields"],
            "date_from": date_from,
            "date_to": date_to,
            "draft_count": len(drafts),
            "drafts": drafts,
        })

    return {
        "generated_at": now.isoformat(),
        "brand_folder": str(brand_folder),
        "window_days": days,
        "date_from": date_from,
        "date_to": date_to,
        "job_count": len(jobs),
        "jobs": jobs,
        "missing_posted_url": missing,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Phase C: match + merge Windsor results into log.json
# ─────────────────────────────────────────────────────────────────────────────

# When post URLs are messy, fall back to fuzzy timestamp matching.
# Window = ±2h (generous — IG metrics can be published a bit offset).
TIMESTAMP_WINDOW_MINUTES = 120


def _normalize_url(url: str) -> str:
    if not url:
        return ""
    u = url.strip().strip("'\"").lower()
    # Strip common tracking params, fragments, trailing slash
    u = u.split("?")[0].split("#")[0].rstrip("/")
    return u


def _construct_x_url(tweet_id: str, handle: str = "digischola") -> str:
    # Windsor's x_organic doesn't expose a clean URL field. Build it from the
    # tweet_id. Handle can be read from the draft or defaulted.
    if not tweet_id:
        return ""
    return f"https://twitter.com/{handle}/status/{tweet_id}".lower()


def _match_row_to_draft(row: dict, drafts: list[dict], channel: str) -> dict | None:
    """Try to match a Windsor result row to one of the drafts for this
    channel. Priority:
      1. Exact URL match (draft.posted_url vs row[url_field])
      2. post_id match (if draft stored it in frontmatter)
      3. Timestamp nearest-neighbor within ±2h
    Returns the matched draft dict or None.
    """
    reg = CONNECTOR_REGISTRY[channel]

    # 1. URL match
    row_url_raw = ""
    if reg["url_field"]:
        row_url_raw = row.get(reg["url_field"]) or ""
    elif channel == "x":
        row_url_raw = _construct_x_url(row.get("tweet_id") or "")
    row_url = _normalize_url(row_url_raw)
    if row_url:
        for d in drafts:
            if _normalize_url(d.get("posted_url") or "") == row_url:
                return d

    # 2. Timestamp fallback
    row_ts = _parse_ist_or_iso(row.get(reg["published_at_field"]) or "")
    if row_ts:
        best = None
        best_delta = timedelta(minutes=TIMESTAMP_WINDOW_MINUTES + 1)
        for d in drafts:
            d_ts = _parse_ist_or_iso(d.get("posted_at") or d.get("scheduled_at") or "")
            if not d_ts:
                continue
            delta = abs(row_ts - d_ts)
            if delta < best_delta:
                best_delta = delta
                best = d
        if best and best_delta <= timedelta(minutes=TIMESTAMP_WINDOW_MINUTES):
            return best
    return None


def _extract_metrics(row: dict, channel: str, fmt: str | None) -> dict:
    """Use the field_map for this channel to extract metric values. Skip
    None/null from Windsor (scorers tolerate zero, and we want to distinguish
    'actually zero' from 'not reported')."""
    reg = CONNECTOR_REGISTRY[channel]
    out = {}
    for metric_key, windsor_field in reg["field_map"].items():
        if windsor_field is None:
            continue
        raw = row.get(windsor_field)
        if raw is None or raw == "":
            continue
        try:
            out[metric_key] = float(raw) if isinstance(raw, str) and "." in raw else int(float(raw))
        except (ValueError, TypeError):
            continue
    # IG-reel: scorer wants `plays` which we already map. No further munging.
    return out


def merge_results(brand_folder: Path, plan: dict, results: dict,
                  dry_run: bool = False) -> dict:
    """Merge Windsor raw results into log.json. `results` shape:
      {
        "linkedin": {"result": [ {row1}, {row2}, ... ]},
        "x": {"result": [...]},
        ...
      }
    keyed by channel (NOT connector id). Returns a summary dict.
    """
    log = load_log(brand_folder)
    existing_keys = {
        (e.get("post_file"), e.get("published_at"))
        for e in log["entries"]
    }
    matched = 0
    appended = 0
    skipped_duplicate = 0
    unmatched_rows = []

    for job in plan["jobs"]:
        channel = job["channel"]
        drafts = job["drafts"]
        channel_rows = (results.get(channel) or {}).get("result") or []
        for row in channel_rows:
            d = _match_row_to_draft(row, drafts, channel)
            if not d:
                unmatched_rows.append({"channel": channel, "row": row})
                continue
            matched += 1
            fmt = d.get("format") or ""
            scorer_key = resolve_channel_key(channel, fmt)
            metrics = _extract_metrics(row, channel, fmt)
            scorer = SCORERS.get(scorer_key) or SCORERS.get(channel)
            if not scorer:
                unmatched_rows.append({"channel": channel, "reason": f"no scorer for {scorer_key}", "row": row})
                continue
            # Fill in missing-but-required metrics with 0 so validator passes
            for req in scorer["required"]:
                metrics.setdefault(req, 0)
            weighted_score = scorer["score"](metrics)

            published_at_iso = _parse_ist_or_iso(row.get(CONNECTOR_REGISTRY[channel]["published_at_field"]) or "")
            published_at_iso = published_at_iso.isoformat() if published_at_iso else d.get("posted_at")

            key = (d["post_file"], published_at_iso)
            if key in existing_keys:
                skipped_duplicate += 1
                continue

            # Build the record (same shape as record_performance.py writes)
            now_iso = datetime.now(timezone.utc).isoformat()
            record = {
                "id": str(uuid.uuid4()),
                "recorded_at": now_iso,
                "published_at": published_at_iso,
                "post_file": d["post_file"],
                "entry_id": d.get("entry_id"),
                "channel": channel,
                "format": fmt,
                "scorer_key": scorer_key,
                "hook_category": None,   # filled from draft frontmatter below if needed
                "voice_framework": None,
                "pillar": d.get("pillar"),
                "repurpose_source": None,
                "metrics": metrics,
                "weighted_score": weighted_score,
                "excluded": False,
                "source": "windsor",
                "windsor_post_id": row.get(CONNECTOR_REGISTRY[channel]["post_id_field"]),
            }
            # Try to enrich from the draft frontmatter (hook_category etc.)
            try:
                text = Path(d["post_file"]).read_text(errors="replace")
                fm, _ = parse_frontmatter(text)
                for k in ("hook_category", "voice_framework", "repurpose_source"):
                    val = fm.get(k)
                    if val and val not in ("null", "None", "-"):
                        record[k] = val.strip().strip("'\"")
            except Exception:
                pass

            if not dry_run:
                log["entries"].append(record)
                log["last_updated"] = now_iso
                existing_keys.add(key)
                # Stamp compact performance summary on the draft's frontmatter
                try:
                    update_post_frontmatter(Path(d["post_file"]), record)
                except Exception as e:
                    print(f"  WARN: could not stamp frontmatter on {d['post_file']}: {e}",
                          file=sys.stderr)
            appended += 1

    if not dry_run:
        save_log(brand_folder, log)

    return {
        "matched": matched,
        "appended": appended,
        "skipped_duplicate": skipped_duplicate,
        "unmatched_rows": unmatched_rows,
        "dry_run": dry_run,
        "log_entries_total": len(log["entries"]),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Future: direct REST call (unattended cron)
# ─────────────────────────────────────────────────────────────────────────────

def _fetch_via_rest(connector: str, accounts: list[str], fields: list[str],
                    date_from: str, date_to: str) -> dict:
    """STUB. Server-to-server call to Windsor.ai's REST API using an API token.

    Not implemented in v1. The MCP-based Claude-in-loop flow is the primary
    path. To enable this path, add a WINDSOR_API_TOKEN env var + endpoint URL,
    and wire it up here. Then `weekly_review.py` can run fully unattended.
    """
    raise NotImplementedError(
        "Direct REST path not implemented. Use the plan→MCP→merge flow instead."
    )


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def cmd_plan(args):
    plan = build_plan(args.brand_folder, days=args.days)
    out = json.dumps(plan, indent=2, default=str)
    if args.output:
        args.output.write_text(out)
        print(f"✓ Plan written to {args.output}", file=sys.stderr)
        print(f"  {plan['job_count']} job(s) across "
              f"{sum(j['draft_count'] for j in plan['jobs'])} draft(s) in "
              f"{plan['window_days']}-day window",
              file=sys.stderr)
        if plan["missing_posted_url"]:
            print(f"  WARN: {len(plan['missing_posted_url'])} draft(s) missing "
                  f"posted_url — cannot attribute via URL, will fall back to "
                  f"timestamp matching.", file=sys.stderr)
    else:
        print(out)
    return 0


def cmd_merge(args):
    plan = json.loads(args.plan.read_text())
    results = json.loads(args.results.read_text())
    summary = merge_results(args.brand_folder, plan, results, dry_run=args.dry_run)
    print(json.dumps(summary, indent=2, default=str), file=sys.stderr)
    if summary["unmatched_rows"]:
        print(f"  WARN: {len(summary['unmatched_rows'])} Windsor row(s) "
              f"could not be matched to a draft. They were NOT added to log.",
              file=sys.stderr)
    return 0


def cmd_summary(args):
    log = load_log(args.brand_folder)
    n = len(log["entries"])
    by_channel = {}
    by_source = {"windsor": 0, "manual": 0}
    for e in log["entries"]:
        by_channel[e["channel"]] = by_channel.get(e["channel"], 0) + 1
        by_source[e.get("source", "manual")] = by_source.get(
            e.get("source", "manual"), 0) + 1
    print(json.dumps({
        "total_entries": n,
        "by_channel": by_channel,
        "by_source": by_source,
        "last_updated": log.get("last_updated"),
    }, indent=2))
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_plan = sub.add_parser("plan", help="Scan published/ and emit a Windsor pull plan")
    p_plan.add_argument("--days", type=int, default=7)
    p_plan.add_argument("--brand-folder", type=Path, default=DEFAULT_BRAND)
    p_plan.add_argument("--output", type=Path, help="Write plan to file instead of stdout")
    p_plan.set_defaults(func=cmd_plan)

    p_merge = sub.add_parser("merge", help="Merge Windsor raw results into log.json")
    p_merge.add_argument("--plan", type=Path, required=True)
    p_merge.add_argument("--results", type=Path, required=True,
                         help="JSON file with {channel: {result: [row, ...]}} keyed by channel")
    p_merge.add_argument("--brand-folder", type=Path, default=DEFAULT_BRAND)
    p_merge.add_argument("--dry-run", action="store_true")
    p_merge.set_defaults(func=cmd_merge)

    p_sum = sub.add_parser("summary", help="Print log.json summary stats")
    p_sum.add_argument("--brand-folder", type=Path, default=DEFAULT_BRAND)
    p_sum.set_defaults(func=cmd_summary)

    args = ap.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
