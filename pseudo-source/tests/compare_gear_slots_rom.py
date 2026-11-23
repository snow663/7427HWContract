"""Replay whole BMHM slots 03 and 0B, with focused witnesses for their shared helpers."""
from dataclasses import dataclass, field, replace
from itertools import product
from pathlib import Path
import random
import sys
import tempfile

from slot_rom_replay import CPU, FixtureMemory, IMAGE, ROM, compare, decode, resident_instructions, word

OBSERVED = (0x83, 0x84, 0x85, 0x98, 0x99, 0xd9, 0x103, 0x135, 0x187, 0xf00, 0x306a, 0x306b)
OWNERS = (0xd9, 0x99, 0x103, 0x4c, 0x8b)
SLOTS = {3: (0x7abd,), 11: (0x7b3d,), 0: (0x7abd, 0x7b3d, 0x7abd)}
BASE = {0x80: 1, 0x81: 1, 0x82: 2, 0x83: 0, 0x84: 0xa5, 0x85: 0x20,
        0x98: 4, 0x99: 0, 0x9c: 0, 0xab: 128, 0xac: 128, 0xb2: 80,
        0xd7: 75, 0xd9: 1, 0x125: 64, 0x126: 0xa5, 0x127: 0x40,
        0x12b: 0x91, 0x12c: 0x20, 0x8a: 4, 0x8b: 0x82, 0x1ac: 0x70,
        0x187: 0x5a, 0x4c: 0x44, 0xf00: 0x47, 0x306a: 0xee, 0x306b: 0x55}


@dataclass
class Case:
    entry: int
    edits: dict = field(default_factory=dict)
    x: int = 0
    d: int = 0
    module: int = 0  # absent / returns after writing service gear / fails
    fail: int = 0
    mutation: int = 0
    alternate: int = 0

    def row(self):
        edits = BASE | self.edits
        values = [self.entry, self.x, self.d, self.module, self.fail, self.mutation,
                  self.alternate, len(edits), *(v for pair in edits.items() for v in pair)]
        return ' '.join(map(str, values))


class StopAtTransaction(Exception):
    pass


class Memory(FixtureMemory):
    def event(self, kind, address, value):
        self.events.append(f'{kind}{address:04x}{value:04x}')
        if len(self.events) == self.case.fail:
            raise StopAtTransaction

    def read8(self, address):
        value = self.mem[address]
        if address == self.operand and 'R' in self.access:
            self.event('r', address, value)
            if self.case.mutation == 1 and address == 0x5d30:
                self.mem[0xd9] = 0
        return value

    def read16(self, address):
        value = (self.mem[address] << 8) | self.mem[(address + 1) & 65535]
        if address == self.operand and 'R' in self.access:
            self.event('R', address, value)
            if self.case.mutation == 2 and address == 0x5d6e:
                self.mem[address] ^= 0x3f
        return value

    def write8(self, address, value):
        if address == self.operand and 'W' in self.access:
            self.event('w', address, value)
        self.mem[address] = value

    def write16(self, address, value):
        if address == self.operand and 'W' in self.access:
            self.event('W', address, value)
        self.mem[address] = value >> 8
        self.mem[(address + 1) & 65535] = value & 255


memory = Memory(ROM)
cpu = CPU(memory)
decoded = {}
coverage = set()


def trace_operand(pc):
    memory.operand = None
    if pc not in decoded:
        ins = decode(ROM.read, pc)
        decoded[pc] = (ins, ins.access())
    ins, access = decoded[pc]
    if access is None:
        return
    address = ins.value
    if ins.mode == 'indexed_x':
        address = (cpu.s.x + address) & 65535
    if ins.mode == 'indexed_y':
        address = (cpu.s.y + address) & 65535
    # HC11 stack locals correspond to C temporaries. C514's explicit
    # provider transaction is STD $306A. Its other observable writes are
    # named fields compared individually below.
    if 0x3b0 <= address < 0x400 or (0xc514 <= pc <= 0xc56e and address != 0x306a):
        return
    memory.operand = address
    memory.access = access['access']


