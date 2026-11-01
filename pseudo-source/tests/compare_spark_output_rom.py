"""Compare AB44..ABCA output and AC51..ACA6 alternate RPM against BMHM.

Normal joined cases stop before the ABCB monitor. 180F/1812 returns are explicit
fixtures, not supplied module implementations or reconstructed machine ABIs.
"""
from pathlib import Path

# Reuse the trusted prior suite's literal fixtures and bounded CPU setup only.
# Its corpus starts after this marker, so none of its comparisons run here.
_prior=Path(__file__).with_name('compare_spark_period_rom.py')
exec(compile(_prior.read_text().split('counts={}')[0],str(_prior),'exec'),globals())
_PeriodMemory=Memory
OUTPUTS=OUTPUTS+[0x4B,0x201,0x3FDC,0x3FDD,0x3FE6,0x3FE7,0x3FE8,0x3FE9,0x3FF6,0x3FF7]
assert len(OUTPUTS)==len(set(OUTPUTS))==124
BASE=BASE|{0x4B:0xB5,0x201:77,0x3FDC:0,0x3FDD:66,0x3FE6:0xA1,0x3FE7:0xB2,
           0x3FE8:0xC3,0x3FE9:0xD4,0x3FF6:0xF0,0x3FF7:0}
LATENCY_CAL=set(range(0x454A,0x4559))
assert LATENCY_CAL<={a for a,_ in defaults}
# A changed cap can use a supplied17-knot profile. Its extra backing is an
# explicit fixture input, not bytes implicitly added to the stock C profile.
EXPANDED_LATENCY=LATENCY_CAL|set(range(0x4559,0x455C))


class Memory(_PeriodMemory):
    def read16(self,a):
        if not 0x3000<=a<0x4000:return super().read16(a)
        assert a in (0x3FC0,0x3FF6,0x3FDC),hex(a)
        count=self.mem[0x90B]
        if count:
            assert self.read_index<count,(hex(a),self.read_index,count)
            start=0x910+2*self.read_index;self.read_index+=1
            value=int.from_bytes(self.mem[start:start+2],'big')
        else:value=int.from_bytes(self.mem[a:a+2],'big')
        self.record('R',16,a,value)
        if self.mem[0x908]==3:self.mem[0x1EC:0x1EE]=bytes.fromhex('ffff')
        if self.mem[0x908]==9 and a==0x3FDC:self.mem[0x1EC:0x1EE]=bytes.fromhex('9abc')
        return value

    def write16(self,a,v):
        if not 0x3000<=a<0x4000:return super().write16(a,v)
        assert a in (0x3FE8,0x3FE6,0x3FDC,0x3FF6),hex(a)
        self.record('W',16,a,v&65535)
        FixtureMemory.write8(self,a,(v>>8)&255);FixtureMemory.write8(self,a+1,v&255)
        if self.mem[0x908]==7 and a==0x3FE6:self.mem[0x1EC:0x1EE]=bytes.fromhex('1234')
        if self.mem[0x908]==8 and a==0x3FE8:self.mem[0x1EC:0x1EE]=bytes.fromhex('5678')


memory=Memory();cpu=memory.cpu;coverage=set()


