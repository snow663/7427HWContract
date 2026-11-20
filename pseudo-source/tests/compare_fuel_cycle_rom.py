"""Independent full BMHM ROM replay for complete $7D4B..$8547 entry.

This deliberately starts from the stock ROM entry rather than hand-joining
callee fragments. It first checks bounded no-fuel and ignition transitions;
other running/async and physical output histories remain separate evidence.
The 0x4000..FFFF bytes come from SHA-checked committed full-ROM evidence.
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

data=json.loads((ROOT/'maps/structure/bmhm_ownership_rom_evidence.json').read_text())
assert data['rom_sha256']==EXPECTED_SHA256
assert data['listing_sha256_lf']==text_sha256(SOURCE)
assert data['rom_size_bytes']==65536
full=bytearray(65536)
seen=set()
for group in data['byte_ranges']:
    a,b=int(group['start'],16),int(group['end_exclusive'],16)
    v=bytes.fromhex(group['bytes_hex'])
    assert len(v)==b-a
    full[a:b]=v
    seen.update(range(a,b))
assert set(range(0x4000,0x10000))<=seen
ADDR=[0x027e,0x027f,0x0044,0x004f,0x0051,0x0062,0x01c5,
      0x01d9,0x01d2,0x01d3,0x0257,0x0258,0x024c,0x024d,
      0x303a,0x3fce,0x3fcf,0x0299,0x01de,0x01df,0x01dc,0x01dd]
memory=FixtureMemory(ROM(data=bytes(full)))
cpu=HC11CPU(memory)
coverage=set()
BASE={0x44:0x10,0x51:0,0x4f:0x90,0x3e:0xa0,0x4:0,0x86:0,0x2:2,
      0x27e:0,0x27f:7,0x400f:0x80,0x400d:0x40,0x1c6:100,
      0x65:49,0x63:50,0x50:0x80,0x1d5:128,0xa6:70,0x2f6:20,
      0x6:160,0x55:128,0x1cc:120,0x303a:0,0x3fce:0,0x3fcf:0,
      0x3012:0,0x3013:0,0x27b:0,0x1d2:0,0x1d3:0,0x1c5:0}
def case(edits=None):return BASE|(edits or {})
def execute(edits):
    memory.mem[:]=full
    memory.mem[:0x4000]=bytes(0x4000)
    for a,v in edits.items():memory.mem[a]=v
    memory.writes.clear()
    memory.cycle_counter=0
    cpu.s.sp=0x3ff;cpu.s.ccr=0xc0
    cpu.s.a,cpu.s.b,cpu.s.x,cpu.s.y=0x12,0x34,0x5678,0x9abc
    cpu._push16(0x7000);cpu.s.pc=0x7d4b
    for i in range(40000):
        pc=cpu.s.pc
        if pc in (0x7000,0x7d8d):
            return {'status':10 if pc==0x7d8d else 0,
                'state':[memory.mem[a] for a in ADDR]}
        if pc==0x1809:
            raise AssertionError('External governor $1809 reached; disable optional flag')
        coverage.add(pc)
        cpu.step()
    raise AssertionError(f'Full fuel cycle blocked at {cpu.s.pc:04X}, steps=40000')
def compare(cases,description):
    count=0
    cases=iter(cases)
    while batch:=list(islice(cases,64)):
        rows=[' '.join(map(str,[len(edits),*(v for pair in edits.items() for v in pair)]))
              for edits in batch]
        x=subprocess.run([sys.argv[1],file],input='\n'.join(rows)+'\n',
                         text=True,capture_output=True,check=True)
        results=x.stdout.splitlines()
        assert len(results)==len(batch),(description,len(results),len(batch),x.stderr)
        for n,(edits,line) in enumerate(zip(batch,results)):
            actual=json.loads(line);expected=execute(edits)
            if actual!=expected:
                diffs=[(f'{a:04X}',a0,e0) for a,a0,e0 in zip(
                    ADDR,actual['state'],expected['state']) if a0!=e0]
                raise AssertionError((description,count+n,
                    {f'{a:04X}':v for a,v in edits.items()},actual['status'],
                    expected['status'],diffs[:25]))
        count+=len(batch)
    print(f'{count:,} full-entry BMHM $7D4B cases matched: {description}',flush=True)
    return count

with tempfile.TemporaryDirectory(prefix='pcm-fuel-full-entry-') as tmp:
    file=str(Path(tmp)/'hash-checked-source.bin')
    Path(file).write_bytes(full)
    direct=[case({2:phase,0x4f:0x90,0x400f:option})
            for phase,option in product([2,3,6,7],[0,0x80])]
    n=compare(direct,'no-fuel authorization, all alternate battery/governor/AFR phase gates')
    # Keep calibration $400D.6 asserted so authorized delivery is blocked
    # until there is a valid capture. Limit advanced states to source-backed
    # controls rather than random ISR/watchdog hardware.
    rng=random.Random(0x317d4b85)
    directed=[case({2:phase,0x27e:elapsed>>8,0x27f:elapsed&255,
                    0x44:flags,0x4f:run,0xa6:tps,0x1d5:oxygen,
                    0x400f:option,0x4009:0xff,0x400a:0xff})
              for phase,elapsed,flags,run,tps,oxygen,option in product(
                  [2,3,6,7],[0,7,8],[0,0x10],[0,0x80,0x90],
                  [0,64,128],[0,128,255],[0,0x80])]
    n+=compare(directed[:2048],'selected ignition, no-fuel, TPS/O2 and phase histories')
    print(f'{n:,} full-entry C/ROM cases passed; {len(coverage)} source PCs reached. '
          'Physical E-cycle timing, $1809 module, and nonzero injector '
          'driver response are not proven by this test.')
