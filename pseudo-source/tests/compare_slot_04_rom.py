"""Run both groups of scheduler slot 04 and compare with the stock HC11 entry."""
from dataclasses import dataclass, field, replace
from itertools import product
from pathlib import Path
import random
import sys
import tempfile

from slot_rom_replay import CPU, FixtureMemory, IMAGE, ROM, compare, decode, resident_instructions, word

# The tests include stock calibration as well as controlled equality, rollover
# and fault profiles. Code bytes remain those of the recorded factory image.
BASE = {0x02: 4, 0x06: 91, 0x16: 1, 0x17: 128, 0x1d: 0, 0x3b: 0,
        0x43: 0, 0x4e: 0xf0, 0x6f: 0x59, 0x87: 0xa4, 0x9e: 1,
        0xa5: 100, 0xa7: 100, 0x82d: 100, 0x2f3: 100, 0xa8: 55, 0xb4: 55,
        0x5b00: 0x60, 0x5b04: 0x18, 0x5b05: 0x66, 0x5b07: 0x87,
        0x5b9a: 2, 0x5d34: 60, 0x5d35: 130, 0x5d36: 60, 0x5d37: 120}
BASE |= word(0xa9, 0x6480) | word(0xb5, 0x5080) | word(0x1ac, 1000) | word(0x5b9b, 500)
BASE |= word(0x5b64, 2) | {0x5b63: 100, 0x5b66: 100, 0x5b67: 2}
for a in (0x5b13, 0x5b15, 0x5b68, 0x5b6b, 0x5b6d, 0x5b71):
    BASE.update({a: 100, a + 1: 2})
for a in (0x5ba2, 0x5ba4, 0x5ba6):
    BASE.update({a: 2, a + 1: 3})
BASE.update({0x5b96: 80, 0x5b97: 140, 0x5b98: 70, 0x5b99: 125})
BASE.update({a: (a * 13 + 45) & 255 for a in range(0x2f8, 0x32c)})


@dataclass
class Case:
    phase: int = 4
    edits: dict = field(default_factory=dict)
    passes: int = 1
    fail: int = 0
    action: int = 0
    masked: int = 0
    stock_cal: bool = False

    def initial(self):
        return ({} if self.stock_cal else BASE) | self.edits | {2: self.phase}

    def row(self):
        edits = self.initial()
        return ' '.join(map(str, [self.passes, self.fail, self.action, self.masked,
                                  len(edits), *(v for pair in edits.items() for v in pair)]))


class Stop(Exception):
    pass


class Memory(FixtureMemory):
    def event(self, kind, a, v):
        self.events.append(f'{kind}{a:04x}{v:04x}')
        if self.fail == len(self.events):
            raise Stop

    def read8(self, a):
        value = self.mem[a]
        if a == self.operand and 'R' in self.access:
            self.event('r', a, value)
            if self.action == 1 and a in (0x5d0b, 0x5d0c, 0x5b96, 0x5b98):
                self.mem[a] ^= 0x75
            if self.action == 2 and a == 0x5d36:
                self.mem[a] = (value + 80) & 255
        return value

    def read16(self, a):
        value = (self.mem[a] << 8) | self.mem[(a + 1) & 65535]
        if a == self.operand and 'R' in self.access:
            self.event('R', a, value)
        return value

    def write8(self, a, v):
        track = a == self.operand and 'W' in self.access
        if track:
            self.event('w', a, v)
        self.mem[a] = v
        if track:
            if self.action == 3 and a == 0x16f:
                self.mem[2] ^= 0x10
            if self.action == 4 and a == 0x17c:
                self.mem[0x3b] |= 4
            if self.action == 6 and a == 0x6f and not self.injected:
                self.injected = True
                self.mem[a] ^= 8

    def write16(self, a, v):
        if a == self.operand and 'W' in self.access:
            self.event('W', a, v)
        self.mem[a] = v >> 8
        self.mem[(a + 1) & 65535] = v & 255


memory = Memory(ROM)
cpu = CPU(memory)
cpu.max_trace = 0
required = resident_instructions((0x7ac7,))
coverage = set()
instructions = {pc: decode(ROM.read, pc) for pc in required}
accesses = {pc: ins.access() for pc, ins in instructions.items()}


