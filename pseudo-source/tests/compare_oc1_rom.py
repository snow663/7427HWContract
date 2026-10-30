"""Compare OC1's compiled C with actual stock interrupt entry/body/RTI.

Counter samples are coherent fixture words, not a physical knock device model.
Calibration variants change only the selected direct-index table entries.
"""
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from build_factory_scheduler import recorded_rom
from factory_scheduler_replay import FixtureMemory, HC11CPU
from factory_rom_decode import decode
from verify_factory_ownership import EVIDENCE
from verify_factory_rom_structure import EXPECTED_SHA256

rom = recorded_rom(json.loads(EVIDENCE.read_text()))
assert sha256(bytes([255])*0x4000+rom.read(0x4000,0xC000)).hexdigest() == EXPECTED_SHA256
assert rom.word(0xFFE8) == 0xCE7C
binary = sys.argv[1]
addresses = set(range(0x45DB,0x461B)) | set(range(0x461C,0x465C))
defaults = [row for row in json.loads(subprocess.check_output([binary,'--defaults'],text=True)) if row[0] in addresses]
assert {row[0] for row in defaults} == addresses
for address,value in defaults:
    assert value == rom.read(address,1)[0], (hex(address),value)


class Failure(Exception):
    pass


class Memory(FixtureMemory):
    def __init__(self):
        super().__init__(rom)
        self.events=[]
        self.word_io=False
        self.attempts=self.fail_at=0

    def record(self,kind,width,address,value):
        self.attempts+=1
        if self.attempts==self.fail_at:
            raise Failure
        self.events.append([kind,width,address,value])

    def read8(self,address):
        value=super().read8(address)
        if not self.word_io and 0x3000<=address<0x4000:
            self.record('R',8,address,value)
        return value

    def read16(self,address):
        if not 0x3000<=address<0x4000:
            return super().read16(address)
        self.word_io=True
        try:
            value=super().read16(address)
            self.record('R',16,address,value)
            return value
        finally:
            self.word_io=False

    def write8(self,address,value):
        if not self.word_io and 0x3000<=address<0x4000:
            self.record('W',8,address,value&255)
        if address==0x3023:
            self.mem[address]&=~value&255  # Explicit CPU timer W1C fixture.
        else:
            super().write8(address,value)

    def write16(self,address,value):
        if not 0x3000<=address<0x4000:
            return super().write16(address,value)
        self.record('W',16,address,value&65535)
        self.word_io=True
        try:
            super().write16(address,value)
        finally:
            self.word_io=False


memory=Memory()
cpu=HC11CPU(memory)
coverage=set()
low_zero=bytes(0x900)
io_zero=bytes(0x70)
asic_zero=bytes(0x3E)


def irq(vector):
    before=(cpu.s.pc,cpu.s.sp,cpu.s.ccr,cpu.s.a,cpu.s.b,cpu.s.x,cpu.s.y)
    assert cpu.interrupt(vector)
    for _ in range(2000):
        pc=cpu.s.pc
        if pc==before[0]:
            break
        coverage.add(pc)
        cpu.step()
    else:
        raise AssertionError(f'IRQ budget at {cpu.s.pc:04X}')
    assert (cpu.s.pc,cpu.s.sp,cpu.s.ccr,cpu.s.a,cpu.s.b,cpu.s.x,cpu.s.y)==before


