#!/usr/bin/env python3
"""Build WRITE_TARGET_NETWORK_INDEX for 7427/$31.

Static-only artifact. Sweeps mutation instructions and emits target dossiers.
It does not create runtime ASM or relax any hardware-output gate.
"""
from __future__ import annotations

import argparse, csv, re
from collections import Counter, defaultdict, deque
from pathlib import Path

SOURCE_CANDIDATES = [Path("source/31/BMHM_HAC_ORG_7100_to_end.asm")]
OUT_CSV = Path("maps/contracts/write_target_network_index.csv")
OUT_MD = Path("docs/contracts/WRITE_TARGET_NETWORK_INDEX.md")
OUT_TEST = Path("docs/tests/WRITE_TARGET_NETWORK_INDEX_TEST.md")
WRITE_OPS = {"STAA","STAB","STD","STS","STX","STY","BSET","BCLR","CLR","INC","DEC","COM","NEG","ASL","LSL","LSR","ROL","ROR"}
BRANCH_OPS = {"BRA","BHI","BLS","BCC","BCS","BNE","BEQ","BVC","BVS","BPL","BMI","BGE","BLT","BGT","BLE","BRSET","BRCLR","JMP","JSR"}
LINE_RE = re.compile(r"^\s*([0-9A-Fa-f]{4}):\s*(?:(L[0-9A-Fa-f]{4})\s+)?([A-Z][A-Z0-9]*)\s*(.*?)\s*(?:;\s*(.*))?$")
IMM_RE = re.compile(r"^#\$([0-9A-Fa-f]{1,4})$")


def source_path(explicit: str | None) -> Path:
    if explicit:
        return Path(explicit)
    for p in SOURCE_CANDIDATES:
        if p.exists():
            return p
    raise FileNotFoundError("source/31/BMHM_HAC_ORG_7100_to_end.asm not found")


def split_ops(s: str) -> list[str]:
    parts, cur = [], ""
    for x in s.split(','):
        x = x.strip()
        if x in {"X","Y"} and cur:
            cur += "," + x
        else:
            if cur: parts.append(cur)
            cur = x
    if cur: parts.append(cur)
    return parts


def sym_addr(t: str, xb: int | None, yb: int | None) -> tuple[str,str,str,str]:
    t = t.strip().upper()
    base_x = f"${xb:04X}" if xb is not None else ""
    base_y = f"${yb:04X}" if yb is not None else ""
    if ',' in t:
        off, idx = t.split(',',1)
        base = xb if idx == 'X' else yb if idx == 'Y' else None
        if off.startswith('$') and base is not None:
            a = (base + int(off[1:],16)) & 0xFFFF
            return f"${a:04X}", f"L{a:04X}", base_x, base_y
        return "", t, base_x, base_y
    if t.startswith('L') and len(t) == 5:
        return f"${int(t[1:],16):04X}", t, base_x, base_y
    if t.startswith('$'):
        a = int(t[1:],16)
        return f"${a:04X}", f"L{a:04X}", base_x, base_y
    return "", t, base_x, base_y


def role(sym: str, op: str) -> tuple[str,str,str]:
    if sym == 'L3FCE': return 'hardware sink:fuel pulsewidth','high','known EFI pulsewidth command sink'
    if sym in {'L3FE8','L3FE6','L3FDC','L3FF6','L3FEC','L3FE4'}: return 'hardware sink/state:spark stock handoff','medium','spark stock handoff/rolling-state candidate'
    if sym in {'L3062','L3060','L3FFC'}: return 'hardware sink/state:IAC candidate','medium','IAC port/phase/enable/park candidate'
    if sym == 'L303A': return 'hardware sink:watchdog/COP','high','COP reset register candidate'
    if sym.startswith('L30'): return 'hardware register/ASIC/CPU peripheral','medium','mapped hardware register range'
    if op in {'BSET','BCLR'}: return 'mode flag/safety gate/state latch','medium','bit mutation'
    return 'RAM state/calculation/shadow','medium','static RAM/state mutation'


