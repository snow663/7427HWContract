"""Pressure/TCC translations: actual instruction replay, joined parent and failure prefixes."""
from dataclasses import replace
from itertools import product
from pathlib import Path
import random
import subprocess
import sys
import tempfile
from compare_batch1 import IMAGE, ROM, compare, decode, successors, word, Case, stock, memory, seen, edges

RANGES=((0xb56b,0xb587),(0xb587,0xb88d),(0xbcc6,0xbe37),(0xc00b,0xc271))
def cases():
    rng=random.Random(0xb587)
    for gear,range_,event,fault in product(range(4),(0,1,2,0x20,0x50),(0,1,8),(0,4)):
        yield Case(0xbcc6,{0xd9:gear,0xa2:range_,0x83:event,0x98:fault,0x8e:1,0xdb:1},3)
    for value in range(256):
        yield Case(0xb587,{0x111:value})
    for flags,request in product((0,0x10,0x20,0x40,0x60),(0,2,4,6,0x84)):
        for command in (0,0x100,0x7fff,0xffff):
            yield Case(0xc00b,{0x89:flags,0x8b:request,0x110:64,
                               **word(0x126,command),**word(0x129,0xffff)},3)
    for mask in (0,0x40,0x80,0xc0):
        yield Case(0xb56b,{0x400f:mask,0x111:20},2)
    for i in range(1600):
        e=RANGES[i%4][0]
        ram={a:rng.randrange(256) for a in (*range(0x7f,0xa4),*range(0xb2,0xb6),
              *range(0xc2,0x100),*range(0x10a,0x12f),*range(0x13c,0x154),
              *range(0x18c,0x19a),0x1ac,0x20c,0x22f,0x844)}
        ram[0xd9]%=4
        ram[0x7f]=1<<(i%4)
        ram[0x9f]=1<<(i%3)
        ram[0x111]=0
        ram[0x400f]=0
        ram[0x8a]&=0xef
        if i%7==0: ram[0x8b]&=~6
        case=Case(e,ram,2)
        yield case
        if i%41==0:
            stock(case)
            for fail in range(1,memory.count+1): yield replace(case,fail=fail)
    for e in (0xb56b,0xb587,0xbcc6,0xc00b):
        case=Case(e,{0x400f:0,0x111:0},2)
        stock(case)
        for fail in range(1,memory.count+1): yield replace(case,fail=fail)
def main(binary):
    with tempfile.TemporaryDirectory() as temp:
        path=Path(temp)/'bmhm.bin'
        path.write_bytes(IMAGE)
        try:
            compare(binary,str(path),stock,cases(),'resident pressure and TCC closure batch 4')
        except AssertionError as error:
            detail=error.args[0]
            if isinstance(detail,tuple) and len(detail)>1 and isinstance(detail[1],Case):
                case=detail[1]
                expected=stock(case)
                observed=subprocess.run([binary,str(path)],input=case.row()+'\n',
                                        text=True,capture_output=True,check=True).stdout.split()
                print('first failure case entry:',hex(case.entry),flush=True)
                print('ROM ordered events:', ' '.join(x for x in expected if len(x)<100),flush=True)
                print('C ordered events:', ' '.join(x for x in observed if len(x)<100),flush=True)
                for want,got in zip((x for x in expected if len(x)>=100),(x for x in observed if len(x)>=100)):
                    diff=[(hex(i//2 if i//2<0x350 else i//2-0x350+0x800),want[i:i+2],got[i:i+2])
                          for i in range(0,min(len(want),len(got)),2) if want[i:i+2]!=got[i:i+2]]
                    print('RAM byte differences:',diff[:40],flush=True)
            raise
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
    print('uncovered instructions:',sorted(hex(x) for x in required-seen))
    print('uncovered conditional edges:',sorted((hex(a),hex(b)) for a,b in conditional-edges))
if __name__=='__main__':
    main(sys.argv[1])
