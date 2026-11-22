"""Compare captured-X guard policy to actual795C..7976 stock instructions.

The existing host contract sweeps every X. Default ROM comparison does too;
--focused keeps development runs to boundaries, byte-class representatives,
callback mutation and each access-failure prefix. LDS/entry remain explicit.
"""
from hashlib import sha256
from itertools import islice,product
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from build_factory_scheduler import recorded_rom
from factory_scheduler_replay import FixtureMemory,HC11CPU
from factory_rom_decode import decode
from verify_factory_ownership import EVIDENCE
from verify_factory_rom_structure import EXPECTED_SHA256
rom=recorded_rom(json.loads(EVIDENCE.read_text()))
assert sha256(bytes([255])*0x4000+rom.read(0x4000,0xc000)).hexdigest()==EXPECTED_SHA256
binary=sys.argv[1];focused='--focused' in sys.argv
coverage=set()
class Failure(Exception):pass
class Memory(FixtureMemory):
    def record(self,op,a,value):
        self.events.append([op,a,value]);self.attempts+=1
        if self.attempts==self.fail:raise Failure
    def read8(self,a):
        value=self.mem[a]
        if a in (0x3a,0x4f):
            self.record('R',a,value)
            if a==0x4f:
                self.reads_4f+=1
                if self.reads_4f==1 and self.action in (1,2):self.mem[a]^=0x80 if self.action==1 else 4
            if a==0x3a and self.action==3:self.mem[a]^=0x80
        return value
    def write8(self,a,value):
        if a in (0x3a,0x4f):self.record('W',a,value&255)
        self.mem[a]=value&255
        if a==0x3a and self.action==4:self.mem[0x4f]^=0xc0
memory=Memory(rom);cpu=HC11CPU(memory)

def execute(item):
    x,flags,faults,action,fail=item
    memory.mem[0x4f]=flags;memory.mem[0x3a]=faults
    memory.events=[];memory.attempts=memory.reads_4f=0;memory.action=action;memory.fail=fail
    cpu.s.pc=0x795c;cpu.s.sp=0x3ff;cpu.s.x=x;cpu.s.ccr=0xc0
    status=0;recovery=False
    try:
        for _ in range(24):
            pc=cpu.s.pc
            if pc in (0x7977,0x797a):recovery=pc==0x7977;break
            coverage.add(pc);cpu.step()
        else:raise AssertionError(f'Guard budget at {cpu.s.pc:04X}')
    except Failure:status=2
    assert cpu.s.sp==0x3ff and cpu.s.x==x
    return {'status':status,'recovery':int(recovery),'flags':memory.mem[0x4f],
        'faults':memory.mem[0x3a],'events':list(memory.events)}

def compare(items,label):
    items=iter(items);count=0
    while chunk:=list(islice(items,512)):
        payload=''.join(' '.join(map(str,item))+'\n' for item in chunk)
        result=subprocess.run([binary,'--cases'],input=payload,text=True,capture_output=True,check=True)
        lines=result.stdout.splitlines();assert len(lines)==len(chunk),result.stderr
        for item,line in zip(chunk,lines):
            actual=json.loads(line);expected=execute(item)
            assert actual==expected,(label,item,actual,expected)
        count+=len(chunk)
    print(f'{count:,} {label} match.',flush=True);return count

subprocess.run([binary,'--contracts'],check=True)
counts={}
xs=range(65536) if not focused else sorted({0,1,0xffff,0x3af,0x3b0,0x3b1,0x3ed,0x3ee,0x3ef,
    0x3f6,0x3f7,0x3f8,0x3ff,0x400}|{high*256+low for high,low in product(range(256),[0,0xaf,0xb0,0xee,0xef,0xf7,0xf8,255])})
counts['x']=compare(((x,flags,0x51,0,0) for x,flags in product(xs,[0x93,0x97])),
    'captured-X bounds across busy/nonbusy and high/low byte classes')
counts['flags']=compare(((x,flags,faults,action,0) for x,flags,faults,action in product(
    [0x3af,0x3b0,0x3ee,0x3ef,0x3f7,0x3f8],range(0,256,17),[0,8,0x20,255],range(5))),
    'cause/busy preservation and captured-versus-fresh RMW callback mutation')
failures=[]
for item in [(0x3af,0x84,0x20,action,0) for action in range(5)]+[(0x3b0,0x84,0x20,0,0)]:
    failures.extend((*item[:4],fail) for fail in range(1,len(execute(item)['events'])+2))
counts['failures']=compare(failures,'each attempted guard read/write failure and success prefix')
required=set();pc=0x795c
while pc<0x7977:required.add(pc);pc=decode(rom.read,pc).next_pc
assert not required-coverage,sorted(required-coverage)
print(f'{sum(counts.values()):,} timer guard C/ROM comparisons; all{len(required)} software starts match. '
      'TSX/PSHX/PULX, LDS and target RTI remain separate.',flush=True)
