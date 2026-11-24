"""Compare scheduler slots 05 and 0A with the recorded BMHM instructions."""
from collections import defaultdict
from dataclasses import dataclass, field, replace
from itertools import product
from pathlib import Path
import random
import sys
import tempfile

from slot_rom_replay import CPU, FixtureMemory, IMAGE, ROM, compare, decode, resident_instructions, successors, word

ENTRIES = {5: 0x7b03, 10: 0x7b39}
RAM = {5: 0, 6: 120, 0x18: 0, 0x3e: 128, 0x41: 0x21, 0x46: 0, 0x4f: 128,
       0x52: 0x11, 0x62: 72, 0x78: 120, 0x79: 180, 0x7e: 1, 0x7f: 1, 0x82: 1,
       0x89: 0, 0x8a: 0x80, 0x8b: 0x80, 0x8c: 0x55, 0x8d: 0xaa, 0x98: 0x11, 0x99: 0,
       0x9c: 0, 0xa2: 0, 0xa8: 130, 0xa9: 140, 0xb5: 100, 0xb2: 40, 0xac: 128,
       0xd7: 100, 0xd9: 1, 0xe2: 100, 0x1c0: 130, 0x1c9: 40, 0x1d6: 99, 0x1d7: 127,
       0x1d8: 2, 0x1d9: 80, 0x20f: 128, 0x232: 48, 0x247: 1, 0x24a: 144,
       0x257: 100, 0x284: 80, 0x84c: 2} | word(0xfd, 0x1000) | word(0x126, 0x1234) | word(0x12b, 0x5678)
CAL = {0x400c: 128, 0x400e: 8, 0x400f: 0x10, 0x406d: 150, 0x406e: 85,
       0x406f: 125, 0x4070: 95, 0x4073: 3, 0x4074: 80, 0x4075: 75, 0x4076: 4,
       0x4024: 50, 0x4025: 3, 0x4026: 130, 0x4027: 126, 0x4028: 135,
       0x4029: 5, 0x402a: 7, 0x402b: 95, 0x402c: 150, 0x402f: 70,
       0x4030: 75, 0x4031: 90, 0x4032: 70, 0x4033: 70, 0x4034: 80, 0x4035: 75,
       0x4059: 1, 0x6ab4: 0, 0x6ab5: 0, 0x6aec: 110, 0x6aed: 120,
       0x412b: 60, 0x412c: 68, 0x412d: 78, 0x412e: 82, 0x412f: 73, 0x4130: 77,
       0x4131: 125} | word(0x402d, 350)
for table, pointer in ((0xc2d6, 0x5000), (0xc2f8, 0x5020), (0xc31a, 0x5040), (0xc33c, 0x5060),
                       (0xc3e6, 0x5100), (0xc3f8, 0x5120)):
    CAL |= {table: 0x80, table + 1: 8} | word(table + 4, pointer)
    CAL |= {pointer + i: (105 + 21 * i) & 255 for i in range(17)}


@dataclass
class Case:
    phase: int
    edits: dict = field(default_factory=dict)
    passes: int = 1
    joined: bool = False
    stock_cal: bool = False
    change: int = 0
    fail: int = 0

    def initial(self):
        return RAM | ({} if self.stock_cal else CAL) | self.edits | {2: self.phase}

    def row(self):
        edits = self.initial()
        params = [self.passes, int(self.joined), self.fail, self.change, len(edits)]
        return ' '.join(map(str, [*params, *(v for pair in edits.items() for v in pair)]))


class FailedAccess(Exception):
    pass


class Memory(FixtureMemory):
    def event(self, op, a, value):
        self.events.append(f'{op}{a:04x}{value:04x}')
        if self.case.fail == len(self.events):
            raise FailedAccess

    def read8(self, a):
        value = self.mem[a]
        if a == self.operand and 'R' in self.access:
            self.event('r', a, value)
            if self.case.change == 1 and a == 0x4091:
                self.mem[a] = (value + 1) & 255
            if self.case.change == 2 and a == 0x1d8:
                self.mem[a] = (value + 1) & 255
            if self.case.change == 3 and a == 0x128:
                self.mem[a] ^= 15
            if self.case.change == 4 and a == 0x6aec:
                self.mem[0x89] ^= 0x40
        return value

    def read16(self, a):
        value = (self.mem[a] << 8) | self.mem[(a + 1) & 65535]
        if a == self.operand and 'R' in self.access:
            self.event('R', a, value)
            if self.case.change == 5 and 0x4036 <= a <= 0x40ff:
                self.mem[a] ^= 0x37
        return value

    def write8(self, a, value):
        if a == self.operand and 'W' in self.access:
            self.event('w', a, value)
            self.mem[a] = value
            if self.case.change == 6 and a == 0x1d6 and not self.injected:
                self.injected = True
                self.mem[0x232] ^= 0xf0
            if self.case.change == 7 and a == 0x52:
                self.mem[0x400f] ^= 0x40
            if self.case.change == 8 and a == 0x7c:
                self.mem[0x232] ^= 0xf0
        else:
            self.mem[a] = value

    def write16(self, a, value):
        if a == self.operand and 'W' in self.access:
            self.event('W', a, value)
        self.mem[a] = value >> 8
        self.mem[(a + 1) & 65535] = value & 255


