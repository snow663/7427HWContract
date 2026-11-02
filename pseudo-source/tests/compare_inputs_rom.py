"""Compare six input/consumer groups and scheduled joins with actual stock BMHM.

Historical suites keep isolated boundary fixtures. This suite links the resident
AC, VSS and shift-lamp bodies. Optional modules and CF16 remain explicit returns.
"""
from pathlib import Path
_prior=Path(__file__).with_name('compare_io_rom.py')
exec(compile(_prior.read_text().rsplit('\ncounts={}',1)[0],str(_prior),'exec'),globals())
INPUT_EXTRA=[101, 137, 443, 453, 459, 485, 521, 579, 626, 645, 2063, 2064, 2065, 2066, 2067, 2095, 2096, 2097, 2098, 2099, 2100, 2101, 2102, 2117, 2118, 2119, 2120, 2121, 2122, 2123, 16352, 16353]
INPUT_CAL=set([16398, 16400, 16401, 16402, 16403, 16404, 16405, 16406, 16407, 16408, 16409, 16410, 16411, 16412, 16413, 16414, 16415, 16416, 16417, 16418, 16419, 16697, 16698, 17846, 17847, 17848, 17849, 17850, 17851, 17852, 17853, 18147, 18148, 18149, 18150, 18151, 18152, 18153, 18154, 18155, 18156, 18157, 18158, 18271, 18272, 18273, 18274, 18275, 18276, 18277, 18278, 18279, 18659, 18664, 19260, 19261, 19262, 19263, 19264, 19265, 19266, 19267, 19268, 19269, 19270, 19271, 19272, 19273, 19274, 19275, 19276, 19300, 19301, 19302, 19303, 19304, 19305, 19306, 19307, 19308, 19309, 19310, 19311, 19312, 19313, 19314, 19315, 19316, 19373, 19374, 19375, 19376, 19377, 19378, 19379, 19380, 19381, 19382, 19383, 19384, 19385, 19386, 19597, 19598, 19599, 19600, 19601, 19602, 19603, 19604, 19605, 20110, 20755, 20756, 20757, 20758, 20759, 20760, 20761, 20762, 20763, 20764, 20765, 20766, 20767, 20768, 20769, 20770, 20771, 20772, 20773, 20774, 20775, 20776, 20777, 20778, 20779, 20780, 20781, 20782, 20783, 20784, 20785, 20786, 20787, 20788, 20789, 20790, 20791, 20792, 20793, 20794, 20795, 20796, 20797, 20798, 20799, 20800, 20801, 20802, 20803, 20804, 20805, 20806, 20807, 20808, 20809, 20810, 20811, 20812, 20813, 20814, 20815, 20816, 20817, 20818, 20819, 20820, 20821, 20822, 20823, 20824, 20825, 20826, 20827])
OUTPUTS=OUTPUTS+INPUT_EXTRA
assert len(OUTPUTS)==len(set(OUTPUTS))
OUTPUT_SET=set(OUTPUTS)
BASE=BASE|{a:(a*23+37)&255 for a in INPUT_EXTRA}
BASE=BASE|{0x47:0,0x3e:0xa0,0x65:0x80,0x63:0x80,0x1c5:0,0x89:0,0x811:39,
    0x285:0,0x82f:100,0x830:0,0x831:0,0x832:0,0x833:0,0x834:0,0x835:0,0x836:0,
    0x400e:3,0x209:7,0x3b:0,0x38f:0xa4,0x390:0,0x845:1,0x846:0,0x847:0,0x848:0,
    0x849:0,0x84a:0,0x84b:0,0x3fe0:0x12,0x3fe1:0x34,0x90e:0,0x90f:0}
