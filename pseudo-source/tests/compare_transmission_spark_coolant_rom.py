"""Compare the final $C4E5 callee at $C40A against the original BMHM instructions."""
import random
import subprocess
import sys

from slot_rom_replay import CPU, FixtureMemory, IMAGE, ROM, decode, resident_instructions, successors


def main(binary):
    rng = random.Random(0xc40a)
    addresses = (0x119, 0xa4, 0x15a, 0xa9, *range(0x70b2, 0x70b8))
    cases = []
    for coolant in range(256):
        for status in (0, 8, 0x17, 0x1f):
            stock = list(IMAGE[0x70b2:0x70b8])
            for cal in (stock, [rng.randrange(256) for _ in stock]):
                cases.append([0, status, rng.randrange(256), coolant, *cal])
        cases.append([coolant, 0xff, 255, coolant, *stock])
    rows = [' '.join(map(str, case)) for case in cases]
    run = subprocess.run([binary, '--spark-coolant'], input='\n'.join(rows)+'\n',
                         text=True, capture_output=True, check=True)
    results = list(map(int, run.stdout.splitlines()))
    assert len(results) == len(rows)
    memory = FixtureMemory(ROM)
    cpu = CPU(memory)
    required = resident_instructions([0xc40a])
    visited, edges = set(), set()
    for case, result in zip(cases, results):
        for address, value in zip(addresses, case):
            memory.mem[address] = value
        cpu.s.sp, cpu.s.ccr = 0x3ff, 0xc0
        cpu._push16(0x7000)
        cpu.s.pc = 0xc40a
        for _ in range(80):
            pc = cpu.s.pc
            visited.add(pc)
            cpu.step()
            edges.add((pc, cpu.s.pc))
            if cpu.s.pc == 0x7000:
                break
        assert cpu.s.pc == 0x7000 and cpu.s.sp == 0x3ff
        assert memory.mem[0x15a] == result, (case, memory.mem[0x15a], result)
    conditional = {(pc, target) for pc in required
                   for ins in [decode(ROM.read, pc)] if len(list(successors(ins))) == 2
                   for target, _ in successors(ins)}
    assert required == visited and conditional <= edges
    print(f'{len(cases)} comparisons, {len(visited)} instruction starts, {len(conditional)} conditional outcomes')


if __name__ == '__main__':
    main(sys.argv[1])
