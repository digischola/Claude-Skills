#!/usr/bin/env python3
"""
Google Keyword Volume Fetcher
Uses Google Ads API KeywordPlanIdeaService to get search volume data.

Usage:
    python google_keyword_volume.py --customer-id 1234567890 --keywords "tiny house NSW,granny flat builder,tiny home Byron Bay" --output /path/to/output
    python google_keyword_volume.py --customer-id 1234567890 --file keywords.txt --output /path/to/output --country AU
    python google_keyword_volume.py --customer-id 1234567890 --keywords "test keyword" --dry-run
    python google_keyword_volume.py --customer-id 1234567890 --file keywords.txt --exact-only --output ./output

Setup:
    1. pip install google-ads
    2. Create ~/google-ads.yaml with credentials (see references/google-ads-api-setup.md)
    3. Ensure developer token has Basic access

Output:
    - {output_dir}/keyword_volume_{timestamp}.json  (for dashboard integration)
    - {output_dir}/keyword_volume_{timestamp}.csv   (for easy reading)
    - Console summary (pretty-printed)
"""

import argparse
import csv
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Google Ads geo target constants — country code → geo target ID
COUNTRY_GEO_TARGETS = {
    "AU": "2036",    # Australia
    "US": "2840",    # United States
    "UK": "2826",    # United Kingdom
    "GB": "2826",    # United Kingdom (alias)
    "CA": "2124",    # Canada
    "NZ": "2554",    # New Zealand
    "IN": "2356",    # India
    "SG": "2702",    # Singapore
}

# Language code → language criterion ID
LANGUAGE_CODES = {
    "en": "1000",    # English
    "es": "1003",    # Spanish
    "fr": "1002",    # French
    "de": "1001",    # German
    "hi": "1023",    # Hindi
    "zh": "1017",    # Chinese (Simplified)
}

BATCH_SIZE = 10          # Max keywords per API request (conservative for quota)
BATCH_DELAY_SECONDS = 2  # Sleep between batches to avoid rate limiting
MICROS_PER_UNIT = 1_000_000  # Google Ads uses micros (1 AUD = 1,000,000 micros)

# Google Ads API version — update when upgrading
GOOGLE_ADS_API_VERSION = "v19"

