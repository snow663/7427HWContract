"""Resident7D4B controller, ignition, governor and scheduled tail versus BMHM.

Previously checked native slices contribute real state and I/O. Newly ported
logical routines also compare RAM/calibration operand transactions.
"""
from pathlib import Path
_parent=Path(__file__).with_name('compare_boot_system_rom.py')
exec(compile(_parent.read_text().split('\nwith tempfile.',1)[0],str(_parent),'exec'),globals())

class ModuleBoundary(Exception):pass
_ParentMemory=Memory
class Memory(_ParentMemory):
    def read8(self,a):
        saved=self.mem[a]
        if not self.fetching and a==self.foreign and a==0x3030:
            ready=self.mem[0x900 if self.control==7 else 0x901 if self.control==0x14 else 0x902]
            self.mem[a]=(saved&0x7f)|(0x80 if self.polls>=ready else 0)
        try:value=super().read8(a)
        finally:
            if not self.fetching and a==self.foreign and a==0x3030:self.mem[a]=saved
        if not self.fetching and a==self.foreign and 'R' in self.foreign_access:
            if self.action==30 and a==0x75:self.mem[a]^=0xd7
            if self.action==31 and a in (0x50e2,0x50e3):self.mem[a]=(value+17)&255
            if self.action==33 and a==0x28e:self.mem[a]=(value+17)&255
            if self.action==36 and a==0x29a:self.mem[a]=(value+17)&255
            if self.action==6 and a==0x3008:self.mem[a]^=0xc7
            if a==0x3030:self.polls+=1
        return value
    def write8(self,a,value):
        old=self.mem[a];super().write8(a,value)
        if a==0x3023:self.mem[a]=old&~value
        if a==self.foreign and a==0x3030:self.control=value;self.polls=0
    def read16(self,a):
        value=super().read16(a)
        if not self.fetching and a==self.foreign and 'R' in self.foreign_access:
            if self.action==32 and 0x50e8<=a<0x5200:self.mem[a]=(self.mem[a]+11)&255
            if self.action==35 and a==0x27e:self.mem[a:a+2]=bytes.fromhex('dead')
            if self.action==37 and a==0x3fca:self.mem[2]^=4
            if self.action==5 and a==0x3fca:
                self.mem[0x44]|=0x10;self.mem[0x50]|=1;self.mem[a:a+2]=bytes.fromhex('abcd')
            if self.action==10 and a==0x3fc0:
                self.mem[0x24e:0x250]=bytes.fromhex('0040');self.mem[0x259:0x25c]=bytes.fromhex('feff80')
        return value
    def write16(self,a,value):
        super().write16(a,value)
        if a==self.foreign:
            if self.action==34 and a==0x28a:self.mem[a]^=0x55
            if self.action==12 and a==0x3fce and value==0:self.mem[0x3e]^=0x10

memory=Memory();cpu=HC11CPU(memory);coverage=set();original_fetch=cpu._fetch8;cpu._fetch8=fetch
BASE={0x44:0,0x4f:0x90,0x51:0,0x86:0,0x3d:2,0x3e:0,0x3f:0x80,0x6f:0,
    0x06:160,0x62:80,0x63:80,0x65:80,0x55:130,0xa7:130,0x1c0:100,0x1c6:100,
    0x1cc:160,0x1ce:160,0x1cf:100,0x1d9:80,0x1a6:80,0x1d5:128,0x24a:147,
    0x248:128,0x283:160,0x4b:0,0x50:0,0x89:0,0x47:0,0x400b:0,
    0x2f6:1,0x2f7:0,0x244:255,0x246:5,0x400f:0x10,0x920:0,0x913:0,0x923:0,
    0x299:80,0x28d:0,0x1bb:128,0x3ffc:0xb9,0x3ffd:0x3a,2:1,0x811:39}
BASE=BASE|word(0x27e,0)|word(0xfd,500)|word(0x28e,0x6000)|word(0x286,0x8000)|word(0x288,0x4000)
BASE=BASE|word(0x1e8,0x2000)|word(0x5f,0x2000)|word(0x3fc0,0x2000)|word(0x24e,4096)|word(0x851,1000)
ENTRIES=[[(0x7d4b,0x7db6)],[(0x8eb4,0x7000)],[(0x90d3,0x7000)],
    [(0x7db6,0x7e4f)],[(0x852c,0x7000)],[(0x7d4b,0x7000)],
    [(0x7d4b,0x7000),(0x751b,0x77c6)],[(0x852c,0x7000),(0x7d4b,0x7000)],[(0x7db6,0x852c)]]
