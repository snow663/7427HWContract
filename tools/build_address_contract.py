#!/usr/bin/env python3
"""Build a focused address-level hardware contract from a 7427 access map.

Example:

    python tools/build_address_contract.py \
      --map maps/current/hardware_access_map_hw_only.csv \
      --name EFI_PW_3FCE \
      --addr 0x3FCE \
      --context-addrs 0x3FCC 0x3FCD 0x3FCF 0x3FD0 \
      --out-md docs/contracts/EFI_PW_3FCE_CONTRACT.md \
      --out-csv maps/contracts/efi_pw_3fce_contract.csv
"""

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


def parse_addr(value: str) -> int:
    s = value.strip().lower()
    if s.startswith('$'):
        return int(s[1:], 16)
    if s.startswith('0x'):
        return int(s, 16)
    return int(s, 16)


def addr_text(value: int) -> str:
    return f'$%04X' % value


def parse_pc(row: dict[str, str]) -> int:
    pc = (row.get('pc') or '0').strip().lower()
    return int(pc[2:] if pc.startswith('0x') else pc, 16)


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline='', encoding='utf-8-sig') as f:
        rows = list(csv.DictReader(f))
    rows.sort(key=parse_pc)
    return rows


def classify_action(name: str, row: dict[str, str], primary: set[int]) -> str:
    ea = row.get('effective_address', '')
    addr = parse_addr(ea) if ea and '-' not in ea else None
    value = row.get('value_source', '')
    mnemonic = row.get('mnemonic', '').upper()
    if name.upper() == 'EFI_PW_3FCE' and addr == 0x3FCE:
        if value == 'D=0x0000': return 'efi_pw_zero/off'
        if value == 'D=0x00C5': return 'diagnostic_3ms_pw_write'
        if value == 'D=0x7FFF': return 'normal_tbi_final_pw_write'
        if value == 'D': return 'fuel_calc_zero_or_transient_gate_write'
        if 'STD' in mnemonic: return 'efi_pw_write'
    return 'target_address_access' if addr in primary else 'context_address_access'


def row_context(rows: list[dict[str, str]], index: int, span: int) -> tuple[str, str]:
    def brief(r: dict[str, str]) -> str:
        return f"{r.get('pc')} {r.get('mnemonic')} -> {r.get('effective_address')}"
    before = ' ; '.join(brief(r) for r in rows[max(0, index - span):index])
    after = ' ; '.join(brief(r) for r in rows[index + 1:index + 1 + span])
    return before, after


def select_rows(rows: list[dict[str, str]], name: str, addrs: set[int], context_addrs: set[int], span: int) -> list[dict[str, str]]:
    wanted = addrs | context_addrs
    out: list[dict[str, str]] = []
    for i, r in enumerate(rows):
        ea = r.get('effective_address', '')
        if not ea or '-' in ea:
            continue
        try:
            addr = parse_addr(ea)
        except ValueError:
            continue
        if addr not in wanted:
            continue
        before, after = row_context(rows, i, span)
        out.append({
            'contract_name': name,
            'effective_address': r.get('effective_address', ''),
            'pc': r.get('pc', ''),
            'mnemonic': r.get('mnemonic', ''),
            'access_type': r.get('access_type', ''),
            'width': r.get('width', ''),
            'bitmask': r.get('bitmask', ''),
            'value_source': r.get('value_source', ''),
            'routine_label': r.get('routine_label', ''),
            'subsystem': r.get('subsystem', ''),
            'context_before': before,
            'context_after': after,
            'contract_action': classify_action(name, r, addrs),
            'confidence': r.get('confidence', ''),
            'notes': r.get('notes', ''),
        })
    return out


def write_csv(rows: list[dict[str, str]], out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    fields = ['contract_name','effective_address','pc','mnemonic','access_type','width','bitmask','value_source','routine_label','subsystem','context_before','context_after','contract_action','confidence','notes']
    with out.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader(); w.writerows(rows)


def write_md(rows: list[dict[str, str]], out: Path, name: str, addr_values: list[int], context_values: list[int]) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    access_counts = Counter(r['access_type'] for r in rows)
    width_counts = Counter(r['width'] for r in rows)
    action_counts = Counter(r['contract_action'] for r in rows)
    md: list[str] = []
    md.append(f"# {name.replace('_', ' ')} Contract")
    md.append('')
    md.append('## Purpose')
    md.append('')
    md.append(f"This address contract documents CPU accesses to {', '.join('`'+addr_text(a)+'`' for a in addr_values)} and selected context addresses ({', '.join('`'+addr_text(a)+'`' for a in context_values) or 'none'}).")
    md.append('')
    md.append('## Access Summary')
    md.append('')
    md.append(f"- selected rows: `{len(rows)}`")
    md.append(f"- access types: `{dict(access_counts)}`")
    md.append(f"- widths: `{dict(width_counts)}`")
    md.append(f"- actions: `{dict(action_counts)}`")
    md.append('')
    md.append('## Static Access Rows')
    md.append('')
    md.append('| PC | Address | Instruction | Access | Width | Value source | Routine | Action | Notes |')
    md.append('|---|---|---|---|---:|---|---|---|---|')
    for r in rows:
        note = (r.get('notes') or '').replace('|','/')
        if len(note) > 120: note = note[:117] + '...'
        md.append(f"| `{r['pc']}` | `{r['effective_address']}` | `{r['mnemonic']}` | {r['access_type']} | {r['width']} | `{r['value_source']}` | `{r['routine_label']}` | {r['contract_action']} | {note} |")
    md.append('')
    out.write_text('\n'.join(md), encoding='utf-8')


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--map', default='maps/current/hardware_access_map_hw_only.csv')
    ap.add_argument('--name', required=True)
    ap.add_argument('--addr', nargs='+', required=True)
    ap.add_argument('--context-addrs', nargs='*', default=[])
    ap.add_argument('--context-span', type=int, default=3)
    ap.add_argument('--out-md', required=True)
    ap.add_argument('--out-csv', required=True)
    args = ap.parse_args()
    addr_values = [parse_addr(a) for a in args.addr]
    context_values = [parse_addr(a) for a in args.context_addrs]
    rows = select_rows(load_rows(resolve_path(args.map)), args.name, set(addr_values), set(context_values), args.context_span)
    write_csv(rows, resolve_path(args.out_csv))
    write_md(rows, resolve_path(args.out_md), args.name, addr_values, context_values)
    print(f'wrote {len(rows)} rows')
    print(resolve_path(args.out_md))
    print(resolve_path(args.out_csv))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
