#!/usr/bin/env python3
"""parse_brief.py — convert Form A / B / C input into concept-board.json.

Forms:
  A — ad-copywriter image-prompts.json (preferred, structured)
  B — free-form concept-board markdown (analyst writes 3-8 concepts)
  C — standalone (Claude in-session asks 3 clarifying questions, builds the markdown)

This script handles A and B parsing + voice-check + auto-attach references + model routing.
Form C requires Claude in-session — this script accepts a generated markdown file as input.

Usage:
    python3 parse_brief.py <input_file> --form A|B --client "<Client>" --project "<Project>" \
        --goal registrations --voice-register religious-grounded \
        [--reference-manifest <path>] --output <concept-board.json>
"""
import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


# Voice rules from shared-context/copywriting-rules.md (kernel)
HYPE_WORDS = [
    "game-changer", "game changer", "revolutionary", "ultimate", "transform your",
    "10x", "skyrocket", "explode", "unlock", "unleash", "supercharge",
    "best ever", "world-class", "cutting-edge", "next-level", "groundbreaking",
    "amazing", "incredible", "mind-blowing",
]
ENGAGEMENT_BAIT = [
    "DM me", "comment below", "like if you", "tag a friend", "share this",
    "follow for more", "tap the link", "swipe up", "smash that",
]
EM_DASH_PATTERN = re.compile(r"[—–]")  # em dash + en dash

# Inferred intent from prompt keywords
INTENT_KEYWORDS = {
    "ad_product_hero":   ["product shot", "product photo", "product close-up", "packshot"],
    "cover_slide":       ["cover slide", "cover image", "title overlay", "headline overlay"],
    "hero_landing":      ["hero image", "landing page hero", "luxury hero", "cinematic hero"],
    "ugc":               ["ugc", "creator-style", "first-person", "selfie", "iphone-shot"],
    "character_consistent": ["same person", "consistent character", "same model", "same talent"],
    "edit_reference":    ["edit this", "modify the", "style transfer", "remix"],
    "wide_banner":       ["banner", "21:9", "leaderboard", "wide hero"],
    "stylized":          ["abstract", "stylized", "illustrated", "artistic", "concept art"],
    "lifestyle":         ["lifestyle", "candid", "in-the-wild", "everyday"],
    "atmospheric":       ["atmospheric", "ambient", "moody", "candlelit", "warm light"],
}

PLACEMENT_TO_ASPECTS = {
    "meta_feed":          ["1:1", "4:5"],
    "instagram_feed":     ["1:1", "4:5"],
    "meta_explore":       ["1:1"],
    "meta_story":         ["9:16"],
    "instagram_story":    ["9:16"],
    "instagram_reel_cover": ["9:16"],
    "meta_marketplace":   ["1:1"],
    "linkedin_feed":      ["1:1"],
    "linkedin_carousel":  ["1:1"],
    "google_display_responsive": ["1:1", "4:5"],
    "landing_page_hero_desktop": ["16:9"],
    "landing_page_hero_mobile":  ["9:16"],
}

# Routing decision tree (mirrors references/model-routing.md)
def route_model(intent: str, tags: list[str], voice_register: str) -> tuple[str, int]:
    """Returns (model_id, expected_credits)."""
    if intent == "ad_product_hero" or "product_shot" in tags:
        return ("marketing_studio_image", 5)
    if intent == "cover_slide":
        if "typography_heavy" in tags:
            return ("gpt_image_2", 6)
        return ("nano_banana_2", 5)
    if intent == "hero_landing" or "luxury" in tags:
        return ("cinematic_studio_2_5", 6)
    if intent == "character_consistent":
        return ("soul_cast", 5)
    if intent == "ugc":
        return ("soul_2", 5)
    if intent == "edit_reference":
        return ("flux_kontext", 5)
    if intent == "stylized":
        return ("grok_image", 4)
    if intent == "wide_banner":
        return ("kling_omni_image", 4)
    return ("nano_banana_flash", 0)  # default unlimited tier


def voice_check(text: str, voice_register: str) -> tuple[str, str]:
    """Returns (status, reason). status = PASS or FAIL."""
    if EM_DASH_PATTERN.search(text):
        return ("FAIL", "contains em dash (banned)")
    text_lower = text.lower()
    for hype in HYPE_WORDS:
        if hype in text_lower:
            return ("FAIL", f"hype word: '{hype}'")
    for bait in ENGAGEMENT_BAIT:
        if bait.lower() in text_lower:
            return ("FAIL", f"engagement bait: '{bait}'")
    if voice_register == "religious-grounded":
        bad = ["seductive", "erotic", "provocative", "sexy"]
        for w in bad:
            if w in text_lower:
                return ("FAIL", f"inappropriate descriptor for religious sector: '{w}'")
    return ("PASS", "")


