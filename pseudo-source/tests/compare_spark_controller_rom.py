"""Check the EST monitor and complete resident A466..ACA6 controller.

This binary links the production alternate adapter. Only 180F/1812 returns are
fixtures; timeout execution stops before SWI. Word transaction ordering is a
host contract, not proof of physical EST timing or module machine ABIs.
"""
from pathlib import Path

_prior=Path(__file__).with_name('compare_spark_output_rom.py')
exec(compile(_prior.read_text().rsplit('\ncounts={}',1)[0],str(_prior),'exec'),globals())
_OutputMemory=Memory
OUTPUTS=OUTPUTS+[0x205,0x206,0x22C,0x391,0x3FE4,0x3FE5]
assert len(OUTPUTS)==len(set(OUTPUTS))==130
BASE=BASE|{0x205:0x12,0x206:0x34,0x22C:2,0x391:0xA5,
           0x3FCA:0x12,0x3FCB:0x34,0x3FEC:0x98,0x3FED:0x76,0x3FE4:0xA5,0x3FE5:0x5A}
MONITOR_CAL={0x5B03,0x4E71,0x4E72}
assert MONITOR_CAL<={a for a,_ in defaults}


class Memory(_OutputMemory):
    def read16(self,a):
        if a not in (0x3FCA,0x3FEC):return super().read16(a)
        count=self.mem[0x90B]
        if count:
            assert self.read_index<count,(hex(a),self.read_index,count)
            start=0x910+2*self.read_index;self.read_index+=1
            value=int.from_bytes(self.mem[start:start+2],'big')
        else:value=int.from_bytes(self.mem[a:a+2],'big')
        self.record('R',16,a,value)
        action=self.mem[0x908]
        if action==3:self.mem[0x1EC:0x1EE]=bytes.fromhex('ffff')
        if action==10 and a==0x3FCA:
            self.mem[0x4F]|=0x40;self.mem[0x205:0x207]=bytes.fromhex('5678')
        if action==11 and a==0x3FEC:
            self.mem[0x4B]&=0xEF;self.mem[0x50]&=0xFB;self.mem[0x44]=(self.mem[0x44]|8)&0xFB
        return value

    def write16(self,a,v):
        if a!=0x3FE4:return super().write16(a,v)
        self.record('W',16,a,v&65535)
        FixtureMemory.write8(self,a,(v>>8)&255);FixtureMemory.write8(self,a+1,v&255)
        if self.mem[0x908]==12:self.mem[0x04]|=0x80;self.mem[0x44]&=0xFB


memory=Memory();cpu=memory.cpu;coverage=set()


def execute(item):
    mode,edits=item
    memory.mem[:0x1000]=blank;memory.mem[0x4000:0x5B04]=cal_bytes
    for a,v in edits.items():memory.mem[a]=v
    memory.events.clear();memory.writes.clear();memory.attempts=memory.read_index=memory.cycle_counter=0
    memory.fail_at=memory.mem[0x907]
    cpu.s.pc=0x7000;cpu.s.sp=0x3FF;cpu.s.ccr=0xD0 if memory.mem[0x909] else 0xC0
    cpu.s.a,cpu.s.b,cpu.s.x,cpu.s.y=0x12,0x34,0x5678,0x9ABC
    status=unresolved=0

    def invoke(start):
        sp=cpu.s.sp;cpu.s.pc=start;cpu._push16(0x7000)
        for _ in range(5000):
            pc=cpu.s.pc
            if pc==0x7000:
                assert cpu.s.sp==sp,(hex(start),hex(cpu.s.sp),hex(sp))
                return True
            if pc==0xA5D7:return False
            if pc in (0x180F,0x1812):
                output=pc==0x180F
                if memory.mem[0x90D if output else 0x90A]:raise Missing(3 if output else 1)
                action=memory.mem[0x908];magnitude=cpu.s.a
                memory.record('T',0,pc,magnitude if output else action)
                if output:
                    if action==6:
                        magnitude^=0xA5;memory.mem[0x4F]|=1;memory.mem[0x62]=0xC1
                        memory.mem[0x5F:0x61]=bytes.fromhex('ff80')
                    cpu.s.a=magnitude
                else:
                    if action==1:
                        memory.mem[0x1FD:0x1FF]=bytes.fromhex('8123');memory.mem[0x86]&=0xBF
                    elif action==2:
                        memory.mem[0x36]|=0x20;memory.mem[0x53]|=0x10;memory.mem[0x06]=255;memory.mem[0x1D9]=7
                    cpu.s.a=0xA5
                cpu.s.b,cpu.s.x,cpu.s.y=0x5A,0xDEAD,0xBEEF;cpu.s.pc=0x7AA5
                continue
            coverage.add(pc);opcode=memory.mem[pc]
            if opcode in (0x0E,0x0F):memory.record('M',0,0,int(opcode==0x0F))
            cpu.step()
            if opcode==0x0E and memory.mem[0x908]==4:
                memory.mem[0x50]|=0x20;memory.mem[0x4F]|=0x80
        raise AssertionError(f'Controller execution budget at {cpu.s.pc:04X}')

    try:
        if mode==49:invoke(0xCA6B)
        invoke(0xABCB if mode==47 else 0xAC51 if mode==50 else 0xA466)
        if cpu.s.pc==0xA5D7:status=6
    except Failure:status=2
    except Missing as e:status=1;unresolved=e.task
    sinks=set(OUTPUTS)|{0x3FE8,0x3FE9,0x3FE6,0x3FE7,0x3FDC,0x3FDD,0x3FF6,0x3FF7}
    assert all(a in sinks or 0x3C0<=a<0x400 for a,_ in memory.writes)
    return {'status':status,'value':0,'state':[memory.mem[a] for a in OUTPUTS],
            'masked':int(bool(cpu.s.ccr&0x10)),'unresolved':unresolved,'partial':0,
            'coordinates':[0,0],'events':list(memory.events)}


