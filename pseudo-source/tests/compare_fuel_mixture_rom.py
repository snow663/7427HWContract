"""Crank admission, startup/AE and commanded AFR/PE against hash-checked BMHM.

Hardware callbacks are supplied fixtures; extension1800 and the BLM/tail joins
remain explicit. The running fuel root is not replaced by these callable stages.
"""
from pathlib import Path
_parent=Path(__file__).with_name('compare_fuel_air_rom.py')
exec(compile(_parent.read_text().split('\ncounts={}',1)[0],str(_parent),'exec'),globals())
mixture_source=json.loads(subprocess.check_output([binary,'--mixture-defaults'],text=True))
MIX_CAL={a for a,_ in mixture_source}
for a,v in mixture_source:assert rom.read(a,1)[0]==v,(hex(a),v,rom.read(a,1).hex())
backing=json.loads(subprocess.check_output([binary,'--mixture-backing'],text=True))
assert len(backing)==10*256+527
for a,v in backing:assert rom.read(a,1)[0]==v,(hex(a),v)
text=Path(__file__).with_name('fuel_mixture_fixture_map.h').read_text()
for kind,address in re.findall(r'\b([BWF])\((0x[0-9a-f]+|\d+),',text.split('static const Mapping mixture_state_map[] = {')[1].split('};')[0]):
    address=int(address,0);RAM.add(address)
    if kind=='W':RAM.add(address+1)
RAM.add(0x3f)
OUTPUTS=sorted(RAM|set(range(0x3000,0x3035))|set(range(0x3fc0,0x3ffe)))
ALL_CAL=ALL_CAL|MIX_CAL
BASE={a:0 for a in RAM|set(range(0x900,0x917))}|BASE
BASE.update({0x4f:0x10,0x3f:0xd0,0x36:0x80,0x3e:0,0x6:120,0x62:80,0x63:100,
    0x66:90,0x1d9:120,0x1db:110,0x1cd:40,0x1e3:20,0x1e4:128,0x23d:64,
    0x232:32,0x242:64,0x24a:147,0x272:128,0x20f:128,0x3d:3,0x2c8:16,
    0x278:64,0x2cd:5,0x2ce:10,0x3fc0:0x20,0x3fc1:0,0x3012:0x20,0x3013:0,
    0x913:1,0x914:111})

memory=Memory();cpu=memory.cpu;coverage=set();table_reads=set()
cal_bytes=rom.read(0x4000,0x2000);temperature_bytes=rom.read(0xfc45,0x211)
class Boundary(Exception):pass

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
    def invoke(start,stops=(0x7000,),afr=False):
        nonlocal status,unresolved
        sp=cpu.s.sp;cpu._push16(0x7000);cpu.s.pc=start
        if afr:cpu.s.a=memory.mem[0x24a]
        for _ in range(6000):
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
            cpu.step()
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
        raise AssertionError(f'Mixture slice budget at {cpu.s.pc:04X}')
    leaf=[(0xae5c,0x7000),(0x7e09,0x7e36),(0x858b,0x7000),(0x85b2,0x7000),
          (0x7e53,0x852c),(0x7e4f,0x7eb2,0x852c),(0x7eb2,0x7f21),(0x7f21,0x7f86),
          (0x7eb2,0x7f86),(0xe30b,0xe33c),(0x8def,0x8e1d),(0xe340,0xe477),
          (0xe38f,0xe3bb),(0xe3bb,0xe43c),(0xe43c,0xe477),(0xe33c,0xe477),
          (0x891e,0x899b),(0x899b,0x8a22),(0x8a22,0x8a8b),(0x8a92,0x8c38),
          (0x8c38,0x8c73),(0x891e,0x8c73)]
    entries=([[x] for x in leaf]+[
        [(0xe30b,0xe33c),(0xe33c,0xe477),(0x891e,0x8c73)],
        [(0x7eb2,0x8032)],[(0x891e,0x8c73),(0x7f86,0x8032),(0x751b,0x77c6)],
        [(0x8def,0x8e1d),(0x7eb2,0x7f86)],[(0x7e53,0x852c),(0x751b,0x77c6)]])
    try:
        for entry in entries[mode]:stop=invoke(entry[0],tuple(entry[1:]),mode==18)
        if mode in (2,17):value=cpu.s.a
        elif mode==3:value=cpu.s.a*256+cpu.s.b
        elif mode==5:value=int(stop==0x7eb2)
    except Failure:status=2
    except Boundary:pass
    unknown=[(a,v) for a,v in memory.writes if a not in OUTPUTS and not (0x3b0<=a<0x400 or 0xad<=a<=0xb2)]
    assert not unknown,[(hex(a),v) for a,v in unknown]
    return {'status':status,'value':value,'unresolved':unresolved,'masked':int(bool(cpu.s.ccr&0x10)),
            'state':[memory.mem[a] for a in OUTPUTS],'events':list(memory.events)}

