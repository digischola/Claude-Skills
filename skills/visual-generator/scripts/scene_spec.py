#!/usr/bin/env python3
"""
scene_spec.py — Normalized scene spec consumed by BOTH Remotion and Hyperframes
render functions. Single scene format → engine-routing decides which engine
renders it.

Consumers:
  - generate_reel.py::render_scene_remotion()    (exists)
  - generate_reel.py::render_scene_hyperframes() (new v7.4)

The spec is intentionally engine-neutral. It carries WHAT the scene shows, not
HOW the engine draws it. Palette / fonts / easing / timing come from
design-tokens.json so both engines render with aligned visual tokens.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

# ── Scene types → engine routing (rule-based, v7.4) ───────────────────────
# Rule 1: UI-mockup teardown scenes → Remotion (uses v7.3 React primitives)
# Rule 2: Social-platform overlay scenes → Hyperframes (uses catalog blocks)
# Rule 3: Brand moments (outro/CTA) → Remotion (uses face-01 iOS-icon treatment)
SCENE_ROUTING = {
    # ── Remotion (v7.3 primitives: BrowserFrame, LandingPageMockup, FormReducer, etc.)
    "hook":          "remotion",
    "problem_beat":  "remotion",
    "insight_beat":  "remotion",
    "data_reveal":   "remotion",
    "cta":           "remotion",
    "outro":         "remotion",

    # ── Hyperframes (catalog blocks, one per scene type)
    "x_post_overlay":        "hyperframes",
    "instagram_follow":      "hyperframes",
    "tiktok_follow":         "hyperframes",
    "reddit_overlay":        "hyperframes",
    "spotify_now_playing":   "hyperframes",
    "macos_notification":    "hyperframes",
    "yt_subscribe_cta":      "hyperframes",
}

# Hyperframes catalog block name per scene_type (for `hyperframes add` + composition-src)
HYPERFRAMES_CATALOG_MAP = {
    "x_post_overlay":       "x-post",
    "instagram_follow":     "instagram-follow",
    "tiktok_follow":        "tiktok-follow",
    "reddit_overlay":       "reddit-post",
    "spotify_now_playing":  "spotify-card",
    "macos_notification":   "macos-notification",
    "yt_subscribe_cta":     "yt-lower-third",
}


@dataclass
class Word:
    """One VO word with frame-aligned timestamps (ms from scene start)."""
    word: str
    start_ms: int
    end_ms: int
    emphasis: Optional[str] = None  # None | "hook" | "insight"


@dataclass
class Scene:
    """Engine-neutral scene spec. Both engines consume this."""
    n: int                             # scene number (1-indexed)
    scene_type: str                    # hook | problem_beat | ... | x_post_overlay | ...
    vo: str                            # full VO text
    words: list[Word]                  # per-word timestamps (scene-local ms)
    duration_sec: float                # canonical duration from design-tokens.json::sceneDuration
    overlay: str = ""                  # any on-screen text overlay (e.g. "9 → 3 fields")
    mood: str = ""                     # free-form director's note
    # Engine-specific props (engine decides what to pull)
    hook_total_count: int = 40         # KineticHook counter target
    data_number: int = 120             # DataReveal main number
    data_suffix: str = "%"
    data_sign: str = "+"
    cta_text: str = "LINK IN BIO"
    cta_url: str = "DIGISCHOLA.IN"
    cta_handle: str = "DIGISCHOLA"
    # Social-overlay props (Hyperframes-routed scenes)
    social_handle: str = ""            # "@digischola"
    social_post_text: str = ""         # for x_post_overlay, reddit_overlay
    social_metrics: dict = field(default_factory=dict)  # {likes: 423, reposts: 89}

    @property
    def engine(self) -> str:
        """Which engine renders this scene."""
        return SCENE_ROUTING.get(self.scene_type, "remotion")

    @property
    def catalog_block(self) -> Optional[str]:
        """Hyperframes catalog block name, if engine == hyperframes."""
        if self.engine != "hyperframes":
            return None
        return HYPERFRAMES_CATALOG_MAP.get(self.scene_type)

    def validate(self) -> list[str]:
        """Return list of validation errors (empty = valid)."""
        errors = []
        if self.scene_type not in SCENE_ROUTING:
            errors.append(f"Unknown scene_type: {self.scene_type}")
        if self.duration_sec <= 0:
            errors.append(f"duration_sec must be positive, got {self.duration_sec}")
        if self.engine == "hyperframes" and not self.catalog_block:
            errors.append(f"Hyperframes scene_type {self.scene_type} has no catalog block mapping")
        for w in self.words:
            if w.start_ms >= w.end_ms:
                errors.append(f"Word '{w.word}' has start_ms >= end_ms")
            if w.end_ms > int(self.duration_sec * 1000) + 500:  # 500ms grace
                errors.append(f"Word '{w.word}' end_ms ({w.end_ms}) exceeds scene duration")
        return errors

    def to_remotion_props(self) -> dict:
        """Serialize to the Remotion composition's props shape."""
        words_arr = [
            {"word": w.word, "start": w.start_ms / 1000, "end": w.end_ms / 1000,
             **({"emphasis": w.emphasis} if w.emphasis else {})}
            for w in self.words
        ]
        base = {"words": words_arr}
        if self.scene_type == "hook":
            base.update({"totalCount": self.hook_total_count, "showLogo": True})
        elif self.scene_type == "data_reveal":
            base.update({
                "number": self.data_number,
                "suffix": self.data_suffix,
                "sign": self.data_sign,
            })
        elif self.scene_type in ("cta", "outro"):
            base = {
                "ctaText": self.cta_text,
                "ctaUrl": self.cta_url,
                "handle": self.cta_handle,
            }
        return base

    def to_hyperframes_ctx(self) -> dict:
        """Serialize to a context dict used to template the Hyperframes HTML."""
        return {
            "composition_id": f"scene-{self.n}-{self.scene_type}",
            "duration_sec": self.duration_sec,
            "catalog_block": self.catalog_block,
            "handle": self.social_handle,
            "post_text": self.social_post_text,
            "metrics": self.social_metrics,
            "overlay": self.overlay,
            "words_ms": [
                {"word": w.word, "t": w.start_ms, "duration": w.end_ms - w.start_ms,
                 "emphasis": w.emphasis}
                for w in self.words
            ],
        }

    def to_json(self) -> str:
        d = asdict(self)
        # Drop Word private repr noise
        d["words"] = [asdict(w) for w in self.words]
        return json.dumps(d, indent=2)


