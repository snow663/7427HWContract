"""Compiled-C comparison with base/environmental spark and shared math ROM.

Calibration variants preserve each source table's bounded storage. A separate
527-byte matrix fixture exercises arbitrary byte strides and row-product wrap.
"""
from hashlib import sha256
from itertools import islice
import json
from pathlib import Path
import random
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from build_factory_scheduler import recorded_rom
from factory_rom_decode import decode
from factory_scheduler_replay import FixtureMemory, HC11CPU
from verify_factory_ownership import EVIDENCE
from verify_factory_rom_structure import EXPECTED_SHA256

rom = recorded_rom(json.loads(EVIDENCE.read_text()))
assert sha256(bytes([255])*0x4000+rom.read(0x4000,0xC000)).hexdigest() == EXPECTED_SHA256
binary = sys.argv[1]
TABLES = [(0x4166,289),(0x428A,289),(0x43AF,144),(0x44D5,66),(0x443A,109),(0x4860,79)]
ADDRESSES = ({0x400B,0x400D,0x45DA,0x43AE,0x4439,0x485E,0x485F,0x55F2} |
             set(range(0x413B,0x4141)) | set(range(0x449D,0x44D0)) |
             set(range(0x4585,0x45A5)) | set(range(0x45BE,0x45D8)))
for address,size in TABLES:
    ADDRESSES.update(range(address,address+3+size))
defaults = json.loads(subprocess.check_output([binary,'--defaults'],text=True))
assert len(defaults) == len(ADDRESSES) == 1095
assert {a for a,_ in defaults} == ADDRESSES
for address,value in defaults:
    assert value == rom.read(address,1)[0], (hex(address),value)

OUTPUTS = [0x06,0x19,0x3D,0x41,0x50,0x61,0x62,0x6E,0x6F,0xA4,0x15A,0x1B2,
           0x1C0,0x1C1,0x1C2,0x1C9,0x1CC,0x1F4,0x1F5,0x1F8,0x1F9,0x1FA,0x1FB,
           0x1FC,0x1FD,0x1FE,0x20A,0x20B,0x22F,0x278,0x2CB,0x83C,0x841,0x843,0x844]
BASE = {0x06:180,0x19:0xA5,0x3D:0x85,0x41:0xA5,0x50:0x25,0x61:65,0x62:100,
        0x6E:0x01,0x6F:0x80,0xA4:0xA0,0x15A:7,0x1B2:128,0x1C0:128,0x1C1:90,
        0x1C2:70,0x1C9:160,0x1CC:140,0x1F4:64,0x1F5:127,0x1F8:30,0x1F9:57,
        0x1FA:20,0x1FB:3,0x1FC:6,0x1FD:0xFF,0x1FE:0xFE,0x20A:100,0x20B:12,
        0x22F:150,0x278:128,0x2CB:4,0x83C:77,0x841:144,0x843:64,0x844:23}
CAL_BYTES = rom.read(0x4000,0x1B04)
MATRIX = bytes((i*73+(i>>2)*19+41)&255 for i in range(527))


class Memory(FixtureMemory):
    def read8(self,address):
        assert not 0x3000<=address<0x4000, f'Unexpected hardware read {address:04X}'
        return super().read8(address)

    def write8(self,address,value):
        assert not 0x3000<=address<0x4000, f'Unexpected hardware write {address:04X}'
        super().write8(address,value)


memory = Memory(rom)
cpu = HC11CPU(memory)
coverage = set()
blank = bytes(0x1000)


def case(mode,edits=None):
    return mode,BASE | (edits or {})


