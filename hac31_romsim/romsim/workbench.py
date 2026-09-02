from __future__ import annotations

from pathlib import Path
from typing import Mapping

from .simulator import RunResult, Simulator


DEFAULT_PROFILE = Path(__file__).resolve().parent / "profiles" / "gm_16197427_31.json"


def parse_number(value: str | int) -> int:
    """Accept normal Python numeric notation plus the $FFFF form used in PCM work."""
    if isinstance(value, int):
        return value
    text = value.strip().replace("_", "")
    if text.startswith("$"):
        return int(text[1:], 16)
    return int(text, 0)


class SimulatorWorkbench:
    """UI-neutral operator layer shared by the desktop GUI and its tests."""

    def __init__(self, simulator: Simulator) -> None:
        self.sim = simulator

    @classmethod
    def default(cls) -> "SimulatorWorkbench":
        return cls(Simulator.from_profile_file(DEFAULT_PROFILE))

    @property
    def image_loaded(self) -> bool:
        return self.sim.bin_path is not None

    def require_image(self) -> None:
        if not self.image_loaded:
            raise RuntimeError("Load a BIN image first")

    def load_bin(self, path: str | Path, base: int | str | None = None) -> None:
        resolved_base = parse_number(base) if base not in {None, ""} else None
        self.sim.load_bin(path, resolved_base)
        self.sim.reset()

    def reset(self) -> None:
        self.require_image()
        self.sim.reset()

    def apply_inputs(self, values: Mapping[str, str | int | float]) -> None:
        for name, value in values.items():
            self.sim.set_input(name, value)

    def step_instructions(self, count: int = 1) -> int:
        self.require_image()
        count = max(1, int(count))
        elapsed = 0
        for _ in range(count):
            elapsed += self.sim.step_instruction()
        return elapsed

    def step_cycles(self, cycles: int) -> RunResult:
        self.require_image()
        return self.sim.run_cycles(max(1, int(cycles)))

    def run_chunk(self, instructions: int = 1_000) -> RunResult:
        self.require_image()
        return self.sim.run(max_instructions=max(1, int(instructions)))

    def read_memory(self, address: str | int, count: str | int = 64) -> bytes:
        self.require_image()
        return self.sim.peek(parse_number(address), max(1, parse_number(count)))

    def write_memory(self, address: str | int, value: str | int, *, patch_rom: bool = False) -> None:
        self.require_image()
        target = parse_number(address) & 0xFFFF
        if self.sim.profile.is_rom(target) and not patch_rom:
            raise PermissionError("ROM is protected; use the explicit session-only Patch ROM action")
        self.sim.poke(target, parse_number(value), allow_rom=patch_rom)

    def toggle_breakpoint(self, address: str | int, *, output: bool = False) -> bool:
        target = parse_number(address) & 0xFFFF
        collection = self.sim.output_breakpoints if output else self.sim.breakpoints
        if target in collection:
            collection.remove(target)
            return False
        collection.add(target)
        return True

    def request_interrupt(self, vector: str | int) -> None:
        self.require_image()
        self.sim.request_interrupt(vector)
