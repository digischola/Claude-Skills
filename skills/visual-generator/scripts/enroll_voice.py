#!/usr/bin/env python3
"""
Voice enrollment wizard — record 10 voice samples for brand voice cloning.

One-time setup. Starts a local HTTP server + dark-mode browser recorder page.
Mayank reads 10 varied sentences (different tones: declarative, data-heavy,
rhetorical question, energetic, measured). Browser captures via MediaRecorder API,
uploads WebM → server converts to WAV via ffmpeg → saves to brand/_engine/voice-samples/.

After all 10 are recorded, writes brand/_engine/wiki/voice-lock.md with metadata + transcripts.
clone_voice.py then uses these samples with F5-TTS to generate VOs in Mayank's voice.

Usage:
  python3 enroll_voice.py                # starts browser recorder at :8766
  python3 enroll_voice.py --port 9090
  python3 enroll_voice.py --status       # show enrollment state + exit
  python3 enroll_voice.py --reset        # delete samples + start fresh
"""

from __future__ import annotations

import argparse
import html
import json
import shutil
import subprocess
import sys
import threading
import webbrowser
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

IST = timezone(timedelta(hours=5, minutes=30))

DEFAULT_BRAND = Path("/Users/digischola/Desktop/Digischola")

# Brand color palette (same as review_queue.py)
PRIMARY = "#3B9EFF"
BG = "#0A0F1C"
CARD_BG = "#111827"
BORDER = "#1F2937"
TEXT = "#E5E7EB"
MUTED = "#9CA3AF"
REC = "#EF4444"
OK = "#10B981"

# 10 enrollment sentences — varied tone / pace / emotion so F5-TTS learns range.
# Uses Mayank's actual brand vocabulary + structures so the clone matches HIS voice,
# not a generic neutral voice. No em dashes per voice-guide.
ENROLLMENT_SENTENCES = [
    {
        "id": 1,
        "tone": "Greeting + positioning (neutral, warm)",
        "text": "Hello, I'm Mayank from Digischola. I help wellness retreats convert more leads at lower cost.",
    },
    {
        "id": 2,
        "tone": "Credentials (measured, confident)",
        "text": "Ex-Google performance marketer. Ten plus years. One billion dollars in ad spend managed.",
    },
    {
        "id": 3,
        "tone": "Brutal truth hook (direct, slight edge)",
        "text": "Here is the honest truth about low budget Meta ads. Most of them never learn.",
    },
    {
        "id": 4,
        "tone": "Data-driven statement (firm, specific)",
        "text": "I audited forty wellness retreat pages this quarter. Most spent five seconds saying nothing.",
    },
    {
        "id": 5,
        "tone": "Rhetorical question (curious, slight lift)",
        "text": "What if I told you the landing page matters more than the ad itself?",
    },
    {
        "id": 6,
        "tone": "Numbers + contrast (clear diction)",
        "text": "Three field forms convert twenty five percent better than nine field forms. That is the data.",
    },
    {
        "id": 7,
        "tone": "Personal pivot (reflective)",
        "text": "I used to quote hours. I now quote outcomes. The math changed everything.",
    },
    {
        "id": 8,
        "tone": "Punchy insight (energetic, quick)",
        "text": "Your CTA copy is the easiest win. Sign up for free becomes trial for free. One hundred and four percent lift.",
    },
    {
        "id": 9,
        "tone": "Value reframe (measured, thoughtful)",
        "text": "Small budget paid media is not about spending less. It is about spending smarter.",
    },
    {
        "id": 10,
        "tone": "Sign-off / call to action (confident, clear)",
        "text": "Audit your landing page in five seconds. Then fix the form, the headline, and the button. In that order.",
    },
]


def voice_samples_dir(brand: Path) -> Path:
    # Post-2026-04-29 _engine/ convention: voice samples live in brand/_engine/.
    return brand / "brand" / "_engine" / "voice-samples"


def voice_lock_path(brand: Path) -> Path:
    # Post-2026-04-29 _engine/ convention: voice-lock.md is brand DNA wiki.
    return brand / "brand" / "_engine" / "wiki" / "voice-lock.md"


def sample_path(brand: Path, idx: int, ext: str = "wav") -> Path:
    return voice_samples_dir(brand) / f"sample-{idx:02d}.{ext}"


