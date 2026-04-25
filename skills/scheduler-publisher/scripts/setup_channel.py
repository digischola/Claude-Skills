#!/usr/bin/env python3
"""
One-time channel setup wizards.

Guides the user through OAuth flow for LinkedIn and X, then stores tokens in
macOS Keychain.

Usage:
  python3 setup_channel.py linkedin
  python3 setup_channel.py x
  python3 setup_channel.py linkedin --verify       # post a test then delete
  python3 setup_channel.py x --verify
  python3 setup_channel.py --reset linkedin        # nuke Keychain entries
  python3 setup_channel.py --reset all
"""

from __future__ import annotations

import argparse
import base64
import getpass
import hashlib
import http.server
import secrets
import socketserver
import sys
import time
import urllib.parse
import webbrowser
from datetime import datetime, timezone, timedelta
from pathlib import Path
from threading import Thread

try:
    import requests
except ImportError:
    sys.exit("requests not installed. Run: pip3 install requests")

sys.path.insert(0, str(Path(__file__).resolve().parent))
import token_store

REDIRECT_PORT = 8765
REDIRECT_URI = f"http://localhost:{REDIRECT_PORT}/callback"


# ── PKCE helper ───────────────────────────────────────────────────────────


def make_pkce_pair() -> tuple[str, str]:
    """Return (verifier, challenge) for PKCE."""
    verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode().rstrip("=")
    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode()).digest()
    ).decode().rstrip("=")
    return verifier, challenge


# ── Local OAuth callback server ───────────────────────────────────────────


class _OAuthCallbackHandler(http.server.BaseHTTPRequestHandler):
    captured_query = None

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path != "/callback":
            self.send_response(404)
            self.end_headers()
            return
        params = dict(urllib.parse.parse_qsl(parsed.query))
        _OAuthCallbackHandler.captured_query = params
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(b"""<!DOCTYPE html>
<html><head><title>Digischola Scheduler</title>
<style>body{font-family:system-ui;padding:60px;background:#000;color:#F8FAFC;text-align:center}
h1{color:#3B9EFF;font-family:'Courier New';letter-spacing:0.1em}
p{color:#9BA8B9}</style></head>
<body><h1>OAUTH OK</h1><p>Token captured. You can close this tab and return to the terminal.</p></body></html>""")

    def log_message(self, *a, **kw):
        pass


def wait_for_callback(timeout: int = 300) -> dict:
    """Run the local server until /callback is hit or timeout. Returns the query params."""
    httpd = socketserver.TCPServer(("127.0.0.1", REDIRECT_PORT), _OAuthCallbackHandler)
    _OAuthCallbackHandler.captured_query = None

    def serve():
        try:
            httpd.serve_forever()
        except Exception:
            pass

    t = Thread(target=serve, daemon=True)
    t.start()
    deadline = time.time() + timeout
    try:
        while time.time() < deadline:
            if _OAuthCallbackHandler.captured_query is not None:
                return _OAuthCallbackHandler.captured_query
            time.sleep(0.1)
        raise TimeoutError("OAuth callback timeout (5 min)")
    finally:
        httpd.shutdown()
        httpd.server_close()


# ── LinkedIn ──────────────────────────────────────────────────────────────


