"""Compare $7C13 and its $3068 handoff with BMHM, retaining state over three ticks."""
import random
import subprocess
import sys

from slot_rom_replay import CPU, FixtureMemory, IMAGE, ROM, decode, resident_instructions, successors

INPUTS = (0x4c, 0x14e, 0xa7, 0x86, 0x8e, 0x14d, 0x14f, 0x150, 0x151,
          0x153, 0x154, 0xb5, 0xfc, *range(0x6e54, 0x6e59))
OUTPUTS = (0x14c, 0x14f, 0x150, 0x151, 0xfc, 0x86, 0x8e, 0x3068, 0x3069)


def cases():
    rng = random.Random(0x7c13)
    for index in range(1800):
        state = {addr: rng.randrange(256) for addr in INPUTS}
        state[0x86] &= 1
        if index % 5 == 0:
            state.update({a: IMAGE[a] for a in range(0x6e54, 0x6e59)})
        if index % 3 == 0:
            state.update({0x4c: 32, 0x86: 0, 0x8e: 0, 0x150: 14,
                          0x151: 0, 0x153: 0, 0x154: 0})
        if index % 7 == 0:
            state[0x14e] = (min(57, state[0x14d]) + index % 3 - 1) & 255
        yield state


def main(binary):
    states = list(cases())
    lines = [' '.join(str(state[a]) for a in INPUTS) for state in states]
    run = subprocess.run([binary, '--current'], input='\n'.join(lines) + '\n',
                         text=True, capture_output=True, check=True)
    actual = run.stdout.splitlines()
    assert len(actual) == len(states) * 3
    memory = FixtureMemory(ROM)
    cpu = CPU(memory)
    visited, edges = set(), set()
    for index, state in enumerate(states):
        memory.mem[:] = IMAGE
        for address, value in state.items():
            memory.mem[address] = value
        for tick in range(3):
            cpu.s.sp, cpu.s.ccr = 0x3ff, 0xc0
            cpu._push16(0x7000)
            cpu.s.pc = 0x7b9b
            for _ in range(160):
                pc = cpu.s.pc
                visited.add(pc)
                cpu.step()
                edges.add((pc, cpu.s.pc))
                if cpu.s.pc == 0x7000:
                    break
            assert cpu.s.pc == 0x7000 and cpu.s.sp == 0x3ff
            expected = [memory.mem[a] for a in OUTPUTS]
            result = list(map(int, actual[index * 3 + tick].split()))
            assert result == expected, (index, tick, state, expected, result)
    required = resident_instructions([0x7c13])
    assert required <= visited, sorted(hex(pc) for pc in required - visited)
    conditional = {(pc, target) for pc in required
                   for ins in [decode(ROM.read, pc)] if len(list(successors(ins))) == 2
                   for target, _ in successors(ins)}
    # CPD #0 cannot borrow, so $7C91 BCC always takes its branch.
    assert conditional - edges == {(0x7c91, 0x7c93)}, conditional - edges
    print(f'{len(actual)} comparisons, {len(required)} current-control instruction starts, '
          f'{len(conditional & edges)}/{len(conditional)} conditional outcomes')


if __name__ == '__main__':
    main(sys.argv[1])
