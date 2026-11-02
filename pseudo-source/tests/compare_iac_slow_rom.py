"""Compare slot9, follower and slow-IAC C routines with actual stock instructions.

EGR CF16 and VSS D4DA remain explicit return fixtures. Joined calls supply
later phase/input admissions; they do not replace the intervening input pipeline.
"""
from pathlib import Path
_prior=Path(__file__).with_name('compare_iac_rom.py')
exec(compile(_prior.read_text().rsplit('\ncounts={}',1)[0],str(_prior),'exec'),globals())
SLOW_EXTRA=[7, 8, 23, 63, 642, 2141, 2142, 2155, 2156, 2171, 2172, 2178, 2179, 2180, 2181, 2182, 2190]
SLOW_CAL=set([20151, 20153, 20155, 20272, 20273, 20423, 20424, 20567, 20568, 20569, 20570, 20571, 20572, 20573, 20574, 20575, 20576, 20577, 20578, 20579, 20580, 20581, 20582, 20583, 20584, 20585, 20586, 20587, 20588, 20589, 20590, 20591, 20592, 20593, 20594, 20595, 20596, 20597, 20598, 20599, 20600, 20601, 20602, 20603, 20604, 20605, 20606, 20607, 20608, 20609, 20610, 20611, 20612, 20613, 20614, 20615, 20616, 20617, 20618, 20619, 20620, 20621, 20622, 20623, 20624, 20625, 20626, 20627, 20628, 20629, 20630, 20631, 20632, 20633, 20634, 20635, 20636, 20637, 20638, 20639, 20640, 20641, 20672, 20673, 20694, 23298])
OUTPUTS=OUTPUTS+SLOW_EXTRA
assert len(OUTPUTS)==len(set(OUTPUTS))==230
OUTPUT_SET=set(OUTPUTS)
BASE=BASE|{a:(a*71+13)&255 for a in SLOW_EXTRA}
BASE=BASE|{2:9,7:99,8:77,9:0x80,0x16:0,0x17:0,0x18:0xB1,0x36:8,0x37:0xA0,0x39:0x20,
    0x3E:0,0x3F:0x95,0x44:0xC4,0x4F:0xF5,0x282:73,0x283:160,0x85C:7,0x85D:1,0x85E:1,
    0x86B:8,0x86C:1,0x87B:9,0x87C:1,0x884:0,0x885:8,0x886:1,0x88E:0,0x90F:0}
BASE=BASE|word(0x880,0x1234)|word(0x882,0x4040)
source_defaults=json.loads(subprocess.check_output([binary,'--iac-slow-defaults'],text=True))
assert {a for a,_ in source_defaults}==SLOW_CAL and len(SLOW_CAL)==86
for a,v in source_defaults:assert v==rom.read(a,1)[0],(hex(a),v)
backing=json.loads(subprocess.check_output([binary,'--follower-backing'],text=True))
assert len(backing)==256
for a,v in backing:assert v==rom.read(a,1)[0],(hex(a),v)
memory=Memory();cpu=memory.cpu;coverage=set()