def execute(item):
    mode,edits = item
    memory.mem[:0x1000] = blank
    memory.mem[0x4000:0x5B04] = CAL_BYTES
    memory.mem[0x6000:0x6003] = bytes([0,0,17])
    memory.mem[0x6003:0x6212] = MATRIX
    memory.mem[0x5FFE:0x6000] = bytes([2,15])
    for address,value in edits.items():
        memory.mem[address] = value
    memory.writes.clear();memory.cycle_counter = 0
    cpu.s.pc,cpu.s.sp,cpu.s.ccr = 0x7000,0x03FF,0xD0
    cpu.s.a,cpu.s.b,cpu.s.x,cpu.s.y = 0x12,0x34,0x5678,0x9ABC

    def invoke(start,stop):
        sp = cpu.s.sp
        if stop == 0x7000:
            cpu._push16(stop)
        cpu.s.pc = start
        for _ in range(3000):
            pc = cpu.s.pc
            if pc == stop:
                assert cpu.s.sp == sp, (hex(start),hex(cpu.s.sp),hex(sp))
                assert cpu.s.ccr&0x10
                return
            coverage.add(pc);cpu.step()
        raise AssertionError(f'Spark execution budget at {cpu.s.pc:04X}')

    value = 0
    if mode == 0:
        invoke(0xA700,0xA72D)
    elif mode == 1:
        invoke(0xA72D,0xA764)
    elif mode == 2:
        invoke(0xA764,0xA77A)
    elif mode == 3:
        invoke(0xA792,0xA7D7)
    elif mode == 4:
        cpu.s.a,cpu.s.b = memory.mem[0x1F4],memory.mem[0x1F5] # Actual incoming D, not a ROM RAM reread.
        invoke(0xA7D7,0xA81E)
    elif mode == 5:
        invoke(0xA81E,0xA84E)
    elif mode == 6:
        invoke(0xCA6B,0xCAB4)
    elif mode == 7:
        invoke(0xCAB4,0xCAD5)
    elif mode == 8:
        invoke(0xCA6B,0x7000)
    elif mode == 9:
        invoke(0xA700,0xA84E)
    elif mode == 10:
        cpu.s.a,cpu.s.b,cpu.s.x = memory.mem[0x900],memory.mem[0x901],0x6000
        saved = cpu.s.b,cpu.s.x,cpu.s.y
        invoke(0xF4DE,0x7000);value = cpu.s.a
        assert (cpu.s.b,cpu.s.x,cpu.s.y) == saved
    elif mode == 11:
        cpu.s.a,cpu.s.b,cpu.s.x = memory.mem[0x900],memory.mem[0x904],memory.read16(0x902)
        saved = cpu.s.x,cpu.s.y
        invoke(0xF459,0x7000);value = cpu.s.a*256+cpu.s.b
        assert (cpu.s.x,cpu.s.y) == saved
    elif mode == 12:
        invoke(0xCA6B,0x7000)
        invoke(0xA700,0xA84E)
    else:
        raise AssertionError(mode)
    sinks = {0x41,0x1C1,0x1C2,0x1F4,0x1F5,0x1F8,0x1F9,0x1FA,0x1FB,0x1FC,0x1FD,
             0x1FE,0x20B,0x83C,0x841,0x843,0x844}
    assert all(a in sinks or 0x3C0<=a<0x400 for a,_ in memory.writes)
    return {'status':0,'value':value,'state':[memory.mem[a] for a in OUTPUTS]}


def compare(items,label):
    iterator = iter(items)
    count = 0
    while chunk := list(islice(iterator,1024)):
        payload = []
        for mode,edits in chunk:
            values = [mode,len(edits)]
            for address,value in edits.items():
                values.extend((address,value))
            payload.append(' '.join(map(str,values)))
        result = subprocess.run([binary],input='\n'.join(payload)+'\n',text=True,capture_output=True,check=True)
        lines = result.stdout.splitlines()
        assert len(lines)==len(chunk), (label,len(lines),len(chunk),result.stderr)
        for index,(item,line) in enumerate(zip(chunk,lines)):
            expected = execute(item)
            assert json.loads(line)==expected, (label,count+index,item,json.loads(line),expected)
        count += len(chunk)
    print(f'{count:,} {label} match.',flush=True)
    return count


