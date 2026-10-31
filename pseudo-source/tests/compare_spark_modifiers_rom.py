"""Compare idle, transient and decel spark with actual stock instructions.

Optional feature/calibration variants are fixture data, not changes to the truck
image. Full-composite witnesses end before external1812 and later limits.
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
CURVES=[(0x44F0,8),(0x44F8,10),(0x4502,8),(0x450A,10)]
ADDRESSES=({0x400F,0x413C,0x4515} | set(range(0x414F,0x4153)) | set(range(0x415A,0x4161)) |
           set(range(0x451B,0x452C)) | set(range(0x46EC,0x46F9)))
for address,length in CURVES:
    ADDRESSES.update(range(address,address+1+length))
defaults=[r for r in json.loads(subprocess.check_output([binary,'--defaults'],text=True)) if r[0] in ADDRESSES]
assert len(defaults)==len(ADDRESSES)==81
assert {a for a,_ in defaults}==ADDRESSES
for address,value in defaults:
    assert value==rom.read(address,1)[0],(hex(address),value)

OUTPUTS=[0x06,0x19,0x3D,0x41,0x50,0x61,0x62,0x6E,0x6F,0xA4,0x15A,0x1B2,
         0x1C0,0x1C1,0x1C2,0x1C9,0x1CC,0x1F4,0x1F5,0x1F8,0x1F9,0x1FA,0x1FB,
         0x1FC,0x1FD,0x1FE,0x20A,0x20B,0x22F,0x278,0x2CB,0x83C,0x841,0x843,0x844,
         0x63,0x64,0x6C,0xFD,0xFE,0x46,0x51,0x53,0x1D9,0x1F2,0x1F3,0x208,0x837,0x838,0x839,0x83A,0x83B,0x857,0x284]
BASE={0x06:180,0x19:0xA5,0x3D:0x85,0x41:0xA5,0x50:0x25,0x61:65,0x62:100,
      0x6E:1,0x6F:0x80,0xA4:0xA0,0x15A:7,0x1B2:128,0x1C0:128,0x1C1:90,0x1C2:70,
      0x1C9:160,0x1CC:140,0x1F4:64,0x1F5:127,0x1F8:30,0x1F9:57,0x1FA:20,0x1FB:3,
      0x1FC:6,0x1FD:0xFF,0x1FE:0xFE,0x20A:100,0x20B:12,0x22F:150,0x278:128,0x2CB:4,
      0x83C:77,0x841:144,0x843:64,0x844:23,0x63:0x33,0x64:1,0x6C:96,0xFD:0,0xFE:10,
      0x46:0xE1,0x51:0x85,0x53:0xA4,0x1D9:0,0x1F2:0x80,0x1F3:0x7F,0x208:43,
      0x837:0x31,0x838:0x33,0x839:0x7F,0x83A:0x81,0x83B:0xEE,0x857:0x20,0x284:2}
CAL_BYTES=rom.read(0x4000,0x1B04)
CURVE_VALUES=bytes((i*73+(i>>2)*19+41)&255 for i in range(17))


class Memory(FixtureMemory):
    def read8(self,address):
        assert not 0x3000<=address<0x4000,f'Unexpected hardware read {address:04X}'
        return super().read8(address)

    def write8(self,address,value):
        assert not 0x3000<=address<0x4000,f'Unexpected hardware write {address:04X}'
        super().write8(address,value)


memory=Memory(rom)
cpu=HC11CPU(memory)
coverage=set()
blank=bytes(0x1000)


def case(mode,edits=None):
    return mode,BASE | (edits or {})


def execute(item):
    mode,edits=item
    memory.mem[:0x1000]=blank
    memory.mem[0x4000:0x5B04]=CAL_BYTES
    memory.mem[0x6300]=128;memory.mem[0x6301:0x6312]=CURVE_VALUES;memory.mem[0x905]=17
    for address,value in edits.items():
        memory.mem[address]=value
    memory.writes.clear();memory.cycle_counter=0
    cpu.s.pc,cpu.s.sp,cpu.s.ccr=0x7000,0x03FF,0xD0
    cpu.s.a,cpu.s.b,cpu.s.x,cpu.s.y=0x12,0x34,0x5678,0x9ABC

    def invoke(start,stop):
        sp=cpu.s.sp
        if stop==0x7000:
            cpu._push16(stop)
        cpu.s.pc=start
        for _ in range(4000):
            pc=cpu.s.pc
            if pc==stop:
                assert cpu.s.sp==sp,(hex(start),hex(cpu.s.sp),hex(sp))
                assert cpu.s.ccr&0x10
                return
            coverage.add(pc);cpu.step()
        raise AssertionError(f'Modifier execution budget at {cpu.s.pc:04X}')

    value=0
    if mode==13:
        cpu.s.a,cpu.s.x=memory.mem[0x900],0x6300
        invoke(0xF499,0x7000);value=cpu.s.a
        assert cpu.s.x==0x6301 and cpu.s.b==0 and cpu.s.y==0x9ABC
    elif mode==14:
        invoke(0xA84E,0xA906)
    elif mode==15:
        invoke(0xA906,0xA97A)
    elif mode==16:
        invoke(0xA97A,0xA9E0)
    elif mode==17:
        invoke(0xA84E,0xA9E0)
    elif mode==18:
        invoke(0xA700,0xA9E0)
    elif mode==19:
        invoke(0xCA6B,0x7000);invoke(0xA700,0xA9E0)
    else:
        raise AssertionError(mode)
    sinks={0x41,0x50,0x51,0x53,0x1C1,0x1C2,0x1F2,0x1F3,0x1F4,0x1F5,0x1F8,0x1F9,0x1FA,
           0x1FB,0x1FC,0x1FD,0x1FE,0x208,0x20B,0x838,0x839,0x83A,0x83B,0x83C,0x841,0x843,0x844}
    assert all(a in sinks or 0x3C0<=a<0x400 for a,_ in memory.writes)
    return {'status':0,'value':value,'state':[memory.mem[a] for a in OUTPUTS]}


def compare(items,label):
    iterator=iter(items);count=0
    while chunk:=list(islice(iterator,1024)):
        payload=[]
        for mode,edits in chunk:
            values=[mode,len(edits)]
            for address,value in edits.items():
                values.extend((address,value))
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


def capped_cases():
    for limit in [0,1,15,16,31,32,96,128,254,255]:
        for value in range(256):
            yield case(13,{0x900:value,0x6300:limit})
    for limit in range(256):
        for value in {0,max(0,limit-1),limit,min(255,limit+1),255}:
            yield case(13,{0x900:value,0x6300:limit})


def idle_cases():
    for rpm in range(65536):
        yield case(14,{0x857:0,0x50:0xA5,0x63:rpm>>8,0x64:rpm&255,
                       0x6C:(rpm*17)&255,0x1C0:(rpm*29)&255})
    for target in [1,127,128,255]:
        for difference in [0,1,15,16,63,64,1023,1024,25471,25472,25599,25600,32767,32768,65280,65535]:
            if difference<=target*256:
                rpm=target*256-difference
                yield case(14,{0x857:target,0x50:0xA5,0x63:rpm>>8,0x64:rpm&255})
    for target in range(256):
        for adder in [0,1,127,128,255]:
            yield case(14,{0x857:target,0x4160:adder,0x53:0xA5})
    for retained in [0x25,0x65]:
        for speed in [0,2,3,255]:
            for throttle in [0,3,4,5,255]:
                for coolant in [0,1,180,255]:
                    yield case(14,{0x50:retained,0x284:speed,0x1D9:throttle,0x06:coolant,0x53:0xA5})
    for threshold in [0,1,255,256,65534,65535]:
        for runtime in {0,max(0,threshold-1),threshold,min(65535,threshold+1),65535}:
            yield case(14,{0x415E:threshold>>8,0x415F:threshold&255,0xFD:runtime>>8,0xFE:runtime&255})
    for derivative in range(256):
        for bias in [0,1,127,128,255]:
            for cap in [0,1,127,128,255]:
                yield case(14,{0x63:0,0x64:0,0x857:0,0x50:0xA5,0x6C:96,
                               0x451B:derivative,0x4514:bias,0x4515:cap})
        yield case(14,{0x6C:derivative,**{0x451B+i:(i*31)&255 for i in range(17)}})


def expanded_idle_cases():
    # Larger supplied backings and nonflat data expose the compressed index,
    # including values that the stock96 cap otherwise maps to one endpoint.
    data={a:((a-0x44F1)*11+37)&255 for a in range(0x44F1,0x451C)}
    data.update({address:255 for address,_ in CURVES})
    data.update({0x906:1,0x4514:128,0x4515:127,0x451B:0,0x6C:96,0x1C0:0,0x50:0xA5})
    differences={0,1,1023,1024,25471,25472,25600,32767,32768,65535}
    for boundary in range(0,65536,128):
        differences.update(d for d in [boundary-1,boundary,boundary+1] if 0<=d<=65535)
    for difference in sorted(differences):
        yield case(14,data|{0x857:0,0x63:difference>>8,0x64:difference&255})
        if difference<=0xFF00:
            rpm=0xFF00-difference
            yield case(14,data|{0x857:255,0x63:rpm>>8,0x64:rpm&255})


def transient_cases():
    for error in range(256):
        for offset in range(256):
            high=(offset*7)&255;word=(error*257+offset*101)&65535
            gain=(error*37+offset)&255;limit=(error*5+offset*23)&255
            yield case(15,{0x400F:0x90,0x46F2:0,0x46F3:255,0x63:(high+error)&255,
                           0x838:high,0x839:(error*13+offset*17)&255,0x837:(error*29+offset*11)&255,
                           0x1D9:0,0x46F4:gain,0x46EC:255,0x46ED:offset,0x46EE:limit,
                           0x46EF:255,0x46F0:offset,0x46F1:limit,0x1FD:word>>8,0x1FE:word&255})
    for lower,upper in [(0,0),(0,255),(255,0),(99,100),(100,100),(255,255)]:
        for coolant in range(256):
            for enabled in [0x10,0x90]:
                for idle in [0x25,0xA5]:
                    yield case(15,{0x06:coolant,0x46F2:lower,0x46F3:upper,0x400F:enabled,0x50:idle})
    for throttle in range(256):
        yield case(15,{0x400F:0x90,0x46F2:0,0x46F3:255,0x1D9:throttle,
                       **{0x46F4+i:value for i,value in enumerate([0,255,0,255,127])}})


def decel_cases():
    for old in range(65536):
        command=(old*13+0x7FFF)&65535
        yield case(16,{0x51:0xA5,0x1F2:old>>8,0x1F3:old&255,0x208:(old*29)&255,
                       0x1D9:14 if old&1 else 0,0x1FD:command>>8,0x1FE:command&255})
    for coolant in range(256):
        for bias in [0,1,127,128,255]:
            yield case(16,{0x46:0xE9,0x1F9:coolant,0x413C:bias,0x4152:(coolant*7+bias*13)&255})
    for amount in range(256):
        for difference in [0,1,127,128,255]:
            yield case(16,{0x46:0xE9,0x1F9:difference,0x413C:0,0x4152:amount,0x1F2:255,0x1F3:255})
        yield case(16,{0x51:0x85,0x208:amount,0x1F2:amount,0x1F3:255-amount})
    for threshold in range(256):
        for throttle in {0,max(0,threshold-1),threshold,min(255,threshold+1),255}:
            yield case(16,{0x51:0xA5,0x4151:threshold,0x1D9:throttle,0x414F:0,0x4150:255})


def variant_cases():
    rng=random.Random(0x31A84E)
    for index in range(2048):
        edits={a:rng.randrange(256) for a in sorted(ADDRESSES)}
        edits.update({a:rng.randrange(256) for a in BASE})
        for address,capacity in CURVES:
            edits[address]=rng.randrange((capacity-1)*16)
        yield case(14+index%6,edits)


counts={}
counts['capped']=compare(capped_cases(),'capped-curve C/ROM cases')
counts['idle']=compare(idle_cases(),'idle-spark C/ROM cases')
counts['expanded_idle']=compare(expanded_idle_cases(),'expanded-curve idle-index witnesses')
counts['transient']=compare(transient_cases(),'transient-spark C/ROM cases')
counts['decel']=compare(decel_cases(),'decel/recovery C/ROM cases')
counts['variants']=compare(variant_cases(),'bounded modifier/state variants')

joined=[]
for rpm in range(256):
    for flags in range(4):
        joined.append(case(19,{0x63:rpm,0x64:255-rpm,0x857:(rpm*7)&255,0x6C:(rpm*11)&255,
                               0x400F:0x90,0x46F2:0,0x46F3:255,0x50:0x25|(0x80 if flags&1 else 0),
                               0x46:0xE9 if flags&2 else 0xE1,0x51:0xA5,0x1F2:rpm,0x1F3:255-rpm,
                               0x1C0:(rpm*17)&255,0x1D9:rpm&7}))
counts['joined']=compare(joined,'auxiliary→full-composite witnesses')

history=[];edits={0x400F:0x90,0x46F2:0,0x46F3:255,0x51:0xA5,0x1F2:0xFE,0x1F3:0xEC}
for tick in range(384):
    flags=(edits.get(0x50,BASE[0x50])&0x7F)|(0x80 if tick%3 else 0)
    edits.update({0x50:flags,0x63:(tick*7)&255,0x64:(tick*13)&255,0x06:(tick*3)&255,
                  0x1C0:(tick*17)&255,0x1D9:4 if 32<=tick<64 else tick&3,0x837:(tick*11)&255,
                  0x857:80,0x46:0xE9 if 200<=tick<220 else 0xE1,0x284:0 if tick%5 else 3})
    item=case(19,dict(edits));history.append(item)
    edits.update(dict(zip(OUTPUTS,execute(item)['state'])))
counts['history']=compare(history,'idle/transient/recovery history calls')

required=set()
for start,end in [(0xA84E,0xA9E0),(0xF499,0xF4A4),(0xF4BD,0xF4DE),(0xF459,0xF479)]:
    pc=start
    while pc<end:
        required.add(pc);pc=decode(rom.read,pc).next_pc
assert required<=coverage,','.join(f'{pc:04X}' for pc in sorted(required-coverage))
print(f'{sum(counts.values()):,} modifier comparisons; all {len(required)} scoped instruction starts exercised; '
      f'{len(defaults)} calibration bytes verified (38 new,43 prior/shared).')
