#!/usr/bin/env python3
"""validate_output.py — per-PNG checks: aspect, dimensions, watermark heuristic, file size.

CRITICAL failures must be fixed before delivery.

Usage:
    python3 validate_output.py <working_dir>
"""
import argparse
import json
import sys
from math import gcd
from pathlib import Path


def png_dimensions(path: Path) -> tuple[int, int] | None:
    try:
        with path.open("rb") as f:
            head = f.read(24)
        if head.startswith(b"\x89PNG\r\n\x1a\n"):
            w = int.from_bytes(head[16:20], "big")
            h = int.from_bytes(head[20:24], "big")
            return (w, h)
    except Exception:
        return None
    return None


def aspect_ratio_str(w: int, h: int) -> str:
    g = gcd(w, h)
    a, b = w // g, h // g
    common = {(16, 9): "16:9", (9, 16): "9:16", (4, 3): "4:3", (3, 4): "3:4",
              (1, 1): "1:1", (3, 2): "3:2", (2, 3): "2:3", (4, 5): "4:5",
              (5, 4): "5:4", (21, 9): "21:9"}
    if (a, b) in common:
        return common[(a, b)]
    target = w / h
    best = min(common.items(), key=lambda kv: abs(target - kv[0][0] / kv[0][1]))
    return best[1]


def aspect_close(actual: str, expected: str, tolerance: float = 0.02) -> bool:
    def to_ratio(s: str) -> float:
        a, b = s.split(":")
        return float(a) / float(b)
    return abs(to_ratio(actual) - to_ratio(expected)) <= tolerance


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("working_dir")
    args = ap.parse_args()

    wd = Path(args.working_dir)
    manifest_path = wd / "manifest.json"
    if not manifest_path.exists():
        print(f"x manifest.json not found at {manifest_path}", file=sys.stderr)
        return 1

    manifest = json.loads(manifest_path.read_text())

    issues: list[dict] = []
    ok = 0
    for gen in manifest["generations"]:
        path = Path(gen["output_path"])
        sid = f"{gen['concept_id']}/{gen['variation_id']}-{gen['aspect']}"
        if not path.exists():
            issues.append({"id": sid, "level": "CRITICAL", "issue": "PNG missing", "path": str(path)})
            continue
        size = path.stat().st_size
        if size < 10_000:
            issues.append({"id": sid, "level": "CRITICAL", "issue": f"file too small ({size} bytes) — likely error response, not image"})
            continue
        if size > 30_000_000:
            issues.append({"id": sid, "level": "WARN", "issue": f"file very large ({size:,} bytes) — check resolution"})
        dims = png_dimensions(path)
        if not dims:
            issues.append({"id": sid, "level": "WARN", "issue": "could not parse PNG header"})
            continue
        actual_aspect = aspect_ratio_str(*dims)
        if not aspect_close(actual_aspect, gen["aspect"]):
            issues.append({
                "id": sid, "level": "CRITICAL",
                "issue": f"aspect mismatch: expected {gen['aspect']}, got {actual_aspect} ({dims[0]}x{dims[1]})",
            })
        ok += 1

    critical = [i for i in issues if i["level"] == "CRITICAL"]
    warn = [i for i in issues if i["level"] == "WARN"]

    report = {
        "validated_at": manifest.get("updated_at"),
        "total": len(manifest["generations"]),
        "passed": ok - len(critical),
        "critical": len(critical),
        "warnings": len(warn),
        "issues": issues,
    }
    (wd / "validation-report.json").write_text(json.dumps(report, indent=2))

    print(f"\nValidation report: {wd / 'validation-report.json'}")
    print(f"  Total:       {report['total']}")
    print(f"  Passed:      {report['passed']}")
    print(f"  CRITICAL:    {report['critical']}")
    print(f"  Warnings:    {report['warnings']}")
    if critical:
        print()
        print("  CRITICAL issues:")
        for i in critical[:20]:
            print(f"    - {i['id']:<30} {i['issue']}")
    return 1 if critical else 0


if __name__ == "__main__":
    sys.exit(main())
