"""Replay the two final slow slots from their stock BMHM scheduler entries."""
from collections import defaultdict
from dataclasses import dataclass, field, replace
from itertools import product
from pathlib import Path
import random
import sys
import tempfile

from slot_rom_replay import CPU, FixtureMemory, IMAGE, ROM, compare, decode, resident_instructions, successors, word

ENTRIES = {12: 0x7b44, 13: 0x7b48}
RAM = {4: 8, 6: 125, 0x3e: 128, 0x4c: 0xd5, 0x4f: 0xc0, 0x61: 70, 0x62: 80,
       0x71: 0x40, 0xa7: 125, 0x1ae: 80, 0x1b4: 110, 0x1ba: 110, 0x1c6: 80, 0x1c9: 90,
       0x1d5: 120, 0x1d6: 117, 0x1d9: 70, 0x1de: 70, 0x20f: 128, 0x284: 75, 0x2f4: 132,
       0x82e: 180, 0x3034: 110, 0x21b: 1, 0x1d0: 120, 0x1d1: 0x87,
       0x3008: 0xa5, 0x3022: 0x15} | word(0xfd, 0x2010) | word(0x3ffc, 0x4405)
CAL = {0x400b: 2, 0x400c: 2, 0x400d: 2, 0x400e: 4, 0x400f: 0xc1,
       0x4e89: 0, 0x4e8a: 99, 0x4e8b: 45, 0x4e8c: 100, 0x4e8d: 3, 0x50dc: 85,
       0x4e2e: 1, 0x4e2f: 2, 0x4e30: 3, 0x4e31: 4,
       0x4e32: 5, 0x4e33: 3, 0x4e34: 5, 0x4e35: 60, 0x4e36: 190,
       0x4e37: 75, 0x4e38: 3, 0x4e39: 100, 0x4e3a: 95, 0x4e3b: 40, 0x4e3c: 100,
       0x4e3d: 125, 0x4e3e: 100, 0x4e3f: 3, 0x4e40: 110,
       0x4e41: 40, 0x4e42: 2, 0x4e43: 3, 0x4e44: 50, 0x4e47: 80, 0x4e48: 120,
       0x4e49: 180, 0x4e4a: 2, 0x4e4b: 7, 0x4e4c: 3, 0x4e4d: 40, 0x4e4e: 150,
       0x4e4f: 30, 0x4e50: 100, 0x4e51: 50, 0x4e52: 2, 0x4e53: 3, 0x4e54: 8,
       0x4e55: 2, 0x4e56: 8, 0x4e57: 50, 0x4e59: 90, 0x4e5a: 100, 0x4e5b: 3,
       0x4e5c: 90, 0x4e5f: 3, 0x4e60: 90, 0x4e61: 140, 0x4e62: 3, 0x4e63: 50,
       0x4e70: 40, 0x4e73: 2, 0x4e78: 85, 0x4e79: 2, 0x4e7a: 4, 0x4e7c: 100,
       0x4e7d: 160, 0x4e82: 95, 0x4e83: 45, 0x4e84: 4, 0x48f7: 12,
       0x48fd: 153, 0x48fe: 103, 0x5b01: 0x70, 0x5b02: 0x40, 0x5b03: 2, 0x5b12: 4,
       0x48be: 127} | word(0x4e45, 30) | word(0x4e5d, 0x0123) | word(0x4e7e, 0x101) | word(0x4e80, 0x203)


@dataclass
class Case:
    phase: int
    edits: dict = field(default_factory=dict)
    passes: int = 1
    joined: bool = False
    stock_cal: bool = False
    action: int = 0
    ready: int = 1
    masked: bool = False
    fail: int = 0

    def initial(self):
        return RAM | ({} if self.stock_cal else CAL) | self.edits | {2: self.phase}

    def row(self):
        edits = self.initial()
        params = [self.passes, int(self.joined), self.fail, self.action, self.ready, int(self.masked), len(edits)]
        return ' '.join(map(str, [*params, *(v for pair in edits.items() for v in pair)]))


