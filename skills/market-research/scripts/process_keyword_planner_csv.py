#!/usr/bin/env python3
"""
Google Keyword Planner CSV Processor

Processes CSV exports from Google Keyword Planner's "Get search volumes and forecasts" tool.
Merges multiple CSV files (from batched seed keyword runs), deduplicates, and outputs
a unified keyword dataset for strategy.md and dashboard integration.

Usage:
    python process_keyword_planner_csv.py /path/to/csv1.csv /path/to/csv2.csv --output /path/to/sources/
    python process_keyword_planner_csv.py /path/to/sources/*.csv --output /path/to/sources/ --country AU
    python process_keyword_planner_csv.py /path/to/csv1.csv --clusters /path/to/clusters.json --output /path/to/sources/

Output:
    - {output_dir}/keyword_data_{timestamp}.json  (structured, for dashboard/skill consumption)
    - {output_dir}/keyword_data_{timestamp}.csv   (clean merged CSV)
    - Console summary with cluster analysis
"""

import argparse
import csv
import json
import os
import sys
import re
from datetime import datetime
from typing import Optional, List, Dict, Any


def parse_volume(vol_str: str) -> Optional[int]:
    """Parse Google Keyword Planner volume strings like '1K - 10K', '10', '100 - 1K'."""
    if not vol_str or vol_str.strip() in ('', '-', 'N/A', 'null'):
        return None

    vol_str = vol_str.strip().replace(',', '')

    # Handle range format: "1K - 10K", "100 - 1K"
    if ' - ' in vol_str or '–' in vol_str:
        parts = re.split(r'\s*[-–]\s*', vol_str)
        if len(parts) == 2:
            low = _parse_single_volume(parts[0])
            high = _parse_single_volume(parts[1])
            if low is not None and high is not None:
                return (low + high) // 2  # midpoint
            return low or high

    return _parse_single_volume(vol_str)


def _parse_single_volume(s: str) -> Optional[int]:
    """Parse a single volume value like '1K', '10K', '100', '1M'."""
    s = s.strip().upper()
    if not s:
        return None

    multiplier = 1
    if s.endswith('K'):
        multiplier = 1000
        s = s[:-1]
    elif s.endswith('M'):
        multiplier = 1000000
        s = s[:-1]

    try:
        return int(float(s) * multiplier)
    except (ValueError, TypeError):
        return None


def parse_cpc(cpc_str: str) -> Optional[float]:
    """Parse CPC strings like '$1.23', 'AU$2.50', '1.23'."""
    if not cpc_str or cpc_str.strip() in ('', '-', 'N/A', 'null'):
        return None

    # Remove currency symbols and codes
    cleaned = re.sub(r'[A-Z]{0,3}\$', '', cpc_str.strip())
    cleaned = cleaned.strip()

    try:
        return round(float(cleaned), 2)
    except (ValueError, TypeError):
        return None


def parse_competition(comp_str: str) -> str:
    """Normalize competition values."""
    if not comp_str or comp_str.strip() in ('', '-', 'N/A', 'null'):
        return 'UNKNOWN'

    comp = comp_str.strip().upper()
    if comp in ('LOW', 'MEDIUM', 'HIGH'):
        return comp

    # Try numeric competition index (0-100)
    try:
        val = float(comp)
        if val <= 33:
            return 'LOW'
        elif val <= 66:
            return 'MEDIUM'
        else:
            return 'HIGH'
    except (ValueError, TypeError):
        return comp


