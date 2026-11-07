"""Conservative normal-return memory effects of the exact released Rev B.

Shared by the read inventory and the CS/EN indexed-write trace. Generic entry
registers, unknown pointers and bounded sets remain explicit. This does not
prove interrupt histories, physical aliases or every possible runtime address.
"""
from __future__ import annotations

import hashlib

from build_factory_state_flow import clear_override
from explain_revb_bin import SHA, sweep
from factory_rom_decode import successors
from factory_state_flow import analyze


class Image:
    def __init__(self, contents):
        if len(contents) != 65536 or hashlib.sha256(contents).hexdigest() != SHA:
            raise ValueError("Requires exact released 64-KiB Rev B")
        self.contents = contents

    def read(self, address, length):
        if not 0x4000 <= address or address + length > 65536:
            raise ValueError("BIN padding cannot supply runtime RAM or hardware")
        return self.contents[address:address + length]

    def word(self, address):
        return int.from_bytes(self.read(address, 2), "big")


def analyze_image(contents):
    rom = Image(contents)
    instructions, frontiers, roots = sweep(contents)
    table = [rom.word(0x7a85 + 2 * index) for index in range(16)]
    entries = set(roots) | {0x7100} | {
        i.target for i in instructions.values()
        if i.op in ("JSR", "BSR") and i.target in instructions
    }
    functions = {}
    for entry in sorted(entries):
        pending, local = [entry], {}
        while pending:
            pc = pending.pop()
            if pc in local:
                continue
            local[pc] = instructions[pc]
            pending.extend(target for target, _ in successors(instructions[pc])
                           if target in instructions)
        functions[entry] = local
    graph = {entry: {i.target for i in local.values()
                     if i.op in ("JSR", "BSR") and i.target in entries}
             for entry, local in functions.items()}
    for entry, local in functions.items():
        if 0x7a4f in local:
            graph[entry].update(table)
    order, active, done = [], set(), set()

    def visit(entry):
        if entry in active:
            raise ValueError(f"Recursive component needs review: {entry:04X}")
        if entry in done:
            return
        active.add(entry)
        for target in sorted(graph[entry]):
            visit(target)
        active.remove(entry)
        done.add(entry)
        order.append(entry)

    for entry in sorted(entries):
        visit(entry)
    summaries = {}
    for entry in order:
        summaries[entry] = analyze(rom, entry, functions[entry], summaries,
                                   table, clear_override)
    return dict(rom=rom, instructions=instructions, roots=roots,
                frontiers=frontiers, functions=functions, summaries=summaries)