class FailedAccess(Exception):
    pass


class Memory(FixtureMemory):
    def event(self, kind, a, v):
        self.events.append(f'{kind}{a:04x}{v:04x}')
        if self.case.fail == len(self.events):
            raise FailedAccess

    def read8(self, a):
        v = self.mem[a]
        if a == self.operand and 'R' in self.access:
            if a == 0x3030:
                self.polls += 1
                if self.case.ready and self.polls >= self.case.ready:
                    v |= 128
            self.event('r', a, v)
            if self.case.action == 1 and a == 0x4e38:
                self.mem[0x21c] = (self.mem[0x21c] + 1) & 255
            if self.case.action == 2 and a == 0x15f:
                self.mem[a] = (v + 1) & 255
            if self.case.action == 3 and a == 0x5b06:
                self.mem[0x5c] ^= 0x20
        return v

    def read16(self, a):
        v = self.mem[a] << 8 | self.mem[(a+1) & 65535]
        if a == self.operand and 'R' in self.access:
            self.event('R', a, v)
        return v

    def write8(self, a, v):
        if a == self.operand and 'W' in self.access:
            self.event('w', a, v)
            if a == 0x3030:
                self.polls = 0
            if self.case.action == 4 and a == 0x223:
                self.mem[0x70] ^= 8
            if self.case.action == 5 and a == 0x22b:
                self.mem[0x58] ^= 1
        self.mem[a] = v

    def write16(self, a, v):
        if a == self.operand and 'W' in self.access:
            self.event('W', a, v)
            if self.case.action == 6 and a == 0x3fda:
                self.mem[0x3b] |= 0x10
        self.mem[a] = v >> 8
        self.mem[(a + 1) & 65535] = v & 255


memory = Memory(ROM)
cpu = CPU(memory)
cpu.max_trace = 0
required = {s: resident_instructions([entry]) for s, entry in ENTRIES.items()}
seen = {s: set() for s in ENTRIES}
taken = {s: defaultdict(set) for s in ENTRIES}
instructions = {pc: decode(ROM.read, pc) for pc in required[12] | required[13]}
accesses = {pc: ins.access() for pc, ins in instructions.items()}
edges = {pc: {target for target, _ in successors(ins)} for pc, ins in instructions.items()}
branches = {pc: exits for pc, exits in edges.items() if len(exits) == 2}

# Exact instructions supplied by named controller fields or typed calibrations.
# Native MAT, ADC flags, BLM cells and the MAP/EST owners are compared in state.
named_reads = {
    0xcc35, 0xcc39, 0xcc63, 0xccc7, 0xccd3, 0xccdb, 0xccf0, 0xccfb, 0xcd0a, 0xcd11,
    0xcd19, 0xcd1d, 0xcd2e, 0xcd40, 0xcd74, 0xcdab, 0xcdb0, 0xcdbd, 0xcdc4, 0xcdd1,
    0xcdd8, 0xcde5, 0xcdec, 0xdc8c, 0xdc93, 0xdca6, 0xdcb0, 0xdccd, 0xdcfb, 0xdd02,
    0xdd18, 0xdd4d, 0xdd5b, 0xdd75, 0xdd8a, 0xdd90, 0xdd94, 0xdd9b, 0xddc3, 0xddd3,
    0xdddb, 0xdde2, 0xddf3, 0xde07, 0xde15, 0xde2f, 0xde40, 0xde48, 0xde6a, 0xde75,
    0xde7c, 0xde9a, 0xdea7, 0xdeb4, 0xdebf, 0xded0, 0xdeef, 0xdf13, 0xdf25, 0xdf36,
    0xdf57, 0xdfd8, 0xdfdd, 0xdfe0, 0xdfed, 0xdff5, 0xe00d, 0xe011, 0xe015, 0xe019,
    0xe021, 0xe028, 0xe02d, 0xe058, 0xe068, 0xe087, 0xe09d, 0xe0b4, 0xe0bc, 0xe0e4,
    0xe0fd, 0xe103, 0xe12b, 0xe1c7, 0xe1cf, 0xe1db, 0xf25f, 0xf26e, 0xf271,
}


