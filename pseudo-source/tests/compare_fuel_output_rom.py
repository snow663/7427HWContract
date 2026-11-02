"""ADC/battery and injector-finalizer C versus actual stock BMHM instructions.

ADC completion and callbacks are supplied bus fixtures, not an electrical model.
The fuel tail at852C and slot-F work afterE306 remain outside these slices.
"""
from hashlib import sha256
from itertools import islice, product
import json
from pathlib import Path
import random
import re
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from build_factory_scheduler import recorded_rom
from factory_scheduler_replay import FixtureMemory, HC11CPU
from factory_rom_decode import decode
from verify_factory_ownership import EVIDENCE
from verify_factory_rom_structure import EXPECTED_SHA256

binary=sys.argv[1]
rom=recorded_rom(json.loads(EVIDENCE.read_text()))
assert sha256(bytes([255])*0x4000+rom.read(0x4000,0xc000)).hexdigest()==EXPECTED_SHA256
source=json.loads(subprocess.check_output([binary,'--defaults'],text=True))
CAL=set(range(0x496d,0x4974))-{0x4971,0x4972}
CAL.update(range(0x4b05,0x4b16))
assert {a for a,_ in source}==CAL
for a,v in source: assert rom.read(a,1)[0]==v,(hex(a),v)
text=Path(__file__).with_name('fuel_output_fixture_map.h').read_text()
state_text=text.split('static const Mapping reference_state_map[] = {')[1].split('};')[0]
state_text+='\n'+text.split('static const Mapping fuel_state_map[] = {')[1].split('};')[0]
RAM=set()
for kind,address in re.findall(r'\b([BWF])\((0x[0-9a-f]+|\d+),',state_text):
    address=int(address,0);RAM.add(address)
    if kind=='W':RAM.add(address+1)
OUTPUTS=sorted(RAM|set(range(0x3000,0x3035))|set(range(0x3fc0,0x3ffe)))
REF_CAL=set()
for kind,address,rest in re.findall(r'\b([BWA])\((0x[0-9a-f]+|\d+),([^\n]+?)\)',text.split('static const Mapping reference_cal_map[] = {')[1].split('};')[0]):
    address=int(address,0);size=2 if kind=='W' else int(rest.split(',')[0]) if kind=='A' else 1
    REF_CAL.update(range(address,address+size))
ALL_CAL=REF_CAL|CAL|{0x4eb6}
BASE={a:0 for a in RAM|set(range(0x900,0x90a))}
BASE.update({0x44:0,0x4f:0x10,0x50:0,0x55:130,0xa7:130,0x3e:0,0x3f:0x80,
    0x3008:0xe7,0x3031:34,0x3032:135,0x3033:198,0x3034:130,
    0x3ffc:0xb9,0x3ffd:0x3a,0x3fce:0xa5,0x3fcf:0x5a,
    0x24e:0x01,0x24f:0x00,0x250:0xab,0x251:0xcd,0x5f:0x12,0x60:0x34,
    0x3fca:0x12,0x3fcb:0x34,0x3ffa:0,0x3ffb:0,0x256:7})
def word(a,v):return {a:v>>8,a+1:v&255}
def case(mode,edits=None):return mode,BASE|(edits or {})

