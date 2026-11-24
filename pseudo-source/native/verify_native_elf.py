#!/usr/bin/env python3
"""Verify a linked MC68HC11 ELF against source-approved ROM/RAM bounds.

Read actual objdump -f/-h and linked nm, not host pointer/sizeof values.
No board internals are assumed. Unexpected allocated sections, executable
RAM, reserved stack, initialized C data, unbound entry => hard failure.
"""
from __future__ import annotations
from dataclasses import dataclass
import argparse
import json
import re
from pathlib import Path
from hc11_layout import Placement, PlacementError

class NativeImageError(ValueError):
    pass

@dataclass(frozen=True)
class Section:
    name: str
    size: int
    vma: int
    lma: int
    flags: frozenset[str]

HEADER=re.compile(r"^\s*\d+\s+(\S+)\s+([0-9a-fA-F]+)\s+"
                  r"([0-9a-fA-F]+)\s+([0-9a-fA-F]+)\s+"
                  r"([0-9a-fA-F]+)\s+(\S+)\s*$")
NM=re.compile(r"^\s*([0-9a-fA-F]{4,8})\s+[A-Za-z]\s+(\S+)\s*$")

def sections_from_objdump(listing: str) -> list[Section]:
    lines=listing.splitlines()
    out=[]
    for i,line in enumerate(lines):
        m=HEADER.match(line)
        if m is None:
            continue
        name,size,vma,lma,offset,align=m.groups()
        del offset,align
        flags=set()
        if i+1<len(lines):
            flags={t.strip() for t in lines[i+1].split(",") if t.strip()}
        out.append(Section(name,int(size,16),int(vma,16),
                           int(lma,16),frozenset(flags)))
    if not out:
        raise NativeImageError("No object sections found in native ELF")
    return out

def check_architecture(header: str):
    # ELF32 may target HC12 instead. Explicitly verify target architecture.
    lowered=header.lower()
    if not re.search(r"file format elf32-m68hc11\b",lowered) or \
       not re.search(r"architecture:\s*m68hc11\b",lowered):
        raise NativeImageError("ELF architecture must be MC68HC11, not HC12/host")

def exact_native_entry(nm_listing: str, symbol: str) -> int:
    matches=[]
    for line in nm_listing.splitlines():
        m=NM.fullmatch(line)
        if m and m.group(2)==symbol:
            matches.append(int(m.group(1),16))
    if len(matches)!=1:
        raise NativeImageError(f"Expected precisely one linked C entry symbol {symbol}")
    return matches[0]

def validate(plan: Placement, arch: str, headers: str, symbols: str):
    plan.check()
    check_architecture(arch)
    sections=sections_from_objdump(headers)
    allowed={".c_code",".c_state",".c_data",".c_initarray"}
    active=[]
    for s in sections:
        if s.size==0:
            continue
        if "ALLOC" not in s.flags:
            continue
        if s.name not in allowed:
            raise NativeImageError(f"Unplanned allocated ELF section {s.name}")
        active.append(s)
    code=[s for s in active if s.name==".c_code"]
    if len(code)!=1:
        raise NativeImageError("Exactly one nonempty .c_code section required")
    code=code[0]
    if not plan.code_start<=code.vma<=plan.rom_end:
        raise NativeImageError("Native C code starts outside approved ROM")
    if code.vma+code.size-1>plan.rom_end or code.lma!=code.vma:
        raise NativeImageError("Native C code overlaps vectors / incorrect load address")
    if "CODE" not in code.flags or "READONLY" not in code.flags:
        raise NativeImageError("Native C code must be read-only executable")
    for s in active:
        if s.name in (".c_data",".c_initarray"):
            raise NativeImageError(f"{s.name} needs native startup initialization")
        if s.name==".c_state":
            if not plan.c_ram_first<=s.vma<=plan.c_ram_last:
                raise NativeImageError("Native C state outside approved RAM")
            if s.vma+s.size-1>plan.c_ram_last:
                raise NativeImageError("Native C RAM exceeds free interval")
            if "CODE" in s.flags:
                raise NativeImageError("Native C state unexpectedly executable")
            if "CONTENTS" in s.flags or "LOAD" in s.flags:
                raise NativeImageError("Native C BSS/softregs must be NOLOAD and cleared on reset")
    entry=exact_native_entry(symbols,"pcm_hc11_c_entry")
    if not code.vma<=entry<code.vma+code.size:
        raise NativeImageError("Linked C entry is not in native code section")
    reset_entry=exact_native_entry(symbols,"pcm_hc11_c_entry_reset")
    if not code.vma<=reset_entry<code.vma+code.size or reset_entry==entry:
        raise NativeImageError("Native C reset routine must occupy a distinct code address")
    c_state=next((s for s in active if s.name==".c_state"),None)
    return {
        "schema":"7427-linked-c-image-inspection-v1",
        "native_architecture":"MC68HC11",
        "linked_entry":f"0x{entry:04X}",
        "linked_reset_entry":f"0x{reset_entry:04X}",
        "code_first":f"0x{code.vma:04X}",
        "code_end_exclusive":f"0x{code.vma+code.size:04X}",
        "code_bytes":code.size,
        "code_capacity":plan.rom_end-plan.code_start+1,
        "state_first":f"0x{c_state.vma:04X}" if c_state else None,
        "state_end_exclusive":f"0x{c_state.vma+c_state.size:04X}" if c_state else None,
        "state_bytes":c_state.size if c_state else 0,
        "state_capacity":plan.ram_length,
        "source_authority":plan.authority,
        "bss_reset_initializer_verified":False,
        "asm11_call_abi_verified":False,
        "flash_ready":False
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for a in ("objdump-file-header","objdump-sections","nm","layout-manifest","out-report"):
        p.add_argument("--"+a,type=Path,required=True)
    a=p.parse_args()
    m=json.loads(a.layout_manifest.read_text())
    plan=Placement(
        asm_code_end=int(m["asm_code_end"],0),
        asm_ram_end=int(m["asm_ram_end"],0),
        c_ram_first=int(m["c_ram_first"],0),
        c_ram_last=int(m["c_ram_last"],0),
        authority=m["authority"])
    report=validate(plan,
                    a.objdump_file_header.read_text(),
                    a.objdump_sections.read_text(),
                    a.nm.read_text())
    a.out_report.parent.mkdir(parents=True,exist_ok=True)
    a.out_report.write_text(json.dumps(report,indent=2)+"\n")
    print(f"Native C .c_code: {report['code_bytes']} bytes; "
          f".c_state: {report['state_bytes']} bytes, "
          "ROM/RAM address-space gates passed. CRT/ABI still open.")

if __name__=="__main__":
    main()
