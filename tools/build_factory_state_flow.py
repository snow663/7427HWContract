#!/usr/bin/env python3
"""Expand scheduler calls and propagate ROM-backed indexed memory effects.

--rom checks the complete stock image; --check-recorded uses committed excerpts
only. All effects are may-effects on normal-return paths. Opaque hooks, runtime
RAM pointers, branch feasibility, and address-set widening remain explicit.
"""
from __future__ import annotations

import argparse
from collections import Counter, deque
import csv
import io
import json
from pathlib import Path

import build_factory_scheduler as scheduler
from factory_structure import ROOT, SOURCE, load_regions, text_sha256
from factory_state_flow import (Effect, Ref, Value, add_constant, add_effect, analyze,
                                byte_part, stack_address, word, write_value)
from verify_factory_rom_structure import EXPECTED_SHA256

OUT = ROOT / "maps/structure"
EVIDENCE = OUT / "bmhm_nested_state_rom_evidence.json"
CLEAR_BYTES = bytes.fromhex("C5 07 27 0A 6F 00 08 83 00 01 26 F4 20 1A 04 04 04 17 C6 08 18 CE 00 00 1A EF 00 1A EF 02 1A EF 04 1A EF 06 3A 4A 26 F0 39")


def classification(value):
    ints = value.ints()
    if ints is not None:
        return "exact_address" if len(ints) == 1 else "bounded_address_set"
    if stack_address(value):
        return "stack_relative"
    if value.items is not None:
        return "caller_parameter"
    return "unresolved"


