#!/usr/bin/env python3
"""Structural checks for the 7427 replacement-ROM modular master.

This is intentionally not an assembler and not a hardware proof. It catches
placement/policy mistakes in the maintainable modular source and complements
the proven ASM11 listing/S19/BIN workflow and separate bench validation.
"""

from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / "source/replacement_os/7427_rom.asm"
LAYOUT = ROOT / "source/replacement_os/include/target_layout.inc"
ABI = ROOT / "source/replacement_os/include/runtime_abi.inc"
HAL_RAM = ROOT / "source/replacement_os/hal/hal_ram.inc"
ADC = ROOT / "source/replacement_os/hal/adc_read.asm"
INIT = ROOT / "source/replacement_os/hal/init_safe.asm"


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def parse_number(token: str, symbols: dict[str, int]) -> int:
    token = token.strip()
    if token.startswith("$"):
        return int(token[1:], 16)
    if token.isdigit():
        return int(token, 10)
    if token in symbols:
        return symbols[token]
    raise ValueError(token)


def parse_equ(text: str, symbols: dict[str, int]) -> None:
    for raw in text.splitlines():
        line = raw.split(";", 1)[0].strip()
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s+EQU\s+([^\s]+)$", line)
        if not m:
            continue
        name, value = m.groups()
        try:
            symbols[name] = parse_number(value, symbols)
        except ValueError:
            # Expressions are deliberately ignored by this small verifier.
            pass


def rmb_size(text: str, symbols: dict[str, int]) -> int:
    total = 0
    for raw in text.splitlines():
        line = raw.split(";", 1)[0].strip()
        m = re.search(r"\bRMB\s+([^\s]+)", line)
        if not m:
            continue
        try:
            total += parse_number(m.group(1), symbols)
        except ValueError as exc:
            fail(f"unresolved RMB size {exc.args[0]!r}")
    return total


def main() -> int:
    files = [MASTER, LAYOUT, ABI, HAL_RAM, ADC, INIT]
    missing = [str(p.relative_to(ROOT)) for p in files if not p.exists()]
    if missing:
        fail(f"missing files: {', '.join(missing)}")

    master = MASTER.read_text()
    layout = LAYOUT.read_text()
    abi = ABI.read_text()
    hal_ram = HAL_RAM.read_text()
    adc = ADC.read_text()
    init = INIT.read_text()

    symbols: dict[str, int] = {}
    parse_equ(layout, symbols)
    parse_equ(abi, symbols)
    parse_equ(hal_ram, symbols)

    required = {
        "RAM_RUNTIME_BASE": 0x0000,
        "STACK_TOP": 0x03FF,
        "RAM_AUX_BASE": 0x0800,
        "RAM_AUX_END": 0x08FF,
        "ROM_CAL_REGION_BASE": 0x4000,
        "ROM_EXEC_BASE": 0x7100,
        "ROM_VECTOR_BASE": 0xFFC0,
        "ROM_RESET_VECTOR": 0xFFFE,
        "ROM_END": 0xFFFF,
    }
    for name, expected in required.items():
        actual = symbols.get(name)
        if actual != expected:
            fail(f"{name} expected ${expected:04X}, got {actual!r}")

    ram_bytes = rmb_size(abi, symbols) + rmb_size(hal_ram, symbols)
    ram_end_exclusive = symbols["RAM_RUNTIME_BASE"] + ram_bytes
    if ram_end_exclusive >= symbols["STACK_TOP"]:
        fail(
            f"allocated low RAM reaches ${ram_end_exclusive:04X}, "
            f"colliding with stack top ${symbols['STACK_TOP']:04X}"
        )

    if 'ORG     ROM_EXEC_BASE' not in master:
        fail("ROM master does not ORG executable code at ROM_EXEC_BASE")
    if 'ORG     ROM_VECTOR_BASE' not in master:
        fail("ROM master does not ORG vector table at ROM_VECTOR_BASE")

    vector_part = master.split('ORG     ROM_VECTOR_BASE', 1)[1]
    vectors = [line for line in vector_part.splitlines() if re.search(r"\bFDB\b", line)]
    if len(vectors) != 32:
        fail(f"expected 32 vector FDB entries from $FFC0-$FFFE, found {len(vectors)}")
    if "RESET_ENTRY" not in vectors[-1]:
        fail("last vector ($FFFE) does not point to RESET_ENTRY")

    forbidden_calls = (
        "JSR     HAL_GM_FUEL_SYNC_COMMIT",
        "JSR     HAL_GM_FUEL_ASYNC_COMMIT",
        "JSR     HAL_GM_IAC_COMMIT",
        "JSR     HAL_GM_PUMP_COMMIT",
        "JSR     HAL_COMMIT_SPARK",
    )
    for call in forbidden_calls:
        if call in master:
            fail(f"first ROM master contains production-output call: {call.strip()}")

    if re.search(r"HC11_OPTION\s+EQU\s+\$3008", adc):
        fail("ADC HAL still mislabels $3008 as HC11_OPTION")
    if not re.search(r"HC11_PORTD\s+EQU\s+\$3008", adc):
        fail("ADC HAL does not identify source-proven $3008 PORTD mux control")
    if not re.search(r"HC11_OPTION_OFF\s+EQU\s+\$39", init):
        fail("processor bootstrap does not use source-proven OPTION offset $39")

    print("PASS: 7427 ROM bootstrap structural checks")
    print(f"PASS: low-RAM allocation = {ram_bytes} bytes, end-exclusive=${ram_end_exclusive:04X}")
    print("PASS: 32 vectors cover $FFC0-$FFFE; reset -> RESET_ENTRY")
    print("PASS: no production-output commit is called by first ROM master")
    print("PASS: ADC mux semantics use PORTD $3008; OPTION remains offset $39")
    return 0


if __name__ == "__main__":
    sys.exit(main())
