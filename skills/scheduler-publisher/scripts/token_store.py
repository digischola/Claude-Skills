#!/usr/bin/env python3
"""
Token storage for the Digischola scheduler-publisher.

All API tokens live in the macOS Keychain under one service:
    Service: digischola-scheduler-publisher
    Accounts: linkedin_client_id, linkedin_access_token, x_refresh_token, etc.

Why Keychain (not .env): zero plaintext on disk. Encrypted with the user's login
password. Visible/auditable in Keychain Access.app. Survives Mac migration.

Public API:
    get(account: str) -> Optional[str]
    put(account: str, value: str) -> None
    delete(account: str) -> None
    list_accounts() -> list[str]
    purge_platform(platform: str) -> int   # nuke all keys with prefix
    is_token_expiring_soon(platform: str, days: int = 7) -> bool
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from typing import Optional

try:
    import keyring
except ImportError:
    sys.exit("keyring not installed. Run: pip3 install keyring")


SERVICE = "digischola-scheduler-publisher"

# Canonical account names. Add here when adding new fields.
LINKEDIN_KEYS = [
    "linkedin_client_id",
    "linkedin_client_secret",
    "linkedin_access_token",
    "linkedin_refresh_token",
    "linkedin_person_urn",
    "linkedin_token_expires_at",
]

X_KEYS = [
    "x_client_id",
    "x_client_secret",
    "x_access_token",
    "x_refresh_token",
    "x_user_id",
    "x_screen_name",
    "x_token_expires_at",
    "x_pkce_verifier",  # transient during OAuth; cleared after exchange
]


def get(account: str) -> Optional[str]:
    return keyring.get_password(SERVICE, account)


def put(account: str, value: str) -> None:
    if value is None:
        delete(account)
        return
    keyring.set_password(SERVICE, account, str(value))


def delete(account: str) -> None:
    try:
        keyring.delete_password(SERVICE, account)
    except keyring.errors.PasswordDeleteError:
        pass  # Not present; idempotent


def list_accounts() -> list[str]:
    """Return which canonical accounts currently have a value (for audit)."""
    present = []
    for k in LINKEDIN_KEYS + X_KEYS:
        if get(k) is not None:
            present.append(k)
    return present


def purge_platform(platform: str) -> int:
    """Nuke all keys for one platform. Returns count deleted."""
    if platform == "linkedin":
        keys = LINKEDIN_KEYS
    elif platform == "x":
        keys = X_KEYS
    elif platform == "all":
        keys = LINKEDIN_KEYS + X_KEYS
    else:
        raise ValueError(f"Unknown platform: {platform}")
    n = 0
    for k in keys:
        if get(k) is not None:
            delete(k)
            n += 1
    return n


# ── Token-expiry helpers ──────────────────────────────────────────────────


def get_expires_at(platform: str) -> Optional[datetime]:
    """Return datetime (UTC) when this platform's access token expires, or None."""
    raw = get(f"{platform}_token_expires_at")
    if not raw:
        return None
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        return None


def set_expires_at(platform: str, expires_in_sec: int) -> None:
    """Compute and store expiry datetime from an `expires_in` (seconds)."""
    dt = datetime.now(timezone.utc) + timedelta(seconds=int(expires_in_sec))
    put(f"{platform}_token_expires_at", dt.isoformat())


def is_token_expiring_soon(platform: str, days: int = 7) -> bool:
    """True if the access token expires within `days`. None expiry → True (refresh)."""
    expires_at = get_expires_at(platform)
    if expires_at is None:
        return True
    return (expires_at - datetime.now(timezone.utc)) <= timedelta(days=days)


def is_token_expired(platform: str) -> bool:
    """True if the access token is already past expiry."""
    expires_at = get_expires_at(platform)
    if expires_at is None:
        return True
    return datetime.now(timezone.utc) >= expires_at


# ── Convenience getters ───────────────────────────────────────────────────


def get_linkedin_credentials() -> Optional[dict]:
    """Returns dict with all LinkedIn keys, or None if any required missing."""
    needed = ["linkedin_access_token", "linkedin_person_urn"]
    if not all(get(k) for k in needed):
        return None
    return {k: get(k) for k in LINKEDIN_KEYS if get(k) is not None}


def get_x_credentials() -> Optional[dict]:
    """Returns dict with all X keys, or None if any required missing."""
    needed = ["x_access_token", "x_user_id"]
    if not all(get(k) for k in needed):
        return None
    return {k: get(k) for k in X_KEYS if get(k) is not None}


# ── CLI for inspection ────────────────────────────────────────────────────


def main():
    import argparse
    ap = argparse.ArgumentParser(description="Inspect / manage scheduler-publisher Keychain entries.")
    ap.add_argument("--list", action="store_true", help="List which accounts are populated")
    ap.add_argument("--show", metavar="ACCOUNT", help="Print the value of one account (you'll see it on screen — careful)")
    ap.add_argument("--purge", choices=["linkedin", "x", "all"], help="Delete all keys for a platform")
    args = ap.parse_args()

    if args.list:
        present = list_accounts()
        if not present:
            print("(no entries in Keychain for service 'digischola-scheduler-publisher')")
            return
        print(f"Service: {SERVICE}")
        for k in present:
            v = get(k)
            redacted = v[:8] + "…" + v[-4:] if v and len(v) > 16 else "(short)"
            if "expires_at" in k:
                redacted = v
            print(f"  {k:32s}  {redacted}")
        for plat in ("linkedin", "x"):
            if any(p.startswith(plat) for p in present):
                soon = "yes" if is_token_expiring_soon(plat) else "no"
                print(f"  [{plat}] token expiring within 7d: {soon}")
        return

    if args.show:
        v = get(args.show)
        print(v if v else "(not set)")
        return

    if args.purge:
        n = purge_platform(args.purge)
        print(f"Deleted {n} entries for {args.purge}.")
        return

    ap.print_help()


if __name__ == "__main__":
    main()
