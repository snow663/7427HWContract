"""Compare candidate C translations against actual BMHM instruction execution."""
from dataclasses import replace
from itertools import product
from pathlib import Path
import random
import sys
import tempfile
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tests'))
from slot_rom_replay import IMAGE, ROM, compare, decode, successors, word
from transmission_group_replay import Case, Memory, CPU, FailedWrite

class ClosureMemory(Memory):
    def write(self,a,v,width):
        if 0x800<=a<0x900:
            self.events.append(f'b{a:04x}{v:02x}' if width==1 else f'w{a:04x}{v:04x}')
            self.count+=1
            if self.count==self.case.fail: raise FailedWrite
            self.mem[a:a+width]=v.to_bytes(width,'big')
            return
        super().write(a,v,width)

memory = ClosureMemory(ROM)
cpu = CPU(memory)
seen, edges = set(), set()
pressure_trace=False
RANGES = ((0xb2b2,0xb2c9),(0xb2c9,0xb2ed),(0xb2ed,0xb319),
          (0xe5cf,0xe5f1),(0xe5f1,0xe60b),(0xe60b,0xe62d),(0xe6f5,0xe717))

def stock(case):
    memory.mem[:] = IMAGE
    for a,v in case.edits.items():
        memory.mem[a] = v
    memory.case, memory.events = case, []
    memory.count = memory.limit_reads = 0
    cpu.s.sp, cpu.s.ccr = 0x3ff, 0xc0
    for _ in range(case.passes):
        cpu._push16(0x7000)
        cpu.s.pc = case.entry
        if case.entry==0xe58c:
            cpu.s.y=0xb9
            cpu.s.x=int.from_bytes(memory.mem[0x350:0x352],'big')
            cpu.s.b=memory.mem[0x352]
        elif case.entry in (0xf420,0xf5a2):
            cpu.s.d=int.from_bytes(memory.mem[0x350:0x352],'big')
            cpu.s.x=int.from_bytes(memory.mem[0x352:0x354],'big')
            cpu.s.y=0x5d0d
        try:
            for _ in range(2500):
                pc=cpu.s.pc
                if pc in (0xaf74,0xafc4): memory.events.append('sei')
                if pc in (0xaf8f,0xafec): memory.events.append('cli')
                if pc==0xf3ed: memory.events.append('delay11')
                if pressure_trace and pc in (0xb5ac,0xb5e3,0xb5f2,0xb680,0xb68c,0xb68f,0xb6b9,0xb6bc,0xb6d6,0xb6e8):
                    print(f'ROM stage {pc:04x} A={cpu.s.a:02x} B={cpu.s.b:02x} X={cpu.s.x:04x}',flush=True)
                seen.add(pc)
                cpu.step()
                edges.add((pc,cpu.s.pc))
                if cpu.s.pc==0x7000: break
            assert cpu.s.pc==0x7000 and cpu.s.sp==0x3ff
            status='ok'
        except FailedWrite:
            status='failed'
        if status=='ok' and case.entry==0xb2b2:
            memory.events.append(f'x{cpu.s.x:04x}')
        if status=='ok' and case.entry in (0xe58c,0xf420,0xf5a2,0xbcc6):
            memory.events.append(f'd{cpu.s.d:04x}')
        memory.events.extend([status,(memory.mem[:0x350]+memory.mem[0x800:0x900]).hex()])
        if status=='failed': break
    return memory.events

def cases():
    rng=random.Random(0xb2ed)
    for gear,range_bit,fault in product(range(256),(0,0x20),(0,4)):
        yield Case(0xb2b2,{0xd9:gear,0xa2:range_bit,0x98:fault})
    for gear,flags,num,den in product((0,3,255),(0,0x20),(0,1,3,4,5,0xffff),(0,1,2,0x7fff,0xffff)):
        edits={0xd9:gear,0x89:flags,0x9a:0xa5}
        edits.update(word(0xc2,num))
        edits.update(word(0xd3,den))
        edits.update(word(0x1ac,num))
        yield Case(0xb2c9,edits,2)
    for temp,old in product(range(256),(0,1,2,3,4,5,6,7,8,127,128,255)):
        yield Case(0xb2ed,{0xb5:temp,0x152:old},2)
    for entry in (0xe5cf,0xe60b,0xe6f5):
        for first,second,sup1,sup2,ena1,ena2 in product((0,255),repeat=6):
            yield Case(entry,{0x16:first,0x17:first,0x1c:second,0x98:0xa5,
                              0x5b34:sup1,0x5b35:sup1,0x5b3a:sup2,
                              0x5b2b:ena1,0x5b2c:ena1,0x5b31:ena2})
        # Independent second-bank admission for E5CF.
        yield Case(entry,{0x16:0,0x17:255,0x1c:255,0x5b34:0,0x5b35:0,
                          0x5b2b:255,0x5b2c:255,0x5b3a:0,0x5b31:255})
    for mask,live,flags,mode in product((0,8,16,24,255),(0,8,16,24,255),(0,128),(0,1,255)):
        yield Case(0xe5f1,{0x5b2f:mask,0x1a:live,0x86:flags,0x100:mode,0x99:0xa5})
    for i in range(700):
        entry=RANGES[i%len(RANGES)][0]
        edits={a:rng.randrange(256) for a in (0xa2,0x98,0x99,0x9a,0xd9,0x89,0xb5,0x152,
            0xc2,0xc3,0xd3,0xd4,0x1ac,0x1ad,0x16,0x17,0x1a,0x1c,0x86,0x100,
            0x5b34,0x5b35,0x5b3a,0x5b2b,0x5b2c,0x5b31,0x5b2f)}
        case=Case(entry,edits,3)
        yield case
        if i%7==0:
            stock(case)
            for fail in range(1,memory.count+1):
                yield replace(case,fail=fail)
    for case in (Case(0xb2c9,{0xd9:3,0x89:0},3), Case(0xb2ed,{0xb5:255},3),
                 *(Case(e,{},3) for e in (0xe5cf,0xe5f1,0xe60b,0xe6f5))):
        stock(case)
        for fail in range(1,memory.count+1):
            yield replace(case,fail=fail)

def main(binary):
    with tempfile.TemporaryDirectory() as temp:
        path=Path(temp)/'bmhm.bin'
        path.write_bytes(IMAGE)
        compare(binary,str(path),stock,cases(),'resident closure batch 1')
    required,conditional=set(),set()
    for start,end in RANGES:
        pc=start
        while pc<end:
            required.add(pc)
            ins=decode(ROM.read,pc)
            targets=list(successors(ins))
            if len(targets)==2:
                conditional.update((pc,dest) for dest,_ in targets)
            pc=ins.next_pc
        assert pc==end
    print(f'{len(required & seen)}/{len(required)} instruction starts; '
          f'{len(conditional & edges)}/{len(conditional)} conditional outcomes')
    assert required<=seen, sorted(hex(p) for p in required-seen)
    assert conditional<=edges, sorted((hex(a),hex(b)) for a,b in conditional-edges)

if __name__=='__main__':
    main(sys.argv[1])
