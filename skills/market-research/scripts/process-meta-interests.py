#!/usr/bin/env python3
"""
Meta Ads Interest Database Processor

Processes raw Meta interest data from eachspy.com API batches:
- Parses raw interest strings
- Deduplicates by Interest Name (keeps first occurrence)
- Filters out noise (entertainment, games, athletes, universities)
- Sorts by Audience High descending
- Exports clean CSV

Usage:
    python3 process-meta-interests.py <input_file> <output_file>

Or programmatically:
    from process_meta_interests import InterestProcessor
    processor = InterestProcessor()
    processor.add_batch(raw_data)
    processor.export_csv('output.csv')
"""

import csv
import sys
from collections import OrderedDict
from pathlib import Path


class InterestProcessor:
    """Process and deduplicate Meta Ads interests."""

    # Noise keywords to filter out
    NOISE_KEYWORDS = {
        'movie', 'film', 'tv', 'television', 'show', 'series', 'actor', 'actress',
        'musician', 'band', 'singer', 'rapper', 'comedian', 'celebrity',
        'game', 'gaming', 'video game', 'esports', 'twitch',
        'university', 'college', 'school', 'student',
        'athlete', 'player', 'coach', 'team member',
        'character', 'fictional', 'anime', 'manga', 'cartoon'
    }

    def __init__(self):
        self.interests = OrderedDict()  # name -> {low, high, category, source}

    def add_batch(self, raw_data, source_name='api'):
        """
        Add a batch of interests from raw data string.

        Expected format per line:
        Interest Name|1000000|2000000|Category
        or
        Interest Name,1000000,2000000,Category
        """
        lines = raw_data.strip().split('\n')

        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            # Try pipe-delimited first, then comma
            parts = line.split('|') if '|' in line else line.split(',')
            if len(parts) < 4:
                continue

            try:
                name = parts[0].strip().strip('"')
                low = int(parts[1].strip().replace(',', ''))
                high = int(parts[2].strip().replace(',', ''))
                category = parts[3].strip().strip('"')
                source = parts[4].strip() if len(parts) > 4 else source_name

                # Filter noise
                if self.is_noise(name):
                    continue

                # Deduplicate: keep first occurrence
                if name not in self.interests:
                    self.interests[name] = {
                        'low': low,
                        'high': high,
                        'category': category,
                        'source': source
                    }
            except (ValueError, IndexError):
                continue

    def is_noise(self, name):
        """Check if interest matches noise patterns."""
        name_lower = name.lower()
        return any(keyword in name_lower for keyword in self.NOISE_KEYWORDS)

    def sort_by_audience(self, descending=True):
        """Sort interests by Audience High."""
        sorted_items = sorted(
            self.interests.items(),
            key=lambda x: x[1]['high'],
            reverse=descending
        )
        self.interests = OrderedDict(sorted_items)

    def export_csv(self, output_path):
        """Export interests to CSV."""
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Interest Name', 'Audience Low', 'Audience High', 'Category', 'Keyword Source'])

            for name, data in self.interests.items():
                writer.writerow([
                    name,
                    data['low'],
                    data['high'],
                    data['category'],
                    data['source']
                ])

        print(f"Exported {len(self.interests)} interests to {output_path}")

    def get_stats(self):
        """Return processing statistics."""
        if not self.interests:
            return {'total': 0, 'avg_low': 0, 'avg_high': 0, 'median_high': 0}

        highs = [d['high'] for d in self.interests.values()]
        lows = [d['low'] for d in self.interests.values()]

        return {
            'total': len(self.interests),
            'avg_low': sum(lows) // len(lows),
            'avg_high': sum(highs) // len(highs),
            'median_high': sorted(highs)[len(highs) // 2],
            'min_high': min(highs),
            'max_high': max(highs),
        }


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 process-meta-interests.py <input_file> <output_file>")
        print("\nInput format (CSV or pipe-delimited):")
        print("  Interest Name,Audience Low,Audience High,Category[,Keyword Source]")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    processor = InterestProcessor()

    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            raw_data = f.read()

        processor.add_batch(raw_data)
        processor.sort_by_audience()
        processor.export_csv(output_file)

        stats = processor.get_stats()
        print(f"\nProcessing Stats:")
        print(f"  Total interests: {stats['total']}")
        print(f"  Audience range: {stats['min_high']:,} - {stats['max_high']:,}")
        print(f"  Average high: {stats['avg_high']:,}")
        print(f"  Median high: {stats['median_high']:,}")

    except FileNotFoundError:
        print(f"Error: File not found: {input_file}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