memory = Memory(ROM)
cpu = CPU(memory)
cpu.max_trace = 0
required = {slot: resident_instructions((entry,)) for slot, entry in ENTRIES.items()}
seen = {slot: set() for slot in ENTRIES}
branch_exits = {slot: defaultdict(set) for slot in ENTRIES}
instructions = {pc: decode(ROM.read, pc) for pc in required[5] | required[10]}
accesses = {pc: ins.access() for pc, ins in instructions.items()}
edges = {pc: {target for target, _ in successors(ins)} for pc, ins in instructions.items()}
branches = {pc: targets for pc, targets in edges.items() if len(targets) == 2}
# These instructions sample canonical named RAM/calibration. The rest of the
# externally addressed operands are compared with the C provider, in order.
named_reads = {
    0x7b0c, 0xd3b3, 0xd3ba, 0xd3c0, 0xd3c7, 0xd3d4, 0xd3ec, 0xd3f8, 0xd403, 0xd438,
    0xd475, 0xd482, 0xd489, 0xd493, 0xc6c7, 0xc6d6, 0xc6e1, 0xc70e, 0xc7cf, 0xc832, 0xc844,
    0xd2b2, 0xd2b9, 0xd2c0, 0xd2c7, 0xd2d7, 0xd2db, 0xd2ec, 0xd2f9, 0xd307, 0xd30e,
    0xd318, 0xd320, 0xd324, 0xd32c, 0xd342, 0xd369, 0xd384, 0xd396,
}


def trace_operand(pc):
    memory.operand = None
    access = accesses[pc]
    if access is None or pc in named_reads:
        return
    ins = instructions[pc]
    address = ins.value
    if ins.mode == 'indexed_x':
        address = (cpu.s.x + address) & 65535
    elif ins.mode == 'indexed_y':
        address = (cpu.s.y + address) & 65535
    if 0x3b0 <= address < 0x400:
        return  # HC11 stack locals
    memory.access = access['access']
    if 0xc6bb <= pc <= 0xc8b0 and address in (0x8a, 0x8b):
        memory.access = memory.access.replace('R', '')  # C514 and C6BB share named owners
    memory.operand = address


def stock(case):
    m = memory.mem
    m[:] = IMAGE
    for a, v in case.initial().items():
        m[a] = v
    memory.case, memory.events, memory.injected = case, [], False
    cpu.s.sp, cpu.s.ccr = 0x3ff, 0xc0
    cpu.s.d, cpu.s.x, cpu.s.y = 0, 0, 0
    phase, status = case.phase, 0
    try:
        for _ in range(case.passes):
            for admission in ((phase, phase + 5) if case.joined else (phase,)):
                m[2] = admission
                slot = admission & 15
                memory.operand = None
                cpu._push16(0x7000)
                cpu.s.pc = ENTRIES[slot]
                for _ in range(4000):
                    pc = cpu.s.pc
                    if pc == 0x7000:
                        assert cpu.s.sp == 0x3ff
                        break
                    seen[slot].add(pc)
                    trace_operand(pc)
                    cpu.step()
                    if pc in branches:
                        branch_exits[slot][pc].add(cpu.s.pc)
                else:
                    raise AssertionError(f'Slot {slot:02X} failed to return at ${cpu.s.pc:04X}')
            phase = (phase + 16) % 160
    except FailedAccess:
        status = 2
    owners = [status, int(bool(m[0x52] & 0x40)), m[0x8b], m[0x8a],
              int.from_bytes(m[0x126:0x128], 'big'), int.from_bytes(m[0x12b:0x12d], 'big'), m[0x89]]
    return [*map(str, owners), m[:0x350].hex(), f'{m[0x84c]:02x}', *memory.events]


