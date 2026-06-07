#!/usr/bin/env python3
"""Compare two 7427 hardware-access CSV files by address/subsystem/access rows."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def resolve_path(path: str | Path) -> Path:
    p = Path(path)
    return p if p.is_absolute() else repo_root() / p


def load(path: Path) -> list[dict[str, str]]:
    with path.open(newline='', encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))


def key(row: dict[str, str]) -> tuple[str, str, str, str]:
    return (
        row.get('pc', ''),
        row.get('access_type', ''),
        row.get('effective_address', ''),
        row.get('mnemonic', ''),
    )


def summarize(name: str, rows: list[dict[str, str]]) -> None:
    print(f'## {name}')
    print(f'rows: {len(rows)}')
    for col in ['address_class', 'subsystem', 'access_type']:
        counts = Counter(r.get(col, '') or '<blank>' for r in rows)
        print(f'{col}: ' + ', '.join(f'{k}={v}' for k, v in counts.most_common(12)))
    print()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--old', required=True)
    ap.add_argument('--new', required=True)
    ap.add_argument('--show', type=int, default=25, help='number of added/removed rows to show')
    args = ap.parse_args()

    old_rows = load(resolve_path(args.old))
    new_rows = load(resolve_path(args.new))
    summarize('old', old_rows)
    summarize('new', new_rows)

    old_keys = {key(r): r for r in old_rows}
    new_keys = {key(r): r for r in new_rows}
    added = [new_keys[k] for k in sorted(set(new_keys) - set(old_keys))]
    removed = [old_keys[k] for k in sorted(set(old_keys) - set(new_keys))]

    print(f'added rows: {len(added)}')
    for r in added[:args.show]:
        print(f"+ {r.get('pc')} {r.get('access_type')} {r.get('effective_address')} {r.get('subsystem')} {r.get('mnemonic')}")
    print(f'\nremoved rows: {len(removed)}')
    for r in removed[:args.show]:
        print(f"- {r.get('pc')} {r.get('access_type')} {r.get('effective_address')} {r.get('subsystem')} {r.get('mnemonic')}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