def execute(item):
    mode,edits=item
    memory.mem[:0x1000]=blank;memory.mem[0x4000:0x5B04]=cal_bytes
    for a,v in edits.items():memory.mem[a]=v
    memory.events.clear();memory.writes.clear();memory.attempts=memory.read_index=memory.cycle_counter=0
    memory.fail_at=memory.mem[0x907]
    cpu.s.pc=0x7000;cpu.s.sp=0x3FF;cpu.s.ccr=0xD0 if memory.mem[0x909] else 0xC0
    cpu.s.a,cpu.s.b,cpu.s.x,cpu.s.y=0x12,0x34,0x5678,0x9ABC
    status=unresolved=0;value=memory.mem[0x900] if mode==39 else 0xBEEF if mode==40 else 0
    coordinates=[0,0]

    def invoke(start,stop,root=False):
        sp=cpu.s.sp;cpu.s.pc=start
        if stop==0x7000 or root:cpu._push16(0x7000)
        for _ in range(5000):
            pc=cpu.s.pc
            if pc==stop:
                assert cpu.s.sp==(sp-2 if root else sp),(hex(start),hex(pc),hex(cpu.s.sp),hex(sp))
                return True
            if root and pc==0x7000:
                assert cpu.s.sp==sp;return False
            if pc==0xA5D7:return False
            if pc==0xAC51 and root and memory.mem[0x90C]:raise Missing(2)
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
        raise AssertionError(f'Output execution budget at {cpu.s.pc:04X}')

    try:
        if mode==38:
            # Three actual instruction fragments expose the pure transform
            # without performing the normal caller's RAM publication stores.
            cpu.s.d=int.from_bytes(memory.mem[0x900:0x902],'big');invoke(0xA600,0xA607);value=cpu.s.d
            cpu.s.d=value;invoke(0xA60A,0xA61E);coordinates[0]=cpu.s.a
            cpu.s.d=value;invoke(0xA623,0xA628);coordinates[1]=cpu.s.a
        elif mode==39:
            cpu.s.a=value;invoke(0xAB62,0xAB69);value=cpu.s.a
        elif mode==40:
            invoke(0xAB44,0xAB89);value=cpu.s.d
        elif mode==41:
            cpu.s.d=int.from_bytes(memory.mem[0x900:0x902],'big');invoke(0xAB89,0xABCB)
        elif mode==42:invoke(0xAB44,0xABCB)
        elif mode==43:invoke(0xAC51,0x7000)
        else:
            assert mode in (44,45,46)
            if mode==46:invoke(0xCA6B,0x7000)
            value=int(invoke(0xA466,0xAB44 if mode==45 else 0xABCB,root=True))
            if cpu.s.pc==0xA5D7:status=6
    except Failure:status=2
    except Missing as e:status=1;unresolved=e.task
    # The pure-helper cases only return values; the production callers' RAM
    # stores are checked separately by output, alternate and joined cases.
    sinks={0x04,0x18,0x41,0x44,0x4B,0x4F,0x50,0x51,0x53,0x5F,0x60,0x61,0x62,0x63,0x64,0x67,0x68,0x69,0x6E,0x6F,
        0x1C0,0x1C1,0x1C2,0x1C9,0x1CF,0x1E6,0x1E7,0x1E8,0x1E9,0x1EA,0x1EB,0x1EC,0x1ED,
        0x1EE,0x1EF,0x1F0,0x1F1,0x1F2,0x1F3,0x1F4,0x1F5,0x1F8,0x1F9,0x1FA,0x1FB,0x1FC,0x1FD,0x1FE,
        0x201,0x202,0x208,0x20B,0x20C,0x20D,0x20E,0x210,0x211,0x229,0x260,0x261,0x28C,0x28D,0x28E,0x28F,0x2CE,
        0x3060,0x306F,0x837,0x838,0x839,0x83A,0x83B,0x83C,0x83D,0x83E,0x83F,0x840,0x841,0x843,0x844,
        0x3FE8,0x3FE9,0x3FE6,0x3FE7,0x3FDC,0x3FDD,0x3FF6,0x3FF7}
    assert all(a in sinks or 0x3C0<=a<0x400 for a,_ in memory.writes)
    return {'status':status,'value':value,'state':[memory.mem[a] for a in OUTPUTS],
            'masked':int(bool(cpu.s.ccr&0x10)),'unresolved':unresolved,'partial':0,
            'coordinates':coordinates,'events':list(memory.events)}


def convert_cases():
    for c in range(65536):
        yield case(40,word(0x1EE,c)|word(0x5F,(c*257+983)&65535)|{0x51:0xC5,0x62:(c*37)&255})
    for gain in range(65536):
        yield case(40,word(0x1F2,gain)|word(0x1EE,0xFF80 if gain&1 else 57)|word(0x5F,65535)|{0x51:0x85,0x62:40})
    for magnitude,factor in product(range(256),repeat=2):
        yield case(40,word(0x1EE,magnitude)|word(0x1F2,factor<<8)|{0x51:0x85})
    synthetic={0x454B+i:(i*73+17)&255 for i in range(17)}
    for rpm,limit in product(range(256),repeat=2):
        yield case(40,synthetic|{0x906:1,0x62:rpm,0x454A:limit})


