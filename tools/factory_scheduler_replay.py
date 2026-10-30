"""Execute bounded scheduler bytes using the repository's existing HC11 CPU.

This is independent of the scheduler-map decoder and guard metadata. External
callees return through the actual ROM RTS at $7AA5, with registers clobbered.
RAM gates are fixture-controlled. ADC is immediately ready and timer registers
are fixture values. Neither callee effects nor real-time hardware are modeled.
"""
from __future__ import annotations

import json
import sys

from factory_structure import ROOT
from build_factory_scheduler import EVIDENCE, recorded_rom

sys.path.insert(0, str(ROOT / "hac31_romsim"))
from romsim.hc11_core import HC11CPU, HC11Memory  # noqa: E402


class FixtureMemory(HC11Memory):
    def __init__(self, rom):
        super().__init__()
        self.available = set(rom.memory)
        for address, value in rom.memory.items():
            self.mem[address] = value
        self.adc_samples = {}
        self.writes = []

    def read8(self, address):
        address &= 0xFFFF
        if address >= 0x4000 and address not in self.available:
            raise ValueError(f"Replay reads unrecorded ROM ${address:04X}")
        if address == 0x3030:
            return self.mem[address] | 0x80  # ADC ready fixture
        if address == 0x3031:
            return self.adc_samples.get(self.mem[0x3030] & 7, self.mem[address])
        return self.mem[address]

    def write8(self, address, value):
        address &= 0xFFFF
        if address >= 0x4000:
            raise ValueError(f"Replay attempted ROM write ${address:04X}")
        self.mem[address] = value & 0xFF
        self.writes.append((address, value & 0xFF))

    def tick(self, cycles):
        self.cycle_counter += cycles  # Instruction accounting only; no physical timing claim.


class SchedulerReplay:
    INTERNAL = {0x7B6D, 0xF3E4, 0xF2FD, 0xF25F, 0xF275}

    def __init__(self):
        self.memory = FixtureMemory(recorded_rom(json.loads(EVIDENCE.read_text())))
        self.cpu = HC11CPU(self.memory)
        self.cpu.s.sp = 0x03FF
        self.cpu.s.ccr = 0xC0
        self.cpu.s.pc = 0x74D0
        self.calls = []
        self.passes = []
        self.executed = []
        self.before_step = None

    def step(self):
        if self.before_step:
            self.before_step(self)
        pc = self.cpu.s.pc
        opcode = self.memory.read8(pc)
        phase = self.memory.read8(2)
        self.executed.append(pc)
        self.cpu.step()
        if opcode not in {0x8D, 0x9D, 0xAD, 0xBD}:
            return
        target = self.cpu.s.pc
        self.calls.append((pc, target, phase, self.cpu.s.ccr))
        if pc == 0x7A4F:
            self.passes.append((phase, target))
        if target in self.INTERNAL or 0x7AA6 <= target < 0x7B6D:
            return
        # Execute a real RTS on the CPU's real call stack. Do not infer the
        # return destination or evaluate guards using the map's decoder.
        self.cpu.s.a, self.cpu.s.b = 0xA5, 0x5A
        self.cpu.s.x, self.cpu.s.y = 0xDEAD, 0xBEEF
        self.cpu.s.pc = 0x7AA5

    def run_until(self, stop_pc, budget=20000):
        for _ in range(budget):
            if self.cpu.s.pc == stop_pc:
                return
            self.step()
        raise RuntimeError(f"Scheduler fixture did not reach ${stop_pc:04X}; stopped at ${self.cpu.s.pc:04X}")

    def tick(self):
        return_pc = self.cpu.s.pc
        if not self.cpu.interrupt(0xFFE4):
            raise RuntimeError("Timer interrupt masked at fixture entry")
        self.run_until(return_pc)

    def count(self, target):
        return sum(call[1] == target for call in self.calls)