def trace_operand(pc):
    memory.operand = None
    access = accesses[pc]
    if (not access or pc in named_reads or 0xdc0d <= pc <= 0xdc88 or
            0xf28e <= pc <= 0xf2a9 or 0xf4c1 <= pc <= 0xf4dd):
        return
    ins = instructions[pc]
    address = ins.value
    if ins.mode == 'indexed_x':
        address = (cpu.s.x + address) & 65535
    elif ins.mode == 'indexed_y':
        address = (cpu.s.y + address) & 65535
    if 0x3b0 <= address < 0x400 and pc != 0xcc4b:
        return
    memory.operand = address
    memory.access = access['access']
    if pc == 0xcc79:
        memory.access = 'W'  # current output shadow is a named transmission owner


def stock(case):
    m = memory.mem
    m[:] = IMAGE
    for a, v in case.initial().items():
        m[a] = v
    memory.case, memory.events, memory.polls = case, [], 0
    cpu.s.sp, cpu.s.ccr = 0x3ff, (0xd0 if case.masked else 0xc0)
    cpu.s.d, cpu.s.x, cpu.s.y = 0, 0, 0
    phase, status, changed = case.phase, 0, False
    try:
        for _ in range(case.passes):
            for admission in ((phase, phase + 1) if case.joined else (phase,)):
                m[2] = admission
                slot = admission & 15
                memory.operand = None
                cpu._push16(0x7000)
                cpu.s.pc = ENTRIES[slot]
                for _ in range(6000):
                    pc = cpu.s.pc
                    if pc == 0x7000:
                        assert cpu.s.sp == 0x3ff
                        break
                    seen[slot].add(pc)
                    trace_operand(pc)
                    if pc in (0xcc59, 0xdbfe, 0xcc78, 0xdc09):
                        memory.event('m', 0, int(pc in (0xcc59, 0xdbfe)))
                    if pc == 0xf3ed:
                        memory.event('d', 0, 11)
                    cpu.step()
                    if case.action == 7 and pc in (0xcc78, 0xdc09) and not changed:
                        m[0x3034] ^= 0xe7
                        m[0x4c] ^= 0x20
                        changed = True
                    if pc in branches:
                        taken[slot][pc].add(cpu.s.pc)
                else:
                    raise AssertionError(f'Slot {slot:02X} failed to return at ${cpu.s.pc:04X}')
            phase = (phase + 16) % 160
    except FailedAccess:
        status = 2
    def flag(a, mask):
        return int(bool(m[a] & mask))
    owners = [m[0x282], m[0x1d5], m[0x4c], flag(0x41, 16), flag(0x53, 4), m[0x16], m[0x6f],
              flag(0x72, 128), flag(0x19, 4), flag(0x19, 8), flag(0x18, 32), flag(0x72, 64),
              flag(0x71, 4), flag(0x70, 4), flag(0x6e, 1), m[0x223], m[0x22c], m[0x205],
              m[0x206], flag(4, 128), flag(0x43, 16)]
    return [str(status), str(int(bool(cpu.s.ccr & 16))), bytes(owners).hex(), m[:0x350].hex(),
            m[0x800:0x900].hex(), m[0x3000:0x3070].hex(), m[0x3fc0:0x4000].hex(), *memory.events]


