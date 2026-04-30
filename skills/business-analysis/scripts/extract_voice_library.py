#!/usr/bin/env python3
"""
Voice Library Extraction Utility.

Step 7 of business-analysis. Produces {client}/_engine/wiki/voice-library.json.

Two modes (auto-detected unless forced):
  MODE_A_ESTABLISHED — extract patterns from past creative copy (Windsor.ai pull,
                       Meta Ad Library scrape, manual paste, OR reference-image OCR).
  MODE_B_BOOTSTRAP   — three-tier bootstrap: sector_seed + founder_voice + competitor_anti.

Spec: ~/.claude/shared-context/voice-library-spec.md
Protocol: business-analysis/references/voice-library-extraction.md

Usage:
  extract_voice_library.py --detect <client_folder>
      → prints "MODE_A_ESTABLISHED" or "MODE_B_BOOTSTRAP" + reasoning

  extract_voice_library.py --bootstrap <client_folder> --sector <sector>
                           [--founder-q1 "..." --founder-q2 "..." --founder-q3 "..."]
                           [--competitors "name1,name2,name3"]
      → loads sector seed, captures founder voice, scans competitors → writes voice-library.json

  extract_voice_library.py --paste <client_folder>
      → opens stdin paste mode for analyst-supplied creative copy → induct patterns

  extract_voice_library.py --windsor <client_folder> --account-id <id> --top-n 3
      → (placeholder for Windsor.ai pull integration; currently emits guidance)

Outputs voice-library.json. Validates against schema before writing. Refuses to overwrite
without --force flag if existing file has more populated fields than the new one (prevents
accidental downgrade).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SECTOR_SEEDS_DIR = SCRIPT_DIR.parent / "references" / "voice-library-sector-seeds"
SECTOR_LENSES_DIR = SCRIPT_DIR.parent / "references" / "sector-lenses"


def detect_mode(client_folder: Path) -> tuple[str, list[str]]:
    """Return (mode, reasoning_lines). Mode is MODE_A_ESTABLISHED or MODE_B_BOOTSTRAP."""
    reasons = []
    has_windsor = False  # placeholder — would check ~/.claude/secrets/windsor.json or env
    has_ads_history = False
    has_reference_images = False

    # Reference images?
    ref_manifest = client_folder / "_engine" / "references" / "images" / "manifest.json"
    if ref_manifest.exists():
        has_reference_images = True
        reasons.append(f"Reference image manifest found at {ref_manifest}")
    else:
        # Multi-program — check parent
        parent_ref = client_folder.parent / "_engine" / "references" / "images" / "manifest.json"
        if parent_ref.exists():
            has_reference_images = True
            reasons.append(f"Reference image manifest found (multi-program parent) at {parent_ref}")

    # Past campaign data — check for Meta pixel + GBP review history etc.
    digital_presence = client_folder / "_engine" / "wiki" / "digital-presence.md"
    if not digital_presence.exists():
        digital_presence = client_folder.parent / "_engine" / "wiki" / "digital-presence.md"
    if digital_presence.exists():
        text = digital_presence.read_text()
        if "Meta Ad Library" in text and "active" in text.lower():
            has_ads_history = True
            reasons.append("digital-presence.md indicates active Meta ad history")

    if has_windsor or has_ads_history or has_reference_images:
        return "MODE_A_ESTABLISHED", reasons + [
            "→ Run extraction from past creatives (Windsor.ai → Ad Library → manual paste → OCR fallback)"
        ]
    return "MODE_B_BOOTSTRAP", reasons + [
        "No Windsor.ai integration, no active Meta ad history, no reference-image manifest",
        "→ Run three-tier bootstrap: sector_seed + founder_voice_intake + competitor_anti_pattern",
    ]


def auto_create_sector_seed(sector: str) -> dict:
    """Auto-generate a sector seed when one doesn't exist yet.

    Triggered the first time business-analysis runs for a sector that has a sector-lens
    markdown file but no voice-library-sector-seed JSON. Builds the seed from:
      - _default.json (universal floor: patterns, CTA pairs, voice rules)
      - sector-lens/<sector>.md reference link (for analysts who want to deepen later)
      - flag `auto_generated: true` so the analyst knows it came from the universal floor

    Saves the new seed to voice-library-sector-seeds/<sector>.json so the NEXT client
    of the same sector picks it up directly. The seed will mature as performance data
    accumulates across multiple clients in that sector.
    """
    default_path = SECTOR_SEEDS_DIR / "_default.json"
    if not default_path.exists():
        sys.stderr.write(f"❌ _default.json missing — cannot auto-create sector seed for '{sector}'\n")
        sys.exit(1)
    with default_path.open() as f:
        seed = json.load(f)

    seed["sector"] = sector
    sector_lens_path = SECTOR_LENSES_DIR / f"{sector}.md"
    if sector_lens_path.exists():
        seed["sector_lens_ref"] = f"business-analysis/references/sector-lenses/{sector}.md"
    else:
        seed["sector_lens_ref"] = None
        sys.stderr.write(
            f"ℹ No sector lens markdown at {sector_lens_path}. Seed built from universal floor only.\n"
        )

    seed["auto_generated"] = True
    seed["auto_generated_at"] = datetime.now(timezone.utc).date().isoformat()
    seed["auto_generated_from"] = "_default.json + sector-lens reference"
    seed["maturity_note"] = (
        f"Auto-created starter pack for the '{sector}' sector. Inherits universal floor patterns "
        "and voice rules. Will mature as: (a) founder voice gets captured for each new client of this "
        "sector during business-analysis Step 5 intake, (b) competitor anti-patterns get scanned in "
        "Step 8 Tier 3, (c) post-launch-optimization promotes proven patterns from real ad performance. "
        "After 2-3 clients in this sector ship campaigns, refine this seed manually with the patterns "
        "that consistently win across clients."
    )

    out_path = SECTOR_SEEDS_DIR / f"{sector}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w") as f:
        json.dump(seed, f, indent=2, ensure_ascii=False)
    sys.stderr.write(f"✓ Auto-created sector seed at {out_path}\n")
    return seed


def load_sector_seed(sector: str) -> dict:
    """Load the matching sector seed JSON, auto-creating one if it doesn't exist yet."""
    candidate = SECTOR_SEEDS_DIR / f"{sector}.json"
    if candidate.exists():
        with candidate.open() as f:
            return json.load(f)

    # Auto-create path: confirm the sector is recognised (has a sector-lens markdown)
    # OR fall back gracefully to default if the sector name is unfamiliar.
    sector_lens_path = SECTOR_LENSES_DIR / f"{sector}.md"
    if sector_lens_path.exists():
        sys.stderr.write(
            f"ℹ No sector seed for '{sector}' yet — auto-creating from sector lens.\n"
        )
        return auto_create_sector_seed(sector)

    # Unknown sector — fall back to _default.json without auto-creating a stale seed
    available_seeds = sorted(p.stem for p in SECTOR_SEEDS_DIR.glob('*.json') if not p.stem.startswith('_'))
    available_lenses = sorted(p.stem for p in SECTOR_LENSES_DIR.glob('*.md'))
    sys.stderr.write(
        f"⚠ Unknown sector '{sector}'. No seed AND no sector-lens markdown found.\n"
        f"   Existing seeds: {available_seeds}\n"
        f"   Existing lenses: {available_lenses}\n"
        f"   Falling back to _default.json (no auto-creation — sector name may be misspelled).\n"
    )
    default_path = SECTOR_SEEDS_DIR / "_default.json"
    if not default_path.exists():
        sys.stderr.write(f"❌ _default.json missing — sector seeds directory broken at {SECTOR_SEEDS_DIR}\n")
        sys.exit(1)
    with default_path.open() as f:
        return json.load(f)


