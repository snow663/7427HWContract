"""Compare board flush, MAP/VSS/brake input and housekeeping with actual BMHM.

The11-cycle delay is an explicit backend boundary. Intervening callback effects
and sequential controller joins do not establish a target ABI or physical pins.
"""
from pathlib import Path
_prior=Path(__file__).with_name('compare_iac_step_rom.py')
exec(compile(_prior.read_text().rsplit('\ncounts={}',1)[0],str(_prior),'exec'),globals())
IO_EXTRA=[71, 78, 106, 107, 114, 115, 116, 156, 251, 451, 452, 2060, 2061, 2062, 12346, 12386, 12388, 12391, 16324, 16325, 16378, 16379, 16380, 16381]
IO_CAL={0x4137,0x4138,0x4e68,0x4e69,0x4e6a,0x5d06}|set(range(0x4e6b,0x4e70))
OUTPUTS=OUTPUTS+IO_EXTRA
assert len(OUTPUTS)==len(set(OUTPUTS))
OUTPUT_SET=set(OUTPUTS)
BASE=BASE|{a:(a*31+19)&255 for a in IO_EXTRA}
BASE=BASE|{0x4b:0xa5,0x4e:0x66,0x72:0x35,0x73:0x40,0x74:0xa5,0x1c3:0x80,0x1c4:0x40,0x47:0,
    0x9c:0xa5,0xfb:0,0x80c:7,0x80d:0x12,0x80e:0x34,0x3060:0x6f,0x3062:0xa5,0x3064:0x15,
    0x3067:0x66,0x303a:0x55,0x3ffc:0xb9,0x3ffd:0x3a,0x3ffa:0x44,0x3ffb:0x5a,
    0x3fc4:0x56,0x3fc5:0x78,0x90f:0,0x908:0,0x907:0,0x400b:0}
source_defaults=json.loads(subprocess.check_output([binary,'--io-defaults'],text=True))
assert {a for a,_ in source_defaults}==IO_CAL
for a,v in source_defaults:assert v==rom.read(a,1)[0],(hex(a),v)
backing=json.loads(subprocess.check_output([binary,'--io-backing'],text=True))
assert len(backing)==8
for a,v in backing:assert v==rom.read(a,1)[0],(hex(a),v)
io_cal_bytes=rom.read(0x4000,0x2000)
_ParentMemory=Memory


def io_effect(m,action,address):
    if action==28 and address==0x3060:m.mem[0x4b]=(m.mem[0x4b]|0x10)&0x7f
    if action==29 and address==0x3060:
        m.mem[0x4b]=0xef;m.mem[0x4c]=0xcd;m.mem[0x4e]=0x89
    if action==30 and address==0x3062:m.mem[0x4d]=0xdd;m.mem[0x3064]=0x26;m.mem[0x4e]=0xef
    if action==31 and address==0x3064:m.mem[0x4d]=0x55;m.mem[0x4e]=0x5a
    if action==32 and address==0x3067:m.mem[0x4d]=0x10
    if action==33 and address==0x3ffc:m.mem[0x3ffc:0x3ffe]=bytes.fromhex('1234');m.mem[0x72]|=0x80
    if action==35 and address==0x3ffc:m.mem[0x4c]=0x6a;m.mem[0x4b]|=0x90
    if action==36 and address==0x3ffa:m.mem[0x73:0x75]=bytes.fromhex('ebcd')
    if action==38 and address==0x3fc4:m.mem[0x80d:0x80f]=m.mem[0x3fc4:0x3fc6]
    if action==39 and address==0x3fc4:
        m.mem[0x80d:0x80f]=bytes([m.mem[0x3fc4]^0x80,m.mem[0x3fc5]]);m.mem[0x80c]=255
    if action in (40,41) and address==0x303a:m.mem[0x400f]=0 if action==40 else 0x44;m.mem[0x4d]=0x15


