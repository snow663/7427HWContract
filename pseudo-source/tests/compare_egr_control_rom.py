"""Resident EGR PI/duty publication, with actual feedback and output joins."""
from pathlib import Path
_parent=Path(__file__).with_name('compare_boot_controllers_rom.py')
exec(compile(_parent.read_text().split('\nwith tempfile.',1)[0],str(_parent),'exec'),globals())

_ControllerMemory=Memory
class Memory(_ControllerMemory):
    def read8(self,a):
        value=super().read8(a)
        if not self.fetching and a==self.foreign and 'R' in self.foreign_access:
            if self.action==23 and a==0x6d:self.mem[a]^=8
            if self.action==25 and a==0x1ba:self.mem[a]=(value+17)&255
            if self.action==26 and a==0x51:self.mem[a]^=0x10
            if self.action==27 and a==0x48af:self.mem[a]=(value+37)&255
        return value
    def read16(self,a):
        value=super().read16(a)
        if not self.fetching and a==self.foreign and 'R' in self.foreign_access:
            if self.action==24 and a==0x1bc:self.mem[a]^=0x55;self.mem[a+1]^=0x55
        return value
memory=Memory();cpu=HC11CPU(memory);coverage=set()
original_fetch=cpu._fetch8;cpu._fetch8=fetch
BASE={0x400d:2,0x70:0,0x72:0,0x3b:0,0x393:0,0x6d:0xa5,0x1ae:80,0x1b9:37,
    0x1ba:0,0x1af:0,0x4f:0x80,0x51:0,0x71:0,0x900:0,0x3034:37,0x1b5:77,0x1b6:128}|word(0x1bc,0)|word(0x1be,0)

def execute(item):
    mode,fail,action,masked,edits=item
    memory.mem[:]=image;memory.mem[:0x4000]=bytes(0x4000)
    for a,value in edits.items():memory.mem[a]=value
    memory.events.clear();memory.attempts=memory.polls=0;memory.fail=fail;memory.action=action;memory.foreign=None
    cpu.s.sp=0x3ff;cpu.s.ccr=0xd0 if masked else 0xc0
    cpu.s.a,cpu.s.b,cpu.s.x,cpu.s.y=0x12,0x34,0x5678,0x9abc
    status=0
    try:
        for entry in [[0xd1f6],[0xcdf7],[0xd1f6,0xcdf7],[0xd14e,0xd1f6,0xcdf7]][mode]:
            cpu._push16(0x7000);cpu.s.pc=entry
            for _ in range(4000):
                pc=cpu.s.pc
                if pc==0x7000:break
                coverage.add(pc)
                inst=decoded.setdefault(pc,decode(rom.read,pc)) if pc not in decoded else decoded[pc]
                memory.foreign=None;memory.foreign_access=''
                access=inst.access()
                if access is not None and pc not in (0xd16e,0xd17d,0xd180):
                    memory.foreign_access=access['access']
                    if inst.mode in ('direct','extended'):memory.foreign=inst.value
                    elif inst.mode=='indexed_x':memory.foreign=(cpu.s.x+inst.value)&65535
                    elif inst.mode=='indexed_y':memory.foreign=(cpu.s.y+inst.value)&65535
                    if memory.foreign is not None and 0x3b0<=memory.foreign<0x400:memory.foreign=None
                opcode=memory.mem[pc]
                if opcode in (0x0e,0x0f):memory.record('M',0,0,int(opcode==0x0f))
                cpu.step()
            else:raise AssertionError(f'EGR budget at {cpu.s.pc:04X}')
    except Failure:status=2
    state=bytearray(memory.mem[:0x900]);state[0x3b0:0x400]=bytes(0x50)
    state+=memory.mem[0x3000:0x3070]+memory.mem[0x3fc0:0x3ffe]
    return {'status':status,'value':0,'state':state.hex(),'events':list(memory.events)}

