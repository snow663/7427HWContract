"""Actual EGR demand/fraction, resident controller joins and fuel/spark consumers.

Optional1815 is a visible host callback fixture, not invented module code.
"""
from pathlib import Path
_parent=Path(__file__).with_name('compare_egr_control_rom.py')
exec(compile(_parent.read_text().split('\nwith tempfile.',1)[0],str(_parent),'exec'),globals())

_EgrMemory=Memory
class Memory(_EgrMemory):
    def read8(self,a):
        value=super().read8(a)
        if not self.fetching and a==self.foreign and 'R' in self.foreign_access:
            if self.action==28 and a==0x470a:self.mem[a]^=2
            if self.action==29 and a in (0x470d,0x4769,0x478c,0x47e7):self.mem[a]=(value+17)&255
            if self.action==31 and a==0x6e:self.mem[a]^=0xf4
            if self.action==32 and a==0x400d:self.mem[a]^=0x26
            if self.action==33 and a==0x1c0:self.mem[a]=(value+17)&255
            if self.action==34 and a==0x232:self.mem[a]=(value+17)&255
        return value
    def read16(self,a):
        value=super().read16(a)
        if not self.fetching and a==self.foreign and 'R' in self.foreign_access:
            if self.action==30 and 0x470e<=a<0x48a4:self.mem[a]=(self.mem[a]+11)&255
            if self.action==34 and a==0x232:self.mem[a]^=0x55
        return value
class MissingModule(Exception):pass
memory=Memory();cpu=HC11CPU(memory);coverage=set();original_fetch=cpu._fetch8;cpu._fetch8=fetch
BASE=BASE|{0x400b:0,0x400d:2,0x282:60,6:180,0x46f9:100,0x46fa:100,0x46fb:110,
    0x230:180,0x46fc:70,0x46fd:60,0x18:0,0x6e:9,0x1c0:120,0x4703:50,0x4704:40,
    0x6f:0,0x1d9:40,0x4701:20,0x4702:10,0x62:80,0x46ff:32,0x4700:24,
    0x16:0,0x284:80,0x46fe:10,0x1c9:120,0x4705:200,0x4706:210,0x4707:200,
    0x24a:147,0x4708:100,0x46:0,0x3e:0x80,0x4709:0,0x470a:1,0x1cf:77,
    0x1bb:128,0x1cc:128,0x1b9:80,0x1ae:80,0x1af:80,0x50:0,
    0x485a:16,0x485d:16,0x86:0,0x3b:0,0x393:0,0x394:77,0x248:128}
BASE=BASE|word(0xfd,500)|word(0x485b,100)|word(0x232,10000)|word(0x1b2,0x1020)|word(0x24e,1800)

def execute(item):
    mode,fail,action,masked,edits=item
    memory.mem[:]=image;memory.mem[:0x4000]=bytes(0x4000)
    for a,value in edits.items():memory.mem[a]=value
    memory.events.clear();memory.attempts=memory.polls=0;memory.fail=fail;memory.action=action;memory.foreign=None
    cpu.s.sp=0x3ff;cpu.s.ccr=0xd0 if masked else 0xc0
    cpu.s.a,cpu.s.b,cpu.s.x,cpu.s.y=0x12,0x34,0x5678,0x9abc
    entries=[[(0xcf16,0x7000)],[(0xd03e,0x7000)],
        [(0xcf16,0x7000),(0xd14e,0x7000),(0xd1f6,0x7000),(0xd03e,0x7000),(0xcdf7,0x7000)],
        [(0xd03e,0x7000),(0x8032,0x8058)],[(0xd03e,0x7000),(0xa792,0xa7d7)]]
    status=0
    try:
        for entry,stop in entries[mode]:
            native=entry in (0x8032,0xa792);cpu.s.pc=entry
            if stop==0x7000:cpu._push16(stop)
            for _ in range(8000):
                pc=cpu.s.pc
                if pc==stop:break
                if pc==0x1815:
                    if action==37:raise Failure
                    memory.record('C',0,pc,0)
                    if action==36:raise MissingModule
                    if action==35:memory.mem[0x1ae]=123;memory.mem[0x3b]|=0x10;memory.mem[0x393]=2
                    cpu.s.pc=cpu._pull16();continue
                coverage.add(pc);inst=decoded.setdefault(pc,decode(rom.read,pc)) if pc not in decoded else decoded[pc]
                memory.foreign=None;memory.foreign_access='';access=inst.access()
                if access is not None and not native and pc not in (0xd16e,0xd17d,0xd180):
                    memory.foreign_access=access['access']
                    if inst.mode in ('direct','extended'):memory.foreign=inst.value
                    elif inst.mode=='indexed_x':memory.foreign=(cpu.s.x+inst.value)&65535
                    elif inst.mode=='indexed_y':memory.foreign=(cpu.s.y+inst.value)&65535
                    if memory.foreign is not None and 0x3b0<=memory.foreign<0x400:memory.foreign=None
                opcode=memory.mem[pc]
                if opcode in (0x0e,0x0f):memory.record('M',0,0,int(opcode==0x0f))
                cpu.step()
            else:raise AssertionError(f'EGR producer budget at {cpu.s.pc:04X}')
    except Failure:status=2
    except MissingModule:status=1
    state=bytearray(memory.mem[:0x900]);state[0x3b0:0x400]=bytes(0x50)
    state+=memory.mem[0x3000:0x3070]+memory.mem[0x3fc0:0x3ffe]
    return {'status':status,'value':0,'state':state.hex(),'events':list(memory.events)}

