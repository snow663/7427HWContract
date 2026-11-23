"""Independent BMHM D5B7..D69E candidate-gear selection C/HC11 differential.

Input is accumulator-B (candidate) at the exact D5B7 instruction boundary.
The gear-slot differential covers its D4F7..D5B6 caller through both scheduled entries.
The original E562 callee is executed in ROM, including indexed reads beyond
the nominal range table. No hardware transmission actuator is exercised.
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

record=json.loads((ROOT/'maps/structure/bmhm_ownership_rom_evidence.json').read_text())
assert record['rom_sha256']==EXPECTED_SHA256
assert record['listing_sha256_lf']==text_sha256(SOURCE)
assert record['rom_size_bytes']==65536
raw=bytearray(65536);available={}
for block in record['byte_ranges']:
    start,end=int(block['start'],16),int(block['end_exclusive'],16)
    chunk=bytes.fromhex(block['bytes_hex'])
    assert len(chunk)==end-start
    raw[start:end]=chunk
    available.update(dict(enumerate(chunk,start)))
assert all(a in available for a in range(0x4000,0x10000))
memory=FixtureMemory(ROM(memory=available))
cpu=HC11CPU(memory)
OBS=(0x0083,0x0085,0x00d9,0x0135,0x0187,0x0103)
BASE={0x0083:0,0x0085:0x20,0x0099:0,0x0098:0,
      0x00d9:2,0x00d7:128,0x00a2:4,0x0197:1,
      0x0103:0,0x0135:5,0x0134:0,0x0118:0,
      0x0125:50,0x0187:12,0x5d30:5,0x5d31:10,
      0x5d32:3,0x5d33:8,0x5d39:128}
visited=set()
def case(candidate,changes=None):return candidate, BASE|(changes or {})
def stock(item):
    candidate,changes=item
    memory.mem[:]=raw;memory.mem[:0x4000]=bytes(0x4000)
    for address,value in changes.items():memory.mem[address]=value
    memory.writes.clear()
    cpu.s.sp=0x3ff;cpu.s.ccr=0xc0
    cpu.s.a,cpu.s.b,cpu.s.x,cpu.s.y=0x12,candidate,0x5678,0x9abc
    cpu._push16(0x7000);cpu.s.pc=0xd5b7
    for _ in range(1400):
        if cpu.s.pc==0x7000:
            return {'status':0,'state':[memory.mem[a] for a in OBS]}
        visited.add(cpu.s.pc)
        cpu.step()
    raise AssertionError(f'D5B7 source did not return: {cpu.s.pc:04X}')
def compare(items,label):
    total=0
    it=iter(items)
    while block:=list(islice(it,128)):
        rows=[' '.join(map(str,[candidate,len(changes),
            *(v for pair in changes.items() for v in pair)]))
            for candidate,changes in block]
        result=subprocess.run([sys.argv[1],romfile],input='\n'.join(rows)+'\n',
            capture_output=True,text=True,check=True)
        outs=result.stdout.splitlines()
        assert len(outs)==len(block),(label,len(outs),len(block),result.stderr)
        for item,line in zip(block,outs):
            actual=json.loads(line);expected=stock(item)
            if actual!=expected:
                diff=list(zip([f'{a:04X}' for a in OBS],actual['state'],expected['state']))
                raise AssertionError((label,total,item,actual['status'],expected['status'],
                    [(a,c,v) for a,c,v in diff if c!=v]))
            total+=1
    print(f'{total:,} BMHM $D5B7..$D69E gear arbitration comparisons passed: {label}',flush=True)
    return total

with tempfile.TemporaryDirectory(prefix='pcm-gear-join-') as d:
    romfile=str(Path(d)/'stock-evidence.bin')
    Path(romfile).write_bytes(raw)
    directed=[]
    for current,candidate,flags,limit_flags,range_code in product(
        [0,1,2,3,255],[0,1,2,3,4,255],
        [0,1,2,3,8,0xff],[0,8,0x80],[0,4]):
        changes={0x00d9:current,0x0099:flags,0x0098:limit_flags,
                 0x00a2:range_code,0x0103:0}
        directed.append(case(candidate,changes))
    n=compare(directed,'candidate vs current, flags and range-cap gates')
    rng=random.Random(0x31d5b7)
    randomized=[]
    fields=[0x0083,0x0085,0x0099,0x0098,0x00d9,0x00d7,
        0x00a2,0x0197,0x0103,0x0135,0x0134,0x0118,0x0125,0x0187,
        0x5d30,0x5d31,0x5d32,0x5d33,0x5d39]
    for index in range(8192):
        changes={a:rng.randrange(256) for a in fields}
        if index%7==0:changes[0x0103]=index%6
        if index%3==0:changes[0x00a2]=index%8
        randomized.append(case(index%256,changes))
    n+=compare(randomized,'random gear candidates, countdown histories and source limits')
    required={0xd5b7,0xd5f0,0xd601,0xd623,0xd65c,0xd670,0xd673,0xd676,0xd68e,0xd69c}
    assert required<=visited,','.join(f'{a:04X}' for a in sorted(required-visited))
    print(f'{n:,} ROM-equivalent finalizer comparisons at $D5B7.')
