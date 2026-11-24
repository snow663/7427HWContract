#!/usr/bin/env python3
"""Bind a native HC11 C reset/BSS initializer into an ASM11 safe ROM.

This composes ACTUAL ASM11 and compiled C SRecords with externally verified
listing offsets and ELF report. It refuses stale/unbound placeholders,
RAM range inconsistencies, overlapping fields, missing reset symbol and
vector changes. It is still simulation-only until the native ABI is proved.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from compose_hc11_rom import (
    ROM_FIRST, ImageError, compose, exact_symbol,
    _flatten, load_srec, stock_safe_vectors
)

SIGNATURE=0xc3
FIELDS={
    "isr_call_word":2,
    "boot_token":1,
    "boot_state_start_word":2,
    "boot_state_end_word":2,
    "boot_reset_call_word":2
}

def required_number(data,key):
    raw=data.get(key)
    if isinstance(raw,bool) or raw is None:
        raise ImageError("Missing verified listing/ELF field "+key)
    try:
        result=int(raw,0) if isinstance(raw,str) else int(raw)
    except (ValueError,TypeError) as error:
        raise ImageError("Bad numeric field "+key) from error
    if not 0<=result<=0xffff:
        raise ImageError("Field outside 16-bit machine space: "+key)
    return result

def compose_boot(asm_segments,c_segments,nm_text,elf_report,asm_fields):
    if asm_fields.get("schema")!="7427-asm11-native-c-boot-bind-v1" or \
       not asm_fields.get("authority"):
        raise ImageError("ASM11 link fields need explicit listing provenance")
    if elf_report.get("schema")!="7427-linked-c-image-inspection-v1" or \
       elf_report.get("native_architecture")!="MC68HC11" or \
       elf_report.get("flash_ready") is not False:
        raise ImageError("Linked native ELF report invalid or missing")
    asm=_flatten(asm_segments,"ASM11",allow_vectors=True)
    compiled=_flatten(c_segments,"native C",allow_vectors=False)
    offsets={name:required_number(asm_fields,name) for name in FIELDS}
    selected=set()
    for name,size in FIELDS.items():
        start=offsets[name]
        if not 0x4000<=start<=0xffbf-size+1:
            raise ImageError("ASM11 patch field outside pre-vector code: "+name)
        for a in range(start,start+size):
            if a in selected or a not in asm or a in compiled:
                raise ImageError("ASM11 patch overlaps missing/other data: "+name)
            selected.add(a)
    if asm[offsets["boot_token"]]!=0:
        raise ImageError("Native C bootstrap already activated or corrupted")
    for name in ("boot_state_start_word","boot_state_end_word"):
        a=offsets[name]
        if asm[a]!=0 or asm[a+1]!=0:
            raise ImageError("Native C BSS address word not zero/unbound: "+name)
    expected_reset=required_number(asm_fields,"expected_boot_reset_unbound")
    reset_word=offsets["boot_reset_call_word"]
    if ((asm[reset_word]<<8)|asm[reset_word+1])!=expected_reset:
        raise ImageError("Native reset call placeholder does not match ASM11 listing")
    if expected_reset==0:
        raise ImageError("Native reset unbound target must be real safe-trap stub")
    link_unbound=required_number(asm_fields,"expected_isr_unbound")
    source_isr=offsets["isr_call_word"]
    # compose() independently verifies ASM11/C overlap, all 32 safe vectors
    # and exact old ISR callword before patching a validated native symbol.
    image,report=compose(asm_segments,c_segments,nm_text,
        symbol="pcm_hc11_c_entry",
        link_address=source_isr,expected_unbound=link_unbound)

    c_entry=exact_symbol(nm_text,"pcm_hc11_c_entry")
    reset_entry=exact_symbol(nm_text,"pcm_hc11_c_entry_reset")
    if c_entry!=required_number(elf_report,"linked_entry") or \
       reset_entry!=required_number(elf_report,"linked_reset_entry"):
        raise ImageError("ELF report/native nm entry address disagreement")
    if reset_entry not in compiled or reset_entry==c_entry:
        raise ImageError("C reset code missing or aliasing ISR entry")
    state_first=required_number(elf_report,"state_first")
    state_end=required_number(elf_report,"state_end_exclusive")
    state_bytes=required_number(elf_report,"state_bytes")
    state_capacity=required_number(elf_report,"state_capacity")
    if state_end<=state_first or state_end-state_first!=state_bytes or \
       state_bytes>state_capacity:
        raise ImageError("Native C BSS/softregs allocation is not internally consistent")
    if state_first<0x0800 and state_end>0x03b0:
        if state_first<0x0400:
            raise ImageError("Native C state overlaps interrupt stack")
    if state_first<0x1000 and state_end>0x0e00:
        raise ImageError("Native C state overlaps EEPROM area")
    if not elf_report.get("source_authority"):
        raise ImageError("Native RAM placement lacks provenance")
    # Forbid compiler allocations in CPU register and board I/O space.
    if state_end>0x2000:
        raise ImageError("Native C state outside source-visible RAM space")

    target=bytearray(image)
    def patch_word(address,value):
        idx=address-ROM_FIRST
        target[idx]=(value>>8)&255
        target[idx+1]=value&255
    patch_word(offsets["boot_state_start_word"],state_first)
    patch_word(offsets["boot_state_end_word"],state_end)
    patch_word(reset_word,reset_entry)
    target[offsets["boot_token"]-ROM_FIRST]=SIGNATURE
    # The earlier compose stage had already preserved original safe vectors.
    for a in range(0xffc0,0x10000):
        if target[a-ROM_FIRST]!=image[a-ROM_FIRST]:
            raise ImageError("Native reset binding modified a vector")
    report.update({
        "sha256":hashlib.sha256(target).hexdigest(),
        "native_c_startup":"boot token C3, checked state-zero and C reset target",
        "native_c_state_start":f"{state_first:04X}",
        "native_c_state_end_exclusive":f"{state_end:04X}",
        "native_c_reset_entry":f"{reset_entry:04X}",
        "asm11_boot_fields_authority":asm_fields["authority"],
        "patched_linkword_bytes":report["patched_linkword_bytes"]+7,
        "flash_ready":False,
        "native_stack_call_ABI":"not tested on target"
    })
    return bytes(target),report

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ("asm-s19","native-c-s19","native-symbols",
                 "native-elf-report","asm11-bindings","out-bin","out-report"):
        p.add_argument("--"+name,type=Path,required=True)
    a=p.parse_args()
    image,report=compose_boot(
        load_srec(a.asm_s19),load_srec(a.native_c_s19),
        a.native_symbols.read_text(encoding="utf-8"),
        json.loads(a.native_elf_report.read_text(encoding="utf-8")),
        json.loads(a.asm11_bindings.read_text(encoding="utf-8")))
    a.out_bin.parent.mkdir(parents=True,exist_ok=True)
    a.out_report.parent.mkdir(parents=True,exist_ok=True)
    a.out_bin.write_bytes(image)
    a.out_report.write_text(json.dumps(report,indent=2)+"\n",
                            encoding="utf-8")
    print(f"Composed CPU $4000+ image SHA256 {report['sha256']}")
    print("C BSS clear/reset linked for simulator; target ABI still unverified.")

if __name__=="__main__":
    main()
