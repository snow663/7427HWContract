"""Foreground self-copy, virtual-stack watermark and startup timer joins.

Logical stack bytes are observed as data. WAI/RTI and native C stack layout
remain explicit target boundaries; no ordinary ISR is delivered while masked.
"""
from pathlib import Path
_parent=Path(__file__).with_name('compare_boot_system_rom.py')
exec(compile(_parent.read_text().split('\nwith tempfile.',1)[0],str(_parent),'exec'),globals())

_ParentMemory=Memory
class Memory(_ParentMemory):
    def read16(self,a):
        value=super().read16(a)
        if not self.fetching and a==self.foreign and 'R' in self.foreign_access:
            if self.action==40 and a==0x50:self.polls=1
            if self.action==41 and a==0x800:self.mem[a]^=0xa5
            if self.action in (44,45) and a==0x2d1:
                if self.polls==0:self.mem[a:a+2]=bytes.fromhex('03b0')
                self.polls+=1
        return value
    def write8(self,a,v):
        previous=self.mem[a];super().write8(a,v)
        if a==self.foreign and a==0x3023:self.mem[a]=previous&~v
memory=Memory();cpu=HC11CPU(memory);coverage=set()
original_fetch=cpu._fetch8;cpu._fetch8=fetch
BASE={a:(17*a+29)&255 for a in [*range(0x400),*range(0x800,0x900)]}
BASE|={0x51:0,4:0,0x3023:0xff}|word(0x29b,0x8f0)|word(0x2d1,0)|word(0x300e,65530)

def execute(item):
    mode,fail,action,masked,edits=item
    memory.mem[:]=image;memory.mem[:0x4000]=bytes(0x4000)
    for a,v in edits.items():memory.mem[a]=v
    memory.events.clear();memory.attempts=memory.polls=0;memory.fail=fail;memory.action=action;memory.foreign=None
    cpu.s.sp=0x3ff;cpu.s.ccr=0xd0 if masked else 0xc0
    cpu.s.a,cpu.s.b,cpu.s.x,cpu.s.y=0x12,0x34,0x5678,0x9abc
    status=0
    def invoke(start,stop):
        cpu.s.pc=start
        for _ in range(20000):
            pc=cpu.s.pc
            if pc==stop:return
            coverage.add(pc)
            if pc==0x7b5a:
                memory.record('T',0,pc,0);cpu.s.pc=0x7b69;continue
            inst=decoded.setdefault(pc,decode(rom.read,pc)) if pc not in decoded else decoded[pc]
            memory.foreign=None;memory.foreign_access=''
            access=inst.access()
            native=(0xf28e<=pc<0xf2aa or 0x7431<=pc<0x7459 or 0x7b52<=pc<0x7b6d)
            # COP writes are provider operations inside the otherwise native
            # existing reset-serial stage. F28E's call frame is ABI-private.
            if access is not None and (not native or pc in (0x7443,0x7448)):
                memory.foreign_access=access['access']
                if inst.mode in ('direct','extended'):memory.foreign=inst.value
                elif inst.mode=='indexed_x':memory.foreign=(cpu.s.x+inst.value)&65535
                elif inst.mode=='indexed_y':memory.foreign=(cpu.s.y+inst.value)&65535
            opcode=memory.mem[pc]
            if opcode in (0x0e,0x0f):memory.record('M',0,0,int(opcode==0x0f))
            cpu.step()
            if opcode==0x0e:
                if action==40 and memory.polls==1:memory.mem[0x50]|=0x20;memory.polls=2
                if action==42 and memory.mem[0x29b:0x29d]==bytes.fromhex('0900'):
                    memory.mem[0x29c]=0xa5;memory.mem[0x51]^=0x80
                if action==43:
                    if memory.polls==0:memory.mem[0x29b:0x29d]=bytes.fromhex('0400')
                    memory.polls+=1
        raise AssertionError(f'Foreground budget at {cpu.s.pc:04X}')
    try:
        if mode==0:invoke(0x746c,0x74b3)
        elif mode==1:invoke(0x74b4,0x74d0)
        elif mode==2:invoke(0x746c,0x74d0);status=9
        elif mode==3:invoke(0x7459,0x746c)
        elif mode==4:
            # Independent callable-slot replay needs a synthetic RTS sentinel.
            # Remove that test frame before supplying the foreground's actual
            # logical-stack snapshot; the sentinel is not a resident writer.
            saved=bytes(memory.mem[0x3fe:0x400])
            cpu._push16(0x7000);invoke(0x7b5a,0x7000)
            cpu._push16(0x7000);invoke(0x7b52,0x7000)
            memory.mem[0x3fe:0x400]=saved
            invoke(0x746c,0x74d0);status=9
        elif mode==5:invoke(0x7431,0x74d0);status=9
    except Failure:status=2
    state=bytearray(memory.mem[:0x900])
    if mode>=4:state[0x3f0:0x400]=bytes(16) # Prior callee frame bytes are ABI-private.
    state+=memory.mem[0x3000:0x3070]+memory.mem[0x3fc0:0x3ffe]
    return {'status':status,'value':0,'state':state.hex(),'events':list(memory.events)}

