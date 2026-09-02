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


if __name__ == "__main__":
    unittest.main()

