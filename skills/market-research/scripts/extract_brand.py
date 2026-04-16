#!/usr/bin/env python3
"""Brand extraction wrapper — delegates to the canonical implementation in business-analysis.
Market-research skill uses the same brand extraction logic to ensure consistency.

The business-analysis version (1225 lines) is the single source of truth, with WP filters,
anomaly detection, prominence scoring, and external CSS parsing. This wrapper imports from
it so bug fixes propagate automatically to both skills."""

import sys
import os

# Add business-analysis scripts to path
BA_SCRIPTS = os.path.join(os.path.dirname(__file__), '..', '..', 'business-analysis', 'scripts')
sys.path.insert(0, os.path.abspath(BA_SCRIPTS))

from extract_brand import extract_brand

if __name__ == "__main__":
    import json
    if len(sys.argv) < 2:
        print("Usage: extract_brand.py <url>", file=sys.stderr)
        sys.exit(1)
    url = sys.argv[1]
    if not url.startswith("http"):
        url = "https://" + url
    result = extract_brand(url)
    print(json.dumps(result, indent=2))
