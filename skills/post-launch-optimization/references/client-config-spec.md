# Client Configuration Spec

Load this file in Step 1. Defines the per-client config structure stored in the client's wiki folder.

## Config Location

`{client-folder}/_engine/wiki/optimization-config.json`

Created on first optimization run. Updated when targets change.

## Schema

```json
{
  "client_name": "Thrive Retreats",
  "platforms": {
    "meta": {
      "windsor_connector": "facebook",
      "account_ids": ["1317575072734826"],
      "conversion_event": "actions_purchase",
      "conversion_value_field": "action_values_purchase"
    },
    "google": {
      "windsor_connector": "google_ads",
      "account_ids": ["316-877-9523"],
      "conversion_event": "conversions",
      "conversion_value_field": "conversion_value"
    }
  },
  "budget": {
    "monthly_total_aud": 5500,
    "currency": "AUD",
    "platform_split": {
      "meta": 1.0,
      "google": 0.0
    }
  },
  "targets": {
    "mode": "baseline",
    "cpa_target": null,
    "roas_target": null,
    "baseline_cpa": null,
    "baseline_roas": null,
    "baseline_set_date": null
  },
  "analysis_history": [
    {
      "date": "2026-04-16",
      "report_path": "_engine/working/thrive-optimization-report.md",
      "top_actions": ["action summary 1", "action summary 2"],
      "cpa_at_analysis": 12.50,
      "roas_at_analysis": 4.2
    }
  ],
  "notes": "Meta only currently. Optimizing for retreat bookings (purchases)."
}
```

## Field Definitions

### platforms
- `windsor_connector`: Windsor.ai connector ID ("facebook" or "google_ads")
- `account_ids`: Array of account IDs from `get_connectors()`. Can include multiple accounts per platform.
- `conversion_event`: Which field to use as "the conversion" in all CPA calculations
- `conversion_value_field`: Which field contains the monetary value (for ROAS calculation). Null if no value tracking.

### budget
- `monthly_total_aud`: Total monthly ad spend budget in AUD
- `platform_split`: Decimal split across platforms (must sum to 1.0). Used for per-platform pacing calculations.

### targets
- `mode`: "baseline" (no fixed target, use historical performance) or "fixed" (explicit CPA/ROAS target)
- When mode = "baseline":
  - First run establishes `baseline_cpa` and `baseline_roas` from last 30 days
  - All Layer 1 thresholds reference these baselines
  - Baselines update after every 4 analyses (monthly recalibration)
- When mode = "fixed":
  - `cpa_target` and/or `roas_target` are set explicitly
  - Kill/scale thresholds reference these fixed targets

### analysis_history
- Array of previous analysis snapshots
- Used by Layer 11 (session memory) to track trends and recommendation outcomes
- Keep last 12 entries (3 months of weekly analysis)

## First-Run Behavior

When no `optimization-config.json` exists:

1. Call `get_connectors()` to identify available accounts
2. Ask user (via chat or AskUserQuestion):
   - Which account(s) to analyze?
   - What conversion event matters?
   - Monthly budget?
3. Create config with `targets.mode = "baseline"`
4. Run analysis — Layer 1 establishes baselines
5. Save baselines to config
6. Skip Layer 3 (prescription) and Layer 11 (session memory) on first run — observe only

## Config Update Triggers

Update the config file when:
- User provides a CPA/ROAS target → switch mode to "fixed"
- Baseline recalibration (every 4th analysis)
- Platform added/removed
- Budget changes
- Account ID changes
