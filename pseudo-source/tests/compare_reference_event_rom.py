"""Differential execution of the complete resident REF handler and its callees.

Inputs provide RAM, calibration variants and explicit peripheral samples. CPU
entry/RTI is real on the ROM side; C ABI, physical timing and ASIC semantics
remain target work. Timer words are a supplied sequence, not a hardware model.
"""
from hashlib import sha256
import json
from pathlib import Path
import random
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from build_factory_scheduler import recorded_rom
from factory_scheduler_replay import FixtureMemory, HC11CPU
from factory_rom_decode import decode
from verify_factory_ownership import EVIDENCE
from verify_factory_rom_structure import EXPECTED_SHA256

BLOCKS = [(0, 0x900), (0x3000, 0x3070), (0x3FC0, 0x3FFE), (0x4000, 0x5B04)]
rom = recorded_rom(json.loads(EVIDENCE.read_text()))
assert sha256(bytes([255])*0x4000 + rom.read(0x4000, 0xC000)).hexdigest() == EXPECTED_SHA256
binary = sys.argv[1]
defaults = json.loads(subprocess.check_output([binary, '--defaults'], text=True))
for address, value in defaults:
    assert rom.read(address, 1)[0] == value, (hex(address), value, rom.read(address, 1).hex())


class Failure(Exception):
    pass


class Memory(FixtureMemory):
    def __init__(self):
        super().__init__(rom)
        self.events = []
        self.word_io = False
        self.attempts = self.fail_at = self.timer_reads = 0
        self.timer_seed = self.timer_step = 0

    def record(self, kind, width, address, value):
        self.attempts += 1
        if self.attempts == self.fail_at:
            raise Failure
        self.events.append([kind, width, address, value])

    def read8(self, address):
        value = super().read8(address)
        if not self.word_io and 0x3000 <= address < 0x4000:
            self.record('R', 8, address, value)
        return value

    def read16(self, address):
        if not 0x3000 <= address < 0x4000:
            return super().read16(address)
        self.word_io = True
        try:
            value = ((self.timer_seed + self.timer_reads*self.timer_step) & 65535
                     if address == 0x300E else super().read16(address))
            self.record('R', 16, address, value)
            if address == 0x300E:
                self.timer_reads += 1
            return value
        finally:
            self.word_io = False

    def write8(self, address, value):
        if not self.word_io and 0x3000 <= address < 0x4000:
            self.record('W', 8, address, value & 255)
        if address == 0x3023:  # Explicit CPU W1C fixture, no timer-edge generation.
            self.mem[address] &= ~value & 255
        else:
            super().write8(address, value)

    def write16(self, address, value):
        if not 0x3000 <= address < 0x4000:
            return super().write16(address, value)
        self.record('W', 16, address, value & 65535)
        self.word_io = True
        try:
            super().write16(address, value)
        finally:
            self.word_io = False


memory = Memory()
coverage = set()


def execute(packed, step, fail=0, helper=False):
    offset = 0
    for start, end in BLOCKS:
        size = end-start
        memory.mem[start:end] = packed[offset:offset+size]
        offset += size
    assert offset == len(packed)
    memory.events.clear()
    memory.attempts = memory.timer_reads = memory.cycle_counter = 0
    memory.fail_at = fail
    memory.timer_seed = int.from_bytes(memory.mem[0x300E:0x3010], 'big')
    memory.timer_step = step
    cpu = HC11CPU(memory)
    cpu.s.pc, cpu.s.sp, cpu.s.ccr = 0x7000, 0x03FF, 0xC0
    cpu.s.a, cpu.s.b, cpu.s.x, cpu.s.y = 0x12, 0x34, 0x5678, 0x9ABC
    before = (cpu.s.pc, cpu.s.sp, cpu.s.ccr, cpu.s.a, cpu.s.b, cpu.s.x, cpu.s.y)
    if helper:
        cpu.s.pc, cpu.s.ccr = 0x7594, 0xD0
    else:
        assert cpu.interrupt(0xFFF2)
    delay_start = None
    try:
        for _ in range(4000):
            pc = cpu.s.pc
            if pc in ({0x7630} if helper else {0x7000, 0xFC11}):
                break
            coverage.add(pc)
            if pc == 0x7524:
                delay_start = memory.cycle_counter
            cpu.step()
            if pc == 0x7527:
                cycles = memory.cycle_counter-delay_start
                assert cycles == 33
                memory.record('D', 0, 0, cycles)
        else:
            raise AssertionError(f'REF execution budget at {cpu.s.pc:04X}')
        status = 4 if cpu.s.pc == 0xFC11 else 0
        if status == 0 and not helper:
            assert (cpu.s.pc, cpu.s.sp, cpu.s.ccr, cpu.s.a, cpu.s.b, cpu.s.x, cpu.s.y) == before
    except Failure:
        status = 2
    ram = bytes(memory.mem[:0x900])
    # The ROM writes its real CPU/JSR stack. C has no target frame yet.
    ram = ram[:0x3C0] + bytes(0x40) + ram[0x400:]
    io = bytes(memory.mem[0x3000:0x3070] + memory.mem[0x3FC0:0x3FFE])
    return {'status': status, 'ram': ram.hex(), 'io': io.hex(), 'events': list(memory.events)}


