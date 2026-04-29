# Launch Runbook Template

Fill-in template for `{{CLIENT_DIR}}/campaign-setup/launch-runbook.md`. This is the ops playbook for the actual upload. Follow it top to bottom on launch day.

Rule: no shortcut. Each step has a verification. Never click Post in Ads Editor or Publish in Ads Manager without completing the prior step's check.

---

# {{CLIENT_NAME}} — Launch Runbook

**Launch date (target):** {{DATE}}
**Primary owner:** {{ANALYST_NAME}}
**Secondary owner (approvals / escalation):** {{CLIENT_CONTACT}}
**Account(s):** Google {{GOOGLE_CID}} · Meta {{META_AD_ACCOUNT_ID}}

---

## Phase 0 — T-24h Pre-Upload Prep

### 0.1 Pre-flight checks
- [ ] Pre-launch-checklist.md: every item checked, both sign-offs in place
- [ ] All `<REPLACE_ME>` tokens resolved in CSVs
- [ ] `scripts/validate_output.py` last run shows 0 CRITICAL, 0 placeholder tokens
- [ ] Client has received and approved ad previews (screenshots or preview links)
- [ ] Landing page(s) live, indexed, form tested end-to-end with fake lead that reached CRM
- [ ] Conversion tracking verified — test conversion fired in Google Ads Conversions report AND Meta Events Manager in last 48h

### 0.2 Tooling
- [ ] Google Ads Editor installed (latest version — `Help → Check for updates`)
- [ ] Ads Editor logged in to correct manager account (MCC) and client account (CID)
- [ ] Meta Ads Manager web access confirmed for client's ad account
- [ ] Meta Business Suite access confirmed (for Asset Library uploads)
- [ ] Chrome + Meta Pixel Helper extension installed on launch machine
- [ ] 2FA devices available for both accounts

### 0.3 Backups
- [ ] Google Ads Editor: `Account → Get recent changes` (snapshot current state)
- [ ] Google Ads Editor: `File → Export → Entire account as CSV` → save to `{{CLIENT_DIR}}/campaign-setup/backups/google-pre-launch-{{DATE}}/`
- [ ] Meta Ads Manager: filter to all existing campaigns → Export → save to `{{CLIENT_DIR}}/campaign-setup/backups/meta-pre-launch-{{DATE}}/`
- [ ] Wiki `log.md` entry: "Pre-launch backup saved at {{TIMESTAMP}}"

---

## Phase 1 — Google Ads Editor Upload (T-0)

### 1.1 Open account
1. Open Google Ads Editor
2. Sidebar → select {{CLIENT_NAME}} account
3. Menu: `Account → Get recent changes` (sync latest)

### 1.2 Import CSVs in order

Use `Tools → Make multiple changes → Paste from clipboard` (faster than file import for the CSV-per-entity workflow).

Import in this exact order — out-of-order imports throw "Campaign not found" errors:

1. **01-campaigns.csv**
   - Paste → `Detect columns automatically`
   - Scope: `Campaigns`
   - Click `Process` → review error count
   - [ ] 0 errors, campaign count matches media plan
2. **02-ad-groups.csv**
   - Paste → scope `Ad groups`
   - [ ] 0 errors, each ad group under correct campaign
3. **03-keywords.csv**
   - Paste → scope `Keywords`
   - [ ] 0 errors, no duplicate keywords (Editor highlights duplicates)
4. **04-responsive-search-ads.csv**
   - Paste → scope `Ads`
   - [ ] 0 errors, Ad Strength shown ≥ Good for each RSA
5. **05-sitelink-extensions.csv**
   - Paste → scope `Sitelink extensions`
   - [ ] 4+ per campaign
6. **06-callout-extensions.csv** → scope `Callout extensions`
7. **07-structured-snippets.csv** → scope `Structured snippets`
8. **08-negative-keywords.csv** → scope `Negative keywords` (or `Shared sets` if shared list)

### 1.3 Editor-level review
- [ ] `Check for errors` button (top-right) → 0 errors, 0 warnings blocking post
- [ ] Each campaign shows Status = Paused
- [ ] Budget column matches media plan
- [ ] Location targeting matches strategy
- [ ] All RSAs: Ad Strength ≥ Good (aim Excellent)

### 1.4 Post changes
- [ ] Click `Post` button (top-right)
- [ ] Review dialog — confirm "{{ENTITY_COUNTS}}" entities will be posted
- [ ] Click `Post` in dialog
- [ ] Wait for "Post complete" confirmation
- [ ] In Google Ads web UI, refresh → confirm campaigns visible, status Paused

### 1.5 Google-side verification
- [ ] Open Google Ads web UI → Campaigns view
- [ ] Each campaign present, status Paused
- [ ] Click one RSA → preview ad → landing page loads → UTMs in URL
- [ ] Tracking → Conversions: conversion actions active and Recording
- [ ] `⚠ Issues` column: zero disapprovals (if disapprovals, fix copy and re-import affected rows)

---

## Phase 2 — Meta Ads Manager Upload (T-0)

### 2.1 Creative upload (MUST precede bulk CSV)
1. Open Meta Business Suite → Asset Library (or Ads Manager → ⋮ → Media Library)
2. For each asset in `creative-upload-manifest.md`:
   - Click `Upload` → select file
   - Wait for processing
   - Click asset → copy Image Hash (32-char) or Video ID
   - Paste into manifest's `image_hash_or_video_id` column, set status = UPLOADED
3. [ ] All manifest rows show status = UPLOADED
4. [ ] Update `meta-bulk-import.csv`: replace each `<REPLACE_ME_ASSET_HASH_{ID}>` with the actual hash