logger = logging.getLogger("google_keyword_volume")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def setup_logging(verbose: bool = False) -> None:
    """Configure logging with appropriate level and format."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def micros_to_currency(micros: int) -> float:
    """Convert Google Ads micros to currency units (e.g. AUD)."""
    if micros is None or micros == 0:
        return 0.0
    return round(micros / MICROS_PER_UNIT, 2)


def sanitize_customer_id(raw: str) -> str:
    """Strip dashes and whitespace from customer ID. Returns digits only."""
    return raw.replace("-", "").replace(" ", "").strip()


def load_keywords_from_file(filepath: str) -> list[str]:
    """Load keywords from a text file (one per line, or comma-separated)."""
    path = Path(filepath)
    if not path.exists():
        logger.error(f"Keyword file not found: {filepath}")
        sys.exit(1)

    content = path.read_text(encoding="utf-8").strip()
    # Support both one-per-line and comma-separated
    if "\n" in content:
        keywords = [k.strip() for k in content.splitlines() if k.strip()]
    else:
        keywords = [k.strip() for k in content.split(",") if k.strip()]

    logger.info(f"Loaded {len(keywords)} keywords from {filepath}")
    return keywords


def chunk_list(lst: list, size: int) -> list[list]:
    """Split a list into chunks of given size."""
    return [lst[i:i + size] for i in range(0, len(lst), size)]


def competition_label(competition_index: int) -> str:
    """Map competition index (0-100) to LOW/MEDIUM/HIGH label."""
    if competition_index is None:
        return "UNKNOWN"
    if competition_index <= 33:
        return "LOW"
    elif competition_index <= 66:
        return "MEDIUM"
    else:
        return "HIGH"


# ---------------------------------------------------------------------------
# Google Ads API Client
# ---------------------------------------------------------------------------

def create_google_ads_client(config_path: str = None):
    """
    Create and return a GoogleAdsClient from yaml config.
    Default config path: ~/google-ads.yaml
    """
    try:
        from google.ads.googleads.client import GoogleAdsClient
    except ImportError:
        logger.error(
            "google-ads library not installed.\n"
            "Run: pip install google-ads\n"
            "See references/google-ads-api-setup.md for full setup."
        )
        sys.exit(1)

    if config_path is None:
        config_path = os.path.expanduser("~/google-ads.yaml")

    if not os.path.exists(config_path):
        logger.error(
            f"Google Ads config not found at {config_path}\n"
            "Create ~/google-ads.yaml with your credentials.\n"
            "See references/google-ads-api-setup.md for setup steps."
        )
        sys.exit(1)

    try:
        client = GoogleAdsClient.load_from_storage(config_path)
        logger.info("Google Ads client initialized successfully.")
        return client
    except Exception as e:
        error_msg = str(e).lower()
        if "authentication" in error_msg or "oauth" in error_msg or "token" in error_msg:
            logger.error(
                f"Authentication error: {e}\n\n"
                "Common fixes:\n"
                "1. Check refresh_token in ~/google-ads.yaml is current\n"
                "2. Verify client_id and client_secret match your GCP project\n"
                "3. Ensure developer_token is present\n"
                "4. Re-generate refresh token: google-ads-api authenticate"
            )
        else:
            logger.error(f"Failed to create Google Ads client: {e}")
        sys.exit(1)


def fetch_keyword_ideas(
    client,
    customer_id: str,
    keywords: list[str],
    geo_target_id: str,
    language_id: str,
    exact_only: bool = False,
) -> list[dict]:
    """
    Call KeywordPlanIdeaService.generate_keyword_ideas for a batch of keywords.
    Returns a list of dicts with keyword metrics.

    Uses GOOGLE_SEARCH network and the specified geo + language targeting.
    When exact_only=True, filters results to only the input keywords.
    """
    keyword_plan_idea_service = client.get_service("KeywordPlanIdeaService")

    # Build the request
    request = client.get_type("GenerateKeywordIdeasRequest")
    request.customer_id = customer_id
    request.language = client.get_service("GoogleAdsService").language_constant_path(language_id)
    request.geo_target_constants.append(
        client.get_service("GoogleAdsService").geo_target_constant_path(geo_target_id)
    )
    request.keyword_plan_network = client.enums.KeywordPlanNetworkEnum.GOOGLE_SEARCH

    # Set seed keywords
    request.keyword_seed.keywords.extend(keywords)

    # Include average monthly searches
    request.include_adult_keywords = False

    results = []
    input_keywords_lower = {k.lower() for k in keywords}

    try:
        response = keyword_plan_idea_service.generate_keyword_ideas(request=request)

        for idea in response:
            keyword_text = idea.text
            metrics = idea.keyword_idea_metrics

            # Filter to exact input keywords if requested
            if exact_only and keyword_text.lower() not in input_keywords_lower:
                continue

            # Extract monthly search volumes (last 12 months)
            monthly_volumes = []
            if metrics.monthly_search_volumes:
                for mv in metrics.monthly_search_volumes:
                    monthly_volumes.append({
                        "year": mv.year,
                        "month": mv.month.name if hasattr(mv.month, "name") else str(mv.month),
                        "monthly_searches": mv.monthly_searches if mv.monthly_searches else 0,
                    })

            # Competition level from enum
            comp_enum = metrics.competition
            if hasattr(comp_enum, "name"):
                competition_level = comp_enum.name  # LOW, MEDIUM, HIGH, UNSPECIFIED
            else:
                competition_level = str(comp_enum)

            result = {
                "keyword": keyword_text,
                "avg_monthly_searches": metrics.avg_monthly_searches if metrics.avg_monthly_searches else 0,
                "competition": competition_level,
                "competition_index": metrics.competition_index if metrics.competition_index else None,
                "low_top_of_page_bid_micros": metrics.low_top_of_page_bid_micros if metrics.low_top_of_page_bid_micros else 0,
                "high_top_of_page_bid_micros": metrics.high_top_of_page_bid_micros if metrics.high_top_of_page_bid_micros else 0,
                "low_cpc_aud": micros_to_currency(metrics.low_top_of_page_bid_micros if metrics.low_top_of_page_bid_micros else 0),
                "high_cpc_aud": micros_to_currency(metrics.high_top_of_page_bid_micros if metrics.high_top_of_page_bid_micros else 0),
                "monthly_volumes": monthly_volumes,
                "is_seed_keyword": keyword_text.lower() in input_keywords_lower,
            }
            results.append(result)

    except Exception as e:
        _handle_api_error(e, keywords)

    return results


def _handle_api_error(error, keywords: list[str]) -> None:
    """Parse Google Ads API errors and provide actionable messages."""
    error_str = str(error).lower()

    if "quota" in error_str or "rate" in error_str:
        logger.error(
            f"Quota/rate limit exceeded.\n"
            f"Keywords in failed batch: {keywords}\n"
            f"Wait a few minutes and retry, or reduce batch size.\n"
            f"Error: {error}"
        )
    elif "customer_id" in error_str or "customer-id" in error_str or "not found" in error_str:
        logger.error(
            f"Invalid customer ID or account not accessible.\n"
            f"Ensure the customer-id belongs to an active Google Ads account\n"
            f"linked to your MCC. Format: 10 digits, no dashes.\n"
            f"Error: {error}"
        )
    elif "authorization" in error_str or "permission" in error_str or "access" in error_str:
        logger.error(
            f"Authorization error — your developer token may lack access,\n"
            f"or the account is not linked to your MCC.\n"
            f"Check: developer token access level (Basic required),\n"
            f"MCC → client account link, OAuth scopes.\n"
            f"Error: {error}"
        )
    elif "developer_token" in error_str or "developer token" in error_str:
        logger.error(
            f"Developer token issue. Ensure your ~/google-ads.yaml has a valid\n"
            f"developer_token. Test tokens only work with test accounts.\n"
            f"Error: {error}"
        )
    else:
        logger.error(f"Google Ads API error: {error}")

    # Don't exit — let the caller decide whether to continue with partial results


# ---------------------------------------------------------------------------
# Output Writers
# ---------------------------------------------------------------------------

def write_json(results: list[dict], output_path: str) -> str:
    """Write results to a JSON file. Returns the file path."""
    output = {
        "generated_at": datetime.now().isoformat(),
        "total_keywords": len(results),
        "seed_keywords": len([r for r in results if r.get("is_seed_keyword")]),
        "suggested_keywords": len([r for r in results if not r.get("is_seed_keyword")]),
        "keywords": results,
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    logger.info(f"JSON output: {output_path}")
    return output_path


def write_csv(results: list[dict], output_path: str) -> str:
    """Write results to a CSV file. Returns the file path."""
    fieldnames = [
        "keyword",
        "avg_monthly_searches",
        "competition",
        "competition_index",
        "low_cpc_aud",
        "high_cpc_aud",
        "is_seed_keyword",
    ]
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in results:
            writer.writerow({k: row.get(k, "") for k in fieldnames})
    logger.info(f"CSV output: {output_path}")
    return output_path


def print_console_summary(results: list[dict], exact_only: bool) -> None:
    """Pretty-print a summary table to console."""
    if not results:
        print("\nNo results returned.")
        return

    seed_results = [r for r in results if r.get("is_seed_keyword")]
    suggested_results = [r for r in results if not r.get("is_seed_keyword")]

    print("\n" + "=" * 90)
    print("KEYWORD VOLUME RESULTS")
    print("=" * 90)

    def print_keyword_table(keyword_list: list[dict], header: str) -> None:
        if not keyword_list:
            return
        print(f"\n--- {header} ({len(keyword_list)}) ---\n")
        print(f"{'Keyword':<45} {'Vol':>8} {'Comp':>8} {'Low CPC':>9} {'High CPC':>9}")
        print("-" * 82)
        # Sort by volume descending
        for r in sorted(keyword_list, key=lambda x: x.get("avg_monthly_searches", 0), reverse=True):
            vol = f"{r['avg_monthly_searches']:,}" if r['avg_monthly_searches'] else "N/A"
            comp = r.get("competition", "N/A")
            low = f"${r['low_cpc_aud']:.2f}" if r['low_cpc_aud'] else "N/A"
            high = f"${r['high_cpc_aud']:.2f}" if r['high_cpc_aud'] else "N/A"
            kw = r["keyword"][:44]
            print(f"{kw:<45} {vol:>8} {comp:>8} {low:>9} {high:>9}")

    print_keyword_table(seed_results, "Seed Keywords")

    if not exact_only and suggested_results:
        print_keyword_table(suggested_results[:30], "Suggested Keywords (top 30 by volume)")

    # Summary stats
    all_vols = [r["avg_monthly_searches"] for r in results if r["avg_monthly_searches"]]
    all_cpcs = [r["high_cpc_aud"] for r in results if r["high_cpc_aud"]]

    print(f"\n--- Summary ---")
    print(f"Total keywords: {len(results)} ({len(seed_results)} seed, {len(suggested_results)} suggested)")
    if all_vols:
        print(f"Volume range: {min(all_vols):,} - {max(all_vols):,}")
        print(f"Avg volume: {sum(all_vols) / len(all_vols):,.0f}")
    if all_cpcs:
        print(f"CPC range (high bid): ${min(all_cpcs):.2f} - ${max(all_cpcs):.2f}")
    print("=" * 90)


# ---------------------------------------------------------------------------
# Dry Run
# ---------------------------------------------------------------------------

def dry_run_summary(keywords: list[str], customer_id: str, country: str, language: str,
                    geo_target_id: str, language_id: str, exact_only: bool, output_dir: str) -> None:
    """Show what would be queried without making API calls."""
    batches = chunk_list(keywords, BATCH_SIZE)
    print("\n" + "=" * 60)
    print("DRY RUN — No API calls will be made")
    print("=" * 60)
    print(f"Customer ID:    {customer_id}")
    print(f"Country:        {country} (geo target: {geo_target_id})")
    print(f"Language:       {language} (criterion: {language_id})")
    print(f"Exact only:     {exact_only}")
    print(f"Output dir:     {output_dir}")
    print(f"Total keywords: {len(keywords)}")
    print(f"Batches:        {len(batches)} (max {BATCH_SIZE} per request)")
    print(f"Est. API calls: {len(batches)}")
    print(f"Est. time:      ~{len(batches) * BATCH_DELAY_SECONDS}s (with rate limiting)")
    print(f"\nKeywords to query:")
    for i, kw in enumerate(keywords, 1):
        print(f"  {i:3d}. {kw}")
    print(f"\nBatch breakdown:")
    for i, batch in enumerate(batches, 1):
        print(f"  Batch {i}: {', '.join(batch)}")
    print("=" * 60)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fetch keyword search volume data from Google Ads API.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    # Required
    parser.add_argument(
        "--customer-id",
        required=True,
        help="Google Ads customer ID (10 digits, dashes ok). Use the client's account ID, not MCC.",
    )

    # Keyword input (one required)
    kw_group = parser.add_mutually_exclusive_group(required=True)
    kw_group.add_argument(
        "--keywords",
        help="Comma-separated list of keywords (e.g. 'tiny house NSW,granny flat builder').",
    )
    kw_group.add_argument(
        "--file",
        help="Path to text file with keywords (one per line or comma-separated).",
    )

    # Optional
    parser.add_argument(
        "--output",
        default=".",
        help="Output directory for JSON and CSV files (default: current directory).",
    )
    parser.add_argument(
        "--country",
        default="AU",
        help="Country code for geo targeting (default: AU). Supported: AU, US, UK, CA, NZ, IN, SG.",
    )
    parser.add_argument(
        "--language",
        default="en",
        help="Language code (default: en). Supported: en, es, fr, de, hi, zh.",
    )
    parser.add_argument(
        "--exact-only",
        action="store_true",
        help="Only return metrics for the exact input keywords (no suggestions).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be queried without making API calls.",
    )
    parser.add_argument(
        "--config",
        default=None,
        help="Path to google-ads.yaml config file (default: ~/google-ads.yaml).",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable debug logging.",
    )

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    setup_logging(verbose=args.verbose)

    # Parse customer ID
    customer_id = sanitize_customer_id(args.customer_id)
    if len(customer_id) != 10 or not customer_id.isdigit():
        logger.error(f"Invalid customer ID: '{args.customer_id}'. Must be exactly 10 digits.")
        sys.exit(1)

    # Parse keywords
    if args.keywords:
        keywords = [k.strip() for k in args.keywords.split(",") if k.strip()]
    else:
        keywords = load_keywords_from_file(args.file)

    if not keywords:
        logger.error("No keywords provided.")
        sys.exit(1)

    # Resolve geo target
    country = args.country.upper()
    geo_target_id = COUNTRY_GEO_TARGETS.get(country)
    if not geo_target_id:
        logger.error(
            f"Unsupported country code: {country}\n"
            f"Supported: {', '.join(sorted(COUNTRY_GEO_TARGETS.keys()))}"
        )
        sys.exit(1)

    # Resolve language
    language = args.language.lower()
    language_id = LANGUAGE_CODES.get(language)
    if not language_id:
        logger.error(
            f"Unsupported language code: {language}\n"
            f"Supported: {', '.join(sorted(LANGUAGE_CODES.keys()))}"
        )
        sys.exit(1)

    # Output directory
    output_dir = os.path.abspath(args.output)
    os.makedirs(output_dir, exist_ok=True)

    # Dry run
    if args.dry_run:
        dry_run_summary(keywords, customer_id, country, language,
                        geo_target_id, language_id, args.exact_only, output_dir)
        sys.exit(0)

    # Initialize client
    client = create_google_ads_client(config_path=args.config)

    # Batch keywords and fetch
    batches = chunk_list(keywords, BATCH_SIZE)
    all_results = []
    seen_keywords = set()  # Deduplicate across batches

    logger.info(f"Fetching keyword data: {len(keywords)} keywords in {len(batches)} batch(es)")

    for i, batch in enumerate(batches, 1):
        logger.info(f"Batch {i}/{len(batches)}: {', '.join(batch)}")

        try:
            batch_results = fetch_keyword_ideas(
                client=client,
                customer_id=customer_id,
                keywords=batch,
                geo_target_id=geo_target_id,
                language_id=language_id,
                exact_only=args.exact_only,
            )

            # Deduplicate (same keyword can appear from different seed batches)
            for result in batch_results:
                kw_lower = result["keyword"].lower()
                if kw_lower not in seen_keywords:
                    seen_keywords.add(kw_lower)
                    all_results.append(result)

            logger.info(f"  Got {len(batch_results)} results ({len(all_results)} total unique)")

        except Exception as e:
            logger.error(f"  Batch {i} failed: {e}")
            # Continue with remaining batches

        # Rate limit between batches (skip after last batch)
        if i < len(batches):
            logger.debug(f"  Sleeping {BATCH_DELAY_SECONDS}s before next batch...")
            time.sleep(BATCH_DELAY_SECONDS)

    if not all_results:
        logger.warning("No results returned from any batch. Check credentials, customer ID, and keyword validity.")
        sys.exit(1)

    # Sort by volume descending
    all_results.sort(key=lambda x: x.get("avg_monthly_searches", 0), reverse=True)

    # Write outputs
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = os.path.join(output_dir, f"keyword_volume_{timestamp}.json")
    csv_path = os.path.join(output_dir, f"keyword_volume_{timestamp}.csv")

    write_json(all_results, json_path)
    write_csv(all_results, csv_path)

    # Console summary
    print_console_summary(all_results, args.exact_only)

    print(f"\nFiles saved:")
    print(f"  JSON: {json_path}")
    print(f"  CSV:  {csv_path}")


if __name__ == "__main__":
    main()
