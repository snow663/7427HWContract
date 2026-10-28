#!/usr/bin/env python3
"""ROM evidence for resident diagnostics, transmission and emissions contracts.

The maps are instruction/table evidence, not a whole-ROM completion metric.
--check-recorded checks committed excerpts; --rom checks a complete stock image.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from build_factory_scheduler import canonical_operand, csv_text, full_rom, recorded_rom, walk_callee
from factory_rom_decode import BRANCHES, decode
from factory_structure import ROOT, SOURCE, load_regions, parse_listing, text_sha256
from verify_factory_rom_structure import EXPECTED_SHA256
from verify_factory_upstream import branch_condition

OUT = ROOT / 'maps/structure'
EVIDENCE = OUT / 'bmhm_dte_rom_evidence.json'
DOCS = {
    'trans': 'docs/analysis/FACTORY_TRANSMISSION_CONTROL.md',
    'diag': 'docs/analysis/FACTORY_DIAGNOSTICS.md',
    'emiss': 'docs/analysis/FACTORY_EMISSIONS_CONTROL.md',
    'index': 'docs/analysis/FACTORY_DIAGNOSTICS_TRANSMISSION_EMISSIONS_CLOSURE.md',
}
# End addresses are exclusive. Embedded descriptors/curves are captured as data.
BLOCKS = [
    ('boot_diagnostic_and_adaptive_validation', 'diag', 0x718A, 0x7272),
    ('boot_DTC_recovery_ages', 'diag', 0x7272, 0x7393),
    ('cam_missing_counter', 'diag', 0x785A, 0x7875),
    ('tick_force_current_acquisition', 'trans', 0x7B6D, 0x7BA7),
    ('force_current_feedback_and_brake', 'trans', 0x7C13, 0x7D4B),
    ('MAP_low_diagnostic', 'diag', 0xA4B3, 0xA4EC),
    ('EST_post_handoff_monitor', 'diag', 0xABCB, 0xAC51),
    ('EST_monitor_shared_return', 'diag', 0xACA0, 0xACA7),
    ('shift_lamp', 'trans', 0xACA7, 0xADAA),
    ('nonelectronic_TCC', 'trans', 0xADAA, 0xAE5C),
    ('VATS_input', 'diag', 0xAE5C, 0xAE85),
    ('transmission_input_pipeline', 'trans', 0xAE85, 0xB010),
    ('pattern_request', 'trans', 0xB018, 0xB084),
    ('input_faults_and_TPS', 'trans', 0xB089, 0xB1AC),
    ('TPS_zero_and_normalization', 'trans', 0xB1AC, 0xB1F0),
    ('speed_slip_ratio_and_gain_selection', 'trans', 0xB1F0, 0xB319),
    ('shift_observation_and_qualifiers', 'trans', 0xB32D, 0xB56B),
    ('pressure_pipeline', 'trans', 0xB56B, 0xB88D),
    ('pressure_environment_and_adaptive_read', 'trans', 0xB88D, 0xB961),
    ('adaptive_restore_and_neutralize', 'trans', 0xB99F, 0xBA32),
    ('adaptive_event_count', 'trans', 0xBA38, 0xBA5F),
    ('adaptive_shift_learning', 'trans', 0xBA65, 0xBC3B),
    ('pressure_shift_shape', 'trans', 0xBC77, 0xBE37),
    ('force_reference_and_TCC_transitions', 'trans', 0xBE5C, 0xC00B),
    ('TCC_apply_release_and_curve', 'trans', 0xC00B, 0xC2D6),
    ('transmission_spark_limit', 'trans', 0xC40A, 0xC483),
    ('pattern_selectors', 'trans', 0xC483, 0xC4E5),
    ('transmission_scheduler_wrappers', 'trans', 0xC4E5, 0xC514),
    ('solenoid_and_TCC_output', 'trans', 0xC514, 0xC56F),
    ('pump_voltage_and_BARO_acquisition', 'diag', 0xC56F, 0xC668),
    ('transmission_BARO', 'trans', 0xC668, 0xC6BB),
    ('TCC_qualification', 'trans', 0xC6BB, 0xC8B1),
    ('transmission_diagnostic_wrapper', 'diag', 0xC8B1, 0xC8D6),
    ('temperature_inputs_and_fallback', 'trans', 0xC8D6, 0xC9F7),
    ('AC_request_and_speed_gate', 'emiss', 0xCB15, 0xCC35),
    ('board_rearm', 'diag', 0xCC35, 0xCCC1),
    ('AIR_purge_shared_outputs', 'emiss', 0xCCC1, 0xCDF7),
    ('EGR_output', 'emiss', 0xCDF7, 0xCE10),
    ('EGR_desired', 'emiss', 0xCF16, 0xD03E),
    ('EGR_fraction', 'emiss', 0xD03E, 0xD14E),
    ('EGR_feedback', 'emiss', 0xD14E, 0xD1F6),
    ('EGR_position_controller', 'emiss', 0xD1F6, 0xD2B2),
    ('purge_controller', 'emiss', 0xD2B2, 0xD3B0),
    ('catalyst_model_and_manifold', 'emiss', 0xD3B0, 0xD4A3),
    ('shift_selection', 'trans', 0xD4EB, 0xD69F),
    ('shift_descriptor_helpers', 'trans', 0xD7E5, 0xD9B7),
    ('transmission_spark_requests', 'trans', 0xD9B7, 0xDBE3),
    ('MAT_acquisition_diagnostics', 'diag', 0xDBFB, 0xDC89),
    ('central_diagnostics_and_log', 'diag', 0xDC89, 0xE1EC),
    ('flash_code_reporting', 'diag', 0xE1EC, 0xE286),
    ('pump_feedback_diagnostic', 'diag', 0xE286, 0xE2C8),
    ('range_gear_cap', 'trans', 0xE562, 0xE57C),
    ('capture_estimator', 'trans', 0xE58C, 0xE5CF),
    ('fault_aggregation', 'diag', 0xE5CF, 0xE717),
    ('local_DTCs_and_long_shift', 'diag', 0xE75F, 0xF20D),
    ('ADC_input_helpers', 'diag', 0xF20D, 0xF280),
    ('ROM_checksum_and_clear_helper', 'diag', 0xF2AA, 0xF326),
    ('checksum_and_clear_A', 'diag', 0xF326, 0xF377),
    ('clear_B', 'diag', 0xF380, 0xF3DB),
    ('lamp_and_board_flush', 'diag', 0xF3EE, 0xF420),
    ('integer_helpers', 'index', 0xF420, 0xF564),
    ('service_selector_and_timeout', 'diag', 0xF64E, 0xF7EA),
]
DATA = [
    ('stock_calibration', 0x4000, 0x7100),
    ('range_decode', 0xB010, 0xB018), ('pattern_decode', 0xB084, 0xB089),
    ('solenoid_and_gains', 0xB319, 0xB32D), ('pressure_pointers', 0xB961, 0xB99F),
    ('adaptive_seed_pointers', 0xBA32, 0xBA38), ('adaptive_count_pointers', 0xBA5F, 0xBA65),
    ('adaptive_pointer_sets', 0xBC3B, 0xBC77), ('pressure_shape_pointers', 0xBE37, 0xBE5C),
    ('TCC_descriptors', 0xC2D6, 0xC40A), ('shift_descriptors', 0xD69F, 0xD7E5),
    ('spark_request_pointers', 0xDBE3, 0xDBFB), ('range_gear_caps', 0xE57C, 0xE58C),
    ('fault_reaction_masks', 0xE717, 0xE75F), ('clear_A_masks', 0xF377, 0xF380),
    ('clear_B_masks', 0xF3DB, 0xF3E4), ('temperature_tables', 0xFC45, 0xFE56),
    ('flash_code_values', 0xFE56, 0xFE9F),
]
ROOT_GROUPS = {
    'trans': [0x7C13,0x7D21,0xACA7,0xADAA,0xAE85,0xAEA4,0xB018,0xB089,0xB0E4,
              0xB1AC,0xB1CF,0xB1F0,0xB23C,0xB2B2,0xB2C9,0xB2ED,0xB32D,0xB334,0xB367,
              0xB4B2,0xB56B,0xB587,0xB88D,0xB91D,0xB99F,0xB9EE,0xBA38,0xBA65,0xBC77,
              0xBCC6,0xBE5C,0xBEBC,0xBF62,0xC00B,0xC271,0xC40A,0xC483,0xC4E5,0xC4F5,
              0xC514,0xC668,0xC6BB,0xC8D6,0xC8FD,0xC96A,0xC9C0,0xD4EB,0xD7E5,0xD840,
              0xD8A7,0xD8CE,0xD8F0,0xD8FE,0xD92E,0xD94B,0xD969,0xD980,0xD9B7,0xDA6F,
              0xDAE2,0xE562,0xE58C],
    'emiss': [0xCB15,0xCCC1,0xCDF7,0xCF16,0xD03E,0xD14E,0xD1F6,0xD2B2,0xD3B0,0xD472],
    'diag': [0x785A,0xABCB,0xAE5C,0xC56F,0xC583,0xC8B1,0xCC35,0xDBFB,0xDC89,0xE1EC,
             0xE5CF,0xE5F1,0xE60B,0xE62D,0xE654,0xE664,0xE674,0xE684,0xE69C,0xE6AC,
             0xE6BC,0xE6E4,0xE6E5,0xE6F5,0xE75F,0xE793,0xE7C7,0xE808,0xE847,0xE8C8,
             0xE905,0xE99E,0xEA40,0xEA7C,0xEAB1,0xEAE4,0xEB17,0xEB18,0xEB19,0xEB4D,
             0xEB81,0xEBC0,0xEC2D,0xEC79,0xECCC,0xECFF,0xED3F,0xED80,0xEDC1,0xEE02,
             0xEE5F,0xEE60,0xEE61,0xEEBC,0xEF2B,0xEF88,0xF02F,0xF0AD,0xF131,0xF1DD,
             0xF20D,0xF245,0xF25F,0xF275,0xF326,0xF333,0xF380,0xF3EE,0xF64E,0xF781],
}
DESCRIPTORS = [
    (0xC2D6,'TCC_release_speed'),(0xC2F8,'TCC_release_kickdown'),
    (0xC31A,'TCC_apply_speed'),(0xC33C,'TCC_apply_kickdown'),
    (0xC35E,'TCC_apply_base'),(0xC380,'TCC_release_base'),
    (0xC3A2,'TCC_apply_increment'),(0xC3C4,'TCC_release_increment'),
    (0xC3E6,'TCC_cold_gain'),(0xC3F8,'TCC_kickdown_cold_gain'),
    (0xD6BD,'upshift_speed'),(0xD6D7,'downshift_speed'),
    (0xD6F7,'upshift_kickdown_speed'),(0xD71D,'downshift_kickdown_speed'),
    (0xD743,'upshift_kickdown_RPM'),
    (0xD787,'upshift_fault_override'),(0xD79B,'downshift_fault_override'),
    (0xD7AF,'shift_cold_gain'),(0xD7C1,'kickdown_speed_floor'),(0xD7D3,'kickdown_RPM_gain'),
]
POINTER_SETS = [
    (0xD69F,6,'upshift helper argument record; kickdown/cold/floor/normal/cold/gain'),
    (0xD6AB,6,'downshift helper argument record; same field order'),
    (0xD6B7,3,'kickdown upshift RPM/cold-offset/gain'),
    (0xD6D1,3,'upshift normal cold-offset curves by gear'),
    (0xD6EB,3,'downshift normal cold-offset curves by gear'),
    (0xD6F1,3,'upshift RPM cold-offset words by gear'),
    (0xD717,3,'upshift kickdown cold-offset scalars by gear'),
    (0xD73D,3,'downshift kickdown cold-offset scalars by gear'),
    (0xD763,9,'upshift direct range overrides; three columns per row'),
    (0xD775,9,'downshift direct range overrides; three columns per row'),
    (0xB961,3,'pressure normal TPS/speed surfaces'),
    (0xB967,3,'pressure wrapped high-speed surfaces'),
    (0xB96D,9,'pressure upshift signed correction; normal/performance/manual'),
    (0xB97F,9,'pressure downshift correction; normal/performance/manual'),
    (0xB991,4,'pressure temperature/TPS surfaces by gear'),
    (0xB999,3,'pressure BARO scalar curves'),
    (0xBA32,3,'adaptive bank restore seeds'),
    (0xBA5F,3,'adaptive observation count banks'),
    (0xBC3B,3,'shift-time to adaptive-step lookup'),
    (0xBC41,3,'normal desired shift-time curves'),
    (0xBC47,3,'cold-BARO desired shift-time curves'),
    (0xBC4D,3,'performance desired shift-time curves'),
    (0xBC53,3,'performance cold-BARO desired shift-time curves'),
    (0xBC59,3,'short mean-ratio decision curves'),
    (0xBC65,3,'retained adaptive cell banks'),
    (0xBC6B,3,'adaptive upper bound curves'),
    (0xBC71,3,'adaptive lower bound curves'),
    (0xBE37,3,'pressure shape ratio decision curves'),
    (0xBE3D,3,'pressure shape initial-rate curves'),
    (0xBE43,3,'pressure shape later-rate curves'),
    (0xBE49,3,'pressure shape duration curves'),
    (0xBE4F,3,'pressure shape steady curves'),
    (0xBE55,3,'pressure shape initial values'),
    (0xDBE3,4,'shift spark surfaces by gear'),
    (0xDBEB,8,'shift spark ratio boundary byte pointers'),
]
# role names retain raw units; nominal physical labels are not new scaling proof.
STATE_ROLES = {
    0x7F:'TCC selector',0x80:'shift selector',0x81:'kickdown selector',0x82:'cold-gain selector',
    0x83:'shift event and direction flags',0x84:'shift threshold source',0x85:'shift observation flags',
    0x86:'run/voltage/output flags',0x87:'temperature selectors',0x89:'TCC apply/release state',
    0x8A:'TCC override and release state',0x8B:'TCC requests',0x8C:'TCC inhibit word',
    0x8E:'pressure transition and current faults',0x8F:'pressure shape seeded',
    0x90:'shift learning qualification',0x91:'shift learning qualification 2',0x92:'shift learning qualification 3',
    0x93:'adaptive event state',0x94:'diagnostic recovery observations',0x95:'diagnostic recovery observations 2',
    0x96:'diagnostic recovery observations 3',0x97:'diagnostic recovery observations 4',
    0x98:'fault reaction flags',0x99:'fault reaction flags 2',0x9A:'history/zero/slip flags',
    0x9C:'decoded transmission switches',0x9D:'previous switch flags',0x9E:'output discrepancy inputs',
    0x9F:'pattern request',0xA0:'previous pattern request',0xA1:'range stability age',0xA2:'range decode',0xA3:'previous range',
    0xA4:'transmission spark mode',0xAB:'cold interpolation weight',0xAC:'transmission BARO word',
    0xB0:'filtered transmission TPS word',0xB2:'biased transmission TPS',0xB4:'raw table temperature',
    0xB5:'filtered transmission temperature word',0xB7:'engine speed word',0xBD:'turbine speed word',
    0xC2:'filtered turbine speed word',0xC4:'gear-adjusted turbine speed word',0xC6:'filtered adjusted turbine speed word',
    0xCC:'output speed sample word',0xD1:'selected output speed word',0xD3:'filtered output speed word',
    0xD5:'last accepted output speed word',0xD7:'normalized transmission speed word',0xD9:'zero-based selected gear',
    0xDA:'shift observation origin',0xDB:'saturating shift age',0xDC:'elapsed shift window',0xDD:'desired-minus-observed shift time',
    0xDF:'adaptive negative headroom',0xE0:'adaptive positive headroom',0xE1:'adaptive step command',
    0xE2:'pressure command',0xE9:'TCC signed adjustment',0xEB:'filtered signed converter slip word',
    0xED:'absolute converter slip word',0xEF:'previous converter slip word',0xF1:'TCC base word',0xF3:'TCC candidate word',
    0xF9:'transmission ratio word',0xFC:'force-current rail qualification age',
    0x103:'service gear selector',0x10A:'service TCC selector',0x111:'service pressure override',
    0x11A:'adaptive restore/reset requests',0x126:'TCC command word',0x129:'TCC upper word bound',0x12B:'TCC lower word bound',
    0x13E:'signed pressure shape word',0x148:'current adaptive offset',0x149:'adaptive cell coordinate',
    0x14C:'force motor duty byte',0x14D:'force current reference',0x14E:'sampled current feedback',
    0x14F:'signed force current error',0x150:'force current accumulator word',0x152:'gain bucket',
    0x153:'force gain A',0x154:'force gain B',0x15A:'transmission spark request',0x15B:'shift spark maximum',
    0x16:'live DTC bank 0',0xB:'retained DTC bank 0',0x14:'retained diagnostic age',0x15:'retained checksum',
    0x3C:'flash reporting state',0x43:'diagnostic switch state',0x55:'pump feedback ADC',0x56:'logging candidate bank 0',
    0x6F:'engine fault/admission flags',0x70:'EGR diagnostic phase',0x71:'logging/lamp/diagnostic flags',0x72:'EGR/O2/lamp flags',
    0x214:'flash digits word',0x216:'flash code scan cursor',0x217:'flash pending bits',0x218:'flash time',
    0x219:'lean O2 timer',0x21A:'rich O2 timer word',0x21C:'O2 inactivity timer',0x21F:'EGR test cycle delay',
    0x220:'EGR stabilization timer',0x221:'EGR response timer',0x222:'EGR saved integrator',0x223:'EGR failure count',
    0x224:'EGR position timer',0x225:'EGR retest interval word',0x227:'EGR low ADC timer',0x228:'high MAP timer',
    0x22A:'pump diagnostic timer',0x22B:'DTC candidate persistence timer',0x22C:'EST no-change timer',
    0x1AE:'desired EGR position/duty',0x1AF:'EGR duty command',0x1B0:'EGR pressure sum',0x1B1:'EGR flow intermediate',
    0x1B2:'filtered EGR fraction word',0x1B4:'EGR ADC',0x1B5:'EGR closed reference word',
    0x1B7:'filtered EGR feedback word',0x1B9:'rounded EGR position',0x1BA:'absolute EGR error',
    0x1BB:'EGR coolant gain',0x1BC:'EGR integral word',0x1BE:'EGR proportional word',
    0x1D6:'purge duty byte',0x1D7:'purge adaptive multiplier',0x1D8:'purge update delay',
    0x78:'filtered catalyst estimate word',0x7A:'catalyst target',0x7B:'catalyst base',0x7C:'catalyst lag coefficient',
    0x7D:'catalyst AFR contribution',0x7E:'catalyst high TPS age',0x84C:'catalyst overtemperature age',
    0x2F8:'1-2 adaptive cell bank',0x309:'2-3 adaptive cell bank',0x31A:'3-4 adaptive cell bank',0x32B:'adaptive bank checksum',
    0x3062:'shared solenoid/IAC latch',0x3068:'force current hardware command word',0x306A:'TCC hardware command word',
    0x3FD4:'shared AC/manifold/governor command word',0x3FD6:'purge hardware command word',
    0x3FD8:'EGR hardware command word',0x3FDA:'AIR hardware command word',
}
WORDS = {0xAC,0xB0,0xB5,0xB7,0xBD,0xC2,0xC4,0xC6,0xCC,0xD1,0xD3,0xD5,0xD7,0xEB,0xED,0xEF,
         0xF1,0xF3,0xF9,0x8C,0x126,0x129,0x12B,0x13E,0x150,0x214,0x21A,0x225,
         0x1B2,0x1B5,0x1B7,0x1BC,0x1BE,0x78,0x3068,0x306A,0x3FD4,0x3FD6,0x3FD8,0x3FDA}


def build(rom):
    anchors = {0x7C4A:'81 01 27 04 81 FF',0xD8FE:'37 36 A6 00',0xC52C:'1E 02 40 16',
               0xEDD3:'12 9E 30 1A',0xCD93:'1F 00 38 0D',0xF6EF:'B6 03 A1 B7 01 11'}
    for pc,value in anchors.items():
        if rom.read(pc,len(bytes.fromhex(value))) != bytes.fromhex(value):
            raise ValueError(f'Changed DTE anchor {pc:04X}')
    ranges=[]; blocks=[]; rows=[]; branches=[]; calls=[]; unique={}; direct={}
    for name,area,start,end in BLOCKS:
        pc=start; count=0
        while pc<end:
            i=decode(rom.read,pc)
            if i.next_pc>end:raise ValueError(f'Crossed DTE block at {pc:04X}')
            if pc in unique:raise ValueError(f'Overlapping DTE instruction {pc:04X}')
            unique[pc]=i; a=i.access()
            row={'block':name,'area':area,'pc':f'{pc:04X}','bytes_hex':i.data.hex(' ').upper(),
                 'mnemonic':i.op,'operand':i.operand,'address_mode':i.mode,
                 'access':a['access'] if a else '', 'width_bits':a['width_bits'] if a else '',
                 'address':f"{a['address']:04X}" if a and a['address'] is not None else ''}
            rows.append(row)
            if a and a['address'] is not None:
                for address in range(a['address'],a['address']+a['width_bits']//8):
                    direct.setdefault(address,[]).append((pc,a['access']))
            if i.op in BRANCHES or i.op in {'BRCLR','BRSET'}:
                branches.append({**{k:row[k] for k in ['block','pc','bytes_hex','mnemonic','operand']},
                                 'condition':branch_condition(i),'target':f'{i.target:04X}','fallthrough':f'{i.next_pc:04X}'})
            if i.op in {'JSR','BSR'}:
                calls.append({'pc':f'{pc:04X}','area':area,'target':f'{i.target:04X}' if i.target is not None else i.operand,
                              'boundary':'opaque low-memory extension' if i.target is not None and i.target<0x4000 else 'resident call; continuation requires return'})
            pc=i.next_pc;count+=1
        blocks.append({'block':name,'area':area,'start':f'{start:04X}','end_exclusive':f'{end:04X}',
                       'instruction_starts':count,'documentation':DOCS[area],
                       'status':'reviewed_resident_software;named_external_interfaces_retained'})
        ranges.append({'purpose':name,'start':f'{start:04X}','end_exclusive':f'{end:04X}',
                       'bytes_hex':rom.read(start,end-start).hex(' ').upper()})
    for name,start,end in DATA:
        ranges.append({'purpose':name,'start':f'{start:04X}','end_exclusive':f'{end:04X}',
                       'bytes_hex':rom.read(start,end-start).hex(' ').upper()})
    roots=[]
    for area,entries in ROOT_GROUPS.items():
        for entry in entries:
            ins,front=walk_callee(rom,entry,load_regions())
            if front or set(ins)-set(unique):raise ValueError(f'DTE root not closed in excerpts {entry:04X}: {front}')
            roots.append({'entry':f'{entry:04X}','area':area,'local_instructions':len(ins),
                          'returns':';'.join(f'{p:04X}' for p,i in sorted(ins.items()) if i.op in {'RTS','RTI'}),
                          'documentation':DOCS[area],'proof':'local CFG; nested calls separately inventoried; no whole-program reachability claim'})
    differences=[]; listing={r.pc:r for r in parse_listing(SOURCE)}
    for pc,i in sorted(unique.items()):
        old=listing.get(pc)
        if old is None or old.op!=i.op or canonical_operand(old.operand)!=canonical_operand(i.operand):
            differences.append({'pc':f'{pc:04X}','bytes_hex':i.data.hex(' ').upper(),'ROM':i.op+' '+i.operand,
                                'listing':old.op+' '+old.operand if old else '',
                                'scope':'covered byte authority; raw HAC and global partial overlay remain separate'})
    descriptors=[]
    for base,role in DESCRIPTORS:
        stop,stride=rom.read(base,2)
        if not stop or stop&(stop-1):raise ValueError('Descriptor stop mask is not one bit')
        for bit in range(stop.bit_length()):
            for gear in range(stride//2):
                p=base+2+stride*bit+2*gear
                descriptors.append({'descriptor':f'{base:04X}','role':role,'stop_mask':f'{stop:02X}',
                                    'stride_bytes':stride,'selector_bit':f'{1<<bit:02X}','gear_column':gear,
                                    'pointer_pc':f'{p:04X}','target':f'{rom.word(p):04X}',
                                    'target_kind':'absent' if rom.word(p)==0 else 'RAM override' if rom.word(p)<0x4000 else 'calibration',
                                    'rule':'first selected bit wins before stop test; null pointer returns C=1'})
    pointer_sets=[]
    for base,count,role in POINTER_SETS:
        for index in range(count):
            a=base+2*index;target=rom.word(a)
            pointer_sets.append({'base':f'{base:04X}','index':index,'word_address':f'{a:04X}',
                                 'target':f'{target:04X}','role':role,
                                 'kind':'absent' if not target else 'RAM' if target<0x4000 else 'resident data or calibration',
                                 'rule':'direct word array; not a D8FE header'})
    dtcs=[]
    for bank in range(9):
        for bit in range(7,-1,-1):
            ordinal=bank*8+7-bit
            code=rom.read(0xFE57+ordinal,1)[0]
            dtcs.append({'code_bcd':f'{code:02X}','live_address':f'{0x16+bank:04X}','mask':f'{1<<bit:02X}',
                         'retained_address':f'{0xB+bank:04X}','candidate_address':f'{0x56+bank:04X}',
                         'logging_enable_address':f'{0x5B00+bank:04X}',
                         'logging_enable_stock':f'{rom.read(0x5B00+bank,1)[0]:02X}',
                         'lamp_mask_address':f'{0x5B09+bank:04X}',
                         'clear_A_keep_mask':f'{rom.read(0xF377+bank,1)[0]:02X}',
                         'clear_B_keep_mask':f'{rom.read(0xF3DB+bank,1)[0]:02X}',
                         'direct_setter_pcs':';'.join(f'{p:04X}' for p,i in sorted(unique.items())
                                                    if i.op=='BSET' and i.mode=='direct' and i.value==0x16+bank and i.mask&(1<<bit)),
                         'limit':'flash-table identity is not proof a populated monitor exists; indexed/boot producers can add setters'})
    with (OUT/'factory_state_index.csv').open(newline='') as f:old_states={r['byte_address']:r for r in csv.DictReader(f)}
    states=[]
    for address,role in sorted(STATE_ROLES.items()):
        width=16 if address in WORDS else 8
        accesses=set().union(*(set(direct.get(address+i,[])) for i in range(width//8)))
        writers={p for p,a in accesses if 'W' in a};readers={p for p,a in accesses if 'R' in a}
        candidates=set().union(*(set(old_states.get(f'{address+i:04X}',{}).get('write_pcs','').split(';')) for i in range(width//8)))-{''}
        states.append({'state':f'{address:04X}','width_bits':width,'role':role,
                       'reviewed_direct_writers':';'.join(f'{p:04X}' for p in sorted(writers)),
                       'reviewed_direct_readers':';'.join(f'{p:04X}' for p in sorted(readers)),
                       'other_listing_writer_candidates':';'.join(sorted(candidates-{f'{p:04X}' for p in writers})),
                       'limit':'direct byte-overlap inventory; indexed cell/capture/clear aliases specified in contracts'})
    evidence={'rom_name':'BMHM.BIN','rom_sha256':EXPECTED_SHA256,'rom_size_bytes':65536,
              'listing_sha256_lf':text_sha256(SOURCE),'block_count':len(blocks),
              'instruction_starts':len(unique),'branch_count':len(branches),'root_count':len(roots),
              'selected_states':len(states),'descriptor_count':len(DESCRIPTORS),
              'scope':'resident transmission/emissions and diagnostic monitors/logging/reporting; service local selectors only',
              'proof':'byte identity; CFG/table inventories; human-reviewed contracts; bounded execution tests separately labeled',
              'byte_ranges':ranges}
    return {EVIDENCE.name:json.dumps(evidence,indent=2,sort_keys=True)+'\n',
            'factory_dte_blocks.csv':csv_text(blocks),'factory_dte_roots.csv':csv_text(roots),
            'factory_dte_instructions.csv':csv_text(rows),'factory_dte_branches.csv':csv_text(branches),
            'factory_dte_calls.csv':csv_text(calls),'factory_dte_states.csv':csv_text(states),
            'factory_dte_listing_discrepancies.csv':csv_text(differences),
            'factory_transmission_descriptors.csv':csv_text(descriptors),
            'factory_transmission_pointer_sets.csv':csv_text(pointer_sets),
            'factory_diagnostic_bits.csv':csv_text(dtcs)}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--rom',type=Path);p.add_argument('--write',action='store_true');p.add_argument('--check-recorded',action='store_true')
    args=p.parse_args()
    if args.check_recorded:
        if args.rom or args.write:p.error('Recorded checking is separate from image/write mode')
        rom=recorded_rom(json.loads(EVIDENCE.read_text()))
    elif args.rom:rom=full_rom(args.rom)
    else:p.error('Supply --rom or --check-recorded')
    for name,content in build(rom).items():
        path=OUT/name
        if args.write:path.write_text(content,encoding='utf-8')
        elif not path.exists() or path.read_text(encoding='utf-8')!=content:raise SystemExit(f'Stale DTE evidence: {path}')
    for path in DOCS.values():
        if not (ROOT/path).exists():raise SystemExit(f'Missing DTE document: {path}')
    print('Factory diagnostics/transmission/emissions ROM evidence verified')


if __name__=='__main__':main()
