#!/usr/bin/env python3
"""Build an init-state/lifetime contract for selected 7427 ASIC registers."""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
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
    return int(value, 16)


def parse_pc(value: str) -> int:
    return parse_int(value)


def addr_value(effective_address: str) -> int | None:
    effective_address = (effective_address or '').strip()
    if not effective_address or '-' in effective_address:
        return None
    try:
        return parse_int(effective_address)
    except ValueError:
        return None


def range_overlaps(effective_address: str, wanted: set[int]) -> bool:
    if '-' not in effective_address:
        return False
    left, right = effective_address.split('-', 1)
    try:
        lo, hi = parse_int(left), parse_int(right)
    except ValueError:
        return False
    return any(lo <= a <= hi for a in wanted)


def selected(row: dict[str, str], wanted: set[int], include_ranges: bool) -> bool:
    ea = row.get('effective_address', '')
    addr = addr_value(ea)
    if addr is not None and addr in wanted:
        return True
    return include_ranges and range_overlaps(ea, wanted)


def boot_init_run_diag(row: dict[str, str], first_3fce_pc: int | None) -> str:
    pc = parse_pc(row['pc'])
    routine = row.get('routine_label', '')
    subsystem = row.get('subsystem', '')
    state = row.get('engine_state_seen', '')
    ea = row.get('effective_address', '')
    if ea == '0x3FC0-0x3FF8' or routine == 'L7100' or pc < 0x7200:
        return 'boot_init'
    if routine == 'L74D3':
        return 'ref_interrupt_pre_fuel_candidate'
    if ea == '0x3FCE' and routine in {'L82ED', 'L84F5'}:
        return 'runtime_fuel'
    if subsystem == 'SPARK_EST':
        return 'runtime_spark_est'
    if routine == 'LFA5B':
        return 'diagnostic_output_cycling'
    if 'ALDL' in state or routine.startswith('LF'):
        return 'diagnostic_or_aldl_output_latch'
    if first_3fce_pc is not None and pc < first_3fce_pc:
        return 'pre_first_3fce_static_pc_order'
    return 'runtime_or_unknown'


def const_or_variable(row: dict[str, str]) -> str:
    src = row.get('value_source', '')
    if '0x' in src:
        return 'constant'
    if src in {'D', 'X', 'A', 'B', 'memory', 'ADDD', 'SUBD'}:
        return 'variable_or_runtime_register'
    return 'unknown'


def possible_role(row: dict[str, str]) -> str:
    ea = row.get('effective_address', '')
    routine = row.get('routine_label', '')
    if ea == '0x3FC0-0x3FF8':
        return 'block_clear_of_asic_window_including_candidate_fuel_registers'
    if ea == '0x3FCE':
        if routine in {'L82ED', 'L84F5'}:
            return 'runtime_efi_pw_handoff'
        if routine == 'LFA5B':
            return 'diagnostic_efi_pw_command_or_zero_off'
        return 'efi_pw_handoff'
    if ea == '0x3FCC':
        if routine == 'LFA5B':
            return 'diagnostic_output_preload_or_mode_word_candidate'
        if routine == 'L74D3':
            return 'ref_interrupt_command_preload_or_persistent_init_candidate'
        return 'fuel_output_mode_command_candidate'
    if ea == '0x3FEA':
        if routine == 'LFA5B':
            return 'diagnostic_output_preload_or_mode_word_candidate'
        if routine == 'L74D3':
            return 'ref_interrupt_command_preload_or_persistent_init_candidate'
        return 'fuel_output_command_candidate'
    if ea == '0x3FE8':
        return 'spark_est_timing_handoff_not_primary_fuel_companion'
    if ea == '0x3FEC':
        return 'asic_status_source_read_not_primary_fuel_companion'
    if ea == '0x3FF6':
        return 'est_fall_counter_scheduler_not_primary_fuel_companion'
    if ea == '0x3FFC':
        return 'external_output_latch_or_io_d_port_global_state'
    if ea in {'0x3FC8', '0x3FCA'}:
        return 'asic_timing_status_read_not_primary_fuel_companion'
    return 'unknown_asic_window_role'


def required_for_minimal(row: dict[str, str]) -> str:
    role = possible_role(row)
    ea = row.get('effective_address', '')
    routine = row.get('routine_label', '')
    if 'runtime_efi_pw_handoff' in role:
        return 'yes_if_3fce_bench_confirmed'
    if ea == '0x3FC0-0x3FF8':
        return 'test_item_required_init_state_possible'
    if ea in {'0x3FCC', '0x3FEA'}:
        if routine == 'LFA5B':
            return 'probably_diagnostic_only_but_bench_confirm'
        return 'test_item_possible_persistent_init_state'
    if ea in {'0x3FE8', '0x3FF6'}:
        return 'not_fuel_writer_but_required_for_spark_contract'
    if ea == '0x3FFC':
        return 'required_for_output_latch_contract_not_direct_3fce'
    if ea in {'0x3FC8', '0x3FCA', '0x3FEC'}:
        return 'status_read_not_direct_3fce'
    return 'unknown_test_item'


