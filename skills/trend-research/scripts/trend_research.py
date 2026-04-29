#!/usr/bin/env python3
"""
Trend Research orchestrator script.

Sub-commands:
  prompt           Generate Perplexity prompts (Mode 2 — deep research, manual)
  ingest-perplexity  Parse a Perplexity response file and append to idea-bank
  ingest           Append a single trend candidate JSON to idea-bank (used by Claude in Mode 1)
  dedupe-check     Test if a candidate would be deduped (returns reason or "ok")
  stats            Show per-pillar trend entry counts in idea-bank
  scan-log         Show last week's scan log

Usage:
  python3 trend_research.py prompt --week 2026-W17
  python3 trend_research.py ingest-perplexity --pillar lp-craft --week 2026-W17
  python3 trend_research.py ingest --pillar lp-craft --json '{"seed":"...","hook_candidate":"...","source_urls":["..."],"relevance_score":4}'
  python3 trend_research.py dedupe-check --json '{"seed":"..."}'
  python3 trend_research.py stats
  python3 trend_research.py scan-log --week 2026-W17
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional


DEFAULT_BRAND = Path("/Users/digischola/Desktop/Digischola")
SKILL_DIR = Path("/Users/digischola/Desktop/Claude Skills/skills/trend-research")

PILLAR_SLUGS = {
    "lp-craft": "Landing-Page Conversion Craft",
    "solo-ops": "Solo Freelance Ops",
    "paid-media": "Small-Budget Paid Media",
    "cross-pillar": "Cross-Pillar",
}

HYPE_WORDS = ["unlock", "revolutionize", "game-changer", "massive", "explode",
              "crush", "10x", "effortless", "secret", "hack"]
PAYWALLED_DOMAINS = ["nytimes.com", "ft.com", "hbr.org", "wsj.com", "businessinsider.com"]


def ist() -> timezone:
    return timezone(timedelta(hours=5, minutes=30), name="IST")


def now_ist_iso() -> str:
    return datetime.now(ist()).isoformat()


def read_idea_bank(brand_folder: Path) -> dict:
    p = brand_folder / "brand" / "_engine" / "idea-bank.json"
    if not p.exists():
        return {"schema_version": "1.0", "description": "...", "entries": []}
    return json.loads(p.read_text())


def write_idea_bank_atomic(brand_folder: Path, data: dict) -> None:
    p = brand_folder / "brand" / "_engine" / "idea-bank.json"
    tmp = p.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    tmp.replace(p)


def normalize_pillar(p: str) -> tuple[str, str]:
    """Returns (slug, human_name). Accepts both forms."""
    if p in PILLAR_SLUGS:
        return p, PILLAR_SLUGS[p]
    for slug, human in PILLAR_SLUGS.items():
        if p.lower() == human.lower():
            return slug, human
    raise ValueError(f"Unknown pillar: {p}")


# ── Dedup ────────────────────────────────────────────────────────────────


def text_similarity(a: str, b: str) -> float:
    """Token overlap ratio. Quick + dirty Jaccard."""
    if not a or not b:
        return 0.0
    ta = set(a.lower().split())
    tb = set(b.lower().split())
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / max(len(ta | tb), 1)


def dedupe_check(candidate: dict, idea_bank: dict, threshold: float = 0.7) -> Optional[str]:
    """Return None if candidate is unique, else a reason string explaining the dup."""
    cand_seed = (candidate.get("seed") or "").strip()
    cand_hook = (candidate.get("hook_candidate") or "").strip()
    cand_urls = set(candidate.get("source_urls") or [])
    cand_pillar = candidate.get("pillar")

    same_pillar_recent_count = 0
    cutoff = datetime.now(ist()) - timedelta(days=30)
    for e in idea_bank.get("entries", []):
        existing_seed = (e.get("seed") or e.get("raw_note") or "").strip()
        existing_hook = (e.get("hook_candidate") or "").strip()
        existing_urls = set(e.get("source_urls") or [])

        # Exact text match
        if cand_seed and (cand_seed == existing_seed or cand_seed == existing_hook):
            return f"exact-match seed text against existing entry"
        if cand_hook and cand_hook == existing_hook:
            return f"exact-match hook against existing entry"

        # Fuzzy match
        if cand_seed and existing_seed:
            sim = text_similarity(cand_seed, existing_seed)
            if sim >= threshold:
                return f"fuzzy-match {sim:.0%} on seed against existing entry"

        # URL overlap
        if cand_urls and existing_urls and cand_urls.issubset(existing_urls):
            return f"all source URLs already in another entry"

        # Same-pillar 30-day cap
        if e.get("type") == "trend" and e.get("pillar") == cand_pillar:
            captured = e.get("captured_at")
            if captured:
                try:
                    dt = datetime.fromisoformat(captured)
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=ist())
                    if dt >= cutoff:
                        same_pillar_recent_count += 1
                except ValueError:
                    pass

    if same_pillar_recent_count >= 8 and (candidate.get("relevance_score", 0) < 5):
        return f"pillar {cand_pillar} already has {same_pillar_recent_count} trends in last 30d (cap reached)"

    return None


# ── Quality filter ───────────────────────────────────────────────────────


def quality_filter(candidate: dict) -> Optional[str]:
    """Return None if candidate passes, else reason string for rejection."""
    score = candidate.get("relevance_score", 0)
    if score < 3:
        return f"relevance_score {score} <3"

    text_blob = " ".join([
        str(candidate.get("seed", "")),
        str(candidate.get("hook_candidate", "")),
    ]).lower()

    if "—" in text_blob or "--" in text_blob:
        return "contains em dash (or --)"

    for hype in HYPE_WORDS:
        if hype in text_blob:
            return f"contains hype word: {hype}"

    urls = candidate.get("source_urls") or []
    if not urls:
        return "no source_urls"
    non_paywalled = [u for u in urls if not any(d in u for d in PAYWALLED_DOMAINS)]
    if not non_paywalled:
        return "all source_urls are paywalled"

    pillar = candidate.get("pillar")
    if pillar not in PILLAR_SLUGS:
        return f"invalid pillar: {pillar}"

    return None


# ── Ingest ───────────────────────────────────────────────────────────────


def build_entry(candidate: dict) -> dict:
    """Normalize a candidate dict into the idea-bank entry schema."""
    slug, human = normalize_pillar(candidate.get("pillar", ""))
    seed = candidate.get("seed", "").strip()
    return {
        "id": candidate.get("id") or str(uuid.uuid4()),
        "type": "trend",
        "pillar": slug,
        "suggested_pillar": human,
        "seed": seed,
        "raw_note": seed,  # backwards compat with content-calendar
        "hook_candidate": candidate.get("hook_candidate", "").strip(),
        "channel_fit": candidate.get("channel_fit") or ["LinkedIn", "X"],
        "format_candidates": candidate.get("format_candidates") or ["LI-post", "X-thread"],
        "source_urls": list(candidate.get("source_urls") or []),
        "tags": list(candidate.get("tags") or []),
        "relevance_score": int(candidate.get("relevance_score", 3)),
        "via": "trend-research",
        "captured_at": candidate.get("captured_at") or now_ist_iso(),
        "status": "raw",
        "manual_review_needed": bool(candidate.get("manual_review_needed", False)),
        "notes": candidate.get("notes", ""),
    }


def ingest_one(brand_folder: Path, candidate: dict, dry_run: bool) -> tuple[str, str]:
    """Returns (status, reason). status in {added, skipped-dup, skipped-quality, dry-run}."""
    bank = read_idea_bank(brand_folder)

    qf = quality_filter(candidate)
    if qf:
        return "skipped-quality", qf

    dup_reason = dedupe_check(candidate, bank)
    if dup_reason:
        return "skipped-dup", dup_reason

    entry = build_entry(candidate)

    if dry_run:
        return "dry-run", json.dumps(entry, indent=2, ensure_ascii=False)

    bank["entries"].append(entry)
    write_idea_bank_atomic(brand_folder, bank)
    return "added", entry["seed"][:80]


# ── Perplexity prompt generation ─────────────────────────────────────────


def generate_perplexity_prompts(brand_folder: Path, week: str) -> list[Path]:
    """Write the 3 pillar prompts to brand/_engine/_research/trends/<week>/<pillar>-prompt.md."""
    template_path = SKILL_DIR / "references" / "perplexity-prompt-templates.md"
    if not template_path.exists():
        sys.exit(f"Template file missing: {template_path}")
    template_text = template_path.read_text()

    # Crude split: each `## Template — Pillar N (...)` block ends at the next `## Template`
    blocks = re.split(r"^## Template — Pillar \d+ \(([^)]+)\)\s*\n+```\s*\n", template_text, flags=re.MULTILINE)
    # blocks: [intro, "Pillar 1 name", "prompt body", "Pillar 2 name", "prompt body", ...]

    pillar_to_slug = {
        "Landing-Page Conversion Craft": "lp-craft",
        "Solo Freelance Ops": "solo-ops",
        "Small-Budget Paid Media": "paid-media",
    }

    out_dir = brand_folder / "brand" / "_engine" / "_research" / "trends" / week
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for i in range(1, len(blocks), 2):
        pillar_name = blocks[i].strip()
        slug = pillar_to_slug.get(pillar_name)
        if not slug:
            continue
        body_block = blocks[i + 1]
        # Trim at the closing ``` of this template
        prompt_body = body_block.split("```", 1)[0].strip()
        out = out_dir / f"{slug}-prompt.md"
        out.write_text(f"# {pillar_name} — Trend Research Prompt ({week})\n\n```\n{prompt_body}\n```\n")
        written.append(out)
    return written


# ── Perplexity response ingestion ────────────────────────────────────────


TOPIC_HEADER_RE = re.compile(r"^## Topic\s+\d+[\s—:-]+(.*?)$", re.MULTILINE)


def parse_perplexity_response(text: str, pillar_slug: str) -> list[dict]:
    """Parse a Perplexity response markdown into candidate dicts."""
    sections = TOPIC_HEADER_RE.split(text)
    if len(sections) < 3:
        return []

    candidates = []
    for i in range(1, len(sections), 2):
        topic_name = sections[i].strip()
        body = sections[i + 1]

        # Crude field extraction
        def extract(label: str) -> str:
            m = re.search(rf"\*\*{re.escape(label)}\*\*[:\s]+(.*?)(?=\n\s*-\s*\*\*|\Z)", body, re.DOTALL)
            return m.group(1).strip() if m else ""

        seed = extract("What it is")
        hook = extract("Suggested hook angle for Mayank")
        contrarian = extract("Contrarian take (if any)")
        why = extract("Why it's trending")
        quant = extract("Quantitative insight")
        expert = extract("Top expert post / source")

        # Collect URLs from anywhere in the body
        urls = re.findall(r"https?://[^\s)\]]+", body)
        urls = list(dict.fromkeys(urls))[:3]  # dedupe + cap at 3

        if not seed:
            continue

        # Score: 5 if 3+ URLs, 4 if 1-2 URLs, 3 if pillar-fit but no URLs
        if len(urls) >= 3:
            score = 5
        elif urls:
            score = 4
        else:
            score = 3

        candidates.append({
            "pillar": pillar_slug,
            "seed": seed,
            "hook_candidate": hook,
            "source_urls": urls,
            "tags": [topic_name.lower().replace(" ", "-")],
            "relevance_score": score,
            "manual_review_needed": (score == 3),
            "notes": f"why_trending: {why[:100]} | contrarian: {contrarian[:100]} | quant: {quant[:100]} | expert: {expert[:100]}",
        })
    return candidates


# ── Scan log ─────────────────────────────────────────────────────────────


def append_scan_log(brand_folder: Path, week: str, lines: list[str]) -> Path:
    log_dir = brand_folder / "brand" / "_engine" / "_research" / "trends" / week
    log_dir.mkdir(parents=True, exist_ok=True)
    log = log_dir / "scan-log.md"
    header = f"# Trend Scan — {week}\n\nRun at: {now_ist_iso()}\n\n"
    if not log.exists():
        log.write_text(header)
    with open(log, "a", encoding="utf-8") as f:
        for line in lines:
            f.write(line + "\n")
    return log


# ── CLI ──────────────────────────────────────────────────────────────────


def cmd_prompt(args):
    written = generate_perplexity_prompts(args.brand_folder, args.week)
    for p in written:
        print(f"  ✓ {p}")
    if written:
        # Copy first prompt to clipboard
        first = written[0].read_text()
        try:
            import subprocess
            subprocess.run(["pbcopy"], input=first.encode("utf-8"), check=True, timeout=5)
            print(f"\nFirst prompt copied to clipboard. Paste into Perplexity, then save the response to:")
            print(f"  {written[0].parent}/{written[0].stem.replace('-prompt', '-response')}.md")
        except Exception:
            pass
    print(f"\nTotal: {len(written)} prompt(s) written.")


def cmd_ingest(args):
    candidate = json.loads(args.json)
    candidate.setdefault("pillar", args.pillar)
    status, reason = ingest_one(args.brand_folder, candidate, args.dry_run)
    print(f"{status}: {reason}")
    sys.exit(0 if status in ("added", "dry-run") else 1)


def cmd_dedupe_check(args):
    candidate = json.loads(args.json)
    bank = read_idea_bank(args.brand_folder)
    reason = dedupe_check(candidate, bank)
    if reason:
        print(f"DUP: {reason}")
        sys.exit(1)
    qf = quality_filter(candidate)
    if qf:
        print(f"QUALITY-REJECT: {qf}")
        sys.exit(1)
    print("ok (would be added)")
    sys.exit(0)


def cmd_ingest_perplexity(args):
    response_path = args.response or (
        args.brand_folder / "brand" / "_engine" / "_research" / "trends" / args.week / f"{args.pillar}-response.md"
    )
    if not response_path.exists():
        sys.exit(f"Response file not found: {response_path}")
    text = response_path.read_text()
    candidates = parse_perplexity_response(text, args.pillar)
    if not candidates:
        sys.exit("No topics parsed from response. Check format (expecting '## Topic N — name' headers).")

    log_lines = [f"\n## {PILLAR_SLUGS.get(args.pillar, args.pillar)}", f"- Source: {response_path.name}", f"- Parsed: {len(candidates)} candidates"]
    counts = {"added": 0, "skipped-dup": 0, "skipped-quality": 0}
    for c in candidates:
        status, reason = ingest_one(args.brand_folder, c, args.dry_run)
        counts[status] = counts.get(status, 0) + 1
        line = f"  - [{status}] {c.get('seed', '')[:80]}"
        if status != "added" and status != "dry-run":
            line += f" ({reason})"
        log_lines.append(line)

    log_path = append_scan_log(args.brand_folder, args.week, log_lines)
    print(f"\nResults: {counts}")
    print(f"Log: {log_path}")


def cmd_stats(args):
    bank = read_idea_bank(args.brand_folder)
    trend_entries = [e for e in bank.get("entries", []) if e.get("type") == "trend"]
    by_pillar = {}
    for e in trend_entries:
        slug = e.get("pillar", "unknown")
        by_pillar[slug] = by_pillar.get(slug, 0) + 1
    print(f"Total trend entries: {len(trend_entries)}")
    for slug in sorted(by_pillar.keys()):
        print(f"  {slug}: {by_pillar[slug]}")
    # Last 30d
    cutoff = datetime.now(ist()) - timedelta(days=30)
    recent = 0
    for e in trend_entries:
        captured = e.get("captured_at")
        if not captured:
            continue
        try:
            dt = datetime.fromisoformat(captured)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=ist())
            if dt >= cutoff:
                recent += 1
        except ValueError:
            pass
    print(f"\nLast 30d: {recent}")


def cmd_scan_log(args):
    log = args.brand_folder / "brand" / "_engine" / "_research" / "trends" / args.week / "scan-log.md"
    if not log.exists():
        print(f"No scan log for {args.week}")
        return
    print(log.read_text())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--brand-folder", type=Path, default=DEFAULT_BRAND)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_prompt = sub.add_parser("prompt")
    p_prompt.add_argument("--week", required=True)
    p_prompt.set_defaults(func=cmd_prompt)

    p_ing = sub.add_parser("ingest")
    p_ing.add_argument("--pillar", required=True, choices=list(PILLAR_SLUGS.keys()))
    p_ing.add_argument("--json", required=True, help="Candidate JSON")
    p_ing.add_argument("--dry-run", action="store_true")
    p_ing.set_defaults(func=cmd_ingest)

    p_dc = sub.add_parser("dedupe-check")
    p_dc.add_argument("--json", required=True)
    p_dc.set_defaults(func=cmd_dedupe_check)

    p_pi = sub.add_parser("ingest-perplexity")
    p_pi.add_argument("--pillar", required=True, choices=list(PILLAR_SLUGS.keys()))
    p_pi.add_argument("--week", required=True)
    p_pi.add_argument("--response", type=Path, default=None)
    p_pi.add_argument("--dry-run", action="store_true")
    p_pi.set_defaults(func=cmd_ingest_perplexity)

    p_stat = sub.add_parser("stats")
    p_stat.set_defaults(func=cmd_stats)

    p_log = sub.add_parser("scan-log")
    p_log.add_argument("--week", required=True)
    p_log.set_defaults(func=cmd_scan_log)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
