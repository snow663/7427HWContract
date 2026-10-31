"""Compare the A466..A5E4 prelude against stock BMHM instructions.

AC51 is an explicit dependency fixture. Stop before the first SWI at A5D7;
the trap frame/handler/loop and A5E5 period/RPM continuation are outside scope.
"""
from hashlib import sha256
from itertools import islice,product
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
CAL=set(range(0x4133,0x4137))|{0x4142,0x4143,0x414E,0x4962,0x4963,0x4D96}|set(range(0x4E64,0x4E68))
defaults=json.loads(subprocess.check_output([binary,'--defaults'],text=True))
assert len(defaults)==len(CAL)==14 and {a for a,_ in defaults}==CAL
for a,v in defaults:assert v==rom.read(a,1)[0],(hex(a),v)
OUTPUTS=[0x04,0x18,0x44,0x4F,0x50,0x51,0x5F,0x60,0x61,0x6F,0x1C0,0x1C6,0x1C9,0x1CE,
         0x1CF,0x1D9,0x1EA,0x1EB,0x1F2,0x1F3,0x202,0x210,0x211,0x229,0x257,0x258,
         0x260,0x261,0x2CE,0x2F4,0x82E,0x3060,0x306F]
BASE={0x04:0xA5,0x18:0xB5,0x44:0xA5,0x4F:0x25,0x50:0x81,0x51:0xA5,0x5F:0x12,0x60:0x34,
      0x61:50,0x6F:0x81,0x1C0:77,0x1C6:100,0x1C9:13,0x1CE:128,0x1CF:23,0x1D9:20,
      0x1EA:0x12,0x1EB:0x34,0x1F2:0x56,0x1F3:0x78,0x202:0,0x210:0,0x211:0,0x229:0,
      0x257:0x23,0x258:0x45,0x260:0,0x261:0,0x2CE:27,0x2F4:200,0x82E:2,
      0x3060:0xB7,0x306F:0x69,0x3FC0:0x07,0x3FC1:0xD0}


class Failure(Exception):pass
class Missing(Exception):pass


class Memory(FixtureMemory):
    def __init__(self):
        super().__init__(rom);self.cpu=HC11CPU(self);self.events=[]
        self.attempts=self.fail_at=self.action=self.read_index=0;self.periods=[]

    def record(self,kind,width,address,value):
        self.attempts+=1
        if self.attempts==self.fail_at:raise Failure
        self.events.append([kind,width,address,value,int(bool(self.cpu.s.ccr&0x10))])

    def read8(self,a):
        value=super().read8(a)
        if 0x3000<=a<0x4000:
            assert a==0x3060,hex(a);self.record('R',8,a,value)
        return value

    def read16(self,a):
        if not 0x3000<=a<0x4000:return super().read16(a)
        assert a==0x3FC0,hex(a)
        value=int.from_bytes(self.mem[a:a+2],'big')
        if self.periods:
            assert self.read_index<len(self.periods)
            value=self.periods[self.read_index];self.read_index+=1
        self.record('R',16,a,value)
        if self.action==1:
            self.mem[0x4F]|=0x40;self.mem[0x51]&=0xBF;self.mem[0x1F2:0x1F4]=bytes.fromhex('8000')
        return value

    def write8(self,a,v):
        if 0x3000<=a<0x4000:
            assert a in (0x3060,0x306F),hex(a);self.record('W',8,a,v&255)
        super().write8(a,v)


memory=Memory();cpu=memory.cpu;coverage=set();blank=bytes(0x900);cal_bytes=rom.read(0x4000,0x1B04)


def word(a,v):return {a:v>>8,a+1:v&255}
def case(mode,edits=None,*,fail=0,masked=0,missing=0,action=0,periods=()):
    return mode,fail,masked,missing,action,periods,BASE|(edits or {})


