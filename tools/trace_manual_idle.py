"""Audit all direct execution paths and idle boundaries in an in-memory overlay.

An exact original Rev A BIN is required. No BIN is created or changed. The
control-flow graph has explicit indexed/external frontiers, not runtime proof.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
from pathlib import Path
from factory_rom_decode import decode
from manual_idle_overlay import ROOT, EXPECTED_SHA, PRESERVED, RETIRED, overlay


def sweep(image, forbidden=frozenset()):
    roots = {int.from_bytes(image[a:a+2], 'big') for a in range(0xffc0, 0x10000, 2)}
    roots |= {int.from_bytes(image[a:a+2], 'big') for a in range(0x7a85, 0x7aa5, 2)}
    pending = [(pc, 'root') for pc in roots]
    decoded, covered, frontiers = {}, {}, []
    while pending:
        pc, parent = pending.pop()
        if pc < 0x4000:
            frontiers.append({'origin': str(parent), 'target': f'{pc:04X}', 'kind': 'external code'})
            continue
        if pc in decoded: continue
        if pc in forbidden: raise AssertionError(f'Execution into retired/data byte {pc:04X} from {parent}')
        if pc in covered: raise AssertionError(f'Conflicting boundary {pc:04X}')
        i = decode(lambda a, n: image[a:a+n], pc)
        for a in range(pc, i.next_pc):
            if a in forbidden or a in covered: raise AssertionError(f'Overlapping/retired byte {a:04X}')
            covered[a] = pc
        decoded[pc] = i
        add = lambda target: pending.append((target, f'{pc:04X}'))
        if i.op in ('RTS', 'RTI', 'SWI', 'WAI', 'STOP'): continue
        if i.op in ('JSR', 'JMP') and i.mode.startswith('indexed'):
            if pc == 0x7a4f:
                for a in range(0x7a85, 0x7aa5, 2): add(int.from_bytes(image[a:a+2], 'big'))
            else: frontiers.append({'origin': f'{pc:04X}', 'kind': 'indexed control'})
            if i.op == 'JSR': add(i.next_pc)
        elif i.op in ('JMP', 'BRA'): add(i.target if i.target is not None else i.value)
        elif i.op in ('JSR', 'BSR'):
            add(i.target if i.target is not None else i.value); add(i.next_pc)
        elif i.op == 'BRN': add(i.next_pc)
        elif i.mode == 'relative' or i.op in ('BRSET', 'BRCLR'):
            add(i.target); add(i.next_pc)
        else: add(i.next_pc)
    return decoded, frontiers, sorted(roots)


def audit(original, out):
    candidate, assembly, retired = overlay(original)
    evidence = json.loads((ROOT / 'maps/maintenance/manual_idle_reva_evidence.json').read_text())
    assert evidence['image_sha256'] == EXPECTED_SHA
    for row in evidence['ranges']:
        lo, hi = int(row['start'], 16), int(row['end_exclusive'], 16)
        assert original[lo:hi] == bytes.fromhex(row['bytes']), f'Excerpt mismatch {lo:04X}'
    baseline, _, roots = sweep(original)
    current, frontiers, _ = sweep(candidate, retired)
    assert all(candidate[lo:hi] == original[lo:hi] for lo, hi in PRESERVED)
    assert int.from_bytes(candidate[0x4006:0x4008], 'big') == sum(candidate[0x4008:]) & 65535
    # Neither original selector may remain in normal reachable decisions.
    gear_decisions = [f'{pc:04X}' for pc, i in current.items()
                      if i.op in ('BRSET', 'BRCLR') and i.value == 0x36 and i.mask & 2]
    assert not gear_decisions, gear_decisions
    old_bank_accesses = [f'{pc:04X}' for pc, i in current.items()
                        if i.access() and i.access()['address'] is not None
                        and 0x2a7 <= i.access()['address'] <= 0x2b0]
    assert not old_bank_accesses, old_bank_accesses
    scoped = [(pc, i) for pc, i in sorted(baseline.items()) if 0x91a3 <= pc < 0xa466]
    replacement = set(assembly.instructions)
    incoming = []
    for pc, i in baseline.items():
        target = i.target if i.target is not None else i.value
        if i.op not in ('JSR', 'JMP') or target is None: continue
        if any(lo <= target < hi for lo, hi in RETIRED) and not any(lo <= pc < hi for lo, hi in RETIRED):
            incoming.append({'origin': f'{pc:04X}', 'entry': f'{target:04X}',
                             'candidate_reachable_origin': pc in current,
                             'entry_live_in_candidate': target in current})
            if pc in current: assert target in current
    accesses = []
    for pc, i in scoped:
        access = i.access()
        if access:
            accesses.append(dict(pc=f'{pc:04X}', instruction=i.op, operand=i.operand,
                access=access['access'], width=access['width_bits'],
                address='' if access['address'] is None else f'{access["address"]:04X}',
                resolution='explicit direct address' if access['address'] is not None
                    else 'indexed: caller/stack/table contract required',
                candidate_disposition='replaced strategy' if any(lo <= pc < hi for lo, hi in RETIRED)
                    else 'preserved guard/driver/helper/service'))
    out.mkdir(parents=True, exist_ok=True)
    with (out / 'manual_idle_original_accesses.csv').open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(accesses[0]), lineterminator='\n'); w.writeheader(); w.writerows(accesses)
    report = dict(baseline_sha256=EXPECTED_SHA,
        assembly_source_sha256=hashlib.sha256((ROOT / 'source/manual_idle/manual_idle.asm').read_bytes()).hexdigest(),
        c_source_sha256=hashlib.sha256((ROOT / 'source/manual_idle/manual_idle.c').read_bytes()).hexdigest(),
        recorded_excerpts_match_exact_image=True,
        overlay_sha256=hashlib.sha256(candidate).hexdigest(),
        original_file_unchanged=True, firmware_file_created=False,
        baseline_instruction_starts=len(baseline), candidate_instruction_starts=len(current),
        idle_scope_original_instruction_starts=len(scoped),
        replacement_instruction_starts=len(replacement), replacement_code_data_bytes=len(assembly.memory),
        roots=[f'{a:04X}' for a in roots], direct_gear_decisions=gear_decisions,
        direct_old_drive_bank_accesses=old_bank_accesses,
        preservation=[[f'{lo:04X}', f'{hi:04X}'] for lo, hi in PRESERVED],
        incoming_replacement_entries=incoming,
        indexed_data_operations=sum(1 for i in current.values() if i.access() and i.access()['address'] is None),
        indexed_data_operations_in_strategy=sum(1 for pc in replacement
            if (access := current[pc].access()) and access['address'] is None),
        execution_frontiers=frontiers,
        scope='Direct CFG from all vectors and 16 dispatcher entries. No retired strategy/data execution. Indexed data and external code are explicit limits, not a complete runtime proof.')
    (out / 'manual_idle_static_audit.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('rom', type=Path)
    p.add_argument('--output', type=Path, default=ROOT / 'maps/maintenance')
    args = p.parse_args()
    original = args.rom.read_bytes(); report = audit(original, args.output)
    assert args.rom.read_bytes() == original
    print(json.dumps({k: v for k, v in report.items() if k not in ('roots', 'preservation', 'incoming_replacement_entries')}, indent=2))
