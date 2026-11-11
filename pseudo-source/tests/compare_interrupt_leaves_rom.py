"""Resident reset/trap/fallback/XIRQ leaves, including factory REF completion.

Normal hardware frame entry/RTI and terminal reset/loop transfers stay explicit.
XIRQ exposes its supplied saved-CCR byte as an ordered logical data access.
"""
from pathlib import Path
_parent=Path(__file__).with_name('compare_boot_system_rom.py')
exec(compile(_parent.read_text().split('\nwith tempfile.',1)[0],str(_parent),'exec'),globals())

_ParentMemory=Memory
class Memory(_ParentMemory):
    def read8(self,a):
        value=super().read8(a)
        if not self.fetching and a==self.foreign and 'R' in self.foreign_access:
            frame=self.mem[0x900]<<8|self.mem[0x901]
            if self.action==50 and a==0:self.mem[frame]=0x80
            if self.action==51 and a==frame:self.mem[frame]=0xaa
            if self.action==52 and a==0:self.mem[0]^=0x55
        return value
    def write8(self,a,v):
        previous=self.mem[a];super().write8(a,v)
        if a==self.foreign and a in (0x3023,0x3025):self.mem[a]=previous&~v
memory=Memory();cpu=HC11CPU(memory);coverage=set()
original_fetch=cpu._fetch8;cpu._fetch8=fetch
BASE={0:0,0x44:1,0x3022:0xff,0x3023:0xff,0x3024:0xff,0x3025:0xff,0x15:0,
    0x3b0:0,0x3b1:0xa5,0x3f7:0,0x3f8:0x5a}|word(0x900,0x3b0)

def execute(item):
    mode,fail,action,masked,edits=item
    memory.mem[:]=image;memory.mem[:0x4000]=bytes(0x4000)
    for a,v in edits.items():memory.mem[a]=v
    memory.events.clear();memory.attempts=0;memory.fail=fail;memory.action=action;memory.foreign=None
    frame=memory.mem[0x900]<<8|memory.mem[0x901]
    cpu.s.sp=(frame-1)&65535;cpu.s.ccr=0xd0 if masked else 0xc0
    cpu.s.a,cpu.s.b,cpu.s.x,cpu.s.y=0x12,0x34,0x5678,0x9abc
    starts=[0xfc04,0xfc1a,0xfc1f,0xfc24,0xfc29,0xfc09,0xfc11,0xfc2f,0xfc3a,0xfc44,0x74ea,0xfc29,0xfc1f]
    stops=[0xfc07,0xfc1d,0x7100,0xfc27,0x7100,0xfc10,0xfc19,0xfc39,0xfc44,0xfc44,0xfc19,0x7100,0x7100]
    status=0
    def invoke(start,stop):
        cpu.s.pc=start
        for _ in range(10000):
            pc=cpu.s.pc
            if pc==stop:return
            coverage.add(pc)
            inst=decoded.setdefault(pc,decode(rom.read,pc)) if pc not in decoded else decoded[pc]
            memory.foreign=None;memory.foreign_access=''
            access=inst.access()
            if access is not None and not 0xf280<=pc<0xf28e and pc!=0x74ea:
                memory.foreign_access=access['access']
                if inst.mode in ('direct','extended'):memory.foreign=inst.value
                elif inst.mode=='indexed_x':memory.foreign=(cpu.s.x+inst.value)&65535
                elif inst.mode=='indexed_y':memory.foreign=(cpu.s.y+inst.value)&65535
            if pc==0xfc0c:memory.foreign=frame;memory.foreign_access='R'
            if pc==0xfc0f:memory.foreign=frame;memory.foreign_access='W'
            cpu.step()
        raise AssertionError(f'Interrupt leaf budget at {cpu.s.pc:04X}')
    try:
        invoke(starts[mode],stops[mode])
        if mode in (0,1,3):status=10
        elif mode in (2,4):status=11
        elif mode>=11:
            # The target reset-entry boundary remains between these resident
            # bodies. Test the later retained-validation cause preservation.
            cpu.s.sp=0x3ff;invoke(0x720c,0x723f)
    except Failure:status=2
    state=bytearray(memory.mem[:0x900])
    if mode>=11:state[0x3f0:0x400]=bytes(16)
    state+=memory.mem[0x3000:0x3070]+memory.mem[0x3fc0:0x3ffe]
    return {'status':status,'value':0,'state':state.hex(),'events':list(memory.events)}

