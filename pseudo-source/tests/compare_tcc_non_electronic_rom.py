"""Independent ADAA..AE5B electronic/non-electronic TCC ROM differential.

The source is the hash-recorded full BMHM ROM, not the HAC labels.
Current test is logic/RAM equivalence, not physical TCC-solenoid behavior.
"""
from itertools import islice,product
from pathlib import Path
import json
import random
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from build_factory_scheduler import ROM
from factory_scheduler_replay import FixtureMemory,HC11CPU
from factory_structure import SOURCE,text_sha256
from verify_factory_rom_structure import EXPECTED_SHA256

source=json.loads((ROOT/'maps/structure/bmhm_ownership_rom_evidence.json').read_text())
assert source['rom_sha256']==EXPECTED_SHA256
assert source['listing_sha256_lf']==text_sha256(SOURCE)
image=bytearray(65536);available={}
for block in source['byte_ranges']:
    begin,end=int(block['start'],16),int(block['end_exclusive'],16)
    chunk=bytes.fromhex(block['bytes_hex'])
    assert len(chunk)==end-begin
    image[begin:end]=chunk
    available.update(dict(enumerate(chunk,begin)))
assert all(a in available for a in range(0x4000,65536))
memory=FixtureMemory(ROM(memory=available))
cpu=HC11CPU(memory)
ADDRESSES=(0x0089,0x0853,0x0854)
BASE={0x400f:0x40,0x284:100,0x1d9:50,0x6:170,0x63:100,
      0x89:0,0x853:0,0x854:50,0x4d:0,0x515a:0,
      0x515b:10,0x515c:5,0x515d:6,0x515e:4,0x515f:0}
def case(edits=None):return BASE|(edits or {})
def execute(edits):
    memory.mem[:]=image;memory.mem[:0x4000]=bytes(0x4000)
    for a,v in edits.items():memory.mem[a]=v
    memory.writes.clear()
    cpu.s.sp=0x3ff;cpu.s.ccr=0xc0
    cpu.s.a,cpu.s.b,cpu.s.x,cpu.s.y=0x12,0x34,0x5678,0x9abc
    cpu._push16(0x7000);cpu.s.pc=0xadaa
    for _ in range(1400):
        if cpu.s.pc==0x7000:
            return {'status':0,'state':[memory.mem[a] for a in ADDRESSES]}
        cpu.step()
    raise AssertionError(f'ADAA did not return, PC={cpu.s.pc:04X}')
def compare(items,label):
    total=0;items=iter(items)
    while batch:=list(islice(items,128)):
        rows=[' '.join(map(str,[len(e),*(v for a in e.items() for v in a)])) for e in batch]
        result=subprocess.run([sys.argv[1],romfile],input='\n'.join(rows)+'\n',
            text=True,capture_output=True,check=True)
        out=result.stdout.splitlines()
        assert len(out)==len(batch),(label,len(out),len(batch),result.stderr)
        for state,line in zip(batch,out):
            got=json.loads(line);expected=execute(state)
            if got!=expected:
                raise AssertionError((label,total,state,got,expected))
            total+=1
    print(f'{total:,} ADAA C/ROM states matched: {label}',flush=True)
    return total

with tempfile.TemporaryDirectory(prefix='pcm-tcc-rom-') as directory:
    romfile=str(Path(directory)/'BMHM-hash-recorded.bin')
    Path(romfile).write_bytes(image)
    groups=[]
    for enable,lock,speed,tps,coolant,rpm,delay in product(
        [0,0x40],[0,0x20],[0,1,39,40,100,127,255],
        [0,1,32,128,255],[0,64,128,255],[0,64,128,255],
        [0,1,2,255]):
        changes={0x400f:enable,0x89:lock,0x284:speed,
            0x1d9:tps,0x6:coolant,0x63:rpm,0x853:delay,
            0x854:tps if tps<100 else 100}
        groups.append(case(changes))
    n=compare(groups,'mode, lock state, speed, TPS, coolant, RPM and delay')
    rng=random.Random(0x31adaa)
    changes=[]
    for i in range(5000):
        edits={addr:rng.randrange(256) for addr in [
            0x89,0x284,0x1d9,0x6,0x63,0x853,0x854,0x4d,
            0x515a,0x515b,0x515c,0x515d,0x515e,0x515f,
            0x5160,0x5161,0x5162,0x5163,0x5164,0x5165,0x5166,0x5167]}
        edits[0x400f]=0x40 if i%7 else 0
        if i%4==0:
            edits.update({addr:rng.randrange(256)
                        for addr in list(range(0x5168,0x518c))})
        changes.append(case(edits))
    n+=compare(changes,'random state/calibration values and interpolation boundaries')
    print(f'{n:,} ROM matches for $ADAA non-electronic TCC logic.')
