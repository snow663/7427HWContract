"""Controller boot entries and real callee joins versus recorded stock BMHM.

Data tracing retains logical operand width/order and excludes private HC11
stack traffic. Previously ported native callees contribute their actual state,
not fabricated address-space events for their native C field operations.
"""
from pathlib import Path
_parent=Path(__file__).with_name('compare_boot_system_rom.py')
exec(compile(_parent.read_text().split('\nwith tempfile.',1)[0],str(_parent),'exec'),globals())

_BootMemory=Memory
class Memory(_BootMemory):
    def read8(self,a):
        saved=self.mem[a]
        if not self.fetching and a==self.foreign and a==0x3030:
            self.mem[a]=(saved&0x7f)|(0x80 if self.polls>=self.mem[0x900] else 0)
        try:value=super().read8(a)
        finally:
            if not self.fetching and a==self.foreign and a==0x3030:self.mem[a]=saved
        if not self.fetching and a==self.foreign and 'R' in self.foreign_access:
            if a==0x3030:self.polls+=1
            if self.action==20 and a==0x3008:self.mem[a]^=0xc7
            if self.action==21 and a in (0x5b25,0x48a8):self.mem[a]=(value+37)&255
            if self.action==22 and a==0x1cc:self.mem[a]=(value+17)&255
        return value
    def write8(self,a,v):
        super().write8(a,v)
        if a==self.foreign and a==0x3030:self.polls=0
memory=Memory();cpu=HC11CPU(memory);coverage=set()
original_fetch=cpu._fetch8;cpu._fetch8=fetch
BASE=BASE|{0x900:0,0x82d:100,0x82e:100,0xa6:40,0x2f6:40,0x2f7:128,
    0x1a6:80,0x1a7:17,0x1a8:29,0x1a9:41,0x1aa:53,0x1d9:67,
    0x9c:1,0x3034:37,0x1b5:77,0x1b6:128,0x3030:1,0x2f4:160,
    0x1c4:123,0x1c8:234,0x1d1:99,0x1d3:98,0x1dd:97,0x1df:96}

def execute(item):
    mode,fail,action,masked,edits=item
    memory.mem[:]=image;memory.mem[:0x4000]=bytes(0x4000)
    for a,v in edits.items():memory.mem[a]=v
    memory.events.clear();memory.attempts=memory.polls=0;memory.fail=fail;memory.action=action;memory.foreign=None
    cpu.s.sp=0x3ff;cpu.s.ccr=0xd0 if masked else 0xc0
    cpu.s.a,cpu.s.b,cpu.s.x,cpu.s.y=0x12,0x34,0x5678,0x9abc
    starts=[0xc614,0x92f1,0x93c5,0x925e,0xb0e4,0xd14e,0x74d3,0x7393]
    cpu.s.pc=starts[mode];stop=0x7431 if mode==7 else 0x7000
    if mode!=7:cpu._push16(stop)
    status=0;native_return=None;gap_start=0
    native_entries={0xc96a,0xc9f7,0xca6b,0x92a4,0x920e,0xb1ac}
    try:
        for _ in range(20000):
            pc=cpu.s.pc
            if pc==stop:break
            if pc==native_return:native_return=None
            if native_return is None and pc in native_entries:
                native_return=memory.mem[(cpu.s.sp+1)&65535]<<8|memory.mem[(cpu.s.sp+2)&65535]
            coverage.add(pc)
            inst=decoded.setdefault(pc,decode(rom.read,pc)) if pc not in decoded else decoded[pc]
            memory.foreign=None;memory.foreign_access=''
            access=inst.access()
            if access is not None and native_return is None and pc not in (0xd16e,0xd17d,0xd180):
                memory.foreign_access=access['access']
                if inst.mode in ('direct','extended'):memory.foreign=inst.value
                elif inst.mode=='indexed_x':memory.foreign=(cpu.s.x+inst.value)&65535
                elif inst.mode=='indexed_y':memory.foreign=(cpu.s.y+inst.value)&65535
                if memory.foreign is not None and 0x3b0<=memory.foreign<0x400:memory.foreign=None
            if pc in (0x74d9,0x74e2):gap_start=memory.cycle_counter
            opcode=memory.mem[pc]
            if opcode in (0x0e,0x0f):memory.record('M',0,0,int(opcode==0x0f))
            cpu.step()
            if pc==0xf3ed:
                gap=memory.cycle_counter-gap_start;assert gap==11
                memory.record('D',0,0,gap)
        else:raise AssertionError(f'Controller boot budget at {cpu.s.pc:04X}')
    except Failure:status=2
    state=bytearray(memory.mem[:0x900]);state[0x3b0:0x400]=bytes(0x50)
    state+=memory.mem[0x3000:0x3070]+memory.mem[0x3fc0:0x3ffe]
    return {'status':status,'value':0,'state':state.hex(),'events':list(memory.events)}

