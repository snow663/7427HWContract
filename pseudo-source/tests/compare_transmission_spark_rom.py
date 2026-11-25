"""Run the five factory callees at $C4E5 in order, plus isolated mode/range/shift
entries. Compare retained RAM and ordered provider writes, including failed prefixes.
The shared HC11 interpreter uses logical RAM and calibrated ROM tables.
"""
from dataclasses import replace
from pathlib import Path
import random
import sys
import tempfile

from slot_rom_replay import IMAGE, ROM, compare, decode, successors
from transmission_group_replay import Case, edges, memory, seen, stock

ENTRIES = (0xc4e5, 0xd9b7, 0xda6f, 0xdae2)
SPANS = ((0xc4e5, 0xc4f5), (0xd9b7, 0xda6f), (0xda6f, 0xdae2), (0xdae2, 0xdbe3))


def cases():
    rng = random.Random(0xc4e5)
    states = [0x18,0x61,0x62,0x83,0x98,0x99,0x9c,0x9f,0xa2,0xa3,0xa4,0xa6,
              0xa9,0xb0,0xb1,0xb2,0xc2,0xc3,0xd7,0xd9,0xf7,0xf9,0x101,0x119,
              0x15a,0x15b,0x15c,0x15d,0x15e,0x162,0x163,0x1ac,0x1ad,0x1c0,
              0x2f6,0x2f7,*range(0x1a6,0x1ab)]
    for i in range(1800):
        data = {a: rng.randrange(256) for a in states}
        data[0xd9] %= 4
        if i % 5:
            data[0x119] = 0
        if i % 3:
            data[0x99] &= ~16
            data[0xa2] &= 15
            data[0xa4] &= 0x88
            data[0x83] &= 1
        if (i // len(ENTRIES)) % 2:
            data.update({a:rng.randrange(256) for a in range(0x70b2, 0x70d5)})
        if i % 11 == 0:
            data[0x15d] = data[0x15c] = 255
        entry = ENTRIES[i % 4]
        # Include joined retained histories as well as direct-entry states.
        case = Case(entry, data, 3 if entry == 0xc4e5 else 1)
        yield case
        if i % 43 == 0:
            stock(case)
            for fail in range(1, memory.count + 1):
                yield replace(case, fail=fail)

    for status, remaining, limit, ramp, floor in [
            (1, 0, 0, 0, 0), (0x14, 2, 3, 100, 200),
            (0x14, 1, 3, 200, 0), (0x10, 0, 0, 250, 0)]:
        yield Case(0xda6f, {0xa4:status, 0x61:65, 0x62:255, 0x15e:remaining,
                           0x70d2:limit, 0x55f3:ramp, 0x55f4:floor})
    yield Case(0xdae2, {0xa4:8, 0x83:8})
    # The second span read supplies zero after a successful rising-window
    # admission. IDIV saturates and the rising direction selects zero.
    yield Case(0xdae2, {0xa4:8, 0xd9:3, 0x15c:5, 0x70cf:20, 0x70ce:0}, mutate=2)
    # $DBBD can borrow only if the second age/upper comparison differs from
    # the earlier admission comparison. Change the last calibration read.
    yield Case(0xdae2, {0xa4:8, 0xd9:3, 0x15c:5, 0x70cf:1, 0x70d1:20}, mutate=1)


def main(binary):
    with tempfile.TemporaryDirectory() as temp:
        image = Path(temp) / 'bmhm.bin'
        image.write_bytes(IMAGE)
        compare(binary, str(image), stock, cases(), 'transmission spark')
    required, outcomes = set(), set()
    for start, end in SPANS:
        pc = start
        while pc < end:
            required.add(pc)
            ins = decode(ROM.read, pc)
            targets = list(successors(ins))
            if len(targets) == 2 and ins.op not in ('JSR', 'BSR'):
                outcomes.update((pc, dest) for dest, _ in targets)
            pc = ins.next_pc
        assert pc == end
    assert required <= seen, sorted(hex(p) for p in required - seen)
    assert outcomes <= edges, sorted((hex(a), hex(b)) for a,b in outcomes - edges)
    print(f'{len(required)} instruction starts, {len(outcomes)} conditional outcomes in the four translated entries')


if __name__ == '__main__':
    main(sys.argv[1])
