"""Compare the resident main IAC and its callees with actual BMHM instructions.

1803/180F/1812 use named well-formed return fixtures, never a guessed machine ABI.
Joined calls supply their own admissions and do not synthesize acquisition or steps.
"""
from pathlib import Path
_prior=Path(__file__).with_name('compare_iac_slow_rom.py')
exec(compile(_prior.read_text().rsplit('\ncounts={}',1)[0],str(_prior),'exec'),globals())
MAIN_EXTRA=[77, 82, 162, 912, 918, 2146, 2147, 2148, 2153, 2157, 2158, 2159, 2160, 2161, 2162, 2163, 2164, 2169, 2170, 2173, 2174, 2175, 2185, 2186, 2187, 2188]
MAIN_CAL=set([20112, 20113, 20114, 20115, 20116, 20117, 20118, 20119, 20120, 20121, 20122, 20123, 20124, 20125, 20126, 20127, 20128, 20129, 20130, 20131, 20132, 20133, 20134, 20135, 20136, 20137, 20138, 20139, 20140, 20141, 20142, 20143, 20144, 20145, 20146, 20147, 20148, 20149, 20152, 20154, 20162, 20163, 20164, 20165, 20166, 20167, 20168, 20169, 20170, 20171, 20172, 20173, 20174, 20175, 20176, 20177, 20178, 20179, 20180, 20181, 20182, 20183, 20184, 20185, 20186, 20187, 20188, 20189, 20190, 20191, 20210, 20211, 20212, 20213, 20214, 20215, 20216, 20217, 20218, 20219, 20220, 20221, 20222, 20223, 20224, 20225, 20226, 20227, 20228, 20229, 20230, 20231, 20232, 20233, 20234, 20235, 20236, 20237, 20238, 20239, 20240, 20241, 20242, 20243, 20244, 20245, 20246, 20247, 20248, 20252, 20253, 20254, 20255, 20256, 20259, 20260, 20261, 20262, 20263, 20264, 20265, 20266, 20267, 20268, 20269, 20270, 20271, 20334, 20335, 20336, 20337, 20338, 20339, 20340, 20341, 20342, 20343, 20344, 20345, 20346, 20347, 20348, 20349, 20350, 20351, 20352, 20353, 20354, 20370, 20371, 20372, 20373, 20374, 20375, 20376, 20377, 20378, 20379, 20380, 20381, 20382, 20383, 20384, 20385, 20386, 20387, 20388, 20389, 20390, 20391, 20392, 20393, 20394, 20395, 20396, 20397, 20398, 20399, 20400, 20401, 20402, 20403, 20404, 20405, 20406, 20407, 20408, 20409, 20410, 20411, 20412, 20413, 20414, 20425, 20426, 20427, 20428, 20429, 20430, 20431, 20432, 20433, 20434, 20435, 20436, 20437, 20438, 20439, 20440, 20441, 20442, 20443, 20444, 20445, 20446, 20447, 20448, 20449, 20450, 20451, 20452, 20453, 20454, 20455, 20456, 20457, 20458, 20459, 20460, 20461, 20462, 20463, 20464, 20465, 20466, 20467, 20468, 20469, 20470, 20471, 20472, 20473, 20474, 20475, 20476, 20477, 20478, 20479, 20480, 20481, 20482, 20483, 20484, 20485, 20486, 20487, 20488, 20489, 20490, 20491, 20492, 20493, 20494, 20495, 20496, 20497, 20498, 20499, 20500, 20501, 20502, 20503, 20504, 20505, 20506, 20507, 20508, 20509, 20510, 20511, 20512, 20513, 20514, 20515, 20516, 20517, 20518, 20519, 20520, 20521, 20522, 20523, 20524, 20525, 20526, 20527, 20528, 20529, 20530, 20531, 20532, 20533, 20534, 20535, 20536, 20537, 20538, 20539, 20540, 20541, 20542, 20543, 20544, 20545, 20546, 20547, 20548, 20549, 20550, 20551, 20552, 20553, 20554, 20555, 20556, 20561, 20562, 20563, 20564, 20565, 20566, 20642, 20643, 20644, 20645, 20646, 20647, 20648, 20649, 20650, 20651, 20652, 20653, 20654, 20655, 20656, 20657, 20658, 20659, 20660, 20661, 20662, 20663, 20664, 20665, 20666, 20667, 20668, 20669, 20674, 20675, 20676, 20677, 20678, 20680, 20681, 20692])
OUTPUTS=OUTPUTS+MAIN_EXTRA
assert len(OUTPUTS)==len(set(OUTPUTS))
OUTPUT_SET=set(OUTPUTS)
BASE=BASE|{a:(a*29+61)&255 for a in MAIN_EXTRA}
BASE=BASE|{2:3,0x09:4,0x16:0,0x36:0x0c,0x37:0,0x38:0x80,0x39:0,0x3b:0,0x3e:0,
    0x41:0,0x44:0xC4,0x4f:0xF5,0x50:0,0x52:0,0x86:0xA0,0xa2:0x40,0x4d:0x80,
    0x390:0,0x391:0,0x395:0,0x396:0,0x38f:0,0x864:0,0x869:0,0x86b:0,0x87b:0,
    0x879:0,0x87a:0,0x877:0,0x876:0,0x900:0x34,0x901:0x56,0x90f:0,0x908:0}