source_defaults=json.loads(subprocess.check_output([binary,'--input-defaults'],text=True))
assert len(source_defaults)==len(INPUT_CAL)==185 and {a for a,_ in source_defaults}==INPUT_CAL
for a,v in source_defaults:assert v==rom.read(a,1)[0],(hex(a),v)
backing=json.loads(subprocess.check_output([binary,'--input-backing'],text=True))
assert len(backing)==12
for a,v in backing:assert v==rom.read(a,1)[0],(hex(a),v)
_InputParentMemory=Memory
class Memory(_InputParentMemory):
    def read16(self,a):
        if a!=0x3fe0:return super().read16(a)
        value=(FixtureMemory.read8(self,a)<<8)|FixtureMemory.read8(self,a+1)
        self.record('R',16,a,value)
        if self.mem[0x908]==44:
            self.mem[0x847:0x849]=bytes.fromhex('abcd');self.mem[a:a+2]=bytes.fromhex('1234')
        return value
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
            if pc in (0x180C,0xCF16):
                memory.record('T',0,pc,action)
                if pc==0x180C:
                    if action==13:memory.mem[0x86]|=0x40;memory.mem[0x4c]^=0x55
                    if action==14:memory.mem[0x86]&=0xbf;memory.mem[0x06]=32
                if pc==0xCF16:
                    if action==20:memory.mem[0x4f]&=0x7f;memory.mem[8]=77
                    if action==21:
                        memory.mem[0x4f]|=0x80;memory.mem[0x36]=(memory.mem[0x36]&0x20)|3
                        memory.mem[0x1d9]=24;memory.mem[0x284]=190;memory.mem[2]=0x29;memory.mem[0x2ac]=100
                cpu.s.a,cpu.s.b,cpu.s.x,cpu.s.y=0xA5,0x5A,0xDEAD,0xBEEF;cpu.s.pc=0x7AA5
                continue
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
            if opcode==0x0F and action==45:memory.mem[0x82f]=50;memory.mem[0x44]|=1
            if opcode==0x0E and action==46:memory.mem[0x400f]=4;memory.mem[0x4d]=0;memory.mem[0x830]=77;memory.mem[0x831]=88
            if opcode==0x0E and action==4:memory.mem[0x50]|=0x20;memory.mem[0x4F]|=0x80
            if opcode==0x0E and action==37:
                memory.mem[0x73:0x75]=bytes.fromhex('0200');memory.mem[0x80d:0x80f]=bytes.fromhex('fffe')
                memory.mem[0x80c]=255;memory.mem[0x4d]=255
            if opcode==0x0E and action==43 and memory.mem[0x73]&0x40:memory.mem[0x3ffa:0x3ffc]=bytes(2)
        raise AssertionError(f'Board I/O execution budget at {cpu.s.pc:04X}')

    try:
        entries=[(0x7DB6,),(0xD4A3,),(0xD4DA,),(0xCB15,),(0xACA7,),(0xC9F7,),
            (0x7DB6,0x7BAA),(0x7BA7,0xD4A3,0xD4DA),(0x7B14,),(0x7B1B,),(0x7B2F,),
            (0xCB15,0x7DB6,0x7BAA,0x9E99,0x93D0),(0xD4A3,0xD4DA,0xA2B0,0xACA7),
            (0xC9F7,0x7B1B,0xA466),(0x9167,0xCB15,0x7DB6,0xF3EE)]
        for start in entries[mode]:
            invoke(start,{0x7DB6:0x7DF1,0x7BAA:0x7BF5}.get(start,0x7000))
        if cpu.s.pc==0xA5D7:status=6
    except Failure:status=2
    except Missing as e:status=1;unresolved=e.task
    assert all(a in OUTPUT_SET or 0x3C0<=a<0x400 for a,_ in memory.writes),[(hex(a),v) for a,v in memory.writes if a not in OUTPUT_SET and not 0x3c0<=a<0x400]
    return {'status':status,'value':value,'state':[memory.mem[a] for a in OUTPUTS],
            'masked':int(bool(cpu.s.ccr&0x10)),'unresolved':unresolved,'partial':0,
            'coordinates':[0,0],'events':list(memory.events)}

