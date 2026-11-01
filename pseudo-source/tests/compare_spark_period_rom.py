"""Check normal period/RPM preparation and joined command building against BMHM.

AC51/1812 effects are explicit dependency fixtures. Stop before SWI or AB44;
neither a trap handler nor physical EST output is implemented by these tests.
"""
import ast
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
defaults=json.loads(subprocess.check_output([binary,'--defaults'],text=True))
assert len(defaults)==1194 and len({a for a,_ in defaults})==1194
for a,v in defaults:assert v==rom.read(a,1)[0],(hex(a),v)
NEW_CAL={0x4141,0x4153,0x4517,0x50E4}
assert NEW_CAL<={a for a,_ in defaults}
# Reuse only the prior suite's literal fixtures, without running that suite.
literals={}
for node in ast.parse((Path(__file__).with_name('compare_spark_command_rom.py')).read_text()).body:
    if isinstance(node,ast.Assign) and isinstance(node.targets[0],ast.Name) and node.targets[0].id in ('BASE','OUTPUTS'):
        literals[node.targets[0].id]=ast.literal_eval(node.value)
OUTPUTS=literals['OUTPUTS']+[0x02,0x04,0x18,0x44,0x4F,0x5F,0x60,0x67,0x68,0x69,0xA7,
    0x1C6,0x1CE,0x1CF,0x1E6,0x1E7,0x1E8,0x1E9,0x1EA,0x1EB,0x1EC,0x1ED,
    0x202,0x210,0x211,0x229,0x257,0x258,0x260,0x261,0x28C,0x28D,0x28E,0x28F,
    0x2CE,0x2F4,0x82E,0x83D,0x83E,0x83F,0x840,0x3060,0x306F,0x880,0x881]
assert len(OUTPUTS)==len(set(OUTPUTS))==114
BASE=literals['BASE']|{0x02:4,0x04:0xA5,0x18:0xB5,0x44:0xAD,0x4F:0xB5,0x50:0x05,
    0x5F:0x12,0x60:0x34,0x67:77,0x68:0x12,0x69:0x80,0xA7:100,
    0x1C6:100,0x1CE:128,0x1CF:23,0x1E6:0x08,0x1E7:0x34,0x1E8:0x07,0x1E9:0xD0,
    0x1EA:0,0x1EB:10,0x1EC:0x12,0x1ED:0x34,0x202:0,0x210:0,0x211:0,0x229:0,
    0x257:0x23,0x258:0x45,0x260:0,0x261:0,0x28C:99,0x28D:0x81,0x28E:0x63,0x28F:0x80,
    0x2CE:27,0x2F4:200,0x82E:2,0x83D:0x20,0x83E:0x80,0x83F:0x12,0x840:0x34,
    0x3060:0xB7,0x306F:0x69,0x3FC0:0x07,0x3FC1:0xD0}
ADMISSION_CAL=set(range(0x4133,0x4137))|{0x4142,0x4143,0x414E,0x4962,0x4963,0x4D96}|set(range(0x4E64,0x4E68))


class Failure(Exception):pass
class Missing(Exception):
    def __init__(self,task):self.task=task


class Memory(FixtureMemory):
    def __init__(self):
        super().__init__(rom);self.cpu=HC11CPU(self);self.events=[]
        self.attempts=self.fail_at=self.read_index=0

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
        count=self.mem[0x90B]
        if count:
            assert self.read_index<count
            start=0x910+2*self.read_index;self.read_index+=1
            value=int.from_bytes(self.mem[start:start+2],'big')
        else:value=int.from_bytes(self.mem[a:a+2],'big')
        self.record('R',16,a,value)
        if self.mem[0x908]==3:self.mem[0x1EC:0x1EE]=bytes.fromhex('ffff')
        return value

    def write8(self,a,v):
        if 0x3000<=a<0x4000:
            assert a in (0x3060,0x306F),hex(a);self.record('W',8,a,v&255)
        super().write8(a,v)


memory=Memory();cpu=memory.cpu;coverage=set();blank=bytes(0x1000);cal_bytes=rom.read(0x4000,0x1B04)


