"""Retained service lifecycle/clear footprints versus actual BMHM bytes.

The AE85..AE9C eight-callee prefix remains a supplied dependency. Native RAM
owners and foreign byte accesses are distinguished explicitly in this fixture.
This is not a target memory-placement or interrupt-timing proof.
"""
from pathlib import Path
_parent=Path(__file__).with_name('compare_serial_rom.py')
exec(compile(_parent.read_text().split('\ncounts={};rng=',1)[0],str(_parent),'exec'),globals())

for a in range(0xa00,0xd00):RAM.discard(a);BASE.pop(a,None)
RAM.update(range(0xa0));RAM.update(range(0x182,0x186));RAM.update([0x817,0x21c,0x81c])
text=Path(__file__).with_name('service_fixture_map.h').read_text()
for kind,address,rest in re.findall(r'\b([BFA])\((0x[0-9a-f]+|\d+),([^\n]+?)\)',text):
    address=int(address,0);size=int(rest.split(',')[0]) if kind=='A' else 1;RAM.update(range(address,address+size))
OUTPUTS=sorted(RAM|set(range(0x3000,0x3035))|set(range(0x3fc0,0x3ffe)))
BASE={a:0 for a in RAM}|BASE
BASE.update({0x920:1,0x921:0,0x38e:4,0x399:4,0x42:3,0x391:0,0x44:4,
    0x15:0xcc,0x103:3,0x10a:0x6f,0x111:0xa5,0x118:0x5a,0x11a:0xb3,0x130:0x12,0x131:0x34})
# These byte accesses are native fields in C. Other logical serial data uses
# the provider, preserving the first batch's explicit address-space interface.
SERIAL_OWNED={0x3b,0x42,0x45,0x399}|set(range(0x360,0x38f))
_SerialMemory=Memory
class Memory(_SerialMemory):
    def __init__(self):super().__init__();self.foreign=None
    def foreign_byte(self,a):return a==self.foreign and not self.in_word
    def read8(self,a):
        a &= 65535;value=super().read8(a)
        if self.foreign_byte(a):
            if not 0x3000<=a<0x4000:self.record('R',8,a,value)
            action=self.mem[0x908]
            if action==25 and a==(self.mem[0x923]<<8|self.mem[0x924]):self.mem[a]^=0x40
            if action==20 and a==0x3a0:self.mem[a]^=0xc0
            if action==21 and a==0x39e:self.mem[0x3b]&=0xf7
            if action==22 and 0xf377<=a<=0xf37f:self.mem[a]^=255
            if action==23 and a==0x391:
                self.mem[0x42]=0;self.mem[0x36a:0x36c]=bytes.fromhex('0001')
        return value
    def write8(self,a,v):
        a &= 65535
        if self.foreign_byte(a) and not 0x3000<=a<0x4000:self.record('W',8,a,v&255)
        super().write8(a,v)

memory=Memory();cpu=memory.cpu;coverage=set();decoded={}

def foreign_address(pc):
    inst=decoded.setdefault(pc,decode(rom.read,pc)) if pc not in decoded else decoded[pc]
    if inst.op in ('JMP','JSR') or pc in (0xf8c3,0xf92a,0xf9ca):return None
    if inst.mode in ('direct','extended'):a=inst.value
    elif inst.mode=='indexed_x':a=(cpu.s.x+inst.value)&65535
    elif inst.mode=='indexed_y':a=(cpu.s.y+inst.value)&65535
    else:return None
    if 0xf326<=pc<0xf377 or 0xf380<=pc<0xf3db:return a
    if 0xf64e<=pc<0xf677 and a in (0x8c,0x8d,0x89,0x93,0x90,0x91,0x92):return a
    if 0xf677<=pc<0xf715 and a in (0x39e,0x39f,0x3a0,0x3a1,0xb319,0xb31a,0xb31b):return a
    if 0xf715<=pc<0xf76a and a==0x391:return a
    if 0xf822<=pc<0xfa5b and a not in SERIAL_OWNED:return a
    return None

