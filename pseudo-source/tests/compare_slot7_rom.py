"""Compare C514 output, F5DC probe and ordered slot7 publication with BMHM.

180C, 9E99 and ACA7 returns are explicit dependency fixtures. Mode3 supplies a
subsequent normal spark call at phase8; it does not replace intervening factory
input work, prove physical output behavior or reconstruct module machine ABIs.
"""
from pathlib import Path

_prior=Path(__file__).with_name('compare_spark_controller_rom.py')
exec(compile(_prior.read_text().rsplit('\ncounts={}',1)[0],str(_prior),'exec'),globals())
_ControllerMemory=Memory
OUTPUTS=OUTPUTS+[0x4C,0xD9,0x99,0x1C,0x1D,0x8E,0x8A,0x8B,0x126,0x127,0x12B,0x12C,
                 0x39A,0x39B,0x306A,0x306B,0x1800,0x1801]
assert len(OUTPUTS)==len(set(OUTPUTS))==148
BASE=BASE|{0x4C:0xCC,0xD9:0,0x99:0xB5,0x1C:0xA5,0x1D:0x25,0x8E:0x25,
           0x8A:0xA5,0x8B:0xF4,0x126:0x81,0x127:0x23,0x12B:0x7F,0x12C:0xFF,
           0x39A:0xA5,0x39B:0xE5,0x306A:0x12,0x306B:0x34,0x1800:0,0x1801:0}
GEAR=set(range(0xB319,0xB419));gear_bytes=rom.read(0xB319,256)
slot_defaults=json.loads(subprocess.check_output([binary,'--slot7-defaults'],text=True))
assert len(slot_defaults)==257 and {a for a,_ in slot_defaults}==GEAR|{0x400F}
for a,v in slot_defaults:assert v==rom.read(a,1)[0],(hex(a),v)


class Memory(_ControllerMemory):
    def read16(self,a):
        if a!=0x1800:return super().read16(a)
        value=int.from_bytes(self.mem[a:a+2],'big');self.record('R',16,a,value)
        if self.mem[0x908]==17:self.mem[0x86]|=0x40;self.mem[0x4C]^=0x55
        return value

    def write16(self,a,v):
        if a!=0x306A:return super().write16(a,v)
        self.record('W',16,a,v&65535)
        FixtureMemory.write8(self,a,(v>>8)&255);FixtureMemory.write8(self,a+1,v&255)
        if self.mem[0x908]==18:self.mem[0x126:0x128]=bytes.fromhex('9abc');self.mem[0x8A]=0


memory=Memory();cpu=memory.cpu;coverage=set()


def execute(item):
    mode,edits=item
    memory.mem[:0x1802]=bytes(0x1802);memory.mem[0x4000:0x5B04]=cal_bytes
    memory.mem[0xB319:0xB419]=gear_bytes
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
                assert cpu.s.sp==sp,(hex(start),hex(cpu.s.sp),hex(sp));return
            if pc==0xA5D7:return
            action=memory.mem[0x908]
            if pc in (0x180C,0x9E99,0xACA7):
                bit,task={0x180C:(1,4),0x9E99:(2,5),0xACA7:(4,6)}[pc]
                if memory.mem[0x90E]&bit:raise Missing(task)
                memory.record('T',0,pc,action)
                if pc==0x180C:
                    if action==13:memory.mem[0x86]|=0x40;memory.mem[0x4C]^=0x55
                    if action==14:memory.mem[0x86]&=0xBF;memory.mem[0x06]=32
                elif pc==0x9E99 and action==15:
                    memory.mem[0x06]=200;memory.mem[0x3D]|=0x20;memory.mem[0x278]=123
                    memory.mem[0x22F]=140;memory.mem[0x1C0]=128;memory.mem[0x62]=180;memory.mem[0x19]|=0x10
                elif pc==0xACA7 and action==16:
                    memory.mem[0x1EE:0x1F0]=bytes.fromhex('beef');memory.mem[0x4C]^=0xA0
                cpu.s.a,cpu.s.b,cpu.s.x,cpu.s.y=0xA5,0x5A,0xDEAD,0xBEEF;cpu.s.pc=0x7AA5
                continue
            if pc in (0x180F,0x1812):
                output=pc==0x180F
                if memory.mem[0x90D if output else 0x90A]:raise Missing(3 if output else 1)
                magnitude=cpu.s.a;memory.record('T',0,pc,magnitude if output else action)
                if output:
                    if action==6:
                        magnitude^=0xA5;memory.mem[0x4F]|=1;memory.mem[0x62]=0xC1
                        memory.mem[0x5F:0x61]=bytes.fromhex('ff80')
                    cpu.s.a=magnitude
                else:
                    if action==1:memory.mem[0x1FD:0x1FF]=bytes.fromhex('8123');memory.mem[0x86]&=0xBF
                    elif action==2:
                        memory.mem[0x36]|=0x20;memory.mem[0x53]|=0x10;memory.mem[0x06]=255;memory.mem[0x1D9]=7
                    cpu.s.a=0xA5
                cpu.s.b,cpu.s.x,cpu.s.y=0x5A,0xDEAD,0xBEEF;cpu.s.pc=0x7AA5
                continue
            coverage.add(pc);opcode=memory.mem[pc]
            if opcode in (0x0E,0x0F):memory.record('M',0,0,int(opcode==0x0F))
            cpu.step()
            if opcode==0x0E and action==4:memory.mem[0x50]|=0x20;memory.mem[0x4F]|=0x80
        raise AssertionError(f'Slot7 execution budget at {cpu.s.pc:04X}')

    try:
        invoke(0xC514 if mode==0 else 0xF5DC if mode==1 else 0x7B1B)
        if mode==3:memory.mem[0x02]=8;invoke(0xA466)
        if cpu.s.pc==0xA5D7:status=6
    except Failure:status=2
    except Missing as e:status=1;unresolved=e.task
    assert all(a in set(OUTPUTS) or 0x3C0<=a<0x400 for a,_ in memory.writes)
    return {'status':status,'value':0,'state':[memory.mem[a] for a in OUTPUTS],
            'masked':int(bool(cpu.s.ccr&0x10)),'unresolved':unresolved,'partial':0,
            'coordinates':[0,0],'events':list(memory.events)}


