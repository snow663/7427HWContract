#!/usr/bin/env python3
"""Link the real MC68HC11 C pseudo-source after source-approved placement.

Requires an actual m6811 cross compiler, nm/objdump/objcopy, measured
ASM11 ROM/RAM ends and explicitly audited free C scratch RAM. Its output
is native C machine code for simulation, NOT an engine-running ROM.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
from hc11_layout import Placement, linker_script, manifest, parse_number
from verify_hc11_toolchain import probe,resolve_command,run
from verify_native_elf import validate
from compose_hc11_rom import load_srec
from native_artifact_binding import artifact_binding

def compile_and_link(args):
    plan=Placement(args.asm_code_end,args.asm_ram_end,
                   args.c_ram_first,args.c_ram_last,args.authority).check()
    out=args.out.resolve()
    out.mkdir(parents=True,exist_ok=True)
    script=out/"hc11_c.ld"
    script.write_text(linker_script(plan),encoding="utf-8")
    (out/"hc11_layout.json").write_text(
        json.dumps(manifest(plan),indent=2)+"\n",encoding="utf-8")

    compiler=resolve_command(args.cc)
    nm=resolve_command(args.nm)
    objdump=resolve_command(args.objdump)
    objcopy=resolve_command(args.objcopy)
    object_dir=out/"objects"
    result=probe(args.cc,args.nm,args.objdump,object_dir,all_sources=True)
    objects=sorted(object_dir.glob("*.o"))
    if len(objects)!=len(result["objects_sha256"]):
        raise RuntimeError("Native object inventory is incomplete")
    elf=out/"pseudo_source_native.elf"
    mapfile=out/"pseudo_source_native.map"
    link=[
        *compiler,"-m6811","-mshort","-Os","-ffreestanding",
        "-nostartfiles","-nostdlib",
        "-Wl,-m,m68hc11elfb",
        "-Wl,-T,"+str(script),
        "-Wl,-Map,"+str(mapfile),
        "-o",str(elf),*[str(p) for p in objects],"-lgcc"
    ]
    # Errors include unresolved symbols, unsupported target ABI and
    # real code/RAM overflow; no synthetic machine code is substituted.
    run(link)
    machine=run([*objdump,"-f",str(elf)])
    sections=run([*objdump,"-h",str(elf)])
    symbols=run([*nm,"-g",str(elf)])
    (out/"native_objdump_file.txt").write_text(machine)
    (out/"native_sections.txt").write_text(sections)
    (out/"native_symbols.nm").write_text(symbols)
    evidence=validate(plan,machine,sections,symbols)
    evidence["linked_elf_sha256"]=hashlib.sha256(elf.read_bytes()).hexdigest()
    # Never copy ELF RAM or synthetic padding into the C S19.
    s19=out/"pseudo_source_native_code.s19"
    run([*objcopy,"--only-section=.c_code","-O","srec",
         str(elf),str(s19)])
    evidence["artifact_binding"]=artifact_binding(load_srec(s19),symbols,evidence)
    (out/"native_link_inspection.json").write_text(
        json.dumps(evidence,indent=2)+"\n",encoding="utf-8")
    print("Real MC68HC11 C ELF linked; code/state memory budgets accepted")
    print(f"Code {evidence['code_bytes']}/{evidence['code_capacity']}; "
          f"state+softregs {evidence['state_bytes']}/{evidence['state_capacity']}")
    print(f"Entry {evidence['linked_entry']} C S19 {s19}")
    print("Native BSS startup and ASM11 JSR/RTS are still unverified.")
    return evidence

def parser():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out",required=True,type=Path)
    for name in ("asm-code-end","asm-ram-end","c-ram-first","c-ram-last"):
        p.add_argument("--"+name,required=True,type=parse_number)
    p.add_argument("--authority",required=True)
    p.add_argument("--cc",default=os.environ.get("HC11_CC","m6811-elf-gcc"))
    p.add_argument("--nm",default=os.environ.get("HC11_NM","m6811-elf-nm"))
    p.add_argument("--objdump",default=os.environ.get("HC11_OBJDUMP","m6811-elf-objdump"))
    p.add_argument("--objcopy",default=os.environ.get("HC11_OBJCOPY","m6811-elf-objcopy"))
    return p

def main():
    compile_and_link(parser().parse_args())

if __name__=="__main__":
    main()
