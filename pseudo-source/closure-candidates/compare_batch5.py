"""AE85 prefix joining and the reset prelude; full parent/boot integration is separate."""
from dataclasses import replace
from itertools import product
from pathlib import Path
import random
import sys
import tempfile
from compare_batch1 import IMAGE, compare, word, Case, stock, memory

def cases():
    for opt2 in range(256):
        case=Case(0x7100,{0x3038:opt2})
        yield case
        if opt2%31==0:
            stock(case)
            for fail in range(1,memory.count+1): yield replace(case,fail=fail)
    rng=random.Random(0xae85)
    for i in range(256):
        ram={a:rng.randrange(256) for a in (*range(0x76,0xa4),*range(0xb7,0xd8),
             *range(0x160,0x180),*range(0x1a1,0x1ae),0x3b,0x3d,0x4d,0x50,0x5f,0x60,0xd9,
             0xeb,0xec,0xed,0xee,0x102,0x16,0x17,0x18,0x1a,0x1c,0x1d,0x1f,0x20,0x21,0x22,0x29,
             0x3000,0x3002,0x3010,0x3011,0x3027,0x3060,0x3062,0x3fc2,0x3fc3,0x3fc6,0x3fc7,
             0x3fe0,0x3fe1,0x3ff8,0x3ff9)}
        ram[0xd9]%=4
        case=Case(0xae85,ram,2)
        yield case
        if i%32==0:
            stock(case)
            for fail in range(1,memory.count+1): yield replace(case,fail=fail)
def main(binary):
    with tempfile.TemporaryDirectory() as temp:
        path=Path(temp)/'bmhm.bin'
        path.write_bytes(IMAGE)
        compare(binary,str(path),stock,cases(),'joined AE85 prefix and 7100 prelude')
    print('Limits: stops at AE9D before resident service tail and at 711C before resident boot components.')
if __name__=='__main__': main(sys.argv[1])
