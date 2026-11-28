"""Factory instruction comparisons for the remaining eight diagnostic entries."""
from dataclasses import replace
from itertools import product
from pathlib import Path
import random
import sys
import tempfile
from compare_batch1 import IMAGE, ROM, compare, decode, successors, word, Case, stock, memory, seen, edges

RANGES=((0xe7c7,0xe808),(0xe808,0xe847),(0xe847,0xe8c8),(0xe8c8,0xe905),
        (0xeb81,0xebc0),(0xebc0,0xec2d),(0xeccc,0xecff),(0xef2b,0xef88))
# entry, enable, error, bit, edge, edge bit, timer, qualification, count, recovery
SIMPLE=((0xe7c7,0x5b00,0x16,1,0x94,1,0x162,0x5b1d,0x1f,0x5b1e),
        (0xe808,0x5b01,0x17,0x80,0x94,2,0x163,0x5b20,0x20,0x5b21),
        (0xe8c8,0x5b01,0x17,2,0x94,8,0x165,0x5b51,0x22,0x5b52),
        (0xeccc,0x5b07,0x1d,0x20,0x95,0x40,0x179,0x5b9d,0,0))

def cases():
    for e,en,live,bit,latch,lb,timer,limit,count,recovery in SIMPLE:
        for frozen,enabled,active,latched,fault,age,n in product((0,4),(0,bit),(0,bit),(0,lb),
                                                                (False,True),(0,1,255),(0,5)):
            a={0x3b:frozen,en:enabled,live:active,latch:latched,timer:age,limit:2}
            if count: a.update({count:n,recovery:5})
            if e==0xe7c7: a.update({0xa6:129 if fault else 128,0x5b1c:128})
            elif e==0xe808: a.update({0xa6:127 if fault else 128,0x5b1f:128})
            elif e==0xe8c8: a[0xa2]=128 if fault else 0
            else: a[0x9f]=8 if fault else 0
            yield Case(e,a,2)
    # E847: valid qualification, then independently suppress every gate.
    v={0x5b01:0x20,0x94:4,0x164:0,0x5b41:2,0x5b42:5,0x1c0:128,0xb2:128,
       0x5b45:64,0x5b46:192,0x5b47:64,0x5b48:192,
       **word(0xd1,10),**word(0x5b3d,20),**word(0xc2,30),**word(0x5b3f,20)}
    yield Case(0xe847,v,3)
    for edit in ({0x3b:4},{0x5b01:0},{0x94:0},{0x17:0x20},{0x18:0x20},{0x18:0x10},
                 {0x16:1},{0x17:0x80},{0x1c0:63},{0x1c0:193},{0xb2:63},{0xb2:193},
                 word(0xd1,20),{0x1c:1},{0x17:2},word(0xc2,20),{0xa2:0x50},{0x164:255}):
        yield Case(0xe847,v|edit,3)
    for count in (0,4,5,255):
        yield Case(0xe847,v|{0x94:0,0x17:0x20,0x21:count},2)
    # EB81 and EF2B: low-speed set and high-speed clear, each timed.
    v={0x5b06:8,0x5b83:2,**word(0x5b81,128),**word(0xb7,127)}
    for edit in ({},{0x3b:4},{0x5b06:0},{0x1c:8},{0x17:2},{0xa2:0x52},
                 word(0xb7,128),word(0xb7,128)|{0x1c:8},{0x174:255}):
        yield Case(0xeb81,v|edit,3)
    v={0x5b06:1,0x5b95:2,**word(0x5b91,128),**word(0xbd,127),
       **word(0xd3,129),**word(0x5b93,128),**word(0x1ac,129),**word(0x5b84,128)}
    for edit in ({},{0x3b:4},{0x5b06:0},{0x1c:1},{0xa2:0x50},{0x17:0x20},
                 {0x1c:4},word(0xd3,128),{0x1c:8},word(0x1ac,128),{0x17:2},
                 word(0xbd,128),word(0xbd,128)|{0x1c:1},{0x177:255}):
        yield Case(0xef2b,v|edit,3)
    # EBC0: unsigned comparison after the literal N/NEG sequence.
    v={0x5b06:4,0x5b8d:2,0x5b8c:5,0xa1:255,**word(0xd5,129),**word(0xcc,0),
       **word(0x5b86,128),**word(0x5b88,128),**word(0x1ac,128),**word(0x5b8a,128)}
    for edit in ({},{0x3b:4},{0x5b06:0},{0xa2:0x50},{0x1c:4},{0x1ab:1},
                 word(0x1ac,127),{0xa1:254},{0x17:2},{0x175:255},word(0xd5,128),
                 word(0xd5,128)|{0x95:0x10},word(0xd5,128)|{0x1c:4,0x29:0},
                 word(0xd5,128)|{0x1c:4,0x29:5}):
        yield Case(0xebc0,v|edit,3)
    for diff,bound,mode in product((0,1,127,128,129,0x7fff,0x8000,0x8001,0xfeff,0xff00,0xff01,0xffff),
                                   (0,1,128,255,256,0x7fff,0xffff),(0,0x50)):
        yield Case(0xebc0,v|word(0xd5,diff)|word(0x5b86,bound)|word(0x5b88,bound)|{0xa2:mode},3)
    rng=random.Random(0xe7c7)
    addresses=(0x3b,0x16,0x17,0x18,0x1c,0x1d,0x1f,0x20,0x21,0x22,0x29,0x94,0x95,
               0xa1,0xa2,0xa6,0xb2,0xb7,0xb8,0xbd,0xbe,0xc2,0xc3,0xcc,0xcd,0xd1,0xd2,
               0xd3,0xd4,0xd5,0xd6,0x9f,0x1ab,0x1ac,0x1ad,0x1c0,0x162,0x163,0x164,
               0x165,0x174,0x175,0x177,0x179,*range(0x5b00,0x5b9e))
    for i in range(1200):
        e=RANGES[i%len(RANGES)][0]
        a={x:rng.randrange(256) for x in addresses}
        if i%3: a[0x3b]&=~4
        case=Case(e,a,3)
        yield case
        if i%8==0:
            stock(case)
            for fail in range(1,memory.count+1): yield replace(case,fail=fail)
    for e,en,live,bit,latch,lb,timer,limit,count,recovery in SIMPLE:
        a={en:bit,live:bit,latch:0,timer:1,limit:2}
        if count: a.update({count:0,recovery:5})
        if e==0xe7c7: a.update({0xa6:128,0x5b1c:128})
        elif e==0xe808: a.update({0xa6:128,0x5b1f:128})
        case=Case(e,a,3)
        stock(case)
        for fail in range(1,memory.count+1): yield replace(case,fail=fail)

def main(binary):
    with tempfile.TemporaryDirectory() as temp:
        path=Path(temp)/'bmhm.bin'
        path.write_bytes(IMAGE)
        compare(binary,str(path),stock,cases(),'resident diagnostic closure batch 2')
    required,conditional=set(),set()
    for start,end in RANGES:
        pc=start
        while pc<end:
            required.add(pc)
            ins=decode(ROM.read,pc)
            targets=list(successors(ins))
            if len(targets)==2: conditional.update((pc,dest) for dest,_ in targets)
            pc=ins.next_pc
        assert pc==end
    print(f'{len(required & seen)}/{len(required)} instruction starts; '
          f'{len(conditional & edges)}/{len(conditional)} conditional outcomes')
    assert required<=seen, sorted(hex(p) for p in required-seen)
    assert conditional<=edges, sorted((hex(a),hex(b)) for a,b in conditional-edges)

if __name__=='__main__':
    main(sys.argv[1])
