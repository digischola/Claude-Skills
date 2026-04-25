#!/usr/bin/env python3
"""
test_routing.py — Smoke test for dual-engine routing logic (v7.4).

Verifies without actually rendering any MP4:
  1. parse_scenes() correctly classifies scenes via HEADING_LABEL_MAP
  2. SCENE_ROUTING dispatches each scene_type to the right engine
  3. HYPERFRAMES_CATALOG_MAP returns a block name for every hyperframes scene_type
  4. SCENE_DURATION has an entry for every routed scene_type
  5. render_scene() correctly populates render_log with routing metadata
  6. scene_spec.py::Scene.engine + catalog_block agree with generate_reel.py SCENE_ROUTING

Run: python3 test_routing.py
Exit 0 on pass, 1 on fail.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generate_reel as gr
import scene_spec as ss


FAILS = []


def check(cond, msg):
    if cond:
        print(f"  ✓ {msg}")
    else:
        print(f"  ✗ {msg}")
        FAILS.append(msg)


# ── 1. HEADING_LABEL_MAP covers all routed scene types ────────────────────
print("\n▶ Test 1: HEADING_LABEL_MAP coverage")
for scene_type in gr.SCENE_ROUTING:
    matching_labels = [k for k, v in gr.HEADING_LABEL_MAP.items() if v == scene_type]
    check(
        len(matching_labels) >= 1,
        f"scene_type={scene_type!r} has at least one label in HEADING_LABEL_MAP",
    )

# ── 2. SCENE_ROUTING + SCENE_DURATION + COMPOSITION/CATALOG parity ────────
print("\n▶ Test 2: Routing tables agree on coverage")
for scene_type, engine in gr.SCENE_ROUTING.items():
    check(scene_type in gr.SCENE_DURATION, f"{scene_type!r} has SCENE_DURATION entry")
    if engine == "remotion":
        check(scene_type in gr.SCENE_COMPOSITION,
              f"{scene_type!r} → Remotion has SCENE_COMPOSITION entry")
    elif engine == "hyperframes":
        check(scene_type in gr.HYPERFRAMES_CATALOG_MAP,
              f"{scene_type!r} → Hyperframes has catalog block")

# ── 3. scene_spec.py agrees with generate_reel.py ─────────────────────────
print("\n▶ Test 3: scene_spec.py + generate_reel.py routing tables match")
check(
    ss.SCENE_ROUTING == gr.SCENE_ROUTING,
    "SCENE_ROUTING in scene_spec.py matches generate_reel.py",
)
check(
    ss.HYPERFRAMES_CATALOG_MAP == gr.HYPERFRAMES_CATALOG_MAP,
    "HYPERFRAMES_CATALOG_MAP in scene_spec.py matches generate_reel.py",
)

# ── 4. Scene.engine property + validate() ──────────────────────────────────
print("\n▶ Test 4: Scene.engine + validate()")
s_rmt = ss.Scene(n=1, scene_type="data_reveal", vo="test",
                 words=[ss.Word("a", 0, 500)], duration_sec=3.8)
check(s_rmt.engine == "remotion", "data_reveal scene routes to remotion")
check(s_rmt.catalog_block is None, "data_reveal has no catalog block")
check(s_rmt.validate() == [], "valid data_reveal scene has no validation errors")

s_hf = ss.Scene(n=2, scene_type="x_post_overlay", vo="test",
                words=[ss.Word("b", 0, 500)], duration_sec=5.0)
check(s_hf.engine == "hyperframes", "x_post_overlay routes to hyperframes")
check(s_hf.catalog_block == "x-post", "x_post_overlay catalog block is x-post")
check(s_hf.validate() == [], "valid x_post_overlay scene has no validation errors")

s_bad = ss.Scene(n=3, scene_type="nonexistent", vo="test",
                 words=[], duration_sec=-1)
errors = s_bad.validate()
check(len(errors) >= 2, f"invalid scene surfaces >=2 errors (got {len(errors)})")

# ── 5. render_scene() dispatches to the right engine + logs ───────────────
print("\n▶ Test 5: render_scene() dispatch + render_log append")
with tempfile.TemporaryDirectory() as td:
    td = Path(td)
    calls = {"remotion": 0, "hyperframes": 0}

    def fake_remotion(scene, out_mp4, smoke_test=True):
        calls["remotion"] += 1
        out_mp4.write_bytes(b"fake-mp4")
        return True

    def fake_hyperframes(scene, out_mp4):
        calls["hyperframes"] += 1
        out_mp4.write_bytes(b"fake-mp4")
        return True

    log: list = []
    with patch.object(gr, "render_scene_remotion", side_effect=fake_remotion), \
         patch.object(gr, "render_scene_hyperframes", side_effect=fake_hyperframes):
        # Remotion-routed
        ok1 = gr.render_scene(
            {"n": 1, "scene_type": "hook"}, td / "s1.mp4",
            smoke_test=True, render_log=log,
        )
        # Hyperframes-routed
        ok2 = gr.render_scene(
            {"n": 2, "scene_type": "x_post_overlay"}, td / "s2.mp4",
            smoke_test=True, render_log=log,
        )
        # Another remotion
        ok3 = gr.render_scene(
            {"n": 3, "scene_type": "outro"}, td / "s3.mp4",
            smoke_test=True, render_log=log,
        )

    check(ok1 and ok2 and ok3, "all 3 render_scene() calls return True")
    check(calls["remotion"] == 2, f"remotion engine called 2× (got {calls['remotion']})")
    check(calls["hyperframes"] == 1, f"hyperframes engine called 1× (got {calls['hyperframes']})")
    check(len(log) == 3, f"render_log has 3 rows (got {len(log)})")
    check(log[0]["engine"] == "remotion" and log[0]["scene_type"] == "hook",
          "log[0] = hook via remotion")
    check(log[1]["engine"] == "hyperframes" and log[1]["scene_type"] == "x_post_overlay",
          "log[1] = x_post_overlay via hyperframes")
    check(log[2]["engine"] == "remotion" and log[2]["scene_type"] == "outro",
          "log[2] = outro via remotion")

# ── 6. parse_scenes() against a dual-engine smoke draft ───────────────────
print("\n▶ Test 6: parse_scenes() on dual-engine smoke draft")
smoke_draft = """---
entry_id: v7.4-smoke
pillar: test
---

