"""Check resident override, signed limits and post-limit service against BMHM.

1812 remains unknown. Active extension witnesses stop at its entry or use an
explicit fixture return/state effect; they do not reconstruct the module ABI.
"""
from hashlib import sha256
from itertools import islice
import json
from pathlib import Path
import random
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from build_factory_scheduler import recorded_rom
from factory_rom_decode import decode
from factory_scheduler_replay import FixtureMemory,HC11CPU
from verify_factory_ownership import EVIDENCE
from verify_factory_rom_structure import EXPECTED_SHA256

rom=recorded_rom(json.loads(EVIDENCE.read_text()))
assert sha256(bytes([255])*0x4000+rom.read(0x4000,0xC000)).hexdigest()==EXPECTED_SHA256
binary=sys.argv[1]
ADDRESSES=({0x4132,0x4E90,0x48DA,0x400F,0x4E77} | set(range(0x4161,0x4166)) |
           set(range(0x4144,0x414E)) | set(range(0x45D8,0x45DB)) | set(range(0x46DF,0x46E3)))
defaults=[r for r in json.loads(subprocess.check_output([binary,'--defaults'],text=True)) if r[0] in ADDRESSES]
assert len(defaults)==len(ADDRESSES)==27
assert {a for a,_ in defaults}==ADDRESSES
for address,value in defaults:
    assert value==rom.read(address,1)[0],(hex(address),value)

OUTPUTS=[0x06,0x19,0x3D,0x41,0x50,0x61,0x62,0x6E,0x6F,0xA4,0x15A,0x1B2,
         0x1C0,0x1C1,0x1C2,0x1C9,0x1CC,0x1F4,0x1F5,0x1F8,0x1F9,0x1FA,0x1FB,
         0x1FC,0x1FD,0x1FE,0x20A,0x20B,0x22F,0x278,0x2CB,0x83C,0x841,0x843,0x844,
         0x63,0x64,0x6C,0xFD,0xFE,0x46,0x51,0x53,0x1D9,0x1F2,0x1F3,0x208,0x837,0x838,0x839,0x83A,0x83B,0x857,0x284,
         0x86,0x36,0x3B,0x395,0x398,0x1EE,0x1EF,0x1F0,0x1F1,0x16,0x1DA,0x20C,0x20D,0x20E,0x842]
BASE={0x06:180,0x19:0xA5,0x3D:0x85,0x41:0xA5,0x50:0x25,0x61:65,0x62:100,
      0x6E:1,0x6F:0x80,0xA4:0xA0,0x15A:0,0x1B2:128,0x1C0:128,0x1C1:90,0x1C2:70,
      0x1C9:160,0x1CC:140,0x1F4:64,0x1F5:127,0x1F8:30,0x1F9:57,0x1FA:20,0x1FB:3,
      0x1FC:6,0x1FD:0xFF,0x1FE:0xFE,0x20A:100,0x20B:12,0x22F:150,0x278:128,0x2CB:4,
      0x83C:77,0x841:144,0x843:64,0x844:23,0x63:0x33,0x64:1,0x6C:96,0xFD:0,0xFE:10,
      0x46:0xE1,0x51:0x85,0x53:0xA4,0x1D9:0,0x1F2:0x80,0x1F3:0x7F,0x208:43,
      0x837:0x31,0x838:0x33,0x839:0x7F,0x83A:0x81,0x83B:0xEE,0x857:0x20,0x284:2,
      0x86:0xA0,0x36:0x81,0x3B:0x85,0x395:0xC5,0x398:33,0x1EE:0x12,0x1EF:0x34,
      0x1F0:0x33,0x1F1:0x33,0x16:0x9F,0x1DA:0,0x20C:12,0x20D:30,0x20E:21,0x842:48}
CAL_BYTES=rom.read(0x4000,0x1B04)


class Failure(Exception):
    pass


class Missing(Exception):
    pass