rng = random.Random(0x31E751B)
cal_bytes = rom.read(0x4000, 0x1B04)


def packed_image(edits=None, varied=False, random_state=True):
    image = bytearray(65536)
    for start, end in BLOCKS[:-1]:
        image[start:end] = rng.randbytes(end-start) if random_state else bytes(end-start)
    image[0x4000:0x5B04] = cal_bytes
    image[0x44] &= 0xFE  # Ordinary mode; factory fixtures are explicit below.
    if varied:
        for address, _ in defaults:
            image[address] = rng.randrange(256)
    if edits:
        for address, value in edits.items():
            if isinstance(value, bytes):
                image[address:address+len(value)] = value
            else:
                image[address] = value
    return b''.join(image[start:end] for start, end in BLOCKS)


cases = []
# Stock calibration plus broad, named-calibration variants use the same ROM code.
for varied in [False, True]:
    for _ in range(1024):
        cases.append((packed_image(varied=varied), rng.randrange(65536), 0))
# Deliberate gates/counter boundaries and both timer banks.
for running in [0, 0x10]:
    for count in [0, 1, 2, 3, 4, 254, 255]:
        for packet in [0, 1, 32, 33, 34, 255, 256, 32767, 32768, 65535]:
            for flag in [0, 1]:
                cases.append((packed_image({
                    0x44: 0, 0x4F: running, 0x50: 1, 0x400B: 0x31,
                    0x400C: 0x0C, 0x400E: 0x10, 0x19: 0,
                    0x2CD: count, 0x2CE: count, 0x829: count, 0x51: 1,
                    0x3023: flag, 0x254: packet.to_bytes(2, 'big'),
                    0x2CF: packet.to_bytes(2, 'big'), 0x4DCD: bytes(17),
                    0x73: 0x40, 0x4516: 0, 0x48DA: 255,
                    0x4518: rng.randrange(256),
                }), rng.choice([0, 1, 2, 32767, 32768, 65535]), 0))
# Force asynchronous shaping, crank gain branches, and age/cap boundaries.
for age in [0, 1, 7, 8, 23, 24, 63, 64, 127, 128, 255]:
    for seed in [0, 1, 128, 255, 256, 32768, 65535]:
        for hot in [0, 0x10]:
            cases.append((packed_image({
                0x44: 0, 0x4F: 0, 0x400B: 4, 0x400C: 4, 0x400E: 0x10,
                0x2CD: 2, 0x2CE: age, 0x2CF: seed.to_bytes(2, 'big'),
                0x04: hot, 0x06: rng.choice([0, 0x71, 0x72, 255]),
            }), rng.randrange(65536), 0))
# Valid complete-handler route to the zero-floor event-age decrement.
cases.append((packed_image({0x44:0,0x4F:0,0x400B:0x10,0x400C:4,0x19:0,
                            0x2CD:2,0x2CE:0,0x53:0x20,0x3023:0,0x4960:255,
                            0x4DCD:bytes(17),0x2CF:bytes.fromhex('ffff'),0x256:0}),0,0))
