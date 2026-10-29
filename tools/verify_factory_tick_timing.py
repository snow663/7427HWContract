#!/usr/bin/env python3
"""Conditional nominal bounds for BMHM's ordinary fast timer service.

Both branch arms are followed, with explicit accepted-stack/non-factory/busy
premises and two proved poll bounds. No complete-main-loop WCET, source-arrival
envelope, bus wait or unprovided code timing is assigned.
"""
from __future__ import annotations

import argparse
import csv
from functools import lru_cache
from hashlib import sha256
import json
from pathlib import Path

from build_factory_scheduler import csv_text, full_rom, recorded_rom
from factory_hc11_cycle_subset import cycles
from factory_rom_decode import decode, successors
from factory_structure import ROOT
from verify_factory_ownership import EVIDENCE
from verify_factory_rom_structure import EXPECTED_SHA256

OUT = ROOT/'maps/structure'
FILES = ('factory_tick_cycle_bounds.csv', 'factory_tick_instruction_cycles.csv',
         'factory_tick_timing_evidence.json')
PERIOD_COUNTS, PRESCALER = 0x0333, 16
PERIOD_E = PERIOD_COUNTS*PRESCALER
ADC_READY_AFTER_WRITE_E = 129  # one E cycle then the four-conversion sequence
ADC7_POLLS = (ADC_READY_AFTER_WRITE_E+6)//7+1  # conservative at any read phase
ADC4_POLLS = 12  # F265 LDAB#0C; F26B DECB; F26C BNE, no other B writer
CALLS = {0x797A:0x7B6D, 0x7B6D:0x91A3, 0x7B97:0xF245, 0x7B9B:0x7C13, 0xF24A:0xF25F}


