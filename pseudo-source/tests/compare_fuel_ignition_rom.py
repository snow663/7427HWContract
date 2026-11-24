"""BMHM $7D4B..$7DB5 C versus executed HC11, including stop/trap boundaries.

Use ROM bytes from the committed SHA-identified upstream evidence, not
the provisional HAC comments or guessed calibration. No live target ABI.
"""
from hashlib import sha256
from itertools import islice,product
import json
from pathlib import Path
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

data=json.loads((ROOT/'maps/structure/bmhm_upstream_rom_evidence.json').read_text())
assert data['rom_size_bytes']==65536 and data['rom_sha256']==EXPECTED_SHA256
assert data['listing_sha256_lf']==text_sha256(SOURCE)
raw=bytearray([255]*65536)
available={}
for block in data['byte_ranges']:
    start,end=int(block['start'],16),int(block['end_exclusive'],16)
    chunk=bytes.fromhex(block['bytes_hex'])
    assert len(chunk)==end-start
    for address,value in enumerate(chunk,start):
        if address in available:assert available[address]==value,(hex(address),value)
        available[address]=value
        raw[address]=value
assert all(address in available for address in range(0x7d4b,0x7db6))
assert all(address in available for address in (0x4009,0x400a))
binary=sys.argv[1]
memory=FixtureMemory(ROM(memory=available))
cpu=HC11CPU(memory)
ADDRS=[0x0004,0x0019,0x003e,0x0044,0x0046,0x004f,0x0051,0x0062,0x0086,
       0x00fd,0x00fe,0x0223,0x024c,0x024d,0x0268,0x027d,0x027e,0x027f,
       0x02cd,0x02ce,0x3039,0x303a]
def word(addr,value):return {addr:(value>>8)&255,addr+1:value&255}
BASE={0x0044:0x10,0x0051:0x08,0x0046:0xff,0x004f:0xff,0x0004:0xff,
      0x0019:0xff,0x0086:0xff,0x003e:0xff,
      0x0223:0x5a,0x027d:0x9a,0x02cd:0x61,0x02ce:0x51,
      0x00fd:0x12,0x00fe:0x34,0x024c:0x56,0x024d:0x78,
      0x0268:0xab,0x0062:0xcd,0x3039:0x88,0x303a:0x99}
BASE.update(word(0x027e,7))
def case(overrides=None):return BASE|(overrides or {})
def execute(edits):
    memory.mem[:]=raw
    for addr,value in edits.items():memory.mem[addr]=value
    memory.writes.clear()
    cpu.s.sp=0x3ff;cpu.s.ccr=0xc0
    cpu.s.a,cpu.s.b,cpu.s.x,cpu.s.y=0x12,0x34,0x5678,0x9abc
    cpu.s.pc=0x7d4b
    for _ in range(180):
        pc=cpu.s.pc
        # Stock $7D8D is $CF (deliberate illegal/terminal byte). The
        # project's HC11 core cannot execute it; compare the completed
        # memory, board and CCR prefix at the instruction boundary.
        if pc in (0x7db6,0x7d8d):
            return {'status':10 if pc==0x7d8d else 0,
                    'masked':int(bool(cpu.s.ccr&0x10)),
                    'state':[memory.mem[a] for a in ADDRS]}
        cpu.step()
    raise AssertionError(f'Prefix exceeded instruction budget: {cpu.s.pc:04X}')
def compare(cases,label):
    cases=iter(cases);count=0
    while chunk:=list(islice(cases,128)):
        payload=[' '.join(map(str,[len(item),*(v for pair in item.items() for v in pair)]))
                 for item in chunk]
        result=subprocess.run([binary,romfile],input='\n'.join(payload)+'\n',
                              text=True,capture_output=True,check=True)
        out=result.stdout.splitlines()
        assert len(out)==len(chunk),(label,len(out),len(chunk),result.stderr)
        for i,(item,line) in enumerate(zip(chunk,out)):
            actual=json.loads(line);expected=execute(item)
            if actual!=expected:
                diff=[(hex(a),got,want) for a,got,want in zip(
                    ADDRS,actual['state'],expected['state']) if got!=want]
                raise AssertionError((label,count+i,item,diff,
                                     actual['status'],expected['status'],
                                     actual['masked'],expected['masked']))
        count+=len(chunk)
    print(f'{count:,} {label} BMHM ignition/initialization cases match.',flush=True)
    return count
with tempfile.TemporaryDirectory(prefix='pcm-ignition-rom-') as folder:
    romfile=str(Path(folder)/'bmhm-evidence-view.bin')
    Path(romfile).write_bytes(raw)
    counts={}
    initial=[case(word(0x027e,elapsed)|{0x0044:ignition,0x0051:flags})
            for elapsed,ignition,flags in product(
                [0,1,7,8,9,15,16,17,255,256,65534,65535],
                [0,8,16,24,255],[0,8,255])]
    counts['initial']=compare(initial,'ignition bit, elapsed threshold and latched-off')
    directed=[case(word(0x027e,elapsed)|word(0x4009,limit)|{0x0044:16,0x0051:flags})
            for elapsed,limit,flags in product(
                [0,7,8,9,15,16,255,65534,65535],
                [0,1,8,9,16,255,65535],[0,8,255])]
    counts['thresholds']=compare(directed,'all trap and watchdog branch boundaries')
    rng=random.Random(0x317d4b)
    random_cases=[]
    mutable=[0x0004,0x0019,0x003e,0x0044,0x0046,0x004f,0x0051,
             0x0062,0x0086,0x0223,0x024c,0x024d,0x0268,0x027d,
             0x027e,0x027f,0x02cd,0x02ce,0x3039,0x303a]
    for i in range(4096):
        edits={a:rng.randrange(256) for a in mutable}
        edits[0x0044]=(edits[0x0044]&~0x10)|(0x10 if i&1 else 0)
        if i%4==0:edits.update(word(0x4009,rng.choice([0,1,7,8,9,16,65535])))
        if i%5==0:edits.update(word(0x027e,rng.choice([0,1,7,8,9,16,65535])))
        random_cases.append(case(edits))
    counts['random']=compare(random_cases,'random RAM, calibrated trap threshold and retained history')
    print(f'{sum(counts.values()):,} complete $7D4B..$7DB5 C/ROM cases match.',flush=True)