AC={0x400f:4,0x82f:100,0x4d:1,0x36:0,0x4f:0x80,0x41:0,0x52:0,0x16:0,0x06:100,0x62:50,
    0x1d9:20,0x284:0,0x830:0,0x831:1,0x832:0,0x833:0,0x834:0,0x835:0,0x836:0,
    0x4010:100,0x4011:120,0x4012:3,0x4013:2,0x4014:4,0x4015:3,0x4016:2,
    0x4017:80,0x4018:60,0x4019:100,0x401a:220,0x401b:230,0x401c:80,0x401d:60,
    0x401e:40,0x401f:80}|word(0xfd,100)|word(0x4020,2)|word(0x4022,20)

SHIFT={0x400e:7,0x50:0,0x3b:0,0x38f:0,0x390:0,0x4f:0x80,0x06:200,0x1d9:100,0x284:20,
    0x62:120,0x845:2,0x846:3,0x53:0,0x1cc:150,0x511f:20,0x5120:10,0x5121:20,0x5122:200,
    0x5123:2,0x5124:4}|word(0x5f,256)|word(0x847,0)|word(0x3fe0,40)
SHIFT |= {0x5113+i:v for i,v in enumerate([100,50,20,0])}
SHIFT |= {0x5117+i:v for i,v in enumerate([50,80,110,140])}
SHIFT |= {0x511b+i:v for i,v in enumerate([80,120,180,240])}
SHIFT |= {0x5125+i:(32+i*13)&255 for i in range(55)}

counts={}
rng=random.Random(0x31CB15)
counts['initial']=compare((case(mode) for mode in range(15)),'six input groups and direct scheduled joins')
variants=[]
for i in range(4096):
    edits={a:rng.randrange(256) for a in sorted(BASE.keys()|INPUT_CAL|IO_CAL|IAC_CAL|SLOW_CAL|MAIN_CAL|{0x4eb6,0x400f})}
    edits.update({0x400b:0,0x907:0,0x908:[0,4,13,14,17,18,19,20,21,23,24,28,29,30,31,32,33,34,35,36,37,38,39,40,41,43,44,45,46][i%29],0x909:i&1,0x90e:0,0x90f:0})
    variants.append(case(i%15,edits))
counts['variants']=compare(variants,'six-group profile/state/callback variants')
edges=[case(3,AC|word(0x834,65535)|{0x41:mirror,0x36:context,0x16:fault,0x4f:running,
    0x1d9:throttle,0x284:speed,0x832:count,0x52:0x10 if count&1 else 0,0x836:delay})
    for mirror,context,fault,running,throttle,speed,count,delay in product([0,0x10],[0,0x10],[0,0x10],
    [0,0x80],[20,80,81,200],[0,60,255],[0,1,3,255],[0,1,255])]
edges.append(case(4,SHIFT|{0x5113+i:255 for i in range(4)}))
edges.extend(case(8,AC|{2:6,0x06:200,0x1c0:128,0x1c2:128,0x20c:13,0x209:7,
    0x52:1,0x82f:sample,0x44:factory,0x400f:option})
    for sample,factory,option in product([0,39,40,99,100,255],[0,1],[0,4]))
counts['edges']=compare(edges,'AC context, throttle-delay and running/inhibit joins plus fifth-gear loop exit')

counts['map_delta']=compare((case(0,{0x47:0,0x41:0,0x89:0,0x400f:0,0x63:a,0x65:b,
    0x413a:(a+b)&255,0x3e:0xa0,0x50:0x80,0x1c5:3}) for a,b in product(range(256),repeat=2)),
    'every MAP RPM pair and unsigned absolute difference')
counts['map_flags']=compare((case(0,{0x47:0,0x41:0,0x89:0,0x63:100,0x65:100,0x3e:a,0x50:b,0x1c5:1})
    for a,b in product(range(256),repeat=2)), 'all coolant/status bytes and partial A0 masks')
