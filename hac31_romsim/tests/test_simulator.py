from __future__ import annotations

from pathlib import Path
from math import ceil
import tempfile
import unittest

from romsim.simulator import Simulator


ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "romsim" / "profiles" / "gm_16197427_31.json"


def synthetic_hac_image() -> bytes:
    image = bytearray(0x10000)
    # Reset stub: BSET $00,#$80 ; JMP $7100
    image[0xFC29:0xFC2F] = bytes([0x14, 0x00, 0x80, 0x7E, 0x71, 0x00])
    # Core of contract-proven BMHM startup through OPTION write.
    image[0x7100:0x7113] = bytes([
        0x8E, 0x03, 0xFF,       # LDS #$03FF
        0xCE, 0x10, 0x00,       # LDX #$1000
        0x86, 0x03,             # LDAA #$03
        0xA7, 0x3D,             # STAA $3D,X (INIT)
        0xCE, 0x30, 0x00,       # LDX #$3000
        0x86, 0xB8,             # LDAA #$B8
        0xA7, 0x39,             # STAA $39,X (OPTION)
        0x20, 0xFE,             # BRA self
    ])
    image[0xFFFE:0x10000] = bytes([0xFC, 0x29])
    return bytes(image)


class SimulatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.sim = Simulator.from_profile_file(PROFILE)
        handle = tempfile.NamedTemporaryFile(suffix=".bin", delete=False)
        handle.write(synthetic_hac_image())
        handle.close()
        self.bin_path = Path(handle.name)
        self.sim.load_bin(self.bin_path)
        self.sim.reset()

    def tearDown(self) -> None:
        self.bin_path.unlink(missing_ok=True)

    def test_reset_and_init_relocation(self) -> None:
        self.assertEqual(self.sim.cpu.s.pc, 0xFC29)
        for _ in range(9):
            self.sim.step_instruction()
        self.assertEqual(self.sim.memory.reg_base, 0x3000)
        self.assertEqual(self.sim.cpu.s.sp, 0x03FF)
        self.assertEqual(self.sim.memory.internal_regs[0x39], 0xB8)

    def test_rom_is_read_only_except_deliberate_patch(self) -> None:
        original = self.sim.memory.mem[0x7100]
        self.sim.poke(0x7100, 0x01)
        self.assertEqual(self.sim.memory.mem[0x7100], original)
        self.sim.poke(0x7100, 0x01, allow_rom=True)
        self.assertEqual(self.sim.memory.mem[0x7100], 0x01)

    def test_adc_is_raw_and_explicit(self) -> None:
        self.sim.memory.debug_write8(0x103D, 0x03)
        self.sim.set_input("adc.7", 200)
        self.sim.memory.write8(0x3030, 0x07)
        self.sim.memory.tick(32)
        self.assertEqual(self.sim.memory.read8(0x3031), 200)
        self.assertTrue(self.sim.memory.read8(0x3030) & 0x80)

    def test_reference_period_contract_model(self) -> None:
        self.sim.set_input("rpm", 1000)
        interval = ceil(self.sim.profile.e_clock_hz * 60 / (4 * 1000))
        self.sim.memory.tick(interval)
        self.assertEqual(self.sim.memory.read16(0x3FC0), 983)

    def test_output_handoff_is_named_and_traced(self) -> None:
        self.sim.memory.context_pc = 0x8426
        self.sim.memory.write16(0x3FCE, 0x1234)
        row = self.sim.trace.outputs[-1]
        self.assertEqual(row.address, 0x3FCE)
        self.assertEqual(row.value, 0x1234)
        self.assertIn("pulse-width", row.name)


if __name__ == "__main__":
    unittest.main()