BASE=BASE|word(0x862,0x1234)|word(0x871,0x0800)|word(0x873,0x1000)|word(0x86e,0x8011)|word(0x87d,0x1200)|word(0x88b,0x1234)
main_defaults=json.loads(subprocess.check_output([binary,'--iac-main-defaults'],text=True))
assert {a for a,_ in main_defaults}==MAIN_CAL
for a,v in main_defaults:assert v==rom.read(a,1)[0],(hex(a),v)
main_backing=json.loads(subprocess.check_output([binary,'--main-backing'],text=True))
assert len(main_backing)==768
for a,v in main_backing:assert v==rom.read(a,1)[0],(hex(a),v)
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
    status=unresolved=value=0
    if mode==9:cpu.s.a,cpu.s.b=memory.mem[0x900],memory.mem[0x901]
    if mode==11:cpu.s.a=memory.mem[0x900];cpu.s.x=0x4ea3

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
            coverage.add(pc);opcode=memory.mem[pc]
            if opcode in (0x0E,0x0F):memory.record('M',0,0,int(opcode==0x0F))
            cpu.step()
            if opcode==0x0E and action==4:memory.mem[0x50]|=0x20;memory.mem[0x4F]|=0x80
        raise AssertionError(f'Main IAC execution budget at {cpu.s.pc:04X}')

    try:
        entries=[(0x93D0,0x7000),(0x92A4,0x7000),(0x9411,0x7000),(0x9537,0x969E),
                 (0x969E,0x9749),(0x99C5,0x7000),(0x9C20,0x7000),(0x9CA6,0x7000),
                 (0x9752,0x7000),(0x983D,0x7000),(0xA407,0x7000),(0xF4A4,0x7000),
                 (0x93D0,0x7000),(0x9E99,0x7000),(0xA2B0,0x7000),(0x93D0,0x7000),(0x93D0,0x7000)]
        invoke(*entries[mode])
        if mode==12:memory.mem[2]=7;invoke(0x9E99)
        if mode in (13,14):memory.mem[2]=3;invoke(0x93D0)
        if mode==15:memory.mem[2]=9;invoke(0xA2B0)
        if mode==16:memory.mem[2]=8;invoke(0xA466)
        if mode==11:value=cpu.s.a
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
                Path('/tmp/iac-main-failure.json').write_text(json.dumps({'item':item,'actual':actual,'expected':expected,'outputs':OUTPUTS}))
                differences=[(hex(a),x,y) for a,x,y in zip(OUTPUTS,actual['state'],expected['state']) if x!=y]
                raise AssertionError((label,count+index,item[0],differences,{k:(actual[k],expected[k]) for k in actual if k!='state' and actual[k]!=expected[k]}))
        count+=len(chunk)
    print(f'{count:,} {label} match.',flush=True);return count


counts={}
rng=random.Random(0x3193D0)
variants=[]
for i in range(4096):
    edits={a:rng.randrange(256) for a in sorted(BASE.keys()|MAIN_CAL|IAC_CAL|SLOW_CAL)}
    edits.update({0x908:[0,23,24][i%3],0x909:i&1,0x90F:0,0x907:0})
    variants.append(case(i%16,edits))
counts['variants']=compare(variants,'main IAC state/profile variants')
counts['initial']=compare((case(mode) for mode in range(17)),'main IAC direct entries and joined defaults')


