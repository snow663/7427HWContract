"""Cut/decel, reservoirs and connected crank/running delivery against BMHM.

The broad ignition/admission prefix and852C scheduled tail stay separate.
Typed bus fixtures do not establish physical injector/ASIC timing or delivered fuel.
"""
from pathlib import Path
_parent=Path(__file__).with_name('compare_fuel_feedback_rom.py')
exec(compile(_parent.read_text().split('\ncounts={}',1)[0],str(_parent),'exec'),globals())
delivery_source=json.loads(subprocess.check_output([binary,'--delivery-defaults'],text=True))
DL_CAL={a for a,_ in delivery_source}
for a,v in delivery_source:assert rom.read(a,1)[0]==v,(hex(a),v,rom.read(a,1).hex())
backing=json.loads(subprocess.check_output([binary,'--delivery-backing'],text=True))
assert len(backing)==17
for a,v in backing:assert rom.read(a,1)[0]==v,(hex(a),v)
text=Path(__file__).with_name('fuel_delivery_fixture_map.h').read_text()
for kind,address in re.findall(r'\b([BWF])\((0x[0-9a-f]+|\d+),',text.split('static const Mapping delivery_state_map[] = {')[1].split('};')[0]):
    address=int(address,0);RAM.add(address)
    if kind=='W':RAM.add(address+1)
OUTPUTS=sorted(RAM|set(range(0x3000,0x3035))|set(range(0x3fc0,0x3ffe)))
ALL_CAL=ALL_CAL|DL_CAL
BASE={a:0 for a in RAM}|BASE
BASE.update({0x3e:0,0x3d:0,0x46:0,0x53:0,0x26a:0,0x244:255,0x245:0,0x246:5,
    0x23a:1,0x23b:0,0x259:0,0x25a:1,0x25b:128,0x87f:0,0x23f:0,0x5:0,
    0x44:0,0x16:0,0x99:0,0x4f:0x10,0x6f:0,0x400b:0,0x400f:1,0x1d9:80,
    0x84d:0,0x3fc0:0x20,0x3fc1:0,0x24e:0x10,0x24f:0,0x248:128})
_DeliveryParentMemory=Memory
class Memory(_DeliveryParentMemory):
    def read16(self,a):
        value=super().read16(a)
        if a==0x3fc0 and self.mem[0x908]==10:
            self.mem[0x24e:0x250]=bytes.fromhex('0040');self.mem[0x259:0x25c]=bytes.fromhex('feff80')
        return value
    def write16(self,a,v):
        super().write16(a,v)
        if a==0x3fce and v==0 and self.mem[0x908]==12:self.mem[0x3e]^=0x10
memory=Memory();cpu=memory.cpu;coverage=set();table_reads=set()
cal_bytes=rom.read(0x4000,0x2000);temperature_bytes=rom.read(0xfc45,0x211)

