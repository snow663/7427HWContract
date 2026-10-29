#!/usr/bin/env python3
"""Conditional masking intervals and non-TOC3 handler costs in stock BMHM.

All rooted SEI sites are inventoried. Bounds include the instruction following
CLI, and complete non-TOC3 handlers include RTI. This is not a bound on event
rates, global timer lateness, full main-pass execution or unprovided code.
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
from verify_factory_tick_timing import ADC7_POLLS

OUT=ROOT/'maps/structure'
FILES=('factory_masked_intervals.csv','factory_leaf_irq_cycle_bounds.csv',
       'factory_masked_instruction_cycles.csv','factory_masked_timing_evidence.json')


def build(rom):
    if sha256(bytes([255])*0x4000+rom.read(0x4000,0xC000)).hexdigest()!=EXPECTED_SHA256:
        raise ValueError('Mapped bytes do not match stock BMHM')
    with (OUT/'factory_global_instructions.csv').open() as source:
        ins={int(r['pc'],16):decode(rom.read,int(r['pc'],16)) for r in csv.DictReader(source)}
    seis=sorted(p for p,i in ins.items() if i.op=='SEI')
    if len(seis)!=29:
        raise ValueError('Rooted SEI inventory changed')
    if rom.read(0x518F,33)!=bytes(33):
        raise ValueError('Stock optional broadcast schedule no longer zero')
    guards={0xF958:'80 55 25 5A 81 22 22 56 B7 03 65',
            0xF9CA:'12 50 08 42',0xFA0A:'81 0B 23 02 86 0B 4D 27 0E',
            0xF265:'C6 0C',0xD174:'C6 0C',0x771C:'18 CE 40 0B',
            0xCCA1:'86 15 A7 3C'}
    for pc,text in guards.items():
        expected=bytes.fromhex(text)
        if rom.read(pc,len(expected))!=expected:
            raise ValueError(f'Timing premise changed at {pc:04X}')

    # Fixed straight-line byte-counter loops. Include the final branch; no
    # call or mask change occurs inside either reviewed body.
    bodies={0xF622:[0xF622,0xF623,0xF625,0xF627,0xF62A,0xF62C,0xF62D,0xF62E,0xF62F,0xF630],
            0xFA16:[0xFA16,0xFA18,0xFA1B,0xFA1C,0xFA1E,0xFA1F]}
    body_hex={0xF622:'3C EE 09 A6 00 18 A7 00 18 08 38 08 08 5A 26 F0',
              0xFA16:'E6 00 18 E7 00 08 18 08 4A 26 F5'}
    for pc,text in body_hex.items():
        if rom.read(pc,len(bytes.fromhex(text)))!=bytes.fromhex(text):
            raise ValueError(f'Counter loop changed at {pc:04X}')
    chains={}
    for root in [0x51BF,0xFBD7]:
        chain=[];p=root
        while p:
            if p in chain:
                raise ValueError('Cyclic SCI root list')
            chain.append(p);p=rom.word(p)
        chains[root]=chain
    lookup_cap=max(map(len,chains.values()))
    if lookup_cap!=3:
        raise ValueError('SCI root lookup envelope changed')

    # The reviewed REF latch is only set within this closure, including its
    # three output helpers. No helper can clear it between test and re-test.
    ref_seen=set();todo=[0x74EA]
    while todo:
        p=todo.pop()
        if p in ref_seen:continue
        ref_seen.add(p);i=ins[p]
        todo.extend(t for t,e in successors(i))
        if i.op in {'JSR','BSR'}:todo.append(i.target)
    with (OUT/'factory_global_flag_writers.csv').open() as source:
        writers=[r for r in csv.DictReader(source) if r['byte_address']=='0051' and r['bit']=='7'
                 and int(r['writer_pc'],16) in ref_seen]
    if {r['writer_pc'] for r in writers}!={'7725','7742','775B'} or any(r['effect_on_bit']!='set' for r in writers):
        raise ValueError('REF latch no longer has set-only writers')
    if rom.read(0x400B,1)!=b'\x04':
        raise ValueError('Stock REF mode constant changed')
    for entry in [0x77C7,0x77F7,0x785A]:
        seen=set();todo=[entry]
        while todo:
            pc=todo.pop()
            if pc in seen:continue
            seen.add(pc);i=ins[pc]
            if i.op in {'LDY','INY','DEY','ABY','PULY','TSY','XGDY'}:
                raise ValueError('REF output helper changes the reviewed Y cursor')
            todo.extend(t for t,e in successors(i))
            if i.op in {'JSR','BSR'}:todo.append(i.target)

    used=set()
    def bound(entry, copy_cap=34, normal_session=False):
        ends=set();active=set()
        @lru_cache(None)
        def walk(pc,returns=(),delay=0,polls=0,lookups=0,latch=-1):
            state=(pc,returns,delay,polls,lookups,latch)
            if state in active:
                raise ValueError(f'Unresolved masked cycle at {pc:04X}')
            active.add(state);used.add(pc);i=ins[pc];cost=cycles(i)
            if delay and i.op!='SEI':
                if i.op=='TAP':raise ValueError('Unreviewed post-CLI TAP')
                ends.add((pc,'following_CLI_instruction_complete'))
                result=cost
            elif i.op=='CLI':
                result=cost+walk(i.next_pc,returns,1,polls,lookups,latch)
            elif i.op=='RTI':
                if returns:raise ValueError('Unbalanced timed RTI')
                ends.add((pc,'RTI_restores_valid_ordinary_entry_I0'))
                result=cost
            elif i.op=='RTS':
                if not returns:raise ValueError(f'Masked return needs caller at {pc:04X}')
                result=cost+walk(returns[-1],returns[:-1],0,polls,lookups,latch)
            elif i.op in {'JSR','BSR'}:
                if i.target not in ins:raise ValueError(f'Opaque masked call at {pc:04X}')
                result=cost+walk(i.target,returns+(i.next_pc,),0,polls,lookups,latch)
            elif pc in bodies:
                body=bodies[pc];used.update(body)
                cap=256 if pc==0xF622 else copy_cap
                result=cap*sum(cycles(ins[p]) for p in body)+walk(ins[body[-1]].next_pc,returns,0,polls,lookups,latch)
            else:
                if i.op=='TAP':raise ValueError(f'Unreviewed masked TAP at {pc:04X}')
                edges=[t for t,e in successors(i)]
                if i.op in {'BSET','BCLR'} and i.mode=='direct' and i.value==0x51 and i.mask&0x80:
                    latch=int(i.op=='BSET')
                if i.op=='BRSET' and i.mode=='direct' and i.value==0x51 and i.mask==0x80 and latch!=-1:
                    edges=[i.target if latch else i.next_pc]
                if pc==0x774F:edges=[i.next_pc]  # LDY400B remains valid; stock04 has bit20 clear.
                elif pc==0xF9CA and normal_session:edges=[i.next_pc]
                elif pc in {0xF265,0xD174}:polls=0
                elif pc in {0xF267,0xD176}:
                    polls+=1
                    if polls>12:raise ValueError('ADC timeout proof exceeded')
                elif pc in {0xF26C,0xD17B}:
                    target=0xF267 if pc==0xF26C else 0xD176
                    if polls==12:edges=[t for t in edges if t!=target]
                elif pc==0x7B79:
                    polls+=1
                    if polls>=ADC7_POLLS:edges=[i.next_pc]
                elif pc in {0xF927,0xF92E}:lookups=0
                elif pc==0xF931:
                    lookups+=1
                    if lookups>lookup_cap:raise ValueError('SCI list lookup proof exceeded')
                elif pc==0xF937 and lookups==lookup_cap:edges=[i.next_pc]
                if not edges:raise ValueError(f'Unexpected masking terminal at {pc:04X}')
                result=cost+max(walk(t,returns,0,polls,lookups,latch) for t in edges)
            active.remove(state)
            return result
        result=walk(entry)
        return result,ends

    masked=[]
    for entry in seis:
        high,ends=bound(entry)
        scope=('stock_schedule_excludes' if entry==0xF616 else 'factory_output_cycle' if entry==0xFB5E else 'ordinary_resident')
        masked.append({'start':f'{entry:04X}','start_instruction':'SEI','scope':scope,
                       'nominal_upper_E':high,'unmask_end_instructions':';'.join(f'{p:04X}' for p,k in sorted(ends)),
                       'end_rules':';'.join(sorted({k for p,k in ends})),
                       'premises':'valid frames; nominal bus timing; ADC7 <=129 E; no supplied-code/alias effects; includes CLI following instruction'})
    high,ends=bound(0x7467)
    masked.append({'start':'7467','start_instruction':'LDAA #A0 after first compare arm',
                   'scope':'conditional_initial_armed_I1_suffix','nominal_upper_E':high,
                   'unmask_end_instructions':';'.join(f'{p:04X}' for p,k in sorted(ends)),
                   'end_rules':';'.join(sorted({k for p,k in ends})),
                   'premises':'if entered I1; earlier boot C57F/D183 can clear I; ordinary foreground; nominal bus; valid refresh cursor/frames; includes CLI following instruction'})
    irq_rows=[]
    for entry in sorted({rom.word(v) for v in range(0xFFD6,0xFFF4,2)}-{0x793D}):
        variants=[('stock_typed_descriptors_RX_N_le34',34,False)] if entry==0xF7EA else [('resident_handler',34,False)]
        if entry==0xF7EA:
            variants+=[('normal_session_copy_le11',11,True),('byte_copy_envelope_le255',255,False)]
        for name,cap,normal in variants:
            high,ends=bound(entry,cap,normal)
            if any(k!='RTI_restores_valid_ordinary_entry_I0' for p,k in ends):
                raise ValueError('A non-TOC3 handler unexpectedly opens ordinary nesting')
            irq_rows.append({'entry':f'{entry:04X}','contract':name,'nominal_handler_upper_E':high,
                             'including_IRQ_entry12_E':high+12,
                             'vectors':';'.join(f'{v:04X}' for v in range(0xFFD6,0xFFF4,2) if rom.word(v)==entry),
                             'premises':'valid frames and typed stock descriptors; nominal bus; no supplied-code/alias effects; IRQ arrival count not bounded'})
    ordinary=[r for r in masked if r['scope']=='ordinary_resident']
    maximum=max(r['nominal_upper_E'] for r in ordinary)
    inst_rows=[{'pc':f'{p:04X}','bytes_hex':ins[p].data.hex(' ').upper(),
                'instruction':ins[p].op+' '+ins[p].operand,'nominal_E_cycles':cycles(ins[p])} for p in sorted(used)]
    meta={'rom_sha256':EXPECTED_SHA256,'SEI_sites':len(seis),'masked_rows':len(masked),
          'ordinary_SEI_rows':len(ordinary),'ordinary_masked_max_E':maximum,
          'ordinary_max_start_pcs':[r['start'] for r in ordinary if r['nominal_upper_E']==maximum],
          'interrupt_rows':len(irq_rows),'instruction_sites':len(inst_rows),
          'REF_latch_bit':'0051.7','REF_latch_set_only_writer_pcs':sorted(r['writer_pc'] for r in writers),
          'REF_output_helpers_preserve_Y':['77C7','77F7','785A'],
          'SCI_root_chains':{f'{r:04X}':[f'{p:04X}' for p in ps] for r,ps in chains.items()},
          'HPRIO_write':{'pc':'CCA3','address':'303C','requested_hex':'15',
                         'F1_PSEL':'5 reserved selection defaults to IRQ'},
          'loop_body_E':{f'{p:04X}':sum(cycles(ins[x]) for x in xs) for p,xs in bodies.items()},
          'stock_broadcast_schedule':'518F..51AF all zero; F616 not selected by ordinary stock polling',
          'terminal_boundaries':['7D8C TAP50;7D8D STOP;7D8E self-loop','SWI/illegal/clock-monitor trap loops',
                                 'factory callback/upload and external hooks','invalid stack/active-frame aliases'],
          'limits':['all29 rooted SEI sites; conditional local masking envelopes, not whole-program WCET',
                    'incoming hardware masks and source-priority arbitration need their own event envelope',
                    'CLI following instruction included; ordinary RTI restores supplied valid entry I0',
                    'ADC7 completion premise excludes held-not-ready failure',
                    'copy caps34/11 require protocol length and mode predicates;255 is a byte-loop overapproximation',
                    'no bound on REF/SCI/other arrival counts; no global L/H or TOC3 nesting claim']}
    return {FILES[0]:csv_text(masked),FILES[1]:csv_text(irq_rows),FILES[2]:csv_text(inst_rows),FILES[3]:json.dumps(meta,indent=2,sort_keys=True)+'\n'}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--rom',type=Path);p.add_argument('--write',action='store_true');p.add_argument('--check-recorded',action='store_true')
    args=p.parse_args()
    if args.check_recorded:
        if args.rom or args.write:p.error('Recorded mode is separate from fresh-ROM/write mode')
        rom=recorded_rom(json.loads(EVIDENCE.read_text()))
    elif args.rom:rom=full_rom(args.rom)
    else:p.error('Supply --rom or --check-recorded')
    for name,content in build(rom).items():
        path=OUT/name
        if args.write:path.write_text(content)
        elif not path.exists() or path.read_text()!=content:raise SystemExit(f'Stale masked timing contract: {path}')
    print('Factory masked intervals and leaf IRQ timing contracts verified')


if __name__=='__main__':main()
