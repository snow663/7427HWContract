"""Initial ADC sampling, partial factory admission and timer prefix versus BMHM.

The factory timer slice stops before FA5B's target SP assignment. Ready-state,
input muxing and selected callback mutations are explicit peripheral fixtures.
"""
from pathlib import Path
_parent=Path(__file__).with_name('compare_fuel_output_rom.py')
exec(compile(_parent.read_text().split('\ncounts={}',1)[0],str(_parent),'exec'),globals())

RAM.update([0,1,2]);OUTPUTS=sorted(set(OUTPUTS)|RAM)
BASE.update({0:0xa0,1:0xff,2:255,0x909:1,0x82f:40,0xa6:252,0x82d:252,0xa5:5,
             0x3031:252,0x3032:64,0x3033:5,0x3034:252})
coverage=set()
def execute(item):
    mode,edits=item
    memory.mem[:0x1800]=bytes(0x1800);memory.mem[0x3000:0x4000]=bytes(0x1000)
    for a,v in edits.items():memory.mem[a]=v
    memory.events.clear();memory.writes.clear();memory.attempts=memory.polls=memory.control=memory.cycle_counter=0
    memory.fail_at=memory.mem[0x907];cpu.s.sp=0x3ff;cpu.s.ccr=0xd0 if memory.mem[0x909] else 0xc0
    cpu.s.a,cpu.s.b,cpu.s.x,cpu.s.y=0x12,0x34,0x5678,0x9abc
    status=0
    def invoke(start,stops):
        cpu.s.pc=start
        for _ in range(4000):
            pc=cpu.s.pc
            if pc in stops:return pc
            coverage.add(pc);opcode=memory.mem[pc]
            if opcode in (0x0e,0x0f):memory.record('M',0,0,int(opcode==0x0f))
            cpu.step()
            action=memory.mem[0x908]
            if opcode==0x0e and action==3:
                memory.mem[0x55]=99;memory.mem[0xa7]=255;memory.mem[0x3034]=7
            if opcode==0x0f and action==4:
                memory.mem[0x82e]=33;memory.mem[0x50]|=1
        raise AssertionError(f'Startup budget at {cpu.s.pc:04X}')
    try:
        if mode in (0,1,3):invoke(0x7193 if mode==0 else 0x718a,{0x71c3,0x7459})
        if mode==2 or (mode==3 and memory.mem[0x44]&1):
            assert memory.mem[0x44]&1
            assert invoke(0x793d,{0xfa5b,0x7958})==0xfa5b
            status=4
    except Failure:status=2
    unknown=[(a,v) for a,v in memory.writes if a not in OUTPUTS and not 0x3c0<=a<0x400]
    assert not unknown,[(hex(a),v) for a,v in unknown]
    return {'status':status,'masked':int(bool(cpu.s.ccr&0x10)),
            'state':[memory.mem[a] for a in OUTPUTS],'events':list(memory.events)}

counts={}
counts['gates']=compare((case(0,{a:value,0x44:flags,0x50:old})
    for a,value,flags,old in product([0x82f,0xa6,0x82d,0xa5],range(256),[0,0xfe,0xff],[0,0xff])),
    'every admission byte with prior factory/diagnostic latch states')
counts['startup']=compare((case(mode,{0x90a:1,0x90b:coolant,0x90c:0x5a,0x90d:0xa5,
    0x90e:diagnostic,0x90f:aux,0x3031:throttle,0x901:ready,0x902:ready,0x50:gate,0x909:masked})
    for mode,diagnostic,throttle,coolant,aux,ready,gate,masked in product([1,3],[39,40,99,100],
    [251,252,255],[251,252,255],[0,5,6],[0,11,12],[0,1],[0,1])),
    'initial mux/ADC/timeout thresholds and admitted first-timer joins')
counts['timer']=compare((case(2,{0x44:0xff,2:phase,0x909:masked}|word(0x301a,old))
    for phase,masked,old in product(range(256),[0,1],[0,1,65535])),
    'factory raw phase wrap and old-compare recurrence')
counts['callbacks']=compare((case(1,{0x908:action,0x901:ready,0x902:ready,0x909:masked})
    for action,ready,masked in product([1,2,3,4,6],[0,11,12],[0,1])),
    'sample/mask/PORTD mutation and fresh input ownership')
failures=[]
for item in [case(0),case(1),case(1,{0x902:12}),case(2,{0x44:1}),case(3)]:
    for failure in range(1,len(execute(item)['events'])+2):failures.append((item[0],item[1]|{0x907:failure}))
counts['failures']=compare(failures,'every selected acquisition/mask/output/timer failure prefix')
history=[];retained={}
for i in range(256):
    item=case(0,retained|{0x82f:[39,40,99,100][i%4],0xa6:251 if i%5==0 else 252,
                        0x82d:255,0xa5:5 if i%7 else 6})
    history.append(item);retained.update(dict(zip(OUTPUTS,execute(item)['state'])))
counts['history']=compare(history,'retained partial-latch/failed-admission histories')
required=set()
for start,end in [(0x718a,0x71c3),(0x793d,0x7958)]:
    pc=start
    while pc<end:required.add(pc);pc=decode(rom.read,pc).next_pc
assert required<=coverage,sorted(required-coverage)
print(f'{sum(counts.values()):,} startup sampling/factory comparisons; all {len(required)} new scoped instruction starts match.',flush=True)
