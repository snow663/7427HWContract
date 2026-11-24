"""Differential of stock BMHM D4EB diagnostics with actual HC11 execution.

Four entry contexts: E684, E6AC, E69C complete RTS and the contiguous
D4EB..D4F7 prefix. The 9-entry E6BC mask loops are executed, not
replaced by HAC label text. The later D4F7..D69E gear decision is OUT
OF SCOPE and must not be silently treated as implemented.
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
raw=bytearray(65536)
available={}
for block in record['byte_ranges']:
    start,end=int(block['start'],16),int(block['end_exclusive'],16)
    values=bytes.fromhex(block['bytes_hex'])
    assert len(values)==end-start
    raw[start:end]=values
    available.update(dict(enumerate(values,start)))
assert all(a in available for a in range(0x4000,0x10000))
memory=FixtureMemory(ROM(memory=available))
cpu=HC11CPU(memory)
ENTRIES=(0xe684,0xe6ac,0xe69c,0xd4eb)
OBSERVABLE=(0x0084,0x0098,0x0099)
visited=set()
BASE={0x001d:0,0x0087:0,0x0084:0xff,
      0x0098:0x53,0x0099:0xa7}
for i in range(1,10):
    BASE[0x5b33+i]=0
    BASE[0x5b2a+i]=0xff
    BASE[0x0015+i]=0
def case(overrides=None):
    return BASE|(overrides or {})
def stock(item):
    mode,edit=item
    memory.mem[:]=raw
    memory.mem[:0x4000]=bytes(0x4000)
    for a,v in edit.items():memory.mem[a]=v
    memory.writes.clear()
    cpu.s.sp=0x3ff
    cpu.s.ccr=0xc0
    cpu.s.a,cpu.s.b,cpu.s.x,cpu.s.y=0x12,0x34,0x5678,0x9abc
    cpu._push16(0x7000)
    cpu.s.pc=ENTRIES[mode]
    expected_stop=0xd4f7 if mode==3 else 0x7000
    for n in range(2000):
        pc=cpu.s.pc
        if pc==expected_stop:
            return {'status':0,'state':[memory.mem[a] for a in OBSERVABLE]}
        visited.add(pc)
        cpu.step()
    raise AssertionError(f'Unreturned source entry {ENTRIES[mode]:04X}: pc={cpu.s.pc:04X}')
def compare(items,label):
    total=0
    it=iter(items)
    while block:=list(islice(it,128)):
        payload=[' '.join(map(str,[mode,len(edit),
                    *(value for pair in edit.items() for value in pair)]))
                 for mode,edit in block]
        result=subprocess.run([sys.argv[1],romfile],
            input='\n'.join(payload)+'\n',capture_output=True,text=True,check=True)
        actual=result.stdout.splitlines()
        assert len(actual)==len(block),(label,len(actual),len(block),result.stderr)
        for item,line in zip(block,actual):
            got=json.loads(line)
            expected=stock(item)
            if got!=expected:
                raise AssertionError((label,total,item,got,expected))
            total+=1
    print(f'{total:,} BMHM E6BC-D4EB prefix C/ROM states: {label}',flush=True)
    return total

with tempfile.TemporaryDirectory(prefix='pcm-d4eb-diag-') as d:
    romfile=str(Path(d)/'verified-rom-view.bin')
    Path(romfile).write_bytes(raw)
    count=compare([(mode,case()) for mode in range(4)],'baseline')
    directed=[]
    for mode,precedence,override,bit,byte,shift in product(
        range(4),[0,0x80],[0,2],[0,1,2,4,8,16,32,64,128],
        [1,5,9],[0,1]):
        alt={0x001d:precedence,0x0087:override,
             0x0098:0xff if shift else 0x11,
             0x0099:0xff if shift else 0x22,
             0x0015+byte:bit,
             0x5b2a+byte:bit if shift else 255,
             0x5b33+byte:bit if shift else 0}
        for table in (0xe73a,0xe743,0xe74c):
            alt[table+byte]=bit
        directed.append((mode,case(alt)))
    count+=compare(directed,'every 1/5/9 mask position, source order, gates and bit selection')
    rng=random.Random(0x31d4ebe6)
    variants=[]
    candidate=list(range(0x16,0x1f))+list(range(0x5b2b,0x5b3d))+list(range(0xe73b,0xe756))
    for i in range(8192):
        edits={a:rng.randrange(256) for a in candidate}
        edits.update({0x001d:rng.randrange(256),0x0087:rng.randrange(256),
                      0x0084:rng.randrange(256),0x0098:rng.randrange(256),
                      0x0099:rng.randrange(256)})
        variants.append((i%4,case(edits)))
    count+=compare(variants,'random live fault/mask/ROM table states and old flag retention')
    required={0xe684,0xe69c,0xe6ac,0xe6bc,0xd4eb,0xd4f4,0xd4f5}
    assert required<=visited,sorted(required-visited)
    print(f'{count:,} stock-verified D4EB prefix cases; {len(visited)} reachable source PCs.')