class Failure(Exception):pass
class Memory(FixtureMemory):
    def __init__(self):
        super().__init__(rom);self.cpu=HC11CPU(self);self.events=[]
        self.attempts=self.fail_at=self.control=self.polls=0
        self.in_word=False
    def record(self,kind,width,a,value):
        self.attempts+=1
        if self.attempts==self.fail_at:raise Failure
        self.events.append([kind,width,a,value,int(bool(self.cpu.s.ccr&0x10))])
    def read8(self,a):
        value=super().read8(a)
        if not self.in_word and 0x3000<=a<0x4000:
            if self.mem[0x90a]:
                mux=(self.mem[0x3008]>>3)&7
                if a==0x3034 and mux in (7,6,1):value=self.mem[0x90b if mux==7 else 0x90c if mux==6 else 0x90d]
                if self.control==0x11 and a==0x3032:value=self.mem[0x90e]
                if self.control==0x11 and a==0x3033:value=self.mem[0x90f]
            if a==0x3030:
                limit=self.mem[0x900 if self.control==7 else 0x901 if self.control==0x14 else 0x902]
                value=(value&127)|(128 if self.polls>=limit else 0)
            self.record('R',8,a,value)
            if a==0x3030:self.polls+=1
            action=self.mem[0x908]
            if a==0x3031 and self.control==0x14 and action in (1,2):
                self.mem[0x50]=(self.mem[0x50]&0xfe)|(action==1)
            if a==0x3008 and action==6:self.mem[a]^=0xc7
        return value
    def read16(self,a):
        if not 0x3000<=a<0x4000:return super().read16(a)
        value=(FixtureMemory.read8(self,a)<<8)|FixtureMemory.read8(self,a+1)
        self.record('R',16,a,value)
        if a==0x3fca and self.mem[0x908]==5:
            self.mem[0x44]|=0x10;self.mem[0x50]|=1;self.mem[a:a+2]=bytes.fromhex('abcd')
        return value
    def write8(self,a,v):
        if not self.in_word and 0x3000<=a<0x4000:self.record('W',8,a,v&255)
        if a==0x3023:self.mem[a]&=~v&255
        else:super().write8(a,v)
        if a==0x3030:self.control=v;self.polls=0
    def write16(self,a,v):
        if not 0x3000<=a<0x4000:return super().write16(a,v)
        self.record('W',16,a,v&65535)
        self.in_word=True
        try:super().write16(a,v)
        finally:self.in_word=False

memory=Memory();cpu=memory.cpu;coverage=set()
def execute(item):
    mode,edits=item
    memory.mem[:0x1800]=bytes(0x1800);memory.mem[0x3000:0x4000]=bytes(0x1000)
    memory.mem[0x4000:0x6000]=rom.read(0x4000,0x2000)
    for a,v in edits.items():memory.mem[a]=v
    memory.events.clear();memory.writes.clear();memory.attempts=memory.polls=memory.control=memory.cycle_counter=0
    memory.fail_at=memory.mem[0x907];cpu.s.sp=0x3ff;cpu.s.ccr=0xd0 if memory.mem[0x909] else 0xc0
    cpu.s.a,cpu.s.b,cpu.s.x,cpu.s.y=0x12,0x34,0x5678,0x9abc
    status=0
    def invoke(start,stop=0x7000,pulse=False):
        sp=cpu.s.sp;cpu._push16(0x7000);cpu.s.pc=start
        if pulse:cpu.s.a,cpu.s.b=memory.mem[0x24e],memory.mem[0x24f]
        for _ in range(4000):
            pc=cpu.s.pc
            if pc==stop:
                if stop!=0x7000:assert cpu._pull16()==0x7000
                assert cpu.s.sp==sp;return
            coverage.add(pc);opcode=memory.mem[pc]
            if opcode in (0x0e,0x0f):memory.record('M',0,0,int(opcode==0x0f))
            if pc==0x7524:delay_start=memory.cycle_counter
            cpu.step()
            if pc==0x7527:
                cycles=memory.cycle_counter-delay_start;assert cycles==33
                memory.record('D',0,0,cycles)
            action=memory.mem[0x908]
            if opcode==0x0e and action==3:
                memory.mem[0x55]=99;memory.mem[0xa7]=255;memory.mem[0x3034]=7
            if opcode==0x0f and action==4:
                memory.mem[0x82e]=33;memory.mem[0x50]|=1
        raise AssertionError(f'Fuel output slice budget at {cpu.s.pc:04X}')
    entries=[[(0xf245,)],[(0x7b70,0x7b9b)],[(0xc56f,)],[(0x8613,)],[(0xe2fb,0xe306)],
             [(0x84bc,0x852c)],[(0x84f5,0x852c,True)],[(0x8548,0x7000,True)],
             [(0xc56f,),(0x8613,),(0xe2fb,0xe306),(0x84bc,0x852c)],
             [(0xe2fb,0xe306),(0x84bc,0x852c),(0x751b,0x77c6)],
             [(0xf245,),(0x751b,0x77c6),(0xf245,)],[(0x7b6d,0x7b9b)],
             [(0xf20d,)],[(0x7aa6,)],[(0x7ab7,)],[(0x7ab7,),(0x8613,),(0xe2fb,0xe306),(0x84bc,0x852c)]]
    try:
        for entry in entries[mode]:invoke(*entry)
    except Failure:status=2
    unknown=[(a,v) for a,v in memory.writes if a not in OUTPUTS and not (0x3c0<=a<0x400 or 0xad<=a<=0xb2)]
    assert not unknown,[(hex(a),v) for a,v in unknown]
    return {'status':status,'masked':int(bool(cpu.s.ccr&0x10)),
            'state':[memory.mem[a] for a in OUTPUTS],'events':list(memory.events)}