def trace_operand(pc):
    memory.operand = None
    access = accesses[pc]
    if access is None:
        return
    ins = instructions[pc]
    address = ins.value
    if ins.mode == 'indexed_x':
        address = (cpu.s.x + address) & 65535
    elif ins.mode == 'indexed_y':
        address = (cpu.s.y + address) & 65535
    # C96A/C9F7 are resident named-RAM/calibration algorithms. The C8D6
    # conversion uses the same native tables and auxiliary range owner.
    if (0xc96a <= pc <= 0xc9bf or 0xc9f7 <= pc <= 0xcb14 or 0xf499 <= pc <= 0xf4dd
            or (0xc8d6 <= pc <= 0xc8fc and address != 0xb4)):
        return
    # The remaining native operands are individual, established named owners.
    if address in (2, 0x3b, 0x11a, 0x82d, 0xa5, 0xa7, 0x2f3, 0xa8) or pc in (0x7af4, 0x7afb):
        return
    if 0x3b0 <= address < 0x400:  # F436 stack locals
        return
    memory.operand, memory.access = address, access['access']


def stock(case):
    memory.mem[:] = IMAGE
    for a, v in case.initial().items():
        memory.mem[a] = v
    memory.events, memory.operand, memory.access = [], None, ''
    memory.fail, memory.action, memory.injected = case.fail, case.action, False
    cpu.s.sp, cpu.s.ccr = 0x3ff, 0xc0 | (0x10 if case.masked else 0)
    cpu.s.d, cpu.s.x, cpu.s.y = 0, 0, 0
    status = 0
    try:
        for pass_number in range(case.passes):
            if pass_number:
                memory.mem[2] = (memory.mem[2] + 16) % 160
            memory.operand = None
            cpu._push16(0x7000)
            cpu.s.pc = 0x7ac7
            for _ in range(6000):
                pc = cpu.s.pc
                if pc == 0x7000:
                    assert cpu.s.sp == 0x3ff
                    break
                coverage.add(pc)
                trace_operand(pc)
                op = instructions[pc].op
                if op in ('SEI', 'CLI'):
                    memory.event('m', 0, int(op == 'SEI'))
                cpu.step()
                if op == 'CLI' and case.action == 5 and not memory.injected:
                    memory.injected = True
                    memory.mem[0x11a] |= 0x80
                    memory.mem[0x32b] = (memory.mem[0x32b] + 1) & 255
            else:
                raise AssertionError(f'Slot 04 failed to return at ${cpu.s.pc:04X}')
    except Stop:
        status = 2
    state = [status, int(bool(cpu.s.ccr & 0x10)), *(memory.mem[a] for a in (0x16, 0x1d, 0x6f, 0x842))]
    return [*map(str, state), memory.mem[:0x350].hex(), *memory.events]