def gear_cases():
    for gear,shadow,option in product(range(256),range(256),[0x10,0x50]):
        yield case(0,{0xD9:gear,0x4C:shadow,0x400F:option,0x909:shadow&1})
    for pattern,shadow in product(range(256),repeat=2):
        yield case(0,{0xD9:37,0xB319+37:pattern,0x4C:shadow,0x400F:0x50})


def command_cases():
    for command in range(65536):
        yield case(0,word(0x126,command)|word(0x12B,((command*73)^0x8000)&65535)|
                   {0x8A:command&255,0x8B:(command>>8)^0x55})
    edges=[0,1,127,128,255,256,0x7FFF,0x8000,0xFF7F,0xFF80,0xFFFF]
    for command,limit,flags in product(edges,edges,range(256)):
        yield case(0,word(0x126,command)|word(0x12B,limit)|{0x8A:flags,0x8B:flags^0xAA})


def gate_cases():
    fields=[(0x39A,0x40),(0x39B,0x40),(0x99,0x08),(0x1C,0x02),(0x1D,0x80),(0x86,0x01),(0x8E,0x80)]
    for bits,option in product(range(128),range(256)):
        edits={a:0xFF if bits&(1<<i) else 0xFF^mask for i,(a,mask) in enumerate(fields)}
        yield case(0,edits|{0x400F:option})
    for (address,mask),value,option in product(fields,range(256),[0x10,0x50]):
        edits={a:0xFF^mask for a,mask in fields};edits.update({address:value,0x400F:option})
        yield case(0,edits)


counts={}
counts['gear']=compare(gear_cases(),'raw gear/window and wrapped shadow C/ROM cases')
counts['command']=compare(command_cases(),'command word/comparison/publication C/ROM cases')
counts['gates']=compare(gate_cases(),'service/inhibit/option C/ROM cases')
counts['signature']=compare((case(1,word(0x1800,s)|{0x86:s&255}) for s in range(65536)),
                            'exact signature and profiling-independent C/ROM cases')

joined=[];rng=random.Random(0x317B1B)
for i in range(2048):
    edits={a:rng.randrange(256) for a in sorted(BASE.keys()|NEW_CAL|ADMISSION_CAL|EXPANDED_LATENCY|MONITOR_CAL|GEAR)}
    edits.update(word(0x1800,0x7E18 if i%3 else 0));edits.update({0x906:1,0x908:i%19,
        0x909:i&1,0x90E:(i>>2)&7,0x90A:int(i%13==0),0x90D:int(i%17==0)})
    joined.append(case(i%4,edits))
for mode,signature,enabled,action,missing in product([1,2,3],[0,0x7E18],[0xA0,0xE0],range(19),range(8)):
    joined.append(case(mode,word(0x1800,signature)|{0x86:enabled,0x908:action,0x90E:missing,0x4439:1}))
counts['joined']=compare(joined,'ordered slot7/normal-spark and callback witnesses')
failures=[]
for item in joined[::11]:
    for fail in range(1,len(execute(item)['events'])+1):failures.append((item[0],item[1]|{0x907:fail}))
counts['failures']=compare(failures,'slot7 output/probe/dependency and following spark failure prefixes')

history=[];edits={0x4F:0xF5,0x44:0x29,0x4B:0xB5,0x90E:0}
for tick in range(256):
    edits.update(word(0x1800,0x7E18 if tick%3 else 0));edits.update(word(0x3FC0,2000+tick*3))
    edits.update({0x02:(7+16*tick)%160,0x50:0x25,0xD9:tick&3,0x908:13+tick%6,0x4439:1})
    item=case(3,dict(edits));history.append(item);edits.update(dict(zip(OUTPUTS,execute(item)['state'])))
counts['history']=compare(history,'slot7 input/publication and following normal-call history steps')

required=set()
for start,end in [(0xC514,0xC56F),(0xF5DC,0xF5E8),(0x7B1B,0x7B2B)]:
    pc=start
    while pc<end:required.add(pc);pc=decode(rom.read,pc).next_pc
assert required<=coverage,','.join(f'{pc:04X}' for pc in sorted(required-coverage))
print(f'{sum(counts.values()):,} slot7 comparisons; all {len(required)} output/probe/wrapper instruction starts exercised; '
      '256 raw-index backing bytes and shared400F match stock. Existing1,197 spark fixture bytes also match. '
      '180C/9E99/ACA7 bodies and physical output meaning remain explicit dependencies.')
