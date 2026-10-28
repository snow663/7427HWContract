#!/usr/bin/env python3
"""ROM-backed rooted CFG and ownership inventory, with explicit external edges.

Conditional branches and normal call returns are overapproximated. WAI/STOP
resume edges are conditional on wake/return. Arbitrary factory targets are not
expanded into an invented set of legal functions. No execution coverage claim.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import csv
import json
from pathlib import Path

from build_factory_scheduler import canonical_operand, csv_text, full_rom, recorded_rom
from factory_rom_decode import decode, successors
from factory_structure import ROOT, SOURCE, parse_listing, text_sha256
from verify_factory_rom_structure import EXPECTED_SHA256
from verify_factory_dte import DATA as DTE_DATA
from verify_factory_idle_governor import DATA as IDLE_DATA
from verify_factory_upstream import CAL_RANGES

OUT = ROOT/'maps/structure'
EVIDENCE = OUT/'bmhm_global_structure_rom_evidence.json'
DOC = ROOT/'docs/analysis/FACTORY_GLOBAL_STRUCTURE_AUDIT.md'
VECTORS = ['SCI', 'SPI', 'pulse_accumulator_edge', 'pulse_accumulator_overflow',
           'timer_overflow', 'TOC5_or_TIC4', 'TOC4', 'TOC3', 'TOC2', 'TOC1',
           'TIC3', 'TIC2', 'TIC1', 'RTI_timer', 'IRQ', 'XIRQ', 'SWI',
           'illegal_opcode', 'COP_failure', 'clock_monitor', 'reset']
# These entry shapes are inspected separately, not silently promoted to reset roots.
ALTERNATES = [(0x7AA5,0x7AA6,'unreferenced RTS before first scheduler slot'),
              (0xA5D8,0xA5DA,'post-SWI branch back to A5D7'),
              (0xF564,0xF5A2,'uncalled rounded saturating16x16 helper'),
              (0xFF90,0xFF99,'three JMP-form external-entry candidates')]
TAIL_DATA = [('zero_tail',0xFE9F,0xFF90),('zero_gap',0xFF99,0xFFA0),
             ('unreferenced_tail_words',0xFFA0,0xFFC0),('reserved_vector_words',0xFFC0,0xFFD6)]
DATA = DTE_DATA+IDLE_DATA+CAL_RANGES+[
    ('main_dispatch_words',0x7A85,0x7AA5), ('factory_serial_and_cycle_data',0xFBD7,0xFC04),
    ('interrupt_vectors',0xFFD6,0x10000)]+TAIL_DATA
SPAN_MAPS = ['factory_upstream_blocks.csv','factory_idle_governor_blocks.csv',
             'factory_dte_blocks.csv','factory_serial_blocks.csv']


def csv_rows(name):
    with (OUT/name).open(newline='') as f: return list(csv.DictReader(f))


def build(rom):
    roots = []
    for index, name in enumerate(VECTORS):
        address = 0xFFD6+2*index; target = rom.word(address)
        roots.append({'vector_address':f'{address:04X}','name':name,'target':f'{target:04X}',
                      'proof':'ROM vector word; interrupt enable/admission is separate'})
    slots = [rom.word(0x7A85+2*i) for i in range(16)]
    instructions = {}; edges = set(); frontiers = set(); pending = [int(r['target'],16) for r in roots]
    while pending:
        pc = pending.pop()
        if pc in instructions: continue
        if not 0x7100 <= pc < 0xFFD6: raise ValueError(f'Unexpected nonresident root {pc:04X}')
        i = decode(rom.read,pc); instructions[pc] = i
        local = successors(i)
        if i.op in {'WAI','STOP'}:
            local.append((i.next_pc,'conditional_resume_after_interrupt_or_wake'))
        for target, kind in local:
            edges.add((pc,target,kind)); pending.append(target)
        if i.op in {'JSR','BSR'}:
            if i.target is not None:
                edges.add((pc,i.target,'call'))
                if i.target < 0x7100:
                    frontiers.add((pc,f'{i.target:04X}','external_extension; effects and return unknown'))
                else: pending.append(i.target)
            elif pc == 0x7A4F:
                for target in slots:
                    edges.add((pc,target,'reviewed16_word_dispatch')); pending.append(target)
            else:
                if pc != 0xFAA5: raise ValueError(f'Unreviewed indirect call {pc:04X}')
                frontiers.add((pc,'wordRAM[038E]','payload_supplied_callback; no resident target whitelist'))
        if i.op == 'JMP' and i.target is None:
            frontiers.add((pc,i.operand,'unresolved_indirect_jump'))
        if i.op == 'SWI':
            edges.add((pc,rom.word(0xFFF6),'software_interrupt'))
    covered = {}; data = defaultdict(set)
    for name,start,end in DATA:
        rom.read(start,end-start)
        for address in range(max(0x7100,start),end): data[address].add(name)
    for pc,i in sorted(instructions.items()):
        for address in range(pc,i.next_pc):
            if address in covered: raise ValueError(f'Rooted instruction overlap at {address:04X}')
            if address in data: raise ValueError(f'Rooted code enters reviewed data at {address:04X}')
            covered[address] = pc
    alternates = []; alternative_bytes = set(); alternate_instructions = {}
    for start,end,reason in ALTERNATES:
        pc = start
        while pc < end:
            i = decode(rom.read,pc)
            if i.next_pc > end: raise ValueError('Alternate decode crosses boundary')
            if any(a in covered or a in data for a in range(pc,i.next_pc)):
                raise ValueError('Alternate review overlaps rooted code or classified data')
            alternate_instructions[pc] = i; alternative_bytes.update(range(pc,i.next_pc))
            alternates.append({'pc':f'{pc:04X}','bytes_hex':i.data.hex(' ').upper(),'mnemonic':i.op,
                               'operand':i.operand,'role':reason,
                               'status':'ROM-decoded alternate candidate; no rooted incoming edge in this graph'})
            pc = i.next_pc
    for start,end in [(0xFE9F,0xFF90),(0xFF99,0xFFA0)]:
        if any(rom.read(start,end-start)): raise ValueError('Recorded zero tail changed')
    spans = []
    for name in SPAN_MAPS:
        for row in csv_rows(name):
            spans.append((int(row['start'],16),int(row['end_exclusive'],16),row['block'],name))
    def names_at(pc): return ';'.join(sorted({name for start,end,name,_ in spans if start<=pc<end}))
    rows = []; differences = []; direct = defaultdict(lambda:{'R':set(),'W':set()}); bits = []
    listing = {r.pc:r for r in parse_listing(SOURCE)}
    for pc,i in sorted(instructions.items()):
        a = i.access()
        rows.append({'pc':f'{pc:04X}','bytes_hex':i.data.hex(' ').upper(),'mnemonic':i.op,'operand':i.operand,
                     'mode':i.mode,'reviewed_span_names':names_at(pc),
                     'proof':'rooted structural may-reach; not execution or semantic proof'})
        old = listing.get(pc)
        if old is None or old.op != i.op or canonical_operand(old.operand) != canonical_operand(i.operand):
            differences.append({'pc':f'{pc:04X}','bytes_hex':i.data.hex(' ').upper(),
                                'ROM':(i.op+' '+i.operand).strip(),
                                'listing':(old.op+' '+old.operand).strip() if old else '',
                                'scope':'rooted ROM decode; raw HAC unchanged'})
        if a and a['address'] is not None:
            for address in range(a['address'],a['address']+a['width_bits']//8):
                for direction in a['access']: direct[address&65535][direction].add(pc)
            if i.op in {'BSET','BCLR'}:
                bits.append({'pc':f'{pc:04X}','address':f"{a['address']:04X}",'operation':i.op,
                             'mask':f'{i.mask:02X}','reviewed_span_names':names_at(pc),
                             'limit':'direct bit mutation; full-byte stores and indexed/opaque writers separate'})
    roles = defaultdict(set)
    for name,column in [('factory_upstream_state_contracts.csv','state'),('factory_idle_governor_states.csv','state'),
                        ('factory_dte_states.csv','state'),('factory_serial_states.csv','address')]:
        for row in csv_rows(name):
            raw = row.get(column) or row.get('address')
            if raw and len(raw)==4:
                roles[int(raw,16)].add(row.get('role') or row.get('meaning') or row.get('name') or name)
    indexed = defaultdict(list)
    for row in csv_rows('factory_indexed_flow.csv'): indexed[int(row['pc'],16)].append(row)
    contextual_alias = defaultdict(set)
    for row in csv_rows('factory_indexed_flow.csv'):
        if 'W' in row['access']:
            for address in row.get('target_bytes','').split(';'):
                if address: contextual_alias[int(address,16)].add(int(row['pc'],16))
    states = []
    for address,accesses in sorted(direct.items()):
        states.append({'byte_address':f'{address:04X}','named_roles_at_base':';'.join(sorted(roles.get(address,set()))),
                       'direct_readers':';'.join(f'{p:04X}' for p in sorted(accesses['R'])),
                       'direct_writers':';'.join(f'{p:04X}' for p in sorted(accesses['W'])),
                       'previous_contextual_indexed_writers':';'.join(f'{p:04X}' for p in sorted(contextual_alias.get(address,set()))),
                       'proof':'all direct rooted byte overlaps; selected previous-context aliases only; arbitrary factory/hook/stack effects not excluded'})
    indexed_rows = []
    for pc,i in sorted(instructions.items()):
        a = i.access()
        if a and a['address'] is None:
            old = indexed.get(pc,[])
            indexed_rows.append({'pc':f'{pc:04X}','bytes_hex':i.data.hex(' ').upper(),'mnemonic':i.op,
                                 'operand':i.operand,'access':a['access'],'width_bits':a['width_bits'],
                                 'previous_context_results':';'.join(sorted({r['classification'] for r in old})),
                                 'previous_roots':';'.join(sorted({r['entry'] for r in old})),
                                 'reviewed_span_names':names_at(pc),
                                 'global_status':'contextual contracts exist; global address union not complete' if old else 'outside previous contextual index; trace caller/pointer lifetime'})
    regions = []; last = None
    for address in range(0x7100,0x10000):
        if address in covered: category,detail = 'rooted_instruction_bytes','structural CFG'
        elif address in data: category,detail = 'data_or_declared_tail',';'.join(sorted(data[address]))
        elif address in alternative_bytes: category,detail = 'alternate_candidate_bytes','separately decoded; no rooted incoming edge'
        else: category,detail = 'unclassified_bytes','needs review'
        key = category,detail
        if last is None or key != last:
            regions.append({'start':f'{address:04X}','end_exclusive':f'{address+1:05X}',
                            'byte_count':1,'classification':category,'evidence_role':detail}); last=key
        else:
            regions[-1]['end_exclusive']=f'{address+1:05X}';regions[-1]['byte_count']+=1
    counts = defaultdict(int)
    for row in regions: counts[row['classification']] += row['byte_count']
    edge_rows = [{'pc':f'{pc:04X}','target':f'{target:04X}','kind':kind,
                  'limit':'normal return/wake and branch feasibility conditional; interrupt ordering not proven'}
                 for pc,target,kind in sorted(edges)]
    tail_words = [{'address':f'{p:04X}','value':f'{rom.word(p):04X}',
                   'status':'literal tail word; intended external consumer not established'} for p in range(0xFFA0,0xFFC0,2)]
    summary = {'rom_name':'BMHM.BIN','rom_sha256':EXPECTED_SHA256,'rom_size_bytes':65536,
               'listing_sha256_lf':text_sha256(SOURCE),'vector_words':len(roots),
               'rooted_instruction_starts':len(instructions),'rooted_instruction_bytes':len(covered),
               'edge_rows':len(edge_rows),'frontier_rows':len(frontiers),'indexed_sites':len(indexed_rows),
               'directly_referenced_bytes':len(states),'direct_bit_writer_rows':len(bits),
               'listing_discrepancies':len(differences),'alternate_instruction_starts':len(alternates),
               'byte_classification_counts':dict(sorted(counts.items())),
               'scope':'ROM7100..FFFF rooted structural may-reach graph plus separately reviewed alternate/tail bytes; no whole-program behavior percentage',
               'proof':'all vectors, direct branches/calls,16 verified scheduler targets; arbitrary callback and eight extensions remain external',
               'byte_ranges':rom.ranges()}
    return {EVIDENCE.name:json.dumps(summary,indent=2,sort_keys=True)+'\n',
            'factory_global_vectors.csv':csv_text(roots),'factory_global_instructions.csv':csv_text(rows),
            'factory_global_control_edges.csv':csv_text(edge_rows),
            'factory_global_frontiers.csv':csv_text([{'pc':f'{p:04X}','target':t,'boundary':r} for p,t,r in sorted(frontiers)]),
            'factory_global_regions.csv':csv_text(regions),'factory_global_alternate_entries.csv':csv_text(alternates),
            'factory_global_listing_discrepancies.csv':csv_text(differences),'factory_global_state_ownership.csv':csv_text(states),
            'factory_global_indexed_accesses.csv':csv_text(indexed_rows),'factory_global_bit_writers.csv':csv_text(bits),
            'factory_global_tail_words.csv':csv_text(tail_words)}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--rom',type=Path);p.add_argument('--write',action='store_true');p.add_argument('--check-recorded',action='store_true')
    args=p.parse_args()
    if args.check_recorded:
        if args.rom or args.write:p.error('Recorded mode is separate from image/write mode')
        rom=recorded_rom(json.loads(EVIDENCE.read_text()))
    elif args.rom:rom=full_rom(args.rom)
    else:p.error('Supply --rom or --check-recorded')
    for name,content in build(rom).items():
        path=OUT/name
        if args.write:path.write_text(content,encoding='utf-8')
        elif not path.exists() or path.read_text(encoding='utf-8')!=content:raise SystemExit(f'Stale global evidence: {path}')
    if not DOC.exists():raise SystemExit(f'Missing global structure document: {DOC}')
    print('Factory global ROM structure and direct ownership inventory verified')


if __name__=='__main__':main()