def enrollment_status(brand: Path) -> dict:
    samples_dir = voice_samples_dir(brand)
    recorded = []
    for s in ENROLLMENT_SENTENCES:
        wav = sample_path(brand, s["id"], "wav")
        recorded.append({
            "id": s["id"],
            "tone": s["tone"],
            "text": s["text"],
            "recorded": wav.exists(),
            "path": str(wav) if wav.exists() else None,
            "size_bytes": wav.stat().st_size if wav.exists() else 0,
        })
    total = len(ENROLLMENT_SENTENCES)
    done = sum(1 for r in recorded if r["recorded"])
    return {
        "total": total,
        "done": done,
        "remaining": total - done,
        "samples": recorded,
        "voice_lock_exists": voice_lock_path(brand).exists(),
    }


def write_voice_lock(brand: Path):
    """Write brand/_engine/wiki/voice-lock.md with metadata + transcripts after all 10 samples recorded."""
    status = enrollment_status(brand)
    if status["done"] < len(ENROLLMENT_SENTENCES):
        return False
    now = datetime.now(IST).isoformat()
    lines = [
        "# Digischola Voice Lock",
        "",
        "Master reference for Mayank's brand voice. Used by `clone_voice.py` (F5-TTS)",
        "to generate Reel voiceovers that sound like Mayank without any cloud API.",
        "",
        f"**Enrolled:** {now}",
        f"**Samples:** {status['done']} / {status['total']} recorded",
        f"**Location:** `brand/_engine/voice-samples/sample-01.wav` … `sample-10.wav`",
        "",
        "## Use from Python",
        "",
        "```python",
        "from pathlib import Path",
        "# Reference sample for F5-TTS. Pick any recorded sample.",
        "ref_wav = Path('brand/_engine/voice-samples/sample-01.wav')",
        "ref_text = \"Hello, I'm Mayank from Digischola. I help wellness retreats convert more leads at lower cost.\"",
        "```",
        "",
        "## Samples + transcripts",
        "",
    ]
    for s in status["samples"]:
        lines.extend([
            f"### Sample {s['id']:02d} — {s['tone']}",
            "",
            f"**Transcript:** {s['text']}",
            "",
            f"**File:** `brand/_engine/voice-samples/sample-{s['id']:02d}.wav`",
            f"**Size:** {s['size_bytes']:,} bytes",
            "",
        ])
    lines.extend([
        "## Re-enrolling",
        "",
        "If voice characteristics change (accent shift, different recording setup, updated mic)",
        "re-run the wizard to refresh all 10 samples:",
        "",
        "```bash",
        "python3 visual-generator/scripts/enroll_voice.py --reset",
        "```",
        "",
        "## Cross-skill impact",
        "",
        "When samples are refreshed, existing cloned VOs remain valid (they were generated",
        "from older samples but already rendered to MP3). Only NEW VO generations after",
        "the refresh will use the updated voice.",
        "",
    ])
    voice_lock_path(brand).write_text("\n".join(lines), encoding="utf-8")
    return True


# ── HTML recorder page ─────────────────────────────────────────────────────

def render_page() -> str:
    sentences_json = json.dumps(ENROLLMENT_SENTENCES)
    return f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>Digischola Voice Enrollment</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;700&family=Orbitron:wght@600;900&family=Space+Grotesk:wght@500;700&display=swap" rel="stylesheet">
