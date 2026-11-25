#!/usr/bin/env python3
"""Strict S19 image composer for *compiled* HC11 C and ASM11 bootstrap.

Inputs are physical HC11 machine-code SRecords, not host C pseudo-source.
No compiler emulation and no guessed symbol address. Non-reset vector words
must target a common supplied entry, including after linkage. Entry presence
does not prove the behavior of a handler or the native calling convention.
"""
from __future__ import annotations
import argparse
from dataclasses import dataclass
import hashlib
import json
import re
from pathlib import Path

ROM_FIRST=0x4000
ROM_LAST=0xFFFF
CODE_LAST=0xFFBF
VECTOR_FIRST=0xFFC0
ACTIVE_VECTORS=range(0xFFD6,0x10000,2)

class ImageError(ValueError):
    pass

@dataclass(frozen=True)
class Segment:
    address: int
    data: bytes

def srecords(text: str) -> list[Segment]:
    segments=[]
    seen_terminal=False
    for number,raw in enumerate(text.splitlines(),1):
        line=raw.strip()
        if not line:
            continue
        if len(line)<4 or not line.startswith("S") or line[1] not in "012356789":
            raise ImageError(f"line {number}: unsupported Motorola record")
        try:
            octets=bytes.fromhex(line[2:])
        except ValueError as exc:
            raise ImageError(f"line {number}: malformed SRecord hex") from exc
        count=octets[0] if octets else -1
        if count!=len(octets)-1 or ((sum(octets)&255)!=255):
            raise ImageError(f"line {number}: count/checksum mismatch")
        kind=line[1]
        naddr={"0":2,"1":2,"2":3,"3":4,"5":2,"6":3,
               "7":4,"8":3,"9":2}[kind]
        if len(octets)<1+naddr+1:
            raise ImageError(f"line {number}: truncated address")
        if kind in "123":
            if seen_terminal:
                raise ImageError("data after S7/S8/S9 termination")
            address=int.from_bytes(octets[1:1+naddr],"big")
            data=octets[1+naddr:-1]
            if not data:
                raise ImageError(f"line {number}: empty data record")
            segments.append(Segment(address,data))
        elif kind in "789":
            seen_terminal=True
    if not segments:
        raise ImageError("No executable S1/S2/S3 data records")
    return segments

def load_srec(path: Path):
    return srecords(path.read_text(encoding="ascii"))

def _flatten(segments: list[Segment], label: str, *, allow_vectors: bool):
    image={}
    for seg in segments:
        for offset,value in enumerate(seg.data):
            a=seg.address+offset
            if a<ROM_FIRST or a>ROM_LAST:
                raise ImageError(f"{label}: data outside CPU ROM window at {a:#06x}")
            if not allow_vectors and a>=VECTOR_FIRST:
                raise ImageError(f"{label}: compiled C overlaps interrupt vectors {a:#06x}")
            if a in image:
                raise ImageError(f"{label}: overlapping SRecord data at {a:#06x}")
            image[a]=value
    return image

def _word(image: dict[int,int],address: int):
    if address not in image or address+1 not in image:
        raise ImageError(f"missing vector/link word at {address:#06x}")
    return image[address]*256+image[address+1]

def stock_safe_vectors(asm: dict[int,int]):
    for address in range(VECTOR_FIRST,0x10000):
        if address not in asm:
            raise ImageError(f"ASM11 vector data missing at {address:#06x}")
    trap=_word(asm,0xFFD6)
    reset=_word(asm,0xFFFE)
    if not ROM_FIRST<=trap<=CODE_LAST:
        raise ImageError("safe-trap target outside code region")
    if not ROM_FIRST<=reset<=CODE_LAST or reset==trap:
        raise ImageError("invalid reset vector")
    for name,target in (("reset",reset),("trap",trap)):
        if target not in asm:
            raise ImageError(f"{name} vector targets absent code at {target:#06x}")
    for address in range(VECTOR_FIRST,0xFFFE,2):
        if _word(asm,address)!=trap:
            raise ImageError(f"unapproved live/non-trap vector {address:#06x}")
    return trap,reset

NM_LINE=re.compile(r"^\s*([0-9a-fA-F]{4,8})\s+[A-Za-z]\s+(\S+)\s*$")

