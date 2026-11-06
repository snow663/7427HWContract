"""Manual-idle strategy against native C and actual HC11 instructions.

The default fixture contains recorded Rev A excerpts, never a bootable BIN.
Tests establish software behavior, not engine stability or target readiness.
"""
from __future__ import annotations
import ctypes
from hashlib import sha256
import json
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'tools'), str(ROOT / 'hac31_romsim')]
from manual_idle_asm import assemble
from manual_idle_overlay import EXPECTED_SHA, RETIRED, SOURCE, layout_header
from romsim.hc11_core import HC11CPU, HC11Memory

ASSEMBLY = assemble(SOURCE)
S = ASSEMBLY.symbols


def fixture():
    evidence = json.loads((ROOT / 'maps/maintenance/manual_idle_reva_evidence.json').read_text())
    assert evidence['image_sha256'] == EXPECTED_SHA
    memory = bytearray(65536)
    for row in evidence['ranges']:
        lo, hi = int(row['start'], 16), int(row['end_exclusive'], 16)
        raw = bytes.fromhex(row['bytes'])
        assert len(raw) == hi - lo
        memory[lo:hi] = raw
    for lo, hi in RETIRED:
        memory[lo:hi] = b'\xff' * (hi - lo)
    for a, byte in ASSEMBLY.memory.items(): memory[a] = byte
    for a in (0x92a4, 0x92f1): memory[a:a + 3] = b'\x7e' + S['mi_init'].to_bytes(2, 'big')
    return memory


def put(m, address, value): m[address:address + 2] = value.to_bytes(2, 'big')
def word(m, address): return int.from_bytes(m[address:address + 2], 'big')


class Memory(HC11Memory):
    def __init__(self, contents):
        super().__init__(); self.mem[:] = contents
        self.written = set(); self.minimum_sp = 0x3ff
    def read8(self, a): return self.mem[a & 65535]
    def write8(self, a, value):
        if a >= 0x3000:
            raise AssertionError(f'Unexpected ROM/hardware write: {a:04X}')
        self.written.add(a); self.mem[a] = value & 255
    def tick(self, n): self.cycle_counter += n


def execute(contents, entry, stop=None):
    memory = Memory(contents); cpu = HC11CPU(memory)
    cpu.s.pc = S.get(entry, entry); cpu.s.sp = 0x3ff; cpu.s.ccr = 0xd0
    cpu._push16(0x7000)
    pcs = []
    for _ in range(2000):
        if cpu.s.pc == (stop if stop is not None else 0x7000):
            if stop is None: assert cpu.s.sp == 0x3ff, hex(cpu.s.sp)
            else: assert cpu.s.sp == 0x3fd, hex(cpu.s.sp)
            return memory, cpu, pcs
        pcs.append(cpu.s.pc)
        cpu.step(); memory.minimum_sp = min(memory.minimum_sp, cpu.s.sp)
        assert not (cpu.halted or cpu.waiting), hex(cpu.s.pc)
    raise AssertionError(f'Instruction budget exceeded at {cpu.s.pc:04X}')


