#!/usr/bin/env python3
"""Build a static spark ASIC handoff contract from a 7427 hardware-access map.

This tool intentionally does not infer a final spark writer. It classifies the
$3FD8-$3FFE ASIC window around the known spark/EST candidates and emits a
candidate contract for bench proof.
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path

DEFAULT_ANCHORS = (0x3FE6, 0x3FE8, 0x3FF6)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def resolve_path(value: str | Path) -> Path:
    p = Path(value)
    return p if p.is_absolute() else repo_root() / p


def parse_int(value: str) -> int:
    value = value.strip().lower()
    if value.startswith('$'):
        return int(value[1:], 16)
    if value.startswith('0x'):
        return int(value, 16)
    return int(value, 16)


def parse_window(value: str) -> tuple[int, int]:
    lo, hi = value.split(':', 1)
    return parse_int(lo), parse_int(hi)


def parse_addr_field(value: str) -> int | tuple[int, int] | None:
    value = (value or '').strip()
    if not value:
        return None
    if '-' in value:
        lo, hi = value.split('-', 1)
        try:
            return parse_int(lo), parse_int(hi)
        except ValueError:
            return None
    try:
        return parse_int(value)
    except ValueError:
        return None


def overlaps_window(addr: int | tuple[int, int] | None, windows: list[tuple[int, int]]) -> bool:
    if addr is None:
        return False
    if isinstance(addr, tuple):
        lo, hi = addr
        return any(not (hi < wlo or lo > whi) for wlo, whi in windows)
    return any(wlo <= addr <= whi for wlo, whi in windows)


def const_or_variable(row: dict[str, str]) -> str:
    src = row.get('value_source', '')
    if '0x' in src:
        return 'constant'
    if src == 'memory':
        return 'memory'
    return 'variable'


def runtime_or_init(row: dict[str, str]) -> str:
    pc = parse_int(row.get('pc', '0'))
    routine = row.get('routine_label', '')
    state = row.get('engine_state_seen', '')
    if row.get('effective_address') == '0x3FC0-0x3FF8' or pc < 0x7200:
        return 'boot_init'
    if routine == 'LA906':
        return 'runtime_spark_calc'
    if routine == 'LFA5B':
        return 'diagnostic_output_cycling'
    if 'ALDL' in state or routine.startswith('LF'):
        return 'diagnostic_or_aldl'
    if row.get('subsystem') == 'SPARK_EST':
        return 'spark_related_runtime_or_diag'
    return 'non_spark_or_unknown'


def nearest_anchor(addr: int | tuple[int, int] | None, anchors: list[int]) -> tuple[str, str]:
    if addr is None:
        return '', ''
    value = addr[0] if isinstance(addr, tuple) else addr
    nearest = min(anchors, key=lambda x: abs(x - value))
    return f'0x{nearest:04X}', str(value - nearest)


def contract_action(row: dict[str, str]) -> str:
    addr = row.get('effective_address', '')
    access = row.get('access_type', '')
    if addr == '0x3FE8' and access == 'W':
        return 'spark_delay_write'
    if addr == '0x3FE6' and access == 'W':
        return 'spark_command_write'
    if addr == '0x3FDC' and access == 'W':
        return 'spark_dwell_write'
    if addr == '0x3FDC' and access == 'R':
        return 'spark_dwell_read_add'
    if addr == '0x3FE4' and access == 'W':
        return 'asic_handshake_mirror'
    if addr == '0x3FEC' and access == 'R':
        return 'spark_status_read'
    if addr == '0x3FF6' and access == 'W':
        return 'est_fall_counter_write'
    if addr == '0x3FF6' and access == 'R':
        return 'ref_timing_read'
    if addr == '0x3FFA' and access == 'R':
        return 'est_status_read'
    if addr == '0x3FFC':
        return 'output_mode_write' if access == 'W' else 'output_latch_read'
    if addr == '0x3FC0-0x3FF8':
        return 'boot_asic_window_clear'
    return 'unknown_spark_related'


def possible_role(row: dict[str, str]) -> str:
    addr = row.get('effective_address', '')
    if addr == '0x3FE8':
        return 'runtime spark/EST timing handoff candidate'
    if addr == '0x3FE6':
        return 'runtime spark companion command candidate'
    if addr == '0x3FDC':
        return 'spark dwell/work-period register candidate'
    if addr == '0x3FE4':
        return 'possible mirror/handshake of $3FEC status/source'
    if addr == '0x3FEC':
        return 'ASIC status/source read used before $3FE4 write'
    if addr == '0x3FF6':
        return 'EST fall counter / scheduling basis'
    if addr == '0x3FFA':
        return 'packed ASIC status read'
    if addr == '0x3FFC':
        return 'global output latch / I/O D; separate contract'
    if addr == '0x3FC0-0x3FF8':
        return 'boot clear of ASIC window including spark candidates'
    if addr in {'0x3FD8', '0x3FDA'}:
        return 'diagnostic/output scheduler slot; not primary spark handoff yet'
    if addr == '0x3FEA':
        return 'fuel/output candidate; verify not spark mode companion'
    return 'window row; classify by bench'


def required_for_minimal(row: dict[str, str]) -> str:
    addr = row.get('effective_address', '')
    if addr in {'0x3FE8', '0x3FE6', '0x3FDC', '0x3FF6', '0x3FE4', '0x3FEC'}:
        return 'yes_or_test_item_for_spark'
    if addr == '0x3FFA':
        return 'test_item_status_decode'
    if addr == '0x3FFC':
        return 'separate_output_latch_contract'
    if addr == '0x3FC0-0x3FF8':
        return 'init_contract_overlap'
    return 'not_primary_spark_until_proven'


def load_rows(path: Path, windows: list[tuple[int, int]], anchors: list[int]) -> list[dict[str, str]]:
    with path.open(newline='', encoding='utf-8-sig') as f:
        source = list(csv.DictReader(f))
    out = []
    for row in source:
        parsed = parse_addr_field(row.get('effective_address', ''))
        if not overlaps_window(parsed, windows):
            continue
        nearest, delta = nearest_anchor(parsed, anchors)
        out.append({
            'contract_name': 'SPARK_ASIC_HANDOFF',
            'address': row.get('effective_address', ''),
            'pc': row.get('pc', ''),
            'mnemonic': row.get('mnemonic', ''),
            'access_type': row.get('access_type', ''),
            'width': row.get('width', ''),
            'bitmask': row.get('bitmask', ''),
            'value_source': row.get('value_source', ''),
            'routine_label': row.get('routine_label', ''),
            'subsystem': row.get('subsystem', ''),
            'constant_or_variable': const_or_variable(row),
            'runtime_or_init': runtime_or_init(row),
            'nearest_spark_candidate_pc': nearest,
            'relative_to_candidate': delta,
            'contract_action': contract_action(row),
            'possible_role': possible_role(row),
            'required_for_minimal_os': required_for_minimal(row),
            'confidence': row.get('confidence', ''),
            'notes': row.get('notes', ''),
        })
    out.sort(key=lambda r: parse_int(r['pc']))
    return out


def write_csv(rows: list[dict[str, str]], out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    fields = ['contract_name','address','pc','mnemonic','access_type','width','bitmask','value_source','routine_label','subsystem','constant_or_variable','runtime_or_init','nearest_spark_candidate_pc','relative_to_candidate','contract_action','possible_role','required_for_minimal_os','confidence','notes']
    with out.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def write_md(rows: list[dict[str, str]], out: Path, windows: list[tuple[int, int]]) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    by_addr = defaultdict(list)
    for row in rows:
        by_addr[row['address']].append(row)
    counts = Counter(r['contract_action'] for r in rows)
    md = []
    md.append('# SPARK ASIC Handoff Contract')
    md.append('')
    md.append('## Purpose')
    md.append('')
    md.append('Document the CPU-to-ASIC contract candidates for commanded ignition timing, EST/bypass state, and spark-related hardware handoff. This is static evidence only; no spark writer is defined here.')
    md.append('')
    md.append('## Scope')
    md.append('')
    md.append('Address window:')
    md.append('')
    for lo, hi in windows:
        md.append(f'- `${lo:04X}-${hi:04X}`')
    md.append('')
    md.append('Primary candidates: `$3FDC`, `$3FE4`, `$3FE6`, `$3FE8`, `$3FEC`, `$3FF6`, `$3FFA`, `$3FFC`.')
    md.append('')
    md.append('## Known Problem')
    md.append('')
    md.append('The new OS must not assume spark table degrees are directly written to hardware. Stock code appears to convert final spark into a hardware timing/delay domain using reference-period state, then writes one or more ASIC registers.')
    md.append('')
    md.append('## Register Summary')
    md.append('')
    md.append('| Address | Access | Width | Static role | Runtime? | Required? | Confidence |')
    md.append('|---|---|---:|---|---|---|---|')
    for addr, items in sorted(by_addr.items()):
        access = '/'.join(sorted(set(i['access_type'] for i in items)))
        width = '/'.join(sorted(set(i['width'] for i in items if i['width'])))
        role = items[0]['possible_role']
        runtime = '/'.join(sorted(set(i['runtime_or_init'] for i in items)))
        required = '/'.join(sorted(set(i['required_for_minimal_os'] for i in items)))
        conf = '/'.join(sorted(set(i['confidence'] for i in items)))
        md.append(f'| `{addr}` | {access} | {width} | {role} | {runtime} | {required} | {conf} |')
    md.append('')
    md.append('## Contract Action Counts')
    md.append('')
    md.append('| Action | Rows |')
    md.append('|---|---:|')
    for action, n in counts.most_common():
        md.append(f'| {action} | {n} |')
    md.append('')
    md.append('## Runtime Write Sites')
    md.append('')
    md.append('| PC | Address | Instruction | Value source | Routine | Action | Notes |')
    md.append('|---|---|---|---|---|---|---|')
    for r in rows:
        if r['access_type'] != 'W':
            continue
        if r['runtime_or_init'] not in {'runtime_spark_calc', 'spark_related_runtime_or_diag', 'diagnostic_output_cycling'} and r['subsystem'] != 'SPARK_EST':
            continue
        notes = r['notes'].replace('|', '/').strip()
        md.append(f"| `{r['pc']}` | `{r['address']}` | `{r['mnemonic']}` | `{r['value_source']}` | `{r['routine_label']}` | {r['contract_action']} | {notes} |")
    md.append('')
    md.append('## Runtime Read Sites')
    md.append('')
    md.append('| PC | Address | Instruction | Used for | Routine | Notes |')
    md.append('|---|---|---|---|---|---|')
    for r in rows:
        if r['access_type'] != 'R':
            continue
        if r['runtime_or_init'] not in {'runtime_spark_calc', 'spark_related_runtime_or_diag'} and r['subsystem'] != 'SPARK_EST':
            continue
        notes = r['notes'].replace('|', '/').strip()
        md.append(f"| `{r['pc']}` | `{r['address']}` | `{r['mnemonic']}` | {r['contract_action']} | `{r['routine_label']}` | {notes} |")
    md.append('')
    md.append('## Dependency Chain')
    md.append('')
    md.append('```text')
    md.append('$3FE8 / $3FE6 / $3FDC / $3FF6 spark ASIC candidate writes')
    md.append('← hardware delay/tick/work-period value')
    md.append('← final spark after modifiers')
    md.append('← base spark table')
    md.append('← idle correction')
    md.append('← coolant correction')
    md.append('← knock retard')
    md.append('← MAP/RPM/CTS/state')
    md.append('← REF period / $3FF6 / ASIC timing basis')
    md.append('```')
    md.append('')
    md.append('## Static Interpretation')
    md.append('')
    md.append('The strongest runtime spark cluster is routine `LA906`:')
    md.append('')
    md.append('```text')
    md.append('0xAB97  ADDD L3FF6   read EST fall counter / timing basis')
    md.append('0xABA4  SUBD L3FF6   subtract EST fall counter / timing basis')
    md.append('0xABAA  STD  L3FE8   write spark/EST timing output candidate')
    md.append('0xABB0  ADDD L3FDC   add dwell/work-period candidate')
    md.append('0xABBA  STD  L3FE6   write spark companion command candidate')
    md.append('0xABC0  STX  L3FDC   update dwell/work-period candidate')
    md.append('0xABC8  STD  L3FF6   update EST fall counter / scheduler')
    md.append('0xAC28  LDX  L3FEC   read ASIC status/source')
    md.append('0xAC2E  STX  L3FE4   write possible status mirror/handshake')
    md.append('```')
    md.append('')
    md.append('This supports Path S-B or S-C more than Path S-A: final spark is probably converted into delay/tick/work-period values before ASIC handoff, and `$3FE4/$3FEC/$3FF6` may be handshake/status/timing companions.')
    md.append('')
    md.append('## Required New-OS Behavior')
    md.append('')
    md.append('The new OS must reproduce, once bench-proven:')
    md.append('')
    md.append('1. EST/bypass-safe startup behavior')
    md.append('2. crank/run spark transition')
    md.append('3. final spark to hardware-unit conversion')
    md.append('4. correct ASIC register write order')
    md.append('5. correct refresh timing')
    md.append('6. zero/limp/default behavior if spark command is invalid')
    md.append('7. optional knock-retard subtraction if knock is retained')
    md.append('')
    md.append('## Open Questions')
    md.append('')
    md.append('- Which register is the final spark command handoff?')
    md.append('- Is the handoff angle-based or delay/tick-based?')
    md.append('- Is `$3FEC → $3FE4` a required mirror/handshake?')
    md.append('- Does `$3FE6` or `$3FE8` receive the final spark timing command?')
    md.append('- What does `$3FF6` do in spark/output scheduling?')
    md.append('- Which bits in `$3FFA` report EST/ref/status?')
    out.write_text('\n'.join(md), encoding='utf-8')


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--map', default='maps/current/hardware_access_map_hw_only.csv')
    ap.add_argument('--name', default='SPARK_ASIC_HANDOFF')
    ap.add_argument('--window', action='append', default=[])
    ap.add_argument('--anchor', action='append', default=[])
    ap.add_argument('--out-md', required=True)
    ap.add_argument('--out-csv', required=True)
    args = ap.parse_args()
    windows = [parse_window(w) for w in args.window] if args.window else [(0x3FD8, 0x3FFE)]
    anchors = [parse_int(a) for a in args.anchor] if args.anchor else list(DEFAULT_ANCHORS)
    rows = load_rows(resolve_path(args.map), windows, anchors)
    write_csv(rows, resolve_path(args.out_csv))
    write_md(rows, resolve_path(args.out_md), windows)
    print(f'wrote {len(rows)} spark handoff rows')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
