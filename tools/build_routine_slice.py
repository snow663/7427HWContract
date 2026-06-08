#!/usr/bin/env python3
"""Build a routine-level slice from the 7427 source listing and hardware map.

This tool is intentionally conservative. It preserves instruction context and tags obvious
hardware/RAM accesses, but it does not claim complete data-flow recovery.
"""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

LINE_RE = re.compile(r'^\s*([0-9A-Fa-f]{4}):\s*(?:(L[0-9A-Fa-f]{4})\s+)?([A-Z][A-Z0-9]*)\s*(.*?)\s*(?:;\s*(.*))?$')
LABEL_RE = re.compile(r'^(L[0-9A-Fa-f]{4})$')
ADDR_RE = re.compile(r'\bL([0-9A-Fa-f]{4})\b|\$([0-9A-Fa-f]{2,4})')

WRITE_OPS = {'STAA','STAB','STD','STX','STY','STS'}
READ_OPS = {'LDAA','LDAB','LDD','LDX','LDY','LDS','ADDD','SUBD','CPD','CMPA','CMPB','CPX','CPY','BITA','BITB','BRSET','BRCLR'}
RMW_OPS = {'BSET','BCLR','INC','DEC','CLR'}
BRANCH_OPS = {'BRA','BEQ','BNE','BCC','BCS','BMI','BPL','BHI','BLS','BLT','BGE','JMP'}
CALL_OPS = {'JSR'}
WIDTH16 = {'LDD','LDX','LDY','LDS','STD','STX','STY','STS','ADDD','SUBD','CPD','CPX','CPY'}

ROLE_BY_ADDR = {
    0x3FDC: 'rolling timing/work-period state candidate',
    0x3FE4: 'ASIC mirror/ack/handshake target from $3FEC candidate',
    0x3FE6: 'computed spark/EST timing command candidate',
    0x3FE8: 'computed spark/EST timing command candidate',
    0x3FEC: 'ASIC spark/status/source read candidate',
    0x3FF6: 'EST fall counter / rolling timing anchor candidate',
    0x3FFA: 'packed ASIC status candidate',
    0x3FFC: 'external output latch / global I/O state candidate',
    0x3FC0: 'last DRP/ref period hardware timing basis',
}

RAM_ROLES = {
    0x01EE: 'current retard / final spark offset accumulator candidate',
    0x01F0: 'spark retard shadow candidate',
    0x01F2: 'startup spark',
    0x01EC: 'spark latency / reference-period correction candidate',
    0x0201: 'spark latency table result',
    0x0205: 'EST monitor previous counter',
    0x020C: 'knock retard',
    0x005F: 'last DRP period address',
    0x004F: 'spark advance/retard direction flag word',
    0x0044: 'minor loop/EST monitor flag word',
    0x0050: 'DRP/closed-throttle status flag word',
}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def resolve_path(value: str | Path) -> Path:
    p = Path(value)
    return p if p.is_absolute() else repo_root() / p


def parse_int(value: str) -> int:
    value = value.strip().lower()
    if value.startswith('0x'):
        return int(value, 16)
    if value.startswith('$'):
        return int(value[1:], 16)
    return int(value, 16)


def parse_source(path: Path) -> list[dict[str, str]]:
    rows = []
    current_label = ''
    for line_no, raw in enumerate(path.read_text(errors='replace').splitlines(), 1):
        m = LINE_RE.match(raw)
        if not m:
            continue
        pc, label, mnemonic, operands, comment = m.groups()
        if label:
            current_label = label
        rows.append({
            'source_line': str(line_no),
            'pc': f'0x{int(pc,16):04X}',
            'label': label or '',
            'routine': current_label,
            'mnemonic': mnemonic.upper(),
            'operands': (operands or '').strip(),
            'comment': (comment or '').strip(),
            'raw': raw.rstrip(),
        })
    return rows


def find_address(operands: str) -> int | None:
    m = ADDR_RE.search(operands or '')
    if not m:
        return None
    token = m.group(1) or m.group(2)
    try:
        return int(token, 16)
    except ValueError:
        return None


def address_class(addr: int | None) -> str:
    if addr is None:
        return ''
    if 0x3F00 <= addr <= 0x3FFF:
        return 'ASIC_3FXX'
    if 0x3000 <= addr <= 0x303F:
        return 'HC11_REG'
    if 0x0000 <= addr <= 0x03FF:
        return 'DIRECT_RAM'
    if 0x4000 <= addr <= 0xFFFF:
        return 'ROM_TABLE'
    return 'UNKNOWN'


def access_type(mnemonic: str, addr: int | None) -> str:
    if addr is None:
        return ''
    if mnemonic in WRITE_OPS:
        return 'W'
    if mnemonic in READ_OPS:
        return 'R'
    if mnemonic in RMW_OPS:
        return 'RMW'
    return ''


def branch_target(mnemonic: str, operands: str) -> str:
    if mnemonic not in BRANCH_OPS:
        return ''
    for part in operands.replace(',', ' ').split():
        if LABEL_RE.match(part):
            return part
    return ''


def call_target(mnemonic: str, operands: str) -> str:
    if mnemonic not in CALL_OPS:
        return ''
    return operands.split()[0] if operands else ''


