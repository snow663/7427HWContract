#!/usr/bin/env python3
"""Build a focused subsystem contract from a 7427 hardware-access map."""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict, Counter
from pathlib import Path

REGISTER_INFO = {
    'FUEL_SCHED_TIMER': {
        '0x301C': ('$301C/$301D', 'TOC4 compare', '16', 'Output compare channel 4 scheduled compare value'),
        '0x301E': ('$301E/$301F', 'TOC5/TIC4 compare', '16', 'Output compare channel 5 / TIC4 scheduled compare value'),
        '0x3020': ('$3020', 'TCTL1', '8/bit', 'Output compare action/mode bits'),
        '0x3022': ('$3022', 'TMSK1', '8/bit', 'Timer interrupt mask/enable bits'),
        '0x3023': ('$3023', 'TFLG1', '8/bit', 'Timer interrupt flags; write-one-to-clear'),
    }
}

FUEL_SCHED_TIMER_CONTEXT = """
## Static Contract Finding

`FUEL_SCHED_TIMER` is not the final EFI pulsewidth handoff. The final normal-TBI EFI PW handoff is `$3FCE`. This subsystem appears to be the HC11 timer/output-compare support path that schedules and services TOC4/TOC5 events using timer compare registers and interrupt flags.

For minimal-OS planning, reproduce this subsystem only if bench testing proves `$3FCE` alone does not make the ASIC generate correct injector pulses. If `$3FCE` is sufficient, keep this contract as the stock-reference fallback and safety map.

## Timing Safety Margin

Both setup helpers apply the same minimum lead-time clamp:

```text
L77C7 TOC5/TIC4 setup:
  LDD L081F
  CPD #$06
  if below 6: D = #$0006
  D = D + TCNT ($300E)
  shadow -> L0821

L77F7 TOC4 setup:
  LDD L081F
  CPD #$06
  if below 6: D = #$0006
  D = D + TCNT ($300E)
  shadow -> L0823
```

Static value: minimum compare lead appears to be `6` timer counts. Exact real-time margin depends on the HC11 timer prescale configured in `TMSK2/OPTION` and should be bench-confirmed before a clean OS relies on this path.
""".strip()


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def resolve_path(path: str | Path) -> Path:
    p = Path(path)
    return p if p.is_absolute() else repo_root() / p


def parse_pc(pc: str) -> int:
    pc = (pc or '').strip().lower()
    if pc.startswith('0x'):
        return int(pc, 16)
    return int(pc, 16)


def classify_action(row: dict[str, str]) -> str:
    addr = row.get('effective_address', '').lower()
    access = row.get('access_type', '')
    mnemonic = row.get('mnemonic', '').upper()
    value_source = row.get('value_source', '').lower()
    notes = row.get('notes', '').lower()

    if addr in {'0x301c', '0x301e'}:
        if access == 'W':
            return 'compare write'
        if access == 'R':
            if 'ADDD' in mnemonic:
                return 'compare base add / pulse extension'
            if 'CPD' in mnemonic:
                return 'compare safety check'
            return 'compare read'
    if addr == '0x3023':
        if access == 'W':
            return 'flag clear'
        return 'flag status read'
    if addr == '0x3022':
        if 'BSET' in mnemonic or value_source.startswith('set'):
            return 'interrupt enable'
        if 'BCLR' in mnemonic or value_source.startswith('clear'):
            return 'interrupt disable'
        if access == 'W':
            return 'interrupt mask init'
        return 'interrupt mask access'
    if addr == '0x3020':
        if 'BSET' in mnemonic or value_source.startswith('set'):
            return 'output mode setup'
        if 'BCLR' in mnemonic or value_source.startswith('clear'):
            return 'output mode clear/disable'
        return 'output mode access'
    if 'bpw' in notes:
        return 'pulsewidth conversion'
    return 'unknown/supporting access'