def execute(item):
    mode,edits=item
    memory.mem[:0x1800]=bytes(0x1800);memory.mem[0x3000:0x4000]=bytes(0x1000)
    memory.mem[0x4000:0x6000]=cal_bytes;memory.mem[0xfc45:0xfe56]=temperature_bytes
    for a,v in edits.items():memory.mem[a]=v
    memory.events.clear();memory.writes.clear();memory.table_reads=table_reads
    memory.attempts=memory.polls=memory.control=memory.cycle_counter=0
    memory.fail_at=memory.mem[0x907];cpu.s.sp=0x3ff;cpu.s.ccr=0xd0 if memory.mem[0x909] else 0xc0
    cpu.s.a,cpu.s.b,cpu.s.x,cpu.s.y=0x12,0x34,0x5678,0x9abc
    status=value=unresolved=0
    def invoke(start,stops=(0x7000,),pulse=False):
        nonlocal status,unresolved
        sp=cpu.s.sp;cpu._push16(0x7000);cpu.s.pc=start
        if pulse:cpu.s.a,cpu.s.b=memory.mem[0x24e],memory.mem[0x24f]
        for _ in range(10000):
            pc=cpu.s.pc
            if pc in stops:
                if pc!=0x7000:assert cpu._pull16()==0x7000
                assert cpu.s.sp==sp;return pc
            if pc==0x1800:
                if not memory.mem[0x913]:status=1;unresolved=1;raise Boundary
                memory.record('T',0,0x1800,0)
                memory.mem[0x24a]=memory.mem[0x914]
                status=memory.mem[0x915]
                if status:raise Boundary
                cpu.s.pc=cpu._pull16();continue
            coverage.add(pc);opcode=memory.mem[pc]
            if opcode in (0x0e,0x0f):memory.record('M',0,0,int(opcode==0x0f))
            if pc==0x7524:delay_start=memory.cycle_counter
            if pc==0x8429:gap_start=memory.cycle_counter
            cpu.step()
            if pc==0xf3ed and cpu.s.pc==0x842c:
                cycles=memory.cycle_counter-gap_start;assert cycles==11
                memory.record('D',0,0,cycles)
                if memory.mem[0x908]==9:
                    memory.mem[0x3fc0:0x3fc2]=bytes.fromhex('0001')
                    memory.mem[0x24e:0x250]=bytes.fromhex('ffff')
                    memory.mem[0x259:0x25c]=bytes.fromhex('ffffff')
            if pc==0x7527:
                cycles=memory.cycle_counter-delay_start;assert cycles==33
                memory.record('D',0,0,cycles)
            action=memory.mem[0x908]
            if opcode==0x0e and action==3:
                memory.mem[0x55]=99;memory.mem[0xa7]=255;memory.mem[0x3034]=7
            if opcode==0x0f and action==4:
                memory.mem[0x82e]=33;memory.mem[0x50]|=1
            if opcode==0x0f and action==7:
                memory.mem[0x3f]=(memory.mem[0x3f]&0x40)|0x6f
                memory.mem[0x66]=255;memory.mem[0x63]=0;memory.mem[0x858]=255;memory.mem[0x36]|=128
            if opcode==0x0e and action==8:
                memory.mem[0x2ca]=0;memory.mem[0x2c8]=255;memory.mem[0x27d]=0;memory.mem[0x270]=0
                memory.mem[0x3f]=(memory.mem[0x3f]&0xf0)|0x2a
            if action==11 and opcode==0x0f:
                memory.mem[0x82a]=255;memory.mem[0x51]|=1;memory.mem[0x24e:0x250]=bytes.fromhex('1234')
            if action==11 and opcode==0x0e:
                memory.mem[0x254:0x256]=bytes(2);memory.mem[0x82a]=255;memory.mem[0x24e:0x250]=bytes.fromhex('4000')
        raise AssertionError(f'Mixture slice budget at {cpu.s.pc:04X}')
    leaves=[(0x8058,0x810c,0x821d),(0x810c,0x8175),(0x8175,0x821d,0x824d),(0x821d,0x82ed),
        (0x824d,0x82ed),(0x8058,0x82ed),(0x83c4,0x8472),(0x842c,0x8476),
        (0x8476,0x84a9,0x84bc),(0x84a9,0x84bc),(0x8476,0x84bc),(0x83b1,0x8476,0x84bc),
        (0x83b1,0x852c),(0x7eb2,0x83b1),(0x7eb2,0x852c),(0x7e4f,0x852c)]
    entries=([[x] for x in leaves]+[
        [(0x891e,0x7000),(0x7e4f,0x852c)],
        [(0x863d,0x7000),(0x891e,0x7000),(0x7e4f,0x852c)],
        [(0x7e4f,0x852c),(0x751b,0x77c6)],
        [(0xe30b,0xe33c),(0xe33c,0xe477),(0xe477,0x7000),(0x863d,0x7000),(0x891e,0x7000),(0x7e4f,0x852c),(0x751b,0x77c6)],
        [(0x83b1,0x852c),(0x83b1,0x852c),(0x83b1,0x852c)],
        [(0x8def,0x8e1d),(0x7eb2,0x852c)]])
    try:
        for entry in entries[mode]:stop=invoke(entry[0],tuple(entry[1:]),pulse=mode in (6,9,11,12,20))
        if mode==0:value=int(stop==0x821d)
        elif mode==2:value=int(stop==0x821d)
        elif mode==8 and stop==0x84a9:value=0x10000|cpu.s.a*256|cpu.s.b
        elif mode==11:value=int(stop==0x8476)
    except Failure:status=2
    except Boundary:pass
    unknown=[(a,v) for a,v in memory.writes if a not in OUTPUTS and not (0x3b0<=a<0x400 or 0xad<=a<=0xb2)]
    assert not unknown,[(hex(a),v) for a,v in unknown]
    return {'status':status,'value':value,'unresolved':unresolved,'masked':int(bool(cpu.s.ccr&0x10)),
            'state':[memory.mem[a] for a in OUTPUTS],'events':list(memory.events)}

counts={};rng=random.Random(0x3183b1)
counts['direct']=compare((case(mode) for mode in range(22)),'direct cut/decel and delivery entries plus connected calculation joins')
variants=[]
for i in range(4096):
    edits={a:rng.randrange(256) for a in sorted(RAM|ALL_CAL)}
    edits.update({0x907:0,0x908:i%13,0x909:i&1,0x900:i%16,0x901:i%15,0x902:i%15,
        0x913:i%3,0x914:i&255,0x915:[0,0,0,4][i%4],0x916:1,0x912:1})
    variants.append(case(i%22,edits))