def conversion_cases():
    for value in range(65536):yield case(9,word(0x900,value))
    # Unity BARO transform with falling/wrapped position knots.
    edits={0x4E8F:0,0x4EA3:0,0x4EA4:0,0x4EA5:0,0x4EA6:128,0x4EA7:128}
    edits.update({0x4E92+i:(255-11*i)&255 for i in range(18)})
    #4EA3 is the endpoint neighbor as well as the BARO descriptor offset.
    edits[0x4EA3]=0
    for value in range(65536):yield case(9,edits|word(0x900,value))
counts['conversion']=compare(conversion_cases(),'every flow word with stock and wrapped falling position tables')
counts['startup']=compare((case(2,{0x283:coolant,0x4E8F:options,0x06:coolant,0x4E91:128})
    for coolant,options in product(range(256),repeat=2)), 'startup coolant/options and retained byte-store cases')
counts['seeds']=compare((case(1,{0x4EB1:base,0x4EB2:255-base,0x4EB3:add,0x4EB4:255-add,
    0x06:base,0x4EB5:128}) for base,add in product(range(256),repeat=2)),
    'default cell high-byte, retained fraction and saturated AC-add cases')


def derivative_cases():
    for ratio,old,signs in product(range(256),range(256),range(4)):
        yield case(7,word(0x86E,(old<<8)|((ratio*17+old)&255))|
                   {0x6C:ratio,0x37:0x80 if signs&1 else 0,0x36:0x80 if signs&2 else 0})
counts['derivative']=compare(derivative_cases(),'every ratio/old-high/D-sign/RPM-sign combination')
counts['proportional']=compare((case(6,{0x858:error,0x36:context,0x284:speed,0x37:prior})
    for error,context,speed,prior in product(range(256),[0,1,2,3,8,9,10,11,128,129,130,131,136,137,138,139],
        [0,9,10,11,19,20,21,255],[0,0x40])), 'P curve selection, speed hysteresis and error-coordinate cases')


def integral_cases():
    for error,current,high in product(range(256),range(256),[0,128]):
        edits={0x858:error,0x36:high|4,0x885:255,0x4EF2:255,0x4EF3:255,0x1D9:0,0x284:0,0x864:0,
               0x866:0,0x867:0,0x868:0,0x3e:0,0x37:0,0x50C2:255,0x87b:0,0x86b:0,
               0x29f:(current+error)&255,0x09:4}
        edits|=word(0x29d,(current<<8)|((current*13+error)&255))|word(0x2a3,0x1000)|word(0x2a5,0x2000)
        yield case(5,edits)
    # Qualification countdown and one-byte position reconciliation, with no phase service.
    for context,delay,hold,low,flow,state,phase in product([0,1,2,3,4,5,6,7,128,129,130,131,132,133,134,135],
            [0,1,2],[0,1],[0,4],[0,1,65535],[0,4,0x40],[0,11,12,159]):
        yield case(5,{0x36:context,0x864:delay,0x866:hold,0x867:hold,0x3E:low,0x09:state,
            0x885:255,0x4EF2:255,0x4EF3:255,0x1D9:0,0x284:0,0x877:0,0x87A:0,0x37:4,0x858:60,
            0x06:255,0x50C2:0,0x50C3:0,0x50C4:0,0x50C5:0,0x50C6:12,2:phase,0x7:0}|word(0x88B,flow))
counts['integral']=compare(integral_cases(),'integral/cold allocation, admission expiry, saturation and count reconciliation')


def context_cases():
    for before,gear,ac,options in product(range(256),[0,0x10,0x40,0x50],[0,0x20],[0,1,0x40,0x41]):
        yield case(3,{0x36:before,0xa2:gear,0x52:ac,0x4E8F:options,0x38:before,
                      0x400F:0x40 if before&4 else 0,0x41:0x20 if before&8 else 0,
                      0x06:0 if before&16 else 255,0x877:0 if before&32 else 1})
    for current,other in product(range(256),repeat=2):
        yield case(3,{0x36:(current>>6)&3,0x52:0x20 if other&1 else 0,0xa2:0x40 if other&2 else 0,
            0x877:0,0x06:0,0x4f29:1,0x4f2a:current,0x4f2b:other,0x4f2c:other,0x4f2d:current,
            0x4f24:current,0x4f25:other,0x4f27:other,0x4f28:current,0x4F0F:other,0x4F1C:current,
            0x38:0x1f,0x4e8f:0,0x29d:current,0x2a0:other,0x2a7:other,0x2aa:current})
