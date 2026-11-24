#!/usr/bin/env python3
"""Source-only proof of safe optional native-C startup in the ASM11 master.

Assembler output/link address, true MC68HC11 compiler ABI and target RAM
need independent verification; this test does not establish any of them.
"""
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[2]
MASTER=(ROOT/"source/replacement_os/7427_rom.asm").read_text()
STARTUP=(ROOT/"source/replacement_os/hal/native_c_startup.asm").read_text()

def require(test,claim):
    if not test:
        raise AssertionError(claim)

require('INCLUDE "hal/native_c_startup.asm"' in MASTER,"New C startup module not included")
reset=MASTER.split("RESET_ENTRY:",1)[1].split("FIRST_ROM_IDLE_LOOP:",1)[0]
require(reset.index("SEI")<reset.index("LDS     #STACK_TOP")<
        reset.index("JSR     OS_SAFE_INIT")<
        reset.index("JSR     HAL_NATIVE_C_INITIALIZE"),
        "C startup must run only after masked HC11 reset and safe OS initialization")
require("CLI" not in reset,"C initialization cannot enable interrupts")
require(re.search(r"HAL_C_STARTUP_TOKEN:\s*\n\s*FCB\s+\$00\b",STARTUP),
        "C startup must default to disabled")
require(re.search(r"HAL_C_STATE_START_WORD:\s*\n\s*FDB\s+\$0000\b",STARTUP),
        "C RAM start must be unbound by default")
require(re.search(r"HAL_C_STATE_END_WORD:\s*\n\s*FDB\s+\$0000\b",STARTUP),
        "C RAM end must be unbound by default")
require("FDB     HAL_C_BOOT_UNBOUND" in STARTUP,
        "C reset target must be a rejecting unbound address")
sequence=STARTUP.split("HAL_NATIVE_C_INITIALIZE:",1)[1].split("HAL_C_BOOT_SKIP:",1)[0]
checks=[
    "LDAA    HAL_C_STARTUP_TOKEN","BEQ     HAL_C_BOOT_SKIP",
    "CMPA    #HAL_C_STARTUP_SIGNATURE","BNE     HAL_C_BOOT_FATAL",
    "LDX     HAL_C_STATE_START_WORD",
    "CPX     HAL_C_STATE_END_WORD","BHI     HAL_C_BOOT_FATAL",
    "CLR     0,X","INX","CPX     HAL_C_STATE_END_WORD",
    "LDX     HAL_C_RESET_CALL_WORD","JSR     0,X"
]
prev=-1
for required in checks:
    pos=sequence.find(required,prev+1)
    require(pos>prev,"C startup order/instruction missing: "+required)
    prev=pos
require("JMP     HAL_FATAL_SAFE_LOOP" in STARTUP,"C startup fault must halt engine")
vector_words=re.findall(r"^\s*FDB\s+(\w+)\s*;\s*\$(\w{4})",MASTER,re.M)
require(len(vector_words)==32,"All 32 ASM11 vectors must remain present")
for sym,address in vector_words:
    expected="RESET_ENTRY" if address.upper()=="FFFE" else "HAL_FATAL_SAFE_LOOP"
    require(sym==expected,"Unexpected live native vector: "+address)
print("PASS: native C BSS/softreg startup disabled by default, ordered after"
      " masked reset, zeroes linked state before RTS C call, safe vector table intact.")
