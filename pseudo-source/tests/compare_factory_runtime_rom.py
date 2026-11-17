"""Recurring factory qualification/upload/callback/output paths versus BMHM.

FA5B's abandoned-frame precondition and FAA5's unknown target are explicit
supplied test bindings. Trap stops before SWI; wait stops at FBD4. No physical
interrupt or arbitrary supplied callback implementation is inferred.
"""
from pathlib import Path
_parent=Path(__file__).with_name('compare_boot_system_rom.py')
exec(compile(_parent.read_text().split('\nwith tempfile.',1)[0],str(_parent),'exec'),globals())

SERIAL_OWNED={0x3b,0x42,0x45,0x38e,0x399}|set(range(0x360,0x38e))
_ParentMemory=Memory
class Memory(_ParentMemory):
    def read8(self,a):
        saved=self.mem[a];operand=not self.fetching and a==self.foreign and 'R' in self.foreign_access
        if operand and a==0x3030:
            self.mem[a]=(saved&0x7f)|(0x80 if self.polls>=self.mem[0x901 if saved==3 else 0x900] else 0)
        if operand and a==0x3031:self.mem[a]=self.mem[0x903 if self.mem[0x3030]==3 else 0x902]
        try:value=super().read8(a)
        finally:
            if operand and a in (0x3030,0x3031):self.mem[a]=saved
        if operand:
            if a==0x3030:self.polls+=1
            if self.action==30 and a==0x3008:self.mem[a]^=0xc7
            if self.action==31 and a==0x3066:self.mem[0x364]=2
            if self.action==33 and a==0x392:self.mem[0x393]^=255
        return value
    def write8(self,a,v):
        previous=self.mem[a];super().write8(a,v)
        if a==self.foreign and a==0x3030:self.polls=0
        if a==self.foreign and a==0x3023:self.mem[a]=previous&~v
memory=Memory();cpu=HC11CPU(memory);coverage=set()
original_fetch=cpu._fetch8;cpu._fetch8=fetch
BASE={0x44:1,0x50:8,0x900:0,0x901:0,0x902:40,0x903:27,0x904:0,
    0x364:0,0x3008:0xa5,0x3060:0xff,0x3062:0xff,0x3064:0x80,0x3066:0x55,
    0x3023:0xff,0x302e:0x80,1:0,2:0}|word(0x38e,0x1000)|word(0x3ffc,0xb93a)|word(0x301a,65530)
BASE|={a:(a*17+29)&255 for a in range(0x390,0x3b0)}

def execute(item):
    mode,fail,action,masked,edits=item
    memory.mem[:]=image;memory.mem[:0x4000]=bytes(0x4000)
    for a,v in edits.items():memory.mem[a]=v
    memory.events.clear();memory.attempts=memory.polls=0;memory.fail=fail;memory.action=action;memory.foreign=None
    cpu.s.sp=0x3ff;cpu.s.ccr=0xd0 if masked else 0xc0
    cpu.s.a,cpu.s.b,cpu.s.x,cpu.s.y=0x12,0x34,0x5678,0x9abc
    starts=[0xfa5b,0x793d,0xfaad,0xfa9f,0xfaca,0xf9be]
    cpu.s.pc=starts[mode];status=0;gap_start=0
    if mode==4:cpu.s.b=memory.mem[0x904]
    if mode==5:cpu.s.x=memory.mem[0x362]<<8|memory.mem[0x363];cpu._push16(0x7000)
    try:
        for _ in range(20000):
            pc=cpu.s.pc
            if mode==2 and pc==0xfac7:break
            if mode==3 and pc==0xfaa7:break
            if pc==0xfa82:status=6;break
            if pc==0xfbd4:status=8;break
            if mode==5 and pc==0x7000:cpu.s.pc=0xfa5b;continue
            if pc==0xfa5b:
                if action==39:status=1;break
                memory.record('T',0,0xfa5b,0)
                if action==37:status=5;break
            if pc==0xfaa5:
                if action==38:status=2;break
                memory.record('C',0,cpu.s.x,0)
                if action==34:
                    memory.mem[0x364]=3;memory.mem[1]^=0xa5;memory.mem[0x390]^=255;memory.mem[0x3ffc]^=0x55
                if action==35:status=6;break
                cpu.s.a,cpu.s.b,cpu.s.x,cpu.s.y=0xa5,0x5a,0xdead,0xbeef
                cpu.s.pc=0xfaa7;coverage.add(pc);continue
            coverage.add(pc)
            inst=decoded.setdefault(pc,decode(rom.read,pc)) if pc not in decoded else decoded[pc]
            memory.foreign=None;memory.foreign_access=''
            access=inst.access()
            if access is not None:
                memory.foreign_access=access['access']
                if inst.mode in ('direct','extended'):memory.foreign=inst.value
                elif inst.mode=='indexed_x':memory.foreign=(cpu.s.x+inst.value)&65535
                elif inst.mode=='indexed_y':memory.foreign=(cpu.s.y+inst.value)&65535
                a=memory.foreign
                if a is not None:
                    width=access['width_bits']
                    if a in SERIAL_OWNED and (width!=16 or ((a+1)&65535) in SERIAL_OWNED):memory.foreign=None
                    if pc in (0xf25f,0xf26e,0xf271):memory.foreign=None # Native ADC flags.
                    if 0x793d<=pc<0x7958 and a<0x3000:memory.foreign=None # Native timer prefix fields.
                    if 0xf9be<=pc<0xfa28 and a==0x50:memory.foreign=None # Native factory/ordinary qualification.
            opcode=memory.mem[pc]
            if opcode in (0x0e,0x0f):memory.record('M',0,0,int(opcode==0x0f))
            if inst.op in ('JSR','BSR') and inst.target in (0xfbd6,0xf3ed):gap_start=memory.cycle_counter
            cpu.step()
            if pc in (0xfbd6,0xf3ed):
                # Shared minimum call/RTS gap; BSR in this CPU model takes one
                # extra nominal cycle. It is not target device timing proof.
                assert memory.cycle_counter-gap_start>=11
                memory.record('D',0,0,11)
        else:raise AssertionError(f'Factory budget at {cpu.s.pc:04X}')
    except Failure:status=2
    state=bytearray(memory.mem[:0x900]);state[0x3b0:0x400]=bytes(0x50)
    state+=memory.mem[0x3000:0x3070]+memory.mem[0x3fc0:0x3ffe]
    return {'status':status,'value':0,'state':state.hex(),'events':list(memory.events)}

