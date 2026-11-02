"""O2/BLM state machines and pulse-correction C versus hash-checked BMHM.

The complete running admission/cut/decel/async path and physical response remain
separate. Explicit test joins do not skip those stages in the production root.
"""
from pathlib import Path
_parent=Path(__file__).with_name('compare_fuel_mixture_rom.py')
exec(compile(_parent.read_text().split('\ncounts={}',1)[0],str(_parent),'exec'),globals())
feedback_source=json.loads(subprocess.check_output([binary,'--feedback-defaults'],text=True))
FB_CAL={a for a,_ in feedback_source}
for a,v in feedback_source:assert rom.read(a,1)[0]==v,(hex(a),v,rom.read(a,1).hex())
backing=json.loads(subprocess.check_output([binary,'--feedback-backing'],text=True))
assert len(backing)==1054
for a,v in backing:assert rom.read(a,1)[0]==v,(hex(a),v)
text=Path(__file__).with_name('fuel_feedback_fixture_map.h').read_text()
state=text.split('static const Mapping feedback_state_map[] = {')[1].split('};')[0]
for kind,address,rest in re.findall(r'\b([BWFA])\((0x[0-9a-f]+|\d+),([^)]*)\)',state):
    address=int(address,0);n=2 if kind=='W' else int(rest.split(',')[0]) if kind=='A' else 1
    RAM.update(range(address,address+n))
OUTPUTS=sorted(RAM|set(range(0x3000,0x3035))|set(range(0x3fc0,0x3ffe)))
ALL_CAL=ALL_CAL|FB_CAL
BASE={a:0 for a in RAM|set(range(0x900,0x918))}|BASE
BASE.update({0x3e:0xa2,0x3d:0,0x46:0,0x4f:0x10,0x3f:0,0x6:180,0x1d4:100,0x1d5:130,
    0x241:0,0x4:3,0x52:0,0x26b:4,0x26c:128,0x26d:160,0x26e:96,0x280:64,
    0x27a:16,0x27b:80,0x27c:10,0x248:128,0x247:0,0x249:128,0x282:128,
    0x273:0,0x274:0,0x1b2:0,0x1b3:0,0x917:128,0x70:0,0x86:0})
BASE.update(word(0x1d2,0x8800));BASE.update({a:128 for a in range(0x2b3,0x2c8)})
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
    def invoke(start,stops=(0x7000,),input_a=False,input_b=False,window_stack=False,window_out=False):
        nonlocal status,unresolved
        sp=cpu.s.sp;cpu._push16(0x7000);cpu.s.pc=start
        if input_a:cpu.s.a=memory.mem[0x917]
        if input_b:cpu.s.b=memory.mem[0x917]
        if window_stack:cpu._push8(memory.mem[0x917])
        for _ in range(6000):
            pc=cpu.s.pc
            if pc in stops:
                if window_out:output=cpu._pull8()
                if pc!=0x7000:assert cpu._pull16()==0x7000
                assert cpu.s.sp==sp;return output if window_out else pc
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
    leaves=[(0x863d,0x8662),(0xe477,0x7000),(0x8662,0x86b0),(0x86b0,0x86f2),
        (0x877c,0x7000),(0x86f2,0x8790,0x7000),(0x8790,0x886f),(0x886f,0x88cd),
        (0x88cd,0x88e9),(0x88e9,0x7000),(0x863d,0x7000),(0xf280,0x7000),(0xf28e,0x7000),
        (0x8c73,0x8d9e),(0x8d9e,0x8def),(0x8e1d,0x7000),(0x8c73,0x7000),(0x891e,0x7000),
        (0x80fc,0x7000),(0x80ee,0x7000),(0x8032,0x8058),(0x82ed,0x8342),
        (0x8342,0x8380),(0x8380,0x83b1),(0x82ed,0x83b1)]
    entries=([[x] for x in leaves]+[
        [(0x7e09,0x7e36),(0x863d,0x7000)],[(0x891e,0x7000),(0x8032,0x8058)],
        [(0x863d,0x7000),(0x891e,0x7000),(0x7f86,0x8032),(0x8032,0x8058),(0x82ed,0x83b1),(0x84bc,0x852c)],
        [(0xe33c,0xe477),(0xe477,0x7000),(0x891e,0x7000)],
        [(0xf28e,0x7000),(0x8c73,0x7000)],
        [(0x863d,0x7000),(0x82ed,0x83b1),(0x84bc,0x852c),(0x751b,0x77c6)]])
    try:
        for entry in entries[mode]:
            stop=invoke(entry[0],tuple(entry[1:]),input_a=mode in (18,19),input_b=mode==8,window_stack=mode==7,window_out=mode==6)
        if mode==5:value=int(stop==0x8790)
        elif mode==6:value=stop
    except Failure:status=2
    except Boundary:pass
    unknown=[(a,v) for a,v in memory.writes if a not in OUTPUTS and not (0x3b0<=a<0x400 or 0xad<=a<=0xb2)]
    assert not unknown,[(hex(a),v) for a,v in unknown]
    return {'status':status,'value':value,'unresolved':unresolved,'masked':int(bool(cpu.s.ccr&0x10)),
            'state':[memory.mem[a] for a in OUTPUTS],'events':list(memory.events)}