def channel(row: dict[str, str]) -> str:
    addr = row.get('effective_address', '').lower()
    bitmask = (row.get('bitmask') or '').lower()
    notes = (row.get('notes') or '').lower()
    routine = (row.get('routine_label') or '').upper()
    if addr == '0x301c' or bitmask in {'0x10', '#$10'} or 'toc4' in notes or routine == 'L77F7' or 'toc4' in (row.get('interrupt_context') or '').lower():
        return 'TOC4'
    if addr == '0x301e' or bitmask in {'0x08', '#$08'} or 'toc5' in notes or 'tic4' in notes or routine == 'L77C7' or 'toc5' in (row.get('interrupt_context') or '').lower():
        return 'TOC5/TIC4'
    if addr == '0x3023' and bitmask in {'0x20', '#$20'}:
        return 'TOC3/support'
    if bitmask == '0x80':
        return 'TOC1/support'
    return 'global/support'


def load_rows(path: Path, subsystem: str) -> list[dict[str, str]]:
    with path.open(newline='', encoding='utf-8-sig') as f:
        rows = [r for r in csv.DictReader(f) if r.get('subsystem', '').upper() == subsystem.upper()]
    rows.sort(key=lambda r: parse_pc(r.get('pc', '0')))
    for r in rows:
        r['contract_action'] = classify_action(r)
        r['channel'] = channel(r)
    return rows


def write_contract_csv(rows: list[dict[str, str]], out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        'pc','routine_label','interrupt_context','channel','contract_action','effective_address','access_type','width','bitmask','mnemonic','value_source','x_base/y_base','notes','confidence'
    ]
    with out.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        w.writeheader()
        w.writerows(rows)


def register_summary(rows: list[dict[str, str]], subsystem: str) -> list[str]:
    info = REGISTER_INFO.get(subsystem, {})
    out = []
    out.append('| Address | Name | Access | Width | Role | Required |')
    out.append('|---|---|---:|---:|---|---|')
    by_addr = defaultdict(list)
    for r in rows:
        by_addr[r['effective_address']].append(r)
    for addr in sorted(info):
        display, name, width, role = info[addr]
        access = '/'.join(sorted({r.get('access_type','') for r in by_addr.get(addr, []) if r.get('access_type')})) or 'not seen'
        out.append(f'| `{display}` | {name} | {access} | {width} | {role} | yes / bench-confirm |')
    return out


def observed_sequences(rows: list[dict[str, str]]) -> list[str]:
    out = []
    groups = defaultdict(list)
    for r in rows:
        groups[(r.get('routine_label',''), r.get('interrupt_context',''), r.get('channel',''))].append(r)
    for (routine, context, ch), items in sorted(groups.items(), key=lambda kv: (kv[0][1], kv[0][0], kv[0][2])):
        if not items:
            continue
        out.append(f'### `{routine}` — {context} — {ch}')
        out.append('')
        out.append('| PC | Instruction | Target | Action | Source / bit | Notes | Confidence |')
        out.append('|---|---|---|---|---|---|---|')
        for r in items:
            note = (r.get('notes','') or '').replace('|','/').strip()
            if len(note) > 120:
                note = note[:117] + '...'
            src = r.get('value_source','') or r.get('bitmask','')
            if r.get('bitmask') and r.get('bitmask') not in src:
                src = (src + ' ' + r.get('bitmask')).strip()
            out.append(f"| `{r.get('pc')}` | `{r.get('mnemonic')}` | `{r.get('effective_address')}` | {r.get('contract_action')} | `{src}` | {note} | {r.get('confidence')} |")
        out.append('')
    return out


def action_counts(rows: list[dict[str, str]]) -> Counter:
    return Counter(r['contract_action'] for r in rows)


