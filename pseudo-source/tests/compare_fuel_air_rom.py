"""TPS, CTS/MAT/BARO and VE/air-charge C versus hash-checked BMHM instructions.

Producer/consumer joins are explicit calls, not a claim that the broad fuel and
slot1/4/D/F roots or target interrupt timing are implemented.
"""
from pathlib import Path
_parent=Path(__file__).with_name('compare_fuel_output_rom.py')
exec(compile(_parent.read_text().split('\ncounts={}',1)[0],str(_parent),'exec'),globals())

air_source=json.loads(subprocess.check_output([binary,'--air-defaults'],text=True))
AIR_CAL={a for a,_ in air_source}
for a,v in air_source:assert rom.read(a,1)[0]==v,(hex(a),v,rom.read(a,1).hex())
backing=json.loads(subprocess.check_output([binary,'--air-backing'],text=True))
assert len(backing)==3*527
for a,v in backing:assert rom.read(a,1)[0]==v,(hex(a),v)
text=Path(__file__).with_name('fuel_air_fixture_map.h').read_text()
for kind,address in re.findall(r'\b([BWF])\((0x[0-9a-f]+|\d+),',text.split('static const Mapping air_state_map[] = {')[1].split('};')[0]):
    address=int(address,0);RAM.add(address)
    if kind=='W':RAM.add(address+1)
OUTPUTS=sorted(RAM|set(range(0x3000,0x3035))|set(range(0x3fc0,0x3ffe)))
ALL_CAL=ALL_CAL|AIR_CAL
BASE={a:0 for a in RAM|set(range(0x900,0x913))}|BASE
BASE.update({0xa6:80,0x2f6:32,0x2f7:0,0x1d9:10,0x1da:2,0x1de:10,0x1df:0,
    0x82d:128,0x43:0x80,0x4e:0xa4,0x06:160,0xfd:1,0xfe:0,0x22f:120,
    0x2f4:180,0x2f5:128,0x1c6:100,0x61:100,0x62:80,0x63:100,0x1c0:100,
    0x1ce:128,0x1e8:0x20,0x1e9:0,0x24a:128,0x232:64,0x233:0,
    0x236:0x9c,0x237:0x40,0x257:0x2e,0x258:0xe0,0x231:128,0x20f:128})

_FuelMemory=Memory
class Memory(_FuelMemory):
    def read8(self,a):
        if 0x4000<=a<0x6000 or 0xfc45<=a<0xfe56:self.table_reads.add(a)
        mux=(self.mem[0x3008]>>3)&7
        if a==0x3034 and (self.mem[0x90a]&2) and mux in (4,5):
            saved=self.mem[a];self.mem[a]=self.mem[0x910 if mux==4 else 0x911]
            try:return super().read8(a)
            finally:self.mem[a]=saved
        return super().read8(a)

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
    status=value=0
    def invoke(start,stop=0x7000):
        sp=cpu.s.sp;cpu._push16(0x7000);cpu.s.pc=start
        for _ in range(5000):
            pc=cpu.s.pc
            if pc==stop:
                if stop!=0x7000:assert cpu._pull16()==0x7000
                assert cpu.s.sp==sp;return
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
        raise AssertionError(f'Air input slice budget at {cpu.s.pc:04X}')
    leaf=[(0xb1ac,),(0xb1cf,),(0x7df1,0x7e09),(0xc96a,),(0xdbfb,),(0xc583,),
          (0x7e40,0x7e4f),(0xe2c8,0xe2fb),(0x7f86,0x7fd8),(0x7fd8,0x8032),(0x7f86,0x8032)]
    entries=([[x] for x in leaf]+[
        [(0xb1ac,),(0x7df1,0x7e09)],
        [(0xc96a,),(0xdbfb,),(0xc583,),(0x7e40,0x7e4f),(0xa466,0xa4b3),(0xe2c8,0xe2fb),(0x7f86,0x8032),(0x84bc,0x852c)],
        [(0xf20d,),(0xc96a,),(0xdbfb,),(0xc583,),(0x7e40,0x7e4f),(0xa466,0xa4b3),(0x7df1,0x7e09),
         (0xe2c8,0xe2fb),(0x7f86,0x8032),(0xe2fb,0xe306),(0x84bc,0x852c)],
        [(0xe2c8,0xe306)],[(0xc96a,),(0xc9f7,)],[(0x7f86,0x8032),(0x751b,0x77c6)],
        [(0xe2c8,0xe2fb),(0x7f86,0x8032),(0xe2c8,0xe2fb),(0x7f86,0x8032)]])
    try:
        for entry in entries[mode]:invoke(*entry)
        if mode==1:value=cpu.s.a
    except Failure:status=2
    unknown=[(a,v) for a,v in memory.writes if a not in OUTPUTS and not (0x3c0<=a<0x400 or 0xad<=a<=0xb2)]
    assert not unknown,[(hex(a),v) for a,v in unknown]
    return {'status':status,'value':value,'masked':int(bool(cpu.s.ccr&0x10)),
            'state':[memory.mem[a] for a in OUTPUTS],'events':list(memory.events)}

