#!/usr/bin/env python3
"""
analyze_source.py — face detection + safe-zone mapping for the source video.

Samples every 0.5s of the source, locates the largest face, emits face-bboxes.json
in TARGET-RENDER-DIMS coordinates (not source coordinates) so the assembler
can use the bboxes directly when placing captions/overlays.

Usage:
  python3 analyze_source.py <source.mp4> <output-dir>

Output file:
  <output-dir>/face-bboxes.json
    [
      { "t": 0.0,   "face_tgt": { "x": 420, "y": 380, "w": 260, "h": 320 } },
      { "t": 0.5,   "face_tgt": { "x": 422, "y": 378, "w": 260, "h": 320 } },
      ...
      { "t": 15.0,  "face_tgt": null }   // no face detected
    ]

The assembler can then:
  - Place captions in the largest contiguous non-face zone
  - Avoid dropping overlays on the speaker's face

No-op gracefully if OpenCV is not installed (prints warning, exits 0).
"""

import json
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) < 3:
        print("usage: analyze_source.py <source.mp4> <output-dir>")
        return 1

    src = Path(sys.argv[1])
    out_dir = Path(sys.argv[2])
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "face-bboxes.json"

    try:
        import cv2
    except ImportError:
        print("[analyze_source] opencv-python not installed — skipping face detection", file=sys.stderr)
        out_path.write_text("[]")
        return 0

    if not src.is_file():
        print(f"ERROR: source not found: {src}", file=sys.stderr)
        return 1

    # Determine target render dims from probe file if present
    probe_path = out_dir / "source-probe.json"
    tgt_w, tgt_h = None, None
    if probe_path.is_file():
        probe = json.loads(probe_path.read_text())
        tgt_w = probe.get("target_render_dims", {}).get("width")
        tgt_h = probe.get("target_render_dims", {}).get("height")

    cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    face_cascade = cv2.CascadeClassifier(cascade_path)
    if face_cascade.empty():
        print("[analyze_source] haar cascade failed to load — skipping", file=sys.stderr)
        out_path.write_text("[]")
        return 0

    cap = cv2.VideoCapture(str(src))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    src_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    src_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    if tgt_w is None or tgt_h is None:
        tgt_w, tgt_h = src_w, src_h

    scale_x = tgt_w / src_w if src_w else 1.0
    scale_y = tgt_h / src_h if src_h else 1.0

    sample_interval = max(1, int(fps * 0.5))
    results = []

    for frame_idx in range(0, total_frames, sample_interval):
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ok, frame = cap.read()
        if not ok:
            continue
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5, minSize=(50, 50))
        t = round(frame_idx / fps, 3)

        if len(faces) > 0:
            fx, fy, fw, fh = max(faces, key=lambda f: f[2] * f[3])
            # Scale to target render dims
            face_tgt = {
                "x": int(fx * scale_x),
                "y": int(fy * scale_y),
                "w": int(fw * scale_x),
                "h": int(fh * scale_y),
            }
            results.append({"t": t, "face_tgt": face_tgt})
        else:
            results.append({"t": t, "face_tgt": None})

    cap.release()

    summary = {
        "source_path": str(src),
        "src_dims": {"width": src_w, "height": src_h},
        "target_dims": {"width": tgt_w, "height": tgt_h},
        "fps": fps,
        "samples": results,
        "samples_with_face": sum(1 for r in results if r["face_tgt"]),
    }
    out_path.write_text(json.dumps(summary, indent=2))
    print(f"[analyze_source] wrote {out_path.name}  "
          f"({len(results)} samples, {summary['samples_with_face']} with face)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
