#!/usr/bin/env python3
"""Build a bench trace matrix from a 7427 hardware-access CSV."""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path

HIGH_PRIORITY_SUBSYSTEMS = {
    'FUEL_SCHED_TIMER', 'FUEL_MATH_HANDOFF', 'SPARK_EST', 'ASIC_STATUS_REF',
    'IO_LATCH_OUTPUT', 'UNKNOWN_306X_BOARD_IO', 'ASIC_COMMAND_OUTPUT', 'ASIC_UNKNOWN',
}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def resolve_path(path: str | Path) -> Path:
    p = Path(path)
    return p if p.is_absolute() else repo_root() / p


def objective(subsystem: str, address: str) -> str:
    if subsystem == 'FUEL_MATH_HANDOFF' and address.lower() == '0x3fce':
        return 'Prove EFI pulsewidth handoff units and zero/no-fuel behavior.'
    if subsystem == 'ASIC_COMMAND_OUTPUT' and address.lower() == '0x3fce':
        return 'Prove EFI pulsewidth handoff units and zero/no-fuel behavior.'
    if subsystem == 'FUEL_SCHED_TIMER':
        return 'Classify whether HC11 timer compare path is still required when $3FCE is driven.'
    if subsystem == 'SPARK_EST':
        return 'Prove spark/EST handoff units, latch timing, and bypass/run behavior.'
    if subsystem == 'ASIC_STATUS_REF':
        return 'Decode status/ref/RPM timing bits and read side effects.'
    if subsystem == 'IO_LATCH_OUTPUT':
        return 'Map output latch bits to physical outputs and safe states.'
    if subsystem == 'UNKNOWN_306X_BOARD_IO':
        return 'Classify board/ASIC-adjacent unknown as required or removable.'
    return 'Classify hardware effect and minimal-OS requirement.'


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--map', default='maps/full/hardware_access_map_v0.2.csv')
    ap.add_argument('--out', default='maps/current/hardware_test_matrix.csv')
    ap.add_argument('--only-high-priority', action='store_true')
    args = ap.parse_args()

    rows = list(csv.DictReader(resolve_path(args.map).open(newline='', encoding='utf-8-sig')))
    groups: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    for r in rows:
        subsystem = r.get('subsystem', '')
        address = r.get('effective_address', '')
        address_class = r.get('address_class', '')
        if not address:
            continue
        if args.only_high_priority and subsystem not in HIGH_PRIORITY_SUBSYSTEMS:
            continue
        if address_class not in {'HC11_REG', 'ALDL', 'ASIC_3FXX', 'UNKNOWN_HW'} and subsystem not in HIGH_PRIORITY_SUBSYSTEMS:
            continue
        groups[(address, address_class, subsystem)].append(r)

    out_rows = []
    for (address, address_class, subsystem), items in sorted(groups.items()):
        accesses = sorted(set(i.get('access_type', '') for i in items if i.get('access_type')))
        risks = [i.get('risk', '') for i in items]
        required = [i.get('minimal_os_required', '') for i in items]
        pcs = ', '.join(i.get('pc', '') for i in items[:8])
        notes = ' | '.join(dict.fromkeys((i.get('notes') or i.get('mnemonic') or '') for i in items if (i.get('notes') or i.get('mnemonic'))))[:500]
        out_rows.append({
            'address': address,
            'address_class': address_class,
            'subsystem': subsystem,
            'accesses': '/'.join(accesses),
            'count': str(len(items)),
            'risk': 'HIGH' if 'HIGH' in risks or 'HIGH_UNCLASSIFIED' in risks else (risks[0] if risks else ''),
            'minimal_os_required': 'YES' if any(x.startswith('YES') or x == 'TEST_ITEM' for x in required) else 'NO_UNLESS_DEPENDENCY_PROVES',
            'first_pcs': pcs,
            'test_objective': objective(subsystem, address),
            'bench_method': 'Capture PC, address, value, D/X/Y, timestamp, engine state; correlate with output/sensor event.',
            'notes': notes,
        })

    out_path = resolve_path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fields = ['address','address_class','subsystem','accesses','count','risk','minimal_os_required','first_pcs','test_objective','bench_method','notes']
    with out_path.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader(); w.writerows(out_rows)
    print(f'wrote {len(out_rows)} rows to {out_path}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
