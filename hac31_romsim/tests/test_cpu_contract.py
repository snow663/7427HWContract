from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from romsim.simulator import Simulator
from test_simulator import PROFILE, synthetic_hac_image


class CPUContractTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()

