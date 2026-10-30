#!/usr/bin/env python3
"""Reproduce global alias, flag-writer and external-interface documentation.

Address formulas remain qualified contracts. A formula is not silently converted
to a physical target set. Opaque calls and arbitrary uploads retain universal
alias effects. No CPU simulator or hardware measurement is used by this pass.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import json
from pathlib import Path

from build_factory_scheduler import csv_text, full_rom, recorded_rom
from build_factory_state_flow import (classification, clear_override,
                                      fixed_loop_footprints, mask_rows, reviewed_stack_footprints,
                                      target_bytes)
from factory_alias_contracts import contracts
from factory_rom_decode import decode, successors
from factory_state_flow import analyze, word
from factory_structure import ROOT, SOURCE, text_sha256
from verify_factory_global_structure import VECTORS, build as global_build
from verify_factory_rom_structure import EXPECTED_SHA256

OUT = ROOT/'maps/structure'
EVIDENCE = OUT/'bmhm_ownership_rom_evidence.json'
DOCS = ['FACTORY_GLOBAL_ALIAS_CONTRACT.md', 'FACTORY_FLAG_LIFETIMES.md',
        'FACTORY_EXTERNAL_HARDWARE_BOUNDARIES.md', 'FACTORY_OWNERSHIP_CLOSURE.md']
GATES = [(0x0001,1,'factory_callback_armed'), (0x001A,0x20,'ROM_fault_fast_group'),
         (0x003A,0x20,'pending_main_pass'), (0x0044,1,'factory_mode'),
         (0x004F,4,'main_pass_busy'), (0x0051,4,'foreground_refresh_request'),
         (0x0086,0x40,'extension_and_profiling_enable'),
         (0x003B,0x10,'engine_service_active'), (0x003B,8,'transmission_service_active'),
         (0x003B,4,'shared_service_monitor_gate'), (0x0042,1,'engine_session'),
         (0x0042,2,'transmission_session')]
HOOKS = [(0x8C6A,0x1800,0x8C66,'AFR before024B publication'),
         (0x93D4,0x1803,0x93D0,'IAC before resident controller'),
         (0xF5D3,0x1806,0xF5CF,'background before0F00 store'),
         (0x8EDF,0x1809,0x8EDB,'governor returned carry/A can bypass target math'),
         (0xF5E4,0x180C,0xF5DC,'independent signature connection/initialization'),
         (0xAB66,0x180F,0xAB62,'spark conversion factor'),
         (0xA9E4,0x1812,0xA9E0,'composite spark before subsequent local override'),
         (0xD029,0x1815,0xD025,'EGR desired before service override')]


def rows(text):
    import io
    return list(csv.DictReader(io.StringIO(text)))


def analyze_global(rom, ins):
    table=[rom.word(0x7A85+2*i) for i in range(16)]
    vector_roots={rom.word(a) for a in range(0xFFD6,0x10000,2)}
    entries=vector_roots|set(table)|{0x7100,0x746C,0xFA5B}
    entries|={i.target for i in ins.values() if i.op in {'JSR','BSR'} and i.target in ins}
    functions={}
    for entry in sorted(entries):
        pending=[entry]; local={}
        while pending:
            pc=pending.pop()
            if pc in local:continue
            i=ins[pc];local[pc]=i
            pending.extend(t for t,_ in successors(i) if t in ins)
        functions[entry]=local
    graph={e:{i.target for i in f.values() if i.op in {'JSR','BSR'} and i.target in entries}
           for e,f in functions.items()}
    for entry,f in functions.items():
        if 0x7A4F in f:graph[entry].update(table)
    order=[]; active=set(); done=set()
    def visit(entry):
        if entry in active:raise ValueError('Recursive component needs a separately reviewed contract')
        if entry in done:return
        active.add(entry)
        for callee in sorted(graph[entry]):visit(callee)
        active.remove(entry);done.add(entry);order.append(entry)
    for entry in sorted(entries):visit(entry)
    summaries={}
    for entry in order:
        s=analyze(rom,entry,functions[entry],summaries,table,clear_override)
        fixed_loop_footprints(rom,s);reviewed_stack_footprints(rom,s)
        summaries[entry]=s
    return functions,summaries


def build(rom):
    # Capture the entire mapped image; low-memory BIN padding is never supplied
    # as runtime RAM, extension contents, or an interrupt input.
    rom.read(0x4000,0xC000)
    authority=global_build(rom)
    ins={int(r['pc'],16):decode(rom.read,int(r['pc'],16))
         for r in rows(authority['factory_global_instructions.csv'])}
    sites={p:i for p,i in ins.items() if i.access() and i.access()['address'] is None}
    functions,summaries=analyze_global(rom,ins)
    reviewed=contracts(rom,ins)
    contexts=[]; by_pc=defaultdict(list); calls=[]
    for entry,s in sorted(summaries.items()):
        for effect in sorted(s.local.values(),key=lambda e:e.pc):
            if effect.pc not in sites:continue
            row={'entry':f'{entry:04X}','pc':f'{effect.pc:04X}',
                 'analysis_class':classification(effect.address),'analysis_expression':effect.address.text(),
                 'analysis_target_bytes':';'.join(f'{a:04X}' for a in sorted(target_bytes(effect))),
                 'qualification':'finite abstract flow; generic entry registers; conditional normal return; no interrupt schedule proof'}
            contexts.append(row);by_pc[effect.pc].append((effect,row))
        for pc,(dest,bindings) in sorted(s.calls.items()):
            calls.append({'entry':f'{entry:04X}','call_pc':f'{pc:04X}',
                          'destinations':dest.text(),'argument_X':bindings['X'].text(),
                          'argument_Y':bindings['Y'].text(),
                          'argument_D':word(bindings['A'],bindings['B']).text(),
                          'scope':'call-specific inputs; unknown and opaque arguments retained'})
    # Bind the remaining state-writing helper signatures by EVERY rooted direct
    # caller, not by choosing one convenient call site. An unexpected argument
    # or non-call predecessor makes this specialization fail.
    for callee,register,expected in [(0xE58C,'Y',{0x00B9,0x00C8}),
                                     (0xF275,'X',{0x3000}),
                                     (0xF25F,'X',{0x3000}),
                                     (0xF479,'X',{0x0068,0x006A})]:
        found=[r for r in calls if r['destinations']==f'${callee:04X}']
        actual={r[f'argument_{register}'] for r in found}
        if not found or actual!={f'${a:04X}' for a in expected}:
            raise ValueError(f'Unbound argument for helper {callee:04X}: {actual}')
        incoming=[r for r in rows(authority['factory_global_control_edges.csv'])
                  if r['target']==f'{callee:04X}' and r['kind']!='call']
        if incoming:raise ValueError('Non-call helper entry requires additional alias context')
        for effect in summaries[callee].local.values():
            i=ins[effect.pc]
            if not i.mode.startswith('indexed_'):continue
            values=effect.address.items
            if not values or not all(getattr(v,'name',None)==register and v.part=='full' for v in values):continue
            offsets={v.offset for v in values}
            addresses=sorted({(base+offset)&65535 for base in expected for offset in offsets})
            reviewed[effect.pc]={'effective_address':effect.address.text(),
                                 'base_expression':f'caller_{register}',
                                 'role':f'all-rooted-caller binding of helper{callee:04X}',
                                 'proof_pcs':';'.join(sorted({r['call_pc'] for r in found})),
                                 'condition':f'only rooted direct calls to{callee:04X}; {register} in '+','.join(f'{a:04X}' for a in sorted(expected)),
                                 'kind':'reviewed_conditional_footprint','addresses':addresses}
    clear_calls=[i for i in ins.values() if i.op in {'JSR','BSR'} and i.target==0xF2FD]
    if {i.pc for i in clear_calls}!={0x716A,0x7173,0x717C,0x7219,0x7222,0x722B}:
        raise ValueError('Additional RAM clear call needs a contract')
    # These entry lengths and destinations are immediate ROM arguments, not a
    # guessed value of a runtime register. Distinguish remainder and block stores.
    clear_starts={p:set() for p in [0xF301,0xF315,0xF318,0xF31B,0xF31E]}
    for call in clear_calls:
        x=decode(rom.read,call.pc-6);d=decode(rom.read,call.pc-3)
        if (x.op,x.mode,d.op,d.mode)!=('LDX','immediate','LDD','immediate'):
            raise ValueError('RAM clear argument shape changed')
        n,base=d.value,x.value
        clear_starts[0xF301].update(range(base,base+n%8))
        for pc,offset in [(0xF315,0),(0xF318,2),(0xF31B,4),(0xF31E,6)]:
            clear_starts[pc].update(base+n%8+8*j+offset for j in range(n//8))
    aliases=[]; alias_bytes={}; formal_writes=[]
    for pc,i in sorted(sites.items()):
        access=i.access(); local=by_pc.get(pc,[]); c=reviewed.get(pc)
        known=set(); frame=False; parameter=False; unknown=False
        for effect,row in local:
            known.update(target_bytes(effect))
            frame |= row['analysis_class']=='stack_relative'
            parameter |= row['analysis_class']=='caller_parameter'
            unknown |= row['analysis_class']=='unresolved'
        if c:
            expression=c['effective_address'];qualification=c['condition'];kind=c['kind']
            role=c['role'];proof=c['proof_pcs']
            if c['addresses'] is not None:
                known={((a+j)&65535) for a in c['addresses'] for j in range(access['width_bits']//8)}
                kind='reviewed_conditional_footprint'
            elif kind in {'runtime_pointer','stock_pruned','local_frame'}:
                known=set()
        else:
            expression=' | '.join(sorted({row['analysis_expression'] for _,row in local}))
            qualification='union of listed generic procedure contexts; instantiate entry parameters with call bindings'
            role='ROM-derived local register/stack flow';proof='factory_global_alias_contexts.csv'
            kind='caller_parameter' if parameter else 'local_frame' if frame else 'finite_context_union'
        if pc in clear_starts:
            known={a+j for a in clear_starts[pc] for j in range(access['width_bits']//8)}
            kind='reviewed_conditional_footprint'
            qualification='union of six immediate-argument ROM calls; 7219/7222/722B conditional on retained checksum rejection'
        if (unknown or not local) and not c:
            raise ValueError(f'Undocumented global alias {pc:04X}')
        if not expression:raise ValueError(f'Empty alias expression {pc:04X}')
        alias_bytes[pc]=known
        aliases.append({'pc':f'{pc:04X}','bytes_hex':i.data.hex(' ').upper(),'mnemonic':i.op,'operand':i.operand,
                        'access':access['access'],'width_bits':access['width_bits'],'contract_class':kind,
                        'address_expression':expression,'conditional_target_bytes':';'.join(f'{a:04X}' for a in sorted(known)),
                        'role':role,'condition':qualification,'proof_pcs_or_map':proof,
                        'procedure_contexts':';'.join(sorted({r['entry'] for _,r in local})),
                        'limit':'explicit memory access only; no arbitrary callback/hook/stack-corruption exclusion'})
        if 'W' in access['access'] and not known and kind not in {'local_frame','stock_pruned'}:
            formal_writes.append({'pc':f'{pc:04X}','address_expression':expression,'contract_class':kind,
                                  'condition':qualification,'limit':'bind this formal footprint before asserting a complete finite byte owner set'})
    # Merge direct and qualified indexed byte overlaps. A word at a base is
    # represented twice, so a neighboring-byte store cannot disappear.
    owners=defaultdict(lambda:{'R':set(),'W':set()})
    origins=defaultdict(set)
    for pc,i in sorted(ins.items()):
        a=i.access()
        if not a:continue
        addresses=alias_bytes.get(pc,set()) if a['address'] is None else {(a['address']+j)&65535 for j in range(a['width_bits']//8)}
        for address in addresses:
            for direction in a['access']:owners[address][direction].add(pc)
            origins[address].add('indexed_condition' if a['address'] is None else 'direct')
    owner_rows=[{'byte_address':f'{a:04X}','readers':';'.join(f'{p:04X}' for p in sorted(v['R'])),
                 'writers':';'.join(f'{p:04X}' for p in sorted(v['W'])),
                 'sources':';'.join(sorted(origins[a])),
                 'limit':'indexed footprints conditional; formal writers and opaque/runtime wildcards separate'}
                for a,v in sorted(owners.items()) if a<0x4000]
    if {r['pc'] for r in formal_writes}!={'FABC'}:
        raise ValueError('Unexpected non-frame writer requires caller/pointer closure')
    if not {0x86FD,0xE49E}<=owners[0x0392]['R']:
        raise ValueError('Lost indexed0392 service consumers')
    masks={(int(r['store_pc'],16),int(r['destination'],16)):int(r['and_mask'],16) for r in mask_rows(rom)}
    bit_rows=[]
    flag_addresses={i.access()['address'] for i in ins.values() if i.op in {'BRSET','BRCLR','BSET','BCLR'} and i.access()['address'] is not None and i.access()['address']<0x1000}
    for pc,i in ins.items():
        if i.op in {'BRSET','BRCLR','BSET','BCLR'} and i.access()['address'] is None:
            flag_addresses.update(a for a in alias_bytes[pc] if a<0x1000)
    flag_addresses.update(a for a,_,_ in GATES)
    flag_addresses.update(range(0x000B,0x001F))
    flag_addresses.update(range(0x0056,0x005F))
    for address in sorted(flag_addresses):
        for pc in sorted(owners[address]['W']):
            i=ins[pc]; a=i.access()
            for bit in range(8):
                mask=1<<bit
                if i.op in {'BSET','BCLR'}:
                    if not i.mask&mask:continue
                    effect='set' if i.op=='BSET' else 'clear'
                elif i.op=='CLR' or pc in clear_starts:effect='clear'
                elif (pc,address) in masks:
                    effect='preserve' if masks[pc,address]&mask else 'clear'
                elif pc in {0x7486,0x748A,0x748E,0x7492,0x7496,0x749A,0x749E,0x74A2}:
                    effect='preserve_by_self_copy'
                else:effect='whole_byte_or_word_mutation; value_flow_required'
                bit_rows.append({'byte_address':f'{address:04X}','bit':bit,'mask':f'{mask:02X}',
                                 'writer_pc':f'{pc:04X}','bytes_hex':i.data.hex(' ').upper(),
                                 'instruction':(i.op+' '+i.operand).strip(),'effect_on_bit':effect,
                                 'condition':'see indexed alias contract' if a['address'] is None else 'instruction admission',
                                 'limit':'local bit effect; does not prove this writer is admitted or exclude formal/opaque aliases'})
    gate_rows=[]
    for address,mask,name in GATES:
        for r in bit_rows:
            if int(r['byte_address'],16)==address and int(r['mask'],16)&mask:
                gate_rows.append({'gate':name,**r})
    enable={int(r['writer_pc'],16):r['effect_on_bit'] for r in gate_rows if r['gate']=='extension_and_profiling_enable'}
    if enable!={0x7492:'preserve_by_self_copy',0xF31E:'clear'}:
        raise ValueError('Extension-enable lifetime now has an additional/value-changing writer')
    for callee,expected in [(0xF333,{0xF74C}),(0xF64E,{0xAEA0}),(0xAE85,{0x7A14})]:
        found={i.pc for i in ins.values() if i.op in {'JSR','BSR'} and i.target==callee}
        if found!=expected:raise ValueError('Special-mode clear admission needs a new caller review')
    hardware=[]
    for address,v in sorted(owners.items()):
        if not 0x3000<=address<0x4000:continue
        hardware.append({'byte_address':f'{address:04X}',
                         'read_pcs':';'.join(f'{p:04X}' for p in sorted(v['R'])),
                         'write_pcs':';'.join(f'{p:04X}' for p in sorted(v['W'])),
                         'evidence':'direct accesses plus conditional indexed footprints; hardware response not inferred'})
    # Record all actual uses of the separately exposed FF90-family entry words.
    alt_refs=[]
    for i in ins.values():
        if i.value in {0xFF90,0xFF93,0xFF96} or i.target in {0xFF90,0xFF93,0xFF96}:
            alt_refs.append({'pc':f'{i.pc:04X}','instruction':i.op+' '+i.operand})
    if alt_refs:raise ValueError('New resident reference to alternate interface needs review')
    frontiers=rows(authority['factory_global_frontiers.csv'])
    if {(int(r['pc'],16),r['target']) for r in frontiers} != {(p,f'{t:04X}') for p,t,_,_ in HOOKS}|{(0xFAA5,'wordRAM[038E]')}:
        raise ValueError('External control-frontier set changed')
    hook_rows=[]
    for pc,target,guard,role in sorted(HOOKS):
        i=ins[pc]
        if (i.op,i.target)!=('JSR',target):raise ValueError('Extension call differs')
        if target==0x180C:
            if rom.read(0xF5DC,8)!=bytes.fromhex('FE 18 00 8C 7E 18 26 03'):
                raise ValueError('Independent extension connection signature check differs')
            condition='word_runtime[1800]==7E18; no0086.6 requirement'
        else:
            g=ins[guard]
            skip=i.next_pc+2 if target==0x1809 else i.next_pc
            if (g.op,g.value,g.mask,g.target)!=('BRCLR',0x86,0x40,skip):
                raise ValueError('Extension enable guard differs')
            condition='0086.6 set at guard; local controller admission still applies'
        hook_rows.append({'call_pc':f'{pc:04X}','bytes_hex':i.data.hex(' ').upper(),
                          'destination':f'{target:04X}','guard_pc':f'{guard:04X}',
                          'condition':condition,'resident_position':role,
                          'boundary':'implementation absent; memory/register/return effects unknown'})
    products={
        'factory_global_alias_sites.csv':csv_text(aliases),
        'factory_global_alias_contexts.csv':csv_text(contexts),
        'factory_global_call_bindings.csv':csv_text(calls),
        'factory_global_alias_owners.csv':csv_text(owner_rows),
        'factory_global_formal_writers.csv':csv_text(formal_writes),
        'factory_global_flag_writers.csv':csv_text(bit_rows),
        'factory_global_gate_lifetimes.csv':csv_text(gate_rows),
        'factory_global_hardware_accesses.csv':csv_text(hardware),
        'factory_external_hook_contracts.csv':csv_text(hook_rows),
    }
    summary={'rom_name':'BMHM.BIN','rom_sha256':EXPECTED_SHA256,'rom_size_bytes':65536,
             'listing_sha256_lf':text_sha256(SOURCE),'procedure_entries':len(functions),
             'indexed_sites':len(aliases),'abstract_context_rows':len(contexts),
             'reviewed_formula_sites':len(reviewed),'call_binding_rows':len(calls),
             'alias_contract_classes':dict(sorted(Counter(r['contract_class'] for r in aliases).items())),
             'formal_writer_sites':len(formal_writes),'byte_owner_rows':len(owner_rows),
             'byte_owner_scope':'runtime addresses below4000; ROM read footprints remain in alias_sites rather than expanding checksum bytes into RAM-like owner rows',
             'flag_writer_rows':len(bit_rows),'gate_writer_rows':len(gate_rows),
             'hardware_byte_rows':len(hardware),
             'external_entry_direct_references':0,
             'scope':'all951 rooted explicit indexed memory sites have a qualified formula/context contract; finite global address closure is not asserted for formal/runtime writers',
             'byte_ranges':rom.ranges()}
    products[EVIDENCE.name]=json.dumps(summary,indent=2,sort_keys=True)+'\n'
    return products


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
        elif not path.exists() or path.read_text(encoding='utf-8')!=content:
            raise SystemExit(f'Stale ownership evidence: {path}')
    for name in DOCS:
        if not (ROOT/'docs/analysis'/name).exists():raise SystemExit(f'Missing ownership contract: {name}')
    print('Factory global alias/flag/interface documentation evidence verified')


if __name__=='__main__':main()