# Exact N-only comparison boundaries for both running timer-arm helpers.
for difference in [0x7FFF,0x8000,0x8001]:
    prior=(0x123A-difference)&65535
    cases.append((packed_image({0x44:0,0x4F:0x10,0x50:0,0x51:0,0x73:0x40,
        0x400B:1,0x400C:0,0x3000:0x18,0x300E:bytes.fromhex('1234'),
        0x81F:bytes(2),0x301C:prior.to_bytes(2,'big'),0x301E:prior.to_bytes(2,'big')}),0,0))
# Factory must leave before prefix/device activity.
for _ in range(16):
    cases.append((packed_image({0x44: rng.randrange(256) | 1}), 0, 0))


def compare(batch, label, helper=False):
    payload = ''.join(f'{step} {fail}\n{packed.hex()}\n' for packed, step, fail in batch)
    process = subprocess.run([binary, *(['--crank-timer'] if helper else [])], input=payload, text=True, capture_output=True, check=True)
    actuals = process.stdout.splitlines()
    assert len(actuals) == len(batch), (label, process.stderr)
    for index, (case, line) in enumerate(zip(batch, actuals)):
        actual = json.loads(line)
        expected = execute(*case, helper=helper)
        # Discard only the RAM bytes used by the actual ROM call/interrupt stack.
        ram = bytes.fromhex(actual['ram'])
        actual['ram'] = (ram[:0x3C0] + bytes(0x40) + ram[0x400:]).hex()
        if actual != expected:
            differences = {}
            for field in expected:
                if actual[field] != expected[field]:
                    if field == 'ram':
                        a, b = bytes.fromhex(actual[field]), bytes.fromhex(expected[field])
                        differences[field] = [(hex(i), x, y) for i, (x, y) in enumerate(zip(a, b)) if x != y][:25]
                    else:
                        differences[field] = (actual[field], expected[field])
            raise AssertionError((label, index, differences))


compare(cases, 'complete REF')
# Inject each failure position for representative paths, including the delay.
failures = []
for selected in [cases[0], cases[1], cases[1024], cases[1025], cases[2048], cases[2049], cases[-17]]:
    packed, step, _ = selected
    result = execute(packed, step)
    failures.extend((packed, step, index) for index in range(1, len(result['events'])+1))
compare(failures, 'I/O failure prefixes')
# Two saturation guards cannot fire through the complete handler's limited
# timer-pulse producer. Exercise those guards at the timer driver's own entry.
helper_cases=[]
for flags in [0,1]:
    for pulse in [0,32767,32768,65535]:
        for latch in [0,0x20]:
            for age in [0,255]:
                helper_cases.append((packed_image({0x44:0,0x250:pulse.to_bytes(2,'big'),
                    0x2CD:2,0x2CE:age,0x53:latch,0x3023:flags,0x4960:255}),rng.randrange(65536),0))
# Exact N-only differences7FFF/8000/8001 for both alternate crank branches.
for flags in [0,1]:
    for step in [32765,32766,32767]:
        helper_cases.append((packed_image({0x44:0,0x250:bytes(2),0x2CD:2,
            0x53:0,0x3023:flags}),step,0))
full_coverage=set(coverage)
compare(helper_cases,'direct crank-timer entry',helper=True)
# Every decoded instruction in these bounded bodies/helpers must be exercised.
required = set()
for start, end in [(0x751B, 0x7875), (0x8548, 0x858B), (0xF479, 0xF499), (0xF4BD, 0xF4DE), (0xF550, 0xF564)]:
    pc = start
    while pc < end:
        required.add(pc)
        pc = decode(rom.read, pc).next_pc
missing = required-coverage
assert required-full_coverage == {0x75B9,0x760D}, 'Unexpected full-handler coverage boundary'
assert not missing, 'Unexercised REF instructions: '+','.join(f'{pc:04X}' for pc in sorted(missing))
print(f'{len(cases)} complete REF C/ROM cases and {len(failures)} I/O failure prefixes match; '
      f'{len(helper_cases)} direct timer-entry cases match; all {len(required)} scoped instruction starts exercised; '
      f'{len(defaults)} calibration bytes verified.')
