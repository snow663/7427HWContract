"""Stack envelopes and complete-handler shared-output witnesses for stock BMHM.

No hardware-timing claim: ADC ready values and IRQ arrivals are fixture inputs.
The IAC/gear witness executes all resident callees of the selected TOC3 passes.
The historical all-or-none BRSET fixture domain remains explicit. The CPU's
all-selected branch semantics are now independently tested over all byte/mask
pairs; partial-mask IAC comparisons are supplied by the newer source suite.
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
from factory_integer_replay import IntegerMemory
from factory_rom_decode import decode
from factory_scheduler_replay import HC11CPU
from verify_factory_ownership import EVIDENCE
import verify_factory_stack_contracts as proof
from test_factory_interrupt_contracts import BoundaryReplay


class Memory(IntegerMemory):
    def __init__(self, rom):
        super().__init__(rom)
        self.adc_ready = True

    def read8(self, address):
        if address == 0x3030 and not self.adc_ready:
            return self.mem[address] & 0x7F
        return super().read8(address)


class Replay(BoundaryReplay):
    def __init__(self, rom):
        super().__init__(rom)
        self.rom = rom
        self.memory = Memory(rom)
        self.cpu = HC11CPU(self.memory)
        self.cpu.s.sp, self.cpu.s.pc, self.cpu.s.ccr = 0x03F4, 0x7000, 0xC0
        self.low_sp = self.cpu.s.sp

    def step(self):
        i = decode(self.rom.read, self.cpu.s.pc)
        if i.op == 'BRSET' and i.mask.bit_count() > 1:
            address = i.value
            if i.mode == 'indexed_x':
                address = (address+self.cpu.s.x) & 65535
            elif i.mode == 'indexed_y':
                address = (address+self.cpu.s.y) & 65535
            selected = self.memory.read8(address) & i.mask
            if selected not in {0, i.mask}:
                raise AssertionError(f'Partial BRSET outside bounded CPU proof at {i.pc:04X}')
        self.low_sp = min(self.low_sp, self.cpu.s.sp)
        super().step()
        self.low_sp = min(self.low_sp, self.cpu.s.sp)


class FactoryStackSharedStateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = recorded_rom(json.loads(EVIDENCE.read_text()))
        cls.generated = proof.build(cls.rom)
        cls.rows = {int(r['entry'], 16): r for r in csv.DictReader(io.StringIO(cls.generated[proof.FILES[0]]))}

    def fixture(self):
        return Replay(self.rom)

    def test_stack_artifacts_and_all_entry_balances_reproduce(self):
        for name, content in self.generated.items():
            self.assertEqual((proof.OUT/name).read_text(), content, name)
        self.assertEqual(len(self.rows), 253)
        for entry, row in self.rows.items():
            expected = '-2;0' if entry == 0xA407 else ('0' if row['pre_RTS_depths'] else '')
            self.assertEqual(row['pre_RTS_depths'], expected, f'{entry:04X}')
            self.assertIn(row['pre_RTI_depths'], ('', '0'))
        meta = json.loads(self.generated[proof.FILES[2]])
        self.assertEqual(meta['SP_assignment_sites'], ['7100', '7977', 'FA5B'])
        self.assertEqual(meta['nonlocal_call_sites'], ['93DE'])
        self.assertEqual(meta['reviewed_local_frame_restore']['bytes'], 6)

    def test_complete_iac_six_byte_frame_restores_sp_at_different_stack_locations(self):
        self.assertEqual(self.rows[0x99C5]['peak_bytes_below_entry_SP'], '14')
        for sp in [0x03D0, 0x03F4, 0x03FF]:
            f = self.fixture()
            f.cpu.s.sp = sp
            f.low_sp = sp
            f.cpu._push16(0x7000)
            entry_sp = f.cpu.s.sp
            f.run(0x99C5, 0x7000)
            self.assertIn(0x9C1D, f.trace)
            self.assertEqual(f.cpu.s.sp, sp)
            self.assertEqual(entry_sp-f.low_sp, 14)

    def test_nested_transmission_math_matches_its_fifteen_byte_envelope(self):
        f = self.fixture()
        f.cpu.s.y, f.cpu.s.b = 0xD69F, 0
        f.memory.mem[0x80] = f.memory.mem[0x81] = 1
        f.memory.mem[0xAB] = 128
        f.cpu._push16(0x7000)
        entry_sp = f.cpu.s.sp
        f.run(0xD840, 0x7000)
        self.assertIn(0xD88B, f.trace)
        self.assertIn(0xF55B, f.trace)
        self.assertEqual(entry_sp-f.low_sp, 15)
        self.assertEqual(self.rows[0xD840]['peak_bytes_below_entry_SP'], '15')
        self.assertEqual(f.cpu.s.sp, 0x03F4)

    def test_iac_service_escape_returns_to_controller_caller(self):
        for kind in ['reset', 'position', 'kicker']:
            f = self.fixture()
            f.memory.mem[0x3B] = 0x10
            f.memory.mem[7], f.memory.mem[8] = 9, 3
            if kind == 'reset':
                f.memory.mem[0x0391] = 0x20
            elif kind == 'position':
                f.memory.mem[0x0395], f.memory.mem[0x0396] = 1, 42
            else:
                f.memory.mem[0x038F], f.memory.mem[0x0390] = 0x40, 0x40
            f.call(0x93D0)
            self.assertIn(0x93DE, f.trace)
            self.assertNotIn(0x93E1, f.trace)
            self.assertEqual(f.cpu.s.sp, 0x03F4)
            if kind == 'reset':
                self.assertEqual((f.memory.mem[7], f.memory.mem[8]), (255, 0))
            elif kind == 'position':
                self.assertEqual(f.memory.mem[8], 42)
            else:
                self.assertEqual(f.memory.mem[0x37] & 4, 4)

    def test_iac_rpm_override_returns_to_local_controller_continuation(self):
        f = self.fixture()
        f.memory.mem[0x3B] = 0x10
        f.memory.mem[0x0395], f.memory.mem[0x0396] = 3, 42
        f.cpu._push16(0x7000)
        entry_sp = f.cpu.s.sp
        f.run(0x93D0, 0x93E1)
        self.assertEqual(f.cpu.s.sp, entry_sp)
        self.assertEqual(f.memory.mem[0x0857], 42)
        self.assertEqual(f.memory.mem[0x38] & 0x40, 0x40)

    def test_wai_prestacks_one_irq_frame_and_wake_does_not_push_a_second(self):
        f = self.fixture()
        f.cpu.s.sp, f.cpu.s.pc = 0x03FF, 0x74D0
        f.low_sp = 0x03FF
        f.memory.mem[0x4F] = 4  # Selected busy-return path.
        f.step()
        self.assertTrue(f.cpu.waiting)
        self.assertEqual(f.cpu.s.sp, 0x03F6)
        self.assertTrue(f.cpu.interrupt(0xFFE4))
        self.assertEqual(f.cpu.s.sp, 0x03F6)
        f.run(0x793D, 0x74D1)
        self.assertEqual(f.cpu.s.sp, 0x03FF)
        self.assertFalse(f.cpu.waiting)

    def test_entry_guard_acceptance_does_not_reserve_all_subsequent_call_bytes(self):
        f = self.fixture()
        f.cpu.s.sp = f.low_sp = 0x03AF
        f.run(0x7958, 0x797A)
        self.assertEqual(f.memory.mem[0x3A] & 8, 0)
        self.assertEqual(f.cpu.s.sp, 0x03AF)
        f.run(0x797A, 0x797D)
        self.assertEqual(f.low_sp, 0x03A9)
        self.assertTrue(any(0x03A0 <= a < 0x03B0 for a, v in f.memory.writes))

    def test_adc_wait_has_constant_stack_but_no_software_poll_limit(self):
        f = self.fixture()
        f.memory.adc_ready = False
        f.cpu._push16(0x7000)
        entry_sp = f.cpu.s.sp
        f.run(0x7B6D, 0x7B79)
        waiting_sp = f.cpu.s.sp
        for _ in range(200):
            f.step()
            self.assertEqual(f.cpu.s.pc, 0x7B79)
            self.assertEqual(f.cpu.s.sp, waiting_sp)
            self.assertFalse(f.cpu.interrupt(0xFFF2))
        self.assertFalse(any(a == 0x303A for a, v in f.memory.writes))
        f.memory.adc_ready = True
        f.run(0x7B79, 0x7000)
        self.assertEqual(f.cpu.s.sp, 0x03F4)
        self.assertEqual(entry_sp-f.low_sp, 4)

    def iac_gear_fixture(self):
        f = self.fixture()
        # A direction reversal on the first tick, then one ring transition on
        # the second, stays inside the CPU's independently usable BRSET cases.
        # Accepted service position override holds target1 across main passes.
        for address, value in [(2,2),(0xA7,128),(0x0A,0x10),(8,1),(7,2),(0x4C,0x10),
                               (0x3B,0x10),(0x42,1),(0x038E,4),(0x0395,1),(0x0396,1)]:
            f.memory.mem[address] = value
        f.word(0x3FC0, 0x0700)
        return f

    def test_complete_toc3_passes_can_publish_a_stale_iac_shadow_after_gear_merge(self):
        baseline = self.iac_gear_fixture()
        baseline.irq(0xFFE4)
        baseline.irq(0xFFE4)
        normal = [(pc, value) for pc, address, value, width in baseline.memory.events if address == 0x3062]
        self.assertEqual(normal, [(0xF411, 0x10), (0xF411, 0x39)])
        for boundary, phase in [(0xC51C,0x18),(0xC51F,0x10),(0xC521,0x10),(0xC522,0x10),(0xC525,0x18)]:
            f = self.iac_gear_fixture()
            injected = False
            def inject(machine):
                nonlocal injected
                if machine.cpu.s.pc == boundary and not injected:
                    injected = True
                    machine.irq(0xFFE4)
            f.irq(0xFFE4, inject)
            self.assertTrue(injected)
            self.assertEqual(f.memory.mem[2], 4)
            self.assertEqual(f.memory.mem[7], 1)
            self.assertEqual(f.memory.mem[0x0A] & 0x1C, 0x18)
            issued = [value for pc, address, value, width in f.memory.events if address == 0x3062]
            self.assertEqual(len(issued), 2)
            self.assertEqual(issued[-1] & 0x1C, phase)
            self.assertEqual(f.memory.mem[0x4C] & 0x1C, phase)
            self.assertEqual(f.cpu.s.sp, 0x03F4)
            # All callees execute: no scheduler substitution or external hook.
            self.assertNotIn(0x7AA5, f.trace)
            self.assertFalse(any(0x1800 <= pc < 0x1818 for pc in f.trace))


if __name__ == '__main__':
    unittest.main()
