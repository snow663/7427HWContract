#!/usr/bin/env python3
"""Probe native MC68HC11 compiler ABI and optional pseudo-source build.

This must execute with REAL 68HC11 cross tools. Native PC gcc output is
explicitly rejected, even if the compiler accepts the C program.
No linkable image is claimed until ROM, RAM, symbol and stack sections
have been independently checked.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[1]

PROBE_SOURCE=r'''#include "hc11_irq_mailbox.h"
#include <limits.h>
typedef char require_8_bit_char[(CHAR_BIT==8)?1:-1];
typedef char require_16_bit_ptr[(sizeof(void*)==2)?1:-1];
typedef char require_16_bit_int[(sizeof(unsigned)==2)?1:-1];
typedef char require_16_bit_u16[(sizeof(uint16_t)==2)?1:-1];
typedef char require_mailbox_8[(PCM_IRQ_MB_SIZE==8)?1:-1];
const uint16_t pcm_hc11_native_sizeof_pcm = (uint16_t)sizeof(Pcm);
const uint16_t pcm_hc11_native_sizeof_platform = (uint16_t)sizeof(PcmPlatform);
const uint16_t pcm_hc11_native_sizeof_calibration = (uint16_t)sizeof(PcmCalibration);
'''

BASE_FLAGS=[
    "-m6811", "-mshort", "-Os", "-std=gnu99", "-ffreestanding",
    "-fno-builtin", "-fno-optimize-sibling-calls",
    "-I", str(ROOT/"include")
]

def resolve_command(value):
    argv=shlex.split(value)
    if not argv or shutil.which(argv[0]) is None:
        raise RuntimeError("Required HC11 cross tool not found: "+value)
    return argv

def run(argv, *, cwd=None):
    result=subprocess.run(argv,cwd=cwd,capture_output=True,text=True)
    if result.returncode!=0:
        raise RuntimeError("Command failed: "+shlex.join(map(str,argv))+
                           "\n"+result.stdout+"\n"+result.stderr)
    return result.stdout

def probe(cc, nm, objdump, output: Path, *, all_sources: bool):
    output.mkdir(parents=True,exist_ok=True)
    source=output/"target_abi_probe.c"
    source.write_text(PROBE_SOURCE,encoding="utf-8")
    compiler=resolve_command(cc)
    symboler=resolve_command(nm)
    disassembler=resolve_command(objdump)
    flags=[*compiler,*BASE_FLAGS]
    objects={}
    targets=[
        ("abi",source),
        ("entry",ROOT/"platform/hc11_c_entry.c"),
        ("mailbox",ROOT/"platform/hc11_irq_mailbox.c"),
        ("vector",ROOT/"platform/hc11_vector_contract.c"),
    ]
    if all_sources:
        targets += [("src_"+p.relative_to(ROOT).as_posix().replace("/","_").replace(".c",""),p)
                    for p in sorted((ROOT/"src").rglob("*.c"))]
        targets += [("cal_"+p.stem,p)
                    for p in sorted((ROOT/"calibration").glob("*.c"))]
        # All other platform fragments are separate from indexed routine count.
        targets += [("platform_"+p.stem,p)
                    for p in sorted((ROOT/"platform").glob("*.c"))
                    if p.name not in {"hc11_c_entry.c","hc11_irq_mailbox.c",
                                      "hc11_vector_contract.c"}]
    for name,path in targets:
        obj=output/(name+".o")
        run([*flags,"-c",str(path),"-o",str(obj)])
        fmt=run([*disassembler,"-f",str(obj)])
        if "m68hc11" not in fmt.lower() or "m68hc12" in fmt.lower():
            raise RuntimeError(f"{name}: output is not an MC68HC11 object:\n{fmt}")
        objects[name]=hashlib.sha256(obj.read_bytes()).hexdigest()
    native_symbols=run([*symboler,"-g",str(output/"entry.o")])
    matching=[line for line in native_symbols.splitlines()
              if line.split() and line.split()[-1]=="pcm_hc11_c_entry"]
    if len(matching)!=1:
        raise RuntimeError("Actual native C entry symbol is absent or ambiguous; "
                           "check compiler name-decoration/ABI")
    entry_listing=run([*disassembler,"-d",str(output/"entry.o")])
    # The unlinked object address is not the final ROM address.
    report={
      "cpu":"MC68HC11", "mode":"m6811 -mshort",
      "linked":False, "native_rom_generated":False,
      "native_entry_symbol":"pcm_hc11_c_entry",
      "entry_object_nm_line":matching[0].strip(),
      "compiler":compiler,
      "objects_sha256":objects,
      "sizeof_probe_object":str(output/"abi.o"),
      "sizeof_values":"inspect native object; host sizeof is not target sizeof",
      "entry_disassembly":str(output/"entry_disassembly.txt"),
      "pending":["native link map","RAM/stack section placement","verified ASM11 JSR/RTS",
                 "fully placed code/calibration and native image","cycle bounds"]
    }
    (output/"entry_disassembly.txt").write_text(entry_listing,encoding="utf-8")
    (output/"native_abi_probe.json").write_text(json.dumps(report,indent=2)+"\n")
    return report

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cc",default=os.environ.get("HC11_CC","m6811-elf-gcc"))
    parser.add_argument("--nm",default=os.environ.get("HC11_NM","m6811-elf-nm"))
    parser.add_argument("--objdump",default=os.environ.get("HC11_OBJDUMP","m6811-elf-objdump"))
    parser.add_argument("--out",type=Path)
    parser.add_argument("--all-sources",action="store_true",
                        help="Compile all resident C sources, beyond the native ABI sample")
    args=parser.parse_args()
    if args.out is None:
        with tempfile.TemporaryDirectory(prefix="7427-hc11-") as tmp:
            report=probe(args.cc,args.nm,args.objdump,Path(tmp),
                         all_sources=args.all_sources)
            print(f"Native HC11 object ABI passed, {len(report['objects_sha256'])} objects")
            print("No native image linked. Supply --out to preserve objects and nm/ABI evidence.")
    else:
        report=probe(args.cc,args.nm,args.objdump,args.out,
                     all_sources=args.all_sources)
        print(f"Native HC11 object ABI passed, {len(report['objects_sha256'])} objects")
        print("Objects written to:",args.out)

if __name__=="__main__":
    main()
