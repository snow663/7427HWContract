#!/usr/bin/env python3
"""Convert 7427 `$3FCE` EFI pulsewidth command counts to milliseconds.

Working hypothesis:
  `$3FCE/$3FCF` stores a 16-bit EFI PW command in 1/65536 second units.

Conversions:
  ms = counts / 65.536
  counts = round(ms * 65.536)
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

COUNTS_PER_SECOND = 65536.0
COUNTS_PER_MS = COUNTS_PER_SECOND / 1000.0
US_PER_COUNT = 1_000_000.0 / COUNTS_PER_SECOND


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def resolve_path(path: str | Path) -> Path:
    p = Path(path)
    return p if p.is_absolute() else repo_root() / p


def parse_count(value: str) -> int:
    value = value.strip().lower()
    if value.startswith('$'):
        return int(value[1:], 16)
    if value.startswith('0x'):
        return int(value, 16)
    return int(value, 10)


def counts_to_ms(counts: int) -> float:
    return counts / COUNTS_PER_MS


def ms_to_counts(ms: float) -> int:
    return int(round(ms * COUNTS_PER_MS))


def print_count(counts: int) -> None:
    print(f'counts_dec: {counts}')
    print(f'counts_hex: 0x{counts:04X}')
    print(f'ms: {counts_to_ms(counts):.6f}')
    print(f'us: {counts_to_ms(counts) * 1000.0:.3f}')


def print_ms(ms: float) -> None:
    counts = ms_to_counts(ms)
    print(f'ms: {ms:.6f}')
    print(f'counts_dec: {counts}')
    print(f'counts_hex: 0x{counts:04X}')
    print(f'roundtrip_ms: {counts_to_ms(counts):.6f}')


def print_table(path: Path) -> None:
    with path.open(newline='', encoding='utf-8-sig') as f:
        rows = list(csv.DictReader(f))
    fields = ['name', 'counts_hex', 'counts_dec', 'expected_ms', 'calc_ms', 'error_ms', 'notes']
    writer = csv.DictWriter(__import__('sys').stdout, fieldnames=fields)
    writer.writeheader()
    for row in rows:
        counts = parse_count(row['counts_hex']) if row.get('counts_hex') else int(row['counts_dec'])
        calc = counts_to_ms(counts)
        expected = float(row['expected_ms'])
        writer.writerow({
            'name': row.get('name', ''),
            'counts_hex': f'0x{counts:04X}',
            'counts_dec': counts,
            'expected_ms': row.get('expected_ms', ''),
            'calc_ms': f'{calc:.6f}',
            'error_ms': f'{calc - expected:+.6f}',
            'notes': row.get('notes', ''),
        })


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument('--ms', type=float, help='convert milliseconds to 16-bit `$3FCE` counts')
    group.add_argument('--counts', help='convert count value to milliseconds, e.g. 0x00C5 or 197')
    group.add_argument('--table', help='read test-vector CSV and append calculated values')
    args = ap.parse_args()

    if args.ms is not None:
        print_ms(args.ms)
    elif args.counts is not None:
        print_count(parse_count(args.counts))
    else:
        print_table(resolve_path(args.table))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