def execute(item):
    mode,edits=item
    memory.mem[:]=image;memory.mem[:0x4000]=bytes(0x4000)
    for a,v in edits.items():memory.mem[a]=v
    memory.events.clear();memory.writes.clear();memory.attempts=memory.cycle_counter=0;memory.foreign=None
    memory.fail_at=(memory.mem[0x91e]<<8|memory.mem[0x91f]) or memory.mem[0x907]
    cpu.s.sp=0x3ff;cpu.s.ccr=0xd0 if memory.mem[0x909] else 0xc0
    cpu.s.a,cpu.s.b,cpu.s.x,cpu.s.y=0x12,0x34,0x5678,0x9abc
    status=value=unresolved=0
    def invoke(start,stops=(0x7000,)):
        nonlocal status,unresolved
        memory.foreign=None;sp=cpu.s.sp;cpu._push16(0x7000);cpu.s.pc=start;gap_start=0
        for _ in range(30000):
            pc=cpu.s.pc
            if pc in stops:
                memory.foreign=None
                if pc!=0x7000:assert cpu._pull16()==0x7000
                assert cpu.s.sp==sp;return
            if pc==0xae85:
                if not memory.mem[0x920]:status=unresolved=1;raise Boundary
                memory.record('T',0,0xae85,memory.mem[0x921])
                if memory.mem[0x908]==24:memory.mem[0x367]=199
                status=memory.mem[0x921]
                if status:raise Boundary
                cpu.s.a,cpu.s.b,cpu.s.x,cpu.s.y=0xa5,0x5a,0xdead,0xbeef
                cpu.s.pc=0xae9d;continue
            coverage.add(pc);opcode=memory.mem[pc];memory.foreign=foreign_address(pc)
            if opcode in (0x0e,0x0f):memory.record('M',0,0,int(opcode==0x0f))
            if pc in (0xf7a5,0xf816,0xfa3e):gap_start=memory.cycle_counter
            cpu.step()
            if pc==0xf3ed:
                cycles=memory.cycle_counter-gap_start;assert cycles==11,(hex(cpu.s.pc),cycles)
                memory.record('D',0,0,cycles)
        raise AssertionError(f'Service slice budget at {cpu.s.pc:04X}')
    def irq():
        previous=cpu.s.ccr&0x10;cpu.s.ccr|=0x10
        invoke(0xf7ea,(0xf821,))
        cpu.s.ccr=(cpu.s.ccr&0xef)|previous
    def wire(split=False):
        n=memory.mem[0x919]<<8|memory.mem[0x91a]
        for i in range(n):
            if split and i+1==n:invoke(0xf781)
            memory.mem[0x302f]=memory.mem[0xa000+i];memory.mem[0x302e]=memory.mem[0xa100+i]
            irq()
        for _ in range(memory.mem[0x91c]<<8|memory.mem[0x91d]):
            control=memory.mem[0x302d]
            if control==0x26:break
            memory.mem[0x302e]=0x80 if control&0x80 else 0x40;irq()
    try:
        if mode==0:invoke(0xf326);value=cpu.s.a
        elif mode==1:invoke(0xf333)
        elif mode==2:invoke(0xf380)
        elif mode==3:invoke(0xf64e,(0xf677,))
        elif mode==4:invoke(0xf677,(0xf715,))
        elif mode==5:invoke(0xf715,(0xf739,))
        elif mode==6:invoke(0xf739,(0xf76a,))
        elif mode==7:invoke(0xf76a)
        elif mode==8:invoke(0xf64e)
        elif mode==9:invoke(0xae9d)
        elif mode==10:invoke(0xae85)
        elif mode==11:wire();invoke(0xae9d)
        elif mode==12:wire();invoke(0xf64e);invoke(0xab1a,(0xab44,))
        elif mode==13:invoke(0xf64e);invoke(0xae9d)
        elif mode==14:invoke(0xf64e);invoke(0xf781);invoke(0xf64e);invoke(0xab1a,(0xab44,))
        elif mode==15:wire();invoke(0xf781);wire();invoke(0xf64e)
        elif mode==16:invoke(0xf781);wire();invoke(0xf64e)
        elif mode==17:invoke(0xf64e);invoke(0xab1a,(0xab44,))
        elif mode==18:
            n=memory.mem[0x919]<<8|memory.mem[0x91a]
            if n==0 or n>255:status=3
            else:wire(True);invoke(0xf64e)
        elif mode==19:
            cpu.s.x=memory.mem[0x362]<<8|memory.mem[0x363];cpu.s.b=memory.mem[0x918]
            invoke(0xf86e,(0xf8e6,));value=cpu.s.a
        else:raise AssertionError(mode)
    except Failure:status=2
    except Boundary:pass
    unknown=[(a,v) for a,v in memory.writes if a not in OUTPUTS and not (0x3b0<=a<0x400 or 0xad<=a<=0xb2)]
    assert not unknown,[(hex(a),v) for a,v in unknown]
    return {'status':status,'value':value,'unresolved':unresolved,'masked':int(bool(cpu.s.ccr&0x10)),
            'state':[memory.mem[a] for a in OUTPUTS],'events':list(memory.events)}