def execute(item):
    mode,fail,masked,missing,action,periods,edits=item
    memory.mem[:0x900]=blank;memory.mem[0x4000:0x5B04]=cal_bytes
    for a,v in edits.items():memory.mem[a]=v
    memory.events.clear();memory.writes.clear();memory.attempts=memory.read_index=memory.cycle_counter=0
    memory.fail_at=fail;memory.action=action;memory.periods=periods
    cpu.s.pc=[0xA466,0xA4B3,0xA581,0xA5C6,0xA4EC,0xA466][mode]
    cpu.s.sp=0x3FF;cpu.s.ccr=0xD0 if masked else 0xC0
    cpu.s.a,cpu.s.b,cpu.s.x,cpu.s.y=0x12,0x34,0x5678,0x9ABC
    if mode==2:cpu._push16(0x7000)
    stop={0:0xA4B3,1:0xA4EC,2:0x7000}.get(mode,0xA5E5)
    status=normal=unresolved=0
    try:
        for _ in range(2000):
            pc=cpu.s.pc
            if pc==stop:
                normal=int(mode in (4,5));break
            if pc==0xA5D7:
                status=6;break # Before SWI/frame/handler/loop, not an emulated return.
            if pc==0xAC51:
                if missing:raise Missing
                memory.record('T',0,pc,action)
                if action==3:
                    memory.mem[0x50]&=0xFB;memory.mem[0x5F:0x61]=bytes.fromhex('ffff');memory.mem[0x61]=0x77
                break # Explicit fixture body/return, not the AC51 implementation/ABI.
            coverage.add(pc)
            if memory.mem[pc] in (0x0E,0x0F):memory.record('M',0,0,int(memory.mem[pc]==0x0F))
            cpu.step()
            if memory.mem[pc]==0x0E and action==2:
                memory.mem[0x50]|=0x20;memory.mem[0x4F]|=0x80
        else:raise AssertionError(f'Admission execution budget at {cpu.s.pc:04X}')
        assert cpu.s.sp==0x3FF,(mode,hex(cpu.s.pc),hex(cpu.s.sp))
    except Failure:status=2
    except Missing:status=unresolved=1
    sinks={0x04,0x18,0x44,0x4F,0x50,0x51,0x5F,0x60,0x6F,0x1C0,0x1C9,0x1CF,0x1EA,0x1EB,
           0x1F2,0x1F3,0x202,0x210,0x211,0x229,0x260,0x261,0x2CE,0x3060,0x306F}
    assert all(a in sinks or 0x3C0<=a<0x400 for a,_ in memory.writes)
    return {'status':status,'normal':normal,'masked':int(bool(cpu.s.ccr&0x10)),
            'unresolved':unresolved,'state':[memory.mem[a] for a in OUTPUTS],'events':list(memory.events)}


def compare(items,label):
    iterator=iter(items);count=0
    while chunk:=list(islice(iterator,1024)):
        payload=[]
        for mode,fail,masked,missing,action,periods,edits in chunk:
            values=[mode,fail,masked,missing,action,len(periods),len(edits),*periods]
            for a,v in edits.items():values.extend((a,v))
            payload.append(' '.join(map(str,values)))
        p=subprocess.run([binary],input='\n'.join(payload)+'\n',text=True,capture_output=True,check=True)
        lines=p.stdout.splitlines();assert len(lines)==len(chunk),(label,p.stderr)
        for i,(item,line) in enumerate(zip(chunk,lines)):
            expected=execute(item);actual=json.loads(line)
            assert actual==expected,(label,count+i,item,actual,expected)
        count+=len(chunk)
    print(f'{count:,} {label} match.',flush=True);return count


