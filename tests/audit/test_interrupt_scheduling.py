"""XIRQ must not be hidden behind a pending maskable IRQ in the coordinator."""
import os
from pathlib import Path
import sys
import unittest

ROOT = Path(os.environ.get("AUDIT_REPO", Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(ROOT / "hac31_romsim"))
from romsim.simulator import Simulator


class InterruptScheduling(unittest.TestCase):
    def simulator(self):
        sim = Simulator.from_profile_file(ROOT / "hac31_romsim/romsim/profiles/gm_16197427_31.json")
        sim.cpu.s.ccr = 0x10
        sim.cpu.s.sp = 0x01FF
        sim.memory.mem[0xFFE8:0xFFEA] = bytes.fromhex("7300")
        sim.memory.mem[0xFFF2:0xFFF6] = bytes.fromhex("71007200")
        return sim

    def test_xirq_precedes_queued_irq_even_when_i_is_clear(self):
        self.check_priority(0)

    def test_masked_head_irq_does_not_block_unmasked_xirq(self):
        self.check_priority(0x10)

    def check_priority(self, ccr):
        sim = self.simulator()
        sim.cpu.s.ccr = ccr  # X=0 in both cases; I varies.
        sim.request_interrupt("irq")
        sim.request_interrupt("xirq", maskable=False)
        self.assertGreater(sim._service_interrupt(), 0)
        self.assertEqual(sim.cpu.s.pc, 0x7200)
        self.assertEqual([item[0] for item in sim.pending_interrupts], [0xFFF2])

    def check_canceled_timer(self, offset, value):
        sim = self.simulator()
        sim.memory.timer.regs[0x22] = 0x80  # OC1 enabled
        sim.memory.timer.regs[0x23] = 0x80  # OC1 flag pending
        self.assertEqual(sim._service_interrupt(), 0)  # I masks recognition
        sim.memory.timer.write(offset, value)
        self.assertIsNone(sim.memory.timer.pending_vector())
        sim.cpu.s.ccr = 0
        self.assertEqual(sim._service_interrupt(), 0,
                         "cleared/disabled timer request must not survive as a queued IRQ")
        self.assertEqual(sim.cpu.s.pc, 0)

    def test_timer_flag_cleared_before_unmask_cancels_request(self):
        self.check_canceled_timer(0x23, 0x80)  # TFLG1 write-one-to-clear

    def test_timer_mask_disabled_before_unmask_cancels_request(self):
        self.check_canceled_timer(0x22, 0)  # TMSK1 disable

    def test_live_timer_request_is_serviced_after_unmask(self):
        sim = self.simulator()
        sim.memory.timer.regs[0x22] = sim.memory.timer.regs[0x23] = 0x80
        self.assertEqual(sim._service_interrupt(), 0)
        sim.cpu.s.ccr = 0
        self.assertGreater(sim._service_interrupt(), 0)
        self.assertEqual(sim.cpu.s.pc, 0x7300)

    def test_consumed_reference_edge_survives_masked_polling(self):
        sim = self.simulator()
        sim.memory.asic.ref_irq_pending = True
        self.assertEqual(sim._service_interrupt(), 0)
        self.assertEqual(sim._service_interrupt(), 0)
        sim.cpu.s.ccr = 0
        self.assertGreater(sim._service_interrupt(), 0)
        self.assertEqual(sim.cpu.s.pc, 0x7100)


if __name__ == "__main__":
    unittest.main()