def before_after(row: dict[str, str], first_pc: int | None) -> tuple[str, str]:
    if first_pc is None:
        return 'unknown', 'unknown'
    pc = parse_pc(row['pc'])
    return ('yes' if pc < first_pc else 'no', 'yes' if pc > first_pc else 'no')


def load_rows(path: Path, wanted: set[int], include_ranges: bool) -> list[dict[str, str]]:
    with path.open(newline='', encoding='utf-8-sig') as f:
        rows = list(csv.DictReader(f))
    rows = [r for r in rows if selected(r, wanted, include_ranges)]
    rows.sort(key=lambda r: parse_pc(r['pc']))
    first_3fce = min((parse_pc(r['pc']) for r in rows if r.get('effective_address') == '0x3FCE'), default=None)
    for r in rows:
        before, after = before_after(r, first_3fce)
        r['before_first_3fce_write'] = before
        r['after_first_3fce_write'] = after
        r['constant_or_variable'] = const_or_variable(r)
        r['possible_role'] = possible_role(r)
        r['boot_init_run_diag'] = boot_init_run_diag(r, first_3fce)
        r['required_for_minimal_os'] = required_for_minimal(r)
    return rows


def write_csv(rows: list[dict[str, str]], out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    fields = ['address','pc','mnemonic','access_type','width','value_source','routine_label','subsystem','boot_init_run_diag','before_first_3fce_write','after_first_3fce_write','constant_or_variable','possible_role','required_for_minimal_os','confidence','notes']
    with out.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({
                'address': r.get('effective_address', ''), 'pc': r.get('pc', ''), 'mnemonic': r.get('mnemonic', ''),
                'access_type': r.get('access_type', ''), 'width': r.get('width', ''), 'value_source': r.get('value_source', ''),
                'routine_label': r.get('routine_label', ''), 'subsystem': r.get('subsystem', ''),
                'boot_init_run_diag': r.get('boot_init_run_diag', ''), 'before_first_3fce_write': r.get('before_first_3fce_write', ''),
                'after_first_3fce_write': r.get('after_first_3fce_write', ''), 'constant_or_variable': r.get('constant_or_variable', ''),
                'possible_role': r.get('possible_role', ''), 'required_for_minimal_os': r.get('required_for_minimal_os', ''),
                'confidence': r.get('confidence', ''), 'notes': r.get('notes', ''),
            })


def write_md(rows: list[dict[str, str]], out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    counts = Counter(r.get('effective_address','') for r in rows)
    writes = Counter(r.get('effective_address','') for r in rows if r.get('access_type') == 'W')
    order = ['0x3FC0-0x3FF8','0x3FC8','0x3FCA','0x3FCC','0x3FCE','0x3FE8','0x3FEA','0x3FEC','0x3FF6','0x3FFC']
    classification = {
        '0x3FC0-0x3FF8':'boot ASIC-window block clear / required-init-state test item',
        '0x3FC8':'status/timing read, not fuel companion',
        '0x3FCA':'RPM/event counter read, not fuel companion',
        '0x3FCC':'fuel/output command preload candidate; ref-interrupt and diagnostic writes seen',
        '0x3FCE':'runtime EFI PW handoff plus diagnostic PW/off writes',
        '0x3FE8':'spark/EST timing handoff, not fuel companion',
        '0x3FEA':'fuel/output command preload candidate; ref-interrupt and diagnostic writes seen',
        '0x3FEC':'ASIC status/source read, not fuel companion',
        '0x3FF6':'EST fall counter/scheduler; diagnostic output cycling also writes it',
        '0x3FFC':'external output latch / I/O D global state, not local 3FCE companion',
    }
    md = ['# EFI Output Init State','','## Purpose','',
          'Determine whether `$3FCC` and `$3FEA` are diagnostic-only, or whether they are initialized/preset before normal `$3FCE/$3FCF` runtime pulsewidth writes can work.','',
          'The companion-register adjacency pass showed no immediate write next to the normal `0x8512 STD L3FCE` runtime fuel handoff. This file maps lifetime/init-state evidence instead.','',
          '## Address Scope','', 'Explicit candidates:', '', '```text', '$3FCC/$3FCD', '$3FCE/$3FCF', '$3FE8/$3FE9', '$3FEA/$3FEB', '$3FEC/$3FED', '$3FF6/$3FF7', '$3FFC/$3FFD', '```', '',
          'Also included: `$3FC0-$3FF8` block-clear/init row because it overlaps the EFI/ASIC window, plus status reads inside `$3FC8-$3FD2`.','',
          '## Static Summary','', '| Address | Total Rows | Write Rows | Static classification |', '|---|---:|---:|---|']
    for addr in order:
        if addr in counts:
            md.append(f'| `{addr}` | {counts[addr]} | {writes[addr]} | {classification.get(addr,"test item")} |')
    md += ['', '## Key Findings', '', '### 1. Normal `$3FCE` runtime writes still have no local companion', '',
           'The normal fuel-path `$3FCE` rows remain direct 16-bit writes. No `$3FCC`, `$3FEA`, or `$3FFC` write appears in the same normal fuel routine immediately around `0x8426` or `0x8512`.', '',
           '```text', '0x8426 STD L3FCE  runtime fuel/no-fuel/transient gate write', '0x8512 STD L3FCE  normal TBI final PW write', '```', '',
           '### 2. `$3FCC` and `$3FEA` are not diagnostic-only by static evidence', '',
           'Both are written once in the ref/DRP interrupt area before the fuel math handoff code region, and again in the diagnostic/output-cycling routine:', '',
           '```text', '0x74D6 STD L3FCC  D=0xD000  ref-interrupt command/preload candidate', '0x74DF STD L3FEA  D=0xDFFF  ref-interrupt command/preload candidate', '0xFADC STX L3FCC  diagnostic output-cycling preload', '0xFAE5 STX L3FEA  diagnostic output-cycling preload', '```', '',
           'Therefore `$3FCC/$3FEA` remain **possible persistent ASIC fuel/output init-state candidates**, not proven diagnostic-only.', '',
           '### 3. Boot/init clears the ASIC window', '',
           'A block-clear row writes even ASIC words from `$3FC0` through before `$3FFA`. This range overlaps `$3FCC`, `$3FCE`, `$3FE8`, `$3FEA`, and `$3FF6`, so any minimal OS must either reproduce or deliberately replace this ASIC-window initialization behavior.', '',
           '### 4. `$3FE8/$3FEC/$3FF6` are not normal EFI-PW companions', '',
           'Static rows place `$3FE8` and `$3FF6` in spark/EST timing paths, and `$3FEC` as a status/source read. They should be handled by spark/status contracts, not by the first minimal fuel-PW writer, unless bench behavior proves otherwise.', '',
           '### 5. `$3FFC` is a separate global output-latch contract', '',
           '`$3FFC` is heavily read/written in boot, output latch, diagnostic, ALDL, and output-cycling paths. It is probably important to board output state, but current static evidence does not make it a local `$3FCE` runtime strobe.', '',
           '## Lifetime Rows', '', '| Address | PC | Access | Width | Source | Routine | Lifetime | Role | Required? |', '|---|---|---:|---:|---|---|---|---|---|']
    for r in rows:
        md.append(f"| `{r.get('effective_address')}` | `{r.get('pc')}` | {r.get('access_type')} | {r.get('width')} | `{r.get('value_source')}` | `{r.get('routine_label')}` | {r.get('boot_init_run_diag')} | {r.get('possible_role').replace('_',' ')} | {r.get('required_for_minimal_os').replace('_',' ')} |")
    md += ['', '## Current Classification', '', '```text',
           'Path A-clean:', '  not proven. Normal runtime has no local companion, but boot/ref init state may matter.', '',
           'Path A-with-init:', '  strongest current static fit. $3FCE appears to be the only runtime fuel-PW command, with possible one-time ASIC-window clear and $3FCC/$3FEA preload/init state.', '',
           'Path C-runtime:', '  not supported by normal local adjacency; no repeated companion write near normal $3FCE.', '',
           'Path C-diagnostic-only:', '  partly supported for the LFA5B output-cycling path, but $3FCC/$3FEA also have earlier ref-interrupt writes, so diagnostic-only is not proven.', '',
           'Path B:', '  still bench-testable, but static $3FCE handoff and unit evidence argue against treating TOC4/TOC5 as the only runtime fuel command.', '```', '',
           '## Minimal-OS Implication', '',
           'Do not write the final minimal EFI PW writer yet. The next gate is to bench-test whether normal boot/ref init state is required before `$3FCE` commands injector pulsewidth.', '',
           'If bench confirms A-with-init, split the future writer into:', '', '```asm', 'EFI_OUTPUT_INIT:', '    ; reproduce only proven ASIC fuel-output init/preload state', '    RTS', '', 'EFI_PW_WRITE:', '    ; D = pulsewidth counts in 1/65536 second units', '    STD L3FCE', '    RTS', '```', '', '## Open Bench Tests', '', 'See `docs/tests/EFI_OUTPUT_INIT_STATE_TEST.md`.', '']
    out.write_text('\n'.join(md), encoding='utf-8')


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--map', default='maps/current/hardware_access_map_hw_only.csv')
    ap.add_argument('--name', default='EFI_OUTPUT_INIT_STATE')
    ap.add_argument('--addr', action='append', required=True)
    ap.add_argument('--include-overlap-ranges', action='store_true', default=True)
    ap.add_argument('--out-md', required=True)
    ap.add_argument('--out-csv', required=True)
    args = ap.parse_args()
    wanted = {parse_int(x) for x in args.addr}
    rows = load_rows(resolve_path(args.map), wanted, args.include_overlap_ranges)
    write_csv(rows, resolve_path(args.out_csv))
    write_md(rows, resolve_path(args.out_md))
    print(f'wrote {len(rows)} init-state rows')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
