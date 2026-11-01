"""HC11 bit branches: all selected set/clear, including an empty mask.

Authority: NXP M68HC11ERG rev2.1 p12, Bit Manipulation Branches:
https://www.nxp.com/docs/en/reference-manual/M68HC11ERG.pdf
This is an instruction-semantic check, not a bus/cycle timing proof.
"""
import unittest
from romsim.hc11_core import HC11CPU, HC11Memory


class BitBranchTests(unittest.TestCase):
    def test_all_byte_mask_pairs_in_direct_and_both_indexed_forms(self):
        memory=HC11Memory();cpu=HC11CPU(memory)
        cpu.s.x=cpu.s.y=0x0200
        for prefix,address,offset in [(b'',0x20,0x20),(b'',0x0234,0x34),(b'\x18',0x0234,0x34)]:
            indexed=address==0x0234
            for clear in (False,True):
                opcode=(0x1f if clear else 0x1e) if indexed else (0x13 if clear else 0x12)
                start=0x4000;size=len(prefix)+4
                memory.mem[start:start+size]=prefix+bytes([opcode,offset,0,3])
                for mask in range(256):
                    memory.mem[start+len(prefix)+2]=mask
                    selected=[1<<bit for bit in range(8) if mask&(1<<bit)]
                    for value in range(256):
                        memory.write8(address,value);cpu.s.pc=start;cpu.s.ccr=0xd5
                        expected=not any(value&bit for bit in selected) if clear else all(value&bit for bit in selected)
                        cpu.step()
                        self.assertEqual((cpu.s.pc,cpu.s.ccr,memory.read8(address)),
                                         (start+size+(3 if expected else 0),0xd5,value),
                                         (prefix,indexed,clear,mask,value))


if __name__=='__main__':unittest.main()
