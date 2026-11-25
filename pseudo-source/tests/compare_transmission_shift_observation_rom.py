"""BMHM $B334 movement and $E654 reaction mask against their C entry points."""
from dataclasses import replace
from itertools import product
from pathlib import Path
import sys
import tempfile

from slot_rom_replay import IMAGE, ROM, compare, decode, successors, word
from transmission_group_replay import Case, edges, memory, seen, stock


def cases():
    signals = (0x1ac, 0xd3, 0xc6)
    for deltas, flag, count, delay in product(product((-1, 0, 1), repeat=3),
                                             (0x45, 0xc5), (0, 9, 254, 255), (0, 10, 255)):
        ram = {0x86:flag, 0xff:count, 0x5d0e:delay}
        for i, (a, delta) in enumerate(zip(signals, deltas)):
            limit = ROM.word(0x5d23 + 2*i)
            ram.update(word(a, (limit + delta) & 65535))
        yield Case(0xb334, ram, passes=3)
    for bank, bit, active, suppressed, enabled in product(range(1, 10), (1, 4, 128),
                                                          (0, 1), (0, 1), (0, 1)):
        ram = {0x98:0xa7, 0x15+bank:bit if active else 0, 0x5b33+bank:bit if suppressed else 0,
               0x5b2a+bank:bit if enabled else 0, 0xe71f+bank:bit}
        yield Case(0xe654, ram)
    for case in (Case(0xb334, {0x86:15, **word(0x1ac, 65535)}),
                 Case(0xb334, {0x86:255, 0xff:18, 0x5d0e:1}),
                 Case(0xe654, {0x98:255})):
        stock(case)
        for fail in range(1, memory.count+1):
            yield replace(case, fail=fail)


def main(binary):
    with tempfile.TemporaryDirectory() as temp:
        path = Path(temp) / 'bmhm.bin'
        path.write_bytes(IMAGE)
        compare(binary, str(path), stock, cases(), 'shift movement and reaction gate')
    required, conditional = set(), set()
    for start, end in ((0xb334, 0xb367), (0xe654, 0xe664)):
        pc = start
        while pc < end:
            required.add(pc)
            ins = decode(ROM.read, pc)
            targets = list(successors(ins))
            if len(targets) == 2 and ins.op != 'JSR':
                conditional.update((pc, dest) for dest, _ in targets)
            pc = ins.next_pc
    assert required <= seen and conditional <= edges, (required - seen, conditional - edges)
    print(f'{len(required)} instruction starts, {len(conditional)} conditional outcomes')


if __name__ == '__main__':
    main(sys.argv[1])
