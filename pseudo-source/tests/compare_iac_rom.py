"""Compare resident desired RPM/background IAC and their caller with stock BMHM.

Only unsupplied180C/180F/1812 and the not-yet-ported ACA7 use return fixtures.
Mode12 supplies a subsequent normal phase8 call, not the intervening input work.
"""
from pathlib import Path
_prior=Path(__file__).with_name('compare_slot7_rom.py')
exec(compile(_prior.read_text().rsplit('\ncounts={}',1)[0],str(_prior),'exec'),globals())
_SlotMemory=Memory
IAC_EXTRA=[9, 55, 56, 57, 62, 562, 583, 584, 643, 669, 670, 671, 672, 673, 674, 675, 676, 677, 678, 679, 680, 681, 682, 683, 684, 685, 686, 687, 688, 689, 690, 758, 759, 911, 2136, 2137, 2138, 2139, 2140, 2143, 2144, 2145, 2150, 2151, 2152, 2154, 2165, 2166, 2167, 2168, 2183, 2184, 2189, 2191, 2192, 2193, 2194, 2195, 2196, 2197, 2198, 2199, 2200, 2201, 2202]
IAC_CAL=set([20111, 20156, 20157, 20158, 20159, 20160, 20161, 20188, 20189, 20190, 20191, 20192, 20193, 20194, 20195, 20196, 20197, 20198, 20199, 20200, 20201, 20202, 20203, 20204, 20205, 20206, 20207, 20208, 20209, 20257, 20258, 20274, 20275, 20276, 20277, 20278, 20279, 20280, 20281, 20282, 20283, 20284, 20285, 20286, 20287, 20288, 20289, 20290, 20291, 20292, 20293, 20294, 20295, 20296, 20297, 20298, 20299, 20300, 20301, 20302, 20303, 20304, 20305, 20306, 20307, 20308, 20309, 20310, 20311, 20312, 20313, 20314, 20315, 20316, 20317, 20318, 20319, 20320, 20321, 20322, 20323, 20324, 20325, 20326, 20327, 20328, 20329, 20330, 20331, 20332, 20333, 20334, 20335, 20349, 20355, 20356, 20357, 20358, 20359, 20360, 20361, 20362, 20363, 20364, 20365, 20366, 20367, 20368, 20369, 20414, 20415, 20416, 20417, 20418, 20419, 20420, 20421, 20422, 20557, 20558, 20559, 20560, 20670, 20671, 20679, 20682, 20683, 20684, 20685, 20686, 20687, 20688, 20689, 20690, 20691, 20693, 20695])
OUTPUTS=OUTPUTS+IAC_EXTRA
assert len(OUTPUTS)==len(set(OUTPUTS))==213
OUTPUT_SET=set(OUTPUTS)
IAC_STATE=set(IAC_EXTRA)|{0x36,0x18,0x4B}
BASE=BASE|{a:(a*53+97)&255 for a in IAC_EXTRA}
BASE=BASE|{0x02:7,0x09:0x85,0x18:0xBD,0x36:0x0C,0x37:0xA0,0x38:0x80,0x39:0xA4,0x3E:0,0x3B:0xA5,
    0x4F:0xF5,0x283:160,0x232:40,0x247:17,0x248:100,0x858:1,0x859:1,0x85A:17,
    0x85B:1,0x85C:0,0x85F:100,0x860:0,0x861:1,0x875:5,0x876:8,0x877:0,0x878:1,
    0x887:8,0x888:1,0x88D:0,0x38F:0xA5,0x3008:0}
BASE=BASE|word(0x29D,0x1020)|word(0x2A0,0x2020)|word(0x2A3,0x1000)|word(0x2A5,0x2000)|\
    word(0x2A7,0x3020)|word(0x2AA,0x5020)|word(0x2AD,0x2000)|word(0x2AF,0x1800)
iac_defaults=json.loads(subprocess.check_output([binary,'--iac-defaults'],text=True))
assert len(iac_defaults)==137 and {a for a,_ in iac_defaults}==IAC_CAL
for a,v in iac_defaults:assert v==rom.read(a,1)[0],(hex(a),v)