def setup_linkedin():
    print("\n=== LinkedIn OAuth Setup ===\n")
    print("Prerequisites (per references/linkedin-api-setup.md):")
    print("  - LinkedIn Developer app exists at developer.linkedin.com/apps")
    print("  - Redirect URI is set to:", REDIRECT_URI)
    print("  - Products enabled: Sign In with LinkedIn (OIDC) + Share on LinkedIn")
    print()
    client_id = input("LinkedIn Client ID: ").strip()
    if not client_id:
        sys.exit("Empty Client ID; aborting.")
    client_secret = getpass.getpass("LinkedIn Client Secret (hidden): ").strip()
    if not client_secret:
        sys.exit("Empty Client Secret; aborting.")

    token_store.put("linkedin_client_id", client_id)
    token_store.put("linkedin_client_secret", client_secret)

    state = secrets.token_urlsafe(16)
    scopes = ["openid", "profile", "email", "w_member_social"]
    auth_params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": REDIRECT_URI,
        "state": state,
        "scope": " ".join(scopes),
    }
    auth_url = f"https://www.linkedin.com/oauth/v2/authorization?{urllib.parse.urlencode(auth_params)}"
    print("\nOpening LinkedIn authorization page in your browser...")
    print(f"  {auth_url}\n")
    webbrowser.open(auth_url)

    print(f"Listening for callback on {REDIRECT_URI}...")
    cb = wait_for_callback()
    if cb.get("state") != state:
        sys.exit(f"State mismatch — possible CSRF. Got: {cb}")
    if "error" in cb:
        sys.exit(f"OAuth error: {cb}")
    code = cb.get("code")
    if not code:
        sys.exit("No code in callback")

    print("\nExchanging code for tokens...")
    r = requests.post(
        "https://www.linkedin.com/oauth/v2/accessToken",
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI,
            "client_id": client_id,
            "client_secret": client_secret,
        },
        timeout=15,
    )
    if r.status_code != 200:
        sys.exit(f"Token exchange failed: {r.status_code} {r.text}")
    body = r.json()
    token_store.put("linkedin_access_token", body["access_token"])
    if "refresh_token" in body:
        token_store.put("linkedin_refresh_token", body["refresh_token"])
    token_store.set_expires_at("linkedin", body.get("expires_in", 5184000))

    # Get the LinkedIn person URN
    r = requests.get(
        "https://api.linkedin.com/v2/userinfo",
        headers={"Authorization": f"Bearer {body['access_token']}"},
        timeout=15,
    )
    if r.status_code != 200:
        sys.exit(f"userinfo failed: {r.status_code} {r.text}")
    info = r.json()
    sub = info.get("sub")
    person_urn = f"urn:li:person:{sub}"
    token_store.put("linkedin_person_urn", person_urn)

    print(f"\n✓ LinkedIn setup complete.")
    print(f"  Person URN: {person_urn}")
    print(f"  Display name: {info.get('name', '?')}")
    print(f"  Email: {info.get('email', '?')}")
    print(f"  Access token expires in {body.get('expires_in', 0) // 86400} days")
    print(f"\nKeys stored in macOS Keychain under service 'digischola-scheduler-publisher'.")
    print(f"Verify anytime: python3 token_store.py --list")


def verify_linkedin():
    """Post a private-test text then auto-delete via DELETE /v2/ugcPosts/{urn}."""
    import re
    import urllib.parse
    from publishers import linkedin as li

    print("\n=== LinkedIn Verification ===\n")
    if not token_store.get_linkedin_credentials():
        sys.exit("LinkedIn not set up. Run: setup_channel.py linkedin")
    print("Posting test message (auto-delete in 3 sec; usually invisible to feed)...")
    # Use a short test string; visibility is PUBLIC but we delete fast enough that the
    # post almost never reaches anyone's feed (LinkedIn feed propagation delay > our delete delay).
    test = f"Digischola scheduler dry-run {datetime.now().strftime('%H:%M:%S IST')}"
    result = li.publish_text(test)
    if result.status != "posted":
        print(f"  ✗ Post failed: {result.reason}")
        sys.exit(1)
    print(f"  ✓ Posted: {result.url}")

    # Extract URN
    m = re.search(r"(urn:li:[a-zA-Z]+:[a-zA-Z0-9_-]+)", result.url or "")
    if not m:
        print(f"  ⚠ Could not extract URN from URL — open {result.url} and delete manually")
        return
    urn = m.group(1)

    # Sleep briefly to let LinkedIn index the post before delete
    time.sleep(3)
    encoded = urllib.parse.quote(urn, safe="")
    r = requests.delete(
        f"https://api.linkedin.com/v2/ugcPosts/{encoded}",
        headers={
            "Authorization": f"Bearer {token_store.get('linkedin_access_token')}",
            "X-Restli-Protocol-Version": "2.0.0",
        },
        timeout=15,
    )
    if r.status_code in (200, 204):
        print(f"  ✓ Auto-deleted ({r.status_code}) — full pipeline verified")
    else:
        print(f"  ⚠ Auto-delete returned {r.status_code}: {r.text[:120]}")
        print(f"    Open {result.url} in a browser and delete the post manually.")


# ── X ─────────────────────────────────────────────────────────────────────