def word(a,v):return {a:v>>8,a+1:v&255}
def case(mode,edits=None,*,periods=()):
    values=BASE|(edits or {})
    if periods:
        values[0x90B]=len(periods)
        for i,v in enumerate(periods):values.update(word(0x910+2*i,v))
    return mode,values


def execute(item):
    mode,edits=item
    memory.mem[:0x1000]=blank;memory.mem[0x4000:0x5B04]=cal_bytes
    for a,v in edits.items():memory.mem[a]=v
    memory.events.clear();memory.writes.clear();memory.attempts=memory.read_index=memory.cycle_counter=0
    memory.fail_at=memory.mem[0x907]
    cpu.s.pc=0x7000;cpu.s.sp=0x3FF;cpu.s.ccr=0xD0 if memory.mem[0x909] else 0xC0
    cpu.s.a,cpu.s.b,cpu.s.x,cpu.s.y=0x12,0x34,0x5678,0x9ABC
    value=partial=status=unresolved=0
    def invoke(start,stop):
        nonlocal partial,unresolved
        sp=cpu.s.sp;cpu.s.pc=start
        if stop==0x7000:cpu._push16(stop)
        for _ in range(5000):
            pc=cpu.s.pc
            if pc==stop:
                assert cpu.s.sp==sp,(hex(start),hex(pc),hex(cpu.s.sp),hex(sp))
                return True
            if pc==0xA5D7:return False
            if pc==0xAC51:
                if memory.mem[0x90C]:raise Missing(2)
                action=memory.mem[0x908];memory.record('T',0,pc,action)
                if action==5:
                    memory.mem[0x50]&=0xFB;memory.mem[0x5F:0x61]=bytes.fromhex('ffff');memory.mem[0x61]=0x77
                assert cpu.s.sp==sp
                return False
            if pc==0x1812:
                if memory.mem[0x90A]:raise Missing(1)
                action=memory.mem[0x908];memory.record('T',0,pc,action)
                if action==1:
                    memory.mem[0x1FD:0x1FF]=bytes.fromhex('8123');memory.mem[0x86]&=0xBF
                elif action==2:
                    memory.mem[0x36]|=0x20;memory.mem[0x53]|=0x10;memory.mem[0x06]=255;memory.mem[0x1D9]=7
                cpu.s.a,cpu.s.b,cpu.s.x,cpu.s.y=0xA5,0x5A,0xDEAD,0xBEEF;cpu.s.pc=0x7AA5
                continue
            if mode==28 and pc==0xF44B:partial=memory.read16(cpu.s.x)
            if mode==29 and pc==0xF48C:partial=memory.read16(0x880)
            coverage.add(pc)
            opcode=memory.mem[pc]
            if opcode in (0x0E,0x0F):memory.record('M',0,0,int(opcode==0x0F))
            cpu.step()
            if opcode==0x0E and memory.mem[0x908]==4:
                memory.mem[0x50]|=0x20;memory.mem[0x4F]|=0x80
        raise AssertionError(f'Period execution budget at {cpu.s.pc:04X}')
    try:
        if mode in (28,29):
            target=int.from_bytes(memory.mem[0x900:0x902],'big');old=int.from_bytes(memory.mem[0x902:0x904],'big')
            memory.mem[0x4153]=memory.mem[0x904];cpu.s.d=target;cpu.s.x=old if mode==28 else 0x880;cpu.s.y=0x4153
            if mode==29:memory.mem[0x880:0x882]=old.to_bytes(2,'big')
            invoke(0xF436 if mode==28 else 0xF479,0x7000);value=cpu.s.d
            # F436 overwrites its saved-X stack word with the intermediate,
            # so PULX returns that word. F479 retains its destination pointer.
            assert cpu.s.x==(partial if mode==28 else 0x880) and cpu.s.y==0x4153
        elif mode==30:
            cpu.s.d=int.from_bytes(memory.mem[0x900:0x902],'big');invoke(0xA6BE,0xA6D9);value=cpu.s.d
        elif mode==31:invoke(0xA5E5,0xA62A)
        elif mode==32:
            # The contiguous caller leaves the just-published0062 coordinate
            # in A. The C slice receives it through the named state interface.
            cpu.s.a=memory.mem[0x62];invoke(0xA62A,0xA687)
        elif mode==33:invoke(0xA687,0xA700)
        elif mode==34:invoke(0xA5E5,0xA700)
        elif mode==36:invoke(0xA5E5,0xAB44)
        else:
            assert mode in (35,37)
            if mode==37:invoke(0xCA6B,0x7000)
            value=int(invoke(0xA466,0xAB44))
            if cpu.s.pc==0xA5D7:status=6
    except Failure:status=2;value=0
    except Missing as e:status=1;unresolved=e.task;value=0
    sinks={0x04,0x18,0x41,0x44,0x4F,0x50,0x51,0x53,0x5F,0x60,0x61,0x62,0x63,0x64,0x67,0x68,0x69,0x6E,0x6F,
        0x1C0,0x1C1,0x1C2,0x1C9,0x1CF,0x1E6,0x1E7,0x1E8,0x1E9,0x1EA,0x1EB,0x1EC,0x1ED,
        0x1EE,0x1EF,0x1F0,0x1F1,0x1F2,0x1F3,0x1F4,0x1F5,0x1F8,0x1F9,0x1FA,0x1FB,0x1FC,0x1FD,0x1FE,
        0x202,0x208,0x20B,0x20C,0x20D,0x20E,0x210,0x211,0x229,0x260,0x261,0x28C,0x28D,0x28E,0x28F,0x2CE,
        0x3060,0x306F,0x837,0x838,0x839,0x83A,0x83B,0x83C,0x83D,0x83E,0x83F,0x840,0x841,0x843,0x844,0x880,0x881}
    assert all(a in sinks or 0x3C0<=a<0x400 for a,_ in memory.writes)
    return {'status':status,'value':value,'state':[memory.mem[a] for a in OUTPUTS],
            'masked':int(bool(cpu.s.ccr&0x10)),'unresolved':unresolved,'partial':partial,'events':list(memory.events)}


