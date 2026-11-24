"""CPU-visible address space, not an electrical reproduction of the PCM.

Memory boundaries originate in the repository's stock INIT03/CS selection
contract. Other than relocated HC11 registers, this initial backend stores
bytes without claiming unverified ASIC side effects. Writes to ROM are blocked.
"""
from dataclasses import dataclass
from typing import Callable

ROM_START = 0x4000
ROM_END = 0xFFFF
INIT_OFFSET = 0x3D
REGISTER_SIZE = 0x60
RESET_REG_BASE = 0x1000
COPRST_OFFSET = 0x3A

class RomWriteError(Exception):
    pass

@dataclass(frozen=True)
class BusEvent:
    direction: str
    address: int
    value: int
    region: str
    width: int = 8

class Bus:
    def __init__(self, on_access: Callable[[BusEvent], None] | None = None):
        self.on_access = on_access
        self.data = bytearray(0x10000)
        self.registers = bytearray(REGISTER_SIZE)
        self.register_base = RESET_REG_BASE
        self.rom_loaded = False
        self.rom_base = ROM_START
        self.cop_sequence: list[int] = []
        self.reset()

    def reset(self):
        # Reset is distinct from loading a BIN: non-ROM storage is volatile.
        self.data[:ROM_START] = bytes(ROM_START)
        self.registers[:] = bytes(REGISTER_SIZE)
        self.register_base = RESET_REG_BASE
        self.cop_sequence.clear()

    def load(self, rom: bytes):
        if len(rom) == 0x10000:
            self.data[:] = rom
            self.rom_base = 0
        elif len(rom) in (0xC000, 0x8000):
            self.data[:] = bytes([0xFF]) * 0x10000
            self.rom_base = 0x10000 - len(rom)
            self.data[self.rom_base:] = rom
        else:
            raise ValueError("ROM must be 32 KiB, 48 KiB, or 64 KiB")
        self.rom_loaded = True
        self.reset()

    def region(self, addr: int) -> str:
        if not 0 <= addr <= 0xFFFF:
            raise ValueError("CPU address outside 16-bit range")
        if self.register_base <= addr < self.register_base + REGISTER_SIZE:
            return "hc11-register"
        if addr < 0x400:
            return "internal-ram"
        if addr < 0x2000:
            return "general-memory"     # includes stock-used shadow 0800-08FF
        if addr < 0x3000:
            return "program-select-unverified"
        if addr < 0x3800:
            return "board-io1"
        if addr < ROM_START:
            return "board-io2"
        return "rom"

    def _emit(self, direction: str, addr: int, value: int, region: str):
        if self.on_access is not None:
            self.on_access(BusEvent(direction, addr, value, region))

    def peek8(self, addr: int) -> int:
        """Nontracing read of CPU-visible memory (no input side effects)."""
        kind = self.region(addr)
        if kind == "hc11-register":
            return self.registers[addr - self.register_base]
        return self.data[addr]

    def read8(self, addr: int) -> int:
        kind = self.region(addr)
        value = self.peek8(addr)
        self._emit("R", addr, value, kind)
        return value

    def read16(self, addr: int) -> int:
        if addr == 0xFFFF:
            raise ValueError("16-bit read crosses address boundary")
        return (self.read8(addr) << 8) | self.read8(addr+1)

    def write8(self, addr: int, value: int):
        kind = self.region(addr)
        value &= 0xFF
        if kind == "rom":
            self._emit("ROM_WRITE_BLOCKED", addr, value, kind)
            raise RomWriteError(f"ROM write at ${addr:04X}")
        if kind == "hc11-register":
            offset = addr - self.register_base
            self.registers[offset] = value
            if offset == INIT_OFFSET:
                # INIT03: CPU register block 1000 -> 3000; RAM stays at 0000.
                self.register_base = (value & 0x0F) << 12
            elif offset == COPRST_OFFSET:
                self.cop_sequence.append(value)
                self.cop_sequence[:] = self.cop_sequence[-2:]
        else:
            self.data[addr] = value
        self._emit("W", addr, value, kind)

    def write16(self, addr: int, value: int):
        if addr == 0xFFFF:
            raise ValueError("16-bit write crosses address boundary")
        self.write8(addr, value >> 8)
        self.write8(addr + 1, value)

    def patch_rom(self, addr: int, value: int):
        """Explicit debugger-only in-memory edit; never edits a user BIN."""
        if not ROM_START <= addr <= 0xFFFF:
            raise ValueError("Debugger ROM patch requires address >= 4000")
        self.data[addr] = value & 0xFF
        self._emit("PATCH", addr, value & 0xFF, "rom")
