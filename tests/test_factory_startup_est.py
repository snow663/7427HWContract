"""Cross-routine factory REF/startup/EST checks using the unchanged BMHM bytes.

The peripheral fixture provides stationary coherent words, not an ASIC model.
Actual REF IRQ entry/RTI and the full A4EC..ACA6 calculation are executed.
These are bounded schedules and chosen inputs, not all-interleaving proofs.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from build_factory_scheduler import recorded_rom
from factory_integer_replay import IntegerMemory
from factory_scheduler_replay import HC11CPU
from verify_factory_ownership import EVIDENCE
from verify_factory_rom_structure import EXPECTED_SHA256


class Fixture:
    def __init__(self, rom):
        self.memory = IntegerMemory(rom)
        self.cpu = HC11CPU(self.memory)
        self.cpu.s.sp = 0x03F4
        self.cpu.s.ccr = 0xC0
        self.trace = []

    def word(self, address, value):
        self.memory.mem[address:address+2] = (value & 65535).to_bytes(2, 'big')

    def readword(self, address):
        return int.from_bytes(self.memory.mem[address:address+2], 'big')

    def step(self):
        self.trace.append(self.cpu.s.pc)
        self.memory.pc = self.cpu.s.pc
        self.cpu.step()

    def run(self, start, stop, budget=20000):
        self.cpu.s.pc = start
        for _ in range(budget):
            if self.cpu.s.pc == stop:
                return
            if self.cpu.s.pc in {0xA5D7, 0xFC04, 0xFC07}:
                raise AssertionError(f'Unexpected reset/trap boundary {self.cpu.s.pc:04X}')
            self.step()
        raise AssertionError(f'Execution budget at {self.cpu.s.pc:04X}')

    def ref_irq(self):
        before = (self.cpu.s.pc, self.cpu.s.sp, self.cpu.s.a, self.cpu.s.b,
                  self.cpu.s.x, self.cpu.s.y, self.cpu.s.ccr)
        assert self.cpu.interrupt(0xFFF2), 'REF IRQ masked at selected fixture boundary'
        assert self.cpu.s.pc == 0x74EA
        self.run(self.cpu.s.pc, before[0])
        after = (self.cpu.s.pc, self.cpu.s.sp, self.cpu.s.a, self.cpu.s.b,
                 self.cpu.s.x, self.cpu.s.y, self.cpu.s.ccr)
        assert after == before

    def call(self, entry):
        self.cpu._push16(0x7000)
        self.run(entry, 0x7000)


class FactoryStartupESTTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        evidence = json.loads(EVIDENCE.read_text())
        cls.rom = recorded_rom(evidence)
        # This reconstructs the FILE identity only; the fixture initializes
        # runtime low memory separately and never uses file padding as RAM.
        file_image = bytes([255])*0x4000 + cls.rom.read(0x4000, 0xC000)
        assert sha256(file_image).hexdigest() == EXPECTED_SHA256

    def fixture(self):
        return Fixture(self.rom)

    def monitor(self, f, sample, fresh=True):
        f.word(0x3FCA, sample)
        if fresh:
            f.memory.mem[0x50] |= 4
        f.call(0xABCB)

    def test_boot_unconditionally_clears_startup_flags_and_seeds_monitor_baseline(self):
        f = self.fixture()
        for a in [0x44, 0x4B, 0x4F, 0x50, 0x51, 0x0202, 0x0210, 0x0211, 0x022C]:
            f.memory.mem[a] = 255
        f.run(0x7164, 0x717F)
        for a in [0x44, 0x4B, 0x4F, 0x50, 0x51, 0x0202, 0x0210, 0x0211, 0x022C]:
            self.assertEqual(f.memory.mem[a], 0)
        f.word(0x3FCA, 0x1234)
        f.run(0x741F, 0x7425)
        self.assertEqual(f.readword(0x0205), 0x1234)

    def test_full_reference_irq_and_stock_calculation_connect_four_startup_admissions(self):
        f = self.fixture()
        self.assertEqual(self.rom.word(0x4133), 0x0888)
        self.assertEqual(self.rom.word(0x4135), 0x0CCC)
        self.assertEqual(self.rom.read(0x4142, 2), bytes([2, 2]))
        f.word(0x3FC0, 0x0700)
        f.word(0x3FCA, 0x1234)
        f.word(0x0205, 0x1234)
        f.word(0x3FEC, 0xBEEF)
        expected = [(0x08, 0x00, 0x00, 0, 0, 0),
                    (0x08, 0x00, 0x00, 1, 1, 0),
                    (0x48, 0x90, 0x00, 0, 0, 0),
                    (0x40, 0xD0, 0x10, 0, 0, 0xBEEF)]
        for row in expected:
            f.cpu.s.pc = 0x7000
            f.ref_irq()
            self.assertTrue(f.memory.mem[0x50] & 0x20)
            f.run(0xA4EC, 0xACA6)
            actual = tuple(f.memory.mem[a] for a in [0x44, 0x4F, 0x4B, 0x0210, 0x0211]) + (f.readword(0x3FE4),)
            self.assertEqual(actual, row)
            self.assertEqual(f.memory.mem[0x50] & 0x24, 0)
            self.assertEqual(f.cpu.s.sp, 0x03F4)
        self.assertEqual(sum(pc == 0xAC2E for pc in f.trace), 1)

    def test_fuel_and_spark_qualification_have_distinct_stock_period_thresholds(self):
        f = self.fixture()
        # 0900 is below the fuel threshold but above the spark threshold.
        # Start after the explicit first-reference latch has been established.
        f.memory.mem[0x44] = 8
        f.word(0x3FC0, 0x0900)
        for _ in range(2):
            f.memory.mem[0x50] |= 0x20
            f.run(0xA4EC, 0xACA6)
        self.assertEqual(f.memory.mem[0x4F] & 0x90, 0x10)
        self.assertEqual(f.memory.mem[0x0210], 0)
        self.assertNotIn(0xABCB, f.trace)

    def test_stock_initial_monitor_requires_unchanged_samples_and_two_goods(self):
        self.assertEqual(self.rom.read(0x4E71, 1), b'\x00')
        self.assertTrue(self.rom.read(0x5B03, 1)[0] & 0x20)
        f = self.fixture()
        f.memory.mem[0x44] = 8
        f.word(0x0205, 0xFFFF)
        f.word(0x3FEC, 0xCAFE)
        self.monitor(f, 0)  # Wrapped delta is 1: bad, despite high byte zero.
        self.assertEqual(f.memory.mem[0x022C], 1)
        self.assertEqual(f.memory.mem[0x44] & 0x40, 0)
        self.monitor(f, 0)
        self.assertEqual(f.memory.mem[0x44] & 0x40, 0x40)
        self.assertEqual(f.memory.mem[0x4F] & 0x40, 0)
        self.monitor(f, 0)
        self.assertEqual(f.memory.mem[0x4F] & 0x40, 0x40)
        self.assertEqual(f.memory.mem[0x44] & 8, 0)
        self.assertEqual(f.memory.mem[0x022C], 0)
        self.assertEqual(f.readword(0x3FE4), 0xCAFE)

    def test_bad_monitor_sample_clears_first_good_but_good_does_not_clear_bad_count(self):
        f = self.fixture()
        f.memory.mem[0x44] = 8
        self.monitor(f, 0)
        self.monitor(f, 1)
        self.assertEqual(f.memory.mem[0x44] & 0x40, 0)
        self.assertEqual(f.memory.mem[0x022C], 1)
        self.monitor(f, 1)
        self.assertEqual(f.memory.mem[0x022C], 1)
        self.assertEqual(f.memory.mem[0x4F] & 0x40, 0)
        self.monitor(f, 1)
        self.assertEqual(f.memory.mem[0x022C], 0)
        self.assertEqual(f.memory.mem[0x4F] & 0x40, 0x40)

    def test_post_qualification_monitor_reuses_baseline_and_counter_for_unchanged_fault(self):
        self.assertEqual(self.rom.read(0x4E70, 4), bytes([4, 0, 4, 4]))
        f = self.fixture()
        f.memory.mem[0x4F] = 0x40
        f.memory.mem[0x61] = 5
        for count in range(1, 6):
            f.run(0xE00D, 0xE041)
            self.assertEqual(f.memory.mem[0x022C], count)
            self.assertEqual(f.memory.mem[4] & 0x80, 0)
        f.run(0xE00D, 0xE041)
        self.assertEqual(f.memory.mem[4] & 0x80, 0x80)
        self.assertEqual(f.memory.mem[0x022C], 5)
        f.call(0xABCB)
        self.assertEqual(f.memory.mem[0x19] & 0x20, 0x20)
        self.assertEqual(f.memory.mem[0x4B] & 0x10, 0)

    def test_reference_before_and_after_latch_clear_gives_distinct_pending_state(self):
        for boundary, pending in [(0xA4F0, 0), (0xA4F3, 0x20)]:
            f = self.fixture()
            f.memory.mem[0x50] = 0x20
            f.run(0xA4EC, boundary)
            f.ref_irq()
            f.run(boundary, 0xA4F6)
            self.assertEqual(f.memory.mem[0x50] & 0x20, pending)
            self.assertEqual(f.memory.mem[0x50] & 4, 4)
        # An IRQ after the no-pending test waits for a subsequent admission.
        f = self.fixture()
        f.run(0xA4EC, 0xA53D)
        f.ref_irq()
        f.run(0xA53D, 0xACA6)
        self.assertEqual(f.memory.mem[0x50] & 0x24, 0x20)

    def test_ignition_off_blocks_reference_pending_latch(self):
        f = self.fixture()
        f.cpu.s.pc = 0x7000
        f.memory.mem[0x44] = 0x10
        f.ref_irq()
        self.assertEqual(f.memory.mem[0x50] & 0x20, 0)
        f.run(0xA4EC, 0xACA6)
        self.assertEqual(f.memory.mem[0x44] & 8, 0)

    def test_software_ignition_cycle_preserves_est_qualification_and_partial_history(self):
        f = self.fixture()
        f.memory.mem[0x44] = 0xD8  # off, first-ref, first-good and lock bits
        f.memory.mem[0x4F] = 0xD0
        f.memory.mem[0x0210] = 1
        f.memory.mem[0x0211] = 1
        f.memory.mem[0x022C] = 3
        f.word(0x027E, 8)
        f.run(0x7D4B, 0x7D81)
        self.assertEqual(f.memory.mem[0x4F] & 0xD0, 0x40)
        self.assertEqual(f.memory.mem[0x44] & 0xC0, 0xC0)
        self.assertEqual(tuple(f.memory.mem[a] for a in [0x0210, 0x0211, 0x022C]), (1, 1, 3))
        f.memory.mem[0x44] &= ~0x10
        f.run(0x7D90, 0x7DB1)
        self.assertEqual(f.memory.mem[0x44] & 8, 0)
        # Retained qualification bypasses the old lock and delta test when
        # a later first-reference latch and fresh conversion are present.
        f.memory.mem[0x44] |= 8
        f.word(0x3FEC, 0xCAFE)
        self.monitor(f, 0x4321)
        self.assertEqual(f.memory.mem[0x19] & 0x20, 0)
        self.assertEqual(f.readword(0x3FE4), 0xCAFE)
        self.assertEqual(f.memory.mem[0x022C], 3)
        self.assertEqual(f.readword(0x0205), 0)

    def test_missing_reference_reaches_swi_trap_after_23_running_admissions(self):
        f = self.fixture()
        f.memory.mem[0x4F] = 0xD0
        f.memory.mem[0x44] = 8
        f.word(0x3FC0, 0x0700)
        for count in range(1, 24):
            f.run(0xA4EC, 0xACA6)
            self.assertEqual(f.memory.mem[0x0202], count)
        f.run(0xA4EC, 0xA5D7)
        self.assertEqual(f.memory.mem[0x4F] & 0xD0, 0x40)
        self.assertEqual(f.memory.mem[0x44] & 8, 0)
        self.assertEqual(f.readword(0x005F), 0xFFFF)
        self.assertEqual(f.memory.mem[0x3060] & 0x10, 0)
        # The actual stock SWI vector traps; hardware watchdog recovery is
        # separate from an immediate software jump back to the reset entry.
        f.step()
        self.assertEqual(f.cpu.s.pc, 0xFC04)
        f.step()
        self.assertEqual(f.memory.mem[0] & 8, 8)
        self.assertEqual(f.cpu.s.pc, 0xFC07)
        f.step()
        self.assertEqual(f.cpu.s.pc, 0xFC07)

    def test_board_flush_publishes_shadow_bit_with_no_invented_wire_identity(self):
        for request in [0, 0x10]:
            f = self.fixture()
            f.memory.mem[0x3060] = 0xFF
            f.memory.mem[0x4B] = request
            f.call(0xF3EE)
            self.assertEqual(f.memory.mem[0x3060], request)
            self.assertEqual(f.memory.mem[0x4B], 0x6F + request)


if __name__ == '__main__':
    unittest.main()