def stock(case):
    memory.case, memory.events, memory.operand = case, [], None
    memory.mem[:] = IMAGE
    for address, value in (BASE | case.edits).items():
        memory.mem[address] = value
    cpu.s.sp, cpu.s.ccr = 0x03ff, 0xc0
    cpu.s.x, cpu.s.y, cpu.s.d = case.x, case.x, case.d
    status = unresolved = result = 0
    try:
        for entry in SLOTS.get(case.entry, (case.entry,)):
            memory.operand = None
            cpu._push16(0x7000)
            cpu.s.pc = entry
            for _ in range(4000):
                pc = cpu.s.pc
                if pc == 0x7000:
                    assert cpu.s.sp == 0x03ff
                    break
                if pc == 0x1806:
                    if not case.module:
                        status = unresolved = 1
                        raise StopAtTransaction
                    memory.event('c', pc, 0)
                    if case.module == 2:
                        raise StopAtTransaction
                    memory.mem[0x103] = 4
                    cpu.s.pc = cpu._pull16()
                    continue
                coverage.add(pc)
                trace_operand(pc)
                cpu.step()
            else:
                raise AssertionError(f'${entry:04X} did not return, PC=${cpu.s.pc:04X}')
        if case.entry == 0xd8fe:
            result = cpu.s.x | (0 if cpu.s.ccr & 1 else 65536)
        elif case.entry == 0xd8a7:
            result = cpu.s.x
        elif case.entry in (0xd980, 0xd92e):
            result = cpu.s.d
    except StopAtTransaction:
        status = status or 2
    state = [status, unresolved, result, *(memory.mem[a] for a in (*OBSERVED, *OWNERS))]
    return [*map(str, state), *memory.events]


def slot_cases():
    # Production descriptors and calibration, including retained 03 -> 0B -> 03.
    for entry, gear, speed, selector, kick in product((3, 11, 0), (0, 1, 2, 3),
                                                     (0, 1, 63, 127, 254, 255), (0, 1, 2, 4), (0, 16)):
        yield Case(entry, {0xd9: gear, 0xd7: speed, 0x80: selector, 0x81: selector, 0x9c: kick})
    # Exercise each source override, equality on each speed comparison, the
    # kickdown RPM equality and bypass, and the two sentinels independently.
    for up, source, threshold, displacement in product((True, False), range(4), (0, 64, 255), (-1, 0, 1)):
        gear = 1 if up else 3
        column = gear if up else gear - 1
        edits = {0xd9: gear, 0xd7: max(0, min(255, threshold + displacement)),
                 0xab: 0, 0x82: 0, 0x9c: 0, 0x98: 4}
        if source == 0:
            edits[(0x104 if up else 0x107) + column] = threshold
        elif source == 1:
            edits |= {0xa2: 1, 0x98: 0, 0x0940: threshold}
            edits |= word((0xd763 if up else 0xd775) + 2 * column, 0x0940)
        elif source == 2:
            edits |= {0x9c: 16, (0x5d44 if up else 0x5d47) + column: threshold}
            edits |= word((0xd6bd if up else 0xd6d7) + 2 + 2 * column, 0)
            edits |= word(0x5d68 + 2 * column, 0x7000)
        else:
            curve = 0x6200
            edits |= word((0xd6bd if up else 0xd6d7) + 2 + 2 * column, curve)
            edits |= {curve + i: threshold for i in range(17)}
        for rpm in (0x6fff, 0x7000, 0x7001) if source == 2 and up else (0x7000,):
            yield Case(3 if up else 11, edits | word(0x1ac, rpm))
            yield Case(11 if up else 3, edits | word(0x1ac, rpm) | {0x99: 0x20}, alternate=1)

    for module, option, flags in product((0, 1, 2), (0, 0x40), (0, 0x40)):
        yield Case(0, {0x86: flags, 0x400f: option}, module=module)

    # Force cold-table absence, kickdown-main absence and a distinct floor.
    for up, selector in product((True, False), (0, 1, 2, 0x80)):
        column = 0 if up else 2
        edits = {0xd9: 0 if up else 3, 0x9c: 16, 0x81: selector}
        for table in ([0xd6d1, 0xd717, 0xd6f1] if up else [0xd6eb, 0xd73d]):
            edits |= word(table + 2 * column, 0)
        yield Case(3, edits)
        yield Case(11, edits | word((0xd6f7 if up else 0xd71d) + 2 + 2 * column, 0))

    # The narrow 2 -> 1 delay window depends on both timers and the prior
    # shift state. Check each strict boundary and the shorter alternate exit.
    for timer, busy, elapsed in product((3, 4, 7, 8), (0, 1), (9, 10)):
        edits = {0xd9: 2, 0x106: 255, 0x108: 200, 0xd7: 50, 0x83: 0x40, 0x135: timer,
                 0x5d32: 3, 0x5d33: 8, 0x118: busy, 0x134: elapsed, 0x5d31: 10}
        yield Case(11, edits)
    yield Case(3, {0xd9: 3, 0x109: 1, 0xd7: 200, 0xa2: 4, 0x197: 1})
    # Saturate both the additive cold RPM offset and the subsequent doubled gain.
    yield Case(3, {0xd9: 0, 0x9c: 16, 0xab: 255, 0x82: 2, 0xac: 0, 0x5d38: 1}
               | word(0x5d68, 0xfffb) | word(0x5d5c, 0x7fff))

    # D65A has to sample D9 again after its downshift-delay comparisons.
    yield Case(11, {0xd9: 3, 0x109: 200, 0xd7: 50, 0x5d30: 200, 0x125: 1}, mutation=1)
    yield Case(3, {0xd9: 0, 0xb2: 0, 0xd7: 250}, mutation=2)
    rng = random.Random(0x31d4eb)
    for n in range(1200):
        edits = {a: rng.randrange(256) for a in (0xd7, 0xb2, 0x83, 0x85, 0x87, 0x98, 0x99,
                 0x9c, 0x8a, 0x8b, 0x8e, 0xab, 0xac, 0x125, 0x134, 0x135, 0x118, 0x187, 0x39a, 0x39b)}
        for a in (0x80, 0x81, 0x82):
            edits[a] = rng.choice((0, 1, 2, 3, 4, 8, 16, 128, 255))
        edits |= {0xd9: rng.choice((0, 1, 2, 3, 4, 127, 128, 129, 254, 255)) if n % 5 == 0 else n % 4,
                  0xa2: rng.randrange(8), 0x103: rng.choice((0, 0, 0, 1, 2, 3, 4, 5, 255))}
        if n % 3 == 0:
            edits.update({a: rng.randrange(256) for a in range(0x104, 0x10a)})
        if n % 7 == 0:
            edits.update({a: rng.randrange(256) for a in range(0x16, 0x1f)})
        yield Case((3, 11, 0)[n % 3], edits, alternate=n % 2)