_parent_compare=compare
def compare(items,label):
    try:return _parent_compare(items,label)
    except AssertionError as error:
        detail=error.args[0]
        if isinstance(detail,tuple) and len(detail)==5:
            raise AssertionError((detail[0],detail[1],detail[2][0],detail[3],detail[4])) from None
        raise

counts={};rng=random.Random(0x318a92)
counts['direct']=compare((case(mode) for mode in range(27)),'direct mixture slices and producer/consumer joins')
variants=[]
for i in range(4096):
    edits={a:rng.randrange(256) for a in sorted(RAM|ALL_CAL)}
    edits.update({0x907:0,0x908:i%7,0x909:i&1,0x900:i%16,0x901:i%15,0x902:i%15,
        0x90a:3,0x910:rng.randrange(256),0x911:rng.randrange(256),0x913:i%3,0x914:i&255,
        0x912:1,0x915:[0,0,0,4][i%4],0x916:1,0x86:0x40 if i&4 else 0})
    variants.append(case(i%27,edits))
counts['variants']=compare(variants,'random state/profile, expanded backing and callback/extension cases')
directed=[]
# Force warm gradual PE, both vehicle-exit routes, zero/equal FDIV and every
# old-count comparison. Header bytes are genuine bus calibration edits.
pe_warm={0x6:120,0x62:80,0x63:100,0x65:100,0x1d9:120,0x1db:120,0x1e3:255,
    0x1cd:0,0x4915:20,0x4916:200,0x4918:200,0x4914:255,0x4917:0,
    0x4c64:255,0x4921:0,0x4923:0,0x491e:200,0x491d:255,0x491f:200,0x4920:255,
    0x491c:200,0x4919:8,0x4926:0,0x4927:1,0x916:1}
pe_warm.update({a:40 for a in range(0x4c65,0x4c6e)})
pe_warm.update({a:160 for a in range(0x4c5b,0x4c64)})
for permission,count,phase,change,upper in product([0,1],[0,1,7,8,255],[0,7,0x17,0x27,0x9f],[0,1,65535],[80,120,160]):
    directed.append(case(19,pe_warm|{0x3d:permission,0x276:count,2:phase}|word(0x818,change)|{a:upper for a in range(0x4c5b,0x4c64)}))
for afr,offset,count,flags,phase,service in product([0,128,255],[0,255],[0,1,255],[0,0x20,0x80,0xa0],[0x17,0x27],[0,4]):
    directed.append(case(21,{0x24a:afr,0x2c8:offset,0x266:count,0x3e:flags,2:phase,0x395:service,
        0x3b:0x10,0x86:0x40,0x913:0,0x48de:0,0x1d9:0,0x284:0,0x272:0,0x20f:128}))
for mode,options,raw,count,phase in product([4,5,22,24,26],[0,1,4,5,0x40,0xff],[0,128,255],[0,1,255],[0,7,0x17,0x27,0x9f]):
    directed.append(case(mode,{0x4f:0x10 if options&1 else 0,0x400c:options,0x400d:options,0x3034:raw,
        0x2cd:count,0x2ce:count,2:phase,0x2ca:count,0x2cc:count,0x270:0,0x27d:0,
        0x86:0x40,0x913:1,0x915:0}))