counts['context']=compare(context_cases(),'gear/AC shared context, wrapped delay math and pending transfers')
counts['service']=compare((case(10,{0x395:flags,0x38f:kicker,0x390:value,0x391:reset,0x44:ignition,0x09:state,
    0x396:(flags*17+state)&255}) for flags,kicker,value,reset,ignition,state in product(range(256),[0,64],[0,64],[0,32],[0xC4,0xD4],[0,1])),
    'service selection, nonlocal exits, desired override and raw kicker setters')
counts['root_reset']=compare((case(0,{0x09:state,0x7:position,0x44:0xD4,0x3b:0})
    for state,position in product(range(256),range(256))), 'reset/completion/park root and default seeding')

# Directed route coverage, including retained cold, VSS floor, zero increment,
# startup/switch consumption, extension failure and saved service-RPM state.
directed=[]
for i in range(4096):
    edits={a:rng.randrange(256) for a in sorted(BASE.keys()|MAIN_CAL|IAC_CAL|SLOW_CAL)}
    edits.update({0x908:[0,23,24][i%3],0x909:i&1,0x90F:0,0x907:0,0x86:0xA0 if i&1 else 0xE0})
    directed.append(case([0,12,13,14,15][i%5],edits))
for error,cell,cold,flags,mode in product([0,1,4,5,16,17,40,41,255],[0,1,65535],[0,1,65535],[0,0x10],[0,128]):
    directed.append(case(5,{0x36:mode|4,0x858:error,0x16:flags,0x885:255,0x4EF2:255,0x4EF3:255,
        0x1D9:0,0x284:0,0x864:0,0x866:0,0x867:0,0x868:0,0x3e:0,0x37:0,
        0x50C2:255,0x87b:0,0x86b:0,0x29f:255,0x09:4}|word(0x29d,cell)|word(0x2a3,cold)|word(0x2a5,65535)))
for tps,flow,dfco,option,kicker in product([0,255],[0,1,0x3fff,0x4000,0x8000,65535],[0,8],[0,4],[0,4]):
    directed.append(case(8,{0x1D9:tps,0x46:dfco,0x4e8f:option,0x37:kicker,0x50A9:255,0x50A8:0,
        0x50AC:255 if tps else 0,0x38:0x20,0x3d:0x20,0x50AA:0x80,0x50AB:1}|
        word(0x862,flow)|word(0x871,flow)|word(0x87d,flow)|word(0x880,flow)))
# Explicitly admit integral routes; random profiles usually close these gates.
for context,tps,speed,filter_high,delay,hold,manual,low in product([0,4,0x80,0x84],
        [0,255],[0,255],[0,255],[0,1],[0,1],[0,1],[0,4]):
    directed.append(case(5,{0x36:context,0x1D9:tps,0x284:speed,0x882:filter_high,0x883:0,
        0x885:0,0x864:delay,0x866:hold,0x867:hold,0x877:0,0x87A:0,0x4E8F:manual,
        0x4EF2:128,0x4EF3:128,0x4EF4:1,0x3e:low,0x37:0,0x868:0}))
for high,stall,error,current,cold,snapshot,increment in product([0,128],[0,16],[0,255],
        [0,1,0x4000,65535],[0,1,0x4000,65535],[0,255],[0,255]):
    edits={0x36:high|stall|4,0x885:255,0x864:0,0x866:0,0x867:0,0x868:255 if stall else 0,
        0x4EF2:255,0x4EF3:255,0x1D9:0,0x284:0,0x3e:0,0x37:0,0x16:0,0x858:error,
        0x50C2:255,0x29f:snapshot,0x87b:0,0x86b:0,0x09:4}
    edits.update({a:increment for a in range(0x4f92,0x4fbf)})
    directed.append(case(5,edits|word(0x29d,current)|word(0x2a3,cold)|word(0x2a5,65535)))
for adder,increment,startup in product([1,2,128,255],[0,1,2,128,255],[False,True]):
    edits={0x36:0x84,0x885:255,0x864:0,0x866:0,0x867:0,0x868:0,0x3e:0,0x37:0,
        0x4EF2:255,0x4EF3:255,0x1D9:0,0x284:0,0x858:255,0x87b:0 if startup else adder,
        0x86b:adder if startup else 0}
    edits.update({a:increment for a in range(0x4f9d,0x4fa9)})
    directed.append(case(5,edits))
