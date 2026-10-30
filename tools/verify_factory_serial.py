#!/usr/bin/env python3
"""Reproduce ROM-byte evidence for factory SCI, ALDL, service and test modes.

This inventories instructions, descriptor words, and local control/state edges.
It is documentation evidence, not a device simulation or whole-program proof.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from build_factory_scheduler import canonical_operand, csv_text, full_rom, recorded_rom
from factory_rom_decode import BRANCHES, decode
from factory_structure import ROOT, SOURCE, parse_listing, text_sha256
from verify_factory_rom_structure import EXPECTED_SHA256
from verify_factory_upstream import branch_condition

OUT = ROOT / 'maps/structure'
EVIDENCE = OUT / 'bmhm_serial_rom_evidence.json'
DOCS = ['docs/analysis/FACTORY_SERIAL_ALDL_PROTOCOL.md',
        'docs/analysis/FACTORY_SERVICE_AND_TEST.md',
        'docs/analysis/FACTORY_SERIAL_SERVICE_CLOSURE.md']
BLOCKS = [
    ('boot_serial_and_factory_admission', 0x7100, 0x71C3),
    ('timer_arm_and_foreground', 0x7459, 0x74D3),
    ('timer_factory_and_normal_dispatch', 0x793D, 0x7A85),
    ('transmission_service_admission', 0xAE85, 0xAEA4),
    ('factory_mode_refresh', 0xCB15, 0xCB31),
    ('register_initializer', 0xCC7C, 0xCCC1),
    ('ADC_test_helpers', 0xF20D, 0xF280),
    ('heartbeat_and_board_flush', 0xF3E4, 0xF420),
    ('extensions_and_optional_broadcast', 0xF5CF, 0xF64E),
    ('service_override_and_timeout', 0xF64E, 0xF7EA),
    ('SCI_ISR', 0xF7EA, 0xF822),
    ('transmitter', 0xF822, 0xF90B),
    ('receiver_and_reply', 0xF90B, 0xFA5B),
    ('factory_test_loop', 0xFA5B, 0xFBD7),
    ('trap_and_fallback_handlers', 0xFC04, 0xFC45),
]
DATA = [('ALDL_configuration', 0x518F, 0x558B),
        ('factory_descriptors_and_output_rows', 0xFBD7, 0xFC04),
        ('interrupt_vectors', 0xFFD6, 0x10000)]
ROOTS = [('engine', 0x51BF), ('transmission', 0x53A8)]
PAGES = [('engine', 0x51EF), ('engine', 0x5276), ('engine', 0x52FD),
         ('transmission', 0x53D8), ('transmission', 0x5463), ('transmission', 0x54DC)]
STATE_ROLES = {
    0x0001: 'factory callback armed bit0', 0x0002: 'scheduler/output-cycle phase',
    0x003B: 'SCI/ALDL flags; clear requests; service-active flags',
    0x0042: 'engine/transmission addressed-session bits0/1',
    0x0044: 'factory-entry bit0 and EST service bit2',
    0x0045: 'edge latches for clear/reset requests',
    0x0050: 'factory table/address-alias bit3; diagnostic input bit4',
    0x0360: 'received/transmitted byte count', 0x0361: 'running modulo256 checksum',
    0x0362: 'active descriptor word', 0x0364: 'last accepted descriptor device ID',
    0x0365: 'RX payload length or TX reply length', 0x0366: 'saved second byte of word',
    0x0367: 'receive-idle timeout count', 0x0368: 'active override duration word',
    0x036A: 'override inhibit/cooldown word', 0x036C: 'shared RX/TX payload base',
    0x038E: 'engine command byte or factory destination high byte',
    0x038F: 'engine masks or factory destination low byte',
    0x0390: 'engine output values or factory upload byte0',
    0x0391: 'engine requests: reset/clear/IAC/heartbeat',
    0x0392: 'engine command retained field without named direct consumer',
    0x0393: 'EGR and purge enable/selection bits',
    0x0394: 'EGR/purge override value', 0x0395: 'IAC/AFR enable and spark selection bits',
    0x0396: 'IAC position or desired RPM override', 0x0397: 'AFR override',
    0x0398: 'spark offset magnitude', 0x0399: 'transmission command byte',
    0x039A: 'transmission output enables', 0x039B: 'transmission output values',
    0x039C: 'transmission retained field without named direct consumer',
    0x039D: 'transmission retained field without named direct consumer',
    0x039E: 'transmission pressure override enable', 0x039F: 'pressure command value',
    0x03A0: 'transmission mode bits6/7', 0x03A1: 'transmission spark override',
    0x03A2: 'transmission retained field without named direct consumer',
    0x03A3: 'transmission retained field without named direct consumer',
    0x303A: 'COP service register', 0x3066: 'heartbeat port',
    0x3FFC: 'board control high byte', 0x3FFD: 'board control low byte; serial driver bit2',
}
WORDS = {0x0362, 0x0368, 0x036A}


def descriptor(rom, base):
    link, ident, flags, size, tx, rx = (rom.word(base), *rom.read(base+2, 3),
                                      rom.word(base+5), rom.word(base+7))
    return {'descriptor': f'{base:04X}', 'link': f'{link:04X}', 'id': f'{ident:02X}',
            'flags': f'{flags:02X}', 'length': size, 'tx_base': f'{tx:04X}',
            'rx_base': f'{rx:04X}', 'bytes_hex': rom.read(base, 9).hex(' ').upper()}


def build(rom):
    instructions = {}; rows = []; blocks = []; branches = []; calls = []
    for name, start, end in BLOCKS:
        pc = start; count = 0
        while pc < end:
            i = decode(rom.read, pc)
            if i.next_pc > end: raise ValueError(f'Instruction crosses {name} boundary')
            if pc in instructions and instructions[pc] != i: raise ValueError('Conflicting decode')
            instructions[pc] = i; a = i.access()
            rows.append({'block': name, 'pc': f'{pc:04X}', 'bytes_hex': i.data.hex(' ').upper(),
                         'mnemonic': i.op, 'operand': i.operand, 'mode': i.mode,
                         'access': a['access'] if a else '', 'width_bits': a['width_bits'] if a else '',
                         'address': f"{a['address']:04X}" if a and a['address'] is not None else ''})
            if i.op in BRANCHES or i.op in {'BRSET', 'BRCLR'}:
                branches.append({'pc': f'{pc:04X}', 'bytes_hex': i.data.hex(' ').upper(),
                                 'mnemonic': i.op, 'operand': i.operand,
                                 'condition': branch_condition(i), 'target': f'{i.target:04X}',
                                 'fallthrough': f'{i.next_pc:04X}'})
            if i.op in {'JSR', 'BSR', 'JMP'}:
                calls.append({'pc': f'{pc:04X}', 'mnemonic': i.op,
                              'target': f'{i.target:04X}' if i.target is not None else i.operand,
                              'boundary': 'runtime word from 038E; no ROM target whitelist' if pc == 0xFAA5
                              else 'external extension' if i.target is not None and i.target < 0x4000
                              else 'resident edge; call continuation requires return'})
            pc = i.next_pc; count += 1
        blocks.append({'block': name, 'start': f'{start:04X}', 'end_exclusive': f'{end:04X}',
                       'instruction_starts': count, 'scope': 'reviewed local software; physical interfaces separate'})
    for name, start, end in BLOCKS + DATA:
        rom.read(start, end-start)  # Capture complete reviewed instruction/data spans.
    desc = {}; commands = []
    for area, base in ROOTS:
        root = descriptor(rom, base); desc[base] = root
        for mode in range(11):
            pointer = base + 9 + mode*2; target = rom.word(pointer)
            if target:
                d = descriptor(rom, target); desc[target] = d
                if d['id'] != root['id']: raise ValueError('Command changes device ID')
            commands.append({'area': area, 'device_id': root['id'], 'command': f'{mode:02X}',
                             'pointer_address': f'{pointer:04X}', 'descriptor': f'{target:04X}',
                             'accepted': int(bool(target)), 'rule': 'mode<=10 and nonzero word; no per-mode RX length check'})
    pages = []
    for area, base in PAGES:
        d = descriptor(rom, base); desc[base] = d
        if d['flags'] != '80': raise ValueError('Live page has unexpected format')
        # The addressed reply length INCLUDES its echoed command byte.
        # Word aliases consume a second slot through 0366, not a second read.
        companion = None
        for index in range(d['length']-1):
            pointer = base+9+2*index; target = rom.word(pointer)
            mapped = target & 0xCFFF if 0x1000 <= target <= 0x3FFF else target
            actual = companion if companion is not None else mapped
            rule = 'saved low byte; this pointer entry is not dereferenced' if companion is not None else 'live word read; next slot uses saved low byte' if 0x1000 <= target <= 0x3FFF else 'live byte read'
            pages.append({'area': area, 'descriptor': f'{base:04X}', 'field_ordinal_1based': index+1,
                          'payload_ordinal_1based': index+2,
                          'pointer_address': f'{pointer:04X}', 'encoded_address': f'{target:04X}',
                          'normal_address': f'{actual:04X}', 'access': rule,
                          'limit': 'normal addressed reply; factory mode preserves encoded address'})
            companion = None if companion is not None else mapped+1 if 0x1000 <= target <= 0x3FFF else None
    for base in [0xFBD7, 0xFBE0, 0xFBE9]: desc[base] = descriptor(rom, base)
    factory = [desc[p] for p in [0xFBD7, 0xFBE0, 0xFBE9]]
    if [d['id'] for d in factory] != ['01', '02', '03'] or factory[-1]['link'] != '0000':
        raise ValueError('Factory linked list changed')
    page_selectors = []
    for area, base in ROOTS:
        initial = rom.word(base+11)
        for selector in range(3):
            word = initial-6+2*selector; target = rom.word(word)
            page_selectors.append({'area': area, 'selector': selector, 'pointer_address': f'{word:04X}',
                                   'descriptor': f'{target:04X}', 'rule': 'selector>=3 coerced to0'})
            if target not in {p for a, p in PAGES if a == area}: raise ValueError('Unknown live page')
    differences = []; listing = {r.pc:r for r in parse_listing(SOURCE)}
    for pc, i in sorted(instructions.items()):
        old = listing.get(pc)
        if old is None or old.op != i.op or canonical_operand(old.operand) != canonical_operand(i.operand):
            differences.append({'pc': f'{pc:04X}', 'bytes_hex': i.data.hex(' ').upper(),
                                'ROM': (i.op+' '+i.operand).strip(),
                                'listing': (old.op+' '+old.operand).strip() if old else '',
                                'scope': 'ROM authority for local span; raw HAC retained'})
    # Include reviewed direct owners from the preceding subsystem contracts.
    owners = dict(instructions)
    for name in ['factory_upstream_instructions.csv', 'factory_idle_governor_instructions.csv',
                 'factory_dte_instructions.csv', 'factory_fuel_rom_instructions.csv',
                 'factory_spark_rom_instructions.csv']:
        with (OUT/name).open(newline='') as f:
            for row in csv.DictReader(f):
                pc = int(row['pc'], 16); owners[pc] = decode(rom.read, pc)
    states = []
    for address, role in sorted(STATE_ROLES.items()):
        width = 2 if address in WORDS else 1; readers = set(); writers = set()
        for pc, i in owners.items():
            a = i.access()
            if a and a['address'] is not None and set(range(address, address+width)) & set(range(a['address'], a['address']+a['width_bits']//8)):
                if 'R' in a['access']: readers.add(pc)
                if 'W' in a['access']: writers.add(pc)
        states.append({'address': f'{address:04X}', 'width_bits': width*8, 'role': role,
                       'reviewed_direct_readers': ';'.join(f'{p:04X}' for p in sorted(readers)),
                       'reviewed_direct_writers': ';'.join(f'{p:04X}' for p in sorted(writers)),
                       'indexed_ownership': 'F9AE shared receive; FA18 service/factory copy; FAB C upload destination can alias any address'.replace('FAB C', 'FABC'),
                       'limit': 'reviewed owner union; external calls, arbitrary factory pointers and implicit stack effects remain explicit'})
    cycles = [{'phase_index': index, 'row': f'{0xFBF2+index*3:04X}',
               'port3060_or': f'{rom.read(0xFBF2+index*3,1)[0]:02X}',
               'port3062_or': f'{rom.read(0xFBF3+index*3,1)[0]:02X}',
               'low3FFD_or': f'{rom.read(0xFBF4+index*3,1)[0]:02X}',
               'role': 'cycled row' if index<5 else 'disabled/default row'} for index in range(6)]
    summary = {'rom_name': 'BMHM.BIN', 'rom_sha256': EXPECTED_SHA256, 'rom_size_bytes': 65536,
               'listing_sha256_lf': text_sha256(SOURCE), 'block_count': len(blocks),
               'instruction_starts': len(instructions), 'branch_count': len(branches),
               'descriptors': len(desc), 'command_rows': len(commands), 'live_pointer_entries': len(pages),
               'selected_states': len(states), 'listing_discrepancies': len(differences),
               'scope': 'resident SCI/ALDL parser/transmitter, normal service and factory test loop; callback target intentionally unconstrained',
               'proof': 'ROM identity and reproducible byte/table/control inventories; human-reviewed documentation; not hardware execution',
               'byte_ranges': rom.ranges()}
    return {EVIDENCE.name: json.dumps(summary, indent=2, sort_keys=True)+'\n',
            'factory_serial_blocks.csv': csv_text(blocks), 'factory_serial_instructions.csv': csv_text(rows),
            'factory_serial_branches.csv': csv_text(branches), 'factory_serial_control_edges.csv': csv_text(calls),
            'factory_serial_descriptors.csv': csv_text([desc[p] for p in sorted(desc)]),
            'factory_serial_commands.csv': csv_text(commands), 'factory_serial_page_selectors.csv': csv_text(page_selectors),
            'factory_serial_live_pointers.csv': csv_text(pages), 'factory_serial_states.csv': csv_text(states),
            'factory_test_output_rows.csv': csv_text(cycles), 'factory_serial_listing_discrepancies.csv': csv_text(differences)}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--rom', type=Path); p.add_argument('--write', action='store_true')
    p.add_argument('--check-recorded', action='store_true'); args = p.parse_args()
    if args.check_recorded:
        if args.rom or args.write: p.error('Recorded mode is separate from image/write mode')
        rom = recorded_rom(json.loads(EVIDENCE.read_text()))
    elif args.rom: rom = full_rom(args.rom)
    else: p.error('Supply --rom or --check-recorded')
    for name, content in build(rom).items():
        path = OUT/name
        if args.write: path.write_text(content, encoding='utf-8')
        elif not path.exists() or path.read_text(encoding='utf-8') != content:
            raise SystemExit(f'Stale serial evidence: {path}')
    for doc in DOCS:
        if not (ROOT/doc).exists(): raise SystemExit(f'Missing serial documentation: {doc}')
    print('Factory SCI/ALDL/service/test ROM evidence verified')


if __name__ == '__main__': main()