with tempfile.TemporaryDirectory(prefix='pcm-egr-control-') as directory:
    path=Path(directory)/'bmhm.bin';path.write_bytes(image);os.environ['PCM_BOOT_ROM']=str(path)
    subprocess.run([binary,'--contracts'],check=True)
    counts={}
    counts['direct']=compare((case(mode) for mode in range(4)),'EGR control/output and real feedback joins')
    counts['gates']=compare((case(0,{0x70:faults,0x400d:mode,0x3b:service,0x393:enable,
        0x72:inhibit,0x1ae:desired}|word(0x1bc,integral)) for faults,mode,service,enable,inhibit,desired,integral
        in product([0,1,4,5],[0,2],[0,0x10],[0,2],[0,0x20],[0,37],[0,0xabab])),
        'inhibit priority, service admission, direct mode and zero-demand PID reset')
    samples=[0,1,2,63,127,128,200,254,255]
    counts['errors']=compare((case(0,{0x1ae:desired,0x1b9:position}|word(0x1bc,integral),action=action)
        for desired,position,integral,action in product(samples,samples,[0,1,0x7fff,0xfffe,0xffff],[0,23,24,25])),
        'error signs, integral saturation, fresh direction/magnitude and retained-state mutation')
    profiles=[]
    for scale,kind,desired,position,integral in product([0,16,255],[0,1,2],[1,127,255],[0,128,255],[1,65535]):
        backing={a:(255 if kind==2 else (a*17 if kind==0 else -a*17)&255) for a in range(0x48a9,0x49b8)}
        backing.update({0x48a9:scale,0x48af:scale,0x48b5:scale,0x1ae:desired,0x1b9:position})
        profiles.append(case(0,backing|word(0x1bc,integral),action=27 if kind==1 else 0))
    counts['curves']=compare(profiles,'scaled lookup index/fraction, live backing and FF00 proportional overflow')
    counts['output']=compare((case(1,{0x51:inhibit,0x4f:running,0x71:force,0x1af:duty},action=action)
        for inhibit,running,force,duty,action in product([0,0x10],[0,0x80],[0,0x80],[0,1,127,255],[0,26])),
        'literal F0 command, running duty and stopped-engine force/inhibit priority')
    counts['joins']=compare((case(3,{0x3034:sample,0x1ae:desired,0x900:ready,0x400d:mode},action=action,masked=1)
        for sample,desired,ready,mode,action in product([0,37,127,255],[0,1,128,255],[0,12],[0,2],[0,20,21,23])),
        'live feedback ADC/timeout, PI control and real hardware command joins')
    failures=[]
    for item in [case(0),case(0,{0x1ae:1,0x1b9:255}),case(0,{0x70:4}),case(0,{0x400d:0}),
            case(1,{0x4f:0,0x71:0x80}),case(3,{0x900:12})]:
        for fail in range(1,len(execute(item)['events'])+2):failures.append((item[0],fail,*item[2:]))
    counts['failures']=compare(failures,'every provider/mask failed prefix of representative EGR paths')
    history=[];retained={}
    for i in range(128):
        item=case(3,retained|{0x3034:(i*29)&255,0x1ae:(i*17)&255,0x70:0,0x4f:0x80,0x51:0})
        history.append(item);state=bytes.fromhex(execute(item)['state']);retained.update(enumerate(state[:0x900]))
        retained.update({0x3000+j:value for j,value in enumerate(state[0x900:0x970])})
        retained.update({0x3fc0+j:value for j,value in enumerate(state[0x970:])})
    counts['history']=compare(history,'retained feedback/PI/output histories without controller task stubs')
    required=set()
    for start,end in [(0xd1f6,0xd2b2),(0xcdf7,0xce10),(0xf4b6,0xf4bd)]:
        pc=start
        while pc<end:required.add(pc);pc=decode(rom.read,pc).next_pc
    missing=required-coverage
    print('Uncovered EGR starts:',','.join(f'{a:04X}' for a in sorted(missing)),flush=True)
    assert not missing
    print(f'{sum(counts.values()):,} EGR control/output comparisons; all{len(required)} new scoped starts match. '
          'Demand/flow and target device timing remain separate.',flush=True)