def build(rom):
    if sha256(bytes([255])*0x4000+rom.read(0x4000,0xC000)).hexdigest() != EXPECTED_SHA256:
        raise ValueError('Mapped bytes do not match stock BMHM')
    with (OUT/'factory_global_instructions.csv').open() as source:
        ins = {int(r['pc'],16):decode(rom.read,int(r['pc'],16)) for r in csv.DictReader(source)}
    guards = {0x7106:'86 03',0x7111:'86 03',0x7113:'A7 24',0x710D:'86 B8',
              0x7940:'C3 03 33',0x7943:'FD 30 1A',0x7946:'86 20',0x7948:'B7 30 23',
              0xF265:'C6 0C',0xF267:'1E 30 80 09',0xF26B:'5A',0xF26C:'26 F9',
              0x7B73:'B7 30 30',0x7B79:'1F 30 80 FC',
              0xFC3A:'86 03',0xFC3C:'B7 30 24'}
    for pc, text in guards.items():
        if ins[pc].data != bytes.fromhex(text):
            raise ValueError(f'Reviewed timing premise changed at {pc:04X}')
    touched = set()

    def bound(entry, stop=None, busy=False):
        active = set()
        @lru_cache(None)
        def walk(pc, returns=(), adc7=0, adc4=0):
            if pc == stop:
                return (0,0)
            state = (pc, returns, adc7, adc4)
            if state in active:
                raise ValueError(f'Unbounded timing cycle at {pc:04X}')
            active.add(state)
            touched.add(pc)
            i = ins[pc]
            cost = cycles(i)
            if i.op in {'JSR','BSR'}:
                if CALLS.get(pc) != i.target:
                    raise ValueError(f'Unreviewed timing call {pc:04X}')
                children = [walk(i.target, returns+(i.next_pc,), adc7, adc4)]
            elif i.op == 'RTS':
                if returns:
                    children = [walk(returns[-1], returns[:-1], adc7, adc4)]
                elif stop is None:
                    children = [(0,0)]
                else:
                    raise ValueError(f'Return before requested timing stop {stop:04X}')
            elif i.op == 'RTI':
                if returns or stop is not None:
                    raise ValueError('Unbalanced or premature timed interrupt return')
                children = [(0,0)]
            else:
                edges = [t for t, edge in successors(i)]
                if pc == 0x794E:  # Ordinary, not redirected factory execution.
                    edges = [0x7958]
                elif pc == 0x795C and busy:
                    edges = [0x7967]
                elif pc in {0x7963,0x796A}:
                    edges = [0x796C]  # accepted upper bound; skip failure BRA7965
                elif pc == 0x796F:
                    edges = [0x797A]  # accepted lower bound
                elif pc == 0x797D:
                    if not busy:
                        raise ValueError('Main body is outside this timing contract')
                    edges = [0x7981]
                elif pc == 0x7B79:
                    adc7 += 1
                    if adc7 >= ADC7_POLLS:
                        edges = [i.next_pc]
                elif pc == 0xF267:
                    adc4 += 1
                    if adc4 > ADC4_POLLS:
                        raise ValueError('ADC timeout count exceeded')
                elif pc == 0xF26C:
                    edges = [t for t in edges if t != 0xF267 or adc4 < ADC4_POLLS]
                if not edges:
                    raise ValueError(f'Unexpected timing terminal {pc:04X}')
                children = [walk(t, returns, adc7, adc4) for t in edges]
            active.remove(state)
            return cost+min(v[0] for v in children), cost+max(v[1] for v in children)
        return walk(entry)

    contracts = [('iac_step',0x91A3,None,False),
                 ('adc_timeout_helper',0xF25F,None,False),
                 ('current_calculation',0x7C13,None,False),
                 ('fast_tick',0x7B6D,None,False),
                 ('entry_to_current_entry',0x793D,0x7C13,False),
                 ('entry_through_3068_store',0x793D,0x7BA6,False),
                 ('entry_to_busy_test',0x793D,0x797D,False),
                 ('busy_entry_through_RTI',0x793D,None,True)]
    rows = []
    for name, entry, stop, busy in contracts:
        low, high = bound(entry, stop, busy)
        rows.append({'contract':name, 'entry':f'{entry:04X}', 'stop_before':f'{stop:04X}' if stop else 'balanced_return_included',
                     'nominal_structural_min_E':low, 'nominal_upper_E':high,
                     'period_E':PERIOD_E, 'strict_no_next_compare_if_L_plus_H_less_than_E':PERIOD_E-high if entry == 0x793D else '',
                     'premises':'accepted stack; ordinary path; ADC7 ready <=129 E after write; no extra bus waits; preemption counted separately as H'})
    boot_costs = {}
    for vector in [0xFFFA,0xFFFE]:
        pc,total = rom.word(vector),0
        while pc != 0x7115:
            touched.add(pc)
            i = ins[pc]
            total += cycles(i)
            if i.op in {'BRA','JMP'}:
                pc = i.target
            elif i.op in {'JSR','BSR'}:
                raise ValueError('Unexpected boot call before prescaler programming')
            else:
                pc = i.next_pc
            if total >= 64:
                raise ValueError('Prescaler programming exceeds the normal write window')
        boot_costs[f'{vector:04X}'] = total
    timing = [{'pc':f'{pc:04X}','bytes_hex':ins[pc].data.hex(' ').upper(),
               'instruction':ins[pc].op+' '+ins[pc].operand,'nominal_E_cycles':cycles(ins[pc])}
              for pc in sorted(touched)]
    meta = {'rom_sha256':EXPECTED_SHA256, 'compare_delta_counts':PERIOD_COUNTS,
            'programmed_prescaler':PRESCALER, 'period_E':PERIOD_E,
            'reset_handler_to_prescaler_write_E':boot_costs,
            'timer_wrap_E':65536*PRESCALER, 'instruction_sites':len(timing),
            'ADC7_ready_after_write_E':ADC_READY_AFTER_WRITE_E, 'ADC7_poll_cap':ADC7_POLLS,
            'ADC4_poll_cap':ADC4_POLLS, 'poll_caps_include_exit_attempt':True,
            'L_definition':'time from prior OC3 match to first instruction at793D; includes prior arbitration/entry delay',
            'H_definition':'additional preemption and extra wait delay during this entry; excludes its nominal own instruction cost',
            'inequality':'L + H + nominal_upper_E < period_E excludes the next scheduled OC3 match before the endpoint',
            'late_rearm':'If newly written compare is behind TCNT and its equality window is past, the next match waits for 16-bit counter wrap; there is no elapsed-interval queue',
            'sources':['https://www.nxp.com/docs/en/reference-manual/M68HC11ERG.pdf Table1 pp13..20',
                       'https://www.nxp.com/docs/en/reference-manual/M68HC11RM.pdf AppendixA and section5.7.2',
                       'https://www.nxp.com/docs/en/data-sheet/MC68HC11F1.pdf sections9.3 and10.3; figure10-3; table9-3'],
            'limits':['nominal HC11/F1-style timing contract, not identified-board measurement',
                      'both branch arms overapproximated; structural lower endpoints are not feasible-path claims',
                      'ADC power/clock/stabilization and completion premise required',
                      'no complete main-pass WCET or bound on L/H/source event rates',
                      'opaque code, factory redirection, stack recovery and reset are excluded',
                      'bus-stretch and compare-write edge behavior need separate treatment at equality borders']}
    return {FILES[0]:csv_text(rows),FILES[1]:csv_text(timing),FILES[2]:json.dumps(meta,indent=2,sort_keys=True)+'\n'}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--rom',type=Path)
    p.add_argument('--write',action='store_true')
    p.add_argument('--check-recorded',action='store_true')
    args=p.parse_args()
    if args.check_recorded:
        if args.rom or args.write:
            p.error('Recorded mode is separate from fresh-ROM/write mode')
        rom=recorded_rom(json.loads(EVIDENCE.read_text()))
    elif args.rom:
        rom=full_rom(args.rom)
    else:
        p.error('Supply --rom or --check-recorded')
    for name, content in build(rom).items():
        path=OUT/name
        if args.write:
            path.write_text(content)
        elif not path.exists() or path.read_text()!=content:
            raise SystemExit(f'Stale tick timing contract: {path}')
    print('Factory conditional fast-tick timing contracts verified')


if __name__=='__main__':
    main()
