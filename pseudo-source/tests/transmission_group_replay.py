"""Shared logical RAM and provider-write oracle for transmission group replays."""
from dataclasses import dataclass
from slot_rom_replay import CPU, FixtureMemory, IMAGE, ROM

OWNED = {0xa4, 0x15a}

@dataclass
class Case:
    entry: int
    edits: dict
    passes: int = 1
    fail: int = 0
    mutate: int = 0

    def row(self):
        fields = [self.passes, self.fail, self.mutate, len(self.edits)]
        fields.extend(x for item in self.edits.items() for x in item)
        return f'{self.entry:x} ' + ' '.join(map(str, fields))


class FailedWrite(Exception):
    pass


class Memory(FixtureMemory):
    def read8(self, a):
        value = super().read8(a)
        if self.case.mutate == 2 and a == 0x70cf:
            self.mem[a] = 0
        if self.case.mutate == 1 and a == 0x70d1:
            self.limit_reads += 1
            if self.limit_reads == 2:
                self.mem[a] = 0
        return value

    def write(self, a, v, width):
        # The stack is private to the HC11 call. A4/015A are named C owners.
        if a not in OWNED and not 0x300 <= a < 0x400:
            assert a < 0x300, hex(a)
            self.events.append(f'b{a:04x}{v:02x}' if width == 1 else f'w{a:04x}{v:04x}')
            self.count += 1
            if self.count == self.case.fail:
                raise FailedWrite
        self.mem[a:a+width] = v.to_bytes(width, 'big')

    def write8(self, a, v):
        self.write(a, v & 255, 1)

    def write16(self, a, v):
        self.write(a, v & 65535, 2)


seen, edges = set(), set()
memory = Memory(ROM)
cpu = CPU(memory)


def stock(case):
    memory.mem[:] = IMAGE
    for a, v in case.edits.items():
        memory.mem[a] = v
    memory.case, memory.events = case, []
    memory.count = memory.limit_reads = 0
    cpu.s.sp, cpu.s.ccr = 0x3ff, 0xc0
    for _ in range(case.passes):
        cpu._push16(0x7000)
        cpu.s.pc = case.entry
        try:
            for _ in range(1500):
                pc = cpu.s.pc
                seen.add(pc)
                cpu.step()
                edges.add((pc, cpu.s.pc))
                if cpu.s.pc == 0x7000:
                    break
            assert cpu.s.pc == 0x7000 and cpu.s.sp == 0x3ff
            status = 'ok'
        except FailedWrite:
            status = 'failed'
        memory.events.extend([status, memory.mem[:0x300].hex()])
        if status == 'failed':
            break
    return memory.events
