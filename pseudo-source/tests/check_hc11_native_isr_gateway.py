#!/usr/bin/env python3
"""Fail-closed ASM11 native ISR entry source contract.

This is not a binary/ABI proof. It enforces safety properties of the
maintainable ASM11 ROM source until an actual linked compiler RTS thunk
and S19/ROM tests exist.
"""
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
RAM=(ROOT/"source/replacement_os/hal/hal_ram.inc").read_text()
ASM=(ROOT/"source/replacement_os/hal/native_isr_gate.asm").read_text()
ROM=(ROOT/"source/replacement_os/7427_rom.asm").read_text()
HEADER=(ROOT/"pseudo-source/include/hc11_irq_mailbox.h").read_text()
VECTOR=(ROOT/"maps/structure/factory_global_vectors.csv").read_text()

def check(value,msg):
    if not value:raise AssertionError(msg)

names=["VECTOR_HI","VECTOR_LO","CCR_ADDR_HI","CCR_ADDR_LO",
       "STATUS","ACTION","BUSY","PROOF"]
allocated=re.findall(r"^\s*HAL_ISR_(\w+):\s+RMB\s+1\s*$", RAM,re.M)
check(allocated==names,"Mailboxes must be eight adjacent one-byte fields")
for i,n in enumerate(names):
    cn=n.replace("CCR_ADDR","CCR")
    check(re.search(r"PCM_IRQ_MB_"+cn+r"\s*=\s*"+str(i)+r"\b",HEADER),
          "C mailbox offset mismatch "+cn)
check('INCLUDE "hal/native_isr_gate.asm"' in ROM,"Modular ROM missing ISR gateway")
check('INCLUDE "hal/hal_ram.inc"' in ROM,"HAL mailbox not allocated")
check(ASM.count("\n        RTI\n")==1,"Gateway must have exactly one guarded RTI")
check("FDB     HAL_ISR_C_UNBOUND" in ASM,"Unbound compiled-C thunk must fail closed")
check("JMP     HAL_FATAL_SAFE_LOOP" in ASM,"Missing fail-closed fatal transfer")

core=ASM.split("HAL_ISR_GATE_COMMON:",1)[1].split("HAL_ISR_GATE_FATAL:",1)[0]
keys=["STD     HAL_ISR_VECTOR_HI","LDAA    HAL_ISR_BUSY",
      "BNE     HAL_ISR_GATE_FATAL","TSX","CPX     #$03B0",
      "BLO     HAL_ISR_GATE_FATAL","CPX     #$03F7",
      "BHI     HAL_ISR_GATE_FATAL","STX     HAL_ISR_CCR_ADDR_HI",
      "STAA    HAL_ISR_BUSY","CLR     HAL_ISR_ACTION",
      "CLR     HAL_ISR_STATUS","STAA    HAL_ISR_PROOF",
      "JSR     HAL_ISR_C_ABI_CALL","LDAA    HAL_ISR_ACTION",
      "CMPA    #HAL_ISR_RETURN_TOKEN","LDAA    HAL_ISR_STATUS",
      "CLR     HAL_ISR_BUSY","RTI"]
last=-1
for token in keys:
    i=core.find(token,last+1)
    check(i>last,"Unsafe gateway instruction ordering/missing: "+token)
    last=i

entries=re.findall(r"^HAL_ISR_ENTRY_(\w+):\s*\n\s*LDD\s+#\$(\w{4})\s*\n\s*JMP\s+HAL_ISR_GATE_COMMON",
                   ASM,re.M)
check(len(entries)==13,"Expected 13 individually identified maskable entry stubs")
vectors=[int(n,16) for _,n in entries]
check(len(set(vectors))==13,"Duplicate native vector entry")
check(all(0xffd6<=n<=0xfff2 and n%2==0 for n in vectors),
      "Bad candidate IRQ vector")
check(not any(v in vectors for v in (0xffe0,0xffe2,0xfff4)),
      "Unresolved OC4/OC5/XIRQ must not be offered as native stubs")
# Preserve every non-reset trap in the modular release source.
section=ROM.split("ORG     ROM_VECTOR_BASE",1)[1]
words=dict((int(a,16),v) for v,a in re.findall(
    r"^\s*FDB\s+(\w+)\s*;\s*\$(\w{4})",section,re.M))
check(len(words)==32,"Vector window must stay complete")
for address in range(0xffc0,0x10000,2):
    expected="RESET_ENTRY" if address==0xfffe else "HAL_FATAL_SAFE_LOOP"
    check(words.get(address)==expected,f"Premature interrupt activation {address:04X}")
check("FFD6,SCI" in VECTOR and "FFFE,reset" in VECTOR,
      "Missing factory-vector evidence")
print("PASS: ASM11 gateway has 8-byte canonical mailbox, 13 masked IRQ stubs, "
      "guarded CCR/SP/RTI path, default reject thunk and 32 safe ROM vectors.")
