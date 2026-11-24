#!/usr/bin/env python3
"""Generate strict 68HC11 C code/state linker placement AFTER ASM11.

The caller supplies actual ASM11 ROM/RAM end symbols and a separately
approved free C RAM interval. We do not guess physical RAM backing or
reuse live stock shadow addresses. This generates a linker script, not a
finished ROM, and cannot approve a calibration/actuator image.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
import argparse
import json

class PlacementError(ValueError):
    pass

@dataclass(frozen=True)
class Placement:
    asm_code_end: int       # first byte AFTER assembled ASM11 code
    asm_ram_end: int        # first byte AFTER its allocated working RAM
    c_ram_first: int        # independently approved scratch RAM interval
    c_ram_last: int         # inclusive
    authority: str         # non-empty source of these exact addresses

    @property
    def code_start(self):
        return (self.asm_code_end+1)&~1

    @property
    def rom_end(self):
        return 0xffbf

    @property
    def ram_length(self):
        return self.c_ram_last-self.c_ram_first+1

    def check(self):
        if not isinstance(self.authority,str) or not self.authority.strip():
            raise PlacementError("Source authority/listing is required")
        if not 0x7100<=self.asm_code_end<=0xffbe:
            raise PlacementError("ASM11 code end outside executable $7100..$FFBE")
        if self.code_start>0xffbf:
            raise PlacementError("No native C code space below vectors")
        if not 0<=self.asm_ram_end<=0x2000:
            raise PlacementError("ASM11 RAM allocation end is invalid")
        lo,hi=self.c_ram_first,self.c_ram_last
        if lo>hi or not 0<=lo<=hi<0x2000:
            raise PlacementError("C scratch RAM interval outside memory contract")
        if lo < self.asm_ram_end:
            raise PlacementError("C RAM overlaps the ASM11-owned allocation")
        forbidden=((0x03b0,0x03ff,"native interrupt stack"),
                   (0x0e00,0x0fff,"conditional EEPROM"))
        for first,last,label in forbidden:
            if lo<=last and hi>=first:
                raise PlacementError(f"C RAM overlaps {label}")
        # RAM map can have shared/aliased addresses that are not FREE.
        # This script cannot certify a caller-provided interval as scratch.
        if self.ram_length<8:
            raise PlacementError("C scratch interval is too small to be useful")
        return self

def linker_script(plan: Placement) -> str:
    plan.check()
    return f"""/* Generated 7427 native C section placement.
 * Authority: {plan.authority.replace('*/','')}.
 * Real ELF/ASM11 listing and free-RAM audit are REQUIRED inputs.
 * ROM vectors, hardware registers and target stack are excluded.
 * NO initialized C data or C++ constructors permitted in this milestone.
 */
OUTPUT_FORMAT("elf32-m68hc11")
OUTPUT_ARCH(m68hc11)
ENTRY(pcm_hc11_c_entry)
MEMORY
{{
  C_ROM (rx) : ORIGIN = 0x{plan.code_start:04X},
               LENGTH = 0x{plan.rom_end-plan.code_start+1:X}
  C_RAM (rw) : ORIGIN = 0x{plan.c_ram_first:04X},
               LENGTH = 0x{plan.ram_length:X}
}}
SECTIONS
{{
  .c_code :
  {{
    __c_code_first = .;
    *(.text .text.* .gnu.linkonce.t.*)
    *(.rodata .rodata.* .gnu.linkonce.r.*)
    __c_code_end = .;
  }} > C_ROM

  .c_data :
  {{
    *(.data .data.* .sdata .sdata.* .gnu.linkonce.d.*)
  }} > C_RAM AT > C_ROM

  .c_initarray :
  {{
    *(.init_array .init_array.* .preinit_array.* .ctors .ctors.*)
  }} > C_ROM

  .c_state (NOLOAD) :
  {{
    __c_state_first = .;
    *(.softregs .softregs.*)
    *(.bss .bss.* .sbss .sbss.* .gnu.linkonce.b.*)
    *(COMMON)
    __c_state_end = .;
  }} > C_RAM

  /DISCARD/ : {{ *(.comment) *(.note*) *(.eh_frame*) *(.debug*) }}
  ASSERT(SIZEOF(.c_code)>0, "native C code cannot be empty")
  ASSERT(SIZEOF(.c_data)==0, "initialized C data needs a real reset-time copier")
  ASSERT(SIZEOF(.c_initarray)==0, "C constructors lack native CRT support")
  ASSERT(__c_code_end <= 0xFFC0, "native C overlaps 7427 vector window")
  ASSERT(__c_state_end <= ORIGIN(C_RAM)+LENGTH(C_RAM),
         "native C state/softregs exceeds approved scratch RAM")
}}
"""

def manifest(plan: Placement) -> dict:
    plan.check()
    return {
        "schema": "7427-hc11-c-section-placement-v1",
        "authority": plan.authority,
        "asm_code_end": f"0x{plan.asm_code_end:04X}",
        "asm_ram_end": f"0x{plan.asm_ram_end:04X}",
        "c_rom_first": f"0x{plan.code_start:04X}",
        "c_rom_last": "0xFFBF",
        "c_ram_first": f"0x{plan.c_ram_first:04X}",
        "c_ram_last": f"0x{plan.c_ram_last:04X}",
        "rom_capacity": plan.rom_end-plan.code_start+1,
        "ram_capacity": plan.ram_length,
        "initialized_data_policy": "forbidden_until_native_CRT_copy_verified",
        "asm_vector_policy": "unchanged_safe_trap",
        "approved_for_flash": False,
        "unverified": [
            "native compiler object and linker map",
            "C scratch RAM alias ownership at each allocated address",
            "C entry JSR/RTS stack and interrupt CCR",
            "native reset-time C BSS clear",
            "timer/WAI/STOP, full dispatcher and output authorization"
        ]
    }

def parse_number(raw: str) -> int:
    return int(raw,0)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ("asm-code-end","asm-ram-end","c-ram-first","c-ram-last"):
        p.add_argument("--"+name,required=True,type=parse_number)
    p.add_argument("--authority",required=True,
                   help="Specific ASM11 listing and free-RAM evidence reference")
    p.add_argument("--out-script",required=True)
    p.add_argument("--out-manifest",required=True)
    a=p.parse_args()
    plan=Placement(a.asm_code_end,a.asm_ram_end,
                   a.c_ram_first,a.c_ram_last,a.authority)
    script=linker_script(plan)
    import pathlib
    target=pathlib.Path(a.out_script)
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(script,encoding="utf-8")
    report=pathlib.Path(a.out_manifest)
    report.parent.mkdir(parents=True,exist_ok=True)
    report.write_text(json.dumps(manifest(plan),indent=2)+"\n",
                      encoding="utf-8")
    print(f"Native C ROM: {plan.code_start:04X}-FFBF; "
          f"C state: {plan.c_ram_first:04X}-{plan.c_ram_last:04X} "
          "(scratch RAM must be independently reviewed)")

if __name__=="__main__":
    main()
