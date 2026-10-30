#!/usr/bin/env python3
"""Verify the ROM side of the 1800 extension and chip-select interface.

Recorded mode uses the previously hash-identified full mapped byte evidence.
The F1 chip-select interpretation is conditional on that CPU register layout;
no external wiring, aliasing, module bytes or bench behavior is invented.
"""
from __future__ import annotations
import argparse
import csv
import json
from pathlib import Path

from build_factory_scheduler import full_rom, recorded_rom
from factory_rom_decode import decode
from factory_structure import ROOT
from verify_factory_rom_structure import EXPECTED_SHA256

OUT = ROOT/'maps/structure/factory_extension_memory_evidence.json'
BASE = ROOT/'maps/structure/bmhm_ownership_rom_evidence.json'
DOC = ROOT/'docs/analysis/FACTORY_EXTENSION_MEMORY_INTERFACE.md'
SPANS = [
    ('boot_relocation',0x7100,0x710D),
    ('CPU_initializer',0xCC7C,0xCCC1),
    ('AFR_hook_result',0x8C53,0x8C73),
    ('governor_hook_result',0x8EC9,0x8EE7),
    ('IAC_hook_continuation',0x93D0,0x93E1),
    ('spark_command_hook',0xA9DD,0xA9F2),
    ('spark_factor_hook',0xAB62,0xAB7C),
    ('EGR_hook_result',0xD022,0xD03E),
    ('background_hook',0xF5CF,0xF5DC),
    ('recurring_presence_check',0xF5DC,0xF5E8),
    ('module_status_admission',0xE4F1,0xE4FF),
    ('profiling_enable',0x7A55,0x7A79),
    ('serial_encoded_address_transform',0xF8B8,0xF8DE),
    ('factory_upload',0xFAB0,0xFACA),
]
CHANNELS = [
    ('1800','8C6A','8C66','RAM024A -> RAM024B; scalar returned A is overwritten'),
    ('1803','93D4','93D0','pre-IAC state hook; normal controller follows; no explicit scalar result'),
    ('1806','F5D3','F5CF','background state hook; A immediately overwritten with F7'),
    ('1809','8EDF','8EDB','entry A=RPM error magnitude; returned C=1 selects returned A ->0299'),
    ('180C','F5E4','F5DC','recurring signature-qualified connection hook; no0086.6 requirement'),
    ('180F','AB66','AB62','returned A saved atAB69 and used as F550 multiplier on word005F'),
    ('1812','A9E4','A9E0','RAM01FD command hook; returned D not directly consumed'),
    ('1815','D029','D025','RAM01AE desired-EGR hook; local service may overwrite afterward'),
]