class Memory(FixtureMemory):
    def __init__(self):
        super().__init__(rom);self.cpu=HC11CPU(self);self.events=[];self.attempts=self.fail_at=0

    def record(self,kind,address,value):
        self.attempts+=1
        if self.attempts==self.fail_at:
            raise Failure
        self.events.append([kind,0,address,value,int(bool(self.cpu.s.ccr&0x10))])

    def read8(self,address):
        assert not 0x3000<=address<0x4000,f'Unexpected hardware read {address:04X}'
        return super().read8(address)

    def write8(self,address,value):
        assert not 0x3000<=address<0x4000,f'Unexpected hardware write {address:04X}'
        super().write8(address,value)


memory=Memory();cpu=memory.cpu;coverage=set();blank=bytes(0x1000)


def case(mode,edits=None):
    return mode,BASE | (edits or {})


def word_edits(address,value):
    return {address:value>>8,address+1:value&255}


def execute(item):
    mode,edits=item
    memory.mem[:0x1000]=blank;memory.mem[0x4000:0x5B04]=CAL_BYTES
    for address,value in edits.items():
        memory.mem[address]=value
    memory.events.clear();memory.writes.clear();memory.cycle_counter=memory.attempts=0
    memory.fail_at=memory.mem[0x907]
    cpu.s.pc,cpu.s.sp,cpu.s.ccr=0x7000,0x03FF,0xD0 if memory.mem[0x909] else 0xC0
    cpu.s.a,cpu.s.b,cpu.s.x,cpu.s.y=0x12,0x34,0x5678,0x9ABC

    def invoke(start,stop):
        sp=cpu.s.sp;cpu.s.pc=start
        if stop==0x7000:
            cpu._push16(stop)
        for _ in range(5000):
            pc=cpu.s.pc
            if pc==stop:
                assert cpu.s.sp==sp,(hex(start),hex(cpu.s.sp),hex(sp))
                return
            if pc==0x1812:
                if memory.mem[0x90A]:
                    raise Missing
                action=memory.mem[0x908];memory.record('T',0x1812,action)
                if action==1:
                    memory.mem[0x1FD:0x1FF]=bytes.fromhex('8123');memory.mem[0x86]&=0xBF
                elif action==2:
                    memory.mem[0x36]|=0x20;memory.mem[0x53]|=0x10
                    memory.mem[0x06]=255;memory.mem[0x1D9]=7
                # Chosen well-formed fixture return, not the unknown module ABI.
                cpu.s.a,cpu.s.b,cpu.s.x,cpu.s.y=0xA5,0x5A,0xDEAD,0xBEEF
                cpu.s.pc=0x7AA5
                continue
            coverage.add(pc)
            if memory.mem[pc] in (0x0E,0x0F):
                memory.record('M',0,int(memory.mem[pc]==0x0F))
            cpu.step()
        raise AssertionError(f'Spark command execution budget at {cpu.s.pc:04X}')

    status=unresolved=0
    try:
        if mode==20: invoke(0xA9E0,0xA9E7)
        elif mode==21: invoke(0xA9E7,0xAA1A)
        elif mode==22: invoke(0xAA1A,0xAA33)
        elif mode==23: invoke(0xAADC,0xAB1A)
        elif mode==24: invoke(0xAB1A,0xAB44)
        elif mode==25: invoke(0xA9E0,0xAB44)
        elif mode==26: invoke(0xA700,0xAB44)
        elif mode==27: invoke(0xCA6B,0x7000);invoke(0xA700,0xAB44)
        else: raise AssertionError(mode)
    except Failure:
        status=2
    except Missing:
        status=unresolved=1
    sinks={0x41,0x50,0x51,0x53,0x1C1,0x1C2,0x1EE,0x1EF,0x1F0,0x1F1,0x1F2,0x1F3,
           0x1F4,0x1F5,0x1F8,0x1F9,0x1FA,0x1FB,0x1FC,0x1FD,0x1FE,0x208,0x20B,0x20C,0x20D,0x20E,
           0x6E,0x838,0x839,0x83A,0x83B,0x83C,0x841,0x843,0x844}
    assert all(a in sinks or 0x3C0<=a<0x400 for a,_ in memory.writes)
    return {'status':status,'value':0,'state':[memory.mem[a] for a in OUTPUTS],
            'masked':int(bool(cpu.s.ccr&0x10)),'unresolved':unresolved,'events':list(memory.events)}


