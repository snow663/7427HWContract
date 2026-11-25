#!/usr/bin/env python3
"""Actual BMHM OC5/OC4 instructions versus the vector-dispatched C bodies.

The factory side fetches both complete handlers from hash-identified committed
bytes, enters through the CPU interrupt API, and executes RTI. No handler or
callee is replaced. PORTA/TCNT samples and W1C are explicit fixture premises;
this is not a timer-edge model, native C ABI test, or cycle-accuracy claim.
The CPU implementation is the independently audited legacy interpreter, not
a second independent emulator. Literal witnesses and RAM access checks below
also constrain its result rather than trusting C/ROM agreement alone.
"""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass, replace
from hashlib import sha256
import json
from pathlib import Path
import random
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "hac31_romsim"))
from build_factory_scheduler import recorded_rom
from romsim.hc11_core import HC11CPU, HC11Memory

IMAGE_SHA = "6188975246cf0042979f3a1694e3d43a2985a1452e7547a3b9e8a66d10e65004"
SPANS = {
    0xFFE0: (0x7875, "71eb097c1c658d5fd1a905028cf33decf1198c0ad9098a060b93b03b359bdad7"),
    0xFFE2: (0x78D9, "7820e2eee3cfee52e547cdc82284f5e5a82de178c8a7f52d5bd9b054eac5ba0e"),
}
# Independently reviewed boundaries, not inferred from observed execution.
OFFSETS = (0, 3, 5, 7, 11, 14, 17, 21, 24, 27, 29, 30, 32, 35,
           37, 40, 41, 42, 45, 48, 50, 53, 54, 56, 59, 61, 64, 66,
           69, 73, 75, 78, 80, 83, 85, 88, 92, 94, 97, 99)
# pc offset: (fall-through offset, taken offset)
BRANCHES = {7: (11, 80), 17: (21, 50), 27: (29, 32), 30: (32, 35),
            54: (56, 59), 73: (75, 97), 92: (94, 97)}
UNCONDITIONAL = {48: 64, 78: 97}
EXPECTED_PCS = {start + off for start, _ in SPANS.values() for off in OFFSETS}
EXPECTED_EDGES = {(start + pc, start + target)
                  for start, _ in SPANS.values()
                  for pc, targets in BRANCHES.items() for target in targets}
EXPECTED_BRA = {(start + pc, start + target)
                for start, _ in SPANS.values() for pc, target in UNCONDITIONAL.items()}


@dataclass(frozen=True)
class Case:
    name: str
    vectors: tuple[int, ...] = (0xFFE0,)
    fail_at: int = 0
    port: int = 0
    mask: int = 0
    flags: int = 0
    ctl: int = 0
    timer_seed: int = 0
    timer_step: int = 0
    toc4: int = 0
    toc5: int = 0
    pulse: int = 0
    reservoir: int = 0
    pending: int = 0
    compare_a: int = 0
    compare_b: int = 0
    extended_a: int = 0
    extended_b: int = 0

    def line(self):
        fields = (len(self.vectors), self.fail_at, self.port, self.mask, self.flags,
                  self.ctl, self.timer_seed, self.timer_step, self.toc4, self.toc5,
                  self.pulse, self.reservoir, self.pending, self.compare_a,
                  self.compare_b, self.extended_a, self.extended_b, *self.vectors)
        return " ".join(map(str, fields))


class ProviderFailure(Exception):
    pass