def setup_x():
    print("\n=== X OAuth Setup ===\n")
    print("⚠ DEPRECATED 2026-04-20: X migrated to console.x.com pay-per-use; the scheduler")
    print("  now routes X via NOTIFICATION-ONLY (manual_pub) instead of autonomous API.")
    print("  This setup still works and stores tokens, but tick.py won't use them.")
    print("  Continue only if you've funded X credits AND manually flipped publisher_map")
    print("  in tick.py back to x_pub.publish_draft for 'x' / 'twitter'.\n")
    cont = input("Continue anyway? [y/N]: ").strip().lower()
    if cont != "y":
        sys.exit("Aborted. X stays on notification mode — no setup needed.")
    print("\nPrerequisites (per references/x-api-setup.md):")
    print("  - X Developer app exists at developer.x.com")
    print("  - Permission set to: Read and write")
    print("  - Type: Web App / Automated App or Bot")
    print("  - Callback URI:", REDIRECT_URI)
    print()
    client_id = input("X OAuth 2.0 Client ID: ").strip()
    if not client_id:
        sys.exit("Empty Client ID; aborting.")
    client_secret = getpass.getpass("X OAuth 2.0 Client Secret (hidden): ").strip()
    if not client_secret:
        sys.exit("Empty Client Secret; aborting.")

    token_store.put("x_client_id", client_id)
    token_store.put("x_client_secret", client_secret)

    state = secrets.token_urlsafe(16)
    verifier, challenge = make_pkce_pair()
    token_store.put("x_pkce_verifier", verifier)

    scopes = ["tweet.read", "tweet.write", "users.read", "offline.access", "media.write"]
    auth_params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": REDIRECT_URI,
        "state": state,
        "scope": " ".join(scopes),
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    }
    auth_url = f"https://twitter.com/i/oauth2/authorize?{urllib.parse.urlencode(auth_params)}"
    print("\nOpening X authorization page in your browser...")
    print(f"  {auth_url}\n")
    webbrowser.open(auth_url)

    print(f"Listening for callback on {REDIRECT_URI}...")
    cb = wait_for_callback()
    if cb.get("state") != state:
        sys.exit(f"State mismatch — possible CSRF. Got: {cb}")
    if "error" in cb:
        sys.exit(f"OAuth error: {cb}")
    code = cb.get("code")
    if not code:
        sys.exit("No code in callback")

    print("\nExchanging code for tokens...")
    r = requests.post(
        "https://api.twitter.com/2/oauth2/token",
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI,
            "code_verifier": verifier,
            "client_id": client_id,
        },
        auth=(client_id, client_secret),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=15,
    )
    if r.status_code != 200:
        sys.exit(f"Token exchange failed: {r.status_code} {r.text}")
    body = r.json()
    token_store.put("x_access_token", body["access_token"])
    if "refresh_token" in body:
        token_store.put("x_refresh_token", body["refresh_token"])
    token_store.set_expires_at("x", body.get("expires_in", 7200))
    token_store.delete("x_pkce_verifier")  # transient

    # Identify user
    r = requests.get(
        "https://api.twitter.com/2/users/me",
        headers={"Authorization": f"Bearer {body['access_token']}"},
        timeout=15,
    )
    if r.status_code != 200:
        sys.exit(f"users/me failed: {r.status_code} {r.text}")
    info = r.json().get("data", {})
    token_store.put("x_user_id", info.get("id", ""))
    token_store.put("x_screen_name", info.get("username", ""))

    print(f"\n✓ X setup complete.")
    print(f"  User ID: {info.get('id', '?')}")
    print(f"  Username: @{info.get('username', '?')}")
    print(f"  Access token expires in {body.get('expires_in', 0) // 60} minutes (auto-refresh on tick)")


def verify_x():
    from publishers import x as x_pub
    print("\n=== X Verification ===\n")
    if not token_store.get_x_credentials():
        sys.exit("X not set up. Run: setup_channel.py x")
    test = f"Digischola scheduler test {datetime.now().strftime('%H:%M:%S')} 🟢"
    print(f"Posting test tweet: {test!r}")
    result = x_pub.publish_single(test)
    if result.status == "posted":
        print(f"  ✓ Posted: {result.url}")
        # Try to delete
        tweet_id = result.url.split("/")[-1] if result.url else None
        if tweet_id:
            time.sleep(3)
            r = requests.delete(
                f"https://api.twitter.com/2/tweets/{tweet_id}",
                headers={"Authorization": f"Bearer {token_store.get('x_access_token')}"},
                timeout=15,
            )
            if r.status_code == 200:
                print(f"  ✓ Test tweet auto-deleted")
            else:
                print(f"  ⚠ Couldn't auto-delete ({r.status_code}); delete manually if needed.")
    else:
        print(f"  ✗ Failed: {result.reason}")
        sys.exit(1)


# ── Main ──────────────────────────────────────────────────────────────────


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("platform", nargs="?", choices=["linkedin", "x"],
                    help="Channel to set up")
    ap.add_argument("--verify", action="store_true",
                    help="Post a test, then delete (where possible)")
    ap.add_argument("--reset", choices=["linkedin", "x", "all"],
                    help="Delete Keychain entries for a platform")
    args = ap.parse_args()

    if args.reset:
        n = token_store.purge_platform(args.reset)
        print(f"Deleted {n} Keychain entries for {args.reset}.")
        return

    if not args.platform:
        ap.print_help()
        sys.exit(1)

    if args.verify:
        if args.platform == "linkedin":
            verify_linkedin()
        else:
            verify_x()
        return

    if args.platform == "linkedin":
        setup_linkedin()
    elif args.platform == "x":
        setup_x()


if __name__ == "__main__":
    main()