counts={};rng=random.Random(0x317f86)
counts['direct']=compare((case(mode) for mode in range(18)),'direct air-input slices and producer/consumer joins')
variants=[]
for i in range(4096):
    edits={a:rng.randrange(256) for a in sorted(RAM|ALL_CAL)}
    edits.update({0x907:0,0x908:i%7,0x909:i&1,0x900:i%16,0x901:i%15,0x902:i%15,
        0x90a:3,0x910:rng.randrange(256),0x911:rng.randrange(256),0x912:1})
    variants.append(case(i%18,edits))
counts['variants']=compare(variants,'random state/profile, expanded matrix backing and callback cases')
directed=[]
qualified={0x5d02:0,0x44:0,0x6f:0,0x1c6:100,0x06:255,0x1d9:200,0x61:100}|word(0x2f4,0xb480)|word(0x1de,200<<8)
for rpm,throttle,difference in product([0,192,255],[129,200,247],[-8,0,8]):
    directed.append(case(5,qualified|{0x62:rpm,0x1d9:throttle}|word(0x1de,(throttle+difference)<<8)))
for rpm,coolant,throttle,difference in product([71,72,224,225],[172,173],[128,129],[-9,-8,0,8,9]):
    directed.append(case(5,qualified|{0x61:rpm,0x06:coolant,0x1d9:throttle}|word(0x1de,(throttle+difference)<<8)))
for flags,sample in product([0,4,8,12,64],[0,244,245,255]):
    directed.append(case(5,qualified|{0x6f:flags,0x1c6:sample,0x61:0}|word(0x2f4,0xff80)))
directed.append(case(5,qualified|{0x1c6:0,0x61:0}|word(0x2f4,0x0080)))
directed.append(case(5,qualified|{0x1c6:250}|word(0x2f4,0xff80)|{a:255 for a in range(0x455b,0x458b)}))
for runtime,speed in product([239,240,241,65535],[0,1,255]):
    directed.append(case(4,{0x3034:128,0x5b01:0x50,0x4e41:128,0x4e49:127,0x21d:255,0x21e:255,
        0x4e42:255,0x4e4a:255,0x284:speed,0x4e47:0,0x17:0xd5}|word(0xfd,runtime)))
counts['directed']=compare(directed,'BARO qualified lookup/fallback boundaries and MAT counter wrap/retention')
assert {0xc5e2,0xc5f3,0xc604}<=coverage,'Directed BARO branches must execute even in the quick run'
if '--quick' in sys.argv:
    print('Preliminary air-input comparison complete.');sys.exit(0)
counts['tps_round']=compare((case(1,word(0x2f6,zero)|{0xa6:raw}) for zero,raw in product(range(65536),[0,255])),
    'every TPS zero word with low/high raw inputs and wrapped rounding')
counts['tps_scale']=compare((case(1,{0xa6:raw,0x5b26:gain}|word(0x2f6,0x0080)) for raw,gain in product(range(256),repeat=2)),
    'all raw-TPS/gain pairs and both shift saturations')
counts['tps_zero']=compare((case(0,word(0x2f6,old)|{0xa6:255,0x5b27:(old^old>>8)&255,0x5b24:old&255}) for old in range(65536)),
    'all retained TPS-zero words, fractional targets and byte cap boundaries')
counts['coolant_values']=compare((case(3,{0x82d:raw,0x43:0x80 if raw&1 else 0,0x4e:0xa4,
    (0xfc45 if raw&1 else 0xfd45)+raw:value,0x16:0}) for raw,value in product(range(256),repeat=2)),
    'all coolant raw/converted pairs across both table views and range hysteresis')
counts['coolant_gates']=compare((case(3,{0x82d:raw,0x43:first,0x4e:flags,0x16:faults}|word(0xfd,runtime))
    for raw,first,flags,faults,runtime in product(range(256),[0,128],[0xa4,0xa5],[0,0x20,0x40,0x60],[159,160,161])),
    'coolant first/range/fault gates and runtime substitution priority')
counts['mat_options']=compare((case(4,{0x3034:raw,0x5b01:options,0x17:0xd5,0x21d:255,0x21e:255,0x284:raw&1}|word(0xfd,65535))
    for raw,options in product(range(256),repeat=2)), 'all MAT samples/options with retained faults and old-count admission')
counts['mat_counters']=compare((case(4,{0x3034:128,0x5b01:0x50,0x4e41:128,0x4e49:127,
    0x21d:count,0x21e:255-count,0x4e42:delay,0x4e4a:255-delay,0x284:count&1,0x4e47:0}|word(0xfd,65535))
    for count,delay in product(range(256),repeat=2)), 'every MAT counter/delay pair, opposite speed gates and byte wrap')
counts['baro_sensor']=compare((case(5,{0x5d02:4,0x3034:sample,0x4158:gain}|word(0x2f4,((sample^gain)<<8)|gain))
    for sample,gain in product(range(256),repeat=2)), 'all sensed BARO/gain pairs, +11 cap and signed lag rounding')