def execute(item):
    mode,edits=item
    memory.mem[:0x1802]=bytes(0x1802);memory.mem[0x4000:0x5B04]=cal_bytes
    memory.mem[0xB319:0xB419]=gear_bytes
    for a,v in edits.items():memory.mem[a]=v
    memory.events.clear();memory.writes.clear();memory.attempts=memory.read_index=memory.cycle_counter=0
    memory.fail_at=memory.mem[0x907]
    cpu.s.pc=0x7000;cpu.s.sp=0x3FF;cpu.s.ccr=0xD0 if memory.mem[0x909] else 0xC0
    cpu.s.a,cpu.s.b,cpu.s.x,cpu.s.y=0x12,0x34,0x5678,0x9ABC
    status=unresolved=0
    if mode==8:cpu.s.a=memory.mem[0x900];cpu.s.x=0x5064

    def invoke(start,stop=0x7000):
        sp=cpu.s.sp;cpu.s.pc=start
        if stop==0x7000:cpu._push16(0x7000)
        for _ in range(5000):
            pc=cpu.s.pc
            if pc==stop:
                assert cpu.s.sp==sp,(hex(start),hex(cpu.s.sp),hex(sp));return
            if pc==0xA5D7:return
            action=memory.mem[0x908]
            if pc in (0xCF16,0xD4DA):
                task=7 if pc==0xCF16 else 8
                if memory.mem[0x90F]&(1 if task==7 else 2):raise Missing(task)
                memory.record('T',0,pc,action)
                if task==7 and action==20:memory.mem[0x4F]&=0x7F;memory.mem[8]=77
                if task==7 and action==21:
                    memory.mem[0x4F]|=0x80;memory.mem[0x36]=(memory.mem[0x36]&0x20)|3
                    memory.mem[0x1D9]=24;memory.mem[0x284]=190;memory.mem[2]=0x29;memory.mem[0x2AC]=100
                if task==8 and action==22:
                    memory.mem[0x882:0x884]=bytes.fromhex('abcd');memory.mem[0x284]=1;memory.mem[2]=9
                cpu.s.a,cpu.s.b,cpu.s.x,cpu.s.y=0xA5,0x5A,0xDEAD,0xBEEF;cpu.s.pc=0x7AA5
                continue
            if pc in (0x180F,0x1812):
                output=pc==0x180F
                if memory.mem[0x90D if output else 0x90A]:raise Missing(3 if output else 1)
                magnitude=cpu.s.a;memory.record('T',0,pc,magnitude if output else action)
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
            coverage.add(pc);opcode=memory.mem[pc]
            if opcode in (0x0E,0x0F):memory.record('M',0,0,int(opcode==0x0F))
            cpu.step()
            if opcode==0x0E and action==4:memory.mem[0x50]|=0x20;memory.mem[0x4F]|=0x80
        raise AssertionError(f'IAC execution budget at {cpu.s.pc:04X}')

    try:
        entries=[(0x9CFD,0x7000),(0xA2BA,0xA32A),(0xA32A,0xA35C),(0xA35C,0xA398),
                 (0xA39C,0xA3E6),(0xA3E6,0x7000),(0xA3FA,0x7000),(0xA2B0,0x7000),
                 (0xF4B6,0x7000),(0x7B2F,0x7000),(0x9E99,0x7000),(0xA2B0,0x7000),(0x7B2F,0x7000)]
        invoke(*entries[mode])
        if mode==10:memory.mem[2]=9;invoke(0xA2B0)
        if mode==11:memory.mem[2]=7;invoke(0x9E99)
        if mode==12:memory.mem[2]=10;invoke(0xA466)
        if cpu.s.pc==0xA5D7:status=6
    except Failure:status=2
    except Missing as e:status=1;unresolved=e.task
    assert all(a in OUTPUT_SET or 0x3C0<=a<0x400 for a,_ in memory.writes)
    return {'status':status,'value':cpu.s.a if mode==8 and status==0 else 0,'state':[memory.mem[a] for a in OUTPUTS],
            'masked':int(bool(cpu.s.ccr&0x10)),'unresolved':unresolved,'partial':0,
            'coordinates':[0,0],'events':list(memory.events)}


counts={}
rng=random.Random(0x319CFD)
variants=[]
for i in range(2048):
    edits={a:rng.randrange(256) for a in sorted(BASE.keys()|SLOW_CAL|IAC_CAL|set(range(0x5065,0x5165)))}
    edits.update({0x908:i%23,0x909:i&1,0x90F:0})
    variants.append(case(i%12,edits))
counts['variants']=compare(variants,'slow-IAC calibration/state variants')
counts['scaled']=compare((case(8,{0x900:x,0x5064:scale}) for x,scale in product(range(256),repeat=2)),
                         'scaled-coordinate/index/fraction C/ROM cases')


def directed_cases():
    window={0x509A:0,0x509B:255,0x509C:255,0x509D:255,0x282:73}
    for option,opened,hold,context,dfco,hot,age in product([0,2],[0,0x80],[0,1],[0,4],[0,8],[0,1],[0,10,255]):
        yield case(0,word(0x882,0x8000)|window|{0x4E8F:option,0x39:opened,0x884:hold,
                   0x36:context,0x46:dfco,0x37:hot,0x886:age,0x1D9:0})
    for minimum,gain,age,hot in product([0,1,64,255],[0,1,128,255],[0,10,255],[0,1]):
        yield case(0,word(0x882,0x8000)|window|{0x36:0,0x39:0,0x884:0,0x46:0,0x1D9:0,
                   0x283:0,0x508A:minimum,0x50A0:gain,0x37:hot,0x886:age})
    for gain,low_gain,load in product([0,1,128,255],[0,1,128,255],[0,99,100,255]):
        yield case(0,word(0x882,0x8000)|{0x36:0,0x39:0x80,0x884:0,0x1D9:0,
                   0x5070:gain,0x5089:low_gain,0x1C0:load,0x5088:100})


counts['directed']=compare(directed_cases(),'zero-gain/DFCO/minimum saturation and age-qualification witnesses')


def follower_cases():
    for value in range(65536):
        yield case(0,word(0x882,value)|word(0x880,65535-value)|
                   {0x36:value&7,0x39:0x80 if value&8 else 0,0x884:0,0x885:value>>8,0x1D9:(value*17)&255})
    for tps,threshold,context,flags,hot in product(range(256),[0,40,255],[0,2],[0,0x80,0x40],range(4)):
        yield case(0,{0x1D9:tps,0x885:threshold,0x36:context,0x39:flags,0x37:hot,
                      0x509A:0,0x509B:255,0x509C:255,0x509D:255})
    # The coolant gain is zero: a saturated RPM product must skip it.
    for value in range(65536):
        yield case(0,word(0x882,value)|{0x884:1,0x36:4,0x37:1,0x39:0x80,0x1D9:0,
                   0x885:0,0x5087:0,0x63:0,0x5065:255,0x5066:0,0x283:0,0x5057:0})


counts['follower']=compare(follower_cases(),'filtered follower words, TPS gates and RPM-overflow C/ROM cases')