class Memory(HC11Memory):
    """Separate deterministic address space; only supplied logical I/O effects."""
    def __init__(self, image, case):
        super().__init__()
        self.mem[:] = image
        self.mem[:0x4000] = bytes(0x4000)
        self.case = case
        self.events, self.ram_events = [], []
        self.attempts = self.timer_reads = 0
        self.word_io = False
        for a, value in ((0x3000, case.port), (0x3022, case.mask),
                         (0x3023, case.flags), (0x3020, case.ctl),
                         (0x46, 0xA4 | case.pending)):
            self.mem[a] = value
        for a, value in ((0x301C, case.toc4), (0x301E, case.toc5),
                         (0x250, case.pulse), (0x23A, case.reservoir),
                         (0x821, case.compare_a), (0x823, case.compare_b),
                         (0x825, case.extended_a), (0x827, case.extended_b)):
            self.mem[a:a+2] = value.to_bytes(2, "big")

    def record(self, kind, width, address, value):
        event = [kind, width, address, value]
        if 0x3000 <= address < 0x4000:
            self.attempts += 1
            if self.attempts == self.case.fail_at:
                raise ProviderFailure
            self.events.append(event)
        elif address < 0x3000:
            self.ram_events.append(event)

    def read8(self, address):
        address &= 0xFFFF
        value = self.mem[address]
        if not self.word_io:
            self.record("R", 8, address, value)
        return value

    def read16(self, address):
        address &= 0xFFFF
        value = ((self.case.timer_seed + self.timer_reads * self.case.timer_step) & 0xFFFF
                 if address == 0x300E else self.raw_word(address))
        self.record("R", 16, address, value)
        if address == 0x300E:
            self.timer_reads += 1
        return value

    def write8(self, address, value):
        address, value = address & 0xFFFF, value & 0xFF
        if not self.word_io:
            self.record("W", 8, address, value)
        if address >= 0x4000:
            raise AssertionError(f"Unexpected factory ROM write {address:04X}")
        if address == 0x3023:
            self.mem[address] &= ~value & 255  # Explicit supplied W1C contract.
        else:
            self.mem[address] = value

    def write16(self, address, value):
        address, value = address & 0xFFFF, value & 0xFFFF
        self.record("W", 16, address, value)
        self.word_io = True
        try:
            self.write8(address, value >> 8)
            self.write8((address + 1) & 0xFFFF, value)
        finally:
            self.word_io = False

    def raw_word(self, address):
        return self.mem[address] << 8 | self.mem[(address + 1) & 0xFFFF]

    def tick(self, cycles):
        self.cycle_counter += cycles  # No timer progression inferred from clocks.

    def snapshot(self, status):
        return {"status": status, "action": 1 if status == 0 else 0,
                "state": [self.raw_word(0x250), self.raw_word(0x23A), self.mem[0x46] & 1,
                          *(self.raw_word(a) for a in (0x821, 0x823, 0x825, 0x827))],
                "io": [self.mem[a] for a in (0x3000, 0x3022, 0x3023, 0x3020)] +
                      [self.raw_word(0x301C), self.raw_word(0x301E)],
                "events": list(self.events)}


def architecture(cpu):
    s = cpu.s
    return s.pc, s.sp, s.ccr, s.a, s.b, s.x, s.y


def check_ram_accesses(before, memory, vector, stack):
    """Check stable-RAM accesses against an independently derived instruction contract."""
    bank_b = vector == 0xFFE2
    mask = 0x10 if bank_b else 8
    arm, ext = (0x823, 0x827) if bank_b else (0x821, 0x825)
    word = lambda a: before[a] << 8 | before[a+1]
    near = (next(e[3] for e in memory.events if e[:3] == ["R", 16, 0x300E]) + 2) & 0xFFFF
    expected = []
    if before[0x3000] & mask:
        expected += [["R", 8, 0x46, before[0x46]], ["R", 16, 0x250, word(0x250)]]
        pulse = word(0x250)
        if before[0x46] & 1:
            expected += [["R", 16, 0x23A, word(0x23A)]]
            pulse += word(0x23A)
        deadline = (min(2*pulse, 65535) + word(0x301C if bank_b else 0x301E)) & 0xFFFF
        expected += [["W", 16, ext, deadline]]
        if before[0x46] & 1:
            expected += [["W", 16, 0x23A, 0], ["R", 8, 0x46, before[0x46]],
                         ["W", 8, 0x46, before[0x46] & 0xFE]]
        expected += [["R", 16, ext, deadline]]
        address = ext
    else:
        deadline, address = word(arm), arm
        expected += [["R", 16, arm, deadline]]
    if (near - deadline) & 0x8000:
        expected += [["R", 16, address, deadline]]
    actual = [e for e in memory.ram_events if e[2] not in stack]
    if actual != expected:
        raise AssertionError(f"Factory RAM-access contract differs: {actual!r} != {expected!r}")