NATIVE_INLINE={0x7db6:0x7e36,0x7e40:0x852c}
NATIVE_CALLEES={0x863d,0x8613,0x891e,0xd4a3}
NATIVE_ROOTS={0x751b};NATIVE_GATES={0x852c,0x853b}
IGNORED_STATE=[(0x3b0,0x400),(0xad,0xb3)];VALUE_MODES=set();ENTRY_WORD_ARGUMENT={}

def execute(item):
    mode,fail,action,masked,edits=item
    memory.mem[:]=image;memory.mem[:0x4000]=bytes(0x4000)
    for a,value in edits.items():memory.mem[a]=value
    memory.events.clear();memory.attempts=memory.polls=memory.control=0;memory.fail=fail;memory.action=action;memory.foreign=None
    cpu.s.sp=0x3ff;cpu.s.ccr=0xd0 if masked else 0xc0
    cpu.s.a,cpu.s.b,cpu.s.x,cpu.s.y=0x12,0x34,0x5678,0x9abc
    status=unresolved=0;native_stop=None;gap_start=delay_start=0
    try:
        for entry,stop in ENTRIES[mode]:
            cpu.s.pc=entry;native_stop=stop if entry in NATIVE_ROOTS else None
            if entry in ENTRY_WORD_ARGUMENT:
                a=ENTRY_WORD_ARGUMENT[entry];cpu.s.x=memory.mem[a]<<8|memory.mem[a+1]
            if stop in (0x7000,0x77c6):cpu._push16(0x7000)
            for _ in range(20000):
                pc=cpu.s.pc
                if pc==stop:break
                if pc==0x7d8c:status=13;raise ModuleBoundary
                if pc==native_stop:native_stop=None
                if native_stop is None and pc in NATIVE_INLINE:
                    native_stop=NATIVE_INLINE[pc]
                    if native_stop is None:native_stop=memory.mem[(cpu.s.sp+1)&65535]<<8|memory.mem[(cpu.s.sp+2)&65535]
                if native_stop is None and pc in NATIVE_CALLEES:
                    native_stop=memory.mem[(cpu.s.sp+1)&65535]<<8|memory.mem[(cpu.s.sp+2)&65535]
                if pc in (0x1809,0x1800):
                    governor=pc==0x1809
                    if not memory.mem[0x920 if governor else 0x913]:
                        status=1;unresolved=2 if governor else 1;raise ModuleBoundary
                    memory.record('T',0,pc,cpu.s.a if governor else 0)
                    if governor:
                        cpu.s.a=memory.mem[0x921];cpu.s.ccr=(cpu.s.ccr&0xfe)|(memory.mem[0x922]&1)
                        status=memory.mem[0x923]
                    else:memory.mem[0x24a]=memory.mem[0x914];status=memory.mem[0x915]
                    if status:raise ModuleBoundary
                    cpu.s.pc=cpu._pull16();continue
                coverage.add(pc);inst=decoded.setdefault(pc,decode(rom.read,pc)) if pc not in decoded else decoded[pc]
                memory.foreign=None;memory.foreign_access='';access=inst.access()
                if access is not None and pc not in NATIVE_GATES:
                    if inst.mode in ('direct','extended'):address=inst.value
                    elif inst.mode=='indexed_x':address=(cpu.s.x+inst.value)&65535
                    elif inst.mode=='indexed_y':address=(cpu.s.y+inst.value)&65535
                    else:address=None
                    if address is not None and not 0x3b0<=address<0x400 and (native_stop is None or 0x3000<=address<0x4000):
                        memory.foreign=address;memory.foreign_access=access['access']
                opcode=memory.mem[pc]
                if opcode in (0x0e,0x0f):memory.record('M',0,0,int(opcode==0x0f))
                if pc==0x8429:gap_start=memory.cycle_counter
                if pc==0x7524:delay_start=memory.cycle_counter
                cpu.step()
                if pc==0xf3ed and cpu.s.pc==0x842c:
                    cycles=memory.cycle_counter-gap_start;assert cycles==11;memory.record('D',0,0,cycles)
                    if action==9:
                        memory.mem[0x3fc0:0x3fc2]=bytes.fromhex('0001');memory.mem[0x24e:0x250]=bytes.fromhex('ffff')
                        memory.mem[0x259:0x25c]=bytes.fromhex('ffffff')
                if pc==0x7527:
                    cycles=memory.cycle_counter-delay_start;assert cycles==33;memory.record('D',0,0,cycles)
                if opcode==0x0e and action==3:memory.mem[0x55]=99;memory.mem[0xa7]=255;memory.mem[0x3034]=7
                if opcode==0x0f and action==4:memory.mem[0x82e]=33;memory.mem[0x50]|=1
                if opcode==0x0f and action==7:
                    memory.mem[0x3f]=(memory.mem[0x3f]&0x40)|0x6f
                    memory.mem[0x66]=255;memory.mem[0x63]=0;memory.mem[0x858]=255;memory.mem[0x36]|=128
                if opcode==0x0e and action==8:
                    memory.mem[0x2ca]=0;memory.mem[0x2c8]=255;memory.mem[0x27d]=memory.mem[0x270]=0
                    memory.mem[0x3f]=(memory.mem[0x3f]&0xf0)|0x2a
                if opcode==0x0f and action==11:
                    memory.mem[0x82a]=255;memory.mem[0x51]|=1;memory.mem[0x24e:0x250]=bytes.fromhex('1234')
                if opcode==0x0e and action==11:
                    memory.mem[0x254:0x256]=bytes(2);memory.mem[0x82a]=255;memory.mem[0x24e:0x250]=bytes.fromhex('4000')
                if opcode==0x0e and action==38:memory.mem[2]^=6
            else:raise AssertionError(f'Fuel controller budget at {cpu.s.pc:04X}')
    except Failure:status=2
    except ModuleBoundary:pass
    state=bytearray(memory.mem[:0x900])
    for start,end in IGNORED_STATE:state[start:end]=bytes(end-start)
    state+=memory.mem[0x3000:0x3070]+memory.mem[0x3fc0:0x3ffe]
    return {'status':status,'value':cpu.s.a if mode in VALUE_MODES and status==0 else 0,'unresolved':unresolved,'masked':int(bool(cpu.s.ccr&0x10)),
        'state':state.hex(),'events':list(memory.events)}