def refresh_and_outputs():
    for running, mode, sentinel, masked, action in product((0, 128), (0, 1), (0, 0xa5), (False, True), (0, 7)):
        yield Case(12, {0x4f: running, 0x400b: mode, 0x3b0: sentinel}, masked=masked, action=action)
    for running, switch, observed, sample in product((0, 128), (0, 128), (0, 16), (90, 170, 171, 255)):
        yield Case(13, {0x4f: running, 0x71: switch, 0x51: observed, 0xa7: sample}, passes=2)
    for service, request, duty in product((0, 16), (0, 4, 8, 16, 32, 60), (0, 17, 254, 255)):
        yield Case(13, {0x3b: service, 0x393: request, 0x394: duty, 0x1d6: 255-duty}, action=6)
    for air, held, request in product((0, 2), (0, 2), (0, 2)):
        yield Case(13, {0x400b: air, 0x3b: 16, 0x38f: held, 0x390: request})
    for phase, edited in product((13, 29), (
        {0x71: 1}, {6: 99}, {0x3d: 32, 0x279: 3}, {0x3d: 32, 0x279: 4}, {0x61: 100}, {0x1c6: 44},
        {0x50: 2}, {0x3e: 0}, {0x52: 8}, {0x41: 16}, {0x62: 85}, {0x89: 32, 0x53: 4})):
        for mode in (0, 1, 4, 0x40):
            yield Case(phase, edited | {0x400f: mode})
    for raw, previous, gain in product((0, 89, 255), (0, 0x807f, 0xff00), (0, 1, 128, 255)):
        yield Case(13, {0x1d5: raw, 0x4e89: gain} | word(0x1d0, previous))


def mat_and_display():
    for data, speed, counts, enables in product((0, 40, 180, 220, 255), (79, 80, 81), (2, 3), (0, 0x10, 0x40, 0x50)):
        yield Case(13, {0x3034: 255-data, 0x284: speed, 0x21d: counts, 0x21e: counts, 0x5b01: enables})
    for ready, flags in product((0, 1, 2, 11, 12, 13), (0, 2, 255)):
        yield Case(13, {0x1a: flags, 0x3a: flags}, ready=ready, masked=True, action=7)
    yield Case(13, word(0xfd, 30))
    yield Case(13, {0xfe45+i: 255-i*14 for i in range(17)})
    for phase, closed, disp, mirror in product((13, 29), (0, 64, 128, 192), (0, 8, 0x18, 0x40), (0, 128)):
        yield Case(phase, {0x50: 16, 0x3e: closed, 0x43: disp, 0x72: mirror})
    for run, held, age in product((9, 10, 255), (0, 2), (3, 4, 254, 255)):
        yield Case(13, {0x43: held, 0x14: age, 0x0b: 255, 0x13: 1} | word(0xfd, run))


def signal_monitors():
    # Centre each input window in CAL, then cross its boundary with one input.
    sweeps = {
        0x6f: (0, 4, 8, 16, 32, 64), 0x71: (0, 4, 64), 0x46: (0, 8), 0x15f: (0, 1, 3, 4, 5, 6, 255),
        0x1d5: (59, 60, 61, 189, 190, 191), 0x21c: (0, 1, 3, 4, 255), 6: (99, 100, 101),
        0x1d9: (69, 75, 76, 109, 110, 111), 0x284: (49, 50, 51, 94, 95, 96),
        0x817: (2, 3, 4, 255), 0x1c6: (124, 125, 126), 0x62: (39, 40, 41, 99, 100, 101),
        0x849: (0, 1), 0x81c: (2, 3, 4, 255), 0x288: (6, 7, 8), 0x5b01: (0, 32),
        0x2f4: (130, 140, 141), 0x82e: (130, 132, 133), 0x228: (2, 3, 4), 0x61: (40, 49, 50, 51),
        0x22c: (1, 2, 3), 0x205: (0, 1), 0x44: (0, 4), 0x4f: (128, 192), 0x50: (0, 8),
        0x3d: (0, 2), 0xa7: (89, 90, 91), 0x5b03: (0, 2), 0x856: (3, 4, 5, 254, 255),
    }
    for phase in (13, 29):
        for a, values in sweeps.items():
            for v in values:
                yield Case(phase, {a: v})
    for timer, age, run, dfco in product((0, 1, 5), (0, 1, 3, 4), (8, 9, 10, 11), (0, 8)):
        yield Case(13, {0x71: 0, 0x46: dfco, 0x15f: timer, 0x21c: age} | word(0xfd, run), action=2)
    yield Case(13, {0x4e84: 255, 0x856: 255})
    yield Case(13, {0x21c: 0}, action=1)


