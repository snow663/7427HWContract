from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import build_factory_scheduler as scheduler
from factory_rom_decode import DecodeError, decode
from factory_scheduler_replay import SchedulerReplay


class FactorySchedulerTests(unittest.TestCase):
    def test_recorded_map_is_deterministic_and_rejects_wrong_rom(self):
        evidence = json.loads(scheduler.EVIDENCE.read_text())
        outputs = scheduler.build(scheduler.recorded_rom(evidence))
        for name, content in outputs.items():
            self.assertEqual((scheduler.OUT / name).read_text(), content, name)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "wrong.bin"
            for data in (b"partial", bytes(65536)):
                path.write_bytes(data)
                with self.assertRaisesRegex(ValueError, "SHA-256"):
                    scheduler.full_rom(path)

    def test_byte_decoder_distinguishes_indexed_word_load_and_call(self):
        data = bytes.fromhex("EE 00 AD 00")
        first = decode(lambda a,n: data[a:a+n], 0)
        second = decode(lambda a,n: data[a:a+n], 2)
        self.assertEqual((first.op, first.access()["width_bits"]), ("LDX", 16))
        self.assertEqual(first.operand, "$00,X")
        self.assertIsNone(second.access())
        with self.assertRaises(DecodeError):
            decode(lambda a,n: bytes(n), 0)

    def test_boot_clear_executes_real_STY_zero_words_without_clearing_neighbors(self):
        replay = SchedulerReplay()
        replay.memory.mem[0x0035:0x0101] = bytes([0xA5]) * 204
        replay.cpu.s.pc = 0x7164
        replay.run_until(0x716D)
        self.assertEqual(replay.memory.mem[0x36:0x100], bytes(0xCA))
        self.assertEqual(replay.memory.mem[0x35], 0xA5)
        self.assertEqual(replay.memory.mem[0x100], 0xA5)
        # $003A pending and $004F busy really lie inside this clear.
        self.assertEqual((replay.memory.mem[0x3A], replay.memory.mem[0x4F]), (0, 0))

    def test_startup_seed_dispatches_slot_F_first(self):
        replay = SchedulerReplay()
        replay.cpu.s.pc = 0x7431
        replay.run_until(0x7435)
        self.assertEqual(replay.memory.mem[2], 0x0E)
        replay.tick()
        self.assertEqual(replay.passes, [(0x0F, 0x7B5A)])
        self.assertEqual(replay.memory.mem[0x51] & 4, 4)

    def test_all_160_phases_call_counts_order_and_interrupt_mask(self):
        replay = SchedulerReplay()
        replay.memory.mem[2] = 0x9F
        for phase in range(160):
            start = len(replay.calls)
            replay.tick()
            calls = replay.calls[start:]
            self.assertEqual(replay.passes[-1][0], phase)
            self.assertEqual(calls[0][1], 0x7B6D)
            self.assertLess(next(i for i,c in enumerate(calls) if c[0] == 0x79F2),
                            next(i for i,c in enumerate(calls) if c[0] == 0x7A4F))
        self.assertEqual(Counter(t for _,t in replay.passes),
                         Counter({t:10 for t in [0x7AA6,0x7AAD,0x7AB7,0x7ABD,0x7AC7,0x7B03,0x7B14,0x7B1B,
                                                0x7B2B,0x7B2F,0x7B39,0x7B3D,0x7B44,0x7B48,0x7B52,0x7B5A]}))
        expected = {0x7B6D:160,0x91A3:160,0xF245:160,0x7C13:160,0x7BA7:160,
                    0x9167:80,0xA466:80,0xD14E:80,0xD1F6:80,0xF5E8:80,
                    0x7D4B:80,0xCDF7:80,0xF3E4:80,0xB56B:40,0xD03E:40,0xAE85:40,
                    0x93D0:40,0xC4E5:40,0xB32D:40,0xC8B1:10,0xB9EE:5,0xE75F:5,0xC6BB:10,0xC514:40}
        for target, count in expected.items():
            self.assertEqual(replay.count(target), count, f"${target:04X}")
        for call in replay.calls:
            if call[1] == 0xF20D:
                self.assertTrue(call[3] & 0x10)
        self.assertEqual(replay.memory.read16(0x301A), (819*160) & 0xFFFF)
        self.assertEqual(replay.memory.mem[2], 0x9F)

    def test_slot4_alternating_group_order_and_fault_bits(self):
        for phase, expected in [(4,[0xC8B1,0xE75F,0xE793,0xC96A,0xC9C0,0xC9F7]),
                                (0x14,[0xC8B1,0xB9EE,0xB99F,0xEAB1,0xEAE4,0xC8D6,0xC8FD])]:
            for faults in range(4):
                replay = SchedulerReplay()
                replay.memory.mem[2] = phase-1
                replay.memory.mem[0x6F] = 0xFF
                replay.memory.mem[0x16] = faults & 1
                replay.memory.mem[0x17] = 0x80 if faults & 2 else 0
                replay.tick()
                actual = [target for pc,target,_,_ in replay.calls if 0x7AC7 <= pc < 0x7B03]
                self.assertEqual(actual, expected)
                self.assertEqual(replay.memory.mem[0x6F] & 0x24, (4 if faults & 1 else 0) | (0x20 if faults & 2 else 0))

    def test_special_mode_skips_fast_groups_but_keeps_table_and_watchdog(self):
        replay = SchedulerReplay()
        replay.memory.mem[2], replay.memory.mem[0x1A] = 0x9F, 0x20
        for _ in range(160):
            replay.tick()
        self.assertEqual(len(replay.passes), 160)
        self.assertEqual(replay.count(0xAC51), 80)
        self.assertEqual(replay.count(0x7BA7), 0)
        self.assertEqual(replay.count(0x9167), 0)
        self.assertEqual(replay.count(0xF3E4), 0)
        self.assertEqual([value for address,value in replay.memory.writes if address == 0x303A], [0xAA,0x55]*80)

    def test_heartbeat_has_two_condition_gate_and_actual_board_write(self):
        for service in (0,0x10):
            for hold in (0,0x80):
                replay = SchedulerReplay()
                replay.memory.mem[0x3B], replay.memory.mem[0x391] = service, hold
                replay.tick()  # phase 1
                skipped = bool(service and hold)
                self.assertEqual(replay.count(0xF3E4), int(not skipped))
                self.assertEqual(replay.memory.mem[0x3066], 0 if skipped else 0x80)
                if skipped:
                    self.assertEqual(replay.memory.mem[0x44] & 4, 4)
                    self.assertEqual(replay.memory.mem[0x43] & 0x80, 0x80)

    def test_slot5_calibration_gate(self):
        for bit in (0,0x40):
            replay = SchedulerReplay()
            replay.memory.mem[2] = 4
            replay.memory.mem[0x400F] = 0x10 | bit  # Deliberate counterfactual fixture.
            replay.tick()
            self.assertEqual(replay.count(0xD3B0), 1)
            self.assertEqual(replay.count(0xD472), 1)
            self.assertEqual(replay.count(0xC6BB), int(not bit))

    def test_multiple_busy_interrupts_coalesce_to_one_catchup(self):
        replay = SchedulerReplay()
        injected = False
        def inject(machine):
            nonlocal injected
            if machine.cpu.s.pc == 0x7A44 and not injected:
                injected = True
                for _ in range(3):
                    machine.tick()
                self.assertEqual(machine.memory.mem[3], 1)
                self.assertEqual(machine.memory.mem[0x3A] & 0x20, 0x20)
        replay.before_step = inject
        replay.tick()
        self.assertEqual([phase for phase,_ in replay.passes], [1,2])
        self.assertEqual(replay.count(0x7B6D), 4)
        self.assertEqual(replay.count(0x7BA7), 2)
        self.assertEqual(replay.memory.mem[0x4F] & 4, 0)
        self.assertEqual(replay.memory.mem[0x3A] & 0x20, 0)
        self.assertEqual(replay.cpu.s.sp, 0x03FF)
        self.assertEqual(replay.cpu.s.pc, 0x74D0)

    def test_stack_check_recovery_sets_fault_and_discards_busy_state(self):
        for busy, sp, valid in [(0,0x03F6,True),(0,0x03F7,False),(0,0x03AE,False),
                                (4,0x03ED,True),(4,0x03EE,False),(4,0x03AF,True)]:
            replay = SchedulerReplay()
            replay.memory.mem[0x4F] = busy
            replay.cpu.s.sp, replay.cpu.s.pc = sp, 0x7958
            replay.run_until(0x797A)
            self.assertEqual(bool(replay.memory.mem[0x3A] & 8), not valid, hex(sp))
            self.assertEqual(replay.cpu.s.sp, sp if valid else 0x03F6)
            self.assertEqual(replay.memory.mem[0x4F] & 4, busy if valid else 0)

    def test_profiling_peak_word_uses_slot_and_pending_extra_819(self):
        for pending in (0,0x20):
            replay = SchedulerReplay()
            replay.cpu.interrupt(0xFFE4)
            replay.cpu.s.pc = 0x7A51
            replay.memory.mem[2] = 0x12
            replay.memory.mem[0x86], replay.memory.mem[0x3A] = 0x40, pending
            replay.memory.write16(0x300E, 1000)
            replay.memory.write16(0x301A, 1100)
            replay.memory.write16(0x02D7, 200)
            replay.run_until(0x74D0)
            self.assertEqual(replay.memory.read16(0x02D7), 719 + (819 if pending else 0))

    def test_wrap_run_timer_preserves_FFFF_but_compares_wrapped_X(self):
        replay = SchedulerReplay()
        replay.memory.mem[2], replay.memory.mem[0x4F], replay.memory.mem[4] = 0x9F, 0x80, 0x10
        replay.memory.write16(0xFD, 0xFFFF)
        replay.tick()
        self.assertEqual(replay.passes[0][0], 0)
        self.assertEqual(replay.memory.read16(0xFD), 0xFFFF)
        self.assertEqual(replay.memory.mem[4] & 0x10, 0x10)

    def test_service_override_copy_bit_and_refresh_handshake(self):
        for requested, value in [(False,0),(True,0),(True,4)]:
            replay = SchedulerReplay()
            replay.memory.mem[0x3B], replay.memory.mem[0x38F] = 0x10, 4 if requested else 0
            replay.memory.mem[0x390], replay.memory.mem[0x72] = value, 0x80
            replay.tick()
            self.assertEqual(replay.memory.mem[0x72] & 0x80, 0x80 if not requested or value else 0)
        for refreshed in (False,True):
            replay = SchedulerReplay()
            replay.memory.mem[2], replay.memory.mem[0x51] = 0x0D, 0 if refreshed else 4
            replay.tick()  # slot E
            self.assertEqual(replay.memory.mem[4] & 4, 0 if refreshed else 4)

    def test_factory_mode_diverts_before_normal_dispatch_and_resets_stack(self):
        replay = SchedulerReplay()
        replay.memory.mem[0x44], replay.memory.mem[2] = 1, 0x9F
        replay.cpu.interrupt(0xFFE4)
        replay.run_until(0xFA5E)
        self.assertEqual(replay.memory.mem[2], 0xA0)  # No normal $A0 wrap in this path.
        self.assertEqual(replay.passes, [])
        self.assertEqual(replay.count(0x7B6D), 0)
        self.assertEqual(replay.cpu.s.sp, 0x03FF)

    def test_factory_callback_uses_full_RAM_word_and_device_handshake(self):
        for device, latched, dispatched in [(2,0,True),(3,0,False),(3,1,True),(4,1,False)]:
            replay = SchedulerReplay()
            replay.cpu.s.pc = 0xFA83
            replay.memory.mem[0x364], replay.memory.mem[1] = device, latched
            replay.memory.write16(0x38E, 0xABCD)
            replay.run_until(0xFBD4 if dispatched else 0xFACA)
            calls = [call for call in replay.calls if call[0] == 0xFAA5]
            self.assertEqual([call[1] for call in calls], [0xABCD] if dispatched else [])
            if dispatched:
                self.assertEqual(replay.memory.mem[1] & 1, 1)

    def test_factory_ADC_lower_threshold_is_decimal_40_and_upload_copies_32_bytes(self):
        replay = SchedulerReplay()
        replay.cpu.s.pc = 0xFA5B
        replay.memory.adc_samples = {1:50,3:30}  # 50 passes ROM $28; HAC's $40 would reject it.
        replay.memory.mem[0x364] = 1
        replay.memory.mem[1] = 1
        replay.memory.write16(0x38E, 0x0200)
        replay.memory.mem[0x390:0x3B0] = bytes(range(32))
        replay.run_until(0xFBD4)
        self.assertEqual(replay.memory.mem[0x200:0x220], bytes(range(32)))
        self.assertEqual(replay.memory.mem[1] & 1, 0)
        self.assertEqual(replay.memory.mem[0x364], 0xFE)

    def test_received_factory_payload_supplies_both_callback_address_bytes(self):
        replay = SchedulerReplay()
        replay.cpu.s.pc = 0xF9C3
        replay.memory.mem[0x50], replay.memory.mem[0x365] = 8, 2
        replay.memory.mem[0x36C:0x36E] = bytes.fromhex("AB CD")
        replay.run_until(0xFA21)
        self.assertEqual(replay.memory.read16(0x38E), 0xABCD)
        replay.memory.mem[0x364] = 2
        replay.cpu.s.pc = 0xFA83
        replay.run_until(0xFBD4)
        self.assertEqual([c[1] for c in replay.calls if c[0] == 0xFAA5], [0xABCD])


if __name__ == "__main__":
    unittest.main()