with tempfile.TemporaryDirectory(prefix='pcm-factory-runtime-') as directory:
    path=Path(directory)/'bmhm.bin';path.write_bytes(image);os.environ['PCM_BOOT_ROM']=str(path)
    subprocess.run([binary,'--contracts'],check=True)
    counts={}
    counts['direct']=compare((case(mode,word(0x362,0xfbd7)) for mode in range(6)),'factory entries and actual serial-accept join')
    counts['qualification']=compare((case(0,{0x902:first,0x903:second,0x900:ready,0x901:ready},masked=masked)
        for first,second,ready,masked in product([0,39,40,63,64,99,100,255],[0,26,27,255],[0,11,12],[0,1])),
        'actual40..99 qualification, channel3 threshold and ADC timeouts')
    counts['ids']=compare((case(0,{0x364:ident,1:armed,2:16,0x3064:gate},action=action)
        for ident,armed,gate,action in product([0,1,2,3,4,254,255],[0,1],[0,128],[0,31])),
        'captured ID, heartbeat mutation, callback arm and disabled-output routing')
    counts['phase']=compare((case(4,{0x904:0,2:phase,0x3062:port})
        for phase,port in product(range(256),[0,4,8,12,255])),
        'every phase byte, clamp, coil toggle and five literal output rows')
    counts['uploads']=compare((case(2,word(0x38e,destination)|{0x364:ident,1:flags},action=action)
        for destination,ident,flags,action in product([0,0x360,0x38e,0x38f,0x390,0x391,0x39f,0x1000,0xfff0],
        [1,2,255],[0,255],[0,33])),
        'fixed32-byte upload, forward overlap, serial aliases, live ID complement and wrap')
    counts['callbacks']=compare((case(0,word(0x38e,address)|{0x364:ident,1:armed},action=action)
        for address,ident,armed,action in product([0,1,0x1000,0x1800,0x7100,0xffff],
        [2,3],[0,1],[0,34,35,38])),
        'full-word callback targets, returned mutation and missing/nonreturning backend boundaries')
    counts['timer']=compare((case(1,{0x364:0,2:phase,0x3062:port},masked=1)
        for phase,port in product(range(256),[0,255])),
        'recurring timer raw phase increment and actual factory output join')
    counts['accept']=compare((case(5,{0x365:length,1:armed}|word(0x362,descriptor)|
        {0x36c:0x10,0x36d:0,0x36e:0xa5})
        for descriptor,length,armed in product([0xfbd7,0xfbe0,0xfbe9],[0,1,2,3,34],[0,1])),
        'real accepted factory payloads, retained short commands and loop action joins')
    counts['bindings']=compare((case(0,action=action) for action in [37,39]),'entry precondition failure boundaries')
    history=[];retained={}
    for i in range(128):
        item=case(1,retained|{0x364:[1,2,3,0,0,3,2,0][i%8],0x44:1,
            0x3064:128,0x38e:3,0x38f:0x91},masked=1)
        history.append(item);state=bytes.fromhex(execute(item)['state'])
        retained.update(enumerate(state[:0x900]))
        retained.update({0x3000+j:v for j,v in enumerate(state[0x900:0x970])})
        retained.update({0x3fc0+j:v for j,v in enumerate(state[0x970:])})
    counts['history']=compare(history,'retained upload/armed callback/serial/output/timer histories')
    failures=[]
    for item in [case(0),case(0,{0x364:1}),case(0,{0x364:2}),case(0,{0x902:39}),
            case(0,{0x900:12,0x901:12}),case(4,{2:16}),case(5,word(0x362,0xfbd7)|{0x365:3})]:
        for fail in range(1,len(execute(item)['events'])+2):failures.append((item[0],fail,*item[2:]))
    counts['failures']=compare(failures,'every provider/mask/delay/entry/callback failed prefix of representative paths')
    required=set();pc=0xfa5b
    while pc<0xfbd7:required.add(pc);pc=decode(rom.read,pc).next_pc
    # Entry SP assignment, SWI and the nonreturning wait are explicit target
    # boundaries. Their entry/status bindings are checked, not claimed as C ABI.
    excluded={0xfa5b,0xfa82,0xfbd4}
    missing=required-coverage-excluded
    print('Uncovered factory starts:',','.join(f'{a:04X}' for a in sorted(missing)),flush=True)
    assert not missing
    print(f'{sum(counts.values()):,} factory runtime comparisons; {len(required-excluded)} resident starts match. '
          'SWI, target SP restart and supplied callback execution remain explicit.',flush=True)
