"""SCI transport/session and boot slices against recorded BMHM instructions.

Coherent logical-address bindings and supplied SCI status are host fixtures.
Target interrupt frames, controller-service execution and physical bus timing
remain separate work. Invalid descriptor cycles have a C-only bounded guard.
"""
from pathlib import Path
_parent=Path(__file__).with_name('compare_fuel_delivery_rom.py')
exec(compile(_parent.read_text().split('\ncounts={}',1)[0],str(_parent),'exec'),globals())
import os
import tempfile

text=Path(__file__).with_name('serial_fixture_map.h').read_text()
for kind,address,rest in re.findall(r'\b([BWFA])\((0x[0-9a-f]+|\d+),([^\n]+?)\)',text):
    address=int(address,0)
    size=2 if kind=='W' else int(rest.split(',')[0]) if kind=='A' else 1
    RAM.update(range(address,address+size))
RAM.update(range(0x360,0x3b0))
RAM.update(range(0xa00,0xd00));RAM.add(0x303a)
OUTPUTS=sorted(RAM|set(range(0x3000,0x3035))|set(range(0x3fc0,0x3ffe)))
BASE={a:0 for a in RAM}|BASE
BASE.update({0x3b:0,0x42:0,0x45:0,0x50:0,0x360:0,0x361:0,0x364:0xf4,
             0x365:3,0x367:0,0x38e:1,0x399:1,0x302d:0x26,0x302e:0x20,0x302f:0xf4,
             0x907:0,0x908:0,0x909:1,0x917:1,0x918:0,0x91a:0,0x91b:0}|word(0x362,0x51bf))
image=bytes([255])*0x4000+rom.read(0x4000,0xc000)

class Memory(FixtureMemory):
    def __init__(self):
        super().__init__(rom);self.cpu=HC11CPU(self);self.events=[]
        self.attempts=self.fail_at=0;self.in_word=False
    def record(self,kind,width,a,value):
        self.attempts+=1
        if self.attempts==self.fail_at:raise Failure
        self.events.append([kind,width,a,value,int(bool(self.cpu.s.ccr&0x10))])
    def read8(self,a):
        a &= 65535;value=self.mem[a]
        if not self.in_word and 0x3000<=a<0x4000:self.record('R',8,a,value)
        if not self.in_word and a==0x302d and self.mem[0x908]==17:
            self.mem[a]^=0xe0;self.mem[0x302e]=0xe0
        return value
    def read16(self,a):
        a &= 65535;value=(self.mem[a]<<8)|self.mem[(a+1)&65535]
        if 0x3000<=a<0x4000:self.record('R',16,a,value)
        if self.mem[0x908]==19 and a in (0x51bb,0x51bd):
            target=0x368 if a==0x51bb else 0x36a;self.mem[target:target+2]=bytes.fromhex('ffff')
        if a==0x1f0 and self.mem[0x908]==15:
            n=(value+0x101)&65535;self.mem[a:a+2]=bytes([n>>8,n&255])
        return value
    def write8(self,a,v):
        a &= 65535;v &= 255
        if not self.in_word and 0x3000<=a<0x4000:self.record('W',8,a,v)
        self.mem[a]=v;self.writes.append((a,v))
        if a==0x302f and self.mem[0x908]==13:self.mem[0x361]=7;self.mem[0x360]=254
        if a==0x302f and self.mem[0x908]==14:
            n=((self.mem[0x1f0]<<8|self.mem[0x1f1])+0x101)&65535
            self.mem[0x1f0:0x1f2]=bytes([n>>8,n&255]);self.mem[0x55]=(self.mem[0x55]+1)&255
    def write16(self,a,v):
        a &= 65535;v &= 65535
        if 0x3000<=a<0x4000:self.record('W',16,a,v)
        self.mem[a]=v>>8;self.mem[(a+1)&65535]=v&255
        self.writes.extend([(a,v>>8),((a+1)&65535,v&255)])

