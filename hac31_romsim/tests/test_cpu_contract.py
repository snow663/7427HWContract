from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from romsim.simulator import Simulator
from romsim.hc11_core import HC11CPU, HC11Memory
from test_simulator import PROFILE, synthetic_hac_image


class CPUContractTests(unittest.TestCase):
    def test_word_stores_do_not_read_their_destination(self) -> None:
        # NXP M68HC11ERG instruction table: STX/STY/STS/STD store a register
        # pair, not a read/modify/write result. Include all indexed prefixes.
        cases = [
            ("DF 80", "x", 0x0080), ("EF 06", "x", 0x3066),
            ("CD EF 06", "x", 0x3166), ("FF 30 68", "x", 0x3068),
            ("18 DF 80", "y", 0x0080), ("1A EF 06", "y", 0x3066),
            ("18 EF 06", "y", 0x3166), ("18 FF 30 68", "y", 0x3068),
            ("9F 80", "sp", 0x0080), ("AF 06", "sp", 0x3066),
            ("18 AF 06", "sp", 0x3166), ("BF 30 68", "sp", 0x3068),
            ("DD 80", "d", 0x0080), ("ED 06", "d", 0x3066),
            ("18 ED 06", "d", 0x3166), ("FD 30 68", "d", 0x3068),
        ]
        for encoding, register, address in cases:
            with self.subTest(encoding=encoding):
                class StoreMemory(HC11Memory):
                    def __init__(self):
                        super().__init__()
                        self.stores = []

                    def read8(self, target):
                        if target in {address, address + 1}:
                            raise AssertionError("Store read its destination")
                        return super().read8(target)

                    def write8(self, target, value):
                        self.stores.append((target, value & 255))
                        super().write8(target, value)

                memory = StoreMemory()
                code = bytes.fromhex(encoding)
                memory.mem[0x7200:0x7200 + len(code)] = code
                cpu = HC11CPU(memory)
                cpu.s.pc, cpu.s.x, cpu.s.y, cpu.s.sp, cpu.s.d = 0x7200, 0x3060, 0x3160, 0x1234, 0x89AB
                cpu.s.ccr = 0xC1
                value = getattr(cpu.s, register)
                cpu.step()
                self.assertEqual(memory.stores, [(address, value >> 8), (address + 1, value & 255)])
                self.assertEqual(cpu.s.pc, 0x7200 + len(code))
                self.assertEqual(cpu.s.ccr & 3, 1)  # Carry retained, overflow clear.

    def make_sim(self, image: bytes) -> tuple[Simulator, Path]:
        handle = tempfile.NamedTemporaryFile(suffix=".bin", delete=False)
        handle.write(image)
        handle.close()
        sim = Simulator.from_profile_file(PROFILE)
        sim.load_bin(handle.name)
        sim.reset()
        return sim, Path(handle.name)

    def test_indexed_bit_opcode_used_by_bmhm(self) -> None:
        image = bytearray(synthetic_hac_image())
        image[0x7200:0x7208] = bytes([
            0xCE, 0x01, 0x00,       # LDX #$0100
            0x1C, 0x00, 0x20,       # BSET 0,X,#$20
            0x20, 0xFE,
        ])
        sim, path = self.make_sim(bytes(image))
        try:
            sim.cpu.s.pc = 0x7200
            sim.step_instruction()
            sim.step_instruction()
            self.assertEqual(sim.memory.internal_ram[0x100], 0x20)
        finally:
            path.unlink(missing_ok=True)

    def test_interrupt_stack_round_trip(self) -> None:
        image = bytearray(synthetic_hac_image())
        image[0x7200] = 0x3B  # RTI
        image[0xFFF2:0xFFF4] = bytes([0x72, 0x00])
        sim, path = self.make_sim(bytes(image))
        try:
            sim.cpu.s.sp = 0x03FF
            sim.cpu.s.pc = 0x7111
            sim.cpu.s.a = 0x12
            sim.cpu.s.b = 0x34
            before = (sim.cpu.s.pc, sim.cpu.s.sp, sim.cpu.s.a, sim.cpu.s.b)
            self.assertTrue(sim.cpu.interrupt(0xFFF2, maskable=False))
            self.assertEqual(sim.cpu.s.pc, 0x7200)
            sim.step_instruction()
            after = (sim.cpu.s.pc, sim.cpu.s.sp, sim.cpu.s.a, sim.cpu.s.b)
            self.assertEqual(after, before)
        finally:
            path.unlink(missing_ok=True)

    def test_page3_y_register_operations_use_x_index(self) -> None:
        image = bytearray(synthetic_hac_image())
        image[0x7200:0x7209] = bytes.fromhex("1A EE 02 1A AC 04 1A EF 06")
        sim, path = self.make_sim(bytes(image))
        try:
            sim.cpu.s.pc, sim.cpu.s.x, sim.cpu.s.y = 0x7200, 0x0100, 0x0300
            sim.memory.write16(0x0102, 0x4567)
            sim.memory.write16(0x0104, 0x4567)
            sim.step_instruction()  # LDY 2,X
            self.assertEqual((sim.cpu.s.x, sim.cpu.s.y), (0x0100, 0x4567))
            sim.step_instruction()  # CPY 4,X
            self.assertTrue(sim.cpu.s.ccr & 4)
            sim.step_instruction()  # STY 6,X
            self.assertEqual(sim.memory.read16(0x0106), 0x4567)
        finally:
            path.unlink(missing_ok=True)

    def test_mul_carry_is_product_bit7_and_other_flags_are_unchanged(self) -> None:
        image = bytearray(synthetic_hac_image())
        image[0x7200] = 0x3D
        sim, path = self.make_sim(bytes(image))
        try:
            for a, b in [(1, 0x80), (0x80, 0x80), (0xFF, 0xFF), (0xFF, 0x80), (0, 0xFF)]:
                sim.cpu.s.pc, sim.cpu.s.a, sim.cpu.s.b, sim.cpu.s.ccr = 0x7200, a, b, 0xA4
                sim.step_instruction()
                product = a * b
                self.assertEqual(sim.cpu.s.d, product)
                self.assertEqual(sim.cpu.s.ccr, 0xA4 | (1 if product & 0x80 else 0))
        finally:
            path.unlink(missing_ok=True)

    def test_pulls_preserve_every_condition_code(self) -> None:
        image=bytearray(synthetic_hac_image())
        sim,path=self.make_sim(bytes(image))
        try:
            for code,register,value,width in [(b"\x32","a",0x00,8),(b"\x33","b",0x80,8),
                                               (b"\x38","x",0,16),(b"\x18\x38","y",0x8000,16)]:
                for ccr in [0,0xFF,0x55,0xAA]:
                    sim.memory.mem[0x7200:0x7200+len(code)]=code
                    sim.cpu.s.pc,sim.cpu.s.sp,sim.cpu.s.ccr=0x7200,0x03FF,ccr
                    (sim.cpu._push8 if width==8 else sim.cpu._push16)(value)
                    sim.step_instruction()
                    self.assertEqual(getattr(sim.cpu.s,register),value)
                    self.assertEqual((sim.cpu.s.sp,sim.cpu.s.ccr),(0x03FF,ccr))
        finally:path.unlink(missing_ok=True)

    def test_divide_flags_distinguish_overflow_zero_and_valid_fraction(self) -> None:
        image=bytearray(synthetic_hac_image())
        sim,path=self.make_sim(bytes(image))
        try:
            for opcode,numerator,divisor in [(2,0,7),(2,65535,128),(2,5,0),
                                             (3,0,7),(3,1,2),(3,2,2),(3,3,2),(3,5,0)]:
                sim.memory.mem[0x7200]=opcode
                sim.cpu.s.pc,sim.cpu.s.d,sim.cpu.s.x,sim.cpu.s.ccr=0x7200,numerator,divisor,0xFF
                sim.step_instruction()
                quotient=0xFFFF if divisor==0 or opcode==3 and numerator>=divisor else ((numerator<<16) if opcode==3 else numerator)//divisor
                expected=(0xFF & ~7)|int(divisor==0)|(int(opcode==3 and numerator>=divisor)<<1)|(int(quotient==0)<<2)
                self.assertEqual((sim.cpu.s.x,sim.cpu.s.ccr),(quotient,expected))
                if divisor and (opcode==2 or numerator<divisor):
                    self.assertEqual(sim.cpu.s.d,((numerator<<16) if opcode==3 else numerator)%divisor)
        finally:path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()