## Scene breakdown

### Scene 1 — Hook
- VO: I audited 40 landing pages.
- Overlay: PAGES AUDITED
- Mood: kinetic

### Scene 2 — X Post
- VO: This one got 12K impressions in a week.
- Overlay: @digischola 12K views
- Mood: proof

### Scene 3 — The Data
- VO: Form cuts lifted conversion 120 percent.
- Overlay: +120% / 9 → 3 fields
- Mood: reveal

### Scene 4 — Outro
- VO: Try it on your next landing page. Visit digischola.in.
- Overlay: DIGISCHOLA.IN
- Mood: handoff
"""
with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
    f.write(smoke_draft)
    draft_path = Path(f.name)
try:
    scenes = gr.parse_scenes(draft_path)
    check(len(scenes) == 4, f"parse_scenes returns 4 scenes (got {len(scenes)})")
    expected = ["hook", "x_post_overlay", "data_reveal", "outro"]
    actual = [s["scene_type"] for s in scenes]
    check(actual == expected,
          f"scene_types in order match {expected!r} (got {actual!r})")
    # Verify routing on parsed scenes
    engines = [gr.SCENE_ROUTING[s["scene_type"]] for s in scenes]
    check(engines == ["remotion", "hyperframes", "remotion", "remotion"],
          f"engine dispatch matches (got {engines!r})")
finally:
    draft_path.unlink()

# ── Report ──────────────────────────────────────────────────────────────────
print(f"\n{'='*60}")
if FAILS:
    print(f"✗ {len(FAILS)} check(s) FAILED:")
    for f in FAILS:
        print(f"  • {f}")
    sys.exit(1)
else:
    print("✓ ALL CHECKS PASSED")
    sys.exit(0)