memory=Memory();cpu=memory.cpu;coverage=set()
def execute(item):
    mode,edits=item
    memory.mem[:]=image;memory.mem[:0x4000]=bytes(0x4000)
    for a,v in edits.items():memory.mem[a]=v
    memory.events.clear();memory.writes.clear();memory.attempts=memory.cycle_counter=0
    memory.fail_at=(memory.mem[0x91e]<<8|memory.mem[0x91f]) or memory.mem[0x907]
    cpu.s.sp=0x3ff;cpu.s.ccr=0xd0 if memory.mem[0x909] else 0xc0
    cpu.s.a,cpu.s.b,cpu.s.x,cpu.s.y=0x12,0x34,0x5678,0x9abc
    status=value=0
    def invoke(start,stops=(0x7000,),boot=False):
        sp=cpu.s.sp
        if not boot:cpu._push16(0x7000)
        cpu.s.pc=start;gap_start=0
        for _ in range(30000):
            pc=cpu.s.pc
            if pc in stops:
                if not boot and pc!=0x7000:assert cpu._pull16()==0x7000
                assert cpu.s.sp==sp;return pc
            coverage.add(pc);opcode=memory.mem[pc]
            if opcode in (0x0e,0x0f):memory.record('M',0,0,int(opcode==0x0f))
            if pc in (0xf63a,0xf7a5,0xf816,0xfa3e):gap_start=memory.cycle_counter
            cpu.step()
            if pc==0xf3ed:
                cycles=memory.cycle_counter-gap_start;assert cycles==11,(hex(cpu.s.pc),cycles)
                memory.record('D',0,0,cycles)
                if memory.mem[0x908]==16:memory.mem[0x3ffc]^=4
            action=memory.mem[0x908]
            if action==18 and opcode==0x0f:
                memory.mem[0x365]=0;memory.mem[0x362:0x364]=bytes.fromhex('a300')
            if action==18 and opcode==0x0e:memory.mem[0x3b]|=16
        raise AssertionError(f'Serial slice budget at {cpu.s.pc:04X}')
    def irq():invoke(0xf7ea,(0xf821,))
    def drain():
        for _ in range(memory.mem[0x91c]<<8|memory.mem[0x91d]):
            control=memory.mem[0x302d]
            if control==0x26:break
            memory.mem[0x302e]=0x80 if control&0x80 else 0x40;irq()
    try:
        descriptor=memory.mem[0x362]<<8|memory.mem[0x363]
        cpu.s.x=descriptor;cpu.s.a=memory.mem[0x917];cpu.s.b=memory.mem[0x918]
        if mode==0:invoke(0xf90b)
        elif mode==1:invoke(0xf822)
        elif mode==2:irq()
        elif mode==3:invoke(0xf5e8)
        elif mode==4:invoke(0xf781)
        elif mode==5:invoke(0xfa4d)
        elif mode==6:invoke(0xfa28)
        elif mode==7:invoke(0xf8e6)
        elif mode==8:invoke(0xf8f4)
        elif mode==9:invoke(0xf96b)
        elif mode==10:invoke(0xf9be)
        elif mode==11:invoke(0xf927,(0xf93b,0xf939));value=cpu.s.x
        elif mode==12:invoke(0xf86e,(0xf8e6,));value=cpu.s.a
        elif mode==13:invoke(0xfa3b if cpu.s.a else 0xf813,(0xfa46 if cpu.s.a else 0xf81e,))
        elif mode==14:invoke(0x717f,(0x718a,),True);value=memory.mem[0x3ff]
        elif mode==15:invoke(0x7431,(0x7459,),True)
        elif mode in (16,18):
            for i in range(memory.mem[0x919]<<8|memory.mem[0x91a]):
                memory.mem[0x302f]=memory.mem[0xa000+i];memory.mem[0x302e]=memory.mem[0xa100+i]
                if mode==18:irq()
                else:invoke(0xf90b)
            if mode==18:drain()
        elif mode==17:drain()
        elif mode==19:invoke(0xf781);invoke(0xf5e8)
        else:raise AssertionError(mode)
    except Failure:status=2
    unknown=[(a,v) for a,v in memory.writes if a not in OUTPUTS and not
             (0x3b0<=a<0x400 or mode==14 and 0x360<=a<0x3ff or 0xad<=a<=0xb2 or 0xa00<=a<0xd00)]
    assert not unknown,[(hex(a),v) for a,v in unknown]
    return {'status':status,'value':value,'unresolved':0,'masked':int(bool(cpu.s.ccr&0x10)),
            'state':[memory.mem[a] for a in OUTPUTS],'events':list(memory.events)}