def egr_monitors():
    sweeps = {0x5b02: (0, 64), 0x70: (0, 1, 4, 8), 0x3e: (0, 128), 0x46: (0, 8), 0x21f: (1, 255),
              0x1ae: (49, 50, 90, 91), 0x1c9: (40, 41, 150, 151), 0x1d9: (30, 31, 100, 101),
              0x1de: (61, 62, 70, 78, 79), 0x284: (49, 50), 0x6e: (0, 1),
              0x20f: (115, 116, 127, 128, 140, 141), 0x220: (1, 2, 3, 255),
              0x1ba: (100, 101), 0x224: (2, 3, 4), 0x1b4: (89, 90)}
    for phase in (13, 29):
        for a, values in sweeps.items():
            for v in values:
                yield Case(phase, {a: v})
    for mode, base, wait, count in product((0, 2, 128, 130), (120, 121, 128, 129), (1, 2), (0, 1, 2, 3, 255)):
        yield Case(13, {0x400d: mode, 0x70: 4, 0x222: base, 0x221: wait, 0x223: count}, action=4)
    for stage, hold, timeout, passes in product((0, 8), (0x122, 0x123), (2, 3), (1, 2)):
        yield Case(13, {0x70: stage, 0x1b4: 89, 0x227: timeout, 0x224: 3} | word(0x225, hold), passes=passes)


def oxygen_monitors():
    for phase, fault, age, state in product((13, 29), (0, 64), (0, 2, 3, 4, 5, 255), (0, 1, 2, 3)):
        yield Case(phase, {0x1d0: 60, 0x72: fault, 0x219: age, 0x3e: (state & 1)*128, 0x71: (state & 2)*2,
                           0x2b3: 255, 0x2b4: 0, 0x2b5: 128} | word(0xfd, 10+(state & 1)))
    for phase, hot, throttle, age in product((13, 29), (0, 32), (44, 45, 95, 96), (0, 0x101, 0x102, 0x203, 0x204, 65535)):
        yield Case(phase, {0x1d0: 200, 0x44: hot, 0x1d9: throttle, 0x4e7c: 255} | word(0x21a, age))
    for state in ({0x71: 4}, {0x3e: 0}, {0x4e7c: 0}, {0x400c: 0}, {0x400e: 32, 0x19: 4}):
        yield Case(13, {0x1d0: 200} | state)


def reporting():
    for i, pending, live, mask, age in product(range(9), (0, 8), (0, 8), (0, 8), (0, 4, 255)):
        yield Case(13, {0x4f: 0, 0x56+i: pending, 0x16+i: live, 0x5b00+i: mask, 0x5b09+i: mask,
                         0x22b: age, 0x0b+i: 0x40}, action=3)
    for flags, inhibited, warm, run, latched in product((0, 1), (0, 16), (0, 8), (0, 8), (0, 2)):
        yield Case(13, {0x71: flags, 0x44: inhibited, 0x50: warm, 4: run, 0x4f: latched,
                        0x56: 4, 0x16: 4, 0x5b00: 4, 0x22b: 8}, action=5)
    for control, countdown, cursor, digit, latch in product((0, 0x40, 0x60, 0x61, 0x62), (0, 1, 2),
                                                             (0, 7, 8, 71, 72, 255), (0, 1), (0, 1)):
        yield Case(13, {0x4f: 0, 0x50: 16, 0x3c: control, 0x218: countdown, 0x216: cursor,
                        0x214: digit, 0x215: digit, 0x71: latch, 0x217: 0x80,
                        0x0c: 0x21, 0x5b01: 255})


