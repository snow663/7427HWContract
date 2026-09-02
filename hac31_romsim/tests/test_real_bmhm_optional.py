from __future__ import annotations

import hashlib
import os
from pathlib import Path
import unittest

from romsim.simulator import Simulator, StopReason
from test_simulator import PROFILE


EXPECTED_SHA = "6188975246cf0042979f3a1694e3d43a2985a1452e7547a3b9e8a66d10e65004"


@unittest.skipUnless(os.environ.get("HAC31_BMHM_BIN"), "set HAC31_BMHM_BIN for real-ROM integration proof")
class RealBMHMTests(unittest.TestCase):
    def setUp(self) -> None:
        self.path = Path(os.environ["HAC31_BMHM_BIN"])
        self.assertEqual(hashlib.sha256(self.path.read_bytes()).hexdigest(), EXPECTED_SHA)
        self.sim = Simulator.from_profile_file(PROFILE)
        self.sim.load_bin(self.path)
        self.sim.reset()

    def test_contract_boot_sequence(self) -> None:
        self.sim.breakpoints.add(0x7150)
        result = self.sim.run(max_instructions=1000)
        self.assertEqual(result.reason, StopReason.BREAKPOINT)
        self.assertEqual(self.sim.memory.reg_base, 0x3000)
        self.assertEqual(self.sim.memory.debug_read8(0x306E), 0x7F)
        self.assertEqual(self.sim.memory.debug_read8(0x306F), 0xFF)
        self.assertEqual(self.sim.memory.debug_read8(0x3FFC), 0xB9)
        self.assertEqual(self.sim.memory.debug_read8(0x3FFD), 0x3A)

    def test_100k_instruction_path_has_no_opcode_trap(self) -> None:
        result = self.sim.run(max_instructions=100_000)
        self.assertNotEqual(result.reason, StopReason.UNKNOWN_OPCODE, result.detail)
        self.assertEqual(result.instructions, 100_000)


if __name__ == "__main__":
    unittest.main()

