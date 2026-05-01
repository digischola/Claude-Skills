#!/usr/bin/env python3
"""render_image_prompts_json.py — emit image-prompts.json sibling from image-prompts.md.

Used by ai-image-generator (client-track) as the structured input. Parses the
markdown blocks of `_engine/working/image-prompts.md` and writes a JSON file
with one entry per creative_id.

Markdown contract: each prompt block starts with a heading like
`### CARD-1` or `### WLF-AD-01` and contains:
  - Concept name on the next line (or in body)
  - JSON dual-format block fenced with ```json
  - requires_reference_image: true|false metadata line
  - reference_subject: ... metadata line
  - aspect_ratio: ... metadata line
  - intended_placement: ... metadata line

Usage:
    python3 render_image_prompts_json.py "<program-folder>"
"""
import argparse
import json
import re
import sys
from pathlib import Path


HEADING_RE = re.compile(r"^###\s+([A-Z][A-Z0-9-]+)\s*(.*)$", re.MULTILINE)
META_RE = re.compile(r"^([a-z_][a-z0-9_]*):\s*(.+)$", re.MULTILINE)


def parse_md_block(block: str, creative_id: str, leading: str) -> dict:
    """Extract structured fields from one prompt block."""
    entry: dict = {
        "creative_id": creative_id,
        "concept_name": leading.strip() or creative_id,
        "intent": "lifestyle",
        "creative_direction": "",
        "intended_placement": ["meta_feed"],
        "tags": [],
        "prompt": "",
        "negative_prompt": "",
        "aspect_ratios": ["1:1"],
        "requires_reference_image": False,
        "reference_subject": "",
        "reference_image_ids": [],
        "model_preference": None,
    }

    for m in META_RE.finditer(block):
        k = m.group(1)
        v = m.group(2).strip().strip("\"',")
        if k == "requires_reference_image":
            entry["requires_reference_image"] = v.lower() in {"true", "yes", "1"}
        elif k == "reference_subject":
            entry["reference_subject"] = v
        elif k == "aspect_ratio":
            entry["aspect_ratios"] = [s.strip() for s in v.split(",") if s.strip()]
        elif k == "aspect_ratios":
            entry["aspect_ratios"] = [s.strip() for s in v.split(",") if s.strip()]
        elif k == "intended_placement":
            entry["intended_placement"] = [s.strip() for s in v.split(",") if s.strip()]
        elif k == "intent":
            entry["intent"] = v
        elif k == "tags":
            entry["tags"] = [s.strip() for s in v.split(",") if s.strip()]
        elif k == "negative_prompt":
            entry["negative_prompt"] = v
        elif k == "model_preference":
            entry["model_preference"] = v if v.lower() != "none" else None

    # Pull spec-prose prompt — everything between heading and the first fenced block,
    # OR the JSON block content if no spec-prose found
    json_match = re.search(r"```json\s*\n(.*?)\n```", block, re.DOTALL)
    if json_match:
        try:
            json_data = json.loads(json_match.group(1))
            if isinstance(json_data, dict):
                entry["prompt"] = json.dumps(json_data, indent=2)
                if not entry["creative_direction"]:
                    entry["creative_direction"] = json_data.get("subject", "") or json_data.get("composition", "")
        except json.JSONDecodeError:
            pass

    # If still no prompt, take prose body after first heading line
    if not entry["prompt"]:
        body_lines = [l for l in block.split("\n") if l.strip() and not META_RE.match(l)]
        entry["prompt"] = "\n".join(body_lines).strip()

    if not entry["creative_direction"]:
        # Use first non-meta sentence
        first_para = next((p for p in block.split("\n\n") if not p.strip().startswith("```") and not META_RE.match(p.strip().split("\n")[0])), "")
        entry["creative_direction"] = first_para.strip()[:500]

    return entry


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("program_folder", help="Path to client/program folder")
    ap.add_argument("--source", help="Override path to image-prompts.md (default: <program>/_engine/working/image-prompts.md)")
    ap.add_argument("--output", help="Override path to image-prompts.json (default: same dir as source)")
    args = ap.parse_args()

    program = Path(args.program_folder)
    src = Path(args.source) if args.source else (program / "_engine" / "working" / "image-prompts.md")
    out = Path(args.output) if args.output else src.parent / "image-prompts.json"

    if not src.exists():
        print(f"x source not found: {src}", file=sys.stderr)
        return 1

    md = src.read_text()
    headings = list(HEADING_RE.finditer(md))
    if not headings:
        print(f"x no creative_id headings found in {src}. Expected `### <CREATIVE-ID>`", file=sys.stderr)
        return 1

    entries: list[dict] = []
    for i, m in enumerate(headings):
        creative_id = m.group(1)
        leading = m.group(2)
        start = m.end()
        end = headings[i + 1].start() if i + 1 < len(headings) else len(md)
        block = md[start:end]
        entries.append(parse_md_block(block, creative_id, leading))

    payload = {
        "client": program.parent.name if program.parent != program else "",
        "project": program.name,
        "image_prompts": entries,
    }
    out.write_text(json.dumps(payload, indent=2))
    print(f"  Wrote {len(entries)} image prompts: {out}")
    print(f"  Next: ai-image-generator can consume via parse_brief.py --form A {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
