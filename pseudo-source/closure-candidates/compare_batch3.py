"""Transmission input and mathematical leaves, with exact RAM and provider replay."""
from dataclasses import replace
from itertools import product
from pathlib import Path
import random
import sys
import tempfile
from compare_batch1 import IMAGE, ROM, compare, decode, successors, word, Case, stock, memory, seen, edges

RANGES=((0xaea4,0xb010),(0xb018,0xb084),(0xb089,0xb0e4),(0xb1f0,0xb23c),
        (0xb23c,0xb2b2),(0xc483,0xc4e5),(0xe58c,0xe5cf),(0xf420,0xf436),(0xf5a2,0xf5cf))

def cases():
    rng=random.Random(0xaea4)
    nums=(0,1,127,128,255,256,32767,32768,65535)
    for a,b in product(nums,repeat=2):
        yield Case(0xf5a2,word(0x350,a)|word(0x352,b))
        for k in (0,1,128,255):
            yield Case(0xf420,word(0x350,a)|word(0x352,b)|{0x5d0d:k})
    for old,now,timeout,gain,dt in product((0,255),(0,1,255),(0,1,2,255),(0,512,65535),(0,1,10000)):
        yield Case(0xe58c,{0xb9:old,0xc1:now,0xbc:timeout,0x352:8,
                           **word(0xba,123),**word(0xbd,4321),**word(0xbf,(123+dt)&65535),
                           **word(0x350,gain)},3)
    for flags,hot in product(range(16),range(8)):
        yield Case(0xc483,{0x9f:flags,0x87:hot},2)
    for temp,old,delay in product(range(0,256,5),(0,1,2,4,9),(0,1,255)):
        yield Case(0xb018,{0x1a1:temp,0x1a4:old,0x1a5:delay,0x5d29:2,
                            0x5d2a:255,0x5d2b:30,0x5d2c:60,0x5d2d:100,0x5d2e:180},3)
    for mode,fault,range_ in product((0,32),(0,4),(0,2)):
        yield Case(0xb018,{0x5d02:mode,0x98:fault,0xa2:range_,0x9f:0xff})
    for i in range(1800):
        e=RANGES[i%len(RANGES)][0]
        a={x:rng.randrange(256) for x in (*range(0x76,0x84),*range(0x86,0xa4),
               *range(0xb7,0xd8),*range(0x160,0x180),*range(0x1a1,0x1ae),
               0x3b,0x3d,0x4d,0x50,0x5f,0x60,0xd9,0xeb,0xec,0xed,0xee,0x100,0x102,
               0x16,0x17,0x18,0x1a,0x1c,0x1d,0x1f,0x20,0x21,0x22,0x29,
               *range(0x350,0x354),*range(0x5d02,0x5d30),*range(0x5b00,0x5b9e),
               0x3000,0x3002,0x3010,0x3011,0x3027,0x3060,0x3062,
               0x3fc2,0x3fc3,0x3fc6,0x3fc7,0x3fe0,0x3fe1,0x3ff8,0x3ff9)}
        case=Case(e,a,3)
        yield case
        if i%9==0:
            stock(case)
            for fail in range(1,memory.count+1): yield replace(case,fail=fail)
    for e in (0xaea4,0xb018,0xb089,0xb1f0,0xb23c,0xc483,0xe58c):
        case=Case(e,{},2)
        stock(case)
        for fail in range(1,memory.count+1): yield replace(case,fail=fail)

def main(binary):
    with tempfile.TemporaryDirectory() as temp:
        path=Path(temp)/'bmhm.bin'
        path.write_bytes(IMAGE)
        compare(binary,str(path),stock,cases(),'resident input closure batch 3')
    required,conditional=set(),set()
    for start,end in RANGES:
        pc=start
        while pc<end:
            required.add(pc)
            ins=decode(ROM.read,pc)
            targets=list(successors(ins))
            if len(targets)==2 and ins.op not in ('JSR','BSR'):
                conditional.update((pc,dest) for dest,_ in targets)
            pc=ins.next_pc
        assert pc==end
    print(f'{len(required & seen)}/{len(required)} instruction starts; '
          f'{len(conditional & edges)}/{len(conditional)} conditional outcomes')
    # Fixed register samples cannot exercise a mid-pair capture change;
    # remaining uncovered outcomes are explicit, not silently certified.
    print('uncovered instructions:',sorted(hex(x) for x in required-seen))
    print('uncovered conditional edges:',sorted((hex(a),hex(b)) for a,b in conditional-edges))

if __name__=='__main__':
    main(sys.argv[1])