def monitor_cases():
    # Every 16-bit wrapped difference, with independent sample/baseline wrap.
    for delta in range(65536):
        sample=(delta*73+0x1234)&65535
        yield case(47,word(0x3FCA,sample)|word(0x205,(sample-delta)&65535)|
                   {0x44:0x29,0x50:0xA5,0x4F:0x25,0x4E71:delta>>8,0x22C:(delta*17)&255})
    # The count comparison is strictly greater; FF can wrap when limit is FF.
    for count,limit in product(range(256),repeat=2):
        yield case(47,{0x44:0x29,0x50:0xA5,0x4F:0x25,0x22C:count,0x4E72:limit},periods=(0x1334,0xBEEF))
    # Equality qualifies: cover each low-byte delta/threshold and both histories.
    for delta,limit in product(range(256),repeat=2):
        yield case(47,{0x44:0x69 if delta&1 else 0x29,0x50:0xA5,0x4F:0x25,0x4E71:limit},
                   periods=(0x1234+delta,0xBEEF))


counts={}
counts['monitor']=compare(monitor_cases(),'wrapped delta/count/qualification C/ROM cases')
gates=[]
for flags,consumed,startup,options in product(range(256),[0xA1,0xA5],[0x25,0x65],[0x9C,0xBC]):
    gates.append(case(47,{0x44:flags,0x50:consumed,0x4F:startup,0x5B03:options,0x909:flags&1}))
for supervision,override,service,request in product(range(256),[0x21,0x25],[0xA5,0xB5],range(256)):
    # No first-reference: request/service/fault routing needs no peripheral I/O.
    gates.append(case(47,{0x04:supervision,0x44:override,0x3B:service,0x391:request,0x4B:request^0x55}))
counts['gates']=compare(gates,'monitor option/latch/service C/ROM cases')

joined=[];rng=random.Random(0x31ABCB)
for i in range(4096):
    edits={a:rng.randrange(256) for a in sorted(BASE.keys()|NEW_CAL|ADMISSION_CAL|EXPANDED_LATENCY|MONITOR_CAL)}
    edits.update({0x906:1,0x908:i%13,0x909:i&1,0x86:0xE0 if i&4 else 0xA0,
                  0x90A:int(i%13==0),0x90D:int(i%17==0)})
    joined.append(case([47,48,49,50][i%4],edits))
for mode,flags,action,masked in product([47,48,49,50],[0x21,0x29,0x69,0xA9,0xE9],range(13),[0,1]):
    joined.append(case(mode,{0x44:flags,0x4F:0xF5,0x50:0x25,0x908:action,0x909:masked},
                       periods=(2000,0xF000,0xF123,66,0x1234,0x4321,0x5678,0x9ABC,0xBEEF,0xFFFE)))
# Monitor success/fault prefixes and callback-time state changes are guaranteed,
# independently of the random joined corpus's entry/option distribution.
for options,startup,latch,action in product([0x9C,0xBC],[0x25,0x65],[0x29,0x69,0xA9],range(13)):
    joined.append(case(47,{0x44:latch,0x4F:startup,0x50:0x25,0x5B03:options,0x908:action}))
counts['joined']=compare(joined,'complete resident controller/alternate and callback witnesses')

failures=[]
for item in joined[::7]:
    for fail in range(1,len(execute(item)['events'])+1):failures.append((item[0],item[1]|{0x907:fail}))
counts['failures']=compare(failures,'controller read/write/hook failure prefixes')

history=[];edits={0x4F:0x25,0x44:0x21,0x4B:0xB5,0x205:0,0x206:0,0x22C:0}
for tick in range(512):
    edits.update(word(0x3FC0,2000+tick*3));edits.update(word(0x3FCA,0 if tick<20 else tick-20))
    edits.update({0x50:0x25 if tick<48 or tick%7==0 else 0x05,0x02:tick%160,
                  0x908:[0,7,8,9,10,11,12][tick%7],0x86:0xA0})
    if tick in (100,240,400):edits.update({0x44:0x21,0x4F:0x25,0x202:0})
    item=case(48,dict(edits));history.append(item);edits.update(dict(zip(OUTPUTS,execute(item)['state'])))
counts['history']=compare(history,'reference/startup/monitor retained-state history calls')

required=set();pc=0xABCB
while pc<0xAC51:required.add(pc);pc=decode(rom.read,pc).next_pc
required|={0xACA0,0xACA3,0xACA6}
assert required<=coverage,','.join(f'{pc:04X}' for pc in sorted(required-coverage))
print(f'{sum(counts.values()):,} controller comparisons; all {len(required)} monitor/cleanup instruction starts exercised; '
      '3 new calibration bytes and all 1,197 fixture bytes match stock. Production adapters require no task bindings; '
      '180F/1812 modules, target trap execution and physical EST timing remain separate.')