def infer_intent(prompt: str, creative_direction: str) -> str:
    text = (prompt + " " + creative_direction).lower()
    for intent, keywords in INTENT_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            return intent
    return "lifestyle"


def auto_attach_references(intent: str, ref_manifest: dict | None) -> list[str]:
    if not ref_manifest:
        return []
    attached: list[str] = []
    for img in ref_manifest.get("images", []):
        auto = img["tags"].get("auto_attach_to_concepts_with_intent", [])
        if intent in auto:
            attached.append(img["id"])
    return attached


def parse_form_b_markdown(md_text: str) -> list[dict]:
    """Parse a Form B markdown into a list of concept dicts.
    Expected format:
      ## Concept N: <name>
      Intent: <intent>
      Direction: <one paragraph>
      Placements: meta_feed, instagram_feed
      Tags: prasadam, atmospheric
      [optional] References: ref-id-1, ref-id-2
    """
    concepts: list[dict] = []
    blocks = re.split(r"^##\s+Concept\s+\d+:\s*", md_text, flags=re.MULTILINE)
    for i, blk in enumerate(blocks[1:], start=1):
        lines = blk.strip().split("\n")
        name = lines[0].strip()
        meta: dict[str, str] = {}
        for line in lines[1:]:
            m = re.match(r"^([A-Za-z][A-Za-z]+):\s*(.+)$", line.strip())
            if m:
                meta[m.group(1).lower()] = m.group(2).strip()
        concept = {
            "concept_id": f"{i:02d}-{re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')[:40]}",
            "concept_name": name,
            "intent": meta.get("intent", "lifestyle"),
            "creative_direction": meta.get("direction", ""),
            "intended_placement": [p.strip() for p in meta.get("placements", "meta_feed").split(",") if p.strip()],
            "tags": [t.strip() for t in meta.get("tags", "").split(",") if t.strip()],
            "explicit_references": [r.strip() for r in meta.get("references", "").split(",") if r.strip()],
        }
        concepts.append(concept)
    return concepts


def parse_form_a_json(input_path: Path) -> list[dict]:
    """Parse ad-copywriter image-prompts.json (the new structured output)."""
    data = json.loads(input_path.read_text())
    concepts: list[dict] = []
    items = data.get("image_prompts", []) if isinstance(data, dict) else data
    for i, item in enumerate(items, start=1):
        cid = item.get("creative_id") or item.get("id") or f"{i:02d}"
        concepts.append({
            "concept_id": cid,
            "concept_name": item.get("concept_name", item.get("name", f"Concept {i}")),
            "intent": item.get("intent", infer_intent(item.get("prompt", ""), item.get("creative_direction", ""))),
            "creative_direction": item.get("creative_direction", ""),
            "intended_placement": item.get("intended_placement") or [item.get("placement", "meta_feed")],
            "tags": item.get("tags") or [],
            "prompt_override": item.get("prompt"),
            "negative_prompt": item.get("negative_prompt", ""),
            "explicit_references": item.get("reference_image_ids") or [],
            "requires_reference_image": item.get("requires_reference_image", False),
            "reference_subject": item.get("reference_subject", ""),
            "force_model": item.get("model_preference"),
            "force_aspects": item.get("aspect_ratios"),
        })
    return concepts