def slot_cases():
    # All ten ordinary admissions per 160-phase cycle, repeated in one retained run.
    for phase in range(4, 160, 16):
        yield Case(phase, stock_cal=True, passes=10)
    for phase, freeze, primary, secondary, load, action in product(
            (4, 20), (0, 4), (0, 1), (0, 128), (0, 0x10, 0xfb), (0, 3, 4, 6)):
        yield Case(phase, {0x3b: freeze, 0x16: primary, 0x17: secondary, 0x6f: load}, passes=2, action=action)
    for phase, input_addr, status, time, mask in (
            (4, 0x82d, 0x16, 0x160, 64), (4, 0x82d, 0x16, 0x161, 32),
            (20, 0xa5, 0x1b, 0x16c, 64), (20, 0xa5, 0x1b, 0x16d, 32),
            (4, 0x2f3, 0x1b, 0x16e, 4), (20, 0x2f3, 0x1b, 0x16f, 2)):
        for sample, age, initial in product((99, 100, 101), (0, 1, 254, 255), (0, mask)):
            yield Case(phase, {input_addr: sample, time: age, status: initial})
    for pattern, live, observed, budget, age in product(range(0, 0x32), (0, 7), (0, 7), (0, 2, 3, 255), (1, 255)):
        yield Case(4, {0x9e: pattern, 0x1d: live, 0x96: observed, **{a: budget for a in (0x2b, 0x2c, 0x2d)},
                       **{a: age for a in (0x17c, 0x17d, 0x17e)}})
    for sample, age, live, seen in product((99, 100, 101), (0, 1, 255, 256, 65534, 65535), (0, 0x18), (0, 255)):
        yield Case(20, word(0x169, age) | {0x16b: age & 255, 0xa7: sample, 0x1a: live, 0x95: seen, 0x97: seen})
    for rpm, live, age, sample, action in product((499, 500, 501), (0, 128), (0, 1, 255), (79, 80, 81), (0, 1)):
        yield Case(4, word(0x1ac, rpm) | {0x1d: live, 0x178: age, 0xb5: 0, 0xa7: sample,
                                           0x5b98: 80, 0x5b99: 60}, action=action)
    for flags, masked, action in product((0, 0x40, 0x80, 0xdf), (0, 1), (0, 5)):
        yield Case(20, {0x11a: flags}, passes=3, action=action, masked=masked)
    # All stock restore cells contain 80. Give each source a distinct byte,
    # permute its bank pointers and include checksum wrap and separate requests.
    pattern = {0x6a81 + i: (13 + 7*i) & 255 for i in range(51)}
    for order, flags, checksum in product(((0, 1, 2), (2, 0, 1)), (0x40, 0x80, 0xc0), (0, 1, 255)):
        edits = pattern | {0x11a: flags, 0x32b: checksum}
        for bank, source in enumerate(order):
            edits |= word(0xba32 + bank*2, 0x6a81 + 17*source)
        yield Case(20, edits, passes=2)
    # Overridden conversion knots exercise exact hysteresis bounds in both channels,
    # upper and lower coolant clamps, fallback selection, and environment underflow.
    for phase, temperature, selection, live in product((4, 20), (0, 15, 16, 79, 80, 106, 107, 120, 121, 192, 209, 255),
                                                       (0, 1, 2), (0, 0x20, 0x40)):
        edits = {0x43: 128 if selection == 2 else 0, 0x4e: 3 if selection == 1 else 0,
                 0xfc45+100: temperature, 0xfd45+100: temperature, 0x16: live, 0x1b: live,
                 0x5b2b: live, 0x5b30: live, 0x48e3: 255, 0x48e8: 255, 0x5b1a: temperature,
                 0x5b1b: temperature, 0x5b17: temperature, 0x5b6a: temperature,
                 0x3f: 0, 0x5d0b: 255, 0x5d0c: 255, 0x46e3: 1}
        yield Case(phase, edits | word(0xfd, selection) | word(0x5b18, 1))
    for coolant, hot, action in product((0, 59, 60, 61, 90, 119, 120, 121, 130, 131, 255),
                                         (0, 2, 255), (0, 1, 2)):
        yield Case(20, {0xa9: coolant, 0x87: hot, 0x6aba: 110, 0x6abb: 100}, action=action)
    rng = random.Random(0x317ac7)
    for i in range(420):
        edits = {a: rng.randrange(256) for a in (*range(0x16, 0x1f), *range(0x2b, 0x2e), 0x43, 0x4e,
                 0x6f, 0x87, 0x95, 0x96, 0x97, 0x9e, 0xa5, 0xa7, 0xa9, 0xb5, 0x82d, 0x2f3,
                 *range(0x160, 0x170), 0x178, 0x17c, 0x17d, 0x17e, *range(0x5b96, 0x5b9d))}
        edits.update({a: rng.randrange(256) for a in (0x5b00, 0x5b04, 0x5b05, 0x5b07, 0x5d04, 0x5d05,
                                                      0x5d34, 0x5d35, 0x5d36, 0x5d37)})
        yield Case(4 if i % 2 else 20, edits, passes=2, action=i % 7)


def failure_cases():
    for case in (Case(4, {0x16: 0x61, 0x1d: 7, 0x169: 255, 0xa7: 110}, masked=1),
                 Case(20, {0x11a: 0xc0, 0x1b: 0x20, 0x5b30: 0x20}, action=1),
                 Case(4, {0x17c: 1, 0x17d: 1, 0x6f: 255}, action=6)):
        stock(case)
        for index in range(1, len(memory.events) + 1):
            yield replace(case, fail=index)


def main():
    with tempfile.TemporaryDirectory(prefix='pcm-slot-04-') as directory:
        romfile = Path(directory) / 'bmhm.bin'
        romfile.write_bytes(IMAGE)
        args = (sys.argv[1], romfile, stock)
        count = compare(*args, slot_cases(), 'Scheduled phases and retained passes')
        missing = required - coverage
        assert not missing, sorted(f'{pc:04X}' for pc in missing)
        print(f'Scheduled cases reached all {len(required)} resident slot 04 instruction starts.', flush=True)
        count += compare(*args, failure_cases(), 'Failed provider transaction prefixes')
        print(f'{count:,} slot 04 C/ROM comparisons passed.')


if __name__ == '__main__':
    main()
