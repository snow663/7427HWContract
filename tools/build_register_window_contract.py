#!/usr/bin/env python3
"""Build a register-window contract around an anchor address.

Example:
  python tools/build_register_window_contract.py \
    --map maps/current/hardware_access_map_hw_only.csv \
    --name EFI_OUTPUT_COMPANION \
    --window 0x3FC8:0x3FD2 \
    --window 0x3FE8:0x3FEC \
    --anchor 0x3FCE \
    --out-md docs/contracts/EFI_OUTPUT_COMPANION_REGISTERS.md \
    --out-csv maps/contracts/efi_output_companion_registers.csv
"""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path


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


def parse_windows(values: list[str]) -> list[tuple[int, int]]:
    windows = []
    for value in values:
        if ':' in value:
            lo, hi = value.split(':', 1)
            windows.append((parse_int(lo), parse_int(hi)))
        else:
            addr = parse_int(value)
            windows.append((addr, addr))
    return windows


def row_addr(row: dict[str, str]) -> int | None:
    text = (row.get('effective_address') or '').strip()
    if not text or '-' in text:
        return None
    try:
        return parse_int(text)
    except ValueError:
        return None


def in_windows(addr: int, windows: list[tuple[int, int]]) -> bool:
    return any(lo <= addr <= hi for lo, hi in windows)


