#!/usr/bin/env python3
"""Functional dual-image comparator and executable *synthetic* BIN adapter.

Real PCM adapters must implement the protocol below with qualified hardware,
interrupt and state contracts. The supplied adapter has flat synthetic memory
and is deliberately NOT a BMHM/7427 peripheral model. A matched scenario is
bounded evidence, never a claim of complete firmware equivalence.
"""
from __future__ import annotations

from collections import deque
from dataclasses import asdict, dataclass, replace
import hashlib
import json
from pathlib import Path
import sys
from typing import Protocol


@dataclass(frozen=True)
class Stimulus:
    epoch: int
    logical_time: int
    inputs: tuple[tuple[str, int], ...]

    def __post_init__(self):
        if type(self.epoch) is not int or type(self.logical_time) is not int or self.epoch < 0 or self.logical_time < 0:
            raise ValueError("epoch and logical time must be nonnegative integers")
        canonical = []
        for item in self.inputs:
            if not isinstance(item, (tuple, list)) or len(item) != 2:
                raise ValueError("each input must have one name and one integer value")
            name, value = item
            if not isinstance(name, str) or not name or type(value) is not int:
                raise ValueError("input names must be nonempty strings and values must be integers")
            canonical.append((name, value))
        # A frozen dataclass alone would leave nested caller-owned lists mutable.
        object.__setattr__(self, "inputs", tuple(canonical))


@dataclass(frozen=True)
class Output:
    channel: str
    operation: str
    value: int
    width: int


@dataclass(frozen=True)
class Snapshot:
    checkpoint: str
    complete: bool
    reason: str
    outputs: tuple[Output, ...]
    state: tuple[tuple[str, int], ...]
    diagnostics: dict


class Adapter(Protocol):
    identity: dict

    def mutable_state_ids(self) -> set[int]:
        """Include CPU, RAM, devices, queues and other mutable environment state."""

    def advance(self, stimulus: Stimulus, instruction_limit: int) -> Snapshot:
        """Deliver one immutable input epoch and stop at a semantic checkpoint.

        Do not reset RAM between epochs, copy peer state, skip unsupported
        accesses, or declare a timeout/unknown instruction a checkpoint.
        Each adapter owns its interrupt and device event queues.
        """


def _digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True,
        separators=(",", ":")).encode("utf-8")).hexdigest()


def _canonical_state(snapshot: Snapshot) -> Snapshot:
    state = []
    names = set()
    for name, value in snapshot.state:
        if not isinstance(name, str) or not name or name in names or type(value) is not int:
            raise ValueError("state requires unique nonempty names and integer values")
        names.add(name)
        state.append((name, value))
    return replace(snapshot, state=tuple(sorted(state)))