def execute_rom(image, case, index, coverage, edges, bra, counters):
    memory, steps, traces = Memory(image, case), [], []
    cpu = HC11CPU(memory)
    cpu.s.pc, cpu.s.sp = 0x7000, 0x03FF - index % 16
    cpu.s.ccr = (index * 37) & 0xEF  # Vary every admissible CCR bit; I=0 at admission.
    cpu.s.a, cpu.s.b = (index * 11 + 0x12) & 255, (index * 29 + 0x34) & 255
    cpu.s.x, cpu.s.y = (index * 103 + 0x5678) & 65535, (index * 109 + 0x9ABC) & 65535
    for vector in case.vectors:
        saved = architecture(cpu)
        start = SPANS[vector][0]
        before = bytes(memory.mem)
        stack = set(range(cpu.s.sp - 8, cpu.s.sp + 1))
        if not cpu.interrupt(vector):
            raise AssertionError("Factory vector was unexpectedly denied")
        counters["interrupt_entries"] += 1
        pc, sp, ccr, a, b, x, y = saved
        expected_frame = bytes((ccr, b, a, x >> 8, x & 255, y >> 8, y & 255, pc >> 8, pc & 255))
        if cpu.s.sp != sp - 9 or bytes(memory.mem[sp-8:sp+1]) != expected_frame:
            raise AssertionError("Factory interrupt's nine-byte frame differs")
        memory.events.clear()
        memory.ram_events.clear()
        retired, attempted, status = [], None, 0
        try:
            for _ in range(80):
                pc = cpu.s.pc
                if pc == saved[0]:
                    break
                if pc not in {start + off for off in OFFSETS}:
                    raise AssertionError(f"Handler escaped reviewed body at {pc:04X}")
                if not cpu.s.ccr & 0x10 or cpu.interrupt(0xFFF2):
                    raise AssertionError("Ordinary IRQ admitted inside masked output handler")
                attempted = pc
                cpu.step()
                coverage.add(pc)  # A failed instruction is not completed coverage.
                retired.append(pc)
                if pc - start in BRANCHES:
                    edges.add((pc, cpu.s.pc))
                if pc - start in UNCONDITIONAL:
                    bra.add((pc, cpu.s.pc))
            else:
                raise AssertionError("Output handler exhausted instruction budget")
            if not retired or retired[-1] != start + 99 or architecture(cpu) != saved:
                raise AssertionError("Factory RTI failed full architectural restoration")
            counters["restored_rti"] += 1
            check_ram_accesses(before, memory, vector, stack)
        except ProviderFailure:
            status = 2
            counters["provider_failures"] += 1
        # No hidden retained-RAM changes are excluded other than the real IRQ frame.
        allowed = stack | {0x46, 0x23A, 0x23B, 0x825, 0x826, 0x827, 0x828}
        if any(before[a] != memory.mem[a] for a in range(0x3000) if a not in allowed):
            raise AssertionError("Factory handler modified unexpected retained RAM")
        steps.append(memory.snapshot(status))
        traces.append({"vector": f"{vector:04X}", "retired_pcs": [f"{p:04X}" for p in retired],
                       "failed_pc": f"{attempted:04X}" if status else None})
        if status:
            break
    return {"steps": steps}, traces


def literal_ack(vector):
    bank_b = vector == 0xFFE2
    mask, action, toc = (16, 4, 0x301C) if bank_b else (8, 1, 0x301E)
    return {"steps": [{"status": 0, "action": 1, "state": [0]*7,
                       "io": [0, 0, 0, action, 2 if bank_b else 0, 0 if bank_b else 2],
                       "events": [["W", 8, 0x3023, mask], ["R", 8, 0x3000, 0],
                                  ["R", 8, 0x3020, 0], ["W", 8, 0x3020, action],
                                  ["R", 16, 0x300E, 0], ["W", 16, toc, 2]]}]}


