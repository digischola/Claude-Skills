# X (Twitter) API Setup — One-Time Walkthrough

~10 minutes. Free tier: 1,500 posts/month, 50/day, 100 reads/month. More than enough for personal-brand volume.

## Why this works without ban risk

X API v2 is X's own published interface. The free tier is sanctioned for "low-volume posting bots" — exactly our use case. As long as posts originate from your authenticated user context (not unattributed automation), there's no flagging risk.

## Steps

### 1. Create the X Developer Account

1. Open https://developer.x.com in Chrome (must be logged in to X)
2. Click **Sign up** → **Free** tier
3. Fill in the use case form:
   - Primary reason: "Building tools for myself"
   - Will you analyze X data: No
   - Will you make X content available to a government entity: No
   - Description: "Personal scheduling tool to post Digischola digital marketing content from my own account, ~10 posts/week."
4. Accept terms → Submit. Approval is instant for free tier.

### 2. Create a Project + App

1. In the developer portal, click **Projects & Apps** → **Add Project**
2. Project name: `Digischola Scheduler`
3. Use case: "Making a bot"
4. Within the project, click **Add App**
5. App name: `digischola-scheduler-app` (must be globally unique; add random suffix if taken)

### 3. Set up User Authentication

1. In your app, find **User authentication settings** → **Set up**
2. **App permissions**: select `Read and write` (not just Read; we need to post)
3. **Type of App**: select `Web App, Automated App or Bot`
4. **App info**:
   - Callback URI: `http://localhost:8765/callback`
   - Website URL: `https://digischola.com`
   - Terms of service URL + Privacy policy URL: any URL (X doesn't validate strictly in free tier)
5. Click **Save**

### 4. Note your Client ID + Secret

After saving, X shows you:
- **OAuth 2.0 Client ID**
- **OAuth 2.0 Client Secret**

Copy both. Have them ready for the setup script.

### 5. Run the setup script

```bash
python3 /Users/digischola/Desktop/Claude\ Skills/skills/scheduler-publisher/scripts/setup_channel.py x
```

The script will:
1. Prompt for Client ID + Secret (Keychain storage, no plaintext)
2. Open the X OAuth2 URL in your browser
3. You click "Authorize app"
4. X redirects to `http://localhost:8765/callback?code=...`
5. Local server exchanges code for access_token + refresh_token (PKCE flow)
6. Calls `/2/users/me` to get your numeric user_id and screen_name
7. Stores everything in Keychain under accounts `x_client_id`, `x_client_secret`, `x_access_token`, `x_refresh_token`, `x_user_id`, `x_screen_name`, `x_token_expires_at`

### 6. Verify

```bash
python3 /Users/digischola/Desktop/Claude\ Skills/skills/scheduler-publisher/scripts/setup_channel.py x --verify
```

Posts a test tweet "Hello from Digischola Scheduler — test 🟢" then deletes it 5 seconds later. If both succeed, the integration is live.

## Token refresh

X OAuth2 access tokens last 2 hours. Refresh tokens last "indefinitely" (until revoked or unused for 6 months). Scheduler refreshes the access token automatically on every tick if it's within 10 min of expiring.

## Permission scopes used

| Scope | Why |
|---|---|
| `tweet.read` | Verify identity post-OAuth |
| `tweet.write` | Post tweets (single + threads) |
| `users.read` | Get your user_id for thread chaining |
| `offline.access` | Required to receive a refresh_token |
| `media.write` | Attach images / videos to tweets |

## Free tier limits

| Limit | Value | Our usage |
|---|---|---|
| Posts (writes) per month | 1,500 | ~30/mo planned |
| Posts per day | 50 | ~3/day max |
| Reads per month | 100 | ~10 (just identity verification) |
| Media uploads | Same as posts | Within budget |

## Troubleshooting

- **`401` from `/2/tweets`**: access token expired and refresh failed. Re-run `setup_channel.py x`.
- **`403 Forbidden` with "duplicate content"**: X blocks identical tweets within 24h. The publisher detects this and marks the post as `failed: duplicate_content` (no retry).
- **`429 Too Many Requests`**: hit the daily limit. Scheduler waits until next IST midnight.
- **OAuth callback never returns**: check that `http://localhost:8765/callback` is exactly the callback URI in X's app settings (no trailing slash mismatch).