def compare(items,label):
    iterator=iter(items);count=0
    while chunk:=list(islice(iterator,1024)):
        payload=[]
        for mode,edits in chunk:
            values=[mode,len(edits)]
            for address,value in edits.items(): values.extend((address,value))
            payload.append(' '.join(map(str,values)))
        result=subprocess.run([binary],input='\n'.join(payload)+'\n',text=True,capture_output=True,check=True)
        lines=result.stdout.splitlines()
        assert len(lines)==len(chunk),(label,len(lines),len(chunk),result.stderr)
        for index,(item,line) in enumerate(zip(chunk,lines)):
            expected=execute(item)
            assert json.loads(line)==expected,(label,count+index,item,json.loads(line),expected)
        count+=len(chunk)
    print(f'{count:,} {label} match.',flush=True)
    return count


BOUNDS=[0x8000,0x8001,0xFFFF,0,1,0x77,0x7FFE,0x7FFF]


def upper_cases():
    for command in range(65536):
        yield case(22,word_edits(0x1FD,command)|word_edits(0x4144,BOUNDS[command>>13])|{0x4132:0})
    edges=sorted({(bound+step)&65535 for bound in BOUNDS for step in [-1,0,1]})
    for bound in edges:
        for command in edges:
            for bias in [0,1,255]:
                yield case(22,word_edits(0x1FD,command)|word_edits(0x4144,bound)|{0x4132:bias})


def lower_cases():
    for command in range(65536):
        yield case(23,word_edits(0x1EE,command)|word_edits(0x4146,BOUNDS[7-(command>>13)]))
    distinct=word_edits(0x4146,0x8001)|word_edits(0x4148,0xFFFE)|word_edits(0x414A,17)|word_edits(0x414C,0x7FFF)
    for flags in range(256):
        for retard in [0,1,255]:
            for recovery in [0x85,0xA5]:
                for throttle in [0,5,6,7,255]:
                    yield case(23,distinct|{0x1EE:0x80,0x1EF:0,0xA4:flags,0x15A:retard,0x51:recovery,0x1D9:throttle})
    for bound in BOUNDS:
        for command in BOUNDS:
            yield case(23,word_edits(0x4146,bound)|word_edits(0x1EE,command))


def override_cases():
    for minimum in [0,100,200,255]:
        for coolant in range(256):
            for active in [0xA4,0xB4]:
                for request in [0x81,0xA1]:
                    for throttle in [0,3,7,255]:
                        yield case(21,{0x4E90:3,0x4161:minimum,0x06:coolant,0x53:active,0x36:request,
                                       0x1D9:throttle,0x4164:3,0x4165:7,0x4162:0x91,0x4163:0x23})
    for options in range(256):
        yield case(21,{0x4E90:options,0x4161:0,0x06:255,0x36:0xA1,0x53:0xB4,0x1D9:0})


def service_cases():
    for command in range(65536):
        flags=0xD8|(0x20 if command&1 else 0)
        yield case(24,word_edits(0x1EE,command)|{0x3B:0x95,0x395:flags,0x398:command>>8})
    for flags in range(256):
        for amount in range(256):
            command=(0xFF80+flags*17)&65535
            yield case(24,word_edits(0x1EE,command)|{0x3B:0x95,0x395:flags,0x398:amount})
        for amount in [0,1,127,128,255]:
            yield case(24,{0x3B:0x85,0x395:flags,0x398:amount})


def pipeline_cases():
    for word in range(65536):
        yield case(25,word_edits(0x1FD,word)|{
            0x20D:(word*17)&255,0x843:word>>8,0x20C:(word*29)&255,0x844:(word*37)&255,
            0x400F:0x18 if word&0x100 else 0x10,0x06:((word>>8)+word)&255,
            0x50:0x35 if word&2 else 0x25,0x6E:3 if word&4 else 1,0x20E:word&255,
            0x3B:0x95 if word&8 else 0x85,0x395:(word>>3)&0x38,0x398:word>>8,
            0xA4:(word*11)&255,0x15A:1 if word&16 else 0,0x51:0xA5 if word&32 else 0x85,
            0x909:word&1})