def write_contract_md(rows: list[dict[str, str]], out: Path, subsystem: str) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    counts = action_counts(rows)
    by_addr = Counter(r['effective_address'] for r in rows)
    md = []
    md.append(f'# {subsystem} Contract')
    md.append('')
    md.append('## Purpose')
    md.append('')
    if subsystem == 'FUEL_SCHED_TIMER':
        md.append('This subsystem schedules and services the two TBI-related HC11 timer/output-compare channels using TOC4 and TOC5/TIC4 support registers. It clears timer flags, arms timer interrupts, sets output-compare action bits, and writes 16-bit future compare values.')
    else:
        md.append('Focused static contract for one hardware subsystem.')
    md.append('')
    md.append(FUEL_SCHED_TIMER_CONTEXT if subsystem == 'FUEL_SCHED_TIMER' else '')
    md.append('')
    md.append('## Hardware Registers')
    md.append('')
    md.extend(register_summary(rows, subsystem))
    md.append('')
    md.append('## Contract Action Counts')
    md.append('')
    md.append('| Action | Rows |')
    md.append('|---|---:|')
    for action, n in counts.most_common():
        md.append(f'| {action} | {n} |')
    md.append('')
    md.append('## Address Counts')
    md.append('')
    md.append('| Address | Rows |')
    md.append('|---|---:|')
    for addr, n in sorted(by_addr.items()):
        md.append(f'| `{addr}` | {n} |')
    md.append('')
    md.append('## Observed Write / Service Sequences')
    md.append('')
    md.extend(observed_sequences(rows))
    md.append('## Required New-OS Behavior')
    md.append('')
    md.append('A new OS must reproduce this behavior only if bench testing proves the `$3FCE` EFI PW handoff is not sufficient by itself. If this path is required, reproduce:')
    md.append('')
    md.append('1. safe minimum compare lead time (`>= 6` timer counts observed statically in setup helpers)')
    md.append('2. correct TFLG1 write-one-clear behavior before or during arm/service')
    md.append('3. correct TMSK1 interrupt-enable and interrupt-disable behavior')
    md.append('4. correct 16-bit TOC4/TOC5 compare writes')
    md.append('5. correct TCTL1 output mode setup/clear bits')
    md.append('6. correct BPW-derived timer extension behavior in the TOC4/TOC5 ISR paths')
    md.append('7. correct zero-fuel / DFCO behavior, preferably via `$3FCE = 0` if bench-proven')
    md.append('')
    md.append('## Open Tests')
    md.append('')
    md.append('- Verify whether `$3FCE` alone commands injector pulsewidth through the ASIC.')
    md.append('- Verify whether TOC4/TOC5 correspond directly to injector A/B or only support delayed/async scheduling.')
    md.append('- Verify output polarity at MCU pin vs injector driver output.')
    md.append('- Verify whether compare write order matters relative to TFLG1/TMSK1.')
    md.append('- Verify minimum usable compare lead time in real timer counts.')
    md.append('- Verify what happens if one channel is armed and the other is not.')
    md.append('')
    md.append('## Minimal Current Conclusion')
    md.append('')
    md.append('Stock code definitely maintains TOC4/TOC5 scheduling machinery. However, the focused fuel-PW handoff finding shows `$3FCE` is the explicit EFI PW register. Therefore, the clean OS should first prove `$3FCE` on the bench. Only recreate TOC4/TOC5 scheduling if `$3FCE` does not fully explain injector output timing.')
    md.append('')
    out.write_text('\n'.join(x for x in md if x is not None), encoding='utf-8')


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--map', default='maps/current/hardware_access_map_hw_only.csv')
    ap.add_argument('--subsystem', required=True)
    ap.add_argument('--out-md', required=True)
    ap.add_argument('--out-csv', required=True)
    args = ap.parse_args()

    rows = load_rows(resolve_path(args.map), args.subsystem)
    if not rows:
        raise SystemExit(f'no rows found for subsystem {args.subsystem!r}')
    write_contract_csv(rows, resolve_path(args.out_csv))
    write_contract_md(rows, resolve_path(args.out_md), args.subsystem.upper())
    print(f'wrote {len(rows)} rows')
    print(resolve_path(args.out_md))
    print(resolve_path(args.out_csv))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