counts={};rng=random.Random(0x31863d)
counts['direct']=compare((case(mode) for mode in range(31)),'direct feedback/correction slices and joins')
variants=[]
for i in range(4096):
    mode=i%31
    edits={a:rng.randrange(256) for a in sorted(RAM|ALL_CAL)}
    edits.update({0x907:0,0x908:i%9,0x909:i&1,0x900:i%16,0x901:i%15,0x902:i%15,
        0x913:i%3,0x914:i&255,0x915:[0,0,0,4][i%4],0x916:1,0x912:1,0x917:i&255})
    if mode==15:edits[0x247]%=21
    variants.append(case(mode,edits))
counts['variants']=compare(variants,'random profiles/state, IRQ callbacks, expanded views and extension failures')
assert rom.read(0x866f,2)==bytes.fromhex('81 80'), 'The HAC airflow cap label is wrong'
assert rom.read(0x87ad,3)==bytes.fromhex('14 46 02'), 'The HAC omits the positive-error BSET'
directed=[]
for mode,flags,service,value,phase in product([1,5,10,17,27,28],[0,2,0x20,0x40,0x80,0xa0,0xa2,0xff],[0,1],[0,1],[0,7,0x27,0x9f]):
    directed.append(case(mode,{0x3e:flags,0x3b:0x10,0x391:service,0x392:value,2:phase,0x913:1,0x915:0}))
for sign,direction,int_value,delay,interval,flags in product([0,2],[0,0x40],[0,1,127,128,129,254,255],[0,1,127,254,255],[0,1,127,254,255],[0,0x80]):
    directed.append(case(7,{0x46:sign,0x3e:direction,0x20f:int_value,0x25f:delay,0x26b:interval,0x52:flags,
        0x280:96,0x4948:0,0x400b:0,0x3f:0}))
for mode,action,context,flags in product([6,10,27],[0,3,4,7,8],range(16),[0,0x40]):
    directed.append(case(mode,{0x908:action,0x3f:0xf0|context,0x50:0x80,0x3e:0x80|flags,
        0x86:0,0x3b:0x10,0x391:1,0x392:0,0x1d2:255,0x26d:0,0x4955:255,0x4956:255}))
for index,mode,phase,margin in product(range(21),[0,1],[0,0x9f],[0,1,128,255]):
    directed.append(case(13,{0x247:index,0x400e:mode,2:phase,0x48f4:margin,0x48f5:margin,
        0x48f6:7,0x1d9:0,0x284:0,0x41:0x30,0x51:1 if index&1 else 0,
        0x48d9:255,0x48da:255}|word(0x81a,65535)))
for index,count,delay,direction in product(range(21),[0,1,126,127,128,254,255],[0,1,255],[0,0x40]):
    directed.append(case(15,{0x247:index,0x274:count,0x273:count,0x48ed:delay,0x3e:2|direction,0x3d:0,
        0x20f:0 if direction else 255,0x48f7:0,0x48f8:0,0x26b:0,0x48fb:255}))
for pw,gain,pe,egr in product([0,1,127,128,255,32767,32768,65535],[0,1,127,128,129,255],[0,0x20],[0,127,128,65535]):
    directed.append(case(20,word(0x24e,pw)|{0x248:gain,0x3d:pe}|word(0x1b2,egr)))