def handoff_cases():
    for saved in range(65536):
        yield case(41,word(0x900,saved)|word(0x1EC,(saved*37)&65535),periods=((saved*73+10)&65535,(saved*257)&65535,(saved*29+0xF000)&65535,(saved*17)&65535))
    for difference in range(65536):
        saved=(difference*17)&65535;rolling=(saved+difference-0xF000)&65535
        yield case(41,word(0x900,saved),periods=(0,rolling,(difference*29)&65535,66))
    for p in range(65536):yield case(41,word(0x900,0xFF22),periods=(p,0xF000,0xF123,66))


def alternate_cases():
    for p in range(65536):yield case(43,word(0x3FC0,p)|{0x44:0xAD})
    for coefficient,p in product(range(256),[0,1,153,154,255,256,2000,0x3FFF,0x4000,0x7FFF,0x8000,0x8001,0xFF7F,0xFFFF]):
        yield case(43,word(0x3FC0,p)|{0x44:0xAD,0x4141:coefficient})
    for flags,first in product(range(256),[0xA5,0xAD]):
        yield case(43,{0x44:first,0x4B:flags,0x50:flags^0x55})


counts={}
counts['coordinates']=compare((case(38,word(0x900,p)) for p in range(65536)),'shared coordinate C/ROM cases')
extension=[]
for magnitude,enabled,missing,action,masked in product(range(256),[0xA0,0xE0],[0,1],[0,6],[0,1]):
    extension.append(case(39,{0x900:magnitude,0x86:enabled,0x90D:missing,0x908:action,0x909:masked}))
counts['extension']=compare(extension,'180F gate/payload witnesses')
counts['convert']=compare(convert_cases(),'magnitude/startup/latency C/ROM cases')
counts['handoff']=compare(handoff_cases(),'ordered handoff C/ROM cases')
counts['alternate']=compare(alternate_cases(),'alternate RPM C/ROM cases')

joined=[];rng=random.Random(0x31AB44)
for i in range(4096):
    edits={a:rng.randrange(256) for a in sorted(BASE.keys()|NEW_CAL|ADMISSION_CAL|EXPANDED_LATENCY)}
    edits.update({0x906:1,0x908:i%10,0x909:i&1,0x86:0xE0 if i&4 else 0xA0,
        0x90A:int(i%13==0),0x90C:int(i%19==0),0x90D:int(i%17==0)})
    joined.append(case([41,42,43,44,45,46][i%6],edits))
for mode,action,masked in product([40,41,42,43,44,45,46],range(10),[0,1]):
    joined.append(case(mode,{0x908:action,0x909:masked},periods=(2000,0xF000,0xF123,66,0x1234,0x4321,0x5678,0x9ABC)))
counts['joined']=compare(joined,'joined publication/alternate and callback witnesses')
failures=[]
for item in joined[::17]+extension[::127]:
    for fail in range(1,len(execute(item)['events'])+1):failures.append((item[0],item[1]|{0x907:fail}))
counts['failures']=compare(failures,'failed read/write/hook publication prefixes')
history=[];edits={0x4F:0x25,0x44:0xA5}
for tick in range(256):
    edits.update(word(0x3FC0,2000+tick*13));edits.update({0x50:0x25 if tick<24 or tick%7==0 else 0x05,
        0x02:tick%160,0x908:[0,7,8,9][tick%4],0x86:0xA0})
    item=case(44,dict(edits));history.append(item);edits.update(dict(zip(OUTPUTS,execute(item)['state'])))
counts['history']=compare(history,'publication/alternate history calls')

required=set()
for start,end in [(0xAB44,0xABCB),(0xAC51,0xACA7)]:
    pc=start
    while pc<end:required.add(pc);pc=decode(rom.read,pc).next_pc
assert required<=coverage,','.join(f'{pc:04X}' for pc in sorted(required-coverage))
print(f'{sum(counts.values()):,} output comparisons; all {len(required)} output/alternate instruction starts exercised; '
      '15 new latency bytes and all 1,194 fixture bytes match stock. ABCB tail and module implementations remain separate.')
