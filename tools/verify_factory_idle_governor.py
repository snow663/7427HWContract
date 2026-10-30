#!/usr/bin/env python3
"""Verify the ROM evidence behind the factory IAC/RPM/VSS/governor documents.

This inventories reviewed software and local state, not physical stepper motion,
all factory diagnostics, or whole-program semantic coverage.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from build_factory_scheduler import csv_text, full_rom, recorded_rom, walk_callee, canonical_operand
from factory_rom_decode import decode, BRANCHES
from factory_structure import ROOT, SOURCE, text_sha256, load_regions, parse_listing
from verify_factory_rom_structure import EXPECTED_SHA256
from verify_factory_upstream import branch_condition

OUT = ROOT / 'maps/structure'
EVIDENCE = OUT / 'bmhm_idle_governor_rom_evidence.json'
DOCS = {
    'iac': 'docs/analysis/FACTORY_IAC_CONTROLLER.md',
    'learn': 'docs/analysis/FACTORY_IAC_LEARNING_AND_OUTPUT.md',
    'speed': 'docs/analysis/FACTORY_RPM_VSS_GOVERNOR.md',
    'index': 'docs/analysis/FACTORY_IDLE_SPEED_CONTROL_CLOSURE.md',
}
# Linear spans exclude the independently read pointer table at 9C96.
BLOCKS = [
    ('governor_target', 'speed', 0x8EB4, 0x90D3),
    ('governor_actuator', 'speed', 0x90D3, 0x9167),
    ('range_switch_inputs', 'iac', 0x9167, 0x91A3),
    ('IAC_step_service', 'learn', 0x91A3, 0x920E),
    ('IAC_kicker_and_input_helpers', 'learn', 0x920E, 0x925E),
    ('IAC_boot_setup', 'learn', 0x925E, 0x92F1),
    ('IAC_retained_cell_setup', 'learn', 0x92F1, 0x93D0),
    ('IAC_reset_startup', 'iac', 0x93D0, 0x9537),
    ('IAC_transition_and_error', 'iac', 0x9537, 0x9752),
    ('IAC_flow_sum_and_step_target', 'iac', 0x9752, 0x989C),
    ('IAC_desired_RPM', 'iac', 0x989C, 0x99C5),
    ('IAC_integral_and_cold_flow', 'iac', 0x99C5, 0x9C20),
    ('IAC_proportional', 'iac', 0x9C20, 0x9C96),
    ('IAC_derivative', 'iac', 0x9CA6, 0x9CFD),
    ('IAC_follower', 'iac', 0x9CFD, 0x9E99),
    ('IAC_background_kicker', 'learn', 0x9E99, 0x9FDE),
    ('IAC_background_decay_and_learning', 'learn', 0x9FDE, 0xA2B0),
    ('IAC_slow_decay_and_diagnostics', 'learn', 0xA2B0, 0xA3E6),
    ('IAC_reset_request', 'learn', 0xA3E6, 0xA407),
    ('IAC_service_override', 'learn', 0xA407, 0xA466),
    ('VSS_sample', 'speed', 0x7BF5, 0x7C0F),
    ('VSS_calculation_and_filter', 'speed', 0xD4A3, 0xD4EB),
    ('RPM_ratio', 'speed', 0x82ED, 0x8342),
    ('REF_RPM_history', 'speed', 0x7765, 0x7792),
    ('crank_RPM_history', 'speed', 0x7535, 0x7539),
    ('fuel_RPM_VSS_limits', 'speed', 0x8058, 0x80EE),
    ('fuel_limit_counter_exits', 'speed', 0x8106, 0x810C),
    ('VSS_fault_local', 'speed', 0xDDBA, 0xDE07),
    ('output_speed_fault_local', 'speed', 0xDE07, 0xDE3A),
    ('governor_fault_local', 'speed', 0xDE3A, 0xDE56),
    ('board_output_service', 'learn', 0xF3EE, 0xF420),
    ('retained_area_validation', 'learn', 0x720C, 0x723C),
    ('retained_checksum', 'learn', 0xF326, 0xF333),
    ('boot_output_shadow', 'learn', 0x7441, 0x744F),
    ('TCC_shared_governor_output', 'speed', 0xCDCE, 0xCDE2),
    ('diagnostic_flag_mirrors', 'speed', 0x7AF1, 0x7B03),
    ('tick_step_order', 'learn', 0x797A, 0x79F2),
    ('fuel_tail_admission', 'speed', 0x852C, 0x8548),
    ('governor_fast_call', 'speed', 0x7E36, 0x7E40),
    ('gear_output_shadow_coowner', 'learn', 0xC514, 0xC54E),
    ('output_shadow_bit7_clear', 'learn', 0xCC79, 0xCC7C),
    ('factory_IAC_latch_coowner', 'learn', 0xFB14, 0xFB5E),
    ('factory_governor_write_1', 'speed', 0xFB8D, 0xFB90),
    ('factory_governor_write_2', 'speed', 0xFBBF, 0xFBC2),
    ('shared_integer_helpers', 'index', 0xF436, 0xF564),
]
ROOTS = [0x8EB4, 0x90D3, 0x9167, 0x91A3, 0x920E, 0x9226, 0x9240,
         0x9247, 0x9250, 0x925E, 0x92A4, 0x92F1, 0x93C5, 0x93D0,
         0x989C, 0x99C5, 0x9C20, 0x9CA6, 0x9CFD, 0x9E99, 0xA2B0,
         0xA407, 0xD4A3, 0xD4DA, 0xF3EE]
DATA = [('stock_calibration', 0x4000, 0x7100), ('IAC_P_table_pointers', 0x9C96, 0x9CA6),
        ('gear_output_lookup', 0xB319, 0xB31D)]
ANCHORS = {0x91D0: '12 02 03 2C', 0x9340: 'B6 4E 8F 95 08',
           0xA0FA: '15 18 08 12 36 02 14', 0xA40B: '12 09 01 56',
           0x9161: '86 1F FD 30 6C', 0xD4BB: '86 E6 3D 05 8F',
           0xF40F: '96 4C B7 30 62'}
CELLS = [
    ('029D', 16, 'park/no-AC integral', '9C04'), ('029F', 8, 'park/no-AC snapshot', ''),
    ('02A0', 16, 'park/AC integral', '9C00'), ('02A2', 8, 'park/AC snapshot', ''),
    ('02A3', 16, 'park cold flow', '9C09'), ('02A5', 16, 'park cold-flow bound', ''),
    ('02A7', 16, 'drive/no-AC integral', '9C04'), ('02A9', 8, 'drive/no-AC snapshot', ''),
    ('02AA', 16, 'drive/AC integral', '9C00'), ('02AC', 8, 'drive/AC snapshot', ''),
    ('02AD', 16, 'drive cold flow', '9C09'), ('02AF', 16, 'drive cold-flow bound', ''),
    ('02B1', 8, 'kicker-on TPS baseline', ''), ('02B2', 8, 'kicker-off TPS baseline', ''),
]
STATES = [('0007',8,'software IAC position'), ('0008',8,'IAC step target'),
          ('0009',8,'retained IAC flags'), ('000A',8,'IAC direction/phase/enable'),
          ('0036',8,'IAC controller flags'), ('0037',8,'IAC follower/kicker flags'),
          ('0038',8,'IAC transfer/override flags'), ('0039',8,'IAC qualification/diagnostic flags'),
          ('004B',8,'shared kicker/board request'), ('004C',8,'shared board output shadow'),
          ('0068',16,'filtered RPM basis'), ('006A',16,'reference-qualified RPM history'), ('006C',8,'RPM ratio'),
          ('0075',8,'governor mode'), ('080C',8,'observed VSS timestamp changes'),
          ('080D',16,'current VSS timestamp'), ('080F',16,'previous VSS batch timestamp'),
          ('0811',8,'VSS timeout'), ('0812',16,'raw VSS'), ('0284',16,'filtered VSS'),
          ('0286',16,'governor target accumulator'), ('0288',16,'governor integral'),
          ('028A',16,'governor target step'), ('028D',8,'RPM sampled change'), ('028E',16,'filtered governor RPM'),
          ('0290',16,'governor lead term'), ('0292',8,'governor speed correction'),
          ('0293',8,'RPM error magnitude'), ('0294',8,'VSS error magnitude'),
          ('0295',16,'governor actuator P'), ('0297',16,'governor actuator I step'),
          ('0299',8,'governor target byte'), ('029A',8,'governor TPS error'),
          ('3062',8,'shared board hardware latch'), ('306C',16,'shared governor/TCC hardware command')]
STATES += [(a,w,role) for a,w,role,_ in CELLS]
STATES += [(f'{a:04X}',w,role) for a,w,role in [
    (0x857,8,'desired idle RPM'),(0x858,8,'absolute RPM error'),(0x859,16,'RPM error lag'),
    (0x85B,8,'BLM-qualified idle timer'),(0x85C,8,'startup RPM adder'),(0x85D,8,'RPM decay divider'),
    (0x85E,8,'RPM decay hold'),(0x85F,8,'slewed base idle RPM'),(0x860,8,'switch RPM offset'),
    (0x861,8,'switch RPM offset delay'),(0x862,16,'selected integral flow'),(0x864,8,'IAC qualification delay'),
    (0x866,8,'underspeed entry hold'),(0x867,8,'overspeed entry hold'),(0x868,8,'stall threshold'),
    (0x869,8,'stall timer'),(0x86A,8,'selected flow snapshot'),(0x86B,8,'startup flow adder'),
    (0x86C,8,'startup flow divider'),(0x86D,8,'proportional flow'),(0x86E,16,'derivative lag'),
    (0x870,8,'derivative flow magnitude'),(0x871,16,'selected cold flow'),(0x873,16,'selected cold bound'),
    (0x875,8,'cold-flow decay delay'),(0x876,8,'AC transition flow'),(0x877,8,'AC transition hold'),
    (0x878,8,'AC transition divider'),(0x879,8,'gear transition flow'),(0x87A,8,'gear transition hold'),
    (0x87B,8,'switch flow adder'),(0x87C,8,'switch flow hold'),(0x87D,16,'previous/base composite flow'),
    (0x87F,8,'IAC-change AE contribution'),(0x880,16,'throttle follower flow'),(0x882,16,'filtered scaled TPS'),
    (0x884,8,'follower delay'),(0x885,8,'TPS closed threshold'),(0x886,8,'cracker age'),
    (0x887,8,'DFCO flow correction'),(0x888,8,'DFCO correction divider'),(0x889,16,'pre-BARO flow'),
    (0x88B,16,'final IAC flow'),(0x88D,8,'kicker timer'),(0x88E,8,'IAC diagnostic timer'),
    (0x88F,16,'park/no-AC transfer'),(0x891,16,'park/AC transfer'),(0x893,16,'park cold transfer'),
    (0x895,16,'drive/no-AC transfer'),(0x897,16,'drive/AC transfer'),(0x899,16,'drive cold transfer')]]


def init_class(a):
    if a < 0x36: return 'conditional low-retained-area clear at 7219/7222; local seed/reset rules apply'
    if a < 0x100: return 'unconditional clear at 716A; local seeds apply'
    if 0x100 <= a < 0x29D: return 'unconditional clear at 7173; later producers apply'
    if 0x29D <= a < 0x34E: return 'conditional retained-area clear at 722B; byte-only seeds may retain fractions'
    if 0x800 <= a < 0x900: return 'unconditional clear at 717C; local seeds apply'
    return 'separate hardware/service owner'


def build(rom):
    for pc, s in ANCHORS.items():
        if rom.read(pc, len(bytes.fromhex(s))) != bytes.fromhex(s):
            raise ValueError(f'Unexpected control bytes at {pc:04X}')
    if [rom.word(0x9C96+2*i) for i in range(8)] != [0x4FE2,0x4FED,0x4FF8,0x5003,0x500E,0x5019,0x5024,0x502F]:
        raise ValueError('IAC proportional table pointers changed')
    rows=[]; branches=[]; calls=[]; blocks=[]; unique={}; ranges=[]; writes={}
    for name, doc, start, end in BLOCKS:
        pc=start; count=0
        while pc < end:
            ins=decode(rom.read,pc)
            if ins.next_pc > end: raise ValueError(f'Block crosses instruction at {pc:04X}')
            if pc in unique: raise ValueError(f'Overlapping reviewed block at {pc:04X}')
            unique[pc]=ins; access=ins.access()
            row={'block':name,'pc':f'{pc:04X}','bytes_hex':ins.data.hex(' ').upper(),'mnemonic':ins.op,'operand':ins.operand,
                 'address_mode':ins.mode,'access':access['access'] if access else '',
                 'width_bits':access['width_bits'] if access else '',
                 'address':f"{access['address']:04X}" if access and access['address'] is not None else ''}
            rows.append(row)
            if access and access['address'] is not None and 'W' in access['access']:
                for a in range(access['address'],access['address']+access['width_bits']//8):writes.setdefault(a,set()).add(pc)
            if ins.op in BRANCHES or ins.op in {'BRSET','BRCLR'}:
                branches.append({**{k:row[k] for k in ['block','pc','bytes_hex','mnemonic','operand']},
                                 'condition':branch_condition(ins),'target':f'{ins.target:04X}','fallthrough':f'{ins.next_pc:04X}'})
            if ins.op in {'JSR','BSR'}:
                calls.append({'block':name,'pc':f'{pc:04X}','target':f'{ins.target:04X}' if ins.target is not None else ins.operand,
                              'boundary':'opaque low-memory extension' if ins.target is not None and ins.target<0x4000 else
                                         'conditional nonlocal stack exit; see IAC service contract' if ins.target==0xA407 else 'resident helper/callee; see contract'})
            pc=ins.next_pc; count+=1
        blocks.append({'block':name,'start':f'{start:04X}','end_exclusive':f'{end:04X}',
                       'instructions':count,'documentation':DOCS[doc],'status':'resident_software_documented;interfaces_explicit'})
        ranges.append({'purpose':name,'start':f'{start:04X}','end_exclusive':f'{end:04X}','bytes_hex':rom.read(start,end-start).hex(' ').upper()})
    for name,start,end in DATA:
        ranges.append({'purpose':name,'start':f'{start:04X}','end_exclusive':f'{end:04X}','bytes_hex':rom.read(start,end-start).hex(' ').upper()})
    roots=[]
    for entry in ROOTS:
        ins, front=walk_callee(rom,entry,load_regions())
        if front: raise ValueError(f'Unreviewed frontier at {entry:04X}: {front}')
        if set(ins)-set(unique): raise ValueError(f'Root outside captured instructions at {entry:04X}')
        roots.append({'entry':f'{entry:04X}','local_instructions':len(ins),
                      'return_sites':';'.join(f'{p:04X}' for p,i in sorted(ins.items()) if i.op in {'RTS','RTI'}),
                      'proof':'intraprocedural CFG; calls retained; A407 nonlocal return documented separately'})
    listing={r.pc:r for r in parse_listing(SOURCE)}; differences=[]
    for pc,ins in sorted(unique.items()):
        old=listing.get(pc)
        if old is None or old.op!=ins.op or canonical_operand(old.operand)!=canonical_operand(ins.operand):
            differences.append({'pc':f'{pc:04X}','bytes_hex':ins.data.hex(' ').upper(),
                                'ROM':ins.op+' '+ins.operand,'listing':old.op+' '+old.operand if old else '',
                                'classification':'local byte authority; original HAC and global partial overlay retained'})
    with (OUT/'factory_state_index.csv').open(newline='') as f: source_states={r['byte_address']:r for r in csv.DictReader(f)}
    states=[]
    for atext,width,role in STATES:
        a=int(atext,16); reviewed=set().union(*(writes.get(a+i,set()) for i in range(width//8)))
        candidates=set().union(*(set(source_states.get(f'{a+i:04X}',{}).get('write_pcs','').split(';')) for i in range(width//8)))-{''}
        other=candidates-{f'{p:04X}' for p in reviewed}
        states.append({'state':atext,'width_bits':width,'role':role,'reviewed_direct_writers':';'.join(f'{p:04X}' for p in sorted(reviewed)),
                       'other_listing_writer_candidates':';'.join(sorted(other)),'initialization':init_class(a),
                       'scope':'direct byte-overlap audit; cell aliases and external co-owners explicit in documentation'})
    cells=[{'address':a,'width_bits':w,'role':role,'indexed_store_pcs':p,
            'scope':'9C00/9C04 conditional X alias; 9C09 X+6; direct seed/background writers in state map'} for a,w,role,p in CELLS]
    consumer_docs={
        **{p:DOCS['iac'] for p in [0x99F2,0x9C4D,0x9D15,0x9D47]},
        **{p:DOCS['learn'] for p in [0x9EA7,0x9F6C,0x9FD3,0xA3F2]},
        **{p:DOCS['speed'] for p in [0x8EE9,0xD4DA,0xD4DD,0xDDC3,0xDE2F]},
        **{p:'docs/analysis/FACTORY_UPSTREAM_FUEL_CALCULATIONS.md' for p in [0x7F45,0x7F9A,0x899B,0x8A92,0x8BCF,0x8C79,0x8C88,0x8CA0,0xCF94]},
        **{p:'docs/analysis/FACTORY_FUEL_INTEGER_HANDOFF.md' for p in [0x8073,0x80C5,0x8213,0x82BC,0x82FC]},
        0x8765:'docs/analysis/FACTORY_CLOSED_LOOP_AND_LEARNING.md',
        0xA85A:'docs/analysis/FACTORY_UPSTREAM_SPARK_CALCULATIONS.md',
        0xAA9D:'docs/analysis/FACTORY_UPSTREAM_SPARK_CALCULATIONS.md',
        **{p:'docs/analysis/FACTORY_TRANSMISSION_CONTROL.md' for p in [0xACFC,0xADB4,0xADDE,0xAE11]},
        **{p:'docs/analysis/FACTORY_EMISSIONS_CONTROL.md' for p in [0xCBD6,0xD2EC,0xD2F9]},
        **{p:'docs/analysis/FACTORY_DIAGNOSTICS.md' for p in [0xDC17,0xDEBF]},
    }
    consumers=[]
    for address in ['0284','0812']:
        for pc_text in source_states[address]['read_pcs'].split(';'):
            pc=int(pc_text,16); ins=decode(rom.read,pc); access=ins.access()
            if not access or access['address']!=int(address,16) or 'R' not in access['access']:
                raise ValueError('VSS source consumer does not match ROM: '+pc_text)
            # Retain a minimal byte excerpt even for separately scoped consumers.
            ranges.append({'purpose':'VSS_consumer_'+pc_text,'start':pc_text,'end_exclusive':f'{ins.next_pc:04X}',
                           'bytes_hex':ins.data.hex(' ').upper()})
            consumers.append({'pc':pc_text,'state':address,'width_bits':access['width_bits'],
                              'bytes_hex':ins.data.hex(' ').upper(),'instruction':ins.op+' '+ins.operand,
                              'documentation':consumer_docs.get(pc,''),
                              'status':'documented_factory_path' if pc in consumer_docs else 'separate_transmission_emissions_AC_or_diagnostic_scope',
                              'proof_limit':'direct listing-seeded ROM-checked reader; not proof of all indexed consumers'})
    evidence={'rom_name':'BMHM.BIN','rom_size_bytes':65536,'rom_sha256':EXPECTED_SHA256,'listing_sha256_lf':text_sha256(SOURCE),
              'block_count':len(blocks),'instruction_starts':len(unique),'branch_count':len(branches),'selected_states':len(states),
              'scope':'resident IAC controller/learning/output and RPM/VSS/governor; raw inputs and physical behavior remain interfaces',
              'proof':'byte identity and regeneration; exact instruction/branch inventory; human-reviewed software derivations; not whole-ROM semantics',
              'byte_ranges':ranges}
    return {EVIDENCE.name:json.dumps(evidence,indent=2,sort_keys=True)+'\n',
            'factory_idle_governor_blocks.csv':csv_text(blocks),'factory_idle_governor_roots.csv':csv_text(roots),
            'factory_idle_governor_instructions.csv':csv_text(rows),'factory_idle_governor_branches.csv':csv_text(branches),
            'factory_idle_governor_calls.csv':csv_text(calls),'factory_idle_governor_states.csv':csv_text(states),
            'factory_idle_governor_iac_cells.csv':csv_text(cells),
            'factory_rpm_vss_consumers.csv':csv_text(consumers),
            'factory_idle_governor_listing_discrepancies.csv':csv_text(differences)}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--rom',type=Path);p.add_argument('--write',action='store_true');p.add_argument('--check-recorded',action='store_true')
    a=p.parse_args()
    if a.check_recorded:
        if a.rom or a.write:p.error('Recorded mode is separate from full-image/write mode')
        rom=recorded_rom(json.loads(EVIDENCE.read_text()))
    elif a.rom:rom=full_rom(a.rom)
    else:p.error('Supply --rom or --check-recorded')
    for name,content in build(rom).items():
        path=OUT/name
        if a.write:path.write_text(content,encoding='utf-8')
        elif not path.exists() or path.read_text()!=content:raise ValueError('Idle/governor evidence differs: '+name)
    if not a.write:
        for doc in DOCS.values():
            if not (ROOT/doc).is_file():raise ValueError('Missing documentation: '+doc)
    print('PASS: IAC/RPM/VSS/governor byte evidence; '+('recorded consistency' if a.check_recorded else 'full stock image verified'))


if __name__=='__main__':main()