def generate_cases(literal_only=False):
    cases = [Case(f"literal_ack_{v:04X}", vectors=(v,)) for v in SPANS]
    if literal_only:
        return cases
    values = (0, 1, 0x7FFE, 0x7FFF, 0x8000, 0x8001, 0xFFFE, 0xFFFF)
    differences = (0, 1, 0x7FFF, 0x8000, 0x8001, 0xFFFF)
    for vector in SPANS:
        bank_b = vector == 0xFFE2
        mask = 16 if bank_b else 8
        base = Case(f"{vector:04X}", vectors=(vector,), port=mask, mask=255, flags=255,
                    ctl=255, timer_seed=0x1000, toc4=0x1000, toc5=0x1000, pulse=1,
                    reservoir=2, pending=1, compare_a=0x1357, compare_b=0x2468,
                    extended_a=0xAA55, extended_b=0x55AA)
        cases.append(replace(base, name=f"literal_shared_{vector:04X}"))
        cases.append(replace(base, name=f"literal_add_carry_{vector:04X}",
                             pulse=0xFFFF, reservoir=1, toc4=1, toc5=1, timer_seed=0xFFFE))
        cases.append(replace(base, name=f"literal_shift_carry_{vector:04X}",
                             pulse=0x8000, pending=0, toc4=1, toc5=1, timer_seed=0xFFFE))
        for near in (0, 1, 0x7FFF, 0x8000, 0xFFFF):
            for diff in differences:
                deadline = (near - diff) & 65535
                cases.append(replace(base, name=f"armed_difference_{vector:04X}_{near}_{diff}",
                                     port=255 & ~mask, timer_seed=(near-2) & 65535,
                                     compare_a=deadline, compare_b=deadline))
        for pending in (0, 1):
            for pulse in values:
                for reservoir in values if pending else (0xA55A,):
                    for diff in differences:
                        near = (pulse + reservoir) & 65535
                        width = min((pulse + (reservoir if pending else 0))*2, 65535)
                        previous = (near - diff - width) & 65535
                        cases.append(replace(base, name=f"pulse_boundary_{vector:04X}_{pending}_{pulse}_{reservoir}_{diff}",
                                             pulse=pulse, reservoir=reservoir, pending=pending,
                                             toc4=previous, toc5=previous, timer_seed=(near-2) & 65535))
        for byte in range(256):
            for high in (False, True):
                cases.append(replace(base, name=f"byte_retention_{vector:04X}_{byte}_{high}",
                                     port=mask if high else 255 & ~mask,
                                     mask=byte, flags=byte ^ 0x5A, ctl=byte ^ 0xA5))
        for port, pending in ((0, 1), (mask, 0), (mask, 1)):
            total = 6 if not port else 9
            for fail in range(1, total + 2):  # Last value must succeed, guarding fail-count boundaries.
                cases.append(replace(base, name=f"failure_prefix_{vector:04X}_{port}_{pending}_{fail}",
                                     port=port, pending=pending, fail_at=fail))
    sequence = Case("retained", vectors=(0xFFE0, 0xFFE2), port=24, mask=255, flags=255,
                    ctl=255, timer_seed=0x1000, timer_step=1, toc4=0x1000, toc5=0x1000,
                    pulse=1, reservoir=2, pending=1, compare_a=0x2000, compare_b=0x3000,
                    extended_a=0xA55A, extended_b=0x5AA5)
    for vectors in ((0xFFE0, 0xFFE2), (0xFFE2, 0xFFE0), (0xFFE0,)*4,
                    (0xFFE2,)*4, (0xFFE0, 0xFFE2)*4, (0xFFE2, 0xFFE0)*4):
        for port in (0, 8, 16, 24):
            cases.append(replace(sequence, name=f"retained_{vectors}_{port}", vectors=vectors, port=port))
    for fail in range(10, 20):
        cases.append(replace(sequence, name=f"second_bank_failure_{fail}", fail_at=fail))
    rng = random.Random(0x31787578D9)
    for i in range(1024):
        cases.append(Case(f"random_retained_{i}",
                          vectors=tuple(rng.choice(tuple(SPANS)) for _ in range(rng.randint(1, 8))),
                          port=rng.randrange(256), mask=rng.randrange(256), flags=rng.randrange(256),
                          ctl=rng.randrange(256), timer_seed=rng.randrange(65536), timer_step=rng.randrange(65536),
                          toc4=rng.randrange(65536), toc5=rng.randrange(65536), pulse=rng.randrange(65536),
                          reservoir=rng.randrange(65536), pending=rng.randrange(2),
                          compare_a=rng.randrange(65536), compare_b=rng.randrange(65536),
                          extended_a=rng.randrange(65536), extended_b=rng.randrange(65536)))
    return cases


