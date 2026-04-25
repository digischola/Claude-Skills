# Token Storage — macOS Keychain via `keyring`

All API tokens live in the macOS Keychain. Zero plaintext anywhere on disk. The Python `keyring` library wraps the Keychain Services API natively — no shelling out.

## Service + account naming

All keys live under one Keychain service for easy audit:

```
Service: digischola-scheduler-publisher
Accounts:
  linkedin_client_id
  linkedin_client_secret
  linkedin_access_token
  linkedin_refresh_token
  linkedin_person_urn
  linkedin_token_expires_at         (ISO 8601 string)
  x_client_id
  x_client_secret
  x_access_token
  x_refresh_token
  x_user_id
  x_screen_name
  x_token_expires_at                (ISO 8601 string)
```

## Visual audit

Open `Keychain Access.app` → search "digischola-scheduler-publisher" → you'll see all entries with their account names. Right-click → "Show password" reveals the value (Mac asks for your login password). This is intentional: full transparency for the user.

## Programmatic access

```python
import keyring
SERVICE = "digischola-scheduler-publisher"

# Write
keyring.set_password(SERVICE, "linkedin_access_token", "AQX...")

# Read
token = keyring.get_password(SERVICE, "linkedin_access_token")  # returns None if absent

# Delete
keyring.delete_password(SERVICE, "linkedin_access_token")
```

The wrapper at `scripts/token_store.py` provides typed accessors (`get_linkedin_token()`, `set_x_tokens(...)`, etc.) and handles refresh-token expiry detection.

## Why not `.env` files?

- `.env` files in the repo would expose tokens to anyone with disk access (cloud sync, leaked backups, accidental git commit).
- Keychain is encrypted with the user's login password and never leaves the device.
- macOS sandboxing means other apps can't read our service unless they ask the user explicitly.

## Removing all tokens (clean slate)

```bash
python3 scripts/setup_channel.py --reset all       # nukes all Keychain entries for this service
python3 scripts/setup_channel.py --reset linkedin  # only LinkedIn
python3 scripts/setup_channel.py --reset x         # only X
```

After reset, re-run `setup_channel.py <platform>` to re-authenticate.

## Backup considerations

If you migrate to a new Mac, the Keychain comes with you via iCloud Keychain (if enabled) or migration assistant. If you want manual export: export the items from Keychain Access.app GUI → save the .keychain file → import on the new Mac. The scheduler picks up the new entries automatically.