def build(source: Path) -> list[dict[str,str]]:
    raw_rows = []
    routine, xb, yb = '', None, None
    branches = deque(maxlen=4)
    for raw in source.read_text(encoding='utf-8', errors='ignore').splitlines():
        m = LINE_RE.match(raw)
        if not m: continue
        pc, label, op, operands, comment = m.groups()
        pc, op = pc.upper(), op.upper()
        if label: routine = label.upper()
        operands = (operands or '').split(';',1)[0].strip()
        ops = split_ops(operands)
        if op in {'LDX','LDY'} and ops:
            im = IMM_RE.match(ops[0].upper())
            if im:
                if op == 'LDX': xb = int(im.group(1),16)
                else: yb = int(im.group(1),16)
        if op in BRANCH_OPS:
            branches.append(f"{pc}:{op} {operands}".strip())
        if op not in WRITE_OPS or not ops: continue
        target = ops[0].upper()
        if not target or target.startswith('#') or target in {'A','B','D','X','Y','SP'}: continue
        addr, sym, xbase, ybase = sym_addr(target, xb, yb)
        r, conf, note = role(sym, op)
        width = '16' if op in {'STD','STS','STX','STY'} else 'bit' if op in {'BSET','BCLR'} else '8'
        raw_rows.append({
            'pc': pc, 'routine_label': routine, 'instruction': op,
            'target_address': addr, 'target_symbol': sym, 'write_width': width,
            'bitmask': ops[1] if op in {'BSET','BCLR'} and len(ops)>1 else '',
            'value_source': {'STAA':'A','STAB':'B','STD':'D','STS':'SP','STX':'X','STY':'Y','CLR':'zero'}.get(op,'read_modify_write' if op not in {'BSET','BCLR'} else op),
            'x_base': xbase, 'y_base': ybase, 'nearby_branch_conditions': ' | '.join(branches),
            'candidate_role': r, 'confidence': conf, 'notes': note,
        })
    grouped = defaultdict(list)
    for row in raw_rows: grouped[row['target_symbol']].append(row)
    out = []
    for sym, rows in sorted(grouped.items()):
        first = rows[0]
        sites = ';'.join(f"{r['pc']}:{r['instruction']}" for r in rows[:20])
        if len(rows) > 20: sites += f";...+{len(rows)-20}"
        out.append({
            'target_symbol': sym, 'target_address': first['target_address'], 'write_count': str(len(rows)),
            'first_pc': first['pc'], 'first_routine_label': first['routine_label'],
            'representative_instruction': first['instruction'], 'write_widths': ' '.join(sorted(set(r['write_width'] for r in rows))),
            'bitmasks': ' '.join(sorted(set(r['bitmask'] for r in rows if r['bitmask']))),
            'value_sources': ' | '.join(f"{k}:{v}" for k,v in Counter(r['value_source'] for r in rows).most_common()),
            'x_y_bases_seen': ' '.join(sorted(set((r['x_base'] or r['y_base']) for r in rows if r['x_base'] or r['y_base']))),
            'call_contexts': ' | '.join(sorted(set(r['routine_label'] for r in rows if r['routine_label']))[:10]),
            'nearby_branch_conditions_sample': first['nearby_branch_conditions'],
            'candidate_role': Counter(r['candidate_role'] for r in rows).most_common(1)[0][0],
            'confidence': first['confidence'], 'write_sites_sample': sites, 'notes': first['notes'],
        })
    return out


def write_csv(path: Path, rows: list[dict[str,str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='', encoding='utf-8') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)


def write_md(path: Path, rows: list[dict[str,str]], source: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rc = Counter(r['candidate_role'] for r in rows)
    lines = ['# WRITE_TARGET_NETWORK_INDEX','', '## Purpose','', 'Whole-ROM static sweep of write targets. Starts from mutations instead of subsystem names so RAM, hardware, shadows, flags, safety gates, rolling state, and dispatcher selectors can be separated by use context.','', 'Static analysis only: no runtime ASM, no gate relaxation, no bench claim.','', '## Source','', f'- source file: `{source}`', f'- target dossier rows emitted: `{len(rows)}`','', '## Candidate role counts','']
    for k,v in rc.most_common(): lines.append(f'- `{k}`: {v}')
    lines += ['', '## High-value target seeds','', '| target | writes | role | note |','|---|---:|---|---|']
    for t in ['L3FCE','L3FE8','L3FE6','L3FDC','L3FF6','L3FEC','L3FE4','L3062','L3060','L3FFC','L303A']:
        m = next((r for r in rows if r['target_symbol']==t), None)
        lines.append(f"| `{t}` | {m['write_count'] if m else 0} | `{m['candidate_role'] if m else 'not written in sweep'}` | {m['notes'] if m else 'no dossier row emitted'} |")
    lines += ['', '## Deletion rule','', 'Do not delete a variable because it looks unimportant. Delete only after its read/write network proves it does not feed hardware, safety, dispatch, or a preserved stock driver.']
    path.write_text('\n'.join(lines)+'\n', encoding='utf-8')


def write_test(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('# WRITE_TARGET_NETWORK_INDEX_TEST\n\nStatic test definition. The builder must sweep mutation instructions, include indexed write forms when resolvable, emit target dossiers, and must not create runtime ASM or relax any hardware-output gate. A write proves mutation only; downstream reads decide importance.\n', encoding='utf-8')


def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument('--source')
    args = ap.parse_args(); src = source_path(args.source)
    rows = build(src)
    write_csv(OUT_CSV, rows); write_md(OUT_MD, rows, src); write_test(OUT_TEST)
    print(f'wrote {len(rows)} target dossier rows')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
