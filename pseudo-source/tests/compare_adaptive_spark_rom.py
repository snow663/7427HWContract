"""Compare callable adaptive/burst spark slices with stock BMHM instructions.

Only CB15 is stubbed at the slot6 boundary; its successful return and selected
input changes are explicit fixtures. This does not implement CB15 or A466.
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
CAL_ADDRESSES = {0x400F} | set(range(0x4585,0x45A5)) | set(range(0x45B6,0x45D8)) | set(range(0x46DF,0x46EF))
defaults = [row for row in json.loads(subprocess.check_output([binary,'--defaults'],text=True)) if row[0] in CAL_ADDRESSES]
assert len(defaults) == len(CAL_ADDRESSES) == 83
assert {a for a,_ in defaults} == CAL_ADDRESSES
for address,value in defaults:
    assert value == rom.read(address,1)[0], (hex(address),value)

OUTPUTS = [0x02,0x06,0x19,0x3D,0x50,0x52,0x62,0x6E,0x6F,0x1C0,0x1C2,0x1C9,
           0x1D9,0x1DA,0x1EE,0x1EF,0x209,0x20A,0x20B,0x20C,0x20D,0x20E,0x841,0x842,0x843,0x844]
BASE = {0x02:6,0x06:200,0x16:0x9F,0x19:0xA5,0x3D:0x85,0x50:0xA5,0x52:0xBC,
        0x62:100,0x63:100,0x6E:0x81,0x6F:0x80,0x1C0:128,0x1C2:128,0x1C9:150,
        0x1D9:20,0x1DA:0,0x1EE:0x12,0x1EF:0x34,0x209:40,0x20A:100,0x20B:55,
        0x20C:13,0x20D:30,0x20E:21,0x284:2,0x841:144,0x842:48,0x843:64,0x844:23}
CAL_BYTES = rom.read(0x4000,0x1B04)


class Failure(Exception):
    pass


class Memory(FixtureMemory):
    def __init__(self):
        super().__init__(rom)
        self.cpu = HC11CPU(self)
        self.events = []
        self.attempts = self.fail_at = 0

    def record(self,kind,width,address,value):
        self.attempts += 1
        if self.attempts == self.fail_at:
            raise Failure
        self.events.append([kind,width,address,value,int(bool(self.cpu.s.ccr&0x10))])

    def read8(self,address):
        value = super().read8(address)
        if 0x3000<=address<0x4000:
            self.record('R',8,address,value)
        return value

    def write8(self,address,value):
        if 0x3000<=address<0x4000:
            self.record('W',8,address,value&255)
        super().write8(address,value)


memory = Memory()
cpu = memory.cpu
coverage = set()
blank_low = bytes(0x900)


def case(mode,edits=None,*,fail=0,masked=0,argument=0):
    return mode,fail,masked,argument,BASE | (edits or {})


def execute(item):
    mode,fail,masked,argument,edits = item
    memory.mem[:0x900] = blank_low
    memory.mem[0x4000:0x5B04] = CAL_BYTES
    for address,value in edits.items():
        memory.mem[address] = value
    memory.events.clear();memory.writes.clear()
    memory.attempts = memory.cycle_counter = 0;memory.fail_at = fail
    cpu.s.pc,cpu.s.sp,cpu.s.ccr = 0x7000,0x03FF,0xC0 | (0x10 if masked else 0)
    cpu.s.a,cpu.s.b,cpu.s.x,cpu.s.y = 0x12,0x34,0x5678,0x9ABC

    def invoke(start,stop=0x7000):
        sp = cpu.s.sp
        if stop == 0x7000:
            cpu._push16(stop)
        cpu.s.pc = start
        for _ in range(1000):
            pc = cpu.s.pc
            if pc == stop:
                assert cpu.s.sp == sp, (hex(start),hex(cpu.s.sp),hex(sp))
                return
            if pc == 0xCB15:
                memory.record('T',0,0xCB15,argument)
                if argument == 1:
                    memory.mem[0x06]=200;memory.mem[0x1C0]=memory.mem[0x1C2]=128
                elif argument == 2:
                    memory.mem[0x19] |= 0x10
                elif argument == 3:
                    memory.mem[0x02] = 6
                # Explicit boundary return through an actual ROM RTS. Register
                # clobbers keep the learner independent of the stub's values.
                cpu.s.a,cpu.s.b,cpu.s.x,cpu.s.y = 0xA5,0x5A,0xDEAD,0xBEEF
                cpu.s.pc = 0x7AA5
                continue
            coverage.add(pc)
            if memory.mem[pc] in (0x0E,0x0F):
                memory.record('M',0,0,int(memory.mem[pc]==0x0F))
            cpu.step()
        raise AssertionError(f'Adaptive spark budget at {cpu.s.pc:04X}')

    status = 0
    try:
        if mode == 7:
            invoke(0xCAD5)
        elif mode == 8:
            invoke(0xCA4C)
        elif mode == 9:
            invoke(0xCE10)
        elif mode == 10:
            invoke(0xA77A,0xA792)
        elif mode == 11:
            invoke(0xAA33,0xAA81)
        elif mode == 12:
            invoke(0xAA33,0xAADC)
        elif mode == 13:
            invoke(0x7B14)
        elif mode == 14:
            invoke(0xCAD5)
            invoke(0xCA4C)
            invoke(0x7B14)
            invoke(0xA77A,0xA792)
            invoke(0xAA33,0xAADC)
        else:
            raise AssertionError(mode)
    except Failure:
        status = 2
    sinks = {0x52,0x6E,0x1EE,0x1EF,0x209,0x20A,0x20B,0x20C,0x20D,0x20E,0x841,0x842,0x843,0x844}
    assert all(a in sinks or 0x3C0<=a<0x400 for a,_ in memory.writes)
    return {'status':status,'state':[memory.mem[a] for a in OUTPUTS],
            'masked':int(bool(cpu.s.ccr&0x10)),'events':list(memory.events)}


def compare(items,label):
    iterator = iter(items)
    count = 0
    while chunk := list(islice(iterator,2048)):
        payload = []
        for mode,fail,masked,argument,edits in chunk:
            values = [mode,fail,masked,1,-1,0,argument,len(edits)]
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


def gain_cases():
    for rpm in range(256):
        for vacuum in range(256):
            status = [0x80,0x88,0xC0,0xC8][(rpm^vacuum)&3]
            yield case(7,{0x62:rpm,0x1C9:vacuum,0x6F:status})
        for status in [0x80,0x88,0xC0,0xC8]:
            yield case(7,{0x62:rpm,0x3D:0xA5,0x6F:status})
    for coolant in range(256):
        for limit in range(256):
            yield case(8,{0x06:coolant,0x46E3:limit})


def burst_cases():
    for throttle in range(256):
        for previous in range(256):
            yield case(11,{0x400F:0x18,0x1C0:0,0x1D9:throttle,0x1DA:previous,0x46E0:255})
    for countdown in range(256):
        for gain in range(256):
            word = (countdown*257+gain*67)&65535
            yield case(11,{0x400F:0x18,0x6E:0x83,0x20E:countdown,0x842:gain,0x1EE:word>>8,0x1EF:word&255})
    for enabled in [0x10,0x18]:
        for switch in [0xA5,0xB5]:
            for coolant in [0,99,100,101,255]:
                for active in [0x81,0x83]:
                    for countdown in [0,1,2,255]:
                        yield case(12,{0x400F:enabled,0x50:switch,0x06:coolant,0x6E:active,
                                       0x20E:countdown,0x1C0:0},masked=countdown&1)
    for threshold in range(256):
        for value in {0,max(0,threshold-1),threshold,min(255,threshold+1),255}:
            yield case(11,{0x400F:0x18,0x46DF:threshold,0x1C0:value})
            yield case(11,{0x400F:0x18,0x1C0:0,0x46E0:threshold,0x1D9:value,0x1DA:0,0x46E1:0})
            yield case(11,{0x400F:0x18,0x1C0:0,0x46E0:255,0x1D9:value,0x1DA:0,0x46E1:threshold})
        yield case(11,{0x400F:0x18,0x1C0:0,0x46E2:threshold})
    for speed in [0,1,2,255]:
        for rpm in [0,63,64]:
            for fault in [0xA5,0xB5]:
                yield case(12,{0x400F:0x18,0x6E:0x83,0x20E:1,0x284:speed,0x63:rpm,0x19:fault})
    for gain,events,old in [(255,255,0),(128,255,1),(0,0,255)]:
        yield case(12,{0x843:gain,0x20D:events,0x20C:old})


def learning_cases():
    for activity in range(256):
        for scale in range(256):
            # Fault decay with decrement0 exposes every byte scale product.
            yield case(9,{0x19:0xB5,0x209:activity,0x45BC:0,0x45BD:scale})
    for load in range(256):
        for previous in range(256):
            yield case(9,{0x1C0:load,0x1C2:previous})
    for high,low in [(12,10),(255,0),(0,255),(255,255),(0,0)]:
        for retard in range(256):
            for flags in range(4):
                yield case(9,{0x45B9:high,0x45BA:low,0x20C:retard,0x52:0xBC|flags})
    for step in range(256):
        for activity in {0,max(0,step-1),step,min(255,step+1),255}:
            yield case(9,{0x52:0xBD,0x209:activity,0x45BB:step})
            yield case(9,{0x19:0xB5,0x209:activity,0x45BC:step})
    for phase in range(256):
        yield case(9,{0x02:phase,0x19:0xB5})
    for threshold in range(256):
        for value in {0,max(0,threshold-1),threshold,min(255,threshold+1),255}:
            yield case(9,{0x45B6:threshold,0x06:value})
            yield case(9,{0x45B7:threshold,0x1C0:value,0x1C2:value})
            yield case(9,{0x45B8:threshold,0x45B7:0,0x1C0:value,0x1C2:0})


def retard_cases():
    for rpm_factor in range(256):
        for scaled in range(256):
            yield case(10,{0x841:rpm_factor,0x20A:scaled,0x45CF:255,0x45D0:255})
    for load in range(256):
        yield case(10,{0x1C0:load,0x841:(load*37)&255,0x20A:(load*71)&255})


def variant_cases():
    rng = random.Random(0x31CE10)
    for index in range(2048):
        edits = {a:rng.randrange(256) for a in CAL_ADDRESSES}
        edits.update({a:rng.randrange(256) for a in BASE})
        edits[0x02] = 6
        yield case([7,8,9,10,11,12,13,14][index%8],edits,masked=index&1,argument=index%4)


counts = {}
counts['gains'] = compare(gain_cases(),'gain/cap C/ROM cases')
counts['burst'] = compare(burst_cases(),'burst C/ROM cases')
counts['learning'] = compare(learning_cases(),'learning C/ROM cases')
counts['retard'] = compare(retard_cases(),'adaptive-retard C/ROM cases')
counts['variants'] = compare(variant_cases(),'calibration/state variants')

sequences = []
for rpm in range(256):
    for active,countdown in [(0x81,21),(0x83,0),(0x83,1),(0x83,2)]:
        sequences.append(case(14,{0x62:rpm,0x400F:0x18,0x6E:active,0x20E:countdown,
                                   0x1C0:80,0x1C2:80,0x45B7:0,0x209:rpm},argument=rpm%4))
    for argument in range(4):
        sequences.append(case(13,{0x02:rpm,0x06:0 if argument==1 else 200},argument=argument))
counts['sequences'] = compare(sequences,'joined gain/learning/correction and slot6 witnesses')

witnesses = [case(12,{0x400F:0x18,0x6E:active,0x20E:countdown},masked=masked)
             for active in [0x81,0x83] for countdown in [0,1,2] for masked in [0,1]]
witnesses += [case(13,argument=a) for a in range(4)] + [case(14,{0x400F:0x18},argument=1)]
failures = []
for item in witnesses:
    for failure in range(1,len(execute(item)['events'])+1):
        failures.append((item[0],failure,*item[2:]))
counts['failures'] = compare(failures,'mask/dependency failure prefixes')

# Preserve state over repeated admission, dequalification, faults and recovery.
histories = []
for label,mode,initial,length in [
    ('learner',9,{0x209:40,0x52:0xBC},120),
    ('burst',12,{0x400F:0x18,0x1C0:0,0x20E:0,0x46E2:0},270)]:
    edits = dict(initial)
    for index in range(length):
        if label=='learner':
            edits.update({0x20C:20 if index<30 else 0 if index<60 else 11 if index<80 else 20,
                          0x19:0xB5 if 90<=index<100 else 0xA5,0x06:0 if index==85 else 200})
        else:
            edits.update({0x400F:0x10 if 30<=index<35 else 0x18,0x20D:25,0x50:0xB5 if index==50 else 0xA5})
        item = case(mode,dict(edits))
        histories.append(item)
        output = execute(item)
        edits.update(dict(zip(OUTPUTS,output['state'])))
counts['histories'] = compare(histories,'learning/burst history calls')

required = set()
for start,end in [(0xCAD5,0xCB15),(0xCA4C,0xCA6B),(0xCE10,0xCE7C),(0xA77A,0xA792),
                  (0xAA33,0xAADC),(0x7B14,0x7B1B),(0xF499,0xF4A4),(0xF4BD,0xF4DE)]:
    pc = start
    while pc<end:
        required.add(pc);pc=decode(rom.read,pc).next_pc
assert required<=coverage, ','.join(f'{pc:04X}' for pc in sorted(required-coverage))
print(f'{sum(counts.values()):,} adaptive spark comparisons; all {len(required)} scoped instruction starts exercised; '
      f'{len(defaults)} new calibration bytes verified. CB15 remains an explicit stub boundary.')
