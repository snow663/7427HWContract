"""Independent BMHM HC11/C differential for the entire governor target.

Runs on the repository's recorded SHA256-identified ROM evidence, not HAC
comments. It compares selected native RAM and $306C output bytes after each
callee. Target stacks/interrupt latency and the optional $1809 interface
remain separate, explicit boundaries. Never claim physical governor testing.
"""
from hashlib import sha256
from itertools import islice,product
import json
import os
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

EVIDENCE=ROOT/'maps/structure/bmhm_idle_governor_rom_evidence.json'
data=json.loads(EVIDENCE.read_text())
assert data['rom_sha256']==EXPECTED_SHA256
assert data['rom_size_bytes']==65536
assert data['listing_sha256_lf']==text_sha256(SOURCE)
raw=bytearray([255]*65536)
available={}
for block in data['byte_ranges']:
    start=int(block['start'],16);end=int(block['end_exclusive'],16)
    recorded=bytes.fromhex(block['bytes_hex'])
    assert len(recorded)==end-start
    for address,value in enumerate(recorded,start):
        if address in available:assert available[address]==value,(hex(address),value,available[address])
        available[address]=value
        raw[address]=value
for a in (0x50d8,0x50e8,0x5109,0xf499,0xf4b6,0xf4c1,0xf550,0x8eb4,0x8f5f,0x9097,0x90d3):
    assert a in available,hex(a)
# The recorded evidence proves these scoped bytes and their source identity;
# the filled image is NOT a complete new hashed firmware BIN.
rom=ROM(memory=available)
binary=sys.argv[1]
ADDRS=[0x75,0x4f,0x86,0x006f,0x1d9,0x284,0x285,0x286,0x287,0x288,0x289,
    0x28a,0x28b,0x28d,0x28e,0x28f,0x290,0x291,0x292,0x293,0x294,
    0x295,0x296,0x297,0x298,0x299,0x29a,0x306c,0x306d]
memory=FixtureMemory(rom)
cpu=HC11CPU(memory)
coverage=set()
def word(address,value):return{address:(value>>8)&255,address+1:value&255}
def case(mode,changes=None):return (mode,BASE|(changes or {}))
BASE={0x400f:1,0x4f:0x80,0x86:0,0x6f:0,0x75:0,0x1d9:80,
    0x284:0,0x285:0x80,0x28d:0,0x293:5,0x294:7,
    0x299:64,0x29a:11,0x292:0,0x295:0,0x296:0,0x297:0,0x298:0,
    0x306c:0,0x306d:0,0x51:0,0x3b:0,0x393:0,0x394:0,
    0x901:77} | word(0x286,0x6400) | word(0x288,0x1000) | \
    word(0x28a,0x0120) | word(0x290,0x0180) | word(0x28e,0x1200)

START=[0x8eb4,0x8f5f,0x9010,0x90d3,0x8f5f,0x8fcc,0x9010,0x9097]
STOP =[0x7000,0x7000,0x7000,0x7000,0x8fcc,0x9097,0x9097,0x7000]

def execute(item):
    mode,changes=item
    memory.mem[:]=raw
    for address,value in changes.items():memory.mem[address]=value
    memory.writes.clear()
    memory.cycle_counter=0
    cpu.s.sp=0x3ff;cpu.s.ccr=0xc0
    cpu.s.a=memory.mem[0x901] if mode==7 else 0x12
    cpu.s.b=0x34;cpu.s.x=0x5678;cpu.s.y=0x9abc
    cpu._push16(0x7000);cpu.s.pc=START[mode]
    stop=STOP[mode]
    for _ in range(20000):
        pc=cpu.s.pc
        if pc==stop:
            return {'status':0,'value':cpu.s.a if mode in (5,6) else 0,
                'state':[memory.mem[a] for a in ADDRS]}
        if pc==0x1809:
            raise AssertionError('Unmodeled optional $1809 reached: case must clear $0086.6')
        coverage.add(pc)
        cpu.step()
    raise AssertionError(f'Governor PC budget exceeded: mode={mode}, pc={cpu.s.pc:04X}')

def compare(items,label):
    total=0
    iterator=iter(items)
    while chunk:=list(islice(iterator,128)):
        payload=[]
        for mode,changes in chunk:
            values=[mode,len(changes)]
            for addr,v in changes.items():values.extend((addr,v))
            payload.append(' '.join(map(str,values)))
        p=subprocess.run([binary,romfile],input='\n'.join(payload)+'\n',
            text=True,capture_output=True,check=True)
        outputs=p.stdout.splitlines()
        assert len(outputs)==len(chunk),(label,len(outputs),len(chunk),p.stderr[:2000])
        for item,line in zip(chunk,outputs):
            actual=json.loads(line);expect=execute(item)
            if actual!=expect:
                diff=[(hex(address),got,want) for address,got,want in zip(
                      ADDRS,actual['state'],expect['state']) if got!=want]
                Path('/tmp/governor-rom-failure.json').write_text(json.dumps(
                    {'label':label,'case':item,'actual':actual,'expected':expect,'differences':diff}))
                raise AssertionError((label,item[0],diff[:16],
                    (actual['status'],expect['status']),
                    (actual['value'],expect['value'])))
        total+=len(chunk)
    print(f'{total:,} {label} C/ROM cases matched.',flush=True)
    return total

with tempfile.TemporaryDirectory(prefix='pcm-governor-rom-') as temp:
    romfile=str(Path(temp)/'recorded-bmhm-view.bin')
    Path(romfile).write_bytes(raw)
    counts={}
    counts['defaults']=compare([case(mode) for mode in range(8)],
        'direct stock-calibration entries')
    # Source-gate and governor state boundaries; $1809 disabled in all cases.
    directed=[]
    for mode,flags,error,derivative,rpm,base,desired in product(
        range(8),[0,1,2,4,0x40,0x44,0x80,0x81,0x84,0xc0,0xff],
        [0,1,32,127,255],[0,1,31,32,127,128,255],
        [0,1,31,127,255],[0,0x0080,0x6400,0xff80],[0,17,64,128,255]):
        if len(directed)>7000:break
        changes={0x75:flags,0x293:error,0x294:255-error,0x28d:derivative,
                 0x299:desired,0x1d9:desired,0x28e:rpm}
        changes.update(word(0x286,base))
        directed.append(case(mode,changes))
    counts['directed']=compare(directed,'sign, saturation and stateful governor branches')
    rng=random.Random(0x318f5f)
    random_cases=[]
    for i in range(4096):
        mode=i%8
        edits={a:rng.randrange(256) for a in [
            0x4f,0x6f,0x75,0x1d9,0x284,0x285,0x286,0x287,0x288,0x289,
            0x28a,0x28b,0x28d,0x28e,0x28f,0x290,0x291,0x292,0x293,
            0x294,0x295,0x296,0x297,0x298,0x299,0x29a,0x51,0x3b,0x393,0x394,0x901]}
        edits[0x86]=rng.randrange(256)&~0x40  # explicit $1809 boundary
        edits[0x400f]=rng.randrange(256)
        if i%4==0:
            # Deliberately exercise live calibration mutation while retaining
            # the source's byte/table read ordering.
            edits.update({a:rng.randrange(256) for a in range(0x50d8,0x5112)})
        random_cases.append(case(mode,edits))
    counts['random']=compare(random_cases,'random RAM, service and calibration states')
    # Real instruction-address coverage; only the original $1809 module
    # branch is an intentionally excluded external frontier.
    print(f'{sum(counts.values()):,} source/ROM governor differential cases; '
          f'{len(coverage)} reachable instruction starts encountered.')