def math_cases():
    for row in range(256):
        for column in range(256):
            yield case(10,{0x900:row,0x901:column})
    for stride in range(256):
        for row in range(256):
            yield case(10,{0x900:row,0x901:(stride*37+row*53)&255,0x6002:stride,
                           0x6000:0 if row&1 else row//3,0x6001:stride//3})
    for old in range(65536):
        yield case(11,{0x900:((old>>8)^old)&255,0x902:old>>8,0x903:old&255,0x904:(old*23)&255})
    for target in range(256):
        for gain in range(256):
            old = (target*193+gain*271+0x807F)&65535
            yield case(11,{0x900:target,0x902:old>>8,0x903:old&255,0x904:gain})
    for stride in [0,17,18,127,128,255]:
        for row in [0,15,16,31,240,255]:
            for column in [0,15,16,255]:
                yield case(10,{0x900:row,0x901:column,0x6002:stride})


def base_cases():
    for rpm in range(256):
        for load in range(256):
            yield case(0,{0x61:65,0x62:rpm,0x1C0:load,0x50:0x65 if (rpm+load)&1 else 0x25})
    for rpm in range(65):
        for load in range(256):
            yield case(0,{0x61:rpm,0x62:255-rpm,0x1C0:load,0x50:0x65 if load&1 else 0x25})


def environment_cases():
    for coolant in range(256):
        for coordinate in range(256):
            yield case(1,{0x06:coolant,0x1C9:coordinate,0x1C0:255-coordinate,0x43AE:coordinate&1,
                           0x50:0xA5 if coordinate&2 else 0x25})
    for baro in range(256):
        for vacuum in range(256):
            yield case(2,{0x400D:0x86,0x1CC:baro,0x1C9:vacuum})
    for coordinate in range(256):
        for rpm in [0,1,31,32,159,160,161,255]:
            old = (coordinate*257+rpm*53)&65535
            yield case(3,{0x6E:0x81,0x485F:1,0x1C9:coordinate,0x62:rpm,0x1F4:old>>8,0x1F5:old&255})
            yield case(3,{0x6E:0x81,0x485F:0,0x1B2:coordinate,0x1B3:255-coordinate,0x62:rpm,
                           0x1F4:old>>8,0x1F5:old&255,0x485E:(coordinate+rpm)&255})
        yield case(2,{0x400D:0x82,0x1FB:coordinate})
        yield case(3,{0x6E:1,0x413E:coordinate,0x1F4:255,0x1F5:255})
    # Force the cold-idle floor route and both sides of the strict threshold.
    for coolant in [0,163,164,165,176,177,208,209,255]:
        edits = {a:0 for a in range(0x43B2,0x4439)}
        edits.update({0x06:coolant,0x50:0xA5,0x413C:255,0x4140:164})
        yield case(1,edits)


def mat_cases():
    for sample in range(256):
        for coordinate in range(256):
            yield case(6,{0x400B:0x44,0x22F:sample,0x1C9:coordinate,0x62:255-coordinate,
                           0x4439:coordinate&1,0x41:0xA7 if sample&1 else 0xA5})
    for raw in range(256):
        for bias in [0,1,127,128,255]:
            yield case(6,{0x400B:0x44,0x22F:80,0x1C9:80,0x4439:0,0x443D:raw,0x413F:bias})
    for sample in range(256):
        yield case(6,{0x400B:4,0x22F:sample,0x41:0xA7})
    for coefficient in range(256):
        for magnitude in range(256):
            word = (coefficient*257+magnitude*97)&65535
            negative = (coefficient+magnitude)&1
            yield case(5,{0x1C0:0,0x41:0xA7 if negative else 0xA5,0x1FA:magnitude,
                           0x449D:coefficient,0x44AE:coefficient,0x1FD:word>>8,0x1FE:word&255})


def pe_sum_cases():
    for coefficient in range(256):
        for fraction in range(256):
            yield case(7,{0x3D:0xA5,0x62:0,0x44BF:coefficient,0x278:fraction})
    for coolant in [0,99,100,101,255]:
        for fault in [0xA5,0xB5]:
            for pe in [0x85,0xA5]:
                for rpm in range(256):
                    yield case(7,{0x06:coolant,0x19:fault,0x3D:pe,0x62:rpm,0x278:rpm})
    for egr in range(65536):
        edits = {a:(egr*k)&255 for a,k in [(0x1FB,3),(0x1F8,7),(0x1FC,11),(0x1F9,13),(0x2CB,17),
                                             (0x413B,19),(0x413C,23),(0x413D,29),(0x413E,31),(0x55F2,37),
                                             (0x20B,41),(0x15A,43)]}
        edits.update({0x1F4:egr>>8,0x1F5:egr&255,0xA4:(egr>>4)&255})
        yield case(4,edits)


def variant_cases():
    rng = random.Random(0x31A700)
    for index in range(2048):
        edits = {a:rng.randrange(256) for a in sorted(ADDRESSES)}
        edits.update({a:rng.randrange(256) for a in BASE})
        # All callers retain their bounded storage; direct math above covers
        # arbitrary strides. Higher axis offsets only reduce the accessed span.
        for address,_ in TABLES:
            row,column,stride = rom.read(address,3)
            edits[address]=rng.randrange(row,256)
            edits[address+1]=rng.randrange(column,256)
            edits[address+2]=rng.randrange(stride+1)
        yield case(index%13 if index%13<10 else 12,edits)


counts = {}
counts['math'] = compare(math_cases(),'matrix/filter C/ROM cases')
counts['base'] = compare(base_cases(),'base-table/history C/ROM cases')
counts['environment'] = compare(environment_cases(),'coolant/altitude/EGR C/ROM cases')
counts['mat'] = compare(mat_cases(),'MAT producer/effect C/ROM cases')
counts['pe_sum'] = compare(pe_sum_cases(),'PE/composite C/ROM cases')
counts['variants'] = compare(variant_cases(),'bounded calibration/state variants')

joined = []
for rpm in range(256):
    for gates in range(8):
        joined.append(case(12,{0x61:rpm,0x62:255-rpm,0x06:(rpm*13)&255,0x1C0:(rpm*37)&255,
                               0x1C9:(rpm*71)&255,0x1CC:(rpm*89)&255,0x22F:rpm,0x278:255-rpm,
                               0x50:0x25 | (0x40 if gates&1 else 0) | (0x80 if gates&2 else 0),
                               0x400B:0x44 if gates&1 else 4,0x400D:0x86 if gates&2 else 0x82,
                               0x3D:0xA5 if gates&4 else 0x85,0x6E:0x81 if gates&4 else 1}))
counts['joined'] = compare(joined,'auxiliary→composite witnesses')

history = []
edits = {0x400B:0x44,0x400D:0x86,0x3D:0xA5}
for tick in range(512):
    edits.update({0x61:tick&255,0x62:(tick*7)&255,0x06:(tick*3)&255,0x1C0:(tick*13)&255,
                  0x1C9:(tick*17)&255,0x22F:(tick*19)&255,0x1B2:(tick*23)&255,
                  0x6E:0x81 if tick%7 else 1,0x400D:0x82 if tick%5 else 0x86,
                  0x400B:4 if tick%11==0 else 0x44,0x50:0xE5 if tick&1 else 0x25})
    item = case(12,dict(edits));history.append(item)
    edits.update(dict(zip(OUTPUTS,execute(item)['state'])))
counts['history'] = compare(history,'retained-term/filter/history calls')

required = set()
for start,end in [(0xA700,0xA84E),(0xCA6B,0xCB15),(0xF459,0xF479),(0xF4C1,0xF550)]:
    pc = start
    while pc<end:
        required.add(pc);pc=decode(rom.read,pc).next_pc
assert required<=coverage, ','.join(f'{pc:04X}' for pc in sorted(required-coverage))
print(f'{sum(counts.values()):,} spark comparisons; all {len(required)} scoped instruction starts exercised; '
      f'{len(defaults)} distinct calibration bytes verified (1,035 new and60 prior/shared).')