def parse_founder_q1(answer: str) -> dict:
    """Parse 'service description' answer into a custom founder_voice headline pattern."""
    sentences = [s.strip() for s in answer.replace("!", ".").replace("?", ".").split(".") if s.strip()]
    examples = [s for s in sentences if 3 <= len(s.split()) <= 14][:2]
    return {
        "id": "founder_voice_natural",
        "name": "Founder voice — natural service description",
        "structure": "<derived from analyst's two-sentence service description>",
        "examples": examples or [answer],
        "max_words": max(len(s.split()) for s in (examples or [answer])) + 2,
        "tone_tags": ["founder-natural", "conversational"],
        "best_for_audience_tier": ["all"],
        "source": "founder_voice (Tier 2 bootstrap, business-analysis Step 5 Q1)"
    }


def parse_founder_q2(answer: str) -> dict:
    """Parse 'objection + reassurance' answer into objection_reassurance pattern example."""
    return {
        "id": "objection_reassurance",
        "name": "Objection question + reassurance (founder-supplied)",
        "structure": "{Negation/objection}? {Reassurance}.",
        "examples": [answer],
        "max_words": min(15, len(answer.split())),
        "tone_tags": ["welcoming", "newcomer-safe"],
        "best_for_audience_tier": ["cold"],
        "source": "founder_voice (Tier 2 bootstrap, business-analysis Step 5 Q2)"
    }