def role_candidate(addr: int | None, comment: str) -> str:
    if addr in ROLE_BY_ADDR:
        return ROLE_BY_ADDR[addr]
    if addr in RAM_ROLES:
        return RAM_ROLES[addr]
    lc = (comment or '').lower()
    if 'spark' in lc or 'est' in lc:
        return 'spark/EST software state candidate'
    if 'knock' in lc:
        return 'knock-retard software state candidate'
    if 'drp' in lc or 'ref' in lc:
        return 'reference-period timing basis candidate'
    return ''


def track_sources(row: dict[str, str], sources: dict[str, str]) -> tuple[str,str,str,str,str]:
    mn = row['mnemonic']
    op = row['operands']
    pc = row['pc']
    addr = find_address(op)
    target_text = f'${addr:04X}' if addr is not None else op
    if mn in {'LDD','LDX','LDY','LDAA','LDAB'}:
        reg = {'LDD':'D','LDX':'X','LDY':'Y','LDAA':'A','LDAB':'B'}[mn]
        sources[reg] = f'{pc} {mn} {op}'.strip()
        if reg in {'A','B'}:
            sources['D'] = 'A/B partial update; D source mixed'
    elif mn in {'ADDD','SUBD'}:
        sources['D'] = f'{pc} {mn} {op} from prior D plus/minus {target_text}'
    elif mn == 'MUL':
        sources['D'] = f'{pc} MUL from A*B'
    elif mn in {'LSRD','LSLD','ASLD','ASRD','ORAA','SUBB','SBCA','ADDB','ADCA','NEGA','NEGB'}:
        sources['D'] = f'{pc} {mn} modifies prior D/A/B'
    elif mn in {'PSHA','PSHB','PULA','PULB','TSX'}:
        if mn == 'TSX':
            sources['X'] = f'{pc} TSX stack pointer to X'
        else:
            sources['D'] = f'{pc} {mn} stack transfer affects A/B/D tracking'
    return sources.get('A',''), sources.get('B',''), sources.get('D',''), sources.get('X',''), sources.get('Y','')


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source', default='source/31/BMHM_HAC_ORG_7100_to_end.asm')
    ap.add_argument('--map', default='maps/full/hardware_access_map_v0.3.csv', help='accepted for interface compatibility; not required by first-pass slice')
    ap.add_argument('--routine', default='LA906')
    ap.add_argument('--start-pc', '--pc-start', dest='start_pc', required=True)
    ap.add_argument('--end-pc', '--pc-end', dest='end_pc', required=True)
    ap.add_argument('--out-md', required=True)
    ap.add_argument('--out-csv', required=True)
    args = ap.parse_args()

    start = parse_int(args.start_pc)
    end = parse_int(args.end_pc)
    rows = [r for r in parse_source(resolve_path(args.source)) if start <= parse_int(r['pc']) <= end]
    sources = {'A':'unknown','B':'unknown','D':'entry D unknown','X':'unknown','Y':'unknown'}
    out_rows = []
    for r in rows:
        addr = find_address(r['operands'])
        atype = access_type(r['mnemonic'], addr)
        a,b,d,x,y = track_sources(r, sources)
        out_rows.append({
            'routine': args.routine,
            'pc': r['pc'],
            'mnemonic': r['mnemonic'],
            'operands': r['operands'],
            'access_type': atype,
            'effective_address': f'0x{addr:04X}' if addr is not None else '',
            'address_class': address_class(addr),
            'width': '16' if r['mnemonic'] in WIDTH16 else ('8' if atype else ''),
            'value_source': 'CPU register / prior arithmetic' if atype == 'W' else ('memory/status input' if atype == 'R' else ''),
            'a_source': a,
            'b_source': b,
            'd_source': d,
            'x_source': x,
            'y_source': y,
            'branch_target': branch_target(r['mnemonic'], r['operands']),
            'call_target': call_target(r['mnemonic'], r['operands']),
            'hardware_role_candidate': role_candidate(addr, r['comment']),
            'notes': r['comment'],
            'confidence': 'medium_static' if atype or r['mnemonic'] in BRANCH_OPS | CALL_OPS else 'context',
        })

    out_csv = resolve_path(args.out_csv)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    fields = ['routine','pc','mnemonic','operands','access_type','effective_address','address_class','width','value_source','a_source','b_source','d_source','x_source','y_source','branch_target','call_target','hardware_role_candidate','notes','confidence']
    with out_csv.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader(); w.writerows(out_rows)

    out_md = resolve_path(args.out_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    md = ['# SPARK LA906 Timing Bridge','','Generated by `tools/build_routine_slice.py`. First-pass source slice; not a complete data-flow proof.','',f'Scope: `{args.routine}` / `{args.start_pc}` through `{args.end_pc}`.','', '## Instruction Slice','', '| PC | Instruction | Access | Address | Role / notes |', '|---|---|---|---|---|']
    for r in out_rows:
        inst = (r['mnemonic'] + ' ' + r['operands']).strip().replace('|','/')
        role = (r['hardware_role_candidate'] or r['notes'] or '').replace('|','/')[:160]
        md.append(f"| `{r['pc']}` | `{inst}` | {r['access_type']} | `{r['effective_address']}` | {role} |")
    out_md.write_text('\n'.join(md), encoding='utf-8')
    print(f'wrote {len(out_rows)} rows')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