class Memory(_ParentMemory):
    def read8(self,a):
        if a not in (0x3060,0x3064):return super().read8(a)
        v=FixtureMemory.read8(self,a);self.record('R',8,a,v)
        if self.mem[0x908] in (28,31):io_effect(self,self.mem[0x908],a)
        return v
    def read16(self,a):
        if a not in (0x3ffc,0x3ffa,0x3fc4):return super().read16(a)
        v=(FixtureMemory.read8(self,a)<<8)|FixtureMemory.read8(self,a+1);self.record('R',16,a,v)
        if self.mem[0x908] in (33,36,38,39):io_effect(self,self.mem[0x908],a)
        return v
    def write8(self,a,v):
        if a not in (0x3060,0x3062,0x3067,0x303a):return super().write8(a,v)
        self.record('W',8,a,v&255);FixtureMemory.write8(self,a,v)
        if self.mem[0x908] in (29,30,32,40,41):io_effect(self,self.mem[0x908],a)
    def write16(self,a,v):
        if a!=0x3ffc:return super().write16(a,v)
        self.record('W',16,a,v&65535);FixtureMemory.write8(self,a,v>>8);FixtureMemory.write8(self,a+1,v)
        if self.mem[0x908]==35:io_effect(self,35,a)


memory=Memory();cpu=memory.cpu;coverage=set()


def execute(item):
    mode,edits=item
    memory.mem[:0x1802]=bytes(0x1802);memory.mem[0x4000:0x6000]=io_cal_bytes
    memory.mem[0xB319:0xB419]=gear_bytes
    for a,v in edits.items():memory.mem[a]=v
    memory.events.clear();memory.writes.clear();memory.attempts=memory.read_index=memory.cycle_counter=0
    memory.fail_at=memory.mem[0x907]
    cpu.s.pc=0x7000;cpu.s.sp=0x3FF;cpu.s.ccr=0xD0 if memory.mem[0x909] else 0xC0
    cpu.s.a,cpu.s.b,cpu.s.x,cpu.s.y=0x12,0x34,0x5678,0x9ABC
    status=unresolved=value=0

    def invoke(start,stop=0x7000):
        nonlocal value
        sp=cpu.s.sp;cpu.s.pc=start
        if stop==0x7000:cpu._push16(0x7000)
        if start==0xA407:cpu._push16(0x93E1)
        for _ in range(6000):
            pc=cpu.s.pc
            if start==0xA407 and pc in (0x93E1,0x7000):
                value=int(pc==0x7000)
                if pc==0x93E1:assert cpu._pull16()==0x7000
                assert cpu.s.sp==sp;return
            if pc==stop:
                assert cpu.s.sp==sp,(hex(start),hex(cpu.s.sp),hex(sp));return
            if pc==0xA5D7:return
            action=memory.mem[0x908]
            if pc==0x1803:
                if memory.mem[0x90F]&4:raise Missing(9)
                memory.record('T',0,pc,action)
                if action==23:
                    memory.mem[0x3b]|=0x10;memory.mem[0x395]=1;memory.mem[0x396]=93
                    memory.mem[0x09]=0;memory.mem[0x38f]&=0xbf;memory.mem[0x44]&=0xef
                if action==24:
                    memory.mem[0x86]&=0xbf;memory.mem[0x38]|=0x40;memory.mem[0x44]|=0x10;memory.mem[0x09]=0
                cpu.s.a,cpu.s.b,cpu.s.x,cpu.s.y=0xA5,0x5A,0xDEAD,0xBEEF;cpu.s.pc=0x7AA5
                continue
            if pc in (0x180F,0x1812):
                output=pc==0x180F;magnitude=cpu.s.a
                memory.record('T',0,pc,magnitude if output else action)
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
            if pc==0xF3F2:
                memory.record('D',0,0,11)
                if action==34:memory.mem[0x3ffc:0x3ffe]=bytes.fromhex('1234');memory.mem[0x72]|=0x80
            coverage.add(pc);opcode=memory.mem[pc]
            if opcode in (0x0E,0x0F):memory.record('M',0,0,int(opcode==0x0F))
            cpu.step()
            if opcode==0x0E and action==4:memory.mem[0x50]|=0x20;memory.mem[0x4F]|=0x80
            if opcode==0x0E and action==37:
                memory.mem[0x73:0x75]=bytes.fromhex('0200');memory.mem[0x80d:0x80f]=bytes.fromhex('fffe')
                memory.mem[0x80c]=255;memory.mem[0x4d]=255
            if opcode==0x0E and action==43 and memory.mem[0x73]&0x40:memory.mem[0x3ffa:0x3ffc]=bytes(2)
        raise AssertionError(f'Board I/O execution budget at {cpu.s.pc:04X}')

    try:
        entries=[(0xF3EE,),(0xF400,),(0x7BAA,),(0x7BF5,),(0x7D21,),(0x9167,),
            (0x7BA7,),(0x7BA7,0x9167),(0x91A3,0x7BA7,0x9167,0x93D0),
            (0x7BA7,0x7765),(0x9167,0x93D0),(0xF3EE,0x9167,0x9E99),(0x7BA7,0xC514,0x91A3)]
        for start in entries[mode]:
            stop={0x7BAA:0x7BF5,0x7BF5:0x7C0F,0x7765:0x77C6}.get(start,0x7000)
            invoke(start,stop)
        if cpu.s.pc==0xA5D7:status=6
    except Failure:status=2
    except Missing as e:status=1;unresolved=e.task
    assert all(a in OUTPUT_SET or 0x3C0<=a<0x400 for a,_ in memory.writes),[(hex(a),v) for a,v in memory.writes if a not in OUTPUT_SET and not 0x3c0<=a<0x400]
    return {'status':status,'value':value,'state':[memory.mem[a] for a in OUTPUTS],
            'masked':int(bool(cpu.s.ccr&0x10)),'unresolved':unresolved,'partial':0,
            'coordinates':[0,0],'events':list(memory.events)}


