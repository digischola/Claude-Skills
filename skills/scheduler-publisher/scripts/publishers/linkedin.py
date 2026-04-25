#!/usr/bin/env python3
"""
LinkedIn publisher — UGC API.

Handles:
- Text posts (`format: text-post`)
- Single image posts (`format: image-post`, asset = single PNG/JPG)
- Carousel posts via DOCUMENT media (slide PNGs auto-stitched into a PDF)
- Video posts (Reels-equivalent: native LinkedIn video)

API reference: https://learn.microsoft.com/en-us/linkedin/consumer/integrations/self-serve/share-on-linkedin
              https://learn.microsoft.com/en-us/linkedin/marketing/integrations/community-management/shares/posts-api

Auth: OAuth2 access token from setup_channel.py linkedin (stored in Keychain).
Refresh: handled by `refresh_token_if_needed()` — called automatically before each publish.

Returns a `PublishResult(status, url, reason)`.
"""

from __future__ import annotations

import io
import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

try:
    import requests
except ImportError:
    sys.exit("requests not installed. Run: pip3 install requests")

# Allow direct invocation via `python3 publishers/linkedin.py ...`
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import token_store  # noqa: E402


API_BASE = "https://api.linkedin.com"
# LinkedIn versions monthly (YYYYMM). They keep ~12-15 months of versions live.
# When you see HTTP 426 NONEXISTENT_VERSION, bump this to current calendar month.
# As of 2026-04: 202604 is active; 202402 was sunset.
API_VERSION = "202604"
USER_AGENT = "DigischolaScheduler/1.0"


@dataclass
class PublishResult:
    status: str         # "posted" | "failed" | "retry_due"
    url: Optional[str] = None
    reason: Optional[str] = None
    retry_after_sec: int = 0


# ── Token refresh ─────────────────────────────────────────────────────────


def refresh_token_if_needed() -> bool:
    """Refresh the LinkedIn access token if it's expiring within 7 days.
    Returns True if refresh happened or token is still fresh; False if refresh failed."""
    if not token_store.is_token_expiring_soon("linkedin", days=7):
        return True
    refresh_token = token_store.get("linkedin_refresh_token")
    client_id = token_store.get("linkedin_client_id")
    client_secret = token_store.get("linkedin_client_secret")
    if not all([refresh_token, client_id, client_secret]):
        return False
    r = requests.post(
        f"{API_BASE}/oauth/v2/accessToken",
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": client_id,
            "client_secret": client_secret,
        },
        timeout=15,
    )
    if r.status_code != 200:
        return False
    body = r.json()
    token_store.put("linkedin_access_token", body["access_token"])
    if "refresh_token" in body:
        token_store.put("linkedin_refresh_token", body["refresh_token"])
    token_store.set_expires_at("linkedin", body.get("expires_in", 5184000))
    return True


# ── Helpers ───────────────────────────────────────────────────────────────


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {token_store.get('linkedin_access_token')}",
        "X-Restli-Protocol-Version": "2.0.0",
        "LinkedIn-Version": API_VERSION,
        "User-Agent": USER_AGENT,
        "Content-Type": "application/json",
    }


def _person_urn() -> str:
    urn = token_store.get("linkedin_person_urn")
    if not urn:
        raise RuntimeError("linkedin_person_urn missing in Keychain — run setup_channel.py linkedin")
    return urn


def _post_url_from_response(response_json: dict) -> Optional[str]:
    """LinkedIn returns the activity URN in the response body or X-RestLi-Id header."""
    activity_urn = response_json.get("id") or response_json.get("activityUrn")
    if not activity_urn:
        return None
    # Convert urn:li:share:... or urn:li:ugcPost:... to a feed URL
    # Public format: https://www.linkedin.com/feed/update/urn:li:activity:xxxxxxxxxx
    return f"https://www.linkedin.com/feed/update/{activity_urn}"


def _classify_error(status: int, body: str) -> tuple[str, int]:
    """Map an HTTP error to (reason, retry_after_sec). retry_after_sec=0 means no retry."""
    if status == 401:
        return ("token_expired", 5)  # retry once after refresh
    if status == 403:
        return ("forbidden_or_scope", 0)
    if status == 429:
        return ("rate_limited", 3600)
    if status == 422:
        return ("malformed_payload", 0)
    if status >= 500:
        return ("server_error", 60)
    return (f"http_{status}", 30)


# ── Asset upload (image) ──────────────────────────────────────────────────


