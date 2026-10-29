#!/usr/bin/env python3
"""Stock BMHM interrupt admission and cold-reset X-mask evidence.

This joins resident handler closures with the separate stack contracts. It is
not a peripheral arbitration/arrival model or a bound on TOC3 nesting. The X
invariant assumes valid interrupt frames and no effects from supplied code.
"""
from __future__ import annotations

import argparse
import csv
from hashlib import sha256
import io
import json
from pathlib import Path

from build_factory_scheduler import csv_text, full_rom, recorded_rom
from factory_rom_decode import BRANCHES, decode, successors
from factory_structure import ROOT
from verify_factory_ownership import EVIDENCE
from verify_factory_rom_structure import EXPECTED_SHA256
import verify_factory_stack_contracts as stacks

OUT = ROOT/'maps/structure'
FILES = ('factory_interrupt_admission.csv', 'factory_xmask_sites.csv',
         'factory_interrupt_admission_evidence.json')
SOURCES = ['SCI', 'SPI', 'pulse_accumulator_input', 'pulse_accumulator_overflow',
           'timer_overflow', 'OC5_IC4', 'OC4', 'OC3_scheduler', 'OC2', 'OC1',
           'IC3', 'IC2', 'IC1', 'real_time_interrupt', 'IRQ_pin_REF']

# Exhaustive for the selected local X-mask proof blocks, not a general CPU
# abstract interpreter. A new instruction outside this inventory fails closed.
A_UNKNOWN = {'ADDA','ADCA','SUBA','SBCA','NEGA','LSRA','ASRA','ASLA','ROLA','RORA',
             'INCA','DECA','PULA','TBA','ABA','SBA','MUL','IDIV','FDIV','XGDX','XGDY',
             'ASLD','LSRD','DAA','ADDD','SUBD'}
PRESERVE_A = set(BRANCHES) | {'BRSET','BRCLR','JMP','RTS','STOP','TAP','CMPA','BITA',
                            'LDAB','STAB','ADDB','ANDB','CMPB','BITB','CLRB','STAA',
                            'STD','BSET','BCLR'}