counts={};rng=random.Random(0x31f64e)
with tempfile.TemporaryDirectory(prefix='pcm-service-rom-') as directory:
    path=Path(directory)/'bmhm.bin';path.write_bytes(image);os.environ['PCM_SERIAL_ROM']=str(path)
    counts['direct']=compare((case(m) for m in range(20)),'direct diagnostic/service and scheduled-tail slices')
    counts['format_read']=compare((case(19,custom(fmt)|word(0x923,0xa203)|{0x908:25,0x918:ordinal,0x42:session,0x364:device,0x38e:command,0x399:command})
        for fmt,ordinal,session,device,command in product([0,0x40,0x80,0xc0],[0,1,2,127,128,255],[0,3],[0xf4,0xf5,0xfe],[0,2,4])),
        'fresh descriptor-format rereads with provider mutation between flag tests')
    counts['status']=compare((case(3,{a:v for a in (0x89,0x8c,0x8d,0x90,0x91,0x92,0x93)}|
        {address:value,0x908:0}) for address,value,v in product([0x89,0x8c,0x8d,0x90,0x91,0x92,0x93],range(256),[0,255])),
        'every diagnostic-status input byte at both unrelated-input extremes')
    counts['clear']=compare((case(m,{a:(a*17+seed)&255 for a in range(0xb,0xa0)}|
        {a:(a*31+seed)&255 for a in [0x817,0x81c,0x21c,*range(0x182,0x186)]}|{0x908:action})
        for m,seed,action in product([1,2],range(256),[0,22])),
        'all clear-mask input bytes, counter holes and repeated ROM-mask sampling')
    counts['gates']=compare((case(8,{0x42:session,0x38e:command,0x399:command,0x3b:requests,0x391:flags,0x45:edges}|
        word(0x36a,expiry)) for session,command,requests,flags,edges,expiry in product(
        [0,1,2,3,0xfc],[0,1,4,255],[0,3,0x18,0x1b],[0,0x10,0x40,0x50,255],[0,0x10,0x80,0xd0,255],[0,1,65535])),
        'service admission, clear-edge priority/rearm, selector retention and cleanup gates')
    counts['wire']=compare((frame(device,payload,bad,mode=m,extra={0x367:age,0x3b:0x18,0x45:0xd0,0x391:0x40}|
        word(0x368,n)|word(0x51bb,threshold))
        for device,payload,bad,m,age,n,threshold in product([0xf4,0xf5],
        [[],[0],[1,0],[4],[4,0,0,0x50],[4,255,255,0x50,1,2,0x38,255,255,255,0x35],[10]],
        [False,True],[11,12,16,18],[0,199],[0,65534],[1,65535])),
        'accepted/rejected packet, duration/checksum-IRQ windows and real spark-service joins')
    counts['callbacks']=compare((case(m,{0x42:3,0x38e:4,0x399:4,0x39a:enable,0x39b:enable,0x391:0x50,
        0x39e:0x80,0x39f:0xa5,0x3a0:0xc0,0x3a1:0xff,0x908:action,0x920:bound,0x921:result})
        for m,enable,action,bound,result in product([4,8,9,10],[0,8,16,24],range(20,25),[0,1],[0,2,6])),
        'callback mutation, captured accumulator/selector, prefix failures and ordering')
    failure_items=[]
    for item in [case(m,{0x391:0x50,0x3b:0x1b,0x39a:0x18,0x39b:8,0x39e:0x80}) for m in range(11)]+\
                [frame(0xf4,[4,255,255,0x50],mode=18),frame(0xf5,[10],mode=11)]:
        for position in range(1,len(execute(item)['events'])+2):failure_items.append((item[0],item[1]|word(0x91e,position)))
    counts['failures']=compare(failure_items,'every foreign-access/mask/driver/prefix failure of representative paths')
    if '--quick' not in sys.argv:
        counts['gear']=compare((case(4,{0x39a:enable,0x39b:value,0x11a:(enable+value)&255,0x39e:value,
            0x39f:enable,0x3a0:value,0x3a1:enable}) for enable,value in product(range(256),repeat=2)),
            'all solenoid mask/value pairs and independent adaptive/TCC/pressure bytes')
        counts['word']=compare((case(9,word(0x368,n)|word(0x36a,n)|word(0x51bb,65535)|
            word(0x51bd,threshold)|{0x3b:flags,0x391:0x40,0x367:age})
            for n,flags,threshold,age in product([0,1,2,255,256,257,32767,32768,65534,65535],[0,0x18],[0,1,255,256,65534,65535],[0,198,199,255])),
            'duration/cooldown boundary words and retained-clear session expiry')
    history=[];retained={}
    for i in range(256):
        if i%4==3:item=case(9,retained|{0x367:199})
        else:item=frame(0xf4 if i&1 else 0xf5,([4,255,255,0x50],[],[10])[i%4],i%11==0,mode=12,extra=retained)
        history.append(item);retained.update(dict(zip(OUTPUTS,execute(item)['state'])))
    counts['history']=compare(history,'retained packet/service/clear/spark/expiry histories')
    required=set()
    for start,end in [(0xf326,0xf377),(0xf380,0xf3db),(0xf64e,0xf781),(0xae9d,0xaea4)]:
        pc=start
        while pc<end:required.add(pc);pc=decode(rom.read,pc).next_pc
    print('Missing scoped starts:',','.join(f'{a:04X}' for a in sorted(required-coverage)),flush=True)
    assert required<=coverage
    print(f'{sum(counts.values()):,} service/diagnostic comparisons; all {len(required)} scoped instruction starts match. '
          'Eight earlier AE85 callees and target ABI/device timing remain explicit.',flush=True)