with tempfile.TemporaryDirectory(prefix='pcm-background-') as directory:
    path=Path(directory)/'bmhm.bin';path.write_bytes(image);os.environ['PCM_BOOT_ROM']=str(path)
    subprocess.run([binary,'--contracts'],check=True)
    counts={}
    counts['direct']=compare((case(mode) for mode in [0,1,2,3,5]),'foreground/watermark/timer/direct startup-tail entries')
    cursors=[*range(0,0x401,16),*range(0x800,0x901,16)]
    counts['cursor']=compare((case(0,word(0x29b,cursor)|{0x51:flags},masked=masked)
        for cursor,flags,masked in product(cursors,[0,4,255],[0,1])),
        'all resident cursor starts, RAM gap, terminal byte clear and request states',8)
    zero_stack={a:0 for a in range(0x3b0,0x400)}
    counts['watermark']=compare((case(1,zero_stack|word(0x2d1,previous)|{first:value},action=action)
        for first,previous,value,action in product([0x3b0,0x3b1,0x3c0,0x3fe,0x3ff],
        [0,0x3b0,0x3bf,0x3ff,0xffff],[0,1,255],[0,44,45])),
        'stack stop/bounds, zero/nonzero minimum and fresh comparison-word reads')
    counts['stack_bytes']=compare((case(1,zero_stack|{first:0xa5}) for first in range(0x3b0,0x400)),
        'every first-used byte of the logical stack window')
    counts['callbacks']=compare((case(2,word(0x29b,cursor)|{0x51:4,0x50:0},action=action)
        for cursor,action in product([0,0x3f0,0x400,0x800,0x8f0,0x900],[40,41,42,43])),
        'per-block IRQ delivery, captured-word rewrite and cursor/flag mutations',8)
    counts['timers']=compare((case(3,word(0x300e,timer)|{0x3023:flags})
        for timer,flags in product([0,1,65527,65528,65535],[0,1,32,255])),
        'startup TFLG1 acknowledgment before wrapped first timer arm')
    counts['slots']=compare((case(4,word(0x29b,cursor)|{0x51:flags,4:old},masked=masked)
        for cursor,flags,old,masked in product([0x3f0,0x8f0,0x900],[0,4,255],[0,255],[0,1])),
        'slot-F request, slot-E late latch and canonical foreground completion')
    failures=[]
    for item in [case(0,{0x51:4}|word(0x29b,0x8f0)),case(1,zero_stack|word(0x2d1,0x3ff)),
            case(2,{0x51:0}),case(3),case(4,word(0x29b,0x900)),case(5)]:
        for fail in range(1,len(execute(item)['events'])+2):failures.append((item[0],fail,*item[2:]))
    counts['failures']=compare(failures,'every provider/mask failed prefix of selected foreground paths')
    counts['full_prefix']=compare((case(0,{0x51:4}|word(0x29b,0),fail=fail)
        for fail in [1,2,3,4,19,20,21,100,1000,1500,1525]),
        'selected early/middle/late failed prefixes of a complete refresh')
    required=set();pc=0x7459
    while pc<0x74d3:required.add(pc);pc=decode(rom.read,pc).next_pc
    excluded={0x74d0,0x74d1} # WAI/frame and the later resume branch are target boundaries.
    missing=required-coverage-excluded
    print('Uncovered foreground starts:',','.join(f'{a:04X}' for a in sorted(missing)),flush=True)
    assert not missing
    print(f'{sum(counts.values()):,} foreground comparisons; all{len(required-excluded)} resident starts match. '
          'Target WAI/frame/resume remain explicit.',flush=True)
