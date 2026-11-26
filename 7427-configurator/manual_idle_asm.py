"""Small, strict HC11 assembler for the manual-idle strategy, not a general assembler.

Only the instructions/directives used by the reviewed source are accepted. The
repository decoder checks every emitted instruction. No binary file is written.
"""
from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
import re

from factory_rom_decode import BRANCHES, GROUP_A, GROUP_B, INHERENT, WORDS, decode


@dataclass
class Assembly:
    memory: dict[int, int]
    symbols: dict[str, int]
    instructions: dict[int, tuple[str, str]]


def expression(text: str, symbols: dict[str, int], unresolved=False) -> int:
    text = re.sub(r"\$([0-9a-fA-F]+)", r"0x\1", text.strip())

    def visit(node):
        if isinstance(node, ast.Constant) and isinstance(node.value, int):
            return node.value
        if isinstance(node, ast.Name):
            if node.id in symbols:
                return symbols[node.id]
            if unresolved:
                return 0
            raise ValueError("Unknown symbol: " + node.id)
        if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub)):
            a, b = visit(node.left), visit(node.right)
            return a + b if isinstance(node.op, ast.Add) else a - b
        raise ValueError("Unsupported expression: " + text)

    return visit(ast.parse(text, mode="eval").body)


def assemble(path: Path) -> Assembly:
    source = []
    for number, line in enumerate(path.read_text().splitlines(), 1):
        line = line.split(";", 1)[0].strip()
        if line:
            source.append((number, line))
    symbols, memory, instructions = {}, {}, {}
    inherent = {name: code for code, name in INHERENT.items()}
    inherent.update(CLRA=0x4f, CLRB=0x5f, INCA=0x4c, DECA=0x4a,
                    LSRA=0x44, ASLA=0x48, NEGA=0x40, DECB=0x5a)
    branches = {name: code + 0x20 for code, name in enumerate(BRANCHES)}
    branches.update(BLO=0x25, BHS=0x24)

    for final in (False, True):
        pc = None
        for number, line in source:
            try:
                if " equ " in line.lower():
                    name, _, expr = line.split(None, 2)
                    if not final:
                        if name in symbols:
                            raise ValueError("Duplicate symbol: " + name)
                        symbols[name] = expression(expr, symbols)
                    continue
                if ":" in line:
                    name, line = line.split(":", 1)
                    if not final:
                        if name in symbols:
                            raise ValueError("Duplicate label: " + name)
                        symbols[name] = pc
                    line = line.strip()
                    if not line:
                        continue
                fields = line.split(None, 1)
                op = fields[0].upper()
                arg = fields[1].strip() if len(fields) == 2 else ""
                val = lambda s: expression(s, symbols, unresolved=not final)
                if op == ".ORG":
                    pc = val(arg)
                    continue
                if pc is None:
                    raise ValueError("Missing .org")
                is_instruction = not op.startswith(".")
                if op in (".BYTE", ".WORD"):
                    data = bytearray()
                    for token in arg.split(","):
                        data.extend(val(token).to_bytes(1 if op == ".BYTE" else 2, "big"))
                elif op in inherent:
                    if arg:
                        raise ValueError("Unexpected operand")
                    data = bytes([inherent[op]])
                elif op in branches:
                    delta = val(arg) - (pc + 2)
                    if final and not -128 <= delta <= 127:
                        raise ValueError(f"Branch out of range: {delta}")
                    data = bytes([branches[op], delta & 255])
                elif op in ("BSET", "BCLR", "BRSET", "BRCLR"):
                    parts = [x.strip() for x in arg.split(",")]
                    if len(parts) != (3 if op.startswith("BR") else 2):
                        raise ValueError("Bit instruction operands")
                    addr, mask = val(parts[0]), val(parts[1].lstrip("#"))
                    data = bytearray([{"BSET": 0x14, "BCLR": 0x15,
                                       "BRSET": 0x12, "BRCLR": 0x13}[op], addr, mask])
                    if op.startswith("BR"):
                        delta = val(parts[2]) - (pc + 4)
                        if final and not -128 <= delta <= 127:
                            raise ValueError(f"Bit branch out of range: {delta}")
                        data.append(delta & 255)
                elif op in ("CLR", "TST", "INC", "DEC", "JMP"):
                    code = {"CLR": 0x7f, "TST": 0x7d, "INC": 0x7c,
                            "DEC": 0x7a, "JMP": 0x7e}[op]
                    data = bytes([code]) + val(arg).to_bytes(2, "big")
                elif op in GROUP_A or op in GROUP_B:
                    group, base = (GROUP_A, 0x80) if op in GROUP_A else (GROUP_B, 0xc0)
                    if arg.startswith("#"):
                        if op.startswith("ST") or op == "JSR":
                            raise ValueError("Illegal immediate instruction")
                        mode, token, width = 0, arg[1:], 2 if op in WORDS else 1
                    elif arg.startswith("<"):
                        mode, token, width = 0x10, arg[1:], 1
                    else:
                        mode, token, width = 0x30, arg, 2
                    data = bytes([base + mode + group.index(op)]) + val(token).to_bytes(width, "big")
                else:
                    raise ValueError("Unsupported opcode: " + op)
                if final:
                    for offset, byte in enumerate(data):
                        address = pc + offset
                        if address in memory or not 0x4000 <= address < 0xffc0:
                            raise ValueError(f"Overlapping/invalid ROM placement: {address:04X}")
                        memory[address] = byte
                    if is_instruction:
                        decoded = decode(lambda a, n: bytes(memory[x] for x in range(a, a + n)), pc)
                        expected = {"BLO": "BCS", "BHS": "BCC"}.get(op, op)
                        if decoded.op != expected or len(decoded.data) != len(data):
                            raise ValueError("Decoder disagreement")
                        instructions[pc] = (op, arg)
                pc += len(data)
            except Exception as exc:
                raise ValueError(f"{path.name}:{number}: {line}: {exc}") from exc
    return Assembly(memory, symbols, instructions)