def load_rows(path: Path, windows: list[tuple[int, int]]) -> list[dict[str, str]]:
    rows = []
    with path.open(newline='', encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            addr = row_addr(row)
            if addr is None or not in_windows(addr, windows):
                continue
            row['_addr_int'] = addr
            row['_pc_int'] = parse_int(row.get('pc', '0'))
            rows.append(row)
    return sorted(rows, key=lambda r: r['_pc_int'])


def nearest_anchor(row: dict[str, str], anchors: list[dict[str, str]]) -> tuple[str, int, str, str]:
    if not anchors:
        return '', 0, 'unrelated_context', 'no'
    same_routine = [a for a in anchors if a.get('routine_label') == row.get('routine_label')]
    pool = same_routine or anchors
    nearest = min(pool, key=lambda a: abs(row['_pc_int'] - a['_pc_int']))
    delta = row['_pc_int'] - nearest['_pc_int']
    same = 'yes' if same_routine else 'no'
    if row.get('effective_address') == nearest.get('effective_address') and delta == 0:
        rel = 'anchor_write'
    elif same == 'yes' and delta < 0:
        rel = 'before_3fce_same_routine'
    elif same == 'yes' and delta > 0:
        rel = 'after_3fce_same_routine'
    elif same == 'yes':
        rel = 'same_routine_no_direct_neighbor'
    else:
        rel = 'unrelated_context'
    return nearest.get('pc', ''), delta, rel, same


def classify_action(row: dict[str, str], anchor_addrs: set[int]) -> str:
    addr = row['_addr_int']
    access = row.get('access_type', '')
    value = (row.get('value_source') or '').upper()
    subsystem = (row.get('subsystem') or '').upper()
    if addr in anchor_addrs and access == 'W':
        if '0X0000' in value:
            return 'anchor_zero_write'
        if '0X00C5' in value:
            return 'anchor_diagnostic_3ms_write'
        return 'anchor_write'
    if access == 'R' and 'STATUS' in subsystem:
        return 'status_read'
    if access == 'W':
        if 'D000' in value or 'DFFF' in value:
            return 'constant_command_write'
        return 'companion_write_candidate'
    if access == 'RMW':
        return 'companion_bit_candidate'
    return 'context_access'


def hypothesis(row: dict[str, str], anchor_addrs: set[int]) -> str:
    addr = row['_addr_int']
    subsystem = (row.get('subsystem') or '').upper()
    if addr in anchor_addrs:
        return 'EFI PW anchor; likely 16-bit pulsewidth command'
    if addr in {0x3FCC, 0x3FEA}:
        return 'possible ASIC mode/enable/preload companion; bench-test required'
    if subsystem == 'SPARK_EST':
        return 'spark/EST side; likely not EFI PW companion'
    if 'STATUS' in subsystem:
        return 'status/ref/timing input; likely not latch/strobe companion'
    return 'context candidate; classify on bench'


def required(row: dict[str, str], anchor_addrs: set[int]) -> str:
    addr = row['_addr_int']
    if addr in anchor_addrs:
        return 'yes_if_confirmed'
    if addr in {0x3FCC, 0x3FEA}:
        return 'test_item'
    return 'no_unless_dependency_proves'


def build_rows(name: str, rows: list[dict[str, str]], anchors: list[dict[str, str]], anchor_addrs: set[int]) -> list[dict[str, str]]:
    out = []
    for row in rows:
        nearest, delta, rel, same = nearest_anchor(row, anchors)
        out.append({
            'contract_name': name,
            'address': row.get('effective_address', ''),
            'pc': row.get('pc', ''),
            'mnemonic': row.get('mnemonic', ''),
            'access_type': row.get('access_type', ''),
            'width': row.get('width', ''),
            'bitmask': row.get('bitmask', ''),
            'value_source': row.get('value_source', ''),
            'routine_label': row.get('routine_label', ''),
            'subsystem': row.get('subsystem', ''),
            'nearest_3fce_pc': nearest,
            'pc_delta_from_3fce': str(delta),
            'relative_to_anchor': rel,
            'same_routine_as_3fce': same,
            'contract_action': classify_action(row, anchor_addrs),
            'hypothesis': hypothesis(row, anchor_addrs),
            'required_for_minimal_os': required(row, anchor_addrs),
            'confidence': row.get('confidence', ''),
            'notes': row.get('notes', ''),
        })
    return out


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ['contract_name','address','pc','mnemonic','access_type','width','bitmask','value_source','routine_label','subsystem','nearest_3fce_pc','pc_delta_from_3fce','relative_to_anchor','same_routine_as_3fce','contract_action','hypothesis','required_for_minimal_os','confidence','notes']
    with path.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader(); writer.writerows(rows)


def write_md(path: Path, name: str, rows: list[dict[str, str]], windows: list[tuple[int, int]], anchors: list[int]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    by_addr = defaultdict(list)
    for row in rows:
        by_addr[row['address']].append(row)
    md = [f'# {name} Register Window Contract', '', 'Generated register-window view.', '', '## Windows']
    md += [f'- `${lo:04X}-${hi:04X}`' for lo, hi in windows]
    md += ['', '## Anchors']
    md += [f'- `${a:04X}`' for a in anchors]
    md += ['', '## Address Rows', '', '| Address | Access | Width | Rows | Relative roles | Hypothesis |', '|---|---|---:|---:|---|---|']
    for addr, items in sorted(by_addr.items()):
        access = '/'.join(sorted({i['access_type'] for i in items if i['access_type']}))
        width = '/'.join(sorted({i['width'] for i in items if i['width']}))
        rels = ', '.join(sorted({i['relative_to_anchor'] for i in items}))
        hyp = '; '.join(dict.fromkeys(i['hypothesis'] for i in items))
        md.append(f'| `{addr}` | {access} | {width} | {len(items)} | {rels} | {hyp} |')
    md += ['', '## Detailed Rows', '', '| PC | Address | Mnemonic | Access | Value | Routine | Relative | Action | Notes |', '|---|---|---|---|---|---|---|---|---|']
    for r in rows:
        notes = (r['notes'] or '').replace('|', '/')[:120]
        md.append(f"| `{r['pc']}` | `{r['address']}` | `{r['mnemonic']}` | {r['access_type']} | `{r['value_source']}` | `{r['routine_label']}` | {r['relative_to_anchor']} | {r['contract_action']} | {notes} |")
    path.write_text('\n'.join(md) + '\n', encoding='utf-8')


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--map', default='maps/current/hardware_access_map_hw_only.csv')
    ap.add_argument('--name', required=True)
    ap.add_argument('--window', action='append', required=True)
    ap.add_argument('--anchor', action='append', required=True)
    ap.add_argument('--out-md', required=True)
    ap.add_argument('--out-csv', required=True)
    args = ap.parse_args()
    windows = parse_windows(args.window)
    anchor_addrs = {parse_int(a) for a in args.anchor}
    rows = load_rows(resolve_path(args.map), windows)
    anchors = [r for r in rows if r['_addr_int'] in anchor_addrs]
    contract_rows = build_rows(args.name, rows, anchors, anchor_addrs)
    write_csv(resolve_path(args.out_csv), contract_rows)
    write_md(resolve_path(args.out_md), args.name, contract_rows, windows, sorted(anchor_addrs))
    print(f'wrote {len(contract_rows)} rows')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
