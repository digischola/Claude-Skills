#!/usr/bin/env python3
"""
scan.py — Classify files and folders against cleanup rules.

Walks target roots, classifies each item as PROTECTED / AUTO-BLOAT / LIKELY-BLOAT /
AMBIGUOUS / UNCLASSIFIED, writes scan-report.json for cleanup.py to consume.

Never modifies the filesystem. Read-only.

Usage:
    python3 scan.py --report scan-report.json
    python3 scan.py --report scan-report.json --root /Users/digischola/Desktop
    python3 scan.py --root /Users/digischola/Desktop --only-tier AUTO-BLOAT
"""
from __future__ import annotations
import argparse
import fnmatch
import json
import os
import re
import sys
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta
from pathlib import Path

VERSION_SUFFIX_RE = re.compile(r"[-_]v\d+(\.\d+)?", re.IGNORECASE)

# Known deliverable suffixes produced by client-track skills.
# Used by the superseded-deliverable detector to group same-type files per client.
DELIVERABLE_SUFFIX_RE = re.compile(
    r"-("
    r"market-research|research-dashboard|"
    r"paid-media-strategy|strategy-dashboard|media-plan|creative-brief|"
    r"ad-copy-report|google-ads|meta-ads|image-prompts|video-storyboards|"
    r"rotation-brief|"
    r"optimization-report|optimization-dashboard|optimization-config|"
    r"landing-page-audit|audit-findings|"
    r"landing-page|page-spec|"
    r"brand-config|client-config"
    r")\.(md|html|json|csv|pdf)$"
)

# Weekly-indexed filenames for brand/performance/ and brand/calendars/
WEEKLY_FILENAME_RE = re.compile(r"^(\d{4})-W(\d{2})\.md$")

HOME = Path(os.path.expanduser("~"))
DESKTOP = HOME / "Desktop"
CLAUDE_PROJECTS = HOME / ".claude" / "projects"
QUARANTINE_ROOT = DESKTOP / ".housekeeping-quarantine"

IST = timezone(timedelta(hours=5, minutes=30))
NOW = datetime.now(IST)


def days_ago(path: Path, stat_result) -> float:
    mtime = datetime.fromtimestamp(stat_result.st_mtime, tz=IST)
    return (NOW - mtime).total_seconds() / 86400


def dir_size(path: Path) -> int:
    total = 0
    for root, dirs, files in os.walk(path, onerror=lambda e: None):
        for f in files:
            try:
                total += (Path(root) / f).lstat().st_size
            except OSError:
                pass
    return total


def newest_child_mtime(path: Path) -> float:
    """Return mtime of the most recently modified file anywhere under path.
    Falls back to the dir's own mtime if empty or unreadable."""
    newest = 0.0
    for root, _, files in os.walk(path, onerror=lambda e: None):
        for f in files:
            try:
                m = (Path(root) / f).lstat().st_mtime
                if m > newest:
                    newest = m
            except OSError:
                pass
    if newest == 0.0:
        try:
            newest = path.lstat().st_mtime
        except OSError:
            pass
    return newest


def human_size(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:.1f}{unit}"
        n /= 1024
    return f"{n:.1f}PB"


# ---------- KNOWN SETS ----------

# Top-level Desktop folders considered "known" (not AMBIGUOUS as orphan).
# Update when new real clients are onboarded.
KNOWN_DESKTOP_FOLDERS = {
    "Digischola", "Claude Skills", ".claude", ".housekeeping-quarantine",
    "Thrive Retreat", "Happy Buddha", "Happy Buddha Retreat",
    "ISKM", "ISKM Pondicherry", "Sri Krishna Mandir",
    "Salt Air Cinema", "Gargi Modi", "Gargi",
    "Bhaktivedanta School of Vedic Studies",
    "Shreyas Retreat",
    "remotion-promo",
}

# Known subfolders inside Desktop/Digischola/brand/ (top-level, post-2026-04-29 _engine/ convention).
# Skill internals (idea-bank.json, brand DNA wiki, _mining, _research, media build dirs, configs)
# all live INSIDE _engine/. Daily-workflow folders stay at top.
KNOWN_BRAND_FOLDERS = {
    "queue", "calendars", "performance", "videos", "social-images",
    "_engine", "_archive", "tools",
}

