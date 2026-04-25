#!/usr/bin/env python3
"""
edit_video.py — ONE-COMMAND video editor.

Runs the full pipeline: scaffold → probe → prepass → transcribe → analyze →
validate-transcript → [content-plan.json] → assemble → lint → render →
postpass → validate → deliver.

The [content-plan.json] step is the one creative step:
  - If running inside Claude Code: the agent generates content-plan.json by reading
    the prepared inputs (probe, transcript, face bboxes, brand config, brief) using
    references/content-plan-recipe.md as the rulebook. The agent calls edit_video.py
    with --phase ship after writing the plan.
  - If ANTHROPIC_API_KEY is set and --auto-plan is passed: content_plan_brain.py is
    called to generate the plan via Claude API autonomously (for cron / scheduled runs).
  - If --content-plan <path> is passed: uses the provided plan file directly.

Two-phase invocation:
  edit_video.py prepare SOURCE --brief "..." --client Digischola [--project Reels]
      → runs everything up to and including analyze_source, then stops and prints
        the project directory path. Exit code 0 if content-plan.json missing,
        exit code 2 if content-plan.json already exists (you can skip to ship).

  edit_video.py ship PROJECT_DIR [--preset apple-premium]
      → assumes content-plan.json exists in PROJECT_DIR. Runs the rest.

One-shot convenience:
  edit_video.py run SOURCE --brief "..." --client Digischola
      → runs prepare, then (inside Claude Code) the agent writes content-plan.json,
        then calls `edit_video.py ship <project-dir>`.

Safe to re-run; each phase is idempotent.

Environment:
  - macOS Darwin
  - Python 3.9+ stdlib (no external deps for the orchestrator itself)
  - Scripts expect ffmpeg, ffprobe, jq, node/npx installed
  - opencv-python is optional (face detection degrades gracefully if missing)
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = SKILL_ROOT / "scripts"
REFERENCES = SKILL_ROOT / "references"


def log(msg: str) -> None:
    print(f"\n[edit_video] {msg}", flush=True)


def run(cmd, cwd=None, check=True, capture=False) -> subprocess.CompletedProcess:
    display = " ".join(str(c) for c in cmd)
    print(f"    >>> {display}", flush=True)
    return subprocess.run(
        cmd, cwd=cwd, check=check, text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
    )


def phase_prepare(args) -> Path:
    """Prepare phase: scaffolds the project and generates all inputs the director step needs."""
    today = date.today().isoformat()
    source = Path(args.source).expanduser().resolve()
    if not source.is_file():
        print(f"ERROR: source not found: {source}", file=sys.stderr)
        sys.exit(1)

    stem = source.stem.lower().replace(" ", "-").replace("_", "-")
    project_name = f"{today}-{stem}"
    client_root = Path.home() / f"Desktop/{args.client}"
    project_parent = client_root / (args.project or "brand/videos/projects")
    project_parent.mkdir(parents=True, exist_ok=True)
    project_dir = project_parent / project_name

    # 1. Scaffold hyperframes project (idempotent — skips if already exists with index.html)
    if not (project_dir / "hyperframes.json").is_file():
        log(f"Scaffolding hyperframes project at {project_dir}")
        run(["npx", "hyperframes", "init", project_name, "--yes"], cwd=project_parent)
    else:
        log(f"Project already scaffolded: {project_dir}")
    (project_dir / "assets").mkdir(exist_ok=True)

    # 2. Probe source
    log("Probing source video")
    run(["bash", str(SCRIPTS / "probe_source.sh"), str(source), str(project_dir)])

    # 3. ffmpeg prepass (silence trim + loudness + dense keyframes)
    if not (project_dir / "prepped.mp4").is_file():
        log("Running ffmpeg prepass (silence trim + normalize + dense keyframes)")
        run([
            "bash", str(SCRIPTS / "ffmpeg_prepass.sh"),
            str(source), str(project_dir / "source-probe.json"),
            str(project_dir), args.preset,
        ])
    else:
        log("prepped.mp4 already exists, skipping prepass")

    # 4. Copy prepped to assets/source.mp4 (hyperframes expects it there)
    assets_src = project_dir / "assets/source.mp4"
    if not assets_src.is_file():
        shutil.copy(project_dir / "prepped.mp4", assets_src)

    # 5. Transcribe (only if missing)
    transcript_path = project_dir / "assets/transcript.json"
    if not transcript_path.is_file():
        log("Transcribing audio via hyperframes CLI (Whisper small.en)")
        run([
            "npx", "hyperframes", "transcribe", str(assets_src),
            "--json", "--model", "small.en", "--language", "en",
        ], cwd=project_dir)
        # transcribe writes transcript.json to project root; move to assets/
        root_tr = project_dir / "transcript.json"
        if root_tr.is_file():
            shutil.move(str(root_tr), str(transcript_path))
    else:
        log("transcript.json already exists, skipping transcription")

    # 6. Validate transcript — flag metric words for operator sanity check
    log("Validating transcript (metric-word accuracy gate)")
    run([
        "python3", str(SCRIPTS / "validate_transcript.py"), str(transcript_path),
    ], check=False)

    # 7. Face detection / source intelligence (best-effort, non-blocking)
    log("Analyzing source (face detection) — non-blocking")
    run([
        "python3", str(SCRIPTS / "analyze_source.py"),
        str(source), str(project_dir),
    ], check=False)

    log(f"PREPARE COMPLETE: {project_dir}")
    log(f"Next step: generate content-plan.json at {project_dir / 'content-plan.json'}")
    log(f"Then run: python3 {SCRIPTS / 'edit_video.py'} ship {project_dir}")
    return project_dir


def phase_ship(args) -> Path:
    """Ship phase: assumes content-plan.json exists; renders + delivers."""
    project_dir = Path(args.project_dir).expanduser().resolve()
    if not project_dir.is_dir():
        print(f"ERROR: project dir not found: {project_dir}", file=sys.stderr)
        sys.exit(1)

    plan_path = project_dir / "content-plan.json"
    if not plan_path.is_file():
        print(f"ERROR: content-plan.json missing at {plan_path}", file=sys.stderr)
        print("       generate it first (manually or via content_plan_brain.py)", file=sys.stderr)
        sys.exit(1)

    # 1. Assemble composition from content-plan
    log("Assembling composition from content-plan.json")
    run([
        "python3", str(SCRIPTS / "assemble_composition.py"),
        str(plan_path), str(project_dir),
    ])

    # 2. Lint (advisory)
    log("Linting hyperframes composition")
    run(["npx", "hyperframes", "lint"], cwd=project_dir, check=False)

    # 3. Render to MP4
    log("Rendering to MP4 (this takes 1-3 minutes)")
    run(["npx", "hyperframes", "render"], cwd=project_dir)

    # 4. Find latest render
    renders_dir = project_dir / "renders"
    renders = sorted(renders_dir.glob("*.mp4"), key=lambda p: p.stat().st_mtime)
    if not renders:
        print(f"ERROR: no MP4 produced in {renders_dir}", file=sys.stderr)
        sys.exit(1)
    raw = renders[-1]
    log(f"Raw render: {raw}")

    # 5. Delivery paths
    # Client root is two levels up from project dir (client/brand/videos/projects/<proj>)
    # So: project_dir.parent.parent / "edits" typically.
    # We try to find a natural edits dir. Fallback: sibling of projects dir.
    edits_candidates = [
        project_dir.parent.parent / "edits",
        project_dir.parent / "edits",
    ]
    edits_dir = next((p for p in edits_candidates if p.parent.is_dir()), edits_candidates[0])
    edits_dir.mkdir(parents=True, exist_ok=True)
    final = edits_dir / f"{project_dir.name}.mp4"

    # 6. Post-pass (fades + loudness + encode)
    log(f"Running ffmpeg postpass → {final}")
    preset = args.preset
    # Try to read preset from content-plan if not overridden
    try:
        plan = json.loads(plan_path.read_text())
        preset = plan.get("preset", preset)
    except Exception:
        pass
    run([
        "bash", str(SCRIPTS / "ffmpeg_postpass.sh"),
        str(raw), str(final), preset,
    ])

    # 7. Validate output
    log("Validating deliverable")
    result = run([
        "python3", str(SCRIPTS / "validate_output.py"),
        str(final), str(project_dir / "source-probe.json"), preset,
    ], check=False)

    log(f"✓ DELIVERED: {final}")
    log(f"  thumbnail: {final.with_suffix('')}-thumb.jpg")
    return final


def main() -> int:
    parser = argparse.ArgumentParser(description="video-edit one-command orchestrator")
    sub = parser.add_subparsers(dest="phase", required=True)

    p = sub.add_parser("prepare", help="Run everything up to content-plan generation")
    p.add_argument("source", help="path to source video")
    p.add_argument("--brief", default="", help="one-line creative brief (recorded for the director step)")
    p.add_argument("--client", required=True, help="client name — Desktop subfolder")
    p.add_argument("--project", default="brand/videos/projects",
                   help="subpath under client for project folder (default: brand/videos/projects)")
    p.add_argument("--preset", default="apple-premium")

    s = sub.add_parser("ship", help="Assemble + render + postpass + deliver")
    s.add_argument("project_dir", help="project directory (must contain content-plan.json)")
    s.add_argument("--preset", default="apple-premium")

    args = parser.parse_args()

    if args.phase == "prepare":
        phase_prepare(args)
    elif args.phase == "ship":
        phase_ship(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