counts['map_hold']=compare((case(0,{0x47:0x40 if a&1 else 0,0x41:0,0x89:0,0x63:100,0x65:100,
    0x3e:0xa0,0x50:0x80,0x1c5:a,0x4139:b}) for a,b in product(range(256),repeat=2)),
    'every MAP hold/reload byte pair and expiry call')
counts['map_context']=compare((case(0,{0x47:old,0x41:ac,0x89:gear,0x400f:option})
    for old,ac,gear,option in product(range(256),[0,0x10],[0,0x20],[0,0x80])),
    'MAP context replacement and option-selected gear mirror')
counts['vss_age']=compare((case(1,{0x80c:count,0x811:age}) for count,age in product(range(256),repeat=2)),
    'all VSS observation-count/age pairs')
counts['vss_division']=compare((case(1,word(0x80d,delta)|word(0x80f,0)|{0x80c:count,0x811:39})
    for delta,count in product(range(65536),[1,142,143,255])),
    'all VSS elapsed words across numerator wrap and FDIV overflow')
counts['vss_filter']=compare((case(2,word(0x812,target)|word(0x284,target^65535)|{0x4e8e:target>>8})
    for target in range(65536)), 'every raw VSS word with split high/fraction filtering')
counts['diagnostic']=compare((case(3,{0x400f:0,0x82f:sample,0x44:factory,0x50:flags})
    for sample,factory,flags in product(range(256),[0,1],[0,8,16,24])),
    'diagnostic input ranges, factory gate and retained feature-off AC')
counts['ac_coolant']=compare((case(3,AC|{0x06:temperature,0x401a:limit,0x401b:limit,
    0x41:0x10 if temperature&1 else 0}) for temperature,limit in product(range(256),repeat=2)),
    'all AC coolant/limit bytes and both mirror states')
counts['ac_rpm']=compare((case(3,AC|{0x62:rpm,0x4017:limit,0x4018:limit,0x4019:limit,
    0x41:0x10 if rpm&1 else 0,0x832:rpm^limit,0x833:(rpm+limit)&255})
    for rpm,limit in product(range(256),repeat=2)), 'all AC RPM thresholds and inhibit routes')
counts['ac_count']=compare((case(3,AC|{0x62:100,0x4019:255,0x832:count,0x4015:limit})
    for count,limit in product(range(256),repeat=2)), 'all AC qualification count/limit byte pairs')
counts['ac_release']=compare((case(3,AC|{0x830:1,0x62:0,0x833:count,0x4016:limit,0x52:0x30})
    for count,limit in product(range(256),repeat=2)), 'all AC release count/limit byte pairs')
counts['ac_throttle']=compare((case(3,AC|word(0x834,count)|word(0x4020,(count*17)&65535)|
    {0x1d9:200,0x4010:0,0x4011:0}) for count in range(65536)),
    'every AC throttle count word with increment/comparison wrap boundaries')
counts['ac_delays']=compare((case(3,AC|{0x830:entry,0x831:exit,0x41:0x10 if exit&1 else 0})
    for entry,exit in product(range(256),repeat=2)), 'all AC entry/exit timer byte pairs')
counts['shift_delta']=compare((case(4,SHIFT|word(0x3fe0,delta)|word(0x5f,period))
    for delta,period in product(range(65536),[0,15,16,256,65535])),
    'all shift counter deltas across fractional/integer divide boundaries')
counts['shift_gain']=compare((case(4,SHIFT|{0x5113:0,0x5117:0,0x511b:gain,0x1d9:throttle,0x5120:0})
    for gain,throttle in product(range(256),repeat=2)),
    'every shift throttle/gain pair with rounding and carry saturation')
counts['shift_curves']=compare((case(4,SHIFT|{0x5113:0,0x5117:0,0x5122:255,0x62:rpm,0x1cc:baro,
    0x53:4 if baro&1 else 0}) for rpm,baro in product(range(256),repeat=2)),
    'all shift RPM/baro bytes and both lamp-selected overlapping table views')