def compare(left: Adapter, right: Adapter, stimuli: tuple[Stimulus, ...],
            *, instruction_limit: int = 10000) -> dict:
    """Compare ordered observables and named retained state after each epoch.

    Diagnostic PC/cycles/physical RAM addresses are not equivalence keys.
    Exact normalized outputs and state are required; tolerance, event merging
    and address translation belong in an explicit reviewed adapter contract.
    """
    if left is right or left.mutable_state_ids() & right.mutable_state_ids():
        raise ValueError("comparison environments share mutable state")
    if not stimuli or instruction_limit <= 0:
        raise ValueError("non-empty stimuli and a positive instruction limit are required")
    if [s.epoch for s in stimuli] != list(range(len(stimuli))):
        raise ValueError("stimulus epochs must be contiguous from zero")
    if any(b.logical_time < a.logical_time for a, b in zip(stimuli, stimuli[1:])):
        raise ValueError("logical input time must not move backwards")
    for stimulus in stimuli:
        keys = [name for name, _ in stimulus.inputs]
        if len(keys) != len(set(keys)):
            raise ValueError("duplicate input channel in one epoch")
    result = {
        "schema": "7427-dual-bin-functional-comparison-v1",
        "scope": "bounded scenarios under the declared adapter contracts",
        "left": left.identity, "right": right.identity,
        "stimulus_sha256": _digest([asdict(s) for s in stimuli]),
        "instruction_limit_per_epoch": instruction_limit,
        "verdict": "INCONCLUSIVE", "completed_epochs": 0,
        "first_divergence": None, "checkpoints": [],
    }
    for stimulus in stimuli:
        snapshots = []
        sharing_detected = False
        for adapter in (left, right):
            try:
                snapshot = _canonical_state(adapter.advance(stimulus, instruction_limit))
            except Exception as error:
                # An adapter failure must never turn into empty matching output.
                snapshot = Snapshot("", False, f"adapter error: {type(error).__name__}: {error}",
                                    (), (), {})
            snapshots.append(snapshot)
            # An adapter may allocate lazy device/queue state during execution.
            sharing_detected |= bool(left.mutable_state_ids() & right.mutable_state_ids())
        a, b = snapshots
        issue = None
        if sharing_detected:
            issue = "shared_mutable_state"
        elif not a.complete or not b.complete:
            issue = "incomplete_execution"
        elif a.checkpoint != b.checkpoint:
            issue = "checkpoint"
        elif a.outputs != b.outputs:
            issue = "ordered_outputs"
        elif a.state != b.state:
            issue = "retained_state"
        row = {"stimulus": asdict(stimulus), "left": asdict(a), "right": asdict(b)}
        result["checkpoints"].append(row)
        if issue:
            result["verdict"] = "INCONCLUSIVE" if issue in {"incomplete_execution", "shared_mutable_state"} else "DIVERGED"
            result["first_divergence"] = {"epoch": stimulus.epoch, "category": issue,
                                           "evidence": row}
            return result
        result["completed_epochs"] += 1
    result["verdict"] = "MATCHED_SCENARIOS"
    return result


class _SyntheticMemory:
    def __init__(self, image: bytes, output_addresses: dict[int, str]):
        self.mem = bytearray(image)
        self.outputs: list[Output] = []
        self.output_addresses = dict(output_addresses)
        self.cycle_counter = 0

    def reset(self):
        self.cycle_counter = 0
        self.outputs.clear()

    def read8(self, address):
        return self.mem[address & 0xFFFF]

    def read16(self, address):
        return (self.read8(address) << 8) | self.read8(address + 1)

    def write8(self, address, value):
        address &= 0xFFFF
        self.mem[address] = value & 255
        if address in self.output_addresses:
            self.outputs.append(Output(self.output_addresses[address], "write8", value & 255, 8))

    def write16(self, address, value):
        # Only a synthetic RAM convention; not an HC11 peripheral latch model.
        self.write8(address, value >> 8)
        self.write8(address + 1, value)

    def tick(self, cycles):
        self.cycle_counter += cycles


