#!/usr/bin/env python3
"""Join stock interrupt sources, finite work and explicit timing boundaries.

Nominal own work is separate from input-arrival envelopes and unprovided code.
All local CFG cycles are inventoried; a scheduler pass ends before its tail.
SCC visit caps deliberately overestimate mutually exclusive paths.
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
from verify_factory_tick_timing import PERIOD_E

OUT=ROOT/'maps/structure'
FILES=('factory_irq_source_lifecycle.csv','factory_timing_loop_contracts.csv',
       'factory_execution_cycle_envelopes.csv','factory_interrupt_timing_closure_evidence.json')
STOCK_REF_GATES={0x7562:0x7566,0x7572:0x7576,0x769B:0x76D9,0x7797:0x77C6}

# Max visits per instruction in one activation of a local cyclic component.
# These are conditional semantic bounds, not arbitrary graph-unroll budgets.
LOOPS={
0x715B:(29,'X=3FC0; X+=2 until3FFA'),
0x7182:(65536,'16-bit X increment until03FF; initial ROM/RAM writes must be valid'),
0x7208:(0,'A is unchanged; A>=100 remains here until reset'),
0x724A:(256,'B decrements once per iteration; no inner B writer'),
0x7262:(256,'B decrements once per iteration'),
0x7473:(4112,'valid 16-byte aligned refresh cursor; wrap plus0400->0800 skip'),
0x74B7:(1024,'foreground X begins0000; increments until nonzero or03FF'),
0x773B:(2,'0051.7 set-only latch; checked output helpers preserve it'),
0x7989:(0,'main/catch-up repeats while asynchronously replenished003A.5; per-pass boundary7A51'),
0x7B79:(20,'powered stabilized E-clock ADC ready<=129 E after ADCTL write'),
0x7D8E:(0,'post-STOP self-loop; no normal return'),
0x868B:(1,'868A CLRB; first iteration restores B0 and exits at869E'),
0xAD29:(5,'AD0D/AD0F initialize0845=1; increment and exit when>=5'),
0xB620:(3,'B<ROM[5F2B] fromB616/B619; X starts5F29'),
0xB9AF:(54,'014A starts0 and reaches3; each row has17 cells; visit cap includes exit tests'),
0xB9FE:(54,'014A starts0 and reaches3; each row has17 cells'),
0xBB76:(6,'014B starts0; increment on each backedge and exit above4'),
0xD176:(12,'D174 loads B12; poll/DECB/BNE'),
0xD90D:(8,'D908 loads A1; shift until carry or selected bit; calls preserve stacked data'),
0xDD32:(9,'DD2F loads X9; DEX/BNE'),
0xE13A:(9,'E137 loads X9; DEX/BNE'),
0xE145:(9,'E142 loads X9; DEX/BNE'),
0xE164:(9,'E160 loads X9; DEX/BNE'),
0xE19B:(9,'E198 loads X9; DEX/BNE'),
0xE1B6:(9,'E1AF loads X9; DEX/BNE'),
0xE228:(73,'0216 increments once per repeated scan; exit when above47 hex'),
0xE633:(9,'E631 loads B9; DECB/BNE'),
0xE6C6:(9,'E6C3 loads B9; DECB/BNE'),
0xF267:(12,'F265 loads B12; poll/DECB/BNE'),
0xF285:(21,'X starts02B3 and increments through02C7'),
0xF297:(21,'X starts02B3 and increments through02C7'),
0xF2B9:(8,'A is a multiple of32; ADDA32 reaches zero'),
0xF2C5:(8192,'byte remainder aligns X to8; ABX8 reaches16-bit wrap; COP serviced each256 blocks'),
0xF2FD:(7,'at most seven remainder-byte clears before D multiple of8 or zero'),
0xF315:(256,'A is byte block count; DECA/BNE; normal caller supplies valid clear span'),
0xF32C:(10,'F329 loads B10; DECB/BNE'),
0xF33A:(9,'F333 loads X9; DEX/BNE'),
0xF387:(9,'F380 loads X9; DEX/BNE'),
0xF622:(256,'B byte count; normal stock broadcast schedule excludes this copy'),
0xF931:(3,'ROM root chains have three candidates and zero terminator'),
0xFA16:(255,'zero count skipped; accepted RX count<=34; normal service clamp<=11'),
0xFAB9:(32,'FAB7 loads B20 hex; upload may alias its own frame/counters and is a boundary'),
0xFBD4:(0,'factory end self-loop'),
0xFC07:(0,'SWI trap loop'),0xFC1D:(0,'illegal instruction trap loop'),0xFC27:(0,'clock-monitor trap loop')}


def components(nodes,edges):
    """Iterative Kosaraju; long ROM paths need no Python recursion increase."""
    seen=set();order=[]
    for start in sorted(nodes):
        if start in seen:continue
        seen.add(start);todo=[(start,iter(edges[start]))]
        while todo:
            p,children=todo[-1]
            try:t=next(children)
            except StopIteration:order.append(p);todo.pop();continue
            if t not in seen:seen.add(t);todo.append((t,iter(edges[t])))
    reverse={p:[] for p in nodes}
    for p in nodes:
        for t in edges[p]:reverse[t].append(p)
    groups=[];seen=set()
    for start in reversed(order):
        if start in seen:continue
        group=[];todo=[start];seen.add(start)
        while todo:
            p=todo.pop();group.append(p)
            for t in reverse[p]:
                if t not in seen:seen.add(t);todo.append(t)
        groups.append(tuple(sorted(group)))
    return groups


def build(rom):
    if sha256(bytes([255])*0x4000+rom.read(0x4000,0xC000)).hexdigest()!=EXPECTED_SHA256:
        raise ValueError('Mapped bytes do not match stock BMHM')
    def rows(name):
        with (OUT/name).open() as source:return list(csv.DictReader(source))
    ins={int(r['pc'],16):decode(rom.read,int(r['pc'],16)) for r in rows('factory_global_instructions.csv')}
    edges={p:[t for t,e in successors(i)] for p,i in ins.items()}
    cyclic=[g for g in components(ins,edges) if len(g)>1 or g[0] in edges[g[0]]]
    if {min(g) for g in cyclic}!=set(LOOPS):raise ValueError('Local cycle inventory changed')
    if rom.read(0x400B,2)!=bytes.fromhex('04 B7'):raise ValueError('Stock mode constants changed')
    guards={0x710D:'86 B8 A7 39',0x7111:'86 03 A7 24',0x7467:'86 A0 B7 30 22',
            0xCC81:'A7 2C',0xCC85:'A7 28',0xCC9D:'86 04 A7 2B 86 15 A7 3C',
            0x7562:'1F 00 04 13',0x756F:'CE 40 0B 1E 00 10 06',
            0x7696:'B6 40 0C 85 08 27 3C',0x7792:'B6 40 0B 85 01 27 2D'}
    for p,h in guards.items():
        data=bytes.fromhex(h)
        if rom.read(p,len(data))!=data:raise ValueError(f'Changed source premise at{p:04X}')
    owners={r['byte_address']:r for r in rows('factory_global_alias_owners.csv')}
    expected={0x3022:'7469;77DF;780F;7880;78E4;CC56;FC31',0x3024:'7113;FC3C',
              0x3028:'CC85',0x302B:'CC9F',0x302C:'CC81',
              0x302D:'7154;F645;F7AF;F811;F907;F950;FA48;FA57',
              0x3039:'710F;7D89',0x303C:'CCA3'}
    for a,writers in expected.items():
        if owners[f'{a:04X}']['writers']!=writers:raise ValueError(f'Changed register writers at{a:04X}')
    flag_writers={}
    for address,bit,pcs in [('003A','5',{'749A','7985','7A7D','F318'}),
                            ('004F','2',{'74A2','7974','7989','7A52','F31E'})]:
        selected=[r for r in rows('factory_global_flag_writers.csv') if r['byte_address']==address and r['bit']==bit]
        if {r['writer_pc'] for r in selected}!=pcs:raise ValueError('Busy/pending ownership changed')
        flag_writers[f'{address}.{bit}']={r['writer_pc']:r['effect_on_bit'] for r in selected}

    seen=set();active=set()
    @lru_cache(None)
    def ref_cost(p,returns=()):
        state=(p,returns)
        if state in active:raise ValueError('Unexpected cycle in stock REF')
        active.add(state);seen.add(p);i=ins[p]
        if i.op in {'JSR','BSR'}:tail=ref_cost(i.target,returns+(i.next_pc,))
        elif i.op=='RTS':tail=ref_cost(returns[-1],returns[:-1]) if returns else 0
        elif i.op=='RTI':tail=0
        else:
            selected=[STOCK_REF_GATES[p]] if p in STOCK_REF_GATES else edges[p]
            tail=max(ref_cost(t,returns) for t in selected)
        active.remove(state);return cycles(i)+tail
    ref_upper=ref_cost(0x74EA)
    if seen&{0x77DF,0x780F}:raise ValueError('Stock REF can enable OC4/5')
    enabler_calls={p for p,i in ins.items() if i.op in {'JSR','BSR'} and i.target in {0x77C7,0x77F7}}
    if enabler_calls!={0x773B,0x7754,0x77BB,0x77BE}:raise ValueError('New injector timer enable caller')

    # Complete local paths through the stack guard; the only call is the
    # previously proved full fast-service envelope, including its RTS.
    fast_upper=int(next(r['nominal_upper_E'] for r in rows('factory_tick_cycle_bounds.csv') if r['contract']=='fast_tick'))
    @lru_cache(None)
    def prefix(p):
        if p==0x797D:return 0
        i=ins[p]
        if p==0x797A:return cycles(i)+fast_upper+prefix(i.next_pc)
        selected=[0x7958] if p==0x794E else edges[p]
        return cycles(i)+max(prefix(t) for t in selected)
    prefix_upper=prefix(0x793D)
    @lru_cache(None)
    def busy_suffix(p):
        i=ins[p]
        if i.op=='RTI':return cycles(i)
        if p==0x7989:return cycles(i)  # first busy publication, before main work
        return cycles(i)+max(busy_suffix(t) for t in edges[p])
    to_busy_set=prefix_upper+cycles(ins[0x797D])+cycles(ins[0x7989])
    busy_with_guards=prefix_upper+busy_suffix(0x797D)

    sources=[]
    active_vectors={0xFFF2,0xFFE8,0xFFE4,0xFFD6}
    info={0xFFF2:('IRQ REF','OPTION.IRQE=1; global I0','edge latch; vector acknowledgment; not TFLG1.0','new falling edge; no ROM lower period'),
          0xFFE8:('OC1','TMSK1.7 & TFLG1.7','CE7E writes80 W1C','7503 writes TCNT+ROM[465D+(RPM62>>1 & FE)]; otherwise wrap'),
          0xFFE4:('OC3','TMSK1.5 & TFLG1.5','7948 writes20 W1C','7943 old_compare+819; first arm TCNT+8'),
          0xFFE2:('OC4','TMSK1.4 & TFLG1.4','78DE writes10 W1C','780F enable unreachable under stock mode gates; high output disables78E4'),
          0xFFE0:('OC5','TMSK1.3 & TFLG1.3','787A writes08 W1C','77DF enable unreachable under stock mode gates; high output disables7880'),
          0xFFD6:('SCI','RIE&(RDRF|OR) or TIE&TDRE or TCIE&TC','status/data read or status/read+data write; control26 at completion','SCCR2 26/24 ->88 ->40 ->26; RE/TIE epochs are exclusive'),
          0xFFD8:('SPI','SPCR.SPIE & (SPIF|MODF)','FC44 RTI does not acknowledge SPI','CC85 writes00; no resident SPI enable'),
          0xFFDA:('PA input','TMSK2.4 & PAIF','FC41 FF W1C TFLG2','TMSK2 only03; mask off'),
          0xFFDC:('PA overflow','TMSK2.5 & PAOVF','FC41 FF W1C TFLG2','TMSK2 only03; mask off'),
          0xFFDE:('timer overflow','TMSK2.7 & TOF','FC41 FF W1C TFLG2','TMSK2 only03; mask off')}
    for v,name,bit in [(0xFFE6,'OC2',6),(0xFFEA,'IC3',0),(0xFFEC,'IC2',1),(0xFFEE,'IC1',2),(0xFFF0,'RTI',6)]:
        info[v]=(name,f'TMSK{2 if v==0xFFF0 else 1}.{bit} & source flag','FC36 writes5F W1C TFLG1; FC31 writesA0 TMSK1','local mask never enabled; RTI flag itself is not cleared by this fallback')
    priorities={v:16-n for n,v in enumerate(range(0xFFD6,0xFFF4,2),1)}
    for v in range(0xFFD6,0xFFF4,2):
        name,request,ack,rearm=info[v]
        sources.append({'vector':f'{v:04X}','entry':f'{rom.word(v):04X}','source':name,
                        'F1_priority':priorities[v],'stock_admission':'live' if v in active_vectors else 'locally_disabled',
                        'request':request,'acknowledgment':ack,'rearm_or_disable':rearm,
                        'scope':'normal resident stock; no supplied code or arbitrary I/O aliases; reset X remains1'})

    loop_rows=[]
    for g in sorted(cyclic):
        start=min(g);cap,why=LOOPS[start]
        loop_rows.append({'component_start':f'{start:04X}','instruction_sites':len(g),
                          'max_visits_per_instruction':cap if cap else '',
                          'status':'conditional_finite' if cap else 'wait_repeat_or_terminal',
                          'premise_or_exit':why,'pcs':';'.join(f'{p:04X}' for p in g),
                          'bytes_sha256':sha256(b''.join(ins[p].data for p in g)).hexdigest()})

    # One main pass cannot include its catch-up jump. All direct procedure
    # entries are also summarized; terminals/opaque work retain named cuts.
    table={rom.word(0x7A85+2*n) for n in range(16)}
    entries={int(r['entry'],16) for r in rows('factory_stack_contracts.csv')}
    entries.add(0x7989)
    functions={}
    for entry in entries:
        local=set();todo=[entry]
        while todo:
            p=todo.pop()
            if p in local or entry==0x7989 and p==0x7A51:continue
            local.add(p);i=ins[p]
            if i.op not in {'WAI','STOP','SWI'}:todo.extend(edges[p])
        functions[entry]=local
    summaries={};busy=set()
    def summarize(entry):
        if entry in summaries:return summaries[entry]
        if entry in busy:raise ValueError('Recursive procedure cycle')
        busy.add(entry);local=functions[entry]
        local_edges={p:[t for t in edges[p] if t in local and ins[p].op not in {'WAI','STOP','SWI'}] for p in local}
        groups=components(local,local_edges);belong={p:n for n,g in enumerate(groups) for p in g}
        weights=[];cuts=set();opaque={}
        for group in groups:
            cyclic_group=len(group)>1 or group[0] in local_edges[group[0]]
            cap=1
            if cyclic_group:
                if min(group) not in LOOPS:raise ValueError('Unreviewed procedure cycle')
                cap=LOOPS[min(group)][0]
                if not cap:cuts.add(f'{min(group):04X}:wait_or_repeat');cap=1
            total=0
            for p in group:
                i=ins[p]
                if i.op in {'STOP','WAI','SWI'}:cuts.add(f'{p:04X}:{i.op}');continue
                total+=cycles(i)
                if p==0xFABC:cuts.add('FABC:arbitrary_upload_alias')
                if i.op in {'JSR','BSR'}:
                    targets=table if p==0x7A4F else {i.target}
                    children=[]
                    for target in targets:
                        if target in entries:
                            child=summarize(target);children.append(child[0]);cuts|=child[1]
                            for site,n in child[2].items():opaque[site]=opaque.get(site,0)+cap*n
                        else:
                            cuts.add(f'{p:04X}:supplied_code');opaque[f'{p:04X}']=opaque.get(f'{p:04X}',0)+cap
                    total+=max(children,default=0)
            weights.append(cap*total)
        graph={n:set() for n in range(len(groups))}
        for p in local:
            graph[belong[p]].update(belong[t] for t in local_edges[p] if belong[t]!=belong[p])
        @lru_cache(None)
        def path(n):return weights[n]+max((path(t) for t in graph[n]),default=0)
        upper=path(belong[entry]);result=(upper,cuts,opaque);summaries[entry]=result;busy.remove(entry);return result
    envelope_rows=[]
    for entry in sorted(entries):
        high,cuts,opaque=summarize(entry)
        envelope_rows.append({'entry':f'{entry:04X}','scope':'one_main_pass_stop_before7A51' if entry==0x7989 else 'procedure_resident_own_work',
                              'conditional_nominal_own_upper_E':high if not any('wait_or_repeat' in cut for cut in cuts) else '',
                              'status':'conditional_finite' if not cuts else 'conditional_own_work_with_boundaries',
                              'boundaries':';'.join(sorted(cuts)),
                              'supplied_call_coefficient_bounds':';'.join(f'{p}:{n}' for p,n in sorted(opaque.items())),
                              'premises':'listed loop entry domains; no interrupt changes to termination counters; valid frames/addresses; nominal costs; cuts are not assigned zero elapsed time'})
    offsets=[rom.word(p) for p in range(0x465D,0x46DD,2)]
    leaf_rows=rows('factory_leaf_irq_cycle_bounds.csv')
    sci_upper=int(next(r['including_IRQ_entry12_E'] for r in leaf_rows if r['contract']=='normal_session_copy_le11'))
    oc1_upper=int(next(r['including_IRQ_entry12_E'] for r in leaf_rows if r['entry']=='CE7C'))
    masked_upper=max(int(r['nominal_upper_E']) for r in rows('factory_masked_intervals.csv') if r['scope']=='ordinary_resident')
    normal_budget=masked_upper+12+busy_with_guards+8*sci_upper+8*(ref_upper+12)+(8+2)*oc1_upper
    foreground_sp=ins[0x7100].value;lower_tsx=ins[0x796C].value
    owners_max=(foreground_sp+1-lower_tsx)//9
    current_peak=int(next(r['peak_bytes_below_entry_SP'] for r in rows('factory_stack_contracts.csv') if r['entry']=='793D'))
    leaf_peak=max(int(r['frame_plus_resident_bytes']) for r in rows('factory_interrupt_admission.csv') if r['entry']!='793D')
    stack_upper=owners_max*9+current_peak+leaf_peak+9+2
    meta={'rom_sha256':EXPECTED_SHA256,'ordinary_vectors':15,'stock_live_vectors':['FFD6','FFE4','FFE8','FFF2'],
          'stock_REF_gates':{f'{p:04X}':f'{t:04X}' for p,t in STOCK_REF_GATES.items()},
          'stock_REF_upper_own_E':ref_upper,'stock_REF_instruction_sites':len(seen),
          'disabled_OC45_enable_sites':['77DF','780F'],'tracked_register_writers':{f'{a:04X}':s.split(';') for a,s in expected.items()},
          'busy_pending_writers':flag_writers,
          'local_cyclic_components':len(cyclic),'procedure_envelopes':len(envelope_rows),
          'SCI_E_per_bit':256,'SCI_8N1_E_per_character':2560,
          'SCI_clean_character_credits':{'initial_pending_and_pipeline':2,'window13104_character_completions_max':6,'IRQ_bound':8},
          'OC1_offset_counts_minmax':[min(offsets),max(offsets)],'OC1_events_in_short_window':'N_REF + 2; includes initial pending plus one preexisting compare; window<counter wrap',
          'fast_service_upper_E_from_tick_contract':fast_upper,
          'all_guard_prefix_to797D_upper_E':prefix_upper,'all_guard_to_busy_set_upper_E':to_busy_set,
          'all_guard_busy_route_upper_E':busy_with_guards,
          'conditional_deadline':{'window_E':PERIOD_E,'N_REF_max':8,'N_SCI_max':8,'N_OC1_max':10,
                                  'sum_E':normal_budget,'strict_extra_wait_limit_E':PERIOD_E-normal_budget,
                                  'REF_min_edge_spacing_sufficient_E':2184,'REF_carry_allowance':2},
          'guard_stack':{'foreground_SP':f'{foreground_sp:04X}','accepted_TSX_min':f'{lower_tsx:04X}','accepted_owner_frames_max':owners_max,
                         'next_entry_recovers':owners_max+1,'LDS_recovery':f'{ins[0x7977].value:04X}','tail_ancestor_resident_bytes':0,
                         'current_resident_peak_bytes':current_peak,'leaf_frame_plus_resident_max':leaf_peak,
                         'accepted_owner_plus_leaf_below_foreground_bytes':owners_max*9+current_peak+leaf_peak,
                         'rejected_entry_prefix_extra_bytes':9+2,
                         'conditional_peak_below_foreground_bytes':stack_upper,
                         'peak_low_SP':f'{foreground_sp-stack_upper:04X}','scope':'deadline/input envelope excludes recursive pre-guard timer entry; valid frames and no aliases; includes rejected ninth prefix before LDS; not extra usable RAM'},
          'COP':{'OPTION_hex':'B8','CR_bits':0,'divider_E':32768,'enable_from':'CONFIG.NOCOP plus operating-mode controls; not BIN padding',
                 'note':'prescaler phase gives nominal timeout uncertainty; watchdog reset is recovery not successful scheduling'},
          'boot_unmask':{'selected_cold_path_first_CLI':'C57F','selected_later_CLI':'D183',
                         'SCI_local_enable':'7154','first_OC3_arm':'7464','first_TMSK1_A0':'7469',
                         'note':'boot can unmask before first timer arm;7467 I1 suffix is conditional not inherited by every boot path'},
          'limits':['stock mode pruning is stronger than the general handler bounds',
                    'clean SCI bound requires nominal matched character clocks or an explicit N_SCI<=8 arrival contract; acknowledged flags; no overrun-only stale request',
                    'REF edge spacing is an input contract; electrical legality alone permits starvation',
                    'per-pass own bounds are conservative SCC sums and keep terminal/supplied-code boundaries',
                    'tail/catch-up count depends on arrivals; no universal main completion time',
                    'peripheral read/write equality borders and board waits remain external timing contracts']}
    return {FILES[0]:csv_text(sources),FILES[1]:csv_text(loop_rows),FILES[2]:csv_text(envelope_rows),FILES[3]:json.dumps(meta,indent=2,sort_keys=True)+'\n'}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--rom',type=Path);p.add_argument('--check-recorded',action='store_true');p.add_argument('--write',action='store_true')
    args=p.parse_args()
    if args.check_recorded:
        if args.rom or args.write:p.error('Recorded mode is separate from fresh-ROM/write mode')
        rom=recorded_rom(json.loads(EVIDENCE.read_text()))
    elif args.rom:rom=full_rom(args.rom)
    else:p.error('Supply --rom or --check-recorded')
    for name,content in build(rom).items():
        path=OUT/name
        if args.write:path.write_text(content)
        elif not path.exists() or path.read_text()!=content:raise SystemExit(f'Stale interrupt/timing closure: {path}')
    print('Factory interrupt sources and conditional timing closure verified')


if __name__=='__main__':main()
