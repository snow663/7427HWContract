"""Compare compiled C startup/REF transactions with bounded stock execution.

Peripheral readbacks are explicit fixture inputs. This checks transaction width,
order, values and the REF latch; it does not model device timing or physical I/O.
"""
from hashlib import sha256
import json
from pathlib import Path
import random
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from build_factory_scheduler import recorded_rom
from factory_scheduler_replay import FixtureMemory, HC11CPU
from verify_factory_ownership import EVIDENCE
from verify_factory_rom_structure import EXPECTED_SHA256


class TraceMemory(FixtureMemory):
    def __init__(self, rom):
        super().__init__(rom)
        self.trace = []
        self.pc = None
        self.in_word = False
        self.board_readback = None
        self.strobe_samples = []

    def hardware(self, address):
        return 0x3000 <= address < 0x4000 and self.pc is not None and any(
            start <= self.pc < end
            for start, end in [(0x711F, 0x7164), (0xCC7C, 0xCCC1), (0x74EA, 0x751B)]
        )

    def read8(self, address):
        if address == 0x3062 and self.strobe_samples:
            value = self.strobe_samples.pop(0)
        else:
            value = super().read8(address)
        if not self.in_word and self.hardware(address):
            self.trace.append(["R", 8, address, value])
        return value

    def read16(self, address):
        self.in_word = True
        try:
            if address == 0x3FFC and self.pc == 0x7140:
                value = self.board_readback
            else:
                value = super().read16(address)
        finally:
            self.in_word = False
        if self.hardware(address):
            self.trace.append(["R", 16, address, value])
        return value

    def write8(self, address, value):
        super().write8(address, value)
        if not self.in_word and self.hardware(address):
            self.trace.append(["W", 8, address, value & 255])

    def write16(self, address, value):
        self.in_word = True
        try:
            super().write16(address, value)
        finally:
            self.in_word = False
        if self.hardware(address):
            self.trace.append(["W", 16, address, value & 65535])


rom = recorded_rom(json.loads(EVIDENCE.read_text()))
assert sha256(bytes([255]) * 0x4000 + rom.read(0x4000, 0xC000)).hexdigest() == EXPECTED_SHA256
memory = TraceMemory(rom)
cpu = HC11CPU(memory)


def run(start, stops):
    cpu.s.pc = start
    cpu.s.sp = 0x03FF
    cpu.s.ccr = 0xD0
    memory.trace.clear()
    for _ in range(1000):
        if cpu.s.pc in stops:
            return cpu.s.pc
        memory.pc = cpu.s.pc
        cpu.step()
    raise AssertionError(f"ROM execution budget at {cpu.s.pc:04X}")


def c_cases(mode, cases):
    result = subprocess.run(
        [sys.argv[1], mode], input="".join(" ".join(map(str, case)) + "\n" for case in cases),
        text=True, capture_output=True, check=True,
    )
    lines = result.stdout.splitlines()
    assert len(lines) == len(cases), (mode, result.stderr)
    return [json.loads(line) for line in lines]


rng = random.Random(0x31C74EA)
readbacks = [0, 65535, 0xB93A, 0xB91A] + [rng.randrange(65536) for _ in range(60)]
boot_cases = [(option, feedback, rng.randrange(65536)) for option in [0, 1] for feedback in readbacks]
for case, actual in zip(boot_cases, c_cases("--boot", boot_cases)):
    option, feedback, serial = case
    # Only this documented calibration selector changes in the option=1 cases.
    memory.mem[0x400B] = (rom.read(0x400B, 1)[0] & 0xFE) | option
    memory.mem[0x302E:0x3030] = serial.to_bytes(2, "big")
    memory.board_readback = feedback
    memory.strobe_samples = []
    assert run(0x7100, {0x7164}) == 0x7164
    assert actual == {"status": 0, "pending": 0, "tail": 0, "events": memory.trace}, (case, actual, memory.trace)
    assert len(memory.trace) == 57
memory.mem[0x400B] = rom.read(0x400B, 1)[0]

ref_cases = [
    (timer, rpm, pending, inhibited, 0, rng.randrange(256), rng.randrange(256))
    for timer in [0, 0xFFFF, 0xFE80, 0x1234] for rpm in range(256)
    for pending in [0, 1] for inhibited in [0, 1]
]
ref_cases.extend(
    (timer, rpm, pending, inhibited, 1, 0, 255)
    for timer in [0, 65535] for rpm in [0, 255] for pending in [0, 1] for inhibited in [0, 1]
)
for case, actual in zip(ref_cases, c_cases("--reference", ref_cases)):
    timer, rpm, pending, inhibited, factory, first, second = case
    memory.mem[0x300E:0x3010] = timer.to_bytes(2, "big")
    memory.mem[0x62] = rpm
    memory.mem[0x44] = factory | (inhibited << 4)
    memory.mem[0x50] = pending << 5
    memory.strobe_samples = [first, second]
    stop = run(0x74EA, {0x751B, 0xFC11})
    expected = {
        "status": 4 if stop == 0xFC11 else 1,  # factory boundary / unported continuation
        "pending": int(bool(memory.mem[0x50] & 0x20)),
        "tail": int(stop == 0x751B),
        "events": memory.trace,
    }
    assert actual == expected, (case, actual, expected)
    assert len(memory.trace) == (0 if factory else 7)

print(f"{len(boot_cases)} startup and {len(ref_cases)} REF compiled-C cases match stock transaction/latch results.")
