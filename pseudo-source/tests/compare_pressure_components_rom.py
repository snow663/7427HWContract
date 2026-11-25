"""BMHM pressure adaptive lookup, learning count, reaction mask, shift reduction and barometric factor."""
from dataclasses import replace
from itertools import product
from pathlib import Path
import random
import sys
import tempfile

from slot_rom_replay import IMAGE, ROM, compare, decode, successors, word
from transmission_group_replay import Case, edges, memory, seen, stock


def cases():
    rng = random.Random(0xbe5c)
    entries = (0xb88d, 0xbe5c, 0xbebc, 0xbf62)
    for i in range(2400):
        ram = {a:rng.randrange(256) for a in (0x83,0x84,0x85,0x87,0x89,0x8b,0x8e,
               0x99,0x9c,0xb2,0xb3,0xb5,0xd7,0xd9,0xe2,0xeb,0xec,0x142,0x147,
               0x18c,0x18d,0x18e,0x1ac,0x20c,0x22f,0x844,*range(0x11b,0x12f))}
        ram[0xd9] %= 4
        if (i//4) % 2:
            for a in (*range(0x6ab4,0x6aec), *range(0x5f16,0x5f53), *range(0x70a1,0x70b2)):
                ram[a] = rng.randrange(256)
        if (i//4) % 7 == 0:
            for a in (0x18c,0x124,0x18d,0x18e): ram[a] = 0
            for a in (0x11b,0x11c,0x11d,0x11e,0x12d,0x12e,0x125): ram[a] = 255
        case = Case(entries[i%4], ram, passes=3)
        yield case
        if i % 91 == 0:
            stock(case)
            for fail in range(1, memory.count+1):
                yield replace(case, fail=fail)
    # The rounded 0xFFFC intermediate carries beyond the command word.
    yield Case(0xc271, {0x6db3:0, 0x6db4:129, 0xb2:16, 0x6e2a:254})
    for i in range(900):
        ram = {a:rng.randrange(256) for a in (0x10b,0x10c,0xe2,0xb2,
               *range(0x6e2a,0x6e3b), *range(0x6db3,0x6dc4))}
        if i % 4: ram[0x10b] = 0
        yield Case(0xc271, ram)
    for gear, flags, throttle, reject in product(range(4), (0, 2, 3, 16),
                                                (0,7,8,15,16,128,247,248,255), (0,1)):
        edits = {0xd9:gear,0x83:flags,0xb2:throttle,0x91:reject,0x148:85,0x149:170}
        edits.update({a:(a*43+7)&255 for a in range(0x2f8,0x32b)})
        yield Case(0xb91d, edits, 2)
    yield Case(0xb91d, {0xd9:2,0x148:255,0x149:255,**word(0xbc67,0)})
    for gear, flags, coordinate in product((1,2,3), (0,0x20,0x40,0x60), (0,8,16)):
        bank = ROM.word(0xba5f + 2*(gear-1))
        ram = {0xd9:gear,0x93:flags|3,0x149:coordinate}
        if bank:
            ram[bank+coordinate] = 255
        yield Case(0xba38, ram, 3)
    for bank, bit, enabled, suppressed in product(range(1,10), (1,4,128), (0,1), (0,1)):
        yield Case(0xe664, {0x98:0x99,0x15+bank:bit,0x5b2a+bank:bit if enabled else 0,
                            0x5b33+bank:bit if suppressed else 0,0xe728+bank:bit})
    for gear, ratio, timer, pressure, amount in product(range(1,5), (99,100,101,200,201),
                                                         (0,1,2), (0,127,128,255), (0,1,128,255)):
        yield Case(0xbc77, {0xd9:gear,0x83:1,0x198:timer,0x199:amount,0x142:pressure,
                            0x5f06:timer,0x5f07:amount,0x5f08:timer,0x5f09:amount,
                            0x5f0a:timer,0x5f0b:amount,**word(0x68af,200),
                            **word(0x68b1,100),**word(0xf9,ratio)}, passes=2)
    yield Case(0xbc77, {0x83:0,0x198:1,0x142:127,0x199:255})
    for baro, gain in product(range(256), (0,1,63,64,127,128,129,254,255)):
        yield Case(0xd969, {0xac:baro,0x70e0:gain})
    for case in (Case(0xb91d,{0xd9:1}), Case(0xba38,{0xd9:2,0x93:32}), Case(0xe664,{}),
                 Case(0xbc77,{0x83:1,0xd9:2,**word(0xf9,65535)})):
        stock(case)
        for fail in range(1,memory.count+1):
            yield replace(case, fail=fail)


def main(binary):
    with tempfile.TemporaryDirectory() as temp:
        path = Path(temp) / 'bmhm.bin'
        path.write_bytes(IMAGE)
        compare(binary, str(path), stock, cases(), 'pressure components')
    required, conditional = set(), set()
    for start, end in ((0xb91d,0xb961), (0xba38,0xba5f), (0xe664,0xe674),
                       (0xbc77,0xbcc6), (0xd969,0xd980), (0xb88d,0xb91d),
                       (0xbe5c,0xbebc), (0xbebc,0xbf62), (0xbf62,0xc00b), (0xc271,0xc2d6)):
        pc = start
        while pc < end:
            required.add(pc)
            ins = decode(ROM.read, pc)
            targets = list(successors(ins))
            if len(targets) == 2 and ins.op != 'JSR':
                conditional.update((pc, dest) for dest,_ in targets)
            pc = ins.next_pc
    assert required <= seen, sorted(hex(p) for p in required-seen)
    # $BFA8 permits INCA only when A is strictly below an unsigned byte.
    assert conditional - edges == {(0xbfab,0xbfb8)}, sorted((hex(a),hex(b)) for a,b in conditional-edges)
    print(f'{len(required)} instruction starts, {len(conditional & edges)}/{len(conditional)} conditional outcomes')


if __name__ == '__main__':
    main(sys.argv[1])
