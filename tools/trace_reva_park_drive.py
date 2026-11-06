"""Exact-image Park/Drive tracing. Only fixture RAM changes; BIN stays unchanged."""
from pathlib import Path
import csv
import hashlib
import json
import sys
import argparse
REPO=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('bin_path',type=Path,help='Exact Rev A full 64K BIN')
parser.add_argument('--output',type=Path,default=REPO/'maps/maintenance/reva_park_drive_cases.json')
args=parser.parse_args()
sys.path.insert(0,str(REPO/'tools'))
sys.path.insert(0,str(REPO/'hac31_romsim'))
from factory_rom_decode import decode
from romsim.hc11_core import HC11Memory,HC11CPU
BIN=args.bin_path
IMAGE=BIN.read_bytes()
SHA='d771e824686d086986ee0bdef37697bfc63274071a13b79fc4ba59746644923e'
assert hashlib.sha256(IMAGE).hexdigest()==SHA
args.output.parent.mkdir(parents=True,exist_ok=True)

class Memory(HC11Memory):
    def __init__(self,seed):
        super().__init__();self.mem[:]=bytes(65536);self.mem[0x4000:]=IMAGE[0x4000:]
        self.pc=0;self.reads=[];self.writes=[]
        for a,v in seed.items():self.mem[a]=v
    def _bus_log(self,*a,**k):pass
    def read8(self,a):
        a&=65535
        if a>=0x4000:self.reads.append((self.pc,a))
        return self.mem[a]
    def write8(self,a,v):
        a&=65535;v&=255
        assert a<0x4000,(hex(self.pc),hex(a))
        self.writes.append((self.pc,a,v));self.mem[a]=v
    def tick(self,n):self.cycle_counter+=n

def word(a,v):return {a:v>>8,a+1:v&255}
def u16(m,a):return int.from_bytes(m.mem[a:a+2],'big')
def run(entry,seed,stop=0x7000,a=0):
    m=Memory(seed);c=HC11CPU(m);c.s.sp=0x3ff;c.s.ccr=0xd0;c.s.pc=entry;c.s.a=a
    if stop==0x7000:c._push16(stop)
    pcs=[]
    for step in range(10000):
        if c.s.pc==stop:
            assert c.s.sp==0x3ff,(hex(entry),hex(c.s.sp));return m,c,pcs
        m.pc=c.s.pc;pcs.append(c.s.pc);c.step()
        assert not(c.halted or c.waiting),(hex(entry),hex(c.s.pc))
    raise AssertionError(('budget',hex(entry),hex(c.s.pc)))

cases=[]
# All ordinary input combinations still enter the same forced Drive branch.
for old in [0,2]:
    for pn in [0,0x20]:
        for status in [0,0x50]:
            m,c,pcs=run(0x9537,{0x36:old,0x41:pn,0xa2:status,0x6:169},stop=0x969e)
            assert m.mem[0x36]&2
            cases.append(dict(group='selector',old_context=old,park_input=bool(pn),range_status=status,
                              final_context=m.mem[0x36],gear_adder=m.mem[0x879],
                              gear_hold=m.mem[0x87a],qualification_delay=m.mem[0x864],
                              selector_path=[f'${p:04X}' for p in pcs if 0x9537<=p<=0x9556]))

# ROM constant still selects the old Drive startup base before the normal
# background target uses FF60. The coordinate is explicit, not an assumed C scale.
for coordinate in [64,87,128,160,169,200]:
    m,c,pcs=run(0x9441,{},stop=0x9473,a=coordinate)
    cases.append(dict(group='startup_target',coolant_coordinate=coordinate,target=m.mem[0x857],
                      target_rpm=m.mem[0x857]*12.5,selected_curve='$4F50',
                      selector_path=[f'${p:04X}' for p in pcs if 0x9442<=p<=0x944f]))
    assert 0x944c in pcs and 0x944f in pcs

# Isolated consumer fixtures deliberately inject the dormant Park context.
# They compare the surviving paths; they do not claim normal Park admission.
for blm in [False,True]:
    for drive in [False,True]:
        seed={0x36:2 if drive else 0,0x283:160,0xa7:140,0x6:200,
              0x247:16 if blm else 0,0x248:110,0x85b:5,0x85f:0}
        m,c,pcs=run(0x989c,seed)
        cases.append(dict(group='normal_target',forced_consumer_context='Drive' if drive else 'Park',
                          blm_adder_admitted=blm,target=m.mem[0x857],target_rpm=m.mem[0x857]*12.5,
                          stall_threshold=m.mem[0x868]))
for qualified in [False,True]:
    for high in [False,True]:
        for drive in [False,True]:
            seed={0x36:(2 if drive else 0)|(0x80 if high else 0)|(8 if qualified else 0),0x858:8}
            m,c,pcs=run(0x9c20,seed)
            cases.append(dict(group='proportional',forced_consumer_context='Drive' if drive else 'Park',
                              qualified=qualified,overspeed=high,rpm_error_coordinate=8,correction=m.mem[0x86d]))
for high in [False,True]:
    for drive in [False,True]:
        seed={0x36:(2 if drive else 0)|(0x80 if high else 0),0x858:8,0x50:0x80,0x63:68,
              0x29f:28,0x2a9:38,**word(0x29d,28<<8),**word(0x2a7,38<<8)}
        m,c,pcs=run(0x99c5,seed)
        cases.append(dict(group='integral',forced_consumer_context='Drive' if drive else 'Park',
                          overspeed=high,rpm_error_coordinate=8,selected_word=u16(m,0x862),
                          park_word=u16(m,0x29d),drive_word=u16(m,0x2a7)))
for rise in [False,True]:
    for drive in [False,True]:
        seed={0x36:2 if drive else 0,0x1d9:20 if rise else 0,0x37:1,0x39:0x80,
              0x63:68,0x283:160,0x1c0:100,**word(0x882,0 if rise else 64<<8)}
        m,c,pcs=run(0x9cfd,seed)
        cases.append(dict(group='follower',forced_consumer_context='Drive' if drive else 'Park',
                          throttle_opening=rise,filtered_word=u16(m,0x882),
                          hold=m.mem[0x884],air_term=u16(m,0x880)))

for park_bound in [0,0x0100]:
    seed={0x36:0x0e,0x6:IMAGE[0x4fbf],0x875:1,0x2a9:0,
          **word(0x2a7,38<<8),**word(0x2a5,park_bound),**word(0x2af,0)}
    m,c,pcs=run(0x9fde,seed)
    cases.append(dict(group='park_bound_dependency',drive_selected=True,park_bound=park_bound,
                      drive_bound=0,drive_snapshot=m.mem[0x2a9],drive_warm_flag=bool(m.mem[9]&0x10),
                      cold_delay=m.mem[0x875]))

assert hashlib.sha256(BIN.read_bytes()).hexdigest()==SHA
result=dict(image=BIN.name,sha256=SHA,cases=cases,case_count=len(cases),
            limits='Bounded HC11 memory fixtures, no interrupts or physical I/O. Park context is injected only at consumer entry; ordinary selection is forced Drive. No BIN modifications.')
args.output.write_text(json.dumps(result,indent=2)+'\n')
for case in cases:print(json.dumps(case))
print('Cases:',len(cases),'unchanged BIN:',SHA)