for coolant,park,hold,delay,context,phase in product([0,120,255],[0,0x20],[0,1,255],[0,1],[0,8],[0,15,16,255]):
    directed.append(case(15,{0x6:coolant,0x41:park,0x27d:hold,0x4959:255,0x4957:120,0x2ca:0,
        0x270:0,0x2cc:delay,0x3e:context,2:phase,0x2cb:255,0x2c8:255}))
for entry,upper,tps,target in product([40,160],[30,160],[20,120],[128,255]):
    directed.append(case(19,pe_warm|{0x3d:0x21,0x4917:255,0x1d9:tps,0x1db:tps,0x63:90,
        0x65:100,0x1cd:255,0x278:128,0x4925:255}|{a:entry for a in range(0x4c65,0x4c6e)}|
        {a:upper for a in range(0x4c5b,0x4c64)}|{a:target for a in range(0x4c6e,0x4c7f)}))
directed.extend([case(19,pe_warm|{0x3d:1,0x1cd:255,0x63:90,0x65:100}),
    case(15,{0x2ca:0,0x2c8:0,0x2cc:0,0x2cb:255,0x200:0,0x232:255}),
    case(15,{0x2ca:0,0x2c8:255,0x270:1,0x27d:0,0x2cc:0,0x2cb:255,0x200:0,0x232:255}),
    case(15,{0x2ca:0,0x2c8:1,0x270:0,0x27d:0,0x3e:0,0x4958:255,0x4957:255,0x232:255}|
        {a:255 for a in range(0x4c44,0x4c5a)}),
    case(17,{0x50:0,0x1d9:0,0x284:0,0x272:100,0x24a:150,0x6:255,0x48de:0,0x48f8:0,0x20f:0,2:0x27})])
for mode,action,hold,masked in product([12,15,22],[7,8],[0,1,255],[0,1]):
    directed.append(case(mode,{0x908:action,0x2ca:hold,0x909:masked,0x3f:0x9f,0x2c8:1,0x270:2}))
counts['directed']=compare(directed,'PE vehicle/gradual routes, AFR mode/extension priority, main/REF and startup gates')
required=set()
for start,end in [(0xae5c,0xae85),(0x7e09,0x7e36),(0x7e4f,0x7f86),(0x858b,0x8613),
                  (0xe30b,0xe477),(0x8def,0x8e1d),(0x891e,0x8c73)]:
    pc=start
    while pc<end:required.add(pc);pc=decode(rom.read,pc).next_pc
# Defensive instructions excluded by their incoming arithmetic invariants:
# 8996: the departure filter approaches an increasing byte target <=FF00, so
# rounding cannot carry beyondFF; 8BB8: round(ratio*part/256)<=part for bytes.
# Both guards are still represented in the saturating C helpers.
defensive={0x8996,0x8bb8}
assert rom.read(0x8996,2)==bytes.fromhex('86 FF')
assert rom.read(0x8bb8,2)==bytes.fromhex('86 00')
required-=defensive
# Check the monotone bounds behind the two unreachable defensive instructions.
assert all(((ratio*part+128)>>8)<=part for ratio,part in product(range(256),repeat=2))
assert all(((delta*255+128)>>8)<=delta for delta in range(1,65536))
if '--quick' in sys.argv:
    print('Missing instruction starts:', ','.join(f'{a:04X}' for a in sorted(required-coverage)))
    print('Preliminary mixture comparison complete.');sys.exit(0)
counts['authorization']=compare((case(0,{0x400d:0x40,0x3d:0}|word(0x3012,(delta+0xfff0)&65535)|word(0x851,0xfff0)) for delta in range(65536)),
    'every wrapped authorization delta including baseline retention and inclusive bounds')
counts['period']=compare((case(2,word(0x3fc0,period)|{0x4141:period&7}) for period in range(65536)),
    'all period words with every low-byte multiplier and FDIV zero/overflow paths')
counts['crank']=compare((case(3,{0x6:coolant,0x1d9:tps,0x2ce:255,0x1cc:(coolant+tps)&255,4:0x10 if tps&1 else 0})
    for coolant,tps in product(range(256),repeat=2)), 'all crank coolant/TPS pairs, BARO overlap neighbors and both age curves')
