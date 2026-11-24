"""Complete C668..C6BA speed-source versus stock BMHM HC11 instructions.

The stock ROM is taken from SHA-identified full 0x4000..FFFF evidence;
synthetic RAM and cases are test-only. Stop at original RTS to 0x7000.
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
image=bytearray(65536)
available={}
for block in e['byte_ranges']:
    a,b=int(block['start'],16),int(block['end_exclusive'],16)
    v=bytes.fromhex(block['bytes_hex'])
    assert len(v)==b-a
    image[a:b]=v
    available.update(dict(enumerate(v,a)))
assert all(a in available for a in range(0x4000,65536))
memory=FixtureMemory(ROM(memory=available))
cpu=HC11CPU(memory)
BASE={0x5b30:0,0x5b2d:0,0x1b:0,0x18:0,0x5d02:4,
      0x2f3:128,0x5d07:64,0x5d08:0x10,0x5d09:0,
      0x5d0a:128,0xac:0x12,0xad:0x34,0x907:0}
def case(edit=None):return BASE|(edit or {})
def source(edit):
    memory.mem[:]=image
    memory.mem[:0x4000]=bytes(0x4000)
    for a,v in edit.items():memory.mem[a]=v
    cpu.s.sp=0x3ff;cpu.s.ccr=0xc0
    cpu.s.a,cpu.s.b,cpu.s.x,cpu.s.y=0x12,0x34,0x5678,0x9abc
    cpu._push16(0x7000);cpu.s.pc=0xc668
    for i in range(2000):
        if cpu.s.pc==0x7000:
            return {'status':0,'word':(memory.mem[0xac]<<8)|memory.mem[0xad]}
        cpu.step()
    raise AssertionError(f'Stuck source C668: {cpu.s.pc:04X}')
def compare(items,label):
    total=0
    it=iter(items)
    while chunk:=list(islice(it,128)):
        payload=[' '.join(map(str,[len(c),*(v for pair in c.items() for v in pair)]))
                 for c in chunk]
        x=subprocess.run([sys.argv[1],path],text=True,input='\n'.join(payload)+'\n',
                         capture_output=True,check=True)
        out=x.stdout.splitlines()
        assert len(out)==len(chunk),(len(out),len(chunk),x.stderr)
        for c,line in zip(chunk,out):
            a=json.loads(line);ref=source(c)
            if a['status']!=ref['status'] or a['word']!=ref['word']:
                raise AssertionError((label,total,c,a,ref))
            assert a['writes']==1,(label,total,c,a)
            total+=1
    print(f'{total:,} C668 full-source ROM/C matches: {label}',flush=True)
    return total

with tempfile.TemporaryDirectory(prefix='pcm-speed-') as folder:
    path=str(Path(folder)/'BMHM-recorded.bin')
    Path(path).write_bytes(image)
    first=[]
    for selector,options,flag,source_bit in [
        (1,4,4,4),(2,2,2,4),(3,0x20,0x20,0),(4,0x10,0x10,0),(5,0,0,4)]:
        for gain,baro,high,low in product(
            [0,1,64,127,128,255],[0,1,127,255],
            [0,127,255],[0,128,255]):
            state={0x5b30:options if selector in (1,2) else 0,
                0x5b2d:options if selector in (3,4) else 0,
                0x1b:flag if selector in (1,2) else 0,
                0x18:flag if selector in (3,4) else 0,
                0x5d02:source_bit,0x5d0a:gain,0x2f3:baro,
                0xac:high,0xad:low,
                0x5b6f:high,0x5b70:low,
                0x5b73:high^0xff,0x5b74:low^0xff}
            first.append(case(state))
    n=compare(first,'primary/secondary source override and F436 BARO fallback')
    rng=random.Random(0x31c668)
    randoms=[]
    for _ in range(3000):
        edits={a:rng.randrange(256) for a in [
            0x5b30,0x5b2d,0x1b,0x18,0x5d02,0x2f3,
            0x5d07,0x5d08,0x5d09,0x5d0a,0xac,0xad,
            0x5b6f,0x5b70,0x5b73,0x5b74]}
        randoms.append(case(edits))
    n+=compare(randoms,'random live RAM and calibration controls')
    print(f'{n:,} speed source C/ROM cases. Slot01 TCC at $ADAA is a separate dependency.')
