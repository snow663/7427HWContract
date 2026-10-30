"""Bounded HC11 ROM decoder for factory control/state tracing.

This decodes bytes, not HAC text. Opcode pages and addressing modes follow
NXP M68HC11ERG, pp. 8-11 and instruction tables. Unsupported encodings fail
explicitly. It is not an emulator, a cycle model, or a whole-ROM code finder.
"""
from __future__ import annotations

from dataclasses import dataclass


BRANCHES = "BRA BRN BHI BLS BCC BCS BNE BEQ BVC BVS BPL BMI BGE BLT BGT BLE".split()
INHERENT = {
    0x01: "NOP", 0x02: "IDIV", 0x03: "FDIV", 0x04: "LSRD", 0x05: "ASLD",
    0x06: "TAP", 0x07: "TPA", 0x08: "INX", 0x09: "DEX", 0x0A: "CLV",
    0x0B: "SEV", 0x0C: "CLC", 0x0D: "SEC", 0x0E: "CLI", 0x0F: "SEI",
    0x10: "SBA", 0x11: "CBA", 0x16: "TAB", 0x17: "TBA", 0x19: "DAA",
    0x1B: "ABA", 0x30: "TSX", 0x31: "INS", 0x32: "PULA", 0x33: "PULB",
    0x34: "DES", 0x35: "TXS", 0x36: "PSHA", 0x37: "PSHB", 0x38: "PULX",
    0x39: "RTS", 0x3A: "ABX", 0x3B: "RTI", 0x3C: "PSHX", 0x3D: "MUL",
    0x3E: "WAI", 0x3F: "SWI", 0x8F: "XGDX", 0xCF: "STOP",
}
UNARY = {0: "NEG", 3: "COM", 4: "LSR", 6: "ROR", 7: "ASR", 8: "ASL",
         9: "ROL", 10: "DEC", 12: "INC", 13: "TST", 14: "JMP", 15: "CLR"}
GROUP_A = "SUBA CMPA SBCA SUBD ANDA BITA LDAA STAA EORA ADCA ORAA ADDA CPX JSR LDS STS".split()
GROUP_B = "SUBB CMPB SBCB ADDD ANDB BITB LDAB STAB EORB ADCB ORAB ADDB LDD STD LDX STX".split()
WORDS = {"SUBD", "ADDD", "CPD", "CPX", "CPY", "LDD", "STD", "LDX", "STX", "LDY", "STY", "LDS", "STS"}
STORES = {"STAA", "STAB", "STD", "STX", "STY", "STS", "CLR"}
MUTATIONS = {"NEG", "COM", "LSR", "ROR", "ASR", "ASL", "ROL", "DEC", "INC", "BSET", "BCLR"}
TERMINALS = {"RTS", "RTI", "SWI", "WAI", "STOP"}


class DecodeError(ValueError):
    pass


@dataclass(frozen=True)
class Instruction:
    pc: int
    data: bytes
    op: str
    mode: str = "inherent"
    value: int | None = None
    target: int | None = None
    mask: int | None = None

    @property
    def next_pc(self):
        return (self.pc + len(self.data)) & 0xFFFF

    @property
    def operand(self):
        if self.mode == "inherent":
            return ""
        if self.mode == "relative":
            return f"${self.target:04X}"
        if self.mode == "immediate":
            return f"#${self.value:0{4 if self.op in WORDS else 2}X}"
        if self.mode.startswith("indexed_"):
            operand = f"${self.value:02X},{self.mode[-1].upper()}"
        else:
            operand = f"${self.value:0{2 if self.mode == 'direct' else 4}X}"
        if self.mask is not None:
            operand += f",#${self.mask:02X}"
        if self.op in {"BRSET", "BRCLR"}:
            operand += f",${self.target:04X}"
        return operand

    def access(self):
        if self.mode not in {"direct", "extended", "indexed_x", "indexed_y"}:
            return None
        if self.op in {"JSR", "JMP"}:
            return None
        access = "W" if self.op in STORES else "RW" if self.op in MUTATIONS else "R"
        target = self.value if self.mode in {"direct", "extended"} else None
        return {"access": access, "width_bits": 16 if self.op in WORDS else 8,
                "address": target, "index": self.mode[-1].upper() if target is None else "",
                "offset": self.value if target is None else None, "mask": self.mask}


