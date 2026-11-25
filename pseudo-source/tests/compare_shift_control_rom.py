"""Compare BMHM shift observation, adaptation and long-shift diagnosis with C.
Replay the parent and individual stages, comparing ordered stores, cell/checksum
critical sections and retained bytes through $032B, including failure prefixes.
"""
from dataclasses import replace
from itertools import product
from pathlib import Path
import random
import sys
import tempfile

from slot_rom_replay import IMAGE, ROM, compare, decode, successors, word
from transmission_group_replay import Case, edges, memory, seen, stock

SPANS = [(0xb32d, 0xb334), (0xb367, 0xb4b2), (0xb4b2, 0xb56b),
         (0xba65, 0xbc3b), (0xf131, 0xf1dd), (0xf1dd, 0xf20d)]


def cases():
    rng = random.Random(0xb32d)
    inputs = [0x16,0x17,0x1b,0x1c,0x1e,0x31,0x32,0x33,0x34,0x3b,0x83,0x85,0x86,
              0x87,0x8e,0x90,0x91,0x92,0x93,0x96,0x98,0x9a,0x9c,0x9f,0xa0,0xa1,
              0xa2,0xac,0xb2,0xb5,0xd7,0xd9,0xda,0xdb,0xdc,0xdd,0xdf,0xe0,0xf9,
              0xfa,0x113,0x114,0x136,0x137,0x138,0x148,0x149,0x187,0x188,0x195,
              0x19a,0x19b,0x19c,0x19d,0x19e,*range(0x2f8,0x32c)]
    entries = [0xb32d,0xb367,0xb4b2,0xba65,0xf131]
    for i in range(3500):
        ram = {a:rng.randrange(256) for a in inputs}
        ram[0xd9] = rng.choice([1,2,3])
        if i % 7:
            ram.update({0x113:0,0x86:8,0x149:rng.randrange(20),0x90:0,0x91:0,0x92:0,
                        0x83:rng.choice([0,1,2,8,0x10,0x11]),0x85:rng.choice([0,2]),
                        0x9a:rng.choice([0,2]),0x114:rng.choice([0,1,32,128,255])})
        if i % 3:
            ram.update({0x3b:0,0x5b08:4,0x1e:0,0x96:0x40})
        if i % 11 == 0:
            ram.update({0xdb:254,0xda:255})
        if i % 13 == 0:
            ram[0x19a] = ram[0x19b] = 255
        if (i // 5) % 2:
            ram.update({a:rng.randrange(256) for a in range(0x68a8,0x68d3)})
        entry = entries[i % len(entries)]
        yield Case(entry, ram, 3 if entry == 0xb32d else 1)

    # Exercise every long-shift gate with an admitted gear, independently
    # of whether the stock adaptive pressure curves admit the diagnostic.
    for gear, block, counter in product((1,2,3), range(12), (0,1,255)):
        ptr = ROM.word(0xbc6b + 2*(gear-1))
        ram = {0xd9:gear,0x5b08:4,0x96:64,0x148:4,0x136+gear-1:255,
               0x5bc4+gear-1:0,0x5bc7+gear-1:2,0x32+gear-1:counter,
               ptr:128,ptr+1:128,0xb5:32,0xb2:0,0xd7:32,0x5bc1:32,0x5bc2:0,0x5bc3:32}
        if block < 10:
            a,v = [(0x1b,64),(0x1b,32),(0xb5,31),(0x16,1),(0x17,128),
                   (0x5bc2,1),(0x17,32),(0x1c,4),(0x1c,1),(0xd7,31)][block]
            ram[a] = v
        yield Case(0xf131, ram, passes=3)

    yield Case(0xb4b2, {0x68b8:20,0xdb:20,0xda:19,0xd9:1})
    for count, limit, fault in ((254,255,4), (1,1,4), (5,6,0)):
        yield Case(0xf131, {0x5b08:4,0x96:0,0x31:count,0x5bca:limit,0x1e:fault})
    curve = ROM.word(0xbc59)
    for measured in (0,127,255):
        yield Case(0xba65, {0xd9:1,0x68a8:2,0x19c:measured,curve:32,curve+1:32})
    yield Case(0xb367, {0xd9:0, 0x68b5:10})
    learning = {0xd9:1,0x149:2,0x114:80,0xdb:80,0xda:0,0xdf:1,
                0x68a8:1,0x699f:0,0x69eb:0,0x6a16:255}
    yield Case(0xba65, learning | {0x113:1})
    yield Case(0xba65, learning)  # $0086.3 blocks the final cell update.
    # Re-sample the classification after E1 publication, and the stored phase
    # at the negative headroom cap. Neither alternate branch is reachable
    # with uninterrupted, stable RAM on this path.
    yield Case(0xba65, learning, mutate=4)
    yield Case(0xba65, learning, mutate=5)
    # Drive a lower-ratio crossing through the parent, into each learned bank,
    # through the checksum store and out to a completed shift on the next tick.
    for gear in (1, 2, 3):
        ram = learning | {0xd9:gear, 0x86:8, 0x85:2, 0x83:2, 0x149:6,
                          0xdb:79, 0x68ca+gear:0, 0x32b:0x97}
        ram.update(word(0x68a9 + 2*(gear-1), 65535))
        ram.update(word(0x68af + 2*(gear-1), 1))
        case = Case(0xb32d, ram, 2)
        expected = stock(case)
        assert expected.count('sei') == expected.count('cli') == 5
        assert sum(e.startswith('b032b') for e in expected) == 5
        assert memory.mem[0x85] & 128
        yield case
        stock(case)
        for fail in range(1, memory.count+1):
            yield replace(case, fail=fail)
    base = {0xd9:1,0x96:64,0x5b08:4,0x148:1,ROM.word(0xbc6b):128}
    yield Case(0xf131, base, mutate=3)
    for g in (0,4,129):
        yield Case(0xf131, base | {0xd9:g})
    # Saturating multiply-by-eight, almost-full average, and the progression
    # of low-cell coordinate, headroom and retained checksum over repeated calls.
    for scaled in (0x20,0x40,0x80):
        yield Case(0xf131, base | {0x148:scaled})
    for i in range(300):
        ram = {0xd9:1+i%3,0x86:8,0x149:i%19,0x114:80,0xdb:80,0xda:0,
               0xdf:rng.choice([0,1,5,15,16]),0xe0:rng.choice([0,1,5,15,16]),
               0x68a8:1,0x699f+i%3:0,0x69e3+8:rng.randrange(256),
               0x69f4+8:rng.randrange(256),0x6a05+8:rng.randrange(256)}
        ram.update({a:rng.randrange(256) for a in range(0x2f8,0x32c)})
        case = Case(0xba65, ram, 2)
        yield case
        if i % 41 == 0:
            stock(case)
            for fail in range(1, memory.count+1):
                yield replace(case, fail=fail)


def main(binary):
    with tempfile.TemporaryDirectory() as temp:
        path = Path(temp) / 'bmhm.bin'
        path.write_bytes(IMAGE)
        compare(binary, str(path), stock, cases(), 'joined shift control and component entries')
    required, conditional = set(), set()
    for start, end in SPANS:
        pc = start
        while pc < end:
            required.add(pc)
            ins = decode(ROM.read, pc)
            targets = list(successors(ins))
            if len(targets) == 2 and ins.op not in ('JSR','BSR'):
                conditional.update((pc, dest) for dest, _ in targets)
            pc = ins.next_pc
        assert pc == end
    assert required <= seen, sorted(hex(p) for p in required - seen)
    assert conditional <= edges, sorted((hex(a),hex(b)) for a,b in conditional - edges)
    print(f'{len(required)} instruction starts, {len(conditional)} conditional outcomes across six entries')


if __name__ == '__main__':
    main(sys.argv[1])
