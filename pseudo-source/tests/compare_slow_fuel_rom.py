"""Slot1, callable slotF suffix and slow fuel producers versus actual BMHM.

The preceding C514/C4F5 slotF group remains an explicit caller precondition.
"""
from pathlib import Path
_parent=Path(__file__).with_name('compare_fuel_controller_rom.py')
exec(compile(_parent.read_text().split('\nwith tempfile.',1)[0],str(_parent),'exec'),globals())

_SlowParentMemory=Memory
class Memory(_SlowParentMemory):
    def read8(self,a):
        value=super().read8(a)
        if not self.fetching and a==self.foreign and 'R' in self.foreign_access:
            if self.action==40 and a==0x89:self.mem[a]^=0x20
            if self.action==41 and a==0x5d0a:self.mem[a]=(value+37)&255
            if self.action==43 and a==0xa7:self.mem[2]^=0x10
            if self.action==44 and a==0x2f3:self.mem[a]=(value+17)&255
            if self.action==45 and 0x5b2b<=a<=0x5b3c:self.mem[a]^=255
            if self.action==46 and a==0x22a:self.mem[a]=(value+17)&255
            if self.action==48 and a==0x72:self.mem[a]^=3
        return value
    def read16(self,a):
        value=super().read16(a)
        if not self.fetching and a==self.foreign and 'R' in self.foreign_access:
            if self.action==42 and 0x5168<=a<0x5190:self.mem[a]=(self.mem[a]+17)&255
        return value
    def write8(self,a,value):
        super().write8(a,value)
        if a==self.foreign and self.action==47 and a in (0x98,0x99):self.mem[2]^=0x10

memory=Memory();cpu=HC11CPU(memory);coverage=set();original_fetch=cpu._fetch8;cpu._fetch8=fetch
ENTRIES=[[(0xc668,0x7000)],[(0xadaa,0x7000)],[(0x7aad,0x7000)],[(0xe286,0xe2c8)],
    [(0xe286,0x7000)],[(0xe62d,0x7000)],[(0xe6bc,0x7000)],[(0xe6e5,0x7000)],
    [(0x7b60,0x7000)],[(0x7aad,0x7000),(0x7d4b,0x7000)],
    [(0x7b60,0x7000),(0x7d4b,0x7000)],
    [(0x7aad,0x7000),(0x7b60,0x7000),(0x7d4b,0x7000),(0x751b,0x77c6)]]
NATIVE_CALLEES=NATIVE_CALLEES|{0xc583}
NATIVE_INLINE=NATIVE_INLINE|{0xe2c8:0xe306,0xe30b:None}
NATIVE_GATES=NATIVE_GATES|{0xe306,0x7b69}
IGNORED_STATE=[(0x3b0,0x400)];VALUE_MODES={6};ENTRY_WORD_ARGUMENT={0xe6bc:0x930}
BASE=BASE|{0x2f3:120,0x2f4:150,0x2f5:128,0x5b04:4,0x72:0,0x1a:0,0x930:0xe7,0x931:0x55,
    0x4e85:3,0x4e86:100,0x4e87:80,0x4e88:90,0x22a:0,0x853:1,0x854:80}
BASE=BASE|word(0xac,0x1234)

