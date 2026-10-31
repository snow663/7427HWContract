"""Check decay, the mux/ADC diagnostic and normal KR against stock instructions.

The IRQ witnesses inject at explicit logical mask boundaries. They do not model
physical knock, ADC settling, HC11 interrupt arbitration or CLI recognition delay.
"""
from hashlib import sha256
from itertools import islice
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from build_factory_scheduler import recorded_rom
from factory_rom_decode import decode
from factory_scheduler_replay import FixtureMemory, HC11CPU
from verify_factory_ownership import EVIDENCE
from verify_factory_rom_structure import EXPECTED_SHA256

rom = recorded_rom(json.loads(EVIDENCE.read_text()))
assert sha256(bytes([255])*0x4000+rom.read(0x4000,0xC000)).hexdigest() == EXPECTED_SHA256
binary = sys.argv[1]
addresses = (set(range(0x45A5,0x45B6)) | set(range(0x45D8,0x461B)) |
             set(range(0x461C,0x465C)) | set(range(0x4E74,0x4E78)) | {0x5B03})
defaults = [row for row in json.loads(subprocess.check_output([binary,'--defaults'],text=True)) if row[0] in addresses]
assert len(defaults) == len(addresses) == 153
assert {a for a,_ in defaults} == addresses
for address,value in defaults:
    assert value == rom.read(address,1)[0], (hex(address),value)

OUTPUTS = [0x02,0x06,0x16,0x19,0x1A,0x3A,0x62,0x63,0x6E,0x1EE,0x1EF,
           0x203,0x204,0x207,0x20C,0x20D,0x284,0x843,0x844,0x3008,0x3030,0x3034,0x3023]
BASE = {0x02:8,0x06:120,0x16:0x9F,0x19:0xA5,0x1A:0xAD,0x3A:0xEE,0x62:100,
        0x63:100,0x6E:0x81,0x1EE:0x12,0x1EF:0x34,0x203:0xFF,0x204:0xFE,
        0x207:159,0x20C:40,0x20D:32,0x284:2,0x843:64,0x844:180,
        0x3008:0xFF,0x3034:128,0x3023:0xFF,0x3FC8:0,0x3FC9:64}


class Failure(Exception):
    pass


class Memory(FixtureMemory):
    def __init__(self):
        super().__init__(rom)
        self.cpu = HC11CPU(self)
        self.events = []
        self.word_io = False
        self.attempts = self.fail_at = self.polls = self.port_reads = 0
        self.ready_after = 1
        self.second_port = -1

    def record(self,kind,width,address,value):
        self.attempts += 1
        if self.attempts == self.fail_at:
            raise Failure
        self.events.append([kind,width,address,value,int(bool(self.cpu.s.ccr&0x10))])

    def read8(self,address):
        if address == 0x3030:
            value = self.mem[address] | (0x80 if self.ready_after and self.polls+1>=self.ready_after else 0)
        elif address == 0x3008 and self.port_reads == 1 and self.second_port >= 0:
            value = self.second_port
        else:
            value = super().read8(address)
        if not self.word_io and 0x3000<=address<0x4000:
            self.record('R',8,address,value)
            if address == 0x3030:
                self.polls += 1
            if address == 0x3008:
                self.port_reads += 1
        return value

    def read16(self,address):
        if not 0x3000<=address<0x4000:
            return super().read16(address)
        self.word_io = True
        try:
            value = super().read16(address)
            self.record('R',16,address,value)
            return value
        finally:
            self.word_io = False

    def write8(self,address,value):
        if 0x3000<=address<0x4000:
            self.record('W',8,address,value&255)
        if address == 0x3023:
            self.mem[address] &= ~value&255
        else:
            super().write8(address,value)
        if address == 0x3030:
            self.polls = 0


memory = Memory()
cpu = memory.cpu
coverage = set()
blank_low = bytes(0x900)
blank_io = bytes(0x70)
blank_asic = bytes(0x3E)


def case(mode=3,edits=None,*,fail=0,masked=0,ready=1,second=-1,point=0,argument=0):
    values = BASE | (edits or {})
    return (mode,fail,masked,ready,second,point,argument,values)