class SyntheticBINAdapter:
    """Execute a tiny full-address-space BIN with an explicit loop checkpoint.

    Independent CPU/RAM state, shared CPU implementation. It tests comparator
    mechanics only. There are no PCM peripherals or interrupt scheduling here.
    """
    def __init__(self, image: bytes, *, input_addresses: dict[str, int],
                 output_addresses: dict[int, str],
                 state_addresses: dict[str, int], checkpoint_pc: int,
                 checkpoint_name: str = "epoch_complete"):
        if len(image) != 0x10000:
            raise ValueError("synthetic adapter requires a 64 KiB image")
        root = Path(__file__).resolve().parents[2]
        sys.path.insert(0, str(root / "hac31_romsim"))
        from romsim.hc11_core import HC11CPU
        self.memory = _SyntheticMemory(image, output_addresses)
        self.cpu = HC11CPU(self.memory)
        self.cpu.reset()
        self.cpu.max_trace = 0
        self.input_addresses = dict(input_addresses)
        self.state_addresses = dict(state_addresses)
        self.checkpoint_pc = checkpoint_pc
        self.checkpoint_name = checkpoint_name
        self.trace = deque(maxlen=16)
        self.pcs: set[int] = set()
        self.edges: set[tuple[int, int]] = set()
        self.opcodes: set[str] = set()
        self.identity = {
            "bin_sha256": hashlib.sha256(image).hexdigest(),
            "cpu_engine": "hac31_romsim.romsim.hc11_core.HC11CPU",
            "adapter": "synthetic-flat-memory-only",
            "hardware_qualification": "none; not a real PCM adapter",
            "input_addresses": dict(input_addresses),
            "output_addresses": dict(output_addresses),
            "state_addresses": dict(state_addresses),
            "checkpoint_pc": checkpoint_pc, "checkpoint_name": checkpoint_name,
        }

    def mutable_state_ids(self):
        return {id(self), id(self.cpu), id(self.cpu.s), id(self.memory),
                id(self.memory.mem), id(self.memory.outputs), id(self.trace),
                id(self.pcs), id(self.edges), id(self.opcodes)}

    def advance(self, stimulus, instruction_limit):
        self.memory.outputs.clear()
        for name, value in stimulus.inputs:
            if name not in self.input_addresses or not 0 <= value <= 255:
                return self._snapshot(False, "unsupported synthetic input", 0)
            self.memory.mem[self.input_addresses[name]] = value
        for count in range(1, instruction_limit + 1):
            pc = self.cpu.s.pc
            instruction = bytes(self.memory.read8(pc + i) for i in range(4))
            self.trace.append({"pc": pc, "bytes": instruction.hex(),
                               "registers_before": asdict(self.cpu.s)})
            if self.cpu.waiting or self.cpu.halted:
                return self._snapshot(False, "unqualified wait/halt", count - 1)
            try:
                self.cpu.step()
            except Exception as error:
                return self._snapshot(False, f"{type(error).__name__}: {error}", count)
            self.pcs.add(pc)
            self.opcodes.add(instruction[:2 if instruction[0] in (0x18, 0x1A, 0xCD) else 1].hex())
            self.edges.add((pc, self.cpu.s.pc))
            if self.cpu.waiting or self.cpu.halted:
                return self._snapshot(False, "unqualified wait/halt", count)
            if self.cpu.s.pc == self.checkpoint_pc:
                return self._snapshot(True, "semantic checkpoint", count)
        return self._snapshot(False, "instruction limit", instruction_limit)

    def _snapshot(self, complete, reason, count):
        return Snapshot(self.checkpoint_name, complete, reason,
            tuple(self.memory.outputs),
            tuple(sorted((name, self.memory.mem[a]) for name, a in self.state_addresses.items())),
            {"instructions_this_epoch": count, "cycles": self.memory.cycle_counter,
             "registers": asdict(self.cpu.s), "trace_tail": list(self.trace),
             "execution_control": {"waiting": self.cpu.waiting, "halted": self.cpu.halted,
                 "irq_inhibit_instructions": self.cpu.irq_inhibit_instructions},
             "executed_pcs": sorted(self.pcs), "executed_edges": sorted(self.edges),
             "executed_opcodes": sorted(self.opcodes)})


def synthetic_pair(*, state_fault=False, output_fault=False):
    """Different code locations, registers, RAM and instruction sequences."""
    def image(pc, code):
        result = bytearray(0x10000)
        result[pc:pc + len(code)] = code
        result[0xFFFE:] = pc.to_bytes(2, "big")
        return bytes(result)
    left = image(0x8000, bytes.fromhex("b62000 bb2100 b72100 b73000 20f2"))
    right_code = bytes.fromhex("f62200 fb2300 f72300 01 f73100")
    if state_fault:
        right_code += bytes.fromhex("7c2300")
    if output_fault:
        right_code += bytes.fromhex("f73100")
    right = image(0x9000, right_code + bytes.fromhex("7e9000"))
    return (SyntheticBINAdapter(left, input_addresses={"sample": 0x2000},
                output_addresses={0x3000: "command"}, state_addresses={"accumulator": 0x2100},
                checkpoint_pc=0x8000),
            SyntheticBINAdapter(right, input_addresses={"sample": 0x2200},
                output_addresses={0x3100: "command"}, state_addresses={"accumulator": 0x2300},
                checkpoint_pc=0x9000))


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--synthetic-demo", action="store_true", required=True)
    parser.add_argument("--state-fault", action="store_true")
    args = parser.parse_args()
    stream = tuple(Stimulus(i, i * 1000, (("sample", value),))
                   for i, value in enumerate((1, 2, 250)))
    result = compare(*synthetic_pair(state_fault=args.state_fault), stream)
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["verdict"] == "MATCHED_SCENARIOS" else 1)