def exact_symbol(table: str, symbol: str) -> int:
    matches=[]
    for raw in table.splitlines():
        m=NM_LINE.fullmatch(raw)
        if m and m.group(2)==symbol:
            matches.append(int(m.group(1),16))
    if len(matches)!=1:
        raise ImageError(f"native symbol {symbol!r} must occur exactly once in nm export")
    value=matches[0]
    if not ROM_FIRST<=value<=CODE_LAST:
        raise ImageError(f"symbol {symbol} outside executable ROM")
    return value

def compose(asm_segments: list[Segment],c_segments: list[Segment],
            nm: str, *, symbol: str,
            link_address: int, expected_unbound: int):
    asm=_flatten(asm_segments,"ASM11",allow_vectors=True)
    compiled=_flatten(c_segments,"native C",allow_vectors=False)
    if not compiled:
        raise ImageError("Native C image empty")
    collisions=sorted(set(asm)&set(compiled))
    if collisions:
        raise ImageError(f"native C overwrites ASM11 at {collisions[0]:#06x}")
    trap,reset=stock_safe_vectors(asm)
    if not ROM_FIRST<=link_address<CODE_LAST:
        raise ImageError("unverified/invalid ASM11 entry-word address")
    if link_address not in asm or link_address+1 not in asm:
        raise ImageError("ASM11 link word not present in SRecord")
    if _word(asm,link_address)!=expected_unbound:
        raise ImageError("ASM11 default-unbound link word mismatch")
    c_entry=exact_symbol(nm,symbol)
    if c_entry not in compiled:
        raise ImageError("native C entry symbol does not point into supplied C code")
    if c_entry==trap or c_entry==reset:
        raise ImageError("C entry aliases reset/trap")
    image=asm.copy()
    image.update(compiled)
    image[link_address]=c_entry>>8
    image[link_address+1]=c_entry&255
    # Re-validate vectors after patch to prevent trampolines into active IRQ.
    final_trap,final_reset=stock_safe_vectors(image)
    if (final_trap,final_reset)!=(trap,reset):
        raise ImageError("vector targets changed during link")
    rom=bytearray([0xFF])*0xC000
    for addr,value in image.items():
        rom[addr-ROM_FIRST]=value
    report={
        "format":"7427-safe-rom-link-v1",
        "mapped_cpu_first":"4000",
        "mapped_cpu_last":"FFFF",
        "binary_size":len(rom),
        "sha256":hashlib.sha256(rom).hexdigest(),
        "reset_vector":f"{reset:04X}",
        "unowned_vector_trap":f"{trap:04X}",
        "asm_linkword_address":f"{link_address:04X}",
        "asm_previous_unbound_target":f"{expected_unbound:04X}",
        "resolved_c_entry":f"{c_entry:04X}",
        "resolved_c_symbol":symbol,
        "asm_bytes":len(asm),
        "native_c_bytes":len(compiled),
        "patched_linkword_bytes":2,
        "non_reset_vectors":"all target the common supplied trap entry",
        "vector_handler_behavior_verified":False,
        "native_compiler_call_ABI":"REQUIRES independent proof; nm address alone is insufficient",
        "flash_ready":False
    }
    return bytes(rom),report

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--asm-s19",type=Path,required=True)
    p.add_argument("--native-c-s19",type=Path,required=True)
    p.add_argument("--nm-symbols",type=Path,required=True)
    p.add_argument("--c-entry-symbol",default="pcm_hc11_c_entry")
    p.add_argument("--entry-word-addr",required=True,help="linker/ASM11 listing backed")
    p.add_argument("--expected-unbound",required=True,help="original ASM11 FDB value")
    p.add_argument("--out-bin",type=Path,required=True)
    p.add_argument("--out-report",type=Path,required=True)
    args=p.parse_args()
    rom,report=compose(load_srec(args.asm_s19),load_srec(args.native_c_s19),
        args.nm_symbols.read_text(encoding="utf-8"),
        symbol=args.c_entry_symbol,
        link_address=int(args.entry_word_addr,0),
        expected_unbound=int(args.expected_unbound,0))
    args.out_bin.parent.mkdir(parents=True,exist_ok=True)
    args.out_report.parent.mkdir(parents=True,exist_ok=True)
    args.out_bin.write_bytes(rom)
    args.out_report.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(f"Linked 48 KiB *simulation-only* 7427 image SHA256 {report['sha256']}")
    print("Non-reset vectors retain a common supplied entry; handler behavior and native ABI remain unverified.")

if __name__=="__main__":
    main()