def execute(case,pair=False):
    sample,baseline,accumulator,rpm,floor,bias,variant,fail,flags=case
    memory.mem[:0x900]=low_zero
    memory.mem[0x3000:0x3070]=io_zero
    memory.mem[0x3FC0:0x3FFE]=asic_zero
    memory.mem[0x45DB:0x461B]=rom.read(0x45DB,64)
    memory.mem[0x461C:0x465C]=rom.read(0x461C,64)
    if variant:
        memory.mem[0x45DB+(rpm>>2)]=floor
        memory.mem[0x461C+(rpm>>2)]=bias
    memory.mem[0x0203:0x0205]=baseline.to_bytes(2,'big')
    memory.mem[0x020D]=accumulator
    memory.mem[0x0062]=rpm
    memory.mem[0x3023]=flags
    memory.mem[0x3FC8:0x3FCA]=sample.to_bytes(2,'big')
    memory.mem[0x0002]=0x93
    memory.mem[0x003A]=0x20
    memory.mem[0x0044]=0 if pair else 1
    memory.mem[0x0050]=0 if pair else 0x20
    if pair:
        memory.mem[0x300E:0x3010]=bytes.fromhex('fffe')
    memory.events.clear();memory.writes.clear()
    memory.attempts=memory.cycle_counter=0;memory.fail_at=fail
    cpu.s.pc,cpu.s.sp,cpu.s.ccr=0x7000,0x03FF,0xC0
    cpu.s.a,cpu.s.b,cpu.s.x,cpu.s.y=0x12,0x34,0x5678,0x9ABC
    status=0
    try:
        if pair:
            irq(0xFFF2)
        irq(0xFFE8)
    except Failure:
        status=2
    allowed={0x203,0x204,0x20D}
    if pair:
        allowed|={0x50,0x6A,0x6B,0x2CD}
    assert all(address in allowed or 0x3C0<=address<0x400 or address>=0x3000 for address,_ in memory.writes)
    return {'status':status,'baseline':memory.read16(0x203),'accumulator':memory.mem[0x20D],
            'flags':memory.mem[0x3023],'pending':int(bool(memory.mem[0x50]&0x20)),
            'crank':memory.mem[0x2CD],'toc1':int.from_bytes(memory.mem[0x3016:0x3018],'big'),
            'events':list(memory.events)}


def compare(cases,label,pair=False):
    payload=''.join(' '.join(map(str,case))+'\n' for case in cases)
    process=subprocess.run([binary,'--ref-oc1' if pair else '--oc1'],input=payload,text=True,capture_output=True,check=True)
    lines=process.stdout.splitlines()
    assert len(lines)==len(cases),(label,process.stderr)
    for index,(case,line) in enumerate(zip(cases,lines)):
        actual=json.loads(line)
        expected=execute(case,pair)
        assert actual==expected,(label,index,case,actual,expected)


cases=[]
# Every unsigned16-bit difference, with wrapping baselines and stock tables.
for difference in range(65536):
    baseline=(difference*257+0xFF80)&65535
    cases.append(((baseline+difference)&65535,baseline,(difference*29)&255,
                  (difference*73)&255,0,0,0,0,(difference>>8)&255))
# Every byte difference/floor pair, including equal and rejecting boundaries.
for difference in range(256):
    for floor in range(256):
        cases.append(((0xFF80+difference)&65535,0xFF80,(difference*3+floor*17)&255,
                      (difference+floor)&255,floor,(difference*7+floor*53)&255,1,0,difference^floor))
# Every positive excess/bias pair and every positive excess/accumulator pair.
for excess in range(1,256):
    for addend in range(256):
        cases.append((excess,0,0,(excess+addend)&255,0,addend,1,0,addend))
        cases.append((excess,0,addend,(excess*3+addend)&255,0,0,1,0,addend))
compare(cases,'OC1 numeric domains')
failures=[(*case[:7],failure,case[8]) for case in [cases[0],cases[1],cases[255],cases[256],cases[65535],cases[65536],cases[-2],cases[-1]]
          for failure in [1,2]]
compare(failures,'OC1 hardware failures')
pairs=[]
for rpm in range(256):
    for sample in [0,1,255,256,65535]:
        pairs.append((sample,0xFFFF,(rpm*17)&255,rpm,0,0,0,0,255))
compare(pairs,'REF then OC1',pair=True)
required=set();pc=0xCE7C
while pc<0xCEBB:
    required.add(pc);pc=decode(rom.read,pc).next_pc
assert required<=coverage,','.join(f'{pc:04X}' for pc in sorted(required-coverage))
print(f'{len(cases):,} OC1 C/ROM numeric cases, {len(failures)} failure prefixes and {len(pairs):,} REF/OC1 pairs match; '
      f'all {len(required)} handler instruction starts exercised; {len(defaults)} stock calibration bytes verified.')
