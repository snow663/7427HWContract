
"""
gm_hc11_pcm_emulator.py

Starter GM PCM / 68HC11 emulator shell for expanded multiplexed mode.

Design goals:
- Flat 64K address space (no fake banking)
- Expanded multiplexed bus model:
    Port B = A8..A15
    Port C = AD0..AD7 (address low during AS, data during E-high phase)
    AS = address strobe
    R/W = direction
- Internal RAM and register block relocatable by INIT
- Timer + SCI internal register stubs
- Execution trace, bus trace, memory watchpoints
- Common HC11 opcode subset implemented
- Unknown opcodes trap cleanly so you can extend on purpose

This is a practical starter, not a finished drop-in full-ISA simulator.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from collections import deque
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Callable, Deque, Dict, List, Optional, Set, Tuple


# ============================================================
# Exceptions
# ============================================================

class HC11EmulatorError(Exception):
    pass


class UnknownOpcode(HC11EmulatorError):
    def __init__(self, pc: int, opcode: int, prefix: Optional[int] = None):
        self.pc = pc & 0xFFFF
        self.opcode = opcode & 0xFF
        self.prefix = None if prefix is None else (prefix & 0xFF)
        if self.prefix is None:
            msg = f"Unknown opcode ${self.opcode:02X} at ${self.pc:04X}"
        else:
            msg = f"Unknown opcode prefix ${self.prefix:02X} ${self.opcode:02X} at ${self.pc:04X}"
        super().__init__(msg)


# ============================================================
# Helpers
# ============================================================

def u8(v: int) -> int:
    return v & 0xFF


def u16(v: int) -> int:
    return v & 0xFFFF


def s8(v: int) -> int:
    v &= 0xFF
    return v - 0x100 if v & 0x80 else v


def s16(v: int) -> int:
    v &= 0xFFFF
    return v - 0x10000 if v & 0x8000 else v


def hi(v: int) -> int:
    return (v >> 8) & 0xFF


def lo(v: int) -> int:
    return v & 0xFF


# ============================================================
# Bus / trace
# ============================================================

@dataclass
class BusEvent:
    cycle: int
    address: int
    data: int
    rw: str                    # "R" or "W"
    internal: bool
    pb_high_addr: int          # Port B output
    pc_low_addr: int           # Port C during address phase
    pc_data: int               # Port C during data phase
    as_asserted: bool = True   # address strobe asserted for address phase
    e_high: bool = True        # E clock high during data phase
    note: str = ""


@dataclass
class ExecTraceEntry:
    cycle: int
    pc: int
    opcode: int
    prefix: Optional[int]
    a: int
    b: int
    x: int
    y: int
    sp: int
    ccr: int
    text: str = ""


# ============================================================
# CPU state
# ============================================================

@dataclass
class CPUState:
    a: int = 0
    b: int = 0
    x: int = 0
    y: int = 0
    sp: int = 0x00FF
    pc: int = 0
    ccr: int = 0xD0  # X, S bits vary by part; reasonable reset-ish default

    @property
    def d(self) -> int:
        return ((self.a & 0xFF) << 8) | (self.b & 0xFF)

    @d.setter
    def d(self, value: int) -> None:
        value &= 0xFFFF
        self.a = (value >> 8) & 0xFF
        self.b = value & 0xFF


# CCR bits
CCR_S = 0x80
CCR_X = 0x40
CCR_H = 0x20
CCR_I = 0x10
CCR_N = 0x08
CCR_Z = 0x04
CCR_V = 0x02
CCR_C = 0x01


# ============================================================
# Internal peripheral stubs
# ============================================================

class TimerStub:
    """
    Minimal free-running timer model.
    Exposes TCNT as register_base + 0x0E / 0x0F.
    """
    def __init__(self) -> None:
        self.counter = 0

    def tick(self, cycles: int) -> None:
        self.counter = (self.counter + max(1, cycles)) & 0xFFFF

    def read(self, offset: int) -> int:
        if offset == 0x0E:
            return hi(self.counter)
        if offset == 0x0F:
            return lo(self.counter)
        return 0x00

    def write(self, offset: int, value: int) -> bool:
        # Mostly read-only in this stub
        return False


class SCIStub:
    """
    Minimal SCI model.
    BAUD  = reg+0x2B
    SCCR1 = reg+0x2C
    SCCR2 = reg+0x2D
    SCSR  = reg+0x2E
    SCDR  = reg+0x2F
    """
    SCSR_TDRE = 0x80
    SCSR_TC   = 0x40
    SCSR_RDRF = 0x20

    def __init__(self) -> None:
        self.baud = 0x00
        self.sccr1 = 0x00
        self.sccr2 = 0x00
        self.tx_log: List[int] = []
        self.rx_fifo: Deque[int] = deque()

    def push_rx_byte(self, value: int) -> None:
        self.rx_fifo.append(u8(value))

    def read(self, offset: int) -> int:
        if offset == 0x2B:
            return self.baud
        if offset == 0x2C:
            return self.sccr1
        if offset == 0x2D:
            return self.sccr2
        if offset == 0x2E:
            status = self.SCSR_TDRE | self.SCSR_TC
            if self.rx_fifo:
                status |= self.SCSR_RDRF
            return status
        if offset == 0x2F:
            if self.rx_fifo:
                return self.rx_fifo.popleft()
            return 0x00
        return 0x00

    def write(self, offset: int, value: int) -> bool:
        value &= 0xFF
        if offset == 0x2B:
            self.baud = value
            return True
        if offset == 0x2C:
            self.sccr1 = value
            return True
        if offset == 0x2D:
            self.sccr2 = value
            return True
        if offset == 0x2F:
            self.tx_log.append(value)
            return True
        return False

    def tx_ascii(self) -> str:
        return "".join(chr(b) if 32 <= b <= 126 else "." for b in self.tx_log)


# ============================================================
# Memory / bus shell
# ============================================================

class HC11Memory:
    """
    Flat 64K memory map with internal RAM/register overlay and expanded-bus logging.
    """
    def __init__(self) -> None:
        self.mem = bytearray(0x10000)
        self.internal_ram = bytearray(512)
        self.internal_regs = bytearray(64)

        # INIT default after reset:
        # RAM nibble = 0x0 -> $0000
        # REG nibble = 0x1 -> $1000
        self.init_value = 0x01
        self.ram_base = 0x0000
        self.reg_base = 0x1000
        self.init_locked = False

        self.config_value = 0x03  # ROMON+EEON default-ish placeholder
        self.timer = TimerStub()
        self.sci = SCIStub()

        self.bus_trace: List[BusEvent] = []
        self.watch_reads: Set[int] = set()
        self.watch_writes: Set[int] = set()
        self.watch_log: List[str] = []
        self.cycle_counter = 0

    # --------------------------
    # Configuration / load
    # --------------------------

    def reset(self) -> None:
        self.bus_trace.clear()
        self.watch_log.clear()
        self.cycle_counter = 0

        self.init_value = 0x01
        self.ram_base = 0x0000
        self.reg_base = 0x1000
        self.init_locked = False

        self.timer = TimerStub()
        self.sci = SCIStub()

    def load_bin(self, data: bytes, base: int = 0x0000) -> None:
        base &= 0xFFFF
        if base + len(data) > 0x10000:
            raise ValueError("BIN does not fit in 64K map at requested base")
        self.mem[base:base + len(data)] = data

    # --------------------------
    # Internal mapping helpers
    # --------------------------

    def _map_init(self, value: int) -> None:
        value &= 0xFF
        self.init_value = value
        self.ram_base = ((value >> 4) & 0x0F) << 12
        self.reg_base = (value & 0x0F) << 12

    def _is_internal_reg(self, addr: int) -> bool:
        addr &= 0xFFFF
        return self.reg_base <= addr < self.reg_base + 64

    def _is_internal_ram(self, addr: int) -> bool:
        addr &= 0xFFFF
        if not (self.ram_base <= addr < self.ram_base + len(self.internal_ram)):
            return False

        # If RAM and regs overlap on same 4K page, registers win over first 64 bytes.
        if (self.ram_base & 0xF000) == (self.reg_base & 0xF000):
            reg_lo = self.reg_base
            reg_hi = self.reg_base + 64
            if reg_lo <= addr < reg_hi:
                return False
        return True

    def _is_internal(self, addr: int) -> bool:
        return self._is_internal_reg(addr) or self._is_internal_ram(addr)

    def _bus_log(self, addr: int, data: int, rw: str, note: str = "") -> None:
        addr &= 0xFFFF
        data &= 0xFF
        self.bus_trace.append(
            BusEvent(
                cycle=self.cycle_counter,
                address=addr,
                data=data,
                rw=rw,
                internal=self._is_internal(addr),
                pb_high_addr=(addr >> 8) & 0xFF,
                pc_low_addr=addr & 0xFF,
                pc_data=data & 0xFF,
                as_asserted=True,
                e_high=True,
                note=note,
            )
        )

    def _watch(self, addr: int, rw: str, value: int) -> None:
        if rw == "R" and addr in self.watch_reads:
            self.watch_log.append(f"[R] ${addr:04X} -> ${value:02X}")
        elif rw == "W" and addr in self.watch_writes:
            self.watch_log.append(f"[W] ${addr:04X} <- ${value:02X}")

    # --------------------------
    # Read/write
    # --------------------------

    def read8(self, addr: int) -> int:
        addr &= 0xFFFF

        if self._is_internal_reg(addr):
            off = addr - self.reg_base

            if off == 0x0E or off == 0x0F:
                value = self.timer.read(off)
            elif 0x2B <= off <= 0x2F:
                value = self.sci.read(off)
            elif off == 0x3D:
                value = self.init_value
            elif off == 0x3F:
                value = self.config_value
            else:
                value = self.internal_regs[off]

            self._bus_log(addr, value, "R", note="internal-reg")
            self._watch(addr, "R", value)
            return value

        if self._is_internal_ram(addr):
            value = self.internal_ram[addr - self.ram_base]
            self._bus_log(addr, value, "R", note="internal-ram")
            self._watch(addr, "R", value)
            return value

        value = self.mem[addr]
        self._bus_log(addr, value, "R", note="external")
        self._watch(addr, "R", value)
        return value

    def write8(self, addr: int, value: int) -> None:
        addr &= 0xFFFF
        value &= 0xFF

        if self._is_internal_reg(addr):
            off = addr - self.reg_base

            handled = False
            if off == 0x0E or off == 0x0F:
                handled = self.timer.write(off, value)
            elif 0x2B <= off <= 0x2F:
                handled = self.sci.write(off, value)
            elif off == 0x3D:
                if not self.init_locked:
                    self._map_init(value)
                    self.init_locked = True
                handled = True
            elif off == 0x3F:
                self.config_value = value
                handled = True

            if not handled:
                self.internal_regs[off] = value

            self._bus_log(addr, value, "W", note="internal-reg")
            self._watch(addr, "W", value)
            return

        if self._is_internal_ram(addr):
            self.internal_ram[addr - self.ram_base] = value
            self._bus_log(addr, value, "W", note="internal-ram")
            self._watch(addr, "W", value)
            return

        self.mem[addr] = value
        self._bus_log(addr, value, "W", note="external")
        self._watch(addr, "W", value)

    def read16(self, addr: int) -> int:
        hi_b = self.read8(addr)
        lo_b = self.read8((addr + 1) & 0xFFFF)
        return (hi_b << 8) | lo_b

    def write16(self, addr: int, value: int) -> None:
        self.write8(addr, hi(value))
        self.write8((addr + 1) & 0xFFFF, lo(value))

    def add_watch_read(self, addr: int) -> None:
        self.watch_reads.add(addr & 0xFFFF)

    def add_watch_write(self, addr: int) -> None:
        self.watch_writes.add(addr & 0xFFFF)

    def tick(self, cycles: int) -> None:
        self.cycle_counter += max(1, cycles)
        self.timer.tick(max(1, cycles))


# ============================================================
# CPU core
# ============================================================

class HC11CPU:
    def __init__(self, memory: HC11Memory):
        self.mem = memory
        self.s = CPUState()
        self.exec_trace: List[ExecTraceEntry] = []
        self.halted = False
        self.waiting = False
        self.max_trace = 100000

    # --------------------------
    # Reset
    # --------------------------

    def reset(self) -> None:
        self.mem.reset()
        self.s = CPUState()
        # Expanded mode commonly fetches reset vector from external space
        self.s.pc = self.mem.read16(0xFFFE)
        self.halted = False
        self.waiting = False
        self.exec_trace.clear()

    def interrupt(self, vector_address: int, maskable: bool = True) -> bool:
        """Enter an HC11 interrupt at an instruction boundary."""
        if maskable and self._get_flag(CCR_I):
            return False
        interrupted_pc = self.s.pc
        if not self.waiting:
            self._push16(self.s.pc)
            self._push16(self.s.y)
            self._push16(self.s.x)
            self._push8(self.s.a)
            self._push8(self.s.b)
            self._push8(self.s.ccr)
        self.waiting = False
        self._set_flag(CCR_I, True)
        self.s.pc = self.mem.read16(vector_address & 0xFFFF)
        self.mem.tick(12)
        self._trace(interrupted_pc, 0x00, None, f"INT ${vector_address & 0xFFFF:04X}")
        return True

    # --------------------------
    # Flag helpers
    # --------------------------

    def _set_flag(self, mask: int, state: bool) -> None:
        if state:
            self.s.ccr |= mask
        else:
            self.s.ccr &= ~mask

    def _get_flag(self, mask: int) -> bool:
        return bool(self.s.ccr & mask)

    def _nz8(self, v: int) -> int:
        v &= 0xFF
        self._set_flag(CCR_N, bool(v & 0x80))
        self._set_flag(CCR_Z, v == 0)
        return v

    def _nz16(self, v: int) -> int:
        v &= 0xFFFF
        self._set_flag(CCR_N, bool(v & 0x8000))
        self._set_flag(CCR_Z, v == 0)
        return v

    def _logic8(self, v: int) -> int:
        v &= 0xFF
        self._set_flag(CCR_V, False)
        return self._nz8(v)

    def _logic16(self, v: int) -> int:
        v &= 0xFFFF
        self._set_flag(CCR_V, False)
        return self._nz16(v)

    def _add8(self, a: int, b: int, carry_in: int = 0) -> int:
        a &= 0xFF
        b &= 0xFF
        carry_in &= 1
        res = a + b + carry_in
        out = res & 0xFF
        self._set_flag(CCR_C, res > 0xFF)
        self._set_flag(CCR_H, ((a & 0x0F) + (b & 0x0F) + carry_in) > 0x0F)
        self._set_flag(CCR_V, bool((~(a ^ b) & (a ^ out)) & 0x80))
        return self._nz8(out)

    def _sub8(self, a: int, b: int, borrow_in: int = 0) -> int:
        a &= 0xFF
        b &= 0xFF
        borrow_in &= 1
        res = a - b - borrow_in
        out = res & 0xFF
        self._set_flag(CCR_C, res < 0)
        self._set_flag(CCR_V, bool(((a ^ b) & (a ^ out)) & 0x80))
        return self._nz8(out)

    def _add16(self, a: int, b: int) -> int:
        a &= 0xFFFF
        b &= 0xFFFF
        res = a + b
        out = res & 0xFFFF
        self._set_flag(CCR_C, res > 0xFFFF)
        self._set_flag(CCR_V, bool((~(a ^ b) & (a ^ out)) & 0x8000))
        return self._nz16(out)

    def _sub16(self, a: int, b: int) -> int:
        a &= 0xFFFF
        b &= 0xFFFF
        res = a - b
        out = res & 0xFFFF
        self._set_flag(CCR_C, res < 0)
        self._set_flag(CCR_V, bool(((a ^ b) & (a ^ out)) & 0x8000))
        return self._nz16(out)

    # --------------------------
    # Stack helpers
    # HC11 stack grows downward
    # --------------------------

    def _push8(self, v: int) -> None:
        self.mem.write8(self.s.sp, v)
        self.s.sp = (self.s.sp - 1) & 0xFFFF

    def _pull8(self) -> int:
        self.s.sp = (self.s.sp + 1) & 0xFFFF
        return self.mem.read8(self.s.sp)

    def _push16(self, v: int) -> None:
        self._push8(lo(v))
        self._push8(hi(v))

    def _pull16(self) -> int:
        hi_b = self._pull8()
        lo_b = self._pull8()
        return ((hi_b & 0xFF) << 8) | (lo_b & 0xFF)

    # --------------------------
    # Fetch helpers
    # --------------------------

    def _fetch8(self) -> int:
        v = self.mem.read8(self.s.pc)
        self.s.pc = (self.s.pc + 1) & 0xFFFF
        return v

    def _fetch16(self) -> int:
        hi_b = self._fetch8()
        lo_b = self._fetch8()
        return (hi_b << 8) | lo_b

    def _direct(self) -> int:
        return self._fetch8()

    def _extended(self) -> int:
        return self._fetch16()

    def _indexed(self, base: int) -> int:
        off = s8(self._fetch8())
        return (base + off) & 0xFFFF

    # --------------------------
    # Branch helpers
    # --------------------------

    def _branch(self, take: bool) -> None:
        rel = s8(self._fetch8())
        if take:
            self.s.pc = (self.s.pc + rel) & 0xFFFF

    def _cond_hi(self) -> bool:
        return (not self._get_flag(CCR_C)) and (not self._get_flag(CCR_Z))

    def _cond_ls(self) -> bool:
        return self._get_flag(CCR_C) or self._get_flag(CCR_Z)

    def _cond_ge(self) -> bool:
        return self._get_flag(CCR_N) == self._get_flag(CCR_V)

    def _cond_lt(self) -> bool:
        return self._get_flag(CCR_N) != self._get_flag(CCR_V)

    def _cond_gt(self) -> bool:
        return (not self._get_flag(CCR_Z)) and self._cond_ge()

    def _cond_le(self) -> bool:
        return self._get_flag(CCR_Z) or self._cond_lt()

    # --------------------------
    # Trace
    # --------------------------

    def _trace(self, pc: int, opcode: int, prefix: Optional[int], text: str = "") -> None:
        if len(self.exec_trace) < self.max_trace:
            self.exec_trace.append(
                ExecTraceEntry(
                    cycle=self.mem.cycle_counter,
                    pc=pc,
                    opcode=opcode,
                    prefix=prefix,
                    a=self.s.a,
                    b=self.s.b,
                    x=self.s.x,
                    y=self.s.y,
                    sp=self.s.sp,
                    ccr=self.s.ccr,
                    text=text,
                )
            )

    # --------------------------
    # Bit-manipulation direct opcodes
    # --------------------------

    def _op_brset(self) -> None:
        direct = self._fetch8()
        mask = self._fetch8()
        rel = s8(self._fetch8())
        value = self.mem.read8(direct)
        if value & mask:
            self.s.pc = (self.s.pc + rel) & 0xFFFF

    def _op_brclr(self) -> None:
        direct = self._fetch8()
        mask = self._fetch8()
        rel = s8(self._fetch8())
        value = self.mem.read8(direct)
        if (value & mask) == 0:
            self.s.pc = (self.s.pc + rel) & 0xFFFF

    def _op_bset(self) -> None:
        direct = self._fetch8()
        mask = self._fetch8()
        value = self.mem.read8(direct)
        self.mem.write8(direct, value | mask)
        self._logic8(value | mask)

    def _op_bclr(self) -> None:
        direct = self._fetch8()
        mask = self._fetch8()
        value = self.mem.read8(direct)
        out = value & (~mask & 0xFF)
        self.mem.write8(direct, out)
        self._logic8(out)

    # --------------------------
    # Single-byte accumulator/memory ops
    # --------------------------

    def _neg8(self, v: int) -> int:
        out = (-v) & 0xFF
        self._set_flag(CCR_C, v != 0)
        self._set_flag(CCR_V, v == 0x80)
        return self._nz8(out)

    def _com8(self, v: int) -> int:
        out = (~v) & 0xFF
        self._set_flag(CCR_C, True)
        self._set_flag(CCR_V, False)
        return self._nz8(out)

    def _lsr8(self, v: int) -> int:
        self._set_flag(CCR_C, bool(v & 0x01))
        out = (v >> 1) & 0x7F
        self._set_flag(CCR_N, False)
        self._set_flag(CCR_Z, out == 0)
        self._set_flag(CCR_V, self._get_flag(CCR_N) ^ self._get_flag(CCR_C))
        return out

    def _ror8(self, v: int) -> int:
        c = 1 if self._get_flag(CCR_C) else 0
        new_c = v & 0x01
        out = ((v >> 1) | (c << 7)) & 0xFF
        self._set_flag(CCR_C, bool(new_c))
        self._set_flag(CCR_N, bool(out & 0x80))
        self._set_flag(CCR_Z, out == 0)
        self._set_flag(CCR_V, self._get_flag(CCR_N) ^ self._get_flag(CCR_C))
        return out

    def _asr8(self, v: int) -> int:
        new_c = v & 0x01
        out = ((v >> 1) | (v & 0x80)) & 0xFF
        self._set_flag(CCR_C, bool(new_c))
        self._set_flag(CCR_N, bool(out & 0x80))
        self._set_flag(CCR_Z, out == 0)
        self._set_flag(CCR_V, self._get_flag(CCR_N) ^ self._get_flag(CCR_C))
        return out

    def _asl8(self, v: int) -> int:
        out = (v << 1) & 0xFF
        self._set_flag(CCR_C, bool(v & 0x80))
        self._set_flag(CCR_N, bool(out & 0x80))
        self._set_flag(CCR_Z, out == 0)
        self._set_flag(CCR_V, self._get_flag(CCR_N) ^ self._get_flag(CCR_C))
        return out

    def _rol8(self, v: int) -> int:
        c = 1 if self._get_flag(CCR_C) else 0
        new_c = bool(v & 0x80)
        out = ((v << 1) | c) & 0xFF
        self._set_flag(CCR_C, new_c)
        self._set_flag(CCR_N, bool(out & 0x80))
        self._set_flag(CCR_Z, out == 0)
        self._set_flag(CCR_V, self._get_flag(CCR_N) ^ self._get_flag(CCR_C))
        return out

    def _inc8(self, v: int) -> int:
        out = (v + 1) & 0xFF
        self._set_flag(CCR_V, v == 0x7F)
        return self._nz8(out)

    def _dec8(self, v: int) -> int:
        out = (v - 1) & 0xFF
        self._set_flag(CCR_V, v == 0x80)
        return self._nz8(out)

    # --------------------------
    # Operand helpers (X or Y indexed)
    # --------------------------

    def _idx_base(self, use_y: bool) -> int:
        return self.s.y if use_y else self.s.x

    # --------------------------
    # Step
    # --------------------------

    def step(self) -> int:
        if self.halted or self.waiting:
            return 0

        start_pc = self.s.pc
        prefix = None
        opcode = self._fetch8()

        use_y_index = False
        if opcode in {0x18, 0x1A, 0xCD}:
            prefix = opcode
            opcode = self._fetch8()
            use_y_index = prefix in {0x18, 0xCD}

        # ---- bit direct ----
        if prefix is None and opcode == 0x12:
            self._op_brset()
            self.mem.tick(6)
            self._trace(start_pc, opcode, prefix, "BRSET")
            return 6
        if prefix is None and opcode == 0x13:
            self._op_brclr()
            self.mem.tick(6)
            self._trace(start_pc, opcode, prefix, "BRCLR")
            return 6
        if prefix is None and opcode == 0x14:
            self._op_bset()
            self.mem.tick(6)
            self._trace(start_pc, opcode, prefix, "BSET")
            return 6
        if prefix is None and opcode == 0x15:
            self._op_bclr()
            self.mem.tick(6)
            self._trace(start_pc, opcode, prefix, "BCLR")
            return 6
        if opcode in {0x1C, 0x1D, 0x1E, 0x1F} and prefix in {None, 0x18}:
            address = self._indexed(self.s.y if prefix == 0x18 else self.s.x)
            mask = self._fetch8()
            value = self.mem.read8(address)
            if opcode == 0x1C:  # BSET indexed
                self.mem.write8(address, value | mask)
                name = "BSET"
            elif opcode == 0x1D:  # BCLR indexed
                self.mem.write8(address, value & (~mask & 0xFF))
                name = "BCLR"
            else:
                relative = s8(self._fetch8())
                take = (value & mask) != 0 if opcode == 0x1E else (value & mask) == 0
                if take:
                    self.s.pc = u16(self.s.pc + relative)
                name = "BRSET" if opcode == 0x1E else "BRCLR"
            cycles = 7 if opcode in {0x1C, 0x1D} else 8
            self.mem.tick(cycles)
            self._trace(start_pc, opcode, prefix, name)
            return cycles

        # ---- inherent / control ----
        if prefix is None and opcode == 0x01:  # NOP
            self.mem.tick(2)
            self._trace(start_pc, opcode, prefix, "NOP")
            return 2
        if prefix is None and opcode == 0x02:  # IDIV
            divisor = self.s.x & 0xFFFF
            if divisor == 0:
                self.s.x = 0xFFFF
                self._set_flag(CCR_C, True)
            else:
                numerator = self.s.d
                self.s.x = numerator // divisor
                self.s.d = numerator % divisor
                self._set_flag(CCR_C, False)
            self._set_flag(CCR_Z, self.s.x == 0)
            self.mem.tick(41)
            self._trace(start_pc, opcode, prefix, "IDIV")
            return 41
        if prefix is None and opcode == 0x03:  # FDIV
            divisor = self.s.x & 0xFFFF
            numerator = self.s.d
            if divisor == 0:
                self.s.x = 0xFFFF
                self._set_flag(CCR_C, True)
            elif numerator >= divisor:
                self.s.x = 0xFFFF
                self.s.d = (numerator - divisor) & 0xFFFF
                self._set_flag(CCR_V, True)
                self._set_flag(CCR_C, False)
            else:
                expanded = numerator << 16
                self.s.x = (expanded // divisor) & 0xFFFF
                self.s.d = expanded % divisor
                self._set_flag(CCR_V, False)
                self._set_flag(CCR_C, False)
            self._set_flag(CCR_Z, self.s.x == 0)
            self.mem.tick(41)
            self._trace(start_pc, opcode, prefix, "FDIV")
            return 41
        if prefix is None and opcode == 0x04:  # LSRD
            old = self.s.d
            self.s.d = old >> 1
            self._set_flag(CCR_C, bool(old & 1))
            self._set_flag(CCR_N, False)
            self._set_flag(CCR_Z, self.s.d == 0)
            self._set_flag(CCR_V, self._get_flag(CCR_C))
            self.mem.tick(3)
            self._trace(start_pc, opcode, prefix, "LSRD")
            return 3
        if prefix is None and opcode == 0x05:  # ASLD
            old = self.s.d
            self.s.d = u16(old << 1)
            self._set_flag(CCR_C, bool(old & 0x8000))
            self._set_flag(CCR_N, bool(self.s.d & 0x8000))
            self._set_flag(CCR_Z, self.s.d == 0)
            self._set_flag(CCR_V, self._get_flag(CCR_N) ^ self._get_flag(CCR_C))
            self.mem.tick(3)
            self._trace(start_pc, opcode, prefix, "ASLD")
            return 3
        if prefix is None and opcode == 0x06:  # TAP
            self.s.ccr = self.s.a & 0xFF
            self.mem.tick(2)
            self._trace(start_pc, opcode, prefix, "TAP")
            return 2
        if prefix is None and opcode == 0x07:  # TPA
            self.s.a = self.s.ccr & 0xFF
            self.mem.tick(2)
            self._trace(start_pc, opcode, prefix, "TPA")
            return 2
        if prefix is None and opcode == 0x08:  # INX
            self.s.x = self._nz16(self.s.x + 1)
            self.mem.tick(3)
            self._trace(start_pc, opcode, prefix, "INX")
            return 3
        if prefix == 0x18 and opcode == 0x08:  # INY
            self.s.y = self._nz16(self.s.y + 1)
            self.mem.tick(4)
            self._trace(start_pc, opcode, prefix, "INY")
            return 4
        if prefix is None and opcode == 0x09:  # DEX
            self.s.x = self._nz16(self.s.x - 1)
            self.mem.tick(3)
            self._trace(start_pc, opcode, prefix, "DEX")
            return 3
        if prefix == 0x18 and opcode == 0x09:  # DEY
            self.s.y = self._nz16(self.s.y - 1)
            self.mem.tick(4)
            self._trace(start_pc, opcode, prefix, "DEY")
            return 4
        if prefix is None and opcode == 0x0A:  # CLV
            self._set_flag(CCR_V, False)
            self.mem.tick(2)
            self._trace(start_pc, opcode, prefix, "CLV")
            return 2
        if prefix is None and opcode == 0x0B:  # SEV
            self._set_flag(CCR_V, True)
            self.mem.tick(2)
            self._trace(start_pc, opcode, prefix, "SEV")
            return 2
        if prefix is None and opcode == 0x0C:  # CLC
            self._set_flag(CCR_C, False)
            self.mem.tick(2)
            self._trace(start_pc, opcode, prefix, "CLC")
            return 2
        if prefix is None and opcode == 0x0D:  # SEC
            self._set_flag(CCR_C, True)
            self.mem.tick(2)
            self._trace(start_pc, opcode, prefix, "SEC")
            return 2
        if prefix is None and opcode == 0x0E:  # CLI
            self._set_flag(CCR_I, False)
            self.mem.tick(2)
            self._trace(start_pc, opcode, prefix, "CLI")
            return 2
        if prefix is None and opcode == 0x0F:  # SEI
            self._set_flag(CCR_I, True)
            self.mem.tick(2)
            self._trace(start_pc, opcode, prefix, "SEI")
            return 2
        if prefix is None and opcode == 0x10:  # SBA
            self.s.a = self._sub8(self.s.a, self.s.b)
            self.mem.tick(2)
            self._trace(start_pc, opcode, prefix, "SBA")
            return 2
        if prefix is None and opcode == 0x11:  # CBA
            self._sub8(self.s.a, self.s.b)
            self.mem.tick(2)
            self._trace(start_pc, opcode, prefix, "CBA")
            return 2
        if prefix is None and opcode == 0x16:  # TAB
            self.s.b = self._nz8(self.s.a)
            self._set_flag(CCR_V, False)
            self.mem.tick(2)
            self._trace(start_pc, opcode, prefix, "TAB")
            return 2
        if prefix is None and opcode == 0x17:  # TBA
            self.s.a = self._nz8(self.s.b)
            self._set_flag(CCR_V, False)
            self.mem.tick(2)
            self._trace(start_pc, opcode, prefix, "TBA")
            return 2
        if prefix is None and opcode == 0x18:
            raise UnknownOpcode(start_pc, opcode, None)
        if prefix is None and opcode == 0x1B:  # ABA
            self.s.a = self._add8(self.s.a, self.s.b)
            self.mem.tick(2)
            self._trace(start_pc, opcode, prefix, "ABA")
            return 2

        # ---- branches ----
        if prefix is None and opcode == 0x20:
            self._branch(True)
            self.mem.tick(3)
            self._trace(start_pc, opcode, prefix, "BRA")
            return 3
        if prefix is None and opcode == 0x22:
            self._branch(self._cond_hi())
            self.mem.tick(3)
            self._trace(start_pc, opcode, prefix, "BHI")
            return 3
        if prefix is None and opcode == 0x23:
            self._branch(self._cond_ls())
            self.mem.tick(3)
            self._trace(start_pc, opcode, prefix, "BLS")
            return 3
        if prefix is None and opcode == 0x24:
            self._branch(not self._get_flag(CCR_C))
            self.mem.tick(3)
            self._trace(start_pc, opcode, prefix, "BCC")
            return 3
        if prefix is None and opcode == 0x25:
            self._branch(self._get_flag(CCR_C))
            self.mem.tick(3)
            self._trace(start_pc, opcode, prefix, "BCS")
            return 3
        if prefix is None and opcode == 0x26:
            self._branch(not self._get_flag(CCR_Z))
            self.mem.tick(3)
            self._trace(start_pc, opcode, prefix, "BNE")
            return 3
        if prefix is None and opcode == 0x27:
            self._branch(self._get_flag(CCR_Z))
            self.mem.tick(3)
            self._trace(start_pc, opcode, prefix, "BEQ")
            return 3
        if prefix is None and opcode == 0x28:
            self._branch(not self._get_flag(CCR_V))
            self.mem.tick(3)
            self._trace(start_pc, opcode, prefix, "BVC")
            return 3
        if prefix is None and opcode == 0x29:
            self._branch(self._get_flag(CCR_V))
            self.mem.tick(3)
            self._trace(start_pc, opcode, prefix, "BVS")
            return 3
        if prefix is None and opcode == 0x2A:
            self._branch(not self._get_flag(CCR_N))
            self.mem.tick(3)
            self._trace(start_pc, opcode, prefix, "BPL")
            return 3
        if prefix is None and opcode == 0x2B:
            self._branch(self._get_flag(CCR_N))
            self.mem.tick(3)
            self._trace(start_pc, opcode, prefix, "BMI")
            return 3
        if prefix is None and opcode == 0x2C:
            self._branch(self._cond_ge())
            self.mem.tick(3)
            self._trace(start_pc, opcode, prefix, "BGE")
            return 3
        if prefix is None and opcode == 0x2D:
            self._branch(self._cond_lt())
            self.mem.tick(3)
            self._trace(start_pc, opcode, prefix, "BLT")
            return 3
        if prefix is None and opcode == 0x2E:
            self._branch(self._cond_gt())
            self.mem.tick(3)
            self._trace(start_pc, opcode, prefix, "BGT")
            return 3
        if prefix is None and opcode == 0x2F:
            self._branch(self._cond_le())
            self.mem.tick(3)
            self._trace(start_pc, opcode, prefix, "BLE")
            return 3

        # ---- stack / transfers ----
        if prefix is None and opcode == 0x30:  # TSX
            self.s.x = self._nz16((self.s.sp + 1) & 0xFFFF)
            self.mem.tick(3)
            self._trace(start_pc, opcode, prefix, "TSX")
            return 3
        if prefix == 0x18 and opcode == 0x30:  # TSY
            self.s.y = self._nz16((self.s.sp + 1) & 0xFFFF)
            self.mem.tick(4)
            self._trace(start_pc, opcode, prefix, "TSY")
            return 4
        if prefix is None and opcode == 0x31:  # INS
            self.s.sp = (self.s.sp + 1) & 0xFFFF
            self.mem.tick(3)
            self._trace(start_pc, opcode, prefix, "INS")
            return 3
        if prefix is None and opcode == 0x32:  # PULA
            self.s.a = self._logic8(self._pull8())
            self.mem.tick(4)
            self._trace(start_pc, opcode, prefix, "PULA")
            return 4
        if prefix is None and opcode == 0x33:  # PULB
            self.s.b = self._logic8(self._pull8())
            self.mem.tick(4)
            self._trace(start_pc, opcode, prefix, "PULB")
            return 4
        if prefix is None and opcode == 0x34:  # DES
            self.s.sp = (self.s.sp - 1) & 0xFFFF
            self.mem.tick(3)
            self._trace(start_pc, opcode, prefix, "DES")
            return 3
        if prefix is None and opcode == 0x35:  # TXS
            self.s.sp = (self.s.x - 1) & 0xFFFF
            self.mem.tick(3)
            self._trace(start_pc, opcode, prefix, "TXS")
            return 3
        if prefix == 0x18 and opcode == 0x35:  # TYS
            self.s.sp = (self.s.y - 1) & 0xFFFF
            self.mem.tick(4)
            self._trace(start_pc, opcode, prefix, "TYS")
            return 4
        if prefix is None and opcode == 0x36:  # PSHA
            self._push8(self.s.a)
            self.mem.tick(3)
            self._trace(start_pc, opcode, prefix, "PSHA")
            return 3
        if prefix is None and opcode == 0x37:  # PSHB
            self._push8(self.s.b)
            self.mem.tick(3)
            self._trace(start_pc, opcode, prefix, "PSHB")
            return 3
        if prefix is None and opcode == 0x38:  # PULX
            self.s.x = self._logic16(self._pull16())
            self.mem.tick(5)
            self._trace(start_pc, opcode, prefix, "PULX")
            return 5
        if prefix == 0x18 and opcode == 0x38:  # PULY
            self.s.y = self._logic16(self._pull16())
            self.mem.tick(6)
            self._trace(start_pc, opcode, prefix, "PULY")
            return 6
        if prefix is None and opcode == 0x39:  # RTS
            self.s.pc = self._pull16()
            self.mem.tick(5)
            self._trace(start_pc, opcode, prefix, "RTS")
            return 5
        if prefix is None and opcode == 0x3A:  # ABX
            self.s.x = u16(self.s.x + self.s.b)
            self.mem.tick(3)
            self._trace(start_pc, opcode, prefix, "ABX")
            return 3
        if prefix == 0x18 and opcode == 0x3A:  # ABY
            self.s.y = u16(self.s.y + self.s.b)
            self.mem.tick(4)
            self._trace(start_pc, opcode, prefix, "ABY")
            return 4
        if prefix is None and opcode == 0x3B:  # RTI
            self.s.ccr = self._pull8()
            self.s.b = self._pull8()
            self.s.a = self._pull8()
            self.s.x = self._pull16()
            self.s.y = self._pull16()
            self.s.pc = self._pull16()
            self.mem.tick(12)
            self._trace(start_pc, opcode, prefix, "RTI")
            return 12
        if prefix is None and opcode == 0x3C:  # PSHX
            self._push16(self.s.x)
            self.mem.tick(4)
            self._trace(start_pc, opcode, prefix, "PSHX")
            return 4
        if prefix == 0x18 and opcode == 0x3C:  # PSHY
            self._push16(self.s.y)
            self.mem.tick(5)
            self._trace(start_pc, opcode, prefix, "PSHY")
            return 5
        if prefix is None and opcode == 0x3D:  # MUL
            product = (self.s.a & 0xFF) * (self.s.b & 0xFF)
            self.s.d = product
            self._set_flag(CCR_C, bool(product & 0x8000))
            self.mem.tick(10)
            self._trace(start_pc, opcode, prefix, "MUL")
            return 10
        if prefix is None and opcode == 0x3E:  # WAI
            self._push16(self.s.pc)
            self._push16(self.s.y)
            self._push16(self.s.x)
            self._push8(self.s.a)
            self._push8(self.s.b)
            self._push8(self.s.ccr)
            self.waiting = True
            self.mem.tick(14)
            self._trace(start_pc, opcode, prefix, "WAI")
            return 14
        if prefix is None and opcode == 0x3F:  # SWI
            self._push16(self.s.pc)
            self._push16(self.s.y)
            self._push16(self.s.x)
            self._push8(self.s.a)
            self._push8(self.s.b)
            self._push8(self.s.ccr)
            self._set_flag(CCR_I, True)
            self.s.pc = self.mem.read16(0xFFF6)
            self.mem.tick(14)
            self._trace(start_pc, opcode, prefix, "SWI")
            return 14

        # ---- accumulator A inherent ----
        if prefix is None and opcode == 0x40:
            self.s.a = self._neg8(self.s.a)
            self.mem.tick(2); self._trace(start_pc, opcode, prefix, "NEGA"); return 2
        if prefix is None and opcode == 0x43:
            self.s.a = self._com8(self.s.a)
            self.mem.tick(2); self._trace(start_pc, opcode, prefix, "COMA"); return 2
        if prefix is None and opcode == 0x44:
            self.s.a = self._lsr8(self.s.a)
            self.mem.tick(2); self._trace(start_pc, opcode, prefix, "LSRA"); return 2
        if prefix is None and opcode == 0x46:
            self.s.a = self._ror8(self.s.a)
            self.mem.tick(2); self._trace(start_pc, opcode, prefix, "RORA"); return 2
        if prefix is None and opcode == 0x47:
            self.s.a = self._asr8(self.s.a)
            self.mem.tick(2); self._trace(start_pc, opcode, prefix, "ASRA"); return 2
        if prefix is None and opcode == 0x48:
            self.s.a = self._asl8(self.s.a)
            self.mem.tick(2); self._trace(start_pc, opcode, prefix, "ASLA"); return 2
        if prefix is None and opcode == 0x49:
            self.s.a = self._rol8(self.s.a)
            self.mem.tick(2); self._trace(start_pc, opcode, prefix, "ROLA"); return 2
        if prefix is None and opcode == 0x4A:
            self.s.a = self._dec8(self.s.a)
            self.mem.tick(2); self._trace(start_pc, opcode, prefix, "DECA"); return 2
        if prefix is None and opcode == 0x4C:
            self.s.a = self._inc8(self.s.a)
            self.mem.tick(2); self._trace(start_pc, opcode, prefix, "INCA"); return 2
        if prefix is None and opcode == 0x4D:
            self._logic8(self.s.a)
            self.mem.tick(2); self._trace(start_pc, opcode, prefix, "TSTA"); return 2
        if prefix is None and opcode == 0x4F:
            self.s.a = 0
            self._logic8(self.s.a)
            self.mem.tick(2); self._trace(start_pc, opcode, prefix, "CLRA"); return 2

        # ---- accumulator B inherent ----
        if prefix is None and opcode == 0x50:
            self.s.b = self._neg8(self.s.b)
            self.mem.tick(2); self._trace(start_pc, opcode, prefix, "NEGB"); return 2
        if prefix is None and opcode == 0x53:
            self.s.b = self._com8(self.s.b)
            self.mem.tick(2); self._trace(start_pc, opcode, prefix, "COMB"); return 2
        if prefix is None and opcode == 0x54:
            self.s.b = self._lsr8(self.s.b)
            self.mem.tick(2); self._trace(start_pc, opcode, prefix, "LSRB"); return 2
        if prefix is None and opcode == 0x56:
            self.s.b = self._ror8(self.s.b)
            self.mem.tick(2); self._trace(start_pc, opcode, prefix, "RORB"); return 2
        if prefix is None and opcode == 0x57:
            self.s.b = self._asr8(self.s.b)
            self.mem.tick(2); self._trace(start_pc, opcode, prefix, "ASRB"); return 2
        if prefix is None and opcode == 0x58:
            self.s.b = self._asl8(self.s.b)
            self.mem.tick(2); self._trace(start_pc, opcode, prefix, "ASLB"); return 2
        if prefix is None and opcode == 0x59:
            self.s.b = self._rol8(self.s.b)
            self.mem.tick(2); self._trace(start_pc, opcode, prefix, "ROLB"); return 2
        if prefix is None and opcode == 0x5A:
            self.s.b = self._dec8(self.s.b)
            self.mem.tick(2); self._trace(start_pc, opcode, prefix, "DECB"); return 2
        if prefix is None and opcode == 0x5C:
            self.s.b = self._inc8(self.s.b)
            self.mem.tick(2); self._trace(start_pc, opcode, prefix, "INCB"); return 2
        if prefix is None and opcode == 0x5D:
            self._logic8(self.s.b)
            self.mem.tick(2); self._trace(start_pc, opcode, prefix, "TSTB"); return 2
        if prefix is None and opcode == 0x5F:
            self.s.b = 0
            self._logic8(self.s.b)
            self.mem.tick(2); self._trace(start_pc, opcode, prefix, "CLRB"); return 2

        # ---- memory shift / inc / dec / jmp / clr (indexed or ext) ----
        if (prefix is None or (prefix == 0x18 and opcode < 0x70)) and opcode in {0x60,0x63,0x64,0x66,0x67,0x68,0x69,0x6A,0x6C,0x6D,0x6E,0x6F,
                                         0x70,0x73,0x74,0x76,0x77,0x78,0x79,0x7A,0x7C,0x7D,0x7E,0x7F}:
            indexed = opcode < 0x70
            addr = self._indexed(self._idx_base(use_y_index)) if indexed else self._extended()
            base_op = opcode & 0x0F
            if base_op == 0x0E:  # JMP
                self.s.pc = addr
                self.mem.tick(3 if indexed else 3)
                self._trace(start_pc, opcode, prefix, "JMP")
                return 3
            value = self.mem.read8(addr)
            if base_op == 0x00:
                out = self._neg8(value)
            elif base_op == 0x03:
                out = self._com8(value)
            elif base_op == 0x04:
                out = self._lsr8(value)
            elif base_op == 0x06:
                out = self._ror8(value)
            elif base_op == 0x07:
                out = self._asr8(value)
            elif base_op == 0x08:
                out = self._asl8(value)
            elif base_op == 0x09:
                out = self._rol8(value)
            elif base_op == 0x0A:
                out = self._dec8(value)
            elif base_op == 0x0C:
                out = self._inc8(value)
            elif base_op == 0x0D:
                self._logic8(value)
                self.mem.tick(6 if indexed else 6)
                self._trace(start_pc, opcode, prefix, "TST")
                return 6
            elif base_op == 0x0F:
                out = 0
                self._logic8(out)
            else:
                raise UnknownOpcode(start_pc, opcode, prefix)
            self.mem.write8(addr, out)
            self.mem.tick(6 if indexed else 6)
            self._trace(start_pc, opcode, prefix, "MEMOP")
            return 6

        # ---- arithmetic/logical groups helper ----

        if opcode == 0x8F and prefix in {None, 0x18}:  # XGDX / XGDY
            old_d = self.s.d
            if use_y_index:
                self.s.d, self.s.y = self.s.y, old_d
                name = "XGDY"
                cycles = 4
            else:
                self.s.d, self.s.x = self.s.x, old_d
                name = "XGDX"
                cycles = 3
            self.mem.tick(cycles)
            self._trace(start_pc, opcode, prefix, name)
            return cycles
        def resolve_addr(mode_opcode: int) -> Tuple[str, int]:
            mode = mode_opcode >> 4
            if mode == 0x8 or mode == 0xC:
                return ("imm", self._fetch8())
            if mode == 0x9 or mode == 0xD:
                addr = self._direct()
                return ("mem", self.mem.read8(addr))
            if mode == 0xA or mode == 0xE:
                addr = self._indexed(self._idx_base(use_y_index))
                return ("mem", self.mem.read8(addr))
            if mode == 0xB or mode == 0xF:
                addr = self._extended()
                return ("mem", self.mem.read8(addr))
            raise UnknownOpcode(start_pc, opcode, prefix)

        # ---- A register immediate/direct/indexed/ext ----
        if opcode in {0x80,0x81,0x82,0x84,0x85,0x88,0x89,0x8A,0x8B,
                      0x90,0x91,0x92,0x94,0x95,0x98,0x99,0x9A,0x9B,
                      0xA0,0xA1,0xA2,0xA4,0xA5,0xA8,0xA9,0xAA,0xAB,
                      0xB0,0xB1,0xB2,0xB4,0xB5,0xB8,0xB9,0xBA,0xBB}:
            _, val = resolve_addr(opcode)
            low = opcode & 0x0F
            if low == 0x0:
                self.s.a = self._sub8(self.s.a, val)
                name = "SUBA"
            elif low == 0x1:
                self._sub8(self.s.a, val)
                name = "CMPA"
            elif low == 0x2:
                borrow = 1 if self._get_flag(CCR_C) else 0
                self.s.a = self._sub8(self.s.a, val, borrow)
                name = "SBCA"
            elif low == 0x4:
                self.s.a = self._logic8(self.s.a & val)
                name = "ANDA"
            elif low == 0x5:
                self._logic8(self.s.a & val)
                name = "BITA"
            elif low == 0x8:
                self.s.a = self._logic8(self.s.a ^ val)
                name = "EORA"
            elif low == 0x9:
                carry = 1 if self._get_flag(CCR_C) else 0
                self.s.a = self._add8(self.s.a, val, carry)
                name = "ADCA"
            elif low == 0xA:
                self.s.a = self._logic8(self.s.a | val)
                name = "ORAA"
            elif low == 0xB:
                self.s.a = self._add8(self.s.a, val)
                name = "ADDA"
            else:
                raise UnknownOpcode(start_pc, opcode, prefix)
            self.mem.tick(2 if opcode < 0x90 else 3 if opcode < 0xA0 else 4 if opcode < 0xB0 else 4)
            self._trace(start_pc, opcode, prefix, name)
            return 4

        # ---- B register immediate/direct/indexed/ext ----
        if opcode in {0xC0,0xC1,0xC2,0xC4,0xC5,0xC8,0xC9,0xCA,0xCB,
                      0xD0,0xD1,0xD2,0xD4,0xD5,0xD8,0xD9,0xDA,0xDB,
                      0xE0,0xE1,0xE2,0xE4,0xE5,0xE8,0xE9,0xEA,0xEB,
                      0xF0,0xF1,0xF2,0xF4,0xF5,0xF8,0xF9,0xFA,0xFB}:
            _, val = resolve_addr(opcode)
            low = opcode & 0x0F
            if low == 0x0:
                self.s.b = self._sub8(self.s.b, val)
                name = "SUBB"
            elif low == 0x1:
                self._sub8(self.s.b, val)
                name = "CMPB"
            elif low == 0x2:
                borrow = 1 if self._get_flag(CCR_C) else 0
                self.s.b = self._sub8(self.s.b, val, borrow)
                name = "SBCB"
            elif low == 0x4:
                self.s.b = self._logic8(self.s.b & val)
                name = "ANDB"
            elif low == 0x5:
                self._logic8(self.s.b & val)
                name = "BITB"
            elif low == 0x8:
                self.s.b = self._logic8(self.s.b ^ val)
                name = "EORB"
            elif low == 0x9:
                carry = 1 if self._get_flag(CCR_C) else 0
                self.s.b = self._add8(self.s.b, val, carry)
                name = "ADCB"
            elif low == 0xA:
                self.s.b = self._logic8(self.s.b | val)
                name = "ORAB"
            elif low == 0xB:
                self.s.b = self._add8(self.s.b, val)
                name = "ADDB"
            else:
                raise UnknownOpcode(start_pc, opcode, prefix)
            self.mem.tick(2 if opcode < 0xD0 else 3 if opcode < 0xE0 else 4 if opcode < 0xF0 else 4)
            self._trace(start_pc, opcode, prefix, name)
            return 4

        # ---- CPD page-3/page-4 ----
        if (prefix == 0x1A and opcode in {0x83,0x93,0xA3,0xB3}) or (prefix == 0xCD and opcode == 0xA3):
            if opcode == 0x83:
                val16 = self._fetch16()
            elif opcode == 0x93:
                val16 = self.mem.read16(self._direct())
            elif opcode == 0xA3:
                val16 = self.mem.read16(self._indexed(self.s.y if prefix == 0xCD else self.s.x))
            else:
                val16 = self.mem.read16(self._extended())
            self._sub16(self.s.d, val16)
            self.mem.tick(5)
            self._trace(start_pc, opcode, prefix, "CPD")
            return 5

        # ---- 16-bit ops LDD / ADDD / SUBD / CPX / CPY / LDS / LDX / LDY ----
        if opcode in {0x83,0x93,0xA3,0xB3,0xC3,0xD3,0xE3,0xF3,
                      0x8C,0x9C,0xAC,0xBC,0xCC,0xDC,0xEC,0xFC,
                      0x8E,0x9E,0xAE,0xBE,0xCE,0xDE,0xEE,0xFE,
                      0xDF,0xEF,0xFF,0x9F,0xAF,0xBF} or (prefix == 0x18 and opcode in {0x8C,0x9C,0xAC,0xBC,0xCE,0xDE,0xEE,0xFE,0xDF,0xEF,0xFF}):
            # 16-bit operand fetch
            def op16_fetch(opc: int) -> Tuple[Optional[int], Optional[int]]:
                if opc in {0x83,0xC3,0x8C,0xCC,0x8E,0xCE}:
                    return (None, self._fetch16())
                if opc in {0x93,0xD3,0x9C,0xDC,0x9E,0xDE,0xDF,0x9F}:
                    addr = self._direct()
                    return (addr, self.mem.read16(addr))
                if opc in {0xA3,0xE3,0xAC,0xEC,0xAE,0xEE,0xEF,0xAF}:
                    addr = self._indexed(self._idx_base(use_y_index))
                    return (addr, self.mem.read16(addr))
                if opc in {0xB3,0xF3,0xBC,0xFC,0xBE,0xFE,0xFF,0xBF}:
                    addr = self._extended()
                    return (addr, self.mem.read16(addr))
                raise UnknownOpcode(start_pc, opcode, prefix)

            addr, val16 = op16_fetch(opcode)

            if opcode in {0x83,0x93,0xA3,0xB3}:  # SUBD
                self.s.d = self._sub16(self.s.d, val16)
                self.mem.tick(4); self._trace(start_pc, opcode, prefix, "SUBD"); return 4
            if opcode in {0xC3,0xD3,0xE3,0xF3}:  # ADDD
                self.s.d = self._add16(self.s.d, val16)
                self.mem.tick(4); self._trace(start_pc, opcode, prefix, "ADDD"); return 4
            if opcode in {0xCC,0xDC,0xEC,0xFC}:  # LDD
                self.s.d = self._logic16(val16)
                self.mem.tick(4); self._trace(start_pc, opcode, prefix, "LDD"); return 4
            if opcode in {0x8C,0x9C,0xAC,0xBC}:  # CPX or CPY with prefix
                _ = self._sub16(self.s.y if prefix == 0x18 else self.s.x, val16)
                self.mem.tick(4); self._trace(start_pc, opcode, prefix, "CPY" if prefix == 0x18 else "CPX"); return 4
            if opcode in {0x8E,0x9E,0xAE,0xBE}:  # LDS
                self.s.sp = self._logic16(val16)
                self.mem.tick(4); self._trace(start_pc, opcode, prefix, "LDS"); return 4
            if opcode in {0xCE,0xDE,0xEE,0xFE}:  # LDX or LDY
                if prefix == 0x18:
                    self.s.y = self._logic16(val16)
                    name = "LDY"
                else:
                    self.s.x = self._logic16(val16)
                    name = "LDX"
                self.mem.tick(4); self._trace(start_pc, opcode, prefix, name); return 4
            if opcode in {0xDF,0xEF,0xFF}:      # STX or STY
                value = self.s.y if prefix == 0x18 else self.s.x
                if addr is None:
                    raise UnknownOpcode(start_pc, opcode, prefix)
                self.mem.write16(addr, value)
                self._logic16(value)
                self.mem.tick(5); self._trace(start_pc, opcode, prefix, "STY" if prefix == 0x18 else "STX"); return 5
            if opcode in {0x9F,0xAF,0xBF}:      # STS
                if addr is None:
                    raise UnknownOpcode(start_pc, opcode, prefix)
                self.mem.write16(addr, self.s.sp)
                self._logic16(self.s.sp)
                self.mem.tick(5); self._trace(start_pc, opcode, prefix, "STS"); return 5

        # ---- loads/stores A/B ----
        if opcode in {0x86,0x96,0xA6,0xB6,0x97,0xA7,0xB7,0xC6,0xD6,0xE6,0xF6,0xD7,0xE7,0xF7}:
            # Load/store A
            if opcode in {0x86,0x96,0xA6,0xB6}:
                if opcode == 0x86:
                    self.s.a = self._logic8(self._fetch8())
                elif opcode == 0x96:
                    self.s.a = self._logic8(self.mem.read8(self._direct()))
                elif opcode == 0xA6:
                    self.s.a = self._logic8(self.mem.read8(self._indexed(self._idx_base(use_y_index))))
                elif opcode == 0xB6:
                    self.s.a = self._logic8(self.mem.read8(self._extended()))
                self.mem.tick(2); self._trace(start_pc, opcode, prefix, "LDAA"); return 2

            if opcode in {0x97,0xA7,0xB7}:
                if opcode == 0x97:
                    addr = self._direct()
                elif opcode == 0xA7:
                    addr = self._indexed(self._idx_base(use_y_index))
                else:
                    addr = self._extended()
                self.mem.write8(addr, self.s.a)
                self._logic8(self.s.a)
                self.mem.tick(3); self._trace(start_pc, opcode, prefix, "STAA"); return 3

            if opcode in {0xC6,0xD6,0xE6,0xF6}:
                if opcode == 0xC6:
                    self.s.b = self._logic8(self._fetch8())
                elif opcode == 0xD6:
                    self.s.b = self._logic8(self.mem.read8(self._direct()))
                elif opcode == 0xE6:
                    self.s.b = self._logic8(self.mem.read8(self._indexed(self._idx_base(use_y_index))))
                else:
                    self.s.b = self._logic8(self.mem.read8(self._extended()))
                self.mem.tick(2); self._trace(start_pc, opcode, prefix, "LDAB"); return 2

            if opcode in {0xD7,0xE7,0xF7}:
                if opcode == 0xD7:
                    addr = self._direct()
                elif opcode == 0xE7:
                    addr = self._indexed(self._idx_base(use_y_index))
                else:
                    addr = self._extended()
                self.mem.write8(addr, self.s.b)
                self._logic8(self.s.b)
                self.mem.tick(3); self._trace(start_pc, opcode, prefix, "STAB"); return 3

        # ---- STD ----
        if opcode in {0xDD,0xED,0xFD}:
            if opcode == 0xDD:
                addr = self._direct()
            elif opcode == 0xED:
                addr = self._indexed(self._idx_base(use_y_index))
            else:
                addr = self._extended()
            self.mem.write16(addr, self.s.d)
            self._logic16(self.s.d)
            self.mem.tick(4); self._trace(start_pc, opcode, prefix, "STD"); return 4

        # ---- JSR / JMP ----
        if opcode in {0x8D,0x9D,0xAD,0xBD}:
            if opcode == 0x8D:  # BSR
                rel = s8(self._fetch8())
                self._push16(self.s.pc)
                self.s.pc = (self.s.pc + rel) & 0xFFFF
                self.mem.tick(7); self._trace(start_pc, opcode, prefix, "BSR"); return 7
            if opcode == 0x9D:
                target = self._direct()
            elif opcode == 0xAD:
                target = self._indexed(self._idx_base(use_y_index))
            else:
                target = self._extended()
            self._push16(self.s.pc)
            self.s.pc = target
            self.mem.tick(6); self._trace(start_pc, opcode, prefix, "JSR"); return 6

        raise UnknownOpcode(start_pc, opcode, prefix)

    # --------------------------
    # Run helpers
    # --------------------------

    def run(self, max_instructions: int = 1000, stop_on_pc: Optional[int] = None) -> int:
        executed = 0
        while executed < max_instructions and not self.halted:
            if stop_on_pc is not None and self.s.pc == (stop_on_pc & 0xFFFF):
                break
            self.step()
            executed += 1
        return executed

    def summary(self) -> str:
        return (
            f"PC=${self.s.pc:04X} SP=${self.s.sp:04X} "
            f"A=${self.s.a:02X} B=${self.s.b:02X} D=${self.s.d:04X} "
            f"X=${self.s.x:04X} Y=${self.s.y:04X} CCR=${self.s.ccr:02X}"
        )


