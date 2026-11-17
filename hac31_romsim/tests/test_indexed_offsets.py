"""Unsigned HC11 indexed operands, distinct from signed relative branches.

Primary authority: NXP AN1283 section5.1.2:
https://www.nxp.com/docs/en/application-note/AN1283.pdf
These are CPU operand/address checks, not device or instruction timing proofs.
"""
import unittest
from romsim.hc11_core import HC11CPU,HC11Memory

class FlatMemory(HC11Memory):
    # The operand test isolates address arithmetic from mapped internal RAM/I/O.
    def read8(self,address):return self.mem[address&65535]
    def write8(self,address,value):self.mem[address&65535]=value&255
    def tick(self,cycles):self.cycle_counter+=cycles

class IndexedOffsetTests(unittest.TestCase):
    def test_every_byte_offset_for_x_y_and_address_wrap(self):
        # All arithmetic/load/store/bit/control families use the same helper.
        # Distinguish the signed-address alternative with poisoned bytes.
        for base in (0x0200,0x7f80,0xff80):
            memory=FlatMemory();cpu=HC11CPU(memory)
            for prefix in (b'',b'\x18'):
                for offset in range(256):
                    target=(base+offset)&65535
                    wrong=(base+offset-256)&65535
                    memory.mem[wrong]=0x55;memory.mem[target]=0xa5
                    memory.mem[0x4000:0x4000+len(prefix)+2]=prefix+bytes((0xa6,offset)) # LDAA
                    cpu.s.pc=0x4000;cpu.s.x=cpu.s.y=base;cpu.step()
                    self.assertEqual(cpu.s.a,0xa5,(base,prefix,offset))
                    memory.mem[0x4000:0x4000+len(prefix)+2]=prefix+bytes((0xa7,offset)) # STAA
                    cpu.s.pc=0x4000;cpu.s.a=0x3c;cpu.step()
                    self.assertEqual(memory.mem[target],0x3c,(base,prefix,offset))

    def test_word_bit_and_control_operands_use_unsigned_offsets(self):
        memory=FlatMemory();cpu=HC11CPU(memory)
        for prefix in (b'',b'\x18'):
            for offset in (0,1,127,128,199,255):
                base=0xff80;target=(base+offset)&65535
                memory.mem[target]=0x12;memory.mem[(target+1)&65535]=0x34
                memory.mem[0x4000:0x4000+len(prefix)+2]=prefix+bytes((0xec,offset)) # LDD
                cpu.s.pc=0x4000;cpu.s.x=cpu.s.y=base;cpu.step()
                self.assertEqual(cpu.s.d,0x1234)
                memory.mem[0x4000:0x4000+len(prefix)+3]=prefix+bytes((0x1c,offset,0x80)) # BSET
                cpu.s.pc=0x4000;cpu.step();self.assertEqual(memory.mem[target],0x92)
                memory.mem[0x4000:0x4000+len(prefix)+2]=prefix+bytes((0x6e,offset)) # JMP
                cpu.s.pc=0x4000;cpu.step();self.assertEqual(cpu.s.pc,target)

    def test_relative_branch_still_sign_extends(self):
        memory=FlatMemory();cpu=HC11CPU(memory)
        for offset in range(256):
            memory.mem[0x4000:0x4002]=bytes((0x20,offset))
            cpu.s.pc=0x4000;cpu.step()
            self.assertEqual(cpu.s.pc,(0x4002+(offset if offset<128 else offset-256))&65535)

if __name__=='__main__':unittest.main()
