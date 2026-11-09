import unittest
from studio.decoder import decode
from studio.autoreason import analyze, register_dataflow, get

class Image:
    def __init__(self, raw, start=0x8000):
        self.raw = raw
        self.start = start
    def contains(self, addr, n=1):
        return self.start <= addr and addr+n <= self.start+len(self.raw)
    def read(self, addr, n=1):
        return self.raw[addr-self.start:addr-self.start+n] if self.contains(addr,n) else b''

class Analyzer:
    def __init__(self, raw, start=0x8000, pcs=None):
        self.img=Image(raw,start)
        self.instructions={}
        pcs = pcs or []
        for pc in pcs: self.instructions[pc]=decode(self.img.read,pc)
        self.entries={pcs[0]}
        self.routines={pcs[0]: {'pcs':set(pcs),'edges':[]}}
    def graph_edges(self, ins):
        if ins.op=='RTS':return []
        if ins.op=='BRA':return [(ins.target,'jump')]
        if ins.op=='BEQ':return [(ins.target,'taken'),(ins.next_pc,'not_taken')]
        return [(ins.next_pc,'fallthrough')]

class AutoReasonTests(unittest.TestCase):
    def test_derived_table_pointer_and_rom_reference(self):
        # LDX #$8030; LDAB #2; ABX; LDAA 0,X; RTS, table byte at 8032
        raw=bytearray([0xff]*0x80)
        raw[:9]=bytes.fromhex('CE 80 30 C6 02 3A A6 00 39')
        raw[0x32]=0x7e
        a=Analyzer(bytes(raw),pcs=[0x8000,0x8003,0x8005,0x8006,0x8008])
        r=analyze(a)
        self.assertEqual(r['instructions']['8006']['before']['X'],'8032')
        self.assertEqual(r['instructions']['8006']['after']['A'],'007E')
        self.assertIn('8032',[x['address'] for x in r['memory_references']])
        self.assertIn('rom_data_reference',[x['kind'] for x in r['suggestions']])
    def test_branch_join_kills_conflicting_constant(self):
        # LDAA #1; BEQ 8008; LDAA #2; BRA 800A; LDAA #3; STAA $35; RTS
        raw=bytearray([0xff]*0x50)
        raw[:13]=bytes.fromhex('86 01 27 04 86 02 20 02 86 03 97 35 39')
        a=Analyzer(bytes(raw),pcs=[0x8000,0x8002,0x8004,0x8006,0x8008,0x800A,0x800C])
        r=analyze(a)
        self.assertEqual(r['instructions']['800A']['before']['A'],'?')
    def test_stack_and_sci_candidate(self):
        # LDS #3FF; PSHA; PULA; LDAA $302E; STAA $302F; RTS
        raw=bytearray([0xff]*0x50)
        raw[:14]=bytes.fromhex('8E 03 FF 36 32 B6 30 2E B7 30 2F 39')
        a=Analyzer(bytes(raw),pcs=[0x8000,0x8003,0x8004,0x8005,0x8008,0x800B])
        r=analyze(a)
        self.assertEqual(r['instructions']['8003']['after']['SP'],'03FE')
        self.assertEqual(r['instructions']['8004']['after']['SP'],'03FF')
        self.assertEqual(r['likely_sci_blocks'][0]['base'],'3000')
    def test_ram_not_read_as_rom_in_full_dump(self):
        raw=bytearray([0xff]*65536)
        raw[0x8000:0x8004]=bytes.fromhex('96 20 39 01')
        raw[0x20]=0x42
        a=Analyzer(bytes(raw),start=0,pcs=[0x8000,0x8002])
        r=analyze(a)
        self.assertEqual(r['instructions']['8000']['after']['A'],'?')
        self.assertEqual(r['memory_references'][0]['category'],'memory_access')

if __name__=='__main__':unittest.main()