### 2.2 Import ads CSV
1. Ads Manager → `⋮ (More)` → `Export & Import` → `Import ads from spreadsheet`
2. Upload `meta-bulk-import.csv`
3. Meta shows per-row preview:
   - Green rows = ready
   - Yellow rows = warnings (review but can proceed)
   - Red rows = errors — must fix
4. [ ] 0 red rows. If any: fix CSV → re-upload.
5. Click `Upload and review` → ads appear in Drafts
6. In Drafts view: filter to newly imported ads
7. [ ] Review each ad preview — desktop, mobile feed, story, reel
8. [ ] Body text not truncated above 125 chars
9. [ ] Landing page loads on click (test in Drafts preview)
10. [ ] Status = Paused for all

### 2.3 Meta-side verification
- [ ] Ads Manager → Campaigns: all campaigns present, Paused
- [ ] Events Manager → Pixel: events received in last 1h (from your test)
- [ ] Events Manager → Event Match Quality ≥ 6.0 for Lead event
- [ ] Aggregated Event Measurement: priority order set
- [ ] Business Manager → Domain verified

### 2.4 Fallback: manual build
If bulk import fails for any campaign (complex targeting, Special Ad Category, Instant Forms), fall back to `campaign-blueprint.md`:
- [ ] Build that campaign manually following blueprint
- [ ] Note failure in wiki log with reason

### 2.5 Publish drafts
- [ ] Final sanity check — client approval email/slack referenced in this runbook
- [ ] Select all newly created campaigns in Drafts
- [ ] Click `Publish` → confirm
- [ ] Status stays Paused (publishing moves draft → live but paused); flip to Active only during Phase 3

---

## Phase 3 — Go Live (T+0)

Final authorization step. Do not proceed without explicit client confirmation timestamped {{LAUNCH_DATETIME}}.

### 3.1 Enable Google campaigns
- [ ] Google Ads UI → Campaigns → select all {{CLIENT_NAME}} campaigns
- [ ] Bulk action → Enable
- [ ] Refresh — all show "Eligible" or "Limited by budget"
- [ ] Screenshot for audit trail → `{{CLIENT_DIR}}/campaign-setup/launch-evidence/google-live-{{DATE}}.png`

### 3.2 Enable Meta campaigns
- [ ] Ads Manager → Campaigns → select all new campaigns
- [ ] Toggle Status → Active
- [ ] Refresh → status shows "Active" or "In review"
- [ ] Screenshot → `{{CLIENT_DIR}}/campaign-setup/launch-evidence/meta-live-{{DATE}}.png`

### 3.3 Launch announcement
- [ ] Slack / email to client: "Campaigns live at {{TIMESTAMP}}. Monitoring window 0-24h."
- [ ] Wiki `log.md` entry: "CAMPAIGN LAUNCH — {{PLATFORM(S)}} — {{N_CAMPAIGNS}} campaigns live"

---

## Phase 4 — Post-Launch Monitoring

### 4.1 First 1 hour
- [ ] Impressions > 0 on at least one campaign (indicates delivery started)
- [ ] No policy disapprovals (Google: Ads Policies; Meta: Ad Account Quality)
- [ ] Landing pages still resolving (dual-check)
- [ ] No billing errors

### 4.2 First 24 hours
- [ ] Each ad group / ad set has impressions
- [ ] No "learning stalled" or "limited delivery" warnings (Meta)
- [ ] Test conversion received within 6h if traffic volume allows
- [ ] CPM / CPC sanity check vs benchmark (from market-research wiki)
- [ ] Search term report (Google): no wasteful queries needing immediate negatives
- [ ] Ad previews still correct on mobile feed / reels

### 4.3 Day 3
- [ ] At least 1 real conversion fired (if budget + intent align)
- [ ] Negative keyword pass — add any obvious waste to shared negative list
- [ ] Bid strategy performing to target (no extreme CPA blow-out)
- [ ] Ad Strength status per RSA (Google) — improve any "Poor" ads
- [ ] Frequency ≤ 2.0 (Meta) — pause or refresh if higher on awareness campaigns

### 4.4 Day 7 — First performance checkpoint
- [ ] Run `post-launch-optimization` skill against live data
- [ ] Generate 7-day performance report
- [ ] Decision: keep, adjust budget, pause, or refresh creative

### 4.5 Day 14 — Learning phase review
- [ ] Meta ad sets exiting Learning phase (≥50 optimization events in 7d)
- [ ] Google bid strategies stabilizing (≥30 conversions in Target CPA / Target ROAS)
- [ ] Second optimization pass

---

## Rollback Triggers

Pause all campaigns immediately if any of the below in first 24h:
- Policy disapprovals on all ads in a campaign
- Landing page down >10 min
- Conversion tracking broken (0 conversions recorded while traffic is landing)
- Spend pacing >150% of daily budget due to bid runaway
- Client request
- Major negative feedback on Meta ads (hide/report rate > 1%)

Rollback = Pause, NOT Delete. Preserves historical data for debugging.

---

## Appendix — Key URLs

- Google Ads: https://ads.google.com/aw/campaigns?ocid={{OCID}}
- Google Ads Editor Help: https://support.google.com/google-ads/editor
- Meta Ads Manager: https://adsmanager.facebook.com/adsmanager/manage/campaigns?act={{META_AD_ACCOUNT_ID}}
- Meta Events Manager: https://business.facebook.com/events_manager2/list/pixel/{{META_PIXEL_ID}}
- Landing page(s): {{LANDING_URLS}}
- Wiki log: `{{CLIENT_DIR}}/_engine/wiki/log.md`