def compare(items,label):
    iterator=iter(items);count=0
    while chunk:=list(islice(iterator,512)):
        payload=[]
        for mode,edits in chunk:
            values=[mode,len(edits)]
            for a,v in edits.items():values.extend((a,v))
            payload.append(' '.join(map(str,values)))
        result=subprocess.run([binary],input='\n'.join(payload)+'\n',text=True,capture_output=True,check=True)
        lines=result.stdout.splitlines();assert len(lines)==len(chunk),(len(lines),len(chunk),result.stderr)
        for index,(item,line) in enumerate(zip(chunk,lines)):
            actual=json.loads(line);expected=execute(item)
            if actual!=expected:
                Path('/tmp/board-io-failure.json').write_text(json.dumps({'item':item,'actual':actual,'expected':expected,'outputs':OUTPUTS}))
                differences=[(hex(a),x,y) for a,x,y in zip(OUTPUTS,actual['state'],expected['state']) if x!=y]
                raise AssertionError((label,count+index,item[0],differences,{k:(actual[k],expected[k]) for k in actual if k!='state' and actual[k]!=expected[k]}))
        count+=len(chunk)
    print(f'{count:,} {label} match.',flush=True);return count


counts={}
rng=random.Random(0x31F3EE)
counts['initial']=compare((case(mode) for mode in range(13)),'board/input direct and sequential joins')
variants=[]
for i in range(2048):
    edits={a:rng.randrange(256) for a in sorted(BASE.keys()|IO_CAL|IAC_CAL|SLOW_CAL|MAIN_CAL|{0x4eb6})}
    edits.update({0x400b:0,0x907:0,0x908:[0,*range(28,42)][i%15],0x909:i&1,0x90f:0})
    variants.append(case(i%13,edits))
counts['variants']=compare(variants,'board/input profile/state/callback variants')
counts['control']=compare((case(0,word(0x3ffc,value)|{0x72:mirror})
    for value,mirror in product(range(65536),[0,0x80])), 'every control word with both service-mirror states')
counts['ports']=compare((case(1,{0x3060:sample,0x4b:command,0x4c:(sample^command),0x3064:command,0x4e:sample})
    for sample,command in product(range(256),repeat=2)), 'all port-input and output-shadow byte pairs')
counts['map_rounding']=compare((case(2,word(0x1c3,value)|{0x6f:0,0x47:0,0x82e:value>>8,0x4137:0})
    for value in range(65536)), 'all MAP filter words with retained fractional rounding')
counts['map_gain']=compare((case(2,word(0x1c3,((target^gain)<<8)|((target+gain)&255))|
    {0x6f:0,0x82e:target,0x47:gain&1,0x4137:gain,0x4138:255-gain})
    for target,gain in product(range(256),repeat=2)), 'all raw MAP/gain bytes and filter selection')
counts['map_fallback']=compare((case(2,{0x6f:0x48,0x4f:0xf5,0x1d9:tps,0x4e69:gain,
    0x62:(tps^gain),0x4e6a:(tps+gain)&255,0x4e68:(tps*7+gain)&255})
    for tps,gain in product(range(256),repeat=2)), 'MAP fallback multiply/shift carries and default caps')
counts['map_bias']=compare((case(2,{0x6f:0x48,0x4f:0xf5,0x1d9:0,0x4e69:0,
    0x62:rpm,0x4e6a:cap,0x4e68:255}) for rpm,cap in product(range(256),repeat=2)),
    'every RPM/cap pair with cap-before-offset lookup')