counts['variants']=compare(variants,'random raw state/profiles, callback order, expanded views and complete running joins')
directed=[]
for mode,option,pending,updated,masked,action in product([6,9,10,11,12,14,15,19,20],[0,1,4],[0,0x80],[0,1],[0,1],range(13)):
    directed.append(case(mode,{0x400b:option,0x3d:pending,0x51:updated,0x909:masked,0x908:action,
        0x44:0,0x4f:0x10,0x50:0x80 if option==4 else 0,0x3e:0,0x4974:0,0x82a:255,
        0x4932:0x03,0x4933:0x12,0x4934:0,0x4935:0,0x4930:0,0x4931:0,0x913:1,0x915:0,
        0x492c:0xff,0x492d:0xff,0x23a:1,0x23b:0,0x259:0,0x25a:1,0x25b:128}))
for flags,phase,delay,timer,load in product([0,8],[0,1,2,15,16,31,159],[0,1,255],[0,1,255],[0,100,255]):
    directed.append(case(2,{0x46:flags,2:phase,0x246:delay,0x245:timer,0x1c0:load,0x1cf:255-load,
        0x6:255,0x41:0,0x6f:0x24,0x65:100,0x63:100,0x4944:0,0x4945:255,0x4946:255,
        0x493d:255,0x493e:255,0x243:0,0x493a:0,0x62:100,0x493b:0,0x493c:0}))
for count,reload,rpm,latch,fault in product([0,1,255],[0,1,255],[0,127,255],[0,8],[0,0x10]):
    directed.append(case(0,{0x84d:count,0x5155:reload,0x61:rpm,0x53:latch,0x16:fault,0x400f:0,
        0x41:0x20 if count&1 else 0,0x812:0,0x5156:0,0x1d9:255,0x5159:0,0x5157:127,0x5158:128}))
for timer,park,loadflag in product([0,1,255],[0,0x20],[0,0x24,0x48,0x6c]):
    directed.append(case(2,{0x245:timer,0x41:park,0x6f:loadflag,0x6:255,0x4944:0,
        0x65:255,0x63:0,0x4945:0,0x23a:0xff,0x23b:0xff,0x493f:0,0x4940:1}))
for mode,drop,factor,ac,transition in product([1,3,4,5],[0,1,128,255],[0,1,31,32,128,255],[0,0x10],[0,1]):
    directed.append(case(mode,{0x23f:drop,0x242:factor,0x41:ac,0x3e:transition,0x87f:drop,
        0x48c6:255,0x48c7:255,0x244:factor,0x4943:128,0x4936:0,0x4937:0,0x4938:255,
        0x4939:255,0x1d9:0,0x1c0:0}|word(0x1de,65535)|word(0x1c7,65535)|
        {a:255 for a in range(0x4b20,0x4b3c)}))
directed.append(case(13,{0x4d92:0,0x4d93:0,0x1b2:0,0x1b3:0,0x248:128,0x3d:0}))
counts['directed']=compare(directed,'mode/IRQ/callback ordering, decel cadence and recovery, qualification and reservoir edges')
required=set()
for start,end in [(0x8058,0x82ed),(0x83b1,0x84bc)]:
    pc=start
    while pc<end:required.add(pc);pc=decode(rom.read,pc).next_pc
