#!/usr/bin/env python3
"""Conservative normal-RTS interrupt-mask summaries from stock BMHM bytes.

Both sides of unqualified branches are followed. Opaque calls may return with
either I value. Callees' normally returning continuations are conditional;
RTI/reset/STOP/WAI and abandoned stack contexts are not normal RTS returns.
This is a finite structural may-result analysis, not a feasible-schedule proof,
instruction timing model, stack bound, or model of arbitrary supplied code.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
from hashlib import sha256
import json
from pathlib import Path

from build_factory_scheduler import csv_text, full_rom, recorded_rom
from factory_rom_decode import decode, successors
from factory_structure import ROOT
from verify_factory_ownership import EVIDENCE
from verify_factory_rom_structure import EXPECTED_SHA256

OUT = ROOT / 'maps/structure'
CSV = 'factory_interrupt_mask_contracts.csv'
META = 'factory_interrupt_mask_evidence.json'


def build(rom):
    # Reconstruct only the file identity, never runtime low-memory contents.
    if sha256(bytes([255])*0x4000 + rom.read(0x4000, 0xC000)).hexdigest() != EXPECTED_SHA256:
        raise ValueError('Mapped bytes do not match stock BMHM')
    with (OUT/'factory_global_instructions.csv').open() as source:
        rows = list(csv.DictReader(source))
    ins = {int(r['pc'], 16): decode(rom.read, int(r['pc'], 16)) for r in rows}
    table = {rom.word(0x7A85+2*i) for i in range(16)}
    entries = {rom.word(a) for a in range(0xFFD6, 0x10000, 2)} | table | {0x7100, 0x746C, 0xFA5B}
    entries |= {i.target for i in ins.values() if i.op in {'JSR', 'BSR'} and i.target in ins}
    functions = {}
    for entry in entries:
        pending = [entry]
        local = {}
        while pending:
            pc = pending.pop()
            if pc in local:
                continue
            if pc not in ins:
                raise ValueError(f'Unreviewed local target {pc:04X}')
            local[pc] = ins[pc]
            pending.extend(p for p, edge in successors(ins[pc]))
        functions[entry] = local

    def destinations(i):
        if i.pc == 0x7A4F:
            return table
        return {i.target} if i.target in entries else set()

    graph = {entry: set().union(*(destinations(i) for i in local.values() if i.op in {'JSR', 'BSR'}))
             for entry, local in functions.items()}
    ordered, active, done = [], set(), set()
    def visit(entry):
        if entry in active:
            raise ValueError('Recursive call component needs a separate mask contract')
        if entry in done:
            return
        active.add(entry)
        for target in graph[entry]:
            visit(target)
        active.remove(entry)
        done.add(entry)
        ordered.append(entry)
    for entry in sorted(entries):
        visit(entry)

    # Track only I and A.bit4. A.bit4=None is unknown. This suffices to
    # preserve the actual TPA/TAP snapshots at 92A9/934C. All other uncertain
    # A writers widen the bit, never assume a value.
    summary, opaque = {}, {}
    a_writers = {'ADDA','ADCA','SUBA','SBCA','NEGA','LSRA','ASRA','ASLA','ROLA','RORA',
                 'INCA','DECA','PULA','TBA','ABA','SBA','MUL','IDIV','FDIV','XGDX','XGDY',
                 'ASLD','LSRD','DAA'}
    for entry in ordered:
        summary[entry] = {}
        opaque[entry] = set()
        for incoming in (0, 1):
            pending = [(entry, incoming, None)]
            seen, results = set(), set()
            while pending:
                pc, mask, abit = pending.pop()
                state = (pc, mask, abit)
                if state in seen:
                    continue
                seen.add(state)
                i = functions[entry][pc]
                if i.op == 'RTS':
                    results.add(mask)
                    continue
                if i.op in {'JSR', 'BSR'}:
                    targets = destinations(i)
                    if targets:
                        masks = set().union(*(summary[t][mask] for t in targets))
                        for target in targets:
                            opaque[entry] |= opaque[target]
                    else:
                        masks = {0, 1}
                        opaque[entry].add(pc)
                    pending.extend((i.next_pc, value, None) for value in masks)
                    continue
                if i.op == 'SEI':
                    mask = 1
                elif i.op == 'CLI':
                    mask = 0
                elif i.op == 'TPA':
                    abit = mask
                elif i.op == 'TAP':
                    if abit is None:
                        for target, edge in successors(i):
                            pending.extend([(target, 0, abit), (target, 1, abit)])
                        continue
                    mask = abit
                elif i.op == 'CLRA':
                    abit = 0
                elif i.op == 'COMA':
                    abit = None if abit is None else 1-abit
                elif i.op in {'LDAA', 'LDD'}:
                    value = i.value if i.op == 'LDAA' else i.value >> 8
                    abit = int(bool(value & 0x10)) if i.mode == 'immediate' else None
                elif i.op in {'ANDA','ORAA','EORA'}:
                    if i.mode != 'immediate':
                        abit = None
                    elif i.op == 'ANDA' and not i.value & 0x10:
                        abit = 0
                    elif i.op == 'ORAA' and i.value & 0x10:
                        abit = 1
                    elif i.op == 'EORA' and i.value & 0x10:
                        abit = None if abit is None else 1-abit
                elif i.op in a_writers or i.op in {'ADDD', 'SUBD'}:
                    abit = None
                pending.extend((target, mask, abit) for target, edge in successors(i))
            summary[entry][incoming] = results

    output = []
    for entry in sorted(entries):
        a, b = summary[entry][0], summary[entry][1]
        if not a and not b:
            kind = 'no_normal_RTS_return'
        elif a == {0} and b == {1}:
            kind = 'preserves_I'
        elif a == b == {0}:
            kind = 'returns_I_clear'
        elif a == b == {1}:
            kind = 'returns_I_set'
        else:
            kind = 'path_or_input_dependent'
        output.append({'entry': f'{entry:04X}', 'input_I0_possible_RTS_I': ';'.join(map(str, sorted(a))),
                       'input_I1_possible_RTS_I': ';'.join(map(str, sorted(b))), 'classification': kind,
                       'local_instruction_starts': len(functions[entry]),
                       'transitive_opaque_call_pcs': ';'.join(f'{p:04X}' for p in sorted(opaque[entry])),
                       'qualification': 'structural may-result; normal returns; both branch arms; no timing or feasible-interleaving proof'})
    metadata = {'rom_sha256': EXPECTED_SHA256, 'entries': len(output),
                'classifications': dict(sorted(Counter(r['classification'] for r in output).items())),
                'TPA_pcs': [f'{p:04X}' for p, i in sorted(ins.items()) if i.op == 'TPA'],
                'TAP_pcs': [f'{p:04X}' for p, i in sorted(ins.items()) if i.op == 'TAP'],
                'opaque_calls': sorted({f'{p:04X}' for v in opaque.values() for p in v}),
                'scope': 'all global procedure entries; I-bit only; qualified structural normal-RTS summaries',
                'limits': 'not an instruction-timing model; branches unqualified; no stack bound; opaque normal return conditional'}
    return {CSV: csv_text(output), META: json.dumps(metadata, indent=2, sort_keys=True)+'\n'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--rom', type=Path)
    p.add_argument('--check-recorded', action='store_true')
    p.add_argument('--write', action='store_true')
    args = p.parse_args()
    if args.check_recorded:
        if args.rom or args.write:
            p.error('Recorded mode is separate from fresh-ROM/write mode')
        rom = recorded_rom(json.loads(EVIDENCE.read_text()))
    elif args.rom:
        rom = full_rom(args.rom)
    else:
        p.error('Supply --rom or --check-recorded')
    for name, content in build(rom).items():
        path = OUT/name
        if args.write:
            path.write_text(content)
        elif not path.exists() or path.read_text() != content:
            raise SystemExit(f'Stale interrupt-mask contract: {path}')
    print('Factory structural interrupt-mask contracts verified')


if __name__ == '__main__':
    main()
