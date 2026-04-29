#!/usr/bin/env python3
"""
Mine Claude Code transcript JSONLs for voice samples, work-history signals,
and client/project mentions. Output feeds personal-brand-dna extraction.

Usage:
  python3 mine_transcripts.py
  python3 mine_transcripts.py --transcripts-dir /custom/path --output-dir /custom/out

Outputs to {output-dir}:
  voice-samples.txt      — up to 100 representative user utterances
  work-topics.json       — client/project mention counts + session metadata
  session-summaries.json — per-session opening snippets (context hints)
"""

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

DEFAULT_TRANSCRIPTS = Path.home() / ".claude/projects/-Users-digischola-Desktop"
DEFAULT_OUTPUT = Path("/Users/digischola/Desktop/Digischola/brand/_engine/_mining")

MIN_LEN = 40
MAX_LEN = 700
SAMPLES_PER_SESSION = 6
MAX_TOTAL_SAMPLES = 120

# Seed list of known work entities from analyst-profile + memory.
# The miner counts mentions; missing entities still show up via topic keywords.
KNOWN_ENTITIES = [
    "Salt Air", "Samir", "ISKM", "Thrive", "CrownTECH",
    "Digischola", "Nikhil", "Wabo",
    "MarketingOS", "market research", "business analysis",
    "ad copy", "landing page", "campaign", "meta ads", "google ads",
]

TOPIC_KEYWORDS = [
    "skill", "wiki", "pillar", "brand", "funnel", "hook", "carousel",
    "reel", "case study", "automation", "dashboard", "workflow",
    "prompt", "agent", "research", "strategy", "creative", "offer",
    "lead", "conversion", "roas", "cpa", "client",
]


def extract_text(message):
    """Pull a flat text string out of a user-turn message object."""
    content = message.get("content") if isinstance(message, dict) else None
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
        return " ".join(parts).strip()
    return ""


def is_voice_carrying(text):
    """Filter out tool-result pastes and synthetic system echoes."""
    if not text:
        return False
    if text.startswith("{") and text.endswith("}"):
        return False
    if "<system-reminder>" in text:
        return False
    if text.startswith("[Request interrupted"):
        return False
    if re.match(r"^tool_use_id|^tool_result", text):
        return False
    return True


def extract_user_turns(jsonl_path):
    with open(jsonl_path, "r", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if obj.get("type") != "user":
                continue
            text = extract_text(obj.get("message", {}))
            if not is_voice_carrying(text):
                continue
            if len(text) < MIN_LEN or len(text) > MAX_LEN:
                continue
            yield {
                "session": jsonl_path.stem,
                "timestamp": obj.get("timestamp", ""),
                "text": text,
            }


def sample_session(turns):
    """Take representative turns: openings, middle, close — captures intent + feedback voice."""
    if len(turns) <= SAMPLES_PER_SESSION:
        return list(turns)
    mid = len(turns) // 2
    return turns[:2] + [turns[mid - 1], turns[mid], turns[mid + 1]] + turns[-2:]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--transcripts-dir", type=Path, default=DEFAULT_TRANSCRIPTS)
    ap.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = ap.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)

    all_samples = []
    entity_counts = Counter()
    topic_counts = Counter()
    per_session = defaultdict(list)
    session_token_total = 0

    jsonls = sorted(args.transcripts_dir.glob("*.jsonl"))
    print(f"Scanning {len(jsonls)} transcript file(s)...")

    for path in jsonls:
        try:
            turns = list(extract_user_turns(path))
        except OSError as exc:
            print(f"  skip {path.name}: {exc}")
            continue
        if not turns:
            continue

        all_text = " ".join(t["text"] for t in turns).lower()
        for ent in KNOWN_ENTITIES:
            if ent.lower() in all_text:
                entity_counts[ent] += 1
        for kw in TOPIC_KEYWORDS:
            topic_counts[kw] += all_text.count(kw)

        sampled = sample_session(turns)
        all_samples.extend(sampled)
        per_session[path.stem] = {
            "turns": len(turns),
            "first_snippet": turns[0]["text"][:200],
            "last_snippet": turns[-1]["text"][:200],
        }
        session_token_total += len(turns)

    all_samples = all_samples[:MAX_TOTAL_SAMPLES]

    voice_path = args.output_dir / "voice-samples.txt"
    with open(voice_path, "w") as f:
        f.write(f"# Voice Samples — mined from {len(jsonls)} transcript(s)\n")
        f.write(f"# {len(all_samples)} representative user utterances\n\n")
        for i, s in enumerate(all_samples, 1):
            f.write(f"--- [{i}] session={s['session'][:8]} ts={s['timestamp']} ---\n")
            f.write(s["text"] + "\n\n")

    topics_path = args.output_dir / "work-topics.json"
    with open(topics_path, "w") as f:
        json.dump(
            {
                "transcripts_scanned": len(jsonls),
                "sessions_with_content": len(per_session),
                "total_user_turns": session_token_total,
                "samples_written": len(all_samples),
                "entity_mentions": dict(entity_counts.most_common()),
                "topic_keyword_frequency": dict(topic_counts.most_common()),
            },
            f,
            indent=2,
        )

    summaries_path = args.output_dir / "session-summaries.json"
    with open(summaries_path, "w") as f:
        json.dump(per_session, f, indent=2)

    print(f"\nDone.")
    print(f"  voice samples     : {voice_path}")
    print(f"  work topics       : {topics_path}")
    print(f"  session summaries : {summaries_path}")
    print(f"\nTop entities : {entity_counts.most_common(10)}")
    print(f"Top topics   : {topic_counts.most_common(10)}")


if __name__ == "__main__":
    main()
