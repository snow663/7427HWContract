#!/usr/bin/env python3
"""Narrow, deterministic RAM-owner gate for literal factory FUEL writes.

This is not a whole-ROM, indexed/pointer, or target hardware completeness test.
It only covers CPU addresses directly listed as WRITE operands in the
maintained source-scoped factory_fuel_memory_accesses.csv.
"""
import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FACTORY = ROOT.parent / "maps/structure/factory_fuel_memory_accesses.csv"
OWNER_READ = ROOT / "src/system/fuel_ram_owner_read8.c"
OWNER_WRITE = ROOT / "src/system/fuel_ram_owner_write8.c"
CASE = re.compile(r"\bcase\s+0x([0-9a-fA-F]+)\s*:")

def addresses(path):
    return {int(s, 16) for s in CASE.findall(path.read_text(encoding="utf-8"))}

def main():
    readers = addresses(OWNER_READ)
    writers = addresses(OWNER_WRITE)
    if readers != writers:
        raise AssertionError("Read/write byte-owner address sets diverged")
    covered_byte_sites = 0
    literal_write_sites = 0
    missing = []
    with FACTORY.open(newline="", encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            address = row["address"].strip()
            if row["access"] != "W" or not re.fullmatch(r"[0-9a-fA-F]{4}", address):
                continue
            start = int(address, 16)
            if start >= 0x1000:
                continue
            bits = int(row["width_bits"])
            if bits not in (8, 16):
                raise AssertionError("Unsupported source width at PC " + row["pc"])
            literal_write_sites += 1
            for byte in range(start, start + bits // 8):
                covered_byte_sites += 1
                if byte not in readers:
                    missing.append((row["pc"], f"{byte:04X}"))
    if literal_write_sites < 45:
        raise AssertionError("Factory literal fuel writer evidence unexpectedly sparse")
    if missing:
        raise AssertionError("Unmapped source-scoped fuel writes: " + repr(missing))
    print(f"Factory fuel low-RAM literal WRITE scope: {literal_write_sites} "
          f"instructions, {covered_byte_sites} byte sites, all have source "
          "RAM read/write owners; indexed/dynamic and hardware remain open.")

if __name__ == "__main__":
    main()