def first_difference(expected, actual, path="result"):
    if type(expected) is not type(actual):
        return f"{path}: expected {type(expected).__name__}, got {type(actual).__name__}"
    if isinstance(expected, dict):
        if expected.keys() != actual.keys():
            return f"{path}: keys {sorted(expected)} != {sorted(actual)}"
        # Event order is the first observable divergence, before final status/state.
        order = sorted(expected, key=lambda key: (key != "events", key))
        for key in order:
            different = first_difference(expected[key], actual[key], f"{path}.{key}")
            if different:
                return different
    elif isinstance(expected, list):
        for i, (left, right) in enumerate(zip(expected, actual)):
            different = first_difference(left, right, f"{path}[{i}]")
            if different:
                return different
        if len(expected) != len(actual):
            index = min(len(expected), len(actual))
            return f"{path}[{index}]: expected {expected[index:index+1]!r}, got {actual[index:index+1]!r} (length {len(expected)} != {len(actual)})"
    elif expected != actual:
        return f"{path}: expected {expected!r}, got {actual!r}"
    return None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("binary", type=Path)
    parser.add_argument("--literal-only", action="store_true", help="two minimal acknowledgment/RTI witnesses; not full coverage")
    parser.add_argument("--literal-vector", choices=("FFE0", "FFE2"),
                        help="select one minimal witness; requires --literal-only")
    parser.add_argument("--report", type=Path, help="write exact scope, hashes, results and coverage JSON")
    args = parser.parse_args()
    if args.literal_vector and not args.literal_only:
        parser.error("--literal-vector requires --literal-only")
    evidence = ROOT / "maps/structure/bmhm_global_structure_rom_evidence.json"
    rom = recorded_rom(json.loads(evidence.read_text()))
    image = bytes([255])*0x4000 + rom.read(0x4000, 0xC000)
    if sha256(image).hexdigest() != IMAGE_SHA:
        raise AssertionError("Committed BMHM image hash mismatch")
    for vector, (start, digest) in SPANS.items():
        if int.from_bytes(image[vector:vector+2], "big") != start or sha256(image[start:start+100]).hexdigest() != digest:
            raise AssertionError("Factory handler/vector bytes changed")
    cases = generate_cases(args.literal_only)
    if args.literal_vector:
        cases = [case for case in cases if case.vectors == (int(args.literal_vector, 16),)]
    stream = "\n".join(case.line() for case in cases) + "\n"
    process = subprocess.run([str(args.binary.resolve())], input=stream, text=True,
                             capture_output=True, check=False, timeout=30)
    if process.returncode:
        raise AssertionError(f"C driver exited {process.returncode}: {process.stderr}")
    outputs = process.stdout.splitlines()
    if len(outputs) != len(cases):
        raise AssertionError(f"C driver output count {len(outputs)} != case count {len(cases)}")
    coverage, edges, bra, counters = set(), set(), set(), Counter()
    result_hash = sha256()
    for index, (case, line) in enumerate(zip(cases, outputs)):
        expected, traces = execute_rom(image, case, index, coverage, edges, bra, counters)
        if case.name.startswith("literal_ack_") and expected != literal_ack(case.vectors[0]):
            raise AssertionError(f"Factory execution failed independent literal witness: {case.name}: {expected}")
        if case.name.startswith("literal_shared_"):
            bank = case.vectors[0] == 0xFFE2
            state = expected["steps"][0]["state"]
            if state[1:3] != [0, 0] or state[6 if bank else 5] != 0x1006:
                raise AssertionError("Factory shared-reservoir literal arithmetic differs")
        if case.name.startswith(("literal_add_carry_", "literal_shift_carry_")):
            bank = case.vectors[0] == 0xFFE2
            result = expected["steps"][0]
            if result["state"][6 if bank else 5] != 0 or result["io"][4 if bank else 5] != 0:
                raise AssertionError("Factory saturation/wrapping literal arithmetic differs")
        actual = json.loads(line)
        difference = first_difference(expected, actual)
        if difference:
            failure = {"status": "FAIL", "case": case.name, "index": index,
                       "first_divergence": difference, "reproduce_stdin": case.line() + "\n",
                       "expected_factory": expected, "actual_c": actual, "factory_trace": traces}
            if args.report:
                args.report.write_text(json.dumps(failure, indent=2) + "\n")
            print(json.dumps(failure, indent=2), file=sys.stderr)
            return 1
        result_hash.update(json.dumps(expected, sort_keys=True, separators=(",", ":")).encode())
    if not args.literal_only and (coverage != EXPECTED_PCS or edges != EXPECTED_EDGES or bra != EXPECTED_BRA):
        raise AssertionError(f"Incomplete/unexpected coverage: PCs missing={sorted(EXPECTED_PCS-coverage)}, extra={sorted(coverage-EXPECTED_PCS)}; "
                             f"conditional edges missing={sorted(EXPECTED_EDGES-edges)}, extra={sorted(edges-EXPECTED_EDGES)}; "
                             f"BRA edges missing={sorted(EXPECTED_BRA-bra)}, extra={sorted(bra-EXPECTED_BRA)}")
    summary = {"status": "PASS", "scope": f"{len(cases)} literal witness(es) only" if args.literal_only else "complete two-handler bodies under declared logical I/O fixture",
               "factory_sha256": IMAGE_SHA, "driver_sha256": sha256(args.binary.read_bytes()).hexdigest(),
               "cpu_source_sha256": sha256((ROOT / "hac31_romsim/romsim/hc11_core.py").read_bytes()).hexdigest(),
               "input_sha256": sha256(stream.encode()).hexdigest(), "results_sha256": result_hash.hexdigest(),
               "cases": len(cases), **dict(counters), "completed_instruction_starts": len(coverage),
               "conditional_branch_edges": len(edges), "unconditional_branch_edges": len(bra),
               "pcs": [f"{pc:04X}" for pc in sorted(coverage)],
               "conditional_edges": [[f"{a:04X}", f"{b:04X}"] for a, b in sorted(edges)],
               "unconditional_edges": [[f"{a:04X}", f"{b:04X}"] for a, b in sorted(bra)],
               "limits": ["Shared corrected legacy CPU implementation; not an independent emulator pair",
                          "PORTA/TCNT sequence and W1C are supplied fixture premises",
                          "C native IRQ entry/RTI ABI, physical timer edges and timing are not tested"]}
    if args.report:
        args.report.write_text(json.dumps(summary, indent=2) + "\n")
    print(f"PASS output-timer ROM differential: {len(cases)} cases; {counters['restored_rti']} restored RTIs; "
          f"{counters['provider_failures']} failure prefixes; {len(coverage)}/80 instruction starts; "
          f"{len(edges)}/28 conditional edges; {len(bra)}/4 BRA edges. Scope: {summary['scope']}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
