"""Strict, incremental MC68HC11 interpreter (not yet full ISA).

Instruction semantics for the implemented subset come from the M68HC11RM.
Unsupported instructions raise UnknownInstruction at their exact fetch PC.
No translation from factory C pseudo-source into CPU execution is implied.
"""
from dataclasses import dataclass
from .bus import Bus

I = 0x10
X_MASK = 0x40
S = 0x80
N = 0x08
Z = 0x04
V = 0x02
C = 0x01

class UnknownInstruction(RuntimeError):
    def __init__(self, pc: int, opcode: int):
        super().__init__(f"Unimplemented HC11 opcode ${opcode:02X} at ${pc:04X}")
        self.pc = pc
        self.opcode = opcode

@dataclass
class Registers:
    a: int = 0
    b: int = 0
    x: int = 0
    y: int = 0
    sp: int = 0
    pc: int = 0
    ccr: int = S | I | X_MASK

    @property
    def d(self) -> int:
        return (self.a << 8) | self.b

    @d.setter
    def d(self, value: int):
        self.a, self.b = (value >> 8) & 0xFF, value & 0xFF

class CPU:
    def __init__(self, bus: Bus):
        self.bus = bus
        self.r = Registers()
        self.instructions = 0
        self.cycles = 0  # provisional: only instructions with reviewed counts
        self.irq_inhibit_instructions = 0

    def reset(self):
        self.r = Registers(pc=self.bus.read16(0xFFFE))
        self.instructions = 0
        self.cycles = 0
        self.irq_inhibit_instructions = 0

    def _fetch8(self) -> int:
        v = self.bus.read8(self.r.pc)
        self.r.pc = (self.r.pc + 1) & 0xFFFF
        return v

    def _fetch16(self) -> int:
        return (self._fetch8() << 8) | self._fetch8()

    def _push8(self, value: int):
        self.bus.write8(self.r.sp, value)
        self.r.sp = (self.r.sp - 1) & 0xFFFF

    def _pull8(self) -> int:
        self.r.sp = (self.r.sp + 1) & 0xFFFF
        return self.bus.read8(self.r.sp)

    def _push16(self, value: int):
        self._push8(value & 0xFF)
        self._push8(value >> 8)

    def _pull16(self) -> int:
        return (self._pull8() << 8) | self._pull8()

    def _nz8(self, value: int):
        self.r.ccr &= ~(N | Z | V)
        if value & 0x80:
            self.r.ccr |= N
        if value == 0:
            self.r.ccr |= Z

    def _nz16(self, value: int):
        self.r.ccr &= ~(N | Z | V)
        if value & 0x8000:
            self.r.ccr |= N
        if value == 0:
            self.r.ccr |= Z

    def _cmp8(self, a: int, b: int):
        result = (a - b) & 0xFF
        self._nz8(result)
        if a < b:
            self.r.ccr |= C
        else:
            self.r.ccr &= ~C
        if ((a ^ b) & (a ^ result) & 0x80) != 0:
            self.r.ccr |= V

    def _cmp16(self, a: int, b: int):
        result = (a - b) & 0xFFFF
        self._nz16(result)
        if a < b:
            self.r.ccr |= C
        else:
            self.r.ccr &= ~C
        if ((a ^ b) & (a ^ result) & 0x8000) != 0:
            self.r.ccr |= V

    def interrupt(self, vector_address: int, *, maskable: bool = True) -> bool:
        """Hardware frame order: PCL,PCH,IYL,IYH,IXL,IXH,A,B,CCR."""
        vector_address &= 0xFFFF
        if (self.r.ccr & X_MASK) if vector_address == 0xFFF4 else (maskable and (self.r.ccr & I or self.irq_inhibit_instructions)):
            return False
        r = self.r
        for byte in (
            r.pc & 0xFF, r.pc >> 8,
            r.y & 0xFF, r.y >> 8,
            r.x & 0xFF, r.x >> 8,
            r.a, r.b, r.ccr
        ):
            self._push8(byte)
        r.ccr |= I
        if vector_address == 0xFFF4:  # XIRQ also masks X on entry
            r.ccr |= X_MASK
        r.pc = self.bus.read16(vector_address)
        return True

    def step(self) -> tuple[int, int]:
        r = self.r
        if self.irq_inhibit_instructions:
            self.irq_inhibit_instructions -= 1
        pc = r.pc
        op = self._fetch8()
        # Any instruction missing from this explicit set fails, even if the
        # last successful command left registers looking plausible.
        if op == 0x01:  # NOP
            pass
        elif op == 0x0F:  # SEI
            r.ccr |= I
        elif op == 0x0E:  # CLI
            self.irq_inhibit_instructions = int(bool(r.ccr & I))
            r.ccr &= ~I
        elif op == 0x8E:  # LDS #imm16
            r.sp = self._fetch16()
            self._nz16(r.sp)
        elif op == 0xCE:  # LDX #imm16
            r.x = self._fetch16()
            self._nz16(r.x)
        elif op == 0x86:  # LDAA #imm
            r.a = self._fetch8()
            self._nz8(r.a)
        elif op == 0xC6:  # LDAB #imm
            r.b = self._fetch8()
            self._nz8(r.b)
        elif op == 0xCC:  # LDD #imm16
            r.d = self._fetch16()
            self._nz16(r.d)
        elif op == 0xB6:  # LDAA extended
            r.a = self.bus.read8(self._fetch16())
            self._nz8(r.a)
        elif op == 0xA7:  # STAA indexed X + unsigned offset
            self.bus.write8((r.x + self._fetch8()) & 0xFFFF, r.a)
            self._nz8(r.a)
        elif op == 0xB7:  # STAA extended
            self.bus.write8(self._fetch16(), r.a)
            self._nz8(r.a)
        elif op == 0xF7:  # STAB extended
            self.bus.write8(self._fetch16(), r.b)
            self._nz8(r.b)
        elif op == 0xFD:  # STD extended (high, low)
            self.bus.write16(self._fetch16(), r.d)
            self._nz16(r.d)
        elif op == 0xFF:  # STX extended
            self.bus.write16(self._fetch16(), r.x)
            self._nz16(r.x)
        elif op == 0x7F:  # CLR extended
            address = self._fetch16()
            # CLR performs an operand read before its write. That read can
            # complete a peripheral status-clear sequence (RM §5.9.3).
            self.bus.read8(address)
            self.bus.write8(address, 0)
            self._nz8(0)
            r.ccr &= ~C
        elif op == 0x6F:  # CLR offset,X
            address = (r.x + self._fetch8()) & 0xFFFF
            self.bus.read8(address)
            self.bus.write8(address, 0)
            self._nz8(0)
            r.ccr &= ~C
        elif op == 0x14:  # BSET direct, #mask
            addr, mask = self._fetch8(), self._fetch8()
            value = self.bus.read8(addr) | mask
            self.bus.write8(addr, value)
            self._nz8(value)
        elif op == 0x15:  # BCLR direct, #mask
            addr, mask = self._fetch8(), self._fetch8()
            value = self.bus.read8(addr) & ~mask
            self.bus.write8(addr, value)
            self._nz8(value)
        elif op == 0x1D:  # BCLR offset,X, #mask
            addr = (r.x + self._fetch8()) & 0xFFFF
            mask = self._fetch8()
            value = self.bus.read8(addr) & ~mask
            self.bus.write8(addr, value)
            self._nz8(value)
        elif op == 0x43:  # COMA
            r.a ^= 0xFF
            self._nz8(r.a)
            r.ccr |= C
        elif op == 0x08:  # INX
            r.x = (r.x + 1) & 0xFFFF
            r.ccr = (r.ccr & ~Z) | (Z if r.x == 0 else 0)
        elif op == 0x09:  # DEX
            r.x = (r.x - 1) & 0xFFFF
            r.ccr = (r.ccr & ~Z) | (Z if r.x == 0 else 0)
        elif op == 0x8C:  # CPX #imm16
            self._cmp16(r.x, self._fetch16())
        elif op == 0x81:  # CMPA #imm8
            self._cmp8(r.a, self._fetch8())
        elif op in (0x20, 0x26, 0x27, 0x22, 0x25):  # relative branches
            delta = self._fetch8()
            if delta & 0x80:
                delta -= 0x100
            take = (op == 0x20 or
                    (op == 0x26 and not r.ccr & Z) or
                    (op == 0x27 and bool(r.ccr & Z)) or
                    (op == 0x22 and not r.ccr & (C | Z)) or
                    (op == 0x25 and bool(r.ccr & C)))
            if take:
                r.pc = (r.pc + delta) & 0xFFFF
        elif op == 0x7E:  # JMP extended
            r.pc = self._fetch16()
        elif op == 0xBD:  # JSR extended
            dest = self._fetch16()
            self._push16(r.pc)
            r.pc = dest
        elif op == 0xAD:  # JSR offset,X
            dest = (r.x + self._fetch8()) & 0xFFFF
            self._push16(r.pc)
            r.pc = dest
        elif op == 0x39:  # RTS
            r.pc = self._pull16()
        elif op == 0x30:  # TSX: X = SP+1
            r.x = (r.sp + 1) & 0xFFFF
        elif op == 0x3B:  # RTI: restore CCR, B, A, X, Y, PC
            stacked_ccr = self._pull8()
            r.ccr = (stacked_ccr & ~X_MASK) | (stacked_ccr & r.ccr & X_MASK)
            self.irq_inhibit_instructions = 0
            r.b = self._pull8()
            r.a = self._pull8()
            r.x = self._pull16()
            r.y = self._pull16()
            r.pc = self._pull16()
        else:
            r.pc = pc
            raise UnknownInstruction(pc, op)
        self.instructions += 1
        return pc, op