<style>
 * {{ box-sizing: border-box; }}
 html, body {{ margin: 0; padding: 0; background: {BG}; color: {TEXT}; font-family: 'Manrope', system-ui; }}
 .wrap {{ max-width: 820px; margin: 0 auto; padding: 40px 24px 80px; }}
 header {{ display: flex; align-items: center; justify-content: space-between; padding: 12px 0 28px; border-bottom: 1px solid {BORDER}; margin-bottom: 40px; }}
 h1 {{ font-family: 'Orbitron'; font-weight: 900; font-size: 20px; letter-spacing: 2px; margin: 0; background: linear-gradient(90deg, {PRIMARY}, #7ec5ff); -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent; }}
 .progress {{ font-family: 'Space Grotesk'; font-weight: 700; font-size: 14px; color: {MUTED}; }}
 .progress .cur {{ color: {PRIMARY}; font-size: 18px; }}
 .progress-bar {{ height: 4px; background: {BORDER}; border-radius: 2px; margin: 12px 0 0; overflow: hidden; }}
 .progress-bar .fill {{ height: 100%; background: linear-gradient(90deg, {PRIMARY}, #7ec5ff); transition: width 0.3s; }}

 .tone {{ font-family: 'Space Grotesk'; font-weight: 700; font-size: 11px; letter-spacing: 2.5px; color: {MUTED}; text-transform: uppercase; margin-bottom: 20px; }}
 .sentence-card {{ background: {CARD_BG}; border: 1px solid {BORDER}; border-radius: 18px; padding: 40px; margin-bottom: 24px; }}
 .sentence {{ font-family: 'Manrope'; font-size: 26px; line-height: 1.5; color: {TEXT}; font-weight: 500; }}

 .record-area {{ text-align: center; padding: 32px 0; }}
 .rec-btn {{ width: 140px; height: 140px; border-radius: 50%; border: 4px solid {PRIMARY}; background: transparent; color: {PRIMARY}; font-family: 'Space Grotesk'; font-weight: 700; font-size: 16px; cursor: pointer; display: inline-flex; align-items: center; justify-content: center; flex-direction: column; gap: 6px; transition: all 0.2s; }}
 .rec-btn:hover {{ background: rgba(59,158,255,0.08); transform: scale(1.03); }}
 .rec-btn.recording {{ border-color: {REC}; color: {REC}; background: rgba(239,68,68,0.08); animation: pulse 1.2s infinite; }}
 .rec-btn .dot {{ width: 22px; height: 22px; border-radius: 50%; background: {PRIMARY}; margin-bottom: 6px; }}
 .rec-btn.recording .dot {{ background: {REC}; }}
 @keyframes pulse {{ 0%,100% {{ box-shadow: 0 0 0 0 rgba(239,68,68,0.4); }} 50% {{ box-shadow: 0 0 0 18px rgba(239,68,68,0); }} }}

 .timer {{ font-family: 'Orbitron'; font-weight: 900; font-size: 36px; color: {TEXT}; margin-top: 16px; letter-spacing: 2px; min-height: 44px; }}
 .timer.warn {{ color: {REC}; }}

 .controls {{ display: flex; gap: 12px; justify-content: center; margin-top: 24px; min-height: 56px; }}
 .btn {{ padding: 14px 28px; border-radius: 10px; font-family: 'Space Grotesk'; font-weight: 700; font-size: 15px; cursor: pointer; border: 1px solid {BORDER}; background: transparent; color: {TEXT}; transition: all 0.15s; }}
 .btn:hover {{ border-color: {PRIMARY}; color: {PRIMARY}; }}
 .btn.primary {{ background: {PRIMARY}; border-color: {PRIMARY}; color: white; }}
 .btn.primary:hover {{ filter: brightness(1.1); color: white; }}
 .btn.ok {{ background: {OK}; border-color: {OK}; color: white; }}
 .btn.ok:hover {{ filter: brightness(1.1); color: white; }}
 .btn.ghost {{ background: transparent; }}
 .btn:disabled {{ opacity: 0.35; cursor: not-allowed; }}

 .status {{ font-family: 'Space Grotesk'; font-weight: 500; font-size: 14px; color: {MUTED}; text-align: center; margin-top: 14px; min-height: 20px; }}
 .status.ok {{ color: {OK}; }}
 .status.err {{ color: {REC}; }}

 .instructions {{ background: rgba(59,158,255,0.06); border: 1px solid rgba(59,158,255,0.25); border-left: 4px solid {PRIMARY}; border-radius: 10px; padding: 18px 22px; margin-bottom: 32px; }}
 .instructions h3 {{ margin: 0 0 10px; font-family: 'Space Grotesk'; font-size: 13px; text-transform: uppercase; letter-spacing: 1.5px; color: {PRIMARY}; }}
 .instructions ul {{ margin: 0; padding-left: 22px; line-height: 1.7; color: {TEXT}; font-size: 14px; }}

 .done-screen {{ text-align: center; padding: 80px 20px; }}
 .done-screen h2 {{ font-family: 'Orbitron'; font-size: 28px; background: linear-gradient(90deg, {PRIMARY}, #7ec5ff); -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent; margin: 0 0 18px; }}
 .done-screen p {{ color: {MUTED}; line-height: 1.7; font-size: 15px; max-width: 540px; margin: 0 auto 14px; }}

 audio {{ width: 100%; margin-top: 16px; }}
</style>
</head><body>
<div class="wrap">
  <header>
    <h1>DIGISCHOLA · VOICE ENROLLMENT</h1>
    <div class="progress"><span class="cur" id="done">0</span>/<span id="total">10</span> recorded</div>
  </header>
  <div class="progress-bar"><div class="fill" id="progress-fill" style="width:0%"></div></div>

  <div class="instructions">
    <h3>🎙 Before you start</h3>
    <ul>
      <li>Quiet room, no background music, no fan noise.</li>
      <li>Mic ~15cm from mouth. Built-in Mac mic is fine; AirPods also work.</li>
      <li>Read naturally, the way you'd say it to a client. Don't over-enunciate.</li>
      <li>Each clip should be 3-8 seconds. Re-record if you stumble.</li>
      <li>This is a one-time ~3 minute setup. Future Reel VOs use these samples.</li>
    </ul>
  </div>

  <div id="main">
    <div class="tone" id="tone-label"></div>
    <div class="sentence-card">
      <div class="sentence" id="sentence-text"></div>
    </div>

    <div class="record-area">
      <button class="rec-btn" id="rec-btn" onclick="toggleRecord()">
        <div class="dot"></div>
        <span id="rec-label">Record</span>
      </button>
      <div class="timer" id="timer"></div>
    </div>

    <div class="controls" id="controls"></div>
    <audio id="playback" controls style="display:none"></audio>
    <div class="status" id="status"></div>
  </div>

  <div class="done-screen" id="done-screen" style="display:none">
    <h2>✓ Voice enrollment complete</h2>
    <p>All 10 samples recorded + saved to <code>brand/_engine/voice-samples/</code>.</p>
    <p><code>brand/_engine/wiki/voice-lock.md</code> written. clone_voice.py can now generate Reel VOs in your voice.</p>
    <p style="margin-top:30px; color:{MUTED}; font-size:13px;">You can close this tab.</p>
  </div>
</div>

<script>
const SENTENCES = {sentences_json};
let currentIdx = 0;
let mediaRecorder = null;
let chunks = [];
let stream = null;
let blob = null;
let timerInterval = null;
let startTime = 0;
let recordedState = {{}};  // {{ id: true/false }}

async function loadStatus() {{
  const r = await fetch('/status');
  const d = await r.json();
  d.samples.forEach(s => {{ recordedState[s.id] = s.recorded; }});
  updateUI();
  // Jump to first un-recorded sentence
  const firstMissing = d.samples.findIndex(s => !s.recorded);
  currentIdx = firstMissing === -1 ? SENTENCES.length - 1 : firstMissing;
  loadSentence();
  if (d.done === SENTENCES.length) {{
    showDone();
  }}
}}

function updateUI() {{
  const done = Object.values(recordedState).filter(Boolean).length;
  document.getElementById('done').textContent = done;
  document.getElementById('progress-fill').style.width = (done / SENTENCES.length * 100) + '%';
}}

function loadSentence() {{
  const s = SENTENCES[currentIdx];
  document.getElementById('tone-label').textContent = `Sentence ${{s.id}} / 10 · ${{s.tone}}`;
  document.getElementById('sentence-text').textContent = s.text;
  document.getElementById('playback').style.display = 'none';
  document.getElementById('status').textContent = '';
  document.getElementById('status').className = 'status';
  blob = null;
  renderControls();
}}

function renderControls() {{
  const c = document.getElementById('controls');
  c.innerHTML = '';
  if (blob) {{
    const saveBtn = button('✓ Save & next', 'ok', () => saveAndNext());
    const reBtn = button('↻ Re-record', 'ghost', () => {{ blob = null; document.getElementById('playback').style.display = 'none'; renderControls(); }});
    c.appendChild(reBtn);
    c.appendChild(saveBtn);
  }} else {{
    if (currentIdx > 0) {{
      c.appendChild(button('← Previous', 'ghost', () => {{ currentIdx--; loadSentence(); }}));
    }}
    if (currentIdx < SENTENCES.length - 1) {{
      const nextBtn = button('Skip →', 'ghost', () => {{ currentIdx++; loadSentence(); }});
      if (!recordedState[SENTENCES[currentIdx].id]) {{
        // Nothing yet
      }}
      c.appendChild(nextBtn);
    }}
  }}
}}

function button(text, variant, onClick) {{
  const b = document.createElement('button');
  b.textContent = text;
  b.className = 'btn ' + variant;
  b.onclick = onClick;
  return b;
}}

async function toggleRecord() {{
  if (mediaRecorder && mediaRecorder.state === 'recording') {{
    stopRecord();
  }} else {{
    await startRecord();
  }}
}}

async function startRecord() {{
  try {{
    if (!stream) {{
      stream = await navigator.mediaDevices.getUserMedia({{ audio: {{ echoCancellation: true, noiseSuppression: true }} }});
    }}
    chunks = [];
    mediaRecorder = new MediaRecorder(stream, {{ mimeType: 'audio/webm' }});
    mediaRecorder.ondataavailable = e => {{ if (e.data.size > 0) chunks.push(e.data); }};
    mediaRecorder.onstop = () => {{
      blob = new Blob(chunks, {{ type: 'audio/webm' }});
      const url = URL.createObjectURL(blob);
      const audio = document.getElementById('playback');
      audio.src = url;
      audio.style.display = 'block';
      document.getElementById('rec-btn').classList.remove('recording');
      document.getElementById('rec-label').textContent = 'Record';
      clearInterval(timerInterval);
      document.getElementById('timer').classList.remove('warn');
      renderControls();
      setStatus('Preview + Save. Or re-record.', 'ok');
    }};
    mediaRecorder.start();
    document.getElementById('rec-btn').classList.add('recording');
    document.getElementById('rec-label').textContent = 'Stop';
    startTime = Date.now();
    timerInterval = setInterval(updateTimer, 100);
    setStatus('Recording... speak now.');
  }} catch (e) {{
    setStatus('Mic permission denied: ' + e.message, 'err');
  }}
}}

function stopRecord() {{
  if (mediaRecorder && mediaRecorder.state === 'recording') {{
    mediaRecorder.stop();
  }}
}}

function updateTimer() {{
  const elapsed = (Date.now() - startTime) / 1000;
  document.getElementById('timer').textContent = elapsed.toFixed(1) + 's';
  if (elapsed > 12) document.getElementById('timer').classList.add('warn');
}}

async function saveAndNext() {{
  setStatus('Uploading + converting to WAV...');
  const fd = new FormData();
  fd.append('audio', blob, 'sample.webm');
  const s = SENTENCES[currentIdx];
  fd.append('transcript', s.text);
  try {{
    const r = await fetch('/sample/' + s.id, {{ method: 'POST', body: fd }});
    const d = await r.json();
    if (!d.ok) throw new Error(d.error || 'unknown error');
    recordedState[s.id] = true;
    updateUI();
    setStatus('✓ Sample saved (' + d.size_bytes + ' bytes WAV)', 'ok');
    // Check if all done
    if (Object.values(recordedState).filter(Boolean).length === SENTENCES.length) {{
      const doneRes = await fetch('/done', {{ method: 'POST' }});
      await doneRes.json();
      showDone();
      return;
    }}
    // Advance
    setTimeout(() => {{
      if (currentIdx < SENTENCES.length - 1) {{
        currentIdx++;
      }}
      loadSentence();
    }}, 800);
  }} catch (e) {{
    setStatus('Save failed: ' + e.message, 'err');
  }}
}}

function setStatus(msg, cls = '') {{
  const el = document.getElementById('status');
  el.textContent = msg;
  el.className = 'status ' + cls;
}}

function showDone() {{
  document.getElementById('main').style.display = 'none';
  document.getElementById('done-screen').style.display = 'block';
  fetch('/shutdown', {{ method: 'POST' }}).catch(() => {{}});
}}

document.getElementById('total').textContent = SENTENCES.length;
loadStatus();
</script>
</body></html>"""


# ── HTTP handler ───────────────────────────────────────────────────────────

class EnrollHandler(BaseHTTPRequestHandler):
    brand: Path = None
    done_event: threading.Event = None

    def log_message(self, fmt, *a):
        pass

    def _json(self, code: int, obj: dict):
        data = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/" or self.path == "":
            page = render_page().encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(page)))
            self.end_headers()
            self.wfile.write(page)
        elif self.path == "/status":
            self._json(200, enrollment_status(self.brand))
        elif self.path == "/favicon.ico":
            self.send_response(204); self.end_headers()
        else:
            self.send_response(404); self.end_headers()

    def do_POST(self):
        if self.path.startswith("/sample/"):
            try:
                idx = int(self.path.split("/")[-1])
            except Exception:
                self._json(400, {"ok": False, "error": "bad index"}); return
            self._handle_sample(idx)
            return
        if self.path == "/done":
            ok = write_voice_lock(self.brand)
            self._json(200, {"ok": ok, "voice_lock_written": ok})
            return
        if self.path == "/shutdown":
            self._json(200, {"ok": True})
            if self.done_event:
                threading.Timer(0.5, self.done_event.set).start()
            return
        self.send_response(404); self.end_headers()

    def _handle_sample(self, idx: int):
        # Parse multipart form data. BaseHTTPRequestHandler doesn't do this for us.
        # Minimal parser: find Content-Type boundary, split, extract "audio" field.
        ctype = self.headers.get("Content-Type", "")
        if "multipart/form-data" not in ctype or "boundary=" not in ctype:
            self._json(400, {"ok": False, "error": "expected multipart"}); return
        boundary = ctype.split("boundary=", 1)[1].encode("utf-8")
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        parts = body.split(b"--" + boundary)
        audio_bytes = None
        for part in parts:
            if b"Content-Disposition" in part and b'name="audio"' in part:
                head, _, content = part.partition(b"\r\n\r\n")
                audio_bytes = content.rstrip(b"\r\n--")
                break
        if not audio_bytes:
            self._json(400, {"ok": False, "error": "no audio field"}); return

        # Save raw webm + convert to wav
        samples_dir = voice_samples_dir(self.brand)
        samples_dir.mkdir(parents=True, exist_ok=True)
        webm_path = samples_dir / f"sample-{idx:02d}.webm"
        wav_path = samples_dir / f"sample-{idx:02d}.wav"
        webm_path.write_bytes(audio_bytes)

        # ffmpeg: convert webm → wav, 24kHz mono (F5-TTS prefers 24kHz)
        try:
            subprocess.run([
                "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                "-i", str(webm_path),
                "-ar", "24000", "-ac", "1",
                str(wav_path),
            ], check=True, timeout=30)
        except subprocess.CalledProcessError as e:
            self._json(500, {"ok": False, "error": f"ffmpeg failed: {e}"}); return
        except FileNotFoundError:
            self._json(500, {"ok": False, "error": "ffmpeg not found. brew install ffmpeg."}); return

        webm_path.unlink(missing_ok=True)  # keep only wav
        self._json(200, {
            "ok": True,
            "path": str(wav_path),
            "size_bytes": wav_path.stat().st_size,
        })


# ── Main ───────────────────────────────────────────────────────────────────

def cmd_status(brand: Path):
    s = enrollment_status(brand)
    print(f"\nVoice enrollment state (brand: {brand})\n")
    print(f"  Recorded: {s['done']} / {s['total']}")
    print(f"  Samples dir: {voice_samples_dir(brand)}")
    print(f"  voice-lock.md: {'✓ exists' if s['voice_lock_exists'] else '✗ missing'}")
    print()
    for r in s["samples"]:
        mark = "✓" if r["recorded"] else "·"
        size = f"{r['size_bytes']:,} bytes" if r["recorded"] else "(not yet)"
        print(f"  [{mark}] {r['id']:02d}  {r['tone'][:40]:40}  {size}")
    print()


def cmd_reset(brand: Path):
    samples_dir = voice_samples_dir(brand)
    if samples_dir.exists():
        shutil.rmtree(samples_dir)
        print(f"Removed: {samples_dir}")
    lock = voice_lock_path(brand)
    if lock.exists():
        lock.unlink()
        print(f"Removed: {lock}")
    print("Reset complete.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--brand-folder", type=Path, default=DEFAULT_BRAND)
    ap.add_argument("--port", type=int, default=8766)
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--reset", action="store_true")
    ap.add_argument("--no-open", action="store_true")
    args = ap.parse_args()

    if args.status:
        cmd_status(args.brand_folder); return
    if args.reset:
        cmd_reset(args.brand_folder); return

    voice_samples_dir(args.brand_folder).mkdir(parents=True, exist_ok=True)

    EnrollHandler.brand = args.brand_folder
    done_event = threading.Event()
    EnrollHandler.done_event = done_event

    try:
        server = HTTPServer(("127.0.0.1", args.port), EnrollHandler)
    except OSError as e:
        sys.exit(f"Port {args.port} in use. Try --port 8767. ({e})")

    threading.Thread(target=server.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{args.port}/"
    print(f"Voice enrollment UI: {url}")

    # Notify + open
    subprocess.run(["osascript", "-e",
                    'display notification "Open in Chrome to record 10 samples (~3 min)" '
                    'with title "Voice enrollment ready" sound name "Glass"'],
                   capture_output=True, timeout=5)

    if not args.no_open:
        webbrowser.open(url)

    print("Waiting for enrollment to complete (or Ctrl+C to exit)...")
    try:
        done_event.wait()
        print("\n✓ Enrollment complete. voice-lock.md written.")
    except KeyboardInterrupt:
        print("\nInterrupted.")
    finally:
        server.shutdown()
        s = enrollment_status(args.brand_folder)
        print(f"Final state: {s['done']}/{s['total']} samples recorded.")


if __name__ == "__main__":
    main()