def decay_cases():
    for amount,divider,phase in product(range(256),range(256),[9,0x19]):
        yield case(1,{0x87B:amount,0x87C:divider,0x86B:amount,0x86C:divider,
                      0x85C:amount,0x85D:divider,0x85E:int(phase==9),0x3F:0x95,2:phase})


counts['decays']=compare(decay_cases(),'switch/startup dividers and RPM-hold expiry C/ROM cases')
counts['drive']=compare((case(2,word(0x2A7,(current<<8)|0x5A)|word(0x2AA,(current<<8)|0xA5)|
    {0x36:2|ac,0x2A9:snapshot,0x2AC:snapshot,0x4FC7:(snapshot+current)&255,0x4FC8:(snapshot+current)&255})
    for snapshot,current,ac in product(range(256),range(256),[0,1])),
    'drive snapshot/current/AC byte-carry C/ROM cases')
counts['kicker_fault']=compare((case(3,{0x39:3,0x09:prior,0x18:(on^off)&4,0x2B1:on,0x2B2:off})
    for on,off,prior in product(range(256),range(256),[0,0x40])),
    'kicker baseline subtraction and retained fault C/ROM cases')
counts['learning_fault']=compare((case(4,word(0x2A3,0)|word(0x2AD,0)|
    {0x36:8,0x09:0,0x859:255,0x50C0:0,0x88E:count,0x50C1:limit,0x18:(count^limit)&8})
    for count,limit in product(range(256),repeat=2)),
    'learning count/limit/wrap C/ROM cases')
counts['reset']=compare((case(5,{0x09:0,0x44:0xC4,0x284:speed,0x4EB7:limit})
    for speed,limit in product(range(256),repeat=2)), 'reset speed/limit C/ROM cases')
counts['reset_flags']=compare((case(5,{0x09:flags,0x284:speed,0x44:0xC4|gate})
    for flags,speed,gate in product(range(256),[0,29,30,31,255],[0,0x10])),
    'reset validity/request and current44.4 C/ROM cases')

joined=[]
for i in range(2048):
    edits={a:rng.randrange(256) for a in sorted(BASE.keys()|SLOW_CAL|IAC_CAL)}
    edits.update({0x908:i%23,0x909:i&1,0x90F:i&3,0x90A:int(i%13==0),0x90D:int(i%17==0)})
    joined.append(case([7,9,10,11,12][i%5],edits))
for mode,phase,action in product([7,9,10,11,12],range(0,160,16),[0,19,20,21,22]):
    joined.append(case(mode,{2:phase|9,0x908:action,0x4E8F:0x9E,0x4F8E:255,0x4F8F:255,0x3008:4}))
# Warm retention, phase gates, nonrunning calls, timer cancel and diagnostic enables.
for mode,flags in product(range(8),range(256)):
    joined.append(case(mode,word(0x2A3,0)|word(0x2AD,0)|{0x36:flags,0x39:flags,0x37:flags,
        0x09:flags,0x3F:flags,0x17:flags,0x16:flags,0x3E:flags,0x5B02:flags,0x4E8F:flags,
        2:flags%160,0x4F:flags,0x282:flags,0x509A:0,0x509B:255,0x509C:0,0x509D:1}))
counts['joined']=compare(joined,'slow/background/slot9/subsequent-normal and callback witnesses')
failures=[]
for item in joined[::7]:
    for fail in range(1,len(execute(item)['events'])+1):failures.append((item[0],item[1]|{0x907:fail}))
counts['failures']=compare(failures,'ordered slot9/hook/switch/publication failure prefixes')
history=[];edits={0x36:8,0x09:0,0x39:0,0x37:0,0x17:0,0x16:0,0x3E:0,0x3F:0x95,
                  0x4F:0xF5,0x90F:0,0x509A:0,0x509B:255,0x509C:255,0x509D:255}
for tick in range(512):
    edits.update({2:(9+16*tick)%160,0x1D9:tick&63,0x284:(tick*7)&255,0x908:[0,20,21,22][tick%4],
                  0x884:max(0,edits.get(0x884,0)-1),0x44:0xD4 if tick%31==0 else 0xC4})
    item=case([9,10,11][tick%3],dict(edits));history.append(item);edits.update(dict(zip(OUTPUTS,execute(item)['state'])))
counts['history']=compare(history,'retained follower/decay/fault/reset history calls')

required=set()
for start,end in [(0x9CFD,0x9E99),(0xA2B0,0xA407),(0x7B2F,0x7B39),(0xF4B6,0xF4BC),(0xF4C5,0xF4DE)]:
    pc=start
    while pc<end:required.add(pc);pc=decode(rom.read,pc).next_pc
assert required<=coverage,','.join(f'{pc:04X}' for pc in sorted(required-coverage))
print(f'{sum(counts.values()):,} slow-IAC comparisons; all {len(required)} follower/slow/slot9/scaled-lookup instruction starts exercised; '
      '86 new source-profile bytes and256 test-only RPM backing bytes match stock. '
      'CF16/D4DA and180F/1812 remain explicit; main IAC and physical stepping remain separate work.')