counts['map_history']=compare((case(6,{0x1c0:255,0x1d9:old&255,0x23d:old&255}|word(0x1c7,old)) for old in range(65536)),
    'every MAP history word with threshold doubling, rounded delta and product saturation')
counts['tps_history']=compare((case(7,{0x1d9:tps,0x5:0x40 if old&1 else 0,2:old&3,0x1e4:old,0x284:old&1}|word(0x1dc,(old<<8)|(128 if tps&1 else 127)))
    for tps,old in product(range(256),repeat=2)), 'all current/previous TPS pairs and fractional rounding, hysteresis and filter phases')
counts['startup_math']=compare((case(15,{0x2c8:value,0x4928:gain,0x1ff:gain,0x2cb:255-value,0x2ca:0,0x2cc:0,
    0x27d:0,0x270:0,0x200:0,0x3e:8,0x4957:0,0x232:(gain^value)&255}) for value,gain in product(range(256),repeat=2)),
    'all startup AFR/gain pairs with complementary spark decay and air-rate reloads')
counts['afr_base']=compare((case(16,{0x6:coolant,0x1c0:load,0x1c9:255-load,0x2c8:load&31,0x50:0x80 if load&1 else 0,
    0x266:1,0x48ec:load,0x4bba:load&1,0x3e:0}|word(0x264,(load^coolant)<<8|coolant)) for coolant,load in product(range(256),repeat=2)),
    'all open AFR coolant/load pairs, startup subtraction and idle-departure lag')
idle=[]
for ready,timer,phase,integrator,park,delay in product([0,2],[0,1,10,11,254,255],[0x17,0x27,0x9f],[0,127,128,129,255],[0,0x20],[0,10]):
    idle.append(case(17,{0x50:ready,0x271:timer,2:phase,0x20f:integrator,0x41:park,0x48de:delay,
        0x48df:10,0x1d9:0,0x284:0,0x6:255,0x272:120,0x24a:150,0x48f8:1,0x400b:0}))
counts['idle']=compare(idle,'idle readiness, strict delay thresholds, phase27 and stability retention')
pe=[]
for gain,count,phase,permission in product(range(256),[0,1,2,3,254,255],[0,7,0x17],[0,1]):
    pe.append(case(19,pe_warm|{0x278:gain,0x277:count,0x491a:2,0x491b:gain,2:phase,0x3d:permission,
        0x276:gain,0x269:count,0x24a:255,0x4925:gain}|word(0x818,1)))
counts['pe']=compare(pe,'PE gain ramps, target interpolation and exit counters across full byte ranges')
failures=[]
for item in variants[::31]+directed[::47]:
    for fail in range(1,len(execute(item)['events'])+1):failures.append((item[0],item[1]|{0x907:fail}))
counts['failures']=compare(failures,'every selected bus/IRQ/extension failure prefix')
history=[];edits={0x4f:0x10,0x3d:3,0x400b:0,0x400c:0,0x400d:0,0x86:0,0x913:1,0x2ca:0,0x270:0,0x27d:0}
for i in range(1024):
    edits.update({0x6:i&255,0x22f:(i*7)&255,0x1d9:(i*13)&255,0x1c0:(i*5)&255,0x62:(i*3)&255,0x63:(i*2)&255,2:i%160})
    item=case([22,25,24,15,21][i%5],edits.copy());history.append(item)
    edits.update(dict(zip(OUTPUTS,execute(item)['state'])))
counts['history']=compare(history,'retained startup/AE/AFR/PE and REF histories')
assert required<=coverage,','.join(f'{a:04X}' for a in sorted(required-coverage))
print(f'{sum(counts.values()):,} fuel-mixture comparisons; all {len(required)} reachable scoped instruction starts (two defensive guards bounded); '
      f'{len(MIX_CAL)} distinct source-profile bytes and 3,087 expanded fixture bytes match stock. '
      'BLM/corrections, common tail, target ABI and physical response remain separate.')