def decode(read, pc: int) -> Instruction:
    data = bytearray()

    def take(n=1):
        block = read(pc + len(data), n)
        if len(block) != n:
            raise DecodeError(f"Truncated instruction at {pc:04X}")
        data.extend(block)
        return int.from_bytes(block, "big")

    prefix = None
    opcode = take()
    if opcode in {0x18, 0x1A, 0xCD}:
        prefix, opcode = opcode, take()

    def result(op, mode="inherent", value=None, target=None, mask=None):
        return Instruction(pc, bytes(data), op, mode, value, target, mask)

    def relative():
        offset = take()
        return (pc + len(data) + (offset if offset < 128 else offset - 256)) & 0xFFFF

    if prefix is None and 0x20 <= opcode <= 0x2F:
        target = relative()
        return result(BRANCHES[opcode - 0x20], "relative", target=target)
    if prefix is None and opcode == 0x8D:
        target = relative()
        return result("BSR", "relative", target=target)
    if prefix is None and 0x12 <= opcode <= 0x15:
        value, mask = take(), take()
        op = {0x12: "BRSET", 0x13: "BRCLR", 0x14: "BSET", 0x15: "BCLR"}[opcode]
        target = relative() if op.startswith("BR") else None
        return result(op, "direct", value, target, mask)
    if prefix in {None, 0x18} and 0x1C <= opcode <= 0x1F:
        value, mask = take(), take()
        op = {0x1C: "BSET", 0x1D: "BCLR", 0x1E: "BRSET", 0x1F: "BRCLR"}[opcode]
        target = relative() if op.startswith("BR") else None
        return result(op, "indexed_y" if prefix else "indexed_x", value, target, mask)
    if prefix is None and opcode in INHERENT:
        return result(INHERENT[opcode])
    if prefix == 0x18 and opcode in {0x08, 0x09, 0x30, 0x35, 0x38, 0x3A, 0x3C, 0x8F}:
        return result({0x08: "INY", 0x09: "DEY", 0x30: "TSY", 0x35: "TYS",
                       0x38: "PULY", 0x3A: "ABY", 0x3C: "PSHY", 0x8F: "XGDY"}[opcode])
    if prefix is None and 0x40 <= opcode <= 0x5F and opcode & 15 in UNARY and opcode & 15 != 14:
        return result(UNARY[opcode & 15] + ("A" if opcode < 0x50 else "B"))
    if (prefix is None and 0x60 <= opcode <= 0x7F or prefix == 0x18 and 0x60 <= opcode <= 0x6F) and opcode & 15 in UNARY:
        mode = "extended" if opcode >= 0x70 else "indexed_y" if prefix else "indexed_x"
        value = take(2 if mode == "extended" else 1)
        op = UNARY[opcode & 15]
        return result(op, mode, value, value if op == "JMP" and mode == "extended" else None)

    if opcode >= 0x80:
        mode = ["immediate", "direct", "indexed_x", "extended"][(opcode >> 4) & 3]
        op = (GROUP_A if opcode < 0xC0 else GROUP_B)[opcode & 15]
        if prefix == 0x1A:
            if opcode in {0x83, 0x93, 0xA3, 0xB3}:
                op = "CPD"
            elif opcode in {0xAC, 0xEE, 0xEF}:
                op = {0xAC: "CPY", 0xEE: "LDY", 0xEF: "STY"}[opcode]
            else:
                raise DecodeError(f"Unsupported 1A {opcode:02X} at {pc:04X}")
        elif prefix == 0xCD:
            if opcode not in {0xA3, 0xAC, 0xEE, 0xEF}:
                raise DecodeError(f"Unsupported CD {opcode:02X} at {pc:04X}")
            op = {0xA3: "CPD", 0xAC: "CPX", 0xEE: "LDX", 0xEF: "STX"}[opcode]
            mode = "indexed_y"
        elif prefix == 0x18:
            if op in {"CPX", "LDX", "STX"}:
                op = {"CPX": "CPY", "LDX": "LDY", "STX": "STY"}[op]
            elif mode != "indexed_x":
                raise DecodeError(f"Unsupported 18 {opcode:02X} at {pc:04X}")
            if mode == "indexed_x":
                mode = "indexed_y"
        if mode == "immediate" and (op in STORES or op == "JSR"):
            raise DecodeError(f"Illegal immediate {op} at {pc:04X}")
        value = take(2 if mode == "extended" or mode == "immediate" and op in WORDS else 1)
        return result(op, mode, value, value if op == "JSR" and mode in {"direct", "extended"} else None)
    raise DecodeError(f"Unsupported opcode {bytes(data).hex(' ').upper()} at {pc:04X}")


def successors(ins: Instruction):
    """Intraprocedural edges. A call continuation is conditional on return."""
    if ins.op in TERMINALS:
        return []
    if ins.op in {"JSR", "BSR"}:
        return [(ins.next_pc, "on_call_return")]
    if ins.op in {"BRA", "JMP"}:
        return [(ins.target, "jump")] if ins.target is not None else []
    if ins.op == "BRN":
        return [(ins.next_pc, "fallthrough")]
    if ins.op in BRANCHES or ins.op in {"BRSET", "BRCLR"}:
        return [(ins.target, "branch_taken"), (ins.next_pc, "branch_not_taken")]
    return [(ins.next_pc, "fallthrough")]