def _register_image_upload() -> tuple[str, str]:
    """Returns (uploadUrl, imageUrn)."""
    r = requests.post(
        f"{API_BASE}/rest/images?action=initializeUpload",
        headers=_headers(),
        json={"initializeUploadRequest": {"owner": _person_urn()}},
        timeout=15,
    )
    r.raise_for_status()
    body = r.json()["value"]
    return body["uploadUrl"], body["image"]


def _upload_image_binary(upload_url: str, image_path: Path) -> None:
    with open(image_path, "rb") as f:
        r = requests.put(
            upload_url,
            data=f.read(),
            headers={"Authorization": f"Bearer {token_store.get('linkedin_access_token')}"},
            timeout=60,
        )
    r.raise_for_status()


def upload_image(image_path: Path) -> str:
    """Upload an image. Returns the LinkedIn image URN (urn:li:image:...)."""
    upload_url, image_urn = _register_image_upload()
    _upload_image_binary(upload_url, image_path)
    return image_urn


# ── Asset upload (video) ──────────────────────────────────────────────────


def _register_video_upload(file_size_bytes: int) -> tuple[list[dict], str]:
    """Returns (upload_instructions, videoUrn). LinkedIn video uses chunked upload."""
    r = requests.post(
        f"{API_BASE}/rest/videos?action=initializeUpload",
        headers=_headers(),
        json={
            "initializeUploadRequest": {
                "owner": _person_urn(),
                "fileSizeBytes": file_size_bytes,
                "uploadCaptions": False,
                "uploadThumbnail": False,
            }
        },
        timeout=15,
    )
    r.raise_for_status()
    body = r.json()["value"]
    return body["uploadInstructions"], body["video"]


def upload_video(video_path: Path) -> str:
    """Upload a video in chunks. Returns the LinkedIn video URN."""
    file_size = video_path.stat().st_size
    instructions, video_urn = _register_video_upload(file_size)
    upload_token_etags = []
    with open(video_path, "rb") as f:
        for instr in instructions:
            url = instr["uploadUrl"]
            first = instr["firstByte"]
            last = instr["lastByte"]
            f.seek(first)
            chunk = f.read(last - first + 1)
            r = requests.put(url, data=chunk, headers={
                "Content-Type": "application/octet-stream",
            }, timeout=120)
            r.raise_for_status()
            etag = r.headers.get("ETag")
            if etag:
                upload_token_etags.append(etag)
    # Finalize
    r = requests.post(
        f"{API_BASE}/rest/videos?action=finalizeUpload",
        headers=_headers(),
        json={
            "finalizeUploadRequest": {
                "video": video_urn,
                "uploadToken": "",
                "uploadedPartIds": upload_token_etags,
            }
        },
        timeout=15,
    )
    r.raise_for_status()
    return video_urn


# ── Carousel: slide PNGs → single PDF ─────────────────────────────────────


def stitch_carousel_pdf(slide_paths: list[Path], output_pdf: Path) -> Path:
    """Combine a list of square/portrait slide PNGs into a single PDF (one page per slide)."""
    try:
        from PIL import Image
    except ImportError:
        sys.exit("Pillow not installed. Run: pip3 install Pillow")
    images = []
    for p in slide_paths:
        img = Image.open(p)
        if img.mode != "RGB":
            img = img.convert("RGB")
        images.append(img)
    if not images:
        raise ValueError("No slides to stitch")
    images[0].save(
        output_pdf,
        save_all=True,
        append_images=images[1:],
        format="PDF",
        resolution=150.0,
    )
    return output_pdf


def upload_document(pdf_path: Path, title: str) -> str:
    """Upload a PDF as a LinkedIn document (used for native carousel)."""
    r = requests.post(
        f"{API_BASE}/rest/documents?action=initializeUpload",
        headers=_headers(),
        json={
            "initializeUploadRequest": {
                "owner": _person_urn(),
            }
        },
        timeout=15,
    )
    r.raise_for_status()
    body = r.json()["value"]
    upload_url = body["uploadUrl"]
    document_urn = body["document"]
    with open(pdf_path, "rb") as f:
        r = requests.put(
            upload_url,
            data=f.read(),
            headers={"Authorization": f"Bearer {token_store.get('linkedin_access_token')}"},
            timeout=60,
        )
    r.raise_for_status()
    return document_urn


# ── Post payload builders ─────────────────────────────────────────────────


def _build_text_post(commentary: str) -> dict:
    return {
        "author": _person_urn(),
        "commentary": commentary,
        "visibility": "PUBLIC",
        "distribution": {
            "feedDistribution": "MAIN_FEED",
            "targetEntities": [],
            "thirdPartyDistributionChannels": [],
        },
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False,
    }