def catalyst_cases():
    # With electronic TCC disabled, isolate catalyst and manifold thresholds.
    skip_tcc = {0x400f: 0x50}
    for phase in range(5, 160, 16):
        for mode, running in product((0, 0x10, 0x40, 0x50), (0, 128)):
            yield Case(phase, {0x400f: mode, 0x4f: running})
    for throttle, rpm, age in product((79, 80, 81), (74, 75, 76), (0, 2, 3, 4, 254, 255)):
        yield Case(5, skip_tcc | {0x1d9: throttle, 0x62: rpm, 0x7e: age})
    # Zero gain holds the seeded estimate so all temperature and age edges
    # can be hit exactly without coupling the expected result to C math.
    for estimate, age, closed, initial in product((84, 85, 86, 94, 95, 96, 124, 125, 126, 150, 151),
                                                  (0, 1, 2, 3, 254, 255), (0, 128), (0, 64)):
        yield Case(5, skip_tcc | {0x232: 0, 0x4077: 0, 0x78: estimate, 0x84c: age, 0x3e: closed, 0x52: initial})
    for base, reaction, afr in product((0, 64, 220, 255), (0, 20, 127, 128, 190, 255), (106, 107, 108, 154, 155, 156)):
        yield Case(5, skip_tcc | {0x62: 0, 0x232: 0, 0x408f: 0, 0x4090: 0, 0x4092: base,
                                  0x24a: afr} | {0x4088 + i: reaction for i in range(7)})
    for initial, rpm, temp, throttle in product((0, 8), (59, 60, 61, 67, 68, 69, 78, 79, 82, 83),
                                               (124, 125), (73, 74, 77, 78)):
        yield Case(21, skip_tcc | {0x52: initial, 0x62: rpm, 0xa8: temp, 0x1d9: throttle})
    rng = random.Random(0xd3b0)
    for _ in range(260):
        yield Case(5, skip_tcc | {a: rng.randrange(256) for a in
                   (0x78, 0x79, 0x62, 0x232, 0x24a, 0x408f, 0x4090, 0x4091, 0x84c)})


def purge_cases():
    for phase in range(10, 160, 16):
        yield Case(phase, stock_cal=True, passes=10)
    for mode, dfco, temp, timer in product((0, 128), (0, 8), (94, 95, 96, 150, 151), (349, 350, 351)):
        yield Case(10, {0x400c: mode, 0x46: dfco, 6: temp} | word(0xfd, timer))
    for active, a, limit in product((0, 128), (0x284, 0x1d9, 0x257), (-1, 0, 1)):
        row = 0x4033 if active else 0x4030
        offset = {0x284: 0, 0x1d9: 2, 0x257: 1}[a]
        yield Case(10, {0x41: 0x25 | active, a: CAL[row + offset] + limit})
    for speed, index, enable in product((69, 70, 71, 80), (0, 1, 20, 255), (0, 1, 255)):
        yield Case(10, {0x284: speed, 0x247: index, 0x4058 + index: enable})
    for vacuum, ae, timer in product((49, 50, 51), (0, 64, 128, 192), (0, 2, 3, 4, 254, 255)):
        yield Case(10, {0x1c9: vacuum, 5: ae, 0x1d8: timer})
    for integrator, multiplier, timer in product((0, 125, 126, 127, 129, 130, 131, 255),
                                                (0, 6, 7, 8, 128, 249, 250, 251, 255), (2, 3)):
        yield Case(10, {0x20f: integrator, 0x1d7: multiplier, 0x1d8: timer})
    for closed, curve, floor, multiplier in product((0, 128), (0, 32, 128, 220, 255),
                                                    (0, 32, 128, 220, 255), (1, 128, 255)):
        yield Case(10, {0x3e: closed, 0x232: 0, 0x4036: curve, 0x4047: floor, 0x4028: multiplier, 0x1d7: multiplier})


