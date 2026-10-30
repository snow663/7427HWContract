"""Compare compiled C fuel arithmetic with actual stock instruction execution."""
from pathlib import Path
import random
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from factory_fuel_replay import FuelReplay
from verify_factory_fuel import defaults

rng=random.Random(0x31C)
cases=[(d,t,v,e,p,a,f) for d,t in [(0,0),(1,1),(1,2),(65535,65535),(65535,1)]
       for v,e,p,a,f in [(206,180,2000,145,7008),(255,255,0,0,0),(0,0,1,1,1),(255,255,1,1,256)]]
cases.extend((rng.randrange(65536),rng.randrange(65536),rng.randrange(256),rng.randrange(256),
              rng.randrange(65536),rng.randrange(256),rng.randrange(65536)) for _ in range(512))
payload=''.join(' '.join(map(str,c))+'\n' for c in cases)
out=subprocess.run([sys.argv[1],'--fuel'],input=payload,text=True,capture_output=True,check=True).stdout.splitlines()
assert len(out)==len(cases)
replay=FuelReplay()
for case,line in zip(cases,out):
    density,temp,volume,ve,period,afr,flow=case
    replay.prepare(defaults())
    for address,value in [(0x257,density),(0x236,temp),(0x1e8,period),(0x4d92,flow)]:replay.word(address,value)
    for address,value in [(0x4d94,volume),(0x231,ve),(0x24a,afr)]:replay.memory.mem[address]=value
    replay.run(0x7fd8,0x8032)
    actual=list(map(int,line.split()))
    expected=[replay.memory.read16(a) for a in [0x238,0x234,0x232,0x24e]]
    assert [actual[i] for i in [0,1,2,4]]==expected,(case,actual,expected)
    # The mixture quotient is an intermediate register result; the four RAM
    # stores above are the independently observed stock outputs.
    assert replay.cpu.s.sp==0x03f4
print(f'{len(cases)} compiled-C cases match the stock base-fuel RAM results.')