def parse_founder_q3(answer: str) -> dict:
    """Parse 'conversion-moment feeling' answer into emotional register tags."""
    keywords = answer.lower()
    tags = []
    if any(k in keywords for k in ["calm", "peaceful", "settled", "relieved"]): tags.append("calm")
    if any(k in keywords for k in ["excited", "energ", "pumped", "fired up"]): tags.append("energetic")
    if any(k in keywords for k in ["proud", "confident", "trusted"]): tags.append("confident")
    if any(k in keywords for k in ["welcomed", "belonging", "home", "warm"]): tags.append("welcoming")
    if any(k in keywords for k in ["empowered", "in control", "capable"]): tags.append("empowered")
    return {"emotional_register_tags": tags or ["unspecified"], "raw_answer": answer}


def merge_founder_voice(seed: dict, q1: str, q2: str, q3: str) -> dict:
    """Stack Tier 2 founder voice on top of Tier 1 sector seed."""
    library = json.loads(json.dumps(seed))  # deep copy
    library["founder_voice_samples"] = {
        "service_description": q1,
        "top_objection_and_reassurance": q2,
        "conversion_moment_feeling": q3,
    }
    library["headline_patterns"].insert(0, parse_founder_q1(q1))
    # Replace or augment objection_reassurance with founder-supplied
    found = False
    for i, p in enumerate(library["headline_patterns"]):
        if p["id"] == "objection_reassurance":
            p["examples"] = [q2] + (p.get("examples") or [])
            p["source"] = (p.get("source") or "sector_seed") + " + founder_voice (Q2)"
            found = True
            break
    if not found:
        library["headline_patterns"].append(parse_founder_q2(q2))
    library["emotional_register_from_founder"] = parse_founder_q3(q3)
    return library


def load_competitor_anti_pattern(competitors: list[str]) -> dict:
    """Tier 3 — store competitor names; actual headline pulling deferred to Chrome MCP / WebFetch by caller."""
    return {
        "usage": "differentiate_from",
        "competitor_names": competitors,
        "samples_note": (
            "Competitor headline samples should be added by analyst/Chrome MCP after first onboarding pass. "
            "Save examples here as a 'don't sound like these' reference, NOT for imitation."
        ),
        "differentiation_rule": (
            "Voice patterns in headline_patterns above are deliberately different from these. "
            "If a generated headline could plausibly appear on any of these competitors without changes, "
            "it has failed differentiation."
        ),
    }


def quality_check(library: dict) -> tuple[bool, list[str]]:
    """Validate voice-library.json against the spec quality bar. Return (ok, issues)."""
    issues = []
    if len(library.get("headline_patterns", [])) < 3:
        issues.append("headline_patterns has <3 entries (spec requires ≥3)")
    for i, p in enumerate(library.get("headline_patterns", [])):
        if not p.get("examples"):
            issues.append(f"headline_patterns[{i}] '{p.get('id')}' has no examples")
    tlt = library.get("trust_line_template", {})
    if not tlt.get("format"):
        issues.append("trust_line_template.format missing")
    if len(tlt.get("examples", [])) < 2:
        issues.append("trust_line_template.examples has <2 entries (spec requires ≥2)")
    if len(library.get("cta_verb_noun_pairs", [])) < 2:
        issues.append("cta_verb_noun_pairs has <2 entries (spec requires ≥2)")
    if not library.get("voice_rules", {}).get("forbidden_phrases"):
        issues.append("voice_rules.forbidden_phrases is empty")
    if not library.get("campaign_type_anchor_pattern"):
        issues.append("campaign_type_anchor_pattern not set for any campaign type")
    return (not issues), issues


def write_library(library: dict, output_path: Path, force: bool = False) -> None:
    if output_path.exists() and not force:
        # Don't accidentally downgrade
        with output_path.open() as f:
            existing = json.load(f)
        existing_count = (
            len(existing.get("headline_patterns", []))
            + len(existing.get("cta_verb_noun_pairs", []))
            + (1 if existing.get("founder_voice_samples") else 0)
        )
        new_count = (
            len(library.get("headline_patterns", []))
            + len(library.get("cta_verb_noun_pairs", []))
            + (1 if library.get("founder_voice_samples") else 0)
        )
        if existing_count > new_count:
            sys.stderr.write(
                f"⚠ Existing voice-library.json appears more populated ({existing_count} signals) "
                f"than the new one ({new_count}). Refusing overwrite. Use --force to override.\n"
            )
            sys.exit(1)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w") as f:
        json.dump(library, f, indent=2, ensure_ascii=False)
    print(f"✓ Wrote {output_path}")