def detect_csv_format(headers: List[str]) -> Dict[str, str]:
    """Map CSV column names to our standard fields. Handles different Keyword Planner export formats."""
    header_map = {}
    normalized = [h.strip().lower().replace('\ufeff', '') for h in headers]

    # Keyword column
    for i, h in enumerate(normalized):
        if h in ('keyword', 'keyword (by relevance)', 'search term', 'keyword text', 'keywords'):
            header_map['keyword'] = headers[i].strip()
            break

    # Volume column
    for i, h in enumerate(normalized):
        if h in ('avg. monthly searches', 'search volume', 'avg monthly searches',
                 'average monthly searches', 'monthly searches', 'volume'):
            header_map['volume'] = headers[i].strip()
            break

    # Competition column (text: Low/Medium/High)
    for i, h in enumerate(normalized):
        if h == 'competition':
            header_map['competition'] = headers[i].strip()
            break

    # Competition index (numeric, separate column)
    for i, h in enumerate(normalized):
        if 'competition' in h and ('index' in h or 'indexed' in h):
            header_map['competition_index'] = headers[i].strip()
            break

    # CPC columns
    for i, h in enumerate(normalized):
        if 'top of page bid' in h and 'low' in h:
            header_map['cpc_low'] = headers[i].strip()
        elif 'top of page bid' in h and 'high' in h:
            header_map['cpc_high'] = headers[i].strip()
        elif h in ('suggested bid', 'cpc', 'avg. cpc', 'average cpc'):
            header_map['cpc'] = headers[i].strip()

    return header_map


def read_keyword_planner_csv(filepath: str) -> List[Dict[str, Any]]:
    """Read and parse a Google Keyword Planner CSV export."""
    keywords = []

    # Try different encodings (Google Keyword Planner exports as UTF-16 LE)
    for encoding in ['utf-16', 'utf-16-le', 'utf-8-sig', 'utf-8', 'latin-1', 'cp1252']:
        try:
            with open(filepath, 'r', encoding=encoding) as f:
                # Skip header rows that aren't the column headers
                # Google Keyword Planner sometimes adds metadata rows
                lines = f.readlines()
            # Verify we got actual content (not garbled)
            if lines and '\x00' not in lines[0]:
                break
        except (UnicodeDecodeError, UnicodeError):
            continue
    else:
        print(f"ERROR: Could not read {filepath} with any encoding")
        return []

    # Find the actual header row (first row with 'keyword' in it)
    header_idx = None
    for i, line in enumerate(lines):
        low = line.lower().strip()
        if low.startswith('keyword') and ('search' in low or 'currency' in low or 'competition' in low):
            header_idx = i
            break

    if header_idx is None:
        # Try first row as header
        header_idx = 0

    # Detect delimiter (tab or comma)
    header_line = lines[header_idx] if header_idx < len(lines) else ''
    delimiter = '\t' if '\t' in header_line else ','

    # Parse CSV from header row onwards
    reader = csv.DictReader(lines[header_idx:], delimiter=delimiter)
    headers = reader.fieldnames or []

    if not headers:
        print(f"WARNING: No headers found in {filepath}")
        return []

    field_map = detect_csv_format(headers)

    if 'keyword' not in field_map:
        print(f"WARNING: Could not identify keyword column in {filepath}")
        print(f"  Headers found: {headers}")
        return []

    for row in reader:
        kw = row.get(field_map.get('keyword', ''), '').strip()
        if not kw:
            continue

        entry = {
            'keyword': kw,
            'volume': None,
            'competition': 'UNKNOWN',
            'competition_index': None,
            'cpc_low': None,
            'cpc_high': None,
            'cpc_avg': None,
            'source_file': os.path.basename(filepath)
        }

        # Volume
        if 'volume' in field_map:
            entry['volume'] = parse_volume(row.get(field_map['volume'], ''))

        # Competition
        if 'competition' in field_map:
            entry['competition'] = parse_competition(row.get(field_map['competition'], ''))

        if 'competition_index' in field_map:
            try:
                entry['competition_index'] = int(float(row.get(field_map['competition_index'], '0')))
            except (ValueError, TypeError):
                pass

        # CPC
        if 'cpc_low' in field_map:
            entry['cpc_low'] = parse_cpc(row.get(field_map['cpc_low'], ''))
        if 'cpc_high' in field_map:
            entry['cpc_high'] = parse_cpc(row.get(field_map['cpc_high'], ''))
        if 'cpc' in field_map:
            entry['cpc_avg'] = parse_cpc(row.get(field_map['cpc'], ''))

        # Calculate avg CPC if we have low+high but no avg
        if entry['cpc_avg'] is None and entry['cpc_low'] and entry['cpc_high']:
            entry['cpc_avg'] = round((entry['cpc_low'] + entry['cpc_high']) / 2, 2)

        keywords.append(entry)

    return keywords