class Memory(_SlotMemory):
    def read8(self,a):
        if a!=0x3008:return super().read8(a)
        value=FixtureMemory.read8(self,a);self.record('R',8,a,value)
        if self.mem[0x908]==19:
            self.mem[0x36]=(self.mem[0x36]&0x20)|3;self.mem[0x857]=250
            self.mem[0x85F]=0x55;self.mem[0x860]=7;self.mem[0x861]=2
        return value


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

    def invoke(start,stop=0x7000):
        sp=cpu.s.sp;cpu.s.pc=start
        if stop==0x7000:cpu._push16(0x7000)
        for _ in range(5000):
            pc=cpu.s.pc
            if pc==stop:
                assert cpu.s.sp==sp,(hex(start),hex(cpu.s.sp),hex(sp));return
            if pc==0xA5D7:return
            action=memory.mem[0x908]
            if pc in (0x180C,0xACA7):
                bit,task={0x180C:(1,4),0x9E99:(2,5),0xACA7:(4,6)}[pc]
                if memory.mem[0x90E]&bit:raise Missing(task)
                memory.record('T',0,pc,action)
                if pc==0x180C:
                    if action==13:memory.mem[0x86]|=0x40;memory.mem[0x4C]^=0x55
                    if action==14:memory.mem[0x86]&=0xBF;memory.mem[0x06]=32
                elif pc==0x9E99 and action==15:
                    memory.mem[0x06]=200;memory.mem[0x3D]|=0x20;memory.mem[0x278]=123
                    memory.mem[0x22F]=140;memory.mem[0x1C0]=128;memory.mem[0x62]=180;memory.mem[0x19]|=0x10
                elif pc==0xACA7 and action==16:
                    memory.mem[0x1EE:0x1F0]=bytes.fromhex('beef');memory.mem[0x4C]^=0xA0
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
        entries=[(0x989C,0x7000),(0x920E,0x7000),(0x9226,0x7000),(0x9EA3,0x9EEA),
                 (0x9EEA,0x9FDE),(0x9FDE,0xA12D),(0xA12D,0xA154),(0xA154,0xA288),
                 (0xA288,0x7000),(0xA29A,0x7000),(0x9E99,0x7000),(0x7B1B,0x7000),(0x7B1B,0x7000)]
        invoke(*entries[mode])
        if mode==12:memory.mem[0x02]=8;invoke(0xA466)
        if cpu.s.pc==0xA5D7:status=6
    except Failure:status=2
    except Missing as e:status=1;unresolved=e.task
    assert all(a in OUTPUT_SET or 0x3C0<=a<0x400 for a,_ in memory.writes)
    return {'status':status,'value':0,'state':[memory.mem[a] for a in OUTPUTS],
            'masked':int(bool(cpu.s.ccr&0x10)),'unresolved':unresolved,'partial':0,
            'coordinates':[0,0],'events':list(memory.events)}


def compare(items,label):
    iterator=iter(items);count=0
    while chunk:=list(islice(iterator,512)):
        payload=[]
        for mode,edits in chunk:
            fields=[mode,len(edits)]
            for a,v in edits.items():fields.extend((a,v))
            payload.append(' '.join(map(str,fields)))
        p=subprocess.run([binary],input='\n'.join(payload)+'\n',text=True,capture_output=True,check=True)
        lines=p.stdout.splitlines();assert len(lines)==len(chunk),(label,p.stderr)
        for i,(item,line) in enumerate(zip(chunk,lines)):
            actual=json.loads(line);expected=execute(item)
            if actual!=expected:
                diffs=[(hex(a),v,w) for a,v,w in zip(OUTPUTS,actual['state'],expected['state']) if v!=w]
                scalars={k:(actual[k],expected[k]) for k in actual if k!='state' and actual[k]!=expected[k]}
                raise AssertionError((label,count+i,'mode',item[0],'state',diffs,'other',scalars,'edits',item[1]))
        count+=len(chunk)
    print(f'{count:,} {label} match.',flush=True);return count


counts={}
rng=random.Random(0x319E99)
smoke=[]
for i in range(1024):
    edits={a:rng.randrange(256) for a in sorted(BASE.keys()|IAC_CAL)}
    edits.update({0x908:i%20,0x909:i&1})
    smoke.append(case(i%11,edits))
counts['smoke']=compare(smoke,'IAC calibration/state variants')


def desired_cases():
    for flags,temperature,startup in product(range(256),range(256),[0,0x81]):
        yield case(0,{0x36:flags,0x283:temperature,0x85C:startup,0x38:0x80})
    for timer,limit,phase in product(range(256),range(256),[7,0x17]):
        yield case(0,{0x85B:timer,0x4F88:limit,0x02:phase,0x38:0x80,0x06:255,0x4F89:0,0x85F:0})
    for offset,delay,switch in product(range(256),range(256),[0,4]):
        yield case(0,{0x860:offset,0x861:delay,0x3008:switch,0x4E8F:0x9E,0x4F8E:255,
                      0x38:0x80,0x857:77,0x85F:100})


def movement_cases():
    for value in range(65536):
        yield case(3,word(0x2A3,value)|word(0x2AD,65535-value)|
                   {0x09:0xA5,0x284:1,0x4EC0:0,0x4EC1:value>>8})
    for amount,divider in product(range(256),repeat=2):
        yield case(3,{0x887:amount,0x888:divider,0x38:0xA0,0x46:0})


def kicker_cases():
    for flags,timer,phase in product(range(256),range(256),[7,0x17]):
        yield case(4,{0x36:flags,0x37:flags^0x55,0x88D:timer,0x02:phase,0x06:200,0x38F:0})
    for a,b in product(range(256),repeat=2):
        yield case(2,{0x37:0xA0,0x2B1:a,0x50D5:b,0x2F7:a^b})
        yield case(1,{0x37:a,0x88D:b,0x36:0xAA,0x4B:a^b})


