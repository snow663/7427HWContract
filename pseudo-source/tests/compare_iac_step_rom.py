"""Check the resident IAC step/count service and selected sequential joins.

Literal mask assignments are observable boundaries; callback effects are fixtures,
not a target interrupt ABI or a guarantee that every count reaches the motor.
"""
from pathlib import Path
_prior=Path(__file__).with_name('compare_iac_main_rom.py')
exec(compile(_prior.read_text().rsplit('\ncounts={}',1)[0],str(_prior),'exec'),globals())
OUTPUTS=OUTPUTS+[10]
assert len(OUTPUTS)==len(set(OUTPUTS))
OUTPUT_SET=set(OUTPUTS)
BASE=BASE|{10:0,7:100,8:150,9:4,2:0,0x3e:0xa1,0x44:0xc4,0xa7:130,0x4c:0xa3,0x908:0,0x90f:0}
step_defaults=json.loads(subprocess.check_output([binary,'--step-defaults'],text=True))
assert step_defaults==[[0x4eb6,rom.read(0x4eb6,1)[0]]]
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
            if opcode==0x0F and action==25:memory.mem[10]=0xE7;memory.mem[0x4C]=0xA3
            if opcode==0x0E and action==26:memory.mem[10]=0xB8;memory.mem[0x4C]=0x5A
            if opcode==0x0F and action==27:
                memory.mem[10]=0xFE;memory.mem[0x4C]=0x63;memory.mem[7]=77;memory.mem[8]=99;memory.mem[2]=3
        raise AssertionError(f'Main IAC execution budget at {cpu.s.pc:04X}')

    try:
        entries=[(0x91A3,),(0x91A3,0x93D0),(0x93D0,0x91A3),(0x91A3,0x9E99),(0x9E99,0x91A3),
                 (0x91A3,0xC514),(0xC514,0x91A3),(0x91A3,)*16,(0x91A3,0xA2B0),(0xA2B0,0x91A3)]
        for index,start in enumerate(entries[mode]):
            invoke(start)
            if mode==7 and index<15:memory.mem[2]=(memory.mem[2]+1)%160
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
                Path('/tmp/iac-step-failure.json').write_text(json.dumps({'item':item,'actual':actual,'expected':expected,'outputs':OUTPUTS}))
                differences=[(hex(a),x,y) for a,x,y in zip(OUTPUTS,actual['state'],expected['state']) if x!=y]
                raise AssertionError((label,count+index,item[0],differences,{k:(actual[k],expected[k]) for k in actual if k!='state' and actual[k]!=expected[k]}))
        count+=len(chunk)
    print(f'{count:,} {label} match.',flush=True);return count


counts={}
rng=random.Random(0x3191A3)
counts['initial']=compare((case(mode) for mode in range(10)),'step direct, sixteen-entry and sequential joins')
variants=[]
for i in range(2048):
    edits={a:rng.randrange(256) for a in sorted(BASE.keys()|MAIN_CAL|IAC_CAL|SLOW_CAL|{0x4EB6})}
    edits.update({0x908:[0,4,25,26,27][i%5],0x909:i&1,0x90F:0,0x907:0})
    variants.append(case(i%10,edits))
counts['variants']=compare(variants,'step state/profile variants and callback joins')
counts['positions']=compare((case(0,{7:position,8:target,10:((position^target)&0xfc)|direction,
    0x4c:(position+target)&255}) for position,target,direction in product(range(256),range(256),[0,1])),
    'every position/target pair with both old directions')
counts['voltage']=compare((case(0,{0xa7:battery,0x4eb6:threshold,0x44:0xc4|off,
    10:0xef|(0x10 if (battery^threshold)&1 else 0),0x3e:(battery+threshold)&255})
    for battery,threshold,off in product(range(256),range(256),[0,0x10])),
    'every battery/threshold pair with both ignition gates')
counts['shadow']=compare((case(0,{10:mode,0x4c:shadow,7:10 if shadow%3==0 else 20,
    8:10 if shadow%3==1 else 20}) for mode,shadow in product(range(256),repeat=2)),
    'all old control/shadow bytes with interleaved count relations')
counts['phase']=compare((case(0,{2:phase,10:mode,9:reset,7:10,8:20})
    for phase,mode,reset in product(range(256),range(0,32,1),[0,1])),
    'all phase bytes and direction/ring/enable states with reset clear/set')
callbacks=[case(0,{10:mode,0x4c:shadow,0x908:action,0x909:masked})
    for mode,shadow,action,masked in product(range(256),[0,255,0xa5],[0,4,25,26,27],[0,1])]
counts['callbacks']=compare(callbacks,'latched command, post-SEI shadow and post-CLI state witnesses')
failures=[]
for item in callbacks:
    for fail in [1,2]:failures.append((item[0],item[1]|{0x907:fail}))
counts['failures']=compare(failures,'SEI/CLI failures after completed count/phase prefixes')
counts['coowners']=compare((case(mode,{0xd9:gear,0x4c:shadow,0x400f:0x40,10:(gear^shadow)&255})
    for gear,shadow,mode in product(range(256),[0,1,0x1c,0x7f,0x80,0xe3,0xff],[5,6])),
    'ordered step/gear co-owner calls across every raw gear index')
joined=[]
for i in range(2048):
    edits={a:rng.randrange(256) for a in sorted(BASE.keys()|MAIN_CAL|IAC_CAL|SLOW_CAL|{0x4EB6})}
    edits.update({0x907:0,0x90f:0,0x908:[0,4,25,26,27][i%5],0x909:i&1})
    joined.append(case([1,2,3,4,8,9][i%6],edits))
counts['joined']=compare(joined,'main/background/slow consumers and returned software commands')
joined_failures=[]
for item in joined[::7]:
    for fail in range(1,len(execute(item)['events'])+1):joined_failures.append((item[0],item[1]|{0x907:fail}))
counts['joined_failures']=compare(joined_failures,'joined step/controller failure prefixes')
history=[];edits={0x09:1,0x44:0xd4,0x86:0xa0,0x3b:0,0x3e:0,0xa7:130,10:1,7:255,8:0,
    0x907:0,0x90f:0,0x908:0,0x4f:0x75}
for entry in range(1024):
    edits.update({2:entry%160,0xa7:[105,106,169,170,130][(entry//31)%5],0x44:0xd4 if entry<512 else 0xc4})
    if entry==512:edits[8]=200
    item=case([0,2,8][entry%3],dict(edits));history.append(item)
    edits.update(dict(zip(OUTPUTS,execute(item)['state'])))
counts['history']=compare(history,'retained reset, park, running-command and step histories')
required=set();pc=0x91a3
while pc<0x920e:required.add(pc);pc=decode(rom.read,pc).next_pc
assert required<=coverage,','.join(f'{a:04X}' for a in sorted(required-coverage))
print(f'{sum(counts.values()):,} step comparisons; all {len(required)} instruction starts exercised; '
      'stock4EB6 matches. No step latch write or physical cadence is inferred.')