for mode,sample in product([2,6,21,22,24,30],[0,1,127,128,129,254,255]):
    directed.append(case(mode,{0x1d2:sample,0x26d:0,0x26e:255,0x4955:255,0x4956:255,0x50:0,
        0x232:sample,0x4949:255,0x1c6:sample,0x1cc:sample,0x4f:0x10,0x3e:0xc0,
        0x4516:0,0x48db:255,0x48dc:255,0x48dd:0}|word(0x68,0)|word(0x6a,65535)))
for direction,integrator in product([0,0x40],[0,127,128,255]):
    directed.append(case(5,{0x3e:0x80|direction,0x3d:0,0x46:0,0x52:0,0x400c:0,
        0x4f:0x10,0x3b:0,0x1c0:0,0x62:100,0x284:255,0x20f:integrator,
        0x490b:255,0x490c:20,0x490d:200,0x490e:0}))
for module,mode in product([0,1,2,3,255],[0,1]):
    directed.append(case(1,{0x4:3,0x50:0,0x18:0,0x19:0,0x72:0,0x3b:0,0x86:0x40,
        0x801:module,0x6:255,0x48d0:0,0x48d6:0,0x48d7:255,0x48d3:255,0x48d4:0,0x48d5:255,
        0x24a:147,0x48e7:147,0x1c9:0,0x1c6:100,0x1cf:100,0x400e:mode,0x6f:0}))
directed.extend([case(23,word(0x24e,65535)|{0x26f:127,0x23e:0}),
    case(23,word(0x24e,65535)|{0x26f:0,0x23e:255})])
counts['directed']=compare(directed,'service polarity, IRQ/context pairs, INT delays, special cells, learning wrap and correction edges')
required=set()
for start,end in [(0x863d,0x891e),(0xe477,0xe562),(0x8c73,0x8eb4),(0xf280,0xf2aa),
    (0x8032,0x8058),(0x80ee,0x8106),(0x82ed,0x83b1)]:
    pc=start
    while pc<end:required.add(pc);pc=decode(rom.read,pc).next_pc
if '--quick' in sys.argv:
    print('Missing instruction starts:',','.join(f'{a:04X}' for a in sorted(required-coverage)))
    print('Preliminary feedback comparison complete.');sys.exit(0)
counts['thresholds']=compare((case(2,{0x232:air,0x4949:gain,0x50:0x80 if air&1 else 0,0x70:4 if gain&1 else 0})
    for air,gain in product(range(256),repeat=2)), 'all airflow/gain pairs, carry caps, idle threshold and interval selection')
counts['direction']=compare((case(3,{0x1d5:raw,0x1d4:old,0x26c:old^raw,0x4947:old,0x3e:0xff if raw&1 else 0x22,
    0x27c:255 if old&1 else 254,0x275:255}) for raw,old in product(range(256),repeat=2)),
    'all raw/previous O2 pairs, threshold overflow/borrow and direction-count retention')
counts['proportional']=compare((case(6,{0x1d2:sample,0x26d:128,0x26e:128,0x4955:gain,0x4956:255-gain,
    0x50:0x80 if gain&1 else 0,0x3e:0x40 if sample&1 else 0,0x3f:sample&15,0x27b:gain})
    for sample,gain in product(range(256),repeat=2)), 'all filtered-O2/gain pairs, both signs, paired context and truncated/rounded P')
counts['integrator']=compare((case(7,{0x20f:value,0x280:error,0x46:2 if error&1 else 0,0x3e:0x40 if error&1 else 0,
    0x26b:0,0x25f:0,0x4948:0,0x400b:0,0x3f:0,0x52:0}) for value,error in product(range(256),repeat=2)),
    'all INT/error bytes, wrapped error doubling and equality-only calibration stops')
counts['window']=compare((case(8,{0x917:window,0x27c:age,0x494e:age^window,0x52:0,0x27a:255})
    for window,age in product(range(256),repeat=2)), 'every P-window/age pair and strict saturating window edges')
counts['combine']=compare((case(9,{0x20f:integrator,0x27a:proportional,0x3e:direction,0x400b:8,0x44:2,0x4912:integrator^proportional})
    for integrator,proportional,direction in product(range(256),range(256),[0,0x40])),
    'every INT/P/direction combination with activity cap, zero floor and signed encoding')
