#!/usr/bin/env python3
"""
X (Twitter) publisher — API v2.

Handles:
- Single tweets (`format: x-single` or `format: text-post`)
- Threads (`format: x-thread` — multiple tweets chained via in_reply_to)
- Image attachments (up to 4 per tweet)
- Video attachments (single video per tweet, MP4 ≤140MB)

Auth: OAuth2 user context (from setup_channel.py x).
Media upload: still uses v1.1 endpoint (the only path X provides for binary media), then
references media_id in v2 tweet payload.
"""

from __future__ import annotations

import json
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

try:
    import requests
except ImportError:
    sys.exit("requests not installed. Run: pip3 install requests")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import token_store  # noqa: E402


API_V2 = "https://api.twitter.com/2"
API_V1_MEDIA = "https://upload.twitter.com/1.1"
TWEET_CHAR_LIMIT = 280


@dataclass
class PublishResult:
    status: str
    url: Optional[str] = None
    reason: Optional[str] = None
    retry_after_sec: int = 0


# ── Token refresh ─────────────────────────────────────────────────────────


def refresh_token_if_needed() -> bool:
    """X access tokens last 2h. Refresh if within 10 min of expiry."""
    if not token_store.is_token_expiring_soon("x", days=0):
        # is_token_expiring_soon with days=0 still returns True if past expiry; flip to "fresh enough"
        from datetime import datetime, timezone, timedelta
        exp = token_store.get_expires_at("x")
        if exp and (exp - datetime.now(timezone.utc)) > timedelta(minutes=10):
            return True
    refresh_token = token_store.get("x_refresh_token")
    client_id = token_store.get("x_client_id")
    if not refresh_token or not client_id:
        return False
    # X uses Basic auth with client_id:client_secret OR public client_id only for PKCE flow
    client_secret = token_store.get("x_client_secret")
    auth = (client_id, client_secret) if client_secret else None
    r = requests.post(
        "https://api.twitter.com/2/oauth2/token",
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": client_id,
        },
        auth=auth,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=15,
    )
    if r.status_code != 200:
        return False
    body = r.json()
    token_store.put("x_access_token", body["access_token"])
    if "refresh_token" in body:
        token_store.put("x_refresh_token", body["refresh_token"])
    token_store.set_expires_at("x", body.get("expires_in", 7200))
    return True


# ── Helpers ───────────────────────────────────────────────────────────────


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {token_store.get('x_access_token')}",
        "Content-Type": "application/json",
    }


def _classify_error(status: int, body: str) -> tuple[str, int]:
    if status == 401:
        return ("token_expired", 5)
    if status == 403:
        if "duplicate" in body.lower():
            return ("duplicate_content", 0)  # no retry
        return ("forbidden", 0)
    if status == 429:
        # Reset at next IST midnight; conservatively wait 1h
        return ("rate_limited", 3600)
    if status == 400:
        return ("bad_request", 0)
    if status >= 500:
        return ("server_error", 60)
    return (f"http_{status}", 30)


def _tweet_url(user_screen_name: str, tweet_id: str) -> str:
    handle = user_screen_name or "i"
    return f"https://x.com/{handle}/status/{tweet_id}"


# ── Media upload (v1.1, chunked for video) ────────────────────────────────


def upload_image(image_path: Path) -> str:
    """Upload an image (PNG/JPG, ≤5MB). Returns media_id_string."""
    with open(image_path, "rb") as f:
        files = {"media": f.read()}
    r = requests.post(
        f"{API_V1_MEDIA}/media/upload.json",
        headers={"Authorization": f"Bearer {token_store.get('x_access_token')}"},
        files={"media": files["media"]},
        timeout=60,
    )
    r.raise_for_status()
    return r.json()["media_id_string"]


