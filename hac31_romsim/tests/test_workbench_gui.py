from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from romsim.gui import APP_TITLE, ROMSimulatorGUI
from romsim.simulator import Simulator
from romsim.workbench import SimulatorWorkbench, parse_number
from test_simulator import PROFILE, synthetic_hac_image


class WorkbenchGUITests(unittest.TestCase):
    def setUp(self) -> None:
        handle = tempfile.NamedTemporaryFile(suffix=".bin", delete=False)
        handle.write(synthetic_hac_image())
        handle.close()
        self.bin_path = Path(handle.name)
        self.workbench = SimulatorWorkbench(Simulator.from_profile_file(PROFILE))
        self.workbench.load_bin(self.bin_path)

    def tearDown(self) -> None:
        self.bin_path.unlink(missing_ok=True)

    def test_gui_module_imports_without_opening_a_window(self) -> None:
        self.assertEqual(APP_TITLE, "7427 $31 ROM Simulator")
        self.assertTrue(callable(ROMSimulatorGUI))

    def test_pcm_number_notation_and_operator_controls(self) -> None:
        self.assertEqual(parse_number("$3FCE"), 0x3FCE)
        self.assertEqual(parse_number("0x7150"), 0x7150)
        self.workbench.apply_inputs({"rpm": "800", "adc.7": 192, "port_c": 0x55})
        self.assertEqual(self.workbench.sim.inputs.rpm, 800.0)
        self.assertEqual(self.workbench.sim.inputs.adc[7], 192)
        self.assertEqual(self.workbench.sim.inputs.port_c, 0x55)
        self.assertTrue(self.workbench.toggle_breakpoint("$7150"))
        self.assertIn(0x7150, self.workbench.sim.breakpoints)
        self.assertFalse(self.workbench.toggle_breakpoint("$7150"))

    def test_load_step_memory_and_session_rom_patch(self) -> None:
        self.assertEqual(self.workbench.sim.cpu.s.pc, 0xFC29)
        before = self.workbench.sim.memory.cycle_counter
        self.workbench.step_instructions(1)
        self.assertGreater(self.workbench.sim.memory.cycle_counter, before)
        original = self.workbench.read_memory("$7100", 1)[0]
        with self.assertRaises(PermissionError):
            self.workbench.write_memory("$7100", "$01")
        self.assertEqual(self.workbench.read_memory("$7100", 1)[0], original)
        self.workbench.write_memory("$7100", "$01", patch_rom=True)
        self.assertEqual(self.workbench.read_memory("$7100", 1)[0], 0x01)


if __name__ == "__main__":
    unittest.main()
