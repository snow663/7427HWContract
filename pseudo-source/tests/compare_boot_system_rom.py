"""Focused retained-boot C/ROM comparisons, including the rooted full checksum.

Foreign operand transactions are recorded separately from instruction fetch and
private HC11 stack traffic. This does not establish a native target ABI.
"""
from hashlib import sha256
from itertools import islice,product
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from build_factory_scheduler import recorded_rom
from factory_scheduler_replay import FixtureMemory,HC11CPU
from factory_rom_decode import decode
from verify_factory_ownership import EVIDENCE
from verify_factory_rom_structure import EXPECTED_SHA256

rom=recorded_rom(json.loads(EVIDENCE.read_text()))
image=bytes([255])*0x4000+rom.read(0x4000,0xc000)
assert sha256(image).hexdigest()==EXPECTED_SHA256
binary=sys.argv[1];focused='--focused' in sys.argv
coverage=set();decoded={}
class Failure(Exception):pass
class Memory(FixtureMemory):
    def __init__(self):
        super().__init__(rom);self.foreign=None;self.fetching=False;self.events=[];self.attempts=0
    def record(self,kind,width,a,value):
        self.attempts+=1
        if self.attempts==self.fail:raise Failure
        self.events.append([kind,width,a,value,int(bool(cpu.s.ccr&0x10))])
    def read8(self,a):
        a&=65535;value=self.mem[a]
        if not self.fetching and a==self.foreign and 'R' in self.foreign_access:
            self.record('R',8,a,value)
            if self.action==1 and a==0x5bca:self.mem[a]=(value+1)&255
            if self.action==2 and a==0x82f:self.mem[a]=0
            if self.action==3 and a==0x15:self.mem[a]^=255
        return value
    def read16(self,a):
        a&=65535;value=self.mem[a]<<8|self.mem[(a+1)&65535]
        if not self.fetching and a==self.foreign and 'R' in self.foreign_access:self.record('R',16,a,value)
        return value
    def write8(self,a,v):
        a&=65535;v&=255
        if a==self.foreign:self.record('W',8,a,v)
        self.mem[a]=v
    def write16(self,a,v):
        a&=65535;v&=65535
        if a==self.foreign:self.record('W',16,a,v)
        self.mem[a]=v>>8;self.mem[(a+1)&65535]=v&255
memory=Memory();cpu=HC11CPU(memory)
# Operand data can equal its own instruction address during the ROM sum.
# Wrap actual fetches instead of inferring fetch/data from address equality.
original_fetch=cpu._fetch8
def fetch():
    memory.fetching=True
    try:return original_fetch()
    finally:memory.fetching=False
cpu._fetch8=fetch

def word(a,v):return{a:v>>8,a+1:v&255}
BASE={0x303f:0x0b,0x82f:0,0x15:0,0x3a:0,0x44:0,0x86:0,0x1e:4,0x31:1,
      **word(0x3ffc,0xb93a),**{a:128 for a in range(0x2f8,0x32c)}}
def case(mode,edits=None,fail=0,action=0,masked=0):return mode,fail,action,masked,BASE|(edits or {})

def execute(item):
    mode,fail,action,masked,edits=item
    memory.mem[:]=image;memory.mem[:0x4000]=bytes(0x4000)
    for a,v in edits.items():memory.mem[a]=v
    memory.events.clear();memory.attempts=0;memory.fail=fail;memory.action=action;memory.foreign=None
    cpu.s.sp=0x3ff;cpu.s.ccr=0xd0 if masked else 0xc0;cpu.s.a=0x12;cpu.s.b=0x34
    cpu.s.x=0x4008;cpu.s.y=0x5678
    status=0;out=0x5aa5;loop_seen=False;gap_start=0
    starts=[0xf2aa,0x71c3,0x720c,0x723f,0x726b,0x71c3]
    stops=[0x7000,0x720c,0x723f,0x726b,0x7393,0x7393]
    if mode==0:cpu._push16(0x7000)
    cpu.s.pc=starts[mode]
    try:
        for _ in range(300000):
            pc=cpu.s.pc
            if pc==stops[mode]:
                if mode==0:out=cpu.s.y
                break
            if pc==0x7208:
                if loop_seen:status=7;break
                loop_seen=True
            coverage.add(pc)
            inst=decoded.setdefault(pc,decode(rom.read,pc)) if pc not in decoded else decoded[pc]
            memory.foreign=None;memory.foreign_access=''
            access=inst.access()
            if access is not None and not 0xf280<=pc<0xf28e:
                memory.foreign_access=access['access']
                if inst.mode in ('direct','extended'):memory.foreign=inst.value
                elif inst.mode=='indexed_x':memory.foreign=(cpu.s.x+inst.value)&65535
                elif inst.mode=='indexed_y':memory.foreign=(cpu.s.y+inst.value)&65535
            if pc==0x71f2:gap_start=memory.cycle_counter
            cpu.step()
            if pc==0xf3ed and cpu.s.pc==0x71f5:
                gap=memory.cycle_counter-gap_start;assert gap==11
                memory.record('D',0,0,gap)
        else:raise AssertionError(f'Boot execution budget at {cpu.s.pc:04X}')
    except Failure:status=2
    state=bytearray(memory.mem[:0x900]);state[0x3b0:0x400]=bytes(0x50)
    state+=memory.mem[0x3000:0x3070]+memory.mem[0x3fc0:0x3ffe]
    return {'status':status,'value':out,'state':state.hex(),'events':list(memory.events)}

