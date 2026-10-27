#!/usr/bin/env python3
"""Pin the factory upstream-calculation documents to actual BMHM bytes.

This builds instruction, branch, table and state inventories for reviewed
software blocks. It verifies byte/document consistency, not physical hardware
behavior or a whole-ROM completion percentage.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from build_factory_scheduler import csv_text,full_rom,recorded_rom
from factory_rom_decode import decode,BRANCHES
from factory_structure import ROOT,SOURCE,text_sha256
from verify_factory_rom_structure import EXPECTED_SHA256

OUT=ROOT/'maps/structure'
EVIDENCE=OUT/'bmhm_upstream_rom_evidence.json'
DOCS={
 'fuel':'docs/analysis/FACTORY_UPSTREAM_FUEL_CALCULATIONS.md',
 'spark':'docs/analysis/FACTORY_UPSTREAM_SPARK_CALCULATIONS.md',
 'adaptive':'docs/analysis/FACTORY_CLOSED_LOOP_AND_LEARNING.md',
 'index':'docs/analysis/FACTORY_ENGINE_CALCULATION_CLOSURE.md',
}
# Ends are exclusive and checked against decoded instruction boundaries.
BLOCKS=[
 ('boot_sensor_seeds','fuel',0x7393,0x73FF,'01C6;01C3;01C0;01C7;0282;01D5;01D0;01D2;01DC;01DA;01DB;01DE','boot; byte-only history seeds and initial producer calls'),
 ('boot_crank_count_seed','fuel',0x744F,0x7459,'02CE','boot; conditional seed while 0004 bit3 is set'),
 ('reference_input','fuel',0x750F,0x7650,'082E;02CD;02CE;024C;0250','reference ISR; crank delivery and counters'),
 ('hot_restart_events','fuel',0x7650,0x7696,'0268;02C9;081E','reference events while fuel-run flag is set'),
 ('crank_event_gain','fuel',0x7827,0x785A,'D return','main/ISR crank pulse gain'),
 ('MAP_lag','fuel',0x7BA7,0x7BF5,'01C3;01C6','ordinary common fast group'),
 ('fuel_mode_and_AE','fuel',0x7D4B,0x7F86,'01D9;01D2;0257;02CF;023E;023F;01DC','ordinary odd fast group'),
 ('VE_selection','fuel',0x7F86,0x7FD8,'0231','ordinary odd; input to completed running-fuel contract'),
 ('crank_equation','fuel',0x858B,0x8613,'D return','crank helper plus its period coordinate'),
 ('battery_ignition_state','fuel',0x8613,0x863D,'0044;0050;0205','fuel tail with phase bit1 set'),
 ('O2_preparation','adaptive',0x863D,0x8790,'027B;026B;026C;026D;026E;003E;020F','fuel tail when phase bit1 clear'),
 ('O2_control','adaptive',0x8790,0x891E,'0280;027A;025F;020F;026F','fuel tail; proportional and integrator calculation'),
 ('AFR_base','fuel',0x891E,0x8A8B,'024A;0264;0266;0271;0050','fuel tail when phase low3=7'),
 ('PE_state','fuel',0x8A8B,0x8C38,'01E0;01E1;01E2;0276;0277;0278;024A;003D','AFR task; PE qualification and slew'),
 ('AFR_final','fuel',0x8C38,0x8C73,'01DB;024A;024B','AFR task; limits; service and extension boundaries'),
 ('BLM_cell_selection','adaptive',0x8C73,0x8D9E,'0247;0248;0818;081A','AFR task; table cell and validity'),
 ('BLM_transitions','adaptive',0x8D9E,0x8DEF,'0249;003D;0052','AFR task; transition handling'),
 ('decel_history_lags','fuel',0x8DEF,0x8E1D,'0240;01DE;01C7','AFR task; lagged TPS/load histories'),
 ('BLM_learning','adaptive',0x8E1D,0x8EB4,'0273;0274;0248;02B3-02C7;0065;01D4','AFR task; learning and last-sample state'),
 ('load_coordinates','fuel',0xA466,0xA4B3,'01C9;01C0;01CF','ordinary even fast group'),
 ('run_admission','spark',0xA4B3,0xA5E5,'004F;0050;0051;01EA;01F2;0202;0210;0211;0260','reference admission; startup and timeout'),
 ('RPM_coordinates','fuel',0xA5E5,0xA687,'005F;01E8;083D;0061;0062;0063;0067;0068;028E','ordinary even; RPM coordinate/filter production'),
 ('not_running_RPM','fuel',0xAC51,0xACA7,'005F;01E8;0061;0062;004B;0050','pre-qualified reference path; no normal spark handoff'),
 ('spark_base_terms','spark',0xA706,0xA792,'01C1;01C2;01F8;01F9;01FB;020B','ordinary even; table and modifier lookups'),
 ('spark_sum','spark',0xA792,0xA81E,'01F4;01FD','EGR term and word accumulator'),
 ('spark_MAT','spark',0xA81E,0xA84E,'083C;01FD','MAT multiplier application'),
 ('spark_idle','spark',0xA84E,0xA906,'0053;0050;01FD','idle qualification and signed correction'),
 ('spark_transient','spark',0xA906,0xA97A,'0838;083A;083B;01FD','temperature-qualified transient correction'),
 ('spark_decel','spark',0xA97A,0xA9E0,'0208;01F2;01FD;0051','decel retard and recovery'),
 ('spark_pre_knock_override','spark',0xA9E0,0xAA1A,'01FD;0053','optional extension and special fixed-demand gate'),
 ('spark_reference_burst','spark',0xAA1A,0xAA81,'01EE;020E;006E','reference subtraction; upper bound; burst logic'),
 ('spark_normal_knock','spark',0xAA81,0xAADC,'020D;020C;01EE','atomic event consumption and normal knock'),
 ('spark_limits_override','spark',0xAADC,0xAB3E,'01EE;D return','signed lower limits and service override'),
 ('fuel_authorization','fuel',0xAE5C,0xAE85,'003D;0851','main fuel call; one-way input-capture interval authorization latch'),
 ('TPS_coordinate','fuel',0xB1CF,0xB1F0,'01A6;A return','TPS normalization from raw input and learned zero'),
 ('BARO_coordinates','fuel',0xC583,0xC668,'02F3;02F4;01CC;01E4;01E3;01CD;01CE','slot1; physical/estimated barometric source'),
 ('coolant_coordinate','fuel',0xC96A,0xC9C0,'00A8;0006;0283','slot4 with phase bit4 clear; conversion and substitution'),
 ('environmental_lookup_inputs','fuel',0xC9F7,0xCA6B,'01E5;0243;0272;01CB;01BB;0842','slot4 with phase bit4 clear; temperature-dependent factors'),
 ('spark_lookup_inputs','spark',0xCA6B,0xCB15,'01FA;01FC;0841;0843;0844','slot7; MAT; PE and knock gains'),
 ('knock_reference_word','spark',0xCDF7,0xCE10,'3FD8','ordinary odd; companion hardware reference word'),
 ('low_octane','spark',0xCE10,0xCE7C,'0209;020A;0052','slot6; executes learning only at full phase06'),
 ('knock_interrupt','spark',0xCE7C,0xCEBB,'0203;020D','knock event interrupt; live3FC8 baseline'),
 ('knock_decay_fault','spark',0xCEBB,0xCF16,'020C;0207;0019','slot8; decay and sensor diagnostic'),
 ('EGR_desired','fuel',0xCF16,0xD03E,'01AE;006E','slot9; command qualification; extension/service boundary'),
 ('EGR_fraction','fuel',0xD03E,0xD14E,'01B0;01B1;01B2;006E','even subgroup0; fraction feeding fuel and spark'),
 ('temperature_startup_admission','fuel',0xE286,0xE562,'0236;0256;0242;023C;023D;02C8;02C9;02CB;003E','slotF; E30B onward only with phase bit4 clear'),
 ('shared_math','index',0xF436,0xF564,'D/A return; saved frame; optional pointed intermediate','shared signed-difference lags; lookups; multiply'),
 ('BLM_reset','adaptive',0xF280,0xF2AA,'02B3-02C7','reset to128 or boot range clamp'),
 ('boot_engine_seeds','index',0x742B,0x7441,'024A;0002;0248;02B3-02C7','boot seeds plus BLM boot clamp'),
 ('source_RPM_writer_exclusion_reader','index',0xB58F,0xB5AC,'A return from lookup','reader of B961/B967 pointer data; source B968 is not an RPM store on this path'),
]
CAL_RANGES=[('stock_calibration',0x4000,0x7100),('coolant_conversion_tables',0xFC45,0xFE45),
            ('source_RPM_false_writer_pointer_data',0xB961,0xB96D)]
ANCHORS={0xA7D7:'C3 00 80 16',0xA4F6:'4F 5F FD 02 60',0x7F86:'F6 01 C0 C1 40',
         0x7E40:'F6 01 C6 4F CE 02 B6 03',0x87E6:'12 3F 03 0E',
         0xCE10:'96 02 81 06 26 65 F6 02 09',0xC96A:'B6 08 2D CE FC 45',
         0x85B2:'96 06 CE 4D 9C',0xE2ED:'CE 4A F4 BD F4 C1',0x8C6A:'BD 18 00'}
STATES=[
 ('01C6',8,'filtered MAP coordinate','fuel'),('01C0',8,'load coordinate','fuel'),('01C9',8,'negative vacuum coordinate','fuel'),
 ('01CF',8,'normalized load coordinate','fuel'),('01CC',8,'barometric coordinate','fuel'),('01D9',8,'normalized TPS','fuel'),
 ('0006',8,'effective coolant coordinate','fuel'),('0283',8,'clipped coolant index','fuel'),('0257',16,'density term','fuel'),
 ('0236',16,'charge-temperature denominator','fuel'),('0231',8,'selected VE','fuel'),('0061',8,'low-speed RPM coordinate','fuel'),
 ('0062',8,'RPM coordinate','fuel'),('0063',16,'filtered idle RPM coordinate','fuel'),('01E8',16,'reference period','fuel'),
 ('024A',8,'commanded AFR','fuel'),('024B',8,'AFR shadow','fuel'),('0272',8,'idle AFR target','fuel'),('0278',8,'PE slew factor','fuel'),
 ('023E',8,'MAP AE synchronous adder','fuel'),('023F',8,'TPS AE contribution','fuel'),('023C',8,'async enrichment temperature factor','fuel'),
 ('023D',8,'MAP AE temperature factor','fuel'),('01E4',8,'TPS AE baro factor','fuel'),('01E5',8,'TPS lag factor','fuel'),
 ('01C7',16,'load history','fuel'),('01DC',16,'TPS AE history','fuel'),('01DE',16,'TPS decel history','fuel'),
 ('02C8',8,'startup AFR subtraction','fuel'),('02C9',8,'additional AFR correction','fuel'),('02CB',8,'startup spark adder','fuel'),
 ('02CF',16,'crank PW before event gain','fuel'),('02CD',8,'crank/reference admission count','fuel'),('02CE',8,'crank/reference gain count','fuel'),
 ('020F',8,'integrator','adaptive'),('027A',8,'proportional term','adaptive'),('026F',8,'signed additive INT/P correction','adaptive'),
 ('0247',8,'selected BLM cell','adaptive'),('0248',8,'selected/learned BLM','adaptive'),('01B2',16,'filtered EGR fraction','fuel'),
 ('01F8',8,'base spark lookup','spark'),('01F9',8,'coolant spark term','spark'),('01FA',8,'MAT spark magnitude','spark'),
 ('01FB',8,'barometric spark term','spark'),('01FC',8,'PE spark adder','spark'),('01F4',16,'filtered EGR spark term','spark'),
 ('01FD',16,'composite spark demand','spark'),('01EE',16,'signed command entering output conversion','spark'),
 ('0209',8,'low-octane activity','spark'),('020A',8,'low-octane base retard','spark'),('020B',8,'scaled low-octane retard','spark'),
 ('020C',8,'normal knock retard','spark'),('020D',8,'pending knock events','spark'),('020E',8,'burst hold count','spark'),
]


def branch_condition(ins):
    if ins.op in {'BRSET','BRCLR'}:
        test=f'(byte[operand] & ${ins.mask:02X})'
        return test+(' == mask (all selected bits)' if ins.op=='BRSET' else ' == 0 (all selected bits clear)')
    return {'BRA':'always','BRN':'never','BCC':'C=0','BCS':'C=1','BHI':'C=0 and Z=0','BLS':'C=1 or Z=1',
            'BNE':'Z=0','BEQ':'Z=1','BPL':'N=0','BMI':'N=1','BVC':'V=0','BVS':'V=1',
            'BGE':'N xor V=0','BLT':'N xor V=1','BGT':'Z=0 and N xor V=0','BLE':'Z=1 or N xor V=1'}.get(ins.op,'')


def initialization(address):
    if 0x36<=address<0x100:return '716A: unconditional zero clear'
    if 0x100<=address<0x29D:return '7173: unconditional zero clear; later producers/boot seeds apply'
    if 0x29D<=address<0x34E:return '722B: conditional nonvolatile-area clear; see startup/BLM reset rules'
    if 0x800<=address<0x900:return '717C: unconditional zero clear'
    return 'external/raw input or separate owner'


def build(rom):
    for pc,expected in ANCHORS.items():
        b=bytes.fromhex(expected)
        if rom.read(pc,len(b))!=b:raise ValueError(f'Upstream anchor differs at {pc:04X}')
    instructions=[];branches=[];blocks=[];writes={};ranges=[];unique={}
    for ident,doc,start,end,outputs,context in BLOCKS:
        pc=start;count=0
        while pc<end:
            ins=decode(rom.read,pc)
            if ins.next_pc>end:raise ValueError(f'Block ends inside instruction: {ident}:{pc:04X}')
            unique[pc]=ins
            row={'block':ident,'pc':f'{pc:04X}','bytes_hex':ins.data.hex(' ').upper(),'mnemonic':ins.op,'operand':ins.operand}
            access=ins.access()
            row.update(access=access['access'] if access else '',width_bits=access['width_bits'] if access else '',
                       address=f"{access['address']:04X}" if access and access['address'] is not None else '',address_mode=ins.mode)
            instructions.append(row)
            if access and 'W' in access['access'] and access['address'] is not None:
                for a in range(access['address'],access['address']+access['width_bits']//8):writes.setdefault(a,set()).add(pc)
            if ins.op in BRANCHES or ins.op in {'BRSET','BRCLR'}:
                branches.append({**{k:row[k] for k in ['block','pc','bytes_hex','mnemonic','operand']},
                                 'condition':branch_condition(ins),'target':f'{ins.target:04X}','fallthrough':f'{ins.next_pc:04X}'})
            pc=ins.next_pc;count+=1
        blocks.append({'block':ident,'start':f'{start:04X}','end_exclusive':f'{end:04X}','instruction_rows':count,
                       'outputs':outputs,'execution_context':context,'documentation':DOCS[doc],
                       'status':'ROM_resident_calculation_documented;external_inputs_explicit'})
        ranges.append({'purpose':ident,'start':f'{start:04X}','end_exclusive':f'{end:04X}','bytes_hex':rom.read(start,end-start).hex(' ').upper()})
    for name,start,end in CAL_RANGES:ranges.append({'purpose':name,'start':f'{start:04X}','end_exclusive':f'{end:04X}','bytes_hex':rom.read(start,end-start).hex(' ').upper()})
    state_rows=[]
    with (OUT/'factory_state_index.csv').open(newline='') as f:direct={r['byte_address']:r for r in csv.DictReader(f)}
    for text,width,role,doc in STATES:
        address=int(text,16);reviewed=set().union(*(writes.get(address+i,set()) for i in range(width//8)))
        indexed=set().union(*(set(direct.get(f'{address+i:04X}',{}).get('write_pcs','').split(';')) for i in range(width//8)))-{''}
        other=indexed-{f'{p:04X}' for p in reviewed}
        explanations={'B968':'source data-as-code candidate: B967/B969/B96B are lookup pointers read at B5A4; not an RPM writer in the reviewed flow',
                      'AB3E':'downstream spark handoff store; see FACTORY_SPARK_INTEGER_HANDOFF.md'}
        unclassified=other-set(explanations)
        if unclassified:raise ValueError('Unexplained source writer candidates for '+text+': '+','.join(sorted(unclassified)))
        state_rows.append({'state':text,'width_bits':width,'role':role,'reviewed_direct_write_pcs':';'.join(f'{p:04X}' for p in sorted(reviewed)),
                           'other_listing_candidate_write_pcs':';'.join(sorted(other)),
                           'other_candidate_classification':';'.join(explanations[p] for p in sorted(other)),
                           'initialization':initialization(address),'documentation':DOCS[doc],
                           'scope':'explicit_direct_writes_and_source_candidates;indexed_helper_effects_and_interfaces_documented_separately'})
    extensions=[{'pc':f'{pc:04X}','bytes_hex':ins.data.hex(' ').upper(),'target':f'{ins.target:04X}',
                 'boundary':'external RAM/extension implementation not in mapped stock ROM; resident call and guard documented'}
                for pc,ins in sorted(unique.items()) if ins.op in {'JSR','BSR'} and ins.target is not None and ins.target<0x4000]
    evidence={'rom_name':'BMHM.BIN','rom_size_bytes':65536,'rom_sha256':EXPECTED_SHA256,'listing_sha256_lf':text_sha256(SOURCE),
              'block_count':len(blocks),'unique_instruction_starts':len(unique),'instruction_rows':len(instructions),
              'scope':'upstream engine arithmetic and local state transitions; normalized/raw sensor and cross-controller interfaces explicit',
              'proof':'ROM identity; instruction and branch decoding; documented arithmetic; no claim of physical behavior or whole-program coverage',
              'branch_rule_reference':'NXP M68HC11ERG page12; BRSET requires all selected bits; BRCLR all selected bits clear',
              'byte_ranges':ranges}
    return {EVIDENCE.name:json.dumps(evidence,indent=2,sort_keys=True)+'\n','factory_upstream_blocks.csv':csv_text(blocks),
            'factory_upstream_instructions.csv':csv_text(instructions),'factory_upstream_branches.csv':csv_text(branches),
            'factory_upstream_state_contracts.csv':csv_text(state_rows),'factory_upstream_external_interfaces.csv':csv_text(extensions)}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--rom',type=Path);p.add_argument('--write',action='store_true');p.add_argument('--check-recorded',action='store_true')
    a=p.parse_args()
    if a.check_recorded:
        if a.rom or a.write:p.error('Recorded checking is separate from full-image mode')
        rom=recorded_rom(json.loads(EVIDENCE.read_text()))
    elif a.rom:rom=full_rom(a.rom)
    else:p.error('Supply --rom or --check-recorded')
    for name,content in build(rom).items():
        path=OUT/name
        if a.write:path.write_text(content,encoding='utf-8')
        elif not path.exists() or path.read_text()!=content:raise ValueError('Upstream evidence differs: '+name)
    if not a.write:
        for path in DOCS.values():
            if not (ROOT/path).is_file():raise ValueError('Missing upstream documentation: '+path)
    print('PASS: upstream document byte/instruction/state evidence; '+('recorded consistency' if a.check_recorded else 'complete stock image verified'))


if __name__=='__main__':main()