counts['blm_select']=compare((case(13,{0x62:rpm,0x1c0:load,0x1cf:255-load,0x400e:load&1,0x247:(rpm^load)%21,
    0x48f4:rpm&31,0x48f5:load&31,0x48f6:0,2:0x9f if rpm&1 else 0,0x284:rpm,0x285:load})
    for rpm,load in product(range(256),repeat=2)), 'all BLM RPM/load coordinates with retained-cell hysteresis and phase9F speed sampling')
counts['blm_transition']=compare((case(14,{0x249:old,0x248:new,0x3d:4,0x52:0,0x400c:0,0x1d9:255,
    0x20f:old^new,0x4909:old,0x490a:new}) for old,new in product(range(256),repeat=2)),
    'every BLM old/new byte pair, signed-byte difference classification and INT retention gates')
counts['blm_learn']=compare((case(15,{0x20f:integrator,0x247:integrator%21,0x2b3+integrator%21:cell,
    0x3e:0x42 if integrator<128 else 2,0x3d:0,0x274:127,0x273:255,0x26b:255,
    0x48f7:0,0x48f8:0,0x48f9:64,0x48fa:80,0x48fc:192,0x48fb:cell})
    for integrator,cell in product(range(256),repeat=2)), 'every INT/cell pair and bounded learning steps with retained127/255 counters')
counts['boot']=compare((case(12,{0x48fd:upper,0x48fe:lower}|{0x2b3+i:(i*13)&255 for i in range(21)})
    for upper,lower in product(range(256),repeat=2)), 'all boot upper/lower pairs including contradictory bounds across all21 cells')
counts['closed_runtime']=compare((case(1,word(0xfd,runtime)|{0x4:1,0x48d2:255,0x241:0,0x282:runtime&255,
    0x50:0,0x18:0,0x19:0,0x72:0,0x86:0,0x3b:0}) for runtime in range(65536)),
    'all runtime words, low-byte elapsed wrap and three starting-coolant time branches')
counts['blm_scale']=compare((case(19,word(0x24e,pulse)|{0x917:pulse&255}) for pulse in range(65536)),
    'every PW word with saturated pre-double and all BLM gain bytes')
counts['signed_apply']=compare((case(23,word(0x24e,pulse)|{0x26f:pulse&255,0x23e:pulse>>8}) for pulse in range(65536)),
    'every PW word with signed feedback, MAP AE saturation and running packet publication')
prefix_inputs=[]
for action,context,masked in product([0,3,4,7,8],range(16),[0,1]):
    prefix_inputs.append(case(6,{0x908:action,0x3f:0xf0|context,0x909:masked,0x50:0x80,0x3e:0x80}))
for action,masked in product([0,3,4,7,8],[0,1]):
    prefix_inputs.append(case(30,{0x908:action,0x909:masked,0x44:0,0x4f:0x10,0x50:0x20,
        0x3e:0x80,0x400b:0,0x400c:0,0x400e:0}))
failures=[]
for item in variants[::29]+directed[::97]+prefix_inputs:
    for fail in range(1,len(execute(item)['events'])+1):failures.append((item[0],item[1]|{0x907:fail}))
counts['failures']=compare(failures,'every selected IRQ/extension/finalizer/REF failure prefix')
history=[];edits={0x4f:0x10,0x3d:0,0x3e:0xa2,0x400b:0,0x400c:0,0x86:0,0x913:1,0x915:0,
    0x391:0,0x392:0,0x18:0,0x19:0,0x72:0,0x2ca:0,0x2cc:0,0x247:0,0x274:0,0x273:0,0x3f:0}
for i in range(1024):
    edits.update({0x1d5:(i*13)&255,0x1d9:(i*7)&255,0x1c0:(i*3)&255,0x1cf:(i*5)&255,
        0x6:100+(i%156),0x62:(i*11)&255,0x63:(i*17)&255,2:i%160,0x284:i&255,0x285:(i*19)&255})
    item=case([25,28,17,27,30][i%5],edits.copy());history.append(item)
    edits.update(dict(zip(OUTPUTS,execute(item)['state'])))
counts['history']=compare(history,'retained O2, admission, PE/BLM learning, corrections and REF histories')
assert required<=coverage,','.join(f'{a:04X}' for a in sorted(required-coverage))
print(f'{sum(counts.values()):,} fuel-feedback comparisons; all {len(required)} scoped instruction starts; '
      f'{len(FB_CAL)} distinct source-profile bytes and 1,054 expanded fixture bytes match stock. '
      'Cut/decel/async routing, broad admissions, target ABI and physical response remain separate.')