def compare(items,label):
    iterator=iter(items);count=0
    while chunk:=list(islice(iterator,512)):
        payload=[]
        for mode,edits in chunk:
            values=[mode,len(edits)]
            for a,v in edits.items():values.extend((a,v))
            payload.append(' '.join(map(str,values)))
        result=subprocess.run([binary],input='\n'.join(payload)+'\n',text=True,capture_output=True,check=True)
        lines=result.stdout.splitlines();assert len(lines)==len(chunk),result.stderr
        for n,(item,line) in enumerate(zip(chunk,lines)):
            actual=json.loads(line);expected=execute(item)
            if actual!=expected:
                Path('/tmp/fuel-output-failure.json').write_text(json.dumps({'item':item,'actual':actual,'expected':expected,'outputs':OUTPUTS}))
                diffs=[(hex(a),x,y) for a,x,y in zip(OUTPUTS,actual['state'],expected['state']) if x!=y]
                raise AssertionError((label,count+n,item,diffs,{k:(actual[k],expected[k]) for k in actual if k!='state' and actual[k]!=expected[k]}))
        count+=len(chunk)
    print(f'{count:,} {label} match.',flush=True);return count

counts={};rng=random.Random(0x3184bc)
counts['direct']=compare((case(mode) for mode in range(16)),'direct slices and joined entries')
variants=[]
for i in range(2048):
    edits={a:rng.randrange(256) for a in sorted(RAM|ALL_CAL)}
    edits.update({0x907:0,0x908:i%7,0x909:i&1,0x900:i%16,0x901:i%15,0x902:i%15})
    edits.update({a:rng.randrange(256) for a in range(0x90a,0x910)});edits[0x90a]=1
    variants.append(case(i%16,edits))
counts['random']=compare(variants,'random state/profile, ADC readiness and callback cases')
if '--quick' in sys.argv:
    print('Preliminary comparison complete.');sys.exit(0)
counts['sync_words']=compare((case(5,word(0x24e,pulse)|{0x256:offset,0x3f:short})
    for pulse,(offset,short) in product(range(65536),[(0,0),(255,0x80)])),
    'all synchronous pulse words at zero/maximum offset')
counts['publish_words']=compare((case(6,word(0x24e,pulse)|{0x256:offset})
    for pulse,offset in product(range(65536),[0,255])), 'all direct-publish words at both offset extremes')
counts['minimum']=compare((case(5,word(0x496d,limit)|word(0x496f,replacement)|word(0x24e,pulse))
    for limit,replacement,pulse in product([0,1,31,32,255,256,32767,65535],[0,1,65535],range(512))),
    'minimum/replacement, subtraction and short-pulse boundary combinations')
counts['short_curve']=compare((case(mode,word(0x24e,pulse)|word(0x4971,subtract)|
    {0x400e:option}|{a:(a*17+subtract)&255 for a in range(0x4979,0x498a)})
    for mode,pulse,subtract,option in product([5,7],range(257),[0,1,255,256,65535],[0,16])),
    'rising/falling short-pulse shaping, async option and subtraction borrow')
counts['delay']=compare((case(6,{0x400b:1,0x4973:gain}|word(0x5f,period))
    for gain,period in product(range(256),[0,1,255,256,16383,16384,32767,32768,65535])),
    'CPI/PFI delay gain and both shift carries')
