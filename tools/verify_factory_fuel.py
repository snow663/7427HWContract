#!/usr/bin/env python3
"""Capture/check actual BMHM fuel-stage bytes and reproducible review vectors."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from build_factory_scheduler import csv_text,full_rom,recorded_rom
from factory_structure import ROOT,SOURCE,text_sha256
from factory_rom_decode import decode
from factory_fuel import FuelModel
from verify_factory_rom_structure import EXPECTED_SHA256

OUT=ROOT/"maps/structure"
EVIDENCE=OUT/"bmhm_fuel_rom_evidence.json"
RANGES=[("ASIC_and_RAM_initialization",0x7156,0x717F,True),
        ("running_fuel_and_delivery",0x7FD8,0x852C,True),
        ("asynchronous_output_helper",0x8548,0x858B,True),
        ("INT_proportional_combination",0x88E9,0x891E,True),
        ("injector_offset_lookup",0xE2FB,0xE306,True),
        ("interpolation_helpers",0xF499,0xF550,True),
        ("rounded_multiply",0xF550,0xF564,True),
        ("RAM_clear_helper",0xF2FD,0xF326,True),
        ("RTS_between_device_accesses",0xF3ED,0xF3EE,True),
        # Includes actual neighboring data reached by all raw byte lookup inputs.
        ("calibration_and_lookup_neighbors",0x4000,0x5200,False)]
ANCHORS={0x7FD8:"FC 02 57 FE 02 36 03",0x8002:"32 4D 32 26 03",0x8027:"32 4D 32 27 03",
         0x80EE:"36 FC 02 4E 05",0x8380:"4F F6 02 6F 2B 0A",0x8424:"4F 5F FD 3F CE",
         0x84FA:"FB 02 56 89 00",0x8512:"FD 3F CE",0x8571:"FD 3F F2"}


def defaults():
    return {"bytes":{"0248":128,"024A":145,"0231":180,"01D9":20,"01C0":70,
                     "01C6":100,"01CC":128,"0055":128,"0256":4,"0050":128},
            "words":{"0257":0x2F00,"0236":0xB000,"01E8":2000,"3FC0":2000,"005F":2000}}


def fixture(rom,inputs):
    memory=bytearray(65536)
    memory[0x4000:0x5200]=rom.read(0x4000,0x1200)
    return seed_memory(memory,inputs)


def seed_memory(memory,inputs):
    for a,value in inputs.get("bytes",{}).items():memory[int(a,16)]=value
    for a,value in inputs.get("words",{}).items():
        a=int(a,16);memory[a:a+2]=value.to_bytes(2,"big")
    for a,value in inputs.get("calibration",{}).items():memory[int(a,16)]=value
    return memory


def review_cases():
    result=[]
    cases=[("stock_running",{}),("lean_BLM",{"0248":100}),("PE_blocks_lean_BLM",{"0248":100,"003D":32}),
           ("additive_INT",{"026F":20}),("negative_INT",{"026F":236}),
           ("MAP_AE",{"023E":200}),("force_no_reference",{"0044":16}),
           ("TBI_async_no_packet",{"0050":0,"0231":10}),("TBI_async_with_packet",{"0050":0,"0231":10,"023A":1000})]
    for name,changes in cases:
        inputs=defaults()
        for a,value in changes.items():inputs["words" if a=="023A" else "bytes"][a]=value
        result.append((name,0x7FD8,inputs))
    for pulse in [0,1,31,32,33,34,255,256,32767,65535]:
        inputs=defaults();inputs["words"]["024E"]=pulse
        result.append((f"shape_{pulse}",0x84BC,inputs))
    return result


def build(rom):
    for pc,data in ANCHORS.items():
        data=bytes.fromhex(data)
        if rom.read(pc,len(data))!=data:raise ValueError(f"Fuel anchor differs at {pc:04X}")
    instructions=[];accesses=[]
    for scope,start,end,is_code in RANGES:
        if not is_code:continue
        pc=start
        while pc<end:
            ins=decode(rom.read,pc)
            if ins.next_pc>end:raise ValueError(f"Fuel instruction crosses range at {pc:04X}")
            row={"scope":scope,"pc":f"{pc:04X}","bytes_hex":ins.data.hex(' ').upper(),"mnemonic":ins.op,"operand":ins.operand}
            instructions.append(row)
            access=ins.access()
            if access:
                accesses.append({**row,"access":access["access"],"width_bits":access["width_bits"],
                                 "address":f"{access['address']:04X}" if access['address'] is not None else "","address_mode":ins.mode})
            pc=ins.next_pc
    vectors=[]
    for name,start,inputs in review_cases():
        model=FuelModel(fixture(rom,inputs)).run(start)
        hardware=[(f"{p:04X}",f"{a:04X}",f"{v:04X}",w) for p,a,v,w in model.writes if 0x3F00<=a<0x4000]
        vectors.append({"case":name,"start":f"{start:04X}","inputs_json":json.dumps(inputs,sort_keys=True),
                        "word_024E":f"{model.w(0x024E):04X}","word_024C":f"{model.w(0x024C):04X}",
                        "word_0250":f"{model.w(0x0250):04X}","hardware_writes_json":json.dumps(hardware),
                        "stage_path":";".join(model.stages)})
    dependencies=[
        {"state":"024E","width":16,"producers":"802F;8049;80E8;80F8;8102;833F;836C;837D;839C;83AB;83B7;83F6",
         "input_boundary":"0231 VE;0236 temperature;0257 density;024A AFR;1E8 period;4D92 flow;state gates and corrections",
         "initialization":"7173:F2FD clears 0100-029C","scope":"running arithmetic; upstream sensor/VE/AFR/AE producers separate"},
        {"state":"0254","width":16,"producers":"83AE","input_boundary":"PW after INT and MAP AE",
         "initialization":"7173:F2FD","scope":"snapshot before delivery arbitration"},
        {"state":"024C","width":16,"producers":"84C3;84F5","input_boundary":"unshaped async-route PW or shaped synchronous PW",
         "initialization":"7173:F2FD","scope":"meaning depends on current route"},
        {"state":"0250","width":16,"producers":"8508","input_boundary":"wrapped byte offset addition then 7FFF cap; no offset for zero",
         "initialization":"7173:F2FD","scope":"not updated on 84C3 async bypass"},
        {"state":"0256","width":8,"producers":"E303","input_boundary":"00A7 byte and4B05 lookup",
         "initialization":"7173:F2FD","scope":"isolated ROM/CPU-verified producer; caller cadence and physical scale separate"},
        {"state":"026F","width":8,"producers":"891A","input_boundary":"020F integrator;027A proportional;3E40 direction;400B08/4402 cap gates",
         "initialization":"7173:F2FD","scope":"bounded INT/P combination and saturating signed addition; not a second BLM multiplier"},
        {"state":"0259-025B","width":24,"producers":"845B;8464;846F;848E;84A3","input_boundary":"live 3FC0 sample; scaled PW; packet reservoir",
         "initialization":"7173:F2FD","scope":"24-bit accumulation; word clears preserve byte025B fraction"},
        {"state":"3FCE","width":16,"producers":"8426;8512","input_boundary":"async-route zero or final synchronous word",
         "initialization":"715B indexed ASIC zero attempts","scope":"software write values; physical delivered fuel not modeled"},
        {"state":"3FF2;3FFC","width":16,"producers":"8571;857F;8587","input_boundary":"packet;0256;live3FFC sample",
         "initialization":"715B covers3FF2;3FFC outside this clear","scope":"async packet word and clear/set0400 word trigger; device dynamics separate"},
    ]
    evidence={"rom_name":"BMHM.BIN","rom_size_bytes":65536,"rom_sha256":EXPECTED_SHA256,"listing_sha256_lf":text_sha256(SOURCE),
              "instruction_rows":len(instructions),"code_scope":"7FD8-852C running fuel plus8548-858B async helper; upstream inputs explicit",
              "memory_scope":"stable RAM/calibration snapshot; separate coherent ASIC samples; no interrupt interleavings",
              "division_scope":"invalid divide quotientFFFF defined; invalid remainder never relied upon by bounded formulas",
              "byte_ranges":[{"purpose":scope,"start":f"{start:04X}","end_exclusive":f"{end:04X}","bytes_hex":rom.read(start,end-start).hex(' ').upper()} for scope,start,end,_ in RANGES]}
    return {EVIDENCE.name:json.dumps(evidence,indent=2,sort_keys=True)+'\n',
            "factory_fuel_rom_instructions.csv":csv_text(instructions),"factory_fuel_memory_accesses.csv":csv_text(accesses),
            "factory_fuel_handoff_vectors.csv":csv_text(vectors),"factory_fuel_dependencies.csv":csv_text(dependencies)}


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
        elif not path.exists() or path.read_text()!=content:raise ValueError('Fuel output differs: '+name)
    print('PASS: fuel bytes, stage vectors and dependencies; '+('recorded consistency' if a.check_recorded else 'complete BMHM identity verified'))


if __name__=='__main__':main()