def tcc_cases():
    # Use a held catalyst phase to vary individual electronic TCC inputs.
    for service, inhibit, state in product((0, 1, 99, 100, 101, 199, 200, 201, 255), (0, 4, 8, 12), (0, 4, 16, 20)):
        yield Case(21, {0x10a: service, 0x99: inhibit, 0x8a: state})
    all_inputs = {0x6ab4: 255, 0x6ab5: 255, 0x18c: 4, 0x18d: 4, 0x124: 4, 0x9c: 3,
                  0x6ab6: 180, 0x6ab7: 181, 0x6ab8: 182, 0x6ab9: 183, 0x6abf: 180,
                  0x6abc: 180, 0x89: 0xc0, 0x99: 4, 0x8b: 8}
    for options, gear, ranges, retained in product((0, 4, 255), (0, 1, 3), (0, 1, 2, 3, 4, 8, 15), (0, 1)):
        yield Case(21, all_inputs | {0x6ab5: options, 0xd9: gear, 0xa2: ranges, 0x8b: 8 | retained})
    for inputs in ({0x87: 2, 0xa2: 1}, {0x18d: 0}, {0x89: 0}, {0x9c: 0}):
        yield Case(21, all_inputs | inputs)
    yield Case(21, {0x6ab4: 1, 0x18c: 1, 0x99: 4, 0xd9: 3})
    yield Case(21, {0xc2d6: 0, 0x7f: 0})
    for sensor, first, second, mask in ((0xb5, 0x6ab8, 0x6ab9, 32), (0xa9, 0x6ab6, 0x6ab7, 64)):
        for value, held in product((99, 100, 101, 119, 120, 121), (0, 1)):
            yield Case(21, {0x6ab4: mask, first: 100, second: 120, sensor: value, 0x8b: held})
    for idx, held, temperature in product(range(1, 10), (0, 4), (100, 120, 150)):
        yield Case(21, {0x6ab5: 4, 0x15 + idx: 0x40, 0x5b33 + idx: 0, 0x5b2a + idx: 0x40,
                        0xe731 + idx: 0x40, 0x89: held, 0xb5: temperature, 0x6ac2: 100, 0x6ac3: 120})
    for faults, mask, retained, load in product((0, 0x10, 0x20, 0x30), (0, 0x10, 0x20, 0x30),
                                                (0, 0x40), (109, 110, 111, 119, 120, 121)):
        yield Case(21, {0x18: faults, 0x5b2d: mask, 0x89: retained, 0x1c0: load})
    for selector, kick, retained, gain in product((0, 1, 2, 4, 128), (0, 16), (0, 64), (0, 1, 2)):
        yield Case(21, {0x7f: selector, 0x9c: kick, 0x89: retained, 0x82: gain})
    for knot, gain, pressure, kick in product((0, 1, 120, 128, 220, 255), (0, 1, 127, 128, 129, 220, 255),
                                              (0, 1, 128, 254, 255), (0, 16)):
        yield Case(21, {0xb2: 0, 0x5000: knot, 0x5020: knot, 0x5100: gain, 0x5120: gain, 0xac: pressure, 0x9c: kick})
    for e2 in (0, 126, 127, 128, 129, 255):
        yield Case(21, {0xe2: e2})
    for held, gear, kick in product((0, 64), (0, 1, 3), (0, 16)):
        table = 0xc31a if held else 0xc2d6
        yield Case(21, {0x89: held, 0x9c: kick, 0xd9: gear} | word(table + 0x22 + 2 + 2 * gear, 0))
    for hold, brake, inhibit, gear in product((0, 1), (0, 1), (0, 4), (1, 3)):
        yield Case(21, {0x18e: hold, 0x9c: brake, 0x99: inhibit, 0xd9: gear})


def histories():
    for phase in range(5, 160, 16):
        yield Case(phase, passes=10, joined=True, stock_cal=True)
        yield Case(phase, passes=10, joined=True)
    for change in range(1, 9):
        yield Case(5, passes=5, joined=True, change=change)
    yield Case(21, {0x6ab5: 4, 0x8b: 8, 0x10a: 101}, 4, True)


def failure_cases():
    for case in (Case(5, change=1), Case(5, {0x400f: 0x50, 0x3e: 0}, change=5),
                 Case(21, {0x6ab4: 255, 0x6ab5: 255, 0x8b: 9, 0x89: 0xc0, 0xa2: 15,
                           0x18d: 1, 0x18c: 1, 0x124: 1, 0x9c: 3, 0x10a: 77}),
                 Case(21, {0x9c: 16, 0x5020: 220, 0x5120: 255, 0xac: 0}, change=3),
                 Case(21, {0x10a: 201, 0x8a: 20}), Case(21, {0x99: 8}),
                 Case(10, change=2), Case(10, {0x1d8: 4, 0x20f: 150}, change=6),
                 Case(10, {0x3e: 0}, change=5), Case(10, {0x400c: 0, 0x284: 0}),
                 Case(10, {6: 151} | word(0xfd, 350))):
        stock(case)
        for i in range(1, len(memory.events) + 1):
            yield replace(case, fail=i)


def main():
    with tempfile.TemporaryDirectory(prefix='slots-05-0a-') as directory:
        romfile = Path(directory) / 'bmhm.bin'
        romfile.write_bytes(IMAGE)
        args = (sys.argv[1], romfile, stock)
        count = 0
        for group in (catalyst_cases, purge_cases, tcc_cases, histories):
            count += compare(*args, group(), group.__name__)
        for slot, starts in required.items():
            missing = starts - seen[slot]
            assert not missing, (f'slot {slot:02X}', [f'{pc:04X}' for pc in sorted(missing)])
            targets = {pc: branches[pc] for pc in starts if pc in branches}
            for pc, exits in targets.items():
                assert exits == branch_exits[slot][pc], (f'slot {slot:02X} branch ${pc:04X}', exits - branch_exits[slot][pc])
            print(f'Slot {slot:02X} reached all {len(starts)} resident instruction starts '
                  f'and both exits at each of its {len(targets)} conditional branches.', flush=True)
        count += compare(*args, failure_cases(), 'Failed transaction prefixes')
        print(f'{count:,} slot 05/0A C/ROM comparisons passed.')


if __name__ == '__main__':
    main()