def upload_video(video_path: Path) -> str:
    """Upload a video via chunked v1.1 INIT → APPEND → FINALIZE flow."""
    file_size = video_path.stat().st_size
    auth_header = {"Authorization": f"Bearer {token_store.get('x_access_token')}"}

    # INIT
    r = requests.post(
        f"{API_V1_MEDIA}/media/upload.json",
        headers=auth_header,
        data={
            "command": "INIT",
            "total_bytes": str(file_size),
            "media_type": "video/mp4",
            "media_category": "tweet_video",
        },
        timeout=15,
    )
    r.raise_for_status()
    media_id = r.json()["media_id_string"]

    # APPEND (1MB chunks)
    chunk_size = 1024 * 1024
    seg = 0
    with open(video_path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            r = requests.post(
                f"{API_V1_MEDIA}/media/upload.json",
                headers=auth_header,
                data={
                    "command": "APPEND",
                    "media_id": media_id,
                    "segment_index": str(seg),
                },
                files={"media": chunk},
                timeout=60,
            )
            r.raise_for_status()
            seg += 1

    # FINALIZE
    r = requests.post(
        f"{API_V1_MEDIA}/media/upload.json",
        headers=auth_header,
        data={"command": "FINALIZE", "media_id": media_id},
        timeout=30,
    )
    r.raise_for_status()
    info = r.json()

    # If processing_info is present, poll until succeeded
    if "processing_info" in info:
        for _ in range(20):  # up to ~3 min
            state = info.get("processing_info", {}).get("state")
            if state == "succeeded":
                break
            if state == "failed":
                raise RuntimeError(f"X video processing failed: {info}")
            wait = info.get("processing_info", {}).get("check_after_secs", 5)
            time.sleep(min(wait, 15))
            r = requests.get(
                f"{API_V1_MEDIA}/media/upload.json",
                headers=auth_header,
                params={"command": "STATUS", "media_id": media_id},
                timeout=15,
            )
            r.raise_for_status()
            info = r.json()
    return media_id


# ── Tweet posting ─────────────────────────────────────────────────────────


def _post_tweet(text: str, media_ids: Optional[list[str]] = None,
                in_reply_to_id: Optional[str] = None) -> tuple[str, str]:
    """POST one tweet. Returns (tweet_id, url)."""
    payload: dict = {"text": text}
    if media_ids:
        payload["media"] = {"media_ids": media_ids}
    if in_reply_to_id:
        payload["reply"] = {"in_reply_to_tweet_id": in_reply_to_id}
    r = requests.post(f"{API_V2}/tweets", headers=_headers(), json=payload, timeout=30)
    if r.status_code not in (200, 201):
        reason, retry_after = _classify_error(r.status_code, r.text)
        if retry_after > 0:
            raise _RetryableError(reason, retry_after, r.text[:200])
        raise _PermanentError(reason, r.text[:200])
    body = r.json()
    tweet_id = body["data"]["id"]
    handle = token_store.get("x_screen_name") or "i"
    return tweet_id, _tweet_url(handle, tweet_id)


class _RetryableError(Exception):
    def __init__(self, reason, retry_after, detail):
        self.reason = reason
        self.retry_after = retry_after
        self.detail = detail


class _PermanentError(Exception):
    def __init__(self, reason, detail):
        self.reason = reason
        self.detail = detail


# ── Thread splitting ──────────────────────────────────────────────────────


def split_thread(body: str) -> list[str]:
    """Split body into thread tweets. Recognizes `## Tweet N` headers from post-writer
    output, otherwise paragraph-splits keeping each chunk under TWEET_CHAR_LIMIT."""
    tweet_blocks = re.split(r"^##\s+Tweet\s+\d+[^\n]*\n", body, flags=re.MULTILINE)
    if len(tweet_blocks) > 1:
        return [b.strip() for b in tweet_blocks if b.strip()]

    # Fallback: paragraph-pack into ≤280-char chunks
    paragraphs = [p.strip() for p in body.split("\n\n") if p.strip()]
    chunks = []
    cur = ""
    for p in paragraphs:
        candidate = (cur + "\n\n" + p).strip() if cur else p
        if len(candidate) <= TWEET_CHAR_LIMIT:
            cur = candidate
        else:
            if cur:
                chunks.append(cur)
            if len(p) <= TWEET_CHAR_LIMIT:
                cur = p
            else:
                # Paragraph too long for one tweet — sentence-split
                for sent in re.split(r"(?<=[.!?])\s+", p):
                    if len(cur) + len(sent) + 1 <= TWEET_CHAR_LIMIT:
                        cur = (cur + " " + sent).strip()
                    else:
                        if cur:
                            chunks.append(cur)
                        cur = sent[:TWEET_CHAR_LIMIT]
    if cur:
        chunks.append(cur)
    return chunks


# ── Main publish entry points ─────────────────────────────────────────────


def publish_single(text: str, media_ids: Optional[list[str]] = None) -> PublishResult:
    if not refresh_token_if_needed():
        return PublishResult(status="failed", reason="token_refresh_failed")
    try:
        tid, url = _post_tweet(text, media_ids=media_ids)
        return PublishResult(status="posted", url=url)
    except _RetryableError as e:
        return PublishResult(status="retry_due", reason=f"{e.reason}: {e.detail}",
                             retry_after_sec=e.retry_after)
    except _PermanentError as e:
        return PublishResult(status="failed", reason=f"{e.reason}: {e.detail}")


def publish_thread(tweets: list[str]) -> PublishResult:
    """Post a chained thread. Returns URL of first tweet."""
    if not refresh_token_if_needed():
        return PublishResult(status="failed", reason="token_refresh_failed")
    try:
        first_id, first_url = _post_tweet(tweets[0])
        prev_id = first_id
        for t in tweets[1:]:
            tid, _ = _post_tweet(t, in_reply_to_id=prev_id)
            prev_id = tid
        return PublishResult(status="posted", url=first_url)
    except _RetryableError as e:
        return PublishResult(status="retry_due", reason=f"{e.reason}: {e.detail}",
                             retry_after_sec=e.retry_after)
    except _PermanentError as e:
        return PublishResult(status="failed", reason=f"{e.reason}: {e.detail}")


# ── Dispatch from a draft ─────────────────────────────────────────────────


def publish_draft(fm: dict, body: str, brand_folder: Path) -> PublishResult:
    fmt = fm.get("format", "text-post")
    assets_dir = fm.get("visual_assets_dir") or fm.get("visual_assets_dir_anim") or fm.get("visual_assets_dir_reel_v2")
    assets_path = (brand_folder / assets_dir) if (assets_dir and not Path(assets_dir).is_absolute()) else (Path(assets_dir) if assets_dir else None)

    # Thread first
    if fmt in ("x-thread", "thread"):
        tweets = split_thread(body)
        return publish_thread(tweets)

    # Single tweet (with optional media)
    text = body.strip()
    if len(text) > TWEET_CHAR_LIMIT:
        # Force-split into thread
        tweets = split_thread(text)
        return publish_thread(tweets)

    media_ids: list[str] = []
    if assets_path and assets_path.exists():
        # Video first
        for name in ("reel.mp4", "animated.mp4", "video.mp4"):
            video = assets_path / name
            if video.exists():
                try:
                    media_ids.append(upload_video(video))
                except Exception as e:
                    return PublishResult(status="failed", reason=f"video_upload: {e}")
                break
        else:
            # Up to 4 images
            slides = sorted(assets_path.glob("slide-*.png"))[:4]
            if not slides:
                slides = sorted(assets_path.glob("*.png"))[:4]
            for img in slides:
                try:
                    media_ids.append(upload_image(img))
                except Exception as e:
                    return PublishResult(status="failed", reason=f"image_upload: {e}")
    return publish_single(text, media_ids=media_ids or None)
