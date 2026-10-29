"""Selected stock-BMHM interrupt contracts needed by an independent rewrite.

No CPU or peripheral simulator is changed. Device words are flat coherent
fixture samples; SCI ready/error bits and arrivals are explicitly supplied.
Scheduler-only tests retain the existing runner's explicit callee stubs.
These witnesses prove selected schedules, not arbitrary timing or interleavings.
"""
from __future__ import annotations

from hashlib import sha256
import csv
import io
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from build_factory_scheduler import recorded_rom
from factory_integer_replay import IntegerMemory
from factory_scheduler_replay import HC11CPU, SchedulerReplay
from verify_factory_ownership import EVIDENCE
from verify_factory_rom_structure import EXPECTED_SHA256
import verify_factory_interrupt_masks as mask_proof


class BoundaryReplay:
    def __init__(self, rom):
        self.memory = IntegerMemory(rom)
        self.cpu = HC11CPU(self.memory)
        self.cpu.s.sp = 0x03F4
        self.cpu.s.ccr = 0xC0
        self.cpu.s.pc = 0x7000
        self.trace = []

    def word(self, address, value):
        self.memory.mem[address:address+2] = (value & 65535).to_bytes(2, 'big')

    def readword(self, address):
        return int.from_bytes(self.memory.mem[address:address+2], 'big')

    def state(self):
        s = self.cpu.s
        return s.pc, s.sp, s.a, s.b, s.x, s.y, s.ccr

    def step(self):
        self.trace.append(self.cpu.s.pc)
        self.memory.pc = self.cpu.s.pc
        self.cpu.step()

    def run(self, start, stop, budget=30000):
        self.cpu.s.pc = start
        for _ in range(budget):
            if self.cpu.s.pc == stop:
                return
            self.step()
        raise AssertionError(f'Budget at {self.cpu.s.pc:04X}')

    def call(self, entry):
        self.cpu._push16(0x7000)
        self.run(entry, 0x7000)

    def irq(self, vector, before_step=None):
        old = self.state()
        assert self.cpu.interrupt(vector)
        for _ in range(30000):
            # A nested handler can itself visit the interrupted PC. Require
            # the original SP too, then verify the complete RTI restoration.
            if (self.cpu.s.pc, self.cpu.s.sp) == old[:2]:
                assert self.state() == old
                return
            if before_step:
                before_step(self)
            self.step()
        raise AssertionError(f'IRQ return budget at {self.cpu.s.pc:04X}')

    def exchange(self, payload, ident=0xF4, corrupt_checksum=False):
        request = bytes([ident, 0x55+len(payload), *payload])
        request += bytes([(-sum(request) + int(corrupt_checksum)) & 255])
        start = len(self.memory.events)
        for value in request:
            self.memory.mem[0x302E] = 0x20
            self.memory.mem[0x302F] = value
            self.irq(0xFFD6)
        for _ in range(300):
            if self.memory.mem[0x302D] == 0x26:
                break
            self.memory.mem[0x302E] = 0xC0
            self.irq(0xFFD6)
        else:
            raise AssertionError('SCI did not finish')
        return bytes(v for pc, a, v, width in self.memory.events[start:] if a == 0x302F)


class ReentryReplay(SchedulerReplay):
    """Existing bounded scheduler fixture, with stack-qualified IRQ return."""
    def tick(self):
        before = (self.cpu.s.pc, self.cpu.s.sp, self.cpu.s.a, self.cpu.s.b,
                  self.cpu.s.x, self.cpu.s.y, self.cpu.s.ccr)
        assert self.cpu.interrupt(0xFFE4)
        for _ in range(50000):
            if (self.cpu.s.pc, self.cpu.s.sp) == before[:2]:
                after = (self.cpu.s.pc, self.cpu.s.sp, self.cpu.s.a, self.cpu.s.b,
                         self.cpu.s.x, self.cpu.s.y, self.cpu.s.ccr)
                assert after == before
                return
            self.step()
        raise AssertionError('Nested scheduler return budget')


class FactoryInterruptContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = recorded_rom(json.loads(EVIDENCE.read_text()))
        file_image = bytes([255])*0x4000 + cls.rom.read(0x4000, 0xC000)
        assert sha256(file_image).hexdigest() == EXPECTED_SHA256

    def fixture(self):
        return BoundaryReplay(self.rom)

    def test_ram_refresh_blocks_maskable_interrupts_across_all_eight_word_pairs(self):
        f = self.fixture()
        f.cpu.s.x = 0x0050
        original = bytes(f.memory.mem[0x50:0x60])
        f.run(0x7483, 0x7484)
        attempts = 0
        while f.cpu.s.pc != 0x74AA:
            before = f.state()
            self.assertFalse(f.cpu.interrupt(0xFFF2))
            self.assertEqual(f.state(), before)
            attempts += 1
            f.step()
        self.assertEqual(attempts, 19)
        self.assertEqual(bytes(f.memory.mem[0x50:0x60]), original)
        self.assertEqual(f.readword(0x029B), 0x0060)
        # Execute CLI and the following branch before delivering REF. The next
        # block self-copy must preserve the new pending flag in the old block.
        f.step()
        f.step()
        f.irq(0xFFF2)
        self.assertEqual(f.memory.mem[0x50] & 0x20, 0x20)
        f.run(f.cpu.s.pc, 0x74AB)
        self.assertEqual(f.memory.mem[0x50] & 0x20, 0x20)

    def test_async_main_caller_masks_every_helper_boundary_then_allows_sci_completion(self):
        f = self.fixture()
        f.word(0x3FFC, 0xB93E)
        f.cpu.s.d = 0x0100
        f.memory.mem[0x302D] = 0x40
        f.memory.mem[0x302E] = 0xC0
        f.run(0x84A9, 0x84AA)
        attempts = 0
        while f.cpu.s.pc != 0x84AD:
            before = f.state()
            self.assertFalse(f.cpu.interrupt(0xFFD6))
            self.assertEqual(f.state(), before)
            attempts += 1
            f.step()
        self.assertGreater(attempts, 15)
        self.assertIn(0x8548, f.trace)
        self.assertEqual(f.readword(0x3FFC), 0xBD3E)
        f.step()  # CLI
        f.step()  # Following BSET
        f.irq(0xFFD6)
        self.assertEqual(f.readword(0x3FFC), 0xBD3A)

    def test_async_ref_caller_inherits_irq_mask_through_the_full_helper(self):
        f = self.fixture()
        f.word(0x3FFC, 0xB93E)
        f.word(0x02CF, 0x0100)
        f.memory.mem[0x02CD] = 0xFF
        f.memory.mem[0x302D] = 0x40
        f.memory.mem[0x302E] = 0xC0
        attempts = []
        def probe(machine):
            if 0x8548 <= machine.cpu.s.pc <= 0x858A:
                attempts.append(machine.cpu.s.pc)
                self.assertFalse(machine.cpu.interrupt(0xFFD6))
        f.irq(0xFFF2, probe)
        self.assertIn(0x762D, f.trace)
        self.assertIn(0x857F, attempts)
        self.assertIn(0x8587, attempts)
        self.assertEqual(f.memory.mem[0x3FFD] & 4, 4)
        f.irq(0xFFD6)
        self.assertEqual(f.memory.mem[0x3FFD] & 4, 0)

    def test_unmasked_async_helper_counterexample_explains_required_caller_contract(self):
        f = self.fixture()
        f.word(0x3FFC, 0xB93E)
        f.cpu.s.d = 0x0100
        f.memory.mem[0x302D] = 0x40
        f.memory.mem[0x302E] = 0xC0
        f.cpu._push16(0x7000)
        f.run(0x8548, 0x857F)
        f.irq(0xFFD6)
        self.assertEqual(f.readword(0x3FFC), 0xB93A)
        f.run(0x857F, 0x7000)
        # This deliberately violates BOTH resident callers' masking contract.
        # It is a counterexample for a rewrite, not an observed factory race.
        self.assertEqual(f.readword(0x3FFC), 0xBD3E)
        self.assertEqual(f.memory.mem[0x302D], 0x26)

    def test_three_early_ticks_dispatch_three_passes_but_busy_ticks_coalesce(self):
        for boundary, expected_phases, expected_tick_phases, pending_writes in [
                (0x797D, [1, 2, 3, 4], [0, 0, 1, 2], 0),
                (0x798C, [1, 2], [0, 0, 0, 0], 3),
                (0x7A44, [1, 2], [0, 1, 1, 1], 3)]:
            r = ReentryReplay()
            injected = False
            def inject(machine):
                nonlocal injected
                if machine.cpu.s.pc == boundary and not injected:
                    injected = True
                    for _ in range(3):
                        machine.tick()
            r.before_step = inject
            r.tick()
            self.assertTrue(injected)
            self.assertEqual([phase for phase, target in r.passes], expected_phases)
            self.assertEqual([phase for pc, target, phase, ccr in r.calls if target == 0x91A3], expected_tick_phases)
            self.assertEqual(sum(a == 0x3A and bool(v & 0x20) for a, v in r.memory.writes), pending_writes)
            self.assertEqual(r.cpu.s.sp, 0x03FF)
            self.assertEqual(r.memory.mem[0x3A] & 0x28, 0)

    def test_explicit_cli_helpers_return_unmasked_even_when_entered_masked(self):
        for entry in [0xF3EE, 0x91A3]:
            f = self.fixture()
            f.cpu.s.ccr |= 0x10
            f.call(entry)
            self.assertEqual(f.cpu.s.ccr & 0x10, 0)
        f = self.fixture()
        f.cpu.s.ccr |= 0x10
        f.cpu.s.d = 0x0100
        f.call(0x8548)
        self.assertEqual(f.cpu.s.ccr & 0x10, 0x10)

    def test_accepted_clear_request_can_be_replaced_before_the_service_poll(self):
        for intervening_poll in [False, True]:
            f = self.fixture()
            f.memory.mem[0x302D] = 0x26
            self.assertEqual(f.exchange([0x0A]), bytes.fromhex('F4 56 0A AC'))
            self.assertEqual(f.memory.mem[0x3B] & 2, 2)
            if intervening_poll:
                f.call(0xF64E)
                self.assertIn(0xF333, f.trace)
            reply = f.exchange([1, 0])
            self.assertEqual(len(reply), 67)
            self.assertEqual(sum(reply) & 255, 0)
            self.assertEqual(f.memory.mem[0x3B] & 3, 0)
            f.call(0xF64E)
            self.assertEqual(f.trace.count(0xF333), int(intervening_poll))

    def test_rejected_packet_keeps_prior_clear_request_but_retains_prefix_effects(self):
        f = self.fixture()
        f.memory.mem[0x302D] = 0x26
        f.exchange([0x0A])
        self.assertEqual(f.exchange([1, 0], corrupt_checksum=True), b'')
        self.assertEqual(f.memory.mem[0x3B] & 2, 2)
        self.assertEqual(f.memory.mem[0x42] & 1, 1)
        self.assertEqual(f.memory.mem[0x036C], 1)
        self.assertEqual(f.memory.mem[0x038E], 0x0A)
        f.call(0xF64E)
        self.assertIn(0xF333, f.trace)

    def test_short_service_packet_retains_unreplaced_suffix_from_previous_command(self):
        f = self.fixture()
        f.memory.mem[0x302D] = 0x26
        f.exchange([4, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        before = bytes(f.memory.mem[0x038E:0x0399])
        f.exchange([4, 0xAA])
        after = bytes(f.memory.mem[0x038E:0x0399])
        self.assertEqual(after[:2], bytes([4, 0xAA]))
        self.assertEqual(after[2:], before[2:])
        self.assertEqual(f.memory.mem[0x42] & 1, 1)

    def test_fault_vectors_distinguish_software_traps_cop_restart_and_clock_monitor(self):
        for vector, target, cause, stop in [
                (0xFFF6, 0xFC04, 0x08, 0xFC07),
                (0xFFF8, 0xFC1A, 0x10, 0xFC1D),
                (0xFFFA, 0xFC1F, 0x20, 0x7100),
                (0xFFFC, 0xFC24, 0x40, 0xFC27),
                (0xFFFE, 0xFC29, 0x80, 0x7100)]:
            f = self.fixture()
            self.assertEqual(f.readword(vector), target)
            f.memory.mem[0] = 1
            # This checks the resident handler body; it does not model the
            # hardware reset event, register defaults or RAM retention.
            f.run(target, stop)
            self.assertEqual(f.memory.mem[0], 1 | cause)
            if stop != 0x7100:
                f.step()
                self.assertEqual(f.cpu.s.pc, stop)

    def test_xirq_handler_edits_stacked_ccr_and_returns_with_x_mask_set(self):
        f = self.fixture()
        f.cpu.s.ccr = 0x80  # X=0 and I=0 before an enabled XIRQ.
        old = f.state()
        self.assertTrue(f.cpu.interrupt(0xFFF4, maskable=False))
        # The generic CPU entry helper only sets I. Supply the real XIRQ
        # entry X=1 precondition here, per M68HC11RM section5.5, without
        # changing the simulator or claiming its XIRQ arbitration is modeled.
        f.cpu.s.ccr |= 0x40
        self.assertEqual(f.cpu.s.pc, 0xFC09)
        f.run(0xFC09, old[0])
        self.assertEqual(f.state()[:-1], old[:-1])
        self.assertEqual(f.cpu.s.ccr, old[-1] | 0x40)
        self.assertEqual(f.memory.mem[0] & 4, 4)

    def test_global_mask_artifacts_reproduce_and_selected_postconditions_match_execution(self):
        generated = mask_proof.build(self.rom)
        for name, content in generated.items():
            self.assertEqual((mask_proof.OUT/name).read_text(), content, name)
        rows = {int(r['entry'], 16): r for r in csv.DictReader(io.StringIO(generated[mask_proof.CSV]))}
        self.assertEqual(len(rows), 253)
        for entry, kind in [(0x8548, 'preserves_I'), (0x92A4, 'preserves_I'),
                            (0x92F1, 'preserves_I'), (0x91A3, 'returns_I_clear'),
                            (0xF3EE, 'returns_I_clear'), (0xF781, 'returns_I_clear')]:
            self.assertEqual(rows[entry]['classification'], kind)
            for incoming in [0, 1]:
                for coolant in [0, 128, 255]:
                    f = self.fixture()
                    f.cpu.s.ccr = 0xC0 | (incoming << 4)
                    f.cpu.s.d = 0x0100
                    f.memory.mem[6] = coolant
                    f.memory.mem[8] = 0xFF
                    f.call(entry)
                    actual = (f.cpu.s.ccr >> 4) & 1
                    allowed = rows[entry][f'input_I{incoming}_possible_RTS_I'].split(';')
                    self.assertIn(str(actual), allowed, (entry, incoming, coolant))
        metadata = json.loads(generated[mask_proof.META])
        self.assertEqual(metadata['opaque_calls'], ['8C6A','8EDF','93D4','A9E4','AB66','D029','F5D3','F5E4','FAA5'])
        self.assertEqual(metadata['TAP_pcs'], ['7D8C','92B3','92D3','9350','936A','9381','939B'])
        for row in rows.values():
            if '1' in row['input_I0_possible_RTS_I'].split(';'):
                self.assertTrue(row['transitive_opaque_call_pcs'], row['entry'])


if __name__ == '__main__':
    unittest.main()
