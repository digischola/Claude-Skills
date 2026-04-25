# LinkedIn API Setup — One-Time Walkthrough

~15 minutes. You need a personal LinkedIn account (Mayank's @digischola account). LinkedIn's Developer platform is free; no payment needed.

## Why this works without ban risk

The LinkedIn UGC API is LinkedIn's own published interface for personal posting. It's used by Buffer, Hootsuite, Sprout, and every third-party scheduler. Personal apps in "Development" mode can post to YOUR OWN account without LinkedIn approval. You'll never need to submit for LinkedIn Marketing Developer Program review (which is for apps posting on behalf of OTHER users).

## Steps

### 1. Create the LinkedIn Developer App

1. Open https://www.linkedin.com/developers/apps in Chrome (must be logged in to LinkedIn)
2. Click **Create app**
3. Fill in:
   - App name: `Digischola Scheduler`
   - LinkedIn Page: pick "Digischola" page if you have one, or create a Company Page first (free, 2 min)
     - If you don't have a Company Page: https://www.linkedin.com/company/setup/new — name it Digischola, single-person agency
   - Privacy policy URL: `https://digischola.com/privacy` (or any page; LinkedIn doesn't strictly verify in dev mode)
   - App logo: upload a 100x100 PNG of the Digischola logo
4. Check the legal terms box, click **Create app**

### 2. Add Required Products

In your new app's dashboard:
1. Click the **Products** tab
2. Request access to **Sign In with LinkedIn using OpenID Connect** (instant approval)
3. Request access to **Share on LinkedIn** (instant approval)

### 3. Configure OAuth Redirect

1. Click the **Auth** tab
2. Under "OAuth 2.0 settings", add Authorized redirect URL: `http://localhost:8765/callback`
3. Verify scopes shown include: `openid`, `profile`, `email`, `w_member_social`

### 4. Note your Client ID + Secret

Still on the Auth tab:
- Copy **Client ID** (long string)
- Copy **Primary Client Secret** (click "show" to reveal)

Have both ready — `setup_channel.py linkedin` will prompt you to paste them.

### 5. Run the setup script

```bash
python3 /Users/digischola/Desktop/Claude\ Skills/skills/scheduler-publisher/scripts/setup_channel.py linkedin
```

The script will:
1. Prompt for Client ID + Secret (pastes go to Keychain, never written to disk)
2. Open `https://www.linkedin.com/oauth/v2/authorization?...` in your default browser
3. You click "Allow" on LinkedIn's permission page
4. LinkedIn redirects to `http://localhost:8765/callback?code=...`
5. Local server captures the code, exchanges it for an access_token + refresh_token
6. Calls `/v2/userinfo` to get your `sub` (LinkedIn person URN like `urn:li:person:abc123`)
7. Stores everything in macOS Keychain under service `digischola-scheduler-publisher`, accounts `linkedin_client_id`, `linkedin_client_secret`, `linkedin_access_token`, `linkedin_refresh_token`, `linkedin_person_urn`, `linkedin_token_expires_at`

### 6. Verify

```bash
python3 /Users/digischola/Desktop/Claude\ Skills/skills/scheduler-publisher/scripts/setup_channel.py linkedin --verify
```

Posts a test "Hello from Digischola Scheduler" private to your account (you can delete it after). If it succeeds, the integration is live.

## Token refresh

LinkedIn access tokens last 60 days. The scheduler refreshes them automatically on every tick — checks `linkedin_token_expires_at`, refreshes if within 7 days of expiry. Refresh tokens themselves last 1 year; if a refresh token expires, you'll see a notification telling you to re-run `setup_channel.py linkedin`.

## Permission scopes used

| Scope | Why |
|---|---|
| `openid` `profile` `email` | Sign in + identify your LinkedIn person URN |
| `w_member_social` | Post on YOUR OWN behalf (text, image, video, document/carousel) |

Nothing else. We do NOT request `r_organization_social` or `w_organization_social` — those need LinkedIn approval and aren't needed for personal posting.

## Troubleshooting

- **"Insufficient permissions" on POST**: scope wasn't granted. Re-run setup; on the LinkedIn consent screen, ensure all checkboxes are ticked.
- **`401` after weeks of working**: refresh token expired. Re-run `setup_channel.py linkedin`.
- **`429` Rate limited**: LinkedIn caps personal posting at ~150/day. We're well under. If hit: scheduler waits 1h then retries.