with tempfile.TemporaryDirectory(prefix='pcm-egr-producers-') as directory:
    path=Path(directory)/'bmhm.bin';path.write_bytes(image);os.environ['PCM_BOOT_ROM']=str(path)
    subprocess.run([binary,'--contracts'],check=True);counts={}
    counts['entries']=compare((case(mode) for mode in range(5)),'resident EGR entries and real fuel/spark consumption')
    gates=[]
    def gate(address,values,options=None):
        for changes in options or [{}]:
            gates.extend(case(0,changes|{address:value}) for value in values)
    gate(0x230,[0,59,60,61,69,70,71,255],[{0x400b:64,0x6e:flag} for flag in (0,128)])
    gate(6,[99,100,101,109,110,111,255],[{0x282:start} for start in (0,99,100,101,255)])
    gate(0x18,[0,0x10,0x20,0x30]);gate(0x1c0,[0,39,40,41,49,50,51,255],[{0x6e:f} for f in (0,16)])
    gate(0x1d9,[0,9,10,11,19,20,21,199,200,201,255],
        [{0x6e:f,0x6f:fault} for f,fault in product([0,32],[0,4,32,36])])
    gate(0x62,[0,23,24,25,31,32,33,160,255],[{0x6e:f} for f in (0,64)])
    gate(0x284,[0,9,10,11,255],[{0x16:f} for f in (0,16)])
    gate(0x1c9,[0,199,200,201,209,210,211,255],[{0x6e:f} for f in (0,4)])
    gate(0x24a,[0,99,100,101,255]);gate(0x4709,[0,1,127,128,254,255])
    gates.extend(case(0,{0x46:dfco,0x400d:option,0x3e:closed,0x51:voltage,0x72:fault})
        for dfco,option,closed,voltage,fault in product([0,8],[2,10],[0,128],[0,16],[0,32]))
    counts['demand_gates']=compare(gates,'demand equality edges, hysteresis retention and output inhibit ordering')
    counts['selectors']=compare((case(0,{0x470a:selector,0x62:rpm,0x1cf:load,0x1c9:load,
        0x1bb:gain,0x1cc:baro,0x46ff:0,0x4700:0,0x4705:255,0x4706:255},action=action)
        for selector,rpm,load,gain,baro,action in product([0,1,2,255],[1,159,160,161,255],
        [0,1,31,127,255],[0,128,255],[95,96,255],[0,28])),
        'captured/fresh load selection, capped RPM, BARO coordinates and doubled-product saturation')
    counts['flow_gates']=compare((case(1,{0x400d:option,0x70:test,0x72:fault,0x50:idle,0x1af:duty})
        for option,test,fault,idle,duty in product([0,2,4,16,18,32,34,38],
        [0,1,4,5],[0,32],[0,128],[0,15,16,255])),
        'fraction branch priority, test/fault admission, idle suppression and nonlinear duty thresholds')
    counts['linear_gates']=compare((case(1,{0x1b9:position}|word(0xfd,timer))
        for position,timer in product([0,15,16,17,127,255],[0,99,100,101,65535])),
        'linear position and full-word run-timer equality edges')
    counts['vacuum']=compare((case(1,{0x400d:option,0x1c9:vacuum})
        for option,vacuum in product([0,2,4,32],range(256))),
        'every vacuum byte in both compressed fraction-coordinate transforms')
    counts['caps']=compare([case(1,{0x400d:4,0x62:255}),case(1,{0x1cc:95})],
        'backpressure RPM cap and below-offset BARO floor')
    divisions=[]
    for flow,gain,denominator in product([0,1,2,127,128,254,255],[0,1,2,127,128,254,255],
            [0,1,2,127,128,255,256,32767,32768,65535]):
        edits={a:0 for a in range(0x47d3,0x47e4)}|{0x70:4,0x1ae:0,0x1c9:0,
            0x47e4:gain,0x47e5:0,0x47e6:0,0x47e7:1,0x1cc:96}
        edits|={a:flow for a in range(0x47e8,0x47eb)}
        edits|={a:255 for a in range(0x4856,0x4868)}|{a:255 for a in range(0x47ce,0x47d3)}
        divisions.append(case(1,edits|word(0x232,denominator)|word(0x1b2,0)))
    counts['division']=compare(divisions,'carry-rounded half product, FDIV zero/overflow and quotient rounding')
    profiles=[]
    for mode,offset,stride,kind,action in product([0,1],[0,64,255],[0,1,17,255],[0,1],[0,29,30]):
        edits={a:((a*17 if kind==0 else -a*29)&255) for a in range(0x470b,0x4a00)}
        for header in (0x470b,0x4767,0x478a,0x47e5):edits|={header:offset,header+1:offset,header+2:stride}
        profiles.append(case(mode,edits|{0x70:4},action=action))
    counts['profiles']=compare(profiles,'matrix offsets, byte-wrapped row strides and fresh backing/stride mutation')
    counts['shared']=compare((case(mode,{0x6e:flags},action=action)
        for mode,flags,action in product([0,1],range(256),[0,31,32,33,34])),
        'all shared flag bytes and fresh option, MAP and airflow rereads')
    counts['hooks']=compare((case(0,{0x86:hook,0x3b:service,0x393:enabled,0x51:inhibit},action=action)
        for hook,service,enabled,inhibit,action in product([0,64],[0,16],[0,2],[0,16],[0,35,36,37])),
        'published demand before optional1815 admission/failure and final service override')
    counts['joins']=compare((case(mode,{0x400d:option,0x70:test,0x3034:sample,0x900:ready,
        0x248:blm,0x3d:pe},action=action)
        for mode,option,test,sample,ready,blm,pe,action in product([2,3,4],[0,2,4,32],[0,4],
        [0,255],[0,12],[0,127,128,255],[0,32],[0,22])),
        'real demand/ADC/PI/fraction/output and fraction-to-fuel/spark joins')
    failures=[]
    for item in [case(0),case(0,{0x400b:64,0x230:0}),case(0,{0x86:64},action=35),
            case(1),case(1,{0x400d:4}),case(1,{0x70:1}|word(0x232,0)),case(2,{0x900:12})]:
        for fail in range(1,len(execute(item)['events'])+2):failures.append((item[0],fail,*item[2:]))
    counts['failures']=compare(failures,'every provider/mask/module failed-operation prefix of representative paths')
    history=[];retained={}
    for i in range(128):
        item=case(2,retained|{0x3034:(i*29)&255,0x1c0:80+i%80,0x6f:0,0x70:0,
            0x4f:128,0x51:0,0x232:20+i%80,0x1d9:40+i%40})
        history.append(item);state=bytes.fromhex(execute(item)['state']);retained.update(enumerate(state[:0x900]))
        retained.update({0x3000+j:value for j,value in enumerate(state[0x900:0x970])})
        retained.update({0x3fc0+j:value for j,value in enumerate(state[0x970:])})
    counts['history']=compare(history,'retained complete EGR demand/feedback/control/flow/output histories')
    required=set()
    for start,end in [(0xcf16,0xd14e),(0xf4bd,0xf4c1),(0xf4de,0xf550)]:
        pc=start
        while pc<end:required.add(pc);pc=decode(rom.read,pc).next_pc
    missing=required-coverage;print('Uncovered EGR producer starts:',','.join(f'{a:04X}' for a in sorted(missing)),flush=True)
    assert not missing
    print(f'{sum(counts.values()):,} EGR producer comparisons; all {len(required)} new scoped starts match. '
          'Optional1815, full scheduler/REF interleaving and target timing remain separate.',flush=True)
