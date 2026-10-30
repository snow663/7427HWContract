#!/usr/bin/env python3
"""Resident stack-pointer envelopes from hash-checked factory BMHM bytes.

Procedure-entry SP excludes its caller's two-byte return frame and any nine-byte
interrupt frame. Both branch arms are structural possibilities. Opaque calls,
arbitrary upload writes and explicit SP resets end a prefix; no depth is assigned
to supplied code. Interrupt nesting and physical event timing are not bounded.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import io
import json
from pathlib import Path

from build_factory_scheduler import csv_text, full_rom, recorded_rom
from factory_rom_decode import decode, successors
from factory_structure import ROOT
from verify_factory_ownership import EVIDENCE, analyze_global
import verify_factory_interrupt_masks as masks

OUT = ROOT/'maps/structure'
FILES = ('factory_stack_contracts.csv', 'factory_stack_segments.csv', 'factory_stack_evidence.json')
SEGMENTS = {0x7103: ('reset_after_LDS7100', 0x03FF),
            0x797A: ('stack_recovery_after_LDS7977', 0x03F6),
            0xFA5E: ('factory_after_LDSFA5B', 0x03FF)}
PUSH = {'PSHA': 1, 'PSHB': 1, 'PSHX': 2, 'PSHY': 2, 'DES': 1}
PULL = {'PULA': 1, 'PULB': 1, 'PULX': 2, 'PULY': 2, 'INS': 1}


def analyze(rom):
    mask_rows = list(csv.DictReader(io.StringIO(masks.build(rom)[masks.CSV])))
    regular = {int(r['entry'], 16) for r in mask_rows}
    entries = regular | set(SEGMENTS)
    with (OUT/'factory_global_instructions.csv').open() as source:
        ins = {int(r['pc'], 16): decode(rom.read, int(r['pc'], 16)) for r in csv.DictReader(source)}
    table = {rom.word(0x7A85+2*i) for i in range(16)}
    functions = {}
    for entry in entries:
        local, todo = {}, [entry]
        while todo:
            pc = todo.pop()
            if pc in local:
                continue
            local[pc] = ins[pc]
            todo.extend(t for t, edge in successors(ins[pc]))
        functions[entry] = local

    # 9C1D is a six-byte local-frame cleanup, not an arbitrary SP reset.
    # Require the complete existing register/stack analysis to recover the
    # saved Y and restored SP; an additional entry or changed argument fails.
    if {e for e, f in functions.items() if 0x9C1D in f} != {0x99C5}:
        raise ValueError('New entry into the reviewed IAC frame cleanup')
    _, flow = analyze_global(rom, ins)
    frame = flow[0x99C5]
    expected = {(0x9C1D, 'SP'): 'entry_SP-6', (0x9C1D, 'Y'): 'entry_SP+1',
                (0x9C1F, 'SP'): 'entry_SP'}
    for (pc, register), value in expected.items():
        if frame.states[pc].get(register).text() != value:
            raise ValueError(f'IAC frame provenance changed at {pc:04X}')
    if frame.outputs['SP'].text() != 'entry_SP+2':
        raise ValueError('IAC frame no longer returns to its direct caller')

    def targets(i):
        if i.pc == 0x7A4F:
            return table
        return {i.target} if i.target in entries else set()

    graph = {e: set().union(*(targets(i) for i in f.values() if i.op in {'JSR', 'BSR'}))
             for e, f in functions.items()}
    order, done, active = [], set(), set()
    def visit(entry):
        if entry in active:
            raise ValueError('Recursive component needs a separate stack contract')
        if entry in done:
            return
        active.add(entry)
        for target in sorted(graph[entry]):
            visit(target)
        active.remove(entry)
        done.add(entry)
        order.append(entry)
    for entry in sorted(entries):
        visit(entry)

    summaries = {}
    for entry in order:
        result = {'peak': 0, 'witness': (), 'returns': set(), 'rti_depths': set(),
                  'cuts': set(), 'unbounded': False, 'nonlocal': set()}
        seen, todo = set(), [(entry, 0)]
        def peak(value, witness):
            if value > result['peak'] or value == result['peak'] and tuple(witness) < result['witness']:
                result['peak'], result['witness'] = value, tuple(witness)
        while todo:
            pc, depth = todo.pop()
            if (pc, depth) in seen:
                continue
            seen.add((pc, depth))
            if abs(depth) > 128:
                # This is a diagnostic for an unconstrained weighted cycle,
                # never a claimed 128-byte upper bound.
                result['unbounded'] = True
                result['cuts'].add((pc, 'nonzero_stack_cycle_or_unresolved_return'))
                continue
            i = functions[entry][pc]
            peak(depth, (pc,))
            if pc == 0x9C1D:
                if depth != 6:
                    raise ValueError('IAC TYS reached with an unexpected local depth')
                todo.append((i.next_pc, 0))
                continue
            if i.op in {'LDS', 'TXS', 'TYS'}:
                result['cuts'].add((pc, 'explicit_SP_assignment'))
                continue
            if pc == 0xFABC:
                result['cuts'].add((pc, 'arbitrary_upload_can_alias_active_frame'))
                continue
            if i.op in {'JSR', 'BSR'}:
                peak(depth+2, (pc,))
                callees = targets(i)
                if not callees:
                    result['cuts'].add((pc, 'opaque_callee_SP_and_depth_unknown'))
                    continue
                for target in sorted(callees):
                    child = summaries[target]
                    peak(depth+2+child['peak'], (pc,)+child['witness'])
                    result['cuts'] |= child['cuts']
                    result['unbounded'] |= child['unbounded']
                    result['nonlocal'] |= child['nonlocal']
                    for returned in sorted(child['returns']):
                        if returned == 0:
                            todo.append((i.next_pc, depth))
                        elif returned < 0 and depth+returned <= -2:
                            # Callee consumed the current function's return
                            # frame. Propagate an exit, never visit i.next_pc.
                            result['returns'].add(depth+returned+2)
                            result['nonlocal'].add(pc)
                        else:
                            result['cuts'].add((pc, 'unresolved_nonlocal_RTS_frame'))
                continue
            if i.op == 'RTS':
                result['returns'].add(depth)
                continue
            if i.op == 'RTI':
                result['rti_depths'].add(depth)
                continue
            if i.op in {'SWI', 'WAI'}:
                peak(depth+9, (pc,))
                continue
            depth += PUSH.get(i.op, 0)-PULL.get(i.op, 0)
            peak(depth, (pc,))
            todo.extend((target, depth) for target, edge in successors(i))
        summaries[entry] = result
    return regular, summaries


def build(rom):
    regular, summaries = analyze(rom)
    def row(entry):
        s = summaries[entry]
        status = ('unresolved_structural_stack_cycle' if s['unbounded'] else
                  'finite_resident_prefix_with_boundaries' if s['cuts'] else 'finite_resident_no_async_envelope')
        return {'entry': f'{entry:04X}', 'status': status,
                'peak_bytes_below_entry_SP': '' if s['unbounded'] else s['peak'],
                'pre_RTS_depths': ';'.join(map(str, sorted(s['returns']))),
                'pre_RTI_depths': ';'.join(map(str, sorted(s['rti_depths']))),
                'peak_call_and_leaf_pcs': ';'.join(f'{p:04X}' for p in s['witness']),
                'nonlocal_call_sites': ';'.join(f'{p:04X}' for p in sorted(s['nonlocal'])),
                'boundary_sites': ';'.join(f'{p:04X}:{why}' for p, why in sorted(s['cuts'])),
                'qualification': 'branch overapproximation; resident prefixes; valid frames; entry frame and async nesting excluded'}
    rows = [row(entry) for entry in sorted(regular)]
    segments = [{**row(entry), 'segment': name, 'entry_SP': f'{sp:04X}'}
                for entry, (name, sp) in sorted(SEGMENTS.items())]
    meta = {'rom_sha256': masks.EXPECTED_SHA256, 'procedure_entries': len(rows),
            'statuses': dict(sorted(Counter(r['status'] for r in rows).items())),
            'segments': len(segments), 'entry_return_frame_bytes': 2, 'interrupt_frame_bytes': 9,
            'SP_assignment_sites': sorted({f'{p:04X}' for s in summaries.values() for p, why in s['cuts'] if why == 'explicit_SP_assignment'}),
            'opaque_call_sites': sorted({f'{p:04X}' for s in summaries.values() for p, why in s['cuts'] if why == 'opaque_callee_SP_and_depth_unknown'}),
            'nonlocal_call_sites': sorted({f'{p:04X}' for s in summaries.values() for p in s['nonlocal']}),
            'reviewed_local_frame_restore': {'entry': '99C5', 'restore_pc': '9C1D',
                                            'bytes': 6, 'Y_before_TYS': 'entry_SP+1',
                                            'SP_after_TYS': 'entry_SP', 'SP_after_RTS': 'entry_SP+2'},
            'limits': 'not a simultaneous-interrupt or WCET bound; nonzero cycles flagged; resets and supplied code cut; explicit memory aliases retain separate contracts'}
    return {FILES[0]: csv_text(rows), FILES[1]: csv_text(segments), FILES[2]: json.dumps(meta, indent=2, sort_keys=True)+'\n'}


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
            raise SystemExit(f'Stale stack contract: {path}')
    print('Factory resident stack envelopes verified')


if __name__ == '__main__':
    main()