def compare(items,label,chunk_size=64):
    items=iter(items);count=0
    while chunk:=list(islice(items,chunk_size)):
        lines=[]
        for mode,fail,action,masked,edits in chunk:
            data=[mode,fail,action,masked,len(edits)]
            for a,v in edits.items():data.extend((a,v))
            lines.append(' '.join(map(str,data)))
        result=subprocess.run([binary],input='\n'.join(lines)+'\n',text=True,capture_output=True,check=True)
        outputs=result.stdout.splitlines();assert len(outputs)==len(chunk),result.stderr
        for item,line in zip(chunk,outputs):
            actual=json.loads(line);expected=execute(item)
            if actual!=expected:
                Path('/tmp/boot-system-failure.json').write_text(json.dumps({'item':item,'actual':actual,'expected':expected}))
                diff=[(i,a,b) for i,(a,b) in enumerate(zip(actual['events'],expected['events'])) if a!=b]
                ram=[(hex(i),a,b) for i,(a,b) in enumerate(zip(bytes.fromhex(actual['state']),bytes.fromhex(expected['state']))) if a!=b]
                raise AssertionError((label,item[:4],{k:(actual[k],expected[k]) for k in ['status','value']},
                    (len(actual['events']),len(expected['events'])),diff[:3],ram[:8]))
        count+=len(chunk)
    print(f'{count:,} {label} match.',flush=True);return count

with tempfile.TemporaryDirectory(prefix='pcm-boot-system-') as directory:
    path=Path(directory)/'bmhm.bin';path.write_bytes(image);os.environ['PCM_BOOT_ROM']=str(path)
    subprocess.run([binary,'--contracts'],check=True)
    counts={}
    counts['direct']=compare((case(mode) for mode in range(6)),'direct checksum/validation/recovery entries',2)
    counts['rom']=compare((case(1,{0x303f:config,0x4008:ident,0x82f:adc}|word(0x4006,expected),action=action)
        for config,ident,adc,expected,action in product([0,0x0b],[0x31,0xaa,0],[99,100],
        [int.from_bytes(image[0x4006:0x4008],'big'),0],[0,2])),
        'ROM/configuration acceptance, AA escape and captured-sample wait',2)
    counts['retained']=compare((case(2,{a:(a*17+seed)&255 for a in range(0xb,0x36)}|
        {0x15:checksum,0x86:flags,0x46:flags}) for seed,checksum,flags in product(
        [0,1,127,255],[0,1,127,255],[0,255])),'retained checksum, reset ranges and canonical owners')
    valid=[]
    for seed in range(16):
        edits={a:(a*17+seed)&255 for a in range(0xb,0x15)}
        edits[0x15]=(-sum(edits.values()))&255
        edits.update({0x2a7:37,0x2b3:23,0x2f6:61,0x2f7:0xa5})
        valid.append(case(2,edits))
    counts['accepted']=compare(valid,'nonzero valid retained logs preserve learned state and TPS zero')
    counts['adaptive']=compare((case(3,{a:value for a in range(0x2f8,0x32c)}|{changed:other})
        for value,changed,other in product([0,128,255],[0x2f8,0x310,0x32b],[0,1,127,128,255])),
        'adaptive cumulative-sum validation and complete fill footprints')
    counts['recovery']=compare((case(4,{a:value for a in range(0x1f,0x35)}|{0x1e:flags,0x400f:mode,
        0x5bca:threshold,0x5bc7:threshold,0x5bc8:threshold,0x5bc9:threshold},action=action)
        for value,flags,mode,threshold,action in product([0,1,2,4,5,127,254,255],[0,4],[0,128],
        [0,1,5,255],[0,1])),'recovery counters, repeated thresholds, literal clears and zero B stores')
    failures=[]
    for item in [case(1,{0x303f:0}),case(2,{0x15:1}),case(3,{a:0 for a in range(0x2f8,0x32c)}),case(4)]:
        for fail in range(1,len(execute(item)['events'])+2):failures.append((item[0],fail,*item[2:]))
    counts['failures']=compare(failures,'every foreign-operation failure of selected boot paths')
    counts['joined']=compare([case(5,{0x15:1}),case(5,{0x303f:0,0x82f:99}),
        case(5,{0x303f:0,0x82f:100},action=2),
        case(5,{a:0 for a in range(0x2f8,0x32c)})],
        'connected ROM-failure/recovery, retained-loss and adaptive-loss boot histories',2)
    # Root checksum failures at source reads and both COP writes, including late
    # prefixes, without an O(N^2) sweep of all49192 operations during development.
    checksum=case(0);trace=execute(checksum)['events']
    positions={1,2,8,2040,2041,2042,len(trace)-2,len(trace)-1,len(trace),len(trace)+1}
    if not focused:positions|={i+1 for i,event in enumerate(trace) if event[0]=='W'}
    counts['checksum_failures']=compare((case(0,fail=fail) for fail in sorted(positions)),
        'selected full-checksum read/COP failed prefixes',2)
    required=set()
    for start,end in [(0x71c3,0x7393),(0xf2aa,0xf2fd)]:
        pc=start
        while pc<end:required.add(pc);pc=decode(rom.read,pc).next_pc
    unreachable={0xf2b9,0xf2bb,0xf2bd,0xf2be,0xf2c0} # Rooted X=4008 skips this prefix.
    missing=required-coverage-unreachable
    print('Uncovered scoped starts:',','.join(f'{a:04X}' for a in sorted(missing)),flush=True)
    assert not missing
    print(f'{sum(counts.values()):,} retained-boot comparisons; {len(required-unreachable)} rooted instruction starts '
          'covered. Five generic checksum-prefix starts remain outside the rooted4008 contract.',flush=True)