def compare(items,label):
    iterator=iter(items);count=0
    while chunk:=list(islice(iterator,1024)):
        payload=[]
        for mode,edits in chunk:
            fields=[mode,len(edits)]
            for a,v in edits.items():fields.extend((a,v))
            payload.append(' '.join(map(str,fields)))
        p=subprocess.run([binary],input='\n'.join(payload)+'\n',text=True,capture_output=True,check=True)
        lines=p.stdout.splitlines();assert len(lines)==len(chunk),(label,p.stderr)
        for i,(item,line) in enumerate(zip(chunk,lines)):
            actual=json.loads(line);expected=execute(item)
            assert actual==expected,(label,count+i,item,actual,expected)
        count+=len(chunk)
    print(f'{count:,} {label} match.',flush=True);return count


def filter_math_cases():
    for difference in range(-65535,65536):
        old=65535 if difference<0 else 0;target=old+difference
        yield case(28+(difference&1),word(0x900,target)|word(0x902,old)|{0x904:((abs(difference)>>8)*37)&255})
    for low,gain,mode in product(range(256),range(256),[28,29]):
        old=0x8080;target=(old+0x8000+low)&65535
        yield case(mode,word(0x900,target)|word(0x902,old)|{0x904:gain})
    edges=[0,1,127,128,255,256,0x7FFF,0x8000,0xFF7F,0xFF80,0xFFFF]
    for target,old,gain,mode in product(edges,edges,[0,1,127,128,129,254,255],[28,29]):
        yield case(mode,word(0x900,target)|word(0x902,old)|{0x904:gain})


def sample_cases():
    for p in range(65536):yield case(31,word(0x3FC0,p))
    for coefficient,p in product(range(256),[0,1,153,154,255,256,2000,0x3FFF,0x4000,0x7FFF,0x8000,0x8001,0xFF7F,0xFFFF]):
        yield case(31,word(0x3FC0,p)|{0x4141:coefficient})