def build(rom):
    if sha256(bytes([255])*0x4000+rom.read(0x4000, 0xC000)).hexdigest() != EXPECTED_SHA256:
        raise ValueError('Mapped bytes do not match stock BMHM')
    with (OUT/'factory_global_instructions.csv').open() as source:
        ins = {int(r['pc'], 16): decode(rom.read, int(r['pc'], 16)) for r in csv.DictReader(source)}
    stack_rows = {int(r['entry'], 16): r for r in csv.DictReader(io.StringIO(stacks.build(rom)[stacks.FILES[0]]))}
    table = {rom.word(0x7A85+2*n) for n in range(16)}

    def closure(entry):
        seen, todo, opaque = set(), [entry], set()
        while todo:
            pc = todo.pop()
            if pc in seen:
                continue
            seen.add(pc)
            i = ins[pc]
            todo.extend(t for t, edge in successors(i))
            if i.op in {'JSR', 'BSR'}:
                targets = table if pc == 0x7A4F else {i.target}
                for target in targets:
                    if target in ins:
                        todo.append(target)
                    else:
                        opaque.add(pc)
        return seen, opaque

    handlers = []
    for vector, name in zip(range(0xFFD6, 0xFFF4, 2), SOURCES, strict=True):
        entry = rom.word(vector)
        reachable, opaque = closure(entry)
        unmask = sorted(p for p in reachable if ins[p].op in {'CLI', 'TAP'})
        if vector != 0xFFE4 and (unmask or opaque):
            raise ValueError(f'New interrupt opening or opaque call in {entry:04X}')
        stack = stack_rows[entry]
        if vector != 0xFFE4 and (stack['pre_RTI_depths'] != '0' or stack['boundary_sites']):
            raise ValueError(f'New return/stack boundary in {entry:04X}')
        handlers.append({'vector': f'{vector:04X}', 'source_F1_layout': name,
                         'entry': f'{entry:04X}', 'resident_instruction_starts': len(reachable),
                         'I_on_hardware_entry': 1,
                         'resident_CLI_or_TAP_pcs': ';'.join(f'{p:04X}' for p in unmask),
                         'ordinary_preemption_inside_handler': 'conditional_at_I0_windows' if unmask else 'blocked_through_RTI',
                         'extra_resident_stack_bytes': stack['peak_bytes_below_entry_SP'],
                         'frame_plus_resident_bytes': 9+int(stack['peak_bytes_below_entry_SP']),
                         'transitive_opaque_calls': ';'.join(f'{p:04X}' for p in sorted(opaque)),
                         'scope': 'resident prefix; valid frames; source request/local enable supplied; excludes reset and supplied-code effects'})

    taps = {}
    for entry in [0x7D86, 0x92A4, 0x92F1]:
        for incoming_x in [0, 1]:
            seen, todo = set(), [(entry, None, None)]
            while todo:
                pc, a6, origin = todo.pop()
                if (pc, a6, origin) in seen:
                    continue
                seen.add((pc, a6, origin))
                i = ins[pc]
                if i.op == 'TPA':
                    a6, origin = incoming_x, pc
                elif i.op in {'LDAA','LDD'}:
                    value = i.value >> 8 if i.op == 'LDD' else i.value
                    a6 = int(bool(value & 0x40)) if i.mode == 'immediate' else None
                    origin = pc if i.mode == 'immediate' else None
                elif i.op == 'CLRA':
                    a6, origin = 0, pc
                elif i.op in A_UNKNOWN:
                    a6, origin = None, None
                elif i.op not in PRESERVE_A:
                    raise ValueError(f'Unreviewed X-mask local operation {i.op} at {pc:04X}')
                if i.op == 'TAP':
                    if a6 is None or origin is None or (incoming_x == 1 and a6 != 1):
                        raise ValueError(f'Cold-reset X can clear or is unresolved at {pc:04X}')
                    taps.setdefault(pc, set()).add((entry, incoming_x, a6, origin))
                todo.extend((target, a6, origin) for target, edge in successors(i))
    all_taps = {pc for pc, i in ins.items() if i.op == 'TAP'}
    if set(taps) != all_taps:
        raise ValueError('Rooted TAP inventory exceeds the reviewed local X-mask proofs')

    tap_rows = []
    for pc, states in sorted(taps.items()):
        origins = {origin for entry, x, a, origin in states}
        if len(origins) != 1:
            raise ValueError(f'Multiple X-bit origins at {pc:04X}')
        origin = origins.pop()
        tap_rows.append({'TAP_pc': f'{pc:04X}', 'bytes_hex': ins[pc].data.hex(' ').upper(),
                         'A6_origin_pc': f'{origin:04X}', 'A6_origin_instruction': ins[origin].op+' '+ins[origin].operand,
                         'requested_X_from_entry_X0': ';'.join(str(a) for a in sorted({a for e, x, a, o in states if x == 0})),
                         'requested_X_from_entry_X1': ';'.join(str(a) for a in sorted({a for e, x, a, o in states if x == 1})),
                         'effective_X': 'preserves_entry_X; writing one cannot set a cleared X',
                         'scope': 'both local branch arms; no intervening asynchronous or supplied-code CCR changes'})

    # The sole intentional stacked-CCR edit ORs X=1. This retains hardware's
    # XIRQ-entry X=1; it cannot manufacture X=1 from X=0 on a real HC11.
    xirq_bytes = bytes.fromhex('14 00 04 32 8A 40 36 3B')
    if rom.word(0xFFF4) != 0xFC09 or rom.read(0xFC09, len(xirq_bytes)) != xirq_bytes:
        raise ValueError('XIRQ stacked-CCR edit changed')
    xirq = stack_rows[0xFC09]
    if xirq['pre_RTI_depths'] != '0' or xirq['boundary_sites']:
        raise ValueError('XIRQ no longer restores its interrupt frame')
    metadata = {'rom_sha256': EXPECTED_SHA256, 'ordinary_vector_count': len(handlers),
                'ordinary_distinct_handlers': len({r['entry'] for r in handlers}),
                'vectors_blocked_through_RTI': [r['vector'] for r in handlers if not r['resident_CLI_or_TAP_pcs']],
                'ordinary_handler_that_opens_nesting': ['793D'],
                'TAP_sites': sorted(f'{p:04X}' for p in all_taps),
                'TPA_sites': sorted(f'{p:04X}' for p, i in ins.items() if i.op == 'TPA'),
                'XIRQ_entry': 'FC09', 'XIRQ_bytes_hex': xirq_bytes.hex(' ').upper(),
                'cold_reset_X_invariant': 'X remains one in reviewed resident execution with valid frames and no supplied-code CCR effects',
                'active_ordinary_nesting_shape': 'zero or more ordinary TOC3 handlers followed by at most one other ordinary handler',
                'limits': ['structural branch overapproximation, not feasible event timing',
                           'no local-enable, priority, pending-flag or peripheral-completion arbitration model',
                           'no global bound on TOC3 depth or execution time',
                           'valid frames required; arbitrary uploads, SP recovery, external code and resets remain boundaries',
                           'XIRQ pin can also affect STOP wakeup even when its vector is masked; no board wake claim']}
    return {FILES[0]: csv_text(handlers), FILES[1]: csv_text(tap_rows),
            FILES[2]: json.dumps(metadata, indent=2, sort_keys=True)+'\n'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path)
    parser.add_argument('--check-recorded', action='store_true')
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    if args.check_recorded:
        if args.rom or args.write:
            parser.error('Recorded mode is separate from fresh-ROM/write mode')
        rom = recorded_rom(json.loads(EVIDENCE.read_text()))
    elif args.rom:
        rom = full_rom(args.rom)
    else:
        parser.error('Supply --rom or --check-recorded')
    for name, content in build(rom).items():
        path = OUT/name
        if args.write:
            path.write_text(content)
        elif not path.exists() or path.read_text() != content:
            raise SystemExit(f'Stale interrupt-admission contract: {path}')
    print('Factory resident interrupt admission and X-mask contracts verified')


if __name__ == '__main__':
    main()