# Direct high/low count correction, including wrap and service/mode vetoes.
for high,phase,service,mode,position in product([0,128],[0,11,12,159],[0,16],[0,16],[0,255]):
    directed.append(case(5,{0x36:high|4,0x885:255,0x864:0,0x866:0,0x867:0,0x868:0,0x37:0,
        0x3e:0,0x4EF2:255,0x4EF3:255,0x1D9:0,0x284:0,0x858:255,0x06:255,0x50C2:0,
        0x50C3:0,0x50C4:0,0x50C5:0,0x50C6:12,0x09:4,0x7:position,2:phase,
        0x3b:service,0x50:mode,0x87b:0,0x86b:0,0x16:0}|word(0x29d,0 if high else 65535)|word(0x2a3,0)))
# Admit every bank/AC variant, including first-stall overflow and VSS floors.
for context,high,fault,cold in product(range(4),[0,128],[0,0x10],[0,1,65535]):
    edits={0x36:context|high|4,0x885:255,0x864:0,0x866:0,0x867:0,0x868:0,0x37:0,0x3e:0,
        0x4EF2:255,0x4EF3:255,0x1D9:0,0x284:0,0x858:255,0x16:fault,0x50C2:255,
        0x87b:0,0x86b:0,0x09:4,0x29f:255,0x2a2:255,0x2a9:255,0x2ac:255}
    for a in [0x29d,0x2a0,0x2a7,0x2aa]:edits|=word(a,0x4000)
    for a in [0x2a3,0x2ad]:edits|=word(a,cold)
    for a in [0x2a5,0x2af]:edits|=word(a,65535)
    directed.append(case(5,edits))
    directed.append(case(5,edits|{0x868:255,0x63:0,0x5051:255,0x5052:255,0x5053:255,0x5054:255}|
        word(0x29d,65535)|word(0x2a0,65535)|word(0x2a7,65535)|word(0x2aa,65535)))
    directed.append(case(5,edits|{0x06:255,0x50C2:0,0x50C3:0,0x50C4:0}))
counts['joined']=compare(directed,'joined main/background/slow, flow saturation and flag-history witnesses')
failures=[]
for item in directed:
    events=execute(item)['events']
    for fail in range(1,len(events)+1):failures.append((item[0],item[1]|{0x907:fail}))
counts['failures']=compare(failures,'optional module and joined-I/O failure prefixes')
counts['missing']=compare((case(0,{0x86:0xE0,0x38:0x40,0x90F:4,0x908:action})
    for action in [0,23,24]),'missing1803 before any resident writes')
history=[];edits={0x09:4,0x36:4,0x38:0,0x39:0,0x37:0,0x44:0xC4,0x4f:0xf5,0x3b:0,
    0x86:0xa0,0x87b:0,0x86b:0,0x16:0,0x17:0,0x3e:0,0x90f:0}
for tick in range(1024):
    edits.update({2:(3+4*tick)%160,0x63:(tick*3)&255,0x1D9:(tick//13)&31,0x284:(tick//7)&31,
        0xa2:0x40 if tick&16 else 0,0x52:0x20 if tick&32 else 0,0x06:180,0x6c:(tick*5)&255})
    item=case([0,12,13,14,15][tick%5],dict(edits));history.append(item)
    edits.update(dict(zip(OUTPUTS,execute(item)['state'])))
counts['history']=compare(history,'retained main/background/slow controller histories')
required=set()
for start,end in [(0x92a4,0x92f1),(0x93d0,0x989c),(0x99c5,0x9c96),(0x9ca6,0x9cfd),(0xa407,0xa466),(0xf4a4,0xf4b6)]:
    pc=start
    while pc<end:required.add(pc);pc=decode(rom.read,pc).next_pc
missing=required-coverage
if missing:raise AssertionError('Unexercised instruction starts: '+','.join(f'{a:04X}' for a in sorted(missing)))
print(f'{sum(counts.values()):,} main-IAC comparisons; all {len(required)} scoped instruction starts; '
      f'{len(MAIN_CAL-(IAC_CAL|SLOW_CAL))} new source bytes and all overlapping views match BMHM. '
      'Physical stepping and target ABI remain separate work.')