def target_bytes(effect):
    ints = effect.address.ints()
    return set() if ints is None else {(a+i)&0xFFFF for a in ints for i in range(effect.width//8)}


def clear_override(rom, state, destination, call_pc, effects):
    if destination != 0xF2FD:
        return False
    n, base = state.get("D").singleton(), state.get("X")
    if not isinstance(n,int) or not 1 <= n <= 512:
        return False
    if rom.read(0xF2FD,len(CLEAR_BYTES)) != CLEAR_BYTES:
        raise ValueError("RAM-clear helper contract does not match actual bytes")
    sp, start = state.get("SP").singleton(), base.singleton()
    if isinstance(sp,int) and isinstance(start,int) and any(((sp-i-start)&0xFFFF)<n for i in (0,1)):
        return False  # The clear would overwrite its own JSR return address.
    remainder, blocks = n%8, n//8
    if remainder:
        address=Value.of(16,[(x+i)&0xFFFF if isinstance(x,int) else Ref(x.name,(x.offset+i)&0xFFFF) for x in base.items or [] for i in range(remainder)]) if base.items is not None else Value(16)
        add_effect(effects,Effect(0xF301,"W",8,address,(call_pc,)))
        write_value(state,address,Value.const(8,0))
    if blocks:
        for pc,offset in [(0xF315,0),(0xF318,2),(0xF31B,4),(0xF31E,6)]:
            addresses=Value.of(16,[(x+remainder+8*i+offset)&0xFFFF if isinstance(x,int) else Ref(x.name,(x.offset+remainder+8*i+offset)&0xFFFF) for x in base.items or [] for i in range(blocks)]) if base.items is not None else Value(16)
            add_effect(effects,Effect(pc,"W",16,addresses,(call_pc,)))
            write_value(state,addresses,Value.const(16,0))
        state.put("Y",Value.const(16,0))
    state.put("X",add_constant(base,n))
    state.put("D",Value.const(16,8 if blocks else 0))
    state.carry,state.predicate=Value.const(1,0),None
    return True


def discover(rom):
    seed=json.loads(scheduler.EVIDENCE.read_text())
    if seed["rom_sha256"] != EXPECTED_SHA256:
        raise ValueError("Scheduler seed has a different ROM authority")
    table=[rom.word(0x7A85+2*i) for i in range(16)]
    roots=set(seed["callee_roots"]) | {0x7100,0x746C,0x793D,0xFA5B} | set(table)
    functions,frontiers,external={},[],set()
    pending=list(sorted(roots)); regions=load_regions()
    while pending:
        entry=pending.pop()
        if entry in functions:continue
        if not 0x7100<=entry<=0xFFFF:
            external.add(entry);continue
        instructions,open_edges=scheduler.walk_callee(rom,entry,regions)
        functions[entry]=instructions
        frontiers.extend((entry,pc,reason) for pc,reason in open_edges)
        pending.extend(i.target for i in instructions.values() if i.op in {"JSR","BSR"} and i.target is not None and i.target not in functions)
    graph={p:{i.target for i in ins.values() if i.op in {"JSR","BSR"} and i.target in functions} for p,ins in functions.items()}
    graph[0x793D].update(table)
    order=[];active=set();done=set()
    def visit(entry):
        if entry in active:raise ValueError("Recursive call component requires a separate widening review")
        if entry in done:return
        active.add(entry)
        for target in sorted(graph[entry]):visit(target)
        active.remove(entry);done.add(entry);order.append(entry)
    for entry in sorted(functions):visit(entry)
    return roots,table,functions,graph,order,frontiers,external


def fixed_loop_footprints(rom, summary):
    """Reviewed constant-counter loops; no X/Y independence assumption at joins."""
    descriptions={
        0xF326: {0xF32C:set(range(0x000B,0x0015))},
        0xF333: {0xF33A:set(range(0x000B,0x0014)),0xF33F:set(range(0x000B,0x0014)),
                 0xF341:set(range(0x0016,0x001F)),0xF346:set(range(0x0016,0x001F)),
                 0xF348:set(range(0x0056,0x005F)),0xF34D:set(range(0x0056,0x005F)),
                 0xF33C:set(range(0xF377,0xF380)),0xF343:set(range(0xF377,0xF380)),0xF34A:set(range(0xF377,0xF380))},
        0xF380: {0xF387:set(range(0x000B,0x0014)),0xF38C:set(range(0x000B,0x0014)),
                 0xF38E:set(range(0x0016,0x001F)),0xF393:set(range(0x0016,0x001F)),
                 0xF389:set(range(0xF3DB,0xF3E4)),0xF390:set(range(0xF3DB,0xF3E4))},
    }
    replacements=descriptions.get(summary.entry,{})
    if not replacements:return
    # Entry constants and counter exits are checked independently of HAC rows.
    anchors={0xF326:(0xF326,"CE 00 14 C6 0A 4F"),0xF333:(0xF333,"CE 00 09 18 CE F3 7F"),0xF380:(0xF380,"CE 00 09 18 CE F3 E3")}
    start,expected=anchors[summary.entry]
    if rom.read(start,len(bytes.fromhex(expected))) != bytes.fromhex(expected):raise ValueError("Constant-loop entry differs")
    exits={0xF326:(0xF32E,"09 5A 26 FA 39"),0xF333:(0xF34F,"18 09 09 26 E6"),0xF380:(0xF395,"18 09 09 26 ED")}
    start,expected=exits[summary.entry]
    if rom.read(start,len(bytes.fromhex(expected))) != bytes.fromhex(expected):raise ValueError("Constant-loop counter exit differs")
    for key,effect in list(summary.local.items()):
        if effect.pc in replacements:
            replacement=Effect(effect.pc,effect.access,effect.width,Value.of(16,replacements[effect.pc]),effect.via)
            summary.local[key]=replacement
            summary.effects[key]=replacement


def mask_rows(rom):
    rows=[]
    for entry,table,stores in [(0xF333,0xF376,[(0xF33F,10),(0xF346,21),(0xF34D,85)]),
                               (0xF380,0xF3DA,[(0xF38C,10),(0xF393,21)])]:
        for index in range(9,0,-1):
            mask=rom.read(table+index,1)[0]
            for pc,offset in stores:
                rows.append({"entry":f"{entry:04X}","store_pc":f"{pc:04X}","iteration":10-index,
                             "destination":f"{offset+index:04X}","mask_rom_address":f"{table+index:04X}",
                             "and_mask":f"{mask:02X}","cleared_bits":f"{(~mask)&255:02X}",
                             "effect":"destination = previous_destination AND mask",
                             "scope":"reviewed_9_iteration_loop;call_admission_conditional"})
    return rows


def witness_path(graph,root,target):
    pending=deque([(root,())]);seen=set()
    while pending:
        entry,path=pending.popleft()
        if entry==target:return ";".join(f"{p:04X}" for p in path+(entry,))
        if entry in seen:continue
        seen.add(entry);pending.extend((q,path+(entry,)) for q in sorted(graph.get(entry,())))
    return ""


def build(rom):
    roots,table,functions,graph,order,frontiers,external=discover(rom)
    summaries={}
    for entry in order:
        result=analyze(rom,entry,functions[entry],summaries,table,clear_override)
        fixed_loop_footprints(rom,result)
        summaries[entry]=result
    baseline={(int(r["scope"],16),int(r["pc"],16)) for r in csv.DictReader(io.StringIO((OUT/"factory_scheduler_callee_accesses.csv").read_text())) if not r["address"]}
    indexed,calls,effects,function_rows,clear_rows=[],[],[],[],[]
    baseline_counts=Counter(); all_instructions={p:i for ins in functions.values() for p,i in ins.items()}
    for entry,summary in sorted(summaries.items()):
        for effect in sorted(summary.local.values(),key=lambda e:e.pc):
            ins=functions[entry][effect.pc]
            if not ins.mode.startswith("indexed_"):continue
            kind=classification(effect.address)
            is_baseline=(entry,effect.pc) in baseline
            if is_baseline:baseline_counts[kind]+=1
            indexed.append({"entry":f"{entry:04X}","pc":f"{effect.pc:04X}","bytes_hex":ins.data.hex(" ").upper(),
                            "mnemonic":ins.op,"operand":ins.operand,"access":effect.access,"width_bits":effect.width,
                            "effective_addresses":effect.address.text(),"classification":kind,
                            "target_bytes":";".join(f"{a:04X}" for a in sorted(target_bytes(effect))),
                            "in_previous_262_rows":int(is_baseline),
                            "proof_limit":"may_addresses;ROM_and_frame_values_only;normal_return_paths;not_branch_coverage"})
        for pc,(targets,bindings) in sorted(summary.calls.items()):
            ins=functions[entry][pc]
            calls.append({"caller_entry":f"{entry:04X}","call_pc":f"{pc:04X}","bytes_hex":ins.data.hex(" ").upper(),
                          "destinations":targets.text(),"argument_X":bindings["X"].text(),"argument_Y":bindings["Y"].text(),
                          "argument_D":word(bindings["A"],bindings["B"]).text(),
                          "resolution":"mapped_ROM" if targets.ints() is not None and all(t in summaries for t in targets.ints()) else "opaque_or_runtime_pointer"})
            if ins.target==0xF2FD:
                n=word(bindings["A"],bindings["B"]).singleton();base=bindings["X"].singleton()
                if isinstance(n,int) and 1<=n<=512 and isinstance(base,int):
                    clear_rows.append({"caller_entry":f"{entry:04X}","call_pc":f"{pc:04X}","helper":"F2FD",
                                       "start":f"{base:04X}","byte_count":n,"end_exclusive":f"{base+n:05X}",
                                       "value_hex":"00","precondition":"1<=D<=512;normal_return;no_return_frame_overlap"})
        read_bytes,write_bytes=set(),set();open_effects=0
        for effect in sorted(summary.effects.values(),key=lambda e:(e.via,e.pc,e.access)):
            addresses=target_bytes(effect)
            if "R" in effect.access:read_bytes.update(addresses)
            if "W" in effect.access:write_bytes.update(addresses)
            if classification(effect.address) in {"unresolved","caller_parameter"}:open_effects+=1
            if not effect.via:continue
            effects.append({"entry":f"{entry:04X}","access_pc":f"{effect.pc:04X}","access":effect.access,"width_bits":effect.width,
                            "addresses":effect.address.text(),"classification":classification(effect.address),
                            "target_bytes":";".join(f"{a:04X}" for a in sorted(addresses)),
                            "call_witness":";".join(f"{p:04X}" for p in effect.via),
                            "scope_limit":"may_effect_union_per_first_call;witness_is_one_path;opaque_effects_separate"})
        function_rows.append({"entry":f"{entry:04X}","local_instruction_count":len(functions[entry]),
                              "normal_return_sites":summary.normal_returns,"dataflow_iterations":summary.iterations,
                              "return_A":summary.outputs["A"].text(),"return_B":summary.outputs["B"].text(),
                              "return_X":summary.outputs["X"].text(),"return_Y":summary.outputs["Y"].text(),
                              "return_SP":summary.outputs["SP"].text(),
                              "preserves_X_on_normal_return":int(summary.outputs["X"]==Value.param(16,"X")),
                              "preserves_Y_on_normal_return":int(summary.outputs["Y"]==Value.param(16,"Y")),
                              "known_read_bytes":";".join(f"{a:04X}" for a in sorted(read_bytes)),
                              "known_write_bytes":";".join(f"{a:04X}" for a in sorted(write_bytes)),
                              "open_effect_templates":open_effects,"opaque_call_sites":";".join(f"{p:04X}" for p in sorted(summary.opaque)),
                              "memory_scope":"known_may_effects_only;opaque_and_unknown_addresses_not_excluded"})
    accounted={(int(r["entry"],16),int(r["pc"],16)) for r in indexed if r["in_previous_262_rows"]}
    pruned=baseline-accounted
    baseline_counts["pruned_by_constant_flow"]=len(pruned)
    for entry,pc in sorted(pruned):
        indexed.append({"entry":f"{entry:04X}","pc":f"{pc:04X}","bytes_hex":functions[entry][pc].data.hex(" ").upper(),
                        "mnemonic":functions[entry][pc].op,"operand":functions[entry][pc].operand,
                        "access":functions[entry][pc].access()["access"],"width_bits":functions[entry][pc].access()["width_bits"],
                        "effective_addresses":"","classification":"pruned_by_constant_flow","target_bytes":"",
                        "in_previous_262_rows":1,"proof_limit":"abstract_entry_paths_pruned;not_whole_program_dead_code"})
    frontier_rows=[{"entry":f"{entry:04X}","pc":f"{pc:04X}","reason":reason,"target":""} for entry,pc,reason in frontiers]
    for entry,ins in sorted(functions.items()):
        for pc,i in sorted(ins.items()):
            if i.op in {"JSR","BSR"} and (i.target in external or i.target is None and pc!=0x7A4F):
                frontier_rows.append({"entry":f"{entry:04X}","pc":f"{pc:04X}","reason":"external_extension_hook" if i.target else "runtime_RAM_callback",
                                      "target":f"{i.target:04X}" if i.target else "wordRAM[038E]"})
    masks=mask_rows(rom)
    for row in masks:row["scheduler_call_witness"]=witness_path(graph,0x793D,int(row["entry"],16))
    malformed=all_instructions[0xA40B]
    control_corrections=[{"pc":"A40B","bytes_hex":malformed.data.hex(" ").upper(),
                          "rom_instruction":malformed.op+" "+malformed.operand,
                          "rom_target":f"{malformed.target:04X}","inherited_operand":"LA4656",
                          "status":"ROM_target_verified;original_listing_and_source_only_index_retained"}]
    outputs={
        "factory_nested_calls.csv":scheduler.csv_text(calls),
        "factory_indexed_flow.csv":scheduler.csv_text(sorted(indexed,key=lambda r:(r["entry"],r["pc"]))),
        "factory_nested_memory_effects.csv":scheduler.csv_text(effects),
        "factory_nested_state_summary.csv":scheduler.csv_text(function_rows),
        "factory_nested_frontiers.csv":scheduler.csv_text(frontier_rows),
        "factory_indexed_clear_calls.csv":scheduler.csv_text(clear_rows),
        "factory_masked_state_updates.csv":scheduler.csv_text(masks),
        "factory_nested_control_corrections.csv":scheduler.csv_text(control_corrections),
    }
    evidence={"rom_name":"BMHM.BIN","rom_size_bytes":65536,"rom_sha256":EXPECTED_SHA256,"listing_sha256_lf":text_sha256(SOURCE),
              "scope_roots":[f"{p:04X}" for p in sorted(roots)],"mapped_routine_entries":len(functions),
              "unique_decoded_instructions":len(all_instructions),"unique_indexed_instruction_sites":sum(i.access() is not None and i.access()["address"] is None for i in all_instructions.values()),
              "external_hook_targets":[f"{p:04X}" for p in sorted(external)],"baseline_indexed_rows":len(baseline),
              "baseline_resolution_counts":dict(sorted(baseline_counts.items())),"call_rows":len(calls),"nested_effect_rows":len(effects),
              "analysis_limit":"bounded_constant_and_affine_entry_register_flow;calls_on_normal_return;RAM_loads_unknown;opaque_calls_clobber_registers_and_memory;not_full_semantics_or_physical_execution",
              "byte_ranges":rom.ranges()}
    outputs[EVIDENCE.name]=json.dumps(evidence,indent=2,sort_keys=True)+"\n"
    return outputs


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom",type=Path);parser.add_argument("--write",action="store_true");parser.add_argument("--check-recorded",action="store_true")
    args=parser.parse_args()
    if args.check_recorded:
        if args.rom or args.write:parser.error("Recorded checking is separate from a complete-ROM check")
        rom=scheduler.recorded_rom(json.loads(EVIDENCE.read_text()))
    elif args.rom:rom=scheduler.full_rom(args.rom)
    else:parser.error("Supply --rom or --check-recorded")
    outputs=build(rom)
    for name,content in outputs.items():
        path=OUT/name
        if args.write:path.write_text(content,encoding="utf-8")
        elif not path.exists() or path.read_text()!=content:raise ValueError(f"Nested state-flow output differs: {name}")
    print(f"PASS: {len(outputs)} nested state-flow outputs; "+("recorded excerpt consistency only" if args.check_recorded else "full BMHM identity and scoped ROM bytes verified"))


if __name__=="__main__":main()