def _build_image_post(commentary: str, image_urn: str, alt_text: str = "") -> dict:
    base = _build_text_post(commentary)
    base["content"] = {"media": {"id": image_urn, "altText": alt_text or "Digischola image"}}
    return base


def _build_video_post(commentary: str, video_urn: str, title: str = "") -> dict:
    base = _build_text_post(commentary)
    base["content"] = {"media": {"id": video_urn, "title": title or "Digischola"}}
    return base


def _build_document_post(commentary: str, document_urn: str, title: str) -> dict:
    base = _build_text_post(commentary)
    base["content"] = {"media": {"id": document_urn, "title": title}}
    return base


# ── Main publish entry points ─────────────────────────────────────────────


def publish_text(commentary: str) -> PublishResult:
    return _publish(_build_text_post(commentary))


def publish_image(commentary: str, image_path: Path, alt_text: str = "") -> PublishResult:
    image_urn = upload_image(image_path)
    return _publish(_build_image_post(commentary, image_urn, alt_text))


def publish_video(commentary: str, video_path: Path, title: str = "") -> PublishResult:
    video_urn = upload_video(video_path)
    # LinkedIn needs ~30s to process video before it's postable
    time.sleep(30)
    return _publish(_build_video_post(commentary, video_urn, title))


def publish_carousel(commentary: str, slide_paths: list[Path], title: str = "Carousel") -> PublishResult:
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        pdf_path = Path(tmp.name)
    try:
        stitch_carousel_pdf(slide_paths, pdf_path)
        document_urn = upload_document(pdf_path, title)
        return _publish(_build_document_post(commentary, document_urn, title))
    finally:
        pdf_path.unlink(missing_ok=True)


def _publish(payload: dict) -> PublishResult:
    if not refresh_token_if_needed():
        return PublishResult(status="failed", reason="token_refresh_failed")
    r = requests.post(
        f"{API_BASE}/rest/posts",
        headers=_headers(),
        json=payload,
        timeout=30,
    )
    if r.status_code in (200, 201):
        # Some endpoints return the URN in the X-RestLi-Id header rather than body
        body = r.json() if r.text else {}
        urn = body.get("id") or r.headers.get("X-RestLi-Id")
        url = f"https://www.linkedin.com/feed/update/{urn}" if urn else None
        return PublishResult(status="posted", url=url)
    reason, retry_after = _classify_error(r.status_code, r.text)
    if retry_after > 0:
        return PublishResult(status="retry_due", reason=f"{reason}: {r.text[:200]}", retry_after_sec=retry_after)
    return PublishResult(status="failed", reason=f"{reason}: {r.text[:200]}")


# ── Dispatch from a draft ─────────────────────────────────────────────────


def publish_draft(fm: dict, body: str, brand_folder: Path) -> PublishResult:
    """Dispatch a draft to the right LinkedIn publish path based on `format`."""
    fmt = fm.get("format", "text-post")
    commentary = body.strip()
    assets_dir = fm.get("visual_assets_dir") or fm.get("visual_assets_dir_anim") or fm.get("visual_assets_dir_reel_v2")

    if fmt == "text-post":
        return publish_text(commentary)

    if not assets_dir:
        # No assets — fall back to text post even if format expected media
        return publish_text(commentary)

    assets_path = brand_folder / assets_dir if not Path(assets_dir).is_absolute() else Path(assets_dir)

    if fmt in ("video-post", "reel"):
        # Look for the rendered MP4
        for name in ("reel.mp4", "animated.mp4", "video.mp4"):
            video = assets_path / name
            if video.exists():
                return publish_video(commentary, video, title=fm.get("entry_id", "Digischola"))
        return PublishResult(status="failed", reason=f"no MP4 found in {assets_path}")

    if fmt in ("carousel", "image-carousel", "carousel-slides"):
        slides = sorted(assets_path.glob("slide-*.png"))
        if not slides:
            return PublishResult(status="failed", reason=f"no slide-*.png in {assets_path}")
        return publish_carousel(commentary, slides, title=fm.get("entry_id", "Carousel"))

    if fmt in ("image-post", "quote-card"):
        for name in ("quote.png", "image.png", "card.png"):
            img = assets_path / name
            if img.exists():
                return publish_image(commentary, img)
        # Fall back to first PNG in folder
        pngs = sorted(assets_path.glob("*.png"))
        if pngs:
            return publish_image(commentary, pngs[0])
        return PublishResult(status="failed", reason=f"no image found in {assets_path}")

    # Unknown format — text fallback
    return publish_text(commentary)