def rpm_filter_cases():
    for r in range(65536):
        yield case(32,word(0x83D,r)|word(0x68,r)|word(0x63,(r*73)&65535)|word(0x28E,(r*17)&65535)|
                   {0x62:(r*13)&255,0x02:r>>8,0x4153:r>>8,0x4517:255-(r>>8),0x50E4:((r>>8)*37)&255})
    for phase,monitor,gain,previous in product(range(256),[0,1,0x7FFF,0xFF7F,0xFF80,0xFFFF],[0,1,128,255],[0,1,255]):
        yield case(32,word(0x28E,monitor)|{0x02:phase,0x50E4:gain,0x28C:previous})


def term_cases():
    for p in range(65536):
        yield case(33,word(0x1E8,p)|word(0x1E6,(p*73+21)&65535)|word(0x1EA,(p*17)&65535)|
                   {0x1C0:p&255,0x1C2:p>>8,0xA7:(p*29)&255})
    for now,old in product(range(256),repeat=2):
        yield case(33,word(0x1E8,2000)|word(0x1E6,2100)|word(0x1EA,0)|{0x1C0:now,0x1C2:old})
    for adaptive in range(65536):
        yield case(33,word(0x1E8,60000)|word(0x1E6,62048)|word(0x1EA,adaptive)|{0x1C0:0,0x1C2:0})
    for battery,p,limit in product(range(256),[0,1,38,39,40,457,458,1637,1638,65535],[0,38,39,40,1000,65535]):
        yield case(33,word(0x1E8,p)|word(0x3FC0,limit)|{0xA7:battery})


counts={}
counts['math']=compare(filter_math_cases(),'word-filter return/intermediate C/ROM cases')
counts['reference']=compare((case(30,word(0x900,p)) for p in range(65536)),'reference-term C/ROM cases')
counts['sample']=compare(sample_cases(),'period-sample/coordinate C/ROM cases')
counts['filters']=compare(rpm_filter_cases(),'RPM/filter C/ROM cases')
counts['terms']=compare(term_cases(),'adaptive-period/battery/limit C/ROM cases')

rng=random.Random(0x31A5E5);joined=[]
for i in range(2048):
    edits={a:rng.randrange(256) for a in sorted(NEW_CAL|ADMISSION_CAL|BASE.keys())}
    edits.update({0x908:i%6,0x909:i&1,0x90A:(i>>1)&1,0x90C:(i>>2)&1,0x86:0xE0 if i&2 else 0xA0})
    joined.append(case([34,35,36,37][i%4],edits))
for mode,action,masked,p,q in product([34,35,36,37],range(6),[0,1],[0,153,154,2000,0x8000,65535],[0,38,39,50000]):
    joined.append(case(mode,{0x908:action,0x909:masked},periods=(p,q,p,q)))
for mode,p in product([35,37],range(256)):
    joined.append(case(mode,{0x50:0x25,0x4F:0x25,0x44:0xAD,0x210:1,0x211:1,0x90B:0},periods=(p*13,p*17,p*19,p*23)))
counts['joined']=compare(joined,'joined precompute/admission/command witnesses')
failures=[]
for item in joined[::19]:
    for failure in range(1,len(execute(item)['events'])+1):failures.append((item[0],item[1]|{0x907:failure}))
counts['failures']=compare(failures,'period/build failure prefixes')
history=[];edits={0x4F:0x25,0x44:0xA5}
for tick in range(256):
    edits.update(word(0x3FC0,2000+tick*7));edits.update({0x50:0x25 if tick<24 or tick%7==0 else 0x05,
        0x02:tick%160,0x908:3 if tick%11==0 else 0,0x86:0xA0})
    item=case(35,dict(edits));history.append(item)
    edits.update(dict(zip(OUTPUTS,execute(item)['state'])))
counts['history']=compare(history,'full-builder history calls')

required=set()
for start,end in [(0xA5E5,0xA700),(0xF436,0xF459),(0xF479,0xF499)]:
    pc=start
    while pc<end:required.add(pc);pc=decode(rom.read,pc).next_pc
assert required<=coverage,','.join(f'{pc:04X}' for pc in sorted(required-coverage))
print(f'{sum(counts.values()):,} period comparisons; all {len(required)} scoped instruction starts exercised; '
      '4 scoped calibration bytes (3 new,1 shared) and all 1,194 fixture bytes match stock. AC51/1812 and SWI/AB44 boundaries stay explicit.')