counts['map_flags']=compare((case(2,{0x6f:flags,0x4f:running,0x47:transient,0x4e69:gain,0x1d9:255})
    for flags,running,transient,gain in product(range(256),[0x65,0x75],[0,1],[0,255])),
    'MAP fault/running/filter flags and overflow exits')
counts['status']=compare((case(3,word(0x3ffa,status)|word(0x80d,status)|word(0x3fc4,status^0x8000)|{0x80c:status&255})
    for status in range(65536)), 'all status words with split REF ownership and VSS admission')
counts['timestamp_equal']=compare((case(3,word(0x3ffa,0x4400)|word(0x80d,value)|word(0x3fc4,value)|{0x80c:value&255})
    for value in range(65536)), 'all unchanged timestamp words with retained observation counts')
counts['brake']=compare((case(4,{0xfb:count,0x5d06:limit,0x4d:source,0x9c:state})
    for count,limit,(source,state) in product(range(256),range(256),[(0,0xa4),(2,0xa5)])),
    'every brake count/limit pair with both mismatched polarities')
counts['brake_agreement']=compare((case(4,{0x4d:input_byte,0x9c:state,0xfb:77,0x5d06:255})
    for input_byte,state in product(range(256),[0xa4,0xa5])), 'brake agreements and unrelated input bits')
counts['housekeeping']=compare((case(5,{0x400f:options,0x4d:inputs,0x41:(options^inputs),0x52:options})
    for options,inputs in product(range(256),repeat=2)), 'every option/input byte pair with AC retention and P/N decoding')
joined=[]
for i in range(2048):
    edits={a:rng.randrange(256) for a in sorted(BASE.keys()|IO_CAL|IAC_CAL|SLOW_CAL|MAIN_CAL|{0x4eb6})}
    edits.update({0x400b:0,0x907:0,0x90f:0,0x908:[0,*range(28,42),43][i%16],0x909:i&1})
    joined.append(case([6,7,8,9,10,11,12][i%7],edits))
for action,mirror,status,mode in product([0,*range(28,42),43],[0,0x80],[0,0x0400,0x4000,0x4400],[0,1,3,5,6,7,8,9,10,11,12]):
    joined.append(case(mode,word(0x3ffa,status)|{0x908:action,0x72:mirror,0x400b:0,0x73:0,0x74:0,0x90f:0}))
counts['joined']=compare(joined,'ordered board/input/controller/REF calls and callback state samples')
failures=[]
for item in joined[::5]:
    for fail in range(1,len(execute(item)['events'])+1):failures.append((item[0],item[1]|{0x907:fail}))
counts['failures']=compare(failures,'every selected mask/read/delay/write failure prefix')
history=[];edits={0x400b:0,0x86:0xa0,0x3b:0,0x4f:0xf5,0x4d:0x15,0x4b:0x10,0x47:0,0x6f:0,
    0x907:0,0x90f:0,0x908:0,0xa7:130,0x73:0,0x74:0,0xfb:0}
for entry in range(1024):
    edits.update({2:entry%160,0x3064:(entry//7)&255,0x82e:(entry*7)&255,0x1d9:entry&31,
        0x908:[0,30,37,43][entry%4],0x62:entry&255})
    edits.update(word(0x3ffa,[0,0x0400,0x4000,0x4400][entry%4]));edits.update(word(0x3fc4,(entry*257)&65535))
    item=case([7,8,9,11,12][entry%5],dict(edits));history.append(item)
    edits.update(dict(zip(OUTPUTS,execute(item)['state'])))
counts['history']=compare(history,'retained board/command/MAP/VSS/brake/REF histories')
required=set()
for start,end in [(0xf3ed,0xf420),(0x7ba7,0x7c13),(0x9167,0x91a3),(0x7d21,0x7d4b),(0xf49a,0xf4a4),(0xf4bd,0xf4de)]:
    pc=start
    while pc<end:required.add(pc);pc=decode(rom.read,pc).next_pc
assert required<=coverage,','.join(f'{a:04X}' for a in sorted(required-coverage))
print(f'{sum(counts.values()):,} board/input comparisons; all {len(required)} scoped instruction starts; '
      '11 source-profile bytes and8 fixture knots match stock. Target ABI, device behavior and physical timing remain separate.')