counts['shift_modes']=compare((case(4,SHIFT|{0x400e:option,0x50:diagnostic,0x4f:running,
    0x3b:service,0x38f:enable,0x390:value,0x845:gear})
    for option,diagnostic,running,service,enable,value,gear in product([3,7],[0,0x10],[0,0x80],
    [0,0x10],[0,1],[0,1],range(256))), 'shift disable, diagnostic/service overrides and retained gear bytes')
counts['environment']=compare((case(5,{0x06:coolant,0x283:index,0x3f:0x40 if index&1 else 0,
    0x48e3:index,0x48e8:(coolant+index)&255}) for coolant,index in product(range(256),repeat=2)),
    'all environmental coolant/index pairs and conditional subtract routes')
counts['environment_cap']=compare((case(5,{0x06:coolant,0x475f:cap})
    for coolant,cap in product(range(256),repeat=2)), 'all environmental cap-before-offset byte pairs')

joined=[]
for i in range(2048):
    edits={a:rng.randrange(256) for a in sorted(BASE.keys()|INPUT_CAL|IO_CAL|IAC_CAL|SLOW_CAL|MAIN_CAL|{0x4eb6,0x400f})}
    edits.update({0x907:0,0x90e:0,0x90f:0,0x400b:0,0x908:[0,4,13,14,17,18,19,20,21,23,24,28,29,30,31,32,33,34,35,36,37,38,39,40,41,43,44,45,46][i%29]})
    joined.append(case(8+i%7,edits))
for mode,action,mirror in product([3,4,7,8,9,10,11,12,13,14],[0,20,21,44,45,46],[0,0x10]):
    joined.append(case(mode,SHIFT|AC|{0x41:mirror,0x908:action,0x3ffa:4,0x3ffb:0}))
counts['joined']=compare(joined,'ordered producer/consumer, slot6/7/9 and hardware callback joins')
failures=[]
for item in joined[::7]:
    for fail in range(1,len(execute(item)['events'])+1):failures.append((item[0],item[1]|{0x907:fail}))
counts['failures']=compare(failures,'all selected completed mask/read/delay/write/dependency failure prefixes')
history=[];edits=SHIFT|AC|{0x400b:0,0x86:0xa0,0x4f:0xf5,0x4b:0x10,0x47:0,0x6f:0,
    0x907:0,0x90e:0,0x90f:0,0x908:0,0xa7:130,0x73:0,0x74:0,0x3e:0xa0}
for entry in range(1024):
    edits.update({2:entry%160,0x3064:(entry//7)&255,0x82f:entry&127,0x82e:(entry*7)&255,
        0x1d9:entry&127,0x62:entry&255,0x06:(entry*3)&255,0x283:(entry*5)&255,
        0x908:[0,44,45,46][entry%4]})
    edits.update(word(0x3ffa,[0,0x0400,0x4000,0x4400][entry%4]))
    edits.update(word(0x3fc4,(entry*257)&65535));edits.update(word(0x3fe0,(entry*631)&65535))
    item=case([6,7,8,9,10,11,12,13,14][entry%9],dict(edits));history.append(item)
    edits.update(dict(zip(OUTPUTS,execute(item)['state'])))
counts['history']=compare(history,'retained input/MAP/VSS/AC/IAC/lamp/environmental histories')
required=set()
for start,end in [(0x7db6,0x7df1),(0xd4a3,0xd4eb),(0xcb15,0xcc35),(0xaca7,0xadaa),
    (0xc9f7,0xca6b),(0xcb14,0xcb15),(0xf436,0xf459),(0xf499,0xf4a4),(0xf4bd,0xf4de)]:
    pc=start
    while pc<end:required.add(pc);pc=decode(rom.read,pc).next_pc
assert required<=coverage,','.join(f'{a:04X}' for a in sorted(required-coverage))
print(f'{sum(counts.values()):,} six-group input comparisons; all {len(required)} scoped instruction starts; '
      f'{len(INPUT_CAL)} checked source-profile bytes and12 density backing knots match stock. '
      'Physical device behavior, target ABI/timing and unported callers remain separate.')