with tempfile.TemporaryDirectory(prefix='pcm-fuel-controller-') as directory:
    path=Path(directory)/'bmhm.bin';path.write_bytes(image);os.environ['PCM_FUEL_CONTROLLER_ROM']=str(path)
    subprocess.run([binary,'--contracts'],check=True);counts={}
    counts['entries']=compare((case(mode) for mode in range(9)),'resident ignition/governor/input/tail/full-controller and REF entries')
    counts['ignition']=compare((case(0,{0x44:inhibit,0x51:old,0x4f:running}|word(0x27e,count)|word(0x4009,limit),action=action)
        for inhibit,old,running,count,limit,action in product([0,16],[0,8],[0,0x90],
        [0,1,7,8,9,255,256,65535],[0,8,256,65535],[0,35])),
        'captured ignition count, cleanup/restart, wrap and pre-TAP STOP boundary')
    counts['clears']=compare((case(0,{address:flags,0x44:16}|word(0x27e,8)|word(0x4009,256))
        for address,flags in product([4,0x19,0x4f,0x51,0x86],range(256))),
        'all shared flag bytes in ordered shutdown RMW clears')
    counts['governor_gates']=compare((case(1,{0x400f:option,0x4f:running,0x6f:faults})
        for option,running,faults in product([0,1],[0,128],range(256))),
        'governor option, engine admission and all partial inhibit masks')
    counts['modes']=compare((case(1,{0x400f:1,0x75:flags,0x50d8:96,0x50d9:90,0x50da:50,
        0x50db:10,0x288:flags&1,0x28e:rpm,0x284:speed,0x285:fraction})
        for flags,rpm,speed,fraction in product(range(256),[95,96,97],[49,50,51],[0,255])),
        'all retained governor mode bytes across RPM/VSS entry, hysteresis and release')
    counts['anticipation']=compare((case(1,{0x400f:1,0x50d8:96,0x28e:95,0x50da:0,
        0x75:flags,0x28d:derivative,6:coolant})
        for flags,derivative,coolant in product([0,2,0x10,0x12],range(256),[0,128,255])),
        'signed derivative including80, anticipation seed/reduction and recovery')
    samples=[0,1,2,63,127,128,200,254,255]
    counts['actuator']=compare((case(2,{0x299:target,0x1d9:tps}|word(0x288,integral),action=action)
        for target,tps,integral,action in product(samples,samples,[0,1,0x7fff,0xfffe,0xffff],[0,32,36])),
        'actuator sign, integral/P bounds, live error/curve reads and target-FF timing')
    counts['overrides']=compare((case(2,{0x51:inhibit,0x3b:service,0x393:enabled,0x394:output})
        for inhibit,service,enabled,output in product([0,16],[0,16],[0,1,2,3],[0,77,255])),
        'literal1F hardware command and voltage/service override priority')
    import random
    rng=random.Random(0x317d4b);profiles=[]
    for i in range(1024):
        edits={a:rng.randrange(256) for a in [0x75,0x1d9,*range(0x284,0x29b),*range(0x50d8,0x5113)]}
        edits.update({0x400f:1,0x4f:0x80,0x6f:0,0x86:0})
        profiles.append(case(1+i%2,edits,action=[0,30,31,32,33,34,36][i%7]))
    counts['profiles']=compare(profiles,'raw governor profiles, retained fractions, live flags and fresh floor/step backing')
    counts['caps']=compare([case(1,{0x400f:1,0x50d8:96,0x28e:95,0x50da:0,0x75:2,0x28d:127}|
        {a:255 for a in range(0x50fa,0x5100)}),case(5,{0x4f:0,0x1cc:0})],
        'anticipation reduction product overflow and below-offset crank BARO floor')
    counts['tail']=compare((case(4,{2:phase,0xa7:battery,0x44:16},action=action)
        for phase,battery,action in product(range(160),[0,39,40,89,90,255],[0,37])),
        'every phase and battery boundary, including fresh post-capture phase admission')
    counts['hooks']=compare((case(1,{0x400f:1,0x86:64,0x920:present,0x921:value,0x922:carry,0x923:status})
        for present,value,carry,status in product([0,1],[0,77,255],[0,1],[0,4])),
        'optional1809 missing/error/carry and returned-A early target publication')
    joined=[]
    for mode,phase,running,tps,option,action in product([3,5,6,7,8],[1,3,5,7,15,31,159],
            [0,0x90],[0,80,255],[0x10,0x11],[0,37,38]):
        joined.append(case(mode,{2:phase,0x4f:running,0x1a6:tps,0x400f:option},action=action))
    counts['joined']=compare(joined,'real input/calculation/tail, enabled governor, crank/running and REF joins')
    failures=[]
    selected=[case(0,{0x44:16}|word(0x27e,8)|word(0x4009,8)),case(0,{0x51:8}),
        case(1,{0x400f:1,0x28e:120}),case(1,{0x400f:1,0x50da:50,0x284:51}),
        case(1,{0x400f:1,0x50da:0,0x28e:80,0x75:2,0x28d:1}),
        case(1,{0x400f:1,0x86:64,0x920:1,0x922:1,0x921:77}),
        case(2,{0x299:1,0x1d9:255}),case(2,{0x299:255,0x1d9:1}),
        case(3,{0x400f:1}),case(4,{2:3,0x44:16}),case(4,{2:7}),
        case(5),case(5,{0x4f:0}),case(6),case(5,{0x400b:4,0x3d:0x82})]
    for item in selected:
        for fail in range(1,len(execute(item)['events'])+2):failures.append((item[0],fail,*item[2:]))
    counts['failures']=compare(failures,'each provider/mask/module failure prefix across ignition, governor and complete fuel paths')
    history=[];retained={}
    for i in range(128):
        item=case(5+i%2,retained|{2:(1+2*i)%160,0x1a6:(i*17)&255,0x4f:0x90,
            0x44:0,0x400f:0x10+(i&1),0x28e:80+i%48,0x28d:i&255},action=0)
        history.append(item);state=bytes.fromhex(execute(item)['state']);retained.update(enumerate(state[:0x900]))
        retained.update({0x3000+j:value for j,value in enumerate(state[0x900:0x970])})
        retained.update({0x3fc0+j:value for j,value in enumerate(state[0x970:])})
    counts['history']=compare(history,'retained controller/REF histories with real governor and injector publication')
    required=set()
    for start,end in [(0x7d4b,0x7db6),(0x7e36,0x7e40),(0x852c,0x8548),(0x8eb4,0x9167),
            (0xf499,0xf4a4),(0xf4b6,0xf4de),(0xf550,0xf564)]:
        pc=start
        while pc<end:required.add(pc);pc=decode(rom.read,pc).next_pc
    required-={0x7d8c,0x7d8d,0x7d8e}
    missing=required-coverage;print('Uncovered fuel-controller starts:',','.join(f'{a:04X}' for a in sorted(missing)),flush=True)
    assert not missing
    print(f'{sum(counts.values()):,} fuel-controller comparisons; all {len(required)} new scoped starts match. '
          'TAP/STOP, optional1809/1800 implementations and target timing remain separate.',flush=True)