counts['battery']=compare((case(3,{0xa7:sample,0x44:flags,0x50:old,0x400c:mode})
    for sample,flags,old,mode in product(range(256),[0xa5,0xb5],[0xa4,0xa5],[0,1])),
    'battery thresholds, capture admission and retained unrelated flag bits')
counts['adc']=compare((case(mode,{0x900:ready7,0x901:ready,0x902:ready,0x50:gate,0x908:action,0x909:masked})
    for mode,ready7,ready,gate,action,masked in product([0,1,2,8,10,11,12,13,14,15],[0,15],[0,1,11,12,13],[0,1],range(7),[0,1])),
    'ADC completion/timeout, mask, MAP gating and callback order')
counts['averages']=compare((case(1,{0x3031:a,0x3032:b,0x3033:(a+b)&255,0x3034:a^b})
    for a,b in product(range(256),repeat=2)), 'all first/second ADC pairs with carry/rounding across four samples')
counts['offset']=compare((case(4,{0xa7:sample}|{a:(a*17+sample)&255 for a in range(0x4b05,0x4b16)})
    for sample in range(256)), 'every battery offset coordinate and rising/falling knots')
counts['auxiliary']=compare((case(mode,{0x90a:1,0x90b:sample,0x90c:sample^255,0x90d:sample,
    0x90e:sample^128,0x90f:sample^64,0x902:ready,0x3008:port,0x44:0x10})
    for mode,sample,ready,port in product([12,13,14,15],range(256),[0,11,12,13],[0,255])),
    'auxiliary mux samples, slot0/2 admissions and raw-battery producer/consumer joins')
joined=[]
for mode,action,sample,gate,pulse in product([8,9,10,11,12,13,14,15],range(7),[0,39,40,89,90,255],[0,1],[0,1,255,256,32767,65535]):
    joined.append(case(mode,{0xa7:sample,0x908:action,0x50:gate,0x44:0x10,0x400b:0x10,
        0x400c:4,0x400e:16,0x4f:0,0x2cd:3,0x2ce:24}|word(0x24e,pulse)|word(0x2cf,pulse)))
counts['joined']=compare(joined,'ADC/battery/finalizer/REF joins with retained packet state')
failures=[]
for item in variants[::31]+joined[::41]:
    for fail in range(1,len(execute(item)['events'])+1):failures.append((item[0],item[1]|{0x907:fail}))
counts['failures']=compare(failures,'all selected read/write/mask/delay failure prefixes')
history=[];edits={0x4f:0,0x400c:4,0x400b:4,0x400e:16,0x2cd:3}
for i in range(1024):
    edits.update({0xa7:[0,39,40,89,90,130,170,255][i%8],0x908:i%7,
        0x901:i%14,0x902:i%14,0x900:i%16,0x3031:i&255,0x3032:(i*7)&255,
        0x3033:(i*11)&255,0x3034:(i*17)&255,2:i%160})
    edits.update(word(0x24e,(i*127)&65535));edits.update(word(0x2cf,(i*257)&65535))
    item=case([8,9,10,11][i%4],edits.copy());history.append(item)
    edits.update(dict(zip(OUTPUTS,execute(item)['state'])))
counts['history']=compare(history,'retained ADC/ignition/pulse/REF histories')
required=set()
for start,end in [(0x7b70,0x7b9b),(0xf20d,0xf280),(0xc56f,0xc583),(0x8613,0x863d),
                  (0xe2fb,0xe306),(0x84bc,0x852c),(0x8548,0x858b),(0x7aa6,0x7aad),(0x7ab7,0x7abd),(0xcf15,0xcf16)]:
    pc=start
    while pc<end:required.add(pc);pc=decode(rom.read,pc).next_pc
assert required<=coverage,','.join(f'{a:04X}' for a in sorted(required-coverage))
print(f'{sum(counts.values()):,} fuel input/output comparisons; all {len(required)} scoped instruction starts; '
      f'{len(CAL)} new profile bytes match stock. Hardware timing, broader fuel controller and scheduled producers remain explicit.')