# ── Scene list builder ──────────────────────────────────────────────────────

def scenes_from_draft(draft_path: Path, word_timestamps: dict[int, list[dict]]) -> list[Scene]:
    """
    Parse ## Scene breakdown section of a draft markdown + word-timestamp dict,
    return list of Scene objects. Scene numbers are 1-indexed.

    word_timestamps: {scene_n: [{"word": str, "start": float_sec, "end": float_sec, "emphasis": str?}]}
    """
    # Import locally to avoid circular dep with generate_reel.py
    from generate_reel import parse_scenes, SCENE_DURATION

    parsed = parse_scenes(draft_path)
    scenes = []
    for p in parsed:
        n = p["n"]
        scene_type = p["scene_type"]
        words_raw = word_timestamps.get(n, [])
        words = [
            Word(
                word=w["word"],
                start_ms=int(round(w["start"] * 1000)),
                end_ms=int(round(w["end"] * 1000)),
                emphasis=w.get("emphasis"),
            )
            for w in words_raw
        ]
        scene = Scene(
            n=n,
            scene_type=scene_type,
            vo=p.get("vo", ""),
            words=words,
            duration_sec=SCENE_DURATION.get(scene_type, 4.0),
            overlay=p.get("overlay", ""),
            mood=p.get("mood", ""),
        )
        # Extract number for data_reveal from overlay/vo
        if scene_type == "data_reveal":
            import re
            combined = f"{p.get('overlay', '')} {p.get('vo', '')}"
            num = re.search(r"(\+|-)?(\d+(?:\.\d+)?)\s*(%|x|K)?", combined)
            if num:
                scene.data_sign = num.group(1) or "+"
                scene.data_number = int(float(num.group(2)))
                scene.data_suffix = num.group(3) or "%"
        # Extract CTA for outro/cta from overlay
        if scene_type in ("cta", "outro"):
            import re
            url_match = re.search(
                r"([a-zA-Z0-9][a-zA-Z0-9\-.]*\.(?:com|in|io|co|app|me)(?:/[^\s]*)?)",
                p.get("overlay", ""),
            )
            if url_match:
                scene.cta_url = url_match.group(1).upper()
        errors = scene.validate()
        if errors:
            raise ValueError(f"Scene {n} ({scene_type}) validation failed: {errors}")
        scenes.append(scene)
    return scenes


if __name__ == "__main__":
    # Self-test
    s = Scene(
        n=1, scene_type="data_reveal",
        vo="Form cuts alone lift conversion 120 percent.",
        words=[Word("Form", 100, 400), Word("cuts", 440, 800),
               Word("alone", 850, 1250),
               Word("lift", 1300, 1650, emphasis="insight"),
               Word("conversion", 1700, 2350),
               Word("120%.", 2400, 3300, emphasis="insight")],
        duration_sec=3.8,
        data_number=120, data_suffix="%", data_sign="+",
    )
    errors = s.validate()
    print(f"validate: {errors}")
    print(f"engine: {s.engine}")
    print(f"catalog_block: {s.catalog_block}")
    print("\nremotion props:")
    print(json.dumps(s.to_remotion_props(), indent=2))
    print("\nhyperframes ctx:")
    print(json.dumps(s.to_hyperframes_ctx(), indent=2))
