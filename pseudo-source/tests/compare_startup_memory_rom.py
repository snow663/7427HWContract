"""Working-RAM reset and literal clear helper versus recorded BMHM instructions.

The provider binds selected existing named owners. Stack/cycle and physical RAM
backing remain target contracts; the digest covers the complete fixture image.
"""
from hashlib import sha256
from itertools import product
import json
import os
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import zlib

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
OWNED=set(range(0x360,0x38f))|{0x3b,0x42,0x45,0x399}
coverage=set()
class Failure(Exception):pass
class Memory(FixtureMemory):
    def __init__(self):
        super().__init__(rom);self.active=False;self.events=[];self.attempts=0;self.fail=0
    def event(self,width,a,v):
        if not self.active or (width==8 and a in OWNED and self.serial_clear):return
        self.attempts+=1
        if self.attempts==self.fail:raise Failure
        self.events.append(['W',width,a,v,1])
    def write8(self,a,v):
        a&=65535;self.event(8,a,v&255);self.mem[a]=v&255
    def write16(self,a,v):
        a&=65535;self.event(16,a,v&65535)
        self.mem[a]=v>>8;self.mem[(a+1)&65535]=v&255
memory=Memory();cpu=HC11CPU(memory)

def execute(item):
    mode,address,count,seed,fail=item
    memory.mem[:]=image;memory.mem[:0x4000]=bytes((37*a+seed)&255 for a in range(0x4000))
    memory.events.clear();memory.attempts=0;memory.fail=fail;memory.active=False
    cpu.s.sp=0x3ff;cpu.s.ccr=0xd0;cpu.s.x=address;cpu.s.a=count>>8;cpu.s.b=count&255
    cpu.s.pc=0x7164 if mode else 0xf2fd;stop=0x718a if mode else 0xf325;status=0
    try:
        for _ in range(20000):
            pc=cpu.s.pc
            if pc==stop:break
            coverage.add(pc)
            memory.serial_clear=pc==0x7182
            memory.active=0xf2fd<=pc<0xf325 or pc==0x7182
            cpu.step()
        else:raise AssertionError(f'Clear budget at {cpu.s.pc:04X}')
    except Failure:status=2
    snapshot=bytearray(memory.mem)
    if mode:snapshot[0x3fe:0x400]=bytes(2) # Private target JSR frame; no native C ABI claim.
    return {'status':status,'digest':zlib.adler32(snapshot),'events':memory.events.copy()}

def compare(items,label):
    items=list(items)
    result=subprocess.run([sys.argv[1]],input=''.join(' '.join(map(str,item))+'\n' for item in items),text=True,capture_output=True,check=True)
    lines=result.stdout.splitlines();assert len(lines)==len(items),(label,result.stderr)
    for item,line in zip(items,lines):
        expected=execute(item);actual=json.loads(line)
        if expected!=actual:
            mismatches=[(i,a,b) for i,(a,b) in enumerate(zip(expected['events'],actual['events'])) if a!=b]
            raise AssertionError((label,item,{k:(expected[k],actual[k]) for k in ('status','digest')},
                                  (len(expected['events']),len(actual['events'])),mismatches[:3]))
    print(f'{len(items):,} {label}',flush=True)
    return len(items)

rng=random.Random(0x31f2fd)
with tempfile.TemporaryDirectory(prefix='pcm-startup-memory-') as directory:
    path=Path(directory)/'bmhm.bin';path.write_bytes(image);os.environ['PCM_SERIAL_ROM']=str(path)
    total=compare(((0,a,n,seed,0) for a,n,seed in product([0,1,0x201,0x800,0xfffe],
        [0,1,2,7,8,9,15,16,202,256,413,2040,2047,2048,2049,4095,4096,65528,65535],[0,255])),
        'clear count/alignment/truncation/address-wrap cases')
    total+=compare(((1,0,0,seed,0) for seed in range(256)),'complete working/serial boot clears')
    failures=[]
    for item in [(1,0,0,0xa5,0),(0,0x201,9,0x5a,0),(0,0xfffe,8,0xa5,0)]:
        for fail in range(1,len(execute(item)['events'])+2):failures.append((*item[:4],fail))
    total+=compare(failures,'every selected write-failure prefix and canonical-state retention')
    required=set()
    for start,end in [(0x7164,0x718a),(0xf2fd,0xf326)]:
        pc=start
        while pc<end:required.add(pc);pc=decode(rom.read,pc).next_pc
    # Direct helper cases stop before RTS; startup calls exercise that instruction.
    assert required<=coverage,sorted(required-coverage)
    print(f'{total:,} startup memory comparisons; all {len(required)} scoped instruction starts match.',flush=True)
