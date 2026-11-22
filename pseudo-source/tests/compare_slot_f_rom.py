"""SlotF diagnostic prefix and complete output/fault/fuel/REF joins versus BMHM."""
from pathlib import Path
_parent=Path(__file__).with_name('compare_slow_fuel_rom.py')
exec(compile(_parent.read_text().split('\nwith tempfile.',1)[0],str(_parent),'exec'),globals())

_SlotFParentMemory=Memory
class Memory(_SlotFParentMemory):
    def read8(self,a):
        value=super().read8(a)
        if not self.fetching and a==self.foreign and 'R' in self.foreign_access:
            if self.action==50 and a==0xd7:self.mem[a]^=0x7f
            if self.action==51 and 0x94<=a<=0x96:self.mem[a]^=0xf0
            if self.action==52 and 0x5b53<=a<=0x5bc0:self.mem[a]=(value+17)&255
            if self.action==55 and a==0x1c:self.mem[a]^=1
            if self.action==56 and 0x166<=a<=0x185:self.mem[a]=(value+17)&255
        return value
    def read16(self,a):
        value=super().read16(a)
        if not self.fetching and a==self.foreign and 'R' in self.foreign_access:
            if self.action==53 and a in (0xeb,0xf9):self.mem[a]^=0x80;self.mem[a+1]^=255
        return value
    def write8(self,a,value):
        super().write8(a,value)
        if a==self.foreign and self.action==54 and a==0x1c:self.mem[0x3b]^=4

memory=Memory();cpu=HC11CPU(memory);coverage=set();original_fetch=cpu._fetch8;cpu._fetch8=fetch
LEAVES=[0xe905,0xe99e,0xee02,0xee61,0xeebc,0xec2d,0xecff,0xef88,0xf02f,0xf0ad]
ENTRIES=[[(entry,0x7000)] for entry in LEAVES]+[[(0xc4f5,0x7000)],[(0x7b5a,0x7000)],
    [(0x7aad,0x7000),(0x7b5a,0x7000),(0x7d4b,0x7000),(0x751b,0x77c6)],
    [(0x7b5a,0x7000),(0x7d4b,0x7000)],[(0x7b5a,0x7000),(0x7b5a,0x7000)]]
NATIVE_CALLEES=NATIVE_CALLEES|{0xc514}
NATIVE_GATES=NATIVE_GATES|set(LEAVES)
VALUE_MODES=set();ENTRY_WORD_ARGUMENT={}
BASE=BASE|{0x3b:0,0x5b02:3,0x5b03:128,0x5b06:0x32,0x5b07:8,0x5b08:0x70,
    0x16:0,0x17:0,0x18:0,0x19:0,0x1b:0,0x1c:0,0x1d:0,0x1e:0,
    0x94:0,0x95:0x2d,0x96:0x38,0x9c:1,0x8e:0,0xb2:100,0xb5:100,
    0xd7:100,0xd9:1,0xa2:15,0x14f:100,0x178:0,0x182:3,0x183:3,0x184:3,0x185:3,
    0x5b53:10,0x5b54:90,0x5b55:2,0x5b56:2,0x5b57:3,0x5b58:3,
    0x5b59:90,0x5b5a:10,0x5b5b:2,0x5b5c:2,0x5b5d:3,0x5b5e:3,
    0x5b61:3,0x5b62:3,0x5b79:3,0x5b7a:3,0x5b7f:3,0x5b80:10,
    0x5b8e:10,0x5b8f:3,0x5b90:3,0x5b9e:90,0x5b9f:100,
    0x5ba8:3,0x5ba9:3,0x5baa:3,0x5bab:3,0x5bac:10,0x5bad:10,0x5bae:10,0x5bbf:3,0x5bc0:3}
BASE|=word(0xeb,100)|word(0xed,100)|word(0x5b5f,100)|word(0x5b77,10)
BASE|=word(0x5b7d,90)|word(0x5b7b,110)|word(0x1ac,1000)|word(0x5b84,10)|word(0x5ba0,3)
for address,value in zip(range(0x5baf,0x5bbf,2),[10,20,30,40,50,60,70,80]):BASE|=word(address,value)
BASE|=word(0xf9,100)
QUALIFIED=[{0x94:0x10},{0x9c:0,0x94:0x80,0xd7:5},{0x89:32},{0x89:32,0xd9:3},
    {0x89:0},{}, {}, {}, {}|word(0xf9,60),{0xd9:2}]
