"""ROM HC11 $D8CE carry-qualified multi-pointer table differential.

D8CE is tested independently of its D4EB caller using the caller's X
table and B entry value. Carry is reflected as the `valid` flag.
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
raw=bytearray(65536);available={}
for block in record['byte_ranges']:
    a,b=int(block['start'],16),int(block['end_exclusive'],16)
    chunk=bytes.fromhex(block['bytes_hex'])
    raw[a:b]=chunk
    available.update(dict(enumerate(chunk,a)))
assert all(a in available for a in range(0x4000,0x10000))
memory=FixtureMemory(ROM(memory=available))
cpu=HC11CPU(memory)
visited=set()
def case(table,slot,edits=None):
    return table,slot,{0x98:0,0xa2:2}|(edits or {})
def stock(item):
    table,slot,edits=item
    memory.mem[:]=raw;memory.mem[:0x4000]=bytes(0x4000)
    for addr,value in edits.items():memory.mem[addr]=value
    cpu.s.sp=0x3ff;cpu.s.ccr=0xc0
    cpu.s.a,cpu.s.b,cpu.s.x,cpu.s.y=0x12,slot,table,0x9abc
    cpu._push16(0x7000);cpu.s.pc=0xd8ce
    for _ in range(120):
        if cpu.s.pc==0x7000:
            return {'status':0,'value':cpu.s.a,'valid':int(not(cpu.s.ccr&1))}
        visited.add(cpu.s.pc);cpu.step()
    raise AssertionError(f'D8CE did not return: {cpu.s.pc:04X}')
def compare(items,label):
    total=0;it=iter(items)
    while chunk:=list(islice(it,128)):
        inputs=[' '.join(map(str,[table,slot,len(edits),
                *(v for pair in edits.items() for v in pair)]))
                for table,slot,edits in chunk]
        p=subprocess.run([sys.argv[1],romfile],input='\n'.join(inputs)+'\n',
            text=True,capture_output=True,check=True)
        lines=p.stdout.splitlines()
        assert len(lines)==len(chunk),(label,len(lines),len(chunk),p.stderr)
        for item,line in zip(chunk,lines):
            actual=json.loads(line);expected=stock(item)
            if actual!=expected:
                raise AssertionError((label,total,item,actual,expected))
            total+=1
    print(f'{total:,} D8CE C/HC11 table-selector cases: {label}',flush=True)
    return total

with tempfile.TemporaryDirectory(prefix='pcm-d8ce-rom-') as d:
    romfile=str(Path(d)/'BMHM-hash-verified.bin')
    Path(romfile).write_bytes(raw)
    directed=[case(table,slot,{0x98:flags,0xa2:gear}) for table,slot,flags,gear in product(
        [0xd763,0xd775],[0,1,2,3,4,127,128,255],[0,4],[0,1,2,3,4,5,6,7,255])]
    n=compare(directed,'source 0/2/7 range gates, flag override, pointer and slot wrap')
    rng=random.Random(0x31d8ce)
    randomized=[]
    for index in range(8192):
        table=[0xd763,0xd775][index&1]
        slot=rng.randrange(256)
        gear=rng.randrange(256)
        off=(2*(slot+3*((gear&7)>>1)))&255
        addr=(table+off)&65535
        changes={0x98:rng.randrange(256),0xa2:gear}
        if index%3==0:
            # Force known successful pointer and overridable output data.
            changes[0x98]=0
            changes[addr]=0x12;changes[(addr+1)&65535]=0x34
            changes[0x1234]=rng.randrange(256)
        if index%5==0:
            changes[addr]=0;changes[(addr+1)&65535]=0
        randomized.append(case(table,slot,changes))
    n+=compare(randomized,'random source pointer, null, override and observation histories')
    assert {0xd8ce,0xd8d3,0xd8d9,0xd8e3,0xd8e7,0xd8ec,0xd8ed,0xd8ee}<=visited
    print(f'{n:,} selected threshold cases matched the stock ROM; no gear decision inferred.')