counts['baro_words']=compare((case(5,{0x5d02:0,0x44:0x10,0x1c6:old&255,0x4158:(old>>8)^old&255}|word(0x2f4,old))
    for old in range(65536)), 'all BARO filter words with direct MAP admission')
counts['baro_flags']=compare((case(5,{0x5d02:0,0x44:0,0x1c6:sample,0x6f:flags,0x61:0}|word(0x2f4,0x8080))
    for sample,flags in product(range(256),repeat=2)), 'BARO fault masks, retained estimates and direct-MAP priority')
counts['density']=compare((case(6,{0x1c6:sample}) for sample in range(256)), 'every zero-extended MAP density numerator')
counts['temperature']=compare((case(7,{0x400b:0x40,0x06:coolant,0x22f:mat,0x232:0,0x4ae3:coolant^mat})
    for coolant,mat in product(range(256),repeat=2)), 'all coolant/MAT pairs with varied charge weights and overflow paths')
counts['blend_edges']=compare((case(7,{0x400b:0x40,0x06:coolant,0x22f:mat,0x232:0,0x4ae3:gain})
    for gain,coolant,mat in product(range(256),[0,1,127,128,129,254,255],[0,64,128,192,255])),
    'charge-weight extremes, difference floors and separate blend saturations')
counts['ve_open']=compare((case(8,{0x1c0:load,0x62:rpm,0x1d9:255}) for load,rpm in product(range(256),repeat=2)),
    'all open-VE load/RPM coordinates and endpoint neighbor reads')
counts['ve_idle']=compare((case(8,{0x1c0:load,0x62:0,0x63:rpm,0x1d9:0,0x284:0,0x4f:0x38,0x20f:rpm})
    for load,rpm in product(range(256),repeat=2)), 'all idle-VE load/filtered-RPM coordinates and O2-reset request states')
counts['base_period']=compare((case(9,word(0x1e8,period)|{0x231:period&255,0x24a:(period>>8)}) for period in range(65536)),
    'every base-fuel period, AFR byte and air-rate publication boundary')
counts['base_flow']=compare((case(9,word(0x4d92,flow)|word(0x257,flow^0x8000)|{0x4d94:flow&255,0x24a:(flow>>8)})
    for flow in range(65536)), 'every injector divisor including zero and staged saturation')
joined=[]
for mode,flags,option,sample,action in product([11,12,13,14,15,16,17],[0,0x08,0x20,0x38],[0,0x40],[0,39,40,106,107,120,121,244,245,255],range(7)):
    joined.append(case(mode,{0x4f:flags|0x10,0x400b:option,0x90a:3,0x910:sample,0x911:255-sample,
        0x3034:sample,0x908:action,0x902:action*2,0x1c0:sample,0x20f:sample,0x06:sample,0x22f:255-sample,
        0x61:100,0x1d9:200,0x5d02:4 if action&1 else 0}|word(0x1de,200<<8)))
counts['joined']=compare(joined,'normalization/air/VE/output/REF joins and callback sampling order')
failures=[]
for item in variants[::23]+joined[::59]:
    for fail in range(1,len(execute(item)['events'])+1):failures.append((item[0],item[1]|{0x907:fail}))
counts['failures']=compare(failures,'every selected input/air/output/REF failure prefix')
history=[];edits={0x4f:0x10,0x400b:0x40,0x5d02:0,0x5b01:0x50,0x90a:3,0x61:100,0x24a:128}
for i in range(1024):
    edits.update({0x910:(i*17)&255,0x911:(i*11)&255,0x82d:i&255,0xa6:(i*7)&255,
        0x902:i%14,0x908:i%7,0x62:(i*3)&255,0x63:(i*5)&255,0x1c6:i&255,2:i%160})
    item=case([11,12,13,14,15,17][i%6],edits.copy());history.append(item)
    edits.update(dict(zip(OUTPUTS,execute(item)['state'])))
counts['history']=compare(history,'retained sensor, zero, BARO, VE and air-rate feedback histories')
required=set()
for start,end in [(0xb1ac,0xb1f0),(0x7df1,0x7e09),(0xc96a,0xc9c0),(0xdbfb,0xdc89),
                  (0xc583,0xc668),(0x7e40,0x7e4f),(0xe2c8,0xe2fb),(0x7f86,0x8032)]:
    pc=start
    while pc<end:required.add(pc);pc=decode(rom.read,pc).next_pc
assert required<=coverage,','.join(f'{a:04X}' for a in sorted(required-coverage))
assert {0x458a,0x4a88,0x4aee}<=table_reads,'Missing endpoint neighbor witness'
print(f'{sum(counts.values()):,} fuel-air comparisons; all {len(required)} scoped instruction starts; '
      f'{len(AIR_CAL)} distinct source-profile bytes and 1,581 expanded fixture bytes match stock. '
      'Broader roots, target ABI, physical timing and output response remain separate.')