def histories():
    # Follow code 12 and one retained fault at each end of the nine-byte bank
    # through all three repeats, then check the exact return to code 12.
    flash = Case(13, {0x4f: 0, 0x50: 16, 0x0b: 0x80, 0x5b00: 0x80, 0x13: 1, 0x5b08: 1}, passes=758)
    stock(flash)
    pairs = [e[5:] for e in memory.events if e.startswith('W0214')]
    assert pairs == ['0102']*3 + ['0103']*3 + ['0902']*3 + ['0102']
    yield flash
    for phase in range(12, 160, 16):
        yield Case(phase, passes=10, joined=True, stock_cal=True)
        yield Case(phase, passes=10, joined=True)
    for action in range(1, 8):
        yield Case(12, {0x393: 60, 0x1d0: 70, 0x4f: 128}, 5, True, action=action)
    rng = random.Random(0xcc35dc89)
    varied = (4, 6, 0x16, 0x17, 0x18, 0x19, 0x1a, 0x3c, 0x3e, 0x3d, 0x43, 0x44, 0x46,
              0x4f, 0x50, 0x51, 0x53, 0x6f, 0x70, 0x71, 0x72, 0x1d0, 0x1d1, 0x1d5, 0x1d9,
              0x214, 0x215, 0x216, 0x217, 0x218, 0x21a, 0x22b, 0x3034, 0x4e89, 0x400b,
              0x400c, 0x400d, 0x400e, 0x400f)
    for i in range(240):
        yield Case((i%10)*16+13, {a: rng.randrange(256) for a in varied}, passes=2)


def failure_cases():
    for case in (Case(12, {0x4f: 0, 0x3b0: 1}, action=7), Case(12, masked=True),
                 Case(13, {0x3b: 16, 0x393: 60, 0x1d0: 200, 0x70: 4, 0x222: 120, 0x3c: 64}, action=4),
                 Case(13, {0x14: 5, 0x1d0: 60, 0x72: 64, 0x3d: 32, 0x219: 5}, action=1),
                 Case(13, {0x4f: 0, 0x71: 0x80, 0x50: 16, 0x3c: 0x60, 0x218: 1, 0x13: 1, 0x5b08: 255}),
                 Case(13, {0x4f: 0, 0x56: 8, 0x16: 8, 0x5b00: 8, 0x22b: 6}, action=5, ready=0),
                 Case(13, {0x46: 8, 0x70: 8, 0x225: 1, 0x1d0: 200, 0x51: 16, 0xa7: 171}, action=2)):
        stock(case)
        for index in range(1, len(memory.events) + 1):
            yield replace(case, fail=index)


groups = (refresh_and_outputs, mat_and_display, signal_monitors, egr_monitors, oxygen_monitors, reporting, histories)


def coverage():
    for s, starts in required.items():
        missing = starts - seen[s]
        partial = {pc: sorted(exits - taken[s][pc]) for pc, exits in branches.items()
                   if pc in starts and exits - taken[s][pc]}
        assert not (missing or partial), (f'slot {s:02X}', sorted(hex(pc) for pc in missing),
                                          {hex(pc): [hex(x) for x in xs] for pc, xs in sorted(partial.items())})
        n = sum(pc in branches for pc in starts)
        print(f'Slot {s:02X} reached all {len(starts)} resident instruction starts and both exits '
              f'at each of its {n} conditional branches.', flush=True)


def main():
    with tempfile.TemporaryDirectory(prefix='slots-0c-0d-') as directory:
        path = Path(directory) / 'bmhm.bin'
        path.write_bytes(IMAGE)
        args = (sys.argv[1], path, stock)
        count = sum(compare(*args, group(), group.__name__) for group in groups)
        coverage()
        count += compare(*args, failure_cases(), 'Failed transaction prefixes')
        print(f'{count:,} slot 0C/0D C/ROM comparisons passed.')


if __name__ == '__main__':
    main()
