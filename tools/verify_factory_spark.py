#!/usr/bin/env python3
"""Capture/check actual BMHM bytes for the bounded spark integer contracts."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path

from build_factory_scheduler import csv_text, full_rom, recorded_rom
from factory_structure import ROOT,SOURCE,text_sha256
from factory_rom_decode import decode
from factory_spark import HandoffInputs,spark_handoff
from verify_factory_rom_structure import EXPECTED_SHA256

OUT=ROOT/"maps/structure"
EVIDENCE=OUT/"bmhm_spark_rom_evidence.json"
RANGES=[
    ("ASIC_init_clear",0x7156,0x7164,True),
    ("RAM_init_clear_calls",0x7164,0x717F,True),
    ("reference_event_flag",0x750F,0x7516,True),
    ("spark_update_admission",0xA4EC,0xA5E5,True),
    ("period_basis_scale",0xA5E5,0xA5FE,True),
    ("period_basis_to_terms",0xA5FE,0xA687,True),
    ("adaptive_and_reference_terms",0xA687,0xA706,True),
    ("knock_saved_byte",0xAACB,0xAADC,True),
    ("spark_conversion_and_handoff",0xAB3E,0xABCB,True),
    ("latency_interpolator",0xF499,0xF4DE,True),
    ("multiply_helper",0xF550,0xF564,True),
    ("delay_RTS",0xF3ED,0xF3EE,True),
    ("RAM_clear_helper",0xF2FD,0xF326,True),
    ("startup_lag_helper",0xF459,0xF479,True),
    ("period_scale_calibration",0x4141,0x4142,False),
    ("latency_header_knots_and_neighbor",0x454A,0x4559,False),
    ("start_reference_period_threshold",0x4133,0x4135,False),
    ("start_reference_count_threshold",0x4142,0x4143,False),
    ("startup_filter_calibration",0x414E,0x414F,False),
    ("pump_timer_threshold",0x4962,0x4964,False),
    ("reference_count_seed",0x4D96,0x4D97,False),
]
ANCHORS={0xAB89:"37 36 30 4F 5F B3 3F C0",0xAB9C:"2B 04",0xABA0:"ED 00",
         0xABAA:"FD 3F E8",0xABBA:"FD 3F E6",0xABC0:"FF 3F DC",0xABC8:"FD 3F F6",
         0xA6DC:"86 78",0xA6D9:"FD 08 3F",0xA50A:"FD 01 EA"}


def build(rom):
    for pc,hex_bytes in ANCHORS.items():
        b=bytes.fromhex(hex_bytes)
        if rom.read(pc,len(b))!=b:raise ValueError(f"Spark anchor differs at {pc:04X}")
    instructions=[]
    for scope,start,end,is_code in RANGES:
        if not is_code:continue
        pc=start
        while pc<end:
            i=decode(rom.read,pc)
            if i.next_pc>end:raise ValueError(f"Spark instruction crosses range at {pc:04X}")
            instructions.append({"scope":scope,"pc":f"{pc:04X}","bytes_hex":i.data.hex(" ").upper(),"mnemonic":i.op,"operand":i.operand})
            pc=i.next_pc
    table=rom.read(0x454A,15)
    vectors=[]
    cases=[HandoffInputs(command=c,startup=s,startup_bypass=b,rpm=r,basis=p,anchor_period=p,
                         rolling1=f,work_read=66,correction1=79)
           for c,s,b,r,p,f in [(0,0,False,0,0,0),(0,0,False,0,1,0),(1,0,True,0,983,0),
                               (0xFFFF,0,True,80,983,0),(0xFF00,0xFFFF,False,255,491,0xFFFF),
                               (0x7FFF,0xFF80,False,192,0xFFFF,0x8000),
                               (0x8000,0x7FFF,False,191,0xFFFF,0x7FFF),
                               (57,0,True,40,983,0xF000)]]
    cases.extend(HandoffInputs(command=c,basis=p,anchor_period=p,rolling1=f,work_read=66,correction1=308)
                 for c in [0,1,0xFFFF,0xFF80] for p in [15,16,17,458,1638] for f in [0,0x8000])
    for n,inputs in enumerate(cases):
        result=spark_handoff(inputs,table)
        vectors.append({"case":n,"inputs_json":json.dumps(asdict(inputs),sort_keys=True),
                        "saved_input":f"{result['saved_input']:04X}","replacement":int(result["replacement"]),
                        **{f"word_{a:04X}":f"{v:04X}" for _,a,v in result["writes"]}})
    dependencies=[
        {"state":"005F","producer_pcs":"A5E8;A5FC;A5CF","consumer_pcs":"AB79:F550",
         "initialization":"716A clears 0036-00FF","role":"period multiply basis; 4141 low-product-byte scaling; FFFF at timeout"},
        {"state":"01EA","producer_pcs":"A50A;A6A4;A6B5","consumer_pcs":"A4FB;A503;A69C;A6A1;A6AD;A6B2;A6E9",
         "initialization":"7173 clears 0100-029C","role":"event decay then reference/load-dependent adaptive addend"},
        {"state":"083F","producer_pcs":"A6D9","consumer_pcs":"A6E6",
         "initialization":"717C clears 0800-08FF","role":"piecewise function of 01E8 reference word"},
        {"state":"01EC","producer_pcs":"A6EC;A6FD","consumer_pcs":"ABB3;ABB7",
         "initialization":"7173 clears 0100-029C","role":"wrapped sum of battery/reference/adaptive terms; unsigned limit"},
        {"state":"3FF6","producer_pcs":"ABC8;FB03;715B indexed clear","consumer_pcs":"AB97;ABA4",
         "initialization":"715B attempts zero on 3FC0-3FF8 even words","role":"rolling handoff word; two live reads are separate inputs"},
        {"state":"3FDC","producer_pcs":"ABC0;FAF7;715B indexed clear","consumer_pcs":"ABB0",
         "initialization":"715B attempts zero on 3FC0-3FF8 even words","role":"live readback then current 01EC handoff; hardware mutation not assumed absent"},
    ]
    evidence={"rom_name":"BMHM.BIN","rom_size_bytes":65536,"rom_sha256":EXPECTED_SHA256,
              "listing_sha256_lf":text_sha256(SOURCE),"instruction_rows":len(instructions),
              "code_scope":"A4FB decay; A687-A706 terms; AB3E-ABCB conversion; normal factory path with 0086 bit6 clear",
              "readback_scope":"separate samples at each ASIC/RAM read PC; coherent word values supplied; no physical timing claim",
              "physical_units":"unassigned_by_this_integer_proof",
              "byte_ranges":[{"purpose":scope,"start":f"{start:04X}","end_exclusive":f"{end:04X}","bytes_hex":rom.read(start,end-start).hex(" ").upper()} for scope,start,end,_ in RANGES]}
    stack_rows=[{"pc":f"{pc:04X}","access":access,"width_bits":width,"address_expression":address,
                 "saved_value":value,"proof":"ROM_bytes_and_CPU_replay;valid_working_RAM_stack;no_incoming_SP_assumption"}
                for pc,access,width,address,value in [(0xAAD4,"R",8,"SP_at_AACF","A_at_AACB >> 1"),
                    (0xAB9A,"R",16,"SP_at_AB89-1","saved signed product minus latency"),
                    (0xAB9E,"R",16,"SP_at_AB89-1","saved signed product minus latency"),
                    (0xABA0,"W",16,"SP_at_AB89-1","replacement candidate"),
                    (0xABA2,"R",16,"SP_at_AB89-1","chosen saved/replacement word")]]
    return {EVIDENCE.name:json.dumps(evidence,indent=2,sort_keys=True)+"\n",
            "factory_spark_rom_instructions.csv":csv_text(instructions),
            "factory_spark_handoff_vectors.csv":csv_text(vectors),
            "factory_spark_dependencies.csv":csv_text(dependencies),
            "factory_spark_stack_accesses.csv":csv_text(stack_rows)}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom",type=Path);parser.add_argument("--write",action="store_true");parser.add_argument("--check-recorded",action="store_true")
    args=parser.parse_args()
    if args.check_recorded:
        if args.rom or args.write:parser.error("Recorded and full-image modes are separate")
        rom=recorded_rom(json.loads(EVIDENCE.read_text()))
    elif args.rom:rom=full_rom(args.rom)
    else:parser.error("Supply --rom or --check-recorded")
    for name,content in build(rom).items():
        path=OUT/name
        if args.write:path.write_text(content,encoding="utf-8")
        elif not path.exists() or path.read_text()!=content:raise ValueError(f"Spark evidence differs: {name}")
    print("PASS: spark instruction/vectors/dependencies; "+("recorded excerpt consistency" if args.check_recorded else "complete BMHM identity and scoped ROM bytes verified"))


if __name__=="__main__":main()
