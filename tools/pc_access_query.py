#!/usr/bin/env python3
"""Query a 7427 hardware-access CSV by address, subsystem, PC, routine, or class."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Iterable


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def resolve_path(path: str | Path) -> Path:
    p = Path(path)
    return p if p.is_absolute() else repo_root() / p


def parse_int(value: str) -> int:
    value = value.strip().lower()
    if value.startswith('$'):
        return int(value[1:], 16)
    if value.startswith('0x'):
        return int(value, 16)
    return int(value, 16 if any(c in value for c in 'abcdef') else 10)


def addr_matches(field: str, wanted: int) -> bool:
    field = (field or '').strip()
    if not field:
        return False
    if '-' in field:
        left, right = field.split('-', 1)
        try:
            return parse_int(left) <= wanted <= parse_int(right)
        except ValueError:
            return False
    try:
        return parse_int(field) == wanted
    except ValueError:
        return False


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline='', encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))


def select_rows(rows: Iterable[dict[str, str]], args: argparse.Namespace) -> list[dict[str, str]]:
    out = []
    wanted_addr = parse_int(args.addr) if args.addr else None
    for row in rows:
        if wanted_addr is not None and not addr_matches(row.get('effective_address', ''), wanted_addr):
            continue
        if args.subsystem and row.get('subsystem', '').lower() != args.subsystem.lower():
            continue
        if args.pc and row.get('pc', '').lower() != args.pc.lower():
            continue
        if args.address_class and row.get('address_class', '').lower() != args.address_class.lower():
            continue
        if args.access and row.get('access_type', '').lower() != args.access.lower():
            continue
        if args.routine and row.get('routine_label', '').lower() != args.routine.lower():
            continue
        if args.contains:
            blob = ' '.join(row.values()).lower()
            if args.contains.lower() not in blob:
                continue
        out.append(row)
    return out


def print_table(rows: list[dict[str, str]], limit: int) -> None:
    cols = ['pc', 'mnemonic', 'access_type', 'effective_address', 'address_class', 'subsystem', 'routine_label', 'notes']
    if limit:
        rows = rows[:limit]
    widths = {c: max(len(c), *(len((r.get(c) or '')[:80]) for r in rows)) if rows else len(c) for c in cols}
    print(' | '.join(c.ljust(widths[c]) for c in cols))
    print('-+-'.join('-' * widths[c] for c in cols))
    for r in rows:
        print(' | '.join((r.get(c) or '')[:80].ljust(widths[c]) for c in cols))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--map', default='maps/full/hardware_access_map_v0.2.csv', help='hardware access CSV')
    ap.add_argument('--addr', help='address to match, e.g. 0x3FCE or $301E')
    ap.add_argument('--subsystem', help='subsystem filter, e.g. FUEL_SCHED_TIMER')
    ap.add_argument('--pc', help='PC filter, e.g. 0x8512')
    ap.add_argument('--routine', help='routine_label filter')
    ap.add_argument('--address-class', help='address_class filter')
    ap.add_argument('--access', help='access_type filter, e.g. R/W/RMW/EXEC')
    ap.add_argument('--contains', help='case-insensitive text search across row')
    ap.add_argument('--format', choices=['table', 'csv', 'json'], default='table')
    ap.add_argument('--limit', type=int, default=50, help='row limit for table output; 0 means unlimited')
    args = ap.parse_args()

    path = resolve_path(args.map)
    rows = select_rows(load_rows(path), args)
    if args.format == 'json':
        print(json.dumps(rows, indent=2))
    elif args.format == 'csv':
        if rows:
            import sys
            w = csv.DictWriter(sys.stdout, fieldnames=list(rows[0].keys()))
            w.writeheader(); w.writerows(rows)
    else:
        print_table(rows, args.limit)
        print(f'\nrows: {len(rows)}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