def execute(item):
    mode,fail,masked,ready,second,point,argument,edits = item
    memory.mem[:0x900] = blank_low
    memory.mem[0x3000:0x3070] = blank_io
    memory.mem[0x3FC0:0x3FFE] = blank_asic
    for address,_ in defaults:
        memory.mem[address] = rom.read(address,1)[0]
    for address,value in edits.items():
        memory.mem[address] = value
    memory.events.clear();memory.writes.clear()
    memory.attempts = memory.polls = memory.port_reads = memory.cycle_counter = 0
    memory.fail_at = fail;memory.ready_after = ready;memory.second_port = second
    cpu.s.pc,cpu.s.sp,cpu.s.ccr = 0x7000,0x03FF,0xC0 | (0x10 if masked else 0)
    cpu.s.a,cpu.s.b,cpu.s.x,cpu.s.y = argument,0x34,0x3000,0x9ABC
    injected = False

    def irq():
        nonlocal injected
        injected = True
        before = (cpu.s.pc,cpu.s.sp,cpu.s.ccr,cpu.s.a,cpu.s.b,cpu.s.x,cpu.s.y)
        if not cpu.interrupt(0xFFE8):
            return
        run_until(before[0],allow_inject=False)
        assert (cpu.s.pc,cpu.s.sp,cpu.s.ccr,cpu.s.a,cpu.s.b,cpu.s.x,cpu.s.y) == before

    def run_until(stop,allow_inject=True):
        for _ in range(2000):
            pc = cpu.s.pc
            if pc == stop:
                return
            coverage.add(pc)
            if rom.read(pc,1)[0] in (0x0E,0x0F):
                masked = int(rom.read(pc,1)[0] == 0x0F)
                if allow_inject and not injected and point == 1 and masked:
                    irq()
                memory.record('M',0,0,masked)
                cpu.step()
                if allow_inject and not injected and ((point==2 and masked) or (point==3 and not masked)):
                    irq()
            else:
                cpu.step()
        raise AssertionError(f'Knock execution budget at {cpu.s.pc:04X}')

    def invoke(start,stop=0x7000):
        sp = cpu.s.sp
        if stop == 0x7000:
            cpu._push16(stop)
        cpu.s.pc = start
        run_until(stop)
        assert cpu.s.sp == sp, (hex(start),hex(cpu.s.sp),hex(sp))

    status = 0
    try:
        if mode == 0:
            invoke(0xCEBB,0xCEDB)
        elif mode == 1:
            invoke(0xCEDB)
        elif mode == 2:
            invoke(0x7B2B)
        elif mode == 3:
            invoke(0xAA81,0xAADC)
        elif mode == 4:
            invoke(0xF275)
        elif mode == 5:
            invoke(0xF25F)
        elif mode == 6:
            irq()
            invoke(0xAA81,0xAADC)
            invoke(0x7B2B)
            invoke(0xAA81,0xAADC)
    except Failure:
        status = 2
    allowed = {0x19,0x1A,0x3A,0x1EE,0x1EF,0x203,0x204,0x207,0x20C,0x20D}
    assert all(a in allowed or 0x3C0<=a<0x400 or 0x3000<=a<0x4000 for a,_ in memory.writes)
    return {'status':status,'state':[memory.mem[a] for a in OUTPUTS],
            'masked':int(bool(cpu.s.ccr&0x10)),'events':list(memory.events)}


def compare(items,label):
    iterator = iter(items)
    count = 0
    while chunk := list(islice(iterator,2048)):
        lines = []
        for item in chunk:
            values = list(item[:7])+[len(item[7])]
            for address,value in item[7].items():
                values.extend((address,value))
            lines.append(' '.join(map(str,values)))
        result = subprocess.run([binary],input='\n'.join(lines)+'\n',text=True,capture_output=True,check=True)
        actual = result.stdout.splitlines()
        assert len(actual) == len(chunk), (label,len(actual),len(chunk),result.stderr)
        for index,(item,line) in enumerate(zip(chunk,actual)):
            expected = execute(item)
            assert json.loads(line) == expected, (label,count+index,item,json.loads(line),expected)
        count += len(chunk)
    print(f'{count:,} {label} match.',flush=True)
    return count


def decay_cases():
    for rpm in range(256):
        for retard in range(256):
            yield case(0,{0x62:rpm,0x20C:retard})
    for rate in range(256):
        for retard in range(256):
            # Constant surrounding knots exercise every rate/retard product.
            yield case(0,{0x20C:retard,0x45AB:rate,0x45AC:rate})
    for phase in range(256):
        yield case(0,{0x02:phase,0x20C:255,0x62:phase})
    for rpm in range(256):
        yield case(0,{0x62:rpm,0x20C:255,**{0x45A5+i:i*15 for i in range(17)}})


def consumer_cases():
    for gain in range(256):
        for events in range(256):
            yield case(edits={0x843:gain,0x20D:events,0x20C:(gain*13+events*7)&255,
                             0x844:(gain*23+events*29)&255})
    for old in range(256):
        for limit in range(256):
            yield case(edits={0x20C:old,0x844:limit,0x20D:(old+limit)&255})
    for word in [0,1,2,63,64,127,128,255,256,32767,32768,65535]:
        for retard in range(256):
            yield case(edits={0x1EE:word>>8,0x1EF:word&255,0x20C:retard,0x20D:0,0x844:255})
    # Branch boundaries and independent flag combinations, including literal
    # unmasking when the entry mask is already set and all observations are0.
    for burst in [0x81,0x83]:
        for faults in [0x9F,0xBF,0xDF,0xFF]:
            for coolant in [0,99,100,101,255]:
                for speed in [0,1,2,255]:
                    for rpm in [0,63,64,255]:
                        for sensor in [0xA5,0xB5]:
                            yield case(edits={0x6E:burst,0x16:faults,0x06:coolant,0x284:speed,0x63:rpm,
                                              0x19:sensor,0x844:0},masked=1)
    for threshold in range(256):
        for value in {0,max(0,threshold-1),threshold,min(255,threshold+1),255}:
            yield case(edits={0x45DA:threshold,0x06:value})
            yield case(edits={0x45DA:0,0x45D8:threshold,0x284:value,0x45D9:255,0x63:0})
            yield case(edits={0x45DA:0,0x45D8:255,0x284:0,0x45D9:threshold,0x63:value})
        yield case(edits={0x19:0xB5,0x4E77:threshold,0x844:0,0x1EF:255-threshold})


