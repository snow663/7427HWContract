"""Stock HC11 $E562..$E57B ROM differential for proposed gear limiter.

The lookup is deliberately allowed to index beyond the nominal 4-byte
tables: this is what the original indexed X arithmetic actually does.
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

e=json.loads((ROOT/'maps/structure/bmhm_ownership_rom_evidence.json').read_text())
assert e['rom_sha256']==EXPECTED_SHA256 and e['listing_sha256_lf']==text_sha256(SOURCE)
raw=bytearray(65536);available={}
for group in e['byte_ranges']:
    a,b=int(group['start'],16),int(group['end_exclusive'],16)
    chunk=bytes.fromhex(group['bytes_hex'])
    assert len(chunk)==b-a
    raw[a:b]=chunk
    available.update(dict(enumerate(chunk,a)))
assert all(a in available for a in range(0x4000,0x10000))
memory=FixtureMemory(ROM(memory=available))
cpu=HC11CPU(memory)
visited=set()
def pointer(range_byte,proposed):
    v=range_byte&7
    if v==0:v=6
    return 0xe57c+4*(v>>1)+proposed
def replay(item):
    proposed,range_byte,mod=item
    memory.mem[:]=raw;memory.mem[:0x4000]=bytes(0x4000)
    memory.mem[0xa2]=range_byte
    if mod<256:memory.mem[pointer(range_byte,proposed)]=mod
    cpu.s.sp=0x3ff;cpu.s.ccr=0xc0
    cpu.s.a,cpu.s.b,cpu.s.x,cpu.s.y=proposed,0x92,0x5678,0x9abc
    cpu._push16(0x7000);cpu.s.pc=0xe562
    for _ in range(100):
        if cpu.s.pc==0x7000:
            return {'status':0,'value':cpu.s.a,'reads':2}
        visited.add(cpu.s.pc);cpu.step()
    raise AssertionError(f'$E562 did not terminate: {cpu.s.pc:04X}')
def compare(cases,label):
    total=0;it=iter(cases)
    while chunk:=list(islice(it,128)):
        payload=['%d %d %d'%c for c in chunk]
        p=subprocess.run([sys.argv[1],romfile],text=True,
                         input='\n'.join(payload)+'\n',capture_output=True,check=True)
        lines=p.stdout.splitlines()
        assert len(lines)==len(chunk),(label,len(lines),len(chunk),p.stderr)
        for item,line in zip(chunk,lines):
            actual=json.loads(line);expected=replay(item)
            if actual!=expected:raise AssertionError((label,total,item,actual,expected))
            total+=1
    print(f'{total:,} stock ROM E562 gear limit cases matched: {label}',flush=True)
    return total

with tempfile.TemporaryDirectory(prefix='pcm-gear-limit-') as d:
    romfile=str(Path(d)/'stock-verified.bin')
    Path(romfile).write_bytes(raw)
    count=compare(((p,r,256) for r,p in product(range(256),range(256))),
        'all range bytes and proposed-gear byte values, unmodified source ROM')
    rng=random.Random(0x31e562)
    variants=[(rng.randrange(256),rng.randrange(256),rng.randrange(256))
              for _ in range(8192)]
    count+=compare(variants,'8k changed source-table byte values, cap and compare directions')
    assert {0xe562,0xe56b,0xe573,0xe575,0xe577,0xe57a,0xe57b}<=visited
    print(f'{count:,} source-backed E562 cases; no real transmission outputs claimed.')
