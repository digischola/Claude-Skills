# Google Ads API Setup Guide (One-Time)

This is a one-time setup. Once done, the `google_keyword_volume.py` script works for all clients. Total time: ~30 minutes (plus developer token approval wait).

## Prerequisites

- A Google Ads Manager (MCC) account (free to create)
- A Google Cloud project (free tier is sufficient)
- Python 3.8+
- A Google Ads account with active billing (test accounts work with test tokens only)

---

## Step 1: Create Google Ads MCC Account (if you don't have one)

An MCC (My Client Center) lets you manage multiple client accounts under one login and one API developer token.

1. Go to [ads.google.com/home/tools/manager-accounts/](https://ads.google.com/home/tools/manager-accounts/)
2. Sign in with your Google account (use your business Google account, not a client's)
3. Click **Create a manager account**
4. Fill in account name (e.g., "Mayank Verma Digital Marketing")
5. Select your use case: **Manage other people's accounts**
6. Choose your country and currency (AUD if Australia-based clients)
7. Submit — your MCC is created immediately

Your MCC has a 10-digit ID (format: XXX-XXX-XXXX) visible in the top-right of the Google Ads interface.

---

## Step 2: Apply for API Developer Token

The developer token is what grants your MCC access to the Google Ads API.

1. Sign into your MCC at [ads.google.com](https://ads.google.com)
2. Click the **Admin** icon (wrench/spanner) in the left nav, or go to **Tools & Settings**
3. Under **Setup**, click **API Center**
4. If you don't see API Center, your MCC may need to have at least one active client account linked first
5. Fill in the application form:
   - **API contact email:** your business email
   - **Developer token use:** "Access keyword planning data for client campaigns"
   - **Company description:** "Digital marketing freelancer managing Google Ads campaigns"
6. Submit the application

**Access levels:**
- **Test account access** — granted immediately, but only works with test Google Ads accounts (no real data). Good for testing the script works end-to-end.
- **Basic access** — sufficient for keyword data. Requires approval (usually 2-5 business days). Apply for this.
- **Standard access** — for high-volume use. Not needed for keyword research.

Your developer token appears in the API Center page once approved. It looks like a ~22-character alphanumeric string.

**While waiting for approval:** use the test account token to verify your setup works. Create a test account in Google Ads (Settings → Test accounts) and use its customer ID.

---

## Step 3: Create Google Cloud Project

The GCP project provides OAuth2 credentials for authenticating API requests.

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Sign in with the same Google account as your MCC
3. Click the project dropdown (top-left, next to "Google Cloud") → **New Project**
4. Name it (e.g., "Google Ads API - Marketing Tools")
5. Click **Create** and wait a few seconds

**Enable the Google Ads API:**

6. Go to [console.cloud.google.com/apis/library](https://console.cloud.google.com/apis/library)
7. Search for **Google Ads API**
8. Click on it → click **Enable**
9. Wait for it to activate (usually instant)

---

## Step 4: Create OAuth2 Credentials

1. Go to [console.cloud.google.com/apis/credentials](https://console.cloud.google.com/apis/credentials)
2. Click **+ Create Credentials** → **OAuth client ID**
3. If prompted to configure the consent screen first:
   - User type: **External** (unless you have a Workspace org, then Internal)
   - App name: "Google Ads API Client"
   - User support email: your email
   - Developer contact: your email
   - Scopes: click **Add or Remove Scopes** → search for `https://www.googleapis.com/auth/adwords` → check it → **Update** → **Save and Continue**
   - Test users: add your own Google email address
   - Review and submit
4. Back on Create OAuth client ID:
   - Application type: **Desktop app**
   - Name: "Google Ads API Desktop Client"
   - Click **Create**
5. A popup shows your **Client ID** and **Client Secret** — copy both
6. Also click **Download JSON** to save `client_secret_XXXX.json` as backup

Save these values — you need them for the config file.

---

## Step 5: Generate Refresh Token

The refresh token is a long-lived credential that lets the script authenticate without a browser login each time.

**Option A: Using the google-ads library's built-in tool (recommended)**

```bash
pip install google-ads
```

Then run the authenticate command:

```bash
google-ads-api authenticate \
  --client-id YOUR_CLIENT_ID \
  --client-secret YOUR_CLIENT_SECRET
```

This opens a browser window. Sign in with the Google account that has access to your MCC. Authorize the app. The tool prints a refresh token — copy it.

If `google-ads-api` command is not found, try:

```bash
python -m google.ads.googleads.auth.authenticate \
  --client_id YOUR_CLIENT_ID \
  --client_secret YOUR_CLIENT_SECRET
```

**Option B: Manual OAuth flow**

1. Construct this URL (replace YOUR_CLIENT_ID):
   ```
   https://accounts.google.com/o/oauth2/auth?client_id=YOUR_CLIENT_ID&redirect_uri=urn:ietf:wg:oauth:2.0:oob&scope=https://www.googleapis.com/auth/adwords&response_type=code&access_type=offline&prompt=consent
   ```
2. Open it in your browser, sign in, authorize
3. Copy the authorization code
4. Exchange it for tokens:
   ```bash
   curl -X POST https://oauth2.googleapis.com/token \
     -d "code=AUTH_CODE_HERE" \
     -d "client_id=YOUR_CLIENT_ID" \
     -d "client_secret=YOUR_CLIENT_SECRET" \
     -d "redirect_uri=urn:ietf:wg:oauth:2.0:oob" \
     -d "grant_type=authorization_code"
   ```
5. The response JSON contains `refresh_token` — save it

**Note:** If you don't get a `refresh_token` in the response, add `&prompt=consent` to the auth URL and try again. Google only returns the refresh token on the first authorization or when consent is explicitly re-prompted.

---

## Step 6: Create ~/.google-ads.yaml

Create the file at `~/.google-ads.yaml` with your credentials:

```yaml
# Google Ads API Configuration
# Used by: google_keyword_volume.py and any future Google Ads API scripts
# Docs: https://developers.google.com/google-ads/api/docs/client-libs/python/configuration

developer_token: "YOUR_DEVELOPER_TOKEN"
client_id: "YOUR_CLIENT_ID.apps.googleusercontent.com"
client_secret: "YOUR_CLIENT_SECRET"
refresh_token: "YOUR_REFRESH_TOKEN"

# Optional: set your MCC login customer ID if using manager account
# This is your MCC's 10-digit ID (no dashes)
login_customer_id: "YOUR_MCC_CUSTOMER_ID"

# Optional: enable API request logging for debugging
# logging:
#   version: 1
#   disable_existing_loggers: false
#   formatters:
#     default:
#       format: "[%(asctime)s - %(levelname)s] %(message)s"
#   handlers:
#     file:
#       class: logging.FileHandler
#       formatter: default
#       filename: /tmp/google_ads_api.log
#   root:
#     level: WARNING
#     handlers: [file]
```

**Important:**
- `login_customer_id` is your MCC's ID (the manager account). Required when querying client accounts under the MCC.
- The `--customer-id` argument in the script is the specific client's Google Ads account ID.
- Both should be 10 digits, no dashes.

Set file permissions (contains secrets):

```bash
chmod 600 ~/.google-ads.yaml
```

---

## Step 7: Install Dependencies

```bash
pip install google-ads
```

Or add to a requirements file:

```
google-ads>=24.0.0
```

The `google-ads` package pulls in `google-auth`, `google-api-core`, `proto-plus`, and `grpcio` automatically.

---

## Step 8: Test

**Dry run (no API calls — verifies CLI and argument parsing):**

```bash
python google_keyword_volume.py \
  --customer-id YOUR_CLIENT_ACCOUNT_ID \
  --keywords "test keyword" \
  --dry-run
```

**Live test (makes one API call):**

```bash
python google_keyword_volume.py \
  --customer-id YOUR_CLIENT_ACCOUNT_ID \
  --keywords "digital marketing" \
  --country AU \
  --exact-only \
  --output /tmp/keyword-test \
  --verbose
```

If this returns volume data, setup is complete.

---

## Troubleshooting

### "google-ads library not installed"
```bash
pip install google-ads
```
If using a virtual environment, ensure it's activated.

### "Config not found at ~/.google-ads.yaml"
Create the file per Step 6. Ensure the path is exactly `~/.google-ads.yaml` (home directory, not the project folder).

### "Authentication error" / "Invalid refresh token"
- Refresh token may have expired if the GCP project's consent screen is in "Testing" mode (tokens expire after 7 days). Fix: publish the consent screen to "Production" (you don't need Google verification for private use), or regenerate the refresh token.
- Ensure `client_id` and `client_secret` in the YAML match your GCP project's OAuth credentials.

### "DEVELOPER_TOKEN_NOT_APPROVED"
Your developer token is still pending approval. Use a test account in the meantime. Create one in Google Ads: Tools & Settings → Setup → Test accounts.

### "CUSTOMER_NOT_FOUND" / "Invalid customer ID"
- The `--customer-id` must be a valid, active Google Ads account (not the MCC ID).
- It must be linked to your MCC. In your MCC: Accounts → Sub-accounts → Link.
- Format: 10 digits, no dashes (the script strips dashes automatically).

### "USER_PERMISSION_DENIED"
- Your MCC doesn't have access to the specified client account.
- The Google account used for OAuth must have admin or standard access to the MCC.

### "QUOTA_EXCEEDED" / "RATE_LIMIT_EXCEEDED"
- The script already batches (10 keywords per request) and sleeps between batches.
- If you still hit limits: wait 1-2 minutes and retry, or reduce the keyword list.
- Basic access: 15,000 requests/day. More than enough for keyword research.

### "GoogleAdsException" with no clear message
Run with `--verbose` flag for debug logging. Also check:
```bash
python -c "from google.ads.googleads.client import GoogleAdsClient; print('Import OK')"
```
If that fails, reinstall: `pip install --force-reinstall google-ads`

### SSL / gRPC errors on macOS
```bash
pip install --upgrade grpcio grpcio-status
```
If using Python installed via Homebrew, you may need to install certificates:
```bash
/Applications/Python\ 3.x/Install\ Certificates.command
```

---

## Using Client Accounts

The keyword volume script needs a Google Ads customer ID to query against. Here's how it works with client accounts:

**The `--customer-id` should be the client's Google Ads account ID, not your MCC.**

The API uses the client's account to determine which keyword data pool to access. This matters because:
- Keyword Planner data availability requires the account to have active billing
- Some metrics (like CPC estimates) are influenced by the account's historical performance

**To find a client's account ID:**
1. In your MCC, go to Accounts → Sub-accounts
2. The 10-digit number next to each account name is the customer ID

**To link a new client account to your MCC:**
1. In your MCC: Accounts → Sub-accounts → blue "+" button → Link existing account
2. Enter the client's Google Ads account ID
3. The client receives an email to approve the link (or you can send them the link request)
4. Once approved, you can query their account via the API

**If the client doesn't have a Google Ads account:**
- You can create one under your MCC (Accounts → Sub-accounts → New account)
- The account needs active billing to get keyword data (even a paused campaign works)
- Alternatively, use any of your existing accounts with active billing — keyword volume data is not account-specific, only CPC estimates vary slightly

**`login_customer_id` in config vs `--customer-id` in script:**
- `login_customer_id` (in ~/.google-ads.yaml) = your MCC ID. Tells the API "I'm authenticating as this manager."
- `--customer-id` (script argument) = the specific account to query. Tells the API "Pull data for this account."

Both are required when querying client accounts through an MCC.