def build(rom):
    with (ROOT/'maps/structure/factory_global_instructions.csv').open(newline='') as f:
        instructions=[decode(rom.read,int(r['pc'],16)) for r in csv.DictReader(f)]
    refs=[i for i in instructions if i.value is not None and 0x1800<=i.value<=0x1817
          or i.target is not None and 0x1800<=i.target<=0x1817]
    expected={int(row[1],16) for row in CHANNELS}|{0xF5DC}
    if {i.pc for i in refs}!=expected:
        raise ValueError('Additional rooted low-memory reference needs review')
    for entry,pc,guard,_ in CHANNELS:
        i=decode(rom.read,int(pc,16))
        if (i.op,i.target)!=('JSR',int(entry,16)):raise ValueError('Hook call changed')
    if rom.read(0x7100,13)!=bytes.fromhex('8E 03 FF CE 10 00 86 03 A7 3D CE 30 00'):
        raise ValueError('INIT/register-base setup changed')
    if rom.read(0xF5DC,12)!=bytes.fromhex('FE 18 00 8C 7E 18 26 03 BD 18 0C 39'):
        raise ValueError('Presence signature/call changed')
    # Straight-line initializer: caller supplies X=3000, and this body never
    # changes X. Derive byte stores from actual immediate values, not comments.
    registers={}; a=None; pc=0xCC7C
    while pc<0xCCC1:
        i=decode(rom.read,pc)
        if i.op=='CLRA':a=0
        elif i.op=='LDAA' and i.mode=='immediate':a=i.value
        elif i.op=='STAA' and i.mode=='indexed_x' and 0x5C<=i.value<=0x5F:
            if a is None:raise ValueError('Unknown chip-select value')
            registers[0x3000+i.value]=a
        elif i.op in {'LDX','PULX','INX','DEX','ABX','XGDX'}:
            raise ValueError('Initializer no longer preserves caller X')
        pc=i.next_pc
    if registers!={0x305C:0,0x305D:0xAC,0x305F:0xCB,0x305E:0}:
        raise ValueError('Chip-select configuration changed')
    ctl,size,addr=registers[0x305D],registers[0x305F],registers[0x305E]
    size_bytes=[65536,32768,16384,8192,4096,2048,1024,0][size&7]
    base=((addr&0xFC)<<8)&~(size_bytes-1) if size_bytes else 0
    ref_rows=[{'pc':f'{i.pc:04X}','bytes_hex':i.data.hex(' ').upper(),
               'mnemonic':i.op,'operand':i.operand,
               'kind':'control_transfer' if i.op=='JSR' else 'signature_data_read'} for i in refs]
    enable=[f'{i.pc:04X}' for i in instructions
            if i.op=='BRCLR' and i.value==0x86 and i.mask==0x40]
    if len(enable)!=9 or not {'7A55','E4F1'}<=set(enable):
        raise ValueError('Enable consumers need review')
    spans=[{'name':name,'start':f'{start:04X}','end_exclusive':f'{end:04X}',
            'bytes_hex':rom.read(start,end-start).hex(' ').upper()} for name,start,end in SPANS]
    return {
        'rom_sha256':EXPECTED_SHA256,
        'byte_source':'bmhm_ownership_rom_evidence.json in recorded mode; full hash-checked ROM in image mode',
        'rooted_instruction_starts':len(instructions),
        'rooted_instruction_bytes':sum(len(i.data) for i in instructions),
        'low_memory_literal_references':ref_rows,
        'enable_bit_86_6_branch_PCs':enable,
        'hardware_decode_model':'MC68HC11F1 expanded-mode register layout; actual package/wiring/aliases not inferred',
        'init_value_hex':'03',
        'register_base':'3000',
        'register_end_inclusive':'305F',
        'internal_RAM_page_base':'0000',
        'chip_select_register_values':{f'{k:04X}':f'{v:02X}' for k,v in sorted(registers.items())},
        'general_chip_select':{'start':f'{base:04X}','end_inclusive':f'{base+size_bytes-1:04X}',
            'size_bytes':size_bytes,'active_low':not bool(size&0x10),
            'address_valid':bool(size&8),'priority_over_program':bool(ctl&8)},
        'IO1_chip_select':{'enabled':bool(ctl&0x80),'start':'3060','end_inclusive':'37FF'},
        'IO2_chip_select':{'enabled':bool(ctl&0x20),'start':'3800','end_inclusive':'3FFF'},
        'program_chip_select':{'enabled_bit_written':bool(ctl&4),'size_bytes':[65536,32768,16384,8192][ctl&3]},
        'callee_observable_channels':[dict(zip(['entry','call','gate','channel'],r)) for r in CHANNELS],
        'byte_spans':spans,
        'limit':'resident calling/dataflow and conditional CPU decode only; external contents and wiring remain unproven',
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--rom',type=Path);p.add_argument('--check-recorded',action='store_true')
    p.add_argument('--write',action='store_true');args=p.parse_args()
    if args.rom and args.check_recorded:p.error('Choose image or recorded mode')
    if args.rom:rom=full_rom(args.rom)
    elif args.check_recorded:rom=recorded_rom(json.loads(BASE.read_text()))
    else:p.error('Supply --rom or --check-recorded')
    result=json.dumps(build(rom),indent=2,sort_keys=True)+'\n'
    if args.write:OUT.write_text(result,encoding='utf-8')
    elif OUT.read_text()!=result:raise SystemExit('Stale extension memory-interface evidence')
    if not DOC.exists():raise SystemExit('Missing extension interface document')
    print('Factory extension memory-map and caller evidence verified')

if __name__=='__main__':main()