with tempfile.TemporaryDirectory(prefix='pcm-boot-controllers-') as directory:
    path=Path(directory)/'bmhm.bin';path.write_bytes(image);os.environ['PCM_BOOT_ROM']=str(path)
    subprocess.run([binary,'--contracts'],check=True)
    counts={}
    counts['entries']=compare((case(mode) for mode in range(8)),'direct controller/helper entries')
    counts['baro']=compare((case(0,{0x2f4:baro,0x4e68:default},action=action)
        for baro,default,action in product([0,1,12,13,127,128,160,254,255],[0,13,255],[0,22])),
        'retained/default BARO and fresh publication coordinates')
    counts['iac']=compare((case(1,{9:flags,8:target,0x4e8f:options,0x4e90:mode,
        6:coolant,0x2a9:250,0x2ac:250,0x5098:20,0x5099:20,0x29d:250,0x29f:249,0x2a7:248,
        0x4eb3:20,0x4eb4:30,0x2a1:17,0x2ab:29})
        for flags,target,options,mode,coolant in product([0,0x10,0x20,0x30],[0,1,8,255],
        [0,1,8,255],[0,1],[0,255])),
        'warm-cell growth, live RAM bit test, fraction retention and AC overflow')
    counts['iac_boot']=compare((case(3,{4:shutdown,0x46:loss,0x2f4:baro,6:coolant,9:flags,
        7:31,10:255,0x4e8f:options,0x37:255})
        for shutdown,loss,baro,coolant,flags,options in product([0,8],[0,0x40],
        [0,255],[0,255],[0,1],[0,4])),
        'lost-memory IAC seeds, shutdown branch and kicker qualification')
    tps=[]
    for flags,high_timer,low_timer,allow,delta,latch,faults,brake in product(
            [0,1],[0,1],[0,1],[0,1],[0,10],[0,4],[0,1,2],[0,1]):
        tps.append(case(4,{0x98:flags,0x162:high_timer,0x163:low_timer,0x5d02:allow,
            0xf7:delta,0xd7:3,0x9a:latch,0x18:faults,0x9c:brake,0x5b2b:1,0x5b34:0,
            0x5b2c:128,0x5b35:0,0x5b29:255},action=21 if allow else 0))
    counts['tps']=compare(tps,'TPS diagnostic routes, decel learning and overlapping history words')
    counts['tps_publish']=compare((case(4,{0x98:1,0x5b22:value,0x101:adjust,
        0x9c:kick,0x9f:manual}) for value,adjust,kick,manual in product(
        [0,1,127,128,129,254,255],[0,1,127,128,129,255],[0,16],[0,4])),
        'signed TPS publication saturation and kickdown hysteresis')
    counts['egr']=compare((case(5,{0x400d:mode,0x3034:sample,0x900:ready,0x41:flags,
        0x1ae:demand}|word(0x1b5,zero)|word(0x1b7,filtered),action=action,masked=flags&1)
        for mode,sample,ready,flags,demand,zero,filtered,action in product(
        [0,2],[0,37,255],[0,12],[0,1],[0,1],[0,0x4d80,0xff80],[0,0xffff],[0,20,21])),
        'EGR mux/timeout, reference tracking, filtered wrap and provider rereads')
    counts['joined']=compare((case(7,{0x82e:map_sample,0x82d:coolant,6:previous,
        0x46:loss,4:shutdown,0x900:ready,0x2f4:baro,0x98:fault})
        for map_sample,coolant,previous,loss,shutdown,ready,baro,fault in product(
        [0,25,26,100,255],[0,255],[0,255],[0,64],[0,8],[0,12],[0,160],[0,1])),
        'joined MAP/coolant/IAC/O2/TPS/EGR and board-baseline boot')
    counts['edges']=compare([
        case(1,{8:255,0x4e8f:255,0x4eb5:0,0x4eb3:0}),
        *[case(4,{0x5b2b:0,0x5b2c:0,0x9a:0,0x18:0,0x9c:1,
            0xf7:100,0xd7:0,0x5b2a:0,0x2f6:250,0x5b29:increment,0x5b24:limit})
          for increment,limit in product([0,1,10],[0,249,255])],
        case(5,{0x400d:2,0x3034:0,0x48a7:255,0x48a6:255})],
        'non-overflow AC restoration, TPS increment wrap/cap and EGR minimum clamp')
    failures=[]
    for item in [case(0),case(1,{9:48,8:255,0x4e8f:255,0x4e90:1}),case(2,{9:0,10:255}),
            case(3,{4:0,0x46:64}),case(4),case(5,{0x900:12}),case(6),case(7)]:
        for fail in range(1,len(execute(item)['events'])+2):failures.append((item[0],fail,*item[2:]))
    counts['failures']=compare(failures,'every provider-operation failed prefix of selected controller paths')
    required=set()
    for start,end in [(0x7393,0x7431),(0x74d3,0x74ea),(0x925e,0x92a4),(0x92f1,0x93d0),
            (0xb0e4,0xb1ac),(0xc614,0xc668),(0xd14e,0xd1f6)]:
        pc=start
        while pc<end:required.add(pc);pc=decode(rom.read,pc).next_pc
    missing=required-coverage
    print('Uncovered controller starts:',','.join(f'{a:04X}' for a in sorted(missing)),flush=True)
    assert not missing
    print(f'{sum(counts.values()):,} controller boot comparisons; all {len(required)} new scoped instruction starts match.',flush=True)
