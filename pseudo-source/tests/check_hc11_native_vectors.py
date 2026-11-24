#!/usr/bin/env python3
"""Check C vector provenance against stock BMHM and both existing ASM11 images.
The current ROM intentionally traps every interrupt except reset.
This is source validation, NOT a native compiler ABI or assembled BIN proof."""
import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "pseudo-source/include/hc11_vector_map.def"
FACTORY = ROOT / "maps/structure/factory_global_vectors.csv"
ROM = ROOT / "source/replacement_os/7427_rom.asm"
BOOT = ROOT / "source/replacement_os/7427_bootstrap_miniide.asm"
ENTRY = re.compile(r"PCM_HC11_VECTOR\(\s*(0x[0-9a-fA-F]+)\s*,\s*(\w+)\s*,\s*(0x[0-9a-fA-F]+)\s*,\s*(\w+)\s*\)")
FDB = re.compile(r"^\s*FDB\s+(\w+)\s*;\s*\$(\w{4})", re.I)

def require(value, note):
    if not value:
        raise AssertionError(note)

def image_vectors(path):
    content = path.read_text(encoding="utf-8")
    require("ORG     ROM_VECTOR_BASE" in content, path.name + " vector ORG missing")
    section = content.split("ORG     ROM_VECTOR_BASE", 1)[1]
    values = {}
    for line in section.splitlines():
        matched = FDB.match(line)
        if matched:
            sym, word = matched.groups()
            vector = int(word, 16)
            require(vector not in values, path.name + " duplicate vector")
            values[vector] = sym
    require(len(values) == 32, path.name + " expected 32 vector words")
    require(set(values) == set(range(0xffc0, 0x10000, 2)), path.name + " vector holes")
    for vector, symbol in values.items():
        expected = "RESET_ENTRY" if vector == 0xfffe else "HAL_FATAL_SAFE_LOOP"
        require(symbol == expected, path.name + f" unsafe 0x{vector:04x} -> {symbol}")
    return values

def main():
    entries = [(int(a, 16), name, int(target, 16), kind)
               for a, name, target, kind in ENTRY.findall(
                   SOURCE.read_text(encoding="utf-8"))]
    require(len(entries) == 21, "21 HC11 vectors expected in C bridge")
    require([z[0] for z in entries] == list(range(0xffd6, 0x10000, 2)),
            "C vector map holes/order")
    with FACTORY.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    require(len(rows) == 21, "Stock BMHM vector evidence changed")
    for row, (vector, name, target, kind) in zip(rows, entries):
        require(int(row["vector_address"], 16) == vector, "Vector address drift")
        require(row["name"] == name, "Vector name drift: " + name)
        require(int(row["target"], 16) == target, "Stock handler drift " + name)
        require(kind.upper() == kind, "Invalid C policy " + name)
    image_vectors(ROM)
    image_vectors(BOOT)
    print("PASS: 21 C dispatch identities match stock vector ROM and both "
          "ASM11 images retain 32 engine-off safe vectors.")

if __name__ == "__main__":
    main()