# IDIV by80 produces remainder0..79. The rounded FDIV fraction cannot carry.
assert rom.read(0x844f,3)==bytes.fromhex('C3 00 01')
assert max(((remainder<<16)//80)+128 for remainder in range(80))<65536
required.remove(0x844f)
if '--quick' in sys.argv:
    print('Missing instruction starts:',','.join(f'{a:04X}' for a in sorted(required-coverage)))
    print('Preliminary delivery comparison complete.');sys.exit(0)
counts['qualification']=compare((case(0,{0x400f:0x80,0x16:0,0x812:0,0x5156:0,0x1d9:tps,0x5159:0,
    0x61:rpm,0x53:8 if tps&1 else 0,0x5157:tps^rpm,0x5158:255-tps,0x400f:0x81,0x6f:0})
    for tps,rpm in product(range(256),repeat=2)), 'all TPS/low-RPM qualification pairs with retained hysteresis')
counts['cut']=compare((case(0,{0x400f:0,0x16:0x10,0x99:rpm&3,0x62:rpm,0x284:speed,0x46:0x10 if speed&1 else 0,
    0x26a:speed,0x4965:128}) for rpm,speed in product(range(256),repeat=2)), 'every RPM/speed pair across fault-adjusted cut thresholds and delay')
counts['cut_delay']=compare((case(0,{0x400f:0,0x16:0x10,0x62:100,0x284:255,0x4966:0,0x496b:0,0x496c:0,
    0x26a:count,0x4965:limit}|{a:255 for a in range(0x4967,0x496b)}) for count,limit in product(range(256),repeat=2)),
    'every old-cut-count/limit pair, including reaching the limit without cutting this call')
counts['reservoir']=compare((case(1,word(0x23a,old)|{0x87f:old&255,0x23c:(old>>8),0x3e:1 if old&1 else 0,
    0x41:0x10,0x48c6:old&255,0x48c7:old>>8,0x23f:255,0x5:0x80 if old&2 else 0}) for old in range(65536)),
    'all retained reservoir words with saturated byte enrichments and wrapped word addition')
counts['recovery']=compare((case(2,word(0x23a,old)|word(0x493f,old^0x8000)|{0x245:1,0x41:0x20,0x6:255,0x4944:0}) for old in range(65536)),
    'all reservoir words with carry-to7FFF recovery, pending packet and timer reload')
active_enlean={0x4936:0,0x4937:0,0x4938:255,0x4939:128,0x400b:0}|{a:20 for a in range(0x4b20,0x4b2b)}|{a:10 for a in range(0x4b2b,0x4b3c)}
counts['enleanment']=compare((case(4,active_enlean|{0x1d9:tps,0x1c0:load,0x242:tps^load,0x284:load}|word(0x1de,65535)|word(0x1c7,65535))
    for tps,load in product(range(256),repeat=2)), 'all TPS/load drop pairs, rounded history caps and active enleanment multipliers')
counts['period']=compare((case(7,word(0x3fc0,period)|word(0x24e,period^0x8000)|{0x259:period&255}|word(0x25a,period))
    for period in range(65536)), 'every live period word with FDIV overflow/zero and24-bit accumulator carry')
counts['pulse']=compare((case(7,word(0x3fc0,64)|word(0x24e,pulse)|{0x259:pulse&255}|word(0x25a,pulse^0x8000))
    for pulse in range(65536)), 'every PW numerator with quotient/fraction publication and80-count packet quantum')
counts['packet']=compare((case(8,word(0x259,(total*17)&65535)|{0x25b:total&255}|word(0x23a,(total-(total*17))&65535))
    for total in range(65536)), 'all wrapped packet totals, maximum/minimum edges and borrowed-reservoir debit')
counts['cpi']=compare((case(6,{0x82a:count,0x4974:limit,0x51:0,0x908:11 if count&1 else 0,0x909:limit&1}|word(0x254,0)|word(0x24e,(count<<8)|limit))
    for count,limit in product(range(256),repeat=2)), 'every CPI count/limit pair, old255 retention and post-CLI pulse reload')
failures=[]
for item in variants[::17]+directed[::41]:
    for fail in range(1,len(execute(item)['events'])+1):failures.append((item[0],item[1]|{0x907:fail}))
counts['failures']=compare(failures,'every selected zero-write/delay/period/mask/async/finalizer/REF failure prefix')
history=[];edits={0x4f:0x10,0x3d:0,0x3e:0,0x44:0,0x16:0,0x400b:0,0x400c:0,0x400f:1,0x86:0,
    0x913:1,0x915:0,0x391:0,0x392:0,0x18:0,0x19:0,0x72:0,0x2ca:0,0x2cc:0,0x247:0,0x274:0,0x273:0}
for i in range(1024):
    edits.update({0x1d5:(i*13)&255,0x1d9:(i*7)&255,0x1c0:(i*3)&255,0x1cf:(i*5)&255,
        0x6:100+i%156,0x62:(i*11)&255,0x63:(i*17)&255,2:i%160,0x284:i&255,0x285:(i*19)&255,
        0x400b:[0,1,4][i%3],0x908:i%13})
    item=case([16,17,18,19,20,21][i%6],edits.copy());history.append(item)
    edits.update(dict(zip(OUTPUTS,execute(item)['state'])))
counts['history']=compare(history,'retained crank/running, O2/BLM, cut/decel and repeated sync/async/REF histories')
assert required<=coverage,','.join(f'{a:04X}' for a in sorted(required-coverage))
assert {0x4b2b,0x4b3b}<=table_reads,'Missing enleanment endpoint neighbor witness'
print(f'{sum(counts.values()):,} fuel-delivery comparisons; all {len(required)} reachable scoped instruction starts '
      f'(one remainder-carry guard bounded); {len(DL_CAL)} profile bytes and17 expanded curve bytes match stock. '
      'Broad ignition/admission, scheduled tail, target ABI and physical response remain separate.')
