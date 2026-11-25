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
        if self.case.mutate == 5 and a == 0xde:
            return 8
        if self.case.mutate == 3 and a == 0xd9:
            self.mem[a] = 0
        if self.case.mutate == 2 and a == 0x70cf:
            self.mem[a] = 0
        if self.case.mutate == 1 and a == 0x70d1:
            self.limit_reads += 1
            if self.limit_reads == 2:
                self.mem[a] = 0
        return value

    def write(self, a, v, width):
        # The stack is private to the HC11 call. A4/015A are named C owners.
        if a not in OWNED and not 0x3c0 <= a < 0x400:
            assert a < 0x350, hex(a)
            self.events.append(f'b{a:04x}{v:02x}' if width == 1 else f'w{a:04x}{v:04x}')
            self.count += 1
            if self.count == self.case.fail:
                raise FailedWrite
        self.mem[a:a+width] = v.to_bytes(width, 'big')
        if self.case.mutate == 4 and a == 0xe1:
            self.mem[0x93] = 0

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
        if case.entry in (0xbc77, 0xb88d):
            cpu.s.a = memory.mem[0x142]
        if case.entry == 0xc271:
            cpu.s.x, cpu.s.y = 0x6db3, 0x10b
        if case.entry == 0xd969:
            cpu.s.x = 0x70e0
        try:
            for _ in range(1500):
                pc = cpu.s.pc
                if pc in (0xbc2a, 0xbc30):
                    memory.events.append('sei' if pc == 0xbc2a else 'cli')
                seen.add(pc)
                cpu.step()
                edges.add((pc, cpu.s.pc))
                if cpu.s.pc == 0x7000:
                    break
            assert cpu.s.pc == 0x7000 and cpu.s.sp == 0x3ff
            status = 'ok'
        except FailedWrite:
            status = 'failed'
        if status == 'ok' and case.entry == 0xd969:
            memory.events.append(f'd{cpu.s.d:04x}')
        if status == 'ok' and case.entry in (0xb91d, 0xbc77, 0xb88d):
            memory.events.append(f'a{cpu.s.a:02x}')
        memory.events.extend([status, memory.mem[:0x350].hex()])
        if status == 'failed':
            break
    return memory.events