def helper_cases():
    # D8FE wraps ASLB before ABX, stops on the first selected null, and
    # retains its last cursor on a stop/overflow. Include 16-bit wrap at FFFF.
    for table, gear, selector, stop, stride in product((0x0940, 0xfffd), (0, 1, 127, 128, 255),
                                                      (0, 1, 2, 3, 128, 255), (0, 1, 2, 128), (0, 6, 255)):
        edits = {table: stop, (table + 1) & 65535: stride}
        yield Case(0xd8fe, edits, table, (selector << 8) | gear)
    for offset, gain, base in product((0, 1, 0x7fff, 0x8000, 0x8001, 0xff00, 0xffff),
                                      (0, 1, 127, 128, 255), (0, 1, 0x7fff, 0x8000, 0xfffe, 0xffff)):
        yield Case(0xd980, {0xab: gain}, base, offset)
    for knot, pressure, value in product((0, 1, 64, 127, 128, 129, 254, 255), (0, 1, 127, 128, 254, 255),
                                         (0, 1, 255, 256, 0x7fff, 0x8000, 0xffff)):
        edits = {0x82: 2, 0xd9: 0, 0x5d38: knot, 0xac: pressure}
        yield Case(0xd92e, edits, 0xd7af, value)
    for selector, cold in product((0, 1, 2, 128), (0, 0x7fff, 0x8000, 0xffff)):
        edits = {0x81: selector, 0x82: 0, 0xab: 255} | word(0x5d5c, cold)
        yield Case(0xd8a7, edits, 0xd6b7, 0)
        yield Case(0xd8a7, edits | word(0xd745, 0), 0xd6b7, 0)


def failures():
    # Run a failure at every attempted provider transaction of these distinct
    # successful paths. The ROM witness stops at the same read/write/callback.
    for case in (Case(3, {0x87: 2}), Case(11, {0xd9: 3, 0x9c: 16, 0x99: 8}),
                 Case(3, {0x86: 0x40, 0x9c: 16}, module=1), Case(3, {0xd9: 0, 0x9c: 16}),
                 Case(11, {0xd9: 2, 0xa2: 1, 0x98: 0, 0x103: 255})):
        stock(case)
        count = len(memory.events)
        for index in range(1, count + 1):
            yield replace(case, fail=index)


def main():
    with tempfile.TemporaryDirectory(prefix='pcm-gear-slots-') as directory:
        romfile = Path(directory) / 'bmhm-fixture.bin'
        romfile.write_bytes(IMAGE)
        args = (sys.argv[1], romfile, stock)
        total = compare(*args, slot_cases(), 'Whole slots and retained passes')
        required = resident_instructions((0x7abd, 0x7b3d), external={0x1806})
        assert coverage == required, (sorted(required - coverage), sorted(coverage - required))
        gear = resident_instructions((0xd4eb,))
        print(f'Whole slots reached all {len(required)} resident instruction starts, '
              f'including all {len(gear)} in the gear selector and its callees.')
        total += compare(*args, helper_cases(), 'Descriptor and arithmetic edges')
        total += compare(*args, failures(), 'Failed transaction prefixes')
    print(f'{total:,} C/ROM comparisons passed.')


if __name__ == '__main__':
    main()