def deduplicate(keywords: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Deduplicate keywords, keeping the entry with most data."""
    seen = {}
    for kw in keywords:
        key = kw['keyword'].lower().strip()
        if key not in seen:
            seen[key] = kw
        else:
            # Keep the one with more data (higher volume takes priority, then more CPC data)
            existing = seen[key]
            if kw['volume'] is not None and (existing['volume'] is None or kw['volume'] > existing['volume']):
                seen[key] = kw
            elif kw['cpc_avg'] is not None and existing['cpc_avg'] is None:
                seen[key] = kw

    return list(seen.values())


def classify_cluster(keyword: str) -> str:
    """Auto-classify keyword into clusters based on patterns."""
    kw = keyword.lower()

    if any(t in kw for t in ['price', 'cost', 'how much', 'cheap', 'affordable', 'budget']):
        return 'Price / affordability'
    elif any(t in kw for t in ['buy', 'for sale', 'purchase', 'order']):
        return 'Purchase intent'
    elif any(t in kw for t in ['builder', 'build', 'company', 'manufacturer']):
        return 'Builder / supplier'
    elif any(t in kw for t in ['plan', 'design', 'layout', 'floor plan', 'blueprint']):
        return 'Design / planning'
    elif any(t in kw for t in ['regulation', 'council', 'permit', 'approval', 'clause', 'legal', 'zoning', 'da ']):
        return 'Regulation / compliance'
    elif any(t in kw for t in ['airbnb', 'rental', 'investment', 'income', 'roi', 'str ']):
        return 'STR / investment'
    elif any(t in kw for t in ['granny flat', 'granny', 'secondary dwelling', 'adu', 'backyard']):
        return 'Granny flat / ADU'
    elif any(t in kw for t in ['nsw', 'sydney', 'byron', 'gold coast', 'melbourne', 'brisbane', 'queensland', 'qld', 'victoria', 'vic']):
        return 'Location-specific'
    elif any(t in kw for t in ['luxury', 'architect', 'premium', 'designer', 'custom', 'high end']):
        return 'Design / premium'
    elif any(t in kw for t in ['wheel', 'mobile', 'relocat', 'transport', 'moveable', 'portable']):
        return 'Mobility / THOW'
    elif any(t in kw for t in ['modular', 'prefab', 'kit']):
        return 'Modular / prefab'
    elif any(t in kw for t in ['tiny house', 'tiny home', 'tiny living', 'small house', 'small home']):
        return 'Core tiny home'
    else:
        return 'Other'


def generate_seed_keywords(client_context: Optional[Dict] = None) -> List[List[str]]:
    """
    Generate 3 batches of 10 seed keywords for Keyword Planner.

    Batch design principles:
    - 10 keywords per batch (Keyword Planner limit for "Get search volumes")
    - Each batch targets a different intent cluster to minimize overlap in suggestions
    - Batch 1: Core product + purchase intent (highest commercial value)
    - Batch 2: Adjacent category + secondary dwellings (capture broader demand)
    - Batch 3: Location + investment + regulation (long-tail, high-intent)

    If client_context is provided, keywords are customized. Otherwise, generic templates.
    """
    # Default AU tiny home context — override with client_context if provided
    product = client_context.get('product', 'tiny house') if client_context else 'tiny house'
    country = client_context.get('country', 'AU') if client_context else 'AU'
    locations = client_context.get('locations', ['NSW', 'Byron Bay']) if client_context else []
    adjacents = client_context.get('adjacent_categories', ['granny flat', 'modular home']) if client_context else []

    batch_1 = [
        product,
        f"{product} for sale",
        f"{product} on wheels",
        f"{product} builder Australia",
        "small house design",
        f"prefab {product.replace('house', 'home') if 'house' in product else product}",
        f"luxury {product.replace('house', 'home') if 'house' in product else product}",
        f"architect designed {product}",
        f"mobile {product}",
        f"{product} cost"
    ]

    batch_2 = [
        adjacents[0] if adjacents else "granny flat",
        f"{adjacents[0]} builder" if adjacents else "granny flat builder",
        f"{adjacents[0]} cost" if adjacents else "granny flat cost",
        "secondary dwelling NSW",
        "backyard cabin",
        f"{adjacents[1]} Australia" if len(adjacents) > 1 else "modular home Australia",
        "relocatable home",
        f"{adjacents[0]} plans" if adjacents else "granny flat plans",
        f"prefab {adjacents[0]}" if adjacents else "prefab granny flat",
        "ADU Australia"
    ]

    batch_3 = [
        f"{product} {locations[0]}" if locations else f"{product} NSW",
        f"{product.replace('house', 'home') if 'house' in product else product} {locations[1]}" if len(locations) > 1 else f"{product} Sydney",
        f"{product} Airbnb",
        f"{product.replace('house', 'home') if 'house' in product else product} investment",
        f"{product} regulations NSW",
        f"tiny homes Sydney",
        f"{adjacents[0]} NSW" if adjacents else "granny flat NSW",
        "Clause 77 moveable dwelling",
        f"{product} Gold Coast",
        f"retreat house tiny home"  # client brand + product
    ]

    return [batch_1, batch_2, batch_3]


def main():
    parser = argparse.ArgumentParser(description='Process Google Keyword Planner CSV exports')
    parser.add_argument('csvs', nargs='*', help='CSV file paths to process')
    parser.add_argument('--output', '-o', required=True, help='Output directory')
    parser.add_argument('--country', default='AU', help='Country code (default: AU)')
    parser.add_argument('--generate-seeds', action='store_true', help='Print seed keyword batches instead of processing CSVs')
    parser.add_argument('--client-context', help='JSON file with client context for seed generation')
    parser.add_argument('--min-volume', type=int, default=0, help='Minimum volume threshold (default: 0)')

    args = parser.parse_args()

    # Seed generation mode
    if args.generate_seeds:
        context = None
        if args.client_context and os.path.exists(args.client_context):
            with open(args.client_context, 'r') as f:
                context = json.load(f)

        batches = generate_seed_keywords(context)
        for i, batch in enumerate(batches, 1):
            print(f"\n--- Batch {i} (copy-paste into Keyword Planner) ---")
            print('\n'.join(batch))
        return

    # CSV processing mode
    if not args.csvs:
        parser.error("Provide CSV file paths or use --generate-seeds")

    # Read and merge all CSVs
    all_keywords = []
    for csv_path in args.csvs:
        if not os.path.exists(csv_path):
            print(f"WARNING: File not found: {csv_path}")
            continue

        keywords = read_keyword_planner_csv(csv_path)
        print(f"Read {len(keywords)} keywords from {os.path.basename(csv_path)}")
        all_keywords.extend(keywords)

    if not all_keywords:
        print("ERROR: No keywords found in any CSV file")
        sys.exit(1)

    # Deduplicate
    unique = deduplicate(all_keywords)
    print(f"\nTotal: {len(all_keywords)} raw → {len(unique)} unique keywords")

    # Filter by minimum volume
    if args.min_volume > 0:
        filtered = [k for k in unique if k['volume'] is not None and k['volume'] >= args.min_volume]
        print(f"After volume filter (>={args.min_volume}): {len(filtered)} keywords")
        unique = filtered

    # Classify into clusters
    for kw in unique:
        kw['cluster'] = classify_cluster(kw['keyword'])

    # Sort by volume (highest first), nulls last
    unique.sort(key=lambda x: (x['volume'] is None, -(x['volume'] or 0)))

    # Generate outputs
    os.makedirs(args.output, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # JSON output
    json_path = os.path.join(args.output, f'keyword_data_{timestamp}.json')
    output_data = {
        'metadata': {
            'generated': datetime.now().isoformat(),
            'country': args.country,
            'total_keywords': len(unique),
            'source_files': list(set(k['source_file'] for k in unique)),
            'clusters': {}
        },
        'keywords': unique
    }

    # Cluster summary
    clusters = {}
    for kw in unique:
        c = kw['cluster']
        if c not in clusters:
            clusters[c] = {'count': 0, 'total_volume': 0, 'keywords': []}
        clusters[c]['count'] += 1
        if kw['volume']:
            clusters[c]['total_volume'] += kw['volume']
        clusters[c]['keywords'].append(kw['keyword'])

    output_data['metadata']['clusters'] = {
        c: {'count': v['count'], 'total_volume': v['total_volume']}
        for c, v in sorted(clusters.items(), key=lambda x: -x[1]['total_volume'])
    }

    with open(json_path, 'w') as f:
        json.dump(output_data, f, indent=2)

    # CSV output
    csv_path = os.path.join(args.output, f'keyword_data_{timestamp}.csv')
    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Keyword', 'Cluster', 'Avg Monthly Volume', 'Competition',
                         'Competition Index', 'CPC Low', 'CPC High', 'CPC Avg'])
        for kw in unique:
            writer.writerow([
                kw['keyword'], kw['cluster'], kw['volume'] or '',
                kw['competition'], kw['competition_index'] or '',
                kw['cpc_low'] or '', kw['cpc_high'] or '', kw['cpc_avg'] or ''
            ])

    # Console summary
    print(f"\n{'='*60}")
    print(f"KEYWORD DATA SUMMARY — {args.country}")
    print(f"{'='*60}")
    print(f"Total unique keywords: {len(unique)}")
    print(f"Keywords with volume data: {sum(1 for k in unique if k['volume'])}")
    print(f"Keywords with CPC data: {sum(1 for k in unique if k['cpc_avg'])}")

    print(f"\n--- Cluster Breakdown ---")
    for cluster, data in sorted(clusters.items(), key=lambda x: -x[1]['total_volume']):
        print(f"  {cluster}: {data['count']} kw, {data['total_volume']:,} total vol/mo")

    print(f"\n--- Top 20 by Volume ---")
    for kw in unique[:20]:
        vol = f"{kw['volume']:>8,}" if kw['volume'] else "    BLANK"
        cpc = f"${kw['cpc_avg']:.2f}" if kw['cpc_avg'] else "  N/A"
        comp = kw['competition'][:3]
        print(f"  {vol}  {comp:>3}  {cpc:>7}  {kw['keyword']}")

    print(f"\n--- Output Files ---")
    print(f"  JSON: {json_path}")
    print(f"  CSV:  {csv_path}")

    # Generate markdown table for strategy.md update
    print(f"\n--- Markdown Table (for strategy.md) ---")
    print("| Cluster | Top Keywords | Volume (AU) | CPC Range |")
    print("|---|---|---|---|")
    for cluster, data in sorted(clusters.items(), key=lambda x: -x[1]['total_volume']):
        top_kws = sorted(
            [k for k in unique if k['cluster'] == cluster and k['volume']],
            key=lambda x: -(x['volume'] or 0)
        )[:3]
        kw_str = ', '.join(f'"{k["keyword"]}"' for k in top_kws)
        vol_str = f"{data['total_volume']:,}/mo" if data['total_volume'] else 'BLANK'
        cpcs = [k['cpc_avg'] for k in top_kws if k['cpc_avg']]
        cpc_str = f"${min(cpcs):.2f}–${max(cpcs):.2f}" if cpcs else 'BLANK'
        print(f"| {cluster} | {kw_str} | {vol_str} | {cpc_str} |")


if __name__ == '__main__':
    main()