def build_variations(concept: dict, ref_manifest: dict | None, voice_register: str) -> list[dict]:
    intent = concept["intent"]
    placements = concept["intended_placement"]
    aspects: list[str] = []
    if concept.get("force_aspects"):
        aspects = concept["force_aspects"]
    else:
        for p in placements:
            for a in PLACEMENT_TO_ASPECTS.get(p, ["1:1"]):
                if a not in aspects:
                    aspects.append(a)

    explicit_refs = concept.get("explicit_references") or []
    auto_refs = auto_attach_references(intent, ref_manifest) if not explicit_refs else []
    refs = list(dict.fromkeys(explicit_refs + auto_refs))

    forced_model = concept.get("force_model")
    base_prompt = concept.get("prompt_override") or concept.get("creative_direction", "")
    negative_prompt = concept.get("negative_prompt", "")

    variations: list[dict] = []
    for aspect in aspects:
        # v1: default tier (free)
        if forced_model:
            model, credits = forced_model, 0
        else:
            model, credits = route_model(intent, concept.get("tags", []), voice_register)
            # Variation 1 always tries default tier first if not forced
            if intent not in ("ad_product_hero", "cover_slide", "hero_landing", "edit_reference", "character_consistent"):
                model, credits = "nano_banana_flash", 0

        vc, reason = voice_check(base_prompt, voice_register)
        variations.append({
            "variation_id": f"v1-{aspect.replace(':', 'x')}",
            "model_choice": model,
            "aspect_ratio": aspect,
            "resolution": "2k",
            "prompt": base_prompt,
            "negative_prompt": negative_prompt,
            "reference_image_ids": refs,
            "reference_role": "style" if refs else "none",
            "expected_credits": credits,
            "voice_check": vc,
            "voice_check_reason": reason,
        })

        # v2: composition variant (also default tier — free)
        composition_swap = " Composition note: try a different camera angle (top-down vs side, wide vs close)."
        v2_prompt = base_prompt + composition_swap
        vc2, reason2 = voice_check(v2_prompt, voice_register)
        variations.append({
            "variation_id": f"v2-{aspect.replace(':', 'x')}",
            "model_choice": "nano_banana_flash",
            "aspect_ratio": aspect,
            "resolution": "2k",
            "prompt": v2_prompt,
            "negative_prompt": negative_prompt,
            "reference_image_ids": refs,
            "reference_role": "style" if refs else "none",
            "expected_credits": 0,
            "voice_check": vc2,
            "voice_check_reason": reason2,
        })

        # v3: premium tier (paid model for hero / cover / typography)
        premium_model, premium_cost = route_model(intent, concept.get("tags", []) + ["typography_heavy"], voice_register)
        if premium_model != "nano_banana_flash":
            variations.append({
                "variation_id": f"v3-premium-{aspect.replace(':', 'x')}",
                "model_choice": premium_model,
                "aspect_ratio": aspect,
                "resolution": "2k",
                "prompt": base_prompt,
                "negative_prompt": negative_prompt,
                "reference_image_ids": refs,
                "reference_role": "style" if refs else "none",
                "expected_credits": premium_cost,
                "voice_check": vc,
                "voice_check_reason": reason,
            })

    return variations


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("input_file", help="image-prompts.json (Form A) OR concept-board.md (Form B)")
    ap.add_argument("--form", required=True, choices=["A", "B"])
    ap.add_argument("--client", required=True)
    ap.add_argument("--project", required=True)
    ap.add_argument("--goal", default="registrations")
    ap.add_argument("--voice-register", default="grounded-default")
    ap.add_argument("--landing-url", default="")
    ap.add_argument("--reference-manifest", help="Path to reference-manifest.json")
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    inp = Path(args.input_file)
    if not inp.exists():
        print(f"x input not found: {inp}", file=sys.stderr)
        return 1

    if args.form == "A":
        concepts_in = parse_form_a_json(inp)
    else:
        concepts_in = parse_form_b_markdown(inp.read_text())

    ref_manifest = None
    if args.reference_manifest:
        ref_path = Path(args.reference_manifest)
        if ref_path.exists():
            ref_manifest = json.loads(ref_path.read_text())

    # Infer intent if missing
    for c in concepts_in:
        if c["intent"] == "lifestyle":
            c["intent"] = infer_intent(c.get("prompt_override", ""), c.get("creative_direction", ""))

    # Build full concepts with variations
    full_concepts: list[dict] = []
    total_gens = 0
    free_count = 0
    paid_count = 0
    total_credits = 0
    for c in concepts_in:
        variations = build_variations(c, ref_manifest, args.voice_register)
        for v in variations:
            total_gens += 1
            if v["expected_credits"] == 0:
                free_count += 1
            else:
                paid_count += 1
                total_credits += v["expected_credits"]
        full_concepts.append({
            "concept_id": c["concept_id"],
            "concept_name": c["concept_name"],
            "intent": c["intent"],
            "creative_direction": c["creative_direction"],
            "intended_placement": c["intended_placement"],
            "tags": c["tags"],
            "variations": variations,
        })

    cb = {
        "campaign_id": f"{args.client.replace(' ', '-')[:20]}-{datetime.now().strftime('%Y%m%d')}",
        "client": args.client,
        "project": args.project,
        "goal": args.goal,
        "landing_url": args.landing_url,
        "voice_register": args.voice_register,
        "concepts": full_concepts,
        "totals": {
            "total_generations": total_gens,
            "free_generations": free_count,
            "paid_generations": paid_count,
            "total_credits_estimate": total_credits,
        },
        "form": args.form,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(cb, indent=2))

    voice_fail = sum(1 for c in full_concepts for v in c["variations"] if v["voice_check"] == "FAIL")

    print(f"\nConcept board: {out}")
    print(f"  Concepts:     {len(full_concepts)}")
    print(f"  Variations:   {total_gens}  ({free_count} free + {paid_count} paid)")
    print(f"  Est credits:  ~{total_credits}")
    if voice_fail:
        print(f"!  Voice-check failures: {voice_fail} (skipped at queue time)")
    print(f"\n  Next: python3 plan_generations.py {out.parent}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
