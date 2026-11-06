"""Reset/interrupt/scheduler fixtures for the manual-idle in-memory overlay.

Requires exact Rev A, never writes a BIN. Sensor/ASIC fixtures are development
models, not a physical PCM or a model of engine response to changed airflow.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
from manual_idle_overlay import ROOT, EXPECTED_SHA, overlay

sys.path.insert(0, str(ROOT / 'hac31_romsim'))
from romsim.simulator import Simulator
from romsim.bus import ContractMemory
from romsim.devices import TimerDevice


class PrescaledTimer(TimerDevice):
    def tick(self, cycles):
        divisor = (1, 4, 8, 16)[self.regs[0x24] & 3]
        elapsed, self.e_remainder = divmod(self.e_remainder + cycles, divisor)
        super().tick(elapsed)


class FixtureMemory(ContractMemory):
    def _bus_log(self, address, value, rw, note=''):
        if rw == 'R' and address in (0x284, 0x285, 0x812, 0x813):
            self.speed_reads.add((self.context_pc, address))

    def read8(self, address):
        offset = self._internal_offset(address)
        if offset is not None and 0x31 <= offset <= 0x34:
            c = self.adc.control & 7
            channel = (c + offset - 0x31) & 7 if self.adc.control & 0x10 else c
            if channel == 1:
                mux = (self.inputs.port_e >> 3) & 7
                table = 0xfc45 if self.debug_read8(0x43) & 0x80 or self.debug_read8(0x4e) & 1 else 0xfd45
                wanted = self.case.get('coolant', 169)
                coolant_adc = min(range(256), key=lambda v: abs(self.mem[table + v] - wanted))
                return (128, 255, 145, 80, 110, 200, 100, coolant_adc)[mux]
            return {0:128, 2:255, 3:0,
                4:145 if self.adc.control & 0x1f == 0x11 else self.case.get('tps', 15),
                5:self.case.get('map', 90), 6:180, 7:128}[channel]
        return super().read8(address)


def run_case(name, image, retired, case, budget, main_calls=0):
    sim = Simulator.from_profile_file(ROOT / 'hac31_romsim/romsim/profiles/gm_16197427_31.json')
    # Load bytes directly into the modeled bus. No temporary firmware file.
    sim.memory.load_bin(image, 0)
    sim.memory.__class__ = FixtureMemory
    sim.memory.case = case; sim.memory.speed_reads = set()
    sim.trace._emit = lambda row: None
    sim.memory.mem[:0x400] = bytes(0x400); sim.memory.mem[0x800:0x900] = bytes(0x100)
    sim.reset(); sim.memory.config_value = 0x0b
    sim.memory.timer.__class__ = PrescaledTimer; sim.memory.timer.e_remainder = 0
    counts, slots, booted, minimum_sp = Counter(), set(), False, 0x3ff
    retired_entries, completed_control, maximum_control_cycles = [], 0, 0
    control_start = None
    for n in range(budget):
        pc = sim.cpu.s.pc
        if pc in retired:
            retired_entries.append(f'{pc:04X}'); break
        counts[pc] += 1
        if pc == 0x746c and not booted:
            booted = True; sim.inputs.rpm = case.get('rpm', 0)
        if pc == 0x93d0: control_start = sim.memory.cycle_counter
        if pc == 0x7a3c and control_start is not None:
            maximum_control_cycles = max(maximum_control_cycles, sim.memory.cycle_counter - control_start)
            completed_control += 1; control_start = None
            if main_calls and completed_control >= main_calls: break
        if booted: minimum_sp = min(minimum_sp, sim.cpu.s.sp)
        if pc == 0x7a44: slots.add(sim.memory.debug_read8(2) & 15)
        if n % 1000 == 0:
            for a in (0x284, 0x285, 0x812, 0x813):
                sim.memory.debug_write8(a, case.get('noise', 0))
            # Old Drive cells have no readers in the overlay. Noise them in
            # addition to range state, leaving reused single-controller RAM.
            if case.get('noise'):
                for a in range(0x2a7, 0x2b1): sim.memory.debug_write8(a, case['noise'])
                sim.memory.debug_write8(0xa2, case['noise'])
        sim.step_instruction()
        if sim.cpu.halted: raise AssertionError(f'Halted at {sim.cpu.s.pc:04X}')
    outputs = [(o.address, o.value, o.width) for o in sim.trace.outputs
               if o.address in (0x3fce, 0x3fe8, 0x3fe6, 0x3fdc, 0x3ff6, 0x3fec, 0x3fe4)]
    result = dict(name=name, fixture=case, steps=n + 1, booted=booted,
        checksum_error=bool(sim.memory.debug_read8(0x3a) & 2),
        retired_execution=retired_entries, slots_seen=sorted(slots),
        timer_entries=counts[0x793d], reference_entries=counts[0x74ea],
        fuel_calls=counts[0x7d4b], spark_calls=counts[0xa466], iac_calls=counts[0x93d0],
        completed_iac_calls=completed_control, maximum_observed_iac_call_cycles=maximum_control_cycles,
        minimum_sp=f'{minimum_sp:04X}',
        final={f'{a:04X}':sim.memory.debug_read8(a) for a in
               (6, 7, 8, 9, 0x36, 0x63, 0x283, 0x29d, 0x29e, 0x2a2, 0x2a4, 0x857, 0x87f)},
        speed_reads=[f'{p:04X}:{a:04X}' for p, a in sorted(sim.memory.speed_reads)],
        engine_output_digest=hashlib.sha256(json.dumps(outputs).encode()).hexdigest())
    assert booted and not result['checksum_error'] and not retired_entries, result
    assert len(slots) == 16 and completed_control > 0
    assert counts[0x793d] > 0 and counts[0x7d4b] > 0 and counts[0xa466] > 0
    assert all(0x7484 <= p <= 0x74a2 for p, a in sim.memory.speed_reads)
    if main_calls: assert completed_control >= main_calls, result
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('rom', type=Path)
    p.add_argument('--budget', type=int, default=420000)
    p.add_argument('--case', choices=('key_on', 'crank', 'hot_idle', 'cold_idle', 'cruise', 'power', 'hot_idle_legacy_noise'))
    p.add_argument('--main-calls', type=int, default=0, help='Require this many completed IAC main calls before ending a selected longer case')
    p.add_argument('--output', type=Path, default=ROOT / 'maps/maintenance/manual_idle_runtime_cases.json')
    args = p.parse_args()
    original = args.rom.read_bytes(); image, assembly, retired = overlay(original)
    cases = [('key_on', dict(rpm=0)), ('crank', dict(rpm=180, coolant=87)),
             ('hot_idle', dict(rpm=875)), ('cold_idle', dict(rpm=1275, coolant=87)),
             ('cruise', dict(rpm=2200, tps=75, map=130)),
             ('power', dict(rpm=3500, tps=200, map=210)),
             ('hot_idle_legacy_noise', dict(rpm=875, noise=255))]
    results = []
    for name, case in cases:
        if args.case and name != args.case: continue
        row = run_case(name, image, retired, case, args.budget, args.main_calls)
        results.append(row); print(json.dumps(row), flush=True)
    if not args.case: assert results[2]['engine_output_digest'] == results[-1]['engine_output_digest']
    assert args.rom.read_bytes() == original
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(dict(baseline_sha256=EXPECTED_SHA,
        overlay_sha256=hashlib.sha256(image).hexdigest(), firmware_file_created=False,
        scope='Full reset and modeled interrupt/scheduler execution. RPM is imposed, not an airflow-responsive engine model. No physical stability, mixture, motor or deadline proof.',
        cases=results), indent=2) + '\n')
