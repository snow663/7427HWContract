#!/usr/bin/env python3
"""
Static hardware-access extractor for GM 7427 / MC68HC11 disassembly listings.

Purpose:
  Parse annotated source listings such as `31_HAC_from_ORG_7100_to_end_NOWRAP.asm`.
  Emit CSV rows for CPU reads/writes/RMW operations.
  Resolve simple indexed addressing when X/Y were recently loaded with constants.

This is intentionally conservative. Unknowns remain unknown/test items rather than being silently discarded.
"""

from __future__ import annotations

import argparse
import csv
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

PC_RE = re.compile(r"^\s*([0-9A-Fa-f]{4}):\s*(.*)$")
LABEL_RE = re.compile(r"\b(L[0-9A-Fa-f]{4})\b")
IMM16_RE = re.compile(r"#\$([0-9A-Fa-f]{4})")
HEX_ADDR_RE = re.compile(r"\$([0-9A-Fa-f]{2,4})")
INDEXED_RE = re.compile(r"\$([0-9A-Fa-f]{1,4})\s*,\s*([XY])\b", re.IGNORECASE)
DIRECT_LABEL_RE = re.compile(r"\bL([0-9A-Fa-f]{4})\b")

LOAD_OPS = {"LDAA", "LDAB", "LDD", "LDS", "LDX", "LDY"}
STORE_OPS = {"STAA", "STAB", "STD", "STS", "STX", "STY"}
RMW_OPS = {"BSET", "BCLR", "INC", "DEC", "CLR", "COM", "NEG", "ASL", "LSL", "LSR", "ROL", "ROR"}
BRANCH_BIT_OPS = {"BRSET", "BRCLR"}
CALL_OPS = {"JSR", "JMP", "RTS", "RTI"}

WIDTH_BY_OP = {
    "STAA": 8, "STAB": 8, "STD": 16, "STS": 16, "STX": 16, "STY": 16,
    "LDAA": 8, "LDAB": 8, "LDD": 16, "LDS": 16, "LDX": 16, "LDY": 16,
    "BSET": 8, "BCLR": 8, "BRSET": 8, "BRCLR": 8,
    "INC": 8, "DEC": 8, "CLR": 8, "COM": 8, "NEG": 8,
    "ASL": 8, "LSL": 8, "LSR": 8, "ROL": 8, "ROR": 8,
}

SUBSYSTEM_RULES = [
    ("FUEL_SCHED_TIMER", {0x301C, 0x301D, 0x301E, 0x301F, 0x3020, 0x3022, 0x3023}),
    ("BOOT_WATCHDOG_CPU", {0x3039, 0x303A, 0x303D, 0x303F, 0x3000, 0x3008, 0x3024, 0x3035, 0x3038}),
    ("SENSOR_ADC", {0x3030, 0x3031, 0x3032, 0x3033, 0x3034}),
    ("ALDL_SCI", {0x302C, 0x302D, 0x302E, 0x302F}),
]

ASIC_STATUS = {0x3FC0, 0x3FC4, 0x3FCA, 0x3FFA}
ASIC_COMMAND = {0x3FCC, 0x3FCE, 0x3FD4, 0x3FD6, 0x3FD8, 0x3FDA, 0x3FDC, 0x3FE0, 0x3FE4, 0x3FE6, 0x3FE8, 0x3FEA, 0x3FEC, 0x3FF2, 0x3FF6, 0x3FF8, 0x3FFC}


@dataclass
class Row:
    pc: str
    opcode: str
    mnemonic: str
    access_type: str
    effective_address: str
    address_class: str
    width: str
    bitmask: str
    value_source: str
    x_base_y_base: str
    routine_label: str
    notes: str
    confidence: str
    subsystem: str
    minimal_os_required: str
    risk: str


def parse_int_hex(s: str) -> int:
    return int(s, 16)


def classify_address(addr: Optional[int]) -> str:
    if addr is None:
        return "UNKNOWN"
    if 0x3000 <= addr <= 0x303F:
        return "HC11_REG"
    if 0x3F00 <= addr <= 0x3FFF:
        return "ASIC_3FXX"
    if 0x0000 <= addr <= 0x03FF:
        return "DIRECT_RAM"
    if 0x0400 <= addr <= 0x0FFF:
        return "EXT_RAM"
    if 0x4000 <= addr <= 0xFFFF:
        return "ROM_TABLE"
    if 0x3060 <= addr <= 0x306F:
        return "UNKNOWN_HW"
    return "UNKNOWN_HW"


def classify_subsystem(addr: Optional[int], op: str, raw: str) -> str:
    if addr is None:
        return "OTHER"
    for name, addrs in SUBSYSTEM_RULES:
        if addr in addrs:
            return name
    if 0x3060 <= addr <= 0x306F:
        return "UNKNOWN_306X_BOARD_IO"
    if addr in ASIC_STATUS:
        return "ASIC_STATUS_REF"
    if addr in ASIC_COMMAND:
        if addr in {0x3FE6, 0x3FE8, 0x3FF6, 0x3FDC}:
            return "SPARK_EST"
        if addr in {0x3FCE}:
            return "FUEL_MATH_HANDOFF"
        if addr in {0x3FFC}:
            return "IO_LATCH_OUTPUT"
        return "ASIC_COMMAND_OUTPUT"
    if 0x3F00 <= addr <= 0x3FFF:
        return "ASIC_UNKNOWN"
    return "OTHER"