with tempfile.TemporaryDirectory(prefix='pcm-interrupt-leaves-') as directory:
    path=Path(directory)/'bmhm.bin';path.write_bytes(image);os.environ['PCM_BOOT_ROM']=str(path)
    subprocess.run([binary,'--contracts'],check=True)
    counts={}
    counts['direct']=compare((case(mode) for mode in range(13)),'direct leaf and factory-REF/retained-validation joins')
    counts['causes']=compare((case(mode,{0:flags},masked=flags&1)
        for mode,flags in product([0,1,2,3,4,6,10],range(256))),
        'every cause-byte value with shared timer bit and both incoming I states')
    counts['xirq']=compare((case(5,word(0x900,frame)|{frame:ccr,0:flags},action=action,masked=masked)
        for frame,ccr,flags,action,masked in product([0x3b0,0x3f7],range(256),[0,255],[0,50,51],[0,1])),
        'every saved CCR byte, supplied frames, ordered mutation and mask-bit preservation')
    counts['fallback']=compare((case(mode,{0x3022:mask,0x3023:flags,0x3024:mask,0x3025:flags},masked=masked)
        for mode,mask,flags,masked in product([6,7,8,9],[0,1,0x5f,0xa0,255],[0,1,0x5f,0xa0,255],[0,1])),
        'fallback masks, literal W1C acknowledgments and empty SPI body')
    counts['retained']=compare((case(mode,{0:flags,0x15:checksum})
        for mode,flags,checksum in product([11,12],[0,1,0x40,0xff],[0,1])),
        'reset cause preservation or loss through existing retained-memory validation')
    counts['mutations']=compare((case(mode,{0:flags},action=52) for mode,flags in product(range(7),[0,1,0x55,255])),
        'captured cause-byte read/modify/write under supplied provider mutation')
    failures=[]
    for mode in range(13):
        item=case(mode)
        for fail in range(1,len(execute(item)['events'])+2):failures.append((item[0],fail,*item[2:]))
    failures.extend(case(11,{0x15:1},fail=fail) for fail in [1,2,3,12,20,100,200])
    counts['failures']=compare(failures,'every provider-operation failure of direct leaf paths plus retained-loss prefixes')
    required=set();pc=0xfc04
    while pc<0xfc45:required.add(pc);pc=decode(rom.read,pc).next_pc
    # Terminal loops and RTI are target control/ABI boundaries. Empty SPI is
    # checked as zero transactions; its only instruction is the delegated RTI.
    excluded={0xfc07,0xfc10,0xfc19,0xfc1d,0xfc27,0xfc39,0xfc44}
    assert required-coverage-excluded==set(),sorted(required-coverage-excluded)
    assert [(a,rom.word(a)) for a in [0xfff6,0xfff8,0xfffa,0xfffc,0xfffe]]==[
        (0xfff6,0xfc04),(0xfff8,0xfc1a),(0xfffa,0xfc1f),(0xfffc,0xfc24),(0xfffe,0xfc29)]
    assert rom.word(0xfff4)==0xfc09 and rom.word(0xffd8)==0xfc44
    assert all(rom.word(a)==0xfc2f for a in [0xffe6,0xffea,0xffec,0xffee,0xfff0])
    assert all(rom.word(a)==0xfc3a for a in [0xffda,0xffdc,0xffde])
    print(f'{sum(counts.values()):,} interrupt-leaf comparisons; all{len(required-excluded)} resident starts match. '
          'Vector words verified; target frame/RTI/reset/halt remain explicit.',flush=True)