def sensor_cases():
    for sample in range(256):
        for count in [0,159,160,161,254,255]:
            for fault in [0xA5,0xB5]:
                yield case(1,{0x3034:sample,0x207:count,0x19:fault,0x1A:0xAF},ready=sample%14)
    for delay in range(256):
        for count in {0,max(0,delay-1),delay,min(255,delay+1),255}:
            yield case(1,{0x4E74:delay,0x207:count,0x3034:0},ready=12)
    for lower,upper in [(0,0),(0,255),(255,255),(255,0),(20,230),(128,128)]:
        for sample in range(256):
            yield case(1,{0x4E76:lower,0x4E75:upper,0x3034:sample,0x207:255},ready=0)
    for phase in range(256):
        yield case(2,{0x02:phase,0x20C:255},ready=phase%14,masked=phase&1)
        yield case(2,{0x02:phase,0x5B03:0xAC,0x19:0xB5,0x1A:0xAF},masked=phase&1)


def driver_cases():
    for selector in range(256):
        for port in [0,7,56,127,128,255]:
            yield case(4,{0x3008:port},argument=selector,second=port^0xC5)
    for control in [0,1,5,20,127,128,255]:
        for ready in range(14):
            for flags in [0xAC,0xAD,0xAE,0xAF]:
                yield case(5,{0x1A:flags,0x3A:flags},argument=control,ready=ready,masked=flags&1)


counts = {}
counts['decay'] = compare(decay_cases(),'decay C/ROM cases')
counts['consumer'] = compare(consumer_cases(),'normal-KR C/ROM cases')
counts['sensor'] = compare(sensor_cases(),'sensor/slot C/ROM cases')
counts['drivers'] = compare(driver_cases(),'mux/ADC C/ROM cases')

# Every successful transaction boundary can fail. Compare all effects completed
# before that boundary, including ADC flags and the deliberately retained mask.
witnesses = [case(1,ready=r,masked=m) for r in range(14) for m in range(2)]
witnesses += [case(2,{0x20C:255},ready=0),case(3),case(3,masked=1),case(4,argument=255),case(5,ready=0)]
failures = []
for item in witnesses:
    result = execute(item)
    for failure in range(1,len(result['events'])+1):
        failures.append((item[0],failure,*item[2:]))
counts['failures'] = compare(failures,'failed-I/O/mask prefixes')

# Coherent counter fixtures, an observation producer, two consumers with an
# intervening scheduled decay/diagnostic, and selected logical IRQ boundaries.
sequences = []
for rpm in range(256):
    for sample in [0,64,255,256,65535]:
        sequences.append(case(6,{0x62:rpm,0x3FC8:sample>>8,0x3FC9:sample&255,
                                 0x20C:rpm,0x20D:255-rpm,0x3034:rpm},ready=rpm%14))
counts['sequences'] = compare(sequences,'OC1/consumer/slot/consumer sequences')
irqs = [case(edits={0x20D:events},point=point,masked=masked)
        for events in range(256) for point in [1,2,3] for masked in [0,1]]
counts['irq'] = compare(irqs,'logical mask-boundary OC1 witnesses')

# Prolonged sensor faults, valid recovery and diagnostic disable/reenable. Each
# call's output seeds the next call, retaining exact counter and fault history.
history = []
edits = {0x207:0,0x19:0xA5,0x20C:255,0x20D:0}
for index in range(330):
    edits.update({0x02:(8+16*index)%160,0x3034:128 if index==325 else 0,
                  0x5B03:0xAC if 162<=index<170 else 0xBC})
    item = case(2,dict(edits),ready=0 if index%3==0 else 12)
    history.append(item)
    output = execute(item)
    edits.update({a:v for a,v in zip(OUTPUTS,output['state']) if a<0x3000})
counts['history'] = compare(history,'sensor history/recovery calls')

required = set()
for start,end in [(0x7B2B,0x7B2F),(0xCEBB,0xCF16),(0xF25F,0xF280),(0xAA81,0xAADC),(0xF4C1,0xF4DE)]:
    pc = start
    while pc<end:
        required.add(pc);pc=decode(rom.read,pc).next_pc
assert required <= coverage, ','.join(f'{pc:04X}' for pc in sorted(required-coverage))
print(f"{sum(counts.values()):,} comparisons; all {len(required)} scoped instruction starts exercised; "
      f'{len(defaults)} calibration bytes verified (24 new,1 shared,128 prior OC1).')
