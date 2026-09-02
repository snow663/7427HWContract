from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
from pathlib import Path
from typing import Iterable

from .bus import ContractMemory
from .contracts import PCMProfile, infer_bin_base
from .devices import EngineInputs
from .hc11_core import CCR_I, HC11CPU, UnknownOpcode
from .scenario import Scenario
from .symbols import SymbolTable
from .trace import TraceRecorder


class StopReason(str, Enum):
    LIMIT = "limit"
    BREAKPOINT = "breakpoint"
    HALTED = "halted"
    WAITING = "waiting"
    UNKNOWN_OPCODE = "unknown_opcode"
    OUTPUT = "output"


@dataclass
class RunResult:
    reason: StopReason
    instructions: int
    cycles: int
    pc: int
    detail: str = ""


class Simulator:
    """Coordinator for CPU, memory bus, devices, scenarios, and operator control."""

    INTERRUPT_VECTORS = {
        "irq": 0xFFF2, "xirq": 0xFFF4, "swi": 0xFFF6,
        "toc1": 0xFFE8, "toc2": 0xFFE6, "toc3": 0xFFE4,
        "toc4": 0xFFE2, "toc5": 0xFFE0, "rti": 0xFFF0,
    }

    def __init__(self, profile: PCMProfile) -> None:
        self.profile = profile
        self.inputs = EngineInputs()
        self.trace = TraceRecorder()
        self.memory = ContractMemory(profile, self.inputs, self.trace)
        self.cpu = HC11CPU(self.memory)
        self.memory.state_provider = lambda: self.cpu.s
        self.symbols = SymbolTable()
        self.scenario = Scenario()
        self.breakpoints: set[int] = set()
        self.output_breakpoints: set[int] = set()
        self.instruction_counter = 0
        self.pending_interrupts: list[tuple[int, bool, str]] = []
        self.bin_path: str | None = None
        self.bin_base: int | None = None
        self.bin_sha256: str | None = None
        self.image_identity = "unloaded"

    @classmethod
    def from_profile_file(cls, path: str | Path) -> "Simulator":
        return cls(PCMProfile.load(path))

    def load_bin(self, path: str | Path, base: int | None = None) -> None:
        data = Path(path).read_bytes()
        if base is None:
            base = infer_bin_base(len(data))
        if base < 0 or base + len(data) > 0x10000:
            raise ValueError("BIN does not fit the 64K CPU address space")
        self.memory.mem[:] = bytes(0x10000)
        self.memory.load_bin(data, base)
        self.bin_path = str(path)
        self.bin_base = base
        self.bin_sha256 = hashlib.sha256(data).hexdigest()
        identities = self.profile.provenance.get("known_images", {})
        self.image_identity = next(
            (name for name, digest in identities.items() if digest.lower() == self.bin_sha256.lower()),
            "unknown-image",
        )

    def reset(self) -> None:
        self.trace.clear()
        self.scenario.reset()
        self.pending_interrupts.clear()
        self.instruction_counter = 0
        self.memory.context_pc = 0xFFFF
        self.memory.context_opcode = 0
        self.cpu.reset()
        self.trace.event("reset", self.memory.cycle_counter, pc=self.cpu.s.pc)

    def load_scenario(self, path: str | Path) -> None:
        self.scenario = Scenario.load(path)

    def load_hac_symbols(self, path: str | Path) -> int:
        return self.symbols.load_hac_html(path)

    def set_input(self, name: str, value: str | int | float) -> None:
        self.inputs.set_value(name, value)
        self.trace.event("input", self.memory.cycle_counter, name=name, value=value)

    def request_interrupt(self, vector: str | int, maskable: bool = True, source: str = "operator") -> None:
        if isinstance(vector, str):
            key = vector.lower()
            if key in self.INTERRUPT_VECTORS:
                address = self.INTERRUPT_VECTORS[key]
            else:
                address = int(vector, 0)
        else:
            address = int(vector)
        self.pending_interrupts.append((address & 0xFFFF, maskable, source))

    def _apply_scenario(self) -> None:
        for event in self.scenario.due(self.memory.cycle_counter):
            for name, value in event.inputs.items():
                self.inputs.set_value(name, value)
            for write in event.writes:
                self.memory.debug_write8(
                    int(str(write["address"]), 0),
                    int(str(write["value"]), 0),
                    allow_rom=bool(write.get("allow_rom", False)),
                )
            if event.interrupt is not None:
                self.request_interrupt(event.interrupt, source="scenario")
            self.trace.event("scenario", self.memory.cycle_counter, note=event.note, inputs=event.inputs)

    def _service_interrupt(self) -> int:
        hardware = self.memory.pending_interrupt_vector()
        if hardware is not None and not any(row[0] == hardware and row[2] == "device" for row in self.pending_interrupts):
            self.pending_interrupts.append((hardware, True, "device"))
        if not self.pending_interrupts:
            return 0
        vector, maskable, source = self.pending_interrupts[0]
        before = self.memory.cycle_counter
        if self.cpu.interrupt(vector, maskable=maskable):
            self.pending_interrupts.pop(0)
            self.trace.event("interrupt", before, vector=vector, source=source, new_pc=self.cpu.s.pc)
            return self.memory.cycle_counter - before
        return 0

    def step_instruction(self) -> int:
        self._apply_scenario()
        pc = self.cpu.s.pc
        self.memory.context_pc = pc
        self.memory.context_opcode = self.memory.mem[pc]
        interrupt_cycles = self._service_interrupt()
        if interrupt_cycles:
            return interrupt_cycles
        if self.cpu.waiting:
            self.memory.tick(1)
            return 1
        before = self.memory.cycle_counter
        self.cpu.step()
        elapsed = self.memory.cycle_counter - before
        self.instruction_counter += 1
        return elapsed

    def run(
        self,
        max_instructions: int = 100_000,
        max_cycles: int | None = None,
        stop_on_output: Iterable[int] = (),
        max_wait_cycles: int | None = None,
    ) -> RunResult:
        start_cycle = self.memory.cycle_counter
        start_instruction = self.instruction_counter
        watched_outputs = {x & 0xFFFF for x in stop_on_output} | self.output_breakpoints
        output_cursor = len(self.trace.outputs)
        wait_cycles = 0
        if max_wait_cycles is None:
            max_wait_cycles = self.profile.e_clock_hz // 4
        try:
            while self.instruction_counter - start_instruction < max_instructions:
                elapsed = self.memory.cycle_counter - start_cycle
                if max_cycles is not None and elapsed >= max_cycles:
                    return self._result(StopReason.LIMIT, start_instruction, start_cycle, "cycle budget")
                if self.cpu.s.pc in self.breakpoints:
                    return self._result(StopReason.BREAKPOINT, start_instruction, start_cycle)
                if self.cpu.halted:
                    return self._result(StopReason.HALTED, start_instruction, start_cycle)
                before_instruction = self.instruction_counter
                before_step_cycle = self.memory.cycle_counter
                self.step_instruction()
                if self.instruction_counter == before_instruction:
                    wait_cycles += self.memory.cycle_counter - before_step_cycle
                    if wait_cycles >= max_wait_cycles:
                        return self._result(StopReason.WAITING, start_instruction, start_cycle, "wait-cycle safety limit")
                else:
                    wait_cycles = 0
                new_outputs = self.trace.outputs[output_cursor:]
                if watched_outputs and any(row.address in watched_outputs for row in new_outputs):
                    return self._result(StopReason.OUTPUT, start_instruction, start_cycle)
                output_cursor = len(self.trace.outputs)
            return self._result(StopReason.LIMIT, start_instruction, start_cycle, "instruction budget")
        except UnknownOpcode as exc:
            return self._result(StopReason.UNKNOWN_OPCODE, start_instruction, start_cycle, str(exc))

    def run_cycles(self, budget: int) -> RunResult:
        """Advance by an E-clock budget, stopping on an instruction boundary."""
        return self.run(max_instructions=max(1, budget), max_cycles=max(1, budget))

    def _result(self, reason: StopReason, start_instruction: int, start_cycle: int, detail: str = "") -> RunResult:
        return RunResult(
            reason=reason,
            instructions=self.instruction_counter - start_instruction,
            cycles=self.memory.cycle_counter - start_cycle,
            pc=self.cpu.s.pc,
            detail=detail,
        )

    def poke(self, address: int, value: int, allow_rom: bool = False) -> None:
        self.memory.debug_write8(address, value, allow_rom=allow_rom)

    def peek(self, address: int, count: int = 16) -> bytes:
        # Debug inspection is intentionally trace-free and does not consume device FIFOs.
        address &= 0xFFFF
        return bytes(self.memory.debug_read8((address + i) & 0xFFFF) for i in range(count))

    def summary(self) -> str:
        state = self.cpu.s
        symbol = self.symbols.label(state.pc)
        label = f" [{symbol}:hac_hint]" if symbol else ""
        return (
            f"PC=${state.pc:04X}{label} SP=${state.sp:04X} A=${state.a:02X} B=${state.b:02X} "
            f"D=${state.d:04X} X=${state.x:04X} Y=${state.y:04X} CCR=${state.ccr:02X} "
            f"CYC={self.memory.cycle_counter} INS={self.instruction_counter} "
            f"REG=${self.memory.reg_base:04X} RAM=${self.memory.ram_base:04X}"
        )

    def image_summary(self) -> str:
        return (
            f"BIN={self.bin_path or '(none)'} BASE={('$%04X' % self.bin_base) if self.bin_base is not None else '(none)'} "
            f"SHA256={self.bin_sha256 or '(none)'} ID={self.image_identity}"
        )