with tempfile.TemporaryDirectory(prefix='pcm-slow-fuel-') as directory:
    path=Path(directory)/'bmhm.bin';path.write_bytes(image);os.environ['PCM_FUEL_CONTROLLER_ROM']=str(path)
    subprocess.run([binary,'--contracts'],check=True);counts={}
    counts['entries']=compare((case(mode) for mode in range(12)),'slot1, slow producers, fault reactions, suffix and real controller/REF entries')
    counts['baro_gates']=compare((case(0,{0x5b30:baro_mask,0x1b:baro_fault,0x5b2d:map_mask,
        0x18:map_fault,0x5d02:option}) for baro_mask,baro_fault,map_mask,map_fault,option
        in product([0,2,4,6],[0,2,4,6],[0,16,32,48],[0,16,32,48],[0,4])),
        'BARO high-before-low substitution, partial fault masks and separate-sensor option')
    counts['baro_filter']=compare((case(0,{0x5b30:0,0x5b2d:0,0x2f3:sample,0x5d07:gain}|
        word(0x5d08,offset)|word(0xac,old),action=action)
        for sample,gain,offset,old,action in product([0,1,127,128,255],[0,1,128,255],
        [0,1,32767,65535],[0,1,32767,32768,65535],[0,41,44])),
        'BARO product/offset wrap, retained word fraction and fresh lag/sample reads')
    window={0x400f:0x40,0x515a:100,0x515b:5,0x515c:10,0x515d:10,0x515e:3,0x515f:7,
        0x5160:200,0x5161:210,0x5162:20,0x5163:30,0x5164:20,0x5165:30,0x5166:40,0x5167:50}
    window|={a:0 for a in range(0x5168,0x5171)}|{a:255 for a in range(0x5171,0x5190)}
    counts['tcc_windows']=compare((case(1,window|{0x89:context,0x4d:gear,0x284:speed,
        0x1d9:throttle,0x854:throttle,0x853:timer},action=action)
        for context,gear,speed,throttle,timer,action in product([0,32,255],[0,1],
        [0,19,20,21,29,30,31,49,50,51,60,79,80,199,200,201,210,255],
        [0,40,128,255],[0,1,255],[0,40,42])),
        'nonelectronic TCC load/speed windows, wrapped coordinates, live context and countdown')
    counts['tcc_qualify']=compare((case(1,window|{0x89:context,0x284:60,0x1d9:throttle,0x854:40,
        0x515c:delta,0x515d:delta,6:coolant,0x63:rpm,0x853:0})
        for context,throttle,delta,coolant,rpm in product([0,32],[39,40,41],[0,1,255],[99,100,101],[19,20,29,30,31])),
        'TCC falling/rising TPS equality, coolant admission and selected RPM threshold')
    counts['tcc_disabled']=compare((case(1,{0x400f:0,0x89:flags,0x853:timer,0x854:77})
        for flags,timer in product([0,32,255],[0,1,255])), 'disabled TCC retains state and history')
    import random
    rng=random.Random(0x317aad);profiles=[]
    for i in range(768):
        edits={a:rng.randrange(256) for a in [6,0x4d,0x63,0x89,0x284,0x1d9,0x853,0x854,*range(0x515a,0x5190)]}
        edits[0x400f]=64;profiles.append(case(1,edits,action=[0,40,42][i%3]))
    counts['tcc_profiles']=compare(profiles,'TCC raw profiles, descending/ascending live curves and retained-history choices')
    counts['pump']=compare((case(3,{0x5b04:enabled,0x72:stage,0xa7:battery,0x55:feedback,
        0x22a:count,0x4f:running},action=action)
        for enabled,stage,battery,feedback,count,running,action in product([0,4],[0,1,2,3,252,255],
        [0,89,90,255],[0,79,80,99,100,255],[0,2,3,255],[0,16],[0,46,48])),
        'pump mask/state retention, incremented-count wrap, feedback/battery edges and live stage')
    faults=[]
    clean={a:0 for a in range(0x16,0x1f)}|{a:0 for a in range(0x5b2b,0x5b3d)}
    clean|={a:0 for a in range(0xe717,0xe720)}|{a:0 for a in range(0xe756,0xe75f)}
    for mode,bank,bit,alt,reaction,live,mask in product([5,6,7],range(1,10),range(8),[0,1],[0,1],[0,1],[0,1]):
        value=1<<bit;edits=clean|{0x5b33+bank:alt*value,0x5b2a+bank:reaction*value,
            0x15+bank:live*value,0xe716+bank:mask*value,0xe755+bank:mask*value}
        faults.append(case(mode,edits))
    counts['fault_basis']=compare(faults,'every bank/bit truth basis for opposite alternate-reaction polarities')
    counts['mask_pointers']=compare((case(6,{**{a:255 for a in range(0x16,0x1f)},
        **{a:255 for a in range(0x5b2b,0x5b34)},**{a:0 for a in range(0x5b34,0x5b3d)}}|word(0x930,pointer),action=action)
        for pointer,action in product([0,1,0x7fff,0xfff7,0xfff8,0xffff,0xe716,0xe755],[0,45])),
        'logical mask-pointer wrap outside target stack and fresh reaction reads')
    counts['phase']=compare((case(mode,{2:phase,0x4f:running,0x50:diagnostic,0x51:0},action=action)
        for mode,phase,running,diagnostic,action in product([4,8],range(160),[0,0x90],[0,16],[0,43,47])),
        'every slow phase, charge/offset-before-gate, startup/closed-loop and post-suffix refresh')
    joined=[]
    for mode,phase,option,baro,running,action in product([9,10,11],[1,15,17,31,49,159],[0x10,0x50],
            [0,4],[0,0x90],[0,41,43,44,47]):
        joined.append(case(mode,{2:phase,0x400f:option,0x5d02:baro,0x4f:running,0x3034:128},action=action))
    counts['joined']=compare(joined,'real slot1/suffix-to-fuel-to-REF joins with shared BARO/TCC/CL owners')
    failures=[]
    selected=[case(0),case(0,{0x5b30:4,0x1b:4}),case(1,window|{0x284:60,0x1d9:40,0x854:40}),
        case(2,{0x5d02:4,0x3034:120}),case(3),case(3,{0x72:1}),case(4),
        case(6),case(5,clean),case(7,clean),case(8),case(11)]
    for item in selected:
        for fail in range(1,len(execute(item)['events'])+2):failures.append((item[0],fail,*item[2:]))
    counts['failures']=compare(failures,'each provider/mask/module failed prefix across slow producers and joined paths')
    history=[];retained={}
    for i in range(128):
        item=case(11,retained|{2:(1+16*i)%160,0x1a6:(i*17)&255,0x4f:0x90,0x44:0,0x86:0,
            0x400f:0x50,0x5d02:i&4,0x3034:(i*11)&255,0x284:(i*7)&255,0x72:0})
        history.append(item);state=bytes.fromhex(execute(item)['state']);retained.update(enumerate(state[:0x900]))
        retained.update({0x3000+j:value for j,value in enumerate(state[0x900:0x970])})
        retained.update({0x3fc0+j:value for j,value in enumerate(state[0x970:])})
    counts['history']=compare(history,'retained slot1/suffix/fuel/REF histories including both AC accumulator bytes')
    required=set()
    for start,end in [(0x7aad,0x7ab7),(0xc668,0xc6bb),(0xadaa,0xae5c),(0xe286,0xe2c8),
        (0xe306,0xe30b),(0xe62d,0xe654),(0xe6bc,0xe6e4),(0xe6e5,0xe6f5),(0x7b60,0x7b6d),
        (0xf436,0xf459),(0xf4bd,0xf4de)]:
        pc=start
        while pc<end:required.add(pc);pc=decode(rom.read,pc).next_pc
    missing=required-coverage;print('Uncovered slow-fuel starts:',','.join(f'{a:04X}' for a in sorted(missing)),flush=True)
    assert not missing
    print(f'{sum(counts.values()):,} slow-fuel comparisons; all {len(required)} new scoped starts match. '
          'SlotF C514/C4F5 prefix, slot4 callers and target timing remain separate.',flush=True)