def frame(device,payload,bad=False,mode=18,extra=None):
    data=[device,0x55+len(payload),*payload]
    data.append((-sum(data)+int(bad))&255)
    return case(mode,word(0x919,len(data))|word(0x91c,100)|
                {0xa000+i:v for i,v in enumerate(data)}|{0xa100+i:0x20 for i in range(len(data))}|(extra or {}))

def custom(format=0,length=3):
    return word(0x362,0xa200)|word(0xa200,0)|{0xa202:0xf4,0xa203:format,0xa204:length}|word(0xa205,0xa00)|word(0xa207,0x36c)|\
           {a:((a*17+3)&255) for a in range(0xa00,0xd00)}|\
           {a:v for i in range(256) for a,v in word(0xa209+2*i,0xb00+i).items()}

counts={};rng=random.Random(0x31f90b)
with tempfile.TemporaryDirectory(prefix='pcm-serial-rom-') as directory:
    path=Path(directory)/'bmhm.bin';path.write_bytes(image);os.environ['PCM_SERIAL_ROM']=str(path)
    counts['direct']=compare((case(m) for m in range(20)),'direct SCI, session and boot slices')
    counts['frames']=compare((frame(device,payload,bad,extra={0x50:factory})
        for device,factory,payload,bad in product([0xf4,0xf5,0xfe],[0,8],
        [[],[0],[1,0],[1,1],[1,2],[1,3],[1,255],[2,8,0],[3,0,0,1,0],[4,255,127,255,127,255,127,255,127,255,127],
         [4],[4,1],[4,*range(1,34)],[10],[11]], [False,True])), 'complete requests and interrupt-driven replies')
    counts['headers']=compare((case(0,{0x302e:s,0x302f:v,0x360:c,0x361:k,0x42:session})
        for s,v,c,k,session in product([0,2,4,8,14,32],range(256),[0,1,2],[0,255],[0,3])),
        'all incoming bytes at ID, length and checksum/error gates')
    counts['idle']=compare((case(4,{0x42:session,0x367:age,0x3b:flags,0x45:255}|word(0x368,n)|word(0x36a,n)|
        word(0x51bb,threshold)|word(0x51bd,threshold))
        for session,age,flags,n,threshold in product([0,1,2,3,0xfc], [0,198,199,200,254,255],
        [0,0x18,0xff],[0,1,65534,65535],[0,1,199,65535])), 'session expiry and service counter boundaries')
    counts['broadcast']=compare((case(3,custom(fmt,n)|word(0x518f+(phase&31),0xa200)|
        {2:phase,0x42:session,0x3b:busy,0x908:action})
        for fmt,n,phase,session,busy,action in product([0,0x40,0x80,0xc0],[0,1,3,34,128,255],
        [0,1,31,32,255],[0,1],[0,0x40],[0,18])), 'broadcast schedule, deferred work and precopy loops')
    counts['callbacks']=compare((case(m,custom(0x80,3)|{0x360:count,0x365:3,0x42:session,0x908:action,
        0x3b:pending,0x366:0xa5}|word(0xa209,0x31f0)|word(0x1f0,0x12ff))
        for m,count,session,action,pending in product([1,2,4,6,7,8,12,13,19],[1,2,3,4,5,6],
        [0,1],range(13,19),[0,128])), 'callback mutation and literal IRQ/control read order')
    failure_items=[]
    for item in [case(m,custom(0x80,3)|{0x42:1,0x367:199}) for m in range(16) if m!=9]+\
                [frame(0xf4,[1,0]),frame(0xf5,[4,1,255,2]),case(3,custom()|word(0x518f,0xa200))]:
        for position in range(1,len(execute(item)['events'])+2):
            failure_items.append((item[0],item[1]|word(0x91e,position)))
    counts['failures']=compare(failure_items,'every observable failure prefix of representative transactions')
    if '--quick' not in sys.argv:
        counts['irq']=compare((case(2,{0x302d:control,0x302e:status,0x302f:0,0x360:6,0x365:3})
            for control,status in product(range(256),repeat=2)), 'all SCI enable/status combinations')
        counts['counts']=compare((case(1,custom(0,3)|{0x360:c,0x365:n})
            for c,n in product(range(256),repeat=2)), 'all transmitter count/length pairs')
        counts['commands']=compare((frame(device,[command,*payload],extra={0x3b:0xa7,0x42:0xfc})
            for device,command,payload in product([0xf4,0xf5],range(256),[[],[0],[1],[2],[255],list(range(1,34))])),
            'all command bytes and short/maximum command payloads')
        counts['address']=compare((case(12,custom(0x40,3)|{0x918:1,0x38e:2,0x364:0xf4,0x50:factory}|
            word(0xa205,0xa100)|word(0xa101,address))
            for address,factory in product(range(65536),[0,8]) if not
            (0x3b0<=address<=0x400 or not factory and 0x3b0<=(address&0xcfff)<=0x400)),
            'complete selected-address domain outside HC11-private call stack')
    counts['captured_age']=compare((case(4,{0x908:19,0x3b:flags}|word(0x368,n)|word(0x36a,n)|
        word(0x51bb,threshold)|word(0x51bd,threshold))
        for flags,n,threshold in product([0,0x18],[0,1,65535],[0,1,100,65535])),
        'duration comparisons retain the captured increment across threshold reads')
    counts['header_adjust']=compare((case(1,custom(0x40,64)|{0x360:1,0x365:n,0x38e:3,0x399:3,0x364:device,0x42:session})
        for n,device,session in product(range(256),[0xf4,0xf5,0xfe],[0,3])),
        'every command03 old length and signed header adjustment')
    counts['formats']=compare((case(12,custom(fmt,3)|{0x918:ordinal,0x42:session,0x364:device,0x38e:command,0x399:command})
        for fmt,ordinal,session,device,command in product([0,0x40,0x80,0xc0],range(256),[0,3],[0xf4,0xf5,0xfe],[0,2,4])),
        'flat/live/requested formats, byte-offset wrap and device command selection')
    counts['startup']=compare((case(15,{2:cap,4:flags,0x4d96:cap,0x48fd:bound,0x48fe:255-bound}|
        {0x2b3+i:(cap+i*13)&255 for i in range(21)})
        for cap,flags,bound in product(range(256),[0,8],[0,127,255])),
        'all conditional boot age seeds and retained-cell bound combinations')
    counts['clear']=compare((case(14,{a:(a*17+seed)&255 for a in range(0x360,0x400)})
        for seed in range(256)), 'all retained03FF values and complete serial boot clear')
    history=[];retained={}
    for i in range(256):
        if i%5==4:
            item=case(4,retained|{0x367:199,0x45:255})
        else:
            payload=([4,*[((i*17+j*13)&255) for j in range(i%11)]],[],[1,i&255],[10])[i%5]
            item=frame(0xf4 if i&1 else 0xf5,payload,i%13==0,extra=retained)
        history.append(item);retained.update(dict(zip(OUTPUTS,execute(item)['state'])))
    counts['history']=compare(history,'retained short/service/page/clear requests, bad frames and idle expiry')
    required=set()
    for start,end in [(0xf5e8,0xf64e),(0xf781,0xfa5b),(0x717f,0x718a),(0x7431,0x7459)]:
        pc=start
        while pc<end:required.add(pc);pc=decode(rom.read,pc).next_pc
    required.remove(0xf821) # Hardware RTI frame/ABI is deliberately a target boundary.
    missing=required-coverage
    print('Missing scoped starts:',','.join(f'{a:04X}' for a in sorted(missing)),flush=True)
    assert not missing
    print(f"{sum(counts.values()):,} SCI/session/boot cases match; all {len(required)} scoped instruction starts executed.",flush=True)