COUNTERS=[0x166,0x167,0x168,0x172,0x173,0x176,0x17a,0x17f,0x180,0x181]
def qualified(mode,edits=None,**kwargs):return case(mode,QUALIFIED[mode]|(edits or {}),**kwargs)

with tempfile.TemporaryDirectory(prefix='pcm-slot-f-') as directory:
    path=Path(directory)/'bmhm.bin';path.write_bytes(image);os.environ['PCM_FUEL_CONTROLLER_ROM']=str(path)
    subprocess.run([binary,'--contracts'],check=True);counts={}
    counts['entries']=compare((case(mode) for mode in range(15)),'ten diagnostic bodies, wrapper, complete slotF and real controller/REF joins')
    counts['freeze']=compare((case(mode,{0x3b:flags,0x51:0}) for mode,flags in product(range(15),[0,4,255])),
        'native freeze gate at each observation while whole-slot outputs/reactions/fuel still execute')
    byte_addresses=[0x16,0x17,0x18,0x19,0x1b,0x1c,0x1d,0x1e,0x8e,0x89,0x94,0x95,0x96,
        0x9c,0xa2,0xb2,0xb5,0xd7,0xd9,0x14f,0x178,*COUNTERS,*range(0x182,0x186)]
    edges=[0,1,2,3,7,8,9,10,11,15,16,31,32,63,64,89,90,91,99,100,101,127,128,129,254,255]
    counts['byte_edges']=compare((qualified(mode,{address:value}) for mode,address,value in product(range(10),byte_addresses,edges)),
        'qualified byte admissions, fault masks, exact boundaries, counter wrap and retained age edges')
    counts['flag_bits']=compare((qualified(mode,{address:value}) for mode,address,value in product(range(10),
        [0x17,0x1c,0x1d,0x94,0x95,0x96,0xa2],range(256))),
        'complete shared flag bytes including partial multi-bit range qualification')
    counts['brake_episodes']=compare((qualified(mode,{0x9c:brake,0x94:flags,0xd7:speed,
        0x182:age,0x183:age,0x184:age,0x185:age,COUNTERS[mode]:timer},action=action)
        for mode,brake,flags,speed,age,timer,action in product([0,1],[0,1],[0,16,32,48,64,128,192,255],
        [0,10,11,89,90,91,255],[0,2,3,254,255],[0,2,255],[0,51])),
        'both brake episodes, strict age windows, suppressed zero writes and fresh latch reads')
    recoveries=[(0,0x18,2,0x23),(1,0x18,1,0x24),(2,0x19,128,0x25),(3,0x1c,32,0x28),
        (4,0x1c,16,None),(5,0x1c,2,0x2a),(7,0x1e,64,0x2e),(8,0x1e,32,0x2f),(9,0x1e,16,0x30)]
    recovery_cases=[]
    for mode,address,bit,budget in recoveries:
        for observed,live,age,allowance in product([0,255],[0,bit,255],[0,1,2,254,255],[0,2,3,254,255]):
            edits={0x94:observed,0x95:observed,0x96:observed,address:live,COUNTERS[mode]:age}
            if mode==0:edits[0x9c]=0
            if mode==1:edits[0x9c]=1
            if mode==3:edits|=word(0xed,0)
            if mode==5:edits[0x14f]=0
            if budget is not None:edits[budget]=allowance
            recovery_cases.append(qualified(mode,edits))
    counts['recovery']=compare(recovery_cases,'first-good observations, one-time budgets, add-two wrap and timed brake recovery')
    counts['word_edges']=compare((qualified(mode,word(address,sample)|word(threshold,limit))
        for mode,address,threshold in [(2,0xeb,0x5b5f),(3,0xed,0x5b77),(4,0xeb,0x5b7d),
            (4,0xeb,0x5b7b),(6,0x17a,0x5ba0),(7,0xf9,0x5baf),(8,0xf9,0x5bb9),(9,0xf9,0x5bb3)]
        for sample,limit in product([0,1,2,3,9,10,11,19,20,21,29,30,31,59,60,61,99,100,101,32767,32768,65534,65535],
                                    [0,1,3,10,30,60,100,32767,32768,65535])),
        'signed slip versus unsigned ratios, word-timer rollover and threshold equality')
    counts['ratio_windows']=compare((qualified(7,word(0xf9,ratio)|{0xd9:gear},action=action)
        for ratio,gear,action in product(range(101),[0,1,2,3,255],[0,53])),
        'four open ratio windows and the intervening gear rejection')
    counts['temperature']=compare((qualified(6,{0xb5:temp,0x1d:live,0x1b:fault}|word(0x17a,timer)|word(0x5ba0,limit))
        for temp,live,fault,timer,limit in product([0,89,90,91,99,100,101,255],[0,8],[0,64],
            [0,1,2,3,255,256,65534,65535],[0,1,3,256,65535])),
        'temperature hysteresis, entry-only sensor fault inhibit and complete sixteen-bit timer')
    enabled=[0x5b02,0x5b03,0x5b06,0x5b07,0x5b08]
    counts['calibration']=compare((qualified(mode,{address:value},action=action)
        for mode,address,value,action in product(range(10),enabled,[0,1,2,8,16,32,64,128,255],[0,52])),
        'enable bits and live calibration capture')
    counts['live']=compare((qualified(mode,{COUNTERS[mode]:2},action=action,masked=masked)
        for mode,action,masked in product(range(10),[50,51,52,53,54,55,56],[0,1])),
        'fresh operands, captured values, inter-monitor freeze changes and unchanged IRQ mask')
    import random
    rng=random.Random(0x31c4f5);profiles=[]
    for i in range(1024):
        mode=i%10;edits={a:rng.randrange(256) for a in byte_addresses}
        edits|={a:rng.randrange(256) for a in range(0x5b53,0x5bc1)}
        profiles.append(qualified(mode,edits,action=[0,50,51,52,53,55,56][i%7]))
    counts['profiles']=compare(profiles,'raw diagnostic profiles with inconsistent limits and retained state')
    joined=[]
    for mode,phase,live,observed,action in product([10,11,12,13,14],[1,15,17,31,159],[0,255],[0,255],[0,51,54,55]):
        joined.append(case(mode,{2:phase,0x1c:live,0x1d:live,0x1e:live,0x94:observed,0x95:observed,
            0x96:observed,0x51:0,0x3034:128,0x72:0,0x400f:0x10}))
        joined[-1]=(joined[-1][0],0,action,0,joined[-1][4])
    counts['joined']=compare(joined,'ordered diagnostics/reactions/fuel/REF and repeated whole-slot observations')
    failures=[]
    selected=[qualified(mode,{COUNTERS[mode]:2}) for mode in range(10)]+[case(10),case(11),case(12),case(14)]
    selected+=recovery_cases[::75]
    for item in selected:
        for fail in range(1,len(execute(item)['events'])+2):failures.append((item[0],fail,*item[2:]))
    counts['failures']=compare(failures,'every failed provider prefix in admitted/recovery/whole-slot paths')
    history=[];retained={}
    for i in range(160):
        item=case(12,retained|{2:(1+16*i)%160,0x9c:(i//20)&1,0xd7:(i*7)&255,0x1a6:(i*17)&255,
            0x4f:0x90,0x44:0,0x86:0,0x400f:0x10,0x3034:(i*11)&255})
        history.append(item);state=bytes.fromhex(execute(item)['state']);retained.update(enumerate(state[:0x900]))
        retained.update({0x3000+j:value for j,value in enumerate(state[0x900:0x970])})
        retained.update({0x3fc0+j:value for j,value in enumerate(state[0x970:])})
    counts['history']=compare(history,'retained slot1/whole-slotF/fuel/REF histories with canonical transmission owners')
    required=set()
    for start,end in [(0xe905,0xea40),(0xee02,0xee5f),(0xee61,0xef2b),(0xec2d,0xec79),
        (0xecff,0xed3f),(0xef88,0xf131),(0xc4f5,0xc514),(0x7b5a,0x7b6d)]:
        pc=start
        while pc<end:required.add(pc);pc=decode(rom.read,pc).next_pc
    missing=required-coverage;print('Uncovered slotF starts:',','.join(f'{a:04X}' for a in sorted(missing)),flush=True)
    assert not missing
    print(f'{sum(counts.values()):,} slotF comparisons; all {len(required)} scoped starts match. '
        'Target ABI, peripheral timing and the remaining slow slots stay separate.',flush=True)