def boundary_cases():
    for mode in [20,25,26,27]:
        for enabled in [0xA0,0xE0]:
            for missing in [0,1]:
                for action in range(3):
                    for masked in [0,1]:
                        yield case(mode,{0x86:enabled,0x90A:missing,0x908:action,0x909:masked,
                                         0x4E90:3,0x4161:200,0x4164:0,0x4165:7,0x4162:0x92,0x4163:0x34})


def variant_cases():
    rng=random.Random(0x31A9E0)
    for index in range(2048):
        edits={a:rng.randrange(256) for a in sorted(ADDRESSES)}
        edits.update({a:rng.randrange(256) for a in BASE})
        edits[0x908]=index%3;edits[0x909]=index&1
        yield case(21+index%7,edits)


counts={}
counts['upper']=compare(upper_cases(),'signed-upper/reference C/ROM cases')
counts['lower']=compare(lower_cases(),'signed-lower/selector C/ROM cases')
counts['override']=compare(override_cases(),'resident-override C/ROM cases')
counts['service']=compare(service_cases(),'service/common-latch C/ROM cases')
counts['pipeline']=compare(pipeline_cases(),'ordered-command C/ROM cases')
burst_gate={0x400F:8,0x45DA:0,0x06:255,0x50:0x25,0x1C0:0,0x46DF:1,
            0x1D9:10,0x46E0:20,0x1DA:0,0x46E1:1,0x46E2:1}
counts['burst_edges']=compare([case(25,burst_gate|{0x6E:1}),
                               case(25,burst_gate|{0x6E:3,0x20E:1})],
                              'command burst-arm/expiry witnesses')
counts['boundary']=compare(boundary_cases(),'explicit extension boundary/return witnesses')
counts['variants']=compare(variant_cases(),'command calibration/state variants')

joined=[]
for rpm in range(256):
    for mode in [26,27]:
        joined.append(case(mode,{0x63:rpm,0x64:255-rpm,0x857:(rpm*7)&255,0x1C0:(rpm*17)&255,
                                 0x400F:0x98,0x46F2:0,0x46F3:255,0x3B:0x95,0x395:rpm,
                                 0x398:255-rpm,0x20D:rpm,0x86:0xE0 if rpm&1 else 0xA0,0x908:rpm%3}))
counts['joined']=compare(joined,'composite→command witnesses')

failures=[]
for mode in [25,26,27]:
    for enabled in [0xA0,0xE0]:
        for action in range(3):
            for masked in [0,1]:
                item=case(mode,{0x86:enabled,0x908:action,0x909:masked})
                for failure in range(1,len(execute(item)['events'])+1):
                    failures.append(case(mode,item[1]|{0x907:failure}))
counts['failures']=compare(failures,'mask/extension failure prefixes')

history=[];edits={0x4E90:3,0x4161:100,0x4164:3,0x4165:7,0x4162:0xFF,0x4163:0xF0,0x36:0xA1}
for tick in range(192):
    edits.update({0x1D9:[3,7,8,4,3,0][tick%6],0x06:100 if tick%7==0 else 180,
                  0x4E90:1 if 40<=tick<48 else 3,0x3B:0x95 if tick&1 else 0x85,
                  0x395:0xF8 if tick%3 else 0xC8,0x398:tick&255,0x20D:(tick*17)&255})
    item=case(27,dict(edits));history.append(item)
    edits.update(dict(zip(OUTPUTS,execute(item)['state'])))
counts['history']=compare(history,'override/service/command history calls')

required=set();pc=0xA9E0
while pc<0xAB44:
    required.add(pc);pc=decode(rom.read,pc).next_pc
assert required<=coverage,','.join(f'{pc:04X}' for pc in sorted(required-coverage))
print(f'{sum(counts.values()):,} command comparisons; all {len(required)} resident instruction starts exercised; '
      f'{len(defaults)} calibration bytes verified (17 new,10 shared). 1812 remains an explicit boundary.')
