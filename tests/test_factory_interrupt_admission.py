"""Resident interrupt nesting, X snapshots and current-loop ordering in BMHM.

All selected handler instructions and resident callees execute. Arrival times,
ready/status bits and flat device samples are supplied inputs, not a model of
the actual timer/ADC/bus. The historical guarded replay retains its zero/full-mask
BRSET witness domain; separate CPU tests now verify all selected-bit patterns.
"""
from __future__ import annotations

import csv
import io
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from build_factory_scheduler import recorded_rom
from verify_factory_ownership import EVIDENCE
import verify_factory_interrupt_admission as proof
from test_factory_stack_and_shared_state import Replay


class FactoryInterruptAdmissionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = recorded_rom(json.loads(EVIDENCE.read_text()))
        cls.generated = proof.build(cls.rom)
        cls.handlers = {int(r['vector'], 16): r for r in csv.DictReader(io.StringIO(cls.generated[proof.FILES[0]]))}

    def fixture(self):
        return Replay(self.rom)

    def test_admission_evidence_covers_every_ordinary_vector_and_all_tap_sites(self):
        for name, content in self.generated.items():
            self.assertEqual((proof.OUT/name).read_text(), content, name)
        self.assertEqual(set(self.handlers), set(range(0xFFD6, 0xFFF4, 2)))
        meta = json.loads(self.generated[proof.FILES[2]])
        self.assertEqual(meta['ordinary_vector_count'], 15)
        self.assertEqual(len(meta['vectors_blocked_through_RTI']), 14)
        self.assertEqual(meta['ordinary_handler_that_opens_nesting'], ['793D'])
        self.assertEqual(meta['TAP_sites'], ['7D8C','92B3','92D3','9350','936A','9381','939B'])
        self.assertEqual(self.handlers[0xFFF2]['source_F1_layout'], 'IRQ_pin_REF')
        for vector, peak in [(0xFFF2,19),(0xFFD6,13),(0xFFE8,11),(0xFFE4,30)]:
            self.assertEqual(int(self.handlers[vector]['frame_plus_resident_bytes']), peak)

    def test_complete_iac_helpers_preserve_both_x_states_through_all_six_snapshot_taps(self):
        observed = set()
        for entry in [0x92A4, 0x92F1]:
            for x in [0, 1]:
                for mask in [0, 1]:
                    for coolant in [0, 128, 255]:
                        f = self.fixture()
                        f.cpu.s.ccr = 0x80 | (x << 6) | (mask << 4)
                        f.memory.mem[6], f.memory.mem[8] = coolant, 255
                        f.call(entry)
                        self.assertEqual((f.cpu.s.ccr >> 6) & 1, x)
                        self.assertEqual((f.cpu.s.ccr >> 4) & 1, mask)
                        observed |= {pc for pc in f.trace if self.rom.read(pc, 1) == b'\x06'}
        self.assertEqual(observed, {0x92B3,0x92D3,0x9350,0x936A,0x9381,0x939B})

    def test_stock_pre_stop_sequence_requests_x_set_and_leaves_i_set(self):
        for incoming_i in [0, 1]:
            f = self.fixture()
            f.cpu.s.ccr = 0xC0 | (incoming_i << 4)
            f.run(0x7D86, 0x7D8D)
            self.assertEqual(f.cpu.s.ccr, 0x50)
            self.assertEqual(f.memory.mem[0x3039], 8)
            # Stop at the real STOP instruction. The generic CPU does not
            # implement STOP wakeup or hardware's write-one X semantics.
            self.assertEqual(self.rom.read(f.cpu.s.pc, 1), b'\xCF')

    def test_each_other_distinct_handler_rejects_timer_at_every_executed_boundary(self):
        entries = set()
        for vector, row in self.handlers.items():
            entry = int(row['entry'], 16)
            if vector == 0xFFE4 or entry in entries:
                continue
            entries.add(entry)
            f = self.fixture()
            f.memory.mem[0x302D], f.memory.mem[0x302E] = 0x40, 0xC0
            attempts = []
            def probe(machine):
                before = machine.state()
                self.assertFalse(machine.cpu.interrupt(0xFFE4))
                self.assertEqual(machine.state(), before)
                attempts.append(machine.cpu.s.pc)
            f.irq(vector, probe)
            self.assertTrue(attempts)
            self.assertEqual(f.cpu.s.sp, 0x03F4)
            self.assertLessEqual(0x03F4-f.low_sp, int(row['frame_plus_resident_bytes']))
        self.assertEqual(entries, {0xF7EA,0xFC44,0xFC3A,0x7875,0x78D9,0xFC2F,0xCE7C,0x74EA})

    def test_ref_and_sci_can_preempt_timer_but_block_a_further_timer_until_rti(self):
        for vector in [0xFFF2, 0xFFD6]:
            f = self.fixture()
            f.memory.mem[2], f.memory.mem[0xA7] = 2, 128
            f.word(0x3FC0, 0x0700)
            f.memory.mem[0x302D], f.memory.mem[0x302E] = 0x40, 0xC0
            injected, rejected = [], []
            def probe_leaf(machine):
                before = machine.state()
                self.assertFalse(machine.cpu.interrupt(0xFFE4))
                self.assertEqual(machine.state(), before)
                rejected.append(machine.cpu.s.pc)
            def inject(machine):
                if machine.cpu.s.pc == 0x7A44 and not injected:
                    injected.append(machine.cpu.s.sp)
                    machine.irq(vector, probe_leaf)
            f.irq(0xFFE4, inject)
            self.assertEqual(len(injected), 1)
            self.assertTrue(rejected)
            self.assertEqual(f.cpu.s.sp, 0x03F4)
            self.assertNotIn(0x7AA5, f.trace)

    def current_fixture(self):
        f = self.fixture()
        # The complete TOC3 busy path runs the current-control service before
        # setting pending and returning; no main task or callee is substituted.
        for address, value in [(0x4F,4),(0x4C,0x20),(0xA7,128),
                               (0x014D,20),(0xB5,40)]:
            f.memory.mem[address] = value
        f.word(0x0150, 0x0400)
        # Obtain the paired coefficients through the actual stock selector,
        # rather than inventing independently chosen RAM gain values.
        f.call(0xB2ED)
        self.assertEqual(tuple(f.memory.mem[0x0153:0x0155]), (64,35))
        return f

    def issued(self, f):
        writes = [(pc, value) for pc, address, value, width in f.memory.events if address == 0x3068]
        self.assertTrue(all(pc == 0x7BA3 for pc, value in writes))
        return [value for pc, value in writes]

    def nested_current(self, boundary):
        f = self.current_fixture()
        injected = []
        def inject(machine):
            if machine.cpu.s.pc == boundary and not injected:
                injected.append(machine.cpu.s.sp)
                machine.irq(0xFFE4)
        f.irq(0xFFE4, inject)
        self.assertEqual(len(injected), 1)
        self.assertEqual(f.cpu.s.sp, 0x03F4)
        self.assertEqual(f.memory.mem[0x3A] & 0x28, 0x20)  # pending, no stack recovery
        self.assertEqual(f.memory.mem[0x4F] & 4, 4)
        self.assertEqual(f.memory.mem[2], 0)  # Neither busy arrival advances main phase.
        self.assertNotIn(0x7AA5, f.trace)
        self.assertFalse(any(0x1800 <= pc < 0x1818 for pc in f.trace))
        return f

    def test_busy_timer_reentry_can_lose_an_accumulator_update_after_its_old_value_was_read(self):
        baseline = self.current_fixture()
        baseline.irq(0xFFE4)
        baseline.irq(0xFFE4)
        self.assertEqual((baseline.readword(0x150), baseline.memory.mem[0x14C]), (1489,106))
        self.assertEqual(self.issued(baseline), [0x0660,0x066A])
        before_load = self.nested_current(0x7C7A)
        self.assertEqual(before_load.readword(0x150), 1489)
        self.assertEqual(self.issued(before_load), [0x0654,0x066A])
        for boundary in [0x7C7D, 0x7C96]:
            f = self.nested_current(boundary)
            self.assertEqual((f.readword(0x150), f.memory.mem[0x14C]), (1344,96))
            self.assertEqual(self.issued(f), [0x0654,0x0660])
            self.assertEqual(f.memory.mem[0x14F], 20)

    def test_reentry_after_accumulator_store_can_preserve_state_but_publish_an_older_command(self):
        for boundary in [0x7C99, 0x7CA5]:
            f = self.nested_current(boundary)
            self.assertEqual(f.readword(0x150), 1489)
            self.assertEqual(f.memory.mem[0x14C], 96)
            self.assertEqual(self.issued(f), [0x066A,0x0660])
            self.assertEqual(f.memory.mem[0x14F], 20)


if __name__ == '__main__':
    unittest.main()