class ManualIdle(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix='manual_idle_')
        output = Path(cls.tmp.name) / 'manual_idle.so'
        subprocess.run(['cc', '-std=c99', '-O2', '-Wall', '-Wextra', '-Werror',
            '-pedantic', '-shared', '-fPIC', str(ROOT / 'source/manual_idle/manual_idle.c'),
            '-o', str(output)], check=True)
        cls.lib = ctypes.CDLL(str(output))
        for function in ('mi_init', 'mi_target', 'mi_stopped', 'mi_run'):
            f = getattr(cls.lib, function)
            f.argtypes = [ctypes.POINTER(ctypes.c_uint8)]
            f.restype = ctypes.c_uint16 if function in ('mi_run', 'mi_stopped') else None
        cls.count = 0; cls.pcs = set(); cls.max_cycles = 0; cls.minimum_sp = 0x3ff

    @classmethod
    def tearDownClass(cls): cls.tmp.cleanup()

    def seed(self):
        m = fixture(); m[0x0283] = 169; m[0x63] = 68; m[0x1cc] = 200
        self.native(m, 'mi_init'); return m

    def native(self, m, function):
        array = (ctypes.c_uint8 * 65536).from_buffer(m)
        return getattr(self.lib, function)(array)

    def compare(self, m, function):
        native = bytearray(m); expected = self.native(native, function)
        stop = 0x983d if function in ('mi_stopped', 'mi_run') else None
        actual, cpu, pcs = execute(m, function, stop)
        difference = [f'{a:04X}:{native[a]:02X}/{actual.mem[a]:02X}'
                      for a in range(0x3000) if not 0x3c0 <= a < 0x400 and native[a] != actual.mem[a]]
        self.assertEqual(difference, [], (function, difference[:15]))
        if stop is not None: self.assertEqual(expected, cpu.s.d)
        self.__class__.count += 1; self.__class__.pcs.update(pcs)
        self.__class__.max_cycles = max(self.max_cycles, actual.cycle_counter)
        self.__class__.minimum_sp = min(self.minimum_sp, actual.minimum_sp)
        return actual, cpu, pcs

    def test_layout_and_source_boundary(self):
        self.assertEqual((ROOT / 'source/manual_idle/manual_idle_layout.h').read_text(), layout_header())
        # Strategy never writes phase, software position, or hardware. The
        # existing guard, converter and driver are outside replacement spans.
        from factory_rom_decode import decode
        m = fixture()
        for a in ASSEMBLY.instructions:
            i = decode(lambda p, n: m[p:p+n], a); access = i.access()
            if access and 'W' in access['access']:
                self.assertNotIn(access['address'], (7, 0xa, 0x4c))
                self.assertLess(access['address'], 0x3000)
            if i.op in ('BRSET', 'BRCLR') and i.value == 0x36:
                self.assertEqual(i.mask & 2, 0, 'Old gear context remains')

    def test_stopped_and_initialization_every_temperature(self):
        for coordinate in range(256):
            for ac in (0, 0x20):
                m = fixture(); m[0x283] = coordinate; m[0x52] = ac
                m[0x36] = 255; m[9] = 255; m[0x18] = 255
                actual, _, _ = self.compare(m, 'mi_stopped')
                self.assertEqual(actual.mem[0x087f], 0, 'Initialization must not inject IAC-change AE')

    def test_state_boundaries_against_hc11(self):
        rng = random.Random(742731)
        for n in range(2400):
            m = self.seed()
            m[0x283] = rng.randrange(256)
            m[0x085f] = rng.choice((0, 68, 88, 112, 255))
            m[0x63] = rng.randrange(256); m[0x1d9] = rng.choice((0, 1, 2, 3, 4, 25, 40, 255))
            m[0x36] = rng.randrange(256); m[0x52] = rng.choice((0, 0x20))
            m[0x38] = rng.choice((0, 0x40)); m[0x0857] = rng.randrange(256)
            m[0x46] = rng.choice((0, 8)); m[0x3e] = rng.choice((0, 4))
            m[S['qualify']] = rng.choice((0, 1, 15, 16, 255))
            m[S['start_air']] = rng.choice((0, 1, 60)); m[S['start_div']] = rng.choice((0, 1, 2, 4))
            m[S['signature']] = rng.choice((0, 0xa5))
            put(m, S['integral'], rng.choice((0, 1, 38 << 8, 180 << 8, 65535)))
            put(m, S['follower'], rng.choice((0, 1, 128, 256, 40 << 8, 65535)))
            put(m, 0x0889, rng.choice((0, 1, 0x2600, 65535)))
            put(m, 0x087d, rng.randrange(65536))
            self.compare(m, 'mi_run')

    def test_hysteresis_limits_and_negative_feedback(self):
        for target in (1, 16, 52, 68, 100, 240, 255):
            for retained in (0, 4):
                threshold = target + (16 if retained else 8)
                for rpm in {max(0, min(255, threshold + delta)) for delta in (-1, 0, 1)}:
                    for tps in (0, 2, 3, 4):
                        m = self.seed(); m[0x38] = 0x40; m[0x0857] = target
                        m[0x36] = retained; m[0x63] = rpm; m[0x1d9] = tps
                        self.native(m, 'mi_run')
                        self.assertEqual(bool(m[0x36] & 4), tps <= (3 if retained else 2) and rpm <= threshold)
        outputs = []
        for rpm in (56, 68, 76):
            m = self.seed(); m[S['start_air']] = 0; m[0x63] = rpm
            outputs.append(self.native(m, 'mi_run'))
        self.assertGreater(outputs[0], outputs[1]); self.assertGreater(outputs[1], outputs[2])

    def test_windup_and_admission(self):
        for rpm in (48, 80):
            for blocked in ('start', 'follower', 'dfco', 'voltage', 'unqualified', 'rail'):
                m = self.seed(); m[S['start_air']] = 0; m[0x36] = 4
                m[S['qualify']] = 16; m[0x63] = rpm
                put(m, 0x0889, 0x2600)
                if blocked == 'start': m[S['start_air']] = 60
                if blocked == 'follower': put(m, S['follower'], 1024)
                if blocked == 'dfco': m[0x46] = 8
                if blocked == 'voltage': m[0x3e] = 4
                if blocked == 'unqualified': m[S['qualify']] = 0; m[0x36] = 0
                if blocked == 'rail': put(m, 0x0889, 65535 if rpm < 68 else 0)
                before = word(m, S['integral']); self.compare(m, 'mi_run')
                self.native(m, 'mi_run'); self.assertEqual(word(m, S['integral']), before, (rpm, blocked))
        for rpm, sign in ((60, 1), (76, -1)):
            m = self.seed(); m[S['start_air']] = 0; m[0x36] = 4
            m[S['qualify']] = 16; m[0x63] = rpm; put(m, 0x0889, 0x2600)
            before = word(m, S['integral']); self.compare(m, 'mi_run'); self.native(m, 'mi_run')
            self.assertEqual(word(m, S['integral']) - before, sign * (8 - 2) * 4)

    def test_integral_floor_and_background_entries(self):
        for initial in (0, 1, 23, 24, 25):
            m = self.seed(); m[S['start_air']] = 0; m[0x36] = 4
            m[S['qualify']] = 16; m[0x63] = 76; put(m, 0x0889, 0x2600)
            put(m, S['integral'], initial)
            actual, _, _ = self.compare(m, 'mi_run')
            self.assertEqual(word(actual.mem, S['integral']), max(0, initial - 24))
        m = self.seed(); m[S['start_air']] = 0; m[0x63] = 76
        put(m, S['integral'], 0); put(m, 0x0889, 0)
        self.compare(m, 'mi_run')
        for entry in ('mi_background', 'mi_slow'):
            m = self.seed(); expected = bytearray(m)
            if entry == 'mi_background': self.native(expected, 'mi_target')
            actual, _, pcs = execute(m, entry)
            self.assertEqual(actual.mem[:0x3c0], expected[:0x3c0])
            self.assertEqual(actual.mem[0x400:0x3000], expected[0x400:0x3000])
            self.__class__.pcs.update(pcs)

    def test_startup_decay_and_unused_state_independence(self):
        a, b = self.seed(), self.seed()
        for n in range(300):
            # Noise in obsolete Drive bank, range and VSS variables. Reused
            # Park-bank locations are intentionally new controller state.
            for address in list(range(0x2a7, 0x2b1)) + [0x41, 0xa2, 0x284, 0x285, 0x812, 0x813]:
                b[address] = (n * 37 + address) & 255
            b[0x36] ^= 2
            fa = self.native(a, 'mi_run'); fb = self.native(b, 'mi_run')
            self.assertEqual((fa, a[0x857], word(a, S['integral'])), (fb, b[0x857], word(b, S['integral'])))
            self.assertEqual(a[S['start_air']], max(0, 60 - (n + 1) // 4))
            if n in (0, 3, 15, 239, 240): self.compare(a, 'mi_run')

    def test_follower_and_stall(self):
        m = self.seed(); m[S['start_air']] = 0; m[0x1d9] = 80
        self.native(m, 'mi_run'); self.assertEqual(word(m, S['follower']), 40 << 8)
        m[0x1d9] = 0
        for _ in range(80): self.native(m, 'mi_run')
        self.assertEqual(word(m, S['follower']), 0)
        for rpm, expected in ((51, True), (52, False), (68, False)):
            m = self.seed(); m[0x63] = rpm; self.native(m, 'mi_run')
            self.assertEqual(bool(m[0x36] & 0x10), expected)

    def test_closed_throttle_overspeed_correction_before_capture(self):
        for tps in (0, 4):
            m = self.seed(); m[S['start_air']] = 0; m[0x63] = 110; m[0x1d9] = tps
            initial = word(m, S['integral'])
            actual, _, _ = self.compare(m, 'mi_run')
            self.assertFalse(actual.mem[0x36] & 0x0c)
            self.assertEqual(word(actual.mem, S['integral']), initial)
            self.assertEqual(word(actual.mem, S['p_word']), 40 * 64 if tps == 0 else 0)

    def test_closed_tps_band_has_no_follower_and_saturation_does_not_skip_p(self):
        for tps in (0, 1, 2):
            m = self.seed(); m[S['start_air']] = 0; m[0x36] = 4
            m[S['qualify']] = 16; m[0x63] = 60; m[0x1d9] = tps
            put(m, 0x0889, 0x2600)
            actual, _, _ = self.compare(m, 'mi_run')
            self.assertEqual(word(actual.mem, S['follower']), 0)
            self.assertGreater(word(actual.mem, S['integral']), 38 << 8)
        m = self.seed(); m[0x283] = 0; m[S['start_air']] = 0; m[0x63] = 200
        put(m, S['integral'], 180 << 8)
        actual, cpu, _ = self.compare(m, 'mi_run')
        self.assertFalse(actual.mem[0x36] & 4)
        self.assertGreater(word(actual.mem, S['p_word']), 0)
        self.assertEqual(cpu.s.d, 65535 - word(actual.mem, S['p_word']))

    def test_preserved_reset_service_and_conversion(self):
        # Existing reset-in-work holds target zero until software homing
        # completes, and does not enter either replaced consumer path.
        m = self.seed(); m[9] = 1; m[7] = 25; m[8] = 80
        memory, _, pcs = execute(m, 0x93d0)
        self.assertEqual(memory.mem[8], 0); self.assertEqual(memory.mem[7], 25)
        self.assertNotIn(S['mi_run'], pcs)
        # Retained direct-position service discards its local frame and exits.
        m = self.seed(); m[0x3b] = 0x10; m[0x395] = 1; m[0x396] = 71
        memory, _, pcs = execute(m, 0x93d0)
        self.assertEqual(memory.mem[8], 71); self.assertNotIn(S['mi_run'], pcs)
        # Running path reaches the exact preserved converter and balances stack.
        m = self.seed(); m[0x4f] = 0x80
        memory, _, pcs = execute(m, 0x93d0)
        self.assertIn(0x983d, pcs); self.assertEqual(memory.mem[0x857], 68)
        self.assertTrue(all(a < 0x3000 for a in memory.written))


if __name__ == '__main__':
    unittest.main(verbosity=2)