def load_cases():
    for a,b in product(range(256),repeat=2):yield case(0,{0x1C6:a,0x2F4:b})
    for n in range(65536):yield case(0,word(0x257,n)|{0x1CE:((n>>8)*13+7)&255})
    for factor in range(256):
        d=factor<<8
        for n in sorted({max(0,min(65535,v)) for v in [0,1,d//8-1,d//8,d//8+1,5*d//8-1,5*d//8,5*d//8+1,d-1,d,d+1,65535]}):
            yield case(0,word(0x257,n)|{0x1CE:factor})


def map_cases():
    for count,limit in product(range(256),repeat=2):
        yield case(1,{0x229:count,0x4E66:limit,0x82E:0,0x4E64:1,0x61:0})
    for sample,limit in product(range(256),repeat=2):
        yield case(1,{0x82E:sample,0x4E64:limit,0x229:3})
    for flags,rpm,tps in product(range(256),[0,63,64,255],[0,26,27,255]):
        yield case(1,{0x6F:flags,0x61:rpm,0x1D9:tps,0x229:2})


def fuel_cases():
    bounds=[0,1,0x887,0x888,0xCCC,0x8000,0xFFFE,0xFFFF]
    for p in range(65536):yield case(2,word(0x3FC0,p)|word(0x4135,bounds[p>>13])|{0x211:p&255})
    for count,limit in product(range(256),repeat=2):
        yield case(2,{0x211:count,0x4143:limit,0x4135:0,0x4136:1,0x3FC0:0,0x3FC1:0})


def admission_cases():
    for v in range(65536):yield case(4,word(0x1EA,v)|{0x50:0xA1,0x4F:0xB5})
    for v in range(65536):
        yield case(4,word(0x1F2,v)|{0x50:0xA1,0x4F:0xF5,0x414E:((v>>8)*37)&255})
    limits=[0,1,159,160,240,0x8000,0xFFFE,0xFFFF]
    for v in range(65536):
        yield case(4,word(0x260,v)|word(0x4962,limits[v>>13])|{0x4F:0xB5,0x2CE:v&255,0x4D96:v>>8},masked=v&1)
    for count,age,masked,running in product(range(256),[0,159,160,239,240,65535],[0,1],[0,1]):
        yield case(4,word(0x260,age)|{0x202:count,0x4F:0xB5 if running else 0x35},masked=masked)
    for flags,count,events in product([0x25,0x35,0x65,0x75,0xA5,0xB5,0xE5,0xF5],range(256),[0,1,2,255]):
        yield case(4,{0x50:0xA1,0x4F:flags,0x44:0xAD,0x210:count,0x211:count,0x4142:events,0x4143:events})


counts={}
counts['load']=compare(load_cases(),'load-coordinate C/ROM cases')
counts['map']=compare(map_cases(),'MAP plausibility C/ROM cases')
counts['fuel']=compare(fuel_cases(),'independent fuel-admission C/ROM cases')
counts['admission']=compare(admission_cases(),'reference/startup/age C/ROM cases')
directed=[]
for mode,masked,missing,action,first,running in product([4,5],[0,1],[0,1],range(4),[0xA5,0xAD],[0x25,0xA5]):
    for p,q in product([0,0x887,0x888,0xCCB,0xCCC,65535],repeat=2):
        directed.append(case(mode,{0x50:0xA1,0x44:first,0x4F:running},masked=masked,missing=missing,action=action,periods=(p,q)))
for mode,masked,value in product([3,4,5],[0,1],range(256)):
    directed.append(case(mode,{0x3060:value,0x202:23},masked=masked))
counts['directed']=compare(directed,'fresh-period/alternate/trap witnesses')

rng=random.Random(0x31A466)
variants=[]
for i in range(2048):
    edits={a:rng.randrange(256) for a in sorted(CAL|BASE.keys())}
    variants.append(case(i%6,edits,masked=i&1,missing=(i>>2)&1,action=i%4))
counts['variants']=compare(variants,'admission calibration/state variants')
failures=[]
for item in directed[::37]+[case(4,{0x50:0xA1,0x44:0xAD,0x4F:0x25},periods=(2000,2000)),
                            case(5,{0x260:0,0x261:159,0x202:23})]:
    for failure in range(1,len(execute(item)['events'])+1):
        failures.append((item[0],failure,*item[2:]))
counts['failures']=compare(failures,'failed-I/O/mask/alternate prefixes')

history=[]
for label,initial in [('run',{0x4F:0x25}),('startup',{0x4F:0xF5,0x1F2:0,0x1F3:0}),('map',{0x4F:0xB5})]:
    edits=dict(initial)
    for tick in range(128):
        edits.update({0x50:0xA1 if label!='map' and (tick<64 or tick%7==0) else 0x81,
                      0x82E:20 if tick%19==0 else 2,0x61:0,0x1D9:30})
        item=case(5,dict(edits));history.append(item)
        edits.update(dict(zip(OUTPUTS,execute(item)['state'])))
counts['history']=compare(history,'admission history calls')

required=set();pc=0xA466
while pc<0xA5E5:
    if pc not in (0xA5D7,0xA5D8):required.add(pc)
    pc=decode(rom.read,pc).next_pc
assert required<=coverage,','.join(f'{pc:04X}' for pc in sorted(required-coverage))
print(f'{sum(counts.values()):,} admission comparisons; all {len(required)} pre-trap instruction starts exercised; '
      '14 new stock calibration bytes verified. AC51 stays explicit; execution stops before SWI.')