def cold_cases():
    for value in range(65536):
        yield case(5,word(0x2A5,value)|word(0x2AF,65535-value)|word(0x2A3,value^0x8000)|
                   word(0x2AD,(value*73)&65535)|{0x875:0,0x4EBD:value>>8,0x4EBE:255,0x4EBF:128})
    for current,other,bank in product(range(256),range(256),[0,1]):
        edits=word(0x2A3,current<<8)|word(0x2AD,other<<8) if bank==0 else word(0x2AD,current<<8)|word(0x2A3,other<<8)
        yield case(5,edits|{0x36:2*bank,0x875:1,0x4EEE:128,0x4EEF:128,0x4EF0:128,0x4EF1:128})
    for flags,coolant in product(range(256),repeat=2):
        yield case(5,word(0x2A5,0xFF)|word(0x2AF,0xFF)|{0x36:flags,0x06:coolant,0x858:0,0x859:0})


def transfer_cases():
    for park,drive,context in product(range(256),range(256),[8,9,10,11]):
        yield case(7,word(0x29D,park<<8)|word(0x2A0,(park<<8)|255)|
                   word(0x2A7,drive<<8)|word(0x2AA,(drive<<8)|255)|{0x36:context,0x3E:0})
    for difference,context in product(range(65536),[8,9,10,11]):
        ac=(0x8000+difference)&65535
        yield case(7,word(0x29D,0x8000)|word(0x2A0,ac)|word(0x2A7,0x8000)|word(0x2AA,ac)|
                   {0x36:context,0x3E:0,0x4FC1:0,0x4FC2:127,0x4FC3:1,0x4FC4:128})


counts['desired']=compare(desired_cases(),'desired RPM/context/expiry/switch C/ROM cases')
counts['movement']=compare(movement_cases(),'movement word/gain and DFCO divider C/ROM cases')
counts['kicker']=compare(kicker_cases(),'kicker timer/flags and enable/disable C/ROM cases')
counts['kicker_qualification']=compare((case(4,word(0x2A7,0)|{0x36:0x8C|2*bank,0x37:0xA4,
    0x06:200,0x38F:0,0x2F4:100,0x50CF:255,0x858:error,0x50D1:limit,0x50D2:limit})
    for bank,error,limit in product([0,1],range(256),[0,1,8,128,255])),
    'kicker low-BARO/undersized-cell/error qualification C/ROM cases')
counts['cold']=compare(cold_cases(),'cold bounds/transfer/warm-snapshot C/ROM cases')
counts['transfer']=compare(transfer_cases(),'queued gear/AC word-transfer C/ROM cases')
counts['decay']=compare((case(6,{0x876:a,0x878:d,0x36:1,0x877:0}) for a,d in product(range(256),repeat=2)),
                        'AC transition amount/divider C/ROM cases')
joined=[]
for i in range(2048):
    edits={a:rng.randrange(256) for a in sorted(BASE.keys()|IAC_CAL)}
    edits.update({0x908:i%20,0x909:i&1,0x90E:i&5,0x90A:int(i%13==0),0x90D:int(i%17==0)})
    edits.update(word(0x1800,0x7E18 if i%3 else 0))
    joined.append(case([0,5,7,8,9,10,11,12][i%8],edits))
for mode,action,switch in product([0,10,11,12],range(20),[0,4]):
    joined.append(case(mode,{0x908:action,0x3008:switch,0x4E8F:0x9E,0x4F8E:255,0x4F8F:255,0x38:0x80}))
counts['joined']=compare(joined,'background/slot7/next-normal-call and callback witnesses')
failures=[]
for item in joined[::7]:
    for fail in range(1,len(execute(item)['events'])+1):failures.append((item[0],item[1]|{0x907:fail}))
counts['failures']=compare(failures,'switch/probe/module/publication failure prefixes')
history=[];edits={0x4F:0xF5,0x36:0x0C,0x38:0x80,0x09:0xA5,0x4EC0:2,0x4EEE:128,0x4EEF:128,0x4EF0:128,0x4EF1:128}
for tick in range(512):
    edits.update({0x02:(7+16*tick)%160,0x284:tick&255,0x50:0x25,0x4F:0x75 if tick%31==0 else 0xF5,
                  0x36:[0x0C,0x0D,0x0E,0x0F][(tick//32)%4],0x06:200,0x908:tick%20})
    item=case(10 if tick%3 else 12,dict(edits));history.append(item);edits.update(dict(zip(OUTPUTS,execute(item)['state'])))
counts['history']=compare(history,'retained cold/learning/kicker/target history calls')

required=set()
for start,end in [(0x989C,0x99C5),(0x920E,0x9240),(0x9250,0x925E),(0x9E99,0xA2B0)]:
    pc=start
    while pc<end:required.add(pc);pc=decode(rom.read,pc).next_pc
assert required<=coverage,','.join(f'{pc:04X}' for pc in sorted(required-coverage))
print(f'{sum(counts.values()):,} background-IAC comparisons; all {len(required)} desired/helper/background instruction starts exercised; '
      '137 new source-profile bytes match stock. 9E99 uses the resident body without its former task binding. '
      'Main/slow IAC and physical stepping remain separate work.')