def detect_client_root_for_voice_library(client_folder: Path) -> Path:
    """Decide where voice-library.json should live — single-program (program folder)
    or multi-program (client root)."""
    config_program = client_folder / "_engine" / "wiki-config.json"
    config_root = client_folder.parent / "_engine" / "wiki-config.json"
    if config_root.exists():
        try:
            with config_root.open() as f:
                cfg = json.load(f)
            if cfg.get("type") == "multi-program" or cfg.get("scope") == "shared":
                return client_folder.parent / "_engine" / "wiki" / "voice-library.json"
        except (json.JSONDecodeError, IOError):
            pass
    return client_folder / "_engine" / "wiki" / "voice-library.json"


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--detect", help="Detect mode for given client folder")
    parser.add_argument("--bootstrap", help="Run BOOTSTRAP for given client folder")
    parser.add_argument("--paste", help="MODE_A paste mode for given client folder")
    parser.add_argument("--windsor", help="MODE_A Windsor.ai pull for given client folder (placeholder)")
    parser.add_argument("--sector", help="Sector key for sector_seed lookup (BOOTSTRAP only)")
    parser.add_argument("--founder-q1", help="Founder service-description answer (BOOTSTRAP)")
    parser.add_argument("--founder-q2", help="Founder objection+reassurance answer (BOOTSTRAP)")
    parser.add_argument("--founder-q3", help="Founder conversion-moment feeling answer (BOOTSTRAP)")
    parser.add_argument("--competitors", help="Comma-separated competitor names (BOOTSTRAP)")
    parser.add_argument("--client-name", help="Client name to populate in the output (BOOTSTRAP)")
    parser.add_argument("--force", action="store_true", help="Overwrite existing voice-library.json even if richer")
    args = parser.parse_args()

    if args.detect:
        client = Path(args.detect).expanduser().resolve()
        mode, reasons = detect_mode(client)
        print(mode)
        for r in reasons:
            print(f"  · {r}")
        return

    if args.bootstrap:
        client = Path(args.bootstrap).expanduser().resolve()
        if not args.sector:
            sys.stderr.write("❌ --sector required for --bootstrap\n")
            sys.exit(1)
        seed = load_sector_seed(args.sector)
        if all([args.founder_q1, args.founder_q2, args.founder_q3]):
            library = merge_founder_voice(seed, args.founder_q1, args.founder_q2, args.founder_q3)
        else:
            sys.stderr.write(
                "⚠ Founder Q1/Q2/Q3 not all provided — Tier 2 (founder voice) skipped.\n"
                "   Library will be Tier-1-only (sector seed). Re-run with founder Qs to enrich.\n"
            )
            library = json.loads(json.dumps(seed))
            library["founder_voice_samples"] = None
        if args.competitors:
            comp_list = [c.strip() for c in args.competitors.split(",") if c.strip()]
            library["competitor_voice_reference"] = load_competitor_anti_pattern(comp_list)
        library["client"] = args.client_name or client.name
        library["bootstrapping"] = True
        library["scope"] = "program-specific"
        library["extracted_from"] = [
            {
                "source": "BOOTSTRAP — sector_seed + founder_voice_intake"
                          + (" + competitor_anti_pattern" if args.competitors else ""),
                "performance": "n/a (bootstrap — no live campaign data yet)",
                "extraction_date": datetime.now(timezone.utc).date().isoformat(),
                "method": "bootstrap_three_tier",
            }
        ]
        library["refresh_trigger"] = {
            "next_review_date": "auto — re-evaluate after 50+ leads OR 30 days continuous spend OR ≥500 link clicks",
            "auto_review_conditions": [
                "First campaign hits 50+ leads",
                "First campaign reaches ≥500 link clicks",
                "30 days continuous spend"
            ]
        }
        ok, issues = quality_check(library)
        if not ok:
            sys.stderr.write("⚠ Quality bar issues:\n")
            for i in issues:
                sys.stderr.write(f"   · {i}\n")
            sys.stderr.write("   → Review the seed; consider adding founder Qs to enrich.\n")
        out = detect_client_root_for_voice_library(client)
        write_library(library, out, force=args.force)
        return

    if args.paste:
        sys.stderr.write(
            "Paste mode: feed creative copy on stdin in the format documented in\n"
            "business-analysis/references/voice-library-extraction.md §3.\n"
            "Pattern induction is heuristic; analyst should review the output.\n"
            "(Implementation: parse stdin → induct patterns → emit voice-library.json.)\n"
            "TODO v1.1 — implement paste-mode parser.\n"
        )
        sys.exit(2)

    if args.windsor:
        sys.stderr.write(
            "Windsor.ai mode: requires Windsor MCP integration.\n"
            "TODO v1.1 — wire to mcp__7b028e43-*__get_data with linkedin_organic / facebook_organic / meta_ads connectors.\n"
            "Until then: pull top-3 ads manually via Windsor UI, then run with --paste.\n"
        )
        sys.exit(2)

    parser.print_help()


if __name__ == "__main__":
    main()