# Files protected anywhere under Desktop/Digischola/brand/_engine/ (or its wiki/ subdir).
LOCKED_BRAND_FILES = {
    "brand-wiki.md", "pillars.md", "voice-guide.md", "brand-identity.md",
    "credentials.md", "channel-playbook.md", "icp.md",
    "voice-flavor.md", "voice-lock.md",
    "wiki-config.json", "idea-bank.json", "credential-usage-log.json",
    "weekly-ritual.state.json", "housekeeping.state.json",
}

SKILL_ARCH_DIRS = {"references", "scripts", "assets", "evals"}

EXEMPT_MARKER = ".housekeeping-keep"


# ---------- CLASSIFICATION ----------

@dataclass
class Finding:
    tier: str
    rule_id: str
    reason: str
    path: str
    is_dir: bool
    size_bytes: int
    size_human: str
    mtime_iso: str
    age_days: float


def under(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def is_protected(path: Path, parts: tuple[str, ...]) -> tuple[str, str] | None:
    """Returns (rule_id, reason) if PROTECTED, else None."""
    name = path.name

    # 1. .claude framework files
    if ".claude" in parts:
        idx = parts.index(".claude")
        sub = parts[idx:]
        if len(sub) >= 2 and sub[1] in ("CLAUDE.md", "settings.local.json", "launch.json"):
            return ("framework-core", f".claude/{sub[1]}")
        if len(sub) >= 3 and sub[1] == "shared-context" and name.endswith(".md"):
            return ("shared-context", f".claude/shared-context/{name}")

    # 2. Skill architecture (anywhere, anything under a skill's SKILL.md sibling dirs)
    if name == "SKILL.md":
        return ("skill-md", f"skill: {path.parent.name}/SKILL.md")
    if any(seg in SKILL_ARCH_DIRS for seg in parts):
        for seg in SKILL_ARCH_DIRS:
            if seg in parts:
                idx = parts.index(seg)
                # Must be inside a skill dir (parent of that seg has a SKILL.md)
                skill_root = Path(*parts[:idx])
                if (Path("/") / skill_root / "SKILL.md").exists() or skill_root.parts and (Path("/" + "/".join(skill_root.parts)) / "SKILL.md").exists():
                    return ("skill-architecture", f"skill {seg}/ directory")
    # simpler path-based check for skill architecture
    p_str = str(path)
    if "/Claude Skills/skills/" in p_str or "/.claude/skills/" in p_str:
        # Anything inside a skill folder's protected subdirs
        for seg in ("/references/", "/scripts/", "/assets/", "/evals/", "/shared-scripts/"):
            if seg in p_str:
                return ("skill-architecture", f"skill arch: {seg.strip('/')}")
        if name == "SKILL.md":
            return ("skill-md", "skill SKILL.md")

    # 3. LOCKED brand wiki (under brand/_engine/ — files at _engine/ root or _engine/wiki/).
    # Post-2026-04-29 _engine/ convention: brand DNA + skill state moved into brand/_engine/.
    if "Digischola" in parts and "brand" in parts and "_engine" in parts:
        if name in LOCKED_BRAND_FILES:
            return ("locked-brand-wiki", f"brand/_engine/{name}")

    # 4. Performance data (performance/ directly under brand/)
    if "Digischola" in parts and "brand" in parts and "performance" in parts:
        if name == "log.json" or name.endswith(".md"):
            return ("performance-data", f"brand/performance/{name}")

    # 5. Client wiki (anything under {Client}/{Project}/_engine/wiki/ or {Client}/_engine/wiki/).
    # Post-2026-04-29: wiki/ moved into _engine/wiki/. _shared/ collapsed into client-root _engine/.
    if "_engine" in parts and "wiki" in parts:
        desktop_idx = _find_desktop_idx(parts)
        if desktop_idx is not None:
            return ("client-wiki", "client wiki page")

    # 6. Client primary deliverables.
    # Post-2026-04-29 _engine/ convention:
    #   - Presentables (HTML/MP4/PDF + campaign-setup folder bundle) sit at folder root.
    #   - Internals (md/json/csv reports, briefs, page-specs) live in _engine/working/.
    desktop_idx = _find_desktop_idx(parts)
    if desktop_idx is not None and not path.is_dir():
        ext = path.suffix.lower()
        # campaign-setup folder bundle (anywhere) stays protected
        if "campaign-setup" in parts:
            return ("client-deliverable", "campaign-setup output tree")
        # Working internals
        if "_engine" in parts and "working" in parts and ext in (".md", ".json", ".csv"):
            return ("client-deliverable", f"working {ext}")
        # _engine/brand-config.json + _engine/wiki-config.json at engine root
        if "_engine" in parts and name in ("brand-config.json", "wiki-config.json"):
            return ("client-deliverable", f"_engine/{name}")
        # Top-level presentables in a client/program folder. We treat depth >= desktop_idx + 3
        # as a program subfolder (Desktop/{Client}/{Project}/file.ext); depth desktop_idx + 2 is
        # client-root presentables (cross-program). Both are deliverables.
        if ext in (".html", ".mp4", ".mov", ".webm", ".pdf"):
            # Skip the .claude tree
            if ".claude" in parts:
                return None
            # Skip Digischola brand/ — those are handled by personal-brand-specific rules elsewhere
            if "Digischola" in parts:
                return None
            return ("client-deliverable", f"top-level presentable {ext}")

    # 7. Active scheduler / housekeeping logs (never delete the live files)
    if name in ("scheduler.log", "scheduler-failures.log", "housekeeping.log"):
        return ("active-log", name)

    # 8. Git
    if ".git" in parts:
        return ("git", ".git tree")

    # 8b. Claude Code session transcripts (.jsonl under .claude/projects/)
    # personal-brand-dna/mine_transcripts.py reads these to build voice samples.
    # Never touch. Individual tool-results/*.json inside session dirs ARE touchable.
    if ".claude" in parts and "projects" in parts and path.suffix == ".jsonl":
        return ("session-transcript", ".claude/projects/**/*.jsonl")

    # 9. .gitignore / .gitattributes
    if name in (".gitignore", ".gitattributes"):
        return ("git", name)

    # 10. Exemption marker (folder containing .housekeeping-keep — check any ancestor)
    cur = path
    while cur != cur.parent:
        if (cur / EXEMPT_MARKER).exists():
            return ("user-exempt", f"parent has {EXEMPT_MARKER}")
        cur = cur.parent
        if not under(cur, DESKTOP) and not under(cur, HOME):
            break

    # 11. KEEP- prefix on filename
    if name.startswith("KEEP-"):
        return ("user-exempt", "KEEP- prefix")

    # 12. Active queue draft (pending-approval/*.md where posting_status not 'posted')
    if "queue" in parts and "pending-approval" in parts and path.suffix == ".md":
        status = _read_posting_status(path)
        if status != "posted":
            return ("active-draft", f"posting_status={status or 'absent'}")

    # 13. Recent published draft (<180 days)
    if "queue" in parts and "published" in parts and path.suffix == ".md":
        try:
            age = days_ago(path, path.lstat())
            if age < 180:
                return ("recent-published", f"{age:.0f}d old (<180d)")
        except OSError:
            pass

    # 14. Calendar files always active
    if "Digischola" in parts and "calendars" in parts and path.suffix == ".md":
        return ("active-calendar", "brand/calendars/{week}.md")

    return None


def _find_desktop_idx(parts: tuple[str, ...]) -> int | None:
    for i, p in enumerate(parts):
        if p == "Desktop":
            return i
    return None


def _read_posting_status(path: Path) -> str | None:
    """Parse frontmatter for posting_status field. Returns value or None if absent."""
    try:
        with path.open("r", encoding="utf-8", errors="replace") as f:
            head = f.read(4096)
        if not head.startswith("---"):
            return None
        end = head.find("\n---", 3)
        if end < 0:
            return None
        fm = head[3:end]
        for line in fm.splitlines():
            if line.strip().startswith("posting_status"):
                return line.split(":", 1)[1].strip().strip("'\"")
    except OSError:
        return None
    return None


def classify_auto_bloat(path: Path, parts: tuple[str, ...], is_dir: bool, stat, age: float) -> tuple[str, str] | None:
    name = path.name
    p_str = str(path)

    # Python caches
    if is_dir and name in ("__pycache__", ".mypy_cache", ".pytest_cache", ".ruff_cache", "htmlcov"):
        return ("py-cache", f"{name}/")
    if name.endswith(".pyc") or name == ".coverage":
        return ("py-artifact", name)

    # macOS junk
    if name == ".DS_Store":
        return ("ds-store", ".DS_Store")
    if name.startswith("._"):
        return ("apple-double", "._ resource fork")

    # Editor swap
    if name.endswith((".swp", ".swo")) or (name.endswith("~") and len(name) > 1):
        return ("editor-swap", name)
    if name.startswith(".~lock."):
        return ("libreoffice-lock", name)

    # Node caches only in eval/fixture trees
    if is_dir and name == "node_modules" and ("evals" in parts or "fixtures" in parts):
        return ("node-modules-eval", "node_modules in eval tree")

    # Tool-result overflow (>14 days)
    if ".claude" in parts and "projects" in parts and "tool-results" in parts:
        if path.suffix in (".json", ".txt") and age > 14:
            return ("tool-results-old", f"{age:.0f}d old tool-result")

    # Build intermediates
    if is_dir and p_str.endswith("/.next/cache"):
        return ("next-cache", ".next/cache")
    if is_dir and p_str.endswith("/.turbo"):
        return ("turbo-cache", ".turbo")
    if is_dir and p_str.endswith("/node_modules/.cache"):
        return ("node-cache", "node_modules/.cache")

    return None


def classify_likely_bloat(path: Path, parts: tuple[str, ...], is_dir: bool, stat, age: float) -> tuple[str, str] | None:
    name = path.name
    p_str = str(path)

    # Raw research sources — perplexity and screenshots and keyword CSVs older than 90d.
    # Post-2026-04-29 _engine/ convention: client sources live in _engine/sources/.
    if "sources" in parts and "_engine" in parts:
        desktop_idx = _find_desktop_idx(parts)
        if desktop_idx is not None and age > 90:
            if name.startswith("perplexity-") and name.endswith(".md"):
                return ("old-perplexity-source", f"{age:.0f}d old perplexity dump")
            if path.suffix.lower() == ".png":
                return ("old-source-screenshot", f"{age:.0f}d old screenshot")
            if "keyword" in name.lower() and path.suffix.lower() == ".csv":
                return ("old-keyword-csv", f"{age:.0f}d old keyword CSV")

    # Brand mining artifacts older than 60 days.
    # Path: Desktop/Digischola/brand/_engine/_mining/...
    if "Digischola" in parts and "_engine" in parts and "_mining" in parts and age > 60:
        return ("old-mining", f"{age:.0f}d old mining artifact")

    # Trend research weekly folders older than 56 days.
    # Path: Desktop/Digischola/brand/_engine/_research/trends/{YYYY-WNN}/
    if "Digischola" in parts and "_engine" in parts and "_research" in parts and "trends" in parts:
        # A weekly folder looks like 2026-W04
        if is_dir and len(name) == 7 and name[4] == "-" and name[5] == "W" and age > 56:
            return ("old-trend-week", f"{age:.0f}d old trend week {name}")

    # Old published drafts (>180 days). queue/ stays at top of brand/.
    if "Digischola" in parts and "queue" in parts and "published" in parts and path.suffix == ".md" and age > 180:
        return ("old-published", f"{age:.0f}d old published draft")

    # Remotion intermediates older than 30 days.
    # Path: Desktop/Digischola/brand/_engine/remotion-studio/out/...
    if "remotion-studio" in parts and "out" in parts and age > 30:
        if path.suffix.lower() in (".mp4", ".png", ".mov", ".webm"):
            return ("remotion-intermediate", f"{age:.0f}d old render intermediate")

    # _renders folder older than 30 days. Path: Desktop/Digischola/brand/_engine/_renders/...
    if "Digischola" in parts and "_renders" in parts and age > 30:
        return ("old-render", f"{age:.0f}d old render")

    # Rotated log archives older than 90 days (scheduler.log.1, housekeeping.log.2026-02, etc.)
    if name.startswith(("scheduler.log.", "housekeeping.log.")) and name not in ("scheduler.log", "housekeeping.log") and age > 90:
        return ("old-log-archive", f"{age:.0f}d old log archive")

    # Explicitly "cleared" or "retired" archive folders (user named them so — intent is immediate).
    # No age threshold: the rename itself is the signal.
    if "queue" in parts and "archive" in parts and is_dir:
        name_lower = name.lower()
        if "cleared" in name_lower or "retired" in name_lower or name_lower.endswith("-done"):
            return ("cleared-archive", f"explicitly-cleared archive ({age:.0f}d old, name signals intent)")

    # Versioned test-iteration renders in queue/assets/ (reel-v7.1.mp4, scene-v2.jsx, etc.)
    if "queue" in parts and "assets" in parts and not is_dir and age > 7:
        if path.suffix.lower() in (".mp4", ".mov", ".webm", ".png", ".jsx") and VERSION_SUFFIX_RE.search(name):
            return ("test-iteration-render", f"versioned test render {age:.0f}d old")

    # Test-prefixed drafts in queue/
    if "queue" in parts and not is_dir and age > 3:
        nl = name.lower()
        if "-test-" in nl or nl.startswith("test-") or "-mvp" in nl or "-wip" in nl:
            return ("test-draft", f"test/mvp/wip draft {age:.0f}d old")

    # Housekeeping's own stale scan runtime (older than 7 days — last run's report is useful for diff)
    if name in ("scan-report.json", "approved-plan.json") and "housekeeping" in parts and age > 7:
        return ("stale-scan-runtime", f"stale housekeeping {name} {age:.0f}d old")

    # Tool-result overflow 7-14 days (AUTO tier catches >14d; this extends coverage)
    if ".claude" in parts and "projects" in parts and "tool-results" in parts:
        if path.suffix in (".json", ".txt") and 7 < age <= 14:
            return ("tool-results-stale", f"tool-result overflow {age:.0f}d old")

    # Tool-results 14-90d (catches stragglers)
    if ".claude" in parts and "projects" in parts and "tool-results" in parts:
        if path.suffix in (".json", ".txt") and 14 < age <= 90:
            # Fall through — AUTO tier handles >14d, so this branch is dead.
            # Keeping placeholder in case AUTO tier is skipped; returns None here.
            return None

    return None


def classify_ambiguous(path: Path, parts: tuple[str, ...], is_dir: bool, stat, age: float) -> tuple[str, str] | None:
    name = path.name

    # Orphan client folders — top-level Desktop folder not in known set, not modified 120d
    desktop_idx = _find_desktop_idx(parts)
    if desktop_idx is not None and len(parts) == desktop_idx + 2 and is_dir:
        folder = parts[desktop_idx + 1]
        if folder not in KNOWN_DESKTOP_FOLDERS and age > 120 and not folder.startswith("."):
            return ("orphan-client-folder", f"unknown Desktop folder, {age:.0f}d untouched")

    # Versioned test folders under Digischola/tools/ (lp-audit-v1, widget-v2, etc.).
    # The -v{N} suffix signals test-iteration, but skip if any child was modified
    # within the last 24h (folder is currently in use).
    if "Digischola" in parts and "tools" in parts and is_dir:
        didx = parts.index("Digischola")
        if len(parts) == didx + 3 and parts[didx + 1] == "tools":
            folder = parts[didx + 2]
            if VERSION_SUFFIX_RE.search(folder):
                child_mtime = newest_child_mtime(path)
                child_age_days = (datetime.now(IST).timestamp() - child_mtime) / 86400
                if child_age_days > 1:
                    return ("tools-version-folder",
                            f"versioned tools/{folder}/ (newest file {child_age_days:.0f}d old)")

    # Unknown top-level in brand/
    if "Digischola" in parts:
        didx = parts.index("Digischola")
        if len(parts) == didx + 3 and parts[didx + 1] == "brand" and is_dir:
            folder = parts[didx + 2]
            if folder not in KNOWN_BRAND_FOLDERS and not folder.startswith("."):
                return ("unknown-brand-subfolder", f"brand/{folder}/ not in known set")

    # Large single files (>50MB) outside known patterns
    if not is_dir:
        size = stat.st_size
        if size > 50 * 1024 * 1024:
            # Allow known patterns. Media build dirs now live under _engine/ post-2026-04-29.
            if ("remotion-studio" in parts or "music" in parts
                    or "face-samples" in parts or "voice-samples" in parts
                    or "hyperframes-scenes" in parts):
                return None
            if path.suffix.lower() in (".mp4", ".mov", ".webm"):
                return None
            return ("large-file", f"{human_size(size)} file")

    # Loose Desktop clutter — screenshot / pdf / zip / dmg older than 30 days
    if desktop_idx is not None and len(parts) == desktop_idx + 2 and not is_dir:
        if age > 30:
            if name.startswith("Screenshot") and name.endswith(".png"):
                return ("loose-screenshot", f"{age:.0f}d old screenshot on Desktop")
            if path.suffix.lower() in (".pdf", ".zip", ".dmg"):
                return ("loose-desktop-file", f"{age:.0f}d old {path.suffix}")

    return None


# ---------- WALK ----------

SKIP_WALK_DIRS = {".git", "node_modules", "__pycache__", ".mypy_cache", ".pytest_cache", ".next"}

# If the parent dir name matches one of these patterns, prune its children from
# further per-file classification — the parent dir itself is the finding, and
# quarantining it moves everything inside. Prevents duplicate flags.
CLEARED_PATTERNS = ("cleared", "retired")


def walk_targets(report: dict, only_tier: str | None = None) -> None:
    roots = [DESKTOP, CLAUDE_PROJECTS]
    for root in roots:
        if not root.exists():
            continue
        for dirpath, dirnames, filenames in os.walk(root, topdown=True):
            dp = Path(dirpath)
            # Don't walk into quarantine itself — handle separately
            if dp == QUARANTINE_ROOT or QUARANTINE_ROOT in dp.parents:
                dirnames[:] = []
                continue
            # Classify each subdirectory before descending; if PROTECTED, keep walking
            # (we still want to clean __pycache__ inside skill scripts/), so we don't
            # prune on PROTECTED at the dir level — we prune on SKIP_WALK_DIRS only.
            # But we DO want to surface __pycache__ as a finding without walking into it.
            to_prune = []
            for d in list(dirnames):
                child = dp / d
                child_parts = child.parts
                if d in SKIP_WALK_DIRS:
                    # Still classify the dir itself, but don't descend
                    _consider(child, child_parts, True, report, only_tier)
                    to_prune.append(d)
                    continue
                # Explicitly-cleared archives: flag the dir, don't double-flag children
                dl = d.lower()
                if ("queue" in child_parts and "archive" in child_parts and
                        (any(p in dl for p in CLEARED_PATTERNS) or dl.endswith("-done"))):
                    _consider(child, child_parts, True, report, only_tier)
                    to_prune.append(d)
            for d in to_prune:
                dirnames.remove(d)

            # Classify remaining dirs + files
            for d in dirnames:
                child = dp / d
                _consider(child, child.parts, True, report, only_tier)
            for f in filenames:
                child = dp / f
                _consider(child, child.parts, False, report, only_tier)


def extract_deliverable_suffix(fname: str) -> str | None:
    m = DELIVERABLE_SUFFIX_RE.search(fname)
    if m:
        return f"-{m.group(1)}.{m.group(2)}"
    return None


def analyze_deliverables_groups(report: dict, only_tier: str | None) -> None:
    """Post-walk: detect same-suffix clusters in any client deliverable surface.

    Post-2026-04-29 _engine/ convention: presentables (HTML/MP4/PDF) live at the
    program-folder root and intermediate working files (md/json/csv) live in
    _engine/working/. We scan both surfaces.

    For each cluster with >=2 files, flag all but the newest as AMBIGUOUS
    'possibly-superseded'. User decides per item (e.g., 'kingscliff' vs
    'kingscliff-lovable' may be legitimate both-kept).
    """
    if only_tier and only_tier != "AMBIGUOUS":
        return

    groups: dict[tuple[str, str], list] = {}
    for root, dirs, files in os.walk(DESKTOP, onerror=lambda e: None):
        rp = Path(root)
        if QUARANTINE_ROOT in rp.parents or rp == QUARANTINE_ROOT:
            dirs[:] = []
            continue
        rp_parts = rp.parts
        # Skip personal-brand and framework dirs.
        if "Digischola" in rp_parts or ".claude" in rp_parts:
            continue
        # Eligible scan surfaces:
        #   1. Inside _engine/working/ (intermediate md/json/csv reports + briefs)
        #   2. Inside campaign-setup/ folder bundles (anywhere)
        #   3. Top-level program/client folder roots: depth 2-3 below Desktop, NOT inside _engine/
        in_engine_working = "_engine" in rp_parts and "working" in rp_parts
        in_campaign_setup = "campaign-setup" in rp_parts
        desktop_idx = _find_desktop_idx(rp_parts)
        in_program_root = (
            desktop_idx is not None
            and len(rp_parts) in (desktop_idx + 2, desktop_idx + 3)
            and "_engine" not in rp_parts
        )
        if not (in_engine_working or in_campaign_setup or in_program_root):
            continue
        for fname in files:
            if fname.startswith("."):
                continue
            suffix = extract_deliverable_suffix(fname)
            if not suffix:
                continue
            p = rp / fname
            try:
                stat = p.lstat()
            except OSError:
                continue
            groups.setdefault((str(rp), suffix), []).append((p, stat))

    # For each group, only flag as superseded when the newer filename STEM is a
    # prefix-extension of the older stem (or vice versa). This catches genuine
    # re-runs like "thrive-market-research.md" vs "thrive-retreat-market-research.md"
    # without false-flagging distinct deliverables like "midweek-reset" vs "ashfield".
    for (parent, suffix), entries in groups.items():
        if len(entries) < 2:
            continue
        entries.sort(key=lambda x: x[1].st_mtime, reverse=True)  # newest first
        flagged_paths = set()
        for i, (newer_path, newer_stat) in enumerate(entries):
            newer_stem = newer_path.name[:-len(suffix)]
            for older_path, older_stat in entries[i + 1:]:
                if older_path in flagged_paths:
                    continue
                older_stem = older_path.name[:-len(suffix)]
                # Stem-prefix relationship (either direction)
                if (newer_stem.startswith(older_stem + "-") or
                        older_stem.startswith(newer_stem + "-") or
                        newer_stem == older_stem):
                    age = days_ago(older_path, older_stat)
                    delta_d = (newer_stat.st_mtime - older_stat.st_mtime) / 86400
                    reason = f"possibly-superseded by {newer_path.name} (newer by {delta_d:.0f}d)"
                    _record(report, "AMBIGUOUS", "superseded-deliverable", reason,
                            older_path, False, older_stat, age)
                    flagged_paths.add(older_path)


def analyze_weekly_archive(report: dict, only_tier: str | None) -> None:
    """Post-walk: flag weekly-indexed files in brand/{performance,calendars}/ older than 52 weeks.

    User explicitly chose 'keep last 52 weeks, archive older'. These are flagged as
    LIKELY-BLOAT; the actual archive (not quarantine) requires scripts/archive_old.py
    when files finally hit the threshold.
    """
    if only_tier and only_tier != "LIKELY-BLOAT":
        return

    weekly_roots = [
        DESKTOP / "Digischola" / "brand" / "performance",
        DESKTOP / "Digischola" / "brand" / "calendars",
    ]
    for root in weekly_roots:
        if not root.exists():
            continue
        for entry in root.iterdir():
            if not entry.is_file():
                continue
            if not WEEKLY_FILENAME_RE.match(entry.name):
                continue
            try:
                stat = entry.lstat()
            except OSError:
                continue
            age = days_ago(entry, stat)
            if age > 364:
                _record(report, "LIKELY-BLOAT", "weekly-over-52w",
                        f"{entry.name} is {age:.0f}d old (>52 weeks) — archive candidate",
                        entry, False, stat, age)


def _consider(path: Path, parts: tuple[str, ...], is_dir: bool, report: dict, only_tier: str | None) -> None:
    try:
        stat = path.lstat()
    except OSError:
        return

    age = days_ago(path, stat)

    # 1. PROTECTED — never add to report
    prot = is_protected(path, parts)
    if prot:
        return

    # 2. AUTO-BLOAT
    hit = classify_auto_bloat(path, parts, is_dir, stat, age)
    if hit:
        if only_tier and only_tier != "AUTO-BLOAT":
            return
        _record(report, "AUTO-BLOAT", hit[0], hit[1], path, is_dir, stat, age)
        return

    # 3. LIKELY-BLOAT
    hit = classify_likely_bloat(path, parts, is_dir, stat, age)
    if hit:
        if only_tier and only_tier != "LIKELY-BLOAT":
            return
        _record(report, "LIKELY-BLOAT", hit[0], hit[1], path, is_dir, stat, age)
        return

    # 4. AMBIGUOUS
    hit = classify_ambiguous(path, parts, is_dir, stat, age)
    if hit:
        if only_tier and only_tier != "AMBIGUOUS":
            return
        _record(report, "AMBIGUOUS", hit[0], hit[1], path, is_dir, stat, age)
        return

    # else UNCLASSIFIED — don't record


def _record(report: dict, tier: str, rule_id: str, reason: str, path: Path, is_dir: bool, stat, age: float) -> None:
    size = dir_size(path) if is_dir else stat.st_size
    mtime_iso = datetime.fromtimestamp(stat.st_mtime, tz=IST).isoformat()
    f = Finding(
        tier=tier,
        rule_id=rule_id,
        reason=reason,
        path=str(path),
        is_dir=is_dir,
        size_bytes=size,
        size_human=human_size(size),
        mtime_iso=mtime_iso,
        age_days=round(age, 1),
    )
    report["findings"].append(asdict(f))
    report["totals"][tier]["count"] += 1
    report["totals"][tier]["bytes"] += size


def main() -> int:
    ap = argparse.ArgumentParser(description="Scan for housekeeping candidates")
    ap.add_argument("--report", default="scan-report.json", help="Output path for JSON report")
    ap.add_argument("--root", default=None, help="Override scan root (default: Desktop + .claude/projects)")
    ap.add_argument("--only-tier", choices=["AUTO-BLOAT", "LIKELY-BLOAT", "AMBIGUOUS"], default=None)
    args = ap.parse_args()

    report = {
        "generated_at": NOW.isoformat(),
        "roots_scanned": [str(DESKTOP), str(CLAUDE_PROJECTS)],
        "totals": {
            "AUTO-BLOAT": {"count": 0, "bytes": 0},
            "LIKELY-BLOAT": {"count": 0, "bytes": 0},
            "AMBIGUOUS": {"count": 0, "bytes": 0},
        },
        "findings": [],
    }

    walk_targets(report, only_tier=args.only_tier)
    analyze_deliverables_groups(report, only_tier=args.only_tier)
    analyze_weekly_archive(report, only_tier=args.only_tier)

    out = Path(args.report)
    out.write_text(json.dumps(report, indent=2))

    # Summary to stderr so stdout stays JSON-parseable if someone pipes
    print(f"Scanned in {(datetime.now(IST) - NOW).total_seconds():.1f}s", file=sys.stderr)
    for tier in ("AUTO-BLOAT", "LIKELY-BLOAT", "AMBIGUOUS"):
        t = report["totals"][tier]
        print(f"  {tier}: {t['count']} items, {human_size(t['bytes'])}", file=sys.stderr)
    print(f"Report: {out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