def is_required(subsystem: str) -> str:
    if subsystem in {
        "FUEL_SCHED_TIMER", "BOOT_WATCHDOG_CPU", "SENSOR_ADC", "ALDL_SCI",
        "ASIC_STATUS_REF", "ASIC_COMMAND_OUTPUT", "SPARK_EST", "FUEL_MATH_HANDOFF",
        "IO_LATCH_OUTPUT", "UNKNOWN_306X_BOARD_IO", "ASIC_UNKNOWN",
    }:
        return "yes_or_test_item"
    return "unknown"


def risk_for(subsystem: str) -> str:
    if subsystem in {"FUEL_SCHED_TIMER", "SPARK_EST", "IO_LATCH_OUTPUT", "UNKNOWN_306X_BOARD_IO", "ASIC_UNKNOWN"}:
        return "high"
    if subsystem in {"ASIC_STATUS_REF", "ASIC_COMMAND_OUTPUT", "BOOT_WATCHDOG_CPU", "SENSOR_ADC"}:
        return "medium"
    return "low"


def extract_mnemonic(text: str) -> tuple[str, str]:
    parts = text.strip().split(None, 1)
    if not parts:
        return "", ""
    return parts[0].upper(), parts[1] if len(parts) > 1 else ""


def resolve_effective_address(operand: str, x_base: Optional[int], y_base: Optional[int]) -> tuple[Optional[int], str]:
    m = INDEXED_RE.search(operand)
    if m:
        offset = parse_int_hex(m.group(1))
        reg = m.group(2).upper()
        base = x_base if reg == "X" else y_base
        base_text = f"{reg}=${base:04X}" if base is not None else f"{reg}=unknown"
        return (base + offset if base is not None else None), base_text
    m = DIRECT_LABEL_RE.search(operand)
    if m:
        return parse_int_hex(m.group(1)), ""
    m = HEX_ADDR_RE.search(operand)
    if m and not operand.strip().startswith("#"):
        return parse_int_hex(m.group(1)), ""
    return None, ""


def extract_bitmask(op: str, operand: str) -> str:
    if op not in RMW_OPS and op not in BRANCH_BIT_OPS:
        return ""
    parts = [p.strip() for p in operand.split(",")]
    for part in reversed(parts):
        if part.startswith("#"):
            return part
    return ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("source", type=Path)
    ap.add_argument("output", type=Path)
    args = ap.parse_args()

    x_base: Optional[int] = None
    y_base: Optional[int] = None
    current_label = ""
    rows: list[Row] = []

    for line in args.source.read_text(errors="replace").splitlines():
        pm = PC_RE.match(line)
        if not pm:
            lm = LABEL_RE.search(line)
            if lm:
                current_label = lm.group(1)
            continue
        pc = pm.group(1).upper()
        body = pm.group(2)
        lm = LABEL_RE.search(body)
        if lm:
            current_label = lm.group(1)
            body = body.replace(current_label, "", 1)
        op, operand = extract_mnemonic(body)
        if not op:
            continue
        if op == "LDX":
            imm = IMM16_RE.search(operand)
            if imm:
                x_base = parse_int_hex(imm.group(1))
        elif op == "LDY":
            imm = IMM16_RE.search(operand)
            if imm:
                y_base = parse_int_hex(imm.group(1))

        if op in STORE_OPS:
            atype = "W"
        elif op in LOAD_OPS:
            atype = "R"
        elif op in RMW_OPS:
            atype = "RMW"
        elif op in BRANCH_BIT_OPS:
            atype = "R"
        else:
            continue

        addr, base_text = resolve_effective_address(operand, x_base, y_base)
        addr_class = classify_address(addr)
        subsystem = classify_subsystem(addr, op, body)
        rows.append(Row(
            pc=pc,
            opcode=op,
            mnemonic=body.strip(),
            access_type=atype,
            effective_address=f"${addr:04X}" if addr is not None else "",
            address_class=addr_class,
            width=str(WIDTH_BY_OP.get(op, "")),
            bitmask=extract_bitmask(op, operand),
            value_source="CPU register/immediate/RAM source - trace backward required",
            x_base_y_base=base_text,
            routine_label=current_label,
            notes="indexed address resolved" if base_text else "",
            confidence="medium" if addr is not None else "low",
            subsystem=subsystem,
            minimal_os_required=is_required(subsystem),
            risk=risk_for(subsystem),
        ))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(Row.__annotations__.keys()))
        w.writeheader()
        for row in rows:
            w.writerow(row.__dict__)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
